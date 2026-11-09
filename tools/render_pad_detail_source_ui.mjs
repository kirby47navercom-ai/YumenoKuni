// Embed exact family RGBA composition; do not introduce a second UI controller.
import fs from 'node:fs/promises';
import path from 'node:path';
import{createWidgetNode}from'../../engineCreate/prototype/ui-assets.js';
export async function applyPadDetailSource({repo,write,w,screen}){
 const dir=path.join(repo,'ui/v4/pad_detail_source'),m=JSON.parse(await fs.readFile(path.join(dir,'layout.json'),'utf8'));
 const prefix='Assets/Art/ui/pad_detail_source/',states={};
 const blackFilter='<defs><filter id="ink" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0"/></filter></defs>';
 const emit=async(row,name,black=false)=>{const file=prefix+name+'.svg',png=await fs.readFile(path.join(dir,row.file));const r=row.rect;await write(file,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${r[2]} ${r[3]}">${black?blackFilter:''}<image${black?' filter="url(#ink)"':''} width="${r[2]}" height="${r[3]}" href="data:image/png;base64,${png.toString('base64')}"/></svg>`);return{...row,asset:file};};
 for(const[id,row]of Object.entries(m.bindings[screen])){
  const n=w.nodes.find(n=>n.id===id);if(!n)throw Error('Missing Pad source target '+screen+':'+id);
  const out=await emit(row,screen+'_'+id);n.type='Image';n.slot.offset=row.rect;Object.assign(n.properties,{texture:out.asset,text:'',background:'#00000000',imageFit:'fill'});
 }
 for(const[key,row]of Object.entries(m.states))if(key.startsWith(screen+'_')||key.startsWith(screen==='report'?'affinity_':screen==='gift'?'techou_present_icon_US_':screen==='skill'?'techou_skill_list_US_':screen==='rules'?'techou_kousoku_text_':'__unused'))states[key]=await emit(row,key);
 if(screen==='skill'||screen==='gift')for(const[key,row]of Object.entries(m.states))if(key.startsWith(screen==='skill'?'techou_skill_list_US_digit_':'techou_present_icon_US_digit_'))states[key+'_black']=await emit(row,key+'_black',true);
 const digitFamily=screen==='skill'?'techou_skill_list_US':screen==='rules'?'techou_kousoku_text':screen==='gift'?'techou_present_icon_US':'';
 const numeric=screen==='skill'?/^(?:PsCost\d+_\d+|PsEquippedCost\d+_\d+|PsTotal\d+|PsFp\d+)$/ :screen==='rules'?/^KrNumber\d+$/ :screen==='gift'?/^PgDigit\d+_\d+$/ :/^__none$/;
 if(digitFamily)for(const n of w.nodes)if(numeric.test(n.id)){n.type='Image';Object.assign(n.properties,{text:'',texture:states[digitFamily+'_digit_0'].asset,imageFit:'fill',color:'#ffffff',background:'#00000000'});}
 // Existing runtime IDs/ports remain stable. Obsolete vector strokes are disabled.
 const obsolete=screen==='skill'?/^PsFrame/:screen==='rules'?/^KrFrame/:screen==='report'?/^PrActorLine/:/^__none$/;
 for(const n of w.nodes)if(obsolete.test(n.id)){n.properties.visible=false;n.properties.texture='';n.properties.background='#00000000';}
 if(screen==='report'){
  for(const n of w.nodes)if(/^PrLabel/.test(n.id))n.properties.color='#000000';
  for(const n of w.nodes)if(/^PrBodyPlate/.test(n.id))n.properties.background='#00000000';
  const n=createWidgetNode('Image','PrSourceBody','root');n.name=n.id;n.slot.offset=[0,0,1280,720];n.slot.zIndex=-1;Object.assign(n.properties,{texture:states.report_profile.asset,imageFit:'fill',background:'#00000000',color:'#ffffff',padding:0,radius:0,borderWidth:0,focusable:false,visible:true});w.nodes.push(n);
  for(let i=0;i<=5;i++){const p=states['affinity_'+i];await write(`Assets/Art/ui/pad_affinity_${i}.svg`,await fs.readFile(path.join(dir,p.file)).then(b=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><image width="128" height="128" href="data:image/png;base64,${b.toString('base64')}"/></svg>`));}
 }
 if(screen==='evidence')for(const[key,file]of[['off','pad_evidence_row'],['on','pad_evidence_row_on']]){const p=states['evidence_row_'+key],b=await fs.readFile(path.join(dir,p.file));await write(`Assets/Art/ui/${file}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${p.rect[2]} ${p.rect[3]}"><image width="${p.rect[2]}" height="${p.rect[3]}" href="data:image/png;base64,${b.toString('base64')}"/></svg>`);}
 if(screen==='gift'){
  w.nodes.find(n=>n.id==='PgTitle').properties.color='#000000';
  const source=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/pad_detail_source/layout.json'),'utf8')).techou_present_US.states.fl_wait;
  for(const[id,prefix,res]of[['PgNumber','p_no/p_number_tx/','no_US.png'],['PgQuantity','p_no/p_kakeru/','number_kakeru.png'],['PgComplete','p_complete/10','number_per.png']]){
   const leaf=source.find(r=>r.path.startsWith(prefix)),b=await fs.readFile(path.join(repo,'ui/v3_authorized/pad_detail_source/techou_present_US',res+'.png')),n=w.nodes.find(n=>n.id===id),asset=prefixPath(id);
   await write(asset,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${leaf.rect[2]} ${leaf.rect[3]}">${id==='PgComplete'?'':blackFilter}<image${id==='PgComplete'?'':' filter="url(#ink)"'} width="${leaf.rect[2]}" height="${leaf.rect[3]}" href="data:image/png;base64,${b.toString('base64')}"/></svg>`);
   n.type='Image';n.slot.offset=leaf.rect;Object.assign(n.properties,{text:'',texture:asset,imageFit:'fill',background:'#00000000'});
  }
  function prefixPath(id){return 'Assets/Art/ui/pad_detail_source/gift_'+id+'.svg';}
  for(const[key,base]of[['Number','p_no/p_item_number_'],['Quantity','p_no/p_item_'],['Complete','p_complete/p_comp_number_']])for(let d=0;d<3;d++){
   const leaf=source.find(r=>r.path.startsWith(base+String(d).padStart(3,'0')+'/')),n=createWidgetNode('Image','Pg'+key+'Digit'+d,'root');n.name=n.id;n.slot.offset=leaf.rect;Object.assign(n.properties,{texture:states['techou_present_icon_US_digit_0'+(key==='Complete'?'':'_black')].asset,imageFit:'fill',color:'#ffffff',background:'#00000000',padding:0,radius:0,borderWidth:0,focusable:false});w.nodes.push(n);
  }
 }
 if(screen==='gift')for(const[name,key]of[['base','gift_base'],['selected','gift_selected'],['unknown','gift_unknown']]){const b=await fs.readFile(path.join(dir,states[key].file));await write(`Assets/Art/ui/pad_gift_${name}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><image width="256" height="256" href="data:image/png;base64,${b.toString('base64')}"/></svg>`);}
 if(screen==='skill')for(const n of w.nodes)if(/^PsPanel/.test(n.id))n.slot.zIndex=-2;
 if(screen==='skill')for(const side of['catalog','equipped']){const n=createWidgetNode('Image','PsSourceFocus'+side,'root');n.name=n.id;n.slot.offset=states['skill_'+side+'_0'].rect;n.slot.zIndex=-1;Object.assign(n.properties,{texture:states['skill_'+side+'_0'].asset,imageFit:'fill',background:'#00000000',color:'#ffffff',padding:0,radius:0,borderWidth:0,focusable:false,visible:false});w.nodes.push(n);}
 await write(`Assets/Data/v4_story/${screen}_source_ui.json`,{scope:m.source,states,bindings:m.bindings[screen]});return states;
}
