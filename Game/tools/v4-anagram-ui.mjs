import {solutionCutin} from './v4-solution-cutin.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../../../engineCreate/prototype/ui-assets.js';
import {emitAnagramTransitions} from './v4-anagram-transition-ui.mjs';
import {trialModeSource} from './v4-panic-showdown-source.mjs';
const repo=path.dirname(path.dirname(path.dirname(fileURLToPath(import.meta.url))));
export async function emitV4AnagramUI({write,body,head}){
 const source=await trialModeSource();
 for(const [name,w,h]of [['background',1280,720],['silhouette',1280,720],['light',682.6667,725.3333],['orb',84,84],['orb_dark',84,84],['aim',36,36],['spot',256,256],['status',440,64],['slot',50,56]])await write('Assets/Art/ui/anagram_'+name+'.svg',await source.raster('anagram_'+name,w,h));
 for(let i=0;i<4;i++)await write('Assets/Art/ui/anagram_orb_'+i+'.svg',await source.raster('anagram_orb_'+i,84,84));
 const svg=(width,height,body)=>`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${body}</svg>`;
 const bank=path.join(repo,'ui/v3_authorized/anagram_start');
 const title=(await fs.readFile(path.join(bank,'title.png'))).toString('base64');
 await write('Assets/Art/ui/anagram_intro_title.png',await fs.readFile(path.join(bank,'title.png')));
 for(const [name,lit]of [['outline',false],['lit',true]]){
  const ink=lit?'<feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 .18 0 0 0 0 .91 0 0 0 0 1 0 0 0 1 0" result="ink"/>':'';
  await write('Assets/Art/ui/anagram_intro_'+name+'.svg',svg(2048,1024,`<defs><filter id="glow" color-interpolation-filters="sRGB"><feGaussianBlur in="SourceAlpha" stdDeviation="13" result="soft"/><feColorMatrix in="soft" type="matrix" values="0 0 0 0 .1 0 0 0 0 .8 0 0 0 0 1 0 0 0 1.7 0" result="halo"/>${ink}<feMerge><feMergeNode in="halo"/><feMergeNode in="${lit?'ink':'SourceGraphic'}"/></feMerge></filter></defs><image href="data:image/png;base64,${title}" width="2048" height="1024" filter="url(#glow)"/>`));
 }
 const subtitle=(await fs.readFile(path.join(bank,'subtitle.png'))).toString('base64');
 const plate=(await source.image('anagram_subtitle_plate')).split(',')[1];
 await write('Assets/Art/ui/anagram_intro_subtitle.svg',svg(1024,128,`<image href="data:image/png;base64,${plate}" width="1024" height="128" preserveAspectRatio="none"/><image href="data:image/png;base64,${subtitle}" y="32" width="1024" height="64"/>`));
 await write('Assets/Art/ui/anagram_dim.svg',svg(1280,720,'<path d="M0 0H1280V720H0Z" fill="#000713"/>'));
 for(const name of ['correct','wrong']){
  const effect=await source.image('anagram_'+(name==='correct'?'correct_ef':'wrong_ef'));
  const label=name==='correct'?`<image href="data:image/svg+xml;base64,${(await fs.readFile(path.join(repo,'ui/v4/debate_feedback/anagram_correct.svg'))).toString('base64')}" x="400" y="318" width="480" height="85"/>`:'';
  await write('Assets/Art/ui/anagram_feedback_'+name+'.svg',svg(1280,720,`<image href="${effect}" x="496" y="216" width="288" height="288"/>${label}`));
 }
 const solution=await solutionCutin();for(const [suffix,key]of [['band','background'],['face','face'],['word','word']])await write('Assets/Art/ui/anagram_result_'+suffix+'.svg',solution[key]);await write('Assets/Art/ui/anagram_result_crack.svg',await fs.readFile(path.join(repo,'ui/v4/debate_feedback/result_crack_agree.svg')));
 const w=createWidgetAsset('AnagramV4');w.scaleMode='scale';w.scaleRule='fit';
 const add=(type,id,rect,props={},z=0)=>{const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=rect;n.slot.zIndex=z;Object.assign(n.properties,{text:'',font:body,fontSize:28,color:'#ffffff',background:'#00000000',padding:0,visible:false,focusable:false,wrap:false,...props});w.nodes.push(n);return n;};
 add('Image','AnaBackground',[0,0,1280,720],{texture:'Assets/Art/ui/anagram_background.svg',imageFit:'fill'},0);
 add('Image','AnaSilhouette',[0,0,1280,720],{texture:'Assets/Art/ui/anagram_silhouette.svg',imageFit:'fill'},1);
 add('Image','AnaLight',[-300,-2.6667,682.6667,725.3333],{texture:'Assets/Art/ui/anagram_light.svg',imageFit:'fill'},2);
 add('Image','AnaSpot',[640,360,0,0],{texture:'Assets/Art/ui/anagram_spot.svg',imageFit:'fill'},3);
 for(let i=0;i<20;i++){
  add('Image','AnaBall'+i,[0,0,84,84],{texture:'Assets/Art/ui/anagram_orb_dark.svg',imageFit:'contain'},5).slot.alignment=[.5,.5];
  add('Text','Orb'+i,[0,0,84,84],{font:head,fontSize:40,align:'center',color:'#ffffff'},6).slot.alignment=[.5,.5];
  add('Image','AnaSlotBack'+i,[0,24,44,56],{texture:'Assets/Art/ui/anagram_slot.svg',imageFit:'fill'},11);
  add('Text','AnaSlot'+i,[0,24,44,56],{font:head,fontSize:40,align:'center',color:'#91b1c0'},12);
 }
 add('Text','AnaAnswerLabel',[52,87,440,27],{text:'답안',font:head,fontSize:19,color:'#76dcff'},12);
 add('Text','AnaTimeLabel',[52,625,160,30],{text:'남은 시간',font:head,fontSize:25,color:'#76dcff'},12);
 add('Text','AnaTime',[98,656,390,44],{font:head,fontSize:34,color:'#76dcff'},12);
 add('Text','AnaQuestionButton',[996,652,250,38],{text:'Q 문제 표시',fontSize:23,align:'center'},12);
 add('Text','AnaQuestion',[680.6667,552,533.3333,38.6667],{fontSize:30,color:'#ffffff'},21);
 add('Image','AnaAim',[622,342,36,36],{texture:'Assets/Art/ui/anagram_aim.svg',imageFit:'contain'},15);
 add('Image','AnaStatus',[810,46,440,64],{texture:'Assets/Art/ui/anagram_status.svg',imageFit:'fill'},30);
 for(let i=0;i<20;i++)add('Image','AnaHeart'+i,[990+i*21,46,22,22],{texture:'Assets/Art/ui/hud_heartOn.svg',imageFit:'contain'},31);
 for(let i=0;i<10;i++)add('Image','AnaStar'+i,[978+i*25,80,24,24],{texture:'Assets/Art/ui/hud_starOn.svg',imageFit:'contain'},31);
 add('Image','AnaIntroDim',[0,0,1280,720],{texture:'Assets/Art/ui/anagram_dim.svg',imageFit:'fill'},40);
 add('Image','AnaIntroTitle',[-12,-36,1304,808],{texture:'Assets/Art/ui/anagram_intro_outline.svg',imageFit:'fill'},41);
 add('Image','AnaIntroLit',[-12,-36,1304,808],{texture:'Assets/Art/ui/anagram_intro_lit.svg',imageFit:'fill'},42);
 add('Image','AnaIntroSubtitle',[242,304,796,100],{texture:'Assets/Art/ui/anagram_intro_subtitle.svg',imageFit:'fill'},43);
 add('Image','AnaFeedback',[0,0,1280,720],{texture:'Assets/Art/ui/anagram_feedback_correct.svg',imageFit:'fill'},45);
 for(const [suffix,rect,z]of [['Band',[0,0,1280,720],50],['Face',[440,0,840,720],51],['Word',[20,30,660,660],52],['Crack',[0,0,1280,720],53]]){
  add('Image','AnaResult'+suffix,rect,{texture:'Assets/Art/ui/anagram_result_'+suffix.toLowerCase()+'.svg',imageFit:'fill'},z);
 }
 await emitAnagramTransitions(write,add);
 if(!validWidgetAsset(w)||w.nodes.length>256)throw Error('Invalid AnagramV4 widget');
 await write('Assets/UI/AnagramV4.hbwidget.json',w);return w;
}
