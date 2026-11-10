// Isolated existing aftermath: actual choices and words, no campaign/duration claim.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const office=process.argv.includes('--office'),chapter=office?'1':'2',prefix=office?'91_':'155_';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/v4-'+(office?'office':'tin')+'-editorial-'+Date.now());
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const graph=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/chapters/'+chapter+'.json'),'utf8'));
const entry=office?'v4:91:P-C02:callback':Object.values(graph.nodes).find(n=>n.source?.file.startsWith(prefix)&&n.source.line===9).id;
const source=JSON.parse(await fs.readFile(path.join(root,'Saved/editorial-fixtures-20261101/chapter-'+chapter+'.json'),'utf8'));
const keys={c:[67,'KeyC'],Control:[17,'ControlLeft'],Enter:[13,'Enter'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],Tab:[9,'Tab'],Backspace:[8,'Backspace']};
const delay=ms=>new Promise(r=>setTimeout(r,ms)),runs=[];
for(const [route,remembered] of office?[['A',true],['B',false]]:[['A',false],['B',true],['C',false]]){
 const folder=path.join(work,route);await fs.mkdir(path.join(folder,'UserData'),{recursive:true});
 const seeded=structuredClone(source),headKey=Object.keys(seeded.items).find(k=>k.includes('yumeno-progress-v4.project.')),head=JSON.parse(seeded.items[headKey]);
 head.node=entry;head.snapshot='2026110111-'+route.charCodeAt(0);head.court.active=false;head.court.dead=['kaede','taiga','ai','yuu'];head.presentation={};head.worldId='kitchen';head.flags['fte:25:complete']=remembered;head.flags['2-C06']='A';delete head.flags['R2-C01'];
 if(office){head.court.dead=[];head.flags['P-C02']=route;delete head.flags['2-C06'];delete head.flags['fte:25:complete'];head.worldId='hotel_lobby';}
 seeded.items[headKey]=JSON.stringify(head);await fs.writeFile(path.join(folder,'UserData/savegames.json'),JSON.stringify(seeded));
 let probe,last;
 try{
  probe=await editorWindowProbe({work:folder,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
  const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
  const stats=async()=>{last=JSON.parse((await call('Stats')).outputs.result);assert(!last.error&&!last.routeBlocked,JSON.stringify(last));return last;};
  const key=async(k,type)=>{const[windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
  const sample=async()=>{const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(60);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=f+2,'input sampled',10000);};
  const tap=async k=>{await key(k,'keyDown');await sample();await key(k,'keyUp');await sample();};
  await tap('c');await probe.until(async()=>{const s=await stats();return office?graph.nodes[s.node]?.source?.file.startsWith(prefix):s.node===entry;},'existing source-bound saved entry',60000);await call('DebugFastRead');
  const observed=new Map();let chosen=office,saved=false,returned=false;const started=Date.now();await key('Control','keyDown');
  while(Date.now()-started<150000){
   const s=await stats(),n=graph.nodes[s.node];assert(n,s.node);
   if(n.source&&!n.source.file.startsWith(prefix)){await key('Control','keyUp');returned=true;break;}
   if(n.source?.file.startsWith(prefix)){
    if(n.type==='say'){const d=JSON.parse((await call('DialogueStats')).outputs.result);if(d.raw===n.text)observed.set(n.source.line,{id:n.id,text:d.raw,speaker:d.speaker});}
    if(!office&&n.type==='menu'&&s.choice.pending<0){
     await key('Control','keyUp');assert(n.id.endsWith('R2-C01'));
     if(route==='B'){
      await tap('Tab');for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x:1047,y:480,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}
      await padSystemAction(stats,tap,'save');const disk=JSON.parse(await fs.readFile(path.join(folder,'UserData/savegames.json'),'utf8')),actual=JSON.parse(disk.items[headKey]);assert.equal(actual.node,n.id);assert.equal(actual.flags['fte:25:complete'],true);assert(!Object.hasOwn(actual.flags,'R2-C01'));
      await fs.copyFile(path.join(folder,'UserData/savegames.json'),path.join(folder,'actual-manual-savegames.json'));await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');await probe.until(async()=>(await stats()).node===n.id,'same unselected actual menu Continue',60000);saved=true;
     }
     const target=n.options.findIndex(o=>o.id===route);assert(target>=0);for(let i=0;i<4&&(await stats()).choice.hover!==target;i++)await tap('s');assert.equal((await stats()).choice.hover,target);await probe.capture('choice.png');await tap('Enter');await probe.until(async()=>(await stats()).node!==n.id,'actual selected aftermath outcome',10000);chosen=true;await key('Control','keyDown');
    }
   }
   await delay(20);
  }
  assert(chosen&&returned);const lines=[...observed.keys()];
  if(office){assert(lines.some(n=>n>=(remembered?11:27)&&n<=(remembered?23:39)));assert(!lines.some(n=>n>=(remembered?27:11)&&n<=(remembered?39:23)));assert(lines.includes(299)&&lines.includes(319));}
  else{assert(lines.some(n=>n>=(remembered?19:41)&&n<=(remembered?35:49)),'selected history must actually display');assert(!lines.some(n=>n>=(remembered?41:19)&&n<=(remembered?49:35)),'private recalled history must not leak');
   for(const [option,lo,hi,echo]of [['A',145,167,241],['B',171,199,245],['C',203,227,249]]){assert.equal(lines.some(n=>n>=lo&&n<=hi),option===route);assert.equal(lines.includes(echo),option===route);}}
  assert.deepEqual(probe.errors,[]);await probe.capture('returned-existing-body.png');
  const result={ok:true,route,remembered,actualManualSaveContinue:saved,observedSay:[...observed.entries()],returnedNode:last.node,wallSeconds:(Date.now()-started)/1000};runs.push(result);await fs.writeFile(path.join(folder,'report.json'),JSON.stringify(result,null,2));
 }catch(error){await fs.writeFile(path.join(folder,'failure.json'),JSON.stringify({error:error.stack,last,runs,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}
 finally{await probe?.stop?.();}
}
await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,fixture:true,normalRoute:false,executable,runs,scope:office?'First-day phone revisit from both explicitly seeded prior dinner choices; actual current utterances and return. No prologue replay, no new native menu or real call/printout. Fast QA input, not playtime proof.':'Three selected aftermath outcomes and both recalled-history conditions; B actual manual Save/Continue before choosing. Fast QA input, isolated seeded saves, not whole campaign or playtime proof.'},null,2));console.log(JSON.stringify({ok:true,work,routes:runs.map(r=>r.route)}));
