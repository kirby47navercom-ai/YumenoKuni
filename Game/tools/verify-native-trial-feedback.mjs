import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),work=path.join(root,'Saved/native-trial-feedback-'+Date.now());
await fs.mkdir(work,{recursive:true});
const build=JSON.parse(await fs.readFile(path.join(root,'Saved/game-trial-work-20261102/current-flat-build-result.json'),'utf8'));
const module=path.join(root,'Saved/game-trial-work-20261102/game-trial-feedback-final-20261103.exe');
const overrides=path.join(root,'Saved/game-trial-work-20261102/trial-feedback-overrides.json');
const reuse=process.argv.find(a=>a.startsWith('--reuse-package='))?.slice(16);
if(reuse)assert(path.resolve(reuse).startsWith(path.join(root,'Saved/native-trial-feedback-')));
const prepared=reuse?{output:path.resolve(reuse),manifest:JSON.parse(await fs.readFile(path.join(reuse,'game.hbpack.json'),'utf8'))}:await createOwnedNativePackage({source:build.output,work,gameModuleCandidate:module,gameContentOverrides:overrides,stats:true});
prepared.executable??=path.join(prepared.output,prepared.manifest.windowsApplication.executable);
const cases=JSON.parse(await fs.readFile(path.join(root,'Saved/native-task-checkpoints.json'),'utf8'));
process.env.YUMENO_NATIVE_IMPACT_TRACE='1';process.env.YUMENO_NATIVE_QA_RECORD='1';
const rows=[];let p;
const read=async f=>JSON.parse(await fs.readFile(f,'utf8'));
try{
 for(const kind of ['choice','showdown','scrum','armament']){
  const c=cases[kind],dir=path.join(work,kind);p=await nativeWindowProbe({source:build.output,prepared,work:dir,resume:path.resolve(repo,c.file),maxFrames:null,heartbeatTimeoutMs:120000});
  await p.hiddenBorderless();await p.resize(640,360);await p.tap('c');
  await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.taskId===c.task;},'exact '+kind,120000);
  for(let i=0;i<80&&(await p.stats()).taskQueue;i++)await p.tap('Enter');
  await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return !s.taskQueue&&s.taskInputArmed&&s.auto.kind!=='wait';},'active '+kind,120000);
  await p.sampled(30);const before=await p.stats();
  await fs.writeFile(path.join(dir,'record.request'),JSON.stringify({name:'failure',seconds:12,fps:12}));
  await p.sampled(4);
  if(kind==='choice'){
   const tasks=await read(path.join(repo,'data/v4_story/native_tasks.json')),spec=tasks.tasks[c.task].stage;
   const target=(spec.answer+1)%spec.options.length;
   await p.move(0,0);await p.sampled(15);
   for(let i=0;i<spec.options.length&&(await p.stats()).stage.selection!==target;i++){await p.tap('s');await p.sampled(15);}
   assert.equal((await p.stats()).stage.selection,target,'Physical selection must be a known wrong option');
   await p.tap('Enter');
  }else if(kind==='scrum'){
   if(before.auto.key==='Enter')await p.tap('s');
   await p.tap('Enter');
  }else if(kind==='showdown'){
   // An actual empty stroke; then let the authored statements reach their failure.
   await p.move(40,80);await p.button(40,80,true);await p.move(180,80);await p.button(180,80,false);
  }
  const hit=kind==='showdown'?await p.stats():await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.trialHp<before.trialHp?s:false;},'physical '+kind+' failure',90000);
  await p.until(async()=>{try{return await read(path.join(dir,'recordings/failure/recording.json'));}catch{return false;}},'recorded '+kind,90000);
  const trace=(await fs.readFile(path.join(dir,'impacts.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
  const damage=kind!=='showdown';
  assert(trace.some(r=>r.flashes.some(f=>f.color[0]>.7&&f.color[1]<.1&&f.color[3]>=(damage?.29:.09))),'Actual native UI must receive the red flash');
  assert(trace.some(r=>r.shake?.intensity>=(damage?.06:.017)&&r.shake.remaining>0),'Actual camera must receive the decaying shake');
  assert(trace.some(r=>r.shake?.remaining>0&&r.shake.remaining<.25),'Shake must decay, not latch');
  if(!damage)assert.equal(hit.trialHp,before.trialHp,'Empty stroke feedback must not invent an HP penalty');
  const movie=await read(path.join(dir,'recordings/failure/recording.json'));
  rows.push({kind,hpBefore:before.trialHp,hpAfter:hit.trialHp,actualFlashFrames:trace.filter(r=>r.flashes.length).length,actualShakeFrames:trace.filter(r=>r.shake?.remaining>0).length,recording:path.join(dir,'recordings/failure/recording.json'),recordedFrames:movie.frames.length,audio:trace.find(r=>r.audio)?.audio});
  const runtime=await p.close();p=null;assert(!runtime.audio?.errors?.length,'Native audio must not fail');
  await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:false,inProgress:true,build:build.id,work,rows},null,2));
  console.log(JSON.stringify({kind,passed:true,hpBefore:before.trialHp,hpAfter:hit.trialHp,work:dir}));
 }
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,build:build.id,work,rows,engineModified:false,scope:'Actual nearby saved tasks, physical wrong selection / empty stroke / unattended authored failure. No injected outcomes; captured native flash and camera state. Candidate only.'},null,2));
}catch(e){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:e.stack,rows,last:await p?.stats()},null,2));throw e;}finally{await p?.close();}
