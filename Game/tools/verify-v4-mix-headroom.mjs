// Existing cue bytes through the shipped WebAudio mixer, rendered offline in our player.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),work=path.join(root,'Saved/v4-mix-headroom-'+Date.now());await fs.mkdir(work,{recursive:true});
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const mixer=JSON.parse(await fs.readFile(path.join(root,'Assets/Audio/MX_Yumeno.hbaudiomixer.json'),'utf8'));
const source=await fs.readFile(path.join(root,'Assets/Audio/bgm_title.ogg'));
let probe;process.env.HB_PLAYER_SOAK_HOURS='1';
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 const moduleURL=await probe.evaluate(`new URL('/prototype/audio-mixer.js',location.href).href`);
 const result=await probe.evaluate(`(async()=>{
  const {AudioMixerGraph,validAudioMixer}=await import(${JSON.stringify(moduleURL)}),bytes=Uint8Array.from(atob(${JSON.stringify(source.toString('base64'))}),c=>c.charCodeAt(0));
  const decoder=new OfflineAudioContext(2,1,48000),buffer=await decoder.decodeAudioData(bytes.buffer),rows=[];
  for(const level of [.6,1])for(const voices of [1,2])for(const profile of [{name:'original',gain:1,protection:false},{name:'headroom',gain:.5,protection:true}]){
   const data=${JSON.stringify(mixer)},master=data.buses.find(b=>b.id==='master');Object.assign(master,{compressor:profile.protection,threshold:-9,ratio:20,attack:0,release:.15});data.buses.find(b=>b.id==='music').volumeDb=20*Math.log10(level);if(!validAudioMixer(data))throw Error('Invalid comparison mixer');
   const ctx=new OfflineAudioContext(buffer.numberOfChannels,buffer.length,buffer.sampleRate),graph=new AudioMixerGraph(ctx,data);for(let i=0;i<voices;i++){const s=ctx.createBufferSource(),g=ctx.createGain();g.gain.value=profile.gain;s.buffer=buffer;s.connect(g);g.connect(graph.input('music'));s.start(0);}const output=await ctx.startRendering();let peak=0,power=0,over=0,samples=0;for(let c=0;c<output.numberOfChannels;c++)for(const value of output.getChannelData(c)){peak=Math.max(peak,Math.abs(value));power+=value*value;over+=Math.abs(value)>1;samples++;}rows.push({level,voices,profile:profile.name,assetGain:profile.gain,peak,rms:Math.sqrt(power/samples),samplesOverFullScale:over,samples});graph.dispose();
  }return {sourceDuration:buffer.duration,rows,scope:'Actual original approved title PCM through the packaged engine AudioMixerGraph in OfflineAudioContext. Two identical concurrent voices are a worst-case aligned overlap fixture, not a claim of ordinary live playback.'};
 })()`);
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,work,executable,...result},null,2));assert.deepEqual(probe.errors,[]);console.log(JSON.stringify({work,...result}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,probeErrors:probe?.errors},null,2));throw error;}finally{await probe?.stop?.();}
