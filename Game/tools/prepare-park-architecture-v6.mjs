// Reuse one owned flat QA package; preserve current code/engine and other UI.
import fs from 'node:fs/promises';import path from 'node:path';import{createHash}from'node:crypto';import{pathToFileURL}from'node:url';import assert from'node:assert/strict';
import{applyParkArchitectureLight}from'./v4-park-architecture-light.mjs';
const root=path.resolve(import.meta.dirname,'../..'),w=path.join(root,'Game/Saved/park-architecture-v6'),output=path.join(w,'package'),sha=b=>createHash('sha256').update(b).digest('hex'),base=JSON.parse(await fs.readFile(path.join(root,'Game/build-result.json'),'utf8')),source=JSON.parse(await fs.readFile(path.join(base.output,'game.hbpack.json'),'utf8')),file=path.join(output,'game.hbpack.json'),old=JSON.parse(await fs.readFile(file,'utf8')),prior=new Map(old.files.map(r=>[r.path,r]));
const baselineFile=path.join(w,'baseline.json'),baseline=await fs.readFile(baselineFile,'utf8').then(JSON.parse,e=>{if(e.code!=='ENOENT')throw e;return null;});let adoptedParkSourceSHA256;
if(baseline&&base.id!==baseline.build){
 assert(process.argv.includes('--adopt-current'),'Independent current changed; reconcile before replacing its code');
 const bank=JSON.parse(await fs.readFile(path.join(root,'art/space_v4/park_levels_v1/manifest.json'),'utf8'));
 const{openGameResources}=await import(pathToFileURL(path.join(base.output,'tools/game-resource-archive.mjs'))),check=await openGameResources(path.join(base.output,source.contentArchive.path));
 try{
  const owned=new Set(Object.values(JSON.parse(await fs.readFile(path.join(root,'art/space_v4/park_levels_v1/architecture_v6/manifest.json'),'utf8')).assets).map(a=>a.district));
  let previous=baseline.parkSourceSHA256;
  if(!previous){const oldManifest=JSON.parse(await fs.readFile(path.join(baseline.output,'game.hbpack.json'),'utf8')),oldArchive=await openGameResources(path.join(baseline.output,oldManifest.contentArchive.path));try{previous=Object.fromEntries(bank.assets.map(a=>[a.id,oldArchive.entries.get(a.runtime)?.sha256]));}finally{await oldArchive.close();}}
  adoptedParkSourceSHA256={};
  for(const a of bank.assets){const current=check.entries.get(a.runtime)?.sha256;adoptedParkSourceSHA256[a.id]=current;if(!owned.has(a.id))assert.equal(current,a.sha256,'Unrelated park changed: '+a.id);else assert([previous[a.id],prior.get('Content/'+a.runtime)?.sha256,a.sha256].includes(current),'Owned park changed independently; reconcile source: '+a.id);}
 }finally{await check.close();}
 await fs.writeFile(path.join(w,'baseline-'+baseline.build+'.json'),JSON.stringify(baseline,null,2));
}
if(!baseline||base.id!==baseline.build)await fs.writeFile(baselineFile,JSON.stringify({build:base.id,output:base.output,executable:base.executable,manifestSHA256:sha(await fs.readFile(path.join(base.output,'game.hbpack.json'))),nativeSHA256:sha(await fs.readFile(path.join(base.output,source.nativeModules[0].binary))),parkSourceSHA256:adoptedParkSourceSHA256,previous:baseline?.build,scope:'Frozen existing current full; all current code/resources preserved, authored architectural assets only, no source or engine compilation.'},null,2));
const{openGameResources}=await import(pathToFileURL(path.join(base.output,'tools/game-resource-archive.mjs'))),archive=await openGameResources(path.join(base.output,source.contentArchive.path)),manifest=structuredClone(source),rows=[],changed=[];
const valid=name=>{assert(!path.isAbsolute(name)&&!name.split(/[\\/]/).includes('..'));return path.join(output,name);};
const put=async(name,bytes)=>{const dest=valid(name);await fs.mkdir(path.dirname(dest),{recursive:true});await fs.writeFile(dest+'.v6.tmp',bytes);await fs.rename(dest+'.v6.tmp',dest);};
try{
 for(const row of source.files){if(row.path===source.contentArchive.path)continue;const before=prior.get(row.path),target=valid(row.path);if(!before||before.sha256!==row.sha256||!await fs.access(target).then(()=>true,()=>false)){await fs.mkdir(path.dirname(target),{recursive:true});await fs.copyFile(path.join(base.output,row.path),target+'.v6.tmp');await fs.rename(target+'.v6.tmp',target);changed.push(row.path);}rows.push(row);}
 const bank=JSON.parse(await fs.readFile(path.join(root,'art/space_v4/park_levels_v1/manifest.json'),'utf8')),owned=new Map(bank.assets.map(a=>[a.runtime,a])),architecture=JSON.parse(await fs.readFile(path.join(root,'art/space_v4/park_levels_v1/architecture_v6/manifest.json'),'utf8'));let reused=0;
 const navigation=await fs.readFile(path.join(w,'site-navigation.json'),'utf8').then(JSON.parse,e=>{if(e.code!=='ENOENT')throw e;return {};});
 const navigationByBucket=new Map();
 if(Object.keys(navigation).length){
  const world=JSON.parse(await archive.read('Assets/Data/explore_world.json'));
  for(const [district,proof] of Object.entries(navigation)){
   const {hub}=world.parkLevels.districts[district],space=world.instances[hub].space,bucket=world.spaces[space].bucket;
   const asset=bank.assets.find(candidate=>candidate.id===district);
   assert.equal(sha(JSON.stringify(asset.collision)),proof.nextCollisionSHA256);
   assert.equal(sha(JSON.stringify(asset.walkSurfaces)),proof.walkSHA256);
   const entries=navigationByBucket.get(bucket)||[];
   entries.push({space,asset,proof});navigationByBucket.set(bucket,entries);
  }
 }
 for(const [name,row]of archive.entries){const full='Content/'+name,a=owned.get(name),target=valid(full);if(a){const bytes=await fs.readFile(path.join(root,a.file));assert.equal(sha(bytes),a.sha256);await put(full,bytes);rows.push({path:full,bytes:bytes.length,sha256:a.sha256});changed.push(full);continue;}
  if(navigationByBucket.has(name)){
   const bucket=JSON.parse(await archive.read(name));
   for(const {space,asset,proof} of navigationByBucket.get(name)){
    const spec=bucket.spaces[space],priorCollision=sha(JSON.stringify(spec.collision));
    assert([proof.previousCollisionSHA256,proof.nextCollisionSHA256].includes(priorCollision),'Independent world navigation changed: '+space);
    assert.equal(sha(JSON.stringify(spec.walk_surfaces)),proof.walkSHA256);
    spec.collision=asset.collision;
   }
   const bytes=Buffer.from(JSON.stringify(bucket));await put(full,bytes);rows.push({path:full,bytes:bytes.length,sha256:sha(bytes)});changed.push(full);continue;
  }
  if(name==='Assets/Scenes/ParkCarnival.hbscene.json'&&architecture.assets.performance_stage?.presentationLights?.length){const scene=JSON.parse(await archive.read(name)),before=scene.objects.filter(o=>!o.id.startsWith('ArchitectureStageKey'));applyParkArchitectureLight(scene,'carnival',architecture);assert.deepEqual(scene.objects.filter(o=>!o.id.startsWith('ArchitectureStageKey')),before);const{validScene}=await import(pathToFileURL(path.join(base.output,'prototype/model.js')));assert(validScene(scene),'Authored local light scene must pass the exact current runtime schema');const bytes=Buffer.from(JSON.stringify(scene));await put(full,bytes);rows.push({path:full,bytes:bytes.length,sha256:sha(bytes)});changed.push(full);continue;}
  const before=prior.get(full);if(before&&before.sha256===row.sha256&&await fs.access(target).then(()=>true,()=>false))reused++;else{const bytes=await archive.read(name);assert.equal(sha(bytes),row.sha256);await put(full,bytes);changed.push(full);}rows.push({path:full,bytes:row.bytes,sha256:row.sha256});
 }
 delete manifest.contentArchive;manifest.files=rows;await fs.writeFile(file,JSON.stringify(manifest));
 const proof={ok:true,base:base.id,output,executable:path.join(output,manifest.windowsApplication.executable),nativeSHA256:sha(await fs.readFile(path.join(output,manifest.nativeModules[0].binary))),geometryManifestSHA256:sha(await fs.readFile(path.join(root,'art/space_v4/park_levels_v1/manifest.json'))),unchangedContentReused:reused,changed,navigationDistricts:Object.keys(navigation),engineSourceChanged:false,scope:'One existing owned QA package with the current code, source park GLBs, the Carnival lights and explicitly verified district collision overrides.'};await fs.writeFile(path.join(w,'qa-package.json'),JSON.stringify(proof,null,2));console.log(JSON.stringify({ok:true,base:base.id,unchangedContentReused:reused,changed:changed.length}));
}finally{await archive.close();}
