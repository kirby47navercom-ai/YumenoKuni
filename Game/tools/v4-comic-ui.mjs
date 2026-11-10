// Climax HUD: original supplied/recovered SFL pixels and affine-baked UI.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {fileURLToPath}from'node:url';
import{createWidgetAsset,createWidgetNode,validWidgetAsset}from'../engineCreate/prototype/ui-assets.js';
import{validGameJson}from'../engineCreate/prototype/game-json.js';
const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
export const comicV4Layout={viewport:[1280,720],caption:[275,520,520,98]};
export const comicV4Textures={};
export function extendComicSlots(widget,nodeIds){
 for(let i=8;i<16;i++)for(const prefix of ['SlotI','PreviousSlot']){
  const id=prefix+i;
  if(!widget.nodes.some(node=>node.id===id)){
   const node=structuredClone(widget.nodes.find(node=>node.id===prefix+'0'));
   node.id=node.name=id;
   widget.nodes.push(node);
  }
  if(!nodeIds.includes(id))nodeIds.push(id);
 }
 assert(validWidgetAsset(widget));
 assert(widget.nodes.length<=256);
}
export async function emitV4ComicUI({write,body,head}){
 const source='ui/v4/climax_original_20261106/',target='Assets/Art/ui/climax_v3/',copied=new Set();
 // The one newly required unlock cue; preserve the rest of the approved bank.
 const cue=JSON.parse(await fs.readFile(path.join(repo,'audio/cues.json'),'utf8')).sfx.v3se_464;
 const audioId='v3se_464',clip='Assets/Audio/'+audioId+'.ogg',asset='Assets/Audio/S_'+audioId+'.hbaudioasset.json';
 await write(clip,await fs.readFile(path.join(repo,'audio',cue.file)));
 await write(asset,{version:1,name:'S_'+audioId,priority:128,virtualize:false,streaming:false,clip,volume:.4,pitch:1,loop:false,spatial:false,autoplay:false,refDistance:1,maxDistance:100,rolloff:1,mixer:'Assets/Audio/MX_Yumeno.hbaudiomixer.json',bus:'sfx'});
 const art=JSON.parse(await fs.readFile(path.join(repo,'Game/Assets/Data/art.json'),'utf8'));art.audio[audioId]=asset;if(cue.len)art.audioLen[audioId]=cue.len;await write('Assets/Data/art.json',art);

 const map=async value=>{if(typeof value==='string'&&value.startsWith(source)){const to=target+value.slice(source.length);if(!copied.has(to)){copied.add(to);await write(to,await fs.readFile(path.join(repo,value)));}return to;}if(Array.isArray(value)){const a=[];for(const v of value)a.push(await map(v));return a;}if(value&&typeof value==='object'){const o={};for(const[k,v]of Object.entries(value))if(!['sha256','sourceScale','sourceSHA256','sourceContainer','sourceResource','sourceCrop','sourcePolygon','derivative','provenanceFile','stockSequenceFiles'].includes(k))o[k]=await map(v);return o;}return value;};
 const bank=await map(JSON.parse(await fs.readFile(path.join(repo,source+'runtime.json'),'utf8')));
 bank.stockSequenceFiles={};
 for(const key of ['open','close']){const sequence=await map(JSON.parse(await fs.readFile(path.join(repo,source+'stock_'+key+'.json'),'utf8')));assert(validGameJson(sequence));const to='Assets/Data/climax_stock_'+key+'.json';await write(to,sequence);bank.stockSequenceFiles[key]=to;}
 const bookSource='ui/v4/climax_book_20261107/',bookTarget='Assets/Art/ui/climax_book/';
 const bookMap=async v=>{if(typeof v==='string'&&v.startsWith(bookSource)){const to=bookTarget+v.slice(bookSource.length);if(!copied.has(to)){copied.add(to);await write(to,await fs.readFile(path.join(repo,v)));}return to;}if(Array.isArray(v))return Promise.all(v.map(bookMap));if(v&&typeof v==='object'){const o={};for(const[k,x]of Object.entries(v))o[k]=await bookMap(x);return o;}return v;};
 const books=JSON.parse(await fs.readFile(path.join(repo,bookSource+'manifest.json'),'utf8'));bank.bookFiles={};
 for(const[id,file]of Object.entries(books.books)){const payload=await bookMap(JSON.parse(await fs.readFile(path.join(repo,file),'utf8')));assert(validGameJson(payload));const to='Assets/Data/climax_books/'+id+'.json';await write(to,payload);bank.bookFiles[id]=to;}
 const turns=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/climax_reference_20261107/source-page-transitions.json'),'utf8'));
 // Original root SFL frames; translation is calibrated to this book's video
 // screen scale. This is not a claim to recover the missing camera/FOV.
 bank.pageTurn={};for(const key of ['fl_l_c','fl_r_c'])bank.pageTurn[key]=turns.transitions[key].frames.map(f=>{const d=f.depths.find(d=>d.name==='p_page_01_01');assert(d);return {scale:d.affine[0],dx:(d.affine[4]-446.2)*.4,dy:(d.affine[5]-267.65)*.4,alpha:d.alpha};});
 const widget=createWidgetAsset('ComicV4');widget.scaleMode='scale';widget.scaleRule='fit';
 const add=(type,id,r,properties={},z=0)=>{const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=r;n.slot.zIndex=z;Object.assign(n.properties,{font:body,fontSize:22,color:'#ffffff',background:'#00000000',padding:0,text:'',visible:false,focusable:false,wrap:false,...properties});widget.nodes.push(n);return n;};
 const image=(id,row,z=0,extra={})=>{if(row?.texture)add('Image',id,row.rect,{texture:row.texture,imageFit:'fill',rotation:row.rotation||0,...extra},z);};
 // Neutral halftone only; original case collage/manga never enters our game.
 const backdrop=target+'own_halftone.svg';await write(backdrop,'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><defs><pattern id="h" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#211c32"/><circle cx="2" cy="2" r="2" fill="#30283f"/><circle cx="6" cy="6" r="2" fill="#30283f"/></pattern><radialGradient id="v"><stop stop-color="#29233c" stop-opacity="0"/><stop offset="1" stop-color="#07060d" stop-opacity=".8"/></radialGradient></defs><rect width="1280" height="720" fill="url(#h)"/><rect width="1280" height="720" fill="url(#v)"/></svg>');
 add('Image','Shade',[0,0,1280,720],{texture:backdrop,imageFit:'fill'},0);
 // Opaque overscan keeps the courtroom out of the fit-layout side bars.
 add('Panel','OverscanMask',[-1280,-720,3840,2160],{background:'#08060c'},-1);
 const components={pageBar:'V3PageBar',pageWord:'V3PageWord',pageCounterBase:'V3PageCounter',stockBase:'V3StockBase',stockWord:'V3StockWord',stockExpandedBase:'V3StockExpandedBase',stockExpandedWord:'V3StockExpandedWord',selectedPanelFrame:'V3SelectedFrame',captionPlate:'CaptionPlate',timerBase:'V3TimerBase',cursor:'V3Cursor',placeOK:'V3PlaceOK',placeNG:'V3PlaceNG',selectedUsed:'V3SelectedUsed',selectedLocked:'V3SelectedLocked'};
 bank.componentNodes={};for(const[k,id]of Object.entries(components)){const row=bank.bakedComponents[k];if(row?.texture){image(id,row,k.startsWith('stock')?30:k==='cursor'?90:k.startsWith('place')?85:k==='pageBar'?20:k==='selectedPanelFrame'?36:40);bank.componentNodes[k]=id;}}
 bank.componentNodes.overscan='OverscanMask';
 const referenceSource='ui/v4/climax_reference_20261107/',referenceTarget='Assets/Art/ui/climax_reference/';
 const referenceMap=async v=>{if(typeof v==='string'&&v.startsWith(referenceSource)){const to=referenceTarget+v.slice(referenceSource.length);if(!copied.has(to)){copied.add(to);await write(to,await fs.readFile(path.join(repo,v)));}return to;}if(Array.isArray(v))return Promise.all(v.map(referenceMap));if(v&&typeof v==='object'){const o={};for(const[k,x]of Object.entries(v))o[k]=await referenceMap(x);return o;}return v;};
 const reference=await referenceMap(JSON.parse(await fs.readFile(path.join(repo,referenceSource+'runtime.json'),'utf8')));
 image('OriginalTitle',reference.title,49);bank.componentNodes.title='OriginalTitle';image('V3Koma',reference.koma,48);
 bank.titleFrames=reference.titleFrames;bank.titleDurationFrames=reference.titleDurationFrames;
 add('Image','V3Unlock',[0,0,1,1],{texture:'',imageFit:'fill'},44);
 add('Image','V3StockMorph',[0,0,1,1],{texture:'',imageFit:'fill'},31);
 image('HoleHintPlate',bank.bakedComponents.holeHint0,61);
 add('Text','HoleHint',[0,0,550,90],{fontSize:25,wrap:true,color:'#ffffff'},62);
 add('Text','Caption',comicV4Layout.caption,{fontSize:25,color:'#17151d',wrap:true,rotation:-2},46);
 add('Text','Hint',[285,690,510,25],{fontSize:15,color:'#dfd8ed'},55);
 for(const n of [5,7,10])image('V3HpBase'+n,bank.bakedComponents['heartBase'+n],45);
 for(let i=0;i<10;i++)add('Image','ComicHeart'+i,[0,0,1,1],{texture:'',imageFit:'fill'},46);
 for(let i=0;i<7;i++)image('V3TimeD'+i,{...bank.timerSlots[i],texture:bank.timerDigits[0]},47);
 for(let i=0;i<4;i++)image('V3PageD'+i,{...bank.pageNumberSlots[i],texture:(i<2?bank.pageDigits:bank.pageActiveDigits)[0]},47);
 const q=bank.sharedPageUI.questionPink.texture;
 for(let i=0;i<8;i++){
  add('Image','SlotP'+i,[0,0,1,1],{texture:q,imageFit:'fill'},10);add('Image','SlotI'+i,[0,0,1,1],{texture:'',imageFit:'fill'},11);
  add('Image','PreviousSlot'+i,[0,0,1,1],{texture:'',imageFit:'fill'},4);
  add('Image','StockI'+i,[0,0,1,1],{texture:'',imageFit:'contain'},33);add('Image','StockMark'+i,[0,0,1,1],{texture:'',imageFit:'fill'},32);add('Image','StockFocus'+i,[0,0,1,1],{texture:'',imageFit:'fill'},34);add('Image','StockRemaining'+i,[0,0,1,1],{texture:'',imageFit:'fill'},35);
  add('Image','CandidateP'+i,[0,0,1,1],{texture:'',imageFit:'fill'},37);add('Image','CandidateI'+i,[0,0,1,1],{texture:'',imageFit:'contain'},38);add('Text','CandidateT'+i,[0,0,1,1],{},39);
 }
 add('Image','PageBook',[0,0,1,1],{texture:'',imageFit:'fill'},9);
 add('Image','PreviousBook',[0,0,1,1],{texture:'',imageFit:'fill'},3);
 for(let p=0;p<3;p++){
  add('Image','PageThumbFrame'+p,[0,0,1,1],{texture:'',imageFit:'fill'},22);
  for(let i=0;i<4;i++)add('Image','PageThumb'+p+'_'+i,[0,0,1,1],{texture:'',imageFit:'fill'},23);
  add('Image','PageThumbGlow'+p,[0,0,1,1],{texture:bank.sharedPageUI.pageActiveGlow.presentationTexture||bank.sharedPageUI.pageActiveGlow.texture,imageFit:'fill',rotation:-6},24);
 }
 for(const [id,x,rotation]of[['PageLeft',470,0],['PageRight',692,180]])add('Image',id,[x,75,65,65],{texture:bank.sharedPageUI.pageArrow.texture,imageFit:'contain',rotation},48);
 for(const [id,text,x]of[['PageLeftKey','Q',493],['PageRightKey','E',715]])add('Text',id,[x,91,26,30],{text,font:head,fontSize:18,color:'#fff138'},49);
 add('Image','PlaceImage',[0,0,1,1],{texture:'',imageFit:'contain'},80);
 add('Panel','ZoomShade',[0,0,1280,720],{background:'#08060bf4'},70);add('Image','ZoomImage',[170,80,940,530],{texture:'',imageFit:'contain'},71);add('Text','ZoomCaption',[150,619,980,75],{wrap:true,fontSize:25,align:'center'},72);
 add('Panel','ReplayShade',[-1280,-720,3840,2160],{background:'#000000'},6);
 add('Image','ReplayImage',[38,30,1204,658],{texture:'',imageFit:'fill'},7);
 add('Image','CompletePage',[38,30,1204,658],{texture:'',imageFit:'fill'},7);
 add('Text','ReplayCaptionShadow',[215,589,950,112],{fontSize:26,color:'#000000',wrap:true},8);
 add('Text','ReplayCaption',[212,586,950,112],{fontSize:26,color:'#ffffff',wrap:true},9);
 for(const id of ['Title','SubTitle','PageNo','PageSheetL','PageSheetR','StockNo','StockLeft','StockRight','ComicTimer','ZoomCaptionPlate','HoleHintTail'])add('Text',id,[0,0,1,1],{},1);
 assert(validWidgetAsset(widget));assert(widget.nodes.length<=256);
 bank.nodeIds=widget.nodes.map(n=>n.id).filter(id=>id!=='root');extendComicSlots(widget,bank.nodeIds);assert(validGameJson(bank),'Climax UI bank exceeds native JSON limits');
 await write('Assets/Data/climax_ui_v3.json',bank);await write('Assets/UI/ComicV4.hbwidget.json',widget);
 return{widget:'Assets/UI/ComicV4.hbwidget.json',nodes:widget.nodes.length,textures:copied.size,originalUI:true,originalMangaIncluded:false,localAdaptations:['Own6/8hole manga pages','Video-calibrated page projection; source camera/FOV not claimed'],runtimeVisualAcceptance:false};
}
