// Only explicitly reviewed scene/time repairs; isolated prior-context fixtures.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const morning=process.argv.includes('--morning'),chapter=morning?'3':'1';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/v4-editorial-'+(morning?'morning':'scenes')+'-'+Date.now());
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const graph=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/chapters/'+chapter+'.json'),'utf8'));
const original=JSON.parse(await fs.readFile(path.join(root,'Saved/editorial-fixtures-20261101/chapter-'+chapter+'.json'),'utf8'));
const cases=morning?[['136','3-03a','hotel_lobby',0],['13a2','3-17a','mirror_maze',0]]:[['11a','1-07k','clinic',1],['11a','1-05G','park_main_gate',0],['11a','1-04L1','plaza',0],['11a2','1-17-F-SA02','hotel_corridor',2],['65','1-07a','dining_room',2],['154','1-09a-01','hotel_lobby',0]];
const only=process.argv.find(a=>a.startsWith('--only='))?.slice(7),from=process.argv.find(a=>a.startsWith('--from='))?.slice(7),runs=[];
assert(!from||cases.some(c=>c[1]===from));
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const keys={c:[67,'KeyC'],Control:[17,'ControlLeft'],Enter:[13,'Enter'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],Tab:[9,'Tab'],Backspace:[8,'Backspace']};
for(const [prefix,location,space,skyPhase]of cases){
 if(only&&only!==location||from&&cases.findIndex(c=>c[1]===location)<cases.findIndex(c=>c[1]===from))continue;
 const folder=path.join(work,location);await fs.mkdir(path.join(folder,'UserData'),{recursive:true});
 const inside=n=>n?.source?.file.startsWith(prefix+'_')&&(prefix==='136'||n.source.location===location);
 const nodes=Object.values(graph.nodes).filter(inside).sort((a,b)=>a.source.line-b.source.line);
 assert(nodes.length);const entry=nodes[0].id,firstSay=nodes.find(n=>n.type==='say');assert(firstSay);
 const seed=structuredClone(original),headKey=Object.keys(seed.items).find(k=>k.includes('yumeno-progress-v4.project.')),head=JSON.parse(seed.items[headKey]);
 head.node=entry;head.snapshot='2026110113-'+cases.findIndex(c=>c[1]===location);head.court.active=false;if(!morning)head.court.dead=[];head.presentation={};head.world={};
 head.worldId=morning?space:space==='clinic'?'hotel_lobby':'clinic';head.playerProgress.skyPhase=morning?skyPhase:skyPhase===1?0:1;head.playerProgress.phase=morning?0:skyPhase===1?0:1;
 seed.items[headKey]=JSON.stringify(head);await fs.writeFile(path.join(folder,'UserData/savegames.json'),JSON.stringify(seed));
 let probe,last;
 try{
  probe=await editorWindowProbe({work:folder,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
  const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
  const stats=async()=>{last=JSON.parse((await call('Stats')).outputs.result);assert(!last.error&&!last.routeBlocked,JSON.stringify(last));return last;};
  const key=async(k,type)=>{const[windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
  const sample=async()=>{const frame=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(60);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=frame+2,'sampled input',10000);};
  const tap=async k=>{await key(k,'keyDown');await sample();await key(k,'keyUp');await sample();};
  await tap('c');await probe.until(async()=>(await stats()).node===firstSay.id,'exact first current utterance',60000);
  assert.equal(last.world.space,space);await delay(900);await probe.capture('scene-entry.png');
  const d=JSON.parse((await call('DialogueStats')).outputs.result);assert.equal(d.raw,firstSay.text);
  await tap('Tab');for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x:1047,y:480,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}
  await padSystemAction(stats,tap,'save');const disk=JSON.parse(await fs.readFile(path.join(folder,'UserData/savegames.json'),'utf8')),saved=JSON.parse(disk.items[headKey]);
  assert.equal(saved.node,firstSay.id);assert.equal(saved.worldId,space);assert.equal(saved.playerProgress.skyPhase,skyPhase);
  await fs.copyFile(path.join(folder,'UserData/savegames.json'),path.join(folder,'actual-manual-savegames.json'));
  let clinic;
  if(morning||location==='1-07k'){
   await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');await probe.until(async()=>(await stats()).node===firstSay.id,'same actual clinic Continue',60000);
   assert.equal(last.world.space,space);await call('DebugFastRead');const observed=new Map(),start=Date.now();
   while(Date.now()-start<120000){const s=await stats(),n=graph.nodes[s.node];assert(n,s.node);if(!inside(n))break;
    if(n.type==='say'){
     await probe.until(async()=>{const shown=JSON.parse((await call('DialogueStats')).outputs.result);return shown.raw===n.text&&shown.shown>=shown.length;},'current utterance/page fully displayed',30000);
     observed.set(n.source.line,{id:n.id,text:n.text});await tap('Enter');
    }else await delay(30);
   }
   assert(!inside(graph.nodes[last.node]));
   const revisions=JSON.parse(await fs.readFile(path.join(root,'../tools/v4_editorial_revisions.json'),'utf8')).revisions.filter(r=>r.prefix===prefix&&(prefix==='136'||r.location===location));
   for(const r of revisions){const n=nodes.find(n=>n.type==='say'&&n.text===r.after.split(']')[1].trim());assert(n,r.after);assert.equal(observed.get(n.source.line)?.text,n.text);}
   if(!morning){assert.equal(observed.get(1051)?.text,'저는 허락한 분께만 손대요.');assert(observed.has(1103));}
   await probe.capture('clinic-return.png');clinic={actualSaveContinue:true,observedSay:[...observed.entries()],revisedUtterances:revisions.length,returnedNode:last.node};
  }
  assert.deepEqual(probe.errors,[]);const result={ok:true,prefix,location,entryNode:entry,firstSay:firstSay.id,seededWorld:head.worldId,seededSky:head.playerProgress.skyPhase,world:space,savedSkyPhase:saved.playerProgress.skyPhase,clinic};
  runs.push(result);await fs.writeFile(path.join(folder,'report.json'),JSON.stringify(result,null,2));
 }catch(error){await fs.writeFile(path.join(folder,'failure.json'),JSON.stringify({error:error.stack,last,runs,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
}
await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,executable,fixture:true,normalRoute:false,runs,scope:morning?'Two chapter3 revised local conversations, every revised utterance individually displayed and real Save/Continue. Their original room/day is seeded, not a new scene binding proof. No full campaign or duration claim.':'Selected local scene/time entries from deliberately different saved room/time; actual menu saves prove runtime sky phase. Clinic current dialogue and real Save/Continue. No full campaign or duration claim.'},null,2));console.log(JSON.stringify({ok:true,work,cases:runs.length}));
