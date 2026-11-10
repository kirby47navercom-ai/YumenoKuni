// Keep the approved standing pose; add a dedicated, transparent thinking cutin.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'..'),relative='ui/v4/debate_feedback/hero_lie_deduction.png',original='art/v4_production/cutins_20261104/mio_lie_original.png';
await fs.mkdir(path.dirname(path.join(root,original)),{recursive:true});await fs.copyFile(path.join(root,relative),path.join(root,original),fs.constants.COPYFILE_EXCL).catch(e=>{if(e.code!=='EEXIST')throw e;});
const source=await fs.readFile(path.join(root,original)),chunks=[source.subarray(0,8)],removed=[];let offset=8;
// The retained host detects SVG by searching the entire byte stream. C2PA's
// embedded SVG badge made this PNG enter its SVG-upscale path. Drop that
// metadata chunk only; copy IHDR/IDAT/alpha/color chunks and CRCs byte-for-byte.
while(offset<source.length){const length=source.readUInt32BE(offset),end=offset+length+12;assert(end<=source.length);const type=source.toString('ascii',offset+4,offset+8);if(type==='caBX')removed.push(type);else chunks.push(source.subarray(offset,end));offset=end;}
const bytes=Buffer.concat(chunks);assert.equal(offset,source.length);await fs.writeFile(path.join(root,relative),bytes);
assert.equal(bytes.toString('hex',0,8),'89504e470d0a1a0a');
const row={outcome:'lie-deduction',source:original,file:relative,width:bytes.readUInt32BE(16),height:bytes.readUInt32BE(20),source_sha256:createHash('sha256').update(source).digest('hex'),runtime_sha256:createHash('sha256').update(bytes).digest('hex'),removedMetadataChunks:removed,method:'Built-in edit of approved hero identity. Original PNG preserved. Only C2PA metadata chunk removed for retained host SVG misdetection; encoded pixel chunks untouched, no crop/resize/color/alpha editing',visualReview:{identity:true,handPose:true,clothing:true,backgroundAlpha:true,runtime:false}};
const file=path.join(root,'ui/v4/debate_feedback/hero_manifest.json'),manifest=JSON.parse(await fs.readFile(file,'utf8'));
manifest.rows=manifest.rows.filter(r=>r.outcome!=='lie-deduction');manifest.rows.push(row);await fs.writeFile(file,JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify({selected:relative,width:row.width,height:row.height,sha256:row.source_sha256,standingPosePreserved:true}));
