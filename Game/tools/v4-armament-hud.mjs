// V3 SFL composed quads and native mask travel. Editable vector artwork is
// an adaptation of the observed HUD, not a recovered original raster/material.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const repo=path.dirname(path.dirname(path.dirname(fileURLToPath(import.meta.url))));
export const ARMAMENT_PLAYER_RECT=[950,470,220,220];
// Floating words retain V3's unboxed placement; ink outlines provide contrast
// against both pale windows and the opponent, rather than borrowing menu cards.
export function applyArmamentTextStyle(widget){
 const player=widget.nodes.find(n=>n.id==='ArmFace');if(!player)throw Error('Missing armament player portrait');player.slot.offset=[...ARMAMENT_PLAYER_RECT];player.properties.imageFit='contain';
 const floating=['ArmLine','ArmQuestion','ArmJoined','ArmNoteKey','ArmNoteType',...Array.from({length:4},(_,i)=>'Piece'+i)];
 for(const id of floating){const node=widget.nodes.find(n=>n.id===id);if(!node)throw Error('Missing armament text '+id);Object.assign(node.properties,{outlineColor:'#070510',outlineWidth:id==='ArmNoteType'?3:4,padding:6});if(id!=='ArmNoteType')node.properties.font='Assets/Fonts/dohyeon/DoHyeon-Regular.ttf';}
 return widget;
}
export async function emitArmamentHud({write,put}){
 const ref=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/armament_rhythm_hud_followup.json'),'utf8'));
 const spec=[['Hp','health',512,32,27,438,'#f9499c'],['Mental','mental',512,32,74,332,'#47dbff'],['Boss','boss',1024,64,136,888,'#f9499c']];
 for(const [name,key,w,h,start,travel,color] of spec){
  const rect=ref[key].parts.fill.first_local_frame_leaves[0].own1280_rect_xywh;
  // The vector's visible span is an explicit adaptation inferred from the
  // retained mask's full->empty travel. Texture alpha is not established.
  const end=name==='Boss'?1024:start+travel,top=h*.30,bottom=h*.72;
  const shape=`M${start} ${top}H${end-12}L${end} ${bottom}H${start+12}Z`;
  await write(`Assets/Art/ui/arm_${name}_track.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><path d="${shape}" fill="#100f20" stroke="#d7e9f1" stroke-width="2"/><path d="M${start+8} ${h*.92}H${end+4}" stroke="#44bcd5" stroke-width="2"/></svg>`);
  put('Image','ArmHud'+name+'Track',rect,{texture:`Assets/Art/ui/arm_${name}_track.svg`,imageFit:'fill'}).slot.zIndex=20;
  for(let percent=0;percent<=100;percent++){
   const loss=1-percent/100,maskX=name==='Boss'?-888*loss: start+travel*loss;
   await write(`Assets/Art/ui/arm_${name}_${percent}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><defs><clipPath id="remaining"><rect x="${maskX}" y="0" width="${w}" height="${h}"/></clipPath></defs><path d="${shape}" fill="${color}" clip-path="url(#remaining)"/><path d="M${start+12} ${top+2}H${end-12}" stroke="white" stroke-opacity=".55" stroke-width="2" clip-path="url(#remaining)"/></svg>`);
  }
  put('Image','ArmHud'+name,rect,{texture:`Assets/Art/ui/arm_${name}_100.svg`,imageFit:'fill'}).slot.zIndex=20;
 }
 for(let i=0;i<20;i++){
  const rect=ref.tension.nodes[i].first_local_frame_leaves[0].own1280_rect_xywh;
  // Ten half/full pairs use their individual, nonuniform source quads.
  const half=i%2===0,d=half?'M6 25L48 7L43 14L9 29Z':'M6 25L55 3L49 14L9 29Z';
  await write(`Assets/Art/ui/arm_tension_${i}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="64" height="32"><path d="${d}" fill="#ffe44c" stroke="#bb7c09" stroke-width="1"/></svg>`);
  put('Image','ArmHudTension'+i,rect,{texture:`Assets/Art/ui/arm_tension_${i}.svg`,imageFit:'fill'}).slot.zIndex=20;
 }
}
