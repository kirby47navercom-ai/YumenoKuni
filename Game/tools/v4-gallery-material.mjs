import fs from 'node:fs/promises';import path from 'node:path';
import {sourceRows,sourceSvg} from './v3-source-svg.mjs';

// Original display-list carriers. Project records, prices and unlocks stay dynamic.
export async function emitGalleryMaterial({repo,write,source}){
 const base='Assets/Art/ui/v3/gallery/',cursors={top:[],list:[]},badges={top:[],list:[]},badgeTextures={top:[],list:[]},receipts=[];
 const render=async(name,rows)=>{if(!rows.length)throw Error('Empty original gallery carrier '+name);const file=base+name+'.svg';await write(file,await sourceSvg(rows));for(const r of rows)if(r.texture&&!receipts.some(x=>x.path===r.texture))receipts.push({path:r.texture,resource:r.resource});return file;};
 const bg=(await sourceRows('g_bg')).filter(r=>!r.path.startsWith('p_chara/'));
 const title=await render('title',await sourceRows('g_title_US'));
 const backgrounds={};
 const newMaster=(await sourceRows('g_menu_new'))[0];
 for(const [kind,f,count]of [['top','g_topmenu_US',8],['list','g_menu_US',11]]){
  const rows=await sourceRows(f);
  backgrounds[kind]=await render(kind,[...bg,...rows.filter(r=>r.path==='p_base/1'||r.path.startsWith('i_kanban_hasira/'))]);
  for(let i=0;i<count;i++){
   const n=String(i).padStart(3,'0');cursors[kind].push(await render('cursor_'+kind+'_'+i,rows.filter(r=>r.path.startsWith('p_ef_'+n+'/'))));
   let badge;if(kind==='top')badge=structuredClone(rows.find(r=>r.path==='p_new_'+n+'/i_mate_new/1'));
   else{
    const slot=rows.find(r=>r.path==='p_new_'+n+'/i_dammy/1');if(!slot)throw Error('Missing gallery NEW attachment '+i);
    badge=structuredClone(newMaster);badge.sourceAffine[4]+=slot.sourceAffine[4];badge.sourceAffine[5]+=slot.sourceAffine[5];badge.rect[0]+=slot.sourceAffine[4]*2/3;badge.rect[1]+=slot.sourceAffine[5]*2/3;
   }
   if(!badge)throw Error('Missing gallery NEW raster '+kind+'/'+i);
   badges[kind].push(badge.rect);badgeTextures[kind].push(await render('new_'+kind+'_'+i,[badge]));
  }
 }
 const coinDigits=[];const manifest=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/all_general/manifest.json'),'utf8'));
 const coinRows=(await sourceRows('g_menu_US')).filter(r=>r.path.startsWith('p_medal/'));
 for(let slot=0;slot<3;slot++){
  const source=coinRows.find(r=>r.path==='p_medal/p_medal_'+String(slot).padStart(3,'0')+'/1');if(!source)throw Error('Missing original coin slot '+slot);coinDigits.push([]);
  for(let digit=0;digit<10;digit++){const t=manifest.textures.find(t=>t.container==='g_menu_US'&&t.resource==='number_'+String(digit).padStart(3,'0')+'.png');if(!t)throw Error('Missing original coin digit '+digit);const row=structuredClone(source);row.texture=t.file;row.resource=t.resource;coinDigits[slot].push(await render('coin_'+slot+'_'+digit,[row]));}
 }
 const playing=[];const list=await sourceRows('g_menu_US');for(let i=0;i<11;i++)playing.push(await render('playing_'+i,list.filter(r=>r.path.startsWith('p_sound_icon_'+String(i).padStart(3,'0')+'/'))));
 return {cursors,badges,badgeTextures,playing,coinDigits,receipts,backgrounds,title,text:{on:'#000000',off:'#ffffff'},policy:'Original gallery backdrop without original character art, steel panels, selection mate, title and NEW bitmap at SFL affine/masks. List NEW child attached to retained native placeholder; project own Korean records, images and unlock policy retained. GPU shader, intro/outro and pulse timing parity unclaimed.'};
}
