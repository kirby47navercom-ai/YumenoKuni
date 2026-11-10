import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {createOwnedNativePackage} from './native-owned-package.mjs';
const root=path.resolve(import.meta.dirname,'..'),build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8')),work=path.join(root,'Saved/native-widget-paint-'+Date.now());
const baseline=path.join(root,'Builds/windows/2026-11-01T13-56-29-441Z-0fce033a'),{NativeWidgetLayer:Original}=await import(pathToFileURL(path.join(baseline,'tools/native-widget-layer.mjs')));
const prepared=await createOwnedNativePackage({source:build.output,work,widgetCandidate:path.join(import.meta.dirname,'native-widget-paint.candidate.mjs'),uiFrameCandidate:path.join(import.meta.dirname,'native-ui-frame.candidate.mjs')});
const {NativeWidgetLayer:Candidate}=await import(pathToFileURL(path.join(prepared.output,'tools/native-widget-layer.mjs')));
const data=JSON.parse(await fs.readFile(path.join(root,'Saved/native-all-tasks-1793541469758/session-1793541481899/task-t3-ns-a11.ui.json'),'utf8')),pack={resolve:async name=>path.join(build.output,'Content',name)},layers=[new Original(pack,async()=>({})),new Candidate(pack,async()=>({}))],views=[];let tests=0;
const originalNow=performance.now;Object.defineProperty(performance,'now',{value:()=>10000,configurable:true});
try{
 for(const layer of layers)views.push(data.widgets.map(w=>layer.create({nodes:structuredClone(w.nodes),referenceSize:[1280,720],scaleMode:'scale'}, {acceptInput:()=>true,event:()=>{},input:()=>{}},{owner:w.owner,instance:w.instance})));
 for(let i=0;i<4;i++){
  if(i){for(const list of views)for(const view of list){for(const n of view.data.nodes){if(n.type==='Text'){n.properties.rotation=i*2;n.properties.text='한글 '+i;n.slot.offset[0]+=i;}if(i===3)for(const key of ['rotation','scale','fillDirection','nineSlice'])delete n.properties[key];}view.update();}}
  for(const layer of layers)await layer.draw(1280,720,1);
  assert.deepEqual(layers[1].canvas.data(),layers[0].canvas.data(),'Exact premultiplied raster frame '+i);assert.equal(layers[1].hits.length,layers[0].hits.length);tests++;
 }
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,tests,exactPremultipliedRaster:true,hitCountUnchanged:true,scope:'Actual trial widgets with repeated text/rotation/position updates; frozen animation clock. Raster only; native compositor checked separately.'},null,2));console.log(JSON.stringify({work,ok:true,tests}));
}finally{for(const layer of layers)layer.dispose();Object.defineProperty(performance,'now',{value:originalNow,configurable:true});}
