// Current source IDs only. Direct reply fixtures plus one actual authored FTE menu.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),work=path.join(root,'Saved/v4-dialogue-continuity-'+Date.now());
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const proof=JSON.parse(await fs.readFile(path.join(root,'Saved/dialogue-continuity-source-proof-2026110117.json'),'utf8'));
const figures=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/court.json'),'utf8')).figures;
const cases=[
 {id:'1',chapter:'1',node:'v4:11a2:1-14:e:945a637990d6:1',portrait:'kaede_T03',dead:[]},
 {id:'2',chapter:'2',node:'v4:12a3:2-30:e:1e4f93b158ea:1',portrait:'yuu_T03',dead:['kaede','taiga']},
 {id:'3',chapter:'3',node:'v4:13a3:3-27a:e:7e746267bb14:1',portrait:'haruka_C02',dead:['kaede','taiga','ai','yuu']},
 {id:'menu',chapter:'1',node:'v4:1:F1-B:call:21',target:'v4:21:KOTO-01B:menu',portrait:'koto',dead:[]},
 {id:'exit',chapter:'1',node:'v4:11a:1-08:e:ed3fda78a865:1',after:'v4:11a:1-08:e:80be0baa3474:1',portrait:'kaede',dead:[]},
 {id:'seat',chapter:'3',node:'v4:13a4:3-34:e:c45624173e76:1',after:'v4:13a4:3-34:e:1054902a6406:1',bridge:true,portrait:'haruka',dead:['kaede','taiga','ai','yuu']}
];
const only=process.argv.find(v=>v.startsWith('--only='))?.slice(7),runs=[];
assert(!only||cases.some(c=>c.id===only));
const delay=ms=>new Promise(r=>setTimeout(r,ms)),keys={c:[67,'KeyC'],Control:[17,'ControlLeft'],Enter:[13,'Enter'],Tab:[9,'Tab'],a:[65,'KeyA'],d:[68,'KeyD'],s:[83,'KeyS'],Backspace:[8,'Backspace']};
for(const fixture of cases.filter(c=>!only||c.id===only)){
 const folder=path.join(work,fixture.id);await fs.mkdir(path.join(folder,'UserData'),{recursive:true});
 const graph=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/chapters/'+fixture.chapter+'.json'),'utf8'));
 const selected=graph.nodes[fixture.after||fixture.target||fixture.node];
 if(fixture.after&&!fixture.bridge)assert(!Object.hasOwn(proof.assignments,selected.id));else assert.equal(proof.assignments[selected.id],fixture.portrait);
 const seed=JSON.parse(await fs.readFile(path.join(root,'Saved/editorial-fixtures-20261101/chapter-'+fixture.chapter+'.json'),'utf8'));
 const headKey=Object.keys(seed.items).find(k=>k.includes('yumeno-progress-v4.project.')),head=JSON.parse(seed.items[headKey]);
 head.node=fixture.node;head.snapshot='2026110117-'+(fixture.id==='menu'?'4':fixture.id==='exit'?'5':fixture.id==='seat'?'6':fixture.id);head.court.active=false;head.court.dead=fixture.dead;head.flags={};head.stack=[];head.world={};head.worldId='hotel_lobby';head.presentation={};seed.items[headKey]=JSON.stringify(head);
 await fs.writeFile(path.join(folder,'UserData/savegames.json'),JSON.stringify(seed));let probe,last;
 try{
  probe=await editorWindowProbe({work:folder,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
  const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
  const stats=async()=>{last=JSON.parse((await call('Stats')).outputs.result);assert(!last.error&&!last.routeBlocked,JSON.stringify(last));return last;};
  const key=async(k,type)=>{const[windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
  const sample=async()=>{const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(65);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=f+2,'sampled input',10000);};
  const tap=async k=>{await key(k,'keyDown');await sample();await key(k,'keyUp');await sample();};
  const visible=async()=>{
   const s=await stats();assert.equal(s.portrait,figures[fixture.portrait].texture);
   const ui=await probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="Portrait"]'),r=e.getBoundingClientRect(),s=getComputedStyle(e);return {display:s.display,visibility:s.visibility,opacity:s.opacity,rect:[r.x,r.y,r.width,r.height]};})()`);
   assert.notEqual(ui.display,'none');assert.notEqual(ui.visibility,'hidden');assert(Number(ui.opacity)>0&&ui.rect[3]>900);return {node:s.node,speaker:s.speaker,portrait:s.portrait,ui};
  };
  await tap('c');await probe.until(async()=>{const s=await stats();return fixture.target?graph.nodes[s.node]?.source?.file.startsWith('21_'):s.node===fixture.node&&s.mode==='story';},'existing saved source entry',60000);await call('DebugFastRead');
  let manualSaveContinue=false,view;
  if(fixture.after){
   const before=await stats();assert(before.portrait.includes('/'+fixture.portrait));await probe.capture('before-actual-'+(fixture.bridge?'sit':'exit')+'.png');
   await probe.until(async()=>{const d=JSON.parse((await call('DialogueStats')).outputs.result);return d.raw===graph.nodes[fixture.node].text&&d.shown>=d.length;},'previous live utterance ready',10000);
   await tap('Enter');await probe.until(async()=>{const s=await stats();return s.node===fixture.after&&s.mode==='story';},'authored exit and exact monologue',10000);
   const s=await stats(),d=JSON.parse((await call('DialogueStats')).outputs.result);assert.equal(d.raw,selected.text);
   if(fixture.bridge){assert.equal(d.speaker,'미오');assert.equal(s.world.space,'screening_room');assert.equal(s.portrait,before.portrait);view={beforePortrait:before.portrait,after:await visible(),dialogue:d};await probe.capture('after-actual-sit-keeps-listener.png');}
   else{
    assert.equal(s.portrait,'');assert.equal(d.speaker,'');
    const hidden=await probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="Portrait"]'),s=getComputedStyle(e);return s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0;})()`);assert(hidden);
    view={beforePortrait:before.portrait,afterPortrait:s.portrait,hidden:true,monologue:d};await probe.capture('after-actual-exit-no-ghost.png');
   }
  }else if(fixture.target){
   let firstChoice=false;await key('Control','keyDown');const start=Date.now();
   while(Date.now()-start<150000){
    const s=await stats(),n=graph.nodes[s.node];
    if(s.node===fixture.target&&s.choice){await key('Control','keyUp');break;}
    if(n?.type==='menu'&&s.choice?.pending<0){await key('Control','keyUp');assert.equal(n.id,'v4:21:KOTO-01A:menu');assert.equal(n.options[0].id,'A');await tap('Enter');firstChoice=true;await key('Control','keyDown');}
    await delay(20);
   }
   assert(firstChoice);assert.equal((await stats()).node,fixture.target);view=await visible();await probe.capture('live-listener-menu.png');
   await tap('Tab');for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x:1047,y:480,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}
   await padSystemAction(stats,tap,'save');const disk=JSON.parse(await fs.readFile(path.join(folder,'UserData/savegames.json'),'utf8')),saved=JSON.parse(disk.items[headKey]);
   assert.equal(saved.node,fixture.target);assert.equal(saved.flags['KOTO-01A'],'A');assert(!Object.hasOwn(saved.flags,'KOTO-01B'));assert(!saved.flags['fte:21:complete']);
   await fs.copyFile(path.join(folder,'UserData/savegames.json'),path.join(folder,'actual-manual-savegames.json'));
   await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');await probe.until(async()=>{const s=await stats();return s.node===fixture.target&&s.choice;},'actual exact unfinished menu Continue',60000);
   await visible();await probe.capture('actual-menu-continue.png');manualSaveContinue=true;
   await tap('Enter');await probe.until(async()=>{const s=await stats();return s.mode==='story'&&s.node!==fixture.target;},'actual selected existing response',10000);assert.equal(graph.nodes[last.node].source.file.split('_')[0],'21');
  }else{
   const d=JSON.parse((await call('DialogueStats')).outputs.result);assert.equal(d.raw,selected.text);assert.equal(d.speaker,'미오');assert(!d.trial);
   view=await visible();await delay(800);await probe.capture('live-listener-protagonist-reply.png');
  }
  assert.deepEqual(probe.errors,[]);const result={ok:true,id:fixture.id,fixture:true,normalRoute:false,literalNode:selected.id,literalSpeaker:selected.speaker||'',expectedPortrait:fixture.portrait,view,actualManualSaveContinue:manualSaveContinue};runs.push(result);await fs.writeFile(path.join(folder,'report.json'),JSON.stringify(result,null,2));
 }catch(e){await fs.writeFile(path.join(folder,'failure.json'),JSON.stringify({error:e.stack,last,runs},null,2));try{await probe?.capture('failure.png');}catch{}throw e;}
 finally{await probe?.stop?.();}
}
await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,executable,runs,scope:'Three existing main-story protagonist reply IDs keep the proven interlocutor physical pose, with literal protagonist name/text unchanged. One existing FTE menu actually selected, saved and Continued before its next answer. Seeded fixture state, not normal full campaign or duration proof.'},null,2));
console.log(JSON.stringify({ok:true,work,cases:runs.map(r=>r.id)}));
