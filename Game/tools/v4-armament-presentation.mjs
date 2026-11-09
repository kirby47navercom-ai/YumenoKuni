import {emitArmamentSourceSites} from './v4-armament-source-sites.mjs';
import {emitArmamentFinalUi} from './v4-armament-final-ui.mjs';
import {armamentTranscript} from './v4-armament-transcript.mjs';
import {emitSolutionCutinActors} from './v4-solution-cutin-actors.mjs';
import {emitEndingSource} from './v4-ending-source.mjs';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
// Reference: user supplied Korean PC footage pMRvvdS6XmI, 1:05:15–1:07:50.
// Original supplied/authorized UI with source SFL transforms; own manuscript and portraits.
import fs from 'node:fs/promises';import path from 'node:path';import {createRequire} from 'node:module';import {createHash} from 'node:crypto';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),require=createRequire(path.join(repo,'../engineCreate/package.json')),{createCanvas,loadImage,GlobalFonts}=require('@napi-rs/canvas');
// Pure presentation patch for retained packages; preserves charts/transcripts and actors.
export function applyArmamentFinalButtonSourceRects(nodes,sourceLayout){
 for(let i=0;i<4;i++){const n=nodes.find(n=>n.id==='ArmPieceKey'+i),shape=['triangle','circle','cross','square'][i],container='t_riron_todome_'+shape;
  if(!n)throw Error('Missing final-fragment button '+i);
  const quad=sourceLayout[container].states.fl_wait.find(row=>row.resource==='t_riron_todome_'+shape+'.png');if(!quad)throw Error('Missing original final-fragment button quad '+container);
  n.rect=[...quad.rect];n.rotation=quad.rotation;
 }
 return nodes;
}
export const armamentDisplayName=s=>s.opponentDisplay||s.finalSubject?.replace(/(?:은|는)$/u,'')||(s.opponent==='lappy'?'래피':s.opponent);
export async function emitArmamentWordTextures({write,tasks,source=game}){
 GlobalFonts.registerFromPath(path.join(source,'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf'),'Armament');
 const transcripts={},assets=new Set();
 for(const [id,task]of Object.entries(tasks))if(task.stage.kind==='armament'){
  let lineBase=0;
  const waves=task.stage.phaseTranscripts?task.stage.waves.map(wave=>wave.pairs.map(pair=>pair.claim.text)):[task.stage.lines];
  const tracks=[];
  for(const wave of waves){
  const track=[];
  for(const row of armamentTranscript(wave,1)){
   const key=createHash('sha256').update(row.text+'#ff80ad'+48+384+72).digest('hex').slice(0,16),asset='Assets/Art/ui/armament_stream/'+key+'.png';
   if(!assets.has(asset)){const c=createCanvas(768,144),ctx=c.getContext('2d');ctx.scale(2,2);ctx.font='48px Armament';ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineJoin='round';ctx.lineWidth=6;ctx.strokeStyle='#171022';ctx.strokeText(row.text,192,36,366);ctx.fillStyle='#ff80ad';ctx.fillText(row.text,192,36,366);await write(asset,c.toBuffer('image/png'));assets.add(asset);}
   track.push({...row,line:row.line+lineBase,texture:asset});
  }
  tracks.push(track);lineBase+=wave.length;
  }
  transcripts[id]=task.stage.phaseTranscripts?tracks:tracks[0];
 }
 return {transcripts,assets:[...assets]};
}
export async function emitRevisedArmamentFigures({write,tasks,source=game}){
 const stages=Object.values(tasks).map(task=>task.stage).filter(stage=>stage.kind==='armament');
 if(!stages.length)return;
 const file='Assets/Data/armament_figures_v4.json';
 const bank=JSON.parse(await fs.readFile(path.join(source,file),'utf8'));
 for(const opponent of new Set(stages.map(stage=>stage.opponent))){
  if(bank.figures[opponent])continue;
  assert(/^[a-z]+$/.test(opponent),'Invalid revised opponent');
  const directory=path.join(repo,'art/revision_armament',opponent);
  const figure=JSON.parse(await fs.readFile(path.join(directory,'runtime.json'),'utf8'));
  assert.deepEqual(figure.states.map(state=>state.phase),['full','half','core']);
  assert(figure.defeat&&figure.name);
  for(const row of [...figure.states,figure.defeat]){
   const prefix='Assets/Art/revision_armament/'+opponent+'/';
   assert(row.texture.startsWith(prefix)&&path.basename(row.texture)===row.texture.slice(prefix.length));
   assert(row.aspect>0&&row.aspect<2);
   const bytes=await fs.readFile(path.join(directory,path.basename(row.texture)));
   assert.equal(createHash('sha256').update(bytes).digest('hex'),row.sha256,'Reviewed figure changed: '+row.texture);
   await write(row.texture,bytes);
  }
  bank.figures[opponent]={states:figure.states,defeat:figure.defeat};
  GlobalFonts.register(await fs.readFile(path.join(source,'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf')),'Armament');
  const canvas=createCanvas(480,84),ctx=canvas.getContext('2d');
  ctx.scale(2,2);ctx.font='24px Armament';ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.lineJoin='round';ctx.lineWidth=6;ctx.strokeStyle='#171022';ctx.strokeText(figure.name,120,21,222);
  ctx.fillStyle='#fff';ctx.fillText(figure.name,120,21,222);
  const label='Assets/Art/revision_armament/'+opponent+'/name.png';
  await write(label,canvas.toBuffer('image/png'));
  bank.presentation.labels[opponent]=label;
 }
 for(const display of new Set(stages.map(stage=>stage.opponentDisplay).filter(Boolean))){
  GlobalFonts.register(await fs.readFile(path.join(source,'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf')),'Armament');
  const canvas=createCanvas(480,84),ctx=canvas.getContext('2d');
  ctx.scale(2,2);ctx.font='24px Armament';ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.lineJoin='round';ctx.lineWidth=6;ctx.strokeStyle='#171022';ctx.strokeText(display,120,21,222);
  ctx.fillStyle='#fff';ctx.fillText(display,120,21,222);
  const label='Assets/Art/revision_armament/labels/'+createHash('sha256').update(display).digest('hex').slice(0,20)+'.png';
  await write(label,canvas.toBuffer('image/png'));
  bank.presentation.labels[display]=label;
 }
 await write(file,bank);
}

export async function refreshArmamentWords({write,read}){
 const tasks=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks,words=await emitArmamentWordTextures({write,tasks});
 const file='Assets/Data/armament_figures_v4.json',bank=await read(file);delete bank.presentation.transcripts;bank.presentation.transcriptsPath='Assets/Data/armament_transcripts_v4.json';
 for(const n of bank.presentation.nodes)if(/^ArSiteWord\d+$/.test(n.id))n.order=3490;
 const c=createCanvas(480,84),ctx=c.getContext('2d');ctx.scale(2,2);ctx.font='24px Armament';ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineJoin='round';ctx.lineWidth=6;ctx.strokeStyle='#171022';ctx.strokeText('래피',120,21,222);ctx.fillStyle='#fff';ctx.fillText('래피',120,21,222);const label='Assets/Art/ui/armament_stream/name_lappy_ko.png';await write(label,c.toBuffer('image/png'));bank.presentation.labels.lappy=label;
 await write(bank.presentation.transcriptsPath,words.transcripts);await write(file,bank);
 const sceneFile='Assets/Scenes/ArmamentHud.hbscene.json',scene=await read(sceneFile);for(const o of scene.objects)if(/^TrialGpu_ArSiteWord\d+$/.test(o.id))o.components.find(c=>c.type==='SpriteRenderer').properties.sortingOrder=3490;await write(sceneFile,scene);
 return {words:Object.values(words.transcripts).map(r=>r.length),textures:words.assets.length,keyForeground:true,storyChanged:false};
}
export async function emitArmamentPresentation({write}){
 GlobalFonts.registerFromPath(path.join(game,'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf'),'Armament');
 const nodes=[],textures={},words={},labels={},aliases={},root='ArmamentRoot',base='Assets/Art/ui/armament_stream/';
 const image=async(name,w,h,paint)=>{const c=createCanvas(w*2,h*2),ctx=c.getContext('2d');ctx.scale(2,2);await paint(ctx);const file=base+name+'.png';await write(file,c.toBuffer('image/png'));textures[name]=file;return file;};
 const text=async(value,{color='#fff',size=38,width=600,height=80}={})=>{const key=createHash('sha256').update(value+color+size+width+height).digest('hex').slice(0,16);return image(key,width,height,ctx=>{ctx.font=size+'px Armament';ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineJoin='round';ctx.lineWidth=6;ctx.strokeStyle='#171022';ctx.strokeText(value,width/2,height/2,width-18);ctx.fillStyle=color;ctx.fillText(value,width/2,height/2,width-18);});};
 const add=(id,rect,texture='',order=3000)=>nodes.push({id,parent:root,image:true,rect,alignment:[0,0],texture,visible:false,opacity:1,order});
 const original=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/armament/manifest.json'),'utf8')),sourceLayout=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/armament/layout.json'),'utf8')),sourceFiles={};
 const source=async(container,resource)=>{const key=container+'/'+resource;if(sourceFiles[key])return sourceFiles[key];const row=original.textures.find(r=>r.container===container&&r.resource===resource);if(!row)throw Error('Missing original armament UI '+key);const file=base+'original/'+container+'/'+resource+'.png';await write(file,await fs.readFile(path.join(repo,row.file)));sourceFiles[key]=file;return file;};
 for(const [key,shape]of [['w','triangle'],['d','circle'],['s','cross'],['a','square']])textures['button_'+key]=await source('t_riron_rythm_US','t_riron_rythm_button_'+shape+'_win.png');
 textures.core=await source('t_riron_rythm_US','t_riron_rythm_base.png');textures.hold=await source('t_riron_rythm_US','t_riron_rythm_base_nagaosi.png');textures.mash=await source('t_riron_rythm_US','t_riron_rythm_renda_gauge_base.png');
 for(const [name,resource]of [['ring','normal'],['hold_ring','nagaoshi'],['mash_ring','renda']]){
  const half=await loadImage(path.join(game,await source('t_riron_rythm_US','t_riron_rythm_gauge_'+resource+'_DXT1.png')));
  await image(name,256,256,ctx=>{ctx.drawImage(half,128,0,128,256);ctx.translate(128,128);ctx.rotate(Math.PI);ctx.drawImage(half,0,-128,128,256);});
 }
 textures.hold_label=await source('t_riron_rythm_US','t_riron_hold_tx_US.png');
 textures.hold_icon=await source('t_riron_rythm_US','t_riron_hold_ico_000.png');
 textures.mash_key=await source('t_riron_rythm_US','t_riron_rythm_renda_button_all_win.png');
 const rhythm=sourceLayout.t_riron_rythm_US.states;
 const siteRects={};
 for(const [key,state,part]of [['core','fl_wait','p_base/1'],['key','fl_wait','p_bt/1'],['holdLabel','fl_nagaosi_wait','p_hold_stop/1'],['holdIcon','fl_nagaosi_wait','p_hold_stop/2']]){
  const leaf=rhythm[state].find(r=>r.path===part);if(!leaf)throw Error('Missing source site quad '+part);siteRects[key]=leaf.rect;
 }
 // Keep the supplied PC WASD bitmap square, at its own pixel size.
 siteRects.mashKey=[-32,-32,64,64];
 const core=await loadImage(path.join(game,textures.core)),hold=await loadImage(path.join(game,textures.hold));
 textures.hold=await image('source_hold_layers',256,256,ctx=>{ctx.drawImage(core,0,0);ctx.drawImage(hold,0,0);});
 const rhythmPart=async(state,resource)=>{const row=rhythm[state].find(r=>r.resource===resource);if(!row)throw Error('Missing authored rhythm part '+resource);return{row,img:await loadImage(path.join(game,await source('t_riron_rythm_US',resource)))};};
 // Source local rects are 1280-space; restore the original 256-square site plane.
 const drawPart=(ctx,{row,img})=>{const [x,y,w,h]=row.rect.map(v=>v*1.5);ctx.save();ctx.translate(128+x+w/2,128+y+h/2);ctx.rotate(row.rotation*Math.PI/180);ctx.globalAlpha=row.opacity;ctx.drawImage(img,-w/2,-h/2,w,h);ctx.restore();};
 const holdBase=await rhythmPart('fl_nagaosi_wait','t_riron_rythm_nagaoshi_gauge_base.png'),holdFill=await rhythmPart('fl_nagaosi_wait','t_riron_rythm_nagaoshi_gauge_gauge_DXT1.png');
 // Reveal only authored gauge pixels clockwise through its original upper-right quadrant.
 const fillCanvas=createCanvas(holdFill.img.width,holdFill.img.height),fillCtx=fillCanvas.getContext('2d');fillCtx.drawImage(holdFill.img,0,0);const fillPixels=fillCtx.getImageData(0,0,fillCanvas.width,fillCanvas.height);
 for(let progress=0;progress<=20;progress++){
  const c=createCanvas(fillCanvas.width,fillCanvas.height),ctx=c.getContext('2d'),pixels=ctx.createImageData(c.width,c.height);pixels.data.set(fillPixels.data);
  for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){const fraction=(Math.atan2(y+.5-c.height,x+.5)+Math.PI/2)/(Math.PI/2);if(fraction>progress/20)pixels.data[(y*c.width+x)*4+3]=0;}
  ctx.putImageData(pixels,0,0);await image('hold_progress_'+progress,256,256,paint=>{drawPart(paint,holdBase);drawPart(paint,{row:holdFill.row,img:c});});
 }
 const mashBase=await rhythmPart('fl_renda_wait','t_riron_rythm_renda_gauge_base.png'),mashDots=[];
 for(let i=0;i<10;i++)mashDots.push(await rhythmPart('fl_renda_wait','t_riron_rythm_renda_memori_'+String(i).padStart(3,'0')+'.png'));
 for(let progress=0;progress<=10;progress++)await image('mash_progress_'+progress,256,256,ctx=>{drawPart(ctx,mashBase);for(let i=0;i<progress;i++)drawPart(ctx,mashDots[i]);});
 textures.finishBackdrop=await source('t_kai_cutin_boushi_JP','t_kai_bg.png');
 textures.spark=await source('t_riron_hit_US','t_riron_ef_critical_DXT1.png');textures.shard=await source('t_riron_hakai','t_riron_hakai_000_DXT1.png');textures.impact=await source('t_riron_hakai','t_riron_hakai_002_DXT1.png');
 await image('clear',8,8,()=>{});
 await image('veil',8,8,ctx=>{ctx.fillStyle='#000';ctx.fillRect(0,0,8,8);});
 await image('white',8,8,ctx=>{ctx.fillStyle='#fff';ctx.fillRect(0,0,8,8);});
 const transformed=new Map();
 const sourceColor=async(container,row)=>{const original=row.resource==='__solid_black'?textures.veil:row.resource==='__solid_white'?textures.white:await source(container,row.resource),mul=row.colorMultiply||[1,1,1],add=row.colorAdd||[0,0,0];if(mul.every(v=>v===1)&&add.every(v=>v===0))return original;const key=original+JSON.stringify([mul,add]);if(transformed.has(key))return transformed.get(key);const img=await loadImage(path.join(game,original)),c=createCanvas(img.width,img.height),ctx=c.getContext('2d');ctx.drawImage(img,0,0);const pixels=ctx.getImageData(0,0,img.width,img.height);for(let at=0;at<pixels.data.length;at+=4)for(let i=0;i<3;i++)pixels.data[at+i]=Math.round(Math.min(255,Math.max(0,pixels.data[at+i]*mul[i]+add[i]*255)));ctx.putImageData(pixels,0,0);const file=original.replace('.png', '_'+createHash('sha256').update(key).digest('hex').slice(0,10)+'.png');await write(file,c.toBuffer('image/png'));transformed.set(key,file);sourceFiles[key]=file;return file;};
 // Clip each source layer by its authored depth-range masks before adaptation.
 // This is the moving alpha mask that draws the two ink-circle halves.
 const masked=new Map();
 const sourceMasked=async(container,row)=>{
  const original=await sourceColor(container,row);if(!row.clips?.length)return original;
  const key=JSON.stringify([original,row.rect,row.rotation,row.clips]);if(masked.has(key))return masked.get(key);
  const img=await loadImage(path.join(game,original)),c=createCanvas(img.width,img.height),ctx=c.getContext('2d');ctx.drawImage(img,0,0);
  const angle=-row.rotation*Math.PI/180,co=Math.cos(angle),si=Math.sin(angle),cx=row.rect[0]+row.rect[2]/2,cy=row.rect[1]+row.rect[3]/2;
  for(const group of row.clips){const mask=createCanvas(img.width,img.height),m=mask.getContext('2d');
   m.scale(img.width/row.rect[2],img.height/row.rect[3]);m.translate(row.rect[2]/2,row.rect[3]/2);m.transform(co,si,-si,co,0,0);m.translate(-cx,-cy);
   for(const clip of group){const p=await loadImage(path.join(game,await sourceColor(container,clip))),r=clip.rect;m.save();m.translate(r[0]+r[2]/2,r[1]+r[3]/2);m.rotate(clip.rotation*Math.PI/180);m.globalAlpha=clip.opacity;m.drawImage(p,-r[2]/2,-r[3]/2,r[2],r[3]);m.restore();}
   ctx.globalCompositeOperation='destination-in';ctx.drawImage(mask,0,0);
  }
  const file=base+'masked_'+createHash('sha256').update(key).digest('hex').slice(0,16)+'.png';await write(file,c.toBuffer('image/png'));masked.set(key,file);sourceFiles[key]=file;return file;
 };
 const tasks=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks;
 const {transcripts}=await emitArmamentWordTextures({write,tasks});
 for(const [taskId,task]of Object.entries(tasks)){const s=task.stage;if(s.kind!=='armament')continue;const name=armamentDisplayName(s);labels[s.opponent]=await text(name,{size:24,width:240,height:42});if(s.opponentDisplay)labels[s.opponentDisplay]=labels[s.opponent];}

 for(const [label,res]of [['HIT','hit'],['CRITICAL','critical'],['MISS','miss']])labels[label]=await source('t_riron_hit_US','t_riron_tx_'+res+'_US.png');
 labels['FEVER TIME']=await source('t_riron_frame_US','t_riron_fever_tx_US.png');labels['이론무장']=await source('t_phase_start_riron_JP','t_start_riron_tx_JP.png');labels['마지막 일격']=await source('t_riron_todome_cutin_JP','t_riron_todome_cutin_tx_JP.png');
 // Completion reuses the already approved Korean solving cut-in until its
 // corresponding supplied original is bound below; never invent a new word.
 labels['해결']=await source('t_kai_cutin_boushi_JP','t_kai_tx_JP.png');
 // The approved protagonist image is cropped to the head/shoulders, not shrunk full body.
 const hero=await loadImage(path.join(game,'Assets/Art/armament_v4/player_mio.webp'));
 await image('hero',220,180,ctx=>{const x=hero.width*.25,y=hero.height*.18,w=hero.width*.43,h=hero.height*.55,scale=Math.min(220/w,180/h);ctx.drawImage(hero,x,y,w,h,(220-w*scale)/2,180-h*scale,w*scale,h*scale);ctx.globalCompositeOperation='source-atop';ctx.fillStyle='#09679455';ctx.fillRect(0,0,220,180);});
 const stage=JSON.parse(await fs.readFile(path.join(game,'Assets/UI/Stage.hbwidget.json'),'utf8'));
 for(const n of stage.nodes){if(!(/^(Arm|Piece)/.test(n.id)||n.id==='Ring'||n.id==='RingCore'))continue;if(!['Image','Panel'].includes(n.type))continue;if(n.id.startsWith('ArmHud'))continue;const texture=n.id.startsWith('ArmPieceBand')?await source('t_riron_todome_triangle','t_riron_todome_pl_000.png'):n.properties.texture||'';add(n.id,n.slot.offset,texture,3400+(n.slot.zIndex||0));nodes.at(-1).native=true;}
 const ref=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/armament_rhythm_hud_followup.json'),'utf8'));
 for(const [name,container,res,mask,travel]of [['Hp','t_riron_gauge_US','t_riron_gauge_ht5_DXT1.png','t_riron_gauge_mask.png',438],['Mental','t_riron_gauge_US','t_riron_gauge_st5_DXT1.png','t_riron_gauge_mask.png',332],['Boss','t_riron_enemy_gauge_US','t_riron_enemy_gauge_DXT1.png','t_riron_enemy_gauge_mask.png',-888]]){
  const fill=await loadImage(path.join(game,await source(container,res))),clip=await loadImage(path.join(game,await source(container,mask))),rect=ref[{Hp:'health',Mental:'mental',Boss:'boss'}[name]].parts.fill.first_local_frame_leaves[0].own1280_rect_xywh;
  for(let percent=0;percent<=100;percent++){const file=base+'gauge_'+name+'_'+percent+'.png',c=createCanvas(fill.width,fill.height),ctx=c.getContext('2d');ctx.drawImage(fill,0,0);ctx.globalCompositeOperation='destination-in';ctx.drawImage(clip,travel*(1-percent/100),0);await write(file,c.toBuffer('image/png'));aliases['Assets/Art/ui/arm_'+name+'_'+percent+'.svg']=file;}
  add('ArmHud'+name,rect,aliases['Assets/Art/ui/arm_'+name+'_100.svg'],3450);nodes.at(-1).additive=true;nodes.at(-1).native=true;add('ArmHud'+name+'Track',rect,textures.clear,3449);nodes.at(-1).native=true;
 }
 for(let i=0;i<20;i++){const pair=Math.floor(i/2),kind=pair<5?'s':pair<8?'m':'l',row=String(pair).padStart(3,'0');add('ArmHudTension'+i,ref.tension.nodes[i].first_local_frame_leaves[0].own1280_rect_xywh,await source('t_riron_gauge_US','t_riron_tension_gauge_'+kind+'_5_'+row+'.png'),3451);}
 for(let tension=0;tension<=20;tension++)for(let i=0;i<20;i++){const pair=Math.floor(i/2),kind=pair<5?'s':pair<8?'m':'l',family=Math.min(5,Math.floor(tension/5)+1),resource='t_riron_tension_gauge_'+kind+'_'+family+'_'+String(pair).padStart(3,'0')+'.png';if(original.textures.some(r=>r.container==='t_riron_gauge_US'&&r.resource===resource))textures['tension_'+tension+'_'+i]=await source('t_riron_gauge_US',resource);}
 let staticIndex=0;
 for(const container of ['t_riron_gauge_US','t_riron_enemy_gauge_US','t_riron_frame_US','t_riron_time'])for(const row of sourceLayout[container].states.fl_wait||[]){
  if(/tension_|gauge_[hs]t|enemy_gauge_DXT|enemy_gauge_max|enemy_name|saihara|time_num/.test(row.resource))continue;
  const id='ArOriginal'+staticIndex++;add(id,row.rect,await source(container,row.resource),row.resource.includes('frame')?3200:3390);nodes.at(-1).rotation=row.rotation;nodes.at(-1).initiallyVisible=true;
 }
 for(let i=0;i<9;i++)add('ArClock'+i,[98+[0,26.67,46.67,73.33,100,126.67,153.33,180,206.67][i],638.67,42.67,42.67],await source('t_riron_time','t_riron_time_num_000.png'),3500);
 for(let i=0;i<11;i++)textures['clock_'+i]=await source('t_riron_time','t_riron_time_num_'+String(i).padStart(3,'0')+'.png');
 for(let i=0;i<10;i++)textures['combo_'+i]=await source('t_riron_combo_US','t_riron_combo_num_'+String(i).padStart(3,'0')+'.png');textures.combo=await source('t_riron_combo_US','t_riron_combo_tx_US.png');
 add('ArComboLabel',[1053.33,435.33,170.67,85.33],textures.combo,3500);for(let i=0;i<3;i++)add('ArComboDigit'+i,[1104-i*46,402+i*11.33,85.33,85.33],textures.combo_0,3501);
 // Exact supplied title animation quads, including all child transforms.
 let sourceHeader='#pragma once\n';
 for(const [container,space]of [['t_phase_start_riron_JP','armingintro'],['t_kai_cutin_boushi_JP','armingfinish'],['t_riron_todome_cutin_JP','arminglast']]){
  const files=[],frames=[];
  for(const frame of sourceLayout[container].frames){const rows=[];for(const row of frame){let file;
   if(row.resource.includes('chara')){file=base+'own_cutin_face.png';if(!textures.ownCutin){const old=await loadImage(path.join(repo,original.textures.find(r=>r.container===container&&r.resource===row.resource).file));const face=await loadImage(path.join(game,'Assets/Art/ui/gpu_anagram/result_face.png'));await image('own_cutin_face',old.width,old.height,ctx=>{ctx.drawImage(face,old.width*.18,old.height*.05,old.width*.66,old.height*.9);});textures.ownCutin=file;}}
   else file=await sourceMasked(container,row);
   let index=files.indexOf(file);if(index<0){index=files.length;files.push(file);}const rect=[...row.rect];rows.push([index,...rect,row.rotation,row.opacity]);}if(rows.length>20)throw Error('Too many source armament layers');frames.push(rows);}
  sourceHeader+='namespace '+space+' { struct Leaf{int texture;float x,y,w,h,rotation,alpha;};inline const std::vector<std::vector<Leaf>> frames{'+frames.map(rows=>'{'+rows.map(r=>'{'+r.map((v,i)=>i?Number(v).toFixed(6)+'f':v).join(',')+'}').join(',')+'}').join(',')+'};inline const std::vector<std::string> textures{'+files.map(v=>JSON.stringify(v)).join(',')+'};}\n';
 }
 sourceHeader+='namespace armingsite { struct Rect{float x,y,w,h;};'+Object.entries(siteRects).map(([name,r])=>'inline constexpr Rect '+name+'{'+r.map(v=>v.toFixed(6)+'f').join(',')+'};').join('')+'}\n';
 await write('Source/ArmamentIntroSourceV4.hpp',sourceHeader);
 // Mind Mine already owns a native overlay. Keep its completion layers there,
 // rather than exceeding the shared Stage widget's 256-node limit.
 stage.nodes=stage.nodes.filter(n=>!n.id.startsWith('SolutionNative'));
 const nativeTemplate=stage.nodes.find(n=>n.id==='MineResultBand');if(!nativeTemplate)throw Error('Missing Mind Mine UI image template');
 const nativeFile='Assets/UI/MineHUDV4.hbwidget.json',nativeHUD=JSON.parse(await fs.readFile(path.join(game,nativeFile),'utf8'));nativeHUD.nodes=nativeHUD.nodes.filter(n=>!n.id.startsWith('SolutionNative'));
 for(let i=-1;i<20;i++){const n=structuredClone(nativeTemplate);n.id='SolutionNative'+(i<0?'Back':i);n.name=n.id;n.parent='root';n.slot.offset=[0,0,1280,720];n.slot.zIndex=900+i+1;Object.assign(n.properties,{texture:'',visible:false,opacity:1,rotation:0,color:'#ffffffff'});nativeHUD.nodes.push(n);}
 const {validWidgetAsset}=await import(pathToFileURL(path.join(repo,'../engineCreate/prototype/ui-assets.js')));
 if(!validWidgetAsset(nativeHUD)||!validWidgetAsset(stage))throw Error('Invalid native solution widget ownership, node budget, name or z-order');
 await write(nativeFile,nativeHUD);await write('Assets/UI/Stage.hbwidget.json',stage);
 add('ArFinishBackdrop',[0,0,1280,720],textures.finishBackdrop,4000);nodes.at(-1).parent='ArmIntroRoot';
 for(let i=0;i<20;i++){add('ArIntro'+i,[0,0,100,100],'',4100+i);nodes.at(-1).parent='ArmIntroRoot';}

 // Source display-list leaves, not reconstructed Core/Key/HOLD widgets.
 const sourceSites=await emitArmamentSourceSites({repo,game,write,source,sourceColor,add,createCanvas,loadImage});

 for(let i=0;i<16;i++)add('ArShard'+i,[0,0,22,22],textures.shard,3800);
 add('ArVeil',[0,0,1280,720],textures.veil,4200);nodes.at(-1).parent='ArmIntroRoot';add('ArImpact',[0,0,1280,720],textures.impact,3801);add('ArTitle',[240,260,800,140],'',4100);add('ArRating',[450,200,320,70],'',3800);add('ArFever',[320,60,640,88],labels['FEVER TIME'],3700);add('ArName',[80,50,240,42],'',3450);add('ArHeroName',[1014,649.33,170.67,21.33],await text('미오',{size:25,width:256,height:32}),3450);add('ArCombo',[1020,402,120,90],'',3500);add('ArSpark',[0,0,100,100],textures.spark,3790);
 // PC release uses WASD for final fragments too; no controller-shape/1–4 labels.
 for(let i=0;i<4;i++)nodes.find(n=>n.id==='ArmPieceKey'+i).texture=textures['button_'+['w','d','s','a'][i]];
 applyArmamentFinalButtonSourceRects(nodes,sourceLayout);
 const face=nodes.find(n=>n.id==='ArmFace');face.texture=textures.hero;face.rect=[987,475,182,149];
 const sceneFile='Assets/Scenes/ArmamentHud.hbscene.json',scene=JSON.parse(await fs.readFile(path.join(game,sceneFile),'utf8')),court=JSON.parse(await fs.readFile(path.join(game,'Assets/Scenes/Court.hbscene.json'),'utf8'));
 scene.objects=scene.objects.filter(o=>!o.id.startsWith('TrialGpu_'));
 for(const o of court.objects)if(o.id==='TrialGpu_CourtDim'||o.id.startsWith('TrialGpu_StageClockDigit'))scene.objects.push(structuredClone(o));
 const template=structuredClone(court.objects.find(o=>o.id==='TrialGpu_CourtDim'));if(!template)throw Error('Missing existing GPU sprite template');
 for(const n of nodes){const o=structuredClone(template);o.id='TrialGpu_'+n.id;o.name='armament/'+n.id;o.parent='Camera';const c=o.components.find(c=>c.type==='SpriteRenderer');Object.assign(c.properties,{texture:'',sprite:'',visible:false,sortingOrder:n.order,shading:'unlit',toneMapping:'display',blendMode:n.additive||n.texture.includes('DXT1')||n.id.startsWith('ArSiteRing')?'additive':'translucent'});scene.objects.push(o);}
 await emitArmamentFinalUi({write,scene});const figures=JSON.parse(await fs.readFile(path.join(game,'Assets/Data/armament_figures_v4.json'),'utf8'));figures.presentation={version:4,sourceSites,transcriptsPath:'Assets/Data/armament_transcripts_v4.json',siteRects,nodes,textures,words,labels,aliases,sourceTextures:Object.values(sourceFiles),reference:{video:'pMRvvdS6XmI',observed:[3915,3930,3985,4000,4020,4050],scope:'Original authorized UI pixels and SFL quads; own text/portraits/charts.'}};await write('Assets/Data/armament_transcripts_v4.json',transcripts);await write('Assets/Data/armament_figures_v4.json',figures);await emitSolutionCutinActors({game,write});await emitEndingSource({write});return{gpuActors:nodes.length,claims:Object.values(transcripts).reduce((n,rows)=>n+rows.length,0),source:'pMRvvdS6XmI'};
}
