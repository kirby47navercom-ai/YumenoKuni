import fs from 'node:fs/promises';
import {sourceRows,sourceSvg} from './v3-source-svg.mjs';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../../../engineCreate/prototype/ui-assets.js';
export async function emitLoadingSourceUI({write}){
 const rows=await sourceRows('loading_s','fl_wait','loading_source'),base='Assets/Art/ui/v3/loading/';
 await write(base+'base.svg',await sourceSvg(rows.filter(r=>/^(p_black|p_base)/.test(r.path))));
 const spin=rows.filter(r=>r.path.startsWith('_a_load'));
 await write(base+'spinner.svg',await sourceSvg(spin,{bounds:[1128,593,96,96]}));
 await write(base+'spinner.webp',await fs.readFile(new URL('../../ui/v4/loading_source/spinner.webp',import.meta.url)));
 const w=createWidgetAsset('LoadingV4');w.scaleMode='scale';w.scaleRule='fit';w.nodes[0].properties.background='#000000';
 const canvas=createWidgetNode('Panel','SourceCanvas','root');canvas.slot.anchors=[.5,.5,.5,.5];canvas.slot.offset=[-640,-360,1280,720];Object.assign(canvas.properties,{visible:true,focusable:false,padding:0,background:'#00000000'});w.nodes.push(canvas);
 const add=(type,id,rect,properties)=>{const n=createWidgetNode(type,id,'SourceCanvas');n.name=id;n.slot.offset=rect;Object.assign(n.properties,{visible:true,focusable:false,padding:0,background:'#00000000',...properties});w.nodes.push(n);};
 add('Image','LoadingSource',[0,0,1280,720],{texture:base+'base.svg',imageFit:'fill'});
 add('Image','LoadingSpinner',[1128,593,96,96],{texture:base+'spinner.webp',imageFit:'fill'});
 add('Text','LoadingLabel',[812,617,285,46],{text:'로딩 중',font:'Assets/Fonts/pretendard/Pretendard-Medium.otf',fontSize:32,color:'#ffffff',align:'right',wrap:false});
 if(!validWidgetAsset(w))throw Error('Invalid original loading UI');await write('Assets/UI/LoadingV4.hbwidget.json',w);return w;
}
