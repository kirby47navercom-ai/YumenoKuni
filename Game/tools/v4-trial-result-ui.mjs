import {emitSourceFamily} from './v3-source-svg.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../../../engineCreate/prototype/ui-assets.js';

export async function emitTrialResultUI({repo,write,body}){
 const head='Assets/Fonts/dohyeon/DoHyeon-Regular.ttf';
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/trial_remaining_ui_contract.json'),'utf8'));
 const base='Assets/Art/ui/v3/trial_result/',assets={};
 for(const [family,f] of Object.entries(c.families))if(family.includes('t_resultt_')){
  const images=new Map();
  for(const r of f.provided_rasters){const bytes=await fs.readFile(r.path);if(createHash('sha256').update(bytes).digest('hex')!==r.png_sha256)throw Error('Result raster changed '+r.resource);
   const dest=base+r.resource;await write(dest,bytes);assets[r.resource]=dest;
   if(r.exact_name_dimension_candidates.length===1)images.set(r.exact_name_dimension_candidates[0].image_id,'data:image/png;base64,'+bytes.toString('base64'));
  }
  const include=l=>family.includes('_header_')?!/saiban_tx|case_tx/.test(l.path):family.includes('_img_')?!/num_|_tx|ico/.test(l.path):false;
  const layers=f.snapshots.fl_wait.filter(l=>include(l)&&l.composed_alpha_from_identity>0&&l.image_ids.length===1&&images.has(l.image_ids[0]));
  if(layers.length){const part=family.includes('_header_')?'header':'detail';await write(base+part+'.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"><g transform="scale(.666666666666667)">${layers.map(l=>{const [x,r,y,b]=l.local_bounds_xmin_xmax_ymin_ymax,m=l.composed_affine_row_major;return `<image href="${images.get(l.image_ids[0])}" x="${x}" y="${y}" width="${r-x}" height="${b-y}" transform="matrix(${[m[0],m[1],m[3],m[4],m[6],m[7]].join(' ')})" opacity="${l.composed_alpha_from_identity}" preserveAspectRatio="none"/>`;}).join('')}</g></svg>`);}
 }
 const source=await fs.readFile(path.join(repo,'ui/v3_authorized/all_general/t_resultt_bg/t_resultt_bg_000_DXT1.png.png'));
 await write(base+'back.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540"><image href="data:image/png;base64,${source.toString('base64')}" width="1024" height="1024"/></svg>`);
 await emitSourceFamily(write,base+'scroll.svg','t_resultt_list_scroll');
 await emitSourceFamily(write,base+'penalty.svg','t_resultt_window_US','fl_wait',r=>!/_tx|score_num|perfect/.test(r.path));
 const w=createWidgetAsset('TrialResultV4');w.scaleMode='scale';w.scaleRule='fit';
 const add=(type,id,rect,props={})=>{const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:true,...props});w.nodes.push(n);};
 add('Image','RsBack',[0,0,1280,720],{texture:base+'back.svg',imageFit:'fill'});
 add('Image','RsScrollArt',[0,0,1280,720],{texture:base+'scroll.svg',imageFit:'fill'});
 add('Image','RsPenaltyArt',[0,0,1280,720],{texture:base+'penalty.svg',imageFit:'fill'});
 add('Image','RsDetailArt',[0,0,1280,720],{texture:base+'detail.svg',imageFit:'fill'});
 add('Image','RsHeaderArt',[0,0,1280,720],{texture:base+'header.svg',imageFit:'fill'});
 add('Text','RsHeader',[60,36,1120,58],{font:head,fontSize:38,color:'#ffffff'});
 const iconNames=['giron','hanron','diver','ana','hakkutu','riron','scrum','climax','panic'];
 for(let i=0;i<8;i++){
  add('Image','RsStrip'+i,[64.666667,88+i*54,478.666667,85.333333],{texture:assets['t_resultt_list_pl_000.png'],imageFit:'fill'});
  add('Text','RsNo'+i,[77,104+i*54,44,34],{fontSize:22,color:'#ffcf16'});
  add('Image','RsIcon'+i,[112,101+i*54,32,32],{imageFit:'contain'});
  add('Text','RsLabel'+i,[152,103+i*54,242,36],{fontSize:23,wrap:false});
  add('Text','RsScore'+i,[398,105+i*54,68,34],{fontSize:24,align:'right'});
  add('Image','RsRank'+i,[445.333333,71.333333+i*54,85.333333,85.333333],{imageFit:'contain'});
 }
 add('Text','RsPage',[75,540,460,35],{fontSize:21});
 add('Text','RsTotalLabel',[620,117,520,40],{font:head,fontSize:30});
 add('Text','RsTotal',[620,163,520,75],{font:head,fontSize:60,color:'#ffcf16',align:'right'});
 add('Text','RsGrade',[620,239,520,42],{font:head,fontSize:34,align:'right'});
 add('Text','RsMedal',[620,299,520,45],{fontSize:30,align:'right'});
 add('Text','RsPenalties',[620,362,520,80],{fontSize:24,wrap:true});
 add('Text','RsSelected',[620,451,520,142],{fontSize:21,wrap:true});
 add('Text','RsGuide',[60,650,1160,38],{fontSize:20,color:'#eef6ff',background:'#09101ae8'});
 if(!validWidgetAsset(w)||w.nodes.length>256)throw Error('Invalid result widget');await write('Assets/UI/TrialResultV4.hbwidget.json',w);
 await write('Assets/Data/v4_story/trial_result_layout.json',{assets,iconNames,sourceScale:2/3,rows:8,pitch:54,policy:'Supplied result rasters checked by SHA. Source affine header/detail and source list/rank carriers; JP rank ink retained, own Korean labels, source background/scroll/window, own Korean font fit and counter animation. Own phase budgets grade at half/quarter initial raw capacity; source chapter rank lists cannot be assigned to different manuscript phases.'});
 return w;
}
