"""Curate source-backed delivery files; generated-count is never a gameplay completion claim."""
from pathlib import Path
import json,hashlib,re,math
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'art/v4_production/completion';D=R/'art/reconstruction_v4';I=R/'art/inspection_v4/delivery';Q=R/'Game/Saved/v4-completion-final'
for p in [D/'candidates',D/'pages',I,Q]:p.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
def store(p,x):(R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def deliver(im,p):
 im.save(p);im.save(p.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
 return {'file':p.relative_to(R).as_posix(),'webp':p.with_suffix('.webp').relative_to(R).as_posix(),'size':list(im.size)}
def contain(im,size,bg='#f3ead9'):
 im=im.convert('RGBA');im.thumbnail(size,Image.Resampling.LANCZOS);out=Image.new('RGBA',size,bg);out.alpha_composite(im,((size[0]-im.width)//2,(size[1]-im.height)//2));return out
contracts=read('art/v4_production/completion/comic_contracts.json')['slots'];latest={}
for p in (R/'art/completion_v4/comic_candidates').glob('*.json'):
 m=re.fullmatch(r'comic_c(\d)_slot(\d+)_candidates_r(\d+)',p.stem)
 if not m:continue
 k=tuple(map(int,m.group(1,2)));rev=int(m[3]);j=read(p.relative_to(R))
 if k not in latest or rev>latest[k][0]:latest[k]=(rev,j)
required={(1,1):2,(1,2):2,(1,6):2,(2,3):2,(2,4):4,(2,6):4,(3,1):2,(3,3):3,(3,4):4,(3,5):4,(3,6):3}
for key,rev in required.items():assert latest[key][0]>=rev,('pending required correction',key,rev)
native={}
for folder in ['ui/v4/reconstruction_diagrams_hd','ui/v4/comic_diagrams_hd']:
 m=read(folder+'/manifest.json')
 for a in m['assets']:
  key=a.get('key',a.get('option',{}).get('key'));ch=a.get('chapter',m.get('chapter'));slot=a.get('slot',m.get('slot'));native[(ch,slot,key)]=a
cache={};cards=[];sequences={};font=ImageFont.truetype(str(R/'fonts/pretendard/Pretendard-Regular.otf'),26)
for slot in contracts:
 ch,n=slot['chapter'],slot['slot'];assert sha(slot['source'])==slot['source_sha256'],slot['source'];sequences.setdefault(ch,[]).append(slot['correct_key'])
 for opt in slot['options']:
  key=opt['key'];ident=f'C{ch}_S{n:02d}_{key}';uv=None
  if (ch,n,key) in native:
   a=native[(ch,n,key)];source=str(Path(a['file']).with_suffix('.png'));crop=None;kind='native_vector_diagram';source_id=a['id'];extra={'semantic_values':a.get('semantic_values',{}),'svg':a['source']}
  elif ch==5 and n==6:
   j=read(f'art/completion_v4/comic_candidate_single/comic_c5_slot06_{key}_single_r3.json');source=j['hd_file'];source_id=j['id'];kind='built_in_single_illustration';crop=None;extra={}
  else:
   j=latest[(ch,n)][1]
   # Curate individual options when a later atlas improves only one panel.
   if ch==2 and n==3 and key in ['B','C']:j=read('art/completion_v4/comic_candidates/comic_c2_slot03_candidates_r1.json')
   if ch==3 and n==6 and key in ['A','C']:j=read('art/completion_v4/comic_candidates/comic_c3_slot06_candidates_r2.json')
   source=j['hd_file'];source_id=j['id'];uv=j['option_uv'][key]
   # The generated C5/S2 handover is top-right, while the intended unused-glass alternative is bottom-left.
   if ch==5 and n==2:uv=j['option_uv'][{'B':'C','C':'B'}.get(key,key)]
   # Exclude two stray baked option letters from the historical-contact montage.
   if ch==6 and n==2 and key=='A':uv=[0,0,.5,.45]
   kind='built_in_illustrated_hypothesis';crop=None;extra={'source_uv':uv}
  if source not in cache:cache[source]=sha(source)
  with Image.open(R/source) as raw:
   if uv:
    w,h=raw.size;crop=tuple(round(v*(w if i%2==0 else h)) for i,v in enumerate(uv));im=raw.crop(crop)
   else:im=raw.copy()
   out=contain(im,(3840,2160))
  rec=deliver(out,D/'candidates'/(ident+'.png'));rec.update(id=ident,chapter=ch,slot=n,key=key,correct=opt['correct'],caption=opt['description'],caption_required=True,caption_source_line=opt['source_line'],manuscript=slot['source'],manuscript_sha256=slot['source_sha256'],source=source,source_sha256=cache[source],source_id=source_id,source_crop_pixels=list(crop) if crop else None,art_type=kind,logical_size=[960,540],presentation='uniform contain/padding; no stretching or semantic repaint; chronology/counts/invisible mental states require source caption',depiction='reconstruction hypothesis illustration, NOT newly discovered photograph/testimony',runtime_integrated=False,**extra);cards.append(rec)
assert len(cards)==114 and len({x['id'] for x in cards})==114
expected={1:'BACBAC',2:'CBACBA',3:'ACBACB',4:'CABCAB',5:'BCABCA',6:'CABCABCA'}
for ch,v in sequences.items():assert ''.join(v)==expected[ch],(ch,v)
pages=[]
for ch in range(1,7):
 correct=sorted([x for x in cards if x['chapter']==ch and x['correct']],key=lambda a:a['slot']);cols=3 if ch<6 else 4;page=Image.new('RGBA',(1920*cols,2160),'#f3ead9')
 for i,a in enumerate(correct):
  with Image.open(R/a['file']) as im:tile=im.convert('RGBA').resize((1920,1080),Image.Resampling.LANCZOS);page.alpha_composite(tile,(i%cols*1920,i//cols*1080))
 rec=deliver(page,D/'pages'/f'chapter_{ch:02d}.png');rec.update(chapter=ch,panels=[a['id'] for a in correct],rows=2,columns=cols,logical_cell_size=[480,270],native_cell_size=[1920,1080],role='actual correct reconstruction panels, horizontal scroll page; NOT fullscreen16:9CG',runtime_integrated=False);pages.append(rec)
inspection=[];meta=[]
for p in (R/'art/completion_v4/inspection_detail').glob('*.json'):
 j=read(p.relative_to(R));base=re.sub(r'_r\d+$','',j['id']);rev=int(j['id'].rsplit('_r',1)[1]);meta.append((base,rev,j))
chosen={}
for base,rev,j in meta:
 if base not in chosen or rev>chosen[base][0]:chosen[base]=(rev,j)
assert len(chosen)==8
for _,j in chosen.values():
 for opt in j['options']:
  ident=opt['logical_id'];uv=j['option_uv'][opt['key']];source=j['hd_file'];crop=None;art_type='built_in_object_inspection'
  if ident=='report_torn_edge':source='ui/v4/documents_hd/report17_matching_fragment.webp';uv=None;art_type='native_exact_mathematical_paper_glyph_match'
  with Image.open(R/source) as raw:
   if uv:
    w,h=raw.size;crop=tuple(round(v*(w if i%2==0 else h)) for i,v in enumerate(uv));im=raw.crop(crop)
   else:im=raw.copy()
   out=contain(im,(3840,2160),'#655e6b' if ident=='report_torn_edge' else '#f3ead9')
  rec=deliver(out,I/(ident+'.png'));rec.update(id=ident,story_reference=opt['evidence_contract'],manuscript=j['source'],source=source,source_sha256=sha(source),source_crop_pixels=list(crop) if crop else None,art_type=art_type,overlay_text='verified document/viewer fields only; never infer facts from generated pseudo-text',runtime_integrated=False);inspection.append(rec)
assert len(inspection)==32
# Exact wide-screen delivery for the one corrected major incident illustration.
j=read('art/completion_v4/cg_correction/incident_c5_cup_correction_r3.json')
with Image.open(R/j['hd_file']) as raw:
 w,h=raw.size;k=min(w//16,h//9);out=raw.convert('RGBA').resize((16*k,9*k),Image.Resampling.LANCZOS)
p=R/'art/completion_v4/cg_correction/incident_c5_cup_correction_delivery.webp';incident=deliver(out,p);incident.update(id='incident_c5',source=j['source_file'],source_hd=j['hd_file'],source_sha256=j['source_image_sha256'],revision='plain NEW glass tumbler instead of incorrect opaque ceramic; original retained',runtime_integrated=False)
old=read('art/v4_production/full/production_catalog.json');story=[x for x in old['cg'] if x['kind']!='climax_page'];legacy=[x for x in old['cg'] if x['kind']=='climax_page']
for a in story:
 if a['logical_id']=='incident_c5':a.update(source=incident['source'],raw_4x=incident['source_hd'],delivery=incident['file'],webp=incident['webp'],size=incident['size'],completion_revision='see completion incident_c5 override')
repair_manifest=R/'art/v4_production/forensic_repair/selected.json'
if repair_manifest.is_file():
 repairs=read(repair_manifest.relative_to(R))
 for a in story:
  if a['logical_id'] in repairs['overrides']:a.update(repairs['overrides'][a['logical_id']])
 for a in inspection:
  if a['id'] in repairs.get('inspection_overrides',{}):a.update(repairs['inspection_overrides'][a['id']])
effects=[]
for p in sorted((R/'art/completion_v4/fx_flipbook').glob('*.json')):
 j=read(p.relative_to(R))
 if j['id'] in ['fx_concentration_border_r1','fx_panic_noise_r1']:continue
 effects.append({'id':j['id'],'source':j['source_file'],'hd':j['hd_file'],'frames':j['cells'],'fps':j['fps'],'loop':False,'frame_opacity':[0]+[1]*6+[0],'role':'moving torn-edge OVERLAY only; actual scene cover/uncover use native masks' if 'scene_ink_wipe' in j['id'] else 'presentation feedback, never an answer detector','runtime_integrated':False})
native_motion=read('ui/v4/motion_hd/manifest.json');effects+=native_motion['assets'][:4];assert len(effects)==14
gifts=read('art/gifts_v4/delivery/manifest.json');actors=read('art/character_delivery_v4/manifest.json');models=[]
for name in ['minigames_v4','interactions_v4','inspection_props_v4']:models+=read(f'art/space_v4/{name}/manifest.json')['assets']
assert len(models)==35
catalog={'status':'all files in the declared asset catalog produced; final technical/visual report is separate from game integration','scope':'original-project art production, no original game extraction, no NAI/external paid generation','story_cg':story,'archived_summary_pages_not_used_for_new_puzzle':legacy,'backgrounds':old['backgrounds'],'spaces':old['space_models'],'base_props':old['prop_models'],'additional_model_files':models,'world_layout':old['world_layout'],'interior_visual_overrides':old['interior_visual_overrides'],'world_maps':'ui/v4/world_maps/manifest.json','ui_components':['ui/v4/hd/manifest.json','ui/v4/systems_hd/manifest.json','ui/v4/trial_hd/manifest.json','ui/v4/completion_hd/manifest.json','ui/v4/brand_hd/manifest.json'],'ui_layouts':'ui/v4/layouts_hd/manifest.json','documents':'ui/v4/documents_hd/manifest.json','exact_paper_match':'ui/v4/documents_hd/report17_matching_fragment.json','characters':'art/character_delivery_v4/manifest.json','reconstruction_candidates':cards,'reconstruction_pages':pages,'inspection_views':inspection,'gift_icons':'art/gifts_v4/delivery/manifest.json','effects':effects,'ground_markers':native_motion['assets'][4:],'new_original_audio':'audio/v4_original/manifest.json','existing_supplied_audio':'audio/cues.json','counts':{'story_cg':len(story),'background_stills':12,'logical_space_states':47,'base_prop_models':44,'additional_glb_files':35,'native_ui_components':243,'full_screen_ui_layouts':22,'inventory_icons':110,'reconstruction_slots':38,'reconstruction_candidates':114,'reconstruction_correct_panels':38,'reconstruction_pages':6,'inspection_views':32,'cutins':actors['counts']['cutins'],'profile_crops':actors['counts']['profiles'],'actor_anchors':len(actors['actors']),'existing_derived_acting_poses':368,'effect_sequences':14,'ground_markers':3,'new_original_audio_cues':34},'runtime_integration':'NOT RUN','game_source_or_data_modified':False,'build_or_game_run':False,'requirements_not_covered_by_art_files':['engine import/native widget binding','new-story evidence/choice answer binding','scene placement/door/physics/collision/actor reflection','timeline/audio/camera gameplay integration','complete game or final story-duration acceptance']}
store('art/v4_production/completion/final_catalog.json',catalog)
if repair_manifest.is_file():
 catalog['forensic_details']=repairs['details'];catalog['forensic_repair_review']='art/v4_production/forensic_repair/visual_review.json'
 catalog['counts'].update(forensic_detail_views=len(repairs['details']),corrected_incident_cg=len(repairs['overrides']))
 store('art/v4_production/completion/final_catalog.json',catalog)
# Review contact pages use real delivered panels with spoiler-sensitive captions kept in metadata.
for start in range(0,len(cards),18):
 page=Image.new('RGB',(1800,1440),'#655e6b');d=ImageDraw.Draw(page)
 for i,a in enumerate(cards[start:start+18]):
  with Image.open(R/a['file']) as im:tile=im.convert('RGB').resize((585,329),Image.Resampling.LANCZOS)
  x=i%3*600+7;y=i//3*240+8;tile.thumbnail((585,210));page.paste(tile,(x,y));d.text((x,y+214),a['id']+' '+a['art_type'],fill='white')
 page.save(Q/f'candidates_{start//18+1:02d}.jpg',quality=96)
print('FINAL_ASSET_CATALOG_READY',json.dumps(catalog['counts'],ensure_ascii=False),flush=True)
