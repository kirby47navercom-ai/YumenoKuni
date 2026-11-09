import {emitV3TrialDialogue} from './v3-trial-dialogue-source.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';

export async function emitV4DialogueWindow({repo,write}){
 const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/dialogue_window_ui_contract.json'),'utf8'));
 const normal=c.families.ordinary_window.snapshots.fl_nomal_wait;
 const body=normal.find(n=>n.text_header),next=c.families.page_indicator.snapshots.fl_wait[0];
 const names={normal:c.name_content_and_first_glyph.source_name_rects.normal.map(n=>n*2/3),hero:c.name_content_and_first_glyph.source_name_rects.hero.map(n=>n*2/3)};
 const namebase={normal:c.name_content_and_first_glyph.source_namebase_rects.normal.map(n=>n*2/3),hero:c.name_content_and_first_glyph.source_namebase_rects.hero.map(n=>n*2/3)};
 const speakers=new Set(['미오']);
 const scan=v=>{if(Array.isArray(v)){v.forEach(scan);return;}if(!v||typeof v!=='object')return;for(const key of ['speaker','who'])if(typeof v[key]==='string'&&v[key]&&v[key].length<40)speakers.add(v[key]);Object.values(v).forEach(scan);};
 for(const dir of ['data/v4_story/chapters','data/v4_story/freetime','data/flow','data/trials'])for(const file of await fs.readdir(path.join(repo,dir)))if(file.endsWith('.json'))scan(JSON.parse(await fs.readFile(path.join(repo,dir,file),'utf8')));
 const nameAssets={};for(const speaker of speakers)nameAssets[speaker]='Assets/Art/ui/v3/dialogue/name_'+createHash('sha256').update(speaker).digest('hex').slice(0,16)+'.svg';
 const rendered=JSON.parse(execFileSync('python',['-X','utf8',path.join(repo,'tools/render_v4_dialogue_names.py')],{input:JSON.stringify({font:path.join(repo,'fonts/blackhansans/BlackHanSans-Regular.ttf'),names:[...speakers]}),encoding:'utf8',maxBuffer:16*1024*1024}));
 for(const [speaker,svg] of Object.entries(rendered))await write(nameAssets[speaker],svg);
 const trialNameAssets={};
 const trialSnapshot=c.families.trial_moving_dialogue.snapshots.fl_d_c_in_wait,trialFrame=c.families.trial_frame_name.snapshots.fl_wait_d;
 const trialBody=trialSnapshot.find(n=>n.text_header).own_projection_rect_1280;
 const nextBar=c.trial_next_indicator.manual_wait_summary.bar_own_rect,nextHand=c.trial_next_indicator.manual_wait_summary.hand_own_rect;
 const nextX=Math.min(nextBar[0],nextHand[0]),nextY=Math.min(nextBar[1],nextHand[1]),nextW=Math.max(nextBar[0]+nextBar[2],nextHand[0]+nextHand[2])-nextX,nextH=Math.max(nextBar[1]+nextBar[3],nextHand[1]+nextHand[3])-nextY;
 const trial={body:trialBody,font:c.trial_dialogue_binding.line_capacity_and_art_limits.nominal_own_font,rows:2,name:trialFrame.find(n=>n.path==='p_t_kaiwa_chara_name_000_jp/depth1').own_projection_rect_1280,icon:trialFrame.find(n=>n.path==='p_t_kaiwa_chara_ico_000/depth1').own_projection_rect_1280,nameAssets:trialNameAssets,next:[nextX,nextY,nextW,nextH],nextBar,nextHand,ownWIN:[0,1,1,1],scope:'Own explicit Normal/Down/Center/in mapping for authored lines without WIN. Native controller/resources proven; not original implicit default. Own approved portrait/full-name ink inside actual name/icon carriers. Trial next retains both SFL quads; external4ab210(80,10) transform meaning unresolved, no invented addition. Source glow/mask/texture ink and name glyph padding unavailable.'};
 const characters=JSON.parse(await fs.readFile(path.join(repo,'data/characters.json'),'utf8'));if(!characters.some(x=>x.id==='0001'&&x.heading.includes('주인공')))throw Error('Own protagonist mapping changed');
 // Resolve QA targets during generation, never scan every runtime shard in one native call.
 const authored=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/chapters/1.json'),'utf8')).nodes;
 const fixtures=Array.from({length:5},(_,kind)=>{
  let selected='',longest=-1;for(const [id,n]of Object.entries(authored)){
   if(n.type!=='say'||String(n.source?.file||'').startsWith('11c')!==(kind===4))continue;
   const match=kind===1||kind===4?n.actor==='mio'&&!n.mono:kind===2?n.mono:kind===3?true:!n.mono&&n.actor&&n.actor!=='mio';
   const bytes=Buffer.byteLength(n.text||'');if(match&&bytes>longest){selected=id;longest=bytes;}
  }if(!selected)throw Error('Missing actual authored dialogue fixture '+kind);return selected;
 });
 const layout={body:body.own_projection_rect_1280,font:c.text_and_color.normal_window_font_axis_height_own_1280,names,namebase,next:next.own_projection_rect_1280,nameAssets,trial,ownPlayer:{actor:'mio',displayName:'미오',sourceCharacterId:'0001'},ownWrap:{width:body.own_projection_rect_1280[2]-8,rows:3},scope:'Static ADV normal/hero and separate trial controller geometry. Own outlined full-name images, measured3/2-line pagination, neutral black missing-raster material and yellow ADV day ornament impression observed on official public system img_08. No first-glyph layer. No original frame/raster/full timing/palette equality.'};
 layout.fixtures=fixtures;
 const ownHeights={};for(const character of characters){const h=Object.values(character.fields||{}).join(' ').match(/(\d+)cm/),words=character.heading.split(/\s+/);if(h)for(const word of words)ownHeights[word]=Number(h[1]);}
 layout.portrait={centerX:640,top:0,referenceSpeaker:'하루카',referenceHeightCm:160,referenceImageHeight:1050,heightCmByName:ownHeights,scope:'User20261030 framing correction: Haruka skirt middle overlaps the ADV dialogue region; preserve own human stature ratios. Explicit project camera/UI calibration, not a recovered V3 pixel value.'};
 const sourceFolder=path.join(repo,'ui/v4/adv_source'),sourceLayout=JSON.parse(await fs.readFile(path.join(sourceFolder,'layout.json'),'utf8'));
 const prefix='Assets/Art/ui/v3/dialogue/source_adv/';
 const sourceSvg=async(name,rect)=>{const bytes=await fs.readFile(path.join(sourceFolder,name+'.png'));return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${rect[2]} ${rect[3]}" preserveAspectRatio="none"><image href="data:image/png;base64,${bytes.toString('base64')}" width="${rect[2]}" height="${rect[3]}" preserveAspectRatio="none"/></svg>`;};
 layout.advSource={palettes:{},sourceDescription:'Original ADV bitmap/RGBA/affine; dynamic own names/portraits/text retained. Settled phase images, not all original runtime animation.'};
 for(const phase of ['day','night','close']){
  const branchAssets={};
  for(const branch of ['normal','hero','nameless']){const file=prefix+`adv_${phase}_${branch}.svg`;await write(file,await sourceSvg(`adv_${phase}_${branch}`,[0,0,1280,720]));branchAssets[branch]=file;if(phase==='day')await write('Assets/Art/ui/v3/dialogue/adv_'+branch+'.svg',await sourceSvg(`adv_${phase}_${branch}`,[0,0,1280,720]));}
  const next=sourceLayout.tiles['next_'+phase],auto=sourceLayout.tiles['auto_'+phase];
  const nextAsset=prefix+'next_'+phase+'.svg',autoAsset=prefix+'auto_'+phase+'.svg';
  await write(nextAsset,await sourceSvg('next_'+phase,next.rect));await write(autoAsset,await sourceSvg('auto_'+phase,auto.rect));
  layout.advSource.palettes[phase]={branches:branchAssets,next:next.rect,nextAsset,autoRect:auto.rect,autoAsset};
 }
 layout.advSource.eventAsset=prefix+'event.svg';await write(layout.advSource.eventAsset,await sourceSvg('event',[0,0,1280,720]));
 // Name bands already belong to the exact full-frame composition. Keep the
 // legacy node/id transparent to avoid drawing a second plain rectangle over it.
 await write('Assets/Art/ui/v3/dialogue/namebase.svg','<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 60"></svg>');
 layout.next=sourceLayout.tiles.next_day.rect;await write('Assets/Art/ui/v3/dialogue/next.svg',await sourceSvg('next_day',layout.next));
 layout.scope='Original ADV ordinary/hero/nameless bitmap alpha/RGB and SFL geometry, with day/night/closed variants and exact manual/AUTO ink available. Own high-resolution portraits, full names and text pagination retained. Settled-state composition only; original GPU/additive effects and in/out animation are not claimed.';
 await emitV3TrialDialogue({repo,write,layout,speakers});

 return layout;
}
