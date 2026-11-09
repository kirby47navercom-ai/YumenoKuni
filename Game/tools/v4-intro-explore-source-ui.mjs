import fs from 'node:fs/promises';import path from 'node:path';import {createHash} from 'node:crypto';
const repo=path.resolve(import.meta.dirname,'../..');
export async function emitIntroExploreSourceUI({write}){
 const m=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/intro_explore_source/manifest.json'),'utf8')),paths=[];
 const raster=async(name,target,w,h)=>{const r=m.records[name];if(!r)throw Error('Missing original Intro/Explore UI '+name);const bytes=await fs.readFile(path.join(repo,r.file));if(createHash('sha256').update(bytes).digest('hex')!==r.sha256)throw Error('Changed original Intro/Explore UI '+name);await write(target,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><image href="data:image/png;base64,${bytes.toString('base64')}" width="${w}" height="${h}" preserveAspectRatio="xMidYMid meet"/></svg>`);paths.push(target);};
 const base='Assets/Art/ui/';
 for(let i=0;i<5;i++)for(const part of ['glyph','glow'])await raster('nonstop_'+part+i,base+'nonstop_'+part+i+'.svg',256,300);
 for(const [name,w,h]of [['title',1280,260],['start',700,300],['start_echo',700,300],['hoop',800,800],['streaks',1660,180]])await raster('nonstop_'+name,base+'nonstop_'+name+'.svg',w,h);
 for(const name of ['ex_cross','ex_cross_on'])await raster(name,base+name+'.svg',200,200);
 for(const key of ['map','bullet','gift','card','rules','option'])await raster('pad_icon_'+key,base+'v3/pad_home/icon_'+key+'.svg',140,140);
 return{source:m.sourceManifest,resources:paths,cameraTimingChanged:false,reticle:{nodeSize:[200,200],idleInkSize:[133.333333,133.333333],focusInkSize:[200,200],centered:true},padSide:'Native theme is already fullscreen. Root hides the invented PdSide panel; no unrelated source is repurposed as a side bar.',area:'No matching native field location panel established; root hides AreaBand/Icon and preserves own AreaName text.'};
}
