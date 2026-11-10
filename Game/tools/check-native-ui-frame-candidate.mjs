import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {zstdDecompressSync} from 'node:zlib';
import {encodeNativeUIFrame} from './native-ui-frame.candidate.mjs';
const require=createRequire(path.resolve(import.meta.dirname,'../../../engineCreate/package.json')),{createCanvas,loadImage}=require('@napi-rs/canvas'),work=path.resolve(import.meta.dirname,'../Saved/native-ui-frame-candidate');await fs.mkdir(work,{recursive:true});const results=[];
for(const [name,width,height]of [['one',1,1],['alpha',513,257],['trial',1280,720],['wide',1920,1080]]){
 const c=createCanvas(width,height),ctx=c.getContext('2d');if(name==='trial'||name==='wide')ctx.drawImage(await loadImage(path.resolve(import.meta.dirname,'../Saved/native-all-tasks-1793541469758/session-1793541481899/task-t3-ns-a11.ui.png')),0,0,width,height);else{const d=ctx.createImageData(width,height);for(let i=0;i<d.data.length;i+=4){d.data[i]=(i>>1)%256;d.data[i+1]=(i>>5)%256;d.data[i+2]=(i>>9)%256;d.data[i+3]=(i>>7)%256;}ctx.putImageData(d,0,0);ctx.fillStyle='#ef835185';ctx.fillRect(0,0,13,21);}
 const png=(await c.encode('png')).toString('base64');let frame,ms=0;for(let i=0;i<5;i++){const start=performance.now();frame=await encodeNativeUIFrame(c);ms+=performance.now()-start;}assert.deepEqual(zstdDecompressSync(Buffer.from(frame.pixels,'base64')),c.data());await fs.writeFile(path.join(work,name+'.json'),JSON.stringify({...frame,png}));results.push({name,width,height,ms:ms/5,compressedBytes:Buffer.from(frame.pixels,'base64').length,exactPremultipliedBytes:true});
}
await fs.writeFile(path.join(work,'codec.json'),JSON.stringify({ok:true,results},null,2));console.log(JSON.stringify(results));
