// A reachable authored choice before discovery, then ordinary input only.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {beginOwnedMovie} from './native-window-recording.mjs';
import {caseSaveCatalogue,publishCaseSave} from './native-case-saves.mjs';
const root=path.resolve(import.meta.dirname,'..'),output=path.join(root,'Saved/native-panic-views-1793690486425/package');
const work=path.join(root,'Saved/complete-discovery-movie-'+Date.now());await fs.mkdir(work,{recursive:true});
const read=async file=>JSON.parse(await fs.readFile(file,'utf8')),manifest=await read(path.join(output,'game.hbpack.json'));
const investigation=process.argv.includes('--investigation');
const catalogue=await caseSaveCatalogue(),entry=investigation?'v4:11b:I-C01':'v4:11a3:1-C04:menu';
const rows=(await fs.readFile(path.join(catalogue.fixtureRoot,'menu-fixtures.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
const branch=rows.find(r=>r.node===entry&&r.option===0);assert(branch?.state);
const graph=await read(path.join(root,'../data/v4_story/chapters/1.json'));
const report={work,fixture:true,accepted:false,events:[],movies:[],scope:investigation?'Reachable authored investigation choice, physical world inspection and normal authored return; existing evidence may be revised without increasing inventory. Not all investigation branches.':'Continuous actual input from the reachable pre-discovery choice through discovery and initial evidence grant. Not full campaign or all investigation branches.'};
process.env.YUMENO_NATIVE_QA_RECORD='1';let p,recording;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
try{
 p=await nativeWindowProbe({source:output,prepared:{output,manifest,executable:path.join(output,manifest.windowsApplication.executable)},work,maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(1280,720);
 report.precondition=await publishCaseSave({work,session:work,catalogue,branch});await p.tap('s');await p.tap('w');
 recording=await beginOwnedMovie(p,'discovery-1',{seconds:300});await p.tap('c');
 await p.until(async()=>(await p.stats()).node===entry,'actual pre-discovery choice',120000);
 const start=Date.now();let lastNode='',lastInput=0,initialCards=(await p.stats()).cards,body=investigation,acquired=false,hubAfter=false;
 while(Date.now()-start<1200000){
  const s=await p.stats();assert(!s.error,s.error);assert(!s.routeBlocked,'Blocked authored route');assert(!s.taskId,'Do not silently enter a trial task');
  if(s.node!==lastNode){lastNode=s.node;const node=graph.nodes[s.node];report.events.push({ms:Date.now()-start,node:s.node,kind:s.v4Kind,mode:s.mode,cards:s.cards,space:s.world?.space});
   if(node?.presentation?.actions?.includes('body_reveal')){body=true;report.bodyReveal={node:s.node,ms:Date.now()-start};await p.capture('body-reveal');}
  }
  // A stage node may run before the next observable line; the adjacent authored
  // discovery range remains the same real route, never a jumped outcome.
  if(s.node?.startsWith('v4:11a3:1-33:'))body=true;
  if(investigation&&!report.investigationEntry&&s.v4Kind==='investigate'&&!s.scenes?.loading){report.investigationEntry={node:s.node,cards:s.cards};initialCards=s.cards;await p.capture('investigation-entry');}
  if(body&&s.cards>initialCards&&(!investigation||report.physicalInspection)){acquired=true;if(!report.acquired){report.acquired={ms:Date.now()-start,node:s.node,cardsBefore:initialCards,cardsAfter:s.cards};await p.capture('acquired');}}
  if(investigation&&report.physicalInspection&&s.v4Kind==='investigate'&&s.node!==report.physicalInspection.node){acquired=true;report.revisedInspectionReturned={node:s.node,cards:s.cards,scope:'The authored physical revisit returned normally; existing evidence revisions do not increase inventory count.'};}
  if(acquired&&s.v4Kind==='investigate'&&!s.scenes?.loading){hubAfter=true;await p.capture('investigation-return');await delay(2500);break;}
  if(recording&&Date.now()-recording.started>260000){const held=s.node;report.movies.push(await recording.finish());recording=await beginOwnedMovie(p,'discovery-'+(report.movies.length+1),{seconds:300});assert.equal((await p.stats()).node,held,'No narrative input across movie rotation');}
  if(s.scenes?.loading){await delay(40);continue;}
  if(investigation&&s.v4Kind==='investigate'&&s.mode==='explore'){
   const target=graph.nodes[s.node]?.spots?.find(t=>t.space_id===s.world?.space&&Array.isArray(t.world_pos));assert(target,'Use a source-bound physical target, never a fabricated marker');
   const [x,y,z]=s.world.position,[tx,ty,tz]=target.world_pos,dx=tx-x,dz=tz-z,distance=Math.hypot(dx,dz),yaw=Math.atan2(-dx,-dz)*180/Math.PI,diff=((yaw-s.world.yaw+540)%360)-180,pitch=Math.atan2(ty-y,Math.max(.1,distance))*180/Math.PI;
   if(Math.abs(diff)>3){await p.tap(diff>0?'ArrowRight':'ArrowLeft',6);continue;}
   if(s.world.control==='free_walk'&&distance>4.2){await p.tap('w',6);continue;}
   if(Math.abs(pitch-s.world.pitch)>3){await p.tap(pitch>s.world.pitch?'ArrowUp':'ArrowDown',6);continue;}
   await p.move(640,360);await p.capture('physical-target');await delay(2200);await p.click(640,360);report.physicalInspection={node:s.node,space:s.world.space,target:target.target_id,method:'Actual look/move and centre-ray click on the authored world target; no map-list selection'};continue;
  }
  const a=s.auto||{};const readable=(a.kind==='key'&&a.key==='Enter')||s.mode==='menu';
  if(readable&&Date.now()-lastInput<2200){await delay(30);continue;}
  if(a.kind==='key'){await p.tap(a.key,6);lastInput=Date.now();}
  else if(a.kind==='click'){await p.click(a.x,a.y);lastInput=Date.now();}
  else if(a.kind==='wait')await delay(30);
  else throw Error('Unhandled authored action '+JSON.stringify(a));
 }
 assert(body&&acquired&&hubAfter,'Recording must include discovery, actual evidence acquisition and investigation return');
 report.movies.push(await recording.finish());recording=null;await p.close();p=null;report.sequenceCompleted=true;
}catch(error){report.error=error.stack;report.last=await p?.stats().catch(()=>null);if(recording){report.partialMovie=await recording.finish().catch(e=>({error:e.message}));recording=null;}process.exitCode=1;}
finally{await p?.close().catch(()=>{});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,sequenceCompleted:report.sequenceCompleted,error:report.error?.split('\n')[0]}));}
