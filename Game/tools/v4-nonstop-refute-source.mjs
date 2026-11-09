import fs from 'node:fs/promises';import path from 'node:path';import {createRequire} from 'node:module';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),require=createRequire(path.join(repo,'../engineCreate/package.json')),{createCanvas,loadImage}=require('@napi-rs/canvas');
// Supplied Korean UI, source display-list transforms. No original protagonist art.
export async function emitNonstopRefuteSource({write,widget:target}){
 const bank=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/armament/layout.json'),'utf8')).t_ronpa_cutin_JP;
 const inv=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/armament/manifest.json'),'utf8'));
 const files=[],frames=[],base='Assets/Art/ui/nonstop_refute/',cache=new Map();
 const texture=async resource=>{
  if(cache.has(resource))return cache.get(resource);
  const row=inv.textures.find(r=>r.container==='t_ronpa_cutin_JP'&&r.resource===resource);if(!row)throw Error(resource);
  let bytes=await fs.readFile(path.join(repo,row.file));
  if(resource==='t_ronpa_cha_body.png'){
   const c=createCanvas(2048,1024),ctx=c.getContext('2d'),hero=await loadImage(path.join(repo,'ui/v4/debate_feedback/hero_refute.webp'));
   ctx.drawImage(hero,600,-130,hero.width*1.65,hero.height*1.65);bytes=c.toBuffer('image/png');
  }else{
   const im=await loadImage(bytes),c=createCanvas(im.width,im.height),ctx=c.getContext('2d');ctx.drawImage(im,0,0);const p=ctx.getImageData(0,0,c.width,c.height);
   // Latest user correction keeps the original blue refutation palette.
   for(let i=0;i<p.data.length;i+=4)if(resource.includes('DXT1'))p.data[i+3]=Math.max(p.data[i],p.data[i+1],p.data[i+2]);ctx.putImageData(p,0,0);bytes=c.toBuffer('image/png');
  }
  const file=base+resource;await write(file,bytes);cache.set(resource,file);return file;
 };
 // Build-time rasterization keeps animated scale/size from rerasterizing SVGs
 // during a shot or charge. Only the active debate widget owns these images.
 for(const name of ['shot_normal','shot_lie','impact','charge_ring','focus_veil']){
  const im=await loadImage(path.join(game,'Assets/Art/ui/'+name+'.svg')),c=createCanvas(im.width*2,im.height*2),ctx=c.getContext('2d');ctx.drawImage(im,0,0,c.width,c.height);await write(base+name+'.png',c.toBuffer('image/png'));
 }
 const widgetFile='Assets/UI/DebateFX.hbwidget.json',widget=target||JSON.parse(await fs.readFile(path.join(game,widgetFile),'utf8'));
 for(const [id,name]of [['ShotTrail','shot_normal'],['ShotImpact','impact'],['ChargeRing','charge_ring'],['FocusVeil','focus_veil']])widget.nodes.find(n=>n.id===id).properties.texture=base+name+'.png';await write(widgetFile,widget);
 const count=bank.labels.fl_in_lang-bank.labels.fl_in;
 for(const source of bank.frames.slice(0,count)){
  const rows=[];for(const row of source){const file=await texture(row.resource);let id=files.indexOf(file);if(id<0){id=files.length;files.push(file);}rows.push([id,...row.rect,row.rotation,row.opacity]);}if(rows.length>9)throw Error('Refute layer budget');frames.push(rows);
 }
 let h='#pragma once\nnamespace nonstoprefutev4 {struct Leaf{int texture;float x,y,w,h,rotation,alpha;};\ninline const std::vector<std::string> textures{'+files.map(JSON.stringify).join(',')+'};\ninline const std::vector<std::vector<Leaf>> frames{\n'+frames.map(rs=>'{'+rs.map(r=>'{'+r.map((v,i)=>i?Number(v).toFixed(6)+'f':v).join(',')+'}').join(',')+'}').join(',\n')+'\n};}\n';
 await write('Source/NonstopRefuteSourceV4.hpp',h);return {frames:frames.length,textures:files.length,source:bank.sha256};
}
