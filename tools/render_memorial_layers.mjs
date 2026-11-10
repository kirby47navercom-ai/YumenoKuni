// Deterministic raster export of the editable SVG's photo/frame layers.
// Explicit neutral photo conversion and alpha compositing, without re-encoding large inline SVGs.
import fs from 'node:fs/promises';


import {createRequire} from 'node:module';
const require=createRequire(new URL('../Game/package.json',import.meta.url));
const sharp=require('sharp');
const [photo,frame,out]=process.argv.slice(2),size=2048,s=size/1254;
const image=await sharp(photo).resize(Math.round(485*s),Math.round(660*s),{fit:'cover',position:'top'}).greyscale().png().toBuffer();
const border=await sharp(frame).resize(size,size).png().toBuffer();
await sharp({create:{width:size,height:size,channels:4,background:{r:0,g:0,b:0,alpha:0}}})
 .composite([{input:image,left:Math.round(420*s),top:Math.round(302*s)},{input:border,left:0,top:0}])
 .webp({lossless:true,effort:4}).toFile(out);
const info=await fs.stat(out);if(info.size<100000)throw Error('Missing memorial layers');
