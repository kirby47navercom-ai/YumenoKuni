// Record compositor frames from our isolated game; no screenshot/Stats polling in the recording loop.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/nonstop-recording-'+Date.now());await fs.mkdir(work,{recursive:true});
const wait=ms=>new Promise(r=>setTimeout(r,ms));let probe,socket;
process.env.HB_PLAYER_SOAK_HOURS='1';
try{
 probe=await editorWindowProbe({work,mode:'player',executable:built.executable});
 await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 for(const type of ['keyDown','keyUp']){await probe.cdp('Input.dispatchKeyEvent',{type,key:'t',code:'KeyT',windowsVirtualKeyCode:84});await wait(90);}
 const data=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/trials/11c.json'),'utf8')),index=data.stages.findIndex(s=>s.kind==='nonstop');
 const jump=()=>probe.evaluate(`window.hbPlayerDebug.call('Driver','Yumeno.DebugJump',{index:${index}})`);
 const stats=()=>probe.evaluate(`window.hbPlayerDebug.call('Driver','Yumeno.Stats',{}).then(r=>JSON.parse(r.outputs.result))`);
 await jump();const initial=await stats();await wait(initial.presentation.duration*1000+250);
 const targets=await(await fetch(`http://127.0.0.1:${probe.debuggingPort}/json/list`)).json();
 const target=targets.find(t=>t.type==='page'&&new URL(t.url).origin===probe.base);assert(target);
 socket=new WebSocket(target.webSocketDebuggerUrl);await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j;});
 let serial=0,start=Infinity;const pending=new Map(),frames=[];
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
 socket.onmessage=({data})=>{
  const m=JSON.parse(data);
  if(m.id){const p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}return;}
  if(m.method==='Page.screencastFrame'){
   const p=m.params;socket.send(JSON.stringify({id:++serial,method:'Page.screencastFrameAck',params:{sessionId:p.sessionId}}));
   if(p.metadata.timestamp>=start)frames.push({timestamp:p.metadata.timestamp,bytes:Buffer.from(p.data,'base64')});
  }
 };
 await send('Page.enable');await send('Page.startScreencast',{format:'jpeg',quality:85,maxWidth:960,maxHeight:540,everyNthFrame:1});
 start=Date.now()/1000;await jump();await wait(initial.presentation.duration*1000+350);await send('Page.stopScreencast');
 const final=await stats();assert.equal(final.presentation.nonstopIntro,false);assert(!final.error);assert.equal(probe.errors.length,0);assert(frames.length>75);
 const recorded=[];
 for(let i=0;i<frames.length;i++){
  const file=`frame-${String(i).padStart(4,'0')}.jpg`;await fs.writeFile(path.join(work,file),frames[i].bytes);recorded.push({file,elapsed:frames[i].timestamp-start});
 }
 const measuredFps=(frames.length-1)/(frames.at(-1).timestamp-frames[0].timestamp);
 const concat=['ffconcat version 1.0'];
 for(let i=0;i<recorded.length;i++){
  concat.push(`file '${recorded[i].file}'`);
  concat.push(`duration ${Math.max(.001,(recorded[i+1]?.elapsed??recorded[i].elapsed+1/measuredFps)-recorded[i].elapsed).toFixed(6)}`);
 }
 concat.push(`file '${recorded.at(-1).file}'`);
 await fs.writeFile(path.join(work,'frames.ffconcat'),concat.join('\n')+'\n');
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({executable:built.executable,frames:recorded,measured_capture_fps:measuredFps,duration:initial.presentation.duration,final,scope:'actual compositor captures of own game; recording frame rate is not the separate uncaptured performance result'},null,2));
 console.log(JSON.stringify({work,frames:frames.length,captureFps:measuredFps}));
}finally{socket?.close();await probe?.stop?.();}
