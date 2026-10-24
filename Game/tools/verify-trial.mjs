// 논스톱 논의 검증 : 타이틀에서 T → 약점에 오답 발사(하트 감소) → 정답 발사(논파) → 논의 3개 클리어.
// node tools/verify-trial.mjs   (결과 : Saved/verification-trial/)
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/verification-trial');await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let probe;
try{
 probe=await editorWindowProbe({work,mode:'player',executable:built.executable});
 await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'player ready',60000);
 const stats=async()=>JSON.parse((await probe.evaluate('window.hbPlayerDebug.call("Driver","Yumeno.Stats",{})')).outputs.result);
 const tap=async(key,code,vk)=>{for(const type of ['keyDown','keyUp']){await probe.cdp('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk});await delay(type==='keyDown'?80:120);}};
 const mouse=async(x,y,click)=>{await probe.cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x,y});await delay(60);if(click)for(const type of ['mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1});await delay(type==='mousePressed'?80:60);}};
 // 약점 줄이 나올 때까지 기다렸다가, 화면 안에 들어온 약점 단어 중앙 좌표를 돌려준다
 const waitWeak=async()=>{for(let i=0;i<300;i++){const s=await stats();const t=s.trial;if(t&&t.kind==='weak'&&!t.clearing){const [x,y,w,h]=t.weakRect;const cx=x+w/2;if(cx>120&&cx<1100)return {s,cx,cy:y+h/2};}await delay(50);}throw Error('약점 줄 대기 시간 초과');};
 const selectBullet=async id=>{for(let i=0;i<6&&(await stats()).trial.bullet!==id;i++)await tap('e','KeyE',69);assert.equal((await stats()).trial.bullet,id,'탄환 선택 '+id);};
 await delay(800);
 await tap('t','KeyT',84);await delay(400);
 let s=await stats();assert.equal(s.mode,'trial','T로 재판 진입');
 await probe.capture('01-debate-start.png');
 // 오답 : 약점에 다른 탄환
 let w=await waitWeak();const hearts=w.s.trial.hearts;
 if((await stats()).trial.bullet===w.s.trial.answer)await tap('e','KeyE',69);
 w=await waitWeak();await mouse(w.cx,w.cy,true);await delay(150);
 await probe.capture('02-wrong.png');
 s=await stats();assert.equal(s.trial.hearts,hearts-1,'오답이면 발언력 감소');
 const report=[];
 // 정답으로 논의 3개 클리어
 for(let debateNo=0;debateNo<3;debateNo++){
  for(let k=0;k<6;k++){
   s=await stats();if(s.mode!=='trial'||s.trial.debate!==debateNo)break;
   w=await waitWeak();
   await selectBullet(w.s.trial.answer);
   w=await waitWeak();await mouse(w.cx,w.cy,false);await delay(30);w=await waitWeak();
   const before=w.s.trial.broken;await mouse(w.cx,w.cy,true);await delay(120);
   s=await stats();
   if(debateNo===0&&k===0)await probe.capture('03-break.png');
   report.push({debate:debateNo,answer:w.s.trial.answer,broken:s.trial?.broken,clearing:s.trial?.clearing});
   assert(s.mode!=='trial'||s.trial.broken>before||s.trial.clearing||s.trial.debate!==debateNo,'정답이면 논파: '+JSON.stringify(s.trial));
   if(s.trial?.clearing){await delay(2700);break;}
  }
 }
 s=await stats();
 await probe.capture('04-end.png');
 assert.equal(s.mode,'end','논의 3개 클리어 후 종료 화면');
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,report},null,1));
 console.log(JSON.stringify({ok:true,breaks:report.length},null,1));
}finally{await probe?.close?.();}
