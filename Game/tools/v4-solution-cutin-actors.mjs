import fs from 'node:fs/promises';import path from 'node:path';
// Reuse the existing camera-space sprite path. Textures are assigned only when
// a correct-answer cinematic starts, and the scene owns the sprite lifetimes.
export async function emitSolutionCutinActors({game,write}){
 const court=JSON.parse(await fs.readFile(path.join(game,'Assets/Scenes/Court.hbscene.json'),'utf8'));
 const template=court.objects.find(o=>o.id==='TrialGpu_CourtDim');if(!template)throw Error('Missing camera-space sprite template');
 for(const name of ['Court','AnagramHud']){
  const file='Assets/Scenes/'+name+'.hbscene.json',scene=JSON.parse(await fs.readFile(path.join(game,file),'utf8'));
  scene.objects=scene.objects.filter(o=>!o.id.startsWith('SolutionGpu'));
  for(let i=-1;i<20;i++){
   const o=structuredClone(template);o.id='SolutionGpu'+(i<0?'Back':i);o.name='solution/'+(i<0?'back':i);o.parent='Camera';
   Object.assign(o.components.find(c=>c.type==='SpriteRenderer').properties,{texture:'',sprite:'',visible:false,sortingOrder:i<0?4000:4100+i,shading:'unlit',toneMapping:'display',blendMode:'translucent'});
   scene.objects.push(o);
  }
  await write(file,scene);
 }
}
