import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),engine=path.resolve(repo,'../engineCreate');
const work=path.join(root,'Saved/native-panic-views-'+Date.now());await fs.mkdir(work,{recursive:true});
const build=JSON.parse(await fs.readFile(path.join(root,'Saved/game-trial-work-20261102/current-flat-build-result.json'),'utf8'));
const reuse=process.argv.find(v=>v.startsWith("--reuse-package="))?.slice(16);
let prepared;if(reuse){assert(path.resolve(reuse).startsWith(path.join(root,"Saved/native-panic-views-")));const manifest=JSON.parse(await fs.readFile(path.join(reuse,"game.hbpack.json"),"utf8"));prepared={output:path.resolve(reuse),manifest,executable:path.join(path.resolve(reuse),manifest.windowsApplication.executable)};}else prepared=await createOwnedNativePackage({source:build.output,work,stats:true,
 gameModuleCandidate:path.join(root,'Saved/game-trial-work-20261102/game-trial-panic-views-20261103.exe'),
 gameContentOverrides:path.join(root,'Saved/game-trial-work-20261102/trial-feedback-overrides.json'),
 rendererCandidate:path.join(engine,'prototype/native-scene-renderer.js'),runnerCandidate:path.join(engine,'tools/native-game-runner.mjs'),
 playerCandidate:path.join(root,'Saved/panic-multiview-20261103/HBNativePlayer.exe')});
// This new module has no existing hardlinked package file.
const helper='prototype/game-render-views.js',bytes=await fs.readFile(path.join(engine,helper));if(!reuse)await fs.writeFile(path.join(prepared.output,helper),bytes,{flag:'wx'});
const {createHash}=await import('node:crypto');if(!reuse)prepared.manifest.files.push({path:helper,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
const candidate=process.argv.find(v=>v.startsWith('--game-module='))?.slice(14);
if(candidate){assert(reuse,'Patch only the existing owned QA package');const relative=prepared.manifest.nativeModules[0].binary,target=path.resolve(prepared.output,relative);assert(target.startsWith(prepared.output+path.sep));await fs.unlink(target);await fs.copyFile(path.resolve(candidate),target);const b=await fs.readFile(target);Object.assign(prepared.manifest.files.find(r=>r.path===relative),{bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')});}
if(candidate)for(const asset of ['Assets/UI/Main.hbwidget.json','Assets/Art/ui/hud_name_reference.svg']){
 const relative='Content/'+asset,target=path.resolve(prepared.output,relative);assert(target.startsWith(prepared.output+path.sep));await fs.mkdir(path.dirname(target),{recursive:true});await fs.unlink(target).catch(e=>{if(e.code!=='ENOENT')throw e;});await fs.copyFile(path.join(root,asset),target);const b=await fs.readFile(target),r=prepared.manifest.files.find(v=>v.path===relative)||{path:relative};if(!prepared.manifest.files.includes(r))prepared.manifest.files.push(r);Object.assign(r,{bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')});if(!prepared.manifest.entries.some(v=>v.path===asset))prepared.manifest.entries.push({path:asset,name:path.basename(asset),kind:asset.endsWith('.svg')?'texture':'widget'});
}
await fs.writeFile(path.join(prepared.output,'game.hbpack.json'),JSON.stringify(prepared.manifest));
const row=JSON.parse(await fs.readFile(path.join(root,'Saved/native-task-checkpoints.json'),'utf8')).panic;
process.env.YUMENO_NATIVE_QA_RENDER_PROFILE='1';let p;const report={work,shipping:false,checks:[]};
try{
 p=await nativeWindowProbe({source:build.output,prepared,work,resume:path.resolve(repo,row.file),maxFrames:null,heartbeatTimeoutMs:120000});
 await p.hiddenBorderless();await p.resize(1920,1080);await p.tap('c');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.taskId===row.task;},'exact Panic checkpoint',120000);
 for(let i=0;i<80&&(await p.stats()).taskQueue;i++)await p.tap('Enter');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return !s.taskQueue&&s.taskInputArmed;},'active Panic',120000);
 if(candidate)await p.sampled(240); // Observe active play after the entrance band, not its first frame.
 for(const [width,height,name] of [[1920,1080,'panic-1080'],[3840,2160,'panic-4k']]){
  await p.resize(width,height);await p.sampled(15);await p.capture(name);
  const ui=JSON.parse(await fs.readFile(path.join(work,name+'.ui.json'),'utf8'));
  assert.equal(ui.renderViews?.length,3,'Three independent game cameras');
  const packets=ui.qaRenderPackets.filter(v=>v.op==='frame');assert(packets.some(v=>v.renderViews===3),'Native GPU rendered all three views');
  assert(ui.renderViews.every(v=>v.eye.length===3&&v.target.length===3));
  if(candidate){const names=ui.world.filter(o=>/^TrialGpu_PanicName[0-2]$/.test(o.id));assert.equal(names.length,3);assert(names.every(o=>!o.sprite.visible),'Old per-pane names must remain hidden');const main=ui.widgets.find(w=>w.instance==='main'),speaker=main.nodes.find(n=>n.id==='TrialSpeaker').properties;assert(speaker.visible,'Shared active speaker name replaces the three labels');assert(speaker.text.trim(),'Visible speaker field must contain the actual actor name');assert(!main.nodes.find(n=>n.id==='StartBand').properties.visible,'Entrance band must finish before active-play evidence');}
  report.checks.push({name,width,height,views:ui.renderViews,render:packets.at(-1)});
 }
 await p.tap('Tab');await p.until(async()=>(await p.stats()).mode==='pad','pad entry');await p.sampled(8);await p.capture('suspended');
 const suspended=JSON.parse(await fs.readFile(path.join(work,'suspended.ui.json'),'utf8'));
 assert(!suspended.renderViews?.length,'Leaving active mode clears view definitions');assert.equal(suspended.qaRenderPackets.filter(v=>v.op==='frame').at(-1).renderViews,0,'GPU view targets released');
 await p.tap('Tab');await p.sampled(10);await p.capture('restored');
 const restored=JSON.parse(await fs.readFile(path.join(work,'restored.ui.json'),'utf8'));assert.equal(restored.renderViews?.length,3,'Modal return restores cameras');
 report.runtime=await p.close();p=null;report.ok=true;
}catch(error){report.error=error.stack;await p?.capture('failure').catch(()=>{});throw error;}
finally{await p?.close().catch(()=>{});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,ok:report.ok,error:report.error?.split('\n')[0]}));}
