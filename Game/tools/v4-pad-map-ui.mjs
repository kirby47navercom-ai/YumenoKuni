import{applyMapOptionsSource}from'../../tools/render_map_options_source_ui.mjs';
import {emitOwnThemeMasks} from './v4-own-character-themes.mjs';
import {execFileSync} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../../../engineCreate/prototype/ui-assets.js';

// V3 source positions around the map; own actual world footprints/links inside.
// This file does not reinterpret native TechouMapX/Y as this game's GLB units.
export async function emitV4PadMapUI({repo,write,body,preparedWorld=null}){
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/pad_map_ui_contract.json'),'utf8'));
 if(!preparedWorld){const manifest=await fs.readFile(path.join(repo,'art/space_v4/park_levels_v1/manifest.json'),'utf8').then(JSON.parse,e=>{if(e.code!=='ENOENT')throw e;return null;});if(manifest?.geometryComplete)preparedWorld=JSON.parse(execFileSync('C:/python/python.exe',['-X','utf8',path.join(repo,'tools/v4_park_levels.py')],{encoding:'utf8',maxBuffer:32*1024*1024,windowsHide:true}));}
 const worldBytes=preparedWorld?Buffer.from(JSON.stringify(preparedWorld)):await fs.readFile(path.join(repo,'art/space_v4/runtime_v1/world.json')),world=preparedWorld||JSON.parse(worldBytes);
 // The older separately baked atlas no longer matches its recorded world hash.
 // Derive each map footprint from the actual runtime catalog instead of hiding
 // that mismatch or rebaking unrelated artwork.
 const groupOf=id=>id==='ferris_cabin'?'cabin':world.parkLevels&&world.instances[id].district&&!['residence','depths'].includes(world.instances[id].district)?world.instances[id].district:id==='hotel_corridor'||id.startsWith('guest_')?'hotel_upper':id==='ferris_cabin'?'cabin':id==='trial_elevator'?'court':world.instances[id].p[1]<-1?'lower':'surface';
 const physical=id=>{const i=world.instances[id],b=world.spaces[i.space].bounds,a=(i.rotation||0)*Math.PI/180;return [[b[0],b[1]],[b[2],b[1]],[b[2],b[3]],[b[0],b[3]]].map(([x,z])=>[i.p[0]+x*Math.cos(a)-z*Math.sin(a),i.p[2]+x*Math.sin(a)+z*Math.cos(a)]);};
 const atlas={assets:[]};
 for(const state of world.parkLevels?[...Object.keys(world.parkLevels.districts),'surface','hotel_upper','lower','court','cabin']:['surface','hotel_upper','lower','court','cabin']){
  const rooms=[];
  for(const id of Object.keys(world.instances).filter(id=>groupOf(id)===state)){
   if(id==='inspection_hall_changed'&&JSON.stringify(physical(id))===JSON.stringify(physical('inspection_hall_normal')))continue;
   const aliases=id==='inspection_hall_normal'&&JSON.stringify(physical(id))===JSON.stringify(physical('inspection_hall_changed'))?['inspection_hall_changed']:[];
   rooms.push({instance:id,aliases,points:physical(id)});
  }
  if(!rooms.length)continue;const points=rooms.flatMap(r=>r.points),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),scale=Math.min(800/(maxX-minX),440/(maxY-minY)),cx=(minX+maxX)/2,cy=(minY+maxY)/2;
  atlas.assets.push({state,worldCenter:[cx,cy],scale,anchors:rooms.map(r=>{const polygon=r.points.map(([x,y])=>[(x-cx)*scale,(y-cy)*scale]),xs=polygon.map(p=>p[0]),ys=polygon.map(p=>p[1]),x=Math.min(...xs),y=Math.min(...ys),w=Math.max(...xs)-x,h=Math.max(...ys)-y;return {...r,anchor:[x+w/2,y+h/2],rect:[x,y,w,h],polygon};})});
 }
 const make=name=>{const w=createWidgetAsset(name);w.scaleMode='scale';w.scaleRule='fit';return w;};
 const add=(w,type,id,r,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=r;const {zIndex=0,...properties}=props;n.slot.zIndex=zIndex;Object.assign(n.properties,{text:'',font:body,fontSize:28.66667,color:'#ffffff',background:'#00000000',padding:0,radius:0,borderWidth:0,focusable:false,visible:true,...properties});w.nodes.push(n);};
 const save=async w=>{if(!validWidgetAsset(w))throw Error('Invalid map widget '+w.name);await write('Assets/UI/'+w.name+'.hbwidget.json',w);};
 const ownSvg=async(name,ink,w=128,h=128)=>{const asset='Assets/Art/ui/map/'+name+'.svg';await write(asset,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">${ink}</svg>`);return asset;};
 const ref=(leaves,p)=>{const x=leaves.find(x=>x.path===p);if(!x)throw Error('Missing source map leaf '+p);return x.own1280_rect_xywh;};
 const map=make('PadMapV4'),field=make('PadMapAtlasV4');
 const viewport=[340,140,880,520],center=[1160*2/3,640*2/3];
 const layout={scope:'Source six place rows/16 character cells/area controls and retained floor variants. Chapter-gated thematic atlas groups, actual 3D footprints/links/anchors, map clipping mask, PC mapping and visited/eligible travel checks. Original common/list raster, floor availability/native exact pan/animation/material identity unclaimed.',sourceWorldSha256:createHash('sha256').update(worldBytes).digest('hex'),viewport,center,place:[],selected:[],cells:[],regions:[],instances:{},geometry:[],edges:[],floorVariants:c.floor_controls.variants.map(v=>({variant:v.variant,leaves:v.leaves.map(x=>({path:x.path,rect:x.own1280_rect_xywh,images:x.image_ids}))}))};
 // Same provided theme outside the map viewport clips moving map ink. The
 // engine's Panel has no clipping flag; no engine or DOM changes are needed.
 add(map,'Image','MpOutsideMask',[0,0,1280,720],{texture:'Assets/Art/ui/v3/map_mask/type_000.svg',imageFit:'fill'});
 const themes=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/pad_system_connection_contract.json'),'utf8')).provided_bank_check.theme_backgrounds.resources;
 for(const theme of themes){const png=(await fs.readFile(theme.path)).toString('base64'),id=String(theme.type_id).padStart(3,'0');await write('Assets/Art/ui/v3/map_mask/type_'+id+'.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"><defs><clipPath id="outside"><path fill-rule="evenodd" clip-rule="evenodd" d="M0 0H1280V720H0ZM${viewport[0]} ${viewport[1]}V${viewport[1]+viewport[3]}H${viewport[0]+viewport[2]}V${viewport[1]}Z"/></clipPath></defs><image href="data:image/png;base64,${png}" width="1280" height="725.333333" preserveAspectRatio="none" clip-path="url(#outside)"/></svg>`);}
 await emitOwnThemeMasks({repo,write});
 const structure=c.place_list.structural_leaves;
 add(map,'Panel','MpListShade',ref(structure,'i_dammy/depth1'),{background:'#08080ddd'});
 for(let i=0;i<6;i++){
  const r=c.place_list.text_rows[i].own1280_rect_xywh;layout.place.push(r);layout.selected.push(c.place_list.selected_states[i].selected_plate.own1280_rect_xywh);
  add(map,'Text','MpPlace'+i,[r[0]+16,r[1],r[2]-16,r[3]],{visible:false,zIndex:2});
 }
 add(map,'Image','MpListActive',layout.selected[0],{texture:'',imageFit:'fill',visible:false,zIndex:1});
 add(map,'Text','MpPlaceTab',ref(structure,'p_place/depth1'),{text:'장소',fontSize:17.06667,align:'center'});
 add(map,'Text','MpStudentTab',ref(structure,'p_student/depth1'),{text:'학생',fontSize:17.06667,align:'center'});
 for(const [id,p,back]of[['MpScrollBase','i_scroll_base/depth1','#08080d'],['MpScrollTrack','i_scroll_base_grey/depth1','#ffffff44'],['MpScroll','p_scroll_color/depth1','#ffffff']])add(map,'Panel',id,ref(structure,p),{background:back});
 layout.scroll=ref(structure,'p_scroll_color/depth1');
 for(const cell of c.character_search.cells){
  const parts=Object.fromEntries(Object.entries(cell.parts).map(([k,v])=>[k,v.own1280_rect_xywh]));layout.cells.push(parts);const i=cell.index;
  add(map,'Panel','MpCharBase'+i,parts.base,{background:'#18181eee',visible:false});
  add(map,'Image','MpChar'+i,parts.portrait,{texture:'',imageFit:'contain',visible:false});
  add(map,'Panel','MpCharDim'+i,parts.disabled_overlay,{background:'#000000b2',visible:false});
  add(map,'Image','MpCharUnavailable'+i,parts.unavailable_overlay,{texture:'',imageFit:'fill',visible:false});
  add(map,'Image','MpCharSelected'+i,parts.selected,{texture:'',imageFit:'fill',visible:false});
 }
 for(const [id,p,label]of[['MpPrev','p_l1/depth1','Q'],['MpNext','p_r1/depth1','E']]){const r=ref(c.region_controls.leaves,p);layout[id]=r;add(map,'Text',id,r,{text:label,fontSize:20,align:'center'});}
 layout.area=ref(c.region_controls.leaves,'p_map_name/_f_map_name');add(map,'Text','MpArea',layout.area,{fontSize:30,align:'center'});
 // The own atlas groups each have one authored map level. Do not pretend the
 // source's eight visual variants are eight freely navigable own floors.
 const floor=c.floor_controls.variants[0].leaves;
 const floorBank=c.provided_texture_bank.floor_textures;
 for(const [id,p,resource]of[['MpFloorTitle','p_title_text/depth1','s_titile_floor_JP.png'],['MpFloorBase','i_floor_off_000/depth1','floor_non.png'],['MpFloorActive','p_floor_on_000/depth1','floor_act.png']]){
  const raw=(await fs.readFile(floorBank.find(x=>x.resource===resource).path)).toString('base64'),r=ref(floor,p),asset=await ownSvg(id,`<image href="data:image/png;base64,${raw}" width="128" height="128" preserveAspectRatio="none"/>`);
  add(map,'Image',id,r,{texture:asset,imageFit:'fill'});
 }
 add(map,'Text','MpFloor',ref(floor,'p_floor_000/depth1'),{text:'',fontSize:24,color:'#000000',align:'center'});
 for(const [id,r,props]of[['MpHintShadow',[41.5,677.5,1200,30],{color:'#000000'}],['MpHint',[40,676,1200,30],{}]])add(map,'Text',id,r,{fontSize:18,align:'right',...props});
 const names={surface:['공원 · 시설','지상'],hotel_upper:['호텔 객실층','2F'],lower:['하부 구역','B1'],court:['재판 승강기','지하'],cabin:['관람차 객실','상공']};
 for(const record of atlas.assets){
  const group=layout.regions.length,[name,floorLabel]=names[record.state]||[world.parkLevels.districts[record.state].name,'지상'];layout.regions.push({id:record.state,name,floor:floorLabel,worldCenter:record.worldCenter,scale:record.scale});
  for(const a of record.anchors){
   const members=[a.instance,...a.aliases].filter(id=>world.instances[id]);if(!members.length)continue;
   const n=layout.geometry.length,anchor=a.anchor,r=a.rect;
   layout.geometry.push({id:a.instance,group,anchor,rect:r,members,label:world.instances[members[0]].label});
   for(const id of members)layout.instances[id]={geometry:n,group,label:world.instances[id].label,anchor,rect:r,space:world.instances[id].space,spawn:world.spaces[world.instances[id].space].spawn,origin:world.instances[id].p,rotation:world.instances[id].rotation||0};
   const isHub=world.parkLevels&&Object.values(world.parkLevels.districts).some(d=>d.hub===a.instance);
   const shape=await ownSvg('room_'+n,`<polygon points="${a.polygon.map(([x,y])=>[x-r[0],y-r[1]].join(',')).join(' ')}" fill="${isHub?'none':'#101017'}" fill-opacity=".92" stroke="#ffffff" stroke-width="1.5" vector-effect="non-scaling-stroke"/>`,r[2],r[3]);
   add(field,'Image','MaRoom'+n,[0,0,1,1],{texture:shape,imageFit:'fill',visible:false});
  }
 }
 if(Object.keys(layout.instances).length!==Object.keys(world.instances).length)throw Error('Own map omits world instances');
 for(const edge of world.connections){
  const a=layout.instances[edge.a],b=layout.instances[edge.b];if(!a||!b||a.group!==b.group||a.geometry===b.geometry)continue;
  const x=Math.min(a.anchor[0],b.anchor[0]),y=Math.min(a.anchor[1],b.anchor[1]),w=Math.max(2,Math.abs(a.anchor[0]-b.anchor[0])),h=Math.max(2,Math.abs(a.anchor[1]-b.anchor[1]));
  const n=layout.edges.length;layout.edges.push({a:edge.a,b:edge.b,group:a.group,rect:[x,y,w,h]});
  const asset=await ownSvg('link_'+n,`<path d="M${a.anchor[0]-x} ${a.anchor[1]-y}L${b.anchor[0]-x} ${b.anchor[1]-y}" fill="none" stroke="#ffffff" stroke-width="2" stroke-dasharray="5 4"/>`,w,h);
  add(field,'Image','MaLink'+n,[0,0,1,1],{texture:asset,imageFit:'fill',visible:false,zIndex:-1});
 }
 const pointer=await ownSvg('player','<path d="M64 7L114 115L64 89L14 115Z" fill="#f0448c" stroke="#000000" stroke-width="7"/>');
 const target=await ownSvg('target','<circle cx="64" cy="64" r="48" fill="none" stroke="#f0448c" stroke-width="8"/><circle cx="64" cy="64" r="56" fill="none" stroke="#000000" stroke-width="3"/>');
 add(field,'Image','MaPlayer',[0,0,22,22],{texture:pointer,imageFit:'contain',visible:false,zIndex:5});add(field,'Image','MaSelected',[0,0,36,36],{texture:target,imageFit:'contain',visible:false,zIndex:4});
 add(field,'Text','MaNameShadow',[0,0,350,34],{fontSize:22,align:'center',color:'#000000',visible:false,zIndex:6});
 add(field,'Text','MaName',[0,0,350,34],{fontSize:22,align:'center',visible:false,zIndex:7});
 for(let i=0;i<16;i++)add(field,'Image','MaPerson'+i,[0,0,28,28],{texture:'',imageFit:'contain',visible:false,zIndex:3});
 await applyMapOptionsSource({repo,write,w:map,screen:'map'});
 if(field.nodes.length>256)throw Error('Park atlas exceeds native widget bounds: '+field.nodes.length);await save(map);await save(field);await write('Assets/Data/v4_story/map_layout.json',layout);return layout;
}
