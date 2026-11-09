// Public footage NDFxB3YCNII 07:45/08:25: outlined claims sit directly over
// the confrontation. They are not contained in a purple menu-shaped plate.
// Font rasterisation is owned UI text, not a commissioned illustration.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game);
const {createCanvas,GlobalFonts}=createRequire(path.join(repo,'../engineCreate/package.json'))('@napi-rs/canvas');
export async function emitScrumText({write}){
 const font=await fs.readFile(path.join(game,'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf'));
 assert(GlobalFonts.register(font,'ScrumClaim'));
 const native=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8'));
 const strings=new Set();for(const t of Object.values(native.tasks))if(t.stage?.kind==='scrum')for(const pair of t.stage.pairs)strings.add(pair.themText);
 const aliases=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/scrum_keyword_labels_20261104.json'),'utf8'));
 const keywordLabels={};
 for(const row of aliases.rows){
  const pairs=native.tasks[row.taskId]?.stage?.pairs;
  assert(pairs?.some(p=>(p[row.field]??p.keyword)===row.source),'Re-review changed scrum keyword: '+row.source);
  assert(!keywordLabels[row.source]||keywordLabels[row.source]===row.display,'Ambiguous scrum alias');
  keywordLabels[row.source]=row.display;
 }
 for(const task of Object.values(native.tasks))if(task.stage?.kind==='scrum')for(const pair of task.stage.pairs)for(const field of ['keyword','responseKeyword'])assert(keywordLabels[pair[field]??pair.keyword],'Missing reviewed scrum label');
 const labelFont=await fs.readFile(path.join(game,'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'));
 assert(GlobalFonts.register(labelFont,'ScrumKeyword'));
 const measure=createCanvas(1,1).getContext('2d');measure.font='24px ScrumKeyword';
 for(const text of Object.values(keywordLabels))assert(measure.measureText(text).width<=280,'Scrum keyword must fit selected tab without scrolling: '+text);
 const bank={version:1,width:620,height:284,scale:3,outline:4,keywordLabels,items:{}};
 for(const text of strings){
  assert(typeof text==='string'&&text.trim());
  const canvas=createCanvas(1860,852),ctx=canvas.getContext('2d');ctx.scale(3,3);
  let lines,size;
  for(size=38;size>=32;size--){
   ctx.font=size+'px ScrumClaim';lines=[];let line='';
   for(const word of text.split(/\s+/u)){const test=line?line+' '+word:word;if(ctx.measureText(test).width<=596)line=test;else{assert(ctx.measureText(word).width<=596,'Unbroken scrum word needs editorial review');if(line)lines.push(line);line=word;}}
   if(line)lines.push(line);if(lines.length*size*1.24<=260)break;
  }
  assert(size>=32,'Split an overlong claim rather than shrinking it: '+text);
  ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineJoin='round';ctx.lineWidth=8;ctx.strokeStyle='#070510';ctx.fillStyle='#ffffff';
  const step=size*1.24,top=142-(lines.length-1)*step/2;
  for(let i=0;i<lines.length;i++){ctx.strokeText(lines[i],310,top+i*step);ctx.fillText(lines[i],310,top+i*step);}
  const key=createHash('sha256').update(font).update(text).update('scrum-620x284-outline4-v1').digest('hex').slice(0,24),texture='Assets/Art/ui/scrum_ink/'+key+'.png';
  await write(texture,canvas.toBuffer('image/png'));bank.items[text]={texture,fontSize:size,lines};
 }
 await write('Assets/Data/scrum_text_v4.json',bank);
 return {claims:strings.size,commissionedImages:0,minimumFont:Math.min(...Object.values(bank.items).map(r=>r.fontSize)),visualAcceptance:false};
}
