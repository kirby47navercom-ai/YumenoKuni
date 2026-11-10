import{applyPadDetailSource}from'../../tools/render_pad_detail_source_ui.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../engineCreate/prototype/ui-assets.js';
export async function emitV4PadRulesUI({repo,write,body,legacyRules}){
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/rules_book_ui_contract.json'),'utf8'));
 const leaves=c.five_representative_carriers.text_overlay.leaves,cover=c.five_representative_carriers.cover_US.leaves;
 const rect=(list,p)=>list.find(x=>x.path===p).rect_1280;
 const w=createWidgetAsset('PadRulesV4');w.scaleMode='scale';w.scaleRule='fit';
 const add=(type,id,r,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=r;Object.assign(n.properties,{text:'',font:body,fontSize:30,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:true,...props});w.nodes.push(n);};
 // Original publication/text/number roles are retained. Supplied menu emblem
 // and approved own host are adapted illustrations, not recovered rule pixels.
 add('Image','KrCover',rect(cover,'p_koushou/d1'),{texture:'Assets/Art/ui/pad_rules_cover.svg',imageFit:'contain'});
 add('Panel','KrCoverTitleBand',rect(cover,'p_title_base/_a_title_base_000_DXT1/d1'),{background:'#08080dcc'});
 add('Text','KrCoverTitle',rect(cover,'p_kousoku_title/_f_kousoku_title'),{text:'유메노쿠니 교칙',align:'center'});
 add('Image','KrFigure',[473.63333,150.26667,375.45834,375.45833],{texture:'Assets/Art/v4/lappy.webp',imageFit:'contain',visible:false});
 // Paint sparse own ink inside the actual three component carriers; their
 // opaque bounding rectangles would incorrectly flatten overlapping pieces.
 add('Panel','KrBodyShade',[139.33333,511.33333,994.65756,170.66667],{background:'#08080dc9',visible:false});
 for(let i=0;i<3;i++)add('Image','KrFrame'+i,[0,0,1,1],{texture:'',visible:false});
 // Own long public notices keep the original body viewport and readable
 // source font; wheel scrolling is an explicit own-content adaptation.
 const viewport=rect(leaves,'p_kousoku_text/_f_kousoku_text');
 add('ScrollBox','KrBodyViewport',viewport,{visible:false});
 add('Text','KrBody',[0,0,880,viewport[3]],{wrap:true,align:'center'},'KrBodyViewport');
 add('Panel','KrNumberBase',rect(leaves,'d18'),{background:'#08080ddd',visible:false});
 for(let i=0;i<4;i++)add('Text','KrNumber'+i,rect(leaves,`p_number_${String(i).padStart(3,'0')}/d1`),{fontSize:23.46615,align:'center',visible:false});
 add('Text','KrSlash',rect(leaves,'p_number_slash/d1'),{text:'/',fontSize:23.46615,align:'center',visible:false});
 for(const [kind,source,flip] of [['Next','000',false],['Prev','001',true]])for(let i=0;i<2;i++){
  const name='pad_rules_arrow_'+kind;
  add('Image','Kr'+kind+i,rect(leaves,`p_yazirusi_${source}/i_yazirusi_${String(i).padStart(3,'0')}/d1`),{texture:`Assets/Art/ui/${name}.svg`,imageFit:'contain',visible:false});
 }
 add('Text','KrHintShadow',[41.5,687.5,1200,26],{fontSize:18,color:'#000000',align:'right',text:'W/S 페이지 · 휠 본문 · Backspace 돌아가기'});
 add('Text','KrHint',[40,686,1200,26],{fontSize:18,align:'right',text:'W/S 페이지 · 휠 본문 · Backspace 돌아가기'});
 await applyPadDetailSource({repo,write,w,screen:'rules'});
 if(!validWidgetAsset(w))throw Error('Invalid Pad rules widget');await write('Assets/UI/PadRulesV4.hbwidget.json',w);
 const records=JSON.parse(await fs.readFile(path.join(repo,'data/presentation/v4_scenes.json'),'utf8')).publicRecords.records;
 const order=Object.keys(records);if(order.length!==new Set(order).size)throw Error('Duplicate public rule id');
 const texts=Object.fromEntries(Object.entries(records).map(([id,r])=>[id,r.rows.join('\n')]));for(const r of legacyRules)texts['legacy:'+r.no]=r.text;
 const bodies=JSON.parse(execFileSync('python',['-X','utf8',path.join(repo,'tools/format_v4_rules_body.py')],{input:JSON.stringify(texts),encoding:'utf8'}));
 await write('Assets/Data/v4_story/rules_layout.json',{order,bodies,body:viewport,cover:rect(cover,'p_koushou/d1'),coverNext:[0,1].map(i=>rect(cover,`p_yazirusi_000/i_yazirusi_${String(i).padStart(3,'0')}/d1`)),figure:[473.63333,150.26667,375.45834,375.45833],transitionSeconds:.24,scope:'Source layout and bounded publication reader. Own PC mapping, 0.24-second directional transition, readable wheel viewport, source rule-reader seal/chrome and own approved host; original illustration and full transition timing equality is not claimed.'});
 return w;
}
