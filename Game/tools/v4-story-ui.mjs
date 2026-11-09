import {createWidgetAsset,createWidgetNode} from '../../../engineCreate/prototype/ui-assets.js';

export async function installV4StoryUI({write,copy,body,head}){
 const widget=createWidgetAsset('W_V4Story');widget.scaleMode='scale';widget.scaleRule='fit';
 const put=(type,id,rect,properties={},parent='root')=>{
  const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;
  Object.assign(n.properties,{font:body,fontSize:24,color:'#ffffff',text:'',background:'#00000000',padding:0,focusable:false,visible:false,...properties});widget.nodes.push(n);return n;
 };
 put('Image','NewFocus',[385,474,510,88],{texture:'Assets/Art/ui/v3/title_new_focus.png',imageFit:'contain'});
 put('Image','New',[405,488,470,62],{texture:'Assets/Art/ui/v3/title_new.png',imageFit:'contain'});
 put('Image','LoadFocus',[385,572,510,88],{texture:'Assets/Art/ui/v3/title_load_focus.png',imageFit:'contain'});
 put('Image','Load',[405,586,470,62],{texture:'Assets/Art/ui/v3/title_load.png',imageFit:'contain'});
 put('Image','TitleOption',[1120,585,110,110],{texture:'Assets/Art/ui/v3/title_option.png',imageFit:'contain'});
 put('Panel','DocumentShade',[0,0,1280,720],{background:'#05050ce8'});
 put('Image','DocumentPaper',[190,75,900,560],{texture:'Assets/Art/ui/v3/pad_bubble.png',imageFit:'contain'});
 put('Text','DocumentTitle',[245,105,790,66],{font:head,fontSize:30,color:'#16121c'});
 put('Text','DocumentBody',[245,190,790,342],{fontSize:24,color:'#16121c',wrap:true});
 put('Text','DocumentHint',[245,573,790,32],{fontSize:18,color:'#16121c',align:'right',text:'Enter / 클릭  닫기'});
 await write('Assets/UI/V4Story.hbwidget.json',widget);
 return widget.nodes.length;
}
