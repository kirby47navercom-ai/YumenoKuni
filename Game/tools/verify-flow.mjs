// 본편 자동 진행 검증 : 새 게임 → 장 진행(대본·프리타임·선물·수사·재판·처형·막간)을 게임이 알려 주는 입력(Stats.auto)으로 끝까지.
// node tools/verify-flow.mjs [시작 장 0~6] [끝 장 0~6]  (결과 : Saved/verification-flow/)
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const from=Number(process.argv[2]||0),to=Number(process.argv[3]??6);
const work=path.join(root,'Saved/verification-flow-'+Date.now().toString(36));await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const KEYS={Tab:[9,'Tab'],Backspace:[8,'Backspace'],m:[77,'KeyM'],g:[71,'KeyG'],y:[89,'KeyY'],Enter:[13,'Enter'],' ':[32,'Space'],e:[69,'KeyE'],q:[81,'KeyQ'],a:[65,'KeyA'],d:[68,'KeyD'],t:[84,'KeyT'],Shift:[16,'ShiftLeft'],1:[49,'Digit1'],2:[50,'Digit2'],3:[51,'Digit3'],4:[52,'Digit4']};
// 플레이어 --smoke-test 는 180초 뒤 스스로 끝난다(엔진 수락 모드). 긴 검증은 소크 시간으로 늘린다.
process.env.HB_PLAYER_SOAK_HOURS??='3';
let probe;
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
 await delay(800);for(let k=0;k<20&&(await stats()).mode==='title';k++){await tap('Enter');await delay(500);}
 if(from>0)await probe.evaluate(`window.hbPlayerDebug.call("Driver","Yumeno.DebugChapter",{index:${from}})`);await delay(500);
 const beats=new Map();
 const seen=new Map(),seenLines=new Set(),seenModes=new Set(),log=[];let padShot=false;let last=-1,steps=0,focused=false,lastSig='',stall=0;
 while(steps++<200000){
  const t0=Date.now();const s=await stats();const dt=Date.now()-t0;
  if(s.error){console.log('GAME ERROR',s.error);break;}
  if(s.mode==='title'||s.chapter>to)break;
  {const sig=JSON.stringify([s.mode,s.chapter,s.beat,s.event,s.stage,s.trial?.index,s.trial?.broken]);if(sig===lastSig){if(++stall>3000){console.log('STALL',sig,JSON.stringify(s.auto));break;}}else{lastSig=sig;stall=0;}}
  if(s.mode!=='trial'){
   const k=`${s.chapter}/${s.beat}`;if(!beats.has(k)){beats.set(k,s.beatKind);console.log('beat',k,s.beatKind,'coins',s.coins,'cards',s.cards,'gifts',s.gifts);if(['card','freetime','investigate','ending','end'].includes(s.beatKind)){await delay(400);try{await probe.capture(`${k.replace('/','-')}-${s.beatKind}.png`);}catch(e){}}}
   if(s.mode==='story'&&s.line&&!seenLines.has(k+s.event)){seenLines.add(k+s.event);if(seenLines.size%400===0){try{await probe.capture(`line-${seenLines.size}.png`);}catch(e){}}}
   if(['explore','map','confirm','popup','grid'].includes(s.mode)&&!seenModes.has(s.mode+s.chapter)){seenModes.add(s.mode+s.chapter);await delay(700);try{await probe.capture(`mode-${s.chapter}-${s.mode}-${s.beat}.png`);}catch(e){}}
   if(s.mode==='explore'&&!padShot){padShot=true;await tap('Tab');await delay(700);try{await probe.capture('pad-menu.png');}catch(e){}
    for(const k of ['Enter']){await tap(k);await delay(600);try{await probe.capture('pad-page0.png');}catch(e){}}
    await tap('Backspace');await delay(200);for(let i=0;i<3;i++){await tap('d');await delay(150);}await tap('Enter');await delay(600);try{await probe.capture('pad-card.png');}catch(e){}
    await tap('Backspace');await delay(200);await tap('Backspace');await delay(400);continue;}
   const a=s.auto;if(!a){await delay(40);continue;}
   if(a.kind==='key')await tap(a.key);else if(a.kind==='click')await click(a.x,a.y);
   continue;
  }
  const st=s.stage;
  if(st.index!==last){last=st.index;log.push({index:st.index,kind:st.kind,hearts:st.hearts});console.log('stage',st.index,st.kind);if(!seen.has(st.kind)){seen.set(st.kind,st.index);await delay(500);try{await probe.capture(`${String(st.index).padStart(2,'0')}-${st.kind}.png`);}catch(e){console.log('capture skipped',st.kind,e.message);}}}
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
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({end,steps,beats:[...beats],trials:log},null,1));
 assert(!end.error,'게임 오류 : '+end.error);
 assert(end.mode==='title'||end.chapter>to,'끝까지 가지 못함 : '+JSON.stringify(end).slice(0,300));
 console.log(JSON.stringify({ok:true,beats:beats.size,trialStages:log.length,coins:end.coins,cards:end.cards,steps}));
}finally{await Promise.race([probe?.close?.(),delay(8000)]);try{(await import('node:child_process')).execSync('taskkill /F /FI "IMAGENAME eq HBGame*"',{stdio:'ignore'});}catch{}process.exit(process.exitCode??0);}
