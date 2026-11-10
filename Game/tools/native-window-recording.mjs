// QA recording only: exact owned off-screen HWND + owned transparent UI HWND.
// Game audio comes from the game's mixer. Never reads a desktop or microphone.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawn,execFile} from 'node:child_process';
import {once} from 'node:events';
import {promisify} from 'node:util';
const exec=promisify(execFile),root=path.resolve(import.meta.dirname,'..');
export async function beginOwnedMovie(p,name,{seconds=300}={}){
 assert(/^[a-z0-9_-]{1,64}$/.test(name));assert(seconds>=2&&seconds<=300);
 assert.equal((await p.windowState())[0],false,'Owned movie starts from hidden player');
 const directory=path.join(p.work,'recordings',name),stop=path.join(directory,'window.stop');
 await fs.mkdir(directory,{recursive:true});await fs.rm(stop,{force:true});
 await fs.writeFile(path.join(p.work,'record.request'),JSON.stringify({name,seconds:seconds+3,fps:30,stream:true,audio:true,audioOnly:true}),{flag:'wx'});
 await p.until(async()=>!!(await fs.stat(path.join(directory,'started.json')).catch(()=>null)),'actual mixer recording started',15000);
 const video=path.join(directory,'window.mp4');
 const encoder=spawn('ffmpeg',['-hide_banner','-loglevel','error','-y','-use_wallclock_as_timestamps','1','-f','image2pipe','-vcodec','bmp','-framerate','30','-i','pipe:0','-fps_mode','vfr','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-an',video],{windowsHide:true,stdio:['pipe','ignore','pipe']});
 const helper=spawn(path.join(root,'Saved/game-trial-work-20261102/owned-window-wgc.exe'),[String(p.child.pid),String(p.windowHandle()),String(Math.ceil(seconds*31)),'--background',stop],{windowsHide:true,stdio:['ignore','pipe','pipe']});
 let helperLog='',encoderLog='',readyResolve;const ready=new Promise(resolve=>readyResolve=resolve);helper.stderr.on('data',c=>{helperLog+=c;for(const line of helperLog.split('\n')){try{const event=JSON.parse(line);if(event.event==='first-frame')readyResolve(event.unixMS);}catch{}}});encoder.stderr.on('data',c=>encoderLog+=c);encoder.stdin.on('error',()=>{});helper.stdout.pipe(encoder.stdin);
 const helperDone=once(helper,'close'),encoderDone=once(encoder,'close');
 let readyTimer,firstFrame;
 try{firstFrame=await Promise.race([ready,helperDone.then(()=>{throw Error('Owned capture exited before first frame: '+helperLog);}),new Promise((_,reject)=>{readyTimer=setTimeout(()=>reject(Error('Owned capture first frame timeout')),15000);})]);}catch(error){helper.kill();encoder.kill();await fs.writeFile(path.join(p.work,'record.stop'),'stop');throw error;}finally{clearTimeout(readyTimer);}
 return {directory,started:firstFrame,async finish(){
  await fs.writeFile(stop,'stop');
  const timeout=setTimeout(()=>{helper.kill();encoder.kill();},20000);
  try{
   assert.equal((await helperDone)[0],0,helperLog);assert.equal((await encoderDone)[0],0,encoderLog);
   await fs.writeFile(path.join(p.work,'record.stop'),'stop');
   await p.until(async()=>!!(await fs.stat(path.join(directory,'recording.json')).catch(()=>null)),'actual mixer recording stopped',20000);
   const capture=JSON.parse(helperLog.trim().split('\n').at(-1)),audio=JSON.parse(await fs.readFile(path.join(directory,'audio.json'),'utf8'));
   assert(capture.frames>=2);assert(audio.peak>0,'Silent audio is not an accepted game-mix recording');
   const audioStart=(audio.beginUnixBefore+audio.beginUnixAfter)/2;
   const offset=(capture.firstFrameUnixMS-audioStart)/1000;assert(offset>=0&&offset<5);
   const movie=path.join(directory,'actual-game.mp4');
   await exec('ffmpeg',['-hide_banner','-loglevel','error','-y','-i',video,'-ss',String(offset),'-i',audio.file,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',movie],{windowsHide:true,timeout:30000});
   const info=JSON.parse((await exec('ffprobe',['-v','error','-show_streams','-show_format','-of','json',movie],{windowsHide:true})).stdout);
   assert.equal(info.streams.length,2);const duration=+info.format.duration;
   assert(Math.abs(duration-(capture.lastFrameUnixMS-capture.firstFrameUnixMS)/1000)<.3,'Video must preserve actual wall-clock movement speed');
   const report={movie,capture,audioPeak:audio.peak,audioOffsetSeconds:offset,audioStartBoundMS:audio.beginUnixAfter-audio.beginUnixBefore,duration,streams:info.streams.map(s=>({type:s.codec_type,codec:s.codec_name,rate:s.avg_frame_rate})),scope:'Actual owned world/UI and actual mixer; approximate timestamp alignment bounded by audio-hook call, not a performance benchmark or full-feature acceptance.'};
   await fs.writeFile(path.join(directory,'movie.json'),JSON.stringify(report,null,2));return report;
  }finally{clearTimeout(timeout);if(helper.exitCode===null)helper.kill();if(encoder.exitCode===null)encoder.kill();}
 }};
}
