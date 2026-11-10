// Existing task QA uses physical Content files. Reuse verified immutable old
// package files, materializing only changed entries from our game's archive.
import fs from 'node:fs/promises';
import {createWriteStream} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {Transform} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/game-trial-work-20261102');
const pointerArgument=process.argv.find(v=>v.startsWith('--output-pointer='))?.slice('--output-pointer='.length),pointer=pointerArgument?path.resolve(root,pointerArgument):path.join(work,'current-flat-build-result.json');
assert(pointer.startsWith(path.join(root,'Saved')+path.sep),'QA pointer must remain in Saved');
const build=JSON.parse(await fs.readFile(process.argv.find(v=>v.startsWith('--build-result='))?.slice(15)||path.join(root,'build-result.json'),'utf8'));
const {openGameResources}=await import(pathToFileURL(path.join(build.output,'tools/game-resource-archive.mjs')));
const {hashBuildFile}=await import(pathToFileURL(path.join(build.output,'tools/build-content.mjs')));
const frozen=JSON.parse(await fs.readFile(path.join(work,'build-result.json'),'utf8'));
let reuse=frozen;
try{
 const current=JSON.parse(await fs.readFile(path.join(work,'current-flat-build-result.json'),'utf8'));
 assert.equal(path.dirname(current.output),work,'Only the owned immutable flat cache may be reused');
 assert(path.basename(current.output).startsWith('flat-current-'));
 const proof=JSON.parse(await fs.readFile(path.join(current.output,'qa-content-receipt.json'),'utf8'));
 assert.equal(proof.baseBuild,current.id);assert.equal(proof.engineFilesChanged,0);reuse=current;
}catch(error){if(error.code!=='ENOENT')throw error;}
const previous=JSON.parse(await fs.readFile(path.join(reuse.output,'game.hbpack.json'),'utf8'));
const manifest=JSON.parse(await fs.readFile(path.join(build.output,'game.hbpack.json'),'utf8'));
assert(manifest.contentArchive);assert.equal(previous.id,manifest.id);
const out=path.join(work,'flat-current-'+build.id);await fs.mkdir(out);const oldFiles=new Map(previous.files.map(f=>[f.path,f]));
const archive=await openGameResources(path.join(build.output,manifest.contentArchive.path));
const receipt={baseBuild:build.id,base:build.output,output:out,reusedBase:reuse.output,engineFilesChanged:0,linked:0,materialized:0,entries:[],scope:'QA-only flat Content representation. Every resource has identical verified bytes; native executable/module/engine runtime remain identical. Not a shipping build.'};
const safe=name=>!path.isAbsolute(name)&&!name.split(/[\\/]/).some(p=>p==='..');
const directories=new Map(),mkdir=dir=>{if(!directories.has(dir))directories.set(dir,fs.mkdir(dir,{recursive:true}));return directories.get(dir);};
try{
 const files=[];
 for(const row of manifest.files){
  if(row.path===manifest.contentArchive.path)continue;assert(safe(row.path));
  const target=path.join(out,row.path);await fs.mkdir(path.dirname(target),{recursive:true});await fs.link(path.join(build.output,row.path),target);files.push(row);
 }
 const entries=[...archive.entries];
 for(let at=0;at<entries.length;at+=16){
 const batch=await Promise.allSettled(entries.slice(at,at+16).map(async([name,entry])=>{
  const relative='Content/'+name;assert(safe(relative));const target=path.join(out,relative);await mkdir(path.dirname(target));const old=oldFiles.get(relative);let linked=false;
  if(old?.bytes===entry.bytes&&old.sha256===entry.sha256){const source=path.join(reuse.output,relative),actual=await hashBuildFile(source,{root:reuse.output});assert.equal(actual.sha256,entry.sha256);assert.equal(actual.bytes,entry.bytes);await fs.link(source,target);receipt.linked++;linked=true;}
  if(!linked){
   const hash=createHash('sha256');let bytes=0;
   if(entry.bytes){const verify=new Transform({transform(chunk,encoding,next){hash.update(chunk);bytes+=chunk.length;next(null,chunk);}});await pipeline(archive.stream(name,0,entry.bytes-1),verify,createWriteStream(target,{flags:'wx'}));}
   else await fs.writeFile(target,'',{flag:'wx'});
   assert.equal(bytes,entry.bytes);assert.equal(hash.digest('hex'),entry.sha256);receipt.materialized++;
  }
  return {file:{path:relative,bytes:entry.bytes,sha256:entry.sha256},proof:{path:name,linked,sha256:entry.sha256}};
 }));
 for(const result of batch)if(result.status==='rejected')throw result.reason;
 for(const result of batch){files.push(result.value.file);receipt.entries.push(result.value.proof);}
 }
 delete manifest.contentArchive;manifest.files=files;await fs.writeFile(path.join(out,'game.hbpack.json'),JSON.stringify(manifest,null,2),{flag:'wx'});
 await fs.writeFile(path.join(out,'qa-content-receipt.json'),JSON.stringify(receipt,null,2),{flag:'wx'});
 await fs.writeFile(pointer,JSON.stringify({...build,output:out,executable:path.join(out,manifest.windowsApplication.executable),qaRepresentation:receipt.scope},null,2));
 console.log(JSON.stringify({build:build.id,output:out,linked:receipt.linked,materialized:receipt.materialized,engineFilesChanged:0}));
}finally{await archive.close();}
