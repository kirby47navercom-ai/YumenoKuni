import fs from 'node:fs/promises';
import path from 'node:path';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../../../engineCreate/prototype/ui-assets.js';
export async function emitV4PadSystemUI({repo,write,body}){
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/pad_system_ui_contract.json'),'utf8'));
 const w=createWidgetAsset('PadSystemV4');w.scaleMode='scale';w.scaleRule='fit';
 const add=(type,id,rect,props={})=>{const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:30,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:true,...props});w.nodes.push(n);};
 const leaf=p=>{const x=c.leaves.find(x=>x.path===p);if(!x)throw Error('Missing source system leaf '+p);return x;};
 const source=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/pad_system_source/layout.json'),'utf8'));
 const asset=id=>'Assets/Art/ui/v3/pad_system_source/'+source.assets[id].file;
 for(const a of Object.values(source.assets))await write('Assets/Art/ui/v3/pad_system_source/'+a.file,await fs.readFile(path.join(repo,'ui/v4/pad_system_source',a.file)));
 const sourceImage=(id,key,rect=source.assets[key].rect)=>add('Image',id,rect,{texture:asset(key),imageFit:'fill'});
 sourceImage('SySourceBack','system_background');
 const labels=['대화 기록','저장','불러오기','환경설정','테마','메인 메뉴'];
 const layout={entries:[],active:[],notice:leaf('p_notice_text/_f_system_notice').rect_1280,lift:c.selection_lift_1280,scope:'Original six-column bitmap, affine, masks and selected states; own Korean text/save behavior. Original GPU shader and intro motion parity unclaimed.'};
 for(let i=0;i<6;i++){
  const key=c.entries[i],n=String(i).padStart(3,'0'),base=leaf(`p_icon_base_${n}/i_icon_beta/depth1`).rect_1280;
  const icon=c.leaves.find(x=>x.path.startsWith('p_icon_'+key+'/')&&x.path.includes('_color/'))?.rect_1280;
  const title=leaf(`p_title_${key}/_a_title_${key}_DXT1/depth1`).rect_1280;
  if(!icon)throw Error('Missing source system icon carrier '+key);
  const unselected=r=>[r[0],r[1]+(i===0?c.selection_lift_1280:0),r[2],r[3]];
  const state=source.systemStates[i];
  const entry={base:unselected(base),icon:unselected(icon),title:unselected(title),...Object.fromEntries(Object.entries(state).map(([k,v])=>[k,asset(v)]))};layout.entries.push(entry);
  sourceImage('SyBase'+i,state.baseOff,entry.base);sourceImage('SyIcon'+i,state.iconOff,entry.icon);
  add('Text','SyLabel'+i,entry.title,{text:labels[i],align:'center'});
 }
 for(let i=0;i<4;i++){const id='SyActive'+i;sourceImage(id,id);layout.active.push(source.assets[id].rect);}
 add('Text','SyNoticeTitle',leaf('p_notice_tx/depth1').rect_1280,{text:'안내',fontSize:21.33333});
 add('Text','SyNotice',layout.notice,{wrap:true});
 add('Text','SyHintShadow',[41.5,677.5,1200,30],{fontSize:18,color:'#000000',align:'right',text:'A/D 고르기 · Enter 실행 · Backspace 돌아가기'});
 add('Text','SyHint',[40,676,1200,30],{fontSize:18,align:'right',text:'A/D 고르기 · Enter 실행 · Backspace 돌아가기'});
 if(!validWidgetAsset(w))throw Error('Invalid Pad system widget');await write('Assets/UI/PadSystemV4.hbwidget.json',w);await write('Assets/Data/v4_story/system_layout.json',layout);return w;
}
