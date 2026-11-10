import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
const game=path.resolve(import.meta.dirname,'..'),work=path.join(game,'Saved/voice-rewrite-20261107');
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),sha=b=>createHash('sha256').update(b).digest('hex');
const final=process.argv.includes('--packed-final');
const build=await read(path.join(work,final?'build-result.json':'base-build.json'));
const module=await read(path.join(game,'Saved/game-trial-work-20261102/game-module-dialogue-pages-v1-20261107.json'));
const cases=await read(path.join(work,'native-model/page-expectations.json'));
const only=process.argv.find(a=>a.startsWith('--only='))?.slice(7);
const selectedCases=only===undefined?cases.map((row,i)=>({row,i})):only.split(',').map(Number).map(i=>{assert(cases[i]);return{row:cases[i],i};});
const original=path.join(game,'Saved/ui-checkpoints/normal-ch3-latest/savegames.json'),originalBytes=await fs.readFile(original),normal=JSON.parse(originalBytes);
const key=Object.keys(normal.items).find(k=>k.startsWith('hbengine.savegame.json.yumeno-progress-v4.project.'));assert(key);
const ownManifest=path.join(work,'native/package/game.hbpack.json');
const prepared=final?{output:build.output,manifest:await read(path.join(build.output,'game.hbpack.json')),executable:build.executable}:await fs.access(ownManifest).then(async()=>{const manifest=await read(ownManifest);return{output:path.dirname(ownManifest),manifest,executable:path.join(path.dirname(ownManifest),manifest.windowsApplication.executable)};},()=>createOwnedNativePackage({source:build.output,work:path.join(work,'native'),gameModuleCandidate:module.binary}));
const batch=Date.now();
const report={base:build.id,moduleSHA256:sha(await fs.readFile(path.join(prepared.output,prepared.manifest.nativeModules[0].binary))),directPackedRun:final,cases:[],fixture:true,scope:'Actual background HWND input and native UI output at six isolated revised dialogue nodes. Each page must match the C++ model; no plot outcome injected. Published source identity and text-only archive parity in package-parity.json. Not continuous campaign playthrough or FPS acceptance.'};
for(const {row,i}of selectedCases){
 const session=path.join(work,'native','session-'+batch+'-case-'+i);await fs.mkdir(path.join(session,'State/Saves'),{recursive:true});
 // The real checkpoint has external log/read shards. Copy those supported
 // save slots too; a header without its shards must correctly fail loading.
 for(const [slotKey,value]of Object.entries(normal.items))if(slotKey.startsWith('hbengine.savegame.json.')&&slotKey.endsWith('.project.004a6371-3a84-4fc3-8b54-31a5001740dd')){const slot=slotKey.slice('hbengine.savegame.json.'.length,-'.project.004a6371-3a84-4fc3-8b54-31a5001740dd'.length);assert(!/[\\/]/.test(slot));await fs.writeFile(path.join(session,'State/Saves',encodeURIComponent(slot)+'.json'),value);}
 const head=JSON.parse(normal.items[key]);head.chapter=row.chapter;head.node=row.id;delete head.taskResume;delete head.growth;head.court={...(head.court||{}),active:row.trial,dead:[]};
 await fs.writeFile(path.join(session,'State/Saves/yumeno-progress-v4.json'),JSON.stringify(head));
 await fs.writeFile(path.join(session,'State/Saves/YumenoKuni-options-v4.json'),JSON.stringify({version:2,autoRead:false,textSpeed:10,frameRate:120}));
 let p;
 try{
  p=await nativeWindowProbe({source:build.output,prepared,work:session,sparse:true,unprofiled:true,maxFrames:null});
  await p.hiddenBorderless();await p.resize(i===2?3440:1920,i===2?1440:1080);await p.tap('c');
  const snapshot=async(name,pixels=false)=>{await p.capture(name,{pixels});return read(path.join(session,name+'.ui.json'));};
  const body=ui=>ui.widgets.find(w=>w.instance==='main')?.nodes.find(n=>n.id==='Body')?.properties;
  const observed=[];
  for(let page=0;page<row.pages.length;page++){
   const expected=row.pages[page].text;
   await p.until(async()=>{const ui=await snapshot('wait-'+page);return body(ui)?.visible&&body(ui)?.text===expected;},'readable complete sentence page '+page,40000,250);
   const ui=await snapshot('page-'+page,true);assert.equal(body(ui).text,expected);observed.push({text:body(ui).text,screen:'page-'+page+'.png',surface:[ui.width,ui.height]});
   if(page===0){await p.tap('Tab');await p.tap('Tab');const restored=await snapshot('pad-return');assert.equal(body(restored).text,expected,'Pad returns to current page');}
   await p.tap('Enter');
  }
  const last=row.pages.at(-1).text;
  await p.until(async()=>{const ui=await snapshot('after');return body(ui)?.text&&body(ui).text!==last;},'authored following dialogue after final page',40000,250);
  await snapshot('following',true);
  const runtime=await p.close();p=null;assert.equal(runtime.exitCode,0);assert(!runtime.forced);
  report.cases.push({id:row.id,session,chapter:row.chapter,trial:row.trial,expectedPages:row.pages.length,observed,padReturnedSamePage:true,followedAuthoredNext:true,runtime,ok:true});
 }catch(e){report.error=e.stack;report.failed=row.id;process.exitCode=1;break;}
 finally{await p?.close().catch(()=>{});}
}
report.originalSaveSHA256=sha(originalBytes);assert.equal(sha(await fs.readFile(original)),report.originalSaveSHA256);
report.ok=report.cases.length===selectedCases.length&&!report.error;
const reportName=(final?'packed-native-report':'native-report')+(only===undefined?'':'-selected-'+only.replaceAll(',','-'))+'.json';
await fs.writeFile(path.join(work,reportName),JSON.stringify(report,null,2));
console.log(JSON.stringify({ok:report.ok,cases:report.cases.length,error:report.error?.split('\n')[0]}));
