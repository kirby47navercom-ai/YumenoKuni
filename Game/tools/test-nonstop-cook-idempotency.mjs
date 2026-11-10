// Reintegrating a published Nonstop cook may not grow the retained glyph bank.
import fs from'node:fs/promises';import path from'node:path';import assert from'node:assert/strict';import{pathToFileURL}from'node:url';
import{mergeNonstopCook}from'./merge-nonstop-cook.mjs';import{validGameJson}from'../../../engineCreate/prototype/game-json.js';
const game=path.resolve(import.meta.dirname,'..'),source=path.join(game,'Saved/nonstop-all-20261106'),work=path.join(game,'Saved/nonstop-guidance-20261106/cook-regression');await fs.mkdir(work,{recursive:true});
for(const file of ['integration.json','full-build-result.json'])await fs.copyFile(path.join(source,file),path.join(work,file));
const integration=JSON.parse(await fs.readFile(path.join(work,'integration.json'),'utf8')),base=integration.publishedOutput,manifest=JSON.parse(await fs.readFile(path.join(base,'game.hbpack.json'),'utf8')),{openGameResources}=await import(pathToFileURL(path.join(base,'tools/game-resource-archive.mjs'))),packed=await openGameResources(path.join(base,manifest.contentArchive.path)),overlays=new Map();
try{
 const archive={entries:packed.entries,read:async name=>overlays.get(name)||packed.read(name)},overlay=async(name,bytes)=>overlays.set(name,bytes),first=await mergeNonstopCook({game,work,archive,overlay}),second=await mergeNonstopCook({game,work,archive,overlay});
 assert.deepEqual(second,first,'A second merge changes the layout');assert(validGameJson(second,{object:false}),'Merged layout exceeds actual runtime data limits');
 const result={ok:true,base:integration.published,glyphs:first.glyphs.length,batches:first.batches.length,mergeCount:2,bytes:Buffer.byteLength(JSON.stringify(second))};await fs.writeFile(path.join(work,'result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{await packed.close();}
