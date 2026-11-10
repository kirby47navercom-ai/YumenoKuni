// Restore reviewed Nonstop data without reverting another mode's newer work.
import fs from'node:fs/promises';import path from'node:path';import assert from'node:assert/strict';import{pathToFileURL}from'node:url';
export async function mergeNonstopCook({game,work,archive,overlay}){
 const own=JSON.parse(await fs.readFile(path.join(work,'full-build-result.json'),'utf8')),m=JSON.parse(await fs.readFile(path.join(own.output,'game.hbpack.json'),'utf8')),{openGameResources}=await import(pathToFileURL(path.join(own.output,'tools/game-resource-archive.mjs'))),a=await openGameResources(path.join(own.output,m.contentArchive.path));
 const json=async(ar,n)=>JSON.parse(await ar.read(n)),write=async(n,d)=>overlay(n,Buffer.from(JSON.stringify(d))),ids=new Set(),lineIds=new Set();let noiseRows=0;
 try{
  for(const name of a.entries.keys())if(/^Assets\/Data\/v4_story\/native_tasks\/pack_\d+\.json$/.test(name)){
   const from=await json(a,name),to=await json(archive,name);let changed=false;
   for(const[bucket,value]of Object.entries(from.buckets))for(const[id,task]of Object.entries(value.tasks||{}))if(task.stage.kind==='nonstop'){
    ids.add(id);for(const l of task.debate.lines)if(l.kind!=='noise')lineIds.add(l.id);
    to.buckets[bucket]??={tasks:{}};to.buckets[bucket].tasks??={};if(JSON.stringify(to.buckets[bucket].tasks[id])!==JSON.stringify(task)){to.buckets[bucket].tasks[id]=task;changed=true;}
   }
   if(changed)await write(name,to);
  }
  assert.equal(ids.size,71);
  const file='Assets/Data/v4_story/trial_direction.json',from=await json(a,file),to=await json(archive,file);
  for(const id of ids){for(const l of from.extra?.[id]||[])lineIds.add(l.id);for(const key of ['noise','extra','nonstopAmmo','nonstopWrongCards','nonstopFeedback'])if(from[key]?.[id]!==undefined){to[key]??={};to[key][id]=from[key][id];}noiseRows+=(to.noise?.[id]||[]).length;}
  for(const id of lineIds)if(from.debate?.[id])to.debate[id]=from.debate[id];await write(file,to);assert.equal(to.noise['T3-NS-A11'].length,11);
  for(const[name,row]of a.entries)if(/^Assets\/Art\/ui\/(gpu_trial\/g_|gpu_noise\/)/.test(name)&&archive.entries.get(name)?.sha256!==row.sha256)await overlay(name,await a.read(name));
  const layout=await json(archive,'Assets/Data/gpu_trial_layout.json'),old=await json(a,'Assets/Data/gpu_trial_layout.json');
  const styles=new Map(layout.styles.map(r=>[r.font+'|'+r.size,r]));for(const r of old.styles){const key=r.font+'|'+r.size,prior=styles.get(key);styles.set(key,{...prior,...r,characters:[...new Set((prior?.characters||'')+r.characters)].join('')});}layout.styles=[...styles.values()];
  // Reintegrating an already integrated publication must be idempotent. A glyph
  // is identified by its complete row, including any page/crop metadata.
  layout.glyphs=[...new Map([...layout.glyphs,...old.glyphs].map(r=>[JSON.stringify(r),r])).values()];const batches=new Map(layout.batches.map(r=>[r.key,r]));for(const r of old.batches)batches.set(r.key,r);layout.batches=[...batches.values()];
  await write('Assets/Data/gpu_trial_layout.json',layout);await write('Assets/Data/gpu_noise_layout.json',await json(a,'Assets/Data/gpu_noise_layout.json'));
  await fs.writeFile(path.join(work,'nonstop-cook-integration.json'),JSON.stringify({source:own.id,base:JSON.parse(await fs.readFile(path.join(work,'integration.json'),'utf8')).published,meetings:ids.size,lineIds:lineIds.size,noiseRows,restoredT3Rows:11,preservedOtherModes:true},null,2));return layout;
 }finally{await a.close();}
}
