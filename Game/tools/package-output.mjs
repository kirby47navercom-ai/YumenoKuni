import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec=promisify(execFile),inside=(root,file)=>{const relative=path.relative(root,file);return relative!==''&&!relative.startsWith('..')&&!path.isAbsolute(relative);};
export async function exportPackage(repo,build,{zip=true}={}){
 repo=await fs.realpath(repo);const builds=await fs.realpath(path.join(repo,'Game/Builds')),source=await fs.realpath(build.output);assert(inside(builds,source),'Package source must be an owned build');
 const dist=path.join(repo,'dist');await fs.mkdir(dist,{recursive:true});assert.equal(await fs.realpath(dist),dist,'dist must not be a redirected directory');
 const manifest=JSON.parse(await fs.readFile(path.join(source,'game.hbpack.json'),'utf8')),names=[...manifest.files.map(f=>f.path),'game.hbpack.json','build-report.json'],seen=new Set();
 for(const name of names){assert(typeof name==='string'&&!path.isAbsolute(name)&&!/[\\:\x00-\x1f]/.test(name)&&!name.split('/').some(p=>!p||p==='.'||p==='..'),'Unsafe package path');assert(!seen.has(name.toLowerCase()),'Duplicate package path');seen.add(name.toLowerCase());assert(inside(source,await fs.realpath(path.join(source,name))),'Package file escaped build');}
 const stage=await fs.mkdtemp(path.join(dist,'.YumenoKuni-')),out=path.join(dist,'YumenoKuni'),zipPath=path.join(dist,'YumenoKuni-'+new Date().toISOString().slice(0,10)+'.zip'),moves=[];let archive,linked=0,copied=0,temporaryZip;
 const quarantine=async file=>{const stat=await fs.lstat(file).catch(e=>{if(e.code!=='ENOENT')throw e;return null;});if(!stat)return;if(stat.isSymbolicLink()||!inside(dist,await fs.realpath(file)))throw Error('Unsafe previous export');const root=path.join(repo,'삭제 대기');await fs.mkdir(root,{recursive:true});assert.equal(await fs.realpath(root),root,'Unsafe quarantine root');archive??=await fs.mkdtemp(path.join(root,'package-'));const destination=path.join(archive,path.basename(file));assert(inside(archive,destination));await fs.rename(file,destination);moves.push({source:file,destination});};
 try{
  for(const name of names){const target=path.join(stage,name);assert(inside(stage,target));await fs.mkdir(path.dirname(target),{recursive:true});try{await fs.link(path.join(source,name),target);linked++;}catch(error){if(!['EPERM','EXDEV','ENOTSUP','EACCES'].includes(error.code))throw error;await fs.copyFile(path.join(source,name),target,fs.constants.COPYFILE_EXCL);copied++;}}
  await quarantine(out);await fs.rename(stage,out);
  if(zip){temporaryZip=path.join(dist,'.YumenoKuni-'+Date.now()+'.zip');await exec(process.platform==='win32'?'C:/Windows/System32/tar.exe':'tar',['-a','-c','-f',temporaryZip,'-C',dist,'YumenoKuni'],{windowsHide:true,maxBuffer:1024*1024});assert((await fs.stat(temporaryZip)).size>0);await quarantine(zipPath);await fs.rename(temporaryZip,zipPath);}else await quarantine(zipPath);
  const result={folder:out,executable:path.join(out,path.basename(build.executable)),zip:zip?zipPath:null,sourceBuildPreserved:source,linked,copied,moves,deleted:0};await fs.mkdir(path.join(repo,'Game/Saved'),{recursive:true});await fs.writeFile(path.join(repo,'Game/Saved','package-export-'+Date.now()+'.json'),JSON.stringify(result,null,2));if(archive)await fs.writeFile(path.join(archive,'이동내역.json'),JSON.stringify(result,null,2));return result;
 }catch(error){await quarantine(stage).catch(()=>{});if(temporaryZip)await quarantine(temporaryZip).catch(()=>{});throw error;}
}
