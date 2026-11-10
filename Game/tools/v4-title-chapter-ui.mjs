import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {sourceRows,sourceSvg} from './v3-source-svg.mjs';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../engineCreate/prototype/ui-assets.js';

export async function emitTitleChapterUI({repo,write,copy,body,head}){
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/title_chapter_remaining_contract.json'),'utf8'));
 const base='Assets/Art/ui/v3/title_chapter/',pngs=new Map(),receipts=[];
 for(const g of c.geometry)for(const t of g.texture_table2)if(t.authorized_png&&!pngs.has(t.source_name)){
  const bytes=await fs.readFile(t.authorized_png);if(bytes.readUInt32BE(16)!==t.provided_size[0]||bytes.readUInt32BE(20)!==t.provided_size[1])throw Error('Title PNG dimensions changed '+t.source_name);
  pngs.set(t.source_name,'data:image/png;base64,'+bytes.toString('base64'));receipts.push({name:t.source_name,path:t.authorized_png,sha256:createHash('sha256').update(bytes).digest('hex')});
 }
 const alphaInput=c.geometry[0].texture_table2.filter(t=>/^kanban_(new|load|chapter|system|extra)_US\.png$/.test(t.source_name)).map(t=>[t.source_name,t.authorized_png]);
 const alphaBounds=JSON.parse(execFileSync('python',['-X','utf8','-c',"import json,sys;from PIL import Image; print(json.dumps({n:Image.open(p).convert('RGBA').getchannel('A').getbbox() for n,p in json.load(sys.stdin)}))"],{input:JSON.stringify(alphaInput),encoding:'utf8'}));
 const svg=s=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" preserveAspectRatio="none">${s}</svg>`;
 // Flash row-vector local*parent becomes SVG column-vector parent*local.
 const matrix=m=>[m[0],m[2],m[3],m[1],m[4],m[5]],identity=[1,0,0,1,0,0];
 const mul=(p,q)=>[p[0]*q[0]+p[2]*q[1],p[1]*q[0]+p[3]*q[1],p[0]*q[2]+p[2]*q[3],p[1]*q[2]+p[3]*q[3],p[0]*q[4]+p[2]*q[5]+p[4],p[1]*q[4]+p[3]*q[5]+p[5]];
 const bounds=(r,m)=>{const [x,b,y,d]=r,pts=[[x,y],[b,y],[b,d],[x,d]].map(([x,y])=>[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]]);const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);return [Math.min(...xs),Math.min(...ys),Math.max(...xs)-Math.min(...xs),Math.max(...ys)-Math.min(...ys)].map(n=>n*2/3);};
 const render=(g,label,keep,options={})=>{
  const roots=structuredClone(g.normal_root),patch=g.wait_record_updates.find(p=>p.label===label);
  for(const p of patch?.updates||[]){let r=roots.find(r=>r.depth===p.depth);if(!r){r={depth:p.depth};roots.push(r);}Object.assign(r,p);}
  const children=new Map(g.child_table5_initial_stopped_states.map(x=>[x.entry,x.children])),shapes=new Map(g.shape_table3_rects.map(x=>[x.entry,x.rects])),textures=new Map(g.texture_table2.map(t=>[t.image_id,t]));
  let serial=0;const hits={};
  const walk=(node,parent,rootName,depth=0,opacity=1,rgb=[1,1,1])=>{
   if(depth>20||!node.ref)return '';const m=mul(parent,node.matrix?matrix(node.matrix):identity),alpha=opacity*(node.rgba_multiply_add?.[0]?.[3]??1)+(node.rgba_multiply_add?.[1]?.[3]??0);
   const tint=rgb.map((v,i)=>v*(node.rgba_multiply_add?.[0]?.[i]??1));if(alpha<=0)return '';const [table,entry]=node.ref;if(table===5)return (children.get(entry)||[]).map(n=>walk(n,m,rootName,depth+1,alpha,tint)).join('');if(table!==3||entry===0)return '';
   return (shapes.get(entry)||[]).map(([image,x,b,y,d])=>{
    const t=textures.get(image);if(!t)return '';const name=t.source_name,rect=[x,b,y,d],w=b-x,h=d-y;
    if(/_ef_DXT1|_mask|chapter_art_/.test(name))return '';let ink='';
    const uri=pngs.get(name);if(uri)ink=`<image href="${uri}" x="${x}" y="${y}" width="${w}" height="${h}" preserveAspectRatio="none"/>`;
    else throw Error('Missing original title raster '+name);
    if(!ink)return '';const ab=alphaBounds[name],hitRect=/^chapter_(?:pro|[1-6])_/.test(name)?[x,b,y+h*.2,y+h*.65]:ab?[x+ab[0]*w/t.source_size[0],x+ab[2]*w/t.source_size[0],y+ab[1]*h/t.source_size[1],y+ab[3]*h/t.source_size[1]]:rect;hits[rootName]??=bounds(hitRect,m);
    const color=tint,filter=color&&color.slice(0,3).some(v=>v<.99)?`<filter id="t${++serial}" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="${color[0]} 0 0 0 0 0 ${color[1]} 0 0 0 0 0 ${color[2]} 0 0 0 0 0 1 0"/></filter>`:'';
    return filter+`<g transform="matrix(${m.join(' ')})" opacity="${Math.min(1,alpha)}"${filter?` filter="url(#t${serial})"`:''}>${ink}</g>`;
   }).join('');
  };
  const art=roots.sort((a,b)=>a.depth-b.depth).filter(keep).map(r=>walk(r,identity,r.name)).join('');return {art:'<g transform="scale(.666666666666667)">'+art+'</g>',hits};
 };
 const main=c.geometry.find(g=>g.resource==='titile_mainmenu_US'),chapter=c.geometry.find(g=>g.resource==='title_chapter_US'),scene=c.geometry.find(g=>g.resource==='title_chapter_scene_US'),monitor=c.geometry.find(g=>g.resource==='title_chapter_moniter_US');
 const modes=['new','load','chapter','system','extra'],mainRects=[];
 for(let selected=0;selected<5;selected++)for(let flags=0;flags<4;flags++){
  const out=render(main,'fl_'+modes[selected]+'_wait',r=>r.name?.startsWith('i_kanban_hasira')||r.name==='p_kanban_kazari_text'||modes.some(m=>r.name==='p_kanban_'+m+'_text')||r.name==='p_load_close'&&!(flags&1)||r.name==='p_chapter_close'&&!(flags&2));
  await write(base+`main_${selected}_${flags}.svg`,svg(out.art));if(selected===0&&flags===3)for(const mode of modes)mainRects.push(out.hits['p_kanban_'+mode+'_text']);
 }
 const chapterRects=[];
 const chapterRows=await sourceRows('title_chapter_US','fl_wait_pro');
 const chapterBack=chapterRows.filter(r=>!r.path.startsWith('p_chapter_')&&!r.path.startsWith('i_chapter_ef_')&&!r.path.startsWith('p_shadow/')&&!r.path.startsWith('p_title/'));
 await write(base+'chapter_back.svg',await sourceSvg(chapterBack));
 for(let selected=0;selected<7;selected++){
  const root=selected?'p_chapter_'+selected+'/':'p_chapter_pro/';
  for(const on of [false,true]){
   const state=on?(selected?'fl_wait_'+selected:'fl_wait_pro'):(selected?'fl_wait_pro':'fl_wait_1');
   const rows=(await sourceRows('title_chapter_US',state)).filter(r=>r.path.startsWith(root));
   if(!rows.length)throw Error('Missing original chapter plate '+root);
   await write(base+`plate_${selected}_${on?'on':'off'}.svg`,await sourceSvg(rows));
   if(!on)chapterRects.push(rows[0].rect);
  }
 }
 for(let count=0;count<=5;count++)for(let selected=0;selected<5;selected++){
  const rows=(await sourceRows('title_chapter_scene_US')).filter(r=>{
   if(r.path.startsWith('p_shadow/'))return false;
   const m=r.path.match(/^p_(beta|act)_(\d{3})\//);
   return !m||Number(m[2])<count&&(m[1]!=='act'||Number(m[2])===selected);
  });await write(base+`parts_${count}_${selected}.svg`,await sourceSvg(rows));
 }
 const mon=await sourceRows('title_chapter_moniter_US','fl_wait_pro'),artAt=mon.findIndex(r=>r.path.startsWith('p_chapter_art'));
 if(artAt<0)throw Error('Missing original monitor art layer');
 await write(base+'monitor_back.svg',await sourceSvg(mon.slice(0,artAt).filter(r=>!r.path.startsWith('_ca_'))));
 await write(base+'monitor.svg',await sourceSvg(mon.slice(artAt+1)));
 await write(base+'description.svg',await sourceSvg(await sourceRows('title_chapter_setumei')));
 const preview=(await sourceRows('title_chapter_moniter_US','fl_wait_pro')).find(r=>r.path.startsWith('p_chapter_art'));
 if(!preview)throw Error('Missing original preview mask');for(const clip of preview.clips||[])for(const row of clip){row.colorMultiply=[0,0,0];row.colorAdd=[1,1,1];}preview.texture='bg/plaza_day.webp';preview.resource='own_plaza_preview.webp';
 const previewData=(await fs.readFile(path.join(repo,'bg/plaza_day.webp'))).toString('base64');
 const previewPNG=execFileSync('python',['-X','utf8','-c',"from PIL import Image,ImageOps;import sys;ImageOps.fit(Image.open(sys.argv[1]).convert('RGBA'),(512,512)).save(sys.stdout.buffer,format='PNG')",path.join(repo,'bg/plaza_day.webp')]).toString('base64');
 const previewSvg=(await sourceSvg([preview])).replace('href="data:image/png;base64,'+previewData+'" width=', 'href="data:image/png;base64,'+previewPNG+'" width=');
 // The own world image is cropped inside the actual monitor alpha mask.
 await write(base+'own_preview.svg',previewSvg.replace('href="data:image/png;base64,'+previewPNG+'" width="512" height="512" preserveAspectRatio="none"','href="data:image/png;base64,'+previewPNG+'" width="512" height="512" preserveAspectRatio="xMidYMid slice"'));

 const make=name=>{const w=createWidgetAsset(name);w.scaleMode='scale';w.scaleRule='fit';return w;};
 const add=(w,type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{font:body,fontSize:24,text:'',color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:true,...props});w.nodes.push(n);};
 const title=make('TitleMenuV4');add(title,'Image','TmArt',[0,0,1280,720],{texture:base+'main_0_0.svg',imageFit:'fill'});add(title,'Text','TmGuide',[780,674,470,32],{fontSize:18,align:'right',text:'W/S 선택 · Enter 결정'});
 const select=make('ChapterSelectV4');add(select,'Panel','CsShade',[0,0,1280,720],{background:'#09080df2'});add(select,'Image','CsChapters',[0,0,1280,720],{texture:base+'chapter_back.svg',imageFit:'fill'});for(let i=0;i<7;i++)add(select,'Image','CsPlate'+i,[0,0,1280,720],{texture:base+`plate_${i}_off.svg`,imageFit:'fill'});add(select,'Image','CsMonitorBack',[0,0,1280,720],{texture:base+'monitor_back.svg',imageFit:'fill'});add(select,'Image','CsPreview',[0,0,1280,720],{texture:base+'own_preview.svg',imageFit:'fill'});add(select,'Image','CsMonitor',[0,0,1280,720],{texture:base+'monitor.svg',imageFit:'fill'});
 add(select,'Image','CsDescription',[0,0,1280,720],{texture:base+'description.svg',imageFit:'fill'});
 add(select,'Text','CsTitle',[70,36,1000,58],{font:head,fontSize:38,text:'장 선택'});const status=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/title_gallery_source/setumei-text-carrier.json'),'utf8'));add(select,'ScrollBox','CsStatusViewport',status.rect_1280);add(select,'Text','CsStatus',[0,0,status.rect_1280[2],status.rect_1280[3]],{fontSize:status.fontSize_1280,wrap:true,align:'center'},'CsStatusViewport');add(select,'Image','CsParts',[0,0,1280,720],{texture:base+'parts_0_0.svg',imageFit:'fill'});
 const parts=c.primary_anchors.segment_text_xy.map(([x,y])=>[x*2/3,y*2/3,650,40]);
 for(let i=0;i<5;i++)add(select,'Text','CsPart'+i,parts[i],{fontSize:26,visible:false});add(select,'Text','CsGuide',[60,656,1160,42],{fontSize:22});
 for(const [name,w]of [['TitleMenuV4',title],['ChapterSelectV4',select]]){if(!validWidgetAsset(w))throw Error('Invalid title widget '+name);await write('Assets/UI/'+name+'.hbwidget.json',w);}
 if([...mainRects,...chapterRects].some(r=>!r))throw Error('Missing source title hit carrier');
 await write('Assets/Data/v4_story/title_chapter_layout.json',{mainRects,chapterRects,parts,receipts,policy:'Original chapter/scene/monitor/description bitmap, mask, affine and selected-state carriers; supplied main-menu art and own Korean content/nonspoiler preview retained. Original global camera, additive shader and intro/outro timeline parity remain unclaimed.'});
}
