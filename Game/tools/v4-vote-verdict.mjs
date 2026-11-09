import fs from 'node:fs/promises';
import path from 'node:path';
import {verdictMachine} from './v4-verdict-machine.mjs';

export const voteAwardPath='Assets/Art/ui/vote_verdict/tally_award.svg';
export const voteAwardArt=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 550 590" width="550" height="590">
<defs><radialGradient id="gold"><stop stop-color="#ffcc70" stop-opacity=".5"/><stop offset="1" stop-color="#e97316" stop-opacity="0"/></radialGradient><linearGradient id="metal" x2="0" y2="1"><stop stop-color="#fff6bb"/><stop offset=".5" stop-color="#ffbe36"/><stop offset="1" stop-color="#b75a08"/></linearGradient></defs>
<ellipse cx="272" cy="276" rx="273" ry="286" fill="url(#gold)"/>
<path d="M300 0h135l115 89v62Z" fill="#c32c1d" stroke="#ff9d36" stroke-width="6"/>
<path d="M420 101l-15 87 32-19 19 20 12-86Z" fill="#d52f1a" stroke="#ffac45" stroke-width="5"/>
<circle cx="447" cy="74" r="51" fill="url(#metal)" stroke="#ffed9c" stroke-width="5"/><circle cx="447" cy="74" r="40" fill="none" stroke="#a85709" stroke-width="3"/>
<path d="M425 74l14 14 29-30" fill="none" stroke="#964308" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M397 30l5 15 15 5-15 5-5 15-5-15-15-5 15-5z" fill="#fff3b0"/>
</svg>`;

export async function emitVoteVerdict({repo,write,set,createCanvas,loadImage,GlobalFonts,landmarks}){
 const base='Assets/Art/ui/vote_verdict/';
 await write(voteAwardPath,voteAwardArt);
 const svg=(w,h,body)=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}">${body}</svg>`;
 await write(base+'cabinet.svg',verdictMachine(svg,false));
 await write(base+'cabinet_angle.svg',verdictMachine(svg,true));
 const tiles=Array.from({length:14},(_,i)=>Array.from({length:34},(_,j)=>{
  const y=530+190*(i/14)**1.8,z=530+190*((i+1)/14)**1.8;
  const x=(j-17)*(32+(y-530)*.32)+640,x2=(j-17)*(32+(z-530)*.32)+640;
  return (i+j)%2===0?`<path d="M${x} ${y}h${32+(y-530)*.32}L${x2+32+(z-530)*.32} ${z}H${x2}Z" fill="#302335"/>`:'';
 }).join('')).join('');
 await write(base+'room.svg',svg(1280,720,`<defs><radialGradient id="wall"><stop stop-color="#47213e"/><stop offset="1" stop-color="#0d071a"/></radialGradient><linearGradient id="shade" x2="0" y2="1"><stop stop-color="#150d23"/><stop offset="1" stop-color="#150d23" stop-opacity="0"/></linearGradient></defs><path fill="url(#wall)" d="M0 0h1280v720H0Z"/><path fill="#22172c" d="M0 530h1280v190H0Z"/>${tiles}<path fill="url(#shade)" d="M0 530h1280v190H0Z"/>`));
 await write(base+'focus.svg',svg(92,75,'<path d="M5 5Q46 -1 87 5L73 70H19Z" fill="#ff669d" fill-opacity=".58" stroke="#fff1fa" stroke-width="5"/><path d="M7 9Q46 3 85 9" fill="none" stroke="#fff8c6" stroke-width="2"/>'));
 const coin=await loadImage(await fs.readFile(path.join(repo,'ui/v3_authorized/all_general/m_coin/coin_00.png.png')));
 for(const [name,tone] of [['silver',[.95,1.01,1.13]],['bronze',[1.12,.82,.64]]]){
  const c=createCanvas(256,256),g=c.getContext('2d');g.drawImage(coin,0,0,256,256);const pixels=g.getImageData(0,0,256,256);
  for(let i=0;i<pixels.data.length;i+=4){
   const gray=.30*pixels.data[i]+.59*pixels.data[i+1]+.11*pixels.data[i+2];
   for(let ch=0;ch<3;ch++)pixels.data[i+ch]=gray*tone[ch];
  }
  g.putImageData(pixels,0,0);await write(base+name+'.png',c.toBuffer('image/png'));
 }
 for(const who of Object.keys(landmarks)){
  const source=await fs.readFile(path.join(repo,'art/space_v4/facility_identity_v1/faces',who+'.png'));
  const face=await loadImage(source);
  if(face.width!==64||face.height!==64)throw Error('Unexpected verdict dot size for '+who);
  const dot=createCanvas(128,128),g=dot.getContext('2d');
  g.imageSmoothingEnabled=false;g.drawImage(face,0,0,128,128);
  await write(base+'dot_'+who+'.png',dot.toBuffer('image/png'));
  const sample=createCanvas(32,32),mask=sample.getContext('2d');mask.imageSmoothingEnabled=false;mask.drawImage(face,0,0,32,32);
  const pixels=mask.getImageData(0,0,32,32).data,led=createCanvas(192,192),l=led.getContext('2d');
  for(let y=0;y<32;y++)for(let x=0;x<32;x++){
   const i=(y*32+x)*4;
   if(pixels[i+3]<128)continue;
   const light=.28+.72*(pixels[i]+pixels[i+1]+pixels[i+2])/765;
   l.fillStyle=`rgba(255,20,110,${light*.4})`;l.fillRect(x*6-1,y*6-1,8,8);
   l.fillStyle=`rgba(255,118,169,${light})`;l.fillRect(x*6+1,y*6+1,4,4);
  }
  await write(base+'led_'+who+'.png',led.toBuffer('image/png'));
 }
 const full=[0,0,1280,720];
 for(const [id,file,z] of [['Room','room.svg',140],['SideL','cabinet.svg',141],['SideR','cabinet.svg',141],['Dial','cabinet.svg',142],['Focus','focus.svg',143],['Seal','',145]])
  set('VoteVerdict'+id,full,{texture:file?base+file:''},z);
 for(let i=0;i<16;i++)set('VoteVerdictDot'+i,[0,0,1,1],{},144);
 const name=set('VoteVerdictName',[0,0,1,1],{font:'Assets/Fonts/galmuri/Galmuri11.ttf',align:'center',color:'#ffd27b',wrap:false},146);name.type='Text';
 for(let i=0;i<34;i++)set('VoteVerdictCoin'+i,[0,0,1,1],{texture:base+(i%3===1?'bronze':'silver')+'.png'},148+i);
 set('VoteVerdictDark',full,{background:'#090713ff'},185).type='Panel';
 const close=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/verdict/layout.json'),'utf8')).t_cutin_heitei_US;
 // The US track shares English title glyphs with the opening. Keep the
 // timing and effects from the close track and draw Korean glyphs in their slots.
 if(!GlobalFonts.registerFromPath(path.join(repo,'Game/Assets/Fonts/dokdo/Dokdo-Regular.ttf'),'Verdict Brush'))
  throw Error('Missing brush font for Korean trial closure');
 const glyph=async(name,w,h,letters,color)=>{
  const art=createCanvas(w,h),g=art.getContext('2d');
  g.font=`${w*.72}px "Verdict Brush"`;g.textAlign='center';g.textBaseline='middle';
  g.shadowColor='#158bb8';g.shadowBlur=w*.045;
  g.fillStyle=color;
  letters.forEach((letter,i)=>g.fillText(letter,w/2,h*(i+.5)/letters.length));
  const texture=base+'close_ko_'+name+'.png';
  await write(texture,art.toBuffer('image/png'));return texture;
 };
 const title=await glyph('title',512,1024,['폐','정'],'#eefaff');
 const words=await Promise.all([...('학급재판')].map((char,i)=>glyph(String(i),512,512,[char],'#89c9e0')));
 const textures=new Map();
 const chunks=[];
 for(let i=0;i<close.frames.length;i+=24){
  const frames=[];
  for(const leaves of close.frames.slice(i,i+24)){
   const rows=[];
   for(const r of leaves){
    if(/^t_start_saiban_tx_US_heitei_/.test(r.resource))continue;
    const word=/^t_start_saiban_tx_US_00([0-3])\.png$/.exec(r.resource);
    if(word||r.resource==='t_start_tx_US_heitei.png'){
     rows.push([word?words[Number(word[1])]:title,...r.rect,r.rotation,r.opacity]);
     continue;
    }
    if(!textures.has(r.texture)){
     const asset=base+'close_'+(r.texture?path.basename(r.texture):'black.svg');
     await write(asset,r.texture?await fs.readFile(path.join(repo,r.texture)):svg(2,2,'<path d="M0 0h2v2H0Z" fill="black"/>'));
     textures.set(r.texture,asset);
    }
    rows.push([textures.get(r.texture),...r.rect,r.rotation,r.opacity]);
   }
   frames.push(rows);
  }
  const file=`Assets/Data/v4_story/vote_close_${i/24}.json`;
  await write(file,{frames});chunks.push(file);
 }
 return {frames:close.frames.length,chunks};
}
