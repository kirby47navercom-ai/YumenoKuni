import {publishTrialGlyphHeader} from './publish-trial-glyph-header.mjs';
// Existing SpriteSkin draws a complete statement in a few submissions.
// The same per-letter transforms and alpha still come from the debate model.
import fs from 'node:fs/promises';import path from 'node:path';import {createHash} from 'node:crypto';import {createRequire} from 'node:module';import {pathToFileURL} from 'node:url';import assert from 'node:assert/strict';
import {archiveGpuTrialArtifacts} from './prune-gpu-trial-artifacts.mjs';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),sdk=path.resolve(repo,'../engineCreate'),require=createRequire(path.resolve(repo,'../engineCreate/package.json'));
const {createCanvas,loadImage}=require('@napi-rs/canvas'),{makeSceneComponent}=await import(pathToFileURL(path.join(sdk,'prototype/scene-components.js'))),{validSpriteRig}=await import(pathToFileURL(path.join(sdk,'prototype/sprite-rig-assets.js')));
const sha=b=>createHash('sha256').update(b).digest('hex');
const hash=s=>{let h=2166136261;for(const b of Buffer.from(s))h=Math.imul(h^b,16777619);return 'g_'+(h>>>0).toString(16).padStart(8,'0');};
export async function emitGpuTrialBatches({output:out,write,layout,court:scene,prototypeTask}){
const src=await fs.readFile(path.join(game,'Source/Yumeno.cpp'),'utf8');
const fonts=new Map([...src.matchAll(/\{"(\w+)",\{"([^"\n]+\.(?:ttf|otf))","([^"\n]+\.(?:ttf|otf))"\}\}/g)].map(m=>[m[1],[m[2],m[3]].map(p=>'Assets/Fonts/'+p)]));
const tasks=Object.values(JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks).filter(t=>!prototypeTask||t.taskId===prototypeTask);
// 줄마다 연출표의 글꼴(Claude, 사양서 25) : C++ 이 같은 글꼴로 이 묶음을 찾는다
const direction=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/trial_direction.json'),'utf8').catch(()=>'{}')),directionFont=l=>direction.debate?.[l.id]?.font?'Assets/Fonts/'+direction.debate[l.id].font:null;
// Crop once per font. Individual actors own only a small glyph texture.
const groups=new Map(),glyphRows=new Map(),crops=new Map(),cropCachePath=path.join(game,'Saved/gpu-trial-crop-cache.json'),cropCache=JSON.parse(await fs.readFile(cropCachePath,'utf8').catch(()=>'{"version":1,"entries":{}}'));
const cropPixels=new Map();const pixels=async e=>{if(!cropPixels.has(e.texture))cropPixels.set(e.texture,await loadImage(path.join(out,e.texture)));return cropPixels.get(e.texture);};
const wantedStyles=new Set();for(const task of tasks)for(const l of task.debate?.lines||[]){const weak=l.kind==='weak',font=directionFont(l)||(l.kind==='noise'?'Assets/Fonts/gaegu/Gaegu-Regular.ttf':(fonts.get(l.actor)||['Assets/Fonts/pretendard/Pretendard-Medium.otf','Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'])[weak?1:0]);wantedStyles.add(font+'|'+(l.kind==='noise'?40:weak?62:54));}
for(const st of layout.styles){if(st.align!=='center'||!wantedStyles.has(st.font+'|'+st.size))continue;const probe=createCanvas(st.w*6,st.h*6),pc=probe.getContext('2d');
 for(const c of st.characters){const k=hash([st.font,st.size,st.w,st.h,st.align,c].join('|')),cached=cropCache.entries[k],sourceBytes=await fs.readFile(path.join(out,'Assets/Art/ui/gpu_trial/'+k+'.png')),sourceSHA256=sha(sourceBytes),cachedBytes=cached?.sourceSHA256===sourceSHA256?await fs.readFile(path.join(out,cached.texture)).catch(e=>{if(e.code==='ENOENT')return null;throw e;}):null;if(cachedBytes&&sha(cachedBytes)===cached.cropSHA256){crops.set(st.font+'|'+st.size+'|'+c,cached);await write(cached.texture,cachedBytes);continue;}const im=await loadImage(sourceBytes);pc.clearRect(0,0,probe.width,probe.height);pc.drawImage(im,0,0);const a=pc.getImageData(0,0,probe.width,probe.height).data;let left=probe.width,right=-1,top=probe.height,bottom=-1;
  for(let py=0;py<probe.height;py++)for(let px=0;px<probe.width;px++)if(a[(py*probe.width+px)*4+3]){left=Math.min(left,px);right=Math.max(right,px);top=Math.min(top,py);bottom=Math.max(bottom,py);}if(right<0)continue;
  const w=right-left+1,h=bottom-top+1,canvas=createCanvas(w,h);canvas.getContext('2d').drawImage(im,left,top,w,h,0,0,w,h);const texture='Assets/Art/ui/gpu_trial/'+k+'_crop.png';const png=canvas.toBuffer('image/png');await write(texture,png);
  const metadata={texture,w,h,left,top,box:st.w,sourceSHA256,cropSHA256:sha(png)};crops.set(st.font+'|'+st.size+'|'+c,metadata);cropCache.entries[k]=metadata;
 }
}
await fs.writeFile(cropCachePath,JSON.stringify(cropCache));
// Chapter aliases keep lookup compact; their textures are shared small glyphs, never large atlases.
for(const task of tasks)for(const l of task.debate?.lines||[]){const chapter=task.taskId.split('-')[0],weak=l.kind==='weak',font=directionFont(l)||(l.kind==='noise'?'Assets/Fonts/gaegu/Gaegu-Regular.ttf':(fonts.get(l.actor)||['Assets/Fonts/pretendard/Pretendard-Medium.otf','Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'])[weak?1:0]),size=l.kind==='noise'?40:weak?62:54;groups.set(chapter+'|'+font+'|'+size,{chapter,font,size});}
for(const {chapter,font,size}of groups.values())for(const [cropKey,e]of crops){if(!cropKey.startsWith(font+'|'+size+'|'))continue;const c=cropKey.slice((font+'|'+size+'|').length),raw=[chapter,font,size,c].join('|'),id='a_'+hash(raw).slice(2),key=Number.parseInt(id.slice(2),16),ox=(e.left+e.w*.5)/6-e.box*.5,oy=(e.top+e.h*.5)/6-e.box*.5,row={key,ox,oy,w:e.w/6,h:e.h/6,raw};assert(!glyphRows.has(key)||glyphRows.get(key).raw===raw,'Glyph hash collision');glyphRows.set(key,row);
 await write('Assets/Art/ui/gpu_trial/'+id+'.hbsprite.json',{version:1,name:id,texture:e.texture,normalTexture:'',pixelsPerUnit:10000,rect:[0,0,e.w,e.h],pivot:[.5,.5],filter:'linear',border:[0,0,0,0],logicalOffset:[ox,oy],logicalSize:[e.w/6,e.h/6],glyph:c,font,fontSize:size});
}
layout.pages=[];
layout.batches=[];const done=new Set();
for(const task of tasks)for(const l of task.debate?.lines||[]){const weak=l.kind==='weak',font=directionFont(l)||(l.kind==='noise'?'Assets/Fonts/gaegu/Gaegu-Regular.ttf':(fonts.get(l.actor)||['Assets/Fonts/pretendard/Pretendard-Medium.otf','Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'])[weak?1:0]),size=l.kind==='noise'?40:weak?62:54,box=l.kind==='noise'?64:80,key=hash(font+'|'+size+'|'+l.text);if(done.has(key))continue;done.add(key);
 const chars=[...l.text].slice(0,48),entries=new Map();let x=2,y=2,shelf=0;
 for(const c of new Set(chars)){const e=crops.get(font+'|'+size+'|'+c);if(!e)continue;if(x+e.w+2>2048){x=2;y+=shelf+4;shelf=0;}entries.set(c,{...e,x,y});x+=e.w+4;shelf=Math.max(shelf,e.h);}
 const aw=Math.min(2048,Math.max(4,...[...entries.values()].map(e=>e.x+e.w+2))),ah=y+shelf+2;assert(aw*ah*4<32*1024*1024,'Statement texture must remain small');const canvas=createCanvas(aw,ah),ctx=canvas.getContext('2d');for(const e of entries.values())ctx.drawImage(await pixels(e),e.x,e.y);
 const texture='Assets/Art/ui/gpu_trial/'+key+'_line.png',sprite='Assets/Art/ui/gpu_trial/'+key+'_line.hbsprite.json',asset='Assets/Art/ui/gpu_trial/'+key+'.hbspriterig.json',atlas={entries,width:aw,height:ah};await write(texture,canvas.toBuffer('image/png'));await write(sprite,{version:1,name:key,texture,normalTexture:'',pixelsPerUnit:1,rect:[0,0,aw,ah],pivot:[.5,.5],filter:'linear',border:[0,0,0,0]});
 const rig={version:1,name:key,sprite,bones:[{id:'root',name:'root',parent:'',position:[0,0],rotation:0,scale:[1,1],length:1}],vertices:[],triangles:[],clips:[],solvers:[]};
 for(let i=0;i<chars.length;i++){const c=chars[i],bone='g'+i;rig.bones.push({id:bone,name:bone,parent:'root',position:[0,0],rotation:0,scale:[1,1],length:1});const e=atlas.entries.get(c);if(!e)continue;const at=rig.vertices.length,u=e.x/atlas.width,v=1-(e.y+e.h)/atlas.height,du=e.w/atlas.width,dv=e.h/atlas.height,left=(e.left/6-40)/100,right=((e.left+e.w)/6-40)/100,top=(40-e.top/6)/100,bottom=(40-(e.top+e.h)/6)/100;
  for(const [px,py,uvx,uvy]of [[left,bottom,u,v],[right,bottom,u+du,v],[left,top,u,v+dv],[right,top,u+du,v+dv]])rig.vertices.push({position:[px,py],uv:[uvx,uvy],weights:[{bone,weight:1}]});rig.triangles.push(at,at+1,at+3,at,at+3,at+2);
 }
 assert(validSpriteRig(rig));await write(asset,rig);layout.batches.push({key,rig:asset,sprite,count:chars.length,chapter:task.taskId.split('-')[0]});
}
scene.objects=scene.objects.filter(o=>!o.id.startsWith('TrialBatch_'));
for(const [layer,colors]of [['MB',3],['MS',1],['MF',3]])for(let c=0;c<colors;c++)scene.objects.push({id:'TrialBatch_'+layer+c,name:'Statement '+layer+c,kind:'sprite',parent:'Camera',position:[0,0,-.2],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('SpriteRenderer',{sprite:'',texture:'',width:.01,height:.01,useCustomSize:true,billboard:false,visible:false,sortingOrder:layer==='MB'?300:layer==='NB'?350:layer==='MS'?400:layer==='MF'?500:550,shading:'unlit',toneMapping:'display',blendMode:'translucent',castShadow:false,receiveShadow:false}),makeSceneComponent('SpriteSkin',{rig:''})]});
scene.objects=scene.objects.filter(o=>!o.id.startsWith('TrialWarmup'));
const rows=[...glyphRows.values()].sort((a,b)=>a.key-b.key),f=n=>String(Math.round(n)),header='#pragma once\n#include <cstdint>\n#include <algorithm>\n#include <iterator>\nnamespace gputrialatlasv4 {\nstruct Glyph {std::uint32_t key;std::int16_t ox,oy,w,h;};\ninline constexpr Glyph entries[]={\n'+rows.map(r=>'{0x'+r.key.toString(16)+'u,'+[r.ox*12,r.oy*12,r.w*6,r.h*6].map(f).join(',')+'}').join(',\n')+'\n};\ninline const Glyph* find(std::uint32_t key){auto p=std::lower_bound(std::begin(entries),std::end(entries),key,[](const Glyph& g,std::uint32_t k){return g.key<k;});return p!=std::end(entries)&&p->key==key?p:nullptr;}\n}\n';
const sourceDir=path.join(out,'Source');await fs.mkdir(sourceDir,{recursive:true});await publishTrialGlyphHeader(sourceDir,header);
const obsolete=await archiveGpuTrialArtifacts({output:out,aliases:rows.map(r=>'a_'+r.key.toString(16).padStart(8,'0')+'.hbsprite.json'),batches:layout.batches});
return {batches:layout.batches.length,actors:7,warmupActors:0,croppedGlyphs:rows.length,atlasPages:0,statementTextures:layout.batches.length,obsolete};
}
