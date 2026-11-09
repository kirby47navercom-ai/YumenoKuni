import{applyPadDetailSource}from'../../tools/render_pad_detail_source_ui.mjs';
// Static V3 clone geometry, not a guessed grid or 256px opaque card.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../../../engineCreate/prototype/ui-assets.js';
export async function emitV4PadGiftUI({repo,write,body}){
 const source=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/pad_gift_icon_scale_followup.json'),'utf8'));
 const leaf=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/pad_report_gift_leaf_followup.json'),'utf8'));
 if(source.parent_scale.scale_xy.join(',')!=='1,1'||source.actual_initialized_grid.length!==27)throw Error('Unverified gift clone geometry');
 const w=createWidgetAsset('PadGiftV4');w.scaleMode='scale';w.scaleRule='fit';
 const add=(type,id,rect,props={})=>{const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:true,...props});w.nodes.push(n);};
 const detail=leaf.gift.details;
 for(const [id,p,background] of [['PgGridPlate','d1','#00000099'],['PgBodyPlate','i_black/d1','#000000b2'],['PgTitlePlate','p_setumei_title_base/d1','#111118ee']])add('Panel',id,detail.find(x=>x.path===p).rect_1280,{background});
 for(const cell of source.actual_initialized_grid){
  const i=cell.slot,a=cell.attachment_origin_1280;
  add('Image','PgBase'+i,cell.base_quad_1280,{texture:'Assets/Art/ui/pad_gift_base.svg',imageFit:'fill'});
  add('Image','PgImage'+i,cell.image_quad_1280,{texture:'Assets/Art/ui/pad_gift_unknown.svg',imageFit:'contain'});
  add('Image','PgFrame'+i,cell.frame_quad_1280,{texture:'Assets/Art/ui/pad_gift_selected.svg',imageFit:'fill',visible:false});
  add('Text','PgNew'+i,[a[0]+52.33333,a[1]+26,68.26562,22.39966],{text:'NEW',fontSize:20,align:'center',color:'#ffe34c',visible:false});
  for(const [digit,key] of [[0,'ones'],[1,'tens'],[2,'hundreds']])add('Text','PgDigit'+i+'_'+digit,cell[key+'_quad_1280'],{fontSize:13.43978,align:'center',visible:false});
  add('Text','PgTimes'+i,cell.times_quad_1280,{text:'×',fontSize:10.26662,align:'center',visible:false});
 }
 add('Text','PgTitle',detail.find(x=>x.path==='p_present_title/_f_present_title').rect_1280,{fontSize:30,align:'center'});
 add('Text','PgBody',detail.find(x=>x.path==='p_present_message/_f_present_message').rect_1280,{fontSize:28,wrap:true});
 add('Text','PgNumber',[73.33333,473.33333,112,22],{fontSize:20});
 add('Text','PgQuantity',[1139.33333,475.33333,72,22],{fontSize:20,align:'right'});
 add('Text','PgComplete',[1113.33333,44.66667,106,21.33333],{fontSize:20,align:'right'});
 await applyPadDetailSource({repo,write,w,screen:'gift'});
 if(!validWidgetAsset(w))throw Error('Invalid Pad gift widget');
 await write('Assets/UI/PadGiftV4.hbwidget.json',w);return w;
}
