// One corrected ADV screen, restored from an existing actual save. No chapter traversal.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const checkpoint=JSON.parse(await fs.readFile(path.join(root,'Saved/ui-checkpoints/adv-standing/checkpoint.json'),'utf8'));
const bytes=await fs.readFile(checkpoint.save);assert.equal(createHash('sha256').update(bytes).digest('hex'),checkpoint.sha256);
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const layout=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/dialogue_layout.json'),'utf8'));
const work=path.join(root,'Saved/v4-standing-resume-'+Date.now());await fs.mkdir(path.join(work,'UserData'),{recursive:true});await fs.writeFile(path.join(work,'UserData/savegames.json'),bytes);
const delay=ms=>new Promise(r=>setTimeout(r,ms));let probe;process.env.HB_PLAYER_SOAK_HOURS='1';
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(700);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const stats=async()=>{const s=JSON.parse((await call('Stats')).outputs.result);assert(!s.error,JSON.stringify(s));return s;};
 const tap=async(key,code,windowsVirtualKeyCode)=>{for(const type of ['keyDown','keyUp']){await probe.cdp('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode});await delay(150);}};
 await tap('c','KeyC',67);await probe.until(async()=>(await stats()).node===checkpoint.node,'restore exact existing ADV node',10000);
 const dialogue=JSON.parse((await call('DialogueStats')).outputs.result);assert.equal(dialogue.speaker,checkpoint.speaker);assert.equal(dialogue.trial,false);if(dialogue.shown<dialogue.length)await tap('Enter','Enter',13);assert.equal((await stats()).node,checkpoint.node);
 const ui=await probe.evaluate(`(()=>{const names=['Portrait','Body','Name','FHudImg'];return Object.fromEntries(names.map(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e.getBoundingClientRect(),i=e.querySelector('img');return[n,{rect:[r.x,r.y,r.width,r.height],visible:getComputedStyle(e).visibility!=='hidden',asset:i?.dataset.asset,loaded:!!i&&i.complete&&i.naturalWidth>0}];}));})()`);
 assert(ui.Portrait.visible&&ui.Portrait.loaded);const expected=[0,0,1280,layout.portrait.referenceImageHeight];ui.Portrait.rect.forEach((v,i)=>assert(Math.abs(v-expected[i])<.1));assert(ui.Name.loaded&&ui.FHudImg.loaded);
 await probe.capture('standing.png');assert.deepEqual(probe.errors,[]);
 const report={ok:true,work,executable,checkpoint,restoredNode:(await stats()).node,checks:['Continue restored existing native save directly at Haruka ADV line','1050px standing image and current source HUD/name loaded','revealing current line did not advance the authored node'],scope:'Only the corrected standing/dialogue screen. No DebugChapter/DebugJump/new game, earlier chapter traversal, other minigame or full campaign regression.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
