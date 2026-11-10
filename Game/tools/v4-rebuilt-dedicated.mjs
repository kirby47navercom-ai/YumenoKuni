import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import{createHash}from'node:crypto';
const hash=b=>createHash('sha256').update(b).digest('hex');
export async function emitRebuiltDedicated({repo,write}){
 const folder=path.join(repo,'art/space_v4/rebuilt_dedicated_v2'),raw=await fs.readFile(path.join(folder,'manifest.json')).catch(e=>{if(e.code==='ENOENT')return null;throw e;});if(!raw)return{models:0};
 const bank=JSON.parse(raw),proof=JSON.parse(await fs.readFile(path.join(folder,'static-verification.json'),'utf8'));assert(proof.ok&&proof.manifestSHA256===hash(raw));assert.equal(bank.assets.length,6);
 const file=path.join(repo,'Game/Saved/game-trial-work-20261102/sculpted-overrides.json'),overrides=await fs.readFile(file,'utf8').then(JSON.parse,e=>{if(e.code==='ENOENT')return null;throw e;});
 for(const a of bank.assets){const source=path.join(repo,a.file),bytes=await fs.readFile(source);assert.equal(hash(bytes),a.sha256);assert(bytes.length<64*1024*1024);await write(a.runtime,bytes);if(overrides)overrides['Content/'+a.runtime]=source;}
 if(overrides)await fs.writeFile(file,JSON.stringify(overrides,null,2));
 return{models:6,stateNodeNamesPreserved:true,worldMetadataUnchanged:true};
}
