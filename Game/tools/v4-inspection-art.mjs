import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {validGameJson} from '../../../engineCreate/prototype/game-json.js';
import {nativeWidgetPng} from './native-png-runtime.mjs';

// The same reviewed geometry/image adapter used by prepare_v4_runtime.py,
// selectively published without recompiling unchanged narrative routes.
export async function publishInspectionArtOnly({repo,root,write}){
 const registry=JSON.parse(await fs.readFile(path.join(repo,'art/inspection_v4/illustrations_20261104/selection.json'),'utf8'));
 const manifest=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/investigation_diagrams_v4/manifest.json'),'utf8'));
 const asset=v=>'Assets/Art/v4_story/'+createHash('sha256').update(v).digest('hex').slice(0,16)+path.extname(v);
 const rows=Object.entries(registry.entries),replacements=new Map(),assets=[],changed=[],tasks=[];
 for(const [key,row]of rows){
  assert.deepEqual(manifest.entries[key].source,row.source);assert.equal(manifest.entries[key].sha256,row.sha256);
  const bytes=await fs.readFile(path.join(repo,row.image));assert.equal(createHash('sha256').update(bytes).digest('hex'),row.sha256);
  const dest=asset(row.image);await write(dest,nativeWidgetPng(bytes));assets.push(dest);replacements.set(asset(row.replaces),dest);
 }
 const bind=v=>{
  if(typeof v==='string')return replacements.get(v)||v;
  if(Array.isArray(v))return v.map(bind);
  if(!v||typeof v!=='object')return v;
  const out=Object.fromEntries(Object.entries(v).map(([k,x])=>[k,bind(x)]));
  for(const [key,row]of rows)if(out.pictureProvenance?.entry===key){
   assert.deepEqual(Object.fromEntries(out.regions.map(r=>[r.id,r.correct])),Object.fromEntries(row.regions.map(r=>[r.id,r.correct])));
   const shapes=new Map(row.regions.map(r=>[r.id,r.polygon]));for(const region of out.regions)region.polygon=shapes.get(region.id);
   out.pictureProvenance.imageSha256=row.sha256;tasks.push(out.id);
  }
  return out;
 };
 for(const file of await fs.readdir(path.join(root,'Assets/Data/v4_story'),{recursive:true})){
  if(!file.endsWith('.json'))continue;const name='Assets/Data/v4_story/'+file.replaceAll('\\','/'),before=await fs.readFile(path.join(root,name),'utf8');
  if(![...replacements.keys(),...replacements.values()].some(ref=>before.includes(ref)))continue;
  const original=JSON.parse(before),next=bind(original);if(JSON.stringify(original)===JSON.stringify(next))continue;
  assert(validGameJson(next),name);await write(name,next);changed.push(name);
 }
 return {inspectionArtOnly:true,assets,changed,tasks:[...new Set(tasks)],answersChanged:false,dialogueChanged:false,nativeVisualAcceptance:false};
}
