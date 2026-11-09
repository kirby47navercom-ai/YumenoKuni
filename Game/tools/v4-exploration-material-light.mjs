// A single shadowed key plus inexpensive sky/fill. Shared by scoped and full generation.
import {readFileSync,existsSync} from 'node:fs';
const newSky=new URL('../../art/environment_v5/celestial-alignment.json',import.meta.url),regraded=existsSync(newSky);
const celestial=JSON.parse(readFileSync(regraded?newSky:new URL('../../art/environment_v4/celestial-alignment.json',import.meta.url),'utf8'));
export function applyExplorationMaterialLight(scene){
 for(const o of scene.objects)for(const c of o.components||[]){
  const p=c.properties;
  // The playable area's bounds are not the visible world's edge. Preserve
  // layered park scenery beyond the former 200m clipping plane.
  if(c.type==='Camera'&&o.id==='Camera')p.far=900;
  if(c.type==='DirectionalLight'&&(/^Outdoor\d+_sun$/.test(o.id)||o.id==='CourtKey'))Object.assign(p,{shadowMapWidth:2048,shadowMapHeight:2048,shadowExtent:32,shadowFar:120,shadowBias:-.0012,shadowNormalBias:.08,shadowRadius:1.5,shadowIntensity:.82});
  if(c.type==='DirectionalLight'&&/^Outdoor[0-2]_sun$/.test(o.id)){
   const phase=['day','night','evening'][Number(o.id[7])],light=celestial[phase];
   o.rotation=[...light.rotationDegrees];
   Object.assign(p,{castShadow:true,shadowExtent:48,shadowFar:180,shadowNormalBias:.035,shadowRadius:1.2});
  }
  if(o.id==='Outdoor0_ambient'&&c.type==='SkyLight')Object.assign(p,{intensity:.65,color:[.48,.61,.75,1],groundColor:[.12,.14,.12,1]});
  if(o.id==='Outdoor1_ambient'&&c.type==='SkyLight')Object.assign(p,{intensity:.6,color:[.18,.24,.36,1],groundColor:[.055,.07,.10,1]});
  if(regraded&&o.id==='Outdoor0_ambient'&&c.type==='SkyLight')Object.assign(p,{intensity:.8,color:[.54,.53,.67,1],groundColor:[.17,.15,.20,1]});
  if(regraded&&o.id==='Outdoor0_sun'&&c.type==='DirectionalLight')Object.assign(p,{intensity:1.35,color:[.78,.77,.88,1],shadowRadius:2.2,shadowIntensity:.58});
  if(regraded&&o.id==='Outdoor2_ambient'&&c.type==='SkyLight')Object.assign(p,{intensity:.65,color:[.34,.26,.43,1],groundColor:[.105,.08,.13,1]});
  if(regraded&&o.id==='Outdoor2_sun'&&c.type==='DirectionalLight')Object.assign(p,{intensity:.7,color:[.74,.49,.48,1],shadowRadius:1.9,shadowIntensity:.65});
  if(regraded&&o.id==='Outdoor1_sun'&&c.type==='DirectionalLight')Object.assign(p,{intensity:.35,color:[.47,.51,.72,1]});
  if(o.id==='CourtAmbient'&&c.type==='SkyLight')Object.assign(p,{intensity:.85,color:[.60,.65,.76,1],groundColor:[.12,.095,.16,1]});
  if(o.id==='CourtKey'&&c.type==='DirectionalLight')Object.assign(p,{intensity:1.8,color:[1,.84,.68,1]});
  if(o.id==='CourtFill'&&c.type==='DirectionalLight')Object.assign(p,{intensity:.38,color:[.57,.66,.85,1]});
 }
 return scene;
}
