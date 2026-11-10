import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {v4Bucket} from './v4-data.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),output=path.join(root,'Saved/native-panic-views-1793690486425/package'),work=path.join(root,'Saved/native-armament-complete-'+Date.now());await fs.mkdir(work,{recursive:true});
const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));
async function put(relative,source,kind){
 const file=path.resolve(output,relative);assert(file.startsWith(output+path.sep));await fs.mkdir(path.dirname(file),{recursive:true});await fs.unlink(file).catch(e=>{if(e.code!=='ENOENT')throw e;});await fs.copyFile(source,file);
 const bytes=await fs.readFile(file),row=manifest.files.find(r=>r.path===relative)||{path:relative};if(!manifest.files.includes(row))manifest.files.push(row);Object.assign(row,{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
 if(kind){const asset=relative.slice(8);if(!manifest.entries.some(e=>e.path===asset))manifest.entries.push({path:asset,name:path.basename(asset),kind});}
}
const moduleArg=process.argv.find(v=>v.startsWith('--game-module='))?.slice(14);
await put(manifest.nativeModules[0].binary,path.resolve(root,moduleArg||'Saved/game-trial-work-20261102/game-trial-comic-hints-20261103.exe'));
await put('Content/Assets/UI/Stage.hbwidget.json',path.join(root,'Assets/UI/Stage.hbwidget.json'));
await put('Content/Assets/Data/armament_text_v4.json',path.join(root,'Assets/Data/armament_text_v4.json'),'data');
for(const name of await fs.readdir(path.join(root,'Assets/Art/ui/armament_ink')))await put('Content/Assets/Art/ui/armament_ink/'+name,path.join(root,'Assets/Art/ui/armament_ink',name),'texture');
await put('Content/Assets/Scenes/ArmamentHud.hbscene.json',path.join(root,'Assets/Scenes/ArmamentHud.hbscene.json'),'scene');
// The reused QA host predates newer camera output fields. Preserve its exact
// already-valid single camera contract; current product scene remains intact.
{
 const name='Content/Assets/Scenes/ArmamentHud.hbscene.json',file=path.join(output,name),scene=JSON.parse(await fs.readFile(file,'utf8'));
 const court=JSON.parse(await fs.readFile(path.join(output,'Content/Assets/Scenes/Court.hbscene.json'),'utf8'));
 scene.objects.find(o=>o.id==='Camera').components=structuredClone(court.objects.find(o=>o.id==='Camera').components);
 const bytes=Buffer.from(JSON.stringify(scene));await fs.writeFile(file+'.qa.tmp',bytes);await fs.rename(file+'.qa.tmp',file);Object.assign(manifest.files.find(r=>r.path===name),{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
}
await put('Content/Assets/Data/armament_figures_v4.json',path.join(root,'Assets/Data/armament_figures_v4.json'),'data');
for(const name of await fs.readdir(path.join(root,'Assets/Art/armament_v4')))await put('Content/Assets/Art/armament_v4/'+name,path.join(root,'Assets/Art/armament_v4',name),name.endsWith('.glb')?'model':'texture');
// Reused QA content predates the parallel manuscript revision. Bind the exact
// current authored claims to the generated ink; leave route/answers/rhythm intact.
{
 const bucket=v4Bucket('T4-AA-01',64),name=`Content/Assets/Data/v4_story/native_tasks/pack_${bucket%32}.json`,file=path.join(output,name),packet=JSON.parse(await fs.readFile(file,'utf8'));
 const tasks=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8'));packet.buckets[bucket].tasks['T4-AA-01'].stage.lines=tasks.tasks['T4-AA-01'].stage.lines;
 const bytes=Buffer.from(JSON.stringify(packet));await fs.writeFile(file+'.ink.tmp',bytes);await fs.rename(file+'.ink.tmp',file);Object.assign(manifest.files.find(r=>r.path===name),{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
}
await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));
const checkpoint=JSON.parse(await fs.readFile(path.join(root,'Saved/native-task-checkpoints.json'),'utf8')).armament;
const report={work,task:checkpoint.task,shipping:false,phases:[],wrongFinal:false};let p;
try{
 p=await nativeWindowProbe({source:output,prepared:{output,manifest,executable:path.join(output,manifest.windowsApplication.executable)},work,resume:path.resolve(repo,checkpoint.file),maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(1920,1080);await p.tap('c');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.taskId===checkpoint.task;},'nearest saved armament',120000);
 for(let i=0;i<80&&(await p.stats()).taskQueue;i++)await p.tap('Enter');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return !s.taskQueue&&s.taskInputArmed&&!s.scenes.loading;},'armament input');await p.sampled(12);await p.capture('entrance');
 const first=await p.stats();report.before=first;
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.armamentV4?.hp<first.armamentV4.hp?s:false;},'unattended miss loses actual HP',30000);report.miss=await p.stats();await p.capture('miss');
 let held=null,wrongStarted=false,wrongHp=0;const started=Date.now();
 while(Date.now()-started<300000){
  const s=await p.stats();assert(!s.error,s.error);
  if(s.taskId!==checkpoint.task||s.taskQueue&&s.taskQueueAfter==='success'){report.after=s;break;}
  const arm=s.armamentV4;if(!arm){await p.sampled(2);continue;}
  const phase=arm.opponent>first.armamentV4.opponent*.66?0:arm.opponent>first.armamentV4.opponent*.33?1:2;
  if(!s.taskQueue&&!report.phases.includes(phase)){report.phases.push(phase);await p.capture('armor-'+phase);}
  if(s.taskQueue){if(held){await p.key(held,false);held=null;}await p.tap('Enter');continue;}
  if(arm.final>=0&&!report.wrongFinal){
   if(!wrongStarted){wrongStarted=true;wrongHp=arm.hp;await p.capture('final-first');const shot=JSON.parse(await fs.readFile(path.join(work,'final-first.ui.json'),'utf8'));const nodes=shot.widgets.find(w=>w.instance==='stage').nodes;report.finalInk=['ArmQuestion','ArmJoined','Piece0','Piece1','Piece2','Piece3'].map(id=>{const n=nodes.find(n=>n.id===id+'Ink'),t=nodes.find(n=>n.id===id);assert(n?.properties.visible&&!t?.properties.visible,'Outlined final ink '+id);assert(n.properties.texture,'Bound final ink '+id);return {id,texture:n.properties.texture,rect:n.slot.offset};});}
   if(arm.selected<4){const used=arm.order||[];let index=arm.layout.findIndex(v=>!used.includes(v)&&v!==arm.selected);if(index<0)index=arm.layout.findIndex(v=>!used.includes(v));await p.tap(String(index+1),1);}
   else await p.sampled(3);
   if((await p.stats()).armamentV4?.hp<wrongHp){report.wrongFinal=true;await p.capture('final-wrong');}continue;
  }
  const a=s.auto||{};
  if(a.kind==='release-after'){if(a.remaining<=.025){await p.key(a.key,false);held=null;}else await p.sampled(1);}
  else if(a.kind==='hold-key'){await p.key(a.key,true);held=a.key;await p.sampled(1);}
  else if(a.kind==='key'||a.kind==='rapid-key')await p.tap(a.key,1);
  else if(a.kind==='click')await p.click(a.x,a.y);
  else await p.sampled(1);
 }
 assert(report.after,'Full rhythm/final/success queue must complete');assert(report.wrongFinal,'Wrong final combination must cause actual damage');assert.deepEqual(report.phases,[0,1,2]);
 await p.capture('success');
 for(let i=0;i<120;i++){const s=await p.stats();assert(!s.error,s.error);if(s.taskId!==checkpoint.task){report.return=s;break;}if(s.taskQueue||s.auto?.key==='Enter')await p.tap('Enter');else await p.sampled(3);}
 assert(report.return,'Authored success dialogue must leave the completed task');await p.until(async()=>!(await p.stats()).scenes.loading,'return scene loaded');await p.sampled(12);await p.capture('return');
 report.runtime=await p.close();p=null;report.ok=true;
}catch(error){report.error=error.stack;report.last=await p?.stats().catch(()=>null);await p?.capture('failure').catch(()=>{});process.exitCode=1;}
finally{await p?.close().catch(()=>{});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,ok:report.ok,error:report.error?.split('\n')[0]}));}
