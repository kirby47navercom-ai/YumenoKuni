import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../engineCreate/prototype/ui-assets.js';
export async function emitTrialVitals({write}){
 const w=createWidgetAsset('TrialVitalsV4');w.scaleMode='scale';w.scaleRule='fit';
 for(let i=0;i<20;i++){const n=createWidgetNode('Image','Heart'+i,'root');n.name='Heart'+i;n.slot.offset=[986+i*12.2,60,13,21]; /* Status 판 안 가로줄(V3 LP Ch1 확인, Claude 2026-11-05) */Object.assign(n.properties,{texture:'Assets/Art/ui/hud_heartOn.svg',imageFit:'contain',visible:false});w.nodes.push(n);}
 if(!validWidgetAsset(w))throw Error('Invalid trial vitality widget');await write('Assets/UI/TrialVitalsV4.hbwidget.json',w);
}
