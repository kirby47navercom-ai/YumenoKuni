import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {createRequire} from 'node:module';import {pathToFileURL} from 'node:url';import {createHash} from 'node:crypto';
import {emitGpuTrialBatches} from './v4-gpu-trial-batches.mjs';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),sdk=path.resolve(repo,'../engineCreate');
const require=createRequire(path.resolve(repo,'../engineCreate/package.json')),{createCanvas,GlobalFonts}=require('@napi-rs/canvas');
const {paintWidgetText}=await import(pathToFileURL(path.join(sdk,'tools/native-widget-paint.mjs'))),{makeSceneComponent}=await import(pathToFileURL(path.join(sdk,'prototype/scene-components.js')));
const hash=s=>{let h=2166136261;for(const b of Buffer.from(s))h=Math.imul(h^b,16777619);return 'g_'+(h>>>0).toString(16).padStart(8,'0');};
function projectiveGlyphRoot(scene){scene.objects=scene.objects.filter(o=>o.id!=='TrialGlyphMotion');scene.objects.push({id:'TrialGlyphMotion',name:'발언 원근 이동',kind:'empty',parent:'Camera',position:[0,0,0],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[]});for(const o of scene.objects)if(/^TrialGpu_M[FSB]\d+$/.test(o.id))o.parent='TrialGlyphMotion';}
async function nonstopFaces(tasks,direction){
 const source=await fs.readFile(path.join(game,'Source/Yumeno.cpp'),'utf8');
 const voices=new Map([...source.matchAll(/\{"(\w+)",\{"([^"\n]+\.(?:ttf|otf))","([^"\n]+\.(?:ttf|otf))"\}\}/g)].map(m=>[m[1],m[2]])),faces=new Map();
 for(const task of tasks.filter(t=>t.stage.kind==='nonstop'))for(const row of [...(task.debate?.lines||[]),...(direction.extra?.[task.taskId]||[])]){
  const d=direction.debate?.[row.id]||{},packed=(d.acting||'').split('|'),font='Assets/Fonts/'+(packed[6]||d.font||voices.get(row.actor)||'pretendard/Pretendard-Medium.otf');
  if(!faces.has(font))faces.set(font,new Set());
  for(const c of row.text+(d.openingRefutation?.text||''))if(c.trim())faces.get(font).add(c);
 }
 const pink='Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf';
 if(!faces.has(pink))faces.set(pink,new Set());
 for(const task of tasks.filter(t=>t.stage.kind==='nonstop'))for(const row of [...(task.debate?.lines||[]).filter(r=>r.kind==='noise'),...(direction.noise?.[task.taskId]||[])])for(const c of row.text)if(c.trim())faces.get(pink).add(c);
 const followup=JSON.parse(await fs.readFile(path.join(repo,'data/presentation/nonstop_followup.json'),'utf8'));
 for(const row of Object.values(followup.tasks))for(const text of row.extraNoise)for(const c of text)if(c.trim())faces.get(pink).add(c);
 return faces;
}
async function emitNonstopWashes(write){
 for(const [name,inner,outer,center,edge] of [
  ['regret','#24303f','#050715',.13,.76],
  ['suspect','#161318','#050309',.02,.77],
  ['spot','#fce1a0','#130a20',.07,.62],
  ['uneasy','#203357','#0a122c',.19,.58]
 ]){
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720"><defs><radialGradient id="m" cx="50%" cy="43%" r="60%"><stop stop-color="${inner}" stop-opacity="${center}"/><stop offset=".38" stop-color="${outer}" stop-opacity=".16"/><stop offset="1" stop-color="${outer}" stop-opacity="${edge}"/></radialGradient></defs><rect width="1280" height="720" fill="url(#m)"/></svg>`;
  await write('Assets/Art/ui/gpu_trial/nonstop_'+name+'.svg',svg);
 }
}
async function appendTrialGlyphs({source,write,layout,styles}){
 let baked=0;
 for(const [index,[style,required]] of styles.entries()){
  if(!layout.styles.includes(style))layout.styles.push(style);
  const chars=new Set(style.characters);
  const alias='AuthoredTrialFace'+index;assert(GlobalFonts.registerFromPath(path.join(source,style.font),alias));
  const canvas=createCanvas(style.w*6,style.h*6),ctx=canvas.getContext('2d');
  for(const c of required){
   const id=hash([style.font,style.size,style.w,style.h,style.align,c].join('|')),base='Assets/Art/ui/gpu_trial/'+id,texture=base+'.png';
   if(!chars.has(c)||!(await fs.stat(path.join(source,texture)).catch(()=>null))||!(await fs.stat(path.join(source,base+'.hbsprite.json')).catch(()=>null))){
    ctx.clearRect(0,0,canvas.width,canvas.height);paintWidgetText(ctx,'Text',{fontSize:style.size,borderWidth:0,padding:0,color:'#ffffff',align:style.align,text:c,wrap:false},canvas.width,canvas.height,6,alias);
    await write(texture,canvas.toBuffer('image/png'));await write(base+'.hbsprite.json',{version:1,name:id,texture,normalTexture:'',pixelsPerUnit:10000,rect:[0,0,canvas.width,canvas.height],pivot:[.5,.5],filter:'linear',border:[0,0,0,0],glyph:c,font:style.font,fontSize:style.size});baked++;
   }
   chars.add(c);
  }
  style.characters=[...chars].join('');
 }
 return baked;
}

const styleFor=(layout,font,size,w,h)=>layout.styles.find(s=>s.font===font&&s.size===size&&s.w===w&&s.h===h&&s.align==='center')||{font,size,w,h,align:'center',characters:''};

export async function emitRevisedDebateFont({source,write,tasks}){
 const name='Assets/Data/gpu_trial_layout.json',layout=JSON.parse(await fs.readFile(path.join(source,name),'utf8'));
 const cpp=await fs.readFile(path.join(game,'Source/Yumeno.cpp'),'utf8');
 const fonts=new Map([...cpp.matchAll(/\{"(\w+)",\{"([^"\n]+\.(?:ttf|otf))","([^"\n]+\.(?:ttf|otf))"\}\}/g)].map(m=>[m[1],[m[2],m[3]].map(p=>'Assets/Fonts/'+p)]));
 const groups=new Map();
 for(const task of Object.values(tasks))for(const row of task.debate?.lines||[]){
  const f=fonts.get(row.actor);assert(f,'Unbound revised debate font: '+row.actor);
  const specs=row.kind==='noise'?[['Assets/Fonts/jua/Jua-Regular.ttf',40,64,64]]:[[f[0],54,80,80],[f[1],62,80,80]];
  for(const spec of specs){
   const key=spec.join('|');if(!groups.has(key))groups.set(key,[styleFor(layout,...spec),new Set()]);
   for(const char of row.text)if(char.trim())groups.get(key)[1].add(char);
  }
 }
 const baked=await appendTrialGlyphs({source,write,layout,styles:[...groups.values()]});
 await write(name,layout);
 return {baked,styles:groups.size};
}

export async function emitNonstopFont({output,write,direction}){
 const tasks=Object.values(JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks);
 const name='Assets/Data/gpu_trial_layout.json',layout=JSON.parse(await fs.readFile(path.join(output,name),'utf8'));
 const faces=await nonstopFaces(tasks,direction);
 const baked=await appendTrialGlyphs({source:output,write,layout,styles:[...faces].map(([font,required])=>[styleFor(layout,font,54,80,80),required])});
 await write(name,layout);await emitNonstopWashes(write);return {fonts:faces.size,required:[...faces.values()].reduce((n,s)=>n+s.size,0),baked};
}
export async function emitGpuTrialAssets({output,source,prototypeTask,write}){
 await emitNonstopWashes(write);
 const content=await fs.stat(path.join(source,'Content')).then(()=>path.join(source,'Content')).catch(()=>source);
 const manifest=await fs.readFile(path.join(source,'game.hbpack.json'),'utf8').then(JSON.parse).catch(()=>({id:'generated-project'}));
 const main=JSON.parse(await fs.readFile(path.join(content,'Assets/UI/Main.hbwidget.json'),'utf8'));
 const selected=n=>/^(M[FB]|MS|N[FB])\d+$/.test(n.id)||['Aim','TimerPanel','Timer','CourtDim','Whip'].includes(n.id);
 const compact=n=>({id:n.id,parent:n.parent,image:n.type==='Image'||n.id==='CourtDim',rect:n.slot.offset,alignment:n.slot.alignment,...Object.fromEntries(['font','fontSize','text','texture','color','align','visible','opacity'].map(k=>[k,n.properties[k]])),...n.id==='CourtDim'?{texture:'Assets/Art/ui/gpu_trial/court_dim.svg'}:{}});
 const nodes=main.nodes.filter(selected).flatMap(n=>n.id==='Timer'?Array.from({length:9},(_,i)=>({...compact(n),id:'Timer'+i,fontSize:34,rect:[990,660,80,38],alignment:[0,0],align:'left',visible:true,text:''})):[compact(n)]);
 const parents=main.nodes.map(n=>({id:n.id,parent:n.parent,visible:n.properties.visible!==false,opacity:n.properties.opacity??1}));
 const fontsSource=await fs.readFile(path.join(game,'Source/Yumeno.cpp'),'utf8'),fonts=new Map([...fontsSource.matchAll(/\{"(\w+)",\{"([^"\n]+\.(?:ttf|otf))","([^"\n]+\.(?:ttf|otf))"\}\}/g)].map(m=>[m[1],[m[2],m[3]].map(p=>'Assets/Fonts/'+p)]));
 assert(fonts.size===17);const tasks=Object.values(JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks).filter(t=>!prototypeTask||t.taskId===prototypeTask);
 const styles=new Map(),add=(font,size,w,h,align,text)=>{const id=[font,size,w,h,align].join('|');let s=styles.get(id);if(!s)styles.set(id,s={font,size,w,h,align,characters:new Set()});for(const c of text)if(c.trim())s.characters.add(c);};
 const direction=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/trial_direction.json'),'utf8').catch(()=>'{}')); // 연출표 글꼴도 글자판에 넣는다(Claude)
 let all='';for(const task of tasks)for(const l of task.debate?.lines||[]){const copy=(l.text||'')+(direction.debate?.[l.id]?.openingRefutation?.text||'');all+=copy;const f=fonts.get(l.actor)||['Assets/Fonts/pretendard/Pretendard-Medium.otf','Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'];for(const [i,font]of f.entries())add(font,i?62:54,80,80,'center',copy);const df=direction.debate?.[l.id]?.font;if(df){add('Assets/Fonts/'+df,54,80,80,'center',copy);add('Assets/Fonts/'+df,62,80,80,'center',copy);}}
 for(const rows of Object.values(direction.extra||{}))for(const l of rows){all+=l.text;const f=fonts.get(l.actor)||['Assets/Fonts/pretendard/Pretendard-Medium.otf','Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'];for(const [i,font]of f.entries())add(font,i?62:54,80,80,'center',l.text);const df=direction.debate?.[l.id]?.font;if(df){add('Assets/Fonts/'+df,54,80,80,'center',l.text);add('Assets/Fonts/'+df,62,80,80,'center',l.text);}} // 늘린 발언(trial_extra.py, Claude)
 for(const [font,characters] of await nonstopFaces(tasks,direction))add(font,54,80,80,'center',[...characters].join(''));
 // Noise includes authored statements and the model's small stock phrases.
 for(const name of await fs.readdir(path.join(game,'Source')))if(/\.(hpp|cpp)$/.test(name))all+=await fs.readFile(path.join(game,'Source',name),'utf8');
 for(const task of Object.values(JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks))for(const l of task.debate?.lines||[])all+=l.text||'';
 // Noise may be injected from the packaged stock banks, outside task.debate.lines.
 const dataRoot=path.join(content,'Assets/Data');for(const f of await fs.readdir(dataRoot,{recursive:true}))if(f.endsWith('.json'))all+=JSON.stringify(JSON.parse(await fs.readFile(path.join(dataRoot,f),'utf8')));
 const expand=v=>{if(typeof v==='string'){all+=v;try{if(v[0]==='{'||v[0]==='[')expand(JSON.parse(v));}catch{}}else if(v&&typeof v==='object')for(const x of Object.values(v))expand(x);};expand(JSON.parse(await fs.readFile(path.join(game,'Saved/ui-checkpoints/normal-ch3-latest/savegames.json'),'utf8')));
 add('Assets/Fonts/gaegu/Gaegu-Regular.ttf',40,64,64,'center',all);
 add('Assets/Fonts/jua/Jua-Regular.ttf',40,64,64,'center',all); // 잡음은 굵은 주아(Claude 2026-11-05 : 가는 손글씨는 성의 없어 보임)
 const timer=main.nodes.find(n=>n.id==='Timer');add(timer.properties.font,34,80,38,'left','0123456789:'); /* 타이머 판 안에 들어가게(Claude 2026-11-05 : 숫자가 판 밖으로 나옴) */
 const aliases=new Map(),keys=[],byKey=new Map(),timerMetrics={},fontHashes=new Map();let count=0;
 const cache=path.join(game,'Saved/gpu-trial-bake-cache');await fs.mkdir(cache,{recursive:true});
 const painterHash=createHash('sha256').update(await fs.readFile(path.join(sdk,'tools/native-widget-paint.mjs'))).digest('hex');
 for(const style of styles.values()){
  let font=aliases.get(style.font);if(!font){font='TrialFont'+aliases.size;const ok=GlobalFonts.registerFromPath(path.join(content,style.font),font);assert(ok,'Font must match the built package');aliases.set(style.font,font);}
  if(!fontHashes.has(style.font))fontHashes.set(style.font,createHash('sha256').update(await fs.readFile(path.join(content,style.font))).digest('hex'));
  const canvas=createCanvas(style.w*6,style.h*6),ctx=canvas.getContext('2d');
  for(const c of style.characters){const raw=[style.font,style.size,style.w,style.h,style.align,c].join('|'),id=hash(raw);assert(!byKey.has(id)||byKey.get(id)===raw,'Glyph hash collision');if(byKey.has(id))continue;byKey.set(id,raw);keys.push(id);ctx.clearRect(0,0,canvas.width,canvas.height);
   const cacheFile=path.join(cache,createHash('sha256').update('v1|'+painterHash+'|'+fontHashes.get(style.font)+'|'+raw).digest('hex')+'.png');let png=await fs.readFile(cacheFile).catch(e=>{if(e.code==='ENOENT')return null;throw e;});
   if(!png){paintWidgetText(ctx,'Text',{fontSize:style.size,borderWidth:0,padding:0,color:'#ffffff',align:style.align,text:c,wrap:false},canvas.width,canvas.height,6,font);png=canvas.toBuffer('image/png');await fs.writeFile(cacheFile,png);}
   const texture='Assets/Art/ui/gpu_trial/'+id+'.png';await write(texture,png);
   await write('Assets/Art/ui/gpu_trial/'+id+'.hbsprite.json',{version:1,name:id,texture,normalTexture:'',pixelsPerUnit:10000,rect:[0,0,canvas.width,canvas.height],pivot:[.5,.5],filter:'linear',border:[0,0,0,0],glyph:c,font:style.font,fontSize:style.size});
   if(style.align==='left'){ctx.font=(style.size*6)+'px '+font;timerMetrics[c]=ctx.measureText(c).width/6;}count++;
  }
 }
 const layout={nodes,parents,reuseFaces:true,glyphPixelsPerUnit:10000,glyphBakeScale:6,styles:[...styles.values()].map(s=>({...s,characters:[...s.characters].join('')})),timerMetrics};
 await write('Assets/Art/ui/gpu_trial/court_dim.svg',Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" preserveAspectRatio="none"><path fill="#12051f" fill-opacity="0.2" d="M0 0h1280v720H0z"/></svg>'));
 const court=JSON.parse(await fs.readFile(path.join(content,'Assets/Scenes/Court.hbscene.json'),'utf8'));
 for(const n of nodes){if(/^[MN]B\d+$/.test(n.id))continue;const order=(n.id==='CourtDim'?100:n.id==='Whip'?200:n.id.startsWith('MB')?300:n.id.startsWith('NB')?350:n.id.startsWith('MS')?400:n.id.startsWith('MF')?500:n.id.startsWith('NF')?550:n.id==='TimerPanel'?800:n.id==='Aim'?1000:900)+Number(n.id.match(/\d+$/)?.[0]||0);
  court.objects.push({id:'TrialGpu_'+n.id,name:n.id,kind:'sprite',parent:'Camera',position:[0,0,-.2],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('SpriteRenderer',{texture:'',sprite:'',width:.01,height:.01,useCustomSize:n.image,billboard:false,visible:false,sortingOrder:order,shading:'unlit',toneMapping:'display',blendMode:'translucent',castShadow:false,receiveShadow:false})]});
 }
 projectiveGlyphRoot(court);const batches=await emitGpuTrialBatches({output,write,layout,court,prototypeTask});await write('Assets/Data/gpu_trial_layout.json',layout);
 for(const n of main.nodes)if(selected(n))n.properties.visible=false;
 await write('Assets/UI/Main.hbwidget.json',main);await write('Assets/Scenes/Court.hbscene.json',court);
 return {...batches,glyphs:count,fonts:aliases.size,styles:styles.size,actors:nodes.length,prototypeTask:prototypeTask||null,referenceSize:[1280,720],glyphBakeScale:6,sourceBuild:manifest.id};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const build=JSON.parse(await fs.readFile(path.join(game,'Saved/game-trial-work-20261102/current-flat-build-result.json'),'utf8')),projectBatch=process.argv.includes('--project-batches'),output=projectBatch?game:path.join(game,'Saved/game-trial-work-20261102/gpu-hud-candidate');await fs.mkdir(output,{recursive:true});const overrides={};
 if(process.argv.includes('--reuse-glyph-faces')){const index=path.join(game,'Saved/game-trial-work-20261102/gpu-chapter-batches/overrides.json'),sceneFile=path.join(game,'Assets/Scenes/Court.hbscene.json'),layoutFile=path.join(game,'Assets/Data/gpu_trial_layout.json'),scene=JSON.parse(await fs.readFile(sceneFile,'utf8')),layout=JSON.parse(await fs.readFile(layoutFile,'utf8'));scene.objects=scene.objects.filter(o=>!/^TrialGpu_[MN]B\d+$/.test(o.id));layout.reuseFaces=true;await fs.writeFile(sceneFile,JSON.stringify(scene));await fs.writeFile(layoutFile,JSON.stringify(layout));const o=JSON.parse(await fs.readFile(index,'utf8'));o['Content/Assets/Scenes/Court.hbscene.json']=sceneFile;o['Content/Assets/Data/gpu_trial_layout.json']=layoutFile;await fs.writeFile(index,JSON.stringify(o));console.log(JSON.stringify({reuseGlyphFaces:true,removedDuplicateActors:74}));process.exit(0);}
 if(process.argv.includes('--projective-glyphs')){const index=path.join(game,'Saved/game-trial-work-20261102/gpu-chapter-batches/overrides.json'),file=path.join(game,'Assets/Scenes/Court.hbscene.json'),scene=JSON.parse(await fs.readFile(file,'utf8'));projectiveGlyphRoot(scene);await fs.writeFile(file,JSON.stringify(scene));const o=JSON.parse(await fs.readFile(index,'utf8'));o['Content/Assets/Scenes/Court.hbscene.json']=file;await fs.writeFile(index,JSON.stringify(o));console.log(JSON.stringify({projectiveGlyphs:true}));process.exit(0);}
 if(process.argv.includes('--camera-overlay')){
  const index=path.join(game,'Saved/game-trial-work-20261102/gpu-chapter-batches/overrides.json');Object.assign(overrides,JSON.parse(await fs.readFile(index,'utf8')));
  const main=JSON.parse(await fs.readFile(path.join(game,'Assets/UI/Main.hbwidget.json'),'utf8')),n=main.nodes.find(n=>n.id==='Whip'),lp=path.join(game,'Assets/Data/gpu_trial_layout.json'),layout=JSON.parse(await fs.readFile(lp,'utf8'));
  layout.nodes=layout.nodes.filter(n=>n.id!=='Whip');layout.nodes.push({id:n.id,parent:n.parent,image:true,rect:n.slot.offset,alignment:n.slot.alignment,texture:n.properties.texture,visible:false,opacity:1});
  const sp=path.join(game,'Assets/Scenes/Court.hbscene.json'),scene=JSON.parse(await fs.readFile(sp,'utf8'));scene.objects=scene.objects.filter(o=>o.id!=='TrialGpu_Whip');scene.objects.push({id:'TrialGpu_Whip',name:'Whip',kind:'sprite',parent:'Camera',position:[0,0,-.2],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('SpriteRenderer',{texture:'',sprite:'',width:.01,height:.01,useCustomSize:true,billboard:false,visible:false,sortingOrder:200,shading:'unlit',toneMapping:'display',blendMode:'translucent',castShadow:false,receiveShadow:false})]});
  for(const [name,value]of [['Assets/Data/gpu_trial_layout.json',layout],['Assets/Scenes/Court.hbscene.json',scene]]){const file=path.join(game,name);await fs.writeFile(file,JSON.stringify(value));overrides['Content/'+name]=file;}await fs.writeFile(index,JSON.stringify(overrides));console.log(JSON.stringify({cameraOverlay:true,index}));process.exit(0);
 }
 if(process.argv.includes('--natural-sprite-units')){
  const index=path.join(game,'Saved/game-trial-work-20261102/gpu-chapter-batches/overrides.json');Object.assign(overrides,JSON.parse(await fs.readFile(index,'utf8')));
  const base=path.join(game,'Assets/Art/ui/gpu_trial'),files=(await fs.readdir(base)).filter(n=>/^[ag]_[0-9a-f]{8}\.hbsprite\.json$/.test(n));
  for(let i=0;i<files.length;i+=32)await Promise.all(files.slice(i,i+32).map(async n=>{const f=path.join(base,n),d=JSON.parse(await fs.readFile(f,'utf8'));d.pixelsPerUnit=10000;await fs.writeFile(f,JSON.stringify(d));overrides['Content/Assets/Art/ui/gpu_trial/'+n]=f;}));
  const layoutPath=path.join(game,'Assets/Data/gpu_trial_layout.json'),layout=JSON.parse(await fs.readFile(layoutPath,'utf8'));layout.glyphPixelsPerUnit=10000;layout.glyphBakeScale=6;await fs.writeFile(layoutPath,JSON.stringify(layout));overrides['Content/Assets/Data/gpu_trial_layout.json']=layoutPath;
  const scenePath=path.join(game,'Assets/Scenes/Court.hbscene.json'),scene=JSON.parse(await fs.readFile(scenePath,'utf8')),textIds=new Set(layout.nodes.filter(n=>!n.image).map(n=>'TrialGpu_'+n.id));for(const o of scene.objects)if(textIds.has(o.id))o.components.find(c=>c.type==='SpriteRenderer').properties.useCustomSize=false;await fs.writeFile(scenePath,JSON.stringify(scene));overrides['Content/Assets/Scenes/Court.hbscene.json']=scenePath;
  await fs.writeFile(index,JSON.stringify(overrides));console.log(JSON.stringify({naturalSpriteUnits:true,glyphSprites:files.length,index}));process.exit(0);
 }
 if(process.argv.includes('--batches-only')){
  if(!projectBatch)Object.assign(overrides,JSON.parse(await fs.readFile(path.join(output,'overrides.json'),'utf8')));for(const k of Object.keys(overrides))if(/_line\.(png|hbsprite\.json)$/.test(k))delete overrides[k];
  const write=async(name,value)=>{const file=path.join(output,name);await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,Buffer.isBuffer(value)?value:JSON.stringify(value));overrides['Content/'+name]=file;};
  const layout=JSON.parse(await fs.readFile(path.join(output,'Assets/Data/gpu_trial_layout.json'),'utf8')),court=JSON.parse(await fs.readFile(path.join(output,'Assets/Scenes/Court.hbscene.json'),'utf8'));
  const result=await emitGpuTrialBatches({output,write,layout,court});await write('Assets/Data/gpu_trial_layout.json',layout);await write('Assets/Scenes/Court.hbscene.json',court);const index=projectBatch?path.join(game,'Saved/game-trial-work-20261102/gpu-chapter-batches/overrides.json'):path.join(output,'overrides.json');await fs.mkdir(path.dirname(index),{recursive:true});await fs.writeFile(index,JSON.stringify(overrides));console.log(JSON.stringify({...result,index}));process.exit(0);
 }
 const result=await emitGpuTrialAssets({output,source:build.output,prototypeTask:process.argv.includes('--all')?null:'T3-NS-A11',write:async(name,value)=>{const file=path.join(output,name);await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,Buffer.isBuffer(value)?value:JSON.stringify(value));overrides['Content/'+name]=file;}});
 await fs.writeFile(path.join(output,'overrides.json'),JSON.stringify(overrides));await fs.writeFile(path.join(output,'generation.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({output,...result}));
}
