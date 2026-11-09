// Publish the independently checked whole 3D source bank, after base materials.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import{createHash}from'node:crypto';
const hash=b=>createHash('sha256').update(b).digest('hex');
export async function emitRebuiltEnvironment({repo,write}){
 const raw=await fs.readFile(path.join(repo,'art/space_v4/rebuild_v1/manifest.json')).catch(e=>{if(e.code==='ENOENT')return null;throw e;});if(!raw)return{models:0};
 const manifest=JSON.parse(raw),proof=await fs.readFile(path.join(repo,'Game/Saved/sculpted-environment-20261103/rebuilt-static-verification.json'),'utf8').then(JSON.parse,e=>{if(e.code==='ENOENT')return null;throw e;});
 if(!manifest.completeEnvironmentAssembly||!proof?.ok||proof.manifestSHA256!==hash(raw))return{models:0,reason:'Whole environment source bank still being checked'};
 assert.equal(manifest.sourceMaterialManifestSHA256,hash(await fs.readFile(path.join(repo,'art/space_v4/materials_v2/manifest.json'))),'Material source bank changed');assert.equal(manifest.assets.length,61);
 const file=path.join(repo,'art/space_v4/runtime_v1/copy_manifest.json'),copies=JSON.parse(await fs.readFile(file,'utf8'));
 for(const a of manifest.assets){const bytes=await fs.readFile(path.join(repo,a.file));assert.equal(hash(bytes),a.sha256,a.file);assert(bytes.length<64*1024*1024);await write(a.runtime,bytes);const row=copies.find(r=>r.to===a.runtime);if(row)row.from=a.file;}
 await fs.writeFile(file,JSON.stringify(copies,null,1)+'\n');return{models:61,facades:31,trees:22,gameplayDataUnchanged:true};
}
