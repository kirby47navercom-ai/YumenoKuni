import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash,randomUUID} from 'node:crypto';
import {hashBuildFile} from '../engineCreate/tools/build-content.mjs';
const inside=(base,file)=>{const r=path.relative(base,file);return r&&!r.startsWith('..'+path.sep)&&r!=='..'&&!path.isAbsolute(r);};
// Packages are immutable outputs. Share only verified identical packaged bytes,
// never editable Game/Assets or source files. No previous file is removed.
export async function installBuildSharing({root,profile,previous,projectId,minBytes=65536,maxBytes=512*1024*1024,bufferBytes=64*1024*1024}){
 const stats={linked:0,reusedBytes:0,fallback:0,streamed:0,disabled:'',previous:'',fileErrors:[]},originalOpen=fs.open;
 if(!previous)return {stats,restore(){}};
 let previousRoot,buildRoot,entries;
 try{buildRoot=await fs.realpath(path.join(root,'Builds',profile));previousRoot=await fs.realpath(previous);if(!inside(buildRoot,previousRoot))throw Error('Previous build outside project profile');const manifest=JSON.parse(await fs.readFile(path.join(previousRoot,'game.hbpack.json'),'utf8'));if(manifest.id!==projectId)throw Error('Previous build identity mismatch');entries=new Map(manifest.files.filter(f=>f.path.startsWith('Content/')&&f.bytes>=minBytes&&f.bytes<=maxBytes).map(f=>[f.path,f]));stats.previous=previousRoot;}catch(error){stats.disabled=error.message;return {stats,restore(){}};}
 fs.open=async function(file,flags,...options){
  if(flags!=='wx'||typeof file!=='string'||stats.disabled)return originalOpen.call(fs,file,flags,...options);
  const target=path.resolve(file),relative=path.relative(buildRoot,target),parts=relative.split(path.sep),name=parts.slice(1).join('/'),entry=entries.get(name);
  if(!inside(buildRoot,target)||parts.length<3||parts[1]!=='Content'||!entry||path.join(buildRoot,parts[0])===previousRoot)return originalOpen.call(fs,file,flags,...options);
  const source=path.resolve(previousRoot,entry.path);if(!inside(previousRoot,source))return originalOpen.call(fs,file,flags,...options);
  let handle=await originalOpen.call(fs,file,flags,...options),closed=false,chunks=[],bytes=0,streaming=entry.bytes>bufferBytes;const digest=createHash('sha256');if(streaming)stats.streamed++;
  const writeAll=async b=>{let at=0;while(at<b.length){const r=await handle.write(b,at,b.length-at);if(!r.bytesWritten)throw Error('Shared build streamed write failed');at+=r.bytesWritten;}};
  return {
   async write(buffer,offset,length){const b=buffer.subarray(offset,offset+length);if(!streaming&&bytes+b.length>bufferBytes){for(const chunk of chunks)await writeAll(chunk);chunks=[];streaming=true;stats.streamed++;}if(streaming)await writeAll(b);else chunks.push(Buffer.from(b));bytes+=b.length;digest.update(b);return {bytesWritten:b.length};},
   async close(){
    if(closed)return;closed=true;const current=digest.digest('hex');let temporary='';
    try{
     if(bytes===entry.bytes&&current===entry.sha256){
      const verified=await hashBuildFile(source,{root:previousRoot});
      if(verified.bytes===bytes&&verified.sha256===current){
       await handle.close();handle=null;temporary=target+'.shared-'+randomUUID();
       try{await fs.link(source,temporary);await fs.rename(temporary,target);temporary='';stats.linked++;stats.reusedBytes+=bytes;return;}catch(error){if(['ENOTSUP','EXDEV'].includes(error.code))stats.disabled=error.code;else if(stats.fileErrors.length<8)stats.fileErrors.push({path:entry.path,code:error.code||'unknown'});}
      }
     }
    }catch(error){if(error.code!=='ENOENT'){await handle?.close().catch(()=>{});handle=null;throw error;}}
    finally{if(temporary)await fs.unlink(temporary).catch(()=>{});}
    if(streaming){await handle?.close();handle=null;stats.fallback++;return;}
    try{if(!handle)handle=await originalOpen.call(fs,target,'r+');await handle.truncate(0);for(const chunk of chunks){let at=0;while(at<chunk.length){const r=await handle.write(chunk,at,chunk.length-at);if(!r.bytesWritten)throw Error('Shared build fallback write failed');at+=r.bytesWritten;}}stats.fallback++;}finally{await handle?.close();handle=null;chunks=[];}
   }
  };
 };
 return {stats,restore(){fs.open=originalOpen;}};
}
