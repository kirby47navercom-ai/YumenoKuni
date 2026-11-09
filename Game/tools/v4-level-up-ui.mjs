import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';

// Missing source pixels: own readable ink, authored root/independent child transforms.
export async function emitLevelUp({repo,write}){
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/growth_remaining_contract.json'),'utf8'));
 const source=c.levelup_and_display_delay.source_UI.record_geometry_followup;
 const bytes=await fs.readFile(source.metadata_path);
 if(createHash('sha256').update(bytes).digest('hex')!==source.metadata_file_sha256)throw Error('Level-up metadata changed');
 const roots=new Map(source.root_records.map(r=>[r.record,r])),children=source.child_loop.local_records;
 const mul=(p,q)=>[p[0]*q[0]+p[2]*q[1],p[1]*q[0]+p[3]*q[1],p[0]*q[2]+p[2]*q[3],p[1]*q[2]+p[3]*q[3],p[0]*q[4]+p[2]*q[5]+p[4],p[1]*q[4]+p[3]*q[5]+p[5]];
 const ink=l=>{
  const [x,r,y,b]=l.local_lrtb,w=r-x,h=b-y;
  if(l.image_id===0)return `<path d="M${x} ${y}H${r}V${b}H${x}Z" fill="#ffdf15"/><path d="M${x} ${b}H${r}" stroke="#151321" stroke-width="2"/>`;
  if(l.image_id===1)return `<path d="M${x+w/2} ${y}L${r} ${b}H${x}Z" fill="#ffdf15" stroke="#151321" stroke-width="2"/>`;
  if(l.image_id===2)return `<text x="${x+w/2}" y="${b-1}" text-anchor="middle" font-family="Arial Black,Malgun Gothic,sans-serif" font-weight="900" font-size="${h}">!</text>`;
  return `<text x="${x+5}" y="${b-5}" font-family="Arial Black,Malgun Gothic,sans-serif" font-weight="900" font-size="${h*.8}" fill="#151321">레벨 업!</text>`;
 };
 const draw=(leaf,m=leaf.affine_design,a=leaf.alpha_product)=>a<=0?'':`<g transform="matrix(${m.join(' ')})" opacity="${a}">${ink(leaf)}</g>`;
 const frame=async(record,child,name)=>{
  const root=roots.get(record),parent=root.named_placements.find(p=>p.path==='i_tri_bikkuri');
  let body=root.leaves.filter(l=>!l.path.startsWith('i_tri_bikkuri/')).map(l=>draw(l)).join('');
  if(parent)body+=children[child%45].leaves.map(l=>draw(l,mul(parent.affine_design,l.affine_design),parent.alpha_product*l.alpha_product)).join('');
  const asset=`Assets/Art/ui/v3/level_up/${name}.svg`;
  await write(asset,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" preserveAspectRatio="none"><g transform="scale(.666666666666667)">${body}</g></svg>`);return asset;
 };
 const layout={in:[],wait:[],out:[],scope:'Source root2..18/19..32 and independent45-record child geometry; own75 readable vector composites and admitted60Hz record clock. Root completion +60hold increments +61st ready exit remain separate. No source pixel/audio identity claim.'};
 for(let i=0;i<16;i++)layout.in.push(await frame(2+i,i,'in_'+i));
 for(let i=0;i<45;i++)layout.wait.push(await frame(18,i,'wait_'+i));
 for(let i=0;i<14;i++)layout.out.push(await frame(19+i,77+i,'out_'+i));
 await write('Assets/Data/v4_story/level_up_layout.json',layout);return layout;
}
