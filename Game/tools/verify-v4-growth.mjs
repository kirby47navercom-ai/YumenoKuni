// Focused native growth proof. Fixtures mark explicit XP boundaries and authored UI entries.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/v4-growth-'+Date.now());await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms)),checks=[];let probe;process.env.HB_PLAYER_SOAK_HOURS='1';
const keys={w:[87,'KeyW'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],c:[67,'KeyC'],Tab:[9,'Tab'],Enter:[13,'Enter'],Backspace:[8,'Backspace']};
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(500);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const value=async name=>JSON.parse((await call(name)).outputs.result),stats=async()=>{const s=await value('Stats');assert(!s.error,JSON.stringify(s));return s;},progress=()=>value('PlayerProgressStats'),growth=()=>value('GrowthStats');
 const key=async(k,type)=>{const [windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
 const sample=async()=>{const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(65);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=f+2,'sampled input',10000);};
 const tap=async k=>{await key(k,'keyDown');await sample();await key(k,'keyUp');await sample();};
 const click=async(x,y)=>{for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x,y,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}};
 const ui=name=>probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="${name}"]'),i=e?.querySelector('img');return {visible:!!e&&getComputedStyle(e).visibility!=='hidden'&&!!e.getBoundingClientRect().width,text:e?.textContent,asset:i?.dataset.asset,loaded:!!i&&i.complete&&i.naturalWidth>0};})()`);
 await call('DebugV4MapFixture');await call('DebugPlayerProgressFixture',{xp:499});assert.equal((await progress()).displayed,1);
 await key('w','keyDown');await probe.until(async()=>(await progress()).level===2,'accepted walking crosses actual XP threshold',15000);await key('w','keyUp');await sample();
 await probe.until(async()=>(await progress()).popup===2,'level-up notification',5000);let p=await progress();assert.equal(p.displayed,2);assert.equal(p.capacity,2);assert(p.gauge.endsWith('gauge_100.svg'));assert((await ui('FLevelUp')).visible);await probe.capture('01-earned-level-up.png');
 checks.push('actual map movement, seeded499 boundary, crosses500; actual Lv/SP2, displayed2 and full gauge during source controller notification');
 await tap('Tab');assert.equal((await stats()).mode,'pad');const frozen=await progress();await delay(450);p=await progress();for(const k of ['xp','popup','frame','hold'])assert.equal(p[k],frozen[k]);assert.equal((await ui('FLevelUp')).visible,false);await probe.capture('02-pad-pauses-level-up.png');await tap('Tab');
 await probe.until(async()=>(await progress()).popup===0,'notification completes only after admitted updates',10000);p=await progress();assert.equal(p.displayed,2);assert(!p.gauge.endsWith('gauge_100.svg'));assert.equal((await ui('FLevelUp')).visible,false);checks.push('Pad hides and freezes notification controller and XP; closing resumes in/hold/out and fractional gauge returns only after completion');
 await call('DebugV4GiftFixture');p=await progress();assert.equal(p.xp,200);assert.equal(p.claims,1);checks.push('explicit canonical completed-FTE fixture awards one GetKakera200 claim, separately from gifts or arbitrary dialogue');
 await call('DebugV4CompletionFixture');await probe.until(async()=>(await growth()).used===2,'equipped fixture',5000);assert.equal((await growth()).capacity,2);assert.equal((await progress()).capacity,2);
 await tap('Tab');assert.equal((await stats()).mode,'pad');await click(1047,480);assert.equal((await stats()).padPage,5);await padSystemAction(stats,tap,'save');await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');
 p=await progress();assert.equal(p.xp,500);assert.equal(p.level,2);assert.equal(p.displayed,2);assert.equal(p.popup,0);assert.equal((await growth()).used,2);assert.equal((await growth()).capacity,2);checks.push('real manual save/Title/Continue preserves Lv2/SP2/equipped cost2 with growthv2; restored display is synchronized and does not replay level-up');
 const missing=await probe.evaluate(`Array.from(document.images).filter(i=>i.offsetWidth>0&&i.src&&i.complete&&i.naturalWidth===0).map(i=>i.src)`);assert.deepEqual(missing,[]);assert.deepEqual(probe.errors,[]);
 const report={ok:true,fixture:true,executable,work,checks,scope:'Focused growth/notification/Pad/SP and save checks; actual walking with seeded XP499, explicit completed-FTE and equipped authored-task fixtures. No replay of previous chapters, full campaign, every XP caller, exact original pixels or original SE048 identity.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,checks,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
