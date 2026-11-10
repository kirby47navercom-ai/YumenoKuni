// Own-game asset isolation using the unchanged packaged painter. Not an FPS claim.
import fs from 'node:fs/promises';import path from 'node:path';import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/game-trial-work-20261102'),build=JSON.parse(await fs.readFile(path.join(work,'build-result.json'),'utf8'));
const {NativeWidgetLayer}=await import(pathToFileURL(path.join(build.output,'tools/native-widget-layer.mjs'))),pack={resolve:async n=>path.join(build.output,'Content',n)};
const p=JSON.parse(await fs.readFile(path.join(root,'Saved/native-all-tasks-1793593447471/progress.json'),'utf8')),data=JSON.parse(await fs.readFile(path.join(p.session,'task-t3-ns-a11.ui.json'),'utf8')),rows=[];
for(const mode of ['all','no-glyphs','main-only','glyphs-only','no-text']){
 const layer=new NativeWidgetLayer(pack,async()=>({}));layer.layout=[];let main;
 try{
  for(const w of data.widgets){const widget=structuredClone(w);if(['main-only','glyphs-only'].includes(mode)&&w.instance!=='main')widget.nodes.find(n=>n.id==='root').properties.visible=false;
   for(const n of widget.nodes){const glyph=/^(M[FSB]|N[FB])\d+$/.test(n.id);if(mode==='no-glyphs'&&glyph)n.properties.visible=false;if(mode==='glyphs-only'&&w.instance==='main'&&!glyph&&!['root','Trial','TrialBack'].includes(n.id))n.properties.visible=false;if(mode==='no-text'&&n.type==='Text')n.properties.visible=false;}
   const v=layer.create({nodes:widget.nodes,referenceSize:[1280,720],scaleMode:'scale',scaleRule:'fit'},{acceptInput:()=>true,event:()=>{},input:()=>{}},{owner:w.owner,instance:w.instance});if(w.instance==='main')main=v;
  }
  const times=[];for(let frame=0;frame<28;frame++){for(const n of main.data.nodes)if(/^(M[FSB]|N[FB])\d+$/.test(n.id))n.slot.offset[0]+=.7;main.update();const start=performance.now();await layer.draw(1280,720,1);if(frame>=4)times.push(performance.now()-start);}
  times.sort((a,b)=>a-b);rows.push({mode,meanMS:times.reduce((a,b)=>a+b,0)/times.length,medianMS:times[Math.floor(times.length/2)],p95MS:times[Math.floor(times.length*.95)]});
 }finally{layer.dispose();}
}
await fs.writeFile(path.join(work,'main-content-profile.json'),JSON.stringify({scope:'24measured draws per own-game content isolation variant; explicit glyph pose changes invalidate Main. Unchanged packaged renderer, no native submit/GPU or end-to-end FPS claim.',rows},null,2));console.log(JSON.stringify(rows));
