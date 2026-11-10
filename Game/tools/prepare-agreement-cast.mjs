import fs from'node:fs/promises';import path from'node:path';import assert from'node:assert/strict';import{createHash}from'node:crypto';import{emitAgreementCast,agreementHeader}from'./v4-agreement-cast.mjs';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),work=path.join(game,'Saved/nonstop-all-20261106'),evidence=path.join(game,'Saved/nonstop-guidance-20261106/agreement-cast');await fs.mkdir(evidence,{recursive:true});
const sourceFile=path.join(work,'integrated/Source/EndingSourceFramesV4.hpp'),before=await fs.readFile(sourceFile,'utf8'),changes=[],resources=[];
const list=s=>JSON.parse('['+s.match(/inline const std::vector<std::string> textures\{(.*?)\};/s)[1]+']');
const result=await emitAgreementCast({game,repo,sourceHeader:before,write:async(name,value)=>{
 const bytes=Buffer.isBuffer(value)?value:Buffer.from(typeof value==='string'?value:JSON.stringify(value));
 const target=name.startsWith('Source/')?path.join(work,'integrated',name):path.join(game,name);await fs.mkdir(path.dirname(target),{recursive:true});
 const row={path:name,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')};if(name.startsWith('Assets/'))resources.push(row);
 const old=await fs.readFile(target).catch(()=>null);if(!old?.equals(bytes)){await fs.writeFile(target,bytes);changes.push(row);}
}});
const after=await fs.readFile(sourceFile,'utf8'),oldFiles=list(before),newFiles=list(after);assert.deepEqual(newFiles.slice(0,oldFiles.length),oldFiles,'Keep all other timeline indices');
const current=path.join(game,'Source/EndingSourceFramesV4.hpp');await fs.writeFile(current,agreementHeader(await fs.readFile(current,'utf8'),result.files,result.shadowFiles));
assert.equal(agreementHeader(after,result.files,result.shadowFiles),after,'Repeat generation must be idempotent');
await fs.writeFile(path.join(evidence,'generated-assets.json'),JSON.stringify({...result,changes,resources,otherTextureIndices:oldFiles.length,addedTextures:newFiles.length-oldFiles.length},null,2));console.log(JSON.stringify({changes:changes.length,resources:resources.length,addedTextures:newFiles.length-oldFiles.length,otherTimelineIndicesPreserved:true}));
