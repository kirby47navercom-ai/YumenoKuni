import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {validGameJson} from '../../../engineCreate/prototype/game-json.js';
export async function emitMineObjects({repo,write}){
 const bank=path.join(repo,'art/v4_production/mine_objects_20261104');
 const entries=JSON.parse(await fs.readFile(path.join(bank,'banks.json'),'utf8'));
 const banks=[];
 for(const entry of entries){
 const selection=JSON.parse(await fs.readFile(path.join(bank,entry.selection),'utf8'));
 for(const ref of selection.sourceStatements||[]){const source=(await fs.readFile(path.join(repo,'docs/design/rewrite_v4',ref.file),'utf8')).replace(/^\uFEFF/,'').replace(/\r\n/g,'\n');assert.equal(createHash('sha256').update(source).digest('hex'),ref.sha256);assert(source.split('\n')[ref.line-1].includes(ref.quote));}
 const masks=JSON.parse(await fs.readFile(path.join(bank,entry.mask),'utf8'));assert(validGameJson(masks));
 // The installed pack validator reserves root `objects` for scene arrays.
 // This bank is a keyed pixel-mask dictionary, so publish an unambiguous name.
 const runtimeMasks={masks:masks.objects};assert(validGameJson(runtimeMasks));await write(entry.target,runtimeMasks);
 const objects=[];
 for(const row of selection.objects){
  const bytes=await fs.readFile(path.join(repo,row.runtime));assert.equal(createHash('sha256').update(bytes).digest('hex'),row.runtimeSHA256);await write(row.texture,bytes);
  const {id,regionId,texture,maskKey,maskAsset,rect,rectByWidth,rotation,cellsByWidth,sizeCells}=row;assert(Number.isFinite(sizeCells)&&sizeCells>0&&sizeCells<20);assert.equal(masks.objects[maskKey].rotations.length,8);
  const hintLocal='Assets/Art/ui/mine-objects/'+id+'_local_hint.svg';const mask=masks.objects[maskKey];
  await write(hintLocal,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${mask.width} ${mask.height}" preserveAspectRatio="none"><defs><filter id="edge" x="-5%" y="-5%" width="110%" height="110%"><feComponentTransfer in="SourceAlpha" result="a"><feFuncA type="discrete" tableValues="0 1"/></feComponentTransfer><feMorphology in="a" operator="dilate" radius="4" result="b"/><feComposite in="b" in2="a" operator="out" result="c"/><feFlood flood-color="#fff4bd"/><feComposite in2="c" operator="in"/></filter></defs><image href="data:${row.runtime.endsWith('.svg')?'image/svg+xml':'image/png'};base64,${bytes.toString('base64')}" width="${mask.width}" height="${mask.height}" filter="url(#edge)"/></svg>`);
  objects.push({id,regionId,texture,maskKey,maskAsset,rect,rectByWidth,rotation,cellsByWidth,sizeCells,hintLocal,hintOutline:hintLocal});
 }
 banks.push({taskId:selection.taskId,objects,mergeCorrectRegions:selection.mergeCorrectRegions||null,comparisonLabel:selection.comparisonLabel||null});
 }
 return banks;
}
export function bindMineObjects(task,bank){
 assert.equal(task.stage.kind,'mindmine');
 if(bank.mergeCorrectRegions){
  const aliases=bank.mergeCorrectRegions,canonical=task.stage.answerRegionId;
  assert(aliases.includes(canonical)&&bank.objects.some(o=>o.regionId===canonical));
  if(task.stage.mineCompositeRegionAliases)assert.deepEqual(task.stage.mineCompositeRegionAliases,aliases);
  else{
   // Several source contours described the same one comparison unit. They
   // must not become separate independently sufficient partial answers.
   assert.deepEqual(task.stage.regions.filter(r=>r.correct).map(r=>r.id).sort(),[...aliases].sort());
   task.stage.mineCompositeRegionAliases=[...aliases];
  }
  task.stage.regions=task.stage.regions.filter(r=>!aliases.includes(r.id)||r.id===canonical);
  if(bank.comparisonLabel)task.stage.regions.find(r=>r.id===canonical).label=bank.comparisonLabel;
 }
 assert.equal(task.stage.regions.length,bank.objects.length);
 for(const region of task.stage.regions){const object=bank.objects.find(o=>o.regionId===region.id);assert(object,'Object must identify an existing authored answer/distractor');region.hintOutline=object.hintOutline;}
 task.stage.mineObjects=bank.objects;return task;
}
export async function publishMineObjectsOnly({root,repo,write}){
 const banks=await emitMineObjects({repo,write}),changed=[],found=new Set();
 for(let i=0;i<32;i++){
  const file='Assets/Data/v4_story/native_tasks/pack_'+i+'.json',pack=JSON.parse(await fs.readFile(path.join(root,file),'utf8'));
  let dirty=false;for(const bank of banks)for(const bucket of Object.values(pack.buckets))if(bucket.tasks[bank.taskId]){assert(!found.has(bank.taskId));found.add(bank.taskId);bindMineObjects(bucket.tasks[bank.taskId],bank);dirty=true;}if(dirty){assert(validGameJson(pack));await write(file,pack);changed.push(file);}
 }
 assert.equal(found.size,banks.length,'Every reviewed bank must match an existing authored task');return {tasks:banks.map(b=>({taskId:b.taskId,objects:b.objects.length})),changed,answersChanged:false};
}
