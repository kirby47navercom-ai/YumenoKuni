// Isolated, explicitly seeded scenes only. Existing campaigns are not replayed.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/v4-trial-expansion-'+Date.now());
const manifest=JSON.parse(await fs.readFile(path.join(root,'Saved/trial-expansion-fixtures-20261101/manifest.json'),'utf8'));
assert(manifest.fixture&&!manifest.normalRoute);
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const delay=ms=>new Promise(r=>setTimeout(r,ms)),runs=[];
const keys={c:[67,'KeyC'],Control:[17,'ControlLeft'],Tab:[9,'Tab'],Enter:[13,'Enter'],Backspace:[8,'Backspace'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD']};
for(const fixture of manifest.fixtures){
 const folder=path.join(work,'chapter-'+fixture.chapter);await fs.mkdir(path.join(folder,'UserData'),{recursive:true});
 await fs.copyFile(path.join(root,'..',fixture.file),path.join(folder,'UserData/savegames.json'));
 const graph=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/chapters/'+fixture.chapter+'.json'),'utf8'));
 let probe,last;
 try{
  probe=await editorWindowProbe({work:folder,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
  const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
  const stats=async()=>{last=JSON.parse((await call('Stats')).outputs.result);assert(!last.error&&!last.routeBlocked,JSON.stringify(last));return last;};
  const sample=async()=>{const frame=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(65);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=frame+2,'input frames',10000);};
  const key=async(k,type)=>{const[windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
  const tap=async k=>{await key(k,'keyDown');await sample();await key(k,'keyUp');await sample();};
  const click=async(x,y)=>{for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x,y,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}};
  await tap('c');await probe.until(async()=>{const s=await stats();return s.chapter===Number(fixture.chapter)&&graph.nodes[s.node]?.source?.file?.startsWith(fixture.sourcePrefix+'_');},'isolated new scene Continue',60000);
  await delay(400);await probe.capture('new-scene-entry.png');await call('DebugFastRead');
  let saved=false,returned=false,musicPlayed=false;const visited=new Set(),musicLocations=new Set(),start=Date.now();await key('Control','keyDown');
  while(Date.now()-start<240000){
   const s=await stats(),n=graph.nodes[s.node];assert(n,s.node);
   const ownBranch=n.type==='branch'&&n.cases?.length&&n.cases.every(c=>graph.nodes[c.to]?.source?.file?.startsWith(fixture.sourcePrefix+'_'));
   if(!n.source?.file?.startsWith(fixture.sourcePrefix+'_')&&!ownBranch){await key('Control','keyUp');returned=true;break;}
   if(n.source)visited.add(n.source.location);
   // Fixture presentation is deliberately empty. Prove normal section entry
   // selects the court bed, rather than asserting a seeded music value.
   if(n.source&&n.source.location!==graph.nodes[fixture.entry].source.location){
    assert.deepEqual(s.audioV4.missing,[]);musicLocations.add(n.source.location);
    if(!musicPlayed){
     await key('Control','keyUp');const samples=[],cue='bgm_trial_main_'+fixture.chapter;
     try{await probe.until(async()=>{const audio=await probe.evaluate('window.hbPlayerDebug.audio()');samples.push(audio);assert.deepEqual(audio.errors,[]);return audio.state==='running'&&audio.voices.some(v=>v.playing&&!v.virtual&&JSON.stringify(v).includes(cue)&&v.time>.25&&v.peak>.0001);},'actual selected court PCM after unseeded section entry',15000);}
     finally{await fs.writeFile(path.join(folder,'actual-court-audio.json'),JSON.stringify({cue,samples},null,2));}
     musicPlayed=true;await key('Control','keyDown');
    }
   }
   if(fixture.chapter==='2'&&!saved&&n.type==='say'&&n.source.location==='T2-Q02'){
    await key('Control','keyUp');await tap('Tab');await click(1047,480);await padSystemAction(stats,tap,'save');
    const disk=JSON.parse(await fs.readFile(path.join(folder,'UserData/savegames.json'),'utf8'));
    const head=JSON.parse(Object.entries(disk.items).find(([k])=>k.includes('yumeno-progress-v4.project.'))[1]);
    assert.equal(head.node,s.node);assert.equal(head.flags['T2-C01'],'A');
    assert.equal(head.presentation.bed,'bgm_trial_main_'+fixture.chapter,'actual saved music is wrong');
    await fs.copyFile(path.join(folder,'UserData/savegames.json'),path.join(folder,'new-scene-actual-manual-savegames.json'));
    await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');
    await probe.until(async()=>(await stats()).node===s.node,'same saved new dialogue',60000);
    assert.equal((await stats()).audioV4.bed,'bgm_trial_main_'+fixture.chapter,'actual save/Continue lost court music');
    saved=true;await probe.capture('actual-manual-save-continue.png');await key('Control','keyDown');
   }else await delay(25);
  }
  assert(returned,'scene did not return to existing dialogue/input');assert(musicPlayed&&musicLocations.size>0,'no nonseeded court PCM observed');if(fixture.chapter==='2')assert(saved);
  await probe.capture('returned-existing-scene.png');assert.deepEqual(probe.errors,[]);
  const report={ok:true,fixture:true,normalRoute:false,chapter:fixture.chapter,sourcePrefix:fixture.sourcePrefix,expectedReturn:fixture.return,observedReturn:last.node,observedLocations:[...visited],actualManualSaveContinue:saved,actualCourtMusicLocations:[...musicLocations],musicSeededInFixture:false,actualCourtPCMPlayed:musicPlayed,subjectiveAuditionClaim:false,elapsedQaSeconds:(Date.now()-start)/1000,scope:'Actual native fixture entry/read-through/original return and nonseeded court PCM playback. Explicitly seeded prior choice/evidence/court state; Control/FastRead elapsed is not ordinary playtime or a normal campaign pass.'};
  await fs.writeFile(path.join(folder,'report.json'),JSON.stringify(report,null,2));runs.push(report);
 }catch(e){await fs.writeFile(path.join(folder,'failure.json'),JSON.stringify({error:e.stack,last,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw e;}finally{await probe?.stop?.();}
}
await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,fixture:true,normalRoute:false,executable,work,runs},null,2));console.log(JSON.stringify({ok:true,work,chapters:runs.map(r=>r.chapter)}));
