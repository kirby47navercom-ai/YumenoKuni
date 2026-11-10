"""Source-grounded missing art: final manuscript comic candidates and presentation FX."""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1];O=R/'art/v4_production/completion';J=O/'jobs';J.mkdir(parents=True,exist_ok=True)
refs={'미오':'art/standing_v4/mio_color_v2.webp','린':'art/standing_v4/rin.webp','나나':'art/standing_v4/nana_fullbody.webp','소라':'art/standing_v4/sora.webp','켄':'art/standing_v4/ken.webp','타이가':'art/masters_clean_v4/taiga.webp','카에데':'art/standing_v4/kaede.webp','아카리':'art/standing_v4/akari.webp','코토':'art/standing_v4/koto.webp','아이':'art/standing_v4/ai.webp','유우':'art/masters_clean_v4/yuu.webp','리쿠':'art/standing_v4/riku.webp','레이':'art/standing_v4/rei.webp','하루카':'art/masters_clean_v4/haruka_r2.webp','사츠키':'art/standing_v4/satsuki.webp','쇼':'art/standing_v4/sho.webp','래피':'art/sprites_nai_v4/lappy/lappy_L01.webp'}
style=('One ORIGINAL mystery visual novel illustration atlas,16:9 fullbleed. Angular fine variable-width INK outlines, detailed thin hair strands, hard clean CEL shadows, subdued ivory/violet/walnut palette, original reference-character continuity. Never imitate an existing franchise character or logo. NO text, lettering, numbers, UI, labels, watermark, gore, exposed wounds, dismemberment, red blood, sexualization or nudity. All figures fully clothed. ')
jobs=[];slots=[]
for ch,num in enumerate(range(157,163),1):
 p=next((R/'docs/design/rewrite_v4').glob(str(num)+'_*.md'));text=p.read_text(encoding='utf8');groups={}
 for ln,line in enumerate(text.splitlines(),1):
  m=re.match(r'\|([1-8])([ABC])\|([^|]+)\|([^|]+)\|',line)
  if m:groups.setdefault(int(m[1]),[]).append({'key':m[2],'description':m[3],'correct':m[4]=='정답','source_line':ln})
 assert len(groups)==(8 if ch==6 else 6)
 for slot,rows in groups.items():
  assert len(rows)==3 and sum(a['correct'] for a in rows)==1
  content=' '.join(a['description'] for a in rows);cast=[name for name in refs if name in content]
  selected=cast or ['미오'];mapping=' '.join(f'Attachment{i+1} is {name}: EXACT present-body physical identity/hair/eye/costume reference.' for i,name in enumerate(selected))
  ident=f'comic_c{ch}_slot{slot:02d}_candidates_r1'
  prompt=style+('ONE 2x2 ATLAS of THREE ALTERNATIVE versions of the SAME reconstruction slot. TOP-LEFT is A, TOP-RIGHT is B, BOTTOM-LEFT is C. Bottom-right is COMPLETELY BLANK ivory paper, no fourth illustration. Exact straight equal quadrants, thin dark gutters. Every drawn quadrant is an independent16:9 narrative panel, never spill a figure into adjacent panel. This is an illustrated reasoning puzzle, not discovered photographic evidence. A wrong option intentionally contradicts the true story; DRAW THAT WRONG ALTERNATIVE as requested, never silently fix it or mark it wrong. No baked correctness symbol or caption. ')+mapping
  if not cast:prompt+=' References supply drawing style ONLY; no humans in object/document-only panels.'
  prompt+=' Visualize these exact Korean source descriptions, do not invent a clue: '+ ' '.join(f'{a["key"]}: {a["description"]}.' for a in rows)
  prompt+=(' Safety/art staging: OMIT violent bodily contact, penetration, choking method and any injured body detail. Represent violent action by non-graphic off-panel transition, separated figures, object/evidence aftermath or shadow composition; never replace the intended chronology or actor identity. No chemical ingredient, poison preparation, dosing or recipe: personal cup / sealed fictional sample only. Purple stains only where story already calls for them. ')
  prompt+=('Physical continuity: Rin LAVENDER bob/cat mask; Nana dusty-pink short hair, long skirt, LEFT wrist ribbon; Sora BLOND/orange jacket; Ken BURGUNDY hair/green uniform/cape. Haruka pink bob/brown eyes. Akari RIGHT watch; Koto longblonde hair. No floating documents or actual magic unless explicitly part of a WRONG candidate. ')
  if ch==1:prompt+='Taiga wrist brace RIGHT. This is SERVICE LOUNGE with small printer and ordinary furniture, NEVER blue stage chest, props or added equipment.'
  if ch==2:prompt+='Blue equipment chest has wheels, TWO external latches, two lid stays, no inside lock. No extra chest replacing the same chest except explicit wrong candidate.'
  if ch==3:prompt+='Ken physical body NEVER acquires blond hair, new eye color, ghost or a second face even if another consciousness controls him. Waiting room has TWO opposite side-wall benches, central aisle; original blond body lies on left bench with head deep/feet toward doorway.'
  if ch==4:prompt+='Second door is blind storage inside actual hall, not exterior exit EXCEPT an explicit wrong-option drawing of the false route. The original water hatch has attached metal hinge and external latch.'
  if ch==5:prompt+='Koto old elbow bandage remains; personal cup is separate from the six newly washed cups; no chemical use shown.'
  if ch==6:prompt+=('Past scenes five years earlier: use clothed navy-uniform SILHOUETTES and cropped hands, indicative hair shapes, never detailed invented younger faces/costumes. Current mascot hands do not become human hands in past. Staff approval scenes use documents/anonymous adult hand silhouettes, no invented named adult portrait. A source description with multiple moments uses subtle inset within THAT quadrant only, never moves into another option. ')
  environment={1:'art/bg_v4/plates_r4/service_lounge_day.webp',2:'Game/Saved/v4-world-full-v2/theatre_preparation_center.png',3:'Game/Saved/v4-world-full-v2/'+('mirror_workbay_center.png' if slot==3 else 'mirror_waiting_center.png'),4:'Game/Saved/v4-world-full-v2/inspection_hall_changed_center.png',5:'art/bg_v4/plates_r4/service_lounge_day.webp'}.get(ch)
  attachments=[refs[x] for x in selected]
  if environment and (R/environment).exists():
   attachments.append(environment);prompt+=f' Attachment{len(attachments)} is AUTHORED environment reference ONLY, use its simple actual geometry and props in relevant panels, redraw in ink/cel style. Do not add lavish new architecture or an unmentioned chest.'
  j={'id':ident,'kind':'comic_candidates','chapter':ch,'slot':slot,'source':p.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'references':attachments,'characters':cast,'options':rows,'correct_key':next(a['key'] for a in rows if a['correct']),'option_uv':{'A':[0,0,.5,.5],'B':[.5,0,1,.5],'C':[0,.5,.5,1]},'prompt':prompt,'transparent_background':False,'runtime_integrated':False}
  jobs.append(j);slots.append({k:j[k] for k in ['id','chapter','slot','source','source_sha256','options','correct_key','option_uv']})
fx={
'statement_fracture':'A taut ivory ink stroke breaks into angular ivory/purple splinters: intact anticipation, sharp central break,6 shards drift outward and fade. No letters or readable words.',
'argument_impact':'A sharp asymmetrical burst of ivory ink with violet core and black cutout spikes; small anticipation, single peak then fragments shrink away. Clean readable hit, not an explosion or fire.',
'slash_trail':'A single sweeping diagonal violet/ivory ink slash from lower-left to upper-right, broad middle thin ends, with two tiny trailing marks; grows then cleanly vanishes. No blade or weapon shown.',
'miss_deflection':'One thin paper-like ivory trajectory bends aside and loses energy, grey/violet fragments fall away; deflection feedback, no aggressive full-screen burst.',
'evidence_reveal':'An ivory paper-edge curl and short violet accent flare opens around a clear center rectangle, then relaxes into a thin frame and fades; no paper text or icon.',
'discovery_border':'Dense black/violet angular ink grows ONLY inward from4outer corners, peak opacity on border, then recedes; keep middle70% transparent; abstract ink NOT blood splatter.',
'panic_noise':'Sparse broken violet/ivory diagonal scratches at edges, briefly stagger and scatter, keep middle65% transparent. No static-TV full-frame noise, flashing white field or repeated strobe.',
'scrum_link_sparks':'Two opposing thin ivory/violet strokes approach, meet once in a small angular diamond spark, connect briefly, then both fade; no text or colored team flags.',
'concentration_border':'Fine quiet dark-violet stippled ink vignette at four corners, extremely subtle slow tightening and release; middle75% clear, no zoom tunnel or flashing.',
'rewind_scan':'Two thin violet horizontal ink bands, sparse offset paper specks sweep once across a clear field from right toward left; restrained visual transition only, not a clock with false duration.',
'scene_ink_wipe':'Irregular black/ivory torn-paper edge progresses left to right, revealing neutral transparent field; smooth one-way advance, no text. Suitable for alpha transition mask, not black screen with decorative object.',
'camera_whip_streak':'Six narrow directional ivory/violet INK speed streaks enter from left edge, stretch horizontally, depart to right edge, clear readable middle. No camera/character/landscape.'}
for ident,scene in fx.items():
 j={'id':'fx_'+ident+'_r1','kind':'fx_flipbook','source':'docs/analysis/v3_rebuild/전면_재제작_분석.md','source_sha256':hashlib.sha256((R/'docs/analysis/v3_rebuild/전면_재제작_분석.md').read_bytes()).hexdigest(),'references':[],'prompt':style+'TRANSPARENT background. ONE animation SPRITESHEET atlas with EXACTLY4COLUMNS x2ROWS,8equal rectangular frames in row-major order. All art contained in each cell, no borders, text or grid lines. Frame1 EMPTY TRANSPARENT. Frames2..7 are SIX successive stages of ONE same effect, consistent scale/anchor/style, chronological motion. Frame8 EMPTY TRANSPARENT. Frame centers align, at least10%clear cell padding, nothing spills across cells. '+scene+' True RGBA transparency, no checkerboard baked in, no solid dark backdrop. Effect colors ivory #f3ead9, muted violet #9770cf, charcoal #14131b only.','transparent_background':True,'frame_grid':[4,2],'frames':8,'fps':16,'loop':False,'blend':'straight-alpha','anchor':[.5,.5],'reduced_motion':'show one restrained frame at max25%opacity for100ms, no camera impulse','runtime_integrated':False}
 jobs.append(j)
for j in jobs:(J/(j['id']+'.json')).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'generation_jobs.json').write_text(json.dumps({'tool':'built-in image_gen ONLY; NAI forbidden','jobs':jobs},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'comic_contracts.json').write_text(json.dumps({'source':'actual final manuscript157..162, not old summary pages','slots':slots,'slot_count':len(slots),'candidate_count':sum(len(x['options']) for x in slots),'runtime_integrated':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared',len(slots),'comic slot atlases/114 candidates +',len(fx),'animated FX atlases')
