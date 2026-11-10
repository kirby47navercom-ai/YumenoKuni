// Read pixels only from our exact native HWND. Never capture desktop/other apps.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {execFile,spawn} from 'node:child_process';import {promisify} from 'node:util';import {createHash} from 'node:crypto';import {once} from 'node:events';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {caseSaveCatalogue,publishCaseSave} from './native-case-saves.mjs';
import {beginOwnedMovie} from './native-window-recording.mjs';
const exec=promisify(execFile),root=path.resolve(import.meta.dirname,'..'),output=path.join(root,'Saved/native-panic-views-1793690486425/package'),work=path.join(root,'Saved/owned-window-capture-'+Date.now());await fs.mkdir(work,{recursive:true});
const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8')),prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)};
const moduleArg=process.argv.find(a=>a.startsWith('--game-module='))?.slice(14);
if(moduleArg){const from=path.resolve(root,moduleArg);assert(from.startsWith(path.join(root,'Saved')+path.sep));const file=manifest.nativeModules[0].binary,bytes=await fs.readFile(from);await fs.writeFile(path.join(output,file),bytes);Object.assign(manifest.files.find(r=>r.path===file),{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));}
const report={work,method:'FFmpeg gdigrab exact owned HWND, hidden window, no desktop or engine edits',accepted:false};let p;
try{
 if(process.argv.includes('--movie')||process.argv.includes('--controlled'))process.env.YUMENO_NATIVE_QA_RECORD='1';
 p=await nativeWindowProbe({source:output,prepared,work,maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(1280,720);
 await publishCaseSave({work,session:work,catalogue:await caseSaveCatalogue(),taskId:'T3-NS-A11'});await p.tap('s');await p.tap('w');await p.tap('c');await p.until(async()=>(await p.stats()).taskId==='T3-NS-A11','retained actual trial input',120000);await p.tap('F2');await p.key('Control',true);
 for(let i=0;i<120;i++){const s=await p.stats();assert(!s.error,s.error);if(!s.taskQueue&&s.taskInputArmed&&!s.presentation?.nonstopIntro)break;await p.tap('Enter');}
 await p.key('Control',false);await p.sampled(90);report.windowState=await p.windowState();assert.equal(report.windowState[0],false);assert.equal(report.windowState[2],false);
 report.hwnd=String(p.windowHandle());assert(/^[1-9][0-9]*$/.test(report.hwnd));await p.capture('native-reference');
 if(process.argv.includes('--controlled')){
  report.method='Reusable exact-owned-window video and actual mixer start/stop';
  const movie=await beginOwnedMovie(p,'controlled-proof',{seconds:15});
  await new Promise(resolve=>setTimeout(resolve,6000));report.movie=await movie.finish();
 }else if(process.argv.includes('--movie')){
  report.method='Exact owned background world+UI WGC video, actual game mixer audio';
  const directory=path.join(work,'recordings','capture-proof');
  await fs.writeFile(path.join(work,'record.request'),JSON.stringify({name:'capture-proof',seconds:20,fps:30,audio:true,audioOnly:true}));
  await p.until(async()=>!!(await fs.stat(path.join(directory,'started.json')).catch(()=>null)),'actual mixer start',15000);
  const video=path.join(work,'video.mp4'),helper=spawn(path.join(root,'Saved/game-trial-work-20261102/owned-window-wgc.exe'),[String(p.child.pid),report.hwnd,'180','--background'],{windowsHide:true,stdio:['ignore','pipe','pipe']});
  const encoder=spawn('ffmpeg',['-hide_banner','-loglevel','error','-y','-use_wallclock_as_timestamps','1','-f','image2pipe','-vcodec','bmp','-framerate','30','-i','pipe:0','-fps_mode','vfr','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-an',video],{windowsHide:true,stdio:['pipe','ignore','pipe']});
  let helperLog='',encoderLog='';helper.stderr.on('data',c=>helperLog+=c);encoder.stderr.on('data',c=>encoderLog+=c);encoder.stdin.on('error',()=>{});helper.stdout.pipe(encoder.stdin);
  const helperDone=once(helper,'close'),encoderDone=once(encoder,'close');
  assert.equal((await helperDone)[0],0,helperLog);assert.equal((await encoderDone)[0],0,encoderLog);
  await fs.writeFile(path.join(work,'record.stop'),'stop');
  await p.until(async()=>!!(await fs.stat(path.join(directory,'recording.json')).catch(()=>null)),'actual mixer stop',20000);
  const started=JSON.parse(await fs.readFile(path.join(directory,'started.json'),'utf8')),capture=JSON.parse(helperLog.trim().split('\n').at(-1)),audio=JSON.parse(await fs.readFile(path.join(directory,'audio.json'),'utf8'));
  const offset=(capture.firstFrameUnixMS-started.startedUnixMS)/1000;assert(offset>=0&&offset<5);assert(audio.peak>0,'Actual mixer must contain audible samples');
  const movie=path.join(work,'actual-game.mp4');await exec('ffmpeg',['-hide_banner','-loglevel','error','-y','-i',video,'-ss',String(offset),'-i',audio.file,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-shortest','-movflags','+faststart',movie],{windowsHide:true,timeout:30000});
  const info=JSON.parse((await exec('ffprobe',['-v','error','-show_streams','-show_format','-of','json',movie],{windowsHide:true})).stdout);
  assert.equal(info.streams.length,2);assert(+info.format.duration>=5.5);report.movie={file:movie,capture,audioPeak:audio.peak,audioOffsetSeconds:offset,duration:+info.format.duration,streams:info.streams.map(s=>({type:s.codec_type,codec:s.codec_name,rate:s.avg_frame_rate})),scope:'Pipeline proof only; not final presentation coverage. Wall-clock start alignment is approximate and requires motion/audio review.'};
 }else if(process.argv.includes('--wgc')){
  report.method='Windows.Graphics.Capture exact owned HWND, no desktop or engine edits';report.attempts=[];
  for(const background of [false,true]){
   const args=[String(p.child.pid),report.hwnd,'1',...(background?['--background']:[])];let captured;
   try{captured=await exec(path.join(root,'Saved/game-trial-work-20261102/owned-window-wgc.exe'),args,{windowsHide:true,timeout:16000,maxBuffer:32*1024*1024,encoding:'buffer'});}catch(error){report.attempts.push({background,error:String(error.stderr||error.message)});continue;}
   const key=background?'wgc-background':'wgc-hidden',bmp=path.join(work,key+'.bmp');await fs.writeFile(bmp,captured.stdout);await exec('ffmpeg',['-hide_banner','-loglevel','error','-y','-i',bmp,path.join(work,key+'.png')],{windowsHide:true,timeout:10000});report.attempts.push({background,file:key+'.png',metadata:captured.stderr.toString()});
  }
 }else{
  const result=await exec('ffmpeg',['-hide_banner','-loglevel','error','-y','-f','gdigrab','-framerate','1','-i','hwnd='+report.hwnd,'-frames:v','1',path.join(work,'gdi-own-window.png')],{windowsHide:true,timeout:12000,maxBuffer:65536});report.stderr=result.stderr;
 }
 report.captured=true;report.accepted=false;report.pending='Direct compare with native-reference before accepting movie capture';
}catch(error){report.error=error.message;}
finally{await p?.close().catch(error=>report.shutdownError=error.message);await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));}
