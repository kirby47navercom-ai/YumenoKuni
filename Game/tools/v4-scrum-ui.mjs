// Cached t_scm SFL anchors and directly viewed V3 screen; not a card menu.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {emitScrumText} from './v4-scrum-text.mjs';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../engineCreate/prototype/ui-assets.js';
const repo=path.dirname(path.dirname(path.dirname(fileURLToPath(import.meta.url))));
export async function emitV4ScrumUI({write,body,head}){
 await emitScrumText({write});
 const startTexture=await fs.access(path.join(repo,'Game/Assets/Art/ui/v3/scrum_start.png')).then(()=> 'Assets/Art/ui/v3/scrum_start.png',()=> 'Assets/Art/ui/v3/scrum_start.webp');
 for(const [name,side]of [['left','l'],['right','r']]){
  const raw=await fs.readFile(path.join(repo,'ui/v4/scrum_source/tab_'+side+'.png'));
  await write('Assets/Art/ui/scrum_'+name+'.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 256"><image width="1024" height="256" href="data:image/png;base64,${raw.toString('base64')}"/></svg>`);
 }
 const button=await fs.readFile(path.join(repo,'ui/v4/scrum_source/push_button.png'));await write('Assets/Art/ui/scrum_push.svg',`<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><image href="data:image/png;base64,${button.toString('base64')}" width="128" height="128"/></svg>`);
 const w=createWidgetAsset('ScrumV4');w.scaleMode='scale';w.scaleRule='fit';
 const add=(type,id,rect,props={},z=0)=>{const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=rect;n.slot.zIndex=z;Object.assign(n.properties,{text:'',font:body,fontSize:30,color:'#ffffff',background:'#00000000',padding:0,visible:false,focusable:false,wrap:false,...props});w.nodes.push(n);return n;};
 add('Image','ScVStatementP',[548,138,732,345],{texture:'',imageFit:'fill'},0);
 add('Text','ScVStatement',[610,180,620,284],{font:head,fontSize:36,color:'#ddd9ce',wrap:true,rotation:-5},1);
 add('Image','ScVClaimInk',[610,180,620,284],{texture:'',imageFit:'contain',rotation:-5},2);
 for(const side of ['L','R'])for(let i=9;i>=0;i--){
  add('Image',`ScV${side}P${i}`,[0,0,683,171],{texture:'Assets/Art/ui/scrum_'+(side==='L'?'left':'right')+'.svg',imageFit:'fill'},20-i);
  add('Image',`ScV${side}F${i}`,[0,0,100,90],{texture:'',imageFit:'cover'},21-i);
  add('Text',`ScV${side}T${i}`,[0,0,293,54],{font:head,fontSize:30,align:side==='L'?'right':'left',wrap:false},22-i);
 }
 add('Image','ScVPush',[562,263,156,156],{texture:'Assets/Art/ui/scrum_push.svg',imageFit:'contain'},35);
 add('Text','ScVKey',[595,305,90,66],{font:head,fontSize:50,align:'center',color:'#13121b'},36);
 add('Text','ScVPushText',[500,275,280,35],{font:head,fontSize:24,align:'center',text:'밀어붙여!'},36);
 // The active V3 intro/lock/push widgets own their source art; this legacy layer is only a black transition carrier.
 add('Image','ScVTunnel',[0,0,1280,720],{texture:'Assets/Art/ui/result_black.svg',imageFit:'fill'},49);
 add('Image','ScBand',[128,232,1024,256],{texture:startTexture,imageFit:'contain'},50);
 if(!validWidgetAsset(w)||w.nodes.length>256)throw Error('Invalid ScrumV4 widget');
 await write('Assets/UI/ScrumV4.hbwidget.json',w);return w;
}
