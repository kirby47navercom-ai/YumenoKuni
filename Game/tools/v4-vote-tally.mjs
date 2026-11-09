import fs from 'node:fs/promises';
import path from 'node:path';

export async function emitVoteTally({repo,write,base,createCanvas,loadImage}){
 const source=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/trial_inputs_motion/layout.json'),'utf8')).t_tosen_memori_US;
 const first=source.labels.fl_count-1,last=source.labels.fl_out-1;
 const frame=source.states.fl_out;
 const rows=Array.from({length:16},()=>[]);
 const names=[];
 let texture;
 for(const layer of frame){
  const name=/^\/p_name_(\d{3})\/1$/.exec(layer.path);
  if(name){
   const [x,y]=layer.rect;
   names[+name[1]]=[x+640,y+360,layer.rotation];
  }
  const slot=/^\/p_memori_(\d+)_(\d+)\/1$/.exec(layer.path);
  if(!slot)continue;
  rows[+slot[1]][+slot[2]]=layer;
  texture??=await loadImage(await fs.readFile(path.join(repo,layer.texture)));
 }
 const reference=rows[0];
 const basis=reference[0].rect;
 const markAt=(marks,index)=>{
  if(marks[index])return marks[index];
  const first=marks[0],ref=reference[Math.min(index,reference.length-1)].rect;
  const extrapolate=index>=reference.length?index-reference.length+1:0;
  const sx=first.rect[2]/basis[2],sy=first.rect[3]/basis[3];
  return {...first,path:null,rect:[
   first.rect[0]+(ref[0]-basis[0]+14*extrapolate)*sx,
   first.rect[1]+(ref[1]-basis[1])*sy,ref[2]*sx,ref[3]*sy
  ]};
 };
 const bounds=[],timing=[];
 for(const [i,sourceMarks] of rows.entries()){
  if(!sourceMarks[0]||!names[i])throw Error('Original tally layout incomplete for row '+i);
  const marks=Array.from({length:16},(_,index)=>markAt(sourceMarks,index));
  const left=Math.floor(Math.min(...marks.map(m=>m.rect[0]))-5);
  const top=Math.floor(Math.min(...marks.map(m=>m.rect[1]))-5);
  const right=Math.ceil(Math.max(...marks.map(m=>m.rect[0]+m.rect[2]))+5);
  const bottom=Math.ceil(Math.max(...marks.map(m=>m.rect[1]+m.rect[3]))+5);
  const width=right-left,height=bottom-top;
  bounds[i]=[left+640,top+360,width,height];
  const canvas=createCanvas(width,height),g=canvas.getContext('2d');
  for(const [j,m] of marks.entries()){
   const [x,y,w,h]=m.rect;
   g.save();g.translate(x+w/2-left,y+h/2-top);g.rotate(m.rotation*Math.PI/180);
   g.drawImage(texture,-w/2,-h/2,w,h);g.restore();
   await write(base+'tally_'+i+'_'+(j+1)+'.png',canvas.toBuffer('image/png'));
  }
  timing[i]=marks.map((m,index)=>{
   const key=m.path??reference[index]?.path;
   const found=source.frames.findIndex((leaves,k)=>k>=first&&leaves.some(r=>r.path===key&&r.opacity>.1));
   return Math.min(last-first,found<0?2*index+2:found-first);
  });
 }
 const start=source.labels.fl_in-1,stop=source.labels.fl_wait-1;
 const rowIn=Array.from({length:16},(_,i)=>{
  const id='t_tosen_memori_chara_'+String(i).padStart(3,'0')+'.png';
  const frames=source.frames.slice(start,stop);
  const index=frames.findIndex(leaves=>leaves.some(r=>r.resource===id&&r.rect[0]<640&&r.rect[1]<360&&r.opacity>.4));
  return index<0?stop-start:index;
 });
 return {names,bounds,timing,rowIn,countFrames:last-first};
}
