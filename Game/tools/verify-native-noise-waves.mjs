// Nearby normal checkpoint: same-frame geometry and physical silencer input.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {assertNoiseWaves} from './native-noise-wave-assert.mjs';
const root=path.resolve(import.meta.dirname,'..'),base=path.join(root,'Saved/game-trial-work-20261102'),shipping=process.argv.includes('--shipping');
const build=JSON.parse(await fs.readFile(path.join(base,'current-flat-build-result.json'),'utf8')),work=path.join(root,'Saved/native-gpu-trial-'+Date.now());await fs.mkdir(work);
const save=path.join(root,'Saved/ui-checkpoints/normal-ch3-latest/savegames.json'),bytes=await fs.readFile(save),hash=b=>createHash('sha256').update(b).digest('hex');
const prepared=await createOwnedNativePackage({source:build.output,work,stats:true,aimStats:true,...shipping?{}:{gameModuleCandidate:path.join(base,'game-noise-waves-candidate.exe'),gameContentOverrides:path.join(base,'noise-wave-overrides.json')}});
const assets=new Map(),asset=async name=>{if(!assets.has(name))assets.set(name,JSON.parse(await fs.readFile(path.join(prepared.output,'Content',name),'utf8')));return assets.get(name);};
const cameraLocal=(o,u)=>{let position=[...o.position],scale=[...o.scale],parent=o.parent;for(let i=0;i<8&&parent&&parent!=='Camera';i++){const p=u.world.find(p=>p.id===parent);assert(p);assert(p.rotation.every(v=>Math.abs(v)<.0001));position=position.map((v,k)=>p.position[k]+v*p.scale[k]);scale=scale.map((v,k)=>v*p.scale[k]);parent=p.parent;}return{position,scale};};
const clock=text=>{const m=/^(\d+):(\d+):(\d+)$/.exec(text);assert(m);return +m[1]*60+(+m[2])+(+m[3])/1000;};
const proofs=[];let p;
const snap=async(name,requireVisible=false)=>{for(let attempt=0;attempt<6;attempt++){const capture=name+'-'+attempt;await p.capture(capture);const u=JSON.parse(await fs.readFile(path.join(work,capture+'.ui.json'),'utf8')),s=await p.stats();assert(!s.error,s.error);const samples=await assertNoiseWaves(u,s,asset,cameraLocal);if(requireVisible&&!samples){await p.sampled(20);continue;}proofs.push({name,capture,size:[u.width,u.height],samples,rows:u.noiseSnapshot?.rows});return{u,s,samples};}throw Error('Original noise must become visible during its normal wave: '+name);};
try{
 p=await nativeWindowProbe({source:build.output,work,prepared,resume:save,maxFrames:null});await p.hiddenBorderless();await p.resize(2560,1440);await p.tap('c');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.auto?.kind==='debate'&&s.taskInputArmed&&!s.taskQueue&&!s.presentation.nonstopIntro&&s.gpuNoiseHud?.ready&&!s.gpuNoiseHud.warming;},'actual prepared ordinary noise',120000);
 const a=await snap('active',true);assert(a.samples>=3);await p.sampled(90);const b=await snap('moving',true);assert(b.samples>=3);assert.notDeepEqual(a.u.world.filter(o=>/^TrialBatch_Noise/.test(o.id)).map(o=>o.skinRuntime?.bones),b.u.world.filter(o=>/^TrialBatch_Noise/.test(o.id)).map(o=>o.skinRuntime?.bones),'The exact letter waves must actually move');
 await p.tap('o');await p.until(async()=>(await p.stats()).options.open,'options');const paused=await snap('options');assert.equal(paused.u.world.filter(o=>/^TrialBatch_Noise/.test(o.id)&&o.sprite?.visible).length,0);await p.sampled(90);const still=await snap('options-paused');assert.deepEqual(still.u.noiseSnapshot.modelPoints,paused.u.noiseSnapshot.modelPoints,'Options must pause the original noise model');await p.tap('Escape');await p.sampled(20);await snap('options-restored',true);
 for(const [name,w,h]of [['4k',3840,2160],['ultrawide',3440,1440],['four-three',1440,1080],['returned',2560,1440]]){await p.resize(w,h);await p.sampled(20);const r=await snap(name,true);assert.deepEqual([r.u.width,r.u.height],[w,h]);assert(r.samples>=3);}
 await p.key('Shift',true);let hit=false;
 for(const end=Date.now()+60000;Date.now()<end;){
  const before=await p.stats();assert(!before.error,before.error);const row=before.gpuNoiseHud?.rows?.find(r=>r[0]===0&&r[5]),point=before.gpuNoiseHud?.modelPoints?.find(r=>r[0]===0&&r[2]>40&&r[2]<1240&&r[3]>40&&r[3]<680);
  if(!row||!point||before.trial?.turning){await p.sampled(5);continue;}
  const previous=before.trial.noise,hp=before.trial.hp,time=clock(before.gpuTrialHud.timer);await p.rightClick(point[2],point[3]);await p.sampled(4);const after=await p.stats();assert(!after.error,after.error);
  if(after.trial.noise!==previous){assert.equal(after.trial.hp,hp,'Right-click noise clearing must preserve HP');assert(clock(after.gpuTrialHud.timer)>time+1,'Original ordinary-noise time reward must apply');proofs.push({name:'physical-noise-clear',before:previous,after:after.trial.noise,hp,remainingTimeGain:clock(after.gpuTrialHud.timer)-time});hit=true;break;}
 }
 await p.key('Shift',false);assert(hit,'Actually clear a visible noise phrase with the physical right mouse button');await snap('after-noise-clear');
 const runtime=await p.close();p=null;assert.equal(hash(await fs.readFile(save)),hash(bytes));await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,noiseOnly:true,shipping,build:build.id,work,proofs,runtime,sourceSaveSHA256:hash(bytes),scope:'Normal authored checkpoint. Same-frame original noise ModelPoints versus actual weighted renderer vertices/crop/parent depth, moving wave, options pause/restore, real1440p/4K/ultrawide/4:3 and physical right-click clearing/time reward. No engine changes or injected outcome.'},null,2));console.log(JSON.stringify({ok:true,work,proofs}));
}catch(error){await p?.capture('failure').catch(()=>{});await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,last:await p?.stats().catch(()=>null),proofs},null,2));throw error;}finally{await p?.key('Shift',false).catch(()=>{});await p?.close().catch(()=>{});}
