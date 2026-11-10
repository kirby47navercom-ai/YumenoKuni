import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..'),file=path.resolve(root,'../../engineCreate/tools/native-widget-layer.mjs'),source=await fs.readFile(file,'utf8'),work=path.join(root,'Saved/native-scroll-candidate-'+Date.now());await fs.mkdir(work,{recursive:true});let candidate=source;
const replace=(before,after)=>{assert(candidate.includes(before),before);candidate=candidate.replace(before,after);};
replace('this.fontKeys=[];','this.fontKeys=[];this.scrollHits=[];');
replace('elements:new Map(),update:', 'elements:new Map(),scrollOffsets:new Map(),update:');
replace("for(const node of data.nodes)view.elements.set(node.id,{querySelector:","for(const node of data.nodes)view.elements.set(node.id,{get scrollTop(){return view.scrollOffsets.get(node.id)||0;},set scrollTop(value){if(!Number.isFinite(value))throw Error('스크롤 위치를 확인하세요.');view.scrollOffsets.set(node.id,Math.max(0,value));thisLayer.revision++;},querySelector:");
replace('create=(data,options,state)=>{const view=', 'create=(data,options,state)=>{const thisLayer=this,view=');
replace('release(){const hit=this.down;', 'release(){this.scrollDrag=null;const hit=this.down;');
replace('this.hits=this.hits.filter(hit=>hit.view!==view);','this.hits=this.hits.filter(hit=>hit.view!==view);this.scrollHits=this.scrollHits.filter(hit=>hit.view!==view);if(this.scrollDrag?.view===view)this.scrollDrag=null;');
replace('input(packet){if(packet.pointer){this.pointer=packet.pointer.position;', `scrollLocal(hit){const m=hit.matrix,d=m.a*m.d-m.b*m.c,dx=this.pointer[0]-m.e,dy=this.pointer[1]-m.f;return [(m.d*dx-m.c*dy)/d,(m.a*dy-m.b*dx)/d];}
 scrollTo(hit,value){const next=clamp(value,0,hit.max);if(next!==hit.view.scrollOffsets.get(hit.node.id)){hit.view.scrollOffsets.set(hit.node.id,next);this.revision++;}return true;}
 input(packet){
  if(packet.device==='mouse'&&String(packet.key).toLowerCase()==='mousewheelaxis'){const hit=[...this.scrollHits].reverse().find(h=>h.max>0&&contains(h,...this.pointer)&&h.view.options.acceptInput());return hit?this.scrollTo(hit,(hit.view.scrollOffsets.get(hit.node.id)||0)-packet.value*48):false;}
  if(packet.pointer){this.pointer=packet.pointer.position;if(this.scrollDrag){const hit=this.scrollDrag;if(hit.view.disposed||!hit.view.options.acceptInput()){this.scrollDrag=null;return false;}return this.scrollTo(hit,(this.scrollLocal(hit)[1]-hit.grab)/(hit.h-hit.thumb)*hit.max);}`);
replace("if(packet.device==='mouse'&&packet.key==='leftmousebutton'){",`if(packet.device==='mouse'&&packet.key==='leftmousebutton'){
   if(!packet.value&&this.scrollDrag){this.scrollDrag=null;return true;}
   if(packet.value){const hit=[...this.scrollHits].reverse().find(h=>h.max>0&&contains(h,...this.pointer)&&this.scrollLocal(h)[0]>=h.w-12&&h.view.options.acceptInput());if(hit){const y=this.scrollLocal(hit)[1],top=(hit.view.scrollOffsets.get(hit.node.id)||0)/hit.max*(hit.h-hit.thumb);hit.grab=y>=top&&y<=top+hit.thumb?y-top:hit.thumb/2;this.scrollDrag=hit;return this.scrollTo(hit,(y-hit.grab)/(hit.h-hit.thumb)*hit.max);}}
  `);
replace('ctx.clearRect(0,0,width,height);this.hits=[];', 'ctx.clearRect(0,0,width,height);this.hits=[];this.scrollHits=[];');
replace("if(node.type==='ScrollBox'){ctx.beginPath();ctx.rect(0,0,w,h);ctx.clip();}ctx.translate(-x,-y);for(let i=0;i<list.length;i++)await draw(list[i],childBox,node.type,i,list,active);ctx.restore();",`let scroll;
    if(node.type==='ScrollBox'){const bottom=Math.max(h,...list.map((child,i)=>{const r=widgetFlexBox(child,childBox,node.type,i,list,scale);return r.y+r.h-y;})),max=Math.max(0,bottom-h),offset=clamp(view.scrollOffsets.get(node.id)||0,0,max);view.scrollOffsets.set(node.id,offset);scroll={...hit,max,offset,thumb:Math.min(h,Math.max(24,h*h/bottom))};this.scrollHits.push(scroll);ctx.beginPath();ctx.rect(0,0,w,h);ctx.clip();ctx.translate(0,-offset);}
    ctx.translate(-x,-y);for(let i=0;i<list.length;i++)await draw(list[i],childBox,node.type,i,list,active);
    if(scroll?.max>0){ctx.translate(x,y+scroll.offset);ctx.globalAlpha*=.65;ctx.fillStyle=p.color;ctx.fillRect(w-8,scroll.offset/scroll.max*(h-scroll.thumb),6,scroll.thumb);}ctx.restore();`);
const destination=path.join(work,'native-widget-layer.candidate.mjs');await fs.writeFile(destination,candidate);const sha=b=>createHash('sha256').update(b).digest('hex');await fs.writeFile(path.join(work,'report.json'),JSON.stringify({source:file,originalSHA256:sha(source),candidateSHA256:sha(candidate),destination,engineOriginalModified:false,scope:'Owned ScrollBox candidate: per-view offset/clamp, clipping, wheel consumption, scrollbar drag and programmatic scrollTop. C++ wheel dispatch is still separately required.'},null,2));console.log(JSON.stringify({file:destination}));
