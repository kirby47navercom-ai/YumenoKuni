// Register a directly inspected built-in output without changing encoded pixels.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..'),dir='art/v4_production/scrum_profile_20261104';
const specs={mio_SL:{size:[1024,1536],bbox:[333,19,667,1491],face:[330,72,280,280]},mio_SR:{size:[1024,1536],bbox:[346,10,671,1499],face:[360,72,280,280]},rei_SL:{size:[1024,1536],bbox:[366,45,666,1492],face:[380,42,260,260]},rei_SR:{size:[1024,1536],bbox:[342,30,662,1509],face:[365,25,270,270]}};
// Additional outputs enter only after direct visual review and read-only alpha
// measurements. Never auto-register an unreviewed imagegen result.
Object.assign(specs,await fs.readFile(path.join(root,dir,'reviewed-inputs.json'),'utf8').then(JSON.parse,e=>{if(e.code==='ENOENT')return {};throw e;}));
const rows={};
for(const [key,spec] of Object.entries(specs)){
 const original=`${dir}/${key}_original.png`,file=`${dir}/${key}.png`,source=await fs.readFile(path.join(root,original)),chunks=[source.subarray(0,8)];let at=8;const removed=[];
 assert.equal(source.toString('hex',0,8),'89504e470d0a1a0a');
 while(at<source.length){const end=at+source.readUInt32BE(at)+12;assert(end<=source.length);const type=source.toString('ascii',at+4,at+8);if(type==='caBX')removed.push(type);else chunks.push(source.subarray(at,end));at=end;}
 const runtime=Buffer.concat(chunks);await fs.writeFile(path.join(root,file),runtime);
 rows[key]={...spec,original,file,sha256:createHash('sha256').update(runtime).digest('hex'),sourceSha256:createHash('sha256').update(source).digest('hex'),removedMetadata:removed,review:{strictProfile:true,identity:true,hands:true,clothing:true,alpha:true,runtime:false},pixelOperation:'None; only caBX metadata removed. Original encoded color and alpha chunks unchanged.'};
}
await fs.writeFile(path.join(root,dir,'selection.json'),JSON.stringify({version:1,rows},null,2)+'\n');console.log(JSON.stringify({profiles:Object.keys(rows)}));
