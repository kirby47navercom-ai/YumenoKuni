import{assertHudScope}from'./native-hud-scope-assert.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),build=JSON.parse(await fs.readFile(process.argv.find(v=>v.startsWith('--build-result='))?.slice(15)||path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/native-mode-matrix-'+Date.now());await fs.mkdir(work,{recursive:true});
const candidate=process.argv.find(a=>a.startsWith('--candidate='))?.slice(12),rendererCandidate=process.argv.find(a=>a.startsWith('--renderer-candidate='))?.slice(21);
const gameModule=process.argv.find(a=>a.startsWith('--game-module='))?.slice(14),gameContentOverrides=process.argv.find(a=>a.startsWith('--content-overrides='))?.slice(20);
const measureSeconds=Number(process.argv.find(a=>a.startsWith('--measure-seconds='))?.slice(18)||0),width=Number(process.argv.find(a=>a.startsWith('--width='))?.slice(8)||0),height=Number(process.argv.find(a=>a.startsWith('--height='))?.slice(9)||0);assert(!measureSeconds||(measureSeconds>=10&&measureSeconds<=30));assert((!width&&!height)||(width>=320&&width<=7680&&height>=240&&height<=4320));if(measureSeconds)process.env.YUMENO_NATIVE_UI_PROFILE='1';
const prepared=await createOwnedNativePackage({source:build.output,work,candidate,rendererCandidate,gameModuleCandidate:gameModule,gameContentOverrides,stats:true});
const cases=JSON.parse(await fs.readFile(path.join(root,'Saved/native-task-checkpoints.json'),'utf8')),only=process.argv.find(a=>a.startsWith('--only='))?.slice(7)?.split(',');
process.env.YUMENO_NATIVE_TRANSITION_TRACE='1';const results=[];
for(const[kind,row]of Object.entries(cases)){
 if(only&&!only.includes(kind))continue;
 let probe;const item={kind,task:row.task,resume:row.file,ok:false},directory=path.join(work,kind);
 try{
  probe=await nativeWindowProbe({source:build.output,work:directory,prepared,resume:path.resolve(repo,row.file)});if(width){await probe.hiddenBorderless();await probe.resize(width,height);}await probe.tap('c');
  await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);return s.mode==='trial'&&s.taskId===row.task?s:false;},'exact saved '+kind,60000);
  for(let i=0;i<60;i++){const s=await probe.stats();if(!s.taskQueue)break;await probe.tap('Enter');}
  let state=await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);return !s.taskQueue&&s.taskInputArmed&&!s.presentation.nonstopIntro?s:false;},'active '+kind,120000);
  // Animated mode entrances are real time. Wait for the authored actionable state.
  if(['mindmine','scrum','armament','climax'].includes(kind))state=await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);return s.auto.kind!=='wait'?s:false;},'mode entrance '+kind,40000);
  assert.equal(state.stage.kind,kind);item.entry=state;item.viewport=await probe.viewport();
  if(process.argv.includes('--settle-capture'))await probe.sampled(60);
  await probe.capture('active');
  const ui=JSON.parse(await fs.readFile(path.join(directory,'active.ui.json'),'utf8'));assert(ui.rects.length>8,'Active mode UI must actually paint');assertHudScope(ui,['nonstop','lie'].includes(kind)?'debate':['panic','anagram','showdown'].includes(kind)?kind:'basic');item.actualPaintedNodes=ui.rects.length;if(kind==='scrum'){const desks=ui.world.filter(o=>/^Podium\d+$/.test(o.id));assert.equal(desks.length,16);assert(desks.every(o=>o.mesh==='Assets/Art/court3d/trial_podium.glb'),'Scrum requires the actual separate podium meshes');const left=desks.filter(o=>Math.abs(o.position[0]+.95)<.05),right=desks.filter(o=>Math.abs(o.position[0]-.95)<.05);assert(left.length&&right.length,'The real podiums must form both opposing rows');assert([...left,...right].every(o=>o.scale[1]>.83),'Actual podium meshes must rise independently');item.podiums={separate:16,left:left.length,right:right.length,raised:true};}
  if(['scrum','showdown'].includes(kind)){const clocks=ui.world.filter(o=>o.name?.startsWith('stage/StageClockDigit')&&o.sprite?.visible);assert.equal(clocks.length,9,'The full original stage countdown must render');let text='';for(const o of clocks.sort((a,b)=>a.name.localeCompare(b.name))){const sprite=JSON.parse(await fs.readFile(path.join(prepared.output,'Content',o.sprite.sprite),'utf8'));assert.equal(sprite.font,'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf');text+=sprite.glyph;}assert(/^\d\d:\d\d:\d\d\d$/.test(text),'Original countdown digits and punctuation');item.stageClock={digits:clocks.length,text,originalFont:true};}
  if(measureSeconds){const first=JSON.parse(await fs.readFile(path.join(directory,'stats.json'),'utf8')),started=Date.now();for(let i=0;i<measureSeconds;i++){await new Promise(r=>setTimeout(r,1000));const s=await probe.stats();assert(!s.error,s.error);assert.equal(s.taskId,row.task,'Performance sample must stay in the actual checkpoint task');}const last=JSON.parse(await fs.readFile(path.join(directory,'stats.json'),'utf8')),seconds=(Date.now()-started)/1000;item.performance={diagnosticOnly:true,statsBinding:true,profile:true,width:width||item.viewport[0],height:height||item.viewport[1],seconds,frames:last.sequence-first.sequence,fps:(last.sequence-first.sequence)/seconds,firstSequence:first.sequence,lastSequence:last.sequence,scope:'Instrumented actual restored mode, unchanged product settings. Read-only per-frame Stats and timing add overhead; not an unprofiled performance acceptance.'};}
  if(['choice','bullet','person','vote','reasoning'].includes(kind)){
   await probe.tap(['person','vote'].includes(kind)?'d':'s');item.afterInput=await probe.stats();assert.notEqual(item.afterInput.stage.selection,state.stage.selection,'Native selection navigation must change selection');
  }else if(['nonstop','panic'].includes(kind)){
   await probe.until(async()=>{const s=await probe.stats();return s.presentation.inputArmed&&!s.trial.turning?s:false;},'debate input');await probe.key('Shift',true);await probe.sampled(4);await probe.key('Shift',false);item.afterInput=await probe.stats();
  }else if(kind==='lie'){
   await probe.key('Space',true);await probe.sampled(40);await probe.capture('charged');await probe.click(460,320);await probe.key('Space',false);item.afterInput=await probe.stats();assert(!item.afterInput.error,item.afterInput.error);assert(item.afterInput.taskQueue||item.afterInput.node!==state.node,'Charged native lie input must advance the authored task');await probe.capture('after-success');
  }else if(state.auto.kind==='click'){
   await probe.click(state.auto.x,state.auto.y);item.afterInput=await probe.stats();assert(!item.afterInput.error,item.afterInput.error);
  }else{await probe.tap('Tab');assert.equal((await probe.stats()).mode,'pad');await probe.tap('Tab');item.afterInput=await probe.stats();assert.equal(item.afterInput.mode,'trial');}
  const runtime=await probe.close();probe=null;item.runtime={frames:runtime.frames,inputs:runtime.inputs,memory:runtime.memory,preparationMS:runtime.preparationMS,audioErrors:runtime.audio.errors};if(item.performance){const rows=runtime.logic.profile.frames.filter(f=>f.frame>item.performance.firstSequence+2&&f.frame<item.performance.lastSequence-2),summary={frames:rows.length,uiChanged:rows.filter(f=>f.ui?.changed).length};for(const key of ['runtimeMs','native.invokeMs','renderAndHUDMs','frameWorkMs','ui.paintMS','ui.encodeMS','ui.submitMS','ui.totalMS']){const a=rows.map(f=>key.split('.').reduce((v,k)=>v?.[k],f)).filter(Number.isFinite).sort((a,b)=>a-b);if(a.length)summary[key]={p50:a[Math.floor((a.length-1)*.5)],p95:a[Math.floor((a.length-1)*.95)]};}item.performance.profileSummary=summary;}item.ok=true;
 }catch(error){item.error=error.stack;item.last=await probe?.stats().catch(()=>null);await probe?.capture('failure').catch(()=>{});}finally{await probe?.close().catch(()=>{});}
 results.push(item);await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:results.every(r=>r.ok),work,build:build.id,shippingEngine:!candidate&&!rendererCandidate,shippingGame:!gameModule&&!gameContentOverrides,candidate,rendererCandidate,gameModule,gameContentOverrides,results,scope:'One actual Win32/D3D11+Skia restored checkpoint per authored trial type. Visible UI and limited native input; not every task success, full campaign or human timing. shippingEngine identifies whether engine candidates were used.'},null,2));console.log(JSON.stringify({kind,ok:item.ok,work:directory,error:item.error?.split('\n')[0]}));
}
if(results.some(r=>!r.ok))process.exitCode=1;
