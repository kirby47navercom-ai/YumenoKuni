import {makeSceneComponent} from '../engineCreate/prototype/scene-components.js';
// HUD capsules stay in the HUD. The projectile uses closed letter meshes.
export function applyKotodamaFlight(widget){
 widget.nodes=widget.nodes.filter(n=>!n.id.startsWith('KotodamaFlight'));
 return widget;
}
export function applyKotodamaScene(scene,source=scene){
 scene.objects=scene.objects.filter(o=>!o.id.startsWith('KotodamaWord'));
 const template=source.objects.find(o=>o.id==='TrialGpu_MF0');
 if(!template)throw Error('Debate mesh template missing');
 for(let i=0;i<48;i++){const o=structuredClone(template);o.id=o.name='KotodamaWord'+i;o.parent='Camera';o.components=o.components.filter(c=>c.type==='MeshRenderer');if(!o.components.length)o.components.push(makeSceneComponent('MeshRenderer',{mesh:'',visible:false,castShadow:false,receiveShadow:false}));for(const c of o.components){c.id='kotodama-mesh-'+i;c.properties.visible=false;c.properties.contributeGI=false;}scene.objects.push(o);}
 return scene;
}
