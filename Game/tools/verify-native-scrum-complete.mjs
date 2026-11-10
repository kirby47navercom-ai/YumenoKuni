import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {emitV4ScrumUI} from './v4-scrum-ui.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),output=path.join(root,'Saved/native-panic-views-1793690486425/package'),work=path.join(root,'Saved/native-scrum-complete-'+Date.now());await fs.mkdir(work,{recursive:true});
const write=async(relative,value)=>{const target=path.join(root,relative);await fs.mkdir(path.dirname(target),{recursive:true});const tmp=target+'.scrum.tmp';await fs.writeFile(tmp,typeof value==='string'||Buffer.isBuffer(value)?value:JSON.stringify(value));await fs.rename(tmp,target);};
await emitV4ScrumUI({write,body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',head:'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'});
const taskPackets=[];for(const name of await fs.readdir(path.join(root,'Assets/Data/v4_story/native_tasks'))){if((await fs.readFile(path.join(root,'Assets/Data/v4_story/native_tasks',name),'utf8')).includes('T4-SD-01'))taskPackets.push('Data/v4_story/native_tasks/'+name);}
const changed=['UI/ScrumV4.hbwidget.json','Data/scrum_text_v4.json',...['left','right','statement','push'].map(n=>'Art/ui/scrum_'+n+'.svg'),...(await fs.readdir(path.join(root,'Assets/Art/ui/scrum_ink'))).map(n=>'Art/ui/scrum_ink/'+n),...taskPackets];
// Merge only profile metadata into this retained QA package, not old story/world.
const courtFile=path.join(output,'Content/Assets/Data/court.json'),court=JSON.parse(await fs.readFile(courtFile,'utf8')),currentCourt=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/court.json'),'utf8'));
court.scrumFaces=currentCourt.scrumFaces||{};
for(const key of Object.keys(court.scrumFaces)){court.figures[key]=currentCourt.figures[key];changed.push(court.figures[key].texture.slice(7),court.scrumFaces[key].slice(7));}
await fs.writeFile(courtFile+'.profiles.tmp',JSON.stringify(court));await fs.rename(courtFile+'.profiles.tmp',courtFile);
for(const relative of changed){
 const target=path.join(output,'Content/Assets',relative);assert(path.resolve(target).startsWith(output+path.sep));await fs.mkdir(path.dirname(target),{recursive:true});await fs.unlink(target).catch(e=>{if(e.code!=='ENOENT')throw e;});await fs.copyFile(path.join(root,'Assets',relative),target);
}
const {createHash}=await import('node:crypto');
const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));
{const bytes=await fs.readFile(courtFile),row=manifest.files.find(r=>r.path==='Content/Assets/Data/court.json');assert(row);Object.assign(row,{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});}
for(const relative of changed){
 const name='Content/Assets/'+relative,b=await fs.readFile(path.join(output,name));
 const row=manifest.files.find(v=>v.path===name)||{path:name};if(!manifest.files.includes(row))manifest.files.push(row);
 row.bytes=b.length;row.sha256=createHash('sha256').update(b).digest('hex');
 const asset='Assets/'+relative;if(!manifest.entries.some(e=>e.path===asset))manifest.entries.push({path:asset,name:path.basename(asset),kind:relative.startsWith('Data/')?'data':relative.startsWith('Art/')?'texture':'widget'});
}
const moduleTarget=path.join(output,manifest.nativeModules[0].binary);await fs.unlink(moduleTarget);
const moduleArg=process.argv.find(v=>v.startsWith('--game-module='))?.slice(14);
await fs.copyFile(path.resolve(root,moduleArg||'Saved/game-trial-work-20261102/game-trial-cutin-eyes-20261104.exe'),moduleTarget);
const moduleBytes=await fs.readFile(moduleTarget),moduleRow=manifest.files.find(r=>r.path===manifest.nativeModules[0].binary);
moduleRow.bytes=moduleBytes.length;moduleRow.sha256=createHash('sha256').update(moduleBytes).digest('hex');
await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));
const prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)};
const c=JSON.parse(await fs.readFile(path.join(root,'Saved/native-task-checkpoints.json'),'utf8')).scrum;
const spec=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks[c.task].stage;
let p;const report={work,task:c.task,pairs:[],pushDirections:[],shipping:false};
try{
 p=await nativeWindowProbe({source:output,prepared,work,resume:path.resolve(repo,c.file),maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(1920,1080);await p.tap('c');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.taskId===c.task;},'exact scrum checkpoint',120000);
 for(let i=0;i<80&&(await p.stats()).taskQueue;i++)await p.tap('Enter');
 await p.capture('entrance');
 const started=Date.now();let first=true,seenPush=false;
 while(Date.now()-started<240000){
  const s=await p.stats();assert(!s.error,s.error);
  if(s.taskId!==c.task||s.taskQueue&&s.taskQueueAfter==='success'){report.after=s;break;}
  const scrum=s.scrumV4;
  if(scrum?.entry>=1&&scrum.mash<0&&!s.taskQueue){
   if(scrum.pair<spec.pairs.length&&!report.pairs.includes(scrum.pair)){report.pairs.push(scrum.pair);if(first){first=false;await p.capture('matching');}else await p.capture('matching-'+scrum.pair);}
  }
  if(scrum?.mash>=0){seenPush=true;if(!report.pushDirections.includes(scrum.phase)){report.pushDirections.push(scrum.phase);if(report.pushDirections.length===1){await p.sampled(3);await p.capture('final-push');}}}
  const a=s.auto||{};
  if(s.taskQueue){await p.tap('Enter');continue;}
  if(scrum?.entry<1){await p.sampled(8);continue;}
  if(a.kind==='key'||a.kind==='rapid-key'){await p.tap(a.key,1);continue;}
  if(a.kind==='click'){await p.click(a.x,a.y);continue;}
  await p.sampled(2);
 }
 assert(report.after,'Complete the authored task, not just its entrance');assert(seenPush,'Final directional struggle must actually be played');assert.equal(report.pairs.length,spec.pairs.length,'All matching rounds must be played');assert(report.pushDirections.length>1,'Final struggle must include changing directional prompts');
 report.runtime=await p.close();p=null;report.ok=true;
}catch(error){report.error=error.stack;report.last=await p?.stats().catch(()=>null);await p?.capture('failure').catch(()=>{});throw error;}
finally{await p?.close().catch(()=>{});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,ok:report.ok,pairs:report.pairs,pushDirections:report.pushDirections,error:report.error?.split('\n')[0]}));}
