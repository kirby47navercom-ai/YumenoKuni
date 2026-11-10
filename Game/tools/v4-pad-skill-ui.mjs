import{applyPadDetailSource}from'../../tools/render_pad_detail_source_ui.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../engineCreate/prototype/ui-assets.js';
export async function emitV4PadSkillUI({repo,write,body}){
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/report_card_ui_contract.json'),'utf8'));
 // 401010 attaches the two independent list roots to these window anchors;
 // 4038a0 consumes the equipped root's stored xy. Symbol-name association is
 // reconstructed from matching SFL roles, not an interned-ID decode claim.
 const origins={catalog:[97*2/3,127*2/3],equipped:[1157*2/3,126*2/3]};
 const shift=(r,o)=>[r[0]+o[0],r[1]+o[1],r[2],r[3]];
 const w=createWidgetAsset('PadSkillV4');w.scaleMode='scale';w.scaleRule='fit';
 const add=(type,id,rect,props={})=>{const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:26.66667,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:true,...props});w.nodes.push(n);};
 const window=c.skill_window_static.snapshots[0].leaves;
 // Source-family compositing below supplies the actual gradient/frame pixels.
 for(const side of ['catalog','equipped'])add('Image','PsPanel'+side,[0,0,1280,720],{texture:'',imageFit:'fill'});
 add('Panel','PsDescriptionPlate',window.find(x=>x.path==='i_window_beta_black/d1').rect_1280,{background:'#000000b2'});
 const frame=window.find(x=>x.path==='i_window_waku/d1').rect_1280;
 add('Image','PsDescriptionFrame',frame,{texture:'Assets/Art/ui/pad_skill_description_frame.svg',imageFit:'fill'});
 const description=c.skill_window_static.catalog_additional_fields.leaves.find(x=>x.path==='p_skill_setumei/_f_skill_setumei')||window.find(x=>x.path==='p_skill_setumei/_f_skill_setumei');
 if(!description)throw Error('Missing source skill description');
 add('Text','PsBody',description.rect_1280,{wrap:true,fontSize:26.66667});
 const layout={catalog:[],equipped:[],origins,scope:'Actual source-family bitmap/affine chrome; static401010 list origins and own skill names, costs, equip/purchase state. Native scripts and all transition timing are not executed.'};
 for(let i=0;i<7;i++){
  const left=shift(c.skill_entry.catalog_text_leaves[i].rect_1280,origins.catalog),right=shift(c.skill_entry.equipped_local_text.text_leaves[i].rect_1280,origins.equipped);layout.catalog.push(left);layout.equipped.push(right);
  add('Text','PsRow'+i,left);add('Text','PsEquipped'+i,right,{visible:false});
  const p=`p_slot_${String(i).padStart(3,'0')}/`;
  for(const [prefix,data,origin] of [['PsCost',c.skill_window_static.catalog_digits,origins.catalog],['PsEquippedCost',c.skill_window_static.equipped_digits,origins.equipped]])for(let d=0;d<2;d++){
   const digit=data.leaves.find(x=>x.path.startsWith(p)&&x.path.endsWith('_'+String(d).padStart(3,'0')+'/d1'));
   if(!digit)throw Error('Missing source skill SP digit '+prefix+i+'_'+d);
   const r=shift(digit.rect_1280,origin);add('Text',prefix+i+'_'+d,r,{fontSize:r[3],align:'center',visible:false});
  }
 }
 for(let d=0;d<3;d++)add('Text','PsFp'+d,[382+d*21.33333+origins.catalog[0],14.66667+origins.catalog[1],21.33333,21.33333],{fontSize:21.33333,align:'center'});
 add('Text','PsFpLabel',[326+origins.catalog[0],14.66667+origins.catalog[1],48,25],{text:'FP',fontSize:21.33333});
 const totals=c.skill_window_static.equipped_digits.leaves;
 for(let d=0;d<4;d++){const r=shift(totals.find(x=>x.path===`p_slot_total/p_total_no_${String(d).padStart(3,'0')}/d1`).rect_1280,origins.equipped);add('Text','PsTotal'+d,r,{fontSize:r[3],align:'center'});}
 add('Text','PsTotalSlash',shift(totals.find(x=>x.path==='p_slot_total/d1').rect_1280,origins.equipped),{text:'/',fontSize:17.0664,align:'center'});
 add('Text','PsTotalLabel',shift(totals.find(x=>x.path==='p_slot_total/p_text_slot/d1').rect_1280,origins.equipped),{text:'SP',fontSize:21.33333,align:'center'});
 add('Text','PsHintShadow',[41.5,677.5,1200,30],{fontSize:18,color:'#000000',align:'right',text:'W/S 고르기 · Q/E 목록 쪽 · Enter 장착/해제 · Backspace 통신부'});
 add('Text','PsHint',[40,676,1200,30],{fontSize:18,align:'right'});
 await applyPadDetailSource({repo,write,w,screen:'skill'});
 if(!validWidgetAsset(w))throw Error('Invalid Pad skill widget');await write('Assets/UI/PadSkillV4.hbwidget.json',w);await write('Assets/Data/v4_story/skill_layout.json',layout);return w;
}
