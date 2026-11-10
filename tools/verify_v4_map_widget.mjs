import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {validWidgetAsset} from '../../engineCreate/prototype/ui-assets.js';
import {emitV4PadMapUI} from '../Game/tools/v4-pad-map-ui.mjs';
const repo=path.dirname(path.dirname(fileURLToPath(import.meta.url))),files=new Map();
const layout=await emitV4PadMapUI({repo,body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',write:async(k,v)=>files.set(k,v)});
const source=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/pad_map_ui_contract.json'),'utf8'));
for(const name of ['PadMapV4','PadMapAtlasV4']){const w=files.get('Assets/UI/'+name+'.hbwidget.json');assert(validWidgetAsset(w));assert(w.nodes.length<=256);}
const widget=files.get('Assets/UI/PadMapV4.hbwidget.json'),nodes=Object.fromEntries(widget.nodes.map(n=>[n.id,n]));
const check=(actual,expected)=>actual.forEach((v,i)=>assert(Math.abs(v-expected[i])<.002));
for(let i=0;i<6;i++){check(nodes['MpPlace'+i].slot.offset,source.place_list.text_rows[i].own1280_rect_xywh);check(layout.selected[i],source.place_list.selected_states[i].selected_plate.own1280_rect_xywh);}
for(let i=0;i<16;i++)for(const [node,part]of[['MpChar','portrait'],['MpCharSelected','selected'],['MpCharDim','disabled_overlay'],['MpCharUnavailable','unavailable_overlay'],['MpCharBase','base']])check(nodes[node+i].slot.offset,source.character_search.cells[i].parts[part].own1280_rect_xywh);
assert(nodes.MpListActive.slot.zIndex<nodes.MpPlace0.slot.zIndex&&nodes.MpListActive.slot.zIndex>nodes.MpListShade.slot.zIndex);
const world=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/runtime_v1/world.json'),'utf8'));assert.deepEqual(Object.keys(layout.instances).sort(),Object.keys(world.instances).sort());
assert.equal(layout.regions.length,5);assert.equal(layout.floorVariants.length,8);assert(JSON.stringify(layout).length<180000);
for(const edge of layout.edges){assert.equal(layout.instances[edge.a].group,layout.instances[edge.b].group);assert(world.connections.some(e=>e.a===edge.a&&e.b===edge.b));}
assert.equal([...files.keys()].filter(k=>k.includes('/map_mask/')).length,38);
console.log(JSON.stringify({ok:true,sourcePlaceRows:6,sourceCharacterParts:80,ownInstances:Object.keys(layout.instances).length,ownGeometry:layout.geometry.length,ownSameAreaLinks:layout.edges.length,originalFloorVariants:8,ownGroups:5,widgets:['PadMapV4','PadMapAtlasV4'].map(n=>({name:n,nodes:files.get('Assets/UI/'+n+'.hbwidget.json').nodes.length})),gameFilesWritten:0,runtimeAccepted:false}));
