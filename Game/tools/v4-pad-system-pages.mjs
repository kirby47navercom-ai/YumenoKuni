import fs from 'node:fs/promises';
import path from 'node:path';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../engineCreate/prototype/ui-assets.js';
import {ownCharacterThemes} from './v4-own-character-themes.mjs';
export async function emitV4PadSystemPages({repo,write,body}){
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/pad_system_connection_contract.json'),'utf8')),g=c.cached_sfl_geometry;
 const find=(list,p)=>{const v=list.find(x=>x.path===p);if(!v)throw Error('Missing system source leaf '+p);return v;};
 const make=name=>{const w=createWidgetAsset(name);w.scaleMode='scale';w.scaleRule='fit';return w;};
 const add=(w,type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:30,color:'#ffffff',background:'#00000000',padding:0,radius:0,borderWidth:0,focusable:false,visible:true,...props});if(type==='Text'&&id.endsWith('Hint')){const s=structuredClone(n);s.id=id+'Shadow';s.name=s.id;s.slot.offset=[rect[0]+1.5,rect[1]+1.5,rect[2],rect[3]];s.slot.zIndex=1;s.properties.color='#000000';n.slot.zIndex=2;w.nodes.push(s);}w.nodes.push(n);};
 const save=async w=>{if(!validWidgetAsset(w))throw Error('Invalid system page '+w.name);await write('Assets/UI/'+w.name+'.hbwidget.json',w);};
 const source=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/pad_system_source/layout.json'),'utf8'));
 const asset=id=>'Assets/Art/ui/v3/pad_system_source/'+source.assets[id].file;
 for(const a of Object.values(source.assets))await write('Assets/Art/ui/v3/pad_system_source/'+a.file,await fs.readFile(path.join(repo,'ui/v4/pad_system_source',a.file)));
 const sourceImage=(w,id,key,rect=source.assets[key].rect)=>add(w,'Image',id,rect,{texture:asset(key),imageFit:'fill'});
 const layout={scope:'Source common-window/backlog/six-slot/detail/seven-theme-row geometry. Original source bitmaps/masks; own Korean type/physical keys and project save/unlock policies. Original LF routing, total manual slot count, load choice text/controller and preview thumbnails remain unclaimed.',manualSlots:30,confirm:{},backlog:{rows:[]},storage:{rows:[]},detail:{},theme:{rows:[],entries:[]}};
 for(const family of ['','load_'])for(const state of ['on','off']){
  const a=source.assets[family+'choice_'+state],raw=await fs.readFile(path.join(repo,'ui/v4/pad_system_source',a.file));
  await write('Assets/Art/ui/pad_'+family+'choice_'+state+'.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${a.rect[2]} ${a.rect[3]}" preserveAspectRatio="none"><image href="data:image/png;base64,${raw.toString('base64')}" width="${a.rect[2]}" height="${a.rect[3]}" preserveAspectRatio="none"/></svg>`);
 }

 {
  const w=make('CommonConfirmV4'),leaves=g.confirm_no.leaves;
  sourceImage(w,'CwSourceBack','confirm_background');
  layout.confirm.yes=find(leaves,'p_yes_on/_f_yes_on').rect_1280;layout.confirm.no=find(leaves,'p_no_on/_f_no_on').rect_1280;
  layout.confirm.noOff=find(leaves,'p_no_off/_f_no_off').rect_1280;
  for(const [id,r,label] of [['CwYes',layout.confirm.yes,'예'],['CwNo',layout.confirm.no,'아니오']])add(w,'Text',id,r,{text:label,align:'center'});
  layout.confirm.choices=[find(leaves,'i_choice_off_00/d1').rect_1280,find(leaves,'p_choise_00/i_choise/d1').rect_1280];
  for(let i=0;i<2;i++)add(w,'Image','CwChoice'+i,layout.confirm.choices[i],{texture:'Assets/Art/ui/pad_choice_off.svg',imageFit:'fill'});
  // Text remains above the source choice carriers.
  for(const id of ['CwYes','CwNo'])w.nodes.find(n=>n.id===id).slot.zIndex=2;
  layout.confirm.body=[1,2,3,6].map(i=>find(leaves,`p_message_text_${i}/_f_window_message_${i}`).rect_1280);
  add(w,'Text','CwBody',layout.confirm.body[1],{wrap:true,align:'center'});
  await save(w);
 }
 {
  const w=make('BacklogV4'),leaves=g.backlog_row1.leaves;
  sourceImage(w,'BlSourceBack','backlog_background');
  for(let i=0;i<4;i++){
   const n=String(i).padStart(3,'0'),r=find(leaves,`p_text_${n}/_f_text_${n}`).rect_1280,name=find(leaves,`p_chara_name_${n}/d1`).rect_1280,portrait=find(leaves,`p_chara_${n}/d1`).rect_1280;
   const plate=find(leaves,`p_name_base_off_${n}/i_name_bata/d1`).rect_1280;layout.backlog.rows.push({body:r,name,portrait,plate});
   sourceImage(w,'BlPlate'+i,'BlPlate'+i,plate);add(w,'Text','BlName'+i,name);
   add(w,'Image','BlFace'+i,portrait,{texture:'',imageFit:'contain'});
   add(w,'ScrollBox','BlViewport'+i,r);add(w,'Text','BlBody'+i,[0,0,880,100],{wrap:true},'BlViewport'+i);
  }
  add(w,'Text','BlHint',[40,677,1200,30],{fontSize:18,align:'right',text:'W/S 기록 · Q/E 쪽 · 휠 본문 · Backspace 돌아가기'});await save(w);
 }
 {
  const w=make('SaveSlotsV4'),leaves=g.save_load_wait0.leaves;
  sourceImage(w,'SvSourceBack','storage_background');
  layout.storage.title=find(leaves,'p_title/_f_st_save_load_title').rect_1280;add(w,'Text','SvTitle',layout.storage.title);
  add(w,'Text','SvPage',find(leaves,'p_tx_st_day/_f_st_day').rect_1280,{fontSize:26.66667,align:'right'});
  for(let i=0;i<6;i++){
   const n=String(i).padStart(3,'0'),chapter=find(leaves,`p_tx_chapter_${n}/_f_st_save_load_chapter_${n}`).rect_1280,date=find(leaves,`p_tx_date_${n}/_f_st_save_load_date_${n}`).rect_1280,icon=find(leaves,`p_icon_${String(i).padStart(2,'0')}/d1`).rect_1280;
   const parts=[1,2,3].map(d=>find(leaves,`i_tab_${n}/d${d}`).rect_1280);layout.storage.rows.push({chapter,date,icon,parts});
   for(let d=0;d<3;d++)sourceImage(w,'SvTab'+i+'_'+d,'SvTab'+i+'_'+d,parts[d]);
   add(w,'Text','SvNumber'+i,icon,{fontSize:38,align:'center'});add(w,'Text','SvChapter'+i,chapter,{fontSize:26.66667});add(w,'Text','SvDate'+i,date,{fontSize:26.66667});
  }
  layout.storage.active=source.assets.SvActive.rect;sourceImage(w,'SvActive','SvActive');
  add(w,'Text','SvHint',[40,685,1200,28],{fontSize:18,align:'right',text:'W/S 고르기 · Q/E 쪽 · Enter 확인 · Backspace 시스템'});
  // Original highlight owns an opaque inner plate; live slot ink must paint above it.
  w.nodes.find(n=>n.id==='SvActive').slot.zIndex=1;
  for(const node of w.nodes)if(node.type==='Text')node.slot.zIndex=10;
  await save(w);
 }
 {
  const w=make('LoadDetailV4'),leaves=g.load_header.leaves;
  sourceImage(w,'LdSourceBack','load_background');
  for(const [id,p,label]of[['LdTitle','p_title/_f_st_save_load_title','불러오기'],['LdGame','p_gametitle/_f_st_load_gametitle',''],['LdDate','p_date/_f_st_date',''],['LdDetail','p_detail/_f_st_date',''],['LdDateLabel','p_date_title/_f_st_date_title','저장 일시'],['LdDetailLabel','p_detail_title/_f_st_detail_title','위치'],['LdBody','p_load_text/_f_load_text','이 데이터를 불러올까요?'],['LdYes','p_00/_f_st_00','불러오기'],['LdNo','p_01/_f_st_01','돌아가기']]){
   const r=find(leaves,p).rect_1280;layout.detail[id]=r;add(w,'Text',id,r,{text:label,wrap:true,fontSize:id==='LdTitle'?30:26.66667,align:['LdYes','LdNo','LdBody'].includes(id)?'center':'left'});
  }
  layout.detail.choices=[find(leaves,'i_off_00/d1').rect_1280,find(leaves,'i_off_01/d1').rect_1280];
  for(let i=0;i<2;i++)add(w,'Image','LdChoice'+i,layout.detail.choices[i],{texture:'Assets/Art/ui/pad_load_choice_off.svg',imageFit:'fill'});
  for(const id of ['LdYes','LdNo'])w.nodes.find(n=>n.id===id).slot.zIndex=2;
  add(w,'Text','LdNumber',find(leaves,'p_icon/d1').rect_1280,{fontSize:60,align:'center'});await save(w);
 }
 {
  const w=make('PadThemeV4'),leaves=g.theme_row0.leaves;
  sourceImage(w,'ThSourceBack','theme_background');
  sourceImage(w,'ThActive','ThActive');layout.theme.active=source.assets.ThActive.rect;
  for(let i=0;i<7;i++){
   const n=String(i).padStart(3,'0'),r=find(leaves,`p_kisekae_text_${n}/_f_kisekae_text_${n}`).rect_1280;layout.theme.rows.push(r);add(w,'Text','ThRow'+i,r);
   for(let d=0;d<2;d++){const p=`p_number_${n}/p_${d===0?'001':'000'}_${n}/d1`,r=find(leaves,p).rect_1280;add(w,'Text','ThNumber'+i+'_'+d,r,{fontSize:17.06641,align:'center'});}
  }
  layout.theme.preview=find(leaves,'p_image/d1').rect_1280;add(w,'Image','ThPreview',layout.theme.preview,{texture:'',imageFit:'contain'});
  add(w,'Text','ThPreviewLabel',find(leaves,'p_image_text/p_image_tx/d1').rect_1280,{text:'미리보기',fontSize:17,align:'right'});
  const desc=find(leaves,'p_kisekae_notice_text/_f_kisekae_notice').rect_1280;add(w,'Text','ThBody',desc,{wrap:true});
  const labels=['기본','기본 · 보라',...Array.from({length:16},(_,i)=>'인물 테마 '+String(i+1).padStart(2,'0')),'학급 재판','남국','모노쿠마','실루엣','스크린','우주','유적','색종이','흑백','하이테크','장미','네온 · 파랑','네온 · 분홍','네온 · 초록','종이 · 파랑','종이 · 분홍','종이 · 회색','노이즈 · 녹색','노이즈 · 노랑','고서'];
  const ownThemes=await ownCharacterThemes({repo,contract:c});
  for(const row of c.provided_bank_check.theme_backgrounds.resources.sort((a,b)=>a.table_row-b.table_row)){
   const raw=await fs.readFile(row.path),name='type_'+String(row.type_id).padStart(3,'0');
   const own=ownThemes.get(row.type_id);
   await write('Assets/Art/ui/v3/themes/'+name+'.svg',own?.svg||`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080"><image href="data:image/png;base64,${raw.toString('base64')}" width="1920" height="1088" preserveAspectRatio="none"/></svg>`);
   layout.theme.entries.push({saveNo:row.save_no,type:row.type_id,name:own?.name||labels[row.type_id],image:'Assets/Art/ui/v3/themes/'+name+'.svg',available:true,...own?{ownContent:true,sourceCarrier:own.sourceCarrier??null}: {}});
  }
  add(w,'Text','ThHint',[40,677,1200,30],{fontSize:18,align:'right',text:'W/S 고르기 · Q/E 쪽 · Enter 적용 · Backspace 시스템'});await save(w);
 }
 // Menu headers are separate from the chosen background, preserving the
 // supplied default header pixels and all their existing settled positions.
 for(const key of ['map','bullet','gift','card','rules','option']){
  const source=await fs.readFile(path.join(repo,'ui/v3_authorized/pad_home/'+key+'.svg'),'utf8');
  const overlay=source.replace(/(<svg[^>]*>)<image[^>]*\/>/,'$1');if(overlay===source)throw Error('Missing supplied menu background layer');await write('Assets/Art/ui/v3/pad_home/'+key+'_overlay.svg',overlay);
 }
 await write('Assets/Data/v4_story/system_pages_layout.json',layout);return layout;
}
