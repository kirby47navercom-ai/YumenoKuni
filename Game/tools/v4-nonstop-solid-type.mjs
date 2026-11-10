import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game);
const {makeSceneComponent}=await import(pathToFileURL(path.resolve(repo,'Game/engineCreate/prototype/scene-components.js')));
export async function emitNonstopSolidType({output,write}){
 const bank=path.join(repo,'art/nonstop_solid_type'),manifest=JSON.parse(await fs.readFile(path.join(bank,'manifest.json'),'utf8'));
 for(const g of manifest.glyphs)for(const color of ['w','y','b']){
  const name=`u_${g.codepoint.toString(16)}_${color}.glb`;
  await write('Assets/Art/nonstop_solid_type/'+name,await fs.readFile(path.join(bank,name)));
 }
 const characters=manifest.glyphs.map(g=>String.fromCodePoint(g.codepoint)).join('');
 await fs.writeFile(path.join(game,'Source/NonstopSolidTypeV4.hpp'),'#pragma once\n#include <string>\nnamespace solidtypev4 { inline const std::string characters='+JSON.stringify(characters)+'; inline bool has(const std::string& c){return characters.find(c)!=std::string::npos;} }\n');
 const file='Assets/Scenes/DebateHud.hbscene.json',scene=JSON.parse(await fs.readFile(path.join(output,file),'utf8'));
 for(const o of scene.objects)if(/^TrialGpu_MF\d+$/.test(o.id)){
  if(!o.components.some(c=>c.type==='MeshRenderer'))o.components.push(makeSceneComponent('MeshRenderer',{mesh:'',visible:false,castShadow:false,receiveShadow:false}));
 }
 await write(file,scene);
 return {glyphs:manifest.glyphs.length,solidActors:scene.objects.filter(o=>/^TrialGpu_MF\d+$/.test(o.id)).length};
}
