import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {writeBuildContent} from '../../../engineCreate/tools/build-content.mjs';
import {installBuildSharing} from './build-share.mjs';
const root=path.resolve('Saved/build-share-unit-'+Date.now()),previous=path.join(root,'Builds/windows/previous'),output=path.join(root,'Builds/windows/current'),hash=b=>createHash('sha256').update(b).digest('hex');
await fs.mkdir(path.join(previous,'Content/Assets'),{recursive:true});await fs.mkdir(output,{recursive:true});
const a=Buffer.alloc(140000,37),b=Buffer.from('old bytes'),largeChanged=Buffer.alloc(150000,38);
await fs.writeFile(path.join(previous,'Content/Assets/a.bin'),a);await fs.writeFile(path.join(previous,'Content/Assets/b.bin'),b);await fs.writeFile(path.join(previous,'Content/Assets/c.bin'),Buffer.from('tampered'));await fs.writeFile(path.join(previous,'Content/Assets/d.bin'),a);
await fs.writeFile(path.join(previous,'game.hbpack.json'),JSON.stringify({id:'unit-project',files:[{path:'Content/Assets/a.bin',bytes:a.length,sha256:hash(a)},{path:'Content/Assets/b.bin',bytes:b.length,sha256:hash(b)},{path:'Content/Assets/c.bin',bytes:b.length,sha256:hash(b)},{path:'Content/Assets/d.bin',bytes:a.length,sha256:hash(a)}]}));
const sharing=await installBuildSharing({root,profile:'windows',previous,projectId:'unit-project',minBytes:0,bufferBytes:65536});
try{
 const ra=await writeBuildContent(output,'Content/Assets/a.bin',a);assert.equal(ra.sha256,hash(a));assert.deepEqual(await fs.readFile(path.join(output,ra.path)),a);assert.equal(sharing.stats.streamed,1);const before=await fs.stat(path.join(previous,ra.path)),after=await fs.stat(path.join(output,ra.path));if(!sharing.stats.disabled){assert.equal(before.ino,after.ino);assert(before.nlink>=2);}
 const different=Buffer.from('new bytes');await writeBuildContent(output,'Content/Assets/b.bin',different);assert.deepEqual(await fs.readFile(path.join(previous,'Content/Assets/b.bin')),b);assert.deepEqual(await fs.readFile(path.join(output,'Content/Assets/b.bin')),different);
 await writeBuildContent(output,'Content/Assets/c.bin',b);assert.deepEqual(await fs.readFile(path.join(output,'Content/Assets/c.bin')),b);assert.equal((await fs.readFile(path.join(previous,'Content/Assets/c.bin'))).toString(),'tampered');
 await writeBuildContent(output,'Content/Assets/d.bin',largeChanged);assert.deepEqual(await fs.readFile(path.join(output,'Content/Assets/d.bin')),largeChanged);assert.deepEqual(await fs.readFile(path.join(previous,'Content/Assets/d.bin')),a);
 await writeBuildContent(output,'metadata.json',Buffer.from('{}'));await assert.rejects(writeBuildContent(output,'Content/Assets/a.bin',a));
 assert.deepEqual(await fs.readFile(path.join(previous,'Content/Assets/a.bin')),a);
}finally{sharing.restore();}
console.log(JSON.stringify({status:'PASS',...sharing.stats,scope:'real filesystem immutable package sharing; altered content fallback; previous bytes preserved; exclusive output; no game player execution'}));
