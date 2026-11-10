// Focused title routes from an actual completed normal save; no chapter traversal.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const audioOnly=process.argv.includes('--audio-only');
const resume=process.env.V4_RESUME;assert(resume,'V4_RESUME must name an actual normal ending save');
const raw=JSON.parse(await fs.readFile(resume,'utf8'));
const headKey=Object.keys(raw.items).find(k=>k.includes('yumeno-progress-v4.project.'));assert(headKey);
const saved=JSON.parse(raw.items[headKey]);assert(saved.trialResults.best['6'].paid);
const actualRead=new Set(saved.read||[]);for(const [k,v] of Object.entries(raw.items))if(k.includes('yumeno-v4-'+saved.snapshot+'-read-'))for(const id of JSON.parse(v).rows)actualRead.add(id);
const archive=JSON.parse(Object.entries(raw.items).find(([k])=>k.includes('yumeno-v4-chapter-index.project.'))[1]);
const titleLayout=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/title_chapter_layout.json'),'utf8'));
const galleryLayout=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/gallery_layout.json'),'utf8'));
const catalog=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/gallery_catalog.json'),'utf8'));
const records={};for(const f of await fs.readdir(path.join(root,'Assets/Data/v4_story/gallery_records'))){if(!f.endsWith('.json'))continue;const data=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/gallery_records',f),'utf8'));for(const bucket of Object.values(data.buckets||{single:data}))Object.assign(records,bucket.records||{});}
const work=path.join(root,'Saved/v4-title-extras-'+Date.now());await fs.mkdir(path.join(work,'UserData'),{recursive:true});await fs.copyFile(resume,path.join(work,'UserData/savegames.json'));
const delay=ms=>new Promise(r=>setTimeout(r,ms)),checks=[];let probe,last;process.env.HB_PLAYER_SOAK_HOURS='1';
const keys={Enter:[13,'Enter'],Backspace:[8,'Backspace'],Tab:[9,'Tab'],w:[87,'KeyW'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],q:[81,'KeyQ'],e:[69,'KeyE'],c:[67,'KeyC']};
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(700);
 const call=(n,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+n)},${JSON.stringify(args)})`);
 const value=async n=>{const r=await call(n);assert.equal(typeof r?.outputs?.result,'string',JSON.stringify(r));return JSON.parse(r.outputs.result);};
 const stats=async()=>{last=await value('Stats');assert(!last.error,JSON.stringify(last));return last;};
 const sample=async()=>{const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(60);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=f+2,'input sampled',10000);};
 const tap=async k=>{const [windowsVirtualKeyCode,code]=keys[k];for(const type of ['keyDown','keyUp']){await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});await sample();}};
 const click=async r=>{const x=r[0]+r[2]/2,y=r[1]+r[3]/2;for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x,y,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}};
 const ui=async n=>probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="'+${JSON.stringify(n)}+'"]'),r=e?.getBoundingClientRect();return {visible:!!r?.width&&getComputedStyle(e).visibility!=='hidden',text:e?.textContent,color:e?getComputedStyle(e).color:null};})()`);
 const disk=async()=>{const d=JSON.parse(await fs.readFile(path.join(work,'UserData/savegames.json'),'utf8'));return JSON.parse(d.items[headKey]);};
 const assertCommon=(h,coins=saved.coins)=>{assert.equal(h.node,saved.node);assert.equal(h.coins,coins);assert.deepEqual(h.trialResults,saved.trialResults);};
 const types=[...archive.entries.filter(x=>x.chapter==='6').map(x=>x.type).sort(),4];assert.equal(types.at(-1),4);
 const titleState=await stats();assert.equal(titleState.mode,'title');if(!audioOnly){await click(titleLayout.mainRects[2]);assert((await ui('CsStatus')).visible);await click(titleLayout.chapterRects[6]);
 await tap('w');await tap('Enter');assert((await ui('RsHeader')).visible&&(await ui('RsHeader')).text.includes('최고 기록'));assert.equal((await ui('RsHeader')).color,'rgb(255, 255, 255)');const boundedResult=await value('TrialResultStats');assert(boundedResult.open&&boundedResult.history&&boundedResult.ledger.summary);assert.equal(boundedResult.ledger.best['6'].records,saved.trialResults.best['6'].records.length);assert.equal((await stats()).coins,titleState.coins);await delay(1900);await probe.capture('01-result-history.png');
 await tap('q');assert((await ui('RsSelected')).text.includes('기본 점수'));await tap('d');assert(Number((await ui('RsPage')).text.split('/')[0].trim())>1);await tap('Backspace');assert((await ui('CsParts')).visible);assertCommon(await disk());checks.push('actual chapter6 result history, details/paging/back return and no reward or canonical save mutation');
 await tap('Backspace');await tap('Backspace');assert((await ui('TmArt')).visible);
 }
 await click(titleLayout.mainRects[4]);await probe.until(async()=>!(await ui('GaStatus')).text.includes('준비 중'),'gallery reads actual normal history',60000);assert.equal((await stats()).mode,'gallery');await probe.capture('02-gallery-top.png');
 let expectedCoins=saved.coins;const purchased=[];
 const pick=async category=>{
  await click(galleryLayout.top[{event:0,artwork:2,bgm:3}[category]]);const rows=catalog.order[category];const index=rows.findIndex(id=>saved.gallery.available.includes(id)&&(category!=='event'||records[id].nodes.some(n=>actualRead.has(n)))&&(category!=='bgm'||records[id].cue!=='bgm_title'));assert(index>=0,'normal save must unlock '+category);
  for(let i=0;i<index;i++)await tap('s');return {id:rows[index],row:records[rows[index]],slot:Math.min(index,10)};
 };
 const buy=async item=>{
  await tap('Enter');if(item.row.price>0){assert((await ui('CwBody')).visible);await tap('Enter');assert(!(await ui('CwBody')).visible);assert.equal((await stats()).coins,expectedCoins,'No is the initial purchase choice');await tap('Enter');await tap('a');await tap('Enter');expectedCoins-=item.row.price;assert.equal((await stats()).coins,expectedCoins);}
  purchased.push(item.id);
 };
 const bgm=await pick('bgm');await buy(bgm);await tap('Enter');assert((await ui('GaPlaying'+bgm.slot)).visible,'selected unlocked track must show playing marker');const audioSamples=[];try{await probe.until(async()=>{const a=await probe.evaluate('window.hbPlayerDebug.audio()');audioSamples.push(a);assert.deepEqual(a.errors,[]);return a.state==='running'&&a.voices.some(v=>v.playing&&!v.virtual&&JSON.stringify(v).includes(bgm.row.cue)&&v.time>.25&&v.peak>.001)&&!a.voices.some(v=>v.playing&&JSON.stringify(v).includes('S_bgm_title.'))&&Object.values(a.levels).some(buses=>buses.music>.0001);},'selected music remains audible after previous title fade finishes',15000);}finally{await fs.writeFile(path.join(work,'gallery-audio.json'),JSON.stringify({cue:bgm.row.cue,samples:audioSamples},null,2));}await probe.capture('03-gallery-playing.png');await tap('Enter');assert(!(await ui('GaPlaying'+bgm.slot)).visible);await tap('Backspace');checks.push('gallery BGM purchase No/Yes, exact wallet deduction, playback indicator, nonzero selected PCM after previous title fade and stop through real input');
 if(!audioOnly){
 const art=await pick('artwork');await buy(art);await tap('Enter');assert((await ui('GaViewer')).visible);await probe.capture('04-gallery-artwork.png');await tap('Backspace');assert(!(await ui('GaViewer')).visible);await tap('Backspace');checks.push('actual unlocked artwork purchase/view/back restores gallery list');
 const event=await pick('event');await buy(event);if(!(await ui('Body')).visible)await tap('Enter');assert((await ui('Body')).visible);await probe.capture('05-gallery-replay.png');assert.equal((await stats()).node,saved.node);await tap('Backspace');assert(!(await ui('Body')).visible);await tap('Backspace');checks.push('only actually read event dialogue opens in replay and returns without advancing the main story');
 await tap('Backspace');assert((await ui('CwBody')).visible);await tap('a');await tap('Enter');await probe.until(async()=>(await ui('TmArt')).visible,'gallery commit/title',120000);let committed=await disk();assertCommon(committed,expectedCoins);for(const id of purchased)assert(committed.gallery.purchased.includes(id));await probe.capture('06-gallery-saved-title.png');checks.push('cooperative gallery save keeps original ending/paid result, persists purchases and deducts each cost once');
 await click(titleLayout.mainRects[2]);await click(titleLayout.chapterRects[6]);await tap('s');await tap('Enter');let d=(await stats()).difficulty;assert(d.open);await tap('a');const logic=(await stats()).difficulty.logic;await tap('s');await tap('d');const action=(await stats()).difficulty.action;await probe.capture('07-replay-difficulty.png');await tap('Backspace');assert((await ui('CsParts')).visible);assertCommon(await disk(),expectedCoins);
 await tap('Enter');await tap('s');await tap('s');await tap('Enter');const entry=archive.entries.find(e=>e.chapter==='6'&&e.type===types[1]);assert(entry);await probe.until(async()=>{const s=await stats();return !s.difficulty.open&&s.node===entry.node;},'exact reached archive restores',90000);await delay(800);let s=await stats();assert.equal(s.node,entry.node);assert.equal(s.coins,expectedCoins);assert.equal(s.difficulty.logic,logic);assert.equal(s.difficulty.action,action);assert(!(await ui('Title')).visible,'title wallpaper must not cover restored world');await probe.capture('08-exact-archive-entry.png');assertCommon(await disk(),expectedCoins);checks.push('chapter replay cancel leaves canonical save intact; confirmed reached investigation entry restores exact node with chosen difficulty and common wallet');
 await tap('Tab');await click([1000,460,90,40]);await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');await probe.until(async()=>(await stats()).mode==='credits','Continue stays canonical ending',60000);assert.equal((await stats()).coins,expectedCoins);checks.push('after archive replay Title/Continue returns to canonical ending, not the replay entry; wallet remains exact');
 }
 assert.deepEqual(await probe.evaluate(`Array.from(document.images).filter(i=>i.offsetWidth>0&&i.src&&i.complete&&i.naturalWidth===0).map(i=>i.src)`),[]);assert.deepEqual(probe.errors,[]);
 const report={ok:true,fixture:false,audioOnly,work,executable,resume,checks,purchased,coinsBefore:saved.coins,coinsAfter:expectedCoins,scope:audioOnly?'Only actual gallery purchase/play/stop and decoded selected music after previous title fade. No repeated result/archive/artwork/story traversal or whole listening acceptance.':'Focused actual completed normal-save title/results/gallery/reached-archive input routes. No chapter traversal, fabricated unlocks, gameplay success injection or exhaustive gallery/campaign acceptance.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,last,checks,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
