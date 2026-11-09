import fs from 'node:fs/promises';
import {createWidgetNode,validWidgetAsset} from '../../../engineCreate/prototype/ui-assets.js';
export async function emitReasoningVisuals({write}){
 const manifest=JSON.parse(await fs.readFile(new URL('../../ui/v4/trial_inputs_source/manifest.json',import.meta.url),'utf8'));
 const raster=async key=>'data:image/png;base64,'+(await fs.readFile(new URL('../../'+manifest.records[key].file,import.meta.url))).toString('base64');
 // This authored replacement has no V3 minigame counterpart. Reuse the actual
 // trial answer carrier for its choice surface, preserving our link rules.
 await write('Assets/Art/ui/reasoning_back.svg',`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720"><image href="${await raster('choice_frame')}" width="1280" height="720"/></svg>`);
 await write('Assets/Art/ui/reasoning_card.svg',`<svg xmlns="http://www.w3.org/2000/svg" width="360" height="92" viewBox="0 0 360 92"><image href="${await raster('choice_gray')}" width="360" height="92" preserveAspectRatio="none"/></svg>`);
 for(let i=0;i<3;i++){
  const end=48+i*110;
  const route=`M 7 158 L 37 158 L 91 ${end} L 120 ${end}`;
  await write(`Assets/Art/ui/reasoning_branch_${i}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="120" height="330" viewBox="0 0 120 330"><path d="${route}" fill="none" stroke="#123754" stroke-width="10"/><path d="${route}" fill="none" stroke="#57dbff" stroke-width="3"/><circle cx="7" cy="158" r="5" fill="#d4f8ff"/></svg>`);
 }

}
export function applyReasoningStage(w){
 const body='Assets/Fonts/pretendard/Pretendard-Medium.otf';
 function put(type,id,rect,properties,back=false){let n=w.nodes.find(n=>n.id===id);if(!n){n=createWidgetNode(type,id,'root');n.name=id;if(back)w.nodes.splice(1,0,n);else w.nodes.push(n);}n.slot.offset=rect;Object.assign(n.properties,{visible:false,focusable:false,...properties});}
 put('Image','ReasoningBack',[0,0,1280,720],{texture:'Assets/Art/ui/reasoning_back.svg',imageFit:'fill'},true);
 put('Text','ReasoningTitle',[60,60,530,54],{text:'추리 연결',font:body,fontSize:34,color:'#e8f4ef',wrap:false});
 for(let i=0;i<3;i++){
  put('Image','ReasoningBranch'+i,[584,180,120,330],{texture:`Assets/Art/ui/reasoning_branch_${i}.svg`,imageFit:'fill'});
  put('Image','ReasoningPastBand'+i,[60+i*400,548,360,92],{texture:'Assets/Art/ui/reasoning_card.svg',imageFit:'fill'});
  put('Text','ReasoningPast'+i,[80+i*400,559,320,70],{text:'',font:body,fontSize:18,color:'#b5d8d4',wrap:true});
 }
 if(w.nodes.length>256||!validWidgetAsset(w))throw Error('Reasoning widget exceeds native bounds');
 return w;
}
