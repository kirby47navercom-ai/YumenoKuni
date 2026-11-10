// World grading must not recolor the cutin, words or brush wipe above it.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {createWidgetNode} from '../engineCreate/prototype/ui-assets.js';
import {makeSceneComponent} from '../engineCreate/prototype/scene-components.js';
export function resultForeground(widget,data){
 for(const [id,x] of [['LieEyeL',-150],['LieEyeR',1050]]){let n=widget.nodes.find(n=>n.id===id);if(!n){n=createWidgetNode('Image',id,'root');n.name=id;widget.nodes.push(n);}n.slot.offset=[x,180,380,190];n.slot.zIndex=120;Object.assign(n.properties,{texture:'Assets/Art/ui/lie_eye_false.svg',imageFit:'contain',visible:false,padding:0,background:'#00000000',focusable:false});}
 for(const [index,p] of data.planes.entries()){
  let node=widget.nodes.find(n=>n.id===p.id);if(!node){node=createWidgetNode('Image',p.id,'ResultRoot');node.name=p.id;widget.nodes.push(node);}
  node.type='Image';node.parent='ResultRoot';node.slot.offset=p.rect;node.slot.zIndex=index;
  Object.assign(node.properties,{texture:p.texture,imageFit:['ResultHero','ResultPartner','ResultWord','ResultWord2'].includes(p.id)?'contain':'fill',visible:false,background:'#00000000',padding:0,focusable:false});
 }
 assert(widget.nodes.length<=256);return widget;
}
export function lieWorldGrade(scene){
 scene.objects=scene.objects.filter(o=>!o.id.startsWith('ResultFx_'));
 if(!scene.objects.some(o=>o.id==='LieWorldGrade'))scene.objects.push({id:'LieWorldGrade',name:'위증 법정 반전',kind:'empty',position:[0,0,0],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('PostProcessVolume',{enabled:true,unbound:true,priority:100,weight:0,postOverrides:['lookup'],colorLookup:'Assets/Art/ui/lie_world_negative_lut.png',lookupIntensity:1})]});
 return scene;
}
export async function emitLieLookup(write){
 const require=createRequire(new URL('../engineCreate/package.json',import.meta.url)),{createCanvas}=require('@napi-rs/canvas'),n=16,c=createCanvas(n*n,n),ctx=c.getContext('2d'),pixels=ctx.createImageData(n*n,n);
 for(let g=0;g<n;g++)for(let b=0;b<n;b++)for(let r=0;r<n;r++){const i=(g*n*n+b*n+r)*4;pixels.data[i]=Math.round(255*(1-r/(n-1)));pixels.data[i+1]=Math.round(255*(1-g/(n-1)));pixels.data[i+2]=Math.round(255*(1-b/(n-1)));pixels.data[i+3]=255;}
 ctx.putImageData(pixels,0,0);await write('Assets/Art/ui/lie_world_negative_lut.png',c.toBuffer('image/png'));
 const bank=new URL('../../ui/v3_authorized/perjury/',import.meta.url);
 for(const [name,resource] of [['fact','eye_00_JP_DXT1.png'],['false','eye_01_JP_DXT1.png']]){const bytes=await fs.readFile(new URL(resource,bank));await write('Assets/Art/ui/lie_eye_'+name+'.png',bytes);const href='data:image/png;base64,'+bytes.toString('base64');await write('Assets/Art/ui/lie_eye_'+name+'.svg',`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="256" viewBox="0 0 128 64"><defs><filter id="key"><feColorMatrix type="matrix" values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 1 1 1 0 0"/></filter><mask id="ink" maskUnits="userSpaceOnUse" x="0" y="0" width="128" height="64"><image href="${href}" width="128" height="64" filter="url(#key)"/></mask></defs><image href="${href}" width="128" height="64" mask="url(#ink)"/></svg>`);}
}
export async function emitNonstopResultPalette(repo,write){
 const directory=path.join(repo,'ui/v4/debate_feedback');
 for(const [kind,original,tint] of [
  ['refute','#e94320','#22ccff'],
  ['agree','#22ccff','#22ccff'],
 ]){
  for(const name of ['result_scene_'+kind,'result_crack_'+kind,...Array.from({length:5},(_,i)=>'result_'+kind+'_break'+i)]){
   const source=await fs.readFile(path.join(directory,name+'.svg'),'utf8');
   assert(source.includes(original),name+' must use its original palette');
   await write('Assets/Art/ui/nonstop_'+name+'.svg',source.replaceAll(original,tint));
  }
 }
}
export async function emitResultForegroundOnly({root,repo,write}){
 for(const name of await fs.readdir(path.join(repo,'ui/v4/debate_feedback')))if(/\.(svg|webp|png)$/.test(name))await write('Assets/Art/ui/'+name,await fs.readFile(path.join(repo,'ui/v4/debate_feedback',name)));
 const file='Assets/Data/debate_fx.json',data=JSON.parse(await fs.readFile(path.join(root,file),'utf8'));for(const r of JSON.parse(await fs.readFile(path.join(repo,'ui/v4/debate_feedback/hero_manifest.json'),'utf8')).rows)data.textures['Assets/Art/ui/'+path.basename(r.file)]=[r.width,r.height];await write(file,data);
 const ui='Assets/UI/DebateFX.hbwidget.json';await write(ui,resultForeground(JSON.parse(await fs.readFile(path.join(root,ui),'utf8')),data));await emitLieLookup(write);
 for(const name of ['Court','DebateHud','PanicHud']){const file='Assets/Scenes/'+name+'.hbscene.json';await write(file,lieWorldGrade(JSON.parse(await fs.readFile(path.join(root,file),'utf8'))));}
 return {debateFxOnly:true,textures:Object.keys(data.textures).length,worldLookup:true,foreground:'native-ui',engineModified:false};
}
