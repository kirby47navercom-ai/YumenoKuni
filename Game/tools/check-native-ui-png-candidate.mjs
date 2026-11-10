import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {encodeNativeUIPNG} from './native-ui-png.candidate.mjs';
const require=createRequire(path.resolve(import.meta.dirname,'../../../engineCreate/package.json'));
const {createCanvas,loadImage}=require('@napi-rs/canvas');
const out=path.resolve(import.meta.dirname,'../Saved/native-ui-png-candidate');await fs.mkdir(out,{recursive:true});
const rows=[];
for(const [name,w,h] of [['alpha',513,257],['trial',1280,720],['4k',3840,2160]]){
 const canvas=createCanvas(w,h),ctx=canvas.getContext('2d');
 if(name==='trial')ctx.drawImage(await loadImage(path.resolve(import.meta.dirname,'../Saved/native-all-tasks-1793541469758/session-1793541481899/task-t6-rs-01.ui.png')),0,0,w,h);
 else {const data=ctx.createImageData(w,h);for(let i=0;i<data.data.length;i+=4){data.data[i]=i%251;data.data[i+1]=(i>>5)%256;data.data[i+2]=(i>>9)%256;data.data[i+3]=(i>>7)%256;}ctx.putImageData(data,0,0);ctx.fillStyle='#ae82bd83';ctx.rotate(.2);ctx.fillRect(42,33,99,77);ctx.font='32px sans-serif';ctx.fillText('Native UI RGBA',50,100);}
 let oldMS=0,newMS=0,oldPNG,newPNG;for(let i=0;i<5;i++){let start=performance.now();oldPNG=await canvas.encode('png');oldMS+=performance.now()-start;start=performance.now();newPNG=await encodeNativeUIPNG(canvas);newMS+=performance.now()-start;}
 const decode=async bytes=>{const target=createCanvas(w,h),c=target.getContext('2d');c.drawImage(await loadImage(bytes),0,0);return c.getImageData(0,0,w,h).data;};
 assert.deepEqual(await decode(newPNG),await decode(oldPNG),name+' exact decoded RGBA');
 await fs.writeFile(path.join(out,name+'-old.png'),oldPNG);await fs.writeFile(path.join(out,name+'-new.png'),newPNG);
 rows.push({name,w,h,exactDecodedRGBA:true,oldMS:oldMS/5,newMS:newMS/5,oldBytes:oldPNG.length,newBytes:newPNG.length});
}
await fs.writeFile(path.join(out,'report.json'),JSON.stringify({ok:true,rows,scope:'Lossless decoded RGBA equivalence and local encode microbenchmark; actual native rendering is checked separately.'},null,2));console.log(JSON.stringify(rows));
