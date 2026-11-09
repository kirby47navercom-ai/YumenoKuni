import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../../../engineCreate/prototype/ui-assets.js';
import {emitCulpritOrbit} from './v4-culprit-orbit.mjs';
import {validGameJson} from '../../../engineCreate/prototype/game-json.js';
export function centerInputFrame(w,stage=false){
 let frame=w.nodes.find(n=>n.id==='InputSourceFrame');if(!frame){frame=createWidgetNode('Canvas','InputSourceFrame','root');frame.name=frame.id;w.nodes.push(frame);}const positionalFrame=stage||w.name==='TrialVitalsV4';frame.slot.anchors=positionalFrame?[0,0,0,0]:[.5,.5,.5,.5];frame.slot.offset=positionalFrame?[0,0,1280,720]:[-640,-360,1280,720];frame.slot.alignment=[0,0];Object.assign(frame.properties,{padding:0,focusable:false,background:'#00000000'});
 for(const n of w.nodes)if(n.id!==frame.id&&n.parent==='root'&&(!stage||/^(Opt[NTC]\d+|Ta[A-Z].*|Spot.*|Cross[HV]|Mark\d+|MarkName|QBand|QText)$/.test(n.id)))n.parent=frame.id;
 if(!stage){const shade=w.nodes.find(n=>n.id==='PkShade');if(shade){shade.parent='root';shade.slot.anchors=[0,0,1,1];shade.slot.offset=[0,0,0,0];}}
 if(w.nodes.length>256||!validWidgetAsset(w))throw Error('Invalid centered input frame '+w.name);return w;
}

// Each selector owns its clock and motion widget; none is loaded by the title scene.
export async function emitTrialInputMotionUI({repo,write,read}){
 const source=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/trial_inputs_motion/manifest.json'),'utf8'));
 const original=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/trial_inputs/layout.json'),'utf8'));
 const cards=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/trial_vote_cards/manifest.json'),'utf8'));
 for(const list of [cards.cursors,...Object.values(cards.cards)])for(const asset of list)await write(asset,await fs.readFile(path.join(repo,'ui/v4/trial_vote_cards',path.basename(asset))));
 const base='Assets/Art/ui/v3/trial_inputs_motion/';
 const guideAsset=base+'decision_guide.png';
 await write(guideAsset,await fs.readFile(path.join(repo,'ui/v3_authorized/trial_inputs/t_kettei/texture_000_t_sub_mondai_bt_pl_000.png.png')));
 const promptIcons={
  mouse:'<rect x="5" y="2" width="14" height="20" rx="6"/><path d="M5 10h14M12 2v8"/><path fill="white" d="M6 8a5 5 0 0 1 5-5v6H6z"/>',
  wheel:'<rect x="5" y="2" width="14" height="20" rx="6"/><path d="M5 10h14M12 4v4" stroke-width="2.5"/>',
  question:'<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 17V7h7M9 11h5"/>',
 };
 for(const [id,shape] of Object.entries(promptIcons))await write(base+'prompt_'+id+'.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><g fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${shape}</g></svg>`);
 const addPromptIcons=(widget,x,y,keys,z,start=0)=>{
  for(const [i,key] of keys.entries()){
   const id='PromptIcon'+(i+start);
   let n=widget.nodes.find(node=>node.id===id);
   if(!n){n=createWidgetNode('Image',id,'root');n.name=id;widget.nodes.push(n);}
   n.slot.offset=[x+i*105,y,20,20];n.slot.zIndex=z;
   Object.assign(n.properties,{texture:base+'prompt_'+key+'.svg',visible:true,focusable:false,imageFit:'contain'});
  }
 };
 const addGuide=(widget,rect,label)=>{
  const [x,y,w,h]=rect;
  const image=createWidgetNode('Image','DecisionGuide','root');image.name=image.id;image.slot.offset=rect;image.slot.zIndex=4;
  Object.assign(image.properties,{texture:guideAsset,visible:true,focusable:false,imageFit:'fill'});widget.nodes.push(image);
  const text=createWidgetNode('Text','DecisionLabel','root');text.name=text.id;text.slot.offset=[x+35,y+9,w-46,h-12];text.slot.zIndex=5;
  Object.assign(text.properties,{text:label,font:'Assets/Fonts/pretendard/Pretendard-Regular.otf',fontSize:19,visible:true,focusable:false,padding:0,color:'#ffffff',background:'#00000000'});widget.nodes.push(text);
  addPromptIcons(widget,x+12,y+9,['mouse'],5);
 };
 for(const [name,file]of Object.entries(source.copies))await write(base+name,await fs.readFile(path.join(repo,file)));
 for(const row of Object.values(source.rasters))await write(base+path.basename(row.file),await fs.readFile(path.join(repo,row.file)));
 const raster=name=>{const r=source.rasters[name];return {asset:base+path.basename(r.file),rect:r.rect};};
 const widgets={};
 for(const kind of ['choice','bullet','vote']){
  const w=createWidgetAsset('TrialInputMotion_'+kind);w.scaleMode='scale';w.scaleRule='fit';
  const add=(id,rect,texture,z=0)=>{const n=createWidgetNode('Image',id,'root');n.name=id;n.slot.offset=rect;n.slot.zIndex=z;Object.assign(n.properties,{texture,visible:false,focusable:false,imageFit:'fill',background:'#00000000'});w.nodes.push(n);};
  if(kind==='choice'){
   const glass=raster(source.glass[0]);add('Glass',glass.rect,glass.asset,1);
   addGuide(w,[965,486,315,39],'결정');
  }
  const clock=raster(kind+'_clock_base');add('ClockBase',clock.rect,clock.asset,2);
  for(let i=0;i<9;i++)add('Clock'+i,source.clocks[kind].rects[i],source.clocks[kind].digits['0'],3);
  if(kind==='vote')for(let i=0;i<25;i++)add('Leaf'+i,[0,0,1,1],'',10+i);
  if(!validWidgetAsset(w))throw Error('Invalid original trial input motion '+kind);
  const file='Assets/UI/TrialInputMotion_'+kind+'.hbwidget.json';await write(file,centerInputFrame(w));widgets[kind]=file;
 }
 const spot=createWidgetAsset('TrialInputMotion_spot');spot.scaleMode='scale';spot.scaleRule='fit';const reticle=createWidgetNode('Image','Lock','root');reticle.name='Lock';reticle.slot.offset=[0,0,1,1];Object.assign(reticle.properties,{visible:false,texture:'',focusable:false,imageFit:'fill'});spot.nodes.push(reticle);widgets.spot='Assets/UI/TrialInputMotion_spot.hbwidget.json';
 addGuide(spot,[28,644,430,47],'결정');
 addPromptIcons(spot,145,653,['question'],5,1);
 const spotQuestion=createWidgetNode('Text','DecisionQuestion','root');spotQuestion.name=spotQuestion.id;spotQuestion.slot.offset=[170,653,110,32];spotQuestion.slot.zIndex=5;
 Object.assign(spotQuestion.properties,{...spot.nodes.find(n=>n.id==='DecisionLabel').properties,text:'문제 표시'});spot.nodes.push(spotQuestion);
 await write(widgets.spot,centerInputFrame(spot));
 const bank={...source,widgets,glass:source.glass.map(raster),cards:cards.cards,cardCursors:cards.cursors,cardPolygons:cards.polygons};delete bank.copies;delete bank.rasters;
 const arrows=original.t_sub_jinbutu_arrow,seats=original.t_sub_jinbutu_zaseki_US;
 const arrowFrames=(from,to)=>arrows.frames.slice(arrows.labels[from]-1,to?arrows.labels[to]-1:undefined)
  .map(rows=>rows.slice(0,2).map(r=>[...r.rect.slice(0,2),r.opacity]));
 const seatOpacity=rows=>rows.find(r=>r.resource==='t_sub_jinbutu_zaseki_base_DXT1.png')?.opacity||0;
 bank.culpritMotion={
  enter:arrowFrames('fl_in','fl_wait'),left:arrowFrames('fl_left','fl_right'),
  right:arrowFrames('fl_right','fl_out'),exit:arrowFrames('fl_out'),
  seatIn:seats.frames.slice(seats.labels.fl_in-1,seats.labels.fl_wait-1).map(seatOpacity),
  seatOut:seats.frames.slice(seats.labels.fl_out-1).map(seatOpacity),
 };
 const intro=original.t_sub_spot_bg;
 bank.spotOpening=intro.frames.slice(intro.labels.fl_in-1,intro.labels.fl_wait).map(rows=>[
  rows.find(r=>r.path==='/1')?.opacity*2||0,
  rows.find(r=>r.path==='/p_scr_img/1')?.opacity||0,
 ]);
 bank.spotExit=intro.frames.slice(intro.labels.fl_out-1).map(rows=>{
  const photo=rows.find(r=>r.path==='/p_scr_img/1');
  return photo?[photo.rect[2]/896,photo.rect[3]/506.6666666666667,photo.opacity]:[1,1,0];
 });
 const evidenceMotion=original.t_ktdm_detail_img_US;
 bank.evidenceExit=evidenceMotion.frames.slice(evidenceMotion.labels.fl_out-1).map(rows=>[
  rows.find(r=>r.path.includes('/p_kotodama/'))?.opacity||0,
  rows.find(r=>r.resource==='t_ktdm_detail_img_frame.png')?.opacity||0,
 ]);
 const nomination=original.t_sub_jinbutu_kettei_US,nominationAssets=new Map();
 const {createCanvas,loadImage}=createRequire(path.join(repo,'../engineCreate/package.json'))('@napi-rs/canvas');
 bank.culpritOrbit=await emitCulpritOrbit({repo,write,base,createCanvas,loadImage,
  focus:original.t_sub_jinbutu_focus,plate:original.t_sub_jinbutu_pl});
 bank.personConfirm=[];
 for(const rows of nomination.frames.slice(nomination.labels.fl_in-1,nomination.labels.fl_out-1)){
  const frame=[];
  for(const row of rows){
   if(!row.texture||!row.opacity)continue;
   if(!nominationAssets.has(row.resource)){
    const asset=base+'nominate_'+row.resource;
    let bytes=await fs.readFile(path.join(repo,row.texture));
    if(row.resource.includes('DXT1')){
     const image=await loadImage(bytes),canvas=createCanvas(image.width,image.height),ctx=canvas.getContext('2d');
     ctx.drawImage(image,0,0);
     const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);
     // The source flare uses additive black. Native Image uses alpha blending.
     for(let i=0;i<pixels.data.length;i+=4){
      const peak=Math.max(pixels.data[i],pixels.data[i+1],pixels.data[i+2]);
      if(peak)for(let c=0;c<3;c++)pixels.data[i+c]=Math.round(pixels.data[i+c]*255/peak);
      pixels.data[i+3]=Math.round(pixels.data[i+3]*peak/255);
     }
     ctx.putImageData(pixels,0,0);bytes=canvas.toBuffer('image/png');
    }
    await write(asset,bytes);nominationAssets.set(row.resource,asset);
   }
   frame.push([nominationAssets.get(row.resource),...row.rect,row.rotation,row.opacity]);
  }
  bank.personConfirm.push(frame);
 }
 const question=original.t_sub_mondai;
 const widths=rows=>rows.find(r=>r.resource==='t_sub_mondai_pl_000.png')?.rect[2]||0;
 bank.questionMotion={
  open:question.frames.slice(question.labels.fl_open-1,question.labels.fl_open_wait).map(widths),
  close:question.frames.slice(question.labels.fl_close-1,question.labels.fl_out-1).map(widths),
 };
 const choice=original.t_choice_frame_US;
 const background=choice.states.fl_wait.find(r=>r.path==='/1');
 const choiceOpeningAsset=base+'choice_opening.png';
 await write(choiceOpeningAsset,await fs.readFile(path.join(repo,background.texture)));
 bank.choiceOpening={texture:choiceOpeningAsset,rest:raster('choice_decor').asset,frames:choice.frames
  .slice(choice.labels.fl_in-1,choice.labels.fl_wait)
  .map(rows=>rows.find(r=>r.path==='/1')?.rect||background.rect)};
 bank.spotLock=source.spotLock.map(raster);
 bank.voteInputName=raster('vote_name_complete').asset;bank.voteResultName=raster('vote_result_name').asset;bank.voteResultBack=raster('vote_result_back').asset;
 bank.tracks={};
 for(const [kind,frames]of Object.entries(source.tracks)){
  const chunks=[];for(let i=0;i<frames.length;i+=24){const file=`Assets/Data/v4_story/trial_input_${kind}_${i/24}.json`,value={frames:frames.slice(i,i+24)};if(!validGameJson(value))throw Error('Original input track exceeds runtime JSON contract '+file);await write(file,value);chunks.push(file);}
  bank.tracks[kind]={frames:frames.length,chunks};
 }
 if(!validGameJson(bank))throw Error('Trial input manifest exceeds runtime JSON contract');
 if(read){
  try{
   const vitals=await read('Assets/UI/TrialVitalsV4.hbwidget.json');
   const sourceStatus=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/nonstop_hud_source/layout.json'),'utf8'));
   for(const [id,tile] of [['SelectorStatus','status'],['SelectorHearts','heart5_10'],['SelectorStars','star5_10']]){
    let node=vitals.nodes.find(n=>n.id===id);
    if(!node){node=createWidgetNode('Image',id,'root');node.name=id;vitals.nodes.push(node);}
    node.slot.offset=sourceStatus.tiles[tile].rect;
    Object.assign(node.properties,{visible:false,focusable:false,imageFit:'fill',texture:'Assets/Art/ui/nonstop_source/'+tile+'.png'});
   }
   await write('Assets/UI/TrialVitalsV4.hbwidget.json',centerInputFrame(vitals));
  }catch(error){if(error.code!=='ENOENT')throw error;}
  const stage=await read('Assets/UI/Stage.hbwidget.json'),frame=stage.nodes.find(n=>n.id==='TaFrame');if(!frame)throw Error('Missing trial answer frame');frame.properties.texture=raster('choice_decor').asset;
  let question='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">';
  for(const name of ['body_plain','frame_plain'])question+=`<image href="data:image/png;base64,${(await fs.readFile(path.join(repo,'ui/v4/trial_dialogue_source',name+'.png'))).toString('base64')}" width="1280" height="720"/>`;
  const questionAsset=base+'choice_question.svg';await write(questionAsset,question+'</svg>');stage.nodes.find(n=>n.id==='TaQuestionPlate').properties.texture=questionAsset;
  let mode=stage.nodes.find(n=>n.id==='SpotModeFrame');if(!mode){mode=createWidgetNode('Image','SpotModeFrame','root');stage.nodes.push(mode);}mode.name='SpotModeFrame';mode.slot.offset=[0,0,1280,720];mode.slot.zIndex=0;Object.assign(mode.properties,{texture:'Assets/Art/ui/v3/trial_picker/title.svg',visible:false,focusable:false,imageFit:'fill'});
  if(!validWidgetAsset(stage)||stage.nodes.length>256)throw Error('Invalid original input Stage overlay');
  await write('Assets/UI/Stage.hbwidget.json',centerInputFrame(stage,true));
  const picker=await read('Assets/UI/TrialPickerV4.hbwidget.json');
  picker.nodes.find(n=>n.id==='PkName').properties.wrap=false;
  const seatLayer=seats.states.fl_wait.filter(r=>r.texture&&!/^\/(?:_a_dead_|p_line_)/.test(r.path)&&!r.resource.includes('_name_')&&!r.resource.includes('_num_'));
  const seatCanvas=createCanvas(1280,720),seatG=seatCanvas.getContext('2d');
  for(const r of seatLayer){
   const [x,y,w,h]=r.rect,im=await loadImage(await fs.readFile(path.join(repo,r.texture)));
   seatG.save();seatG.translate(x+w/2,y+h/2);seatG.rotate(r.rotation*Math.PI/180);
   seatG.globalAlpha=r.opacity;seatG.drawImage(im,-w/2,-h/2,w,h);seatG.restore();
  }
  const seatPixels=seatG.getImageData(0,0,1280,720);
  for(let i=0;i<seatPixels.data.length;i+=4){
   const [red,green,blue]=seatPixels.data.subarray(i,i+3),low=Math.min(red,green,blue),contrast=Math.max(red,green,blue)-low;
   if(blue<red||contrast<12)continue;
   seatPixels.data[i]=low+contrast;seatPixels.data[i+1]=low+contrast*.13;seatPixels.data[i+2]=low+contrast*.34;
  }
  seatG.putImageData(seatPixels,0,0);await write(base+'culprit_seat_plate.png',seatCanvas.toBuffer('image/png'));
  const imported=await fs.readdir(path.join(repo,'ui/v3_authorized/trial_inputs/t_sub_jinbutu_zaseki_US'));
  for(let i=0;i<16;i++){
   const id=String(i).padStart(3,'0'),file=imported.find(n=>n.includes('_num_'+id+'_'));
   const im=await loadImage(await fs.readFile(path.join(repo,'ui/v3_authorized/trial_inputs/t_sub_jinbutu_zaseki_US',file)));
   const canvas=createCanvas(im.width,im.height),g=canvas.getContext('2d');g.drawImage(im,0,0);
   const pixels=g.getImageData(0,0,im.width,im.height);
   for(let n=0;n<pixels.data.length;n+=4){
    const value=Math.max(pixels.data[n],pixels.data[n+1],pixels.data[n+2]);
    pixels.data[n]=255;pixels.data[n+1]=196+59*(value/255)**3;pixels.data[n+2]=32+183*(value/255)**3;pixels.data[n+3]*=value/255;
   }
   g.putImageData(pixels,0,0);await write(base+'culprit_number_'+i+'.png',canvas.toBuffer('image/png'));
  }
  picker.nodes=picker.nodes.filter(node=>!/^Culprit(?:Echo|Orbit|Sweep|Focus|Number)/.test(node.id));
  for(const [id,offset,z] of [['CulpritOrbit',[0,0,1024,432],1],['CulpritSweep',[0,0,1280,720],2],['CulpritNumber',[703.33,237.33,110.67,110.67],3]]){
   const node=createWidgetNode('Image',id,'root');node.name=id;node.slot.offset=offset;node.slot.zIndex=z;
   Object.assign(node.properties,{visible:false,focusable:false,imageFit:'fill'});picker.nodes.push(node);
  }
  for(const [prefix,count,z] of [['CulpritClock',9,8]]){
   for(let i=0;i<count;i++){
    const id=prefix+i;
    let n=picker.nodes.find(node=>node.id===id);
    if(!n){n=createWidgetNode('Image',id,'root');n.name=id;picker.nodes.push(n);}
    n.slot.zIndex=z;
    if(prefix==='CulpritClock'){
     const [x,,w,h]=source.clocks.bullet.rects[i];
     n.slot.offset=[989+x-515.333333,655,w,h];n.properties.texture=source.clocks.bullet.digits['0'];
    }
    Object.assign(n.properties,{visible:false,focusable:false,imageFit:'fill'});
   }
  }
  for(let i=0;i<4;i++){
   const id='PersonConfirm'+i;
   let n=picker.nodes.find(node=>node.id===id);
   if(!n){n=createWidgetNode('Image',id,'root');n.name=id;picker.nodes.push(n);}
   n.slot.zIndex=95+i;Object.assign(n.properties,{visible:false,focusable:false,imageFit:'fill'});
  }
  const questionBack=picker.nodes.find(n=>n.id==='PkQuestionBack');
  questionBack.type='Image';
  Object.assign(questionBack.properties,{texture:'Assets/Art/ui/sub_question_source.svg',imageFit:'fill',background:'#00000000'});
  const questionText=picker.nodes.find(n=>n.id==='PkQuestion');
  Object.assign(questionText.properties,{fontSize:20,padding:0,wrap:false});
  const preview=original.t_ktdm_detail_img_US.states.fl_wait;
  const frameRow=preview.find(r=>r.resource==='t_ktdm_detail_img_frame.png');
  const imageRow=preview.find(r=>r.path.includes('/p_kotodama/'));
  const origin=original.t_ktdm_detail.states.fl_wait.find(r=>r.path==='/p_t_ktdm_detail_img/1').rect;
  const evidenceFrame=base+'evidence_frame.png';
  await write(evidenceFrame,await fs.readFile(path.join(repo,frameRow.texture)));
  const evidence=picker.nodes.find(n=>n.id==='PkEvidenceImage');
  const [ix,iy,iw,ih]=imageRow.rect;
  // This native carrier rotates a rectangle. Inset it inside the sheared source mat.
  evidence.slot.offset=[origin[0]+ix+iw*.075,origin[1]+iy,iw*.85,ih];
  evidence.properties.rotation=imageRow.rotation;
  let outline=picker.nodes.find(n=>n.id==='PkEvidenceFrame');
  if(!outline){outline=createWidgetNode('Image','PkEvidenceFrame','root');outline.name=outline.id;picker.nodes.splice(picker.nodes.indexOf(evidence)+1,0,outline);}
  outline.slot.offset=[origin[0]+frameRow.rect[0],origin[1]+frameRow.rect[1],...frameRow.rect.slice(2)];
  Object.assign(outline.properties,{texture:evidenceFrame,rotation:frameRow.rotation,visible:false,focusable:false,imageFit:'fill'});
  const guide=picker.nodes.find(n=>n.id==='PkGuide');
  addPromptIcons(picker,62,660,['mouse','question','wheel'],5);
  for(const [i,label] of ['결정','문제 표시','스크롤'].entries()){
   const id='PromptLabel'+i;
   let n=picker.nodes.find(node=>node.id===id);
   if(!n){n=createWidgetNode('Text',id,'root');n.name=id;picker.nodes.push(n);}
   n.slot.offset=[87+i*105,657,95,32];n.slot.zIndex=5;
   Object.assign(n.properties,{...guide.properties,text:label,fontSize:19,visible:false});
  }
  for(const state of ['on','off']){const bytes=await fs.readFile(path.join(repo,source.rasters['bullet_row_'+state].file));await write('Assets/Art/ui/v3/trial_picker/bullet_'+state+'.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 670 60"><image href="data:image/png;base64,${bytes.toString('base64')}" width="670" height="60" preserveAspectRatio="none"/></svg>`);}
  for(const name of ['bullet_cylinder','bullet_scroll']){const r=raster(name);let n=picker.nodes.find(n=>n.id===name);if(!n){n=createWidgetNode('Image',name,'root');picker.nodes.push(n);}n.name=name;n.slot.offset=r.rect;n.slot.zIndex=-1;Object.assign(n.properties,{texture:r.asset,visible:false,focusable:false,imageFit:'fill'});}
  for(const name of ['PkText0','PkText1','PkText2','PkText3','PkText4','PkText5','PkText6','PkText7','PkText8','PkEvidenceTitle','PkEvidenceBody']){const n=picker.nodes.find(n=>n.id===name);n.properties.font='Assets/Fonts/pretendard/Pretendard-Regular.otf';n.properties.fontSize=name==='PkEvidenceBody'?22:name==='PkEvidenceTitle'?28:24;}
  await write('Assets/UI/TrialPickerV4.hbwidget.json',centerInputFrame(picker));
  const vote=await read('Assets/UI/Vote.hbwidget.json');
  vote.nodes.find(n=>n.id==='VoteResultRows').properties.texture=raster('vote_result_board').asset;
  const mark=await fs.readFile(path.join(repo,'ui/v4/trial_inputs_motion',path.basename(source.voteMark)));
  for(let count=0;count<=16;count++)await write(`Assets/Art/ui/vote_v4/count_${count}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 24">${Array.from({length:count},(_,i)=>`<image href="data:image/png;base64,${mark.toString('base64')}" x="${i*8}" y="4" width="8" height="16"/>`).join('')}</svg>`);
  for(let i=0;i<16;i++)vote.nodes.find(n=>n.id==='VoteP'+i).slot.zIndex=5;
  for(const [id,name]of [['VoteTitleArt','vote_title_complete'],['VoteNamePlate','vote_name_complete']]){const n=vote.nodes.find(n=>n.id===id);n.slot.offset=[0,0,1280,720];n.properties.texture=raster(name).asset;}
  for(let i=0;i<16;i++){let n=vote.nodes.find(n=>n.id==='VoteD'+i);if(!n){n=createWidgetNode('Image','VoteD'+i,'root');vote.nodes.push(n);}n.name=n.id;n.slot.offset=source.voteCards[i];n.slot.zIndex=6;Object.assign(n.properties,{texture:source.voteDead,visible:false,focusable:false,imageFit:'fill'});}
  if(!validWidgetAsset(picker)||!validWidgetAsset(vote))throw Error('Invalid original picker/vote overlay');
  await write('Assets/UI/Vote.hbwidget.json',centerInputFrame(vote));
 }
 await write('Assets/Data/v4_story/trial_input_motion.json',bank);return bank;
}
