import assert from 'node:assert/strict';
export async function assertNoiseWaves(ui,stats,asset,cameraLocal){
 const noise=ui.noiseSnapshot;
 const actors=ui.world.filter(o=>/^TrialBatch_Noise[012]$/.test(o.id));
 if(ui.scene==='Assets/Scenes/Title.hbscene.json'){assert.equal(actors.length,0);return 0;}
 assert.equal(actors.length,3,'Only three shared-wave rows, preserving individual character/podium actors');
 assert(noise?.ready,'Current debate must own its actual noise bank');assert(!noise.error,noise.error);
 assert(!ui.world.some(o=>/^TrialGpu_N[FB]\d+$/.test(o.id)&&o.sprite?.visible),'Banked noise must not draw duplicate individual letters');
 const layout=await asset('Assets/Data/gpu_noise_layout.json');let samples=0;
 for(const [slot,index,mx,my]of noise.modelPoints||[]){
  const o=actors.find(o=>o.id==='TrialBatch_Noise'+slot&&o.sprite?.visible);if(!o)continue;
  const row=noise.rows.find(r=>r[0]===slot),spec=layout.bank.find(r=>r.key===row?.[1]);assert(spec);
  assert.equal(o.sprite.sprite,spec.sprite);assert.equal(o.skin.rig,spec.rig);
  const glyph=spec.glyphs.find(g=>g.index===index);if(!glyph)continue;
  const rig=await asset(spec.rig),poses=new Map(o.skinRuntime.bones.map(b=>[b.id,b]));let x=0,y=0;
  for(const v of rig.vertices.slice(glyph.vertex,glyph.vertex+4)){
   let dx=0,dy=0;for(const w of v.weights){const b=poses.get(w.bone);assert(b);assert.deepEqual(b.scale,[1,1]);assert.equal(b.rotation,0);dx+=b.position[0]*w.weight;dy+=b.position[1]*w.weight;}
   x+=(v.position[0]+dx)/4;y+=(v.position[1]+dy)/4;
  }
  x-=glyph.cropCenter[0]/layout.units;y-=glyph.cropCenter[1]/layout.units;
  const pose=cameraLocal(o,ui),depth=-pose.position[2],unit=2*depth*Math.tan(43.6*Math.PI/360)/ui.height,fit=Math.min(ui.width/1280,ui.height/720),px=pose.position[0]+x*pose.scale[0],py=pose.position[1]+y*pose.scale[1],point=[(px/unit+ui.width/2)/fit,(ui.height/2-py/unit)/fit];
  assert(Math.hypot(point[0]-mx,point[1]-my)<1.1,'Actual weighted noise wave must preserve the original glyph model within1.1logical pixels');
  if(ui.trialSnapshot?.speakerSeat>=0){const cam=ui.world.find(o=>o.id==='Camera'),speaker=ui.world.find(o=>o.id==='Seat'+ui.trialSnapshot.speakerSeat),[rx,ry]=cam.rotation.map(v=>v*Math.PI/180),d=speaker.position.map((v,i)=>v-cam.position[i]),plane=-d[0]*Math.sin(ry)+d[1]*Math.sin(rx)*Math.cos(ry)-d[2]*Math.cos(rx)*Math.cos(ry);assert(depth>plane-.001,'Ordinary noise must remain behind the actual speaker plane');}
  samples++;
 }
 return samples;
}
