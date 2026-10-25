// 재판 카메라 연출 확인 : 1장 재판을 열고 대사를 넘기며 일정 간격으로 화면을 찍는다(컷·드리프트·휩·입상 겹침 확인).
// node tools/capture-trial-camera.mjs [시작 단계 번호]  (결과 : Saved/camera/)
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/camera');await fs.rm(work,{recursive:true,force:true});await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
process.env.HB_PLAYER_SOAK_HOURS??='1';
let probe;
try{
 probe=await editorWindowProbe({work,mode:'player',executable:built.executable});
 await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'player ready',60000);
 const tap=async(key,code,vk)=>{for(const type of ['keyDown','keyUp']){await probe.cdp('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk});await delay(60);}};
 await delay(800);await tap('t','KeyT',84);await delay(600);
 if(process.argv[2])await probe.evaluate(`window.hbPlayerDebug.call("Driver","Yumeno.DebugJump",{index:${Number(process.argv[2])}})`);
 if(process.argv[3]==='fast'){for(let i=0;i<40;i++){await delay(200);await probe.capture(`f${String(i).padStart(2,'0')}.png`);}console.log('ok');process.exit(0);}
 for(let i=0;i<10;i++){
  await delay(250);await probe.capture(`${String(i).padStart(2,'0')}a.png`);
  await delay(1400);await probe.capture(`${String(i).padStart(2,'0')}b.png`);
  await tap('Enter','Enter',13);
 }
 console.log('ok');
}finally{await Promise.race([probe?.close?.(),delay(8000)]);try{(await import('node:child_process')).execSync('taskkill /F /FI "IMAGENAME eq HBGame*"',{stdio:'ignore'});}catch{}process.exit(0);}
