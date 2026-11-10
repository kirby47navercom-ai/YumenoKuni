// Crop transparent padding from approved, already locally4x-upscaled character deliveries.
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const require=createRequire(import.meta.url);let sharp;try{sharp=require('sharp');}catch{sharp=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'));}
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),out=path.join(root,'ui/v4/debate_feedback');
await fs.mkdir(out,{recursive:true});const rows=[];
for(const [kind,pose] of [['refute','T01'],['lie','T02'],['agree','T03']]){
 const source=`art/character_delivery_v4/cutins/mio_${pose}.webp`,file=`ui/v4/debate_feedback/hero_${kind}.webp`;
 const bytes=await fs.readFile(path.join(root,source));
 const trimmed=await sharp(bytes).trim({threshold:4}).png().toBuffer(),meta=await sharp(trimmed).metadata();
 const {data,info}=await sharp(trimmed).webp({lossless:true,effort:4}).toBuffer({resolveWithObject:true});
 await fs.writeFile(path.join(root,file),data);rows.push({outcome:kind,source,file,width:info.width,height:info.height,source_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),method:'transparent padding trimmed only; complete approved locally4x pose retained, including head and both hands; no redraw, flip or generation'});
}
for(const slug of ['mio','rin','ken','nana','taiga','ai','rei','sora','haruka','sho','koto','akari','riku','satsuki','yuu','kaede']){
 const source=`art/character_delivery_v4/cutins/${slug}_T03.webp`,file=`ui/v4/debate_feedback/partner_${slug}.webp`,bytes=await fs.readFile(path.join(root,source));
 const trimmed=await sharp(bytes).trim({threshold:4}).png().toBuffer(),m=await sharp(trimmed).metadata();
 const {width,height}=m;
 await sharp(trimmed).webp({lossless:true,effort:4}).toFile(path.join(root,file));
 await sharp(trimmed).negate({alpha:false}).webp({lossless:true,effort:4}).toFile(path.join(out,`negative_${slug}.webp`));
 rows.push({character:slug,source,file,width,height,source_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),method:'transparent padding trimmed only; complete approved4x agreement pose retained; actual target identity, no portrait substitution'});
}
await fs.writeFile(path.join(out,'hero_manifest.json'),JSON.stringify({rows},null,2)+'\n');console.log('3 own-character outcome cutins exported');
