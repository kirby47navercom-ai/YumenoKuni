// Technical capability probe in our own player, not gameplay/visual acceptance.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/svg-motion-'+Date.now());let probe;
await fs.mkdir(work,{recursive:true});
try{
 probe=await editorWindowProbe({work,mode:'player',executable:built.executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 if(process.argv.includes('--aliases')){
  const result=await probe.evaluate(`(async()=>{const out=[];for(const path of ['Assets/Art/ui/result_refute.svg','Assets/Art/ui/./result_refute.svg','Assets/Art/ui//.//result_refute.svg']){const r=await fetch('/api/file?path='+encodeURIComponent(path)),text=await r.text();out.push({path,status:r.status,redirected:r.redirected,url:r.url,text});}return out;})()`);
  assert(result.every(r=>r.status===200&&!r.redirected&&r.text===result[0].text));await fs.writeFile(path.join(work,'aliases.json'),JSON.stringify({result:result.map(({text,...r})=>r),scope:'Same known project SVG via safe in-directory relative aliases; no parent traversal, external network or source change.'},null,2));console.log(JSON.stringify({ok:true,work,result:result.map(({text,...r})=>r)}));
 }else{
 const result=await probe.evaluate(`(async()=>{
  const url=tag=>'data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><!--'+tag+'--><rect width="32" height="32" fill="red"><animate attributeName="fill" from="red" to="blue" dur="1s" fill="freeze"/></rect></svg>');
  const image=new Image(),canvas=document.createElement('canvas');canvas.width=canvas.height=32;image.style.cssText='position:fixed;top:0;left:0;width:32px;height:32px;z-index:99999';document.body.append(image);
  const wait=ms=>new Promise(r=>setTimeout(r,ms)),out=[];
  for(const tag of ['A','B','A']){await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=url(tag);});await wait(100);const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);const early=Array.from(ctx.getImageData(16,16,1,1).data);await wait(1050);ctx.drawImage(image,0,0);const late=Array.from(ctx.getImageData(16,16,1,1).data);out.push({tag,early,late});}
  image.remove();return out;
 })()`);
 await fs.mkdir(work,{recursive:true});await fs.writeFile(path.join(work,'report.json'),JSON.stringify({executable:built.executable,result,scope:'SVG-image declarative animation restart probe only; A/B/A source resources in our own runtime.'},null,2));
 for(const row of result){assert(row.early[0]>150&&row.early[2]<100);assert(row.late[2]>200&&row.late[0]<50);}
 console.log(JSON.stringify({ok:true,work,result}));
 }
}finally{await probe?.stop?.();}
