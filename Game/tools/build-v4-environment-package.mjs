// Resource-only rebuild from the frozen verified native build. The SDK archive
// writer packages art; executable/module/story/engine bytes stay at that baseline.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash,randomBytes} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/sculpted-environment-20261103');
const previous=await fs.readFile(path.join(work,'build-result.json'),'utf8').then(JSON.parse,e=>{if(e.code!=='ENOENT')throw e;return null;});
const base=process.argv.find(v=>v.startsWith('--baseline='))?.slice('--baseline='.length)||previous?.output||path.join(root,'Builds/windows/2026-11-03T04-40-39-740Z-74e5ced4'),flat=process.argv.find(v=>v.startsWith('--flat-source='))?.slice('--flat-source='.length)||path.join(root,'Saved/game-trial-work-20261102/flat-current-2026-11-03T04-40-39-740Z-74e5ced4');
const manifest=JSON.parse(await fs.readFile(path.join(base,'game.hbpack.json'),'utf8'));
const selectedBaseline=await fs.readFile(path.join(work,'rebuilt-baseline-build.json'),'utf8').then(JSON.parse,e=>{if(e.code==='ENOENT')return null;throw e;});
const {openGameResources,writeGameResources}=await import(pathToFileURL(path.join(base,'tools/game-resource-archive.mjs')));
const {fileContent,hashBuildFile}=await import(pathToFileURL(path.join(base,'tools/build-content.mjs')));
const overrides=JSON.parse(await fs.readFile(path.join(root,'Saved/game-trial-work-20261102/sculpted-overrides.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex'),id=new Date().toISOString().replace(/[:.]/g,'-')+'-'+randomBytes(4).toString('hex'),output=path.join(root,'Builds/windows',id);
const readFrozen=async file=>{for(let attempt=0;;attempt++){try{return await fs.readFile(file);}catch(error){if(attempt>=4||!['EBUSY','EPERM'].includes(error.code))throw error;await new Promise(resolve=>setTimeout(resolve,100));}}};
const surfaceManifest=await fs.readFile(path.join(root,'../art/space_v4/materials_v2/manifest.json'));
const surfaceProof=JSON.parse(await fs.readFile(path.join(work,'surface-static-verification.json'),'utf8'));assert(surfaceProof.ok&&surfaceProof.manifestSHA256===sha(surfaceManifest),'Current surface manifest must pass its static gate before packaging');
const lowpolyManifest=await fs.readFile(path.join(root,'../art/space_v4/lowpoly_v1/manifest.json')).catch(e=>{if(e.code==='ENOENT')return null;throw e;});
if(lowpolyManifest){const lowpoly=JSON.parse(lowpolyManifest),proof=JSON.parse(await fs.readFile(path.join(work,'lowpoly-static-verification.json'),'utf8'));assert(lowpoly.complete&&proof.ok&&proof.manifestSHA256===sha(lowpolyManifest),'Current complete low-poly bank must pass its independent geometry/material gate');for(const row of lowpoly.assets){const override=overrides['Content/'+row.runtime];assert(override,row.runtime);assert.equal(sha(await fs.readFile(override)),row.sha256,row.runtime);}}
const rebuiltRaw=await fs.readFile(path.join(root,'../art/space_v4/rebuild_v1/manifest.json')).catch(e=>{if(e.code==='ENOENT')return null;throw e;});
if(rebuiltRaw){const rebuilt=JSON.parse(rebuiltRaw),proof=JSON.parse(await fs.readFile(path.join(work,'rebuilt-static-verification.json'),'utf8'));assert(rebuilt.completeEnvironmentAssembly&&proof.ok&&proof.manifestSHA256===sha(rebuiltRaw),'Whole environment bank must pass independent geometry/material checks');assert.equal(rebuilt.assets.length,61);for(const row of rebuilt.assets){const override=overrides['Content/'+row.runtime];assert(override,row.runtime);assert.equal(sha(await fs.readFile(override)),row.sha256,row.runtime);}}
if(rebuiltRaw&&JSON.parse(rebuiltRaw).facilityArchitectureVersion>=2){
 const proof=JSON.parse(await fs.readFile(path.join(root,'../art/space_v4/facility_identity_v1/static-verification.json'),'utf8'));
 const identityManifest=await fs.readFile(path.join(root,'../art/space_v4/facility_identity_v1/manifest.json'));
 assert(proof.ok&&proof.environmentManifestSHA256===sha(rebuiltRaw)&&proof.facilityManifestSHA256===sha(identityManifest),'Current architecture and printed identity pixels must pass their exact-bank gate');
}
const dedicatedRaw=await fs.readFile(path.join(root,'../art/space_v4/rebuilt_dedicated_v2/manifest.json')).catch(e=>{if(e.code==='ENOENT')return null;throw e;});
if(dedicatedRaw){const bank=JSON.parse(dedicatedRaw),proof=JSON.parse(await fs.readFile(path.join(root,'../art/space_v4/rebuilt_dedicated_v2/static-verification.json'),'utf8'));assert(proof.ok&&proof.manifestSHA256===sha(dedicatedRaw));assert.equal(bank.assets.length,6);for(const a of bank.assets){assert.equal(sha(await fs.readFile(overrides['Content/'+a.runtime])),a.sha256);}}
await fs.mkdir(output);
const archive=await openGameResources(path.join(base,manifest.contentArchive.path)),content=new Map(),expected=new Map(),rows=[...archive.entries],changed=[],streamed=new Map(),packagingRetries=[];
try{
 for(let at=0;at<rows.length;at+=64){
  const batch=await Promise.allSettled(rows.slice(at,at+64).map(async([name,entry])=>{
   const override=overrides['Content/'+name];
   if(override){assert(name==='Assets/Scenes/Explore.hbscene.json'||(name.startsWith('Assets/Art/explore3d/')||['Assets/Art/court3d/courtroom_stage.glb','Assets/Art/court3d/trial_podium.glb'].includes(name))&&name.endsWith('.glb'));const bytes=await fs.readFile(override);return {name,value:bytes,bytes:bytes.length,sha256:sha(bytes),changed:true};}
   const source=path.join(flat,'Content',name);
   if(entry.bytes<256*1024){const bytes=await readFrozen(source);assert.equal(bytes.length,entry.bytes);assert.equal(sha(bytes),entry.sha256);return {name,value:bytes,...entry};}
   return {name,value:await fileContent(source,{root:flat}),file:source,...entry};
  }));
  for(const r of batch){if(r.status==='rejected')throw r.reason;const v=r.value;content.set(v.name,v.value);expected.set(v.name,{bytes:v.bytes,sha256:v.sha256});if(v.file)streamed.set(v.name,v.file);if(v.changed)changed.push(v.name);}
 }
 assert.deepEqual(changed.sort(),Object.keys(overrides).map(n=>n.slice(8)).sort());
 console.log(JSON.stringify({frozenContentReady:content.size,artChanges:changed.length}));
 for(let attempt=0;;attempt++){
  try{manifest.contentArchive=await writeGameResources(output,content);break;}
  catch(error){
   // A concurrent QA hardlink changes NTFS ctime even when bytes are identical.
   // Resample descriptors after the SDK has removed its incomplete archive;
   // never bypass its guard. The final archive must still match EVERY expected
   // baseline SHA/length, so genuine byte changes cannot become accepted output.
   if(attempt>=2||!String(error.message).includes('빌드 중 원본이 변경됐어요'))throw error;
   packagingRetries.push({attempt:attempt+1,error:error.message});
   const entries=[...streamed];for(let at=0;at<entries.length;at+=64){const batch=await Promise.allSettled(entries.slice(at,at+64).map(async([name,file])=>[name,await fileContent(file,{root:flat})]));for(const row of batch){if(row.status==='rejected')throw row.reason;content.set(...row.value);}}
  }
 }
 const files=[];
 for(const row of manifest.files){
  if(row.path==='game.hbdata'){files.push({path:'game.hbdata',bytes:manifest.contentArchive.bytes,sha256:manifest.contentArchive.sha256});continue;}
  const source=path.join(base,row.path),actual=await hashBuildFile(source,{root:base});assert.equal(actual.sha256,row.sha256);assert.equal(actual.bytes,row.bytes);
  const target=path.join(output,row.path);await fs.mkdir(path.dirname(target),{recursive:true});await fs.link(source,target);files.push(row);
 }
 manifest.files=files;const checked=await openGameResources(path.join(output,'game.hbdata'));
 try{assert.equal(checked.entries.size,expected.size);for(const [name,row]of checked.entries){assert.equal(row.sha256,expected.get(name).sha256,name);assert.equal(row.bytes,expected.get(name).bytes,name);}}finally{await checked.close();}
 await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest,null,2));
 const receipt={ok:true,id,output,baseline:base,baselineId:path.basename(base),changes:changed,actualChanges:changed.filter(name=>archive.entries.get(name).sha256!==expected.get(name).sha256),entries:expected.size,packagingRetries,engineFilesChanged:0,nativeModuleChanged:false,storyAndSourceChanged:false,archive:manifest.contentArchive,scope:'Art-only resource package built with the frozen SDK writer. Every unchanged entry retains baseline byte length/SHA; executable/native module/engine/story/source retain baseline. Not a story revision build or signed release.'};
 await fs.writeFile(path.join(output,'environment-build-receipt.json'),JSON.stringify(receipt,null,2));
 const result={id,output,executable:path.join(output,manifest.windowsApplication.executable),engineSDKRoot:selectedBaseline&&path.resolve(selectedBaseline.output)===path.resolve(base)?selectedBaseline.engineSDKRoot:previous?.engineSDKRoot||'C:/Users/kirby/HBEngine/Versions/276176917dbd5c9e',environmentOnly:true,baseline:path.resolve(base)};
 await fs.writeFile(path.join(work,'build-result.json'),JSON.stringify(result,null,2));
 const current=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
 if(current.id==='2026-11-03T05-43-07-215Z-58deff7e')await fs.writeFile(path.join(root,'build-result.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify({ok:true,id,output,changed:changed.length}));
}finally{await archive.close();}
