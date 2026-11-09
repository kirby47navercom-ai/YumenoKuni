// Compose the original family display list; callers choose its actual visual slots.
import fs from 'node:fs/promises';import path from 'node:path';
const root=path.resolve(import.meta.dirname,'../..'),banks=new Map(),textures=new Map();
const esc=s=>s.replaceAll('&','&amp;').replaceAll('"','&quot;');
export async function sourceBank(name='all_general'){if(!banks.has(name))banks.set(name,JSON.parse(await fs.readFile(path.join(root,'ui/v3_authorized',name,'layout.json'),'utf8')));return banks.get(name);}
export async function sourceRows(family,state='fl_wait',bank='all_general'){const d=await sourceBank(bank),f=d[family];if(!f)throw Error('Missing original UI family '+family);const r=f.states[state];if(!r)throw Error('Missing original UI state '+family+'/'+state);return structuredClone(r);}
export async function sourceSvg(rows,{bounds=[0,0,1280,720]}={}){
 let serial=0;const defs=[];
 const image=async r=>{if(!r.opacity)return '';const[a,b,c,d,x,y]=r.sourceAffine,w=r.rect[2]*1.5/Math.hypot(a,b),h=r.rect[3]*1.5/Math.hypot(c,d);let ink;
  if(r.resource?.startsWith('__solid_'))ink='<rect width="'+w+'" height="'+h+'" fill="'+(r.resource==='__solid_white'?'white':'black')+'"/>';
  else{if(!r.texture)throw Error('Missing original raster '+r.resource);if(!textures.has(r.texture))textures.set(r.texture,'data:image/png;base64,'+(await fs.readFile(path.join(root,r.texture))).toString('base64'));ink='<image href="'+textures.get(r.texture)+'" width="'+w+'" height="'+h+'" preserveAspectRatio="none"/>';}
  const m=r.colorMultiply||[1,1,1],v=r.colorAdd||[0,0,0];let filter='';if(m.some((n,i)=>n!==1||v[i]!==0)){const id='color'+serial++;defs.push('<filter id="'+id+'" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="'+[m[0],0,0,0,v[0],0,m[1],0,0,v[1],0,0,m[2],0,v[2],0,0,0,1,0].join(' ')+'"/></filter>');filter=' filter="url(#'+id+')"';}
  let out='<g transform="matrix('+[a,b,c,d,x,y].join(' ')+')" opacity="'+r.opacity+'"'+filter+'>'+ink+'</g>';
  for(const clip of r.clips||[]){const id='mask'+serial++,parts=[];for(const row of clip)parts.push(await image({...row,colorMultiply:[0,0,0],colorAdd:[1,1,1]}));defs.push('<mask id="'+id+'" mask-type="alpha" maskUnits="userSpaceOnUse" x="-4096" y="-4096" width="8192" height="8192">'+parts.join('')+'</mask>');out='<g mask="url(#'+id+')">'+out+'</g>';}
  return out;
 };
 const parts=[];for(const row of rows)parts.push(await image(row));return '<svg xmlns="http://www.w3.org/2000/svg" width="'+bounds[2]+'" height="'+bounds[3]+'" viewBox="'+bounds.join(' ')+'" preserveAspectRatio="none"><defs>'+defs.join('')+'</defs><g transform="scale(.666666666666667)">'+parts.join('')+'</g></svg>';
}
export async function emitSourceFamily(write,target,family,state='fl_wait',select=()=>true,bank='all_general'){
 const rows=(await sourceRows(family,state,bank)).filter(select);if(!rows.length)throw Error('Empty original UI selection '+family+'/'+state);await write(target,await sourceSvg(rows));return rows;
}
