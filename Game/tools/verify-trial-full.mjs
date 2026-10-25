// 1장 학급 재판 전 단계(27) 자동 진행 검증 : 게임이 알려 주는 정답 입력(Stats.auto)을 실제 키·마우스 이벤트로 넣는다.
// 단계마다 첫 화면을 캡처한다. node tools/verify-trial-full.mjs  (결과 : Saved/verification-full/)
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,process.argv[2]==='2'?'Saved/verification-full2':'Saved/verification-full');await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const KEYS={y:[89,'KeyY'],Enter:[13,'Enter'],' ':[32,'Space'],e:[69,'KeyE'],q:[81,'KeyQ'],a:[65,'KeyA'],d:[68,'KeyD'],t:[84,'KeyT'],Shift:[16,'ShiftLeft'],1:[49,'Digit1'],2:[50,'Digit2'],3:[51,'Digit3'],4:[52,'Digit4']};
// 플레이어 --smoke-test 는 180초 뒤 스스로 끝난다(엔진 수락 모드). 긴 검증은 소크 시간으로 늘린다.
process.env.HB_PLAYER_SOAK_HOURS??='3';
let probe;
try{
 probe=await editorWindowProbe({work,mode:'player',executable:built.executable});
 await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'player ready',60000);
 const t00=Date.now();const wd=setInterval(()=>{if(probe.ended){console.log('ENDED',((Date.now()-t00)/1000).toFixed(1),JSON.stringify(probe.ended),JSON.stringify(probe.errors).slice(0,1500));clearInterval(wd);}},300);wd.unref();
 const stats0=async()=>JSON.parse((await probe.evaluate('window.hbPlayerDebug.call("Driver","Yumeno.Stats",{})')).outputs.result);
 const stats=async()=>{try{return await stats0();}catch(e){
  console.log('HANG',e.message);await delay(3000);console.log('ENDED',JSON.stringify(probe.ended),JSON.stringify(probe.errors).slice(0,1500));
  try{
   const targets=await(await fetch('http://127.0.0.1:'+probe.debuggingPort+'/json/list')).json();
   const t=targets.find(x=>x.type==='page');const ws=new WebSocket(t.webSocketDebuggerUrl);let id=0;
   const got=new Promise((res,rej)=>{ws.onmessage=ev=>{const m=JSON.parse(ev.data);if(m.method==='Debugger.paused')res(m.params);};setTimeout(()=>rej(Error('no pause')),20000);});
   await new Promise(r=>ws.onopen=r);ws.send(JSON.stringify({id:++id,method:'Debugger.enable'}));ws.send(JSON.stringify({id:++id,method:'Debugger.pause'}));
   const p=await got;console.log('STACK');for(const f of p.callFrames.slice(0,25))console.log(' ',f.functionName||'(anon)',f.url.split('/').slice(-2).join('/'),f.location.lineNumber+1,f.location.columnNumber);
  }catch(x){console.log('diag fail',x.message);}
  throw e;}};
 const key=async(k,type)=>{const [vk,code]=KEYS[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode:vk});};
 const tap=async k=>{await key(k,'keyDown');await delay(60);await key(k,'keyUp');await delay(60);};
 const move=async(x,y)=>{await probe.cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x,y});await delay(30);};
 const press=async(x,y,type)=>probe.cdp('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1});
 const click=async(x,y,hold=60)=>{await move(x,y);await press(x,y,'mousePressed');await delay(hold);await press(x,y,'mouseReleased');await delay(60);};
 const drag=async(x0,x1,y)=>{await move(x0,y);await press(x0,y,'mousePressed');for(let i=1;i<=6;i++){await move(x0+(x1-x0)*i/6,y);}await press(x1,y,'mouseReleased');await delay(60);};
 const which=process.argv[2]==='2'?'y':'t';await delay(800);await tap(which);await delay(500);
 if(process.argv[3])await probe.evaluate(`window.hbPlayerDebug.call("Driver","Yumeno.DebugJump",{index:${Number(process.argv[3])}})`);await delay(500);
 const seen=new Map(),log=[];let last=-1,steps=0,focused=false,lastErr='';
 while(steps++<6000){
  const t0=Date.now();const s=await stats();const dt=Date.now()-t0;if(steps%100===0)console.log('mem',dt,s.stage?.index,await probe.evaluate('JSON.stringify({heap:Math.round(performance.memory.usedJSHeapSize/1e6),dom:document.getElementsByTagName("*").length,img:document.images.length,canv:document.getElementsByTagName("canvas").length})'));
  if(s.error&&s.error!==lastErr){lastErr=s.error;console.log('GAME ERROR',s.error,JSON.stringify(s.stage));}
  if(s.mode!=='trial')break;
  const st=s.stage;
  if(st.index!==last){last=st.index;log.push({index:st.index,kind:st.kind,hearts:st.hearts});console.log('stage',st.index,st.kind);if(!seen.has(st.kind)){seen.set(st.kind,st.index);await delay(['panic','scrum','armament','vote'].includes(st.kind)?2500:500);try{await probe.capture(`${String(st.index).padStart(2,'0')}-${st.kind}.png`);}catch(e){console.log('capture skipped',st.kind,e.message);}}}
  const a=s.auto;
  if(a.kind==='debate'){
   const t=s.trial;
   if(!t||t.clearing||t.turning||t.kind!=='weak'||!t.weakPoint){if(focused){await key('Shift','keyUp');focused=false;}await delay(40);continue;}
   if(t.bullet!==t.answer){await tap('e');continue;}
   if(!focused){await key('Shift','keyDown');focused=true;await delay(80);continue;}
   await click(...t.weakPoint,t.needLie?700:40);
  }else{
   if(focused){await key('Shift','keyUp');focused=false;}
   if(a.kind==='key')await tap(a.key);
   else if(a.kind==='click')await click(a.x,a.y);
   else if(a.kind==='drag')await drag(a.x0,a.x1,a.y);
   else await delay(a.kind==='wait'&&a.scale!==undefined?8:40);
  }
 }
 const end=await stats();
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({end:end.mode,steps,log,kinds:[...seen.keys()]},null,1));
 assert.equal(end.mode,'title','27단계를 모두 지나 재판이 끝남 (마지막 : '+JSON.stringify(log.at(-1))+')');
 assert(log.length>=(process.argv[2]==='2'?29:27),'단계 수 '+log.length);
 console.log(JSON.stringify({ok:true,stages:log.length,kinds:[...seen.keys()],steps},null,1));
}finally{await Promise.race([probe?.close?.(),delay(8000)]);try{(await import('node:child_process')).execSync('taskkill /F /FI "IMAGENAME eq HBGame*"',{stdio:'ignore'});}catch{}process.exit(process.exitCode??0);}
