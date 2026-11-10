// Exact packed resources, no Stats/content/engine overrides. Isolated environment
// save fixtures select review rooms, never imply a normally played unlock route.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import {createOwnedNativePackage} from './native-owned-package.mjs';import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),build=JSON.parse(await fs.readFile(path.join(root,'Saved/sculpted-environment-20261103/build-result.json'),'utf8')),work=path.join(root,'Saved/native-generated-surfaces-'+Date.now());await fs.mkdir(work);
const source=path.join(root,'Saved/native-outdoor-checkpoint-1793680307759/actual-native-savegames.json'),original=await fs.readFile(source),hash=b=>createHash('sha256').update(b).digest('hex'),world=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/runtime_v1/world.json'),'utf8'));
const rooms=(process.argv.find(v=>v.startsWith('--rooms='))?.slice(8)||'dining_room,service_lounge,hotel_corridor,guest_01,reading_room,screening_room,clinic,maintenance_workshop,park_garden,plaza,plaza-night').split(',');
const viewFile=process.argv.find(v=>v.startsWith('--views='))?.slice(8),views=viewFile?JSON.parse(await fs.readFile(path.resolve(root,viewFile),'utf8')):rooms.map(label=>({label,room:label.replace(/-(night|evening)$/,''),phase:label.endsWith('-night')?1:label.endsWith('-evening')?2:0}));
// Later source-constrained sets are separate from the original common-world bank.
const dedicated=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/dedicated_v1/world_extension.json'),'utf8'));
for(const [id,spec]of Object.entries(dedicated.spaces)){world.spaces[id]=spec;world.instances[id]={space:id};}
const candidateSource=process.argv.find(v=>v.startsWith('--candidate-source='))?.slice(19),overrides=process.argv.find(v=>v.startsWith('--content-overrides='))?.slice(20);assert(!!candidateSource===!!overrides);const packageSource=candidateSource||build.output;
const reuseWork=process.argv.find(v=>v.startsWith('--reuse-prepared='))?.slice('--reuse-prepared='.length);let prepared;
if(reuseWork){
 const prior=path.resolve(root,reuseWork),proof=JSON.parse(await fs.readFile(path.join(prior,'report.json'),'utf8')),owned=JSON.parse(await fs.readFile(path.join(prior,'owned-package.json'),'utf8'));
 assert(proof.ok&&path.resolve(root,owned.source)===path.resolve(root,packageSource)&&!owned.stats,'Reuse requires a successful same-source owned package');
 const manifest=JSON.parse(await fs.readFile(path.join(owned.output,'game.hbpack.json'),'utf8')),declared=overrides?JSON.parse(await fs.readFile(overrides,'utf8')):{};
 assert.deepEqual(owned.alterations.map(a=>a.name).sort(),Object.keys(declared).sort());
 for(const a of owned.alterations){const expected=await fs.readFile(declared[a.name]);assert.equal(hash(expected),a.after.sha256);assert.equal(hash(await fs.readFile(path.join(owned.output,a.name))),a.after.sha256);}
 prepared={output:owned.output,manifest,executable:path.join(owned.output,manifest.windowsApplication.executable)};
 await fs.writeFile(path.join(work,'owned-package.json'),JSON.stringify({...owned,reusedFrom:prior},null,2));
}else prepared=await createOwnedNativePackage({source:packageSource,work,stats:false,gameContentOverrides:overrides});
const rows=[];let p;
try{
 for(const view of views){const {label,room,phase=0}=view,spec=world.spaces[world.instances[room]?.space||room];assert(spec&&/^[a-z0-9_-]+$/.test(label)&&[0,1,2].includes(phase));const save=JSON.parse(original),key=Object.keys(save.items).find(k=>k.startsWith('hbengine.savegame.json.yumeno-progress-v4.project.')),head=JSON.parse(save.items[key]);head.worldId=room;head.world[room]=view.pose||[...spec.spawn,spec.yaw||0,0];assert(head.world[room].length===5&&head.world[room].every(Number.isFinite));head.playerProgress.skyPhase=phase;head.playerProgress.phase=phase;save.items[key]=JSON.stringify(head);save.fixture=true;save.fixtureEntry='Generated material review: '+label+'; not normal route.';
  const run=path.join(work,label);await fs.mkdir(run);const resume=path.join(run,'fixture-save.json');await fs.writeFile(resume,JSON.stringify(save));p=await nativeWindowProbe({source:packageSource,prepared,work:run,resume,sparse:true,maxFrames:null});await p.tap('c');let ui,image;
  for(let i=0;i<8;i++){await new Promise(r=>setTimeout(r,1500));image=await p.capture('view-'+i);ui=JSON.parse(await fs.readFile(path.join(run,'view-'+i+'.ui.json'),'utf8'));if(ui.world.some(o=>o.id==='ExploreGeometry'&&o.mesh===spec.mesh))break;}
  assert(ui.world.some(o=>o.id==='ExploreGeometry'&&o.mesh===spec.mesh),label+' Continue must restore selected room');assert.equal(ui.world.some(o=>o.id==='ExteriorContext'&&o.mesh),!!spec.outdoor);
  await new Promise(r=>setTimeout(r,1800));image=await p.capture('review');ui=JSON.parse(await fs.readFile(path.join(run,'review.ui.json'),'utf8'));if(view.pose){const actual=ui.world.find(o=>o.id==='Camera')?.position,expected=[300+view.pose[0],view.pose[1],view.pose[2]];assert(actual&&actual.every((v,i)=>Math.abs(v-expected[i])<.12),label+' requested art camera was rejected/restored elsewhere');}const runtime=await p.close();p=null;assert(runtime.renderer.info.calls>0);rows.push({label,room,image,runtime,fixture:true,cameraPoseAsserted:!!view.pose});await fs.writeFile(path.join(work,'progress.json'),JSON.stringify({build:build.id,rows},null,2));console.log(JSON.stringify({captured:label,image}));
 }
 assert.equal(hash(await fs.readFile(source)),hash(original));const owned=JSON.parse(await fs.readFile(path.join(work,'owned-package.json'),'utf8'));if(!candidateSource)assert.deepEqual(owned.alterations,[]);
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,build:build.id,work,rows,fixture:true,unchangedPackedResources:!candidateSource,candidateSource:candidateSource||null,overrides:overrides||null,sourceSaveUnchanged:true,scope:'Actual native room/day-night fixture renders; '+(candidateSource?'DECLARED GAME ART CANDIDATE, not unchanged shipping resources. ':'Exact packed art, no Stats/content/engine substitutions. ')+'Separate human visual review and FPS evidence. Not normal progression or every room acceptance.'},null,2));console.log(JSON.stringify({ok:true,work,captures:rows.length}));
}catch(e){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:e.stack,rows},null,2));throw e;}finally{await p?.close().catch(()=>{});}
