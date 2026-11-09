import {emitAgreementCast,centerEndingSourceCanvas} from './v4-agreement-cast.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game);
const require=createRequire(path.join(repo,'../engineCreate/package.json'));
const {createCanvas,loadImage}=require('@napi-rs/canvas');

// Crack and final lettering are distinct original timelines. The scene-pixel
// fracture is a separate effect; these assets must not stand in for it.
export async function emitEndingSource({write}){
 const root=path.join(repo,'ui/v3_authorized/endings');
 const inv=JSON.parse(await fs.readFile(path.join(root,'manifest.json'),'utf8'));
 const layout=JSON.parse(await fs.readFile(path.join(root,'layout.json'),'utf8'));
 const names={crack:'t_ronpa_crack',showdownCrack:'t_ronpa_hanron_crack',panicCrack:'t_ronpa_panic_crack_01',agreeCrack:'t_ronpa_sansei_crack',lieInk:'t_ronpa_uso_enogu',complete:'t_minigame_break_US',refuteBreak:'t_ronpa_break_US',panicBreak:'t_ronpa_panic_break_US',agreeBreak:'t_ronpa_sansei_break_US',lieBreak:'t_ronpa_uso_break_US'};
 Object.assign(names,{panicCutin:'t_ronpa_panic_cutin_JP',agreeCutin:'t_ronpa_sansei_momota_JP',lieCutin:'t_ronpa_uso_cutin_boushi_JP',climax:'t_climax_break',nominate:'t_sub_kuro_kettei_JP'});
 for(let i=1;i<=5;i++)names['scrum'+i]='t_zenronpa_cutin_0'+i+'_JP';
 const files=[],banks={},cache=new Map();
 const fileIndex=file=>{let at=files.indexOf(file);if(at<0){at=files.length;files.push(file);}return at;};
 const portraits={},cast=['mio','rin','ken','nana','taiga','ai','rei','sora','haruka','sho','koto','akari','riku','satsuki','yuu','kaede'];
 const variants=[[768,768],[1536,768],[1024,616]];
 // Each original portrait has its own aspect (including the tall right slot).
 // Keep that aspect when swapping our cast; one wide texture stretches faces.
 const portraitVariant=new Map();
 for(const r of inv.textures){
  if(!/(?:chara|cha_body)/.test(r.resource)&&!(r.container===names.climax&&/^hero_/.test(r.resource))&&!(r.container.startsWith('t_zenronpa_cutin_')&&/^t_zenronpa_(?!base_|ef_|line_|tx_)/.test(r.resource)))continue;
  const [rw,rh]=r.size,scale=Math.min(1,1024/Math.max(rw,rh)),dims=[Math.round(rw*scale),Math.round(rh*scale)];
  let variant=variants.findIndex(([w,h])=>Math.abs(w/h-rw/rh)<.0001);
  if(variant<0){variant=variants.length;variants.push(dims);}
  portraitVariant.set(r.container+'/'+r.resource,variant);
 }
 const variantOf=(container,resource,fallback)=>portraitVariant.get(container+'/'+resource)??fallback;
 async function ownFace(slug,variant,pose=''){
  const key='face:'+slug+':'+variant+':'+pose;if(cache.has(key))return cache.get(key);
  const source=slug==='mio'?path.join(repo,'ui/v4/debate_feedback/hero_'+(pose||'refute')+'.webp'):path.join(repo,'ui/v4/debate_feedback/partner_'+slug+'.webp');
  const im=await loadImage(source),[w,h]=variants[variant],c=createCanvas(w,h),ctx=c.getContext('2d');
  // Own approved art only; the original display list still owns every quad.
  const ratio=w/h,crop=im.height*(ratio<.75?.9:ratio<1.3?.6:.4),scale=Math.max(w*.82/im.width,h/crop);
  ctx.drawImage(im,0,0,im.width,crop,(w-im.width*scale)/2,0,im.width*scale,crop*scale);
  const file='Assets/Art/ui/ending_source/face_'+slug+'_'+variant+(pose?'_'+pose:'')+'.png';await write(file,c.toBuffer('image/png'));cache.set(key,file);return file;
 }
 for(const slug of cast){portraits[slug]=[];for(let i=0;i<variants.length;i++)portraits[slug].push(fileIndex(await ownFace(slug,i)));}
 const teamResources=new Map();
 for(let i=1;i<=5;i++){const container=names['scrum'+i];teamResources.set(container,inv.textures.filter(r=>r.container===container&&/^t_zenronpa_(?!chara_|base_|ef_|line_|tx_)/.test(r.resource)).map(r=>r.resource).sort());}
 function portraitRole(container,resource){
  if(container===names.agreeCutin&&resource==='t_ronpa_chara_001.png')return {role:1,variant:variantOf(container,resource,0)};
  const team=teamResources.get(container);if(team&&team.includes(resource))return {role:2+team.indexOf(resource),variant:variantOf(container,resource,2)};
  if(/(?:chara|cha_body)/.test(resource)||container===names.climax&&/^hero_/.test(resource))return {role:0,variant:variantOf(container,resource,team?2:container===names.agreeCutin?0:1)};
  return {role:-1,variant:0};
 }
 async function texture(container,row){
  const key=JSON.stringify([container,row.resource,row.colorMultiply,row.colorAdd,row.clips,row.clips?.length?row.rect:null,row.clips?.length?row.rotation:null]);
  if(cache.has(key))return cache.get(key);
  const source=inv.textures.find(r=>r.container===container&&r.resource===row.resource);
  const solid=row.resource.startsWith('__solid_');
  if(!source&&!solid)throw Error('Missing ending texture '+container+'/'+row.resource);
  const im=source?await loadImage(path.join(repo,source.file)):null;
  const c=createCanvas(im?.width||8,im?.height||8),ctx=c.getContext('2d');
  const portrait=portraitRole(container,row.resource);
  if(portrait.role>=0){
   const pose=container===names.lieCutin?'lie':container===names.agreeCutin?'agree':'refute';
   if(container===names.climax){
    const own=await loadImage(path.join(game,await ownFace('mio',portrait.variant,pose)));ctx.drawImage(own,0,0,c.width,c.height);
   }else{
    // Preserve the original portrait's transparent margins as well as its quad.
    const raw=await loadImage(path.join(repo,'ui/v4/debate_feedback/hero_'+pose+'.webp'));
    const probe=createCanvas(im.width,im.height),pc=probe.getContext('2d');pc.drawImage(im,0,0);const alpha=pc.getImageData(0,0,im.width,im.height).data;
    let left=im.width,top=im.height,right=0,bottom=0;
    for(let y=0;y<im.height;y++)for(let x=0;x<im.width;x++)if(alpha[(y*im.width+x)*4+3]>8){left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x+1);bottom=Math.max(bottom,y+1);}
    if(right<=left||bottom<=top){left=top=0;right=c.width;bottom=c.height;}
    const crop=raw.height*.6,scale=(bottom-top)/crop;
    ctx.drawImage(raw,0,0,raw.width,crop,(left+right-raw.width*scale)/2,top,raw.width*scale,crop*scale);
   }
  }else if(im)ctx.drawImage(im,0,0);else{ctx.fillStyle=row.resource==='__solid_black'?'#000':'#fff';ctx.fillRect(0,0,c.width,c.height);}
  const mul=row.colorMultiply||[1,1,1],add=row.colorAdd||[0,0,0];
  const pixels=ctx.getImageData(0,0,c.width,c.height);
  for(let at=0;at<pixels.data.length;at+=4){
   if(row.resource.includes('DXT1'))pixels.data[at+3]=Math.max(pixels.data[at],pixels.data[at+1],pixels.data[at+2]);
   for(let i=0;i<3;i++)pixels.data[at+i]=Math.round(Math.min(255,Math.max(0,pixels.data[at+i]*mul[i]+add[i]*255)));
  }
  ctx.putImageData(pixels,0,0);
  if(row.clips?.length){
   const angle=-row.rotation*Math.PI/180,co=Math.cos(angle),si=Math.sin(angle);
   const [x,y,w,h]=row.rect,cx=x+w/2,cy=y+h/2;
   for(const group of row.clips){
    const mask=createCanvas(c.width,c.height),m=mask.getContext('2d');
    m.scale(c.width/w,c.height/h);m.translate(w/2,h/2);m.transform(co,si,-si,co,0,0);m.translate(-cx,-cy);
    for(const clip of group){const file=await texture(container,clip),p=await loadImage(path.join(game,file)),r=clip.rect;m.save();m.translate(r[0]+r[2]/2,r[1]+r[3]/2);m.rotate(clip.rotation*Math.PI/180);m.globalAlpha=clip.opacity;m.drawImage(p,-r[2]/2,-r[3]/2,r[2],r[3]);m.restore();}
    ctx.globalCompositeOperation='destination-in';ctx.drawImage(mask,0,0);
   }
  }
  const file='Assets/Art/ui/ending_source/'+createHash('sha256').update(key).digest('hex').slice(0,20)+'.png';
  await write(file,c.toBuffer('image/png'));cache.set(key,file);return file;
 }
 for(const [name,container]of Object.entries(names)){
  const source=layout[container];if(!source?.frames)throw Error('Missing ending frames '+container);
  banks[name]=[];
  const frameCount=source.labels.fl_in_lang?source.labels.fl_in_lang-source.labels.fl_in:source.frames.length;
  for(const frame of source.frames.slice(0,frameCount)){
   const rows=[];
   for(const row of frame){const file=await texture(container,row),portrait=portraitRole(container,row.resource);rows.push([fileIndex(file),...row.rect,row.rotation,row.opacity,portrait.role>0?portrait.role:-1,portrait.variant]);}
   if(rows.length>48)throw Error('Ending source layer budget '+container);
   banks[name].push(rows);
  }
 }
 let header='#pragma once\nnamespace endingsourcev4 {struct Leaf{int texture;float x,y,w,h,rotation,alpha;int portrait,variant;};\n';
 header+='inline const std::vector<std::string> textures{'+files.map(JSON.stringify).join(',')+'};\n';
 header+='inline const std::map<std::string,std::array<int,'+variants.length+'>> portraits{'+Object.entries(portraits).map(([name,ids])=>'{'+JSON.stringify(name)+',{'+ids.join(',')+'}}').join(',')+'};\n';
 const tasks=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks;
 const targets=Object.values(tasks).filter(t=>t.stage.kind==='armament').map(t=>[Number(t.stage.chapter),t.stage.opponent]);
 header+='inline const std::map<int,std::string> climaxTargets{'+targets.map(([chapter,who])=>'{'+chapter+','+JSON.stringify(who)+'}').join(',')+'};\n';
 header+='}\n';
 for(const [name,frames]of Object.entries(banks)){
  const body='#pragma once\nnamespace endingsourcev4 {inline const std::vector<std::vector<Leaf>> '+name+'Frames{'+frames.map(rs=>'{'+rs.map(r=>'{'+r.map((v,i)=>i>0&&i<7?Number(v).toFixed(6)+'f':v).join(',')+'}').join(',')+'}').join(',')+'};}\n';
  if(Buffer.byteLength(body)>480000)throw Error('Ending source include exceeds native file budget '+name);
  const file='EndingTimeline_'+name+'V4.inl';await write('Source/'+file,body);header+='#include "'+file+'"\n';
 }
 header+='namespace endingsourcev4 {inline const std::map<std::string,std::vector<std::vector<Leaf>>> frames{'+Object.keys(banks).map(name=>'{'+JSON.stringify(name)+','+name+'Frames}').join(',')+'};}\n';
 await write('Source/EndingSourceFramesV4.hpp',header);
 const template=JSON.parse(await fs.readFile(path.join(game,'Assets/UI/MineHUDV4.hbwidget.json'),'utf8'));
 const image=template.nodes.find(n=>n.id==='SolutionNative0');
 const widget={...template,name:'W_EndingSourceV4',nodes:[structuredClone(template.nodes[0])]};
 for(let i=-1;i<48;i++){
  const node=structuredClone(image);node.id=node.name=i<0?'EndingBlack':'EndingLeaf'+i;
  node.slot.offset=[0,0,1280,720];node.slot.zIndex=700+i+1;
  Object.assign(node.properties,{texture:'',visible:false,opacity:1});widget.nodes.push(node);
 }
 const black=createCanvas(8,8),ink=black.getContext('2d');ink.fillStyle='#000';ink.fillRect(0,0,8,8);
 await write('Assets/Art/ui/ending_source/black.png',black.toBuffer('image/png'));
 widget.nodes[1].properties.texture='Assets/Art/ui/ending_source/black.png';
 const {validWidgetAsset}=await import('../../../engineCreate/prototype/ui-assets.js');
 centerEndingSourceCanvas(widget);
 if(!validWidgetAsset(widget))throw Error('Invalid ending widget');
 await write('Assets/UI/EndingSourceV4.hbwidget.json',widget);
 await emitAgreementCast({game,repo,write});
 return {timelines:Object.fromEntries(Object.entries(banks).map(([name,frames])=>[name,frames.length])),textures:files.length,scenePixelFractureIncluded:false};
}
