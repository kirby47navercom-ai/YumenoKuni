import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {validScene} from '../../../engineCreate/prototype/model.js';
const repo=path.resolve(import.meta.dirname,'../..');
// Own scene: the real court and its sixteen moving podiums remain untouched.
export async function emitArmamentScene(court,write){
 const root={id:'SceneRoot',name:'이론무장 구간 자원',kind:'empty',position:[0,0,0],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[]};
 const keep=new Set(['Camera','CourtAmbient','CourtKey','CourtFill','SceneAntialias']);
 const rows=court.objects.filter(o=>keep.has(o.id)).map(o=>structuredClone(o));
 const camera=rows.find(o=>o.id==='Camera');assert(camera);camera.position=[0,3.3,10];camera.rotation=[0,0,0];camera.parent='SceneRoot';
 camera.components.find(c=>c.type==='Camera').properties.priority=10;
 const model=structuredClone(court.objects.find(o=>o.id==='CourtGeometry'));assert(model);
 model.id='ArmamentHall';model.name='이론무장 회랑';model.position=[0,0,0];model.rotation=[0,0,0];model.scale=[1.5,1,3];model.parent='SceneRoot';
 const mesh=model.components.find(c=>c.type==='MeshRenderer');mesh.properties.mesh='Assets/Art/armament_v4/hall.glb';mesh.properties.castShadow=false;
 await write(mesh.properties.mesh,await fs.readFile(path.join(repo,'art/space_v4/armament_hall_v1/armament_hall.glb')));
 rows.push(model);
 const seat=court.objects.find(o=>o.id==='Seat0');assert(seat);
 for(const id of ['ArmamentBoss','ArmamentBossPrevious']){
  const actor=structuredClone(seat);actor.id=id;actor.name=id;actor.position=[-2,4,0];actor.rotation=[0,0,0];actor.scale=[1,1,1];actor.parent='SceneRoot';
  const sprite=actor.components.find(c=>c.type==='SpriteRenderer');Object.assign(sprite.properties,{texture:'',sprite:'',visible:false,billboard:true,width:5.33,height:8,castShadow:false,receiveShadow:false,blendMode:'translucent'});rows.push(actor);
 }
 const bank=JSON.parse(await fs.readFile(path.join(repo,'art/v4_production/armament_20261103/runtime-bank.json'),'utf8'));
 await write('Assets/Art/armament_v4/player_mio.webp',await fs.readFile(path.join(repo,'art/character_delivery_v4/portraits/mio.webp')));
 for(const spec of Object.values(bank.figures))for(const state of spec.states)await write(state.texture,await fs.readFile(path.join(repo,state.source)));
 // Keep original-file provenance in the authoring bank. The build follows
 // every path in runtime JSON, so repository/imagegen source paths must not
 // become game resource dependencies.
 const runtimeBank=structuredClone(bank);
 const defeat=JSON.parse(await fs.readFile(path.join(repo,'art/v4_production/armament_defeat_20261106/manifest.json'),'utf8'));
 for(const [name,figure]of Object.entries(runtimeBank.figures)){
  const pose=defeat.figures[name];assert(pose,'Missing reviewed defeat pose '+name);
  await write(pose.texture,await fs.readFile(path.join(repo,pose.source)));
  figure.defeat={texture:pose.texture,aspect:pose.aspect};
 }
 for(const spec of Object.values(runtimeBank.figures))for(const state of spec.states){delete state.source;delete state.generatedSource;}
 await write('Assets/Data/armament_figures_v4.json',runtimeBank);
 const widgets=['main','flow','v4story','stage','trialvitalsv4','intro','debatefx','modal','loadingv4'];
 const scene={...structuredClone(court),sceneName:'CourtArmament',objects:[root,{...structuredClone(root),id:'CourtArmamentScene'},...rows,...widgets.map(id=>({...structuredClone(root),id:'UI_'+id,name:id+' UI'}))]};
 for(const actor of scene.objects)if(actor.parent)assert(scene.objects.some(p=>p.id===actor.parent));
 assert(!scene.objects.some(o=>/^Podium|^Seat\d/.test(o.id)));
 assert(validScene(scene),'The emitted armament scene must satisfy the actual scene schema');
 await write('Assets/Scenes/ArmamentHud.hbscene.json',scene);return {objects:scene.objects.length,armoredOpponents:Object.keys(bank.figures).length,scene:'ArmamentHud',normalCourtChanged:false};
}
