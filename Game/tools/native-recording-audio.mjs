// Actual game mixer capture through the retained engine's public audio hooks.
// QA only: no soundtrack reconstruction and no desktop/microphone capture.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';

export async function startRecordingAudio(world, runner, output, seconds) {
 if(seconds+4>67108864/(48000*4))throw Error('Split native audio recordings at scene boundaries before the 64 MiB PCM limit');
 const require=createRequire(runner);
 const audio=await import(pathToFileURL(require.resolve('node-web-audio-api')));
 if(!globalThis.AudioWorkletNode)globalThis.AudioWorkletNode=audio.AudioWorkletNode;
 // The retained Node implementation rejects URL objects and imports Windows
 // drive paths as ESM schemes. Its supported Blob route is QA-local.
 // Loading a scene can block this diagnostic process longer than the mixer
 // recorder's four 4096-frame blocks. Reserve a bounded 16-second recycle
 // pool in this QA worklet, preserving every sample rather than accepting a
 // truncated recording. Installed/original engine files remain unchanged.
 const proto=audio.AudioWorklet.prototype;
 if(!proto.qaRecordingURLAdapter){const add=proto.addModule;proto.addModule=async function(url,...args){if(!(url instanceof URL)||url.protocol!=='file:')return add.call(this,url,...args);let bytes=await fs.readFile(fileURLToPath(url));if(url.pathname.endsWith('/audio-capture-worklet.js')){const source=bytes.toString('utf8');if(!source.includes("registerProcessor('hb-mix-capture'")||source.split('length:3').length!==2||source.split('pool.length<3').length!==2)throw Error('Re-review changed QA mixer worklet before adapting its recycle pool');bytes=Buffer.from(source.replace('length:3','length:192').replace('pool.length<3','pool.length<192'));}const blob=URL.createObjectURL(new Blob([bytes],{type:'text/javascript'}));try{return await add.call(this,blob,...args);}finally{URL.revokeObjectURL(blob);}};Object.defineProperty(proto,'qaRecordingURLAdapter',{value:true});}
 if(typeof world?.hooks.beginAudioCapture!=='function')throw Error('Native game mix capture hook unavailable');
 const before=performance.now(),beginUnixBefore=Date.now();
 await world.hooks.beginAudioCapture({maxSeconds:seconds+4,maxBytes:67108864});
 return {world,output,beginBefore:before,beginAfter:performance.now(),beginUnixBefore,beginUnixAfter:Date.now()};
}

export async function stopRecordingAudio(recording) {
 const {world,output}=recording;
 let value;
 try{value=await world.hooks.endAudioCapture();}finally{world.hooks.acceptAudioCapture();}
 if(value.info.reason!=='stopped'||value.info.frames<4800)throw Error('Incomplete actual game audio capture: '+JSON.stringify(value.info));
 const bytes=Buffer.from(value.bytes);
 if(bytes.toString('ascii',0,4)!=='RIFF')throw Error('Native game capture did not return WAV');
 let peak=0,sum=0;
 for(let i=44;i<bytes.length;i+=2){const sample=bytes.readInt16LE(i)/32768;peak=Math.max(peak,Math.abs(sample));sum+=sample*sample;}
 const file=path.join(output,'actual-game-mix.wav');await fs.writeFile(file,bytes);
 const info={...value.info,file,peak,rms:Math.sqrt(sum/Math.max(1,(bytes.length-44)/2)),beginBefore:recording.beginBefore,beginAfter:recording.beginAfter,beginUnixBefore:recording.beginUnixBefore,beginUnixAfter:recording.beginUnixAfter,
  qaRecyclePoolBlocks:192,scope:'PCM captured from the actual native game mixer, including its bus gains/effects. QA-local bounded recycle pool protects scene-load stalls; sample processing unchanged. No installed/original engine edits, desktop audio, synthetic soundtrack or original V3 execution.'};
 await fs.writeFile(path.join(output,'audio.json'),JSON.stringify(info,null,2));return info;
}
