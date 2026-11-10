// Refresh the single retained QA, preserving only its read-only blueprint probes.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),output=path.join(root,'Saved/native-panic-views-1793690486425/package');
const build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
assert(build.output.startsWith(path.join(root,'Builds')+path.sep));
const manifest=JSON.parse(await fs.readFile(path.join(build.output,'game.hbpack.json'),'utf8'));
const old=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));assert.equal(old.id,manifest.id);
assert(manifest.entries.some(e=>e.path==='Assets/Scenes/ArmamentHud.hbscene.json'));
const runner=await fs.readFile(path.join(build.output,'tools/native-game-runner.mjs'),'utf8');
const renderer=await fs.readFile(path.join(build.output,'prototype/native-scene-renderer.js'),'utf8');
assert(runner.includes('gameRenderViews')&&renderer.includes('renderer.hbViews'),'The game requires the approved three-camera runtime; do not silently publish a single-view SDK');
assert((await fs.readFile(path.join(build.output,manifest.windowsApplication.executable))).includes(Buffer.from('Render view count invalid')),'The native executable must match the approved multiview protocol too');
const {openGameResources}=await import(pathToFileURL(path.join(build.output,'tools/game-resource-archive.mjs')));
const archive=await openGameResources(path.join(build.output,manifest.contentArchive.path));
const digest=b=>createHash('sha256').update(b).digest('hex'),safe=name=>!path.isAbsolute(name)&&!name.split(/[\\/]/).some(p=>p==='..');
const files=[],receipt={build:build.id,runtime:0,reused:0,copied:0,copiedBytes:0,scope:'One retained QA; archived content and runtime verified. Only existing read-only Stats/F2/Aim blueprint graph instrumentation is preserved.'};
const bpName='Assets/Blueprints/BP_Yumeno.hbblueprint.json',probe=JSON.parse(await fs.readFile(path.join(output,'Content',bpName),'utf8'));
try{
 // Reject a stale package before changing the retained QA. Source may have
 // changed while a long build was running; never test that as the current game.
 for(const [name] of archive.entries)if(name.startsWith('Source/')){
  assert.equal(digest(await archive.read(name)),digest(await fs.readFile(path.join(root,name))),'Current game source differs from packed build: '+name);
 }
 for(const row of manifest.files){
  if(row.path===manifest.contentArchive.path)continue;assert(safe(row.path));const bytes=await fs.readFile(path.join(build.output,row.path));assert.equal(bytes.length,row.bytes);assert.equal(digest(bytes),row.sha256);
  const target=path.join(output,row.path);await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target+'.refresh.tmp',bytes);await fs.rename(target+'.refresh.tmp',target);files.push(row);receipt.runtime++;
 }
 const rows=[...archive.entries];
 for(let at=0;at<rows.length;at+=16){
  const batch=await Promise.allSettled(rows.slice(at,at+16).map(async([name,row])=>{
   assert(safe(name));const target=path.join(output,'Content',name);let bytes;
   if(name===bpName){const canonical=JSON.parse((await archive.read(name)).toString('utf8'));probe.native=canonical.native;bytes=Buffer.from(JSON.stringify(probe));}
   else{
    const prior=await fs.readFile(target).catch(e=>{if(e.code==='ENOENT')return null;throw e;});
    if(prior?.length===row.bytes&&digest(prior)===row.sha256){receipt.reused++;return {path:'Content/'+name,bytes:row.bytes,sha256:row.sha256};}
    bytes=await archive.read(name);
   }
   await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target+'.refresh.tmp',bytes);await fs.rename(target+'.refresh.tmp',target);receipt.copied++;receipt.copiedBytes+=bytes.length;
   return {path:'Content/'+name,bytes:bytes.length,sha256:digest(bytes)};
  }));
  for(const result of batch){if(result.status==='rejected')throw result.reason;files.push(result.value);}
 }
 delete manifest.contentArchive;manifest.files=files;await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));
 const module=await fs.readFile(path.join(output,manifest.nativeModules[0].binary));receipt.moduleSHA256=digest(module);
 const frozen=path.join(root,'Saved/game-trial-work-20261102/game-presentation-runtime-20261104.exe');await fs.writeFile(frozen,module);receipt.frozenModule=frozen;
 await fs.writeFile(path.join(root,'Saved/game-trial-work-20261102/qa-presentation-runtime-refresh-20261104.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
}finally{await archive.close();}
