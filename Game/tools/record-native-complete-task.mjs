// Actual input, intro and authored return. Uses the one retained QA package.
// A recording failure remains internal evidence, never a completed user clip.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {beginOwnedMovie} from './native-window-recording.mjs';
import {caseSaveCatalogue,publishCaseSave} from './native-case-saves.mjs';
import {trialAimPlan} from './v4-aim-test-input.mjs';
import {bulletCycleKey} from './v4-bullet-test-input.mjs';
import {createHash} from 'node:crypto';
import {proveMineWall} from './native-mine-wall-proof.mjs';
import {SPOT_RECT} from './v4-spot-ui.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),output=path.join(root,'Saved/native-panic-views-1793690486425/package');
const arg=(k,d)=>process.argv.find(v=>v.startsWith('--'+k+'='))?.slice(k.length+3)??d;
const taskId=arg('task','T3-NS-A11'),seconds=Number(arg('seconds','240'));
const task=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks[taskId];assert(task?.ready);
const authoredThought=JSON.parse(await fs.readFile(path.join(repo,'data/presentation/nonstop_followup.json'),'utf8')).tasks[taskId]?.hint;
const thoughtParts=authoredThought?.split(/(?<=[.?!]) +/),compact=s=>s.replace(/\s/g,'');
const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));
const moduleArg=arg('game-module','');if(moduleArg){const file=path.resolve(root,moduleArg);assert(file.startsWith(path.join(root,'Saved')+path.sep));const relative=manifest.nativeModules[0].binary,destination=path.resolve(output,relative);assert(destination.startsWith(output+path.sep));const bytes=await fs.readFile(file);await fs.writeFile(destination+'.movie.tmp',bytes);await fs.rename(destination+'.movie.tmp',destination);Object.assign(manifest.files.find(r=>r.path===relative),{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));}
const work=path.join(root,'Saved/complete-task-movie-'+Date.now());await fs.mkdir(work,{recursive:true});process.env.YUMENO_NATIVE_QA_RECORD='1';process.env.YUMENO_NATIVE_IMPACT_TRACE='1';
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const report={work,taskId,kind:task.stage.kind,shipping:false,accepted:false,events:[],scope:'Actual current QA input and continuous recording from the identified entry save. No injected outcome. Must be visually reviewed before delivery.'};let p,recording;
report.packageExecutableSHA256=createHash('sha256').update(await fs.readFile(path.join(output,manifest.windowsApplication.executable))).digest('hex');
report.gameModuleSHA256=createHash('sha256').update(await fs.readFile(path.join(output,manifest.nativeModules[0].binary))).digest('hex');
try{
 p=await nativeWindowProbe({source:output,prepared:{output,manifest,executable:path.join(output,manifest.windowsApplication.executable)},work,maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(1280,720);
 report.precondition=await publishCaseSave({work,session:work,catalogue:await caseSaveCatalogue(),taskId});
 await p.tap('s');await p.tap('w');
 recording=await beginOwnedMovie(p,'complete-task',{seconds});
 await p.tap('c');await p.until(async()=>(await p.stats()).taskId===taskId,'current actual task entry',120000);await p.tap('F2');
 const owned=(task.stage.options||[]).filter(o=>!task.stage.filterOwnedEvidence||report.precondition.evidence.includes(o.id)).map(o=>o.id);
 const direction=JSON.parse(await fs.readFile(path.join(output,'Content/Assets/Data/v4_story/trial_direction.json'),'utf8'));
 const options=direction.nonstopAmmo?.[taskId]?.filter(id=>owned.includes(id)||report.precondition.evidence.includes(id))||owned;
 if(task.stage.kind==='nonstop')report.ammunition=options;
 const preferLie=process.argv.includes('--prefer-lie')&&task.transformation?.intentionalHold;
 if(process.argv.includes('--prefer-agree'))assert([...task.debate.lines,...(direction.extra?.[taskId]||[])].some(r=>r.kind==='agree'),'Choose an authored agreement task before recording');
 const observeCycle=process.argv.includes('--observe-cycle')&&task.stage.kind==='nonstop';
 const expectNoNoise=arg('expect-noise','')==='absent';report.expectNoNoise=expectNoNoise;
 const observeFeedback=observeCycle||process.argv.includes('--observe-feedback');
 const observeFlight=task.stage.kind==='nonstop'&&process.argv.includes('--observe-flight');
 const observeWhip=task.stage.kind==='nonstop'&&process.argv.includes('--observe-whip');
 let priorShot,turn;
 const trackWhip=state=>{
  const row=state.trial,pose=state.presentation?.camera;
  if(!pose||!row||state.taskQueue||row.clearing||state.presentation.nonstopIntro){priorShot=turn=null;return;}
  const sample={ms:Date.now()-recording.started,yaw:pose[3],x:pose[0],z:pose[2]};
  if(row.turning){
   if(!turn&&priorShot&&priorShot.seat!==row.speakerSeat)
    turn={from:priorShot.seat,to:row.speakerSeat,start:priorShot.sample,samples:[]};
   if(turn&&turn.samples.at(-1)?.yaw!==sample.yaw)turn.samples.push(sample);
  }else{
   if(turn&&turn.samples.length>=3){
    (report.cameraTurns??=[]).push({...turn,end:sample});
   }
   turn=null;priorShot={seat:row.speakerSeat,sample};
  }
 };

 let lastLine=-1,pendingNonstopRestart=null;
 const captureFeedback=async(name,prefix)=>{
  const file=await p.capture(name,{pixels:false}),snapshot=JSON.parse(await fs.readFile(file,'utf8'));
  const node=snapshot.widgets.find(w=>w.instance==='main')?.nodes.find(n=>n.id==='TrialMsg');
  if(task.stage.kind==='nonstop'&&prefix==='오답'){assert(!node?.properties.visible,'Invented wrong-shot HUD text must stay hidden');assert((await p.stats()).taskQueue,'Authored wrong-response queue must be active');return {elapsedMS:Date.now()-recording.started,authoredQueue:true,inventedHudAbsent:true};}
  assert(node?.properties.visible&&node.properties.text.startsWith(prefix),name+' feedback was not visible');
  return {elapsedMS:Date.now()-recording.started,text:node.properties.text};
 };
 let talkAt=0,focus=false,wrongSent=process.argv.includes('--correct-only'),wrongHP=null,afterAt=0,returnReadyAt=0,actions=0,lastSignature='';
 while(Date.now()-recording.started<(seconds-3)*1000){
  const s=await p.stats();assert(!s.error,s.error);assert(!s.routeBlocked,'Authored route blocked');
  if(observeWhip)trackWhip(s);
  if(process.argv.includes('--observe-loop-contract')){
   if(s.taskQueue&&['nonstop-loop','nonstop-wrong'].includes(s.queueAfter)&&!pendingNonstopRestart){
    pendingNonstopRestart={phase:s.queueAfter,hp:s.trialHp,timer:s.presentation?.timer,bullet:s.trial?.bullet};
    report[s.queueAfter]={elapsedMS:Date.now()-recording.started,...pendingNonstopRestart};
    await p.capture(s.queueAfter);
   }else if(pendingNonstopRestart&&!s.taskQueue&&s.trial&&s.taskInputArmed&&!s.presentation?.nonstopIntro){
    assert.equal(s.trial.index,0,'Reaction/monologue must restart from the first utterance');
    assert(s.presentation.statementTime<.7,'The first utterance restarts at its beginning');
    assert.equal(s.trialHp,pendingNonstopRestart.hp,'Internal restart must not heal damage');
    assert(s.presentation.timer<=pendingNonstopRestart.timer+.1&&s.presentation.timer>=pendingNonstopRestart.timer-1,'Internal restart must preserve remaining time');
    assert.equal(s.trial.bullet,pendingNonstopRestart.bullet,'Selected evidence survives internal restart');
    report[pendingNonstopRestart.phase].restart={index:s.trial.index,time:s.presentation.statementTime,hp:s.trialHp,timer:s.presentation.timer};
    await p.capture(pendingNonstopRestart.phase+'-first-row');pendingNonstopRestart=null;
   }
   report.maxConcurrentNoise=Math.max(report.maxConcurrentNoise||0,s.trial?.noiseRows?.length||0);
   if(s.trial?.noiseRows?.length>=2&&s.presentation?.statementTime>=4&&!report.concurrentNoiseLate&&!s.trial.turning&&!s.taskQueue){report.concurrentNoiseLate={elapsedMS:Date.now()-recording.started,index:s.trial.index,time:s.presentation.statementTime,count:s.trial.noiseRows.length};await p.capture('concurrent-noise-with-statement-late');}
  }

  if(process.argv.includes('--observe-noise-coverage')&&s.trial&&!s.taskQueue&&!s.trial.turning&&!s.presentation?.nonstopIntro){
   if(taskId.startsWith('T1-'))assert.notEqual(s.trial.kind,'agree','Chapter 1 must not show blue agreement');
   if(s.trial.noise>=0&&(s.gpuNoiseHud?.modelPoints||[]).some(v=>v[4]>.95)){
    report.noiseCoverage??={};const index=s.trial.index;
    if(!report.noiseCoverage[index]){report.noiseCoverage[index]={elapsedMS:Date.now()-recording.started,kind:s.trial.kind,rows:s.trial.noiseRows};const image=await p.capture('noise-utterance-'+index);const frame=JSON.parse(await fs.readFile(image.replace(/\.png$/,'.ui.json'),'utf8'));const actors=new Map(frame.world.map(o=>[o.id,o]));const root=actors.get('TrialSpeakerDepth');const pink=frame.world.filter(o=>/^TrialGpu_NF\d+$/.test(o.id)&&o.sprite?.visible&&o.sprite.color[3]>.9);assert(pink.length,'Pink text must actually render');for(const o of pink)assert(-o.position[2]*(root?.scale?.[2]||1)<.3,'Noise must stay in front of court figures');report.noiseCoverage[index].foreground=true;}
   }
  }
  const a=s.auto||{},signature=JSON.stringify({node:s.node,queue:s.taskQueue,armed:s.taskInputArmed,kind:a.kind,intro:!!s.presentation?.nonstopIntro,phase:s.armamentV4?.phase,panic:s.panicV4?.phase});
  if(signature!==lastSignature){lastSignature=signature;report.events.push({elapsedMS:Date.now()-recording.started,node:s.node,queue:s.taskQueue,armed:s.taskInputArmed,auto:a.kind,intro:!!s.presentation?.nonstopIntro,hp:s.trialHp});}
  if(wrongSent&&wrongHP!==null&&s.trialHp<wrongHP&&!report.wrong){report.wrong={elapsedMS:Date.now()-recording.started,hpBefore:wrongHP,hpAfter:s.trialHp};if(observeFeedback)report.wrong.feedback=await captureFeedback('wrong-feedback','오답');}
  if(s.lastTaskOutcome?.taskId===taskId&&s.taskId!==taskId&&!afterAt){report.outcome=s.lastTaskOutcome;report.returnNode=s.node;afterAt=Date.now();if(observeFeedback)report.correctFeedback={elapsedMS:Date.now()-recording.started,judgment:s.lastTaskOutcome.judgment,authoredReturn:true,cinematic:report.resultCinematic};if(focus){await p.key('Shift',false);focus=false;}}
  if(afterAt){
   if(s.scenes?.loading){await delay(30);continue;}
   if(!returnReadyAt){await p.sampled(12);await p.capture('returned-script-ready');returnReadyAt=Date.now();report.returnReady={elapsedMS:returnReadyAt-recording.started,node:s.node};}
   if(Date.now()-returnReadyAt>=1800)break;
   await delay(30);continue;
  }
  if(s.trial?.resultTime>0&&!report.resultCinematic)report.resultCinematic={elapsedMS:Date.now()-recording.started,result:s.trial.result};
  if(s.taskQueue){
   if(focus){await p.key('Shift',false);focus=false;}
   if(s.scenes?.loading){await delay(30);continue;}
   if(Date.now()-talkAt>2200){
    talkAt=Date.now();
    if(s.queueAfter==='nonstop-loop'){
     const name='loop-thought-'+(report.loopThoughts?.length||0),file=await p.capture(name,{pixels:false}),snap=JSON.parse(await fs.readFile(file,'utf8')),nodes=snap.widgets.find(w=>w.instance==='main')?.nodes||[],next=nodes.find(n=>n.id==='Next'),body=nodes.find(n=>n.id==='Body');
     // A capture can precede the final glyph by one native frame. Sending Enter
     // then can advance the newly completed line without its readable capture.
     // Observe the actual page indicator first; never skip an unrecorded thought.
     if(!next?.properties.visible){talkAt=0;await delay(100);continue;}
     if(next?.properties.visible&&body?.properties.text){
      const text=body.properties.text;assert(!/논파|위증|동의|찬성|힌트|좌클릭|우클릭/.test(text),'No mechanical answer label in protagonist thought');
      report.loopThoughts??=[];if(!report.loopThoughts.includes(text)){report.loopThoughts.push(text);await p.capture(name+'-readable');await delay(1100);}
     }
    }
    await p.tap('Enter',1);actions++;
   }else await delay(30);continue;
  }
  if(!s.taskInputArmed||s.scenes?.loading||s.presentation?.nonstopIntro){await delay(20);continue;}
  if(!report.activeStageHeld){await p.sampled(12);await p.capture('active-stage');await delay(2200);report.activeStageHeld=true;continue;}
  if(task.stage.kind==='panic'&&!report.panicViewSnapshot){await p.capture('panic-active');report.panicViewSnapshot=true;}
  if(!wrongSent&&task.stage.kind==='spot'&&a.kind==='click'){
   wrongHP=s.trialHp;wrongSent=true;report.wrongRequested=true;await p.click(SPOT_RECT[0]+5,SPOT_RECT[1]+5);actions++;await delay(700);continue;
  }
  if(!wrongSent&&task.stage.kind==='choice'&&['key','click'].includes(a.kind)){
   wrongHP=s.trialHp;wrongSent=true;report.wrongRequested=true;if(task.stage.answer===0)await p.tap('s',1);await p.tap('Enter',1);actions++;await delay(700);continue;
  }
  if(!wrongSent&&task.stage.kind==='reasoning'&&['key','click'].includes(a.kind)){
   const q=task.stage.questions[0],correct=q.options.indexOf(q.answer);assert(correct>=0&&q.options.length>1);wrongHP=s.trialHp;wrongSent=true;report.wrongRequested=true;if(correct===0)await p.tap('s',1);await p.tap('Enter',1);actions++;await delay(700);continue;
  }
  if(task.stage.kind==='mindmine'&&arg('mine-wall','0')==='1'&&!report.mineWall&&['click','move','key'].includes(a.kind)){report.mineWall=await proveMineWall(p,work);continue;}
  if(task.stage.kind==='mindmine'&&s.mineV4?.covered===0&&s.mineV4.successTime<0&&!report.mineReadable){
   await p.tap('Space');await p.sampled(12);await p.capture('readable-object');
   const frame=JSON.parse(await fs.readFile(path.join(work,'readable-object.ui.json'),'utf8')),owner=frame.widgets.find(w=>w.nodes.some(n=>n.id==='MineQuestionText'));
   assert.equal(owner?.nodes.find(n=>n.id==='MineQuestionText').properties.visible,false);
   report.mineReadable={elapsedMS:Date.now()-recording.started,method:'Actual Space input hides the question strip before ordinary object selection'};await delay(2200);continue;
  }
  if(!wrongSent&&task.stage.kind==='climax'&&s.comicV4&&!s.comicV4.replay&&a.kind==='click'){
   const first=task.stage.slots[0],wrong=(first.candidates.findIndex(o=>o.id===first.answer)+1)%first.candidates.length;
   while((await p.stats()).comicV4.spread>0)await p.tap('q');
   while((await p.stats()).comicV4.stockPage>0)await p.tap('z');
   for(let n=0;n<8&&(await p.stats()).comicV4.stock!==wrong;n++)await p.tap('d');
   const now=await p.stats(),r=now.comicV4.slotRects[0];wrongHP=now.trialHp;wrongSent=true;report.wrongRequested=true;
   await p.click(r[0]+r[2]/2,r[1]+r[3]/2);actions++;continue;
  }
  if(!report.air&&task.stage.kind==='showdown'&&a.kind==='drag'){
   const trace=path.join(work,'impacts.jsonl'),before=(await fs.readFile(trace,'utf8').catch(()=>''));
   await p.move(630,690);await p.button(630,690,true);await p.move(650,690);await p.button(650,690,false);await delay(200);
   const after=await p.stats(),newRows=(await fs.readFile(trace,'utf8').catch(()=>'')).slice(before.length).trim().split('\n').filter(Boolean).map(JSON.parse);
   report.air={elapsedMS:Date.now()-recording.started,hpBefore:s.showdownV4.hp,hpAfter:after.showdownV4?.hp,redFlashAndShake:newRows.some(r=>r.shake?.remaining>0&&r.flashes?.some(f=>f.color[0]>.7&&f.color[1]<.1))};
   assert.equal(report.air.hpAfter,report.air.hpBefore,'Air swing reaction must not invent HP damage');assert(report.air.redFlashAndShake,'Air swing must visibly flash/shake through its actual miss cue');actions++;continue;
  }
  if(!wrongSent&&['person','bullet','vote'].includes(task.stage.kind)&&['key','click'].includes(a.kind)){
   wrongHP=s.trialHp;if(a.kind==='key'&&a.key==='Enter')await p.tap(task.stage.kind==='bullet'?'s':'d',1);await p.tap('Enter',1);wrongSent=true;report.wrongRequested=true;actions++;await delay(700);continue;
  }
  if(task.stage.kind==='armament'&&!report.wrong&&s.armamentV4?.final>=0){
   const arm=s.armamentV4;if(wrongHP===null)wrongHP=s.trialHp;
   wrongSent=true;report.wrongRequested=true;
   if(arm.selected<4){const used=arm.order||[];let index=arm.layout.findIndex(v=>!used.includes(v)&&v!==arm.selected);if(index<0)index=arm.layout.findIndex(v=>!used.includes(v));assert(index>=0);await p.tap(String(index+1),1);actions++;}else await p.sampled(3);
   continue;
  }
  if(a.kind==='debate'){
   const tr=s.trial;
   if(expectNoNoise&&tr){assert(tr.noise<0&&!(tr.noiseRows||[]).length,'Noise appeared before its introduction');report.noiseFreeSamples=(report.noiseFreeSamples||0)+1;}
   if(process.argv.includes('--observe-noise-contract')&&tr&&!report.noiseGap){
    if(!report.obstructionShot){
     if(!tr.turning&&tr.shotRecovery?.ready&&tr.answer&&tr.answer!=='decoy:none'&&tr.noiseBlockPoint){
      if(tr.bullet!==tr.answer){await p.tap(bulletCycleKey(options,tr.bullet,tr.answer),1);continue;}
      await p.capture('noise-over-weak-point');const fresh=await p.stats(),point=fresh.trial?.noiseBlockPoint;if(!point)continue;report.obstructionShot={index:fresh.trial.index,hp:fresh.trial.hp,blocked:fresh.trial.noiseBlockedShots,shots:fresh.trial.shots,started:Date.now()};await p.move(...point);await p.button(...point,true,tr.shotButton||'right');await p.button(...point,false,tr.shotButton||'right');
     }
     await delay(20);continue;
    }
    if(!report.obstruction){if(Date.now()-report.obstructionShot.started>2000&&!tr.shotInFlight&&tr.noiseBlockedShots===report.obstructionShot.blocked){assert.equal(tr.hp,report.obstructionShot.hp);delete report.obstructionShot;continue;}if(tr.noiseBlockedShots>report.obstructionShot.blocked&&!tr.shotInFlight){assert.equal(tr.hp,report.obstructionShot.hp);assert.equal(tr.index,report.obstructionShot.index);assert(!tr.clearing&&!s.taskQueue);report.obstruction={elapsedMS:Date.now()-recording.started,correctEvidenceBlocked:true,hp:tr.hp,index:tr.index};await p.capture('truth-bullet-stopped-by-noise');}await delay(20);continue;}
    if(tr.index===report.obstructionShot.index&&tr.noise<0&&tr.weakPoint){report.noiseGap={elapsedMS:Date.now()-recording.started,naturalExit:true,withoutSilencer:true,hp:tr.hp};await p.capture('natural-gap-before-refute');}await delay(20);continue;
   }
   if(process.argv.includes('--observe-partial-noise')&&tr&&(!report.partialNoise||!report.noiseRespawn)){
    if(!report.partialNoise){
     const row=(tr.noiseRows||[]).find(r=>r.durability>1),point=row&&(s.gpuNoiseHud?.modelPoints||[]).find(([, ,x,y,alpha,at])=>at===row.index&&alpha>.95&&x>200&&x<1080&&y>150&&y<520);
     if(point&&!tr.turning&&tr.shotRecovery?.ready){
      const before={hp:tr.hp,time:s.presentation.timer,damage:row.damage,silenced:tr.noiseSilenced};await p.move(point[2],point[3]);await (tr.noiseButton==='right'?p.rightClick(point[2],point[3]):p.click(point[2],point[3]));const after=await p.stats(),hit=after.trial?.noiseDamage?.[row.index];
      if(hit>before.damage){assert.equal(after.trial.hp,before.hp);if(hit<row.durability){assert.equal(after.trial.noiseSilenced,before.silenced);assert(after.presentation.timer<=before.time+.01);report.partialFirstHit={id:row.id,elapsedMS:Date.now()-recording.started,before,after:{hp:after.trial.hp,time:after.presentation.timer,damage:hit,debris:after.trial.noiseDebris}};await p.capture('partial-noise-outer-letters-broken');}else{assert(report.partialFirstHit);assert(after.presentation.timer>before.time+1.3);report.partialNoise={id:row.id,elapsedMS:Date.now()-recording.started,damage:hit,hp:after.trial.hp,timerBonus:after.presentation.timer-before.time};await p.capture('partial-noise-final-break');}}
     }
    }else if((tr.noiseRows||[]).some(r=>r.id===report.partialNoise.id&&r.damage===0)){report.noiseRespawn={elapsedMS:Date.now()-recording.started,id:report.partialNoise.id,damage:0};await p.capture('destroyed-noise-next-cycle');}
    await delay(25);continue;
   }
   if(process.argv.includes('--observe-buttons')&&!report.buttons&&tr&&!tr.turning&&tr.shotRecovery?.ready){
    const before=tr.shots,hp=tr.hp;await p.move(1240,610);await p.button(1240,610,true);await p.button(1240,610,true,'right');await p.sampled(1);await p.button(1240,610,false,'right');await p.button(1240,610,false);await delay(500);const after=await p.stats();
    assert.equal(after.trial.shots,before+1,'Overlapping silencer input must not swallow or duplicate a truth shot');assert.equal(after.trial.hp,hp,'Empty-space shot must not invent weak-point damage');report.buttons={before,after:after.trial.shots,hp,overlappingMouseButtons:true};continue;
   }
   if(process.argv.includes('--observe-focus')&&!report.focus&&tr&&!tr.turning&&tr.shotRecovery?.ready){
    const before=await p.stats(),at=Date.now();await p.key('Shift',true);await delay(800);const during=await p.stats();await p.capture('focus');await p.key('Shift',false);await delay(800);const after=await p.stats();focus=false;
    assert(during.trial.focus<before.trial.focus,'Concentration must consume mental gauge');assert(after.trial.focus>during.trial.focus,'Release must regenerate mental gauge');
    const wall=(Date.now()-at)/1000;assert(before.presentation.timer-during.presentation.timer<wall*.5,'Concentration must slow the countdown');report.focus={before:before.trial.focus,during:during.trial.focus,after:after.trial.focus,countdown:before.presentation.timer-during.presentation.timer};continue;
   }
   if(process.argv.includes('--observe-silencer')&&!report.silencer&&tr&&!tr.turning){
    const point=(s.gpuNoiseHud?.modelPoints||[]).find(p=>p[4]>.5&&p[2]>50&&p[2]<1230&&p[3]>50&&p[3]<620);
    if(point&&tr.shotRecovery?.ready){const plan=trialAimPlan([point[2],point[3]],await p.aim());if(plan.kind==='mouse'){
     const before=tr.noiseSilenced,hp=tr.hp;await p.move(...plan.point);await p.button(...plan.point,true,tr.noiseButton||'left');await delay(90);await p.button(...plan.point,false,tr.noiseButton||'left');const after=await p.stats();if(after.trial?.noiseSilenced>before){report.noise=true;report.silencer={elapsedMS:Date.now()-recording.started,before,after:after.trial.noiseSilenced,hpBefore:hp,hpAfter:after.trial.hp,debris:after.trial.noiseDebris};await p.capture('silencer-impact');assert.equal(after.trial.hp,hp);}
    }}await delay(20);continue;
   }
   if(observeFeedback&&tr){
    if(task.stage.kind!=='nonstop'&&tr.clearing&&tr.resultTime<=0&&!report.correctFeedback)report.correctFeedback=await captureFeedback('correct-feedback',tr.result==='agree'?'동의 성공':tr.result==='lie'?'위증 성공':'논파 성공');
    if(observeCycle&&!report.loopFeedback){
     const palette=tr.kind==='agree'?'blue':tr.kind==='weak'?'yellow':null;
     if(palette&&tr.weakPoint&&!tr.turning&&!report[palette]){report[palette]=true;await p.capture(palette,{pixels:false});}
     if(tr.noise>=0&&!tr.turning&&!report.noise&&(s.gpuNoiseHud?.modelPoints||[]).some(([, ,x,y])=>x>300&&x<900&&y>100&&y<550)){report.noise=true;await p.capture('noise',{pixels:false});}
     if(lastLine>tr.index){const file=await p.capture('cycle-return',{pixels:false});const snap=JSON.parse(await fs.readFile(file,'utf8'));const msg=snap.widgets.find(w=>w.instance==='main')?.nodes.find(n=>n.id==='TrialMsg');assert(!msg?.properties.visible||!msg.properties.text.includes('논의 한 바퀴'));report.loopFeedback={elapsedMS:Date.now()-recording.started,returnedToFirstRow:true,inventedMessageAbsent:true};}
     lastLine=tr.index;
     await delay(40);continue;
    }
   }
   if(process.argv.includes('--clear-noise')&&tr&&!tr.turning&&['weak','agree'].includes(tr.kind)&&tr.shotRecovery?.ready){
    const pink=(s.gpuNoiseHud?.modelPoints||[]).find(p=>p[4]>.5&&p[2]>40&&p[2]<1240&&p[3]>40&&p[3]<640);
    if(pink){const aim=trialAimPlan([pink[2],pink[3]],await p.aim());if(aim.kind==='mouse'){await p.move(...aim.point);await p.button(...aim.point,true,tr.noiseButton||'left');await delay(120);await p.button(...aim.point,false,tr.noiseButton||'left');continue;}}
   }
   if(!tr||tr.shotInFlight||!tr.answer||tr.answer==='decoy:none'||tr.clearing||tr.turning||tr.shotRecovery?.ready===false||!['weak','agree'].includes(tr.kind)||!tr.weakPoint){if(focus){await p.key('Shift',false);focus=false;}await delay(20);continue;}
   if(process.argv.includes('--prefer-agree')&&wrongSent&&tr.kind!=='agree'){await delay(20);continue;}
   const wrongBullet=options.find(id=>id!==tr.answer),want=!wrongSent&&wrongBullet?wrongBullet:tr.answer;
   if(tr.bullet!==want){await p.tap(bulletCycleKey(options,tr.bullet,want),1);actions++;continue;}
   if(!focus){await p.key('Shift',true);focus=true;await p.sampled(2);continue;}
   const plan=trialAimPlan(tr.weakPoint,await p.aim());
   if(plan.kind==='key'){await p.key(plan.key,true);await delay(plan.ms);await p.key(plan.key,false);await p.sampled(1);}
   else{
    await p.move(...plan.point);await p.button(...plan.point,true,tr.shotButton||'right');
    let release=plan.point;
    if(tr.needLie||(preferLie&&wrongSent&&tr.bullet===task.transformation.sourceEvidenceId)){
     const charged=await p.until(async()=>{const state=await p.stats();assert(!state.error,state.error);return state.trial?.lie?state:false;},'Held input transforms selected Kotodama',10000,25);
     if(preferLie){assert(charged.trial?.lie,'Held input must visibly transform the selected truth bullet');report.lieCharged=true;await p.capture('lie-charged',{pixels:false});}
     if(charged.trial?.weakPoint){const corrected=trialAimPlan(charged.trial.weakPoint,await p.aim());if(corrected.kind==='mouse'){release=corrected.point;await p.move(...release);}}
    }
    await p.button(...release,false,tr.shotButton||'right');
    if(observeFlight&&!report.projectile){
     const fired=await p.until(async()=>{
      const state=await p.stats();
      return state.trial?.shotInFlight&&state.trial.shots>tr.shots?state:false;
     },'actual projectile before judgment',1000,5);
     assert.equal(fired.trialHp,s.trialHp,'No judgment damage before projectile arrival');
     report.projectile={elapsedMS:Date.now()-recording.started,shots:fired.trial.shots,hpBeforeImpact:fired.trialHp};
    }
    if(!wrongSent&&wrongBullet){wrongHP=s.trialHp;report.wrongRequested=true;wrongSent=true;await delay(task.stage.kind==='nonstop'?420:160);}
   }
   actions++;continue;
  }
  if(focus){await p.key('Shift',false);focus=false;}
  if(a.kind==='key'||a.kind==='rapid-key'){await p.tap(a.key,1);actions++;await delay(a.kind==='rapid-key'?15:150);}
  else if(a.kind==='hold-key'||a.kind==='release-after'){await p.key(a.key,true);await delay(Math.max(1,(a.seconds??a.remaining)*1000));await p.key(a.key,false);actions++;}
  else if(a.kind==='hold-target'){await p.key(a.key,true);await delay(a.seconds*1000);await p.click(a.x,a.y);await p.key(a.key,false);actions++;}
  else if(a.kind==='click'){await p.click(a.x,a.y);actions++;await delay(150);}
  else if(a.kind==='move'){if(task.stage.kind==='mindmine')await p.rightClick(a.x,a.y);else await p.move(a.x,a.y);actions++;}
  else if(a.kind==='drag'||a.kind==='blade-drag'){
   const sd=task.stage.kind==='showdown',x0=sd?20:a.x0,x1=sd?1260:a.x1;
   if(sd)await p.key('d',true);if(a.kind==='blade-drag')await p.key('Space',true);await p.move(x0,a.y);await p.button(x0,a.y,true);await p.move(x1,a.y);await p.button(x1,a.y,false);if(a.kind==='blade-drag')await p.key('Space',false);if(sd)await p.key('d',false);actions++;
  }else await delay(30);
 }
 for(const k of ['Shift','Space','d'])await p.key(k,false);
 report.movie=await recording.finish();recording=null;report.actions=actions;
 assert(report.outcome&&report.returnNode&&report.returnReady,'A partial recording without actual success/return is not deliverable');
 if(preferLie)assert(report.lieCharged&&report.outcome?.judgment==='lie','Actual held input must take the authored lie route');
 if(process.argv.includes('--prefer-agree'))assert.equal(report.outcome?.judgment,'agree','Actual blue agreement route required');
 if(observeWhip)assert(report.cameraTurns?.length>=2,'Actual speaker changes must contain several intermediate camera poses');
 if(observeFlight)assert(report.projectile&&report.wrong?.hpAfter<report.projectile.hpBeforeImpact,'Visible flight must precede the wrong-shot HP change');
 if(observeFeedback)assert(report.correctFeedback&&report.wrong?.feedback,'Wrong and correct feedback must be visible');
 if(process.argv.includes('--observe-noise-contract'))assert(report.obstruction&&report.noiseGap,'Actual obstruction and natural clear gap required');
 if(process.argv.includes('--observe-partial-noise'))assert(report.partialFirstHit&&report.partialNoise&&report.noiseRespawn,'Partial damage, final break, and next-cycle respawn required');
 if(process.argv.includes('--observe-silencer')){assert(report.silencer,'Actual silencer impact required');report.noise=true;}
 if(process.argv.includes('--observe-loop-contract'))assert(report['nonstop-loop']?.restart&&report['nonstop-wrong']?.restart&&report.concurrentNoiseLate&&report.maxConcurrentNoise>=2,'Actual loop hint, wrong reaction, first-row restarts and concurrent late-life noise required');
 if(process.argv.includes('--observe-noise-coverage')){
  const main=task.debate.lines.filter(l=>l.kind!=='noise').length+(direction.extra?.[taskId]?.length||0);
  assert.equal(Object.keys(report.noiseCoverage||{}).length,main,'Every utterance needs an actual visible pink response');
 }
 if(observeCycle){assert(report.loopFeedback&&report.yellow&&(expectNoNoise?report.noiseFreeSamples>0:report.noise)&&(taskId[1]==='1'?!report.blue:report.blue),'Cycle, target colors and noise evidence required');assert(thoughtParts.every(text=>(report.loopThoughts||[]).some(actual=>compact(actual)===compact(text))),'Every authored thought sentence must be visibly readable');}
 if(report.wrongRequested)assert(report.wrong,'Requested wrong-input feedback must actually occur');
 report.runtime=await p.close();p=null;report.sequenceCompleted=true;
}catch(error){report.error=error.stack;report.last=await p?.stats().catch(()=>null);if(recording){report.partialMovie=await recording.finish().catch(e=>({error:e.message}));recording=null;}process.exitCode=1;}
finally{await p?.close().catch(e=>{report.shutdownError=e.message;process.exitCode=1;});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,taskId,sequenceCompleted:report.sequenceCompleted,accepted:report.accepted,error:report.error?.split('\n')[0]}));}
