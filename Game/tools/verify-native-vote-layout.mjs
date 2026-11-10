import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {v4Bucket} from './v4-data.mjs';
const resultTest=process.argv.includes('--results');
const candidate=process.argv.find(x=>x.startsWith('--module='))?.slice(9);assert(!candidate||/^[a-z0-9-]+\.exe$/.test(candidate));
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),work=path.join(root,'Saved/native-vote-layout-'+Date.now());await fs.mkdir(work,{recursive:true});
const output=path.join(root,'Saved/native-panic-views-1793690486425/package');
assert(output.startsWith(path.join(root,'Saved/native-panic-views-')));
const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));
const writeOwned=async(relative,from)=>{const target=path.resolve(output,relative);assert(target.startsWith(output+path.sep));await fs.mkdir(path.dirname(target),{recursive:true});await fs.unlink(target).catch(e=>{if(e.code!=='ENOENT')throw e;});await fs.copyFile(from,target);};
await writeOwned(manifest.nativeModules[0].binary,path.join(root,'Saved/game-trial-work-20261102',candidate||'game-trial-vote-'+(resultTest?'results':'layout')+'-20261103.exe'));
for(const relative of ['UI/Vote.hbwidget.json',...(await fs.readdir(path.join(root,'Assets/Art/ui/vote_v4'))).map(n=>'Art/ui/vote_v4/'+n)])await writeOwned('Content/Assets/'+relative,path.join(root,'Assets',relative));
const {createHash}=await import('node:crypto');
if(resultTest){
 const stages=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks;
 for(const [id,task] of Object.entries(stages).filter(([,task])=>task.stage.kind==='vote')){
  const bucket=v4Bucket(id,64),relative=`Content/Assets/Data/v4_story/native_tasks/pack_${bucket%32}.json`,file=path.join(output,relative),packet=JSON.parse(await fs.readFile(file,'utf8'));assert(packet.buckets[bucket].tasks[id]);
  const current=JSON.parse(await fs.readFile(path.join(root,`Assets/Data/v4_story/native_tasks/pack_${bucket%32}.json`),'utf8'));assert(current.buckets[bucket].tasks[id]);
  packet.buckets[bucket].tasks[id].stage=current.buckets[bucket].tasks[id].stage;const bytes=Buffer.from(JSON.stringify(packet));await fs.writeFile(file+'.vote.tmp',bytes);await fs.rename(file+'.vote.tmp',file);
  const row=manifest.files.find(v=>v.path===relative);assert(row);Object.assign(row,{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
 }
}
for(const relative of ['UI/Vote.hbwidget.json',...(await fs.readdir(path.join(root,'Assets/Art/ui/vote_v4'))).map(n=>'Art/ui/vote_v4/'+n)]){
 const name='Content/Assets/'+relative,b=await fs.readFile(path.join(output,name)),row=manifest.files.find(v=>v.path===name)||{path:name};if(!manifest.files.includes(row))manifest.files.push(row);Object.assign(row,{bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')});
}
for(const row of manifest.files.filter(r=>r.path.startsWith('Content/Assets/Art/ui/vote_v4/'))){const asset=row.path.slice(8);if(!manifest.entries.some(v=>v.path===asset))manifest.entries.push({path:asset,name:path.basename(asset),kind:'texture'});}
const moduleBytes=await fs.readFile(path.join(output,manifest.nativeModules[0].binary));const moduleRow=manifest.files.find(v=>v.path===manifest.nativeModules[0].binary);Object.assign(moduleRow,{bytes:moduleBytes.length,sha256:createHash('sha256').update(moduleBytes).digest('hex')});
await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));
const prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)};
const c=JSON.parse(await fs.readFile(path.join(root,'Saved/native-task-checkpoints.json'),'utf8')).vote;
const task=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks[c.task].stage;
const answer=task.candidates.findIndex(v=>(typeof v==='string'?v:v.id)===task.answer);assert(answer>=0);
let p;const report={work,task:c.task,shipping:false,reference:'https://www.youtube.com/watch?v=gBNt-hmEBKA&t=51s'};
try{
 p=await nativeWindowProbe({source:output,prepared,work,resume:path.resolve(repo,c.file),maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(1920,1080);await p.tap('c');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.taskId===c.task;},'vote checkpoint',120000);
 for(let i=0;i<80&&(await p.stats()).taskQueue;i++)await p.tap('Enter');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.taskInputArmed&&!s.taskQueue;},'vote active',120000);await p.sampled(12);await p.capture('input');
 let ui=JSON.parse(await fs.readFile(path.join(work,'input.ui.json'),'utf8'));report.before=await p.stats();
 // Pixel placement is inspected from actual native output, rather than treating
 // an input smoke test as visual approval.
 report.uiNodes=ui.widgets;
 assert.equal(ui.widgets.find(w=>w.instance==='vote').nodes.find(n=>n.id==='VoteResultRows').properties.visible,false,'Result rows must not cover voting input');
 await p.click(278,212);await p.sampled(10);report.afterSelection=await p.stats();assert.equal(report.afterSelection.taskId,c.task,'Selecting a portrait must not submit a vote');
 await p.resize(3840,2160);await p.sampled(8);await p.capture('input-4k');await p.resize(1920,1080);
 for(let i=0;i<18&&(await p.stats()).stage.selection!==answer;i++){await p.tap('d');await p.sampled(4);}
 assert.equal((await p.stats()).stage.selection,answer);await p.tap('Enter');
 if(resultTest){
  await p.capture('counting');const start=Date.now();await p.until(async()=>Date.now()-start>=2600,'count animation',5000);await p.capture('result');
  const resultUI=JSON.parse(await fs.readFile(path.join(work,'result.ui.json'),'utf8')),vote=resultUI.widgets.find(w=>w.instance==='vote');assert(vote);
  const props=id=>vote.nodes.find(n=>n.id===id)?.properties;
  assert.equal(props('VoteTitle').text,'투표 결과');assert.equal(props('VoteName').visible,true);
  assert.equal(props('VoteResultRows').visible,true);assert.equal(props('VoteTitle').visible,false,'Final tally uses the portrait/name presentation, not an extra heading');
  assert.equal(props('VoteCommit').visible,false);assert.equal(props('VoteP0').visible,false);
  const expected=task;
  const counts=expected.voteCounts&&typeof expected.voteCounts==='object'?expected.voteCounts:expected.authoredResult;
  report.resultCounts=task.candidates.map((id,i)=>{const logical=typeof id==='string'?id:id.id,mark=props('VoteRB'+i),caption=props('VoteRC'+i);const n=Number(mark.texture.match(/count_(\d+)\.svg$/)?.[1]||0);assert.equal(mark.visible,!!counts&&Number(counts[logical]||0)>0);if(counts)assert.equal(n,Number(counts[logical]||0));else assert.equal(caption.text,logical===expected.answer?'다수표':'');const rect=vote.nodes.find(n=>n.id==='VoteRF'+i).slot.offset;assert.equal(rect[0],91+Math.floor(i/8)*306);assert.equal(rect[1],142+(i%8)*58);return [logical,counts?n:caption.text];});
  const physical=expected.candidateOverrides?.[expected.answer]?.physicalActor;
  if(physical){const court=JSON.parse(await fs.readFile(path.join(output,'Content/Assets/Data/court.json'),'utf8'));assert.equal(props('VotePortrait').texture,court.figures[physical].texture);report.physicalActorVerified=physical;}
 }
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.taskQueue||s.taskId!==c.task;},'vote result and authored return',120000);
 report.after=await p.stats();report.runtime=await p.close();p=null;report.ok=true;
}catch(error){report.error=error.stack;await p?.capture('failure').catch(()=>{});throw error;}
finally{await p?.close().catch(()=>{});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,ok:report.ok,error:report.error?.split('\n')[0]}));}
