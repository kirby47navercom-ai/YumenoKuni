import {emitLoadingSourceUI} from './v4-loading-source-ui.mjs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {emitParkScenes} from './v4-park-levels.mjs';
// One authored object definition feeds both editor scenes and runtime instances.
import assert from 'node:assert/strict';
import {applyExplorationMaterialLight} from './v4-exploration-material-light.mjs';
import {createWidgetAsset,createWidgetNode} from '../engineCreate/prototype/ui-assets.js';
import {emitCulpritWorldOrbit} from './v4-culprit-orbit.mjs';
import {emitArmamentScene} from './v4-armament-scene.mjs';
export async function emitRuntimeScenes(scene,write){
 const camera=scene.objects.find(o=>o.id==='Camera');assert(camera);
 const explore=o=>/^(Explore|Outdoor|Exterior)/.test(o.id);
 const persistent=o=>o.id==='Driver'||o.id==='IntroOwner'||o.id.startsWith('UI_');
 const court=scene.objects.filter(o=>!persistent(o)&&!explore(o));
 const lights=court.filter(o=>/^Court(?:Ambient|Key|Fill)$/.test(o.id));
 const exploration=[structuredClone(camera),...structuredClone(lights),...scene.objects.filter(o=>explore(o)||o.id==='SceneAntialias')];
 const root=()=>({id:'SceneRoot',name:'구간 자원',kind:'empty',position:[0,0,0],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[]});
 for(const [name,objects]of [['Court',court],['Explore',exploration]]){
  const rows=structuredClone(objects);if(name==='Explore')for(const o of rows)if(o.id==='OutdoorSkyDome'||o.id.startsWith('Exterior')){const mesh=o.components?.find(c=>c.type==='MeshRenderer');if(mesh)mesh.properties.mesh='';}
  for(const o of rows){if(o.id==='Camera')o.components.find(c=>c.type==='Camera').properties.priority=10;if(!o.parent)o.parent='SceneRoot';}
  const widgets=name==='Court'?['main','flow','v4story','stage','trialvitalsv4','minev4','vote','intro','debatefx','panes','panicv4','comicv4','scrumv4','anagramv4','modal','loadingv4']:['main','flow','v4story','explore','modal','loadingv4'];
  const prefab={objects:[root(),{...root(),id:name+'Scene'},...rows,...widgets.map(i=>({...root(),id:'UI_'+i,name:i+' UI'}))]};
  const output={...structuredClone(scene),sceneName:name,objects:prefab.objects};
  if(name==='Court')await emitCulpritWorldOrbit(output,write);
  await write('Assets/Scenes/'+name+'.hbscene.json',name==='Explore'?applyExplorationMaterialLight(output):output);
  if(name==='Court')await emitArmamentScene(output,write);
  else await emitParkScenes({repo:path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),explore:applyExplorationMaterialLight(output),write});
 }
 const bootCamera=structuredClone(camera);bootCamera.id='BootCamera';bootCamera.name='타이틀 카메라';bootCamera.components.find(c=>c.type==='Camera').properties.priority=-10;
 const boot={...scene,sceneName:'Title',objects:[bootCamera,{...root(),id:'TitleScene'},...['titleshellv4','titlemenuv4','modal','loadingv4'].map(i=>({...root(),id:'UI_'+i,name:i+' UI'}))]};

 assert(!boot.objects.some(o=>o.components?.some(c=>['MeshRenderer','SpriteRenderer'].includes(c.type))));
 await write('Assets/Scenes/Title.hbscene.json',boot);
 await write('Assets/Scenes/Main.hbscene.json',boot);
 await emitLoadingSourceUI({write});
 return {startupObjects:boot.objects.length,courtObjects:court.length,exploreObjects:exploration.length};
}
