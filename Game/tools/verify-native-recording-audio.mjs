// Infrastructure proof, never a finished presentation clip or FPS benchmark.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {nativeWindowProbe} from './native-window-probe.mjs';
const exec=promisify(execFile),root=path.resolve(import.meta.dirname,'..');
const output=path.join(root,'Saved/native-panic-views-1793690486425/package');
const work=path.join(root,'Saved/native-recording-audio-'+Date.now());await fs.mkdir(work,{recursive:true});
const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));
const prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)};
process.env.YUMENO_NATIVE_QA_RECORD='1';
let p;
try{
 p=await nativeWindowProbe({source:output,prepared,work,maxFrames:null,heartbeatTimeoutMs:120000});
 await p.hiddenBorderless();await p.resize(1280,720);
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.mode==='title'&&!s.scenes.loading;},'native title ready',120000);
 await p.sampled(60);
 await fs.writeFile(path.join(work,'record.request'),JSON.stringify({name:'infrastructure',seconds:6,fps:12,stream:true,audio:true}),{flag:'wx'});
 const movie=await p.until(async()=>{await p.stats();return fs.readFile(path.join(work,'recordings/infrastructure/recording.json'),'utf8').then(JSON.parse,()=>false);},'actual picture and native mixer capture',120000);
 assert.equal(movie.audio,true);assert(movie.frames.length>=30);
 assert(movie.audioCapture.peak>.001,'Actual native mixer PCM must contain audible game samples');
 const offset=(movie.videoStarted-movie.audioCapture.beginAfter)/1000+movie.frames[0].elapsed;
 assert(offset>=0&&offset<1,'Measured picture/capture request offset is bounded');
 const video=path.join(work,'recordings/infrastructure/with-actual-game-audio.mp4');
 await exec('ffmpeg',['-hide_banner','-loglevel','error','-y','-i',movie.video,'-ss',offset.toFixed(6),'-i',movie.audioCapture.file,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',video],{windowsHide:true});
 const probe=JSON.parse((await exec('ffprobe',['-v','error','-show_streams','-show_format','-of','json',video],{windowsHide:true})).stdout);
 assert(probe.streams.some(s=>s.codec_type==='audio'&&s.sample_rate==='48000'));
 assert(probe.streams.some(s=>s.codec_type==='video'&&s.width===1280&&s.height===720));
 const runtime=await p.close();p=null;
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,work,video,frames:movie.frames.length,audio:movie.audioCapture,offsetSeconds:offset,streams:probe.streams.map(s=>({type:s.codec_type,codec:s.codec_name,duration:s.duration})),runtimeExit:runtime.exitCode??0,scope:'Infrastructure proof only: six seconds of actual title picture and actual native game mixer PCM. Not a completed gameplay presentation, not final UI acceptance, not an FPS test. No synthesized replacement soundtrack, desktop/microphone capture or engine edits.'},null,2));
 console.log(JSON.stringify({ok:true,work,actualAudio:true}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,scope:'Native recording infrastructure, not game UI acceptance'},null,2));throw error;
}finally{if(p)await p.close();}
