// Compare the art-only candidate with its frozen baseline, independently of emission.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import{pathToFileURL}from'node:url';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/sculpted-environment-20261103');
const build=JSON.parse(await fs.readFile(path.join(work,'build-result.json'),'utf8')),baseArg=process.argv.find(v=>v.startsWith('--baseline='))?.slice('--baseline='.length),base=baseArg?{output:path.resolve(root,baseArg),id:path.basename(baseArg)}:JSON.parse(await fs.readFile(path.join(work,'rebuilt-baseline-build.json'),'utf8'));
assert.equal(path.resolve(build.baseline),path.resolve(base.output));
const old=JSON.parse(await fs.readFile(path.join(base.output,'game.hbpack.json'),'utf8')),now=JSON.parse(await fs.readFile(path.join(build.output,'game.hbpack.json'),'utf8'));
const{openGameResources}=await import(pathToFileURL(path.join(build.output,'tools/game-resource-archive.mjs')));
const a=await openGameResources(path.join(base.output,old.contentArchive.path)),b=await openGameResources(path.join(build.output,now.contentArchive.path));
try{
 const allowed=new Set(Object.keys(JSON.parse(await fs.readFile(path.join(root,'Saved/game-trial-work-20261102/sculpted-overrides.json'),'utf8'))).map(n=>n.slice(8))),changed=[];
 assert.equal(a.entries.size,b.entries.size);
 for(const[name,row]of a.entries){const other=b.entries.get(name);assert(other,name);if(row.sha256!==other.sha256||row.bytes!==other.bytes){assert(allowed.has(name),'Unexpected non-art change: '+name);changed.push(name);}}
 assert.deepEqual(old.files.filter(f=>f.path!==old.contentArchive.path),now.files.filter(f=>f.path!==now.contentArchive.path));assert.deepEqual(old.nativeModules,now.nativeModules);
 const result={ok:true,build:build.id,output:build.output,baseline:base.id,entries:b.entries.size,changedResources:changed,allowedArtResources:allowed.size,nativeModules:now.nativeModules,engineAndNativeModuleIdentical:true,storyAndOtherContentIdentical:true,scope:'Archive entries compared by byte length/SHA. All changed entries are declared generated art; every executable/module/engine file and native module descriptor equals frozen baseline. No current parallel source changes are incorporated.'};
 await fs.writeFile(path.join(work,'final-package-identity.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({ok:true,build:build.id,entries:b.entries.size,changedResources:changed.length,engineAndStoryIdentical:true}));
}finally{await a.close();await b.close();}
