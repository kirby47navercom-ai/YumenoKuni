// Owned candidate only: preserve the browser fallback and exact texture bytes.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..'),owner=path.resolve(root,'../../engineCreate/prototype/native-scene-renderer.js'),source=await fs.readFile(owner,'utf8'),work=path.join(root,'Saved/native-base64-candidate-'+Date.now());await fs.mkdir(work,{recursive:true});
const before="export function rgbaBase64(bytes){let text='';for(let i=0;i<bytes.length;i+=32768)text+=String.fromCharCode(...bytes.subarray(i,i+32768));return btoa(text);}";
const after="export function rgbaBase64(bytes){if(typeof Buffer!=='undefined'&&ArrayBuffer.isView(bytes)&&bytes.BYTES_PER_ELEMENT===1)return Buffer.from(bytes.buffer,bytes.byteOffset,bytes.byteLength).toString('base64');let text='';for(let i=0;i<bytes.length;i+=32768)text+=String.fromCharCode(...bytes.subarray(i,i+32768));return btoa(text);}";
assert(source.includes(before));const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const evaluate=text=>Function(text.replace('export ','')+';return rgbaBase64;')(),baseline=evaluate(before),candidate=evaluate(after),fixtures=[];
for(const size of [0,1,2,3,31,32767,32768,32769,4*1024*1024]){
 const backing=Buffer.alloc(size+19);for(let i=0;i<backing.length;i++)backing[i]=(i*73+19)&255;
 const bytes=new Uint8Array(backing.buffer,backing.byteOffset+7,size);const start=performance.now(),old=baseline(bytes),oldMs=performance.now()-start,t=performance.now(),actual=candidate(bytes),newMs=performance.now()-t;
 assert.equal(actual,old);assert.equal(actual,Buffer.from(bytes).toString('base64'));
 fixtures.push({size,oldMs,newMs,sha256:sha(actual)});
}
// Native full-resolution texture: same data/budget, no downsample or truncation.
const large=Buffer.alloc(5016*5016*4,173),started=performance.now(),encoded=candidate(large);assert.deepEqual(Buffer.from(encoded,'base64'),large);const largeMs=performance.now()-started;
const file=path.join(work,'native-scene-renderer.candidate.js');await fs.writeFile(file,source.replace(before,after));
await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,owner,file,originalSHA256:sha(source),candidateSHA256:sha(await fs.readFile(file)),fixtures,largeBytes:large.length,largeEncodeAndRoundtripMs:largeMs,engineOriginalOrDistModified:false,scope:'Exact base64 equivalence including sliced views, empty/tail/chunk boundaries and4MiB payload; full5016-square RGBA roundtrip. Browser fallback retained. Owned performance candidate only; actual native rendering measured separately.'},null,2));console.log(JSON.stringify({ok:true,file,largeMs}));
