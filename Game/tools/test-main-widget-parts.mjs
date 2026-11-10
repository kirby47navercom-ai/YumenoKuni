import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {pathToFileURL} from 'node:url';
import {mainWidgetParts} from './main-widget-parts.mjs';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/game-trial-work-20261102'),build=JSON.parse(await fs.readFile(path.join(work,'build-result.json'),'utf8'));
const {NativeWidgetLayer}=await import(pathToFileURL(path.join(build.output,'tools/native-widget-layer.mjs'))),pack={resolve:async name=>path.join(build.output,'Content',name)};
const run=path.join(root,'Saved/native-all-tasks-1793593447471'),progress=JSON.parse(await fs.readFile(path.join(run,'progress.json'),'utf8'));
const report=JSON.parse(await fs.readFile(path.join(run,'report.json'),'utf8')),results=[];
const originalNow=performance.now;Object.defineProperty(performance,'now',{value:()=>10000,configurable:true});
try{
 for(const row of report.results){
  const capture=JSON.parse(await fs.readFile(path.join(progress.session,'task-'+row.taskId.toLowerCase()+'.ui.json'),'utf8'));
  const main=capture.widgets.find(w=>w.instance==='main');assert(main);
  const plan=mainWidgetParts({name:'Main',nodes:main.nodes,referenceSize:[1280,720],scaleMode:'scale',scaleRule:'fit'});
  const layers=[new NativeWidgetLayer(pack,async()=>({})),new NativeWidgetLayer(pack,async()=>({}))];
  for(const layer of layers)layer.layout=[];
  try{
   for(const [index,layer]of layers.entries())for(const w of capture.widgets){
    const widgets=index===1&&w===main?plan.parts.map(p=>({owner:'UI_'+p.instance,instance:p.instance,data:p.data})):[{owner:w.owner,instance:w.instance,data:{nodes:structuredClone(w.nodes),referenceSize:[1280,720],scaleMode:'scale',scaleRule:'fit'}}];
    for(const v of widgets)layer.create(v.data,{acceptInput:()=>true,event:()=>{},input:()=>{}},{owner:v.owner,instance:v.instance});
   }
   for(const [width,height]of [[1280,720],[1024,768],[1600,900]]){
    for(const layer of layers)await layer.draw(width,height,1);
    assert(layers[0].canvas.data().equals(layers[1].canvas.data()),'Exact pixels: '+row.taskId+' '+width+'x'+height);
    assert.deepEqual(layers[1].layout.map(({id,x,y,w,h})=>({id,x,y,w,h})).filter(n=>!['root','Trial','TrialBack'].includes(n.id)),layers[0].layout.map(({id,x,y,w,h})=>({id,x,y,w,h})).filter(n=>!['root','Trial','TrialBack'].includes(n.id)),'Input rectangles');
    results.push({task:row.taskId,kind:row.kind,width,height,exactPixels:true,inputRectsExact:true});
   }
  }finally{for(const layer of layers)layer.dispose();}
 }
 await fs.writeFile(path.join(work,'main-parts-pixels.json'),JSON.stringify({ok:true,cases:results.length,results,scope:'Existing unchanged packaged painter; actual15task snapshots at3sizes. Game widget owner partition only; exact UI pixels and leaf input rectangles.'},null,2));console.log(JSON.stringify({ok:true,cases:results.length}));
}finally{Object.defineProperty(performance,'now',{value:originalNow,configurable:true});}
