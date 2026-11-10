// Lossless runtime sizes from the retained5016px color masters; never grayscale these files.
import fs from 'node:fs/promises';import path from 'node:path';import os from 'node:os';import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);let sharp;try{sharp=require('sharp');}catch{sharp=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'));}
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),out='art/trial3d/id_portraits_color_v1/runtime';await fs.mkdir(path.join(root,out),{recursive:true});
const rows=[];
for(const slug of 'mio rin ken nana taiga ai rei sora haruka sho koto akari riku satsuki yuu kaede'.split(' ')){
 const source=`art/hd_v4/id_portraits_color_v1/${slug}.webp`,bytes=await fs.readFile(path.join(root,source));
 for(const [suffix,size] of [['',1536],['_thumb',256]]){
  const file=`${out}/${slug}${suffix}.webp`;await sharp(bytes).resize(size,size,{fit:'cover',kernel:'lanczos3'}).webp({lossless:true,effort:4}).toFile(path.join(root,file));
  rows.push({character:slug,source,file,size:[size,size],color:true,source_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),method:'color-preserving Lanczos3 runtime export from retained local4x master; lossless WebP;256px avatars avoid decoding16 giant masters for tiny icons'});
 }
}
await fs.writeFile(path.join(root,'art/trial3d/id_portraits_color_v1/runtime_manifest.json'),JSON.stringify({rows},null,2)+'\n');console.log('Student ID:16 color1536px photos +16 tiny avatars;5016px originals retained');
