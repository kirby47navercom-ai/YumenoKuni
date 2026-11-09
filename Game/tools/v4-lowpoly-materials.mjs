// Publish a complete, verified high-to-low bake bank after the material source bank.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
const hash=b=>createHash('sha256').update(b).digest('hex');
export async function emitLowpolyMaterials({repo,write}){
 const file=path.join(repo,'art/space_v4/lowpoly_v1/manifest.json'),raw=await fs.readFile(file).catch(e=>{if(e.code==='ENOENT')return null;throw e;});if(!raw)return {models:0};
 const manifest=JSON.parse(raw),proof=await fs.readFile(path.join(repo,'Game/Saved/sculpted-environment-20261103/lowpoly-static-verification.json'),'utf8').then(JSON.parse,e=>{if(e.code==='ENOENT')return null;throw e;});
 if(!manifest.complete||!proof?.ok||proof.manifestSHA256!==hash(raw))return {models:0,reason:'Unpublished bake bank is still being verified'};
 assert.equal(manifest.sourceManifestSHA256,hash(await fs.readFile(path.join(repo,'art/space_v4/materials_v2/manifest.json'))),'High source bank changed; rebake before publishing');
 const copiesFile=path.join(repo,'art/space_v4/runtime_v1/copy_manifest.json'),copies=JSON.parse(await fs.readFile(copiesFile,'utf8'));
 for(const a of manifest.assets){const b=await fs.readFile(path.join(repo,a.file));assert.equal(hash(b),a.sha256,a.file);await write(a.runtime,b);const row=copies.find(r=>r.to===a.runtime);if(row)row.from=a.file;}
 await fs.writeFile(copiesFile,JSON.stringify(copies,null,1)+'\n');return {models:manifest.assets.length,beforeTriangles:manifest.beforeTriangles,afterTriangles:manifest.afterTriangles};
}
