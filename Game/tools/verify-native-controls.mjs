// Owned hidden window only. Reads UI and saves; sends ordinary mouse/key events.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),read=async file=>JSON.parse((await fs.readFile(file,'utf8')).replace(/^\uFEFF/,''));
const build=await read(process.argv[2]||path.join(root,'build-result.json'));
const manifest=await read(path.join(build.output,'game.hbpack.json'));
const work=path.resolve(process.argv[3]||path.join(root,'Saved/native-controls-'+Date.now()));
const prepared={output:build.output,executable:build.executable,manifest},checks=[];
await fs.mkdir(work,{recursive:true});
let probe,dir;
const frame=async(name='frame',pixels=false)=>{await probe.capture(name,{pixels});return read(path.join(dir,name+'.ui.json'));};
const props=(s,id,instance='optionsv4')=>s.widgets.find(w=>w.instance===instance)?.nodes.find(n=>n.id===id)?.properties;
const visible=(s,instance)=>s.widgets.some(w=>w.instance===instance);
const wait=async(predicate,label)=>probe.until(async()=>{const s=await frame();return predicate(s)&&s;},label,35000,80);
const clickRect=async(s,id,rx=.5,ry=.5)=>{const r=s.rects.find(r=>r.id===id);assert(r,'actual visible rectangle '+id);const size=await probe.viewport(),fit=Math.min(size[0]/1280,size[1]/720);await probe.click((r.x+r.w*rx)/fit,(r.y+r.h*ry)/fit);};
const keysPage=async()=>{
 await probe.tap('ArrowUp');await probe.tap('ArrowUp'); // Wrap to settings row13.
 await probe.tap('Enter');
 return wait(s=>props(s,'Label0')?.text==='앞으로 / 위 항목','binding list');
};
try{
 for(const size of [[1280,720],[1920,1080],[3440,1440],[1600,1200]]){
  dir=path.join(work,size.join('x'));await fs.mkdir(dir,{recursive:true});
  probe=await nativeWindowProbe({source:build.output,prepared,work:dir,sparse:true,unprofiled:true,maxFrames:null});
  await probe.hiddenBorderless();await probe.resize(...size);
  await wait(s=>visible(s,'titlemenuv4'),'ready title');
  await probe.tap('Escape');
  await wait(s=>visible(s,'optionsv4'),'Escape opens settings');
  let s=await keysPage();assert.equal(props(s,'Value0').text,'W');
  await frame('key-list',true);
  await clickRect(s,'Value0');
  await wait(s=>props(s,'Value0')?.text==='새 키를 눌러 주세요','actual row click starts capture');
  await probe.tap('e');
  await wait(s=>props(s,'Description')?.text.includes('사용 중이에요'),'duplicate binding rejected');
  await probe.tap('Escape');
  s=await wait(s=>props(s,'Value0')?.text==='W','cancel preserves binding');
  await clickRect(s,'Value0');await wait(s=>props(s,'Value0')?.text==='새 키를 눌러 주세요','capture again');
  await probe.tap('j');
  s=await wait(s=>props(s,'Value0')?.text==='J','new binding displayed');
  assert(props(s,'Description').text.includes('앞으로 / 위 항목'));
  await frame('bound-j',true);
  await probe.tap('Escape');
  await wait(s=>props(s,'Label6')?.text==='조작키 안내 · 변경','back to settings');
  await probe.tap('Escape');
  await wait(s=>!visible(s,'optionsv4'),'Escape closes settings');
  const saved=await read(path.join(dir,'State/Saves/YumenoKuni-options-v4.json'));
  assert.equal(saved.keys.w,'j');assert.equal(saved.frameRate,120);
  // On the title, the remapped key must move the selected menu item.
  await probe.tap('s');let before=await frame();
  const artBefore=props(before,'TmArt','titlemenuv4')?.texture;
  await probe.tap('w');assert.equal(props(await frame(),'TmArt','titlemenuv4')?.texture,artBefore,'old W is no longer the forward/up action');
  await probe.tap('j');assert.notEqual(props(await frame(),'TmArt','titlemenuv4')?.texture,artBefore,'J reaches the actual game input consumer');
  const runtime=await probe.close();probe=null;
  checks.push({size,cursorClicks:true,cancel:true,duplicateRejected:true,remapConsumedByGame:true,saved:true,exit:runtime.exitCode});
  await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:false,build:build.id,checks},null,2));
 }
 // Reuse the final isolated save in a fresh native process.
 dir=path.join(work,'restart');await fs.mkdir(path.join(dir,'State/Saves'),{recursive:true});
 await fs.copyFile(path.join(work,'1600x1200/State/Saves/YumenoKuni-options-v4.json'),path.join(dir,'State/Saves/YumenoKuni-options-v4.json'));
 probe=await nativeWindowProbe({source:build.output,prepared,work:dir,sparse:true,unprofiled:true,maxFrames:null});await probe.hiddenBorderless();await probe.tap('Escape');await wait(s=>visible(s,'optionsv4'),'restarted settings');
 let s=await keysPage();assert.equal(props(s,'Value0').text,'J');
 await probe.tap('ArrowUp');await probe.tap('ArrowUp'); // Restore keys row, penultimate item.
 s=await wait(s=>s.widgets.find(w=>w.instance==='optionsv4')?.nodes.some(n=>n.id.startsWith('Label')&&n.properties.text==='조작키 기본값 복원'),'restore keys row visible');
 await probe.tap('Enter');await probe.tap('Escape');await probe.tap('Escape');await wait(s=>!visible(s,'optionsv4'),'settings closed after reset');
 const reset=await read(path.join(dir,'State/Saves/YumenoKuni-options-v4.json'));assert.equal(reset.keys.w,'w');
 const runtime=await probe.close();probe=null;checks.push({restartPersistence:true,restoreDefaults:true,exit:runtime.exitCode});
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,build:build.id,checks,scope:'Physical input on hidden owned native windows. Functional checks, not performance measurements.'},null,2));
 console.log(JSON.stringify({ok:true,work,checks}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,checks},null,2));throw error;}
finally{await probe?.close().catch(()=>{});}
