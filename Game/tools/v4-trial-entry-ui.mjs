import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../engineCreate/prototype/ui-assets.js';

export async function emitTrialEntryUI({write}){
 const widget=createWidgetAsset('TrialEntryV4');
 widget.scaleMode='scale';
 widget.scaleRule='fit';
 const add=(type,id,parent,rect,properties)=>{
  const node=createWidgetNode(type,id,parent);
  node.name=id;
  node.slot.offset=rect;
  Object.assign(node.properties,{padding:0,focusable:false,...properties});
  widget.nodes.push(node);
 };
 const full=[0,0,1280,720];
 const font='Assets/Fonts/pretendard/Pretendard-Medium.otf';
 add('Panel','Prep','root',full,{background:'#080c20db'});
 add('Panel','PrepRule','Prep',[96,228,1088,3],{background:'#41e4ff'});
 add('Text','PrepTitle','Prep',[100,139,610,78],{text:'변론준비',font,fontSize:64,color:'#f2faff'});
 for(const [i,label] of ['재판 시작','언령 확인','스킬 장착'].entries()){
  const id='PrepChoice'+i;
  add('Panel',id,'Prep',[770,285+i*64,390,56],{background:'#133858',borderColor:'#50dfff',borderWidth:2});
  add('Text',id+'Label',id,[28,6,340,44],{text:label,font,fontSize:31,color:'#f2faff'});
 }
 add('Panel','Opening','root',full,{visible:false,background:'#090d21c9'});
 const openingArt='Assets/Art/ui/trial_opening_v4.svg';
 await write(openingArt,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
 <rect width="1280" height="720" fill="#05050c"/>
 <path d="M0 372L382 0H590L0 575ZM1280 225L753 720H552L1280 42Z" fill="#102b56" opacity=".42"/>
 <path d="M-25 355L420 720M42 720L895 0M573 720L1220 0M1002 720L1189 0M185 0L411 720M0 597L1280 372" fill="none" stroke="#ec38df" stroke-opacity=".28" stroke-width="16"/>
 <path d="M-25 355L420 720M42 720L895 0M573 720L1220 0M1002 720L1189 0M185 0L411 720M0 597L1280 372" fill="none" stroke="#f547e5" stroke-width="3"/>
 </svg>`);
 add('Image','OpeningArt','Opening',full,{texture:openingArt,imageFit:'fill'});
 const brush='Assets/Fonts/eastseadokdo/EastSeaDokdo-Regular.ttf';
 add('Text','OpeningCourt','Opening',[180,183,980,268],{text:'학급재판',font:brush,fontSize:235,color:'#49beff'});
 add('Text','OpeningTitle','Opening',[525,318,575,240],{text:'개정',font:brush,fontSize:205,color:'#ffffff'});
 if(!validWidgetAsset(widget))throw Error('Invalid trial entry widget');
 await write('Assets/UI/TrialEntryV4.hbwidget.json',widget);
}
