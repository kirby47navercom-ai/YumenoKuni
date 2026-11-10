// Visual inventory of the frozen shipping package, never the in-progress story.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {caseSaveCatalogue,publishCaseSave} from './native-case-saves.mjs';
const root=path.resolve(import.meta.dirname,'..');
const build=JSON.parse(await fs.readFile(path.join(root,'Saved/game-trial-work-20261102/current-flat-build-result.json'),'utf8'));
const work=path.join(root,'Saved/native-presentation-library-'+Date.now());
await fs.mkdir(work,{recursive:true});
const prepared=await createOwnedNativePackage({source:build.output,work,stats:true});
const shots=[],failures=[];let p;const openingOnly=process.argv.includes('--only=opening');
const save=()=>fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:failures.length===0,build:build.id,work,shots,failures,scope:'Hidden shipping native renders. Reachable menu prerequisites are explicitly marked fixtures. No current manuscript overlays, outcome injection or original save changes. Stills/key frames, not audio/video or an exhaustive full-playthrough recording.'},null,2));
async function snap(name,label,category,fixture=false,spoiler=true){
 const file=await p.capture(name),s=await p.stats();assert(!s.error,s.error);
 const u=JSON.parse(await fs.readFile(file.replace(/\.png$/,'.ui.json'),'utf8'));
 shots.push({file,label,category,fixture,spoiler,node:s.node,mode:s.mode,chapter:s.chapter,width:u.width,height:u.height});await save();
}
async function start(name,resume){p=await nativeWindowProbe({source:build.output,prepared,work:path.join(work,name),resume,maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(1920,1080);}
async function end(){await p?.close();p=null;}
try{
 await start('fresh');await snap('title','시작 화면','시작·메뉴',false,false);
 await p.tap('o');await p.until(async()=>(await p.stats()).options.open,'options');await snap('options-top','환경 설정','시작·메뉴',false,false);
 for(let i=0;i<12;i++)await p.tap('s');await snap('options-display','프레임·창 모드·해상도 설정','시작·메뉴',false,false);await p.tap('Backspace');
 await p.tap('Enter');await p.until(async()=>(await p.stats()).difficulty.open,'difficulty');await snap('difficulty','난이도 선택','시작·메뉴',false,false);await p.tap('s');await p.tap('s');await p.tap('Enter');
 await p.until(async()=>{const s=await p.stats();return s.contentVersion==='v4'&&s.world?.active&&!s.scenes.loading;},'new game',120000);
 await snap('opening','프롤로그 첫 장면','일상·대화');
 for(let i=0;i<18;i++){await p.tap('Enter');await p.sampled(3);if([3,7,11,17].includes(i))await snap('opening-'+i,'프롤로그 대화 '+(i+1),'일상·대화');if((await p.stats()).mode==='menu')break;}
 await p.tap('Tab');if((await p.stats()).mode==='pad'){
  await snap('pad-home','전자 수첩 홈','패드·기록');
  const labels=['지도','증거·기록','인물 수첩','성장·스킬','규칙','시스템'];
  for(let i=0;i<6;i++){
   // Home icon selection is real keyboard input; no direct scene/state calls.
   if(i)await p.tap('d');await p.tap('Enter');await p.sampled(3);
   if((await p.stats()).padPage>=0)await snap('pad-'+i,labels[i],'패드·기록');
   await p.tap('Backspace');
  }
 }await end();
}catch(error){failures.push({part:'opening-and-pad',error:error.stack});await end().catch(()=>{});await save();}
const catalogue=await caseSaveCatalogue();
const rows=(await fs.readFile(path.join(catalogue.fixtureRoot,'menu-fixtures.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
const picks=[];
for(const chapter of ['P','1','2','3','4','5','6']){
 const r=rows.find(r=>r.chapter===chapter);if(r)picks.push(r);
}
const free=rows.find(r=>r.node==='v4:1:F1-A');if(free)picks.push(free);
const meeting=rows.find(r=>r.node.includes('F-NA01-A:menu'));if(meeting)picks.push(meeting);
for(const [i,row]of (openingOnly?[]:picks).entries()){
 try{
  await start('menu-'+i);
  const fixture=await publishCaseSave({work,session:p.work,catalogue,branch:row});
  await p.tap('s');await p.tap('w');await p.tap('c');
  await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.node===row.node&&s.mode==='menu';},'authored menu',120000);await p.sampled(4);
  const category=i>=7?'자유행동':'일상·선택';
  await snap('choice','선택 장면 · '+row.chapter+'장',category,true);
  await p.tap('Enter');await p.sampled(6);await snap('selected','선택 후 대화 · '+row.chapter+'장',category,true);
  await p.tap('Enter');await p.sampled(6);await snap('dialogue','후속 대화 · '+row.chapter+'장',category,true);
  await end();
 }catch(error){failures.push({part:'menu-'+i,node:row.node,error:error.stack});await end().catch(()=>{});await save();}
}
for(const [label,resume,category]of (openingOnly?[]:[
 ['investigation','Saved/v4-live-world-save-1793499346988/actual-manual-savegames.json','탐색·수사'],
 ['outdoor','Saved/native-outdoor-checkpoint-1793680307759/actual-native-savegames.json','탐색·수사']
])){
 try{await start(label,path.join(root,resume));await p.tap('c');await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.world?.active&&!s.scenes.loading;},label,120000);await snap('world',label==='outdoor'?'광장·외부 공간':'실내 탐색·수사',category,label==='outdoor');await p.key('ArrowRight',true);await p.sampled(12);await p.key('ArrowRight',false);await snap('world-view','시선 이동 후 화면',category,label==='outdoor');await p.tap('m');await p.sampled(4);await snap('map','탐색 지도',category,label==='outdoor');await end();}
 catch(error){failures.push({part:label,error:error.stack});await end().catch(()=>{});await save();}
}
await save();console.log(JSON.stringify({work,build:build.id,shots:shots.length,failures}));if(failures.length)process.exitCode=1;
