// Imported by the project generator; this module never runs a game or build.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createWidgetAsset,createWidgetNode} from '../../engineCreate/prototype/ui-assets.js';

export async function emitPresentationV4({repo,copy,write}) {
  const contract=JSON.parse(await fs.readFile(path.join(repo,'data/presentation/v4.json'),'utf8'));
  const names=new Map();let frames=0;
  for(const seq of Object.values(contract.sequences)) {
    const mapped=[];
    for(const source of seq.frames) {
      const target='Assets/Art/presentation_v4/'+path.basename(source);
      if(names.has(target)&&names.get(target)!==source)throw new Error('Presentation frame basename collision: '+source);
      if(!names.has(target)){await copy(source,target);names.set(target,source);frames++;}
      mapped.push(target);
    }
    seq.frames=mapped;
  }
  // This is the runtime copy. Keep the authored source contract repo-relative.
  await write('Assets/Data/presentation/v4.json',contract);
  const widget=createWidgetAsset('W_PresentationV4');widget.scaleMode='scale';widget.scaleRule='fit';
  for(const id of ['FxFocus','FxNoise','FxImpact','FxTransition']) {
    const n=createWidgetNode('Image',id,'root');n.name=id;n.slot.offset=[0,0,1280,720];
    Object.assign(n.properties,{texture:'',imageFit:'fill',visible:false,opacity:1,focusable:false,padding:0});
    widget.nodes.push(n);
  }
  if(widget.nodes.length>256)throw new Error('Presentation widget node limit');
  await write('Assets/UI/PresentationV4.hbwidget.json',widget);
  return {widget:'Assets/UI/PresentationV4.hbwidget.json',contract:'Assets/Data/presentation/v4.json',frames,nodes:widget.nodes.length};
}
