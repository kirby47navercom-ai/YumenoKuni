// Preserve every archived package path and byte; share immutable duplicate Content.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import {hashBuildFile} from '../../engineCreate/tools/build-content.mjs';
const root=await fs.realpath(path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..')),quarantine=await fs.realpath(path.join(root,'삭제 대기')),apply=process.argv.includes('--apply'),latestOnly=process.argv.includes('--latest-only');
const inside=(base,p)=>{const r=path.relative(base,p);return !!r&&!r.startsWith('..'+path.sep)&&r!=='..'&&!path.isAbsolute(r);};
const read=async p=>JSON.parse((await fs.readFile(p,'utf8')).replace(/^\uFEFF/,''));
const result=await read(path.join(root,'Game/build-result.json')),latestRoot=await fs.realpath(path.dirname(result.executable)),sourceRoot=latestOnly?await fs.realpath(result.contentSharing.previous):latestRoot;
if(!inside(path.join(root,'Game/Builds'),sourceRoot))throw Error('Authoritative package is outside Game/Builds');
if(!inside(path.join(root,'Game/Builds'),latestRoot)||latestOnly&&sourceRoot===latestRoot)throw Error('Latest/previous package roots are invalid');
const sourceManifest=await read(path.join(sourceRoot,'game.hbpack.json')),entries=new Map(sourceManifest.files.filter(f=>f.path.startsWith('Content/')&&f.bytes>=65536).map(f=>[f.path,f])),archives=new Set();
if(latestOnly)archives.add(latestRoot);else for(const name of await fs.readdir(path.join(root,'Game/Saved'))){if(!/^build-retention-.*\.json$/.test(name))continue;const receipt=await read(path.join(root,'Game/Saved',name));for(const r of receipt.records||[])if(r.moved&&r.reason==='superseded-generated-build'&&r.destination){let p;try{p=await fs.realpath(r.destination);}catch(e){if(e.code==='ENOENT')continue;throw e;}if(inside(quarantine,p))archives.add(p);}}
const report={mode:apply?'apply':'dry-run',source:sourceRoot,scope:latestOnly?'Only latest package immutable Content against its recorded previous package; exact project/manifest/actual bytes verified, paths preserved. No player launch or editable Assets/source linked.':'Only receipted superseded-generated-build immutable Content. All package/source/save/report paths and file bytes preserved; no editable Assets/originals linked.',archives:archives.size,eligible:0,eligibleBytes:0,linked:0,linkedBytes:0,alreadyShared:0,invalid:[],errors:[],files:[]},verified=new Map();
for(const archive of archives){
 let manifest;try{manifest=await read(path.join(archive,'game.hbpack.json'));}catch(e){report.errors.push({archive,error:e.message});continue;}
 if(manifest.id!==sourceManifest.id){report.invalid.push({archive,reason:'project-identity'});continue;}
 for(const entry of manifest.files){const source=entries.get(entry.path);if(!source||entry.bytes!==source.bytes||entry.sha256!==source.sha256)continue;
  const targetPath=path.resolve(archive,entry.path),sourcePath=path.resolve(sourceRoot,source.path);if(!inside(archive,targetPath)||!inside(sourceRoot,sourcePath)||!entry.path.startsWith('Content/'))throw Error('Package path escaped verified roots');
  let temporary='';try{
   const target=await fs.realpath(targetPath),canonical=await fs.realpath(sourcePath);if(!inside(archive,target)||!inside(sourceRoot,canonical))throw Error('Package content resolved outside build');
   const [old,original]=await Promise.all([fs.stat(target,{bigint:true}),fs.stat(canonical,{bigint:true})]);if(!old.isFile()||!original.isFile())throw Error('Package content is not regular file');
   if(old.dev===original.dev&&old.ino===original.ino){report.alreadyShared++;continue;}
   report.eligible++;report.eligibleBytes+=entry.bytes;if(!apply)continue;
   if(!verified.has(canonical)){const actual=await hashBuildFile(canonical,{root:sourceRoot});if(actual.bytes!==source.bytes||actual.sha256!==source.sha256)throw Error('Authoritative package bytes differ from manifest');verified.set(canonical,actual);}
   const actual=await hashBuildFile(target,{root:archive});if(actual.bytes!==entry.bytes||actual.sha256!==entry.sha256){report.invalid.push({path:target,reason:'archived-bytes-differ'});continue;}
   temporary=target+'.dedup-'+randomUUID();await fs.link(canonical,temporary);await fs.rename(temporary,target);temporary='';
   const linked=await fs.stat(target,{bigint:true});if(linked.dev!==original.dev||linked.ino!==original.ino||Number(linked.size)!==entry.bytes)throw Error('Shared archived file identity mismatch');
   report.linked++;report.linkedBytes+=entry.bytes;report.files.push({path:target,sha256:entry.sha256,bytes:entry.bytes,previousLinks:Number(old.nlink),inode:String(linked.ino)});
  }catch(e){report.errors.push({path:targetPath,error:e.message});}finally{if(temporary)await fs.unlink(temporary).catch(()=>{});}
 }
}
const output=path.join(root,'Game/Saved',(latestOnly?'latest-content-dedup-':'archived-content-dedup-')+Date.now()+'.json');await fs.writeFile(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({...report,files:report.files.length,invalid:report.invalid.length,errors:report.errors.slice(0,3),receipt:output}));if(report.errors.length)process.exitCode=1;
