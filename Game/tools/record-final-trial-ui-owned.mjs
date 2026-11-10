// Actual retained-package footage. Entry fixtures only; no result injection.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {execFile}from'node:child_process';import{promisify}from'node:util';import{createHash}from'node:crypto';
import{nativeWindowProbe}from'./native-window-probe.mjs';import{beginOwnedMovie}from'./native-window-recording.mjs';
import{padSystemAction}from'./v4-pad-test-input.mjs';
import{caseSaveCatalogue,publishCaseSave}from'./native-case-saves.mjs';import{trialAimPlan}from'./v4-aim-test-input.mjs';import{bulletCycleKey}from'./v4-bullet-test-input.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),output=path.join(root,'Saved/native-panic-views-1793690486425/package');
const arg=(name,d)=>process.argv.find(v=>v.startsWith('--'+name+'='))?.slice(name.length+3)??d;
assert(process.argv.includes('--ready-final')||process.argv.includes('--ready-v7'),'Root must explicitly signal final package readiness');
const work=path.join(root,'Saved/final-trial-ui-movies-'+Date.now());await fs.mkdir(work,{recursive:true});
const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));assert(!manifest.contentArchive);
const tasks=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks;
const direction=JSON.parse(await fs.readFile(path.join(output,'Content/Assets/Data/v4_story/trial_direction.json'),'utf8'));
const ids=arg('tasks','T1-PERSON-A01,T1-EVIDENCE-A01,T1-ANSWER-A01,T1-SPOT-A01,T1-PN-A02,T1-RS-A02,T1-MM-A02,T1-FA-A03,T1-RL-A02,T1-AA-01,T1-MG-01,T1-VOTE-01,T1-SD-01,T3-NS-A11').split(',');
const delay=ms=>new Promise(r=>setTimeout(r,ms)),catalogue=await caseSaveCatalogue(),exec=promisify(execFile);
process.env.YUMENO_NATIVE_QA_RECORD='1';
const report={version:arg('version','v7'),work,package:output,newPackageCreated:false,shipping:false,accepted:false,scope:'Owned hidden-window actual game + actual mixer at natural wall-clock speed. Reachable entry save fixtures are explicitly listed. No success/outcome injection. Raw clips require final visual review.',moduleSHA256:createHash('sha256').update(await fs.readFile(path.join(output,manifest.nativeModules[0].binary))).digest('hex'),rows:[]};
assert.equal(report.moduleSHA256,arg('expect-module-sha','0e46f6770cb8590b8b3ad8a2a96018fbebdfacde81ed01196e1734fad5a3a94b'),'Unexpected final QA module');
await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));
for(const taskId of ids){
 const task=tasks[taskId];assert(task?.ready,taskId);let p,recording,focus=false;
 const row={taskId,kind:task.stage.kind,completed:false,events:[]};report.rows.push(row);
 try{
  const session=path.join(work,taskId.toLowerCase());p=await nativeWindowProbe({source:output,prepared:{output,manifest,executable:path.join(output,manifest.windowsApplication.executable)},work:session,maxFrames:null,heartbeatTimeoutMs:120000});
  await p.hiddenBorderless();assert.deepEqual(await p.resize(1280,720),[1280,720]);
  row.fixture=await publishCaseSave({work,session:p.work,catalogue,taskId});await p.tap('s');await p.tap('w');
  recording=await beginOwnedMovie(p,taskId.toLowerCase(),{seconds:240});row.started=recording.started;await delay(700);await p.tap('c');
  const owned=new Set(row.fixture.evidence),available=(task.stage.options||[]).filter(o=>!task.stage.filterOwnedEvidence||owned.has(o.id)).map(o=>o.id),bullets=task.stage.kind==='nonstop'?(direction.nonstopAmmo[taskId]||available).filter(id=>owned.has(id)||available.includes(id)):available;
  let talkAt=0,activeHeld=false,returnAt=0,actions=0,signature='',minePause=false,entrySeen=false,panicEntry=0,phaseCaptured=false;
  while(Date.now()-recording.started<235000){
   const s=await p.stats();assert(!s.error,s.error);assert(!s.routeBlocked,'Authored route blocked');const a=s.auto||{};
   const stamp=JSON.stringify([s.mode,s.node,s.taskId,s.taskQueue,a.kind,s.presentation?.nonstopIntro,s.mineV4?.successPhase]);
   if(stamp!==signature){signature=stamp;row.events.push({seconds:(Date.now()-recording.started)/1000,mode:s.mode,node:s.node,taskId:s.taskId,queue:s.taskQueue,auto:a.kind});}
   if(s.taskId===taskId)entrySeen=true;
   if(taskId==='T1-PN-A02'&&s.taskId===taskId&&!s.scenes?.loading&&!phaseCaptured){await delay(180);const phase=await p.capture('panic-source-phase-entry-'+panicEntry);(row.phaseCaptures??=[]).push({entry:panicEntry,seconds:(Date.now()-recording.started)/1000,capture:phase});phaseCaptured=true;}
   if(entrySeen&&s.lastTaskOutcome?.taskId===taskId&&s.taskId!==taskId&&!returnAt){row.outcome=s.lastTaskOutcome;row.returnNode=s.node;returnAt=Date.now();if(focus){await p.key('Shift',false);focus=false;}}
   if(returnAt){if(!s.scenes?.loading&&Date.now()-returnAt>2500){row.returnState={mode:s.mode,node:s.node,loading:false};if(taskId==='T1-PN-A02'&&panicEntry===0){row.firstEntryOutcome=row.outcome;row.firstEntryReturn=row.returnState;await p.sampled(12);await p.tap('Tab');if((await p.stats()).mode!=='pad'){await p.sampled(12);await p.tap('Tab');}await p.until(async()=>(await p.stats()).mode==='pad','Pad for Panic reentry');await p.click(1047,480);await padSystemAction(p.stats,p.tap,'title');await padSystemAction(p.stats,p.tap,'title_yes');await p.until(async()=>(await p.stats()).mode==='title','Panic actual title return');row.reentryFixture=await publishCaseSave({work,session:p.work,catalogue,taskId});await p.tap('s');await p.tap('w');await p.tap('c');panicEntry=1;entrySeen=false;phaseCaptured=false;returnAt=0;activeHeld=false;talkAt=0;row.outcome=null;row.returnState=null;row.reentryStarted=(Date.now()-recording.started)/1000;continue;}break;}await delay(40);continue;}
   if(s.taskQueue||(s.taskId!==taskId&&s.mode!=='title')){if(focus){await p.key('Shift',false);focus=false;}if(!s.scenes?.loading&&Date.now()-talkAt>1350){talkAt=Date.now();await p.tap('Enter',1);}else await delay(35);continue;}
   if(s.mode==='title'||s.scenes?.loading||s.taskId!==taskId||!s.taskInputArmed||s.presentation?.nonstopIntro){await delay(35);continue;}
   if(!activeHeld){activeHeld=true;if(process.argv.includes('--capture-active'))row.activeCapture=await p.capture('actual-active-ui');await delay(['armament','scrum','showdown','anagram'].includes(task.stage.kind)?250:1800);continue;}
   if(task.stage.kind==='mindmine'&&s.mineV4?.successTime>=0){await delay(35);continue;}
   if(task.stage.kind==='mindmine'&&!minePause&&s.mineV4?.covered===0){minePause=true;await delay(1700);continue;}
   if(a.kind==='debate'){
    const tr=s.trial;if(!s.presentation?.inputArmed||!tr||tr.clearing||tr.turning||tr.shotInFlight||tr.shotRecovery?.ready===false||!tr.answer||tr.answer==='decoy:none'||!['weak','agree'].includes(tr.kind)||!tr.weakPoint){if(focus){await p.key('Shift',false);focus=false;}await delay(18);continue;}
    const pink=(s.gpuNoiseHud?.modelPoints||[]).find(v=>v[4]>.95&&v[2]>45&&v[2]<1235&&v[3]>45&&v[3]<630);
    if(pink){const aim=trialAimPlan([pink[2],pink[3]],await p.aim());if(aim.kind==='mouse'){await p.move(...aim.point);await p.button(...aim.point,true,tr.noiseButton||'left');await delay(70);await p.button(...aim.point,false,tr.noiseButton||'left');actions++;continue;}}
    if(tr.bullet!==tr.answer){await p.tap(bulletCycleKey(bullets,tr.bullet,tr.answer),1);actions++;await delay(100);continue;}
    if(!focus){await p.key('Shift',true);focus=true;await p.sampled(2);continue;}
    const plan=trialAimPlan(tr.weakPoint,await p.aim());if(plan.kind==='key'){await p.key(plan.key,true);await delay(plan.ms);await p.key(plan.key,false);}
    else{await p.move(...plan.point);await p.button(...plan.point,true,tr.shotButton||'right');let release=plan.point;if(tr.needLie){const ready=await p.until(async()=>{const q=await p.stats();return q.trial?.lie?q:false;},'Actual lie charge',10000,30);if(ready.trial?.weakPoint){const aim=trialAimPlan(ready.trial.weakPoint,await p.aim());if(aim.kind==='mouse'){release=aim.point;await p.move(...release);}}}await p.button(...release,false,tr.shotButton||'right');}actions++;await delay(90);continue;
   }
   if(focus){await p.key('Shift',false);focus=false;}
   if(a.kind==='sd-slash'){await p.move(a.x,a.y);await delay(80);if(a.blade){await p.rightClick(a.x,a.y);await delay(250);const q=(await p.stats()).auto||a;await p.click(q.kind==='sd-slash'?q.x:a.x,q.kind==='sd-slash'?q.y:a.y);}else await p.click(a.x,a.y);actions++;}
   else if(a.kind==='key'||a.kind==='rapid-key'){if(a.key==='mouse0')await p.click(640,360);else await p.tap(a.key,1);actions++;await delay(a.kind==='rapid-key'?15:85);}
   else if(a.kind==='hold-key'||a.kind==='release-after'){await p.key(a.key,true);await delay(Math.max(1,(a.seconds??a.remaining)*1000));await p.key(a.key,false);actions++;}
   else if(a.kind==='hold-target'){await p.key(a.key,true);await delay(a.seconds*1000);await p.click(a.x,a.y);await p.key(a.key,false);actions++;}
   else if(a.kind==='click'){await p.click(a.x,a.y);actions++;await delay(task.stage.kind==='mindmine'?65:170);}
   else if(a.kind==='move'){if(task.stage.kind==='mindmine')await p.rightClick(a.x,a.y);else await p.move(a.x,a.y);actions++;}
   else if(a.kind==='drag'||a.kind==='blade-drag'){const sd=task.stage.kind==='showdown',x0=sd?20:a.x0,x1=sd?1260:a.x1;if(sd)await p.key('d',true);if(a.kind==='blade-drag')await p.key('Space',true);await p.move(x0,a.y);await p.button(x0,a.y,true);await p.move(x1,a.y);await p.button(x1,a.y,false);if(a.kind==='blade-drag')await p.key('Space',false);if(sd)await p.key('d',false);actions++;}
   else await delay(30);
  }
  for(const k of ['Shift','Space','d','w','a','s'])await p.key(k,false);
  row.movie=await recording.finish();recording=null;row.actions=actions;assert(row.outcome&&row.returnState,'Missing actual success or authored returned screen');row.completed=true;
 }catch(error){row.error=error.stack;row.last=await p?.stats().catch(()=>null);if(recording){row.partialMovie=await recording.finish().catch(e=>({error:e.message}));recording=null;}}
 finally{await p?.close().catch(e=>row.shutdownError=e.message);await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({taskId,completed:row.completed,duration:row.movie?.duration,error:row.error?.split('\n')[0],work}));}
}
// Pack whole clips without cutting introductions/results, changing speed, or
// injecting UI. The original per-case clips and entry receipts remain linked.
if(report.rows.every(r=>r.completed)){
 const packs=Array.from({length:Math.min(3,report.rows.length)},()=>({rows:[],seconds:0}));for(const row of report.rows.slice().sort((a,b)=>b.movie.duration-a.movie.duration)){let p=packs.filter(p=>p.seconds+row.movie.duration<=298).sort((a,b)=>a.seconds-b.seconds)[0];if(!p&&packs.length<4){p={rows:[],seconds:0};packs.push(p);}assert(p,'Natural-speed complete sequences exceed four300-second packs');p.rows.push(row);p.seconds+=row.movie.duration;}
 report.packs=[];for(const [i,pack]of packs.entries()){pack.rows.sort((a,b)=>ids.indexOf(a.taskId)-ids.indexOf(b.taskId));const list=path.join(work,'pack-'+i+'.txt'),movie=path.join(work,'trial-ui-'+(i+1)+'.mp4');await fs.writeFile(list,pack.rows.map(r=>"file '"+r.movie.movie.split(path.sep).join('/').replaceAll("'","'\\''")+"'").join('\n'));await exec('ffmpeg',['-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',list,'-c','copy','-movflags','+faststart',movie],{windowsHide:true,timeout:120000});report.packs.push({movie,tasks:pack.rows.map(r=>r.taskId),seconds:pack.seconds,actualGame:true,actualMixer:true,speed:1});}
 report.sequenceCompleted=true;
}else process.exitCode=1;
await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,complete:report.sequenceCompleted,packs:report.packs}));
