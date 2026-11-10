// 반론 쇼다운 직접 실행 확인(Claude 2026-11-05) : 녹화 없이 실제 속도로 과제를 띄워 게임이 주는 정답 조작(s.auto)으로 끝까지 풀고,
// 단계가 바뀔 때마다 그 순간의 게임 화면을 찍는다. 결과 : Saved/claude-scrum-check/<과제>/<단계>.png + result.json
// node tools/claude-showdown-check.mjs --tasks=T1-RS-01,... --build-result=... --module=... [--content=...]
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {prepareTaskFixtures} from './native-task-fixtures.mjs';
import {caseSaveCatalogue,publishCaseSave} from './native-case-saves.mjs';
const delay=ms=>new Promise(r=>setTimeout(r,ms)),root=path.resolve(import.meta.dirname,'..');
const arg=(k,d)=>process.argv.find(a=>a.startsWith('--'+k+'='))?.slice(k.length+3)??d;
const build=JSON.parse(await fs.readFile(path.resolve(arg('build-result','build-result.json')),'utf8'));
const work=path.join(root,'Saved/claude-scrum-check-work-'+Date.now()),outRoot=path.join(root,'Saved/claude-scrum-check');await fs.mkdir(work,{recursive:true});
let content='';if(arg('content','')){const o=JSON.parse(await fs.readFile(path.resolve(arg('content','')),'utf8'));for(const [k,v] of Object.entries(o))if(!await fs.access(v).then(()=>true,()=>false))delete o[k];content=path.join(work,'content.json');await fs.writeFile(content,JSON.stringify(o));} /* 다른 작업이 생성 파일을 바꿔도 없는 파일은 빼고 묶음 원본을 쓴다 */
const prepared=await prepareTaskFixtures(build.output,work,{...(arg('module','')?{gameModuleCandidate:path.resolve(arg('module',''))}:{}),...(content?{gameContentOverrides:content}:{})});
const catalogue=await caseSaveCatalogue(),tasks=arg('tasks','').split(',').filter(Boolean),limit=Number(arg('seconds',240)),results=[];
for(const task of tasks){
 const key=task.toLowerCase(),out=path.join(outRoot,task);await fs.mkdir(out,{recursive:true});let p,shots=[],res={task,ok:false};
 try{
  p=await nativeWindowProbe({source:build.output,prepared,work:path.join(work,key),maxFrames:null,heartbeatTimeoutMs:120000});
  await p.hiddenBorderless();await p.resize(1280,720);
  await publishCaseSave({work,session:p.work,catalogue,taskId:task});await p.tap('s');await p.tap('w');await p.tap('c');
  await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.mode==='trial'&&s.taskId===task;},'task '+task,120000);
  const seen=new Set(),shot=async label=>{if(seen.has(label))return;seen.add(label);const f=await p.capture((key+'-'+label).replace(/[^a-z0-9_-]/g,'-'));await fs.copyFile(f,path.join(out,label+'.png'));shots.push(label);};
  const started=Date.now();let lastTalk=0,lastShot=0,n=0;
  for(;;){
   if(Date.now()-started>limit*1000){res.why='시간 초과';await shot('z-timeout');break;}
   const s=await p.stats();assert(!s.error,s.error);const a=s.auto||{kind:'none'};
   if(s.lastTaskOutcome?.taskId===task||s.taskId!==task){res.ok=true;await delay(400);await shot('zz-after');break;}
   if(Date.now()-lastShot>Number(arg('every',2500))){lastShot=Date.now();await shot(String(n++).padStart(3,'0'));}
   const talk=s.taskQueue||a.kind==='key'&&a.key==='Enter'&&s.mode!=='trial';
   if(talk){if(Date.now()-lastTalk>700){lastTalk=Date.now();await p.tap('Enter');}await delay(30);continue;}
   if(a.kind==='rapid-key'){await p.tap(a.key==='mouse0'?'Enter':a.key,1);await delay(40);}
   else if(a.kind==='key'){let k=a.key;if(arg('wrong','')&&!res.wrongDone&&k==='s'&&(res.sCount=(res.sCount||0)+1)>=Number(arg('wrong','1'))){k='Enter';res.wrongDone=true;}await p.tap(k,1);await delay(160);} /* --wrong=1 : 첫 합에서 일부러 틀린 아군을 고른다 */
   else if(a.kind==='click'){await p.click(a.x,a.y);await delay(200);}
   else await delay(30);
  }
 }catch(e){res.why=String(e.message||e).split(/\r?\n/).filter(x=>!x.includes('QA snapshot')).join(' | ').slice(0,3000);}
 finally{if(p)await p.close().catch(()=>{});}
 res.shots=shots.length;results.push(res);console.log(JSON.stringify(res));
}
