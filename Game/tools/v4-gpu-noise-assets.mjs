// Ordinary authored noise: preserve Wave using four shared sine/cosine bones.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),sdk=path.resolve(repo,'../engineCreate');
const require=createRequire(path.join(sdk,'package.json')),{createCanvas,loadImage}=require('@napi-rs/canvas');
const {validSpriteRig}=await import(pathToFileURL(path.join(sdk,'prototype/sprite-rig-assets.js')));
const {makeSceneComponent}=await import(pathToFileURL(path.join(sdk,'prototype/scene-components.js')));
const hash=s=>{let n=2166136261;for(const c of Buffer.from(s))n=Math.imul(n^c,16777619);return 'g_'+(n>>>0).toString(16).padStart(8,'0');};
const font='Assets/Fonts/gaegu/Gaegu-Regular.ttf',units=100,size=1.25,depth=860, /* Debate.hpp 잡음 크기·깊이(Claude 2026-11-04) */amplitude=7,frequency=20,phase=.5;
export async function emitGpuNoiseAssets({output,write}){
 const model=await fs.readFile(path.join(game,'Source/Debate.hpp'),'utf8');
 for(const text of ['case Motion::Wave:{' /* 잡음은 글자마다 길로 그린다 — 이 rig 는 게임이 안 쓴다(Yumeno.cpp, Claude 2026-11-05) */,'if(l.kind=="noise")return l.noiseLoud?1.7f:1.4f;'])
  assert(model.includes(text),'Noise model changed; update its exact bake');
 assert(model.includes("c==' '?.26f:c<0x80?.56f:.86f")&&model.includes('return .7f;'));
 const source=JSON.parse(await fs.readFile(path.join(repo,'data/presentation/v4_trial_noise.json'),'utf8'));
 const tasks=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks;
 const rows=Object.entries(source.tasks).filter(([id])=>tasks[id]?.debate?.kind==='nonstop').flatMap(([,t])=>t.noiseSources);
 const crops=new Map();
 const crop=async c=>{
  if(c===' ')return null;if(crops.has(c))return crops.get(c);
  const key=hash([font,40,64,64,'center',c].join('|')),im=await loadImage(path.join(output,'Assets/Art/ui/gpu_trial/'+key+'.png'));
  assert.equal(im.width,384);assert.equal(im.height,384);const canvas=createCanvas(384,384),ctx=canvas.getContext('2d');ctx.drawImage(im,0,0);
  const pixels=ctx.getImageData(0,0,384,384).data;let l=384,t=384,r=-1,b=-1;
  for(let y=0;y<384;y++)for(let x=0;x<384;x++)if(pixels[(y*384+x)*4+3]){l=Math.min(l,x);r=Math.max(r,x);t=Math.min(t,y);b=Math.max(b,y);}
  assert(r>=l&&b>=t,'Authored noise glyph must paint');const image=createCanvas(r-l+1,b-t+1);image.getContext('2d').drawImage(im,l,t,image.width,image.height,0,0,image.width,image.height);
  const result={left:l,top:t,w:image.width,h:image.height,image};crops.set(c,result);return result;
 };
 const bank=[],done=new Set();
 for(const row of rows){
  assert((row.noiseRole||'ordinary')==='ordinary');const chars=[...row.text];assert(chars.length&&chars.length<=26);
  const key=hash(font+'|40|'+row.text);if(done.has(key))continue;done.add(key);
  const entries=new Map();let x=2,y=2,shelf=0;
  for(const c of new Set(chars)){const e=await crop(c);if(!e)continue;if(x+e.w+2>2048){x=2;y+=shelf+4;shelf=0;}entries.set(c,{...e,x,y});x+=e.w+4;shelf=Math.max(shelf,e.h);}
  const aw=Math.max(4,...[...entries.values()].map(e=>e.x+e.w+2)),ah=y+shelf+2;assert(aw<=2048&&aw*ah*4<32*1024*1024);
  const canvas=createCanvas(aw,ah),ctx=canvas.getContext('2d');for(const e of entries.values())ctx.drawImage(e.image,e.x,e.y);
  const prefix='Assets/Art/ui/gpu_noise/'+key,texture=prefix+'.png',sprite=prefix+'.hbsprite.json',asset=prefix+'.hbspriterig.json';
  await write(texture,canvas.toBuffer('image/png'));await write(sprite,{version:1,name:key,texture,normalTexture:'',pixelsPerUnit:1,rect:[0,0,aw,ah],pivot:[.5,.5],filter:'linear',border:[0,0,0,0]});
  const rig={version:1,name:key,sprite,bones:['root','cp','cn','sp','sn'].map(id=>({id,name:id,parent:id==='root'?'':'root',position:[0,0],rotation:0,scale:[1,1],length:1})),vertices:[],triangles:[],clips:[],solvers:[]};
  const em=c=>c===' '?.26:c.codePointAt(0)<128?.56:.86,widths=chars.map(c=>em(c)*40*.7),total=widths.reduce((a,b)=>a+b,0);let off=0;const glyphs=[];
  for(let i=0;i<chars.length;i++){
   const local=off+widths[i]/2-total/2;off+=widths[i];const e=entries.get(chars[i]);if(!e)continue;
   const left=e.left/6-32+local,right=(e.left+e.w)/6-32+local,top=32-e.top/6,bottom=32-(e.top+e.h)/6,u=e.x/aw,v=1-(e.y+e.h)/ah,du=e.w/aw,dv=e.h/ah,at=rig.vertices.length,c=Math.cos(i*phase),s=Math.sin(i*phase);
   const weights=[{bone:c>=0?'cp':'cn',weight:Math.abs(c)/2},{bone:s>=0?'sp':'sn',weight:Math.abs(s)/2},{bone:'root',weight:1-(Math.abs(c)+Math.abs(s))/2}].filter(w=>w.weight>1e-10);
   for(const [px,py,ux,uy]of [[left,bottom,u,v],[right,bottom,u+du,v],[left,top,u,v+dv],[right,top,u+du,v+dv]])rig.vertices.push({position:[px/units,py/units],uv:[ux,uy],weights});
   rig.triangles.push(at,at+1,at+3,at,at+3,at+2);glyphs.push({index:i,vertex:at,local,cropCenter:[(e.left+e.w/2)/6-32,32-(e.top+e.h/2)/6]});
   for(let time=0;time<=1;time+=.025){const a=-2*amplitude/size*Math.sin(frequency*time),b=-2*amplitude/size*Math.cos(frequency*time),offset={root:0,cp:a,cn:-a,sp:b,sn:-b};assert(Math.abs(weights.reduce((n,w)=>n+w.weight*offset[w.bone],0)+amplitude/size*Math.sin(frequency*time+i*phase))<1e-10);}
  }
  assert(validSpriteRig(rig));await write(asset,rig);bank.push({key,sprite,rig:asset,count:chars.length,firstLocal:widths[0]/2-total/2,glyphs});
 }
 const sceneFile='Assets/Scenes/DebateHud.hbscene.json',scene=JSON.parse(await fs.readFile(path.join(output,sceneFile),'utf8'));
 assert(scene.objects.some(o=>o.id==='TrialSpeakerDepth'));scene.objects=scene.objects.filter(o=>!o.id.startsWith('TrialBatch_Noise'));
 for(let i=0;i<3;i++)scene.objects.push({id:'TrialBatch_Noise'+i,name:'Ordinary noise '+i,kind:'sprite',parent:'TrialSpeakerDepth',position:[0,0,-.2*depth/900],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('SpriteRenderer',{sprite:'',texture:'',width:.01,height:.01,useCustomSize:true,billboard:false,visible:false,sortingOrder:350+i,shading:'unlit',toneMapping:'display',blendMode:'translucent',castShadow:false,receiveShadow:false}),makeSceneComponent('SpriteSkin',{rig:''})]});
 await write(sceneFile,scene);await write('Assets/Data/gpu_noise_layout.json',{version:1,units,size,depth,amplitude,frequency,phase,bank});
 return{phrases:bank.length,actors:3,sharedBonesPerActor:4,originalWave:true,originalRaster:true,originalDepth:depth};
}
