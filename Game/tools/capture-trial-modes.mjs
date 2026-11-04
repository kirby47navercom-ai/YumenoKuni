// 재판 모드 연출 확인(Claude) : 저장 지점에서 모드를 열고, 들어가는 연출부터 일정 간격으로 화면을 찍는다.
// node tools/capture-trial-modes.mjs --only=nonstop,showdown [--frames=16] [--every=6]   (결과 : Saved/trial-modes-*/<모드>/)
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const arg=(k,d)=>process.argv.find(a=>a.startsWith('--'+k+'='))?.slice(k.length+3)??d;
const only=arg('only','nonstop').split(','),frames=Number(arg('frames',16)),every=Number(arg('every',6));
const work=path.join(root,'Saved/trial-modes-'+Date.now());await fs.mkdir(work,{recursive:true});
// --sparse : 빌드가 리소스 묶음(game.hbdata)이라 상태값(Stats) 주입이 안 될 때. 시간 기준으로 넘기며 찍는다
const sparse=process.argv.includes('--sparse'),enters=Number(arg('enters',0)),wait=Number(arg('wait',600));
const prepared=await createOwnedNativePackage({source:build.output,work,stats:!sparse});
const cases=JSON.parse(await fs.readFile(path.join(root,'Saved/native-task-checkpoints.json'),'utf8'));
// --resume=<저장 파일> --keys=Tab,ArrowRight,… : 아무 저장 지점에서 키를 하나씩 누르며 찍는다(수첩·ESC·탐색 화면 확인용)
const resumeFile=arg('resume','');if(resumeFile){cases.custom={file:resumeFile,task:''};only.splice(0,only.length,'custom');}
const keys=arg('keys','').split(',').filter(Boolean);
for(const kind of only){
 const row=cases[kind];if(!row){console.log('no checkpoint',kind);continue;}
 let probe;
 try{
  probe=await nativeWindowProbe({source:build.output,work:path.join(work,kind),prepared,resume:path.resolve(repo,row.file),sparse});await probe.tap('c');
  if(sparse){let n=0;const shot=async()=>{await probe.capture('f'+String(n++).padStart(2,'0'));};await probe.sampled(wait);for(const k of keys){await shot();await probe.tap(k);await probe.sampled(45);}for(let i=0;i<enters;i++){await shot();await probe.tap('Enter');await probe.sampled(30);}for(let i=0;i<frames;i++){await shot();await probe.sampled(every);}console.log(kind,'frames',n);continue;}
  await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);return s.mode==='trial'&&s.taskId===row.task?s:false;},'saved '+kind,60000);
  // 들어가는 대사부터 찍는다 : 대사는 Enter 로 넘기며 사이사이 찍는다
  let n=0;const shot=async()=>{await probe.capture('f'+String(n++).padStart(2,'0'));};
  for(let i=0;i<60;i++){const s=await probe.stats();if(!s.taskQueue)break;await shot();await probe.tap('Enter');}
  for(let i=0;i<frames;i++){await shot();await probe.sampled(every);}
  console.log(kind,'frames',n);
 }catch(error){console.log(kind,'FAIL',error.message);await probe?.capture('failure').catch(()=>{});}
 finally{await probe?.close().catch(()=>{});}
}
console.log(work);
