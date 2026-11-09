import fs from'node:fs/promises';
import path from'node:path';
import{applyPadDetailSource}from'../../tools/render_pad_detail_source_ui.mjs';
// Composed techou_kotodama SFL bounds; supplied artwork is not re-extracted.
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../../../engineCreate/prototype/ui-assets.js';
export async function emitV4PadEvidenceUI({repo,write,body}){
 const w=createWidgetAsset('PadEvidenceV4');w.scaleMode='scale';w.scaleRule='fit';
 const add=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:31.25,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:true,...props});w.nodes.push(n);return n;};
 add('Panel','PeImagePlate',[578,75.3333,542,310],{background:'#08080de6',radius:0});
 add('Image','PeImage',[581.3333,78.6667,535.348,303.318],{texture:'',imageFit:'contain'});
 add('Panel','PePagePlate',[580,350.6667,100,32.6667],{background:'#08080ddd',radius:0,visible:false});
 add('Text','PePage',[589.3333,354.6667,170,36],{fontSize:24,visible:false});
 add('Panel','PeBodyPlate',[581.3333,389.3333,733.3405,246.6686],{background:'#08080dcc',radius:0});
 add('ScrollBox','PeBody',[586,396,633.3372,220.0013],{padding:0});
 add('Text','PeText',[2.0111,10.6778,533.336,209.32],{wrap:true},'PeBody');
 await applyPadDetailSource({repo,write,w,screen:'evidence'});
 if(!validWidgetAsset(w))throw Error('Invalid Pad evidence widget');
 await write('Assets/UI/PadEvidenceV4.hbwidget.json',w);return w;
}
