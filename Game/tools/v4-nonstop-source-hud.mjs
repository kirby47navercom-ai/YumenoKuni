import {createRequire} from 'node:module';
import fs from'node:fs/promises';import path from'node:path';import{createWidgetAsset,createWidgetNode,validWidgetAsset}from'../../../engineCreate/prototype/ui-assets.js';
export async function emitNonstopSourceHud({repo,root,write}){
 await write('Assets/Fonts/pretendard/Pretendard-Regular.otf',await fs.readFile(path.join(repo,'fonts/pretendard/Pretendard-Regular.otf')));
 const folder=path.join(repo,'ui/v4/nonstop_hud_source'),data=JSON.parse(await fs.readFile(path.join(folder,'layout.json'),'utf8')),prefix='Assets/Art/ui/nonstop_source/';
 const {createCanvas,loadImage}=createRequire(path.join(repo,'../engineCreate/package.json'))('@napi-rs/canvas');
 for(const name of await fs.readdir(folder))if(name.endsWith('.png')){
  const png=await fs.readFile(path.join(folder,name));
  await write(prefix+name,png);
  if(!/^ammo(?:Cylinder\d+|Frame(?:Shot\d+)?|Plate(?:Left|Middle|Tip))\.png$/.test(name))continue;
  const image=await loadImage(png),canvas=createCanvas(image.width,image.height),ctx=canvas.getContext('2d');
  ctx.drawImage(image,0,0);
  const pixels=ctx.getImageData(0,0,image.width,image.height);
  for(let i=0;i<pixels.data.length;i+=4){
   const [r,g,b]=pixels.data.subarray(i,i+3);
   const accent=Math.max(0,b-r);
   pixels.data[i]=r+accent;
   pixels.data[i+1]=Math.max(0,g-.48*accent);
   pixels.data[i+2]=b-accent;
  }
  ctx.putImageData(pixels,0,0);
  await write(prefix+'panic_'+name,canvas.toBuffer('image/png'));
 }
 await write(prefix+'panic_wash.svg','<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" preserveAspectRatio="none"><defs><radialGradient id="g"><stop stop-color="#7b1927" stop-opacity=".10"/><stop offset="1" stop-color="#410a19" stop-opacity=".48"/></radialGradient></defs><path fill="url(#g)" d="M0 0h1280v720H0z"/></svg>');
 const w=createWidgetAsset('NonstopSourceHud');w.scaleMode='scale';w.scaleRule='fit';Object.assign(w.nodes[0].properties,{background:'#00000000',visible:false,focusable:false});
 const add=(type,id,rect,properties,parent='root',right=false)=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;if(right){n.slot.anchors=[1,0,1,0];n.slot.offset[0]-=1280;}Object.assign(n.properties,{visible:true,focusable:false,padding:0,background:'#00000000',...properties});w.nodes.push(n);return n;};
 const image=(id,key,right=false)=>add('Image',id,data.tiles[key].rect,{texture:prefix+key+'.png',imageFit:'fill'},'root',right);
 image('Status','status',true);image('Hearts','heart5_10',true);image('Stars','star5_10',true);image('Name','name');
 const clockNode=(id,rect,file)=>{const n=add('Image',id,rect,{texture:prefix+file,imageFit:'fill'},'root',true);n.slot.anchors=[1,1,1,1];n.slot.offset[1]-=720;};
 clockNode('Clock',data.tiles.clock.rect,'clock.png');
 for(let i=0;i<9;i++)clockNode('Clock'+i,data.tiles.clockDigits.rects[i],'digit0.png');
 add('Text','Speaker',data.tiles.speakerText.rect,{text:'',font:'Assets/Fonts/pretendard/Pretendard-Regular.otf',fontSize:20,color:'#e2e7f1',wrap:false});
 for(let i=0;i<20;i++)add('Image','Dot'+i,[...data.tiles.dot.positions[i],...data.tiles.dot.rect.slice(2)],{texture:prefix+'dot.png'});
 add('Image','DotActive',data.tiles.dotActive.rect,{texture:prefix+'dotActive.png'});
 const ammo=add('Canvas','Ammo',[0,-270,440,270],{});ammo.slot.anchors=[0,1,0,1];
 const ammoRect=[0,0,440,270];
 add('Image','Cylinder',ammoRect,{texture:prefix+'ammoCylinder0.png',imageFit:'fill'},'Ammo');
 add('Image','AmmoFrame',ammoRect,{texture:prefix+'ammoFrame.png',imageFit:'fill'},'Ammo');
 for(let i=0;i<9;i++)add('Image','AmmoStock'+i,ammoRect,{texture:prefix+'ammoStock'+i+'.png',imageFit:'fill',visible:false},'Ammo');
 const p=data.tiles.ammo.plate;
 add('Canvas','Cartridge',[p.left,p.pivotY-450-p.height/2,300,p.height],{rotation:p.rotation},'Ammo');
 for(const [id,file,x] of [['BulletPlate','Left',0],['PlateMiddle','Middle',p.cap],['PlateTip','Tip',300-p.cap]])add('Image',id,[x,0,p.cap,p.height],{texture:prefix+'ammoPlate'+file+'.png',imageFit:'fill'},'Cartridge');
 add('Text','Bullet',[27,30,246,30],{text:'',font:'Assets/Fonts/pretendard/Pretendard-Medium.otf',fontSize:20,color:'#173b48',wrap:false},'Cartridge');
 const aim=`<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><g fill="none" stroke="#15baff" stroke-width="2"><path d="M14 20L3 32L14 44M50 20L61 32L50 44M20 14L32 3L44 14M20 50L32 61L44 50"/><path d="M12 32L32 12L52 32L32 52Z" stroke-opacity=".5"/></g><g fill="#c9f6ff"><circle cx="32" cy="32" r="1.5"/><circle cx="20" cy="32" r="1.5"/><circle cx="44" cy="32" r="1.5"/><circle cx="32" cy="20" r="1.5"/><circle cx="32" cy="44" r="1.5"/></g><circle cx="46" cy="12" r="7" fill="none" stroke="#efffff" stroke-width="3"/></svg>`;
 await write(prefix+'aim_focus.svg',aim);
 if(!validWidgetAsset(w))throw Error('Invalid source Nonstop HUD');await write('Assets/UI/NonstopSourceHud.hbwidget.json',w);
 const main=JSON.parse(await fs.readFile(path.join(root,'Assets/UI/Main.hbwidget.json'),'utf8'));const runtime={prefix,idleAim:main.nodes.find(n=>n.id==='Aim').properties.texture,hearts:{},stars:{},clock:data.tiles.clock.rect,clockDigits:data.tiles.clockDigits.rects};for(const n of [5,7,10]){runtime.hearts[n]=data.tiles['heart'+n+'_0'].rect;runtime.stars[n]=data.tiles['star'+n+'_0'].rect;}
 runtime.ammo=data.tiles.ammo;
 runtime.speakerMarkerPositions=data.tiles.dotActive.positions;
 await write('Assets/Data/nonstop_source_hud.json',runtime);
 const file='Assets/Data/gpu_trial_layout.json',layout=JSON.parse(await fs.readFile(path.join(root,file),'utf8'));layout.nonstopOriginalClock=runtime;
 await write(file,layout);return{nodes:w.nodes.length,sourceAffine:true,originalClockDigits:true};
}
