// Actual game ScrollBox asset, isolated native painter/input reproduction.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {openNativePackage} from '../../../engineCreate/tools/native-game-platform.mjs';
import {NativeWidgetLayer} from '../../../engineCreate/tools/native-widget-layer.mjs';
const root=path.resolve(import.meta.dirname,'..'),build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8')),work=path.join(root,'Saved/native-scroll-'+Date.now());await fs.mkdir(work,{recursive:true});
const pack=await openNativePackage(build.output),widget=JSON.parse(await fs.readFile(await pack.resolve('Assets/UI/TrialPickerV4.hbwidget.json'),'utf8'));
const names=new Set(['Root','PkBodyScroll','PkEvidenceBody']);for(const n of widget.nodes)n.properties.visible=names.has(n.name);const body=widget.nodes.find(n=>n.name==='PkEvidenceBody');body.properties.text=Array.from({length:24},(_,i)=>'근거 설명 '+(i+1)+'번째 줄').join('\n');body.slot.offset[3]=24*39;
let png;const layer=new NativeWidgetLayer(pack,async(op,data)=>{assert.equal(op,'ui');png=Buffer.from(data.png,'base64');});layer.layout=[];
try{
 layer.create(widget,{acceptInput:()=>true,event:()=>{},input:()=>{}},{owner:'diagnostic',instance:'actual-game-scroll-fixture'});await layer.draw(1280,720);const before=png,rect=layer.layout.find(n=>n.id==='PkBodyScroll');assert(rect);layer.input({device:'mouse',pointer:{position:[rect.x+30,rect.y+40]}});let consumed=false;for(let i=0;i<8;i++)consumed=!!layer.input({device:'mouse',key:'MouseWheelAxis',value:-1})||consumed;await layer.draw(1280,720);assert(before.equals(png),'Baseline must reproduce unchanged clipped ScrollBox');assert.equal(consumed,false);
 const cpp=await fs.readFile(path.resolve(root,'../../engineCreate/native/desktop/HBNativePlayer.cpp'),'utf8');assert(!cpp.includes('WM_MOUSEWHEEL'));
 await fs.writeFile(path.join(work,'clipped.png'),png);await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,productBehavior:'FAIL-native-ScrollBox-has-no-scrolling',work,build:build.id,actualWidget:'TrialPickerV4.hbwidget.json',fixture:true,visibleHeight:rect.h,textHeight:body.slot.offset[3],wheelConsumed:consumed,pixelsUnchanged:true,cppWheelMessageHandler:false,pngSHA256:createHash('sha256').update(png).digest('hex'),scope:'Own game ScrollBox with explicit long-text fixture in the actual native widget layer. C++ host also lacks wheel dispatch. Read-only engine proof; not an authored task played-path claim.'},null,2));console.log(JSON.stringify({work,behavior:'FAIL-native-ScrollBox-has-no-scrolling'}));
}finally{layer.dispose();pack.host.close();}
