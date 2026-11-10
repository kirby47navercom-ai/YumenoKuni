"""Source-bound incident replacements and literal HD crops; no painted synthetic clues."""
from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'art/v4_production/forensic_repair';D=R/'art/forensic_v4/details';Q=R/'Game/Saved/v4-forensic-repair'
for p in [D,Q]:p.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads((R/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
def put(p,j):(R/p).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
review=read('art/v4_production/forensic_repair/selection_review.json');catalog=read('art/v4_production/completion/final_catalog.json');overrides={};details=[];rows=[]
for logical,a in review['assets'].items():
 ident=a['id'];j=read(f'art/cg_v4/builtin/{ident}.json');assert (R/Path(j['hd_file']).with_suffix('.json')).is_file();assert sha(j['source'])==j['manuscript_sha256']
 rec={'selected_id':ident,'metadata':f'art/cg_v4/builtin/{ident}.json','source':j['source_file'],'raw_4x':j['hd_file'],'delivery':j['delivery_file'],'webp':str(Path(j['delivery_file']).with_suffix('.webp')),'size':j['delivery_size'],'manuscript':j['source'],'manuscript_sha256':j['manuscript_sha256'],'source_review':'art/v4_production/forensic_repair/visual_review.json','completion_revision':'injury/trace/posture/object review replaces previous incident selection','runtime_integrated':False}
 overrides[logical]=rec
 for old in catalog['story_cg']:
  if old['logical_id']==logical:old.update(rec)
 with Image.open(R/j['delivery_file']) as raw:
  raw=raw.convert('RGBA');w,h=raw.size
  for region,uv,caption in a['regions']:
   box=tuple(round(v*(w if i%2==0 else h))for i,v in enumerate(uv));tile=raw.crop(box);ident2=logical+'_'+region;path=D/(ident2+'.png');tile.save(path);tile.save(path.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
   details.append({'id':ident2,'file':path.relative_to(R).as_posix(),'webp':path.with_suffix('.webp').relative_to(R).as_posix(),'size':list(tile.size),'source':j['delivery_file'],'source_sha256':sha(j['delivery_file']),'source_uv':uv,'source_crop_pixels':list(box),'caption':caption,'caption_required':True,'method':'literal pixel crop of selected exact16:9 local4x delivery; no repaint/mirror/new invented detail/no second upscale','runtime_integrated':False})
  small=raw.convert('RGB');small.thumbnail((1200,675));small.save(Q/(logical+'_overview.jpg'),quality=96)
 rows.append({'logical_id':logical,'selected_id':j['id'],'checks':a['checks'],'source':j['source'],'source_sha256':j['manuscript_sha256'],'limits':a['limits'],'regions':[x['id']for x in details if x['id'].startswith(logical+'_')]})
# Object-only evidence absent or misleading in earlier generic detail art.
j=read('art/cg_v4/builtin/'+review['object_atlas']+'.json');assert (R/Path(j['hd_file']).with_suffix('.json')).is_file()
with Image.open(R/j['delivery_file']) as raw:
 w,h=raw.size
 for key,uv,caption in [('original_floor_cover',[.025,.067,.495,.94],'발견 장소와 다른 직원 통로. 방수 덮개 위의 닦인 흔적과 틈 아래로 스며든 흔적을 구분한다. 사진만으로 혈액 주인/정확 시각을 판정하지 않는다.'),('detached_base',[.505,.067,.978,.94],'선반 아래의 분리된 마이크 받침. 봉이 없고, 천이 일부 덮고 있으며 찌그러진 가장자리의 흔적/바닥의 검은 마감 조각을 구분한다. 함 안의 일반 추와 다른 물건이다.')]:
  box=tuple(round(v*(w if i%2==0 else h))for i,v in enumerate(uv));tile=raw.crop(box).convert('RGBA');p=D/('evidence_c2_'+key+'.png');tile.save(p);tile.save(p.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
  details.append({'id':'evidence_c2_'+key,'file':p.relative_to(R).as_posix(),'webp':p.with_suffix('.webp').relative_to(R).as_posix(),'size':list(tile.size),'source':j['delivery_file'],'source_sha256':sha(j['delivery_file']),'source_uv':uv,'source_crop_pixels':list(box),'caption':caption,'caption_required':True,'method':'literal crop from authored body-free object atlas; no quantitative weapon/injury match inferred','runtime_integrated':False})
base=details[-1]
with Image.open(R/base['file'])as raw:
 raw=raw.convert('RGBA');raw.thumbnail((3840,2160),Image.Resampling.LANCZOS);mat=Image.new('RGBA',(3840,2160),'#655e6b');mat.alpha_composite(raw,((3840-raw.width)//2,(2160-raw.height)//2));p=R/'art/inspection_v4/delivery/microphone_base_forensic_r2.webp';mat.save(p);mat.save(p.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
inspection_override={'file':p.relative_to(R).as_posix(),'webp':p.with_suffix('.webp').relative_to(R).as_posix(),'size':[3840,2160],'source':base['source'],'source_sha256':base['source_sha256'],'source_crop_pixels':base['source_crop_pixels'],'art_type':'original evidence object: rod detached/dent/residue/chip/halfcloth; uniform contain on dark mat','story_reference':base['caption']}
for a in catalog['inspection_views']:
 if a['id']=='microphone_base':a.update(inspection_override)
selected={'overrides':overrides,'inspection_overrides':{'microphone_base':inspection_override},'details':details,'runtime_integrated':False};put('art/v4_production/forensic_repair/selected.json',selected)
catalog.update(forensic_details=details,forensic_repair_review='art/v4_production/forensic_repair/visual_review.json');catalog['counts'].update(forensic_detail_views=len(details),corrected_incident_cg=6);put('art/v4_production/completion/final_catalog.json',catalog)
put('art/v4_production/forensic_repair/visual_review.json',{'scope':'six incident CG selected originals individually inspected;14 literal incident crops+2object views; see actual HD contact/native sample review status recorded after inspection','scenes':rows,'object_review':'two-view floor/base source inspected; first version rejected for invented wall hole; second has shallow scuff and separate floor chip, rod absent','retained_rejected':['incident_c1_forensic_r1:missing report strip wrongly in room','incident_c3b_forensic_r1:sleep look/old camera','incident_c3b_forensic_r2:invented white collar flap','incident_c4_forensic_r1:duplicate ambiguous mark on second hand','evidence_c2_original_site_forensic_r1:invented wall hole'],'detail_view_count':len(details),'blood_policy':'purple only; latest user explicitly requested readable bleeding and settled floor pools for existing bleeding neck injury scenes; pressure bruise is not external bleeding; old elbow mark is not poisoning evidence','uncertainty':'anatomical side/precise depth/angle/dimensions/individual stain physics are not newly established facts; source-silent illustration detail cannot be a sole-answer clue','runtime_integrated':False})
# Contact sheets contain actual new outputs; do not display story-sensitive sheets in chat.
for start in range(0,len(details),6):
 sheet=Image.new('RGB',(1800,1000),'#655e6b');draw=ImageDraw.Draw(sheet)
 for i,a in enumerate(details[start:start+6]):
  with Image.open(R/a['file'])as tile:tile=tile.convert('RGB');tile.thumbnail((580,450));x=i%3*600+8;y=i//3*500+8;sheet.paste(tile,(x,y))
  draw.text((x,y+465),a['id'],fill='white')
 sheet.save(Q/f'details_{start//6+1:02}.jpg',quality=96)
points={'incident_c1':(.685,.373),'incident_c2':(.435,.265),'incident_c3a':(.55,.32),'incident_c3b':(.24,.32),'incident_c4':(.21,.49),'incident_c5':(.435,.616)}
sheet=Image.new('RGB',(1050,680),'#655e6b');draw=ImageDraw.Draw(sheet)
for i,(logical,(u,v))in enumerate(points.items()):
 with Image.open(R/overrides[logical]['raw_4x'])as raw:
  x=round(raw.width*u);y=round(raw.height*v);tile=raw.crop((x-150,y-150,x+150,y+150)).convert('RGB');sheet.paste(tile,(i%3*350+10,i//3*340+10))
 draw.text((i%3*350+10,i//3*340+315),logical+' HD 1:1 sample',fill='white')
sheet.save(Q/'injury_native_samples.jpg',quality=98)
print('FORENSIC_SELECTED',len(overrides),'incident replacements;',len(details),'literal/object detail views;1inspection override',flush=True)
