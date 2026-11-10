// Real pad navigation: protagonist ID photo, all15 contact cards, page restoration.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/student-id-photos-'+Date.now());await fs.mkdir(work,{recursive:true});
const wait=ms=>new Promise(r=>setTimeout(r,ms));const students='rei sora ken nana riku akari yuu koto satsuki taiga rin sho ai haruka kaede'.split(' ');let p;
process.env.HB_PLAYER_SOAK_HOURS='1';
try{
 p=await editorWindowProbe({work,mode:'player',executable:build.executable});await p.until(()=>p.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 const stats=()=>p.evaluate("window.hbPlayerDebug.call('Driver','Yumeno.Stats',{}).then(r=>JSON.parse(r.outputs.result))");
 const keys={Enter:[13,'Enter'],Tab:[9,'Tab'],Backspace:[8,'Backspace'],d:[68,'KeyD']};
 const tap=async key=>{for(const type of ['keyDown','keyUp']){await p.cdp('Input.dispatchKeyEvent',{type,key,code:keys[key][1],windowsVirtualKeyCode:keys[key][0]});await wait(70);}};
 const node=name=>p.evaluate(`(()=>{let e=document.querySelector('[data-widget-name="${name}"]'),r=e?.getBoundingClientRect();return {html:(e?.outerHTML??'').replace(/%2f/gi,'/'),x:r?.x,y:r?.y,w:r?.width,h:r?.height,visible:!!e&&r.width>0&&getComputedStyle(e).visibility!=='hidden',color:e?getComputedStyle(e).color:null,left:e?.style.left,top:e?.style.top};})()`);
 await tap('Enter');await p.evaluate("window.hbPlayerDebug.call('Driver','Yumeno.DebugChapter',{index:1})");await wait(250);
 for(let i=0;i<12&&!['story','explore','menu','map'].includes((await stats()).mode);i++)await tap('Enter');
 await tap('Tab');assert.equal((await stats()).mode,'pad');
 const owner=await node('PdFace');assert(owner.html.includes('student_ids/mio.webp'));
 await p.capture('owner-color-photo.png');
 for(let i=0;i<3;i++)await tap('d');await tap('Enter');assert.equal((await stats()).padPage,3);
 const inspected=[];
 for(let i=0;i<students.length;i++){
  const slug=students[i],s=await stats();assert(!s.error,s.error);assert.equal(s.padRow,i);
  const photo=await node('PdStand'),frame=await node('PdPic'),body=await node('PdPicText');
  assert(photo.visible&&frame.visible);assert(photo.html.includes('student_ids/'+slug+'.webp'));
  assert(frame.html.includes('student_id_frame.svg'));assert(Math.abs(photo.w-175)<1&&Math.abs(photo.h-240)<1);
  assert(body.color==='rgb(26, 31, 54)'||body.color==='rgb(26, 31, 53)'||body.color==='rgb(26, 31, 54, 1)',body.color);
  const thumb=await node('PdSil'+i);assert(thumb.html.includes('student_ids/thumb/'+slug+'.webp'));
  await wait(100);const screenshot='student-id-'+String(i).padStart(2,'0')+'.png';await p.capture(screenshot);
  inspected.push({character:slug,screenshot,photo,frame});await tap('d');
 }
 assert.equal((await stats()).padRow,0,'wrap to first student');
 await tap('Backspace');await tap('d');await tap('Enter');assert.equal((await stats()).padPage,4);
 const restored=await node('PdPicText');const restoredRgb=restored.color.match(/\d+/g).map(Number);assert(restoredRgb.every((v,i)=>Math.abs(v-[230,242,255][i])<=1),restored.color);
 await p.capture('other-page-restored.png');assert.equal(p.errors.length,0);await p.evaluate('window.hbPlayerDebug.report()');
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,executable:build.executable,ownerPhoto:'mio',contactCards:inspected,otherPageRestored:true,scope:'All16 color student ID assets are connected: protagonist header plus15 individually navigated contact cards; memorial grayscale export checked separately.'},null,2));
 console.log(JSON.stringify({ok:true,work,photos:16,contactCards:inspected.length}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:String(error)},null,2));throw error;}
finally{await p?.stop?.();}
