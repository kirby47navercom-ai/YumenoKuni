// Source-authored local fixtures belong to their park scene, not the engine.
export function applyParkArchitectureLight(scene,district,architecture){
 scene.objects=scene.objects.filter(o=>!o.id.startsWith('ArchitectureStageKey'));
 for(const asset of Object.values(architecture?.assets||{})){
  if(asset.district!==district||!asset.sourceReviewed)continue;
  for(const rig of asset.presentationLights||[]){
   const [x,y,z]=rig.position,[tx,ty,tz]=rig.target,dx=tx-x,dy=ty-y,dz=tz-z;
   if(![x,y,z,tx,ty,tz,rig.intensity,rig.radius,rig.angle].every(Number.isFinite))throw Error('Invalid source-authored park light');
   const pitch=Math.atan2(dy,Math.hypot(dx,dz))*180/Math.PI,yaw=Math.atan2(-dx,-dz)*180/Math.PI;
   scene.objects.push({id:'Architecture'+rig.id,name:'무대 작업 조명',kind:'spotLight',parent:'SceneRoot',position:[300+x,y,z],rotation:[pitch,yaw,0],scale:[1,1,1],visible:true,components:[{id:'Architecture'+rig.id+'Component',name:'SpotLight',type:'SpotLight',properties:{enabled:true,color:rig.color,intensity:rig.intensity,radius:rig.radius,angle:rig.angle,penumbra:rig.penumbra,castShadow:false}}]});
  }
 }
 return scene;
}
