// 반론 쇼다운 직접 실행 확인(Claude 2026-11-05) : 녹화 없이 실제 속도로 과제를 띄워 게임이 주는 정답 조작(s.auto)으로 끝까지 풀고,
// 단계가 바뀔 때마다 그 순간의 게임 화면을 찍는다. 결과 : Saved/claude-sd-check/<과제>/<단계>.png + result.json
// node tools/claude-showdown-check.mjs --tasks=T1-RS-01,... --build-result=... --module=... [--content=...]
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {prepareTaskFixtures} from './native-task-fixtures.mjs';
import {caseSaveCatalogue,publishCaseSave} from './native-case-saves.mjs';
const delay=ms=>new Promise(r=>setTimeout(r,ms)),root=path.resolve(import.meta.dirname,'..');
const arg=(k,d)=>process.argv.find(a=>a.startsWith('--'+k+'='))?.slice(k.length+3)??d;
const build=JSON.parse(await fs.readFile(path.resolve(arg('build-result','build-result.json')),'utf8'));
const work=path.join(root,'Saved/claude-sd-check-work-'+Date.now()),outRoot=path.join(root,'Saved/claude-sd-check');await fs.mkdir(work,{recursive:true});
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
  const started=Date.now();let lastTalk=0,advT=0,playT=0,lastKey='';
  for(;;){
   if(Date.now()-started>limit*1000){res.why='시간 초과';const s=await p.stats().catch(()=>({}));res.last={sd:s.showdownV4,stats:Object.keys(s),auto:s.auto,queue:s.taskQueue,mode:s.mode};await shot('z-timeout');break;}
   const s=await p.stats();assert(!s.error,s.error);const sd=s.showdownV4||{},a=s.auto||{kind:'none'};{const k=[sd.phase,sd.group,sd.entry,sd.hp,sd.retries,sd.inScript,sd.playing,sd.talk,sd.restart,a.kind,!!s.taskQueue].join('|');if(k!==lastKey){lastKey=k;res.log=(res.log||[]).concat(((Date.now()-started)/1000).toFixed(1)+' '+k+' rem='+Math.round(sd.remaining)+' intro='+(+sd.intro).toFixed(2));}}
   if(s.lastTaskOutcome?.taskId===task||s.taskId!==task){res.ok=true;await delay(400);await shot('9-after');break;}
   if(sd.intro>0.3&&sd.intro<2.2)await shot('0-cutin');
   if(s.taskQueue&&sd.intro>=2.6&&sd.intro<2.7)await shot('1-pre');
   if(sd.intro>=5.2&&sd.intro<6)await shot('2-title');
   if(sd.intro>=9&&sd.intro<11)await shot('3-list');
   if(sd.intro<0&&sd.phase===0){if(!playT)playT=Date.now();if(Date.now()-playT>1500)await shot('4-play');if(Date.now()-playT>6000)await shot('5-play2');}
   if(sd.phase===3){if(!advT)advT=Date.now();if(Date.now()-advT>300)await shot('6-advance');if(Date.now()-advT>2600)await shot('7-talk');}
   if(sd.group>=1&&sd.phase===0&&a.blade)await shot('8-blade');
   if(sd.decoy&&sd.phase===0){if(!res.decoyAt)res.decoyAt=Date.now();if(Date.now()-res.decoyAt>1500)await shot('8-decoy');}res.blades=sd.blades;res.decoys=Math.max(res.decoys||0,0)+(sd.decoy&&sd.statement!==res._ds?1:0);if(sd.decoy)res._ds=sd.statement;
   const talk=s.taskQueue||a.kind==='key'&&a.key==='Enter'&&s.mode!=='trial';
   if(talk){if(Date.now()-lastTalk>700){lastTalk=Date.now();await p.tap('Enter');}await delay(30);continue;}
   if(a.kind==='rapid-key'){await p.click(640,370);await delay(25);}
   else if(a.kind==='key'){await p.tap(a.key,1);await delay(120);}
   else if(a.kind==='sd-slash'){await p.move(a.x,a.y);await delay(40);if(a.blade){await delay(250);await p.rightClick(a.x,a.y);await delay(700);await shot('8-alert');let tx=a.x,ty=a.y;{const s2=await p.stats(),b=s2.auto||{};if(b.kind==='sd-slash'){tx=b.x;ty=b.y;await p.move(tx,ty);await delay(250);}}await p.click(tx,ty);await delay(500);await shot('8-break');}else await p.click(a.x,a.y);}
   else await delay(20);
  }
 }catch(e){res.why=String(e.message||e).slice(0,300);}
 finally{if(p)await p.close().catch(()=>{});}
 res.shots=shots;results.push(res);console.log(JSON.stringify(res));
}
await fs.writeFile(path.join(outRoot,'result.json'),JSON.stringify(results,null,1));
