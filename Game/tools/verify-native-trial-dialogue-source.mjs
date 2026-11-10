// Physical native presentation proof; isolated checkpoint at an actually visited
// ordinary return line. Never injects a minigame result or changes canonical saves.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {caseSaveCatalogue,publishCaseSave} from './native-case-saves.mjs';
import {beginOwnedMovie} from './native-window-recording.mjs';
const game=path.resolve(import.meta.dirname,'..'),output=path.join(game,'Saved/native-panic-views-1793690486425/package');
const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));
const work=path.join(game,'Saved/trial-dialogue-source-'+Date.now()),auto=process.argv.includes('--auto'),daily=process.argv.includes('--daily');
await fs.mkdir(work,{recursive:true});
const report={work,auto,daily,scope:'Native physical input; isolated presentation checkpoint at previously observed return node or authored daily say. No outcome injection or original-game execution.',screens:[]};
report.precondition=await publishCaseSave({work,session:work,catalogue:await caseSaveCatalogue(),taskId:'T3-NS-A11'});
const slot=path.join(work,'State/Saves/yumeno-progress-v4.json'),head=JSON.parse(await fs.readFile(slot,'utf8'));
head.node='v4:13c1:T3-11:e:3d8e98084ef0:1';delete head.taskResume;
const layout=JSON.parse(await fs.readFile(path.join(output,'Content/Assets/Data/v4_story/dialogue_layout.json'),'utf8'));
if(daily){head.node=layout.fixtures[1];head.chapter='1';head.court={...head.court,active:false};}
await fs.writeFile(slot,JSON.stringify(head));
await fs.writeFile(path.join(work,'State/Saves/YumenoKuni-options-v4.json'),JSON.stringify({version:2,autoRead:auto,autoWait:5,textSpeed:10,frameRate:120}));
report.moduleSHA256=createHash('sha256').update(await fs.readFile(path.join(output,manifest.nativeModules[0].binary))).digest('hex');
let p,movie;
try{
 process.env.YUMENO_NATIVE_QA_RECORD='1';
 p=await nativeWindowProbe({source:output,prepared:{output,manifest,executable:path.join(output,manifest.windowsApplication.executable)},work,maxFrames:null});
 await p.hiddenBorderless();await p.resize(1280,720);movie=await beginOwnedMovie(p,'trial-dialogue',{seconds:60});await p.tap('c');
 await p.until(async()=>{const s=await p.stats();return s.node===head.node&&!s.scenes?.loading;},'ordinary return dialogue',120000);
 const take=async(width,height)=>{
  await p.resize(width,height);
  await p.until(async()=>{const file=await p.capture('wait',{pixels:false});const j=JSON.parse(await fs.readFile(file,'utf8'));return j.widgets.find(w=>w.instance==='main')?.nodes.find(n=>n.id==='Next')?.properties.visible;},'fully readable line',15000,150);
  const name='dialogue-'+width+'-'+(auto?'auto':'manual'),file=await p.capture(name),j=JSON.parse(await fs.readFile(file.replace('.png','.ui.json'),'utf8'));
  const rows=j.widgets.find(w=>w.instance==='main').nodes,by=id=>rows.find(n=>n.id===id),props=id=>by(id).properties;
  assert(props('Body').visible&&props('Body').text.length>10);assert(!props('NameHead').visible);
  if(daily){
   for(const id of ['DialogueOrnament','DialogFrameMiddle','DialogFrameRight','DialogueOrnamentMiddle','DialogueOrnamentRight'])assert(!props(id).visible,'No trial decoration in daily say');
   assert(props('Body').font.endsWith('Pretendard-Medium.otf'));
   assert(props('Name').texture.endsWith('.svg'));assert(props('Next').texture.endsWith('dialogue/next.svg'));
   assert.deepEqual(by('Body').slot.offset.map(Math.round),[layout.body[0]-640,layout.body[1]-720,layout.body[2],layout.body[3]].map(Math.round));
  }else{
   for(const id of ['DialogFrame','DialogueOrnament','Nameplate','Name','Next'])assert(props(id).texture.startsWith('Assets/Art/ui/v3/dialogue/source/'),id+' must use source-compatible trial art');
   assert(props('Body').font.endsWith('Pretendard-Regular.otf'));assert.deepEqual(by('Body').slot.offset,[-320,-110,740,100]);
   assert(props('Name').texture.endsWith('.png'),'Alias must never squeeze the old ADV SVG');
   assert(props('Next').texture.endsWith(auto?'auto.png':'next.png'));
  }
  assert.deepEqual([j.width,j.height],[width,height]);
  report.screens.push({file,width,height,speaker:(await p.stats()).speaker,body:props('Body').text,portrait:props('Nameplate').texture,name:props('Name').texture,indicator:props('Next').texture});
 };
 if(auto||daily)await take(1920,1080);else for(const size of [[1280,720],[1920,1080],[3440,1440],[3840,2160]])await take(...size);
 report.movie=await movie.finish();movie=null;report.runtime=await p.close();p=null;report.ok=true;
}catch(e){report.error=e.stack;process.exitCode=1;}finally{if(movie)report.partial=await movie.finish().catch(()=>null);await p?.close().catch(()=>{});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,ok:report.ok,error:report.error?.split('\n')[0]}));}
