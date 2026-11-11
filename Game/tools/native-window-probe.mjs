// Real targeted Win32 input and read-only Stats; no browser/CDP/debug outcome calls.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import readline from 'node:readline';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {pathToFileURL} from 'node:url';
import {createOwnedNativePackage,importLegacySaveForQA} from './native-owned-package.mjs';
const delay=ms=>new Promise(r=>setTimeout(r,ms)),exec=promisify(execFile);
export function canvasClientPoint([x,y],[width,height],[referenceWidth,referenceHeight]){
 assert([x,y,width,height,referenceWidth,referenceHeight].every(Number.isFinite)&&x>=0&&y>=0&&width>0&&height>0&&referenceWidth>0&&referenceHeight>0);const scale=Math.min(width/referenceWidth,height/referenceHeight),point=[Math.round(x*scale),Math.round(y*scale)];assert(point.every(v=>v>=0&&v<32768));return point;
}
export async function nativeWindowProbe({source,work,candidate,rendererCandidate,resume,prepared,legacyOnly=false,heartbeatTimeoutMs=20000,maxFrames=36000,sparse=false,unprofiled=false,visible=false,silent=true}){
 await fs.mkdir(work,{recursive:true});
 const owned=prepared||await createOwnedNativePackage({source,work,candidate,rendererCandidate,stats:!sparse}),state=path.join(work,'State');
 const imported=resume&&!legacyOnly?await importLegacySaveForQA(resume,state,owned.manifest.id):null;
 if(resume&&legacyOnly){await fs.mkdir(state,{recursive:true});await fs.copyFile(resume,path.join(state,'savegames.json'),fs.constants.COPYFILE_EXCL);}
 if(imported)await fs.writeFile(path.join(work,'save-import.json'),JSON.stringify(imported,null,2));
 const env={...process.env,HB_NATIVE_TEST_STATE:state,YUMENO_NATIVE_QA_DIR:work,YUMENO_NATIVE_QA_SPARSE:sparse?'1':'0',NODE_OPTIONS:'--import='+pathToFileURL(path.join(import.meta.dirname,'native-ui-capture.mjs')).href};
 for(const k of ['HB_USER_DATA_DIR','HB_PLAYER_ACCEPTANCE','HB_PLAYER_SMOKE','WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'])delete env[k];
 assert(!unprofiled||sparse,'Unprofiled probe requires sparse external telemetry');
 const reportFile=path.join(work,'runtime.json'),child=spawn(owned.executable,[...(visible?[]:['--hidden']),...(silent?['--silent']:[]),...(maxFrames===null?[]:['--frames',String(maxFrames)]),...(unprofiled?[]:['--report',reportFile])],{cwd:work,env,windowsHide:!visible,stdio:['ignore','pipe','pipe']});let output='',ended=false;
 child.stdout.on('data',b=>output+=b);child.stderr.on('data',b=>output+=b);
 const done=new Promise((resolve,reject)=>{child.once('error',reject);child.once('close',(code,signal)=>{ended=true;resolve({code,signal});});});
 const controller=spawn('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',path.join(import.meta.dirname,'native-window-input.ps1')],{windowsHide:true,stdio:['pipe','pipe','pipe']});let serial=1,handle;const pending=new Map();let controllerErrors='';controller.stderr.on('data',b=>controllerErrors+=b);
 readline.createInterface({input:controller.stdout}).on('line',line=>{try{const result=JSON.parse(line),r=pending.get(result.id);if(r){pending.delete(result.id);clearTimeout(r.timer);result.ok?r.resolve(result.value):r.reject(Error(result.error));}}catch{}});
 const command=data=>new Promise((resolve,reject)=>{const id=serial++,timer=setTimeout(()=>{pending.delete(id);reject(Error('Owned input response timeout '+controllerErrors));},10000);pending.set(id,{resolve,reject,timer});controller.stdin.write(JSON.stringify({...data,id,pid:child.pid,handle})+'\n');});
 const statsFile=path.join(work,sparse?'frame-heartbeat.json':'stats.json');
 const snapshot=async()=>{for(let i=0;i<20;i++){try{return JSON.parse(await fs.readFile(statsFile,'utf8'));}catch(e){if(i===19||!(e instanceof SyntaxError)&&!['ENOENT','EPERM','EBUSY'].includes(e.code))throw e;await delay(25);}}};
 let healthSequence=-1,healthChanged=Date.now(),healthChecked=0;
 const stats=async()=>{assert(!sparse,'Sparse baseline has no per-frame game Stats');const row=await snapshot(),now=Date.now();if(row.sequence!==healthSequence){healthSequence=row.sequence;healthChanged=now;}else if(now-healthChanged>2000&&now-healthChecked>1000){healthChecked=now;const log=await fs.readFile(path.join(state,'native-runtime.log'),'utf8').catch(()=>'');if(/^Error:|^script exit [1-9]/m.test(log))throw Error('Owned native runtime failed: '+log);}return row.stats;};
 const until=async(fn,label,ms=20000,pollMs=30)=>{const start=Date.now();let last;while(Date.now()-start<ms){if(ended)throw Error('Native exited early: '+output+' '+await fs.readFile(path.join(state,'native-runtime.log'),'utf8').catch(()=>''));try{const value=await fn();if(value)return value;}catch(e){last=e;}await delay(pollMs);}throw Error(label+' timeout '+(last?.message||''));};
 const aim=()=>until(async()=>{const value=JSON.parse(await fs.readFile(path.join(work,'aim.json'),'utf8'));return value?.physical&&value?.desired?value:false;},'complete aiming snapshot',2000,4);
 const sampled=async(count=2)=>{const first=(await snapshot()).sequence;await until(async()=>(await snapshot()).sequence>=first+count,'native frame heartbeat',heartbeatTimeoutMs,4);};
 const post=(message,w=0,l=0)=>command({op:'post',message,w,l});
 const vk={Enter:13,Space:32,Tab:9,Escape:27,Backspace:8,Control:17,Shift:16,ArrowLeft:37,ArrowUp:38,ArrowRight:39,ArrowDown:40};
 const key=async(name,down)=>{const value=vk[name]??(/^F(?:[1-9]|1[0-9]|2[0-4])$/.test(name)?111+Number(name.slice(1)):name.toUpperCase().charCodeAt(0));assert(Number.isInteger(value)&&value>0&&value<=255);await post(down?0x100:0x101,value,down?1:0xc0000001);};
 const tap=async(name,frames=2)=>{await key(name,true);await sampled(frames);await key(name,false);await sampled(frames);};
 const coordinates=async(x,y)=>{const[px,py]=canvasClientPoint([x,y],await command({op:'size'}),[owned.manifest.width,owned.manifest.height]);return (py<<16)|px;};
 const move=async(x,y)=>{await post(0x200,0,await coordinates(x,y));await sampled();};
 const click=async(x,y)=>{await move(x,y);const l=await coordinates(x,y);await post(0x201,1,l);await sampled(3);await post(0x202,0,l);await sampled(3);};
 const rightClick=async(x,y)=>{await move(x,y);const l=await coordinates(x,y);await post(0x204,2,l);await sampled(3);await post(0x205,0,l);await sampled(3);};
 // Sparse telemetry reports once a second. Short physical inputs should not
 // require three telemetry periods; callers still wait for observed UI state.
 const tapMS=async(name,ms=90)=>{assert(Number.isInteger(ms)&&ms>=80&&ms<=1000);await key(name,true);await delay(ms);await key(name,false);await delay(ms);};
 const clickMS=async(x,y,ms=90)=>{assert(Number.isInteger(ms)&&ms>=80&&ms<=1000);const l=await coordinates(x,y);await post(0x200,0,l);await post(0x201,1,l);await delay(ms);await post(0x202,0,l);await delay(ms);};
 const button=async(x,y,down,side='left')=>{assert(side==='left'||side==='right');const right=side==='right';await post(right?(down?0x204:0x205):(down?0x201:0x202),down?(right?2:1):0,await coordinates(x,y));await sampled();};
 const wheel=async(x,y,delta)=>{assert(Number.isInteger(delta)&&Math.abs(delta)<=16);await move(x,y);const l=await coordinates(x,y);await command({op:'wheel',delta,x:l&0xffff,y:(l>>>16)&0xffff});await sampled();};
 const capture=async(name,{pixels=true}={})=>{assert(/^[a-z0-9_-]{1,64}$/.test(name));const request=path.join(work,'capture.request'),snapshot=path.join(work,name+'.ui.json'),previous=await fs.stat(snapshot).then(s=>s.mtimeMs,()=>null);await fs.writeFile(request,pixels?name:'snapshot:'+name,{flag:'wx'});await until(async()=>{const stamp=await fs.stat(snapshot).then(s=>s.mtimeMs,()=>null);return stamp!==null&&stamp!==previous&&await fs.access(request).then(()=>false,()=>true);},'fresh native capture',40000);return pixels?path.join(work,name+'.png'):snapshot;};
 let closePromise;const close=()=>closePromise??(closePromise=(async()=>{const closeStarted=Date.now();let forced=false;try{if(!ended){if(handle)await post(0x10);let graceTimer;try{await Promise.race([done,new Promise(resolve=>{graceTimer=setTimeout(resolve,30000);})]);}finally{clearTimeout(graceTimer);}if(!ended){forced=true;await exec('taskkill.exe',['/PID',String(child.pid),'/T','/F'],{windowsHide:true});}}const exit=await done;await fs.writeFile(path.join(work,'shutdown.json'),JSON.stringify({exitCode:exit.code,forced,graceMS:30000,elapsedMS:Date.now()-closeStarted}));await fs.writeFile(path.join(work,'process-output.txt'),output);assert.equal(exit.code,0,output);if(unprofiled){const log=await fs.readFile(path.join(state,'native-runtime.log'),'utf8').catch(()=>'');assert(!/^Error:|^script exit [1-9]/m.test(log),log);return {unprofiled:true,exitCode:exit.code,scope:'No --report/profile instrumentation. External frame heartbeat/UI capture only; no native renderer/audio summary claim.'};}const report=JSON.parse(await fs.readFile(reportFile,'utf8'));assert.equal(report.webview,false);assert.deepEqual(report.audio.errors,[]);return report;}finally{controller.stdin.end();for(const r of pending.values()){clearTimeout(r.timer);r.reject(Error('Owned controller closed'));}pending.clear();}})());
 try{await until(async()=>handle=await command({op:'find'}),'own native window',30000);await until(async()=>await fs.access(unprofiled?statsFile:reportFile+'.ready.json').then(()=>true,()=>false),'first physical frame',120000);if(!sparse)await until(async()=>{const s=await stats();return s.mode==='title';},'actual game title Stats',30000);else await until(async()=>await snapshot(),'actual sparse frame heartbeat',30000);}catch(e){await close().catch(()=>{});throw e;}
 return {work,child,windowHandle:()=>handle,imported,stats,aim,frameSample:snapshot,until,sampled,key,tap,tapMS,move,click,clickMS,rightClick,button,wheel,capture,close,viewport:()=>command({op:'size'}),display:()=>command({op:'display'}),resources:()=>command({op:'resources'}),windowState:()=>command({op:'state'}),focus:()=>command({op:'focus'}),hiddenBorderless:()=>command({op:'hidden-borderless'}),resize:async(width,height)=>{await command({op:'resize',width,height});await sampled();return command({op:'size'});}};
}
