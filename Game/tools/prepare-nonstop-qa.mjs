// Refresh the retained owned QA package from one immutable full build.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/nonstop-all-20261106');await fs.mkdir(work,{recursive:true});
const build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const out=path.join(root,'Saved/native-panic-views-1793690486425/package');
const m=JSON.parse(await fs.readFile(path.join(out,'game.hbpack.json'),'utf8')),base=JSON.parse(await fs.readFile(path.join(build.output,'game.hbpack.json'),'utf8'));
assert(!m.contentArchive);const {openGameResources}=await import(pathToFileURL(path.join(build.output,'tools/game-resource-archive.mjs'))),archive=await openGameResources(path.join(build.output,base.contentArchive.path));
const rows=new Map(m.files.map(r=>[r.path,r])),updated=[];let addedBytes=0;
async function put(name,bytes){const file=path.resolve(out,name);assert(file.startsWith(out+path.sep));await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file+'.nonstop.tmp',bytes);await fs.rename(file+'.nonstop.tmp',file);const row={path:name,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')};if(rows.has(name))Object.assign(rows.get(name),row);else{rows.set(name,row);m.files.push(row);}updated.push(name);addedBytes+=bytes.length;}
try{
 for(const [name,row]of archive.entries){
  const target='Content/'+name;if(name==='Assets/Blueprints/BP_Yumeno.hbblueprint.json')continue;
  if(rows.get(target)?.sha256===row.sha256&&await fs.access(path.join(out,target)).then(()=>true,()=>false))continue;
  await put(target,await archive.read(name));
 }
 for(const row of base.files){if(row.path===base.contentArchive.path)continue;if(rows.get(row.path)?.sha256!==row.sha256)await put(row.path,await fs.readFile(path.join(build.output,row.path)));}
 const file='Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json',bp=JSON.parse(await fs.readFile(path.join(out,file),'utf8')),original=JSON.parse(await archive.read('Assets/Blueprints/BP_Yumeno.hbblueprint.json'));
 bp.native=original.native;await put(file,Buffer.from(JSON.stringify(bp)));m.nativeModules=base.nativeModules;m.entries=base.entries;m.startupScene=base.startupScene;
 await fs.writeFile(path.join(out,'game.hbpack.json'),JSON.stringify(m));await fs.writeFile(path.join(work,'build.json'),JSON.stringify(build,null,2));
 const receipt={build:build.id,output:out,updated,addedBytes,newFullPackage:false,engineModified:false,scope:'Immutable full resources/module; retained Stats/F2 fixture bindings only. No outcome injection.'};await fs.writeFile(path.join(work,'qa-sync.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify({build:build.id,updated:updated.length,addedBytes}));
}finally{await archive.close();}
