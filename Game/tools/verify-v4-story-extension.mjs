// New authored scenes only. Explicit chapter-entry fixture, real choices and Save/Continue.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/v4-story-extension-'+Date.now());await fs.mkdir(work,{recursive:true});
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const graph=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/chapters/6.json'),'utf8'));
const keys={Control:[17,'ControlLeft'],Tab:[9,'Tab'],Enter:[13,'Enter'],Backspace:[8,'Backspace'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],c:[67,'KeyC']},runs=[];
const resumeRun=process.argv.find(a=>a.startsWith('--resume-run='))?.slice('--resume-run='.length);
if(resumeRun){const prior=JSON.parse(await fs.readFile(path.join(resumeRun,'failure.json'),'utf8'));assert.deepEqual(prior.runs.map(r=>r.route),['A']);runs.push(...prior.runs);await fs.mkdir(path.join(work,'UserData'),{recursive:true});await fs.copyFile(path.join(resumeRun,'UserData/savegames.json'),path.join(work,'UserData/savegames.json'));}
const delay=ms=>new Promise(r=>setTimeout(r,ms));let probe,last;
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const stats=async()=>{last=JSON.parse((await call('Stats')).outputs.result);assert(!last.error&&!last.routeBlocked,JSON.stringify(last));return last;};
 const key=async(k,type)=>{const[windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
 const sample=async()=>{const frame=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(55);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=frame+2,'sample',10000);};
 const tap=async k=>{await key(k,'keyDown');await sample();await key(k,'keyUp');await sample();};
 for(const route of resumeRun?['B','C']:['A','B','C']){
  const resumed=!!resumeRun&&route==='B';await key('Control','keyUp');if(resumed)await tap('c');else await call('DebugV4Chapter',{index:6});await call('DebugFastRead');await sample();const first=await stats();assert.equal(first.chapter,6);if(resumed)assert(first.node.endsWith('6-LC01'));else assert(graph.nodes[first.node].source.file.startsWith('188_'));
  const visited=new Set(),menus=[];let saved=resumed,returned=false;const start=Date.now();await key('Control','keyDown');
  while(Date.now()-start<180000){
   const s=await stats(),node=graph.nodes[s.node];assert(node,s.node);visited.add(node.source?.location||'');
   if(node.source?.file.startsWith('16a_')){await key('Control','keyUp');returned=true;break;}
   if(s.v4Kind==='menu'){
    if(s.choice.pending>=0){await delay(40);continue;}
    await key('Control','keyUp');assert(['6-DC01','6-LC01'].some(flag=>node.id.endsWith(flag)));
    if(route==='B'&&node.id.endsWith('6-LC01')&&!saved){
     await tap('Tab');for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x:1047,y:480,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}
     await padSystemAction(stats,tap,'save');const disk=JSON.parse(await fs.readFile(path.join(work,'UserData/savegames.json'),'utf8'));
     const head=JSON.parse(Object.entries(disk.items).find(([k])=>k.includes('yumeno-progress-v4.project.'))[1]);assert.equal(head.node,s.node);assert.equal(head.flags['6-DC01'],'B');assert(!Object.hasOwn(head.flags,'6-LC01'));assert.equal(head.playerProgress.skyPhase,0);
     await fs.copyFile(path.join(work,'UserData/savegames.json'),path.join(work,'choice-after-corridor-savegames.json'));
     await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');await probe.until(async()=>(await stats()).node===s.node,'same new saved menu',60000);saved=true;
    }
    const target=node.options.findIndex(o=>o.id===route);assert(target>=0);for(let i=0;i<4&&(await stats()).choice.hover!==target;i++)await tap('s');assert.equal((await stats()).choice.hover,target);await probe.capture(route+'-'+node.source.location+'-choice.png');await tap('Enter');await probe.until(async()=>(await stats()).node!==s.node,'actual authored choice confirmation',10000);menus.push(node.source.location);await key('Control','keyDown');
   }else await delay(20);
  }
  assert(returned,'new scene never returned to existing body');assert.equal(menus.length,resumed?1:2);assert((resumed||visited.has('6-DR01'+route))&&visited.has('6-LR01'+route));for(const other of 'ABC')if(other!==route)assert(!visited.has('6-DR01'+other)&&!visited.has('6-LR01'+other));if(route==='B')assert(saved);
  runs.push({route,menus,observedLocations:[...visited],returnedNode:last.node,actualManualSaveContinue:saved,resumedFromPriorActualSave:resumed?resumeRun:null,wallSeconds:(Date.now()-start)/1000});await probe.capture(route+'-returned-original-body.png');
 }
 assert.deepEqual(probe.errors,[]);const report={ok:true,fixture:true,executable,work,runs,scope:'Only the newly authored corridor/arrival scenes. Explicit native chapter6 entry fixture, physical A/A B/B C/C selections and actual B-route manual Save/Continue. All9 source combinations have a separate pure graph proof. Control/DebugFastRead QA pacing; elapsed seconds are not ordinary reading/playtime.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,work,runs:runs.map(r=>({route:r.route,saveContinue:r.actualManualSaveContinue}))}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,last,runs,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
