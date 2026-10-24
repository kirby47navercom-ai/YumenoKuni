// 빌드된 플레이어를 별도 테스트 창으로 띄워 타이틀 → 대사 진행 → 래피 패드를 확인하고 캡처한다.
// node tools/verify.mjs   (결과 : Saved/verification/)
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/verification');await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let probe;
try{
 probe=await editorWindowProbe({work,mode:'player',executable:built.executable});
 await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'player ready',60000);
 const stats=async()=>JSON.parse((await probe.evaluate('window.hbPlayerDebug.call("Driver","Yumeno.Stats",{})')).outputs.result);
 const codes={Enter:[13,'Enter'],Tab:[9,'Tab'],' ':[32,'Space']};
 const tap=async k=>{const [vk,code]=codes[k];for(const type of ['keyDown','keyUp']){await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode:vk});await delay(type==='keyDown'?90:140);}};
 await delay(800);
 assert.equal((await stats()).mode,'title','타이틀에서 시작');
 await probe.capture('01-title.png');
 await tap('Enter');await delay(300);
 let s=await stats();assert.equal(s.mode,'story','Enter로 이야기 시작');
 const lines=[];
 for(let i=0;i<40;i++){
  s=await stats();lines.push({scene:s.scene,event:s.event,speaker:s.speaker,line:s.line.slice(0,40),portrait:s.portrait});
  if(i===3||i===25)await probe.capture(`02-story-${i}.png`);
  await tap('Enter');await delay(60);await tap('Enter');await delay(60);
 }
 assert(lines.some(l=>l.portrait),'화자 스프라이트 표시');
 assert(new Set(lines.map(l=>l.event+'/'+l.scene)).size>20,'대사가 계속 넘어감');
 await tap('Tab');await delay(300);assert.equal((await stats()).mode,'pad','Tab으로 래피 패드');
 await probe.capture('03-pad.png');
 await tap('Tab');await delay(200);assert.equal((await stats()).mode,'story','Tab으로 닫기');
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,lines},null,1));
 console.log(JSON.stringify({ok:true,last:lines.at(-1),portraits:[...new Set(lines.map(l=>l.portrait).filter(Boolean))]},null,1));
}finally{await probe?.close?.();}
