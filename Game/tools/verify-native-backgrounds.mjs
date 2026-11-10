// Hidden, full-size runtime captures. Secondary art previews are explicit QA fixtures.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {createOwnedNativePackage} from './native-owned-package.mjs';
const root=path.resolve(import.meta.dirname,'..');
const build=JSON.parse(await fs.readFile(process.argv.find(v=>v.startsWith('--build-result='))?.slice(15)||path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/native-backgrounds-'+Date.now()),proofs=[];
let probe;
await fs.mkdir(work,{recursive:true});
try{
 for(const [asset,sizes] of [
  ['title',[[1280,720],[2560,1440],[3440,1440],[3840,2160]]],
  ['roof_garden_day',[[2560,1440]]],['parade_float_day',[[2560,1440]]]
 ]){
  if(process.argv.includes('--title-only')&&asset!=='title')continue;
  const run=path.join(work,asset);let prepared;
  if(asset!=='title'){
   await fs.mkdir(run,{recursive:true});
   const name='Content/Assets/UI/TitleShellV4.hbwidget.json';
   const widget=JSON.parse(await fs.readFile(path.join(build.output,name),'utf8'));
   widget.nodes.find(n=>n.id==='TitleBg').properties.texture='Assets/Art/bg/'+asset+'.webp';
   const candidate=path.join(run,'preview-widget.json'),overrides=path.join(run,'overrides.json');
   await fs.writeFile(candidate,JSON.stringify(widget));await fs.writeFile(overrides,JSON.stringify({[name]:candidate}));
   prepared=await createOwnedNativePackage({source:build.output,work:run,stats:true,gameContentOverrides:overrides});
  }
  probe=await nativeWindowProbe({source:build.output,work:run,prepared,maxFrames:null});
  await probe.hiddenBorderless();
  for(const [width,height] of sizes){
   await probe.resize(width,height);await probe.sampled(8);
   const name=`${asset}-${width}x${height}`,image=await probe.capture(name);
   const ui=JSON.parse(await fs.readFile(path.join(run,name+'.ui.json'),'utf8'));
   const state=await probe.windowState(),stats=await probe.stats();
   assert.deepEqual(await probe.viewport(),[width,height]);assert.equal(ui.width,width);assert.equal(ui.height,height);
   assert(!state[0]&&!state[1]&&!state[2],'QA must stay hidden, unminimized and unfocused');
   assert.equal(stats.mode,'title');assert(!ui.world?.some(o=>/CourtGeometry|ExploreGeometry/.test(o.id)));
   const bg=ui.rects.find(n=>n.id==='TitleBg');assert(bg&&Math.abs(bg.x)<1&&Math.abs(bg.y)<1&&Math.abs(bg.w-width)<1&&Math.abs(bg.h-height)<1,'Background must cover the actual client');
   proofs.push({asset,fixture:asset!=='title',width,height,image,bg,window:state});
  }
  const runtime=await probe.close();probe=null;assert.deepEqual(runtime.audio.errors,[]);
 }
 const report={ok:true,build:build.id,work,proofs,scope:'Actual unchanged game title at 720p/1440p/ultrawide/4K. '+(proofs.some(p=>p.fixture)?'Two explicitly substituted QA art previews at1440p. ':'No secondary art substitution in this run. ')+'Physical rendering and full background coverage checked; no all-background or all-hardware performance claim. No engine/base-package changes, foregrounding or cursor movement.'};
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,build:build.id,work,captures:proofs.length}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,proofs},null,2));throw error;}finally{await probe?.close().catch(()=>{});}
