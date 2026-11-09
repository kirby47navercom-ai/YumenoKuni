import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {emitLevelUp} from './v4-level-up-ui.mjs';

// Only the existing, supplied UI bank is read. No original archive is opened.
export async function emitV4ExplorationHud({repo,write}){
 const contract=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/exploration_hud_ui_contract.json'),'utf8'));
 const leaves=contract.geometry.chapter_level.states.find(s=>s.root_label==='fl_wait').leaves;
 const bindings=contract.provided_raster.chapter_level_bindings.bindings;
 const images=new Map();
 for(const binding of bindings){
  const bytes=await fs.readFile(binding.provided_PNG_path);
  if(createHash('sha256').update(bytes).digest('hex')!==binding.provided_PNG_file_sha256)throw Error('Changed supplied HUD texture '+binding.source_image_id);
  images.set(binding.source_image_id,'data:image/png;base64,'+bytes.toString('base64'));
 }
 const svg=body=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" preserveAspectRatio="none">${body}</svg>`;
 const image=(leaf,id=leaf.image_id,dx=0)=>{
  const [left,right,top,bottom]=leaf.local_lrtb,m=[...leaf.affine_design];m[4]+=dx;
  return `<image href="${images.get(id)}" x="${left}" y="${top}" width="${right-left}" height="${bottom-top}" preserveAspectRatio="none" opacity="${leaf.alpha_product}" transform="matrix(${m.join(' ')})"/>`;
 };
 const get=p=>leaves.find(l=>l.path===p),mask=get('p_level_base/i_guage_mask/d1'),gauge=get('p_level_base/p_guage/d1');
 const variants={};
 for(const phase of ['day','night','close'])for(const chapter of [0,1,2,3,4,5,6,7,9,10]){
  const phaseId={day:0,night:1,close:2}[phase];
  const replacements=new Map([[27,[27,28,26][phaseId]],[40,[40,44,36][phaseId]],[39,[39,43,35][phaseId]],[41,[41,45,37][phaseId]],[38,[38,42,34][phaseId]],[15,[15,17,14][phaseId]]]);
  const numbered=chapter>=1&&chapter<=6,number=[null,19,20,21,23,22,24][chapter]; // Source4/5 ordinals are reversed.
  const title=chapter===0?32:chapter===7?30:chapter===9?33:chapter===10?31:29;
  const body=leaves.filter(l=>l.kind==='raster_quad'&&l.alpha_product>0&&!l.path.includes('guage')&&(numbered||!l.path.startsWith('p_ep_no')&&!['p_ef_s/d1','p_ef_l/d1'].includes(l.path))).map(l=>image(l,l.image_id===29?title:l.image_id===19?number:(replacements.get(l.image_id)??l.image_id))).join('');
  const asset=`Assets/Art/ui/v3/exploration/chapter_${phase}_${chapter}.svg`;variants[phase+chapter]=asset;
  await write(asset,svg(`<g transform="scale(.666666666666667)">${body}</g>`));
 }
 // Fixed silhouette, translated inside the sibling mask. Never stretch a fill by its XP fraction.
 // Source p_guage receives an extra XY offset: authored17+(136*ratio-4), Y14.
 for(let percent=0;percent<=100;percent++){
  const scalar=136*percent/100-4;
  await write(`Assets/Art/ui/v3/exploration/gauge_${percent}.svg`,svg(`<g transform="scale(.666666666666667)"><defs><mask id="gauge" maskUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080">${image(mask)}</mask></defs><g mask="url(#gauge)">${image(gauge,25,scalar)}</g></g>`));
 }
 const layout={variants,level:contract.chapter_level.key_rects_1280.level_text,ownReadableLevelFont:12,levelPrefix:'Level ',gaugeSteps:100,
  sourceLeaves:leaves.map(l=>({path:l.path,rect:l.rect_1280,image:l.image_id,alpha:l.alpha_product})),
  target:contract.target_and_reticle,
  scope:'Exact authored fl_wait affine/local shape sizes and supplied texture identities; p_guage extra XY offset and sibling clip. Own static phase selected by current authored background, chapter0 Prologue/1..6 number mapping, readable12px level ink fit, immediate displayed level,1% gauge sampling. Full source phase overrides/levelup animation timing/movement-art show consumer and original font ink remain separate.'};
 await write('Assets/Data/v4_story/exploration_hud_layout.json',layout);
 await write('Assets/Data/v4_story/player_progress.json',{levels:contract.player_growth.tables.Level.rows,gains:contract.player_growth.tables.Experiance.rows,cap:168500,scope:'Source permanent XP thresholds; project walking stride maps existing world phase radians to half-cycle events. Bonds/own skill SP are separate. No XP inferred from old bonds or existing cards.'});
 await emitLevelUp({repo,write});
 return layout;
}
