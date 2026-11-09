// 본편 자동 진행 검증 : 새 게임 → 장 진행(대본·프리타임·선물·수사·재판·처형·막간)을 게임이 알려 주는 입력(Stats.auto)으로 끝까지.
// node tools/verify-flow.mjs [시작 장 0~6] [끝 장 0~6]  (결과 : Saved/verification-flow/)
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const runtime=JSON.parse(await fs.readFile(path.join(path.dirname(built.executable),'game.hbpack.json'),'utf8')).windowsRuntime;
assert.notEqual(runtime,'native','This Legacy flow runner requires WebView/CDP. Use the Win32 native QA tools; do not count this as native gameplay acceptance.');
const from=Number(process.argv[2]||0),to=Number(process.argv[3]??6);
// 선택/수사/미니게임은 실제 입력으로 진행하고, 대사만 기존 Control 스킵을 선택적으로 사용한다.
const fastStory=process.env.HB_VERIFY_FAST_STORY==='1';
// Preserve proof and saves. The move-only build-retention tool handles closed caches.
const work=path.join(root,'Saved/verification-flow-'+Date.now().toString(36));await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const KEYS={Control:[17,'ControlLeft'],Tab:[9,'Tab'],Backspace:[8,'Backspace'],w:[87,'KeyW'],s:[83,'KeyS'],m:[77,'KeyM'],g:[71,'KeyG'],y:[89,'KeyY'],o:[79,'KeyO'],Enter:[13,'Enter'],' ':[32,'Space'],e:[69,'KeyE'],q:[81,'KeyQ'],a:[65,'KeyA'],d:[68,'KeyD'],t:[84,'KeyT'],Shift:[16,'ShiftLeft'],1:[49,'Digit1'],2:[50,'Digit2'],3:[51,'Digit3'],4:[52,'Digit4']};
// 플레이어 --smoke-test 는 180초 뒤 스스로 끝난다(엔진 수락 모드). 긴 검증은 소크 시간으로 늘린다.
process.env.HB_PLAYER_SOAK_HOURS??='3';
let probe,lastState;
try{
 probe=await editorWindowProbe({work,mode:'player',executable:built.executable});
 await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'player ready',60000);
 const stats=async()=>JSON.parse((await probe.evaluate('window.hbPlayerDebug.call("Driver","Yumeno.Stats",{})')).outputs.result);
 const key=async(k,type)=>{const [vk,code]=KEYS[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode:vk});};
 const tap=async k=>{await key(k,'keyDown');await delay(60);await key(k,'keyUp');await delay(60);};
 const move=async(x,y)=>{await probe.cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x,y});await delay(30);};
 const press=async(x,y,type)=>probe.cdp('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1});
 const click=async(x,y,hold=60)=>{await move(x,y);await press(x,y,'mousePressed');await delay(hold);await press(x,y,'mouseReleased');await delay(60);};
 const drag=async(x0,x1,y)=>{await move(x0,y);await press(x0,y,'mousePressed');for(let i=1;i<=6;i++){await move(x0+(x1-x0)*i/6,y);}await press(x1,y,'mouseReleased');await delay(60);};
 await delay(800);
 if(fastStory)await probe.evaluate('window.hbPlayerDebug.call("Driver","Yumeno.DebugFastRead",{})'); // Explicit QA pacing, separate from source settings.
 for(let k=0;k<20&&(await stats()).mode==='title';k++){await tap('Enter');await delay(500);}
 if(from>0)await probe.evaluate(`window.hbPlayerDebug.call("Driver","Yumeno.DebugChapter",{index:${from}})`);await delay(500);
 const beats=new Map();
 const seen=new Map(),seenLines=new Set(),seenModes=new Set(),log=[];let padShot=false;let last=-1,steps=0,beatAt=Date.now(),focused=false,lastSig='',stall=0,skipping=false;
 while(steps++<200000){
  const t0=Date.now();const s=await stats();const dt=Date.now()-t0;lastState=s;
  if(s.error){console.log('GAME ERROR',s.error);break;}
  if(skipping&&s.mode!=='story'&&!(s.mode==='trial'&&s.stage?.script)){await key('Control','keyUp');skipping=false;}
  if(s.mode==='title'||s.chapter>to)break;
  {const sig=JSON.stringify([s.mode,s.chapter,s.beat,s.event,s.stage,s.trial?.index,s.trial?.broken]);if(sig===lastSig){if(++stall>3000){console.log('STALL',sig,JSON.stringify(s.auto));break;}}else{lastSig=sig;stall=0;}}
  if(s.mode!=='trial'){
   const k=`${s.chapter}/${s.beat}`;if(beats.has(k)&&Date.now()-beatAt>600000){console.log('LOOP',k,s.mode,JSON.stringify(s.auto));break;} // 상태가 돌기만 하고 비트가 10분째 그대로
   if(!beats.has(k)){beats.set(k,s.beatKind);beatAt=Date.now();await fs.writeFile(path.join(work,'checkpoint.json'),JSON.stringify({steps,state:s},null,2));console.log('beat',k,s.beatKind,'coins',s.coins,'cards',s.cards,'gifts',s.gifts);if(['card','freetime','investigate','ending','end'].includes(s.beatKind)){await delay(400);try{await probe.capture(`${k.replace('/','-')}-${s.beatKind}.png`);}catch(e){}}}
   if(s.mode==='story'&&s.line&&!seenLines.has(k+s.event)){seenLines.add(k+s.event);if(seenLines.size%400===0){try{await probe.capture(`line-${seenLines.size}.png`);}catch(e){}}}
   if(['explore','map','confirm','popup','grid'].includes(s.mode)&&!seenModes.has(s.mode+s.chapter)){seenModes.add(s.mode+s.chapter);await delay(700);try{await probe.capture(`mode-${s.chapter}-${s.mode}-${s.beat}.png`);}catch(e){}}
   if(s.mode==='explore'&&!padShot){padShot=true;await tap('Tab');await delay(700);try{await probe.capture('pad-menu.png');}catch(e){}
    for(const k of ['Enter']){await tap(k);await delay(600);try{await probe.capture('pad-page0.png');}catch(e){}}
    await tap('Backspace');await delay(200);for(let i=0;i<3;i++){await tap('d');await delay(150);}await tap('Enter');await delay(600);try{await probe.capture('pad-card.png');}catch(e){}
    await tap('Backspace');await delay(200);await tap('Backspace');await delay(400);continue;}
   const a=s.auto;if(!a){await delay(40);continue;}
   if(fastStory&&s.mode==='story'&&a.kind==='key'&&a.key==='Enter'){if(!skipping){await key('Control','keyDown');skipping=true;}await delay(80);continue;}
   if(a.kind==='key')await tap(a.key);else if(a.kind==='click')await click(a.x,a.y);
   continue;
  }
  const st=s.stage;beatAt=Date.now();
  if(st.index!==last){last=st.index;log.push({index:st.index,kind:st.kind,hearts:st.hearts});console.log('stage',st.index,st.kind);if(!seen.has(st.kind)){seen.set(st.kind,st.index);await delay(500);try{await probe.capture(`${String(st.index).padStart(2,'0')}-${st.kind}.png`);}catch(e){console.log('capture skipped',st.kind,e.message);}}}
  const a=s.auto;
  if(fastStory&&st.script){if(!skipping){await key('Control','keyDown');skipping=true;}await delay(80);continue;}
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
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({end,steps,fastStory,executable:built.executable,beats:[...beats],trials:log},null,1));
 assert(!end.error,'게임 오류 : '+end.error);
 assert(beats.size>0&&steps>1,'실제 진행 구간이 없어요. V4는 정상 저장을 지정한 verify-v4-flow.mjs로 검사하세요. 타이틀 복귀만으로 전편 PASS를 내지 않아요.');
 assert(end.mode==='title'||end.chapter>to,'끝까지 가지 못함 : '+JSON.stringify(end).slice(0,300));
 console.log(JSON.stringify({ok:true,beats:beats.size,trialStages:log.length,coins:end.coins,cards:end.cards,steps}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,lastState,executable:built.executable,fastStory},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
