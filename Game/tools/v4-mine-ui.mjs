import {solutionCutin} from './v4-solution-cutin.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../engineCreate/prototype/ui-assets.js';
const repoRoot=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
async function mineSource(){
 const manifest=JSON.parse(await fs.readFile(path.join(repoRoot,'ui/v4/mine_source/manifest.json'),'utf8'));
 return async(name,w,h)=>{const r=manifest.records[name];if(!r)throw Error('Missing original Imagination UI '+name);const bytes=await fs.readFile(path.join(repoRoot,r.file));if(createHash('sha256').update(bytes).digest('hex')!==r.sha256)throw Error('Changed original Imagination UI '+name);return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><image href="data:image/png;base64,${bytes.toString('base64')}" width="${w}" height="${h}" preserveAspectRatio="none"/></svg>`;};
}
export async function emitMineVisuals({write}){
 const raster=await mineSource(),base='Assets/Art/ui/';
 await write(base+'mine_cursor.svg',await raster('cursor_0',80,80));
 for(let i=0;i<5;i++)await write(base+`mine_cursor_${i}.svg`,await raster('cursor_'+i,80,80));
 for(let i=1;i<=2;i++)await write(base+`mine_hit_${i}.svg`,await raster('hit_'+i,80,80));
 for(const name of ['w','p','y','b']){
  for(const suffix of ['', '_break',...Array.from({length:15},(_,i)=>'_edge'+(i+1))])await write(base+'mine_'+name+suffix+'.svg',await raster('tile_'+name+suffix,80,80));
 }
 for(const [name,w,h]of [['stage',1280,720],['meter',24,12],['focus',24,12],['board_frame',1080,600],['bottom_frame',1280,50],['meter_back',258,30]])await write(base+'mine_'+name+'.svg',await raster(name,w,h));
 // Preserve the established own protagonist, solution lettering and result
 // sequence; the source correction here changes the puzzle UI materials only.
 await write(base+'mine_result_band.svg',(await solutionCutin()).combined);
 for(const [name,source]of [['mine_clear','mine_clear'],['mine_complete','puzzle_complete']])await write(base+name+'.svg',await fs.readFile(path.join(repoRoot,'ui/v4/debate_feedback/'+source+'.svg')));
 await write(base+'mine_result_crack.svg',await fs.readFile(path.join(repoRoot,'ui/v4/debate_feedback/result_crack_agree.svg'),'utf8'));
 for(let i=0;i<6;i++)await write(base+`result_shard${i}.svg`,await fs.readFile(path.join(repoRoot,`ui/v4/debate_feedback/result_shard${i}.svg`)));
 await write(base+'result_black.svg',await fs.readFile(path.join(repoRoot,'ui/v4/debate_feedback/result_black.svg')));
}
export function applyMineStage(widget){
 widget.nodes=widget.nodes.filter(n=>n.id!=='MineResultFace'&&n.id!=='MineResultWord');
 let cursor=widget.nodes.find(n=>n.id==='MineCursor');if(!cursor){cursor=createWidgetNode('Image','MineCursor','root');cursor.name='MineCursor';widget.nodes.push(cursor);}cursor.slot.offset=[600,320,80,80];cursor.slot.zIndex=70;Object.assign(cursor.properties,{texture:'Assets/Art/ui/mine_cursor.svg',imageFit:'fill',padding:0,visible:false,focusable:false});
 for(let i=0;i<10;i++){const id='MineObject'+i;let n=widget.nodes.find(n=>n.id===id);if(!n){n=createWidgetNode('Image',id,'root');n.name=id;widget.nodes.push(n);}n.slot.offset=[160,40,100,100];n.slot.zIndex=20;Object.assign(n.properties,{texture:'',imageFit:'fill',padding:0,visible:false,focusable:false});}
 const result=[['Band',[0,0,1280,720],'mine_result_band.svg'],['Crack',[0,0,1280,720],'mine_result_crack.svg'],...Array.from({length:12},(_,i)=>['Shard'+i,[560,280,160,160],`result_shard${i%6}.svg`]),['Black',[0,0,1280,720],'result_black.svg']];
 for(const [i,[suffix,rect,texture]] of result.entries()){const id='MineResult'+suffix;let n=widget.nodes.find(n=>n.id===id);if(!n){n=createWidgetNode('Image',id,'root');n.name=id;widget.nodes.push(n);}n.slot.offset=rect;n.slot.zIndex=suffix==='Black'?103:100+i+(i>=3?1:0);Object.assign(n.properties,{texture:'Assets/Art/ui/'+texture,imageFit:'fill',visible:false,focusable:false});}
 for(const [id,rect,texture]of [['MineBackdrop',[0,0,1280,720],'mine_stage.svg'],['MineHealth',[964,667,260,12],'mine_meter.svg'],['MineFocus',[964,687,260,8],'mine_focus.svg']]){
  let n=widget.nodes.find(n=>n.id===id);if(!n){n=createWidgetNode('Image',id,'root');n.name=id;if(id==='MineBackdrop')widget.nodes.splice(1,0,n);else widget.nodes.push(n);}
  n.slot.offset=rect;Object.assign(n.properties,{texture:'Assets/Art/ui/'+texture,imageFit:'fill',visible:false,focusable:false});
 }
 let timer=widget.nodes.find(n=>n.id==='MineTimer');if(!timer){timer=createWidgetNode('Text','MineTimer','root');timer.name='MineTimer';widget.nodes.push(timer);}
 timer.slot.offset=[430,652,320,58];Object.assign(timer.properties,{font:'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf',fontSize:42,color:'#e9b865',align:'center',visible:false,wrap:false,focusable:false});
 for(const [id,rect,texture,z]of [['MineBoardFrame',[100,48,1080,600],'mine_board_frame.svg',15],['MineBottomFrame',[0,638,1280,50],'mine_bottom_frame.svg',40],['MineMeterBack',[878,649,300,34],'mine_meter_back.svg',41],...Array.from({length:20},(_,i)=>[`${i<10?'MineHealth':'MineFocus'}Segment${i%10}`,[880+(i%10)*29.5,i<10?651:669,28,11],i<10?'mine_meter.svg':'mine_focus.svg',42])]){
  let n=widget.nodes.find(n=>n.id===id);if(!n){n=createWidgetNode('Image',id,'root');n.name=id;widget.nodes.push(n);}n.slot.offset=rect;n.slot.zIndex=z;Object.assign(n.properties,{texture:'Assets/Art/ui/'+texture,imageFit:'fill',visible:false,padding:0,focusable:false});
 }
 for(const [id,label,rect,size,color] of [['MinePenalty','−10초',[0,0,162,52],35,'#ff3e9b'],['MineTimeout','시간 초과',[390,302,500,92],52,'#ff679c']]){
  let n=widget.nodes.find(n=>n.id===id);if(!n){n=createWidgetNode('Text',id,'root');n.name=id;widget.nodes.push(n);}
  n.slot.offset=rect;n.slot.zIndex=96;Object.assign(n.properties,{text:label,font:'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf',fontSize:size,color,align:'center',visible:false,wrap:false,focusable:false});
 }
 timer.slot.offset=[478,647,324,38];timer.slot.zIndex=50;timer.properties.fontSize=30;timer.properties.color='#fff0cd';
 if(widget.nodes.length>256)throw Error('Mine result exceeds Stage widget node budget');return widget;
}
export function mineHintSvg(polygon){
 if(!Array.isArray(polygon)||polygon.length<3||polygon.length>128||polygon.some(p=>!Array.isArray(p)||p.length!==2||p.some(v=>!Number.isFinite(v)||v<0||v>1)))throw Error('Mine hint needs a bounded authored UV polygon');
 const area=polygon.reduce((sum,p,i)=>{const q=polygon[(i+1)%polygon.length];return sum+p[0]*q[1]-q[0]*p[1];},0);if(Math.abs(area)<1e-9)throw Error('Mine hint polygon has zero area');
 const d=polygon.map((p,i)=>(i?'L':'M')+(p[0]*740).toFixed(3)+' '+(p[1]*420).toFixed(3)).join(' ')+' Z';
 return `<svg xmlns="http://www.w3.org/2000/svg" width="740" height="420" viewBox="0 0 740 420" preserveAspectRatio="none"><path d="${d}" fill="none" stroke="#ffdf00" stroke-width="5" stroke-linejoin="round"/><path d="${d}" fill="none" stroke="#ffffff" stroke-width="2" stroke-linejoin="round"/></svg>`;
}
export async function emitMineV4({write}){
 const raster=await mineSource();
 await write('Assets/Art/ui/mine_question.svg',await raster('question',680,52));
 const hud=createWidgetAsset('W_MineHUDV4');hud.scaleMode='scale';hud.scaleRule='fit';
 const vector=(w,h,d)=>`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${d}</svg>`;
 const bank=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../ui/v3_authorized/mine_start');
 for(const [name,w,h] of [['title',2048,1024],['subtitle',1024,64],['blur',2048,1024],['echo',2048,1024],['rays',512,512],['spark',512,256]]){
  const png=await fs.readFile(path.join(bank,(name==='echo'?'title':name)+'.png'));
  if(name==='title'){await write('Assets/Art/ui/mine_entry_title.png',png);continue;}
  if(name==='subtitle'){
   const plate=await fs.readFile(path.join(bank,'subtitle-plate.png'));
   await write('Assets/Art/ui/mine_entry_subtitle.svg',vector(1024,128,`<image href="data:image/png;base64,${plate.toString('base64')}" x="0" y="0" width="1024" height="128" preserveAspectRatio="none"/><image href="data:image/png;base64,${png.toString('base64')}" x="0" y="31" width="1024" height="64"/>`));continue;
  }
  const href='data:image/png;base64,'+png.toString('base64');
  if(name==='echo'){
   // The lit phase has a warm halo outside the Korean strokes and a cool core.
   await write('Assets/Art/ui/mine_entry_echo.svg',vector(w,h,`<defs><filter id="ink" color-interpolation-filters="sRGB">
    <feGaussianBlur in="SourceAlpha" stdDeviation="15" result="spread"/>
    <feColorMatrix in="spread" type="matrix" values="0 0 0 0 1  0 0 0 0 .87  0 0 0 0 .33  0 0 0 1.5 0" result="halo"/>
    <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 .27  0 0 0 0 .86  0 0 0 0 1  0 0 0 .96 0" result="stroke"/>
    <feMerge><feMergeNode in="halo"/><feMergeNode in="stroke"/></feMerge>
   </filter></defs><image href="${href}" width="${w}" height="${h}" filter="url(#ink)"/>`));continue;
  }
  if(name==='rays'||name==='spark'){
   await write('Assets/Art/ui/mine_entry_'+name+'.svg',vector(w,h,`<defs><filter id="light" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0 0 0 0 .37  0 0 0 0 .78  0 0 0 0 1  0 .45 1.35 0 0"/></filter></defs><image href="${href}" width="${w}" height="${h}" filter="url(#light)"/>`));continue;
  }
  // Lift the light encoded against black so it outlines the dark title.
  await write('Assets/Art/ui/mine_entry_blur.svg',vector(w,h,`<defs><filter id="light" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="1 0 0 0 .12  0 1 0 0 .18  0 0 1 0 .18  .45 .85 .35 0 0"/></filter></defs><image href="${href}" width="${w}" height="${h}" filter="url(#light)"/>`));
 }
 await write('Assets/Art/ui/mine_entry_dim.svg',vector(1280,720,'<path fill="#03070d" d="M0 0H1280V720H0Z"/>'));
 for(let i=0;i<4;i++)await write(`Assets/Art/ui/mine_chip_${i}.svg`,await raster('chip_'+i,24,24));
 const layer=(id,rect,texture,z)=>{const n=createWidgetNode('Image',id,'root');n.name=n.id;n.slot.offset=rect;n.slot.zIndex=z;Object.assign(n.properties,{texture:'Assets/Art/ui/'+texture,imageFit:'fill',padding:0,visible:false,focusable:false});hud.nodes.push(n);};
 layer('MineEntryClear',[180,255,920,210],'mine_clear.svg',106);
 layer('MineEntryComplete',[340,285,600,150],'mine_complete.svg',116);
 layer('MineEntryDim',[0,0,1280,720],'mine_entry_dim.svg',80);
 layer('MineEntryBlur',[-12,-36,1304,808],'mine_entry_blur.svg',82);
 layer('MineEntryTitle',[-12,-36,1304,808],'mine_entry_title.png',84);
 layer('MineEntryEcho',[-12,-36,1304,808],'mine_entry_echo.svg',86);
 layer('MineEntryRays',[105,-30,1070,780],'mine_entry_rays.svg',87);
 layer('MineEntrySubtitle',[242,304,796,100],'mine_entry_subtitle.svg',88);
 layer('MineEntrySpark',[424,222,432,216],'mine_entry_spark.svg',89);
 for(let i=0;i<10;i++)layer('MineBurst'+i,[0,0,16+i%3*4,16+i%3*4],'mine_chip_0.svg',92);

 for(const palette of ['g','r'])for(const value of [...Array.from({length:10},(_,i)=>i),'colon'])await write(`Assets/Art/ui/mine_digit_${palette}${value}.svg`,await raster('digit_'+palette+value,20,31));
 for(let i=0;i<9;i++){const n=createWidgetNode('Image','MineClock'+i,'root');n.name=n.id;n.slot.offset=[558+i*18,651,16,25];Object.assign(n.properties,{texture:'Assets/Art/ui/mine_digit_g0.svg',imageFit:'fill',padding:0,visible:false,focusable:false});hud.nodes.push(n);}
 const pointer=createWidgetNode('Image','MineCursor','root');pointer.name=pointer.id;pointer.slot.offset=[600,320,80,80];pointer.slot.zIndex=100;Object.assign(pointer.properties,{texture:'Assets/Art/ui/mine_cursor.svg',imageFit:'fill',padding:0,visible:false,focusable:false});hud.nodes.push(pointer);

 for(const [type,id,rect,props]of [['Image','MineQuestionPlate',[0,580,680,52],{texture:'Assets/Art/ui/mine_question.svg',imageFit:'fill'}],['Text','MineQuestionText',[26,582,648,48],{font:'Assets/Fonts/pretendard/Pretendard-Medium.otf',fontSize:18,color:'#ffffff',wrap:true,align:'left'}],['Text','MineToggle',[28,666,380,40],{font:'Assets/Fonts/pretendard/Pretendard-Medium.otf',fontSize:16,color:'#eeeeee',wrap:false,align:'left'}]]){const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=rect;Object.assign(n.properties,{padding:0,visible:false,focusable:false,...props});hud.nodes.push(n);}
 // Shared source solution renderer paints these retained native layers after success.
 for(let i=-1;i<20;i++){const id=i<0?'SolutionNativeBack':'SolutionNative'+i,n=createWidgetNode('Image',id,'root');n.name=id;n.slot.offset=[0,0,1280,720];n.slot.zIndex=200+i;Object.assign(n.properties,{texture:'',imageFit:'fill',padding:0,visible:false,focusable:false});hud.nodes.push(n);}
 if(!validWidgetAsset(hud))throw Error('Invalid mine question HUD');await write('Assets/UI/MineHUDV4.hbwidget.json',hud);
 const w=createWidgetAsset('W_MineV4');w.scaleMode='scale';w.scaleRule='fit';
 // Legacy keeps its20-column default. V4 paints the chosen grid in bounded batches.
 for(let i=0;i<242;i++){const n=createWidgetNode('Image','Cell'+i,'root');n.name='Cell'+i;n.slot.offset=[270+(i%20)*37,180+Math.floor(i/20)*(420/11),37,420/11];Object.assign(n.properties,{texture:'Assets/Art/ui/mine_w.svg',imageFit:'fill',visible:false,padding:0,focusable:false});w.nodes.push(n);}
 for(let i=0;i<10;i++){const n=createWidgetNode('Image','MineHint'+i,'root');n.name='MineHint'+i;n.slot.offset=[270,180,740,420];Object.assign(n.properties,{texture:'Assets/Art/ui/mine_y.svg',imageFit:'fill',visible:false,padding:0,focusable:false,opacity:.65});w.nodes.push(n);}
 const hit=createWidgetNode('Image','MineHintHit','root');hit.name='MineHintHit';hit.slot.offset=[0,0,48,48];hit.slot.zIndex=25;Object.assign(hit.properties,{texture:'Assets/Art/ui/mine_hit_1.svg',imageFit:'fill',visible:false,padding:0,focusable:false});w.nodes.push(hit);
 if(!validWidgetAsset(w)||w.nodes.length>256)throw Error('Mine widget bounds');await write('Assets/UI/MineV4.hbwidget.json',w);return {nodes:w.nodes.length,maximumCells:242};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
 const write=async(file,data)=>{const target=path.join(root,file),temporary=target+'.tmp';await fs.writeFile(temporary,typeof data==='string'||Buffer.isBuffer(data)?data:JSON.stringify(data,null,1)+'\n');await fs.rename(temporary,target);};
 await emitMineVisuals({write});await emitMineV4({write});await write('Assets/UI/Stage.hbwidget.json',applyMineStage(JSON.parse(await fs.readFile(path.join(root,'Assets/UI/Stage.hbwidget.json'),'utf8'))));console.log(JSON.stringify({mineVisuals:true}));
}
