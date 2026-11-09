import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../../../engineCreate/prototype/ui-assets.js';

export async function emitTrialPickerUI({repo,write,body,head}){
 const personSelection=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/v3_reference/person_picker/selection.json'),'utf8'));
 const source=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/trial_inputs_source/manifest.json'),'utf8'));
 const base='Assets/Art/ui/v3/trial_picker/';
 const {createCanvas,loadImage}=createRequire(path.join(repo,'../engineCreate/package.json'))('@napi-rs/canvas');
 const wrap=(bytes,w,h)=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><image href="data:image/png;base64,${bytes.toString('base64')}" width="${w}" height="${h}" preserveAspectRatio="none"/></svg>`;
 const raster=async(name,target,w=1280,h=720)=>{
  const row=source.records[name];if(!row)throw Error('Missing original picker UI '+name);
  const bytes=await fs.readFile(path.join(repo,row.file));
  if(row.sha256&&createHash('sha256').update(bytes).digest('hex')!==row.sha256)throw Error('Changed picker UI '+name);
  await write(base+target,wrap(bytes,w,h));
  if(!/^picker_(title|seat(?:_\d+)?|arrow_(left|right)|person_back)$/.test(name))return;
  // Reference culprit palette on the existing source plates. Preserve alpha and neutral highlights.
  const image=await loadImage(bytes),canvas=createCanvas(image.width,image.height),ctx=canvas.getContext('2d');
  ctx.drawImage(image,0,0);
  const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);
  for(let i=0;i<pixels.data.length;i+=4){
   const [r,g,b]=pixels.data.subarray(i,i+3),peak=Math.max(r,g,b),floor=Math.min(r,g,b),chroma=peak-floor;
   if(b<r||chroma<12)continue;
   pixels.data[i]=peak;
   pixels.data[i+1]=floor+Math.round(chroma*.13);
   pixels.data[i+2]=floor+Math.round(chroma*(name.startsWith('picker_seat')?.34:.18));
  }
  ctx.putImageData(pixels,0,0);
  await write(base+'culprit_'+target,wrap(canvas.toBuffer('image/png'),w,h));
 };
 await raster('picker_seat','seat.svg');await raster('picker_title','title.svg');
 for(let i=0;i<16;i++){await raster('picker_seat_'+i,`seat_${i}.svg`);await raster('picker_dead_'+i,`dead_${i}.svg`);}
 for(const [name,target,w,h]of[['picker_arrow_left','arrow_left.svg',304,106],['picker_arrow_right','arrow_right.svg',304,106],['picker_bullet_on','bullet_on.svg',670,60],['picker_bullet_off','bullet_off.svg',670,60],['picker_guide','guide.svg',526.677083,55.833333],['picker_person_back','person_back.svg',1280,720],['picker_evidence_back','evidence_back.svg',1280,720]])await raster(name,target,w,h);
 for(const row of personSelection.entries.filter(r=>r.role)){
  const bytes=await fs.readFile(path.join(repo,row.file));if(createHash('sha256').update(bytes).digest('hex')!==row.pngSHA256)throw Error('Changed reviewed Korean person title');await write(base+row.role+'.png',bytes);
 }
 const w=createWidgetAsset('TrialPickerV4');w.scaleMode='scale';w.scaleRule='fit';
 const add=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:26.666667,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:false,...props});w.nodes.push(n);return n;};
 add('Image','PkShade',[0,0,1280,720],{texture:base+'person_back.svg',imageFit:'fill'});
 add('Image','PkTitleArt',[0,0,1280,720],{texture:base+'title.svg',imageFit:'fill'});
 add('Image','PkTitle',[124,-3.333333,341.333333,170.666667],{texture:base+'person_title_ko.png',imageFit:'fill'});
 add('Image','PkSeat',[0,0,1280,720],{texture:base+'seat.svg',imageFit:'fill'});
 add('Image','PkSelected',[0,0,1280,720],{texture:base+'seat_0.svg',imageFit:'fill'});
 for(let i=0;i<16;i++)add('Image','PkDead'+i,[0,0,1280,720],{texture:base+`dead_${i}.svg`,imageFit:'fill'});
 add('Text','PkName',[836.385083,282,368.671197,90],{font:head,fontSize:40,align:'left',rotation:8.000035,wrap:false});
 add('Image','PkPhoto',[135,130,590,370],{texture:'',imageFit:'contain'});
 add('Image','PkLeft',[53.333333,240,202.666667,70.666667],{texture:base+'arrow_left.svg',imageFit:'fill'});
 add('Image','PkRight',[598.666667,470.666667,202.666667,70.666667],{texture:base+'arrow_right.svg',imageFit:'fill'});
 add('Image','PkEvidenceBack',[0,0,1280,720],{texture:base+'evidence_back.svg',imageFit:'fill'});
 // Keep evidence art below the live status HUD; large newly bound pictures
 // previously painted over its lower focus row because widgets share a view.
 add('Image','PkEvidenceImage',[571.333333,140,600,242],{texture:'',imageFit:'contain'});
 add('Text','PkEvidencePage',[1060,358,110,32],{fontSize:22,align:'right'});
 for(let i=0;i<9;i++){
  add('Image','PkRow'+i,[62,140+i*50.666667,446.666667,40],{texture:base+'bullet_off.svg',imageFit:'fill'});
  add('Text','PkText'+i,[96,144+i*50.666667,370,36],{wrap:false,color:'#000000'});
 }
 add('Text','PkCount',[62,95,420,34],{fontSize:22});
 add('Text','PkEvidenceTitle',[571.333333,400,600,52],{fontSize:33.333333,wrap:false});
 add('ScrollBox','PkBodyScroll',[571.333333,462.666667,600,200]);
 // Prewrap words to580 with real font metrics; the native multiline Text
 // carrier still needs wrap=true to honor those explicit line breaks.
 add('Text','PkEvidenceBody',[0,0,600,200],{wrap:true,visible:true,fontSize:30},'PkBodyScroll');
 add('Panel','PkQuestionBack',[69.333333,554,694,58],{background:'#09090bea'});
 add('Text','PkQuestion',[69.333333,554,694,47.333333],{fontSize:30,wrap:false});
 add('Image','PkGuideBack',[28,644,526.677083,55.833333],{texture:base+'guide.svg',imageFit:'fill'});
 add('Text','PkGuide',[62.666667,654.666667,480,46],{fontSize:18,wrap:true});
 add('Text','PkConfirm',[300,240,420,128],{font:head,fontSize:72,align:'center',background:'#07070aab'});
 if(!validWidgetAsset(w)||w.nodes.length>256)throw Error('Invalid trial picker widget');
 await write('Assets/UI/TrialPickerV4.hbwidget.json',w);
 await write('Assets/Data/v4_story/trial_picker_layout.json',{titles:{person:base+'person_title_ko.png',culprit:base+'culprit_title_ko.png'},rows:9,buffer:10,rowAnchor:[62,140],pitch:50.666667,detailTitle:[571.333333,400,600,52],detailBody:[571.333333,462.666667,600,200],scope:'Original trial_inputs SFL mask/affine seat, person backdrop, arrows, t_ktdm_detail backdrop, source three-slice bullet rows and t_sub_mondai guide. Own actor names, evidence art, logical selection, scroll and hit-box contracts retained. DXT1 black-matte adaptation explicit; source shader/material timing not claimed.'});
 return w;
}
