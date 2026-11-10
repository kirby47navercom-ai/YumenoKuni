// Incremental three-way merge: preserve our current reviewed delta and new publications.
import fs from'node:fs/promises';import path from'node:path';import assert from'node:assert/strict';import{pathToFileURL}from'node:url';import{spawnSync}from'node:child_process';import{createHash}from'node:crypto';
const game=path.resolve(import.meta.dirname,'..'),work=path.join(game,'Saved/nonstop-all-20261106'),read=async p=>JSON.parse(await fs.readFile(p,'utf8')),receipt=await read(path.join(work,'integration.json')),latest=await read(path.join(game,'build-result.json'));
if(latest.id===receipt.published){console.log('Integration already current');process.exit(0);}
const{openGameResources}=await import(pathToFileURL(path.join(latest.output,'tools/game-resource-archive.mjs'))),open=async out=>{const m=await read(path.join(out,'game.hbpack.json'));return openGameResources(path.join(out,m.contentArchive.path));},base=await open(receipt.publishedOutput),next=await open(latest.output),changes=new Map(),conflicts=[];
const text=b=>b.toString('utf8').replaceAll('\r\n','\n'),hash=b=>createHash('sha256').update(b).digest('hex');
try{for(const[name,row]of next.entries)if(name.startsWith('Source/')&&row.sha256!==base.entries.get(name)?.sha256){
 const file=path.join(work,'integrated',name),ours=await fs.readFile(file).then(text,()=>''),before=base.entries.has(name)?text(await base.read(name)):'',theirs=text(await next.read(name));let merged;
 if(ours===before||ours===theirs)merged=theirs;else if(before===theirs)merged=ours;else{
  const temp=path.join(work,'integrated','refresh-'+path.basename(name));for(const[s,value]of [['ours',ours],['base',before],['theirs',theirs]])await fs.writeFile(temp+'.'+s,value);
  const r=spawnSync('git',['merge-file','-p',temp+'.ours',temp+'.base',temp+'.theirs'],{encoding:'utf8',windowsHide:true,maxBuffer:8*1024*1024});merged=r.stdout;if(r.status!==0){conflicts.push(name);await fs.writeFile(temp+'.conflict',merged);}
 }changes.set(name,Buffer.from(merged));
}
assert.equal(conflicts.length,0,'Resolve incremental conflicts: '+conflicts.join(','));for(const[name,bytes]of changes)await fs.writeFile(path.join(work,'integrated',name),bytes);
receipt.previousPublished=receipt.published;receipt.published=latest.id;receipt.publishedOutput=latest.output;receipt.incrementalChanges=[...changes.keys()];receipt.sourceSHA256={};for(const f of await fs.readdir(path.join(work,'integrated/Source')))receipt.sourceSHA256['Source/'+f]=hash(await fs.readFile(path.join(work,'integrated/Source',f)));await fs.writeFile(path.join(work,'integration.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify({published:latest.id,changes:[...changes.keys()]}));
}finally{await base.close();await next.close();}
