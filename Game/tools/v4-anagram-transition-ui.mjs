import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {trialModeSource} from './v4-panic-showdown-source.mjs';
const repo=path.resolve(import.meta.dirname,'../..'),sdk=path.resolve(repo,'Game/engineCreate');
const {createCanvas,loadImage,GlobalFonts}=createRequire(path.join(sdk,'package.json'))('@napi-rs/canvas');
export async function emitAnagramTransitions(write,add){
 const svg=(w,h,b)=>`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${b}</svg>`;
 for(const name of ['blur','echo']){
  const image=await loadImage(await fs.readFile(path.join(repo,'ui/v3_authorized/anagram_start',name+'.png'))),canvas=createCanvas(image.width,image.height),ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);const pixels=ctx.getImageData(0,0,image.width,image.height);
  // These supplied DXT1 effects encode additive light on opaque black.
  for(let i=0;i<pixels.data.length;i+=4){const a=Math.max(pixels.data[i],pixels.data[i+1],pixels.data[i+2]);if(a)for(let j=0;j<3;j++)pixels.data[i+j]=Math.round(pixels.data[i+j]*255/a);pixels.data[i+3]=a;}
  ctx.putImageData(pixels,0,0);await write('Assets/Art/ui/anagram_intro_'+name+'.png',canvas.toBuffer('image/png'));
 }
 add('Image','AnaIntroEcho',[-12,-36,1304,808],{texture:'Assets/Art/ui/anagram_intro_echo.png',imageFit:'fill'},42);
 add('Image','AnaIntroBlur',[-12,-36,1304,808],{texture:'Assets/Art/ui/anagram_intro_blur.png',imageFit:'fill'},42);
 const source=await trialModeSource();
 await write('Assets/Art/ui/anagram_rays.svg',await source.raster('anagram_rays',1280,720));
 add('Image','AnaIntroRays',[0,0,1280,720],{texture:'Assets/Art/ui/anagram_rays.svg',imageFit:'fill'},41);
 add('Image','AnaEndBlack',[-1280,-720,3840,2160],{texture:'Assets/Art/ui/anagram_dim.svg',imageFit:'fill'},44);
 // The shattered surface uses the actual puzzle background, not generic glass triangles.
 const bg=await loadImage(await fs.readFile(path.join(repo,'ui/v4/trial_modes_source/anagram_background.png'))),silhouette=await loadImage(await fs.readFile(path.join(repo,'ui/v4/trial_modes_source/anagram_silhouette.png')));
 const point=(x,y)=>[x*1280/6+(x>0&&x<6&&y>0&&y<4?Math.sin(x*17+y*11)*43:0),y*180+(x>0&&x<6&&y>0&&y<4?Math.cos(x*13+y*19)*36:0)];
 let count=0,cracks='';
 for(let y=0;y<4;y++)for(let x=0;x<6;x++){
  const a=point(x,y),b=point(x+1,y),c=point(x+1,y+1),d=point(x,y+1);
  for(const triangle of [[a,b,c],[a,c,d]]){
   cracks+=`<path d="M${triangle.map(p=>p.join(' ')).join('L')}Z" fill="none" stroke="#000711" stroke-width="7"/>`;
   const left=Math.floor(Math.min(...triangle.map(p=>p[0]))),top=Math.floor(Math.min(...triangle.map(p=>p[1]))),w=Math.ceil(Math.max(...triangle.map(p=>p[0])))-left,h=Math.ceil(Math.max(...triangle.map(p=>p[1])))-top;
   const canvas=createCanvas(w*3,h*3),ctx=canvas.getContext('2d');ctx.scale(3,3);ctx.translate(-left,-top);ctx.beginPath();triangle.forEach(([u,v],i)=>i?ctx.lineTo(u,v):ctx.moveTo(u,v));ctx.closePath();ctx.clip();ctx.drawImage(bg,0,0,1280,720);ctx.drawImage(silhouette,0,0,1280,720);ctx.strokeStyle='#0b1d30';ctx.lineWidth=2;ctx.stroke();
   const texture=`Assets/Art/ui/anagram_shard_${count}.png`;await write(texture,canvas.toBuffer('image/png'));add('Image','AnaShard'+count,[left,top,w,h],{texture,imageFit:'fill'},46);count++;
  }
 }
 await write('Assets/Art/ui/anagram_result_crack.svg',svg(1280,720,cracks));
 const complete=await loadImage(await fs.readFile(path.join(repo,'ui/v4/debate_feedback/puzzle_complete.svg'))),word=createCanvas(1800,450);
 word.getContext('2d').drawImage(complete,0,0,1800,450);
 await write('Assets/Art/ui/anagram_complete.png',word.toBuffer('image/png'));
 add('Image','AnaEndComplete',[340,285,600,150],{texture:'Assets/Art/ui/anagram_complete.png',imageFit:'fill'},48);
 return count;
}
