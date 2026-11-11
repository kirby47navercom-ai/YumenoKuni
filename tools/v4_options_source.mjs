import{applyMapOptionsSource}from'./render_map_options_source_ui.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../Game/engineCreate/prototype/ui-assets.js';

// Static SFL row ink/RGBA and supplied Korean raster substitutions, with the
// original PC kind order0..9,12. The project has no optional voice packs.
export async function emitSourceOptions({repo,write}){
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/options_ui_contract.json'),'utf8'));
 const raster=new Map();for(const r of c.provided_rasters.resources)raster.set(r.source_image_id,(await fs.readFile(path.join(repo,r.path))).toString('base64'));
 const canvas=[63.33333,79.33333,1153.34147,60];
 const render=async(style,on,value)=>{
  const template=c.row_templates[`fl_${(style==='fps'||style==='value')?'one':style.startsWith('two_')?'two':style}_${on?'on':'off'}`];let shapes='',filters='',i=0;
  for(const leaf of template.composed_first_visible_row_leaves){
   if(leaf.image_id===undefined||leaf.alpha_product===0)continue;
   const p=leaf.path;if((style==='fps'||style==='value')&&(p==='i_shokika/d1'||p==='p_one_text/d1'))continue;
   const gauge=p.match(/p_(on|off)_bgm_vol_(\d+)/);
   if(gauge&&((gauge[1]==='on')!==on||Number(gauge[2])>=value))continue;
   const target=p.match(/p_(on|off)_target_(\d+)/);
   if(target&&((target[1]==='on')!==on||Number(target[2])!==value))continue;
   const choice=p.match(/^p_on_(left|right)\//);if(choice&&((choice[1]==='left')!==(value===1)))continue;
   const choiceText=p.match(/^p_(on|off)_(left|right)_text\//);
   if(choiceText){const selected=(choiceText[2]==='left')===(value===1);if(choiceText[1]==='on'&&!selected)continue;if(choiceText[1]==='off'&&selected&&on)continue;}
   let image=leaf.image_id;const replacement={two_invert:[1,2],two_controls:[0,3],two_map:[9,8]}[style];if(choiceText&&replacement)image=replacement[choiceText[2]==='left'?0:1];
   const q=leaf.quad_1280,a=q[1][0]-q[0][0],b=q[1][1]-q[0][1],d=q[3][0]-q[0][0],e=q[3][1]-q[0][1];
   const m=leaf.composed_multiply_rgba,v=leaf.composed_add_rgba,id='f'+i++;
   filters+=`<filter id="${id}" x="-2%" y="-2%" width="104%" height="104%" color-interpolation-filters="sRGB"><feComponentTransfer>${['R','G','B','A'].map((channel,j)=>`<feFunc${channel} type="linear" slope="${m[j]}" intercept="${v[j]}"/>`).join('')}</feComponentTransfer></filter>`;
   shapes+=`<use href="#r${image}" transform="matrix(${a} ${b} ${d} ${e} ${q[0][0]-canvas[0]} ${q[0][1]-canvas[1]})" filter="url(#${id})"/>`;
  }
  if(style==='fps')shapes+=`<path d="M${657+value*173.11111} 49h110" stroke="${on?'#000000':'#ffffff'}" stroke-width="3"/>`;
  const defs=[...raster].map(([id,png])=>`<image id="r${id}" width="1" height="1" preserveAspectRatio="none" href="data:image/png;base64,${png}"/>`).join('');
  await write(`Assets/Art/ui/options/v3row/${style}_${on?'on':'off'}_${value}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${canvas[2]} ${canvas[3]}" preserveAspectRatio="none"><defs>${defs}${filters}</defs>${shapes}</svg>`);
 };
 for(const on of [false,true])for(const style of ['guage','slowfast','two','two_invert','two_controls','two_map','fps','value','one'])for(let value=0;value<(style==='guage'?11:style==='slowfast'?5:style.startsWith('two')?2:style==='fps'?3:1);value++)await render(style,on,value);
 const w=createWidgetAsset('W_OptionsV4');w.scaleMode='scale';w.scaleRule='fit';
 const add=(type,id,rect,properties={},parent='OptionsRoot')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',visible:true,focusable:false,color:'#ffffff',background:'#00000000',font:'Assets/Fonts/pretendard/Pretendard-Medium.otf',fontSize:30,padding:0,radius:0,borderWidth:0,...properties});w.nodes.push(n);};
 add('Panel','OptionsRoot',[-640,-360,1280,720],{visible:false},'root');w.nodes.find(n=>n.id==='OptionsRoot').slot.anchors=[.5,.5,.5,.5];
 const main=c.main_geometry.leaves,leaf=p=>main.find(x=>x.path===p);
 for(const [id,p,bg]of[['OptionsListShade','i_icon_base_beta/d1','#000000e5'],['OptionsNoticeShade','i_setumei_base_beta/d1','#000000b2']])add('Panel',id,leaf(p).rect_1280,{background:bg});
 for(let i=0;i<4;i++){
  const r=leaf(`p_line_waku_${String(i).padStart(3,'0')}/i_line_000/d1`).rect_1280;
 add('Image','OptionsFrame'+i,r,{texture:'Assets/Art/ui/options/frame'+i+'.svg',imageFit:'fill'});
 }
 const rows=[];
 for(let i=0;i<8;i++){
  const dy=c.coordinate_contract.row_origins_1280[i][1]-canvas[1],r=[canvas[0],canvas[1]+dy,canvas[2],canvas[3]],label=[...c.key_first_row_geometry.label_text];label[1]+=dy;rows.push({row:r,label});
  add('Image','Row'+i,r,{texture:'Assets/Art/ui/options/v3row/guage_off_0.svg',imageFit:'fill'});add('Text','Label'+i,label);for(let f=0;f<3;f++)add('Text','FPS'+i+'_'+f,[688.66667+f*173.11111,r[1]+10,173.11111,40],{text:String([30,60,120][f]),fontSize:28,align:'center',visible:false});
  add('Text','Value'+i,[688.66667,r[1]+10,519.33333,40],{fontSize:28,align:'center',visible:false});
 }
 for(const [id,p,bg]of[['OptionsScrollBase','i_scroll_base/d1','#000000'],['OptionsScrollTrack','i_scroll_yohaku_base/d1','#ffffff44'],['OptionsScroll','p_scroll/d1','#ffffff']])add('Panel',id,leaf(p).rect_1280,{background:bg});
 add('Text','Description',c.main_geometry.notice_text_rect,{wrap:true});
 add('Text','ControlsShadow',[41.5,677.5,1200,30],{fontSize:18,align:'right',color:'#000000',text:'휠 / 방향키 항목 · 좌우 변경 · Enter 결정 · Esc / Backspace 돌아가기'});
 add('Text','Controls',[40,676,1200,30],{fontSize:18,align:'right',text:'휠 / 방향키 항목 · 좌우 변경 · Enter 결정 · Esc / Backspace 돌아가기'});
 add('Panel','DisplayConfirm',[340,240,600,220],{background:'#090716fa',visible:false},'OptionsRoot');
 add('Text','DisplayQuestion',[30,25,540,90],{fontSize:28,wrap:true,align:'center'},'DisplayConfirm');
 for(const [id,x,label]of [['DisplayKeep',40,'유지'],['DisplayRevert',320,'되돌리기']]){add('Image',id,[x,130,240,50],{texture:'Assets/Art/ui/v3/choice_off.svg',imageFit:'fill'},'DisplayConfirm');add('Text',id+'Label',[x,135,240,40],{text:label,fontSize:26,align:'center'},'DisplayConfirm');}
 await applyMapOptionsSource({repo,write,w,screen:'options'});
 if(!validWidgetAsset(w))throw Error('Invalid source options widget');await write('Assets/UI/OptionsV4.hbwidget.json',w);
 await write('Assets/Data/options_layout.json',{visible:8,total:15,kinds:[0,1,2,3,4,5,6,7,8,9,'frameRate','windowMode','resolution','bindings',12],rows,scroll:leaf('p_scroll/d1').rect_1280,sourceControl:c.key_first_row_geometry.control_frame,scope:'Eight source row positions/RGBA/provided Korean labels. Source PC kinds0..9,12; original numeric defaults and separate consumers. Own voice files/packs unavailable so preview/language reload not reconstructed; PC bindings, reveal update time base and disk policy are own adaptations. Original complete material/animation identity unclaimed.'});
 return w.nodes.length;
}
