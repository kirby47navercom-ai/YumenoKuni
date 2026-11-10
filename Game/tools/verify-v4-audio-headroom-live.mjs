// Real own-player options input and streamed PCM meters, no gameplay-state fixture.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),work=path.join(root,'Saved/v4-audio-headroom-live-'+Date.now());await fs.mkdir(work,{recursive:true});
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const keys={o:[79,'KeyO'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],Backspace:[8,'Backspace']},samples=[];
const delay=ms=>new Promise(r=>setTimeout(r,ms));let probe;
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 const value=async name=>JSON.parse((await probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},{})`)).outputs.result);
 const tap=async key=>{const [windowsVirtualKeyCode,code]=keys[key];for(const type of ['keyDown','keyUp']){const frame=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await probe.cdp('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode});await delay(65);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=frame+2,'input frame',10000);}};
 const audio=async label=>{const a=await probe.evaluate('window.hbPlayerDebug.audio()');assert.deepEqual(a.errors,[]);samples.push({label,...a});return a;};
 await tap('o');assert((await value('Stats')).options.open);let o=await value('OptionsStats');assert.equal(o.values.music,6);
 for(let i=0;i<4;i++)await tap('d');o=await value('OptionsStats');assert.equal(o.values.music,10);assert(Math.abs(o.db.Music)<.001);
 await probe.until(async()=>{const a=await audio('music-maximum');return a.state==='running'&&a.voices.some(v=>v.playing&&v.clip.includes('S_bgm_title.')&&v.peak>.01)&&Object.values(a.levels).some(b=>b.music>.01);},'actual streamed title maximum',15000);
 for(let i=0;i<12;i++){await delay(250);await audio('music-maximum');}
 await tap('d');o=await value('OptionsStats');assert.equal(o.values.music,0);assert(o.db.Music<=-79.9);await delay(350);
 const muted=await audio('music-muted');assert(Object.values(muted.levels).every(b=>b.music<1e-6));
 await tap('a');assert.equal((await value('OptionsStats')).values.music,10);
 await tap('s');for(let i=0;i<4;i++)await tap('d');o=await value('OptionsStats');assert.equal(o.values.sfx,10);assert(Math.abs(o.db.SFX)<.001&&Math.abs(o.db.UI)<.001);
 const full=await audio('music-and-ui-maximum');assert(full.voices.some(v=>v.clip.includes('ui_'))||full.recent.some(v=>v.clip.includes('ui_')));
 await tap('d');o=await value('OptionsStats');assert.equal(o.values.sfx,0);assert(o.db.SFX<=-79.9&&o.db.UI<=-79.9);await delay(350);const seMuted=await audio('se-muted');assert(Object.values(seMuted.levels).every(b=>b.sfx<1e-6&&b.ui<1e-6));
 await tap('Backspace');assert(!(await value('Stats')).options.open);
 const titlePeaks=samples.flatMap(s=>s.voices.filter(v=>v.clip.includes('S_bgm_title.')).map(v=>v.peak));assert(Math.max(...titlePeaks)>.01&&Math.max(...titlePeaks)<.7);assert.deepEqual(probe.errors,[]);
 const report={ok:true,executable,work,samples,maximumObservedTitleVoicePeak:Math.max(...titlePeaks),fixture:false,gameStateInjected:false,scope:'Physical source-options input in the packaged own player. Actual streamed title/UI voices, max-volume independent readback, music mute and SE/UI mute, return to title. Voice peak is pre-bus analyser history and bus levels are RMS; not a full output peak bound or whole-bank listening certificate.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,work,titlePeak:report.maximumObservedTitleVoicePeak}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,samples,probeErrors:probe?.errors},null,2));throw error;}finally{await probe?.stop?.();}
