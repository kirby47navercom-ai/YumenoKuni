// 재판 연출 확인 영상(Claude) : 저장 지점에서 모드에 들어가는 대사·연출부터 실제 게임 화면과 실제 게임 소리를 함께 녹화한다.
// node tools/record-trial-directions.mjs [--only=nonstop,scrum] [--seconds=40]   결과 : ../연출 영상/claude/<번호-이름>.mp4
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';import {promisify} from 'node:util';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {prepareTaskFixtures} from './native-task-fixtures.mjs';
import {trialAimPlan} from './v4-aim-test-input.mjs';
import {bulletCycleKey} from './v4-bullet-test-input.mjs';
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const exec=promisify(execFile),root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),out=path.join(repo,'연출 영상','claude');
const arg=(k,d)=>process.argv.find(a=>a.startsWith('--'+k+'='))?.slice(k.length+3)??d;
const only=arg('only','')?.split(',').filter(Boolean),seconds=Number(arg('seconds',300));
const build=JSON.parse(await fs.readFile(arg('build-result','')?path.resolve(arg('build-result','')):path.join(root,'build-result.json'),'utf8')); // Stats 녹화는 평평한(flat) 묶음만 된다
const work=path.join(root,'Saved/trial-directions-'+Date.now());await fs.mkdir(work,{recursive:true});await fs.mkdir(out,{recursive:true});
process.env.YUMENO_NATIVE_QA_RECORD='1';
// --module=<게임 C++ 모듈> : 전체 빌드가 막혔을 때 마지막 전체 빌드에 현재 C++ 만 바꿔 끼운다(build-game-glyph-module.mjs --current-source)
const moduleFile=arg('module','');
const prepared=await prepareTaskFixtures(build.output,work,{...(moduleFile?{gameModuleCandidate:path.resolve(moduleFile)}:{}),...(arg('content','')?{gameContentOverrides:path.resolve(arg('content',''))}:{})}); // 조준 정보(AimStats)까지 넣는 QA 묶음, --content=<바뀐 자원 목록 json>
const cases=JSON.parse(await fs.readFile(path.join(root,'Saved/native-task-checkpoints.json'),'utf8'));
const names={nonstop:'01-논스톱-논의',panic:'02-패닉-논의',showdown:'03-반론-쇼다운',scrum:'04-의논-스크럼',armament:'05-이론-무장',climax:'06-클라이맥스-추리',anagram:'07-섬광-애너그램',mindmine:'08-마인드-마인',vote:'09-투표',lie:'10-위증',person:'11-인물-지목',spot:'12-지점-지목',bullet:'13-증거-제시',choice:'14-정답-선택',reasoning:'15-추리-연결'};
const read=async f=>{try{return JSON.parse(await fs.readFile(f,'utf8'));}catch{return null;}};
const rows=[];
for(const name of Object.keys(names)){
 if(only.length&&!only.includes(name))continue;const row=cases[name];if(!row)continue;let p;
 try{
  p=await nativeWindowProbe({source:build.output,prepared,work:path.join(work,name),resume:path.resolve(repo,row.file),maxFrames:null,heartbeatTimeoutMs:120000,silent:false});
  await p.hiddenBorderless();await p.resize(Number(arg('w',960)),Number(arg('h',540)));await p.tap('c');
  await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.mode==='trial'&&s.taskId===row.task;},'saved '+name,120000);
  // 녹화는 구간(seg) 단위. 녹화 부하로 게임이 느려져 못 넘기는 스크럼 연타만 잠시 멈췄다가 이어 찍는다.
  const segs=[];let recOn=false;
  const startSeg=async()=>{const seg=name+'-'+segs.length;segs.push(seg);await fs.writeFile(path.join(p.work,'record.request'),JSON.stringify({name:seg,seconds,fps:Number(arg('fps',20)),stream:true,audio:true}),{flag:'wx'});recOn=true;};
  const stopSeg=async()=>{const f=path.join(p.work,'recordings',segs.at(-1),'recording.json');await fs.writeFile(path.join(p.work,'record.stop'),'1').catch(()=>{});const r=await p.until(()=>read(f),'stop '+segs.at(-1),60000,80);recOn=false;return r;};
  await startSeg();
  // 앞 : 들어가는 대사를 읽을 만큼(2초) 두고 넘긴다. 연출 : 게임이 주는 정답 조작(s.auto)으로 실제로 끝까지 푼다.
  // 뒤 : 끝난 뒤 이어지는 대사·화면을 after 초 동안 그대로 이어 찍고 멈춘다.
  const after=Number(arg('after',25)),started=Date.now();let lastTalk=0,focus=false,finished=0;
  const tasks=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks,task=tasks[row.task];
  for(;;){
   if(Date.now()-started>(seconds+30)*1000){console.log(name,'timeout: 끝까지 못 풀어 여기까지만 묶는다');break;}
   const s=await p.stats();assert(!s.error,s.error);
   if(!finished&&(s.lastTaskOutcome?.taskId===row.task||s.taskId!==row.task)){finished=Date.now();if(focus){await p.key('Shift',false);focus=false;}if(!recOn)await startSeg();}
   if(finished&&Date.now()-finished>after*1000)break;
   if(recOn&&s.scrum?.mash>=0&&!finished){await stopSeg();}
   if(!recOn&&!(s.scrum?.mash>=0)&&!finished)await startSeg();
   if(Date.now()-(globalThis.lastLog||0)>1000){globalThis.lastLog=Date.now();(globalThis.timeline??=[]).push({t:(Date.now()-started)/1000,mode:s.mode,task:s.taskId,queue:s.taskQueue,stage:s.stage?.kind,auto:s.auto,scrum:s.scrum??s.scrumV4,outcome:s.lastTaskOutcome?.taskId});}
   const a=s.auto||{kind:'none'},talk=s.taskQueue||a.kind==='key'&&a.key==='Enter'&&(s.mode!=='trial'||s.stage?.script||finished);
   if(talk){if(Date.now()-lastTalk>2000){lastTalk=Date.now();await p.tap(a.key||'Enter');}await delay(40);continue;}
   if(finished){if(Date.now()-lastTalk>2000){lastTalk=Date.now();await p.tap('Enter');}await delay(40);continue;}
   if(a.kind==='debate'){
    const tr=s.trial;if(!tr||tr.clearing||tr.turning||tr.shotRecovery?.ready===false||!['weak','agree'].includes(tr.kind)||!tr.weakPoint){if(focus){await p.key('Shift',false);focus=false;}await delay(30);continue;}
    if(tr.bullet!==tr.answer){const opts=(task?.stage?.options||[]).map(o=>o.id);await p.tap(opts.length?bulletCycleKey(opts,tr.bullet,tr.answer):'e');await delay(250);continue;}
    if(!focus){await p.key('Shift',true);focus=true;await p.sampled(2);continue;}
    const plan=trialAimPlan(tr.weakPoint,await p.aim());if(plan.kind==='key'){await p.key(plan.key,true);await delay(plan.ms);await p.key(plan.key,false);await p.sampled(1);}else{await p.move(...plan.point);await p.click(...plan.point);await delay(400);}
    continue;
   }
   if(focus){await p.key('Shift',false);focus=false;}
   if(s.scrum?.mash>=0&&a.kind==='key'){for(let i=0;i<(s.scrum.phase>=3?6:3);i++){await p.key(a.key,true);await delay(70);await p.key(a.key,false);await delay(60);}continue;} /* 스크럼 연타 : 방향이 6~10타 유지되므로 3타씩 */
   if(a.kind==='key'||a.kind==='rapid-key'){await p.tap(a.key,1);await delay(a.kind==='rapid-key'||s.scrum?.mash>=0?20:350);} /* 스크럼 연타는 바로바로 */
   else if(a.kind==='hold-key'||a.kind==='release-after'){await p.key(a.key,true);await delay(Math.max(1,(a.seconds??a.remaining)*1000));await p.key(a.key,false);await p.sampled(1);}
   else if(a.kind==='hold-target'){await p.key(a.key,true);await delay(a.seconds*1000);await p.click(a.x,a.y);await p.key(a.key,false);}
   else if(a.kind==='click'){await p.move(a.x,a.y);await delay(350);await p.click(a.x,a.y);await delay(350);}
   else if(a.kind==='move'){if(s.stage?.kind==='mindmine')await p.rightClick(a.x,a.y);else await p.move(a.x,a.y);await delay(120);}
   else if(a.kind==='drag'||a.kind==='blade-drag'){const sd=s.stage?.kind==='showdown',x0=sd?20:a.x0,x1=sd?1260:a.x1;if(sd)await p.key('d',true);if(a.kind==='blade-drag')await p.key('Space',true);await p.move(x0,a.y);await p.button(x0,a.y,true);await p.move(x1,a.y);await p.button(x1,a.y,false);if(a.kind==='blade-drag')await p.key('Space',false);if(sd)await p.key('d',false);await delay(200);}
   else await delay(30);
  }
  for(const k of ['Shift','Space','d'])await p.key(k,false);
  if(recOn)await stopSeg();else if(segs.length&&!(await read(path.join(p.work,'recordings',segs.at(-1),'recording.json'))))await stopSeg();
  await fs.writeFile(path.join(out,names[name]+'.timeline.json'),JSON.stringify(globalThis.timeline||[],null,0));globalThis.timeline=[];
  const parts=[];let frames=0,secs=0,peak=0,shakeFrames=0;
  for(const seg of segs){const r=await read(path.join(p.work,'recordings',seg,'recording.json'));if(!r?.frames?.length)continue;const wav=r.audioCapture?.file,part=path.join(p.work,seg+'.mp4');
   await exec('ffmpeg',['-hide_banner','-loglevel','error','-y','-i',r.video,...(wav?['-i',wav]:['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']),'-map','0:v','-map','1:a','-c:a','aac','-b:a','160k','-shortest','-c:v','copy',part],{windowsHide:true});
   parts.push(part);frames+=r.frames.length;secs+=r.frames.at(-1).elapsed;peak=Math.max(peak,r.audioCapture?.peak||0);shakeFrames+=r.frames.filter(f=>f.shake).length;}
  const video=path.join(out,names[name]+'.mp4'),list=path.join(p.work,'parts.txt');await fs.writeFile(list,parts.map(f=>"file '"+f.split(path.sep).join('/')+"'").join('\n'));
  await exec('ffmpeg',['-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',list,'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',video],{windowsHide:true});
  rows.push({name,video:path.relative(repo,video),segments:parts.length,frames,seconds:secs,fps:frames/(secs||1),audio:true,peak,shakeFrames,wall:(Date.now()-started)/1000});
  console.log(JSON.stringify(rows.at(-1)));
 }catch(error){await fs.writeFile(path.join(out,names[name]+'.timeline.json'),JSON.stringify(globalThis.timeline||[])).catch(()=>{});globalThis.timeline=[];rows.push({name,error:error.message});console.log(name,'FAIL',error.message);}
 finally{await p?.close().catch(()=>{});}
}
await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify({build:build.id,rows},null,2));console.log(out);
