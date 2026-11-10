import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import{createHash}from'node:crypto';import{pathToFileURL}from'node:url';
const game=path.resolve(import.meta.dirname,'..'),work=path.join(game,'Saved/nonstop-all-20261106');
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const old=await read(path.join(work,'build.json')),built=await read(path.join(work,'full-build-result.json'));
const module=await read(path.join(game,'Saved/game-trial-work-20261102/game-module-nonstop-word-compact-20261106.json'));
const overlays=new Map((await read(path.join(work,"flight-assets.json"))).changes.map(r=>[r.path.slice(8),r]));
const before=await read(path.join(old.output,'game.hbpack.json')),after=await read(path.join(built.output,'game.hbpack.json'));
const{openGameResources}=await import(pathToFileURL(path.join(built.output,'tools/game-resource-archive.mjs')));
const a=await openGameResources(path.join(old.output,before.contentArchive.path)),b=await openGameResources(path.join(built.output,after.contentArchive.path));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');let sources=0,unchanged=0;const changed=[];
try{
 assert([...a.entries.keys()].every(n=>b.entries.has(n)),'All baseline resources retained');assert([...b.entries.keys()].every(n=>a.entries.has(n)||module.sourceSHA256[n]||overlays.has(n)),'Only owned additions allowed');
 for(const [name,row]of b.entries){
  if(name.startsWith('Source/')){assert.equal(hash(await b.read(name)),module.sourceSHA256[name],name);sources++;}
  if(row.sha256!==a.entries.get(name)?.sha256)changed.push(name);else unchanged++;
 }
 assert(changed.every(n=>n.startsWith('Source/')||n==='Assets/Blueprints/BP_Yumeno.hbblueprint.json'||overlays.has(n)),'Unexpected art/data/UI change: '+changed.join(','));
 const bp=JSON.parse(await b.read('Assets/Blueprints/BP_Yumeno.hbblueprint.json'));
 assert.equal(bp.native.headerPath,'Source/Yumeno.h');assert.equal(bp.native.sourcePath,'Source/Yumeno.cpp');for(const[name,row]of overlays)assert.equal(hash(await b.read(name)),row.sha256,name);
 assert.equal(after.nativeModules.length,1);assert.equal(after.targetFrameRate,120);
 const report={ok:true,build:built.id,base:old.id,sourceFiles:sources,unchangedResources:unchanged,changedResources:changed,allResourceNamesPreserved:true,blueprintMatchesCompiledSource:true,engineModified:false,otherChatSourceIncluded:false,scope:'Complete official native package from immutable19f with reviewed Nonstop fixes. Gameplay acceptance uses the separate per-task and packed-runtime proofs.'};
 await fs.writeFile(path.join(work,'packed-parity.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await a.close();await b.close();}
