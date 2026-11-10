// Declared game-owned scene/data/source/module revision over a frozen full build.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {createHash,randomBytes} from 'node:crypto';import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/park-levels-20261104'),baseline=JSON.parse(await fs.readFile(path.join(work,'baseline-build.json'),'utf8')),module=JSON.parse(await fs.readFile(path.join(work,'game-module.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex'),bank=await fs.readFile(path.join(root,'../art/space_v4/park_levels_v1/manifest.json')),gate=JSON.parse(await fs.readFile(path.join(work,'static-verification.json'),'utf8'));
assert(gate.ok&&gate.geometryManifestSHA256===sha(bank));
const authored=JSON.parse(await fs.readFile(path.join(root,'../art/space_v4/park_levels_v1/theme_park_v2/authoring.json'),'utf8')),raw=JSON.parse(await fs.readFile(path.join(root,'../art/space_v4/park_levels_v1/raw-manifest.json'),'utf8'));
if(raw.levels.some(r=>r.raw.surfaceDetailRevision===3)){
 const detail=JSON.parse(await fs.readFile(path.join(work,'detail-surface-verification.json'),'utf8'));
 assert(detail.ok&&detail.geometryManifestSHA256===sha(bank)&&detail.rows.length===5&&(detail.unchangedConnectorExact||detail.materialRevision===5&&detail.unchangedConnectorGeometry),'Current five-park surface/UV/navigation proof required');
 for(const row of raw.levels)if(row.id!=='perimeter')assert.equal(row.raw.surfaceDetailRevision,3,'Surface revision must cover every public park');
}
if(raw.levels.some(r=>r.raw.surfaceMaterialRevision===5)){
 const material=JSON.parse(await fs.readFile(path.join(root,'Saved/park-materials-20261104/static.json'),'utf8'));
 assert(material.ok&&material.geometryManifestSHA256===sha(bank)&&material.rows.length===6&&material.catalogGroupsChecked===65,'Current all-six material/geometry/65-group proof required');
 const gallery=JSON.parse(await fs.readFile(path.join(root,'Saved/park-materials-20261104/gallery/review.json'),'utf8'));
 assert(gallery.ok&&gallery.geometryManifestSHA256===sha(bank)&&gallery.reviewedGroups===65,'Actual65 current material render review required');
 for(const r of raw.levels)assert.equal(r.raw.surfaceMaterialRevision,5);
}
for(const row of raw.levels){assert(row.raw.textFreePublicArchitecture,'Unrevised name-bearing public level: '+row.id);if(row.id!=='perimeter')assert(row.raw.themeParkRevision===2&&authored.districts[row.id]?.paths.primaryVisitorCircuits>0,'All five whole-level visitor layouts required: '+row.id);}
const visual=JSON.parse(await fs.readFile(path.join(work,'native-review.json'),'utf8'));assert(visual.ok&&visual.results.length===6&&visual.gameModuleSHA256===module.binarySHA256&&visual.geometryManifestSHA256===sha(bank),'Current six-park native ownership/view proof required');
const artReview=JSON.parse(await fs.readFile(path.join(work,'theme-v2-visual-review.json'),'utf8'));assert(artReview.ok&&artReview.geometryManifestSHA256===sha(bank)&&artReview.gameModuleSHA256===module.binarySHA256&&artReview.districts.length===6,'Current whole-level native visual review required; authoring counts are insufficient');
const traversal=JSON.parse(await fs.readFile(path.join(work,'native-traversal.json'),'utf8'));assert(traversal.ok&&traversal.gameModuleSHA256===module.binarySHA256&&traversal.geometryManifestSHA256===sha(bank),'Native gate/indoor/save traversal required');
const performance=JSON.parse(await fs.readFile(path.join(work,'native-performance.json'),'utf8'));assert(performance.ok&&performance.gameModuleSHA256===module.binarySHA256&&performance.geometryManifestSHA256===sha(bank)&&performance.rows.filter(r=>r.performance?.seconds>=29&&r.performance.fps>119).length===2,'Current bank/module unprofiled 4K/ultrawide motion proof required');
const finishFile=path.join(work,'public-space-finish/native.json');if(await fs.access(finishFile).then(()=>true,()=>false)){const finish=JSON.parse(await fs.readFile(finishFile,'utf8'));assert(finish.ok&&finish.moduleSHA256===module.binarySHA256);for(const[id,sha]of Object.entries(finish.testedAssetSHA256))assert.equal(sha,JSON.parse(bank).assets.find(a=>a.id===id).sha256,'Changed public-space mesh needs new traversal: '+id);}
if(raw.levels.some(r=>r.raw.hotelArchitectureRevision===4)){
 const hotel=JSON.parse(await fs.readFile(path.join(work,'hotel-architecture/static.json'),'utf8'));
 assert(hotel.ok&&hotel.geometryManifestSHA256===sha(bank)&&(hotel.unchangedGeometryDistricts||hotel.unchangedDistricts).length===5&&hotel.actualBlenderRenders.length===6,'Current one-building geometry and actual render review required');
 assert.equal(hotel.sourceSHA256,sha(await fs.readFile(path.join(root,'../art/space_v4/park_levels_v1/dream_hotel_v4/hotel-source.blend'))));
 for(const view of ['front','quarter','entry'])assert(performance.rows.some(r=>r.id==='fairytale-hotel-'+view),'Actual native hotel view required: '+view);
 const entry=JSON.parse(await fs.readFile(finishFile,'utf8'));
 assert(entry.ok&&entry.geometryManifestSHA256===sha(bank)&&entry.rows.some(r=>r.id==='hotel-door'&&r.after.space==='hotel_lobby'),'Actual rebuilt hotel door input/room lifecycle required');
}
const overrides={};for(const [name,file]of Object.entries(JSON.parse(await fs.readFile(path.join(work,'candidate-overrides.json'),'utf8'))))if(!name.startsWith('Content/Source/'))overrides[name.slice(8)]=file;
assert.equal(sha(await fs.readFile(module.scopedCodeBaseline)),module.scopedCodeBaselineSHA256);const codeBase=JSON.parse(await fs.readFile(module.scopedCodeBaseline,'utf8'));
assert(module.frozenNativeReuse&&module.binarySHA256===codeBase.binarySHA256);
for(const name of module.changedSource){const file=module.sourceFiles['Source/'+name];assert.equal(sha(await fs.readFile(file)),module.sourceSHA256['Source/'+name]);const content=await fs.readFile(codeBase.sourceFiles['Source/'+name],'utf8');assert.equal(sha(content),codeBase.sourceSHA256['Source/'+name]);assert.equal(sha(content),module.sourceSHA256['Source/'+name]);overrides['Source/'+name]=file;}
const base=baseline.base.output,manifest=JSON.parse(await fs.readFile(path.join(base,'game.hbpack.json'),'utf8'));
const {openGameResources,writeGameResources}=await import(pathToFileURL(path.join(base,'tools/game-resource-archive.mjs'))),{fileContent,hashBuildFile}=await import(pathToFileURL(path.join(base,'tools/build-content.mjs')));
const archive=await openGameResources(path.join(base,manifest.contentArchive.path)),id=new Date().toISOString().replace(/[:.]/g,'-')+'-'+randomBytes(4).toString('hex'),output=path.join(root,'Builds/windows',id);await fs.mkdir(output);
const content=new Map(),expected=new Map(),changes=[];const qa=path.join(work,'native-review/package');
try{
 const names=new Set([...archive.entries.keys(),...Object.keys(overrides)]);
 for(const name of names){
  const before=archive.entries.get(name),file=overrides[name];
  if(file){const bytes=await fs.readFile(file),row={bytes:bytes.length,sha256:sha(bytes)};content.set(name,bytes);expected.set(name,row);if(before?.sha256!==row.sha256)changes.push(name);continue;}
  assert(before);
  if(before.bytes<256*1024){content.set(name,await archive.read(name));expected.set(name,before);}
  else{const source=path.join(qa,'Content',name),row=await hashBuildFile(source,{root:qa});assert.equal(row.sha256,before.sha256,name);assert.equal(row.bytes,before.bytes,name);content.set(name,await fileContent(source,{root:qa}));expected.set(name,before);}
 }
 manifest.contentArchive=await writeGameResources(output,content);
 const entries=new Set(manifest.entries.map(r=>r.path));for(const name of names)if(!entries.has(name))manifest.entries.push({path:name,name:path.basename(name),kind:name.startsWith('Source/')?'code':name.endsWith('.hbscene.json')?'scene':name.endsWith('.hbwidget.json')?'widget':name.endsWith('.glb')?'model':name.endsWith('.json')?'json':'texture'});
 const files=[];for(const row of manifest.files){
  if(row.path==='game.hbdata'){files.push({path:row.path,bytes:manifest.contentArchive.bytes,sha256:manifest.contentArchive.sha256});continue;}
  const target=path.join(output,row.path);await fs.mkdir(path.dirname(target),{recursive:true});
  if(row.path===manifest.nativeModules[0].binary){const bytes=await fs.readFile(module.binary);assert.equal(sha(bytes),module.binarySHA256);await fs.writeFile(target,bytes);files.push({path:row.path,bytes:bytes.length,sha256:sha(bytes)});}
  else{const source=path.join(base,row.path),actual=await hashBuildFile(source,{root:base});assert.equal(actual.sha256,row.sha256);await fs.link(source,target);files.push(row);}
 }
 manifest.files=files;manifest.nativeModules[0].signature=module.signature;const checked=await openGameResources(path.join(output,manifest.contentArchive.path));try{assert.equal(checked.entries.size,expected.size);for(const [name,row]of checked.entries){assert.equal(row.sha256,expected.get(name).sha256,name);assert.equal(row.bytes,expected.get(name).bytes,name);}}finally{await checked.close();}
 await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest,null,2));
 const result={id,output,executable:path.join(output,manifest.windowsApplication.executable),engineSDKRoot:module.engineSDKRoot,baseline:base,parkLevels:true};
 await fs.writeFile(path.join(work,'build-result.json'),JSON.stringify(result,null,2));await fs.writeFile(path.join(output,'park-level-build-receipt.json'),JSON.stringify({ok:true,base:baseline.base.id,changes,engineFilesChanged:0,nativeModuleChanged:true,gameModuleSHA256:module.binarySHA256,sourceChanged:module.changedSource,geometryManifestSHA256:sha(bank),entries:expected.size,scope:'Six separate outdoor scenes, chapter-gated public routes, related map/geography dialogue, game-only C++ lifecycle. Original engine and all undeclared shipped content retain exact hashes. Development package, not signed release.'},null,2));console.log(JSON.stringify(result));
}finally{await archive.close();}
