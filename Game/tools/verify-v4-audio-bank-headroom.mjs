// Technical PCM bounds for the already-approved cue bank; no listening/playtime claim.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),work=path.join(root,'Saved/v4-audio-bank-headroom-'+Date.now());
await fs.mkdir(work,{recursive:true});
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const mixer=JSON.parse(await fs.readFile(path.join(root,'Assets/Audio/MX_Yumeno.hbaudiomixer.json'),'utf8'));
const assets=(await fs.readdir(path.join(root,'Assets/Audio'))).filter(f=>/^S_.*\.hbaudioasset\.json$/.test(f));
const packaged=process.argv.includes('--packaged'),gain=Number(process.argv.find(a=>a.startsWith('--gain='))?.split('=')[1]??.5),rows=[];
const baselinePath=process.argv.find(a=>a.startsWith('--focus-from='))?.slice('--focus-from='.length),baseline=baselinePath?JSON.parse(await fs.readFile(path.resolve(baselinePath),'utf8')):null;
const selected=new Set(['S_bgm_title.hbaudioasset.json']);if(baseline)for(const bus of new Set(baseline.rows.map(r=>r.bus)))selected.add(baseline.rows.filter(r=>r.bus===bus).sort((a,b)=>b.peak-a.peak)[0].asset);
const toRender=baseline?assets.filter(f=>selected.has(f)):assets;
assert(gain>0&&gain<=1);let probe;
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 const moduleURL=await probe.evaluate(`new URL('/prototype/audio-mixer.js',location.href).href`);
 for(const file of toRender){
  const asset=JSON.parse(await fs.readFile(path.join(root,'Assets/Audio',file),'utf8')),bytes=await fs.readFile(path.join(root,asset.clip));
  const actualGain=packaged?asset.volume:gain;assert(actualGain>0&&actualGain<=1);
  const result=await probe.evaluate(`(async()=>{
   const {AudioMixerGraph}=await import(${JSON.stringify(moduleURL)}),data=${JSON.stringify(mixer)},ctx=new OfflineAudioContext(2,1,48000),buffer=await ctx.decodeAudioData(Uint8Array.from(atob(${JSON.stringify(bytes.toString('base64'))}),c=>c.charCodeAt(0)).buffer);
   const render=new OfflineAudioContext(buffer.numberOfChannels,buffer.length,buffer.sampleRate),graph=new AudioMixerGraph(render,data),s=render.createBufferSource(),g=render.createGain();s.buffer=buffer;g.gain.value=${actualGain};s.connect(g);g.connect(graph.input(${JSON.stringify(asset.bus)}));s.start();const out=await render.startRendering();let peak=0,power=0,over=0,samples=0;for(let c=0;c<out.numberOfChannels;c++)for(const v of out.getChannelData(c)){peak=Math.max(peak,Math.abs(v));power+=v*v;over+=Math.abs(v)>1;samples++;}graph.dispose();return{duration:buffer.duration,peak,rms:Math.sqrt(power/samples),over,samples};
  })()`);
  rows.push({asset:file,clip:asset.clip,bus:asset.bus,gain:actualGain,...result});
  if(rows.length%20===0)console.log(JSON.stringify({files:rows.length,total:assets.length,maxPeak:Math.max(...rows.map(r=>r.peak))}));
 }
 const report={ok:rows.every(r=>r.over===0&&r.rms>0),work,executable,comparisonGain:packaged?null:gain,gainSource:packaged?'generated asset descriptors':'comparison override',packaged,baseline:baselinePath??null,rows,errors:probe.errors,scope:baseline?'Focused re-render of the loudest prior full-bank cue per bus and title with generated asset gain. All exposed mixer levels maximum. Offline WebView PCM; unchanged DSP is linear with compressors disabled. Other bank bounds are scaled predictions, not a second full render.':'Full approved single-cue PCM through the existing real WebView AudioMixerGraph, all exposed levels at maximum. Offline rendering; no human listening, multi-voice bound or actual game-duration claim. Gain is a proposed asset headroom comparison unless packaged asset volume is separately verified.'};
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));assert.deepEqual(probe.errors,[]);console.log(JSON.stringify({ok:report.ok,work,files:rows.length,maxPeak:Math.max(...rows.map(r=>r.peak)),failures:rows.filter(r=>r.over).map(r=>({asset:r.asset,peak:r.peak,over:r.over}))}));assert(report.ok);
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,rows,probeErrors:probe?.errors},null,2));throw error;}finally{await probe?.stop?.();}
