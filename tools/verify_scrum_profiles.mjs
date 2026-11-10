import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const bank='art/v4_production/scrum_profile_20261104/',selection=JSON.parse(await fs.readFile(bank+'selection.json','utf8')),court=JSON.parse(await fs.readFile('Game/Assets/Data/court.json','utf8'));
const slugs=['mio','rei','rin','nana','ken','taiga','ai','sora','haruka','sho','koto','akari','riku','satsuki','yuu','kaede'];
assert.deepEqual(Object.keys(selection.rows).sort(),slugs.flatMap(s=>[s+'_SL',s+'_SR']).sort());
const pixelChunks=bytes=>{let at=8;const chunks=[];while(at<bytes.length){const end=at+bytes.readUInt32BE(at)+12;assert(end<=bytes.length);if(bytes.toString('ascii',at+4,at+8)!=='caBX')chunks.push(bytes.subarray(at,end));at=end;}assert.equal(at,bytes.length);return Buffer.concat(chunks);};
for(const [key,row]of Object.entries(selection.rows)){
 const source=await fs.readFile(row.original),runtime=await fs.readFile(row.file),published=await fs.readFile('Game/'+court.figures[key].texture);
 assert(pixelChunks(source).equals(pixelChunks(runtime)),'Encoded color/alpha chunks must stay unchanged '+key);assert(runtime.equals(published));assert.equal(createHash('sha256').update(runtime).digest('hex'),row.sha256);
 assert.deepEqual([runtime.readUInt32BE(16),runtime.readUInt32BE(20)],row.size);assert(row.face[0]>=0&&row.face[1]>=0&&row.face[0]+row.face[2]<=row.size[0]&&row.face[1]+row.face[3]<=row.size[1]);assert(row.bbox[3]>row.bbox[1]);assert(court.figures[key].height>0&&court.figures[key].width>0);assert.equal(court.scrumFaces[key],`Assets/Art/scrum_profiles/${key}_face.svg`);
}
console.log(JSON.stringify({ok:true,profiles:32,originalPixelChunksPreserved:true,courtAndFaceBindings:true,runtimeAllViewsAccepted:false}));
