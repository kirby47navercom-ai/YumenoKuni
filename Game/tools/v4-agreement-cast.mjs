// Agreement owns its art/pivots. Never replace the generic T03 used by other modes.
import fs from'node:fs/promises';import path from'node:path';import assert from'node:assert/strict';import{createHash}from'node:crypto';import{createRequire}from'node:module';
import{createWidgetNode}from'../engineCreate/prototype/ui-assets.js';
const require=createRequire(new URL('../engineCreate/package.json',import.meta.url)),{createCanvas,loadImage}=require('@napi-rs/canvas');
export function centerEndingSourceCanvas(widget){
 widget.nodes=widget.nodes.filter(n=>n.id!=='EndingContent');
 const template=widget.nodes.find(n=>n.id==='EndingLeaf0');
 for(const node of widget.nodes)if(/^EndingLeaf\d+$/.test(node.id)){node.parent='root';node.slot.anchors=[0,0,0,0];}
 for(let i=0;i<16;i++)for(const wide of [false,true]){
  const id=(wide?'EndingWide':'EndingAgree')+i;let node=widget.nodes.find(n=>n.id===id);if(!node){node=structuredClone(template);node.id=node.name=id;widget.nodes.push(node);}
  node.parent='root';node.slot.anchors=wide?[0,.5,1,.5]:[.5,.5,.5,.5];node.slot.offset=wide?[0,-360,0,720]:[-640,-360,1280,720];node.slot.zIndex=701+i;node.properties.visible=false;
 }
 const black=widget.nodes.find(n=>n.id==='EndingBlack');black.slot.anchors=[0,0,1,1];black.slot.offset=[0,0,0,0];return widget;
}
export function agreementHeader(header,files,shadowFiles){
 const match=header.match(/inline const std::vector<std::string> textures\{(.*?)\};/s);assert(match,'Existing ending texture table');
 const textures=JSON.parse('['+match[1]+']'),ids=file=>{let i=textures.indexOf(file);if(i<0){i=textures.length;textures.push(file);}return i;};
 const records=Object.entries(files).map(([slug,[normal,shadow]])=>[slug,[ids(normal),ids(shadow)]]),shadowIds=shadowFiles.map(file=>{const at=textures.indexOf(file);assert(at>=0,'Original source shadow carrier '+file);return at;});
 header=header.replace(match[0],'inline const std::vector<std::string> textures{'+textures.map(JSON.stringify).join(',')+'};');
 header=header.replace(/\/\/ AGREEMENT_CAST_BEGIN[\s\S]*?\/\/ AGREEMENT_CAST_END\n?/g,'');
 const block='// AGREEMENT_CAST_BEGIN\ninline const std::map<std::string,std::array<int,2>> agreePortraits{'+records.map(([slug,index])=>'{'+JSON.stringify(slug)+',{'+index.join(',')+'}}').join(',')+'};\ninline const std::set<int> agreeShadowTextures{'+shadowIds.join(',')+'};\n// AGREEMENT_CAST_END\n';
 return header.replace('inline const std::map<int,std::string> climaxTargets',block+'inline const std::map<int,std::string> climaxTargets');
}
export async function emitAgreementCast({game,repo,write,sourceHeader}){
 const root=path.join(repo,'ui/v4/debate_feedback/agreement'),manifest=JSON.parse(await fs.readFile(path.join(root,'manifest.json'),'utf8')),files={};
 for(const row of manifest.rows.filter(r=>r.role!=='hero')){const file='Assets/Art/ui/ending_source/agree_'+row.file;await write(file,await fs.readFile(path.join(root,row.file)));files[row.slug]??=[];files[row.slug][row.role==='shadow'?1:0]=file;}
 assert.equal(Object.keys(files).length,16);
 const container='t_ronpa_sansei_momota_JP',layout=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/endings/layout.json'),'utf8'))[container],inventory=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/endings/manifest.json'),'utf8'));
 const rows=new Map(),shadows=[];for(const frame of layout.frames)for(const row of frame)if(/^t_ronpa_chara_00[01]\.png$/.test(row.resource)){
  const key=JSON.stringify([container,row.resource,row.colorMultiply,row.colorAdd,row.clips,row.clips?.length?row.rect:null,row.clips?.length?row.rotation:null]),file='Assets/Art/ui/ending_source/'+createHash('sha256').update(key).digest('hex').slice(0,20)+'.png';rows.set(file,row);
 }
 const hero=await loadImage(path.join(root,'mio_hero.png'));
 for(const[file,row]of rows){
  assert(!row.clips?.length,'Agreement character clip requires an explicit source mapping');
  if(row.resource==='t_ronpa_chara_001.png'){if(row.colorMultiply.every(v=>v===0))shadows.push(file);continue;}
  const source=inventory.textures.find(r=>r.container===container&&r.resource===row.resource);assert(source);const [w,h]=source.size;assert.equal(w,h,'Square source character carrier');
  const c=createCanvas(w,h),ctx=c.getContext('2d');ctx.drawImage(hero,0,0,w,h);const pixels=ctx.getImageData(0,0,w,h),mul=row.colorMultiply||[1,1,1],add=row.colorAdd||[0,0,0];
  for(let at=0;at<pixels.data.length;at+=4)for(let channel=0;channel<3;channel++)pixels.data[at+channel]=Math.round(Math.min(255,Math.max(0,pixels.data[at+channel]*mul[channel]+add[channel]*255)));
  ctx.putImageData(pixels,0,0);await write(file,c.toBuffer('image/png'));
 }
 assert(shadows.length);const before=sourceHeader??await fs.readFile(path.join(game,'Source/EndingSourceFramesV4.hpp'),'utf8');await write('Source/EndingSourceFramesV4.hpp',agreementHeader(before,files,shadows));
 const heroRows=[...rows].filter(([,r])=>r.resource==='t_ronpa_chara_000.png');
 return {files,shadowFiles:shadows,overwrittenHero:heroRows.map(([file])=>file),heroNormal:heroRows.find(([,r])=>r.colorMultiply.some(v=>v>0))[0],heroShadow:heroRows.find(([,r])=>r.colorMultiply.every(v=>v===0))[0],sourceQuadRetained:true,otherTimelineIndicesRetained:true};
}
