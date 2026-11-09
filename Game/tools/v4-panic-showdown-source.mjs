import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const repo=path.resolve(import.meta.dirname,'../..');
export async function trialModeSource(){
 const manifest=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/trial_modes_source/manifest.json'),'utf8'));
 const data=new Map();
 const image=async name=>{if(!data.has(name)){const row=manifest.records[name];if(!row)throw Error('Missing original trial mode UI '+name);const b=await fs.readFile(path.join(repo,row.file));if(createHash('sha256').update(b).digest('hex')!==row.sha256)throw Error('Changed original trial mode UI '+name);data.set(name,'data:image/png;base64,'+b.toString('base64'));}return data.get(name);};
 const svg=(w,h,ink)=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">${ink}</svg>`;
 const raster=async(name,w,h)=>svg(w,h,`<image href="${await image(name)}" width="${w}" height="${h}" preserveAspectRatio="none"/>`);
 return {manifest,image,svg,raster};
}
export async function emitPanicShowdownSource({write}){
 const {image,svg,raster}=await trialModeSource(),base='Assets/Art/ui/';
 // Keep the original full-screen red/blue SFL pattern in its own plane. Each
 // legacy half-screen node crops that plane, rather than stretching half art.
 for(const [name,x]of [['showdown_left',0],['showdown_grid',640]])await write(base+name+'.svg',svg(640,720,`<image href="${await image('showdown_frame')}" x="${-x}" width="1280" height="720"/>`));
 await write(base+'showdown_divider.svg',svg(88,720,`<image href="${await image('showdown_divider')}" x="-596" width="1280" height="720"/>`));
 await write(base+'showdown_pointer_bg.svg',await raster('showdown_pointer_bg',256,256));
 await write(base+'showdown_pointer_mask.svg',await raster('showdown_pointer_mask',256,256));
 const line=await image('panic_line');
 const boundary=([x1,y1,x2,y2])=>{const len=Math.hypot(x2-x1,y2-y1),angle=Math.atan2(y2-y1,x2-x1)*180/Math.PI-90;return `<image href="${line}" x="-3.333333" y="0" width="6.666667" height="${len}" transform="translate(${x1} ${y1}) rotate(${angle})" preserveAspectRatio="none"/>`;};
 // These are the existing native-CDV camera pane boundaries. Camera output
 // remains live; no invented tinted polygons or static character pictures.
 for(let i=0;i<3;i++)await write(base+`panic_${i}.svg`,svg(1280,720,i===0?[[761,0,253,720],[577,266,1226,720]].map(boundary).join(''):''));
 for(let i=0;i<3;i++)await write(base+`panic_intro_${i}.svg`,await raster('panic_intro_'+i,683.333333,85.333333));
 await write(base+'panic_word_lock.svg',await raster('panic_word_lock',1280,720));
 return {scope:'Actual original t_hr and t_panic bitmaps/SFL planes; existing input/camera/state logic unchanged',hooks:{SdLeft:{type:'Image',texture:base+'showdown_left.svg',rect:[0,0,640,720]},SdRight:{texture:base+'showdown_grid.svg',rect:[640,0,640,720]},SdDivider:{texture:base+'showdown_divider.svg',rect:[596,0,88,720]},SdBladeFrame:'Keep live hud_katana_sheathed.webp / katana_compose source bindings; the pointer icon is not the ammunition HUD.',PanicFrame:'Keep IDs/Panes; call this emitter after legacy polygon writes and before GPU bake',optionalPanicIntro:{textures:[0,1,2].map(i=>base+`panic_intro_${i}.svg`),note:'Source entrance name plates only; existing own name Text goes above. Do not always show the intro art.'}}};
}
