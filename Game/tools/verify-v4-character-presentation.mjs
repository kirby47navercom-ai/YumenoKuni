// Actual own-player visual fixtures; does not claim normal campaign traversal.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const tasks=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/native_tasks.json'),'utf8')).tasks;
const work=path.join(root,'Saved/v4-character-presentation-'+Date.now());await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms)),checks=[];let probe;process.env.HB_PLAYER_SOAK_HOURS='1';
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(700);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const stats=async()=>{const s=JSON.parse((await call('Stats')).outputs.result);assert(!s.error);return s;};
 const control=type=>probe.cdp('Input.dispatchKeyEvent',{type,key:'Control',code:'ControlLeft',windowsVirtualKeyCode:17});
 const ui=()=>probe.evaluate(`(()=>Object.fromEntries(['Portrait','SdFace','ArmFace','DialogueOrnament'].map(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e?.getBoundingClientRect(),im=e?.querySelector('img');return[n,{visible:!!r?.width&&getComputedStyle(e).visibility!=='hidden',asset:im?.dataset.asset,loaded:!!im?.complete&&im.naturalWidth>0,rect:r?[r.x,r.y,r.width,r.height]:null}]})))()`);
 await call('DebugFastRead');const states=[];
 for(const kind of ['showdown','armament']){
  const fixture=Object.entries(tasks).find(([,v])=>v.stage.kind===kind);assert(fixture);
  await call('DebugV4Task',{taskId:fixture[0]});await control('keyDown');
  await probe.until(async()=>{const s=await stats();return !s.taskQueue&&s.stage?.kind===kind&&s.taskInputArmed;},'active '+kind,60000);
  await control('keyUp');await delay(300);const s=await stats(),u=await ui();assert(!u.DialogueOrnament.visible,'dialogue ornament leaked into task');
  if(kind==='armament'){assert(u.ArmFace.visible&&u.ArmFace.loaded);assert.equal(u.ArmFace.asset,'Assets/Art/armament_v4/player_mio.webp');}
  for(const n of ['SdFace','ArmFace'])if(u[n].visible)assert(u[n].loaded);
  states.push({task:fixture[0],kind,ui:u});await probe.capture(kind+'.png');checks.push(kind+' actual authored entry uses curated character routes, loaded cutin and no dialogue-frame residue');
 }
 assert.deepEqual(await probe.evaluate('Array.from(document.images).filter(i=>i.offsetWidth>0&&i.src&&i.complete&&i.naturalWidth===0).map(i=>i.src)'),[]);assert.deepEqual(probe.errors,[]);
 const report={ok:true,work,executable,checks,states,fixture:true,scope:'Own native actual task entry screenshots and character-owner cleanup. Static curated839-route provenance gate is separate. Not normal campaign progression, all poses, played minigame completion or source artwork/pixel equality.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,checks,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
