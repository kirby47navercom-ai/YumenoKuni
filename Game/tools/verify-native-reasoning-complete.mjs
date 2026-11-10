import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),output=path.join(root,'Saved/native-panic-views-1793690486425/package');
const work=path.join(root,'Saved/native-reasoning-complete-'+Date.now());await fs.mkdir(work,{recursive:true});
const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));
const copy=async(name,from)=>{const file=path.join(output,name),bytes=await fs.readFile(from);await fs.mkdir(path.dirname(file),{recursive:true});const temp=file+'.reasoning.tmp';await fs.writeFile(temp,bytes);await fs.rename(temp,file);let row=manifest.files.find(r=>r.path===name);if(!row){row={path:name};manifest.files.push(row);}row.bytes=bytes.length;row.sha256=createHash('sha256').update(bytes).digest('hex');if(name.startsWith('Content/')){const asset=name.slice(8);if(!manifest.entries.some(e=>e.path===asset))manifest.entries.push({path:asset,name:path.basename(asset),kind:asset.endsWith('.hbwidget.json')?'widget':'texture'});}};
await copy(manifest.nativeModules[0].binary,path.join(root,'Saved/game-trial-work-20261102/game-trial-reasoning-20261103.exe'));
for(const file of ['UI/Stage.hbwidget.json','Art/ui/reasoning_back.svg','Art/ui/reasoning_card.svg',...[0,1,2].map(i=>'Art/ui/reasoning_branch_'+i+'.svg')])await copy('Content/Assets/'+file,path.join(root,'Assets',file));
await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));
const prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)};
const checkpoint=JSON.parse(await fs.readFile(path.join(root,'Saved/native-task-checkpoints.json'),'utf8')).reasoning;
const spec=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks[checkpoint.task].stage;
const report={work,task:checkpoint.task,shipping:false,links:[],wrongVerified:false};let p;
const view=async name=>{await p.capture(name);return JSON.parse(await fs.readFile(path.join(work,name+'.ui.json'),'utf8')).widgets.find(w=>w.instance==='stage');};
try{
 p=await nativeWindowProbe({source:output,prepared,work,resume:path.resolve(repo,checkpoint.file),maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(1920,1080);await p.tap('c');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.taskId===checkpoint.task;},'exact reasoning checkpoint',120000);
 for(let i=0;i<80&&(await p.stats()).taskQueue;i++)await p.tap('Enter');
 const initial=await view('entrance');const props=(w,id)=>w.nodes.find(n=>n.id===id)?.properties;
 assert.equal(props(initial,'Hourglass').visible,false);assert.equal(props(initial,'ReasoningBack').visible,true);
 assert.equal(props(initial,'ReasoningPast0').visible,false,'No future correct answer in the history');
 const entry=await p.stats(),wrong=(spec.questions[0].options.indexOf(spec.questions[0].answer)+1)%3;
 await p.click(900,228+wrong*110);await p.sampled(4);
 const damaged=await p.stats();assert.equal(damaged.taskLink,0);assert(damaged.trialHp<entry.trialHp);report.wrongVerified=true;await view('wrong');
 const started=Date.now();let shownHistory=false;
 while(Date.now()-started<180000){
  const s=await p.stats();assert(!s.error,s.error);
  if(s.taskId!==checkpoint.task){report.after=s;break;}
  if(s.taskLink>0&&!report.links.includes(s.taskLink))report.links.push(s.taskLink);
  if(s.taskQueue){await p.tap('Enter');continue;}
  if(s.taskLink>0&&!shownHistory){const v=await view('connected');assert.equal(props(v,'ReasoningPast0').visible,true);assert.equal(props(v,'ReasoningPast0').text.replace(/\s+/g,''),spec.questions[0].answer.replace(/\s+/g,''));await p.resize(3840,2160);await view('connected-4k');shownHistory=true;}
  if(s.auto?.kind==='click')await p.click(s.auto.x,s.auto.y);else if(s.auto?.kind==='key')await p.tap(s.auto.key);else await p.sampled(3);
 }
 assert(report.after,'Must finish all links and reach the authored return');assert(shownHistory);report.historyVerified=true;
 report.runtime=await p.close();p=null;report.ok=true;
}catch(error){report.error=error.stack;report.last=await p?.stats().catch(()=>null);await p?.capture('failure').catch(()=>{});process.exitCode=1;}
finally{await p?.close().catch(()=>{});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,ok:report.ok,links:report.links,error:report.error?.split('\n')[0]}));}
