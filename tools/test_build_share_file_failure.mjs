import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {installBuildSharing} from '../Game/tools/build-share.mjs';
const root=await fs.mkdtemp(path.resolve('Game/Saved/build-share-unit-'));
const hash=b=>createHash('sha256').update(b).digest('hex');
for(const streaming of [false,true]){
 const base=path.join(root,streaming?'stream':'buffer'),old=path.join(base,'Builds/windows/old'),next=path.join(base,'Builds/windows/new');
 await fs.mkdir(path.join(old,'Content'),{recursive:true});await fs.mkdir(path.join(next,'Content'),{recursive:true});
 const rows=['one.bin','two.bin'].map((name,i)=>({path:'Content/'+name,bytes:70000,sha256:hash(Buffer.alloc(70000,31+i))}));
 for(const [i,row]of rows.entries())await fs.writeFile(path.join(old,row.path),Buffer.alloc(row.bytes,31+i));
 await fs.writeFile(path.join(old,'game.hbpack.json'),JSON.stringify({id:'file-failure-unit',files:rows}));
 const rename=fs.rename;let failures=0;
 fs.rename=async function(a,b){if(String(a).includes('.shared-')&&String(b).endsWith('one.bin')){failures++;throw Object.assign(Error('injected per-file sharing violation'),{code:'EPERM'});}return rename.call(fs,a,b);};
 const sharing=await installBuildSharing({root:base,profile:'windows',previous:old,projectId:'file-failure-unit',bufferBytes:streaming?1000:100000});
 try{for(const [i,row]of rows.entries()){const h=await fs.open(path.join(next,row.path),'wx');const bytes=Buffer.alloc(row.bytes,31+i);await h.write(bytes,0,bytes.length);await h.close();}}
 finally{sharing.restore();fs.rename=rename;}
 assert.equal(failures,1);assert.equal(sharing.stats.disabled,'');assert.equal(sharing.stats.linked,1);assert.equal(sharing.stats.fallback,1);assert.deepEqual(sharing.stats.fileErrors,[{path:'Content/one.bin',code:'EPERM'}]);
 for(const row of rows){assert.equal(hash(await fs.readFile(path.join(old,row.path))),row.sha256);assert.equal(hash(await fs.readFile(path.join(next,row.path))),row.sha256);}
 assert.equal((await fs.stat(path.join(old,'Content/two.bin'))).ino,(await fs.stat(path.join(next,'Content/two.bin'))).ino);
 assert.notEqual((await fs.stat(path.join(old,'Content/one.bin'))).ino,(await fs.stat(path.join(next,'Content/one.bin'))).ino);
 assert(!(await fs.readdir(path.join(next,'Content'))).some(n=>n.includes('.shared-')));
}
console.log(JSON.stringify({status:'PASS',scope:'EPERM stays per-file, later verified content still shares; buffered/streamed fallback preserves both packages, no temporary links remain',fixture:root,playerLaunch:false}));
