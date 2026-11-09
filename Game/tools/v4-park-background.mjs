import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';

const directory = 'art/space_v4/park_levels_v1/background';
const cctvMesh = 'Assets/Art/park_levels/background/cctv-head.glb';

export async function readParkCctvHead(repo) {
 const source = JSON.parse(await fs.readFile(path.join(repo,directory,'cctv-head.json'),'utf8'));
 const bytes = await fs.readFile(path.join(repo,source.file));
 if (createHash('sha256').update(bytes).digest('hex') !== source.sha256) throw Error('Park CCTV head SHA');
 return {runtime:cctvMesh,bytes};
}

export async function readParkBackgrounds(repo) {
 const rows = JSON.parse(await fs.readFile(path.join(repo,directory,'manifest.json'),'utf8'));
 return new Map(await Promise.all(rows.map(async row => {
  const bytes = await fs.readFile(path.join(repo,row.file));
  if (createHash('sha256').update(bytes).digest('hex') !== row.sha256) throw Error('Park background SHA: '+row.id);
  return [row.id,{...row,bytes}];
 })));
}

export function applyParkBackground(scene, background) {
 const park = scene.objects.find(object => object.id === 'ParkGeometry');
 const volume = scene.objects.find(object => object.id === 'SceneAntialias')?.components.find(component => component.type === 'PostProcessVolume');
 if (!park || !volume) throw Error('Park mesh or FXAA volume missing in '+scene.sceneName);
 const backdrop = structuredClone(park);
 Object.assign(backdrop,{id:'ParkBackground',name:'외곽 철창과 감시 카메라',parent:park.id,position:[0,0,0]});
 const renderer = backdrop.components.find(component => component.type === 'MeshRenderer');
 renderer.id = 'ParkBackgroundMesh';
 Object.assign(renderer.properties,{mesh:background.runtime,castShadow:false});
 scene.objects = scene.objects.filter(object => object.id !== backdrop.id && !object.id.startsWith('ParkCctv'));
 scene.objects.push(backdrop);
 for (const [index,placement] of background.cameras.entries()) {
  const head = structuredClone(backdrop);
  Object.assign(head,{id:'ParkCctv'+index,name:'회전형 CCTV',parent:backdrop.id,
    position:placement.position,rotation:[0,placement.yaw,0]});
  const mesh = head.components.find(component => component.type === 'MeshRenderer');
  Object.assign(mesh,{id:head.id+'Mesh'});
  mesh.properties.mesh = cctvMesh;
  scene.objects.push(head);
 }
 Object.assign(volume.properties,{colorGradingEnabled:true,postExposure:.08,contrast:9,saturation:-12,
  lift:[.004,.006,.009],gain:[.98,1,1.02]});
}
