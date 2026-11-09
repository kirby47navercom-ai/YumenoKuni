// Keep each current-task statement on a stable rig; switching a lane only changes visibility.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const game=path.resolve(import.meta.dirname,'..');
export async function emitPanicCacheScene({output,write}){
 const tasks=Object.values(JSON.parse(await fs.readFile(path.join(game,'../data/v4_story/native_tasks.json'),'utf8')).tasks).filter(t=>t.debate?.kind==='panic');
 const capacity=Math.max(...tasks.map(t=>t.debate.lines.length));assert(capacity>0&&capacity<=16);
 const file='Assets/Scenes/PanicHud.hbscene.json',scene=JSON.parse(await fs.readFile(path.join(output,file),'utf8')),layout=JSON.parse(await fs.readFile(path.join(output,'Assets/Data/gpu_panic_layout.json'),'utf8'));
 const original=scene.objects.find(o=>/^TrialBatch_Panic(?:0|Slot0)$/.test(o.id));assert(original?.components.some(c=>c.type==='SpriteSkin'));
 scene.objects=scene.objects.filter(o=>!o.id.startsWith('TrialBatch_Panic'));
 for(let i=0;i<capacity;i++){
  const actor=structuredClone(original);actor.id='TrialBatch_PanicSlot'+i;actor.name='Panic statement slot '+i;actor.parent='Camera';
  for(const c of actor.components){const h=createHash('sha256').update(actor.id+':'+c.type).digest('hex');c.id=[h.slice(0,8),h.slice(8,12),h.slice(12,16),h.slice(16,20),h.slice(20,32)].join('-');if(c.type==='SpriteRenderer')Object.assign(c.properties,{sprite:'',texture:'',visible:false,sortingOrder:850});if(c.type==='SpriteSkin')c.properties.rig='';}
  scene.objects.push(actor);
 }
 layout.cacheSlots=capacity;assert.equal(scene.objects.filter(o=>/^Podium\d+$/.test(o.id)).length,16);
 await write(file,scene);await write('Assets/Data/gpu_panic_layout.json',layout);
 return {cacheSlots:capacity,loadedStatements:'current task only',independentPodiums:16};
}
