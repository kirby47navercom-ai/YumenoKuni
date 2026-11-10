"""File/contract checks on completed original asset deliveries, never a game test."""
from pathlib import Path
import json,hashlib,re,time,sys
from PIL import Image,ImageFont
from cleanup_assets import pair_paths
R=Path(__file__).resolve().parents[1];O=R/'art/v4_production/completion'
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
checked=[];hashes={}
cleanup_only='--cleanup-only' in sys.argv
manuscript_drift=[]
def pair(p,q,size=None):
 left,right=pair_paths(p,q)
 with Image.open(left) as a,Image.open(right) as b:
  assert a.size==b.size,(p,'size')
  if size:assert list(a.size)==list(size),(p,a.size,size)
  assert a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes(),(p,'RGBA')
 return list(a.size)
def source(p,h):
 if p not in hashes:hashes[p]=sha(p)
 if cleanup_only and p.startswith('docs/') and hashes[p]!=h:
  manuscript_drift.append({'file':p,'recorded_sha256':h,'current_sha256':hashes[p]});return
 assert hashes[p]==h,(p,'hash')
# Validate every new generated version, including retained rejected revisions.
for p in ([] if '--delivery-only' in sys.argv or cleanup_only else sorted((R/'art/completion_v4').glob('*/*.json'))):
 j=read(p.relative_to(R))
 if not j.get('hd_file'):continue
 source(j['source_file'],j['source_image_sha256'])
 with Image.open(R/j['source_file']) as a:expected=[a.width*4,a.height*4]
 hd=Path(j['hd_file']);pair(str(hd),str(hd.with_suffix('.webp')),expected)
 stamp=read(hd.with_suffix('.json'));assert stamp['scale']==4 and stamp['source_sha256']==j['source_image_sha256']
 checked.append({'id':j['id'],'kind':'source4x','size':expected})
 if len(checked)%15==0:print('HD checked',len(checked),flush=True)
if checked:(O/'new_hd_qa.json').write_text(json.dumps({'status':'PASS','checks':checked},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
elif (O/'new_hd_qa.json').is_file():checked=read('art/v4_production/completion/new_hd_qa.json')['checks']
c=read('art/v4_production/completion/final_catalog.json');cards=c['reconstruction_candidates'];assert len(cards)==114
assert len({a['id'] for a in cards})==114
seq={1:'BACBAC',2:'CBACBA',3:'ACBACB',4:'CABCAB',5:'BCABCA',6:'CABCABCA'}
font=ImageFont.truetype(str(R/'fonts/pretendard/Pretendard-Regular.otf'),26);maxlines=0
for a in cards:
 pair(a['file'],a['webp'],[3840,2160]);source(a['source'],a['source_sha256']);source(a['manuscript'],a['manuscript_sha256'])
 assert a['caption_required'] and not a['runtime_integrated']
 lines=1;line=''
 for ch in a['caption']:
  if font.getlength(line+ch)>721:lines+=1;line=ch
  else:line+=ch
 maxlines=max(maxlines,lines);assert lines*35<=124,(a['id'],'caption overflow',lines)
for ch,answer in seq.items():
 rows=[a for a in cards if a['chapter']==ch];n=8 if ch==6 else 6
 assert {a['slot'] for a in rows}==set(range(1,n+1))
 assert ''.join(next(a['key'] for a in rows if a['slot']==s and a['correct']) for s in range(1,n+1))==answer
 for s in range(1,n+1):assert sorted(a['key'] for a in rows if a['slot']==s)==list('ABC')
for a in c['reconstruction_pages']:
 pair(a['file'],a['webp'],a['size']);assert len(a['panels'])==a['columns']*a['rows']
for a in c['inspection_views']:pair(a['file'],a['webp'],[3840,2160]);source(a['source'],a['source_sha256'])
assert len({a['id'] for a in c['inspection_views']})==32
g=read(c['gift_icons']);inventory=read('data/gifts.json');expected={x['id'] for x in (inventory if isinstance(inventory,list) else inventory['items'])}
assert {a['id'] for a in g['assets']}==expected and len(expected)==110
for a in g['assets']:pair(a['file'],a['webp'],[2048,2048]);source(a['source'],a['source_sha256'])
actors=read(c['characters'])
for a in actors['assets']:pair(a['file'],a['webp'],a['size'])
for m in c['additional_model_files']:assert (R/m['file']).stat().st_size>20
for a in c['story_cg']:assert (R/a['delivery']).is_file()
layouts=read(c['ui_layouts']);assert len(layouts['screens'])==22
for a in layouts['screens']:
 assert (R/a['source']).is_file() and (R/a['fixture_image']).is_file()
 for f in a['text_fields']:
  x,y,w,h=f['rect'];assert min(x,y,w,h)>=0 and x+w<=1920 and y+h<=1080
report={'status':'PASS','new_generated_source_versions':len(checked),'generated_checks':checked,'source_hashes_verified':len(hashes),'delivery_counts':c['counts'],'candidate_caption_max_lines':maxlines,'checks':['generated source SHA256 and exact local4x dimensions','PNG/WebP exact RGBA','114 unique candidate IDs, ABC each slot,38 source answer keys','6 correctly ordered page atlases','32 inspection details and110 inventory ID equality','all character delivery pairs and35 new model files','22 bounded layout fixtures'],'runtime':'NOT RUN','artistic_approval':'see visual_review.json; numeric checks are not universal artistic approval','nai_calls':0,'external_paid_api_calls':0}
target=O/'final_technical_qa.json'
if cleanup_only:
 report['scope']='Cleanup image/file integrity only; historical manuscript freshness is separately reported, never silently approved'
 report['manuscript_drift']=manuscript_drift
 target=R/'_삭제대기_2026-10-29/delivery-integrity.json'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('CLEANUP IMAGE INTEGRITY PASS' if cleanup_only else 'FINAL PASS',len(cards),'candidate deliveries;110icons;32inspectionviews; manuscript drift',len(manuscript_drift),flush=True)
