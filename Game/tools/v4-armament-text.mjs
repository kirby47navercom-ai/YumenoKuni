// Native-size text ink, including V3-style black outlines. This avoids a host
// that accepts outline metadata but paints only the white fill. No menu panel.
import fs from 'node:fs/promises';import path from 'node:path';import {createHash} from 'node:crypto';import {createRequire} from 'node:module';import assert from 'node:assert/strict';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),require=createRequire(path.join(repo,'../engineCreate/package.json')),{createCanvas,GlobalFonts}=require('@napi-rs/canvas');
export async function emitArmamentText({write,revisionTasks,source=game}){
 const font=await fs.readFile(path.join(source,'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf'));assert(GlobalFonts.register(font,'ArmamentInk'));
 const tasks=revisionTasks||JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks;
 const stages=Object.values(tasks).map(t=>t.stage).filter(s=>s.kind==='armament'),strings=new Set();
 for(const stage of stages)for(const text of stage.lines)strings.add(text);
 const bank={version:2,width:640,height:112,scale:3,outline:4,items:{},final:{}};
 const wrap=(ctx,text,width)=>{const lines=[];let line='';for(const word of text.split(/\s+/u)){const candidate=line?line+' '+word:word;if(ctx.measureText(candidate).width<=width)line=candidate;else{if(line)lines.push(line);line=word;}}if(line)lines.push(line);return lines;};
 for(const text of strings){
  const c=createCanvas(1920,336),ctx=c.getContext('2d');ctx.scale(3,3);let size=30,lines;
  for(;size>=22;size--){ctx.font=size+'px ArmamentInk';lines=wrap(ctx,text,616);if(lines.length*(size*1.2)<=100)break;}
  assert(size>=22,'Split an overlong authored claim instead of shrinking it: '+text);
  ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineJoin='round';ctx.lineWidth=8;ctx.strokeStyle='#070510';ctx.fillStyle='#ffffff';
  const step=size*1.2,top=56-(lines.length-1)*step/2;for(let i=0;i<lines.length;i++){ctx.strokeText(lines[i],320,top+i*step);ctx.fillText(lines[i],320,top+i*step);}
  const png=c.toBuffer('image/png'),key=createHash('sha256').update(font).update(text).update('640x112-outline4-v1').digest('hex').slice(0,24),texture='Assets/Art/ui/armament_ink/'+key+'.png';await write(texture,png);bank.items[text]={texture,fontSize:size,lines,width:640,height:112};
 }
 // Every possible prefix, including a wrong ordering, needs the same legible
 // treatment as a correct final phrase. None of these strings changes rules.
 const roles={question:{width:440,height:110,color:'#ff4fa3'},piece:{width:315,height:56,color:'#ffffff'},joined:{width:920,height:84,color:'#ffffff'}};
 const texts={question:new Set(),piece:new Set(),joined:new Set()};
 if(revisionTasks){
  stages.push(...stages.flatMap(stage=>stage.controllerQuestions||[]));
 }else{
  const finalController=JSON.parse(await fs.readFile(path.join(repo,'data/presentation/armament_final_questions.json'),'utf8'));
  await write('Assets/Data/armament_final_questions.json',finalController);
  stages.push(...finalController.questions);
 }
 for(const s of stages){texts.question.add(s.question||'');for(const t of s.final)texts.piece.add(t);const visit=(prefix,indices)=>{texts.joined.add(prefix);for(const i of indices)visit(prefix+(prefix?' ':'')+s.final[i],indices.filter(j=>j!==i));};visit(s.finalSubject||'',[0,1,2,3]);}
 for(const [role,spec] of Object.entries(roles)){bank.final[role]={};for(const text of texts[role]){if(!text)continue;const {width,height,color}=spec,c=createCanvas(width*3,height*3),ctx=c.getContext('2d');ctx.scale(3,3);let size=30,lines;for(;size>=22;size--){ctx.font=size+'px ArmamentInk';lines=wrap(ctx,text,width-20);if(lines.length*size*1.2<=height-10)break;}assert(size>=22,'Overlong final '+role+': '+text);ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineJoin='round';ctx.lineWidth=8;ctx.strokeStyle='#070510';ctx.fillStyle=color;const step=size*1.2,top=height/2-(lines.length-1)*step/2;for(let i=0;i<lines.length;i++){ctx.strokeText(lines[i],width/2,top+i*step);ctx.fillText(lines[i],width/2,top+i*step);}const key=createHash('sha256').update(font).update(role+text).update('final-ink-v1').digest('hex').slice(0,24),texture='Assets/Art/ui/armament_ink/'+key+'.png';await write(texture,c.toBuffer('image/png'));bank.final[role][text]={texture,fontSize:size,lines,width,height};}}
 await write(revisionTasks?'Assets/Data/armament_text_revision.json':'Assets/Data/armament_text_v4.json',bank);return {claims:strings.size,final:Object.fromEntries(Object.entries(bank.final).map(([k,v])=>[k,Object.keys(v).length])),outline:4,smallestFont:Math.min(...Object.values(bank.items).map(r=>r.fontSize)),pixelUpscale:false};
}
export function applyArmamentInkNode(widget){
 for(const id of ['ArmLine','ArmQuestion','ArmJoined','Piece0','Piece1','Piece2','Piece3']){const line=widget.nodes.find(n=>n.id===id);assert(line);let ink=widget.nodes.find(n=>n.id===id+'Ink');if(!ink){ink=structuredClone(line);ink.id=ink.name=id+'Ink';ink.type='Image';widget.nodes.push(ink);}Object.assign(ink.properties,{text:'',texture:'',imageFit:'contain',visible:false});ink.slot.zIndex=Math.max(30,line.slot.zIndex||0);if(id.startsWith('Piece')){const i=Number(id.slice(-1)),rects=[[485.6667,116.6667,308.6667,56],[852.9333,335,308.6823,56],[485.6667,552.6667,308.6667,56],[111.6667,334.6667,308.6667,56]];ink.slot.offset=rects[i];}if(id==='ArmJoined'){ink.slot.offset[1]=444;ink.slot.offset[3]=84;}}
 assert(widget.nodes.length<=256,'Stage widget node budget');return widget;
}
