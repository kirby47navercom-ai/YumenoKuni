import fs from'node:fs/promises';import path from'node:path';import{createWidgetNode}from'../Game/engineCreate/prototype/ui-assets.js';
export async function applyMapOptionsSource({repo,write,w,screen}){
 const dir=path.join(repo,'ui/v4/map_options_source'),m=JSON.parse(await fs.readFile(path.join(dir,'layout.json'),'utf8'));
 const emit=async(name,row)=>{const asset='Assets/Art/ui/map_options_source/'+name+'.svg',b=await fs.readFile(path.join(dir,row.file)),r=row.rect;await write(asset,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${r[2]} ${r[3]}"><image width="${r[2]}" height="${r[3]}" href="data:image/png;base64,${b.toString('base64')}"/></svg>`);return asset;};
 for(const[id,row]of Object.entries(m.bindings[screen])){const n=w.nodes.find(n=>n.id===id);if(!n)throw Error('Missing exact Map/options binding '+id);n.type='Image';n.slot.offset=row.rect;Object.assign(n.properties,{text:'',texture:await emit(screen+'_'+id,row),imageFit:'fill',background:'#00000000'});}
 const extra=async(key,id,parent,z)=>{const row=m.extra[key],n=createWidgetNode('Image',id,parent);n.name=id;n.slot.offset=row.rect;n.slot.zIndex=z;Object.assign(n.properties,{texture:await emit(key,row),imageFit:'fill',color:'#ffffff',background:'#00000000',padding:0,radius:0,borderWidth:0,focusable:false});w.nodes.push(n);};
 if(screen==='map'){await extra('map_region','MpRegionChrome','root',1);for(const n of w.nodes)if(['MpArea','MpPrev','MpNext','MpPlaceTab','MpStudentTab'].includes(n.id))n.slot.zIndex=2;}
 else{await extra('options_notice','OptionsNoticeChrome','OptionsRoot',0);for(const n of w.nodes)if(n.type==='Text')n.slot.zIndex=2;const p=w.nodes.find(n=>n.id==='DisplayConfirm');p.properties.background='#00000000';await extra('display_confirm','DisplayConfirmPlate','DisplayConfirm',-1);}
 await write('Assets/Data/v4_story/'+screen+'_chrome_source.json',{sourceDescription:m.source,bindings:m.bindings[screen]});
}
