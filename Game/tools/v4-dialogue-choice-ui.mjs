import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
// Original adv_choices bitmap ink and source geometry; own narrative text stays dynamic.
export async function emitV4DialogueChoice({repo,write}){
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/dialogue_choice_ui_contract.json'),'utf8'));
 const source=c.ordinary_geometry.own_projection;
 const tracks=c.selection_confirm.tracks.map(t=>({count:t.count,index:t.selected_index,slot:t.physical_slot,frames:t.select_track.map(f=>({base:f.base_xy.map(n=>n*2/3),text:f.text_xy.map(n=>n*2/3),active:f.active_xy?.map(n=>n*2/3)||null}))}));
 const characters=new Set(Array.from('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ×·…「」!? /:+-()'));
 const collect=v=>{if(typeof v==='string'){for(const ch of v)characters.add(ch);}else if(Array.isArray(v))v.forEach(collect);else if(v&&typeof v==='object')Object.values(v).forEach(collect);};
 for(const dir of ['chapters','freetime'])for(const name of await fs.readdir(path.join(repo,'data/v4_story',dir)))if(name.endsWith('.json'))collect(JSON.parse(await fs.readFile(path.join(repo,'data/v4_story',dir,name),'utf8')));
 collect(JSON.parse(await fs.readFile(path.join(repo,'data/gifts.json'),'utf8')));
 const advances=JSON.parse(execFileSync('python',['-X','utf8','-c','import json,sys;from PIL import ImageFont;p=json.load(sys.stdin);f=ImageFont.truetype(p["font"],300);print(json.dumps({c:round(f.getlength(c)/300*p["size"],5) for c in p["chars"]},ensure_ascii=False))'],{input:JSON.stringify({font:path.join(repo,'fonts/pretendard/Pretendard-Medium.otf'),size:source.font_height,chars:[...characters]}),encoding:'utf8',maxBuffer:8*1024*1024}));
 const entries=Object.entries(advances),buckets=[];for(let i=0;i<entries.length;i+=512)buckets.push(Object.fromEntries(entries.slice(i,i+512)));
 const layout={source,tracks,advances:buckets,own_long_label_width:390,own_confirm_updates:12};
 const authored=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/chapters/1.json'),'utf8')).nodes;
 layout.fixtures=Object.entries(authored).filter(([,n])=>n.type==='menu').map(([id,n])=>({id,score:Math.max(0,...n.options.map(o=>Buffer.byteLength(o.label||'')))})).sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).map(n=>n.id);
 const sourceFolder=path.join(repo,'ui/v4/adv_source'),sourceLayout=JSON.parse(await fs.readFile(path.join(sourceFolder,'layout.json'),'utf8'));
 const wrap=async(file,w,h)=>{const raw=await fs.readFile(path.join(sourceFolder,file));return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><image href="data:image/png;base64,${raw.toString('base64')}" width="${w}" height="${h}" preserveAspectRatio="none"/></svg>`;};
 for(const name of ['off','on','flash'])await write('Assets/Art/ui/v3/choice_'+name+'.svg',await wrap('choice_'+name+'.png',880,75));
 await write('Assets/Art/ui/v3/choice_check.svg',await wrap('choice_check.png',60,60));
 for(const track of layout.tracks){track.confirmationAssets=[];for(const [frame,file]of sourceLayout.confirmationFrames[track.count+':'+track.index].entries()){const target=`Assets/Art/ui/v3/choice_confirm_${track.count}_${track.index}_${frame}.svg`;await write(target,await wrap(file,880,75));track.confirmationAssets.push(target);}}
 layout.scope='Original adv_choices bitmap ink/alpha, exact 2/3/4-slot focus tracks and original confirm color/RGBA frames. Current PC input, authored decisions and bounded long-label marquee remain; original in/out and additive renderer timing are not claimed.';
 layout.sourceRasterManifest='ui/v3_authorized/adv_source/manifest.json';layout.sourceConfirmUpdates=12;
 await write('Assets/Data/v4_story/choice_layout.json',layout);
 return layout;
}
