import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {publishWorldData} from './v4-data.mjs';
import {emitV4PadMapUI} from './v4-pad-map-ui.mjs';
import {applyExplorationMaterialLight} from './v4-exploration-material-light.mjs';
import {createHash} from 'node:crypto';
import {applyParkArchitectureLight} from './v4-park-architecture-light.mjs';
import {applyParkBackground,readParkBackgrounds,readParkCctvHead} from './v4-park-background.mjs';

export async function emitParkScenes({repo,explore,write}){
 const manifest=await fs.readFile(path.join(repo,'art/space_v4/park_levels_v1/manifest.json'),'utf8').then(JSON.parse,e=>{if(e.code!=='ENOENT')throw e;return null;});
 if(!manifest?.geometryComplete)return [];
 const plan=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/park_levels_v1/plan.json'),'utf8'));
 const backgrounds=await readParkBackgrounds(repo);
 const cctv=await readParkCctvHead(repo);
 await write(cctv.runtime,cctv.bytes);
 const architecture=await fs.readFile(path.join(repo,'art/space_v4/park_levels_v1/architecture_v6/manifest.json'),'utf8').then(JSON.parse,e=>{if(e.code!=='ENOENT')throw e;return null;});
 const output=[];
 for(const d of plan.districts){
  const scene=structuredClone(explore);scene.sceneName=d.scene;
  scene.objects=scene.objects.filter(o=>!o.id.startsWith('Exterior')&&o.id!=='ParkGeometry');
  const marker=scene.objects.find(o=>o.id==='ExploreScene');if(!marker)throw Error('Missing exploration ownership marker');marker.id=d.scene+'Scene';
  const source=scene.objects.find(o=>o.id==='ExploreGeometry');if(!source)throw Error('Missing exploration mesh prototype');
  source.components.find(c=>c.type==='MeshRenderer').properties.mesh='';
  const park=structuredClone(source);park.id='ParkGeometry';park.name=d.name+' · 전용 환경';park.position=[300,0,0];park.visible=true;
  Object.assign(park.components.find(c=>c.type==='MeshRenderer').properties,{mesh:'Assets/Art/park_levels/'+d.id+'.glb',visible:true});scene.objects.push(park);
  // Keep the same supplied marker pixels, but move their camera projection on
  // the GPU rather than repainting a full-resolution UI surface every frame.
  const person=scene.objects.find(o=>o.id==='ExplorePerson0');if(!person)throw Error('Missing exploration sprite prototype');
  for(let k=0;k<10;k++){const marker=structuredClone(person);marker.id='ExploreTarget'+k;marker.name='조사 표식 '+k;marker.parent='Camera';marker.position=[0,0,-.2];marker.rotation=[0,0,0];marker.scale=[.4,.4,.4];marker.visible=true;Object.assign(marker.components.find(c=>c.type==='SpriteRenderer').properties,{texture:'Assets/Art/ui/vpoint.svg',width:30*.5/900,height:30*.5/900,billboard:false,visible:false,color:[1,1,1,.7],shading:'unlit',toneMapping:'display',blendMode:'translucent',castShadow:false,sortingOrder:10000});scene.objects.push(marker);}
  if(d.id==='fairytale'){const gates=[['carnival_midway',59,1],['mirror_midway',64,-42],['clockwork_midway',-64,-24],['starlight_midway',24,64]];for(const [hub,x,z]of gates){const gate=structuredClone(park);gate.id='ParkGate_'+hub;gate.name='구역 출입문';gate.position=[300+x,0,z];gate.components.find(c=>c.type==='MeshRenderer').properties.mesh='Assets/Art/park_levels/gate.glb';scene.objects.push(gate);}}
  applyExplorationMaterialLight(scene);
  applyParkArchitectureLight(scene,d.id,architecture);
  const background=backgrounds.get(d.id);
  if(!background)throw Error('Missing park background: '+d.id);
  applyParkBackground(scene,background);
  await write(background.runtime,background.bytes);
  const dest='Assets/Scenes/'+d.scene+'.hbscene.json';await write(dest,scene);output.push(dest);
 }
 return output;
}

export async function emitParkLevels({root,repo,write}){
 const manifest=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/park_levels_v1/manifest.json'),'utf8'));if(!manifest.geometryComplete)throw Error('Park geometry incomplete');
 const world=JSON.parse(execFileSync('python',['-X','utf8',path.join(repo,'tools/v4_park_levels.py')],{encoding:'utf8',maxBuffer:32*1024*1024,windowsHide:true}));
 const paths=[],overrides={};const tracked=async(dest,value)=>{await write(dest,value);paths.push(dest);};
 for(const phase of ['day','evening','night'])await tracked('Assets/Art/environment/sky_'+phase+'.glb',await fs.readFile(path.join(repo,'art/environment_v5/sky_'+phase+'.glb')));
 const localNames=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/park_levels_v1/theme_park_v2/local-names-manifest.json'),'utf8'));
 for(const row of localNames.assets){const source=await fs.readFile(path.join(repo,row.source));if(createHash('sha256').update(source).digest('hex')!==row.sourceSHA256)throw Error('Refresh name-free own local mesh: '+row.source);await tracked(row.runtime,await fs.readFile(path.join(repo,row.file)));}
 // Only this presentation change over the shipped widget. Keep unrelated
 // authoring UI changes in the shared workspace out of the scoped package.
 const frozen=JSON.parse(await fs.readFile(path.join(root,'Saved/park-levels-20261104/baseline-build.json'),'utf8'));
 const hints=JSON.parse(await fs.readFile(path.join(frozen.flat,'Content/Assets/UI/Explore.hbwidget.json'),'utf8'));
 const hint=hints.nodes.find(n=>n.id==='ExHint');if(!hint)throw Error('Missing shipped exploration hint owner');
 const retired=structuredClone(hints.nodes.find(n=>n.id==='root'));Object.assign(retired,{id:'RetiredExploreHints',name:'Retired hint compatibility',parent:'root'});Object.assign(retired.properties,{visible:false,text:'',background:'#00000000'});hints.nodes.push(retired);
 hint.parent=retired.id;Object.assign(hint.properties,{visible:false,text:'',color:'#00000000'});
 const hintFile=path.join(root,'Saved/park-levels-20261104/textfree-explore.hbwidget.json');await fs.writeFile(hintFile,JSON.stringify(hints));overrides['Content/Assets/UI/Explore.hbwidget.json']=hintFile;
 const gate=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/park_levels_v1/gate-manifest.json'),'utf8'));await tracked(gate.runtime,await fs.readFile(path.join(repo,gate.file)));
 for(const a of manifest.assets)await tracked(a.runtime,await fs.readFile(path.join(repo,a.file)));
 // Compact survey maps are derived from authored footprints; the pad retains its
 // existing V3 presentation and chapter-aware runtime visibility.
 for(const [id,d] of Object.entries(world.parkLevels.districts)){
  const rooms=Object.entries(world.instances).filter(([,i])=>i.district===id),b=world.spaces[world.instances[d.hub].space].bounds;
  const rect=rooms.map(([,i])=>{const r=world.spaces[i.space].bounds;return `<rect x="${i.p[0]+r[0]}" y="${i.p[2]+r[1]}" width="${r[2]-r[0]}" height="${r[3]-r[1]}" fill="#282330" stroke="#ffda24" stroke-width=".35"/>`;}).join('');
  await tracked('Assets/Art/park_levels/map_'+id+'.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${b[0]} ${b[1]} ${b[2]-b[0]} ${b[3]-b[1]}">${rect}</svg>`);
 }
 await emitV4PadMapUI({repo,write:tracked,body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',preparedWorld:world});
 await publishWorldData(world,tracked);
 const explore=JSON.parse(await fs.readFile(path.join(root,'Assets/Scenes/Explore.hbscene.json'),'utf8'));
 const scenes=await emitParkScenes({repo,explore,write:tracked});
 await write('Saved/park-levels-20261104/emission.json',{paths:[...new Set(paths)],overrides,scenes,geometryComplete:true,runtimeVerified:false});
 return {parks:scenes.length,assets:manifest.assets.length,paths:paths.length,runtimeVerified:false};
}
