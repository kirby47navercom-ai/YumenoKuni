// Actual hidden native renders of the authored separate parks, isolated saves.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import {createOwnedNativePackage} from './native-owned-package.mjs';import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/park-levels-20261104'),runRoot=path.join(work,'native-review');await fs.mkdir(runRoot,{recursive:true});
const baseline=JSON.parse(await fs.readFile(path.join(work,'baseline-build.json'),'utf8')),emission=JSON.parse(await fs.readFile(path.join(work,'emission.json'),'utf8')),overrides=JSON.parse(await fs.readFile(path.join(work,'baseline-overrides.json'),'utf8'));
for(const name of Object.keys(overrides))if(!name.startsWith('Content/Assets/'))delete overrides[name];
for(const name of emission.paths)overrides['Content/'+name]=path.join(root,name);
Object.assign(overrides,emission.overrides||{});
for(const row of JSON.parse(await fs.readFile(path.join(work,'story-candidate.json'),'utf8')).rows)overrides['Content/'+row.runtime]=row.file;
const mapFile=path.join(work,'candidate-overrides.json');await fs.writeFile(mapFile,JSON.stringify(overrides,null,2));
const module=JSON.parse(await fs.readFile(path.join(work,'game-module.json'),'utf8'));
const blueprintName='Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json',blueprint=JSON.parse(await fs.readFile(overrides[blueprintName]||path.join(baseline.flat,blueprintName),'utf8'));blueprint.native.header=await fs.readFile(module.sourceFiles['Source/Yumeno.h'],'utf8');blueprint.native.source=await fs.readFile(module.sourceFiles['Source/Yumeno.cpp'],'utf8');const blueprintFile=path.join(work,'module-blueprint.json');await fs.writeFile(blueprintFile,JSON.stringify(blueprint));overrides[blueprintName]=blueprintFile;await fs.writeFile(mapFile,JSON.stringify(overrides,null,2));
const manifestFile=path.join(runRoot,'package/game.hbpack.json');
let prepared;
if(await fs.access(manifestFile).then(()=>true,()=>false)){
 const receipt=JSON.parse(await fs.readFile(path.join(runRoot,'owned-package.json'),'utf8')),manifest=JSON.parse(await fs.readFile(manifestFile,'utf8'));assert.equal(receipt.source,baseline.flat);
 // Revisions of this one closed owned candidate reuse storage, with replacement
 // by rename so shared baseline hardlinks are never opened for truncation.
 const rows=new Map(manifest.files.map(r=>[r.path,r]));
 for(const [name,file] of [...Object.entries(overrides),[manifest.nativeModules[0].binary,module.binary]]){
  const bytes=await fs.readFile(file),target=path.join(runRoot,'package',name);await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target+'.parks.tmp',bytes);await fs.rename(target+'.parks.tmp',target);
  let row=rows.get(name);if(!row){assert(name.startsWith('Content/Assets/'));row={path:name};manifest.files.push(row);rows.set(name,row);const asset=name.slice(8);if(!manifest.entries.some(r=>r.path===asset))manifest.entries.push({path:asset,name:path.basename(asset),kind:asset.endsWith('.hbscene.json')?'scene':'texture'});}Object.assign(row,{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
 }
 await fs.writeFile(manifestFile,JSON.stringify(manifest));prepared={output:path.dirname(manifestFile),manifest,executable:path.join(path.dirname(manifestFile),manifest.windowsApplication.executable)};
}else prepared=await createOwnedNativePackage({source:baseline.flat,work:runRoot,stats:false,gameModuleCandidate:module.binary,gameContentOverrides:mapFile});
for(const [name,file]of Object.entries(module.sourceFiles)){const bytes=await fs.readFile(file),target=path.join(prepared.output,'Content',name);await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target+'.source.tmp',bytes);await fs.rename(target+'.source.tmp',target);let row=prepared.manifest.files.find(r=>r.path==='Content/'+name);if(!row){row={path:'Content/'+name};prepared.manifest.files.push(row);prepared.manifest.entries.push({path:name,name:path.basename(name),kind:'code'});}Object.assign(row,{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});}prepared.manifest.nativeModules[0].signature=module.signature;await fs.writeFile(manifestFile,JSON.stringify(prepared.manifest));
if(process.argv.includes('--prepare-only')){console.log(JSON.stringify({prepared:true,output:prepared.output,gameModule:module.binarySHA256}));process.exit(0);}
const source=path.join(root,'Saved/native-outdoor-checkpoint-1793680307759/actual-native-savegames.json'),original=await fs.readFile(source),plan=JSON.parse(await fs.readFile(path.join(root,'../art/space_v4/park_levels_v1/plan.json'),'utf8'));
const representative=process.argv.includes('--representative');
const only=process.argv.find(a=>a.startsWith('--only='))?.slice(7).split(',')||(representative?['fairytale']:undefined),results=[];let p;
const geometryBytes=await fs.readFile(path.join(root,'../art/space_v4/park_levels_v1/manifest.json')),geometry=JSON.parse(geometryBytes);
const previous=only&&!representative?JSON.parse(await fs.readFile(path.join(work,'native-review.json'),'utf8')):null;
const snapshotArg=process.argv.find(a=>a.startsWith('--reuse-snapshot='))?.slice(17);
const priorSnapshot=only&&!representative?await fs.readFile(snapshotArg?path.resolve(snapshotArg):path.join(work,'public-space-finish/manifest-before-perimeter.json')):null;
if(previous&&priorSnapshot)assert.equal(previous.geometryManifestSHA256,createHash('sha256').update(priorSnapshot).digest('hex'),'Selected verification needs the exact previous bank snapshot');
try{for(const d of plan.districts){
 if(only&&!only.includes(d.id))continue;
 const run=path.join(runRoot,d.id+'-'+Date.now());await fs.mkdir(run);const save=JSON.parse(original),key=Object.keys(save.items).find(k=>k.startsWith('hbengine.savegame.json.yumeno-progress-v4.project.')),s=JSON.parse(save.items[key]);
 const chapter=String(Math.max(1,d.chapter)),graph=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/chapters/'+chapter+'.json'),'utf8'));s.chapter=chapter;s.node=Object.values(graph.nodes).find(n=>n.type==='investigate').id;s.flags={};s.stack=[];s.court.active=false;for(const k of ['taskResume','pendingTaskResume'])delete s[k];
 s.worldId=d.hub;s.world[d.hub]=[...d.spawn,0,0];save.items[key]=JSON.stringify(s);save.fixture=true;
 const resume=path.join(run,'fixture.json');await fs.writeFile(resume,JSON.stringify(save));p=await nativeWindowProbe({source:baseline.flat,prepared,work:run,resume,sparse:true,maxFrames:null});await p.tap('c');let ui,image;
 await p.until(async()=>{image=await p.capture('poll-'+Date.now());ui=JSON.parse(await fs.readFile(image.replace(/\.png$/,'.ui.json'),'utf8'));return ui.world.some(o=>o.id==='ParkGeometry'&&o.mesh==='Assets/Art/park_levels/'+d.id+'.glb');},d.scene,60000,400);
 await p.sampled(120);image=await p.capture('review');ui=JSON.parse(await fs.readFile(path.join(run,'review.ui.json'),'utf8'));
 assert.equal(ui.world.filter(o=>o.mesh?.startsWith('Assets/Art/park_levels/')&&!o.mesh.endsWith('/gate.glb')).length,1);assert(!ui.world.some(o=>o.id.startsWith('Exterior')&&o.mesh));assert(!ui.world.some(o=>o.id==='ExploreGeometry'&&o.mesh));
 assert.equal(ui.world.find(o=>o.id==='ExploreGeometry')?.meshVisible,false,'No empty local mesh renderer may draw its default cube in a park');
 assert(!ui.world.some(o=>o.kind==='cube'&&o.mesh===''&&o.meshVisible===true),'No visible empty-mesh fallback cube');
 const nodes=ui.widgets.flatMap(w=>w.nodes),hint=nodes.find(n=>n.id==='ExHint'),retired=nodes.find(n=>n.id==='RetiredExploreHints');assert(!hint||hint.properties.visible===false||(hint.parent===retired?.id&&retired.properties.visible===false),'Permanent movement-control sentence must be effectively hidden');
 const extraImages=[];
 if(d.id!=='perimeter'){
  await p.key('ArrowRight',true);await p.sampled(120);await p.key('ArrowRight',false);extraImages.push(await p.capture('right-attraction'));
  await p.key('w',true);await p.sampled(120);await p.key('w',false);extraImages.push(await p.capture('right-after-walk'));
  await p.key('ArrowLeft',true);await p.sampled(240);await p.key('ArrowLeft',false);extraImages.push(await p.capture('left-attraction'));
 }
 const runtime=await p.close();p=null;results.push({district:d.id,scene:d.scene,image,extraImages,run,runtime,fixture:true,geometrySHA256:geometry.assets.find(a=>a.id===d.id).sha256});await fs.writeFile(path.join(work,'native-review-progress.json'),JSON.stringify({results},null,2));console.log(JSON.stringify({captured:d.id,image,extraImages}));
 }assert((await fs.readFile(source)).equals(original));
 if(previous){const prior=JSON.parse(priorSnapshot);for(const row of previous.results){if(results.some(r=>r.district===row.district))continue;const sha=row.geometrySHA256||prior.assets.find(a=>a.id===row.district).sha256;assert.equal(sha,geometry.assets.find(a=>a.id===row.district).sha256,'Changed district needs new native view: '+row.district);results.push({...row,geometrySHA256:sha,reusedExactMeshProof:true});}}
 assert.equal(results.length,representative?1:6);await fs.writeFile(path.join(work,representative?'theme-v2-representative.json':'native-review.json'),JSON.stringify({ok:true,base:baseline.base.id,gameModuleSHA256:module.binarySHA256,geometryManifestSHA256:createHash('sha256').update(geometryBytes).digest('hex'),results,fixture:true,scope:representative?'Actual first revised district plus camera turns and physical walk; visual review in progress, not all-park completion.':'Actual native separate park render/ownership checks; unchanged districts may retain their exact-mesh proof. Not a normal chapter unlock or performance acceptance.'},null,2));
}finally{await p?.close().catch(()=>{});}
