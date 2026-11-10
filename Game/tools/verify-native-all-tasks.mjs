// Every authored task must reach its actual success through physical Win32 input.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {prepareTaskFixtures} from './native-task-fixtures.mjs';
import {trialAimPlan} from './v4-aim-test-input.mjs';
import {bulletCycleKey} from './v4-bullet-test-input.mjs';
import {caseSaveCatalogue,publishCaseSave} from './native-case-saves.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
import {createHash} from 'node:crypto';
import {publishPresentationAssets} from './native-presentation-assets.mjs';
import {proveMineWall} from './native-mine-wall-proof.mjs';
import {nonstopProof} from './native-nonstop-proof.mjs';
import {proveLieHud} from './native-nonstop-lie-hud-proof.mjs';
import {proveAgreementCast} from './native-agreement-cast-proof.mjs';
const root=path.resolve(import.meta.dirname,'..'),build=JSON.parse(await fs.readFile(process.argv.find(v=>v.startsWith('--build-result='))?.slice(15)||path.join(root,'build-result.json'),'utf8')),tasks=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/native_tasks.json'),'utf8')).tasks;
const arg=prefix=>process.argv.find(a=>a.startsWith(prefix))?.slice(prefix.length),resume=arg('--resume='),only=arg('--only=')?.split(','),minimumHours=Number(arg('--hours=')||0),desiredJudgment=arg('--judgment='),stabilityProof=arg('--stability-proof=');
const work=resume?path.resolve(resume):path.join(root,'Saved/native-all-tasks-'+Date.now());await fs.mkdir(work,{recursive:true});
const prior=await fs.readFile(path.join(work,'progress.json'),'utf8').then(JSON.parse,()=>null);if(prior)assert.equal(prior.build,build.id,'Changed builds require an explicit evidence inheritance decision');
const firstKinds=[...new Map(Object.entries(tasks).map(([id,t])=>[t.stage.kind,id])).values()];
const results=prior?.results||[],passed=new Set(results.filter(r=>r.ok&&(!desiredJudgment||r.outcome?.judgment===desiredJudgment)).map(r=>r.taskId)),ids=[...new Set(only||['T3-NS-A11',...firstKinds,...Object.keys(tasks)])].filter(id=>tasks[id]&&!passed.has(id));
const reused=arg('--reuse-package=');let prepared;
if(reused){const output=path.resolve(root,reused);assert(output.startsWith(path.join(root,'Saved/native-panic-views-')),'Reuse only the owned presentation QA package');const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));assert(!manifest.contentArchive);if(arg('--game-module=')){const from=path.resolve(root,arg('--game-module=')),relative=manifest.nativeModules[0].binary,target=path.resolve(output,relative);assert(from.startsWith(path.join(root,'Saved')+path.sep)&&target.startsWith(output+path.sep));const bytes=await fs.readFile(from);await fs.writeFile(target+'.tasks.tmp',bytes);await fs.rename(target+'.tasks.tmp',target);Object.assign(manifest.files.find(r=>r.path===relative),{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));}prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)};await fs.writeFile(path.join(work,'reuse-receipt.json'),JSON.stringify({output,newPackageCreated:false,sourcePackageModified:false,shipping:false}));}
else prepared=await fs.access(path.join(work,'package/game.hbpack.json')).then(async()=>{const manifest=JSON.parse(await fs.readFile(path.join(work,'package/game.hbpack.json'),'utf8'));return {output:path.join(work,'package'),manifest,executable:path.join(work,'package',manifest.windowsApplication.executable)};},()=>prepareTaskFixtures(build.output,work,{gameModuleCandidate:arg('--game-module=')}));
const testedModuleSHA256=createHash('sha256').update(await fs.readFile(path.join(prepared.output,prepared.manifest.nativeModules[0].binary))).digest('hex');await fs.writeFile(path.join(work,'tested-module.json'),JSON.stringify({sha256:testedModuleSHA256,binary:prepared.manifest.nativeModules[0].binary,base:build.id},null,2));
const session=path.join(work,'session-'+Date.now()),started=Date.now(),delay=ms=>new Promise(r=>setTimeout(r,ms));let probe;const catalogue=await caseSaveCatalogue();
const fullNonstop=process.argv.includes('--nonstop-proof'),lieHudProof=process.argv.includes('--nonstop-lie-hud-proof'),direction=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/trial_direction.json'),'utf8'));const lieHud=[];
const mineExpectedCounts=new Map();
if(process.argv.includes('--mine-object-proof')){
 const bank=path.resolve(root,'../art/v4_production/mine_objects_20261104');
 for(const row of JSON.parse(await fs.readFile(path.join(bank,'banks.json'),'utf8'))){
  const s=JSON.parse(await fs.readFile(path.join(bank,row.selection),'utf8')),source=tasks[s.taskId].stage;
  if(s.mergeCorrectRegions){assert.deepEqual(source.regions.filter(r=>r.correct).map(r=>r.id).sort(),[...s.mergeCorrectRegions].sort());assert.equal(s.objects.filter(o=>o.regionId===source.answerRegionId).length,1);assert.equal(s.objects.length,source.regions.length-s.mergeCorrectRegions.length+1);}
  else assert.equal(s.objects.length,source.regions.length);
  mineExpectedCounts.set(s.taskId,s.objects.length);
 }
}
if(arg('--candidate-assets=')){assert(reused,'Candidate assets require the single owned QA package');const receipt=await publishPresentationAssets(root,prepared.output,prepared.manifest,arg('--candidate-assets=').split(','));await fs.writeFile(path.join(work,'candidate-assets.json'),JSON.stringify(receipt,null,2));}
const resizeSequence=(arg('--resize-sequence=')||'').split(',').filter(Boolean).map(value=>{assert(/^\d+x\d+$/.test(value));return value.split('x').map(Number);});
const save=async extra=>fs.writeFile(path.join(work,'progress.json'),JSON.stringify({build:build.id,work,session,elapsedSeconds:(Date.now()-started)/1000,passed:results.filter(r=>r.ok).length,totalAuthored:Object.keys(tasks).length,results,...extra},null,2));
const json=async file=>{for(let i=0;i<5;i++){try{return JSON.parse(await fs.readFile(path.join(session,file),'utf8'));}catch(e){if(i===4)throw e;await delay(5);}}};
try{
 probe=await nativeWindowProbe({source:build.output,work:session,prepared,maxFrames:null,heartbeatTimeoutMs:120000});
 const width=Number(arg('--width=')||prepared.manifest.width),height=Number(arg('--height=')||prepared.manifest.height);assert(Number.isInteger(width)&&Number.isInteger(height));if(arg('--width=')||arg('--height=')){await probe.hiddenBorderless();const viewport=await probe.resize(width,height);assert.deepEqual(viewport,[width,height]);await fs.writeFile(path.join(work,'viewport.json'),JSON.stringify({width,height,visible:false,build:build.id}));}
 for(const taskId of ids){
  const t=tasks[taskId],begin=Date.now();let entry,last,actions=0,focus=false,captured=false,objectCaptured=false;const armUI={phases:{},captures:[]};const resultPhases=new Set(),proof=fullNonstop&&t.stage.kind==='nonstop'?nonstopProof(taskId,t,direction,process.argv.includes('--noise-ink-proof')?stem=>json(stem+'.ui.json'):null):null;
  try{
   for(const k of ['Control','Shift','Space','w','d','s','a'])await probe.key(k,false);
   if((await probe.stats()).mode!=='title'){
    await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);return !s.scenes?.loading&&!s.routeBlocked;},'finish authored scene transition before opening Pad',120000);await probe.sampled(12);await probe.tap('Tab');if((await probe.stats()).mode!=='pad'){await probe.sampled(12);await probe.tap('Tab');}await probe.until(async()=>(await probe.stats()).mode==='pad','Pad between cases');await probe.click(1047,480);assert.equal((await probe.stats()).padPage,5);await padSystemAction(probe.stats,probe.tap,'title');await padSystemAction(probe.stats,probe.tap,'title_yes');await probe.until(async()=>(await probe.stats()).mode==='title','own title between cases');
   }
   const checkpoint=await publishCaseSave({work,session,catalogue,taskId});
   // Re-read title availability after publishing an isolated entry save.
   await probe.tap('s',1);await probe.tap('w',1);
   await probe.tap('c');entry=await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);return s.taskId===taskId?s:false;},'authored task Continue '+taskId,120000);await probe.tap('F2');await probe.key('Control',!fullNonstop);
   const owned=new Set(checkpoint.evidence),available=(t.stage.options||[]).filter(o=>!t.stage.filterOwnedEvidence||owned.has(o.id)).map(o=>o.id),bullets=t.stage.kind==='nonstop'?direction.nonstopAmmo[taskId].filter(id=>owned.has(id)||available.includes(id)):available;
   while(Date.now()-begin<(proof?420000:300000)){
    const s=last=await probe.stats();assert(!s.error,s.error);assert(!s.routeBlocked,'authored route is blocked');
    if(proof)await proof.observe(s,probe);
    if(s.node!==entry.node&&s.lastTaskOutcome?.taskId===taskId){assert(actions>0);assert(s.lastTaskOutcome.target);break;}
    if(desiredJudgment&&s.trial?.resultTime>0&&!resultPhases.has('nonstop-result')){await delay(1800);await probe.capture(taskId.toLowerCase()+'-'+desiredJudgment+'-result');if(process.argv.includes('--agreement-cast-proof')){assert.equal(desiredJudgment,'agree');const actor=t.debate.lines.find(r=>r.kind==='agree')?.actor;assert(actor);const evidence=await proveAgreementCast(probe,taskId,actor);await fs.writeFile(path.join(session,taskId.toLowerCase()+'-agreement-pair-proof.json'),JSON.stringify(evidence,null,2));}resultPhases.add('nonstop-result');continue;}
    if(process.argv.includes('--armament-ui-proof')&&t.stage.kind==='armament'&&s.armamentV4){const arm=s.armamentV4,key=String(arm.phase),points=armUI.phases[key]??=[];for(const n of arm.notes||[]){const p=[n.x,n.y];if(!points.some(q=>q[0]===p[0]&&q[1]===p[1]))points.push(p);}if(arm.hud&&arm.intro<0&&(arm.notes||[]).length&&!resultPhases.has('arm-ui-'+key)){resultPhases.add('arm-ui-'+key);const name=taskId.toLowerCase()+'-source-ui-phase-'+key;await probe.capture(name);armUI.captures.push(name);}}
    if(s.taskQueue){await probe.tap('Enter',1);actions++;continue;}
    if(process.argv.includes('--solution-cutin-proof')&&s.solutionV4?.frame>=0){const frame=s.solutionV4.frame;for(const [name,lo,hi]of [['ink-start',16,20],['ink-growing',21,28],['ink-word',35,100]])if(frame>=lo&&frame<=hi&&!resultPhases.has(name)){await probe.capture(taskId.toLowerCase()+'-'+name);resultPhases.add(name);break;}await delay(5);continue;}
    if(!s.taskInputArmed||s.presentation?.nonstopIntro||s.scenes?.loading){await delay(20);continue;}
    if(process.argv.includes('--solution-cutin-proof')&&t.stage.kind==='anagram'&&s.anagramV4?.filled>=Array.from(t.stage.answer||'').length&&!resultPhases.has('solution-fullscreen')){await delay(1100);await probe.capture(taskId.toLowerCase()+'-solution-fullscreen');resultPhases.add('solution-fullscreen');continue;}
    if(process.argv.includes('--solution-cutin-proof')&&t.stage.kind==='mindmine'&&s.mineV4?.successTime>=2.9&&s.mineV4.successTime<3.45&&!resultPhases.has('solution-fullscreen')){await probe.capture(taskId.toLowerCase()+'-solution-fullscreen');resultPhases.add('solution-fullscreen');continue;}
    if(t.stage.kind==='mindmine'&&s.mineV4?.successTime>=0){const phase=s.mineV4.successPhase;if(s.mineV4.successTime>=.9&&s.mineV4.successTime<1.1&&!resultPhases.has('mine-selected')){resultPhases.add('mine-selected');await probe.capture(taskId.toLowerCase()+'-mine-result-selected');}else if(s.mineV4.successTime>=1.55&&phase===1&&!resultPhases.has(phase)){resultPhases.add(phase);await probe.capture(taskId.toLowerCase()+'-mine-result-korean');}else if(phase>=2&&phase<=3&&!resultPhases.has(2)){resultPhases.add(2);await probe.capture(taskId.toLowerCase()+'-mine-result-break');}await probe.sampled(2);continue;}
    if(t.stage.kind==='mindmine'&&taskId===(arg('--mine-object-task=')||'T2-MM-A02')&&process.argv.includes('--mine-object-proof')&&s.mineV4?.covered===0&&s.mineV4.successTime<0&&!objectCaptured){
     await probe.move(640,360);await probe.button(640,360,true);await probe.button(640,360,false);await probe.sampled(60);await probe.capture(taskId.toLowerCase()+'-mine-objects-revealed');const ui=await json(taskId.toLowerCase()+'-mine-objects-revealed.ui.json'),stage=ui.widgets.find(w=>w.instance==='stage'),objects=stage.nodes.filter(n=>/^MineObject\d+$/.test(n.id)&&n.properties.visible);assert.equal(objects.length,mineExpectedCounts.get(taskId));const cursor=ui.widgets.find(w=>w.instance==='minehudv4').nodes.find(n=>n.id==='MineCursor');assert(cursor.properties.visible);assert.deepEqual(cursor.slot.offset,[600,320,80,80]);assert.equal(stage.nodes.find(n=>n.id==='MineBg').properties.visible,false);assert(objects.every(n=>n.properties.texture.startsWith('Assets/Art/mine_objects/')));assert.equal(new Set(objects.map(n=>JSON.stringify(n.slot.offset))).size,objects.length);await fs.writeFile(path.join(session,taskId.toLowerCase()+'-mine-object-poses.json'),JSON.stringify(objects.map(n=>({id:n.id,texture:n.properties.texture,rotation:n.properties.rotation,rect:n.slot.offset})),null,2));objectCaptured=true;
    }
    if(objectCaptured&&!resultPhases.has('question-toggle')&&t.stage.kind==='mindmine'){
     const before=await json(taskId.toLowerCase()+'-mine-objects-revealed.ui.json');
     const owner=before.widgets.find(w=>w.nodes.some(n=>n.id==='MineQuestionText'));assert(owner,'Mine question widget owner must exist');
     assert.equal(owner.nodes.find(n=>n.id==='MineQuestionText').properties.visible,false);
     await probe.tap('Space');await probe.sampled(12);const name=taskId.toLowerCase()+'-mine-question-shown';await probe.capture(name);
     const snapshot=await json(name+'.ui.json'),widget=snapshot.widgets.find(w=>w.instance===owner.instance);
     assert.equal(widget.nodes.find(n=>n.id==='MineQuestionText').properties.visible,true);
     assert.equal(widget.nodes.find(n=>n.id==='MineQuestionPlate').properties.visible,true);
     await probe.tap('Space');await probe.sampled(3);resultPhases.add('question-toggle');
    }
    // Entry snapshots previously caught an unpainted mine board and the first
    // dark-orb animation frame. Let the unchanged game render before evidence.
    if(!captured){await probe.sampled(120);const ready=await probe.stats();assert(!ready.error,ready.error);if(ready.scenes?.loading)continue;}
    if(!captured&&t.stage.kind==='mindmine'&&process.argv.includes('--mine-wall-proof')){await probe.until(async()=>{const m=(await probe.stats()).mineV4;return m&&m.time<18000&&m.paint===m.width*m.height;},'Mine board enters timed play',15000);}
    if(!captured){if(resizeSequence.length){await probe.hiddenBorderless();const checks=[];for(const [width,height]of resizeSequence){assert.deepEqual(await probe.resize(width,height),[width,height]);await probe.move(640,360);await probe.button(640,360,true);let aim;try{aim=await probe.until(async()=>{const a=await probe.aim();assert(Array.isArray(a.physical)&&a.physical.length===2);return Math.abs(a.physical[0]-640)<1&&Math.abs(a.physical[1]-360)<1?a:false;},'Resized pointer must retain canvas coordinates',10000);}finally{await probe.button(640,360,false);}actions+=2;const name='resize-'+width+'x'+height;await probe.capture(name);const ui=await json(name+'.ui.json');assert.equal(ui.width,width);assert.equal(ui.height,height);checks.push({width,height,physical:aim.physical,capture:name});}await fs.writeFile(path.join(work,'resize-input-'+taskId+'.json'),JSON.stringify(checks,null,2));}await probe.capture('task-'+taskId.toLowerCase());captured=true;if(t.stage.kind==='mindmine'&&process.argv.includes('--mine-wall-proof'))await proveMineWall(probe,session);}
    if(proof?.observing){await delay(35);continue;}
    const a=s.auto;
    if(a.kind==='debate'){
     const tr=s.trial;if(!s.presentation?.inputArmed){await delay(20);continue;}
     if(t.stage.kind==='panic'&&process.argv.includes('--clear-noise')&&tr?.noise>=0){
      const pink=(s.gpuNoiseHud?.panicPoints||[]).find(([,x,y,,opacity])=>opacity>.65&&x>40&&x<1240&&y>40&&y<640);
      if(pink){await probe.rightClick(pink[1],pink[2]);actions++;continue;}
     }
     if(!tr||tr.clearing||tr.turning||tr.shotRecovery?.ready===false||!tr.answer||(tr.answer==='decoy:none'&&!proof?.wrongNeeded)||!['weak','agree'].includes(tr.kind)||!tr.weakPoint){if(focus){await probe.key('Shift',false);focus=false;}await delay(12);continue;}
     if(proof||process.argv.includes('--clear-noise')){const pink=(s.gpuNoiseHud?.modelPoints||[]).find(p=>p[4]>.9&&p[2]>40&&p[2]<1240&&p[3]>40&&p[3]<640);if(pink){await (tr.noiseButton==='right'?probe.rightClick(pink[2],pink[3]):probe.click(pink[2],pink[3]));actions++;continue;}}
     if(desiredJudgment==='agree'&&!proof?.wrongNeeded&&tr.kind!=='agree'){await delay(15);continue;}
     const targetBullet=proof?.wrongNeeded?bullets.find(id=>id!==tr.answer):desiredJudgment==='lie'?t.transformation.sourceEvidenceId:tr.answer;
     if(tr.bullet!==targetBullet){await probe.tap(bulletCycleKey(bullets,tr.bullet,targetBullet));actions++;continue;}
     if(!focus){await probe.key('Shift',true);focus=true;await probe.sampled(2);continue;}
     const plan=trialAimPlan(tr.weakPoint,await probe.aim());if(plan.kind==='key'){await probe.key(plan.key,true);await delay(plan.ms);await probe.key(plan.key,false);await probe.sampled(1);}else{await probe.move(...plan.point);if(desiredJudgment==='lie'){let release=plan.point;await probe.button(...release,true,tr.shotButton||'right');try{const charged=await probe.until(async()=>{const state=await probe.stats();assert(!state.error,state.error);return state.trial?.lie?state:false;},'Actual held input transforms the bullet',10000,25);if(lieHudProof&&!resultPhases.has('lie-hud-charge')){lieHud.push({taskId,...await proveLieHud(probe,taskId,t.transformation.lieLabel,'charge')});resultPhases.add('lie-hud-charge');await fs.writeFile(path.join(work,'lie-hud.json'),JSON.stringify(lieHud,null,2));}const latestCharged=await probe.stats();if(latestCharged.trial?.weakPoint){const corrected=trialAimPlan(latestCharged.trial.weakPoint,await probe.aim());if(corrected.kind==='mouse'){release=corrected.point;await probe.move(...release);}}}finally{await probe.button(...release,false,tr.shotButton||'right');}if(lieHudProof&&!resultPhases.has('lie-hud-flight')){const flying=await probe.until(async()=>{const aim=await probe.aim();return aim.projectile?.phase==='word'?aim:false;},'Actual transformed word flight',2000,5);lieHud.push({taskId,...await proveLieHud(probe,taskId,flying.projectile.label,'flight')});resultPhases.add('lie-hud-flight');await fs.writeFile(path.join(work,'lie-hud.json'),JSON.stringify(lieHud,null,2));}}else{await probe.button(...plan.point,true,tr.shotButton||'right');if(tr.needLie)await delay(Math.ceil((tr.chargeRequired??.45)*1000)+100);await probe.button(...plan.point,false,tr.shotButton||'right');}}actions++;continue;
    }
    if(focus){await probe.key('Shift',false);focus=false;}
    if(a.kind==='sd-slash'){await probe.move(a.x,a.y);await delay(80);if(a.blade){await probe.rightClick(a.x,a.y);await delay(250);const fresh=(await probe.stats()).auto||a;await probe.click(fresh.kind==='sd-slash'?fresh.x:a.x,fresh.kind==='sd-slash'?fresh.y:a.y);}else await probe.click(a.x,a.y);actions++;}
    else if(a.kind==='key'||a.kind==='rapid-key'){if(a.key==='mouse0')await probe.click(640,360);else await probe.tap(a.key,1);actions++;}
    else if(a.kind==='hold-key'||a.kind==='release-after'){await probe.key(a.key,true);await delay(Math.max(1,(a.seconds??a.remaining)*1000));await probe.key(a.key,false);await probe.sampled(1);actions++;}
    else if(a.kind==='hold-target'){await probe.key(a.key,true);await delay(a.seconds*1000);await probe.click(a.x,a.y);await probe.key(a.key,false);actions++;}
    else if(a.kind==='click'){await probe.click(a.x,a.y);actions++;}
    else if(a.kind==='move'){if(t.stage.kind==='mindmine')await probe.rightClick(a.x,a.y);else await probe.move(a.x,a.y);actions++;}
    else if(a.kind==='drag'||a.kind==='blade-drag'){
     const showdown=s.stage.kind==='showdown',x0=showdown?20:a.x0,x1=showdown?1260:a.x1;
     if(showdown)await probe.key('d',true);if(a.kind==='blade-drag')await probe.key('Space',true);await probe.move(x0,a.y);await probe.button(x0,a.y,true);
     await probe.move(x1,a.y);await probe.button(x1,a.y,false);if(a.kind==='blade-drag')await probe.key('Space',false);if(showdown)await probe.key('d',false);actions++;
    }else await delay(a.scale!==undefined?4:16);
    if(actions%25===0)await save({active:{taskId,kind:t.stage.kind,seconds:(Date.now()-begin)/1000,actions,auto:a,mine:s.mineV4,taskLink:s.taskLink}});
   }
   if(process.argv.includes('--armament-ui-proof')&&t.stage.kind==='armament'){const ps=Object.values(armUI.phases);assert(ps.length>=3,'Actual authored armament phases observed');assert(ps.every(p=>p.length>=2),'UI metadata must use multiple real source positions in every phase');await fs.writeFile(path.join(session,taskId.toLowerCase()+'-source-ui-proof.json'),JSON.stringify(armUI,null,2));}
   assert(last.node!==entry.node&&last.lastTaskOutcome?.taskId===taskId,'Task success timeout '+taskId);if(desiredJudgment){assert.equal(last.lastTaskOutcome.judgment,desiredJudgment);const route=Object.values(t.outcomes).find(o=>o.judgment===desiredJudgment);if(route){assert.equal(last.lastTaskOutcome.target,route.to);assert.deepEqual(last.lastTaskOutcome.sets,route.sets||{});}}const row={taskId,kind:t.stage.kind,ok:true,seconds:(Date.now()-begin)/1000,actions,outcome:last.lastTaskOutcome,checkpoint:checkpoint,gameModuleSHA256:testedModuleSHA256,nonstopProof:proof?.finish(),scope:'Actual Win32 gameplay success from the identified real checkpoint or explicit reachable-state entry fixture. No current task success injection.'};results.push(row);passed.add(taskId);await save();console.log(JSON.stringify({taskId,ok:true,kind:row.kind,passed:passed.size,seconds:row.seconds}));
  }catch(error){results.push({taskId,kind:t.stage.kind,ok:false,error:error.stack,actions,last});await save();await probe.capture('failure-'+taskId.toLowerCase()).catch(()=>{});throw error;}
 }
 for(const k of ['Control','Shift','Space'])await probe.key(k,false);
 let reusedStability=null;
 while(Date.now()-started<minimumHours*3600000){
  if(stabilityProof){const p=path.resolve(root,stabilityProof);assert(p.startsWith(path.join(root,'Saved')+path.sep));const proof=await fs.readFile(p,'utf8').then(JSON.parse,()=>null);if(proof?.ok&&proof.build===build.id&&proof.continuousSeconds>=minimumHours*3600){reusedStability={file:p,continuousSeconds:proof.continuousSeconds};break;}}
  await probe.tap('Tab');await probe.sampled(60);await probe.tap('Tab');await delay(10000);await save({soak:{requestedHours:minimumHours,telemetry:await json('telemetry.json')}});
 }
 const runtime=await probe.close();probe=null;await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,build:build.id,work,results,passed:passed.size,totalAuthored:Object.keys(tasks).length,completeAuthoredCoverage:passed.size===Object.keys(tasks).length,selection:{only,desiredJudgment},wallSeconds:(Date.now()-started)/1000,reusedStability,runtime,scope:'Actual Win32 input for isolated authored task fixtures. No task success injection, altered game timers or original source/save modifications. A natural campaign route and every narrative choice are separate evidence. A separate same-build reviewed stability proof can satisfy only the optional soak wait, never task outcomes.'},null,2));await save({closed:true});console.log(JSON.stringify({ok:true,work,passed:passed.size}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,results,session},null,2));throw error;}finally{await probe?.close().catch(()=>{});}
