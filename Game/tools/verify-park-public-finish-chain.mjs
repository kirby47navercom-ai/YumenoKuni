// Sequential owned-player checks. Never build or author assets during FPS runs.
import fs from 'node:fs/promises';import path from 'node:path';import {spawn} from 'node:child_process';import {createHash} from 'node:crypto';import assert from 'node:assert/strict';
const repo=path.resolve(import.meta.dirname,'../..'),work=path.join(repo,'Game/Saved/park-levels-20261104/public-space-finish');
const stages=[['views','verify-native-park-levels.mjs'],['public-walk','verify-native-park-public-spaces.mjs'],['lifecycle','verify-native-park-traversal.mjs'],['performance','verify-native-park-performance.mjs']],from=process.argv.find(a=>a.startsWith('--from='))?.slice(7)||'views',start=stages.findIndex(r=>r[0]===from);assert(start>=0,'Unknown checkpoint '+from);
const completed=[];
if(start){
 const bank=createHash('sha256').update(await fs.readFile(path.join(repo,'art/space_v4/park_levels_v1/manifest.json'))).digest('hex'),module=JSON.parse(await fs.readFile(path.join(work,'../game-module.json'),'utf8'));
 for(const [id]of stages.slice(0,start)){
  const file={views:'native-review.json','public-walk':'public-space-finish/native.json',lifecycle:'native-traversal.json'}[id],proof=JSON.parse(await fs.readFile(path.join(work,'..',file),'utf8'));
  assert(proof.ok&&proof.geometryManifestSHA256===bank&&(proof.gameModuleSHA256||proof.moduleSHA256)===module.binarySHA256,'Stale checkpoint '+id);completed.push(id);
 }
}
for(const [id,script]of stages.slice(start)){
 await fs.writeFile(path.join(work,'chain.json'),JSON.stringify({running:id,completed},null,2));
 const log=await fs.open(path.join(work,id+'.log'),'w');let exit;
 try{exit=await new Promise((resolve,reject)=>{const child=spawn(process.execPath,[path.join(repo,'Game/tools',script)],{cwd:repo,windowsHide:true,stdio:['ignore',log.fd,log.fd]});child.once('error',reject);child.once('exit',(code,signal)=>resolve({code,signal}));});}finally{await log.close();}
 assert.equal(exit.code,0,id+' failed; read its log before retrying');completed.push(id);console.log(JSON.stringify({completed:id}));
}
await fs.writeFile(path.join(work,'chain.json'),JSON.stringify({ok:true,completed},null,2));
