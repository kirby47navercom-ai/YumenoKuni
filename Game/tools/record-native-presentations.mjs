// Real sequential native frames, not a slideshow of previous screenshots.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';import {promisify} from 'node:util';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {caseSaveCatalogue,publishCaseSave} from './native-case-saves.mjs';
const exec=promisify(execFile),root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),out=path.join(repo,'연출 영상');
const arg=p=>process.argv.find(v=>v.startsWith(p))?.slice(p.length),only=arg('--only=')?.split(',');
const build=JSON.parse(await fs.readFile(path.join(root,'Saved/game-trial-work-20261102/current-flat-build-result.json'),'utf8'));
const work=path.join(root,'Saved/native-video-'+Date.now());await fs.mkdir(work,{recursive:true});await fs.mkdir(out,{recursive:true});
process.env.YUMENO_NATIVE_QA_RECORD='1';
const prepared=await createOwnedNativePackage({source:build.output,work,stats:true});
const cases=JSON.parse(await fs.readFile(path.join(root,'Saved/native-task-checkpoints.json'),'utf8'));
const names={nonstop:'01-논스톱-논의',panic:'02-패닉-논의',showdown:'03-반론-쇼다운',mindmine:'04-발굴-이매지네이션',anagram:'05-섬광-애너그램',scrum:'06-논의-스크럼',armament:'07-이론무장',climax:'08-클라이맥스-추리',vote:'09-인물-투표',person:'10-인물-지목',spot:'11-지점-지목',bullet:'12-증거-제시',choice:'13-정답-선택',reasoning:'14-추리-연결',lie:'15-우소다마',daily:'16-프롤로그-대화','choice-daily':'17-자유행동-선택',explore:'18-탐색-이동'};
const previous=await fs.readFile(path.join(out,'manifest.json'),'utf8').then(JSON.parse,()=>null);
const clips=previous?.build===build.id?previous.clips:[],failures=[];let p;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const read=async file=>{try{return JSON.parse(await fs.readFile(file,'utf8'));}catch{return null;}};
async function report(){await fs.writeFile(path.join(work,'report.json'),JSON.stringify({build:build.id,work,clips,failures,audio:false,scope:'Continuous actual native frames from isolated current shipping game. No original save changes, no current manuscript overlays. Video timestamps preserve the recorded cadence; recording overhead is not an FPS benchmark.'},null,2));await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify({build:build.id,clips,failures,audio:false},null,2));}
async function start(name,resume){p=await nativeWindowProbe({source:build.output,prepared,work:path.join(work,name),resume,maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(640,360);}
async function close(){await p?.close();p=null;}
async function record(name,label,seconds,action){
 assert(/^[a-z0-9_-]{1,64}$/.test(name),'ASCII internal recording key required');
 const directory=path.join(p.work,'recordings',name),finished=path.join(directory,'recording.json');
 await fs.writeFile(path.join(p.work,'record.request'),JSON.stringify({name,seconds,fps:12}),{flag:'wx'});
 const running=Date.now();let nextAction=0;
 const movie=await p.until(async()=>{const r=await read(finished);if(r)return r;const s=await p.stats();assert(!s.error,s.error);if(action&&Date.now()-nextAction>800){nextAction=Date.now();await action(s,(Date.now()-running)/1000);}return false;},'native movie '+name,seconds*5000+60000,80);
 assert(movie.frames.length>=8,'Recording must contain sequential actual frames');
 const concat=['ffconcat version 1.0'];
 for(let i=0;i<movie.frames.length;i++){const f=movie.frames[i],next=movie.frames[i+1];concat.push("file '"+f.file+"'",'duration '+Math.max(.001,(next?.elapsed??f.elapsed+.083333)-f.elapsed).toFixed(6));}
 concat.push("file '"+movie.frames.at(-1).file+"'");const input=path.join(directory,'frames.ffconcat');await fs.writeFile(input,concat.join('\n')+'\n');
 const stem=names[name]||name,video=path.join(out,stem+'.mp4'),gif=path.join(out,stem+'.gif');
 await exec('ffmpeg',['-hide_banner','-loglevel','error','-y','-safe','0','-i',input,'-fps_mode','vfr','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart','-an',video],{windowsHide:true,maxBuffer:2097152});
 await exec('ffmpeg',['-hide_banner','-loglevel','error','-y','-i',video,'-filter_complex','fps=10,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3','-loop','0',gif],{windowsHide:true,maxBuffer:2097152});
 const row={name,label,video:path.relative(repo,video).replaceAll('\\','/'),gif:path.relative(repo,gif).replaceAll('\\','/'),frames:movie.frames.length,seconds:movie.frames.at(-1).elapsed,captureFPS:(movie.frames.length-1)/movie.frames.at(-1).elapsed,width:movie.frames[0].width,height:movie.frames[0].height,audio:false,recording:finished,build:build.id};const existing=clips.findIndex(c=>c.name===name);if(existing>=0)clips.splice(existing,1);clips.push(row);await report();console.log(JSON.stringify(row));
}
for(const name of Object.keys(names)){
 if(only&&!only.includes(name))continue;const row=cases[name];if(!row)continue;
 try{
  await start(name,path.resolve(repo,row.file));await p.tap('c');
  await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.mode==='trial'&&s.taskId===row.task;},'saved '+name,120000);
  for(let i=0;i<80&&(await p.stats()).taskQueue;i++)await p.tap('Enter');
  await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return !s.taskQueue&&s.taskInputArmed;},'armed '+name,120000);
  if(name!=='nonstop')await p.until(async()=>{const s=await p.stats();return !s.presentation.nonstopIntro&&s.auto.kind!=='wait';},'entrance '+name,60000);
  await p.sampled(name==='nonstop'?3:60);
  let actions=0;
  await record(name,names[name].slice(3),name==='nonstop'?18:12,async s=>{
   actions++;
   if(s.presentation.nonstopIntro||s.auto?.kind==='wait')return;
   if(['choice','reasoning','person','vote','bullet'].includes(name)){await p.tap(['person','vote'].includes(name)?'d':actions%4===0?'w':'s');return;}
   if(name==='lie'){
    if(actions===3)await p.key('Space',true);
    if(actions===7){await p.click(460,320);await p.key('Space',false);}
    if(actions>8&&s.taskQueue)await p.tap('Enter');
    return;
   }
   if(['nonstop','panic'].includes(name)){if(actions%4===0){await p.key('Shift',true);}if(actions%4===1)await p.key('Shift',false);return;}
   if(s.auto?.kind==='click'){await p.click(s.auto.x,s.auto.y);return;}
   if(name==='climax'){await p.tap(actions%2?'d':'s');return;}
   if(name==='armament'){await p.tap(actions%2?'d':'a');return;}
   if(name==='showdown'){await p.tap(actions%2?'a':'d');return;}
   await p.tap(actions%2?'d':'a');
  });await p.key('Space',false);await p.key('Shift',false);await close();
 }catch(error){failures.push({name,error:error.stack});await close().catch(()=>{});await report();console.error(name,error.message);}
}
if(!only||only.includes('daily')){
 try{await start('daily');await p.tap('Enter');await p.tap('s');await p.tap('s');await p.tap('Enter');await p.until(async()=>{const s=await p.stats();return s.world?.active&&!s.scenes.loading;},'fresh daily',120000);await p.sampled(40);await record('daily','프롤로그 대화·인물 전환',22,async s=>{if(s.mode==='story')await p.tap('Enter');});await close();}
 catch(error){failures.push({name:'daily',error:error.stack});await close().catch(()=>{});await report();}
}
if(!only||only.includes('choice-daily')){
 try{const catalogue=await caseSaveCatalogue(),rows=(await fs.readFile(path.join(catalogue.fixtureRoot,'menu-fixtures.jsonl'),'utf8')).trim().split('\n').map(JSON.parse),row=rows.find(r=>r.node==='v4:1:F1-A');await start('choice-daily');await publishCaseSave({work,session:p.work,catalogue,branch:row});await p.tap('s');await p.tap('w');await p.tap('c');await p.until(async()=>(await p.stats()).mode==='menu','daily choices',120000);await p.sampled(40);let step=0;await record('choice-daily','자유행동 선택·대화 전환',18,async s=>{step++;if(s.mode==='menu'){if(step<6)await p.tap('s');else await p.tap('Enter');}else if(s.mode==='story')await p.tap('Enter');});await close();}
 catch(error){failures.push({name:'choice-daily',error:error.stack});await close().catch(()=>{});await report();}
}
if(!only||only.includes('explore')){
 try{await start('explore',path.join(root,'Saved/native-outdoor-checkpoint-1793680307759/actual-native-savegames.json'));await p.tap('c');await p.until(async()=>{const s=await p.stats();return s.world?.active&&!s.scenes.loading;},'outdoor world',120000);await p.sampled(40);let i=0;await record('explore','탐색 이동·시선 전환',16,async()=>{i++;await p.key('w',i%6<3);await p.key('ArrowRight',i%6>=3);});await p.key('w',false);await p.key('ArrowRight',false);await close();}
 catch(error){failures.push({name:'explore',error:error.stack});await close().catch(()=>{});await report();}
}
await report();console.log(JSON.stringify({complete:true,work,clips:clips.length,failures}));if(failures.length)process.exitCode=1;
