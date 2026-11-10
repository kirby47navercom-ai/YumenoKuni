// Technical SVG layer rendering using the already bundled workspace Sharp.
import fs from 'node:fs/promises';
import path from 'node:path';

import {createRequire} from 'node:module';
const require=createRequire(new URL('../Game/package.json',import.meta.url));
const sharp=require('sharp');
const source=path.resolve(process.argv[2]);let svg=await fs.readFile(source,'utf8');
for(const match of [...svg.matchAll(/xlink:href="([^"]+)"/g)]){
 const file=path.resolve(path.dirname(source),match[1]);
 // librsvg image layers require PNG/JPEG, even though Sharp itself reads WebP.
 const bytes=await sharp(file).png().toBuffer();
 svg=svg.replace(match[0],`xlink:href="data:image/png;base64,${bytes.toString('base64')}"`);
}
await sharp(Buffer.from(svg),{unlimited:true}).webp({lossless:true,effort:4}).toFile(source.replace(/\.svg$/,'.webp'));
