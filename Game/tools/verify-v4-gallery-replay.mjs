// Cold title Gallery, using only records actually read in an unchanged normal save.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..');
const baseline=process.argv.includes('--baseline');
const resume=path.join(root,'Saved/v4-title-extras-1793435532005/UserData/savegames.json');
const source=await fs.readFile(resume),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const raw=JSON.parse(source),headKey=Object.keys(raw.items).find(k=>k.includes('yumeno-progress-v4.project.')),head=JSON.parse(raw.items[headKey]);
const targets=JSON.parse(await fs.readFile(path.join(root,'Saved/gallery-replay-target-2026110118.json'),'utf8'));
assert.deepEqual(targets.map(t=>t.kind),['listener','npc']);
const title=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/title_chapter_layout.json'),'utf8'));
const layout=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/gallery_layout.json'),'utf8'));
const figures=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/court.json'),'utf8')).figures;
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/v4-gallery-replay-'+Date.now());await fs.mkdir(path.join(work,'UserData'),{recursive:true});await fs.writeFile(path.join(work,'UserData/savegames.json'),source);
const delay=ms=>new Promise(r=>setTimeout(r,ms)),checks=[];
const keys={Enter:[13,'Enter'],Backspace:[8,'Backspace'],s:[83,'KeyS'],a:[65,'KeyA'],c:[67,'KeyC']};let probe,last;
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 const call=n=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+n)},{})`);
 const stats=async()=>{last=JSON.parse((await call('Stats')).outputs.result);assert(!last.error,JSON.stringify(last));return last;};
 const sample=async()=>{const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(70);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=f+2,'sampled input',10000);};
 const tap=async k=>{const[windowsVirtualKeyCode,code]=keys[k];for(const type of ['keyDown','keyUp']){await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});await sample();}};
 const click=async r=>{for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x:r[0]+r[2]/2,y:r[1]+r[3]/2,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}};
 const ui=async id=>probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="'+${JSON.stringify(id)}+'"]'),r=e?.getBoundingClientRect(),s=e?getComputedStyle(e):null;return {visible:!!r?.width&&s?.display!=='none'&&s?.visibility!=='hidden'&&Number(s?.opacity)>0,text:e?.textContent,color:s?.color};})()`);
 assert.equal((await stats()).mode,'title');await click(title.mainRects[4]);await probe.until(async()=>!(await ui('GaStatus')).text.includes('준비 중'),'actual read archive ready',60000);
 let coins=head.coins;
 for(const target of targets){
  await click(layout.top[0]);for(let i=0;i<target.index;i++)await tap('s');await tap('Enter');
  if(!target.owned){if(target.price){assert((await ui('CwBody')).visible);await tap('a');await tap('Enter');coins-=target.price;await tap('Enter');}}
  await probe.until(async()=>(await ui('Body')).visible,'actual read replay opens',10000);
  const s=await stats(),dialogue=JSON.parse((await call('DialogueStats')).outputs.result);
  assert.equal(dialogue.raw,target.target.text);assert.equal(s.node,head.node);assert.equal(s.coins,coins);
  const portrait=await ui('Portrait');const expected=figures[target.target.actor==='mio'?target.target.dialoguePortrait:target.target.pose||target.target.appearanceActor||target.target.actor].texture;
  let audio=null;
  if(baseline){assert.equal(s.portrait,'');assert(!portrait.visible);}
  else{
   assert(!(await ui('Title')).visible);
   assert.equal(s.portrait,expected);assert(portrait.visible);assert(s.gallery.replay&&s.gallery.worldActive&&s.gallery.worldVisible);assert.equal(s.gallery.node,target.target.id);assert.equal(s.gallery.space,target.target.scene.space);assert.equal(s.gallery.music,'bgm_daily_pastel');
   await probe.until(async()=>{audio=await probe.evaluate('window.hbPlayerDebug.audio()');assert.deepEqual(audio.errors,[]);return audio.voices.some(v=>v.playing&&!v.virtual&&JSON.stringify(v).includes('bgm_daily_pastel')&&v.time>.25&&v.peak>.001)&&!audio.voices.some(v=>v.playing&&JSON.stringify(v).includes('S_bgm_title.'));},'source section music audible after title fade',15000);
  }
  await delay(650);await probe.capture(target.kind+'.png');checks.push({kind:target.kind,node:target.target.id,portrait:s.portrait,visible:portrait.visible,gallery:s.gallery,dialogue,audio});
  await tap('Backspace');assert(!(await ui('Body')).visible);assert(!(await ui('Portrait')).visible);
  if(!baseline){const close=await stats();assert(!close.gallery.replay&&!close.gallery.worldVisible);assert.equal(close.gallery.music,'bgm_title');assert.equal(close.audioV4.ambient,'');}
  await tap('Backspace');
 }
 // Replay itself must never advance or overwrite the canonical ending/history.
 const disk=JSON.parse((JSON.parse(await fs.readFile(path.join(work,'UserData/savegames.json'),'utf8'))).items[headKey]);
 assert.deepEqual(disk,head);
 let committed=false;
 if(!baseline){
  await tap('Backspace');assert((await ui('CwBody')).visible);await tap('a');await tap('Enter');await probe.until(async()=>(await stats()).mode==='title','gallery save returns to title',60000);assert((await ui('Title')).visible);
  const after=JSON.parse((JSON.parse(await fs.readFile(path.join(work,'UserData/savegames.json'),'utf8'))).items[headKey]);assert.equal(after.coins,coins);for(const t of targets)assert(after.gallery.purchased.includes(t.id));
  const common=h=>Object.fromEntries(Object.entries(h).filter(([k])=>!['coins','gallery','galleryBank'].includes(k)));assert.deepEqual(common(after),common(head));committed=true;
  await tap('c');await probe.until(async()=>(await stats()).mode==='credits','canonical completed save Continue',60000);assert.equal((await stats()).node,head.node);assert.equal((await stats()).coins,coins);
 }
 assert.equal(sha(await fs.readFile(resume)),sha(source));assert.deepEqual(probe.errors,[]);
 const report={ok:true,baseline,work,executable,sourceSha256:sha(source),checks,canonicalUnchanged:true,committedPurchasesAndCanonicalContinue:committed,scope:'Cold title -> actually unlocked/read event purchases -> replay NPC and protagonist-listener with source scene/music -> close/save/title/canonical Continue. Original normal source save immutable; no fake unlocks, chapter traversal or playtime acceptance.'};
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,baseline,work,checks:checks.map(c=>({kind:c.kind,node:c.node,portrait:c.portrait,visible:c.visible}))}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,last,checks,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
