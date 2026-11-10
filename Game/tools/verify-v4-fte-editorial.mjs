// Existing FTE calls from isolated saves; actual words/choices/return, not campaign time.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root);
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const graph=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/chapters/2.json'),'utf8'));
const revisions=JSON.parse(await fs.readFile(path.join(repo,'tools/v4_editorial_revisions.json'),'utf8')).revisions.filter(r=>['44','45'].includes(r.prefix));
const targets=new Map(revisions.map(r=>{
 const text=r.after.split('] ',2)[1],found=Object.values(graph.nodes).filter(n=>n.type==='say'&&n.source?.file.startsWith(r.prefix+'_')&&n.source.location===r.location&&n.text===text&&!n.id.includes(':late:'));
 assert.equal(found.length,1,r.after);return [found[0].id,found[0]];
}));
assert.equal(targets.size,28);
const source=JSON.parse(await fs.readFile(path.join(root,'Saved/editorial-fixtures-20261101/chapter-2.json'),'utf8'));
const work=path.join(root,'Saved/v4-fte-editorial-'+Date.now()),runs=[],seen=new Set();
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const keys={c:[67,'KeyC'],Control:[17,'ControlLeft'],Enter:[13,'Enter'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],Tab:[9,'Tab'],Backspace:[8,'Backspace']};
const prefixes=process.argv.includes('--rei-only')?['45']:['44','45'];
const listeners=process.argv.includes('--listeners');
for(const prefix of prefixes)for(let route=1;route<=3;route++){
 const folder=path.join(work,prefix+'-'+route);await fs.mkdir(path.join(folder,'UserData'),{recursive:true});
 const seeded=structuredClone(source),headKey=Object.keys(seeded.items).find(k=>k.includes('yumeno-progress-v4.project.')),head=JSON.parse(seeded.items[headKey]);
 const caller=graph.nodes['v4:2:F2-A:call:'+prefix];assert(caller?.type==='call');
 let returnedSay=caller.returnTo;
 while(graph.nodes[returnedSay]?.type==='stage')returnedSay=graph.nodes[returnedSay].next;
 assert.equal(graph.nodes[returnedSay]?.type,'say');
 head.node=caller.id;head.snapshot='2026110116-'+prefix+'-'+route;head.court.active=false;head.court.dead=['kaede','taiga'];head.presentation={};head.world={};head.worldId=prefix==='45'?'park_garden':'hotel_lobby';head.stack=[];
 head.flags=prefix==='44'?{'fte:24:complete':true,'F-YU01-A':'A'+route,'F-YU01-B':route===2?'B2':'B1','F-YU01-B2-N':'N2'}:{'fte:27:complete':true,'F-RE01-B':'B'+route};
 seeded.items[headKey]=JSON.stringify(head);await fs.writeFile(path.join(folder,'UserData/savegames.json'),JSON.stringify(seeded));
 let probe,last;
 try{
  probe=await editorWindowProbe({work:folder,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
  const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
  const stats=async()=>{last=JSON.parse((await call('Stats')).outputs.result);assert(!last.error&&!last.routeBlocked,JSON.stringify(last));return last;};
  const key=async(k,type)=>{const[windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
  const sample=async()=>{const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(60);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=f+2,'input sampled',10000);};
  const tap=async k=>{await key(k,'keyDown');await sample();await key(k,'keyUp');await sample();};
  await tap('c');await probe.until(async()=>graph.nodes[(await stats()).node]?.source?.file.startsWith(prefix+'_'),'saved existing FTE call',60000);await call('DebugFastRead');await delay(800);
  if(process.argv.includes('--rei-only')){const entry=await stats();assert.equal(entry.world.space,'garden_rest_area');assert.equal(entry.world.yaw,50);}
  await probe.capture('fte-entry.png');
  const observed=new Map(),chosen=[],listenerChecks=[];let saved=false,returned=false;const started=Date.now();await key('Control','keyDown');
  const checkListener=async(s,id)=>{
   assert(s.portrait.endsWith('/'+(prefix==='45'?'rei':'yuu')+'.webp'),s.portrait);
   const box=await probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="Portrait"]'),r=e.getBoundingClientRect(),s=getComputedStyle(e);return {display:s.display,visibility:s.visibility,opacity:s.opacity,rect:[r.x,r.y,r.width,r.height]};})()`);
   assert.notEqual(box.display,'none');assert.notEqual(box.visibility,'hidden');assert(Number(box.opacity)>0);assert(box.rect[3]>900);
   listenerChecks.push({id,portrait:s.portrait,box});
  };
  while(Date.now()-started<150000){
   const s=await stats(),n=graph.nodes[s.node];assert(n,s.node);
   if(n.id===caller.returnTo||n.source&&!n.source.file.startsWith(prefix+'_')){await key('Control','keyUp');assert.equal(n.id,returnedSay);returned=true;break;}
   if(n.type==='say'){
    const d=JSON.parse((await call('DialogueStats')).outputs.result);
    if(d.raw===n.text){observed.set(n.id,{line:n.source?.line,text:d.raw,speaker:d.speaker});if(targets.has(n.id))seen.add(n.id);
     if(listeners&&n.actor==='mio'&&!n.mono&&!listenerChecks.some(x=>x.id===n.id)){assert.equal(d.speaker,'미오');await checkListener(s,n.id);}
    }
   }
   if(n.type==='menu'&&s.choice.pending<0){
    await key('Control','keyUp');
    if(listeners)await checkListener(await stats(),n.id);
    const option=(n.id.includes('02-A')?'A':'B')+route,target=n.options.findIndex(o=>o.id===option);assert(target>=0,n.id+' '+option);
    if(prefix==='45'&&route===2&&n.id.includes('02-B')){
     await tap('Tab');for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x:1047,y:480,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}
     await padSystemAction(stats,tap,'save');const disk=JSON.parse(await fs.readFile(path.join(folder,'UserData/savegames.json'),'utf8')),actual=JSON.parse(disk.items[headKey]);
     assert.equal(actual.node,n.id);assert.equal(actual.flags['F-RE02-A'],'A2');assert(!actual.flags['fte:45:complete']);assert(!Object.hasOwn(actual.flags,'F-RE02-B'));
     if(process.argv.includes('--rei-only'))assert.equal(actual.world.garden_rest_area[3],50);
     await fs.copyFile(path.join(folder,'UserData/savegames.json'),path.join(folder,'actual-manual-savegames.json'));
     await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');await probe.until(async()=>(await stats()).node===n.id,'same actual unfinished FTE Continue',60000);
     if(process.argv.includes('--rei-only'))assert.equal((await stats()).world.yaw,50);
     if(listeners)await checkListener(await stats(),n.id+':after-actual-Continue');
     saved=true;
    }
    for(let i=0;i<4&&(await stats()).choice.hover!==target;i++)await tap('s');assert.equal((await stats()).choice.hover,target);
    await probe.capture('choice-'+chosen.length+'.png');await tap('Enter');await probe.until(async()=>(await stats()).node!==n.id,'actual selected FTE option',10000);chosen.push(option);await key('Control','keyDown');
   }
   await delay(15);
  }
  assert(returned);assert.deepEqual(chosen,['A'+route,'B'+route]);
  // Native flags are reported separately from the authored onReturnSet contract.
  assert.deepEqual(probe.errors,[]);await probe.capture('returned-existing-body.png');
  if(listeners)assert(listenerChecks.length>2);
  const result={ok:true,prefix,route,chosen,actualManualSaveContinue:saved,observedSay:[...observed.entries()],listenerChecks,returnNode:last.node,wallSeconds:(Date.now()-started)/1000};runs.push(result);await fs.writeFile(path.join(folder,'report.json'),JSON.stringify(result,null,2));
 }catch(error){await fs.writeFile(path.join(folder,'failure.json'),JSON.stringify({error:error.stack,last,runs,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}
 finally{await probe?.stop?.();}
}
const missing=[...targets].filter(([id,n])=>prefixes.includes(n.source.file.split('_')[0])&&!seen.has(id)).map(([id])=>id);assert.deepEqual(missing,[],'every changed selected line must actually display');
await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,fixture:true,normalRoute:false,executable,runs,observedRevisedSay:seen.size,scope:'Existing two FTE calls, three actual choice pairs each; seeded previous choices, exact existing return, Rei A2 before B2 actual Save/Continue. Fast input, not whole campaign, all history combinations or duration proof.'},null,2));
console.log(JSON.stringify({ok:true,work,runs:runs.length,observedRevisedSay:seen.size}));
