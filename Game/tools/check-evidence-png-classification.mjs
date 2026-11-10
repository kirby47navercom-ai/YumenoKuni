import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {nativeWidgetPng} from './native-png-runtime.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root);
const review=JSON.parse(await fs.readFile(path.join(repo,'art/v4_production/death_posture_20261103/review.json'),'utf8'));
const {nativeWidgetImage,NativeSVGImage}=await import(pathToFileURL(path.join(root,'Saved/native-panic-views-1793690486425/package/tools/native-webp-animation.mjs')));
const chunks=bytes=>{const out=[];for(let at=8;at<bytes.length;){const end=at+bytes.readUInt32BE(at)+12,kind=bytes.toString('ascii',at+4,at+8);if(kind!=='caBX')out.push(bytes.subarray(at,end));at=end;}return out;};
const cases=[];
for(const row of review.rows){
 const raw=await fs.readFile(path.join(repo,row.delivery)),runtime=nativeWidgetPng(raw);
 assert.deepEqual(chunks(raw),chunks(runtime),'All pixel/color/alpha chunks stay byte-identical');
 assert(nativeWidgetPng(runtime).equals(runtime),'Metadata adapter is idempotent');
 const relative='Assets/Art/v4_story/'+createHash('sha256').update(row.delivery).digest('hex').slice(0,16)+'.png';
 assert((await fs.readFile(path.join(root,relative))).equals(runtime),'Published bytes use the canonical compatibility adapter');
 const before=await nativeWidgetImage(raw),after=await nativeWidgetImage(runtime);
 assert(before instanceof NativeSVGImage);assert(!(after instanceof NativeSVGImage));before.dispose();after.dispose?.();
 cases.push({id:row.logical,originalSha256:createHash('sha256').update(raw).digest('hex'),runtimeSha256:createHash('sha256').update(runtime).digest('hex'),allNonCaBXChunksUnchanged:true,originalMisclassified:true,runtimeStaticImage:true});
}
assert.throws(()=>nativeWidgetPng(Buffer.from('not a PNG')));
await fs.writeFile(path.join(root,'Saved/evidence-art-png-classification-20261104.json'),JSON.stringify({ok:true,cases,originalFilesChanged:false,engineModified:false,scope:'Actual retained native loader, PNG metadata-only publication and idempotence. No medical inference or gameplay result claim.'},null,2));
console.log(JSON.stringify({ok:true,cases:cases.length,pixelsUnchanged:true,engineModified:false}));
