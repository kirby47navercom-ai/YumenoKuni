import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../engineCreate/prototype/ui-assets.js';
import {validGameJson} from '../engineCreate/prototype/game-json.js';
export async function emitDifficultyV4({repo,write}){
 const contract=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/difficulty_remaining_contract.json'),'utf8')),g=contract.UI_reference.geometry;
 const children=new Map(g.child_table5_samples.map(x=>[x.entry,x.children])),shapes=new Map(g.shape_table3_rects.map(x=>[x.entry,x.rects])),textures=new Map(),receipts=[];
 for(const t of g.texture_table2){const bytes=await fs.readFile(path.join(repo,t.provided_png));if(bytes.readUInt32BE(16)!==t.provided_size[0]||bytes.readUInt32BE(20)!==t.provided_size[1])throw Error('Difficulty PNG size changed '+t.source_name);textures.set(t.image_id,{...t,uri:'data:image/png;base64,'+bytes.toString('base64')});receipts.push({name:t.source_name,path:t.provided_png,sha256:createHash('sha256').update(bytes).digest('hex')});}
 const alphaBounds=JSON.parse(execFileSync('python',['-X','utf8','-c',"import json,sys;from PIL import Image;print(json.dumps({n:Image.open(p).convert('RGBA').getchannel('A').getbbox() for n,p in json.load(sys.stdin)}))"],{input:JSON.stringify(g.texture_table2.map(t=>[t.source_name,path.join(repo,t.provided_png)])),encoding:'utf8'}));
 const matrix=m=>[m[0],m[2],m[3],m[1],m[4],m[5]],identity=[1,0,0,1,0,0];
 const mul=(p,q)=>[p[0]*q[0]+p[2]*q[1],p[1]*q[0]+p[3]*q[1],p[0]*q[2]+p[2]*q[3],p[1]*q[2]+p[3]*q[3],p[0]*q[4]+p[2]*q[5]+p[4],p[1]*q[4]+p[3]*q[5]+p[5]];
 const rect=(r,m)=>{const [x,b,y,d]=r,pts=[[x,y],[b,y],[b,d],[x,d]].map(([x,y])=>[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]]),xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);return [Math.min(...xs),Math.min(...ys),Math.max(...xs)-Math.min(...xs),Math.max(...ys)-Math.min(...ys)].map(v=>v*2/3);};
 const variants=[],valueRects=[[],[]];let startRect;
 for(let row=0;row<3;row++){variants[row]=[];for(let logic=0;logic<3;logic++){variants[row][logic]=[];for(let action=0;action<3;action++){
  const roots=structuredClone(g.normal_root),patch=g.wait_record_patches.find(p=>p.label===(row===0?'fl_wait_000':row===1?'fl_wait_001':'fl_wait_ok'));
  for(const p of patch?.updates||[]){let r=roots.find(r=>r.depth===p.depth);if(!r){r={depth:p.depth};roots.push(r);}Object.assign(r,p);}
  let serial=0;const hits={};
  const walk=(node,parent,root,depth=0,opacity=1,rgb=[1,1,1])=>{
   if(depth>20||!node.ref)return '';const m=mul(parent,node.matrix?matrix(node.matrix):identity),alpha=opacity*(node.color?.[0]?.[3]??1)+(node.color?.[1]?.[3]??0),tint=rgb.map((v,i)=>v*(node.color?.[0]?.[i]??1));if(alpha<=0)return '';const [table,entry]=node.ref;
   if(table===5)return (children.get(entry)||[]).sort((a,b)=>a.depth-b.depth).map(n=>walk(n,m,root,depth+1,alpha,tint)).join('');
   if(table===4&&root==='p_nanido_setumei'){const caption=row===0?'오답의 피해와 추리 시간을 조절해요.':row===1?'조작 판정과 구슬의 속도를 조절해요.':'선택한 두 난이도로 시작해요.';return `<g transform="matrix(${m.join(' ')})"><text x="0" y="44" font-family="Malgun Gothic" font-size="44" fill="#efeeea">${caption}</text></g>`;}
   if(table!==3)return '';return (shapes.get(entry)||[]).map(([image,x,b,y,d])=>{
    const t=textures.get(image);if(!t||/_ef_DXT1|material_ef/.test(t.source_name))return '';const a=alphaBounds[t.source_name],w=b-x,h=d-y;hits[root]??=rect(a?[x+a[0]*w/t.provided_size[0],x+a[2]*w/t.provided_size[0],y+a[1]*h/t.provided_size[1],y+a[3]*h/t.provided_size[1]]:[x,b,y,d],m);
    const filter=tint.some(v=>v<.99)?`<filter id="t${++serial}" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="${tint[0]} 0 0 0 0 0 ${tint[1]} 0 0 0 0 0 ${tint[2]} 0 0 0 0 0 1 0"/></filter>`:'';
    return filter+`<g transform="matrix(${m.join(' ')})" opacity="${Math.min(1,alpha)}"${filter?` filter="url(#t${serial})"`:''}><image href="${t.uri}" x="${x}" y="${y}" width="${b-x}" height="${d-y}" preserveAspectRatio="none"/></g>`;
   }).join('');
  };
  const art=roots.sort((a,b)=>a.depth-b.depth).map(r=>{
   const match=r.name?.match(/^p_(off_on|off|on)_(\d{2})_(\d{2})$/);if(match){const axis=Number(match[2]),value=Number(match[3]),selected=(axis?action:logic)===value,kind=selected?(row===axis?'on':'off_on'):'off';if(match[1]!==kind)return '';r.color??=[[1,1,1,1],[0,0,0,0]];r.color[0][3]=1;}
   return walk(r,identity,r.name);
  }).join('');
  const file=`Assets/Art/ui/v3/difficulty/state_${row}_${logic}_${action}.svg`;variants[row][logic][action]=file;await write(file,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" preserveAspectRatio="none"><g transform="scale(.666666666666667)">${art}</g></svg>`);
  for(let axis=0;axis<2;axis++)for(let value=0;value<3;value++){const prefix=`${String(axis).padStart(2,'0')}_${String(value).padStart(2,'0')}`;valueRects[axis][value]??=hits['p_off_'+prefix]||hits['p_off_on_'+prefix]||hits['p_on_'+prefix];}startRect??=hits.p_start_JP_text_000;
 }}}
 const union=rects=>{const l=Math.min(...rects.map(r=>r[0])),t=Math.min(...rects.map(r=>r[1])),right=Math.max(...rects.map(r=>r[0]+r[2])),bottom=Math.max(...rects.map(r=>r[1]+r[3]));return [l,t,right-l,bottom-t];};
 if(!startRect||valueRects.flat().some(r=>!r))throw Error('Missing difficulty source hit carriers');
 const layout={variants,values:valueRects,rows:[...valueRects.map(union),startRect],receipts,scope:'Provided26 Korean PNGs and normal-stop25 composed affine/row-wait colors, alpha-ink hit bounds. Own explicit on/off/off_on root-selection policy because3ad9b0 body is absent; additive effects and original in/out playback are not claimed. Description is own Korean text at retained text root, not an original literal.'};
 const widget=createWidgetAsset('DifficultyV4');widget.scaleMode='scale';widget.scaleRule='fit';for(const [type,id,props]of [['Panel','DfShade',{background:'#19151eef'}],['Image','DfArt',{texture:variants[0][1][1],imageFit:'fill'}]]){const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=[0,0,1280,720];Object.assign(n.properties,{padding:0,focusable:false,...props});widget.nodes.push(n);}
 if(!validWidgetAsset(widget)||!validGameJson(layout))throw Error('Difficulty native JSON bounds');await write('Assets/UI/DifficultyV4.hbwidget.json',widget);await write('Assets/Data/v4_story/difficulty_layout.json',layout);return {nodes:widget.nodes.length,variants:27,provided:receipts.length};
}
// Focused producer entry avoids re-exporting every character/map for a UI-only edit.
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),root=path.join(repo,'Game');
 const write=async(file,data)=>{const target=path.join(root,file);await fs.mkdir(path.dirname(target),{recursive:true});const temporary=target+'.tmp';await fs.writeFile(temporary,typeof data==='string'?data:JSON.stringify(data,null,1)+'\n');await fs.rename(temporary,target);};
 console.log(JSON.stringify(await emitDifficultyV4({repo,write})));
}
