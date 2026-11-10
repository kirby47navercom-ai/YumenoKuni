// Reuse the closed owned candidate; no engine/Stats/profiling substitutions.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';import {nativeWindowProbe} from './native-window-probe.mjs';
const architecture=process.argv.includes('--architecture-v6'),baseline=process.argv.includes('--baseline'),steady=process.argv.includes('--steady'),packed=process.argv.includes('--packed');
const only=process.argv.find(a=>a.startsWith('--only='))?.slice(7).split(','),profile=process.argv.includes('--profile');
assert(!baseline||(architecture&&only&&!profile),'Use an unprofiled, targeted architectural baseline sample');
assert(!steady||(architecture&&only&&!profile&&!baseline),'Use a targeted sustained architectural sample');
assert(!packed||(architecture&&!baseline&&!profile),'Use an unprofiled architectural package sample');
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,architecture?'Saved/park-architecture-v6':'Saved/park-levels-20261104'),candidate=path.join(work,architecture?'package':'native-review/package');
const base=baseline?JSON.parse(await fs.readFile(path.join(work,'baseline.json'),'utf8')):null;
const compressed=packed?JSON.parse(await fs.readFile(path.join(work,'packed-build.json'),'utf8')):null;
const output=base?.output??compressed?.build.output??candidate,manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8')),prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)};
const qa=architecture?JSON.parse(await fs.readFile(path.join(work,'qa-package.json'),'utf8')):null;
const source=path.join(root,'Saved/native-outdoor-checkpoint-1793680307759/actual-native-savegames.json'),original=await fs.readFile(source),bpBytes=await fs.readFile(path.join(candidate,'Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json'));
const bp=JSON.parse(bpBytes);assert(!bp.nodes.some(n=>n.nativeId==='Yumeno.Stats'),'Read-only Stats binding must be removed before FPS measurement');
if(base||compressed){
 const {pathToFileURL}=await import('node:url');
 const {openGameResources}=await import(pathToFileURL(path.join(output,'tools/game-resource-archive.mjs')));
 const archive=await openGameResources(path.join(output,manifest.contentArchive.path));
 try{assert((await archive.read('Assets/Blueprints/BP_Yumeno.hbblueprint.json')).equals(bpBytes));}finally{await archive.close();}
 assert.equal(createHash('sha256').update(await fs.readFile(path.join(output,manifest.nativeModules[0].binary))).digest('hex'),qa.nativeSHA256);
}
if(compressed)assert.equal(compressed.receipt.geometryManifestSHA256,qa.geometryManifestSHA256);
const cases=[{id:'fairytale-4k',room:'plaza',pose:[0,1.55,13,0,0],width:3840,height:2160},{id:'carnival-ultrawide',room:'carnival_midway',pose:[-30,1.6,46,0,0],width:3440,height:1440},{id:'mirror-platform',room:'mirror_midway',pose:[14,7.45,-3.5,180,0],width:2560,height:1440,viewOnly:true},{id:'cabin-local',room:'ferris_cabin',pose:[-.111,1.6,.854,0,0],width:2560,height:1440,viewOnly:true},{id:'starlight-night',room:'starlight_midway',pose:[-24,1.6,44,0,0],phase:1,width:2560,height:1440,viewOnly:true}];
cases.push(...[
 {id:'fairytale-carousel',room:'plaza',pose:[-33,1.6,39,0,0]},
 {id:'carnival-swing',room:'carnival_midway',pose:[33,1.6,52,0,0]},
 {id:'mirror-funhouse',room:'mirror_midway',pose:[-6,1.6,28,0,0]},
 {id:'clockwork-coaster',room:'clockwork_midway',pose:[-5,1.6,34,0,0]},
 {id:'starlight-orbit',room:'starlight_midway',pose:[35,1.6,51,0,0]},
 {id:'starlight-evening',room:'starlight_midway',pose:[-24,1.6,44,0,0],phase:2},
 {id:'starlight-entry-close',room:'starlight_midway',pose:[-34,1.6,18.5,0,0]},
 {id:'fairytale-hotel-front',room:'plaza',pose:[4.2,1.6,1,9.5,15]},
 {id:'fairytale-hotel-quarter',room:'plaza',pose:[14,1.6,0,30.26,15]},
 {id:'fairytale-hotel-entry',room:'plaza',pose:[0,1.6,-14,0,20]},
].map(c=>({...c,width:2560,height:1440,viewOnly:true})));
if(architecture)cases.splice(2,cases.length-2,
 {id:'mirrors-4k',chapter:3,room:'mirror_midway',pose:[0,1.6,33,24.8,10],width:3840,height:2160},
 {id:'clockwork-ultrawide',chapter:4,room:'clockwork_midway',pose:[-5,1.6,34,-31.4,7],width:3440,height:1440},
 {id:'starlight-4k',chapter:5,room:'starlight_midway',pose:[35,1.6,51,0,4],width:3840,height:2160},
 {id:'perimeter-ultrawide',chapter:6,room:'outside_threshold',pose:[0,1.6,6,0,6],width:3440,height:1440},
);
if(profile)process.env.YUMENO_NATIVE_UI_PROFILE='1';
const rows=[];let p;try{for(const c of cases){if(only&&!only.includes(c.id))continue;
 const run=path.join(work,(base?'baseline-performance-':steady?'steady-performance-':packed?'packed-performance-':'performance-')+c.id+'-'+Date.now());await fs.mkdir(run);const save=JSON.parse(original),key=Object.keys(save.items).find(k=>k.startsWith('hbengine.savegame.json.yumeno-progress-v4.project.')),s=JSON.parse(save.items[key]);
 const chapter=String(c.chapter??(c.id.startsWith('fairytale')?1:c.id.startsWith('carnival')?2:c.id.startsWith('mirror')?3:c.id.startsWith('clockwork')?4:5)),graph=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/chapters/'+chapter+'.json'),'utf8'));s.chapter=chapter;s.node=Object.values(graph.nodes).find(n=>n.type==='investigate').id;s.flags={};s.stack=[];s.court.active=false;for(const k of ['taskResume','pendingTaskResume'])delete s[k];
 s.worldId=c.room;s.world[c.room]=c.pose;s.playerProgress.skyPhase=c.phase||0;save.items[key]=JSON.stringify(s);save.fixture=true;
 const options=Object.keys(save.items).find(k=>k.startsWith('hbengine.savegame.json.YumenoKuni-options-v4.project.'))||'hbengine.savegame.json.YumenoKuni-options-v4.project.'+encodeURIComponent(manifest.id);save.items[options]=JSON.stringify({...JSON.parse(save.items[options]||'{"version":2}'),frameRate:120});const resume=path.join(run,'fixture.json');await fs.writeFile(resume,JSON.stringify(save));
 const captureFree=architecture&&!c.viewOnly;
 p=await nativeWindowProbe({source:output,prepared,work:run,resume,sparse:true,unprofiled:!profile,maxFrames:null});await p.hiddenBorderless();await p.resize(c.width,c.height);await p.tap('c');await p.sampled(400);await p.capture('before',{pixels:!captureFree});let ui=JSON.parse(await fs.readFile(path.join(run,'before.ui.json'),'utf8'));assert.equal(ui.width,c.width);assert.equal(ui.height,c.height);assert(ui.world.some(o=>o.id==='ParkGeometry'&&o.mesh));assert.equal(ui.hostFrameRate,120);
 if(c.viewOnly){const camera=ui.world.find(o=>o.id==='Camera').position,expected=[300+c.pose[0],c.pose[1],c.pose[2]];assert(camera.every((v,k)=>Math.abs(v-expected[k])<.12),'Requested local view pose must actually restore');}
 if(c.phase===1)assert(ui.world.some(o=>o.id==='OutdoorSkyDome'&&o.mesh.endsWith('/sky_night.glb')));
 if(c.phase===2)assert(ui.world.some(o=>o.id==='OutdoorSkyDome'&&o.mesh.endsWith('/sky_evening.glb')));
 if(c.room==='ferris_cabin')assert(ui.world.some(o=>o.id==='ExploreGeometry'&&o.mesh==='Assets/Art/explore3d/ferris_cabin.glb'),'Cabin local geometry must be loaded only on cabin entry');
 assert.equal(ui.world.find(o=>o.id==='ExploreGeometry')?.meshVisible,c.room==='ferris_cabin','Only the fixed-view cabin needs additional local geometry');
 let performance=null;
 if(!c.viewOnly){
  // Read a fresh heartbeat after the metadata request, with no PNG or GPU readback.
  if(captureFree)await p.sampled(2);
  const turn=async duration=>{
   for(let elapsed=0;elapsed<duration;elapsed++){
    const key=elapsed%4<2?'ArrowRight':'ArrowLeft';
    await p.key(key,true);await new Promise(r=>setTimeout(r,1000));await p.key(key,false);
   }
  };
  if(steady){await turn(8);await p.capture('before',{pixels:false});ui=JSON.parse(await fs.readFile(path.join(run,'before.ui.json'),'utf8'));await p.sampled(2);}
  const first=await p.frameSample();const a=ui.world.find(o=>o.id==='Camera').rotation;
  await turn(30);
  const last=await p.frameSample();await p.capture('after',{pixels:!captureFree});ui=JSON.parse(await fs.readFile(path.join(run,'after.ui.json'),'utf8'));assert.equal(ui.width,c.width);assert.equal(ui.height,c.height);assert.notDeepEqual(ui.world.find(o=>o.id==='Camera').rotation,a);performance={seconds:(last.time-first.time)/1000,frames:last.sequence-first.sequence,fps:(last.sequence-first.sequence)/((last.time-first.time)/1000),captureFree,priorCameraSweepSeconds:steady?8:0,first,last};assert(performance.seconds>=29);
 }
 await p.close();p=null;rows.push({id:c.id,room:c.room,width:c.width,height:c.height,phase:c.phase||0,run,performance,fixture:true});console.log(JSON.stringify(rows.at(-1)));await fs.writeFile(path.join(work,base?'baseline-performance-progress.json':steady?'steady-performance-progress.json':only?'performance-selected-progress.json':'performance-progress.json'),JSON.stringify({rows},null,2));
 }assert((await fs.readFile(source)).equals(original));
 const ok=rows.length>0&&rows.every(row=>!row.performance||row.performance.fps>119);
 await fs.writeFile(path.join(work,base?'baseline-performance-selected.json':steady?'native-performance-steady.json':profile?'native-performance-diagnostic.json':only?'native-performance-selected.json':'native-performance.json'),JSON.stringify({ok,rows,targetFPS:120,noStats:true,noProfile:!profile,hidden:true,sourceSaveUnchanged:true,gameModuleSHA256:qa?.nativeSHA256??JSON.parse(await fs.readFile(path.join(work,'game-module.json'),'utf8')).binarySHA256,...(base?{baselineBuild:base.build}:{geometryManifestSHA256:qa?.geometryManifestSHA256??createHash('sha256').update(await fs.readFile(path.join(root,'../art/space_v4/park_levels_v1/manifest.json'))).digest('hex')}),profile,...(compressed?{compressedPackage:true,build:compressed.build.id}:{}),scope:'Native runtime frame heartbeat over 30 seconds of moving-camera input at 4K or ultrawide on this PC.'},null,2));
 assert(ok,'Read the recorded rows for any park performance regression');
}finally{await p?.close().catch(()=>{});}
