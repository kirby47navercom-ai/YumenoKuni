// 다이내믹 논스톱 논의 검증 : 3D 글자(화자 앞·뒤 통과) · 오답 감점 · 집중(V포인트) · V논파 · 거짓 탄환 · 논의 3개 클리어
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
 const key=async(key,code,vk,type)=>probe.cdp('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk});
 const tap=async(k,code,vk)=>{await key(k,code,vk,'keyDown');await delay(80);await key(k,code,vk,'keyUp');await delay(120);};
 const move=async(x,y)=>{await probe.cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x,y});await delay(40);};
 const click=async(x,y,hold=70)=>{await move(x,y);await probe.cdp('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',clickCount:1});await delay(hold);await probe.cdp('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',clickCount:1});await delay(90);};
 let maxBack=0,maxFront=0;const motions=new Set();
 const waitWeak=async()=>{for(let i=0;i<400;i++){const s=await stats(),t=s.trial;if(t){maxBack=Math.max(maxBack,t.glyphsBack);maxFront=Math.max(maxFront,t.glyphsFront);motions.add(t.motion);}if(t&&t.kind==='weak'&&!t.clearing&&t.weakPoint)return s;await delay(40);}throw Error('약점 줄 대기 시간 초과');};
 const selectBullet=async id=>{for(let i=0;i<6&&(await stats()).trial.bullet!==id;i++)await tap('e','KeyE',69);assert.equal((await stats()).trial.bullet,id,'탄환 선택 '+id);};
 await delay(800);await tap('t','KeyT',84);await delay(400);
 assert.equal((await stats()).mode,'trial','T로 재판 진입');
 await probe.capture('01-debate-start.png');
 // 1) 오답
 let s=await waitWeak();const hearts=s.trial.hearts;
 if(s.trial.bullet===s.trial.answer)await tap('e','KeyE',69);
 s=await waitWeak();await click(...s.trial.weakPoint);await delay(120);
 assert.equal((await stats()).trial.hearts,hearts-1,'오답이면 발언력 감소');
 await probe.capture('02-wrong.png');
 // 2) 집중 + V포인트 + V논파
 s=await waitWeak();await selectBullet(s.trial.answer);
 await key('Shift','ShiftLeft',16,'keyDown');await delay(250);
 s=await waitWeak();assert(s.trial.vpoint,'집중 중 V포인트 표시');
 assert(s.trial.focus<100,'집중 게이지 소모');
 await probe.capture('03-focus-vpoint.png');
 s=await waitWeak();const vBefore=s.trial.vBreaks;await click(...s.trial.vpoint);
 await key('Shift','ShiftLeft',16,'keyUp');await delay(150);
 await probe.capture('04-vbreak.png');
 assert.equal((await stats()).trial.vBreaks,vBefore+1,'V포인트 명중 = V논파');
 // 3) 거짓 탄환 : 길게 누르면 거짓 탄환(발언력 1칸 걸고), 거짓 정답이 없는 장이라 빗나가면 그 칸을 잃는다
 s=await waitWeak();const h2=s.trial.hearts;await click(40,700,700);
 assert.equal((await stats()).trial.hearts,h2-1,'거짓 탄환 장전에 발언력 소모');
 // 4) 정답으로 논의 3개 클리어
 const report=[];
 for(let n=0;n<60;n++){
  s=await stats();if(s.mode!=='trial')break;
  if(s.trial.clearing){await delay(2700);continue;}
  s=await waitWeak();await selectBullet(s.trial.answer);
  // 집중(Shift)으로 시간을 늦추고 쏜다. 글자가 움직이므로 최대 4번까지 다시 조준
  await key('Shift','ShiftLeft',16,'keyDown');
  let after,deb,before;
  for(let shot=0;shot<4;shot++){s=await waitWeak();before=s.trial.broken;deb=s.trial.debate;await click(...s.trial.weakPoint,s.trial.needLie?700:40);after=await stats();if(after.mode!=='trial'||after.trial.broken>before||after.trial.clearing||after.trial.debate!==deb)break;}
  await key('Shift','ShiftLeft',16,'keyUp');
  report.push({debate:deb,answer:s.trial.answer,lie:s.trial.needLie,motion:s.trial.motion});
  assert(after.mode!=='trial'||after.trial.broken>before||after.trial.clearing||after.trial.debate!==deb,'정답이면 논파');
 }
 s=await stats();await probe.capture('05-end.png');
 assert.equal(s.mode,'title','논의 3개 클리어 후 타이틀로');
 assert(maxBack>0,'글자가 화자 뒤로 지나감(뒤층 사용)');assert(maxFront>0,'화자 앞 글자');
 assert(report.some(r=>r.lie),'거짓 탄환 필수 논의 통과');
 const result={ok:true,breaks:report.length,lies:report.filter(r=>r.lie).length,maxBack,maxFront,motions:[...motions]};
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({...result,report},null,1));
 console.log(JSON.stringify(result,null,1));
}finally{await probe?.close?.();}
