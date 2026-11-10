import{applyPadDetailSource}from'../../tools/render_pad_detail_source_ui.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../engineCreate/prototype/ui-assets.js';
export async function emitV4PadReportUI({repo,write,body}){
 const ref=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/pad_report_gift_leaf_followup.json'),'utf8')).report;
 const contrast=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/pad_theme_contrast_contract.json'),'utf8'));
 const w=createWidgetAsset('PadReportV4');w.scaleMode='scale';w.scaleRule='fit';
 const add=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;const {zIndex=0,...properties}=props;n.slot.zIndex=zIndex;Object.assign(n.properties,{text:'',font:body,fontSize:30,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:true,...properties});w.nodes.push(n);};
 const character=ref.character.leaves,strip=ref.character_switch_strip.leaves;
 const rect=p=>character.find(x=>x.path===p).rect_1280;
 // Reuse the source profile and first-record page carriers. Own FTE records
 // paginate inside the latter; later original cumulative rank pages are not
 // mislabeled as our independent FTE pages. Source bitmap bodies are supplied
 // by applyPadDetailSource, with these legacy IDs kept for runtime compatibility.
 const bodyPanels={};
 for(const [key,state]of Object.entries(contrast.report_page_panels)){
  bodyPanels[key]=state.panels.map(p=>({rect:p.rect_1280,alpha:p.alpha_product,visible:p.source_visible}));
 }
 for(let i=0;i<3;i++)add('Panel','PrBodyPlate'+i,[0,0,1,1],{background:'#000000',radius:0,borderWidth:0,visible:false});
 // Source standing, full-width name band and sixteen narrow switch portraits.
 add('Image','PrStanding',rect('p_chara_image_000/d1'),{texture:'',imageFit:'contain',zIndex:10});
 for(const [id,p,background] of [['PrNamePlate','i_bg/d1','#00000099'],['PrNameTop','i_beta_000/d1','#000000'],['PrNameBottom','i_beta_001/d1','#000000']])add('Panel',id,rect(p),{background});
 add('Text','PrName',rect('p_name_tx_000/d1'),{fontSize:48});
 add('Image','PrAffinity',rect('p_kizuna/d1'),{texture:'',imageFit:'contain'});
 add('Panel','PrStrip',strip.find(x=>x.path==='i_base/d1').rect_1280,{background:'#000000d9'});
 for(let i=0;i<16;i++){
  const r=strip.find(x=>x.path===`p_kirikae_chara_${String(i).padStart(3,'0')}/d1`).rect_1280;
  add('Image','PrActor'+i,r,{texture:'',imageFit:'contain',zIndex:20});
  add('Panel','PrActorLine'+i,[r[0],r[1]+r[3]-3,r[2],3],{background:'#ffffff',visible:false,zIndex:20});
 }
 const profile=ref.message_pages[0].visible_text_leaves;
 for(let i=0;i<8;i++)for(const [prefix,key] of [['PrLabel','p_c_'],['PrValue','p_a_']]){
  const r=profile.find(x=>x.path.startsWith(key+String(i).padStart(3,'0')+'/'));
  add('Text',prefix+i,r.rect_1280,{fontSize:30,wrap:false});
 }
 const memo=ref.message_pages[1].visible_text_leaves;
 add('Text','PrSkillEntry',[152.66667,390.66667,240,46.66667],{text:'스킬',fontSize:30,visible:false});
 add('Text','PrPageLabel',memo[0].rect_1280,{visible:false});add('Text','PrPageValue',memo[1].rect_1280,{visible:false,align:'right'});
 add('ScrollBox','PrMemoViewport',memo[2].rect_1280,{visible:false});
 add('Text','PrMemo',[0,0,600,320],{wrap:true},'PrMemoViewport');
 add('Text','PrHintShadow',[41.5,677.5,1200,30],{fontSize:18,align:'right',color:'#000000',zIndex:49});
 add('Text','PrHint',[40,676,1200,30],{fontSize:18,align:'right',zIndex:50});
 await applyPadDetailSource({repo,write,w,screen:'report'});
 if(!validWidgetAsset(w))throw Error('Invalid Pad report widget');await write('Assets/UI/PadReportV4.hbwidget.json',w);
 // Eight basic, non-ability fields from the existing authored character sheet.
 // Magical abilities and private backstory are never copied to this data page.
 const chars=JSON.parse(await fs.readFile(path.join(repo,'data/characters.json'),'utf8'));
 const order=['mio','rei','sora','ken','nana','riku','akari','yuu','koto','satsuki','taiga','rin','sho','ai','haruka','kaede'];
 const items={};for(let i=0;i<16;i++){
  const f=chars[i].fields,physical=(f['나이 · 키 · 체중 · 신발']||'').split('·').map(x=>x.trim()),birth=(f['생일 · 혈액형']||'').split('·').map(x=>x.trim());
  // Master-sheet editorial notes are not in-world profile values.
  const blood=birth[1]?.match(/^(?:AB|A|B|O)형/)?.[0]||'미확인',birthday=birth[0]?.match(/\d+월\s*\d+일/)?.[0]||'미확인';
  items[order[i]]={name:chars[i].heading.split(' (')[0].replace(/ —.*/,''),labels:['나이','키','체중','혈액형','생일','좋아하는 것','싫어하는 것','지망'],values:[physical[0]||'',physical[1]||'',physical[2]||'',blood,birthday,f['좋아하는 것']||'',f['싫어하는 것']||'',f['지망(꿈)']||'']};
 }
 const widths=Array.from({length:8},(_,i)=>profile.find(x=>x.path.startsWith('p_a_'+String(i).padStart(3,'0')+'/')).rect_1280[2]);
 const metrics=JSON.parse(execFileSync('python',['-X','utf8','-c',`import json,sys;from PIL import ImageFont;p=json.load(sys.stdin);f=ImageFont.truetype(p['font'],300);print(json.dumps({k:[min(30,p['widths'][i]*.97/(f.getlength(v)/300)) if v else 30 for i,v in enumerate(row['values'])] for k,row in p['items'].items()}))`],{input:JSON.stringify({font:path.join(repo,'fonts/pretendard/Pretendard-Medium.otf'),items,widths}),encoding:'utf8'}));
 for(const [id,values] of Object.entries(metrics)){if(Math.min(...values)<20)throw Error('Profile needs a readable long-value layout: '+id);items[id].fontSizes=values;}
 await write('Assets/Data/v4_story/report_layout.json',{strip:strip.filter(x=>/^p_kirikae_chara_/.test(x.path)).map(x=>x.rect_1280),bodyPanels});
 await write('Assets/Data/v4_story/report_profiles.json',{items,scope:'Existing physical/preferences sheet only; no ability, family, hidden history or old relationship memo.'});return w;
}
