// Compose only our reviewed source delta onto the latest completed shared build.
import fs from'node:fs/promises';import path from'node:path';import assert from'node:assert/strict';import{pathToFileURL}from'node:url';import{spawnSync}from'node:child_process';import{createHash}from'node:crypto';
const game=path.resolve(import.meta.dirname,'..'),work=path.join(game,'Saved/nonstop-all-20261106'),read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const base=await read(path.join(work,'build.json')),latest=await read(path.join(game,'build-result.json')),own=await read(path.join(work,'full-build-result.json'));
const{openGameResources}=await import(pathToFileURL(path.join(latest.output,'tools/game-resource-archive.mjs')));
const open=async b=>{const m=await read(path.join(b.output,'game.hbpack.json'));return{m,a:await openGameResources(path.join(b.output,m.contentArchive.path))};};
const b=await open(base),l=await open(latest),o=await open(own),out=path.join(work,'integrated');await fs.mkdir(path.join(out,'Source'),{recursive:true});const changed=[],conflicts=[];
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
try{
 for(const[name,row]of l.a.entries)if(name.startsWith('Source/'))await fs.writeFile(path.join(out,name),await l.a.read(name));
 for(const[name,row]of o.a.entries)if(name.startsWith('Source/')&&row.sha256!==b.a.entries.get(name)?.sha256){
  const ours=await o.a.read(name),before=b.a.entries.has(name)?await b.a.read(name):Buffer.alloc(0),theirs=l.a.entries.has(name)?await l.a.read(name):Buffer.alloc(0);let merged;
  if(!before.length){assert(!theirs.length||hash(ours)===hash(theirs),'Different new source: '+name);merged=ours;}
  else if(hash(theirs)===hash(before)||hash(theirs)===hash(ours))merged=ours;
  else{const temp=path.join(out,'merge-'+path.basename(name));for(const[suffix,bytes]of [['ours',ours],['base',before],['theirs',theirs]])await fs.writeFile(temp+'.'+suffix,bytes);const r=spawnSync('git',['merge-file','-p',temp+'.ours',temp+'.base',temp+'.theirs'],{encoding:'utf8',windowsHide:true,maxBuffer:8*1024*1024});if(r.status!==0)conflicts.push(name);merged=Buffer.from(r.stdout||'');}
  await fs.writeFile(path.join(out,name),merged);changed.push(name);
 }
 const receipt={base:base.id,published:latest.id,publishedOutput:latest.output,own:own.id,changedSources:changed,conflicts,sourceSHA256:{}};
 for(const name of await fs.readdir(path.join(out,'Source')))receipt.sourceSHA256['Source/'+name]=hash(await fs.readFile(path.join(out,'Source',name)));
 await fs.writeFile(path.join(work,'integration.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify({published:latest.id,files:Object.keys(receipt.sourceSHA256).length,conflicts}));assert.equal(conflicts.length,0,'Resolve only listed three-way conflicts before compiling');
}finally{await b.a.close();await l.a.close();await o.a.close();}
