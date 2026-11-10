// Actual task snapshots, unchanged packaged painter: hiding blank glyph leaves
// must preserve every pixel and every non-glyph input rectangle.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/game-trial-work-20261102');
const build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const {NativeWidgetLayer}=await import(pathToFileURL(path.join(build.output,'tools/native-widget-layer.mjs')));
const frozen=JSON.parse(await fs.readFile(path.join(work,'build-result.json'),'utf8'));
const pack={resolve:async name=>path.join(frozen.output,'Content',name),readBytes:async name=>fs.readFile(path.join(frozen.output,'Content',name))};
const source=JSON.parse(await fs.readFile(path.join(root,'Assets/UI/Main.hbwidget.json'),'utf8'));
const glyph=n=>/^(M[FB]|MS|N[FB])\d+$/.test(n.id)||/^P[0-2]G\d+$/.test(n.id);
const panic=JSON.parse(await fs.readFile(path.join(root,'Assets/UI/PanicV4.hbwidget.json'),'utf8'));
const eligible=[...source.nodes,...panic.nodes].filter(glyph);assert.equal(eligible.length,340);
for(const n of eligible){assert.equal(n.type,'Text');assert.equal(n.properties.background,'#00000000');assert(![...source.nodes,...panic.nodes].some(c=>c.parent===n.id));for(const field of ['events','bindings'])assert(!n[field]||Object.keys(n[field]).length===0);}
const run=path.join(root,'Saved/native-all-tasks-1793593447471');
const progress=JSON.parse(await fs.readFile(path.join(run,'progress.json'),'utf8')),report=JSON.parse(await fs.readFile(path.join(run,'report.json'),'utf8'));
const now=performance.now,results=[];let blanks=0;Object.defineProperty(performance,'now',{value:()=>10000,configurable:true});
try{
 for(const row of report.results){
  const capture=JSON.parse(await fs.readFile(path.join(progress.session,'task-'+row.taskId.toLowerCase()+'.ui.json'),'utf8'));
  const layers=[new NativeWidgetLayer(pack,async()=>({})),new NativeWidgetLayer(pack,async()=>({}))];for(const l of layers)l.layout=[];
  try{
   for(const [index,layer]of layers.entries())for(const w of capture.widgets){
    const nodes=structuredClone(w.nodes);
    if(index&&['main','panicv4'].includes(w.instance))for(const n of nodes)if(glyph(n)&&(n.properties.opacity===0||/^[ \t\r\n]*$/.test(n.properties.text||''))){if(n.properties.visible!==false&&n.properties.opacity!==0)blanks++;n.properties.visible=false;}
    layer.create({nodes,referenceSize:[1280,720],scaleMode:'scale',scaleRule:'fit'},{acceptInput:()=>true,event:()=>{},input:()=>{}},{owner:w.owner,instance:w.instance});
   }
   for(const [width,height]of [[1280,720],[1024,768],[1600,900]]){
    for(const l of layers)await l.draw(width,height,1);
    assert(layers[0].canvas.data().equals(layers[1].canvas.data()),'Pixel change '+row.taskId+' '+width+'x'+height);
    const rects=l=>l.layout.filter(n=>!glyph(n)).map(({id,x,y,w,h})=>({id,x,y,w,h}));assert.deepEqual(rects(layers[0]),rects(layers[1]));
    results.push({task:row.taskId,kind:row.kind,width,height,exactPixels:true,inputRectsExact:true});
   }
  }finally{for(const l of layers)l.dispose();}
 }
 assert(blanks>0,'The test must actually hide rendered blank cells');
 await fs.writeFile(path.join(work,'blank-glyph-pixels.json'),JSON.stringify({ok:true,painterBuild:build.id,cases:results.length,blankCellsTested:blanks,results,scope:'Actual15task snapshots at3sizes, unchanged packaged painter. Only340 inert Main/Panic glyph Text leaves. No gameplay, spacing, collision or non-glyph UI changes.'},null,2));console.log(JSON.stringify({ok:true,cases:results.length,blankCellsTested:blanks}));
}finally{Object.defineProperty(performance,'now',{value:now,configurable:true});}
