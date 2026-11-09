// Approved strict profile originals stay intact; geometry accounts for padding.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
export async function applyScrumProfiles({repo,write,figures}){
 const bank=JSON.parse(await fs.readFile(path.join(repo,'art/v4_production/scrum_profile_20261104/selection.json'),'utf8'));
 const faces={};
 for(const [key,row] of Object.entries(bank.rows)){
  const bytes=await fs.readFile(path.join(repo,row.file));
  assert.equal(createHash('sha256').update(bytes).digest('hex'),row.sha256);
  assert.equal(bytes.readUInt32BE(16),row.size[0]);assert.equal(bytes.readUInt32BE(20),row.size[1]);
  const slug=key.split('_')[0],base=figures[slug];assert(base);
  const scale=base.height/(row.bbox[3]-row.bbox[1]);
  const texture=`Assets/Art/scrum_profiles/${key}.png`,face=`Assets/Art/scrum_profiles/${key}_face.svg`;
  await write(texture,bytes);
  // Native SVG viewport is a UI framing operation, not a derived bitmap.
  await write(face,`<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="${row.face.join(' ')}"><image width="${row.size[0]}" height="${row.size[1]}" href="data:image/png;base64,${bytes.toString('base64')}"/></svg>`);
  figures[key]={texture,back:texture,width:row.size[0]*scale,height:row.size[1]*scale,center:.1+(row.bbox[3]-row.size[1]/2)*scale};
  faces[key]=face;
 }
 return faces;
}
