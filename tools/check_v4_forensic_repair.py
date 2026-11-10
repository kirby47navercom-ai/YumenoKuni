"""Verify only corrected image lineage, source contracts, HD and exact-pixel clue views."""
from pathlib import Path
import json,hashlib,re,sys
from PIL import Image
import numpy as np
from cleanup_assets import retained,pair_paths
R=Path(__file__).resolve().parents[1];O=R/'art/v4_production/forensic_repair'
def read(p):return json.loads(retained(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(retained(p).read_bytes()).hexdigest()
def equal(p,q,size=None):
 left,right=pair_paths(p,q)
 with Image.open(left)as a,Image.open(right)as b:
  assert a.size==b.size
  if size:assert list(a.size)==list(size)
  assert a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes(),p
reports=[]
cleanup_only='--cleanup-only' in sys.argv
manuscript_drift=[]
for p in sorted((O/'jobs').glob('*.json')):
 path=R/'art/cg_v4/builtin'/(p.stem+'.json')
 if not path.exists():continue
 j=read(path.relative_to(R));assert sha(j['source_file'])==j['source_sha256']
 fresh=sha(j['source'])==j['manuscript_sha256']
 if cleanup_only and not fresh:manuscript_drift.append({'id':j['id'],'file':j['source'],'recorded_sha256':j['manuscript_sha256'],'current_sha256':sha(j['source'])})
 else:assert fresh,(j['id'],'source manuscript changed')
 for ref in j['references']:assert sha(ref)==j['reference_sha256'][ref],(j['id'],'reference hash')
 equal(j['source_file'],str(Path(j['source_file']).with_suffix('.webp')),j['source_size'])
 expected=[x*4 for x in j['source_size']];equal(j['hd_file'],str(Path(j['hd_file']).with_suffix('.webp')),expected)
 stamp=read(Path(j['hd_file']).with_suffix('.json'));assert stamp['source_sha256']==j['source_sha256'] and stamp['scale']==4
 w,h=j['delivery_size'];assert w*9==h*16;equal(j['delivery_file'],str(Path(j['delivery_file']).with_suffix('.webp')),[w,h]);assert sha(j['delivery_file'])==j['delivery_sha256']
 reports.append({'id':j['id'],'source_SHA256':'PASS','manuscript_SHA256':'PASS' if fresh else 'DRIFT','reference_SHA256':'PASS','exact4x_lossless':'PASS','exact16_9_lossless':'PASS'})
 print('Image pair checks',len(reports),flush=True)
selected=read('art/v4_production/forensic_repair/selected.json');c=read('art/v4_production/completion/final_catalog.json');assert len(selected['overrides'])==6
for logical,override in selected['overrides'].items():
 a=next(x for x in c['story_cg']if x['logical_id']==logical);assert a['selected_id']==override['selected_id'] and a['delivery']==override['delivery']
for a in selected['details']:
 assert sha(a['source'])==a['source_sha256'];equal(a['file'],a['webp'],a['size'])
 with Image.open(R/a['source'])as p,Image.open(R/a['file'])as q:
  assert p.crop(tuple(a['source_crop_pixels'])).convert('RGBA').tobytes()==q.convert('RGBA').tobytes(),(a['id'],'crop is not literal source pixels')
a=next(x for x in c['inspection_views']if x['id']=='microphone_base');assert a['file']==selected['inspection_overrides']['microphone_base']['file'];equal(a['file'],a['webp'],[3840,2160])
# A color/readability measurement, NOT an automatic diagnosis or proof of amount/cause.
color_checks=[]
for logical,previous,region in [('incident_c2','incident_c2_forensic_r2',[.34,.15,.47,.36]),('incident_c3a','incident_c3a_forensic_r1',[.38,.20,.76,.99]),('incident_c3b','incident_c3b_forensic_r3',[0,.15,.43,.99]),('incident_c4','incident_c4_forensic_r2',[.12,.75,.31,.99])]:
 new=selected['overrides'][logical]['source']
 def violet_count(path):
  with Image.open(retained(path))as im:
   w,h=im.size;box=tuple(round(x*(w if i%2==0 else h))for i,x in enumerate(region));p=np.asarray(im.crop(box).convert('RGB')).astype(float);rr,gg,bb=p[:,:,0],p[:,:,1],p[:,:,2];return int(((rr>80)&(bb>125)&(gg<rr*.70)&(gg<bb*.65)&(bb>=rr*.85)).sum())
 before=violet_count('art/cg_v4/builtin/'+previous+'.png');after=violet_count(new);assert after>before,(logical,'requested violet contrast failed',before,after)
 color_checks.append({'logical_id':logical,'prior_saturated_violet_pixels':before,'new_saturated_violet_pixels':after,'meaning':'contrast in annotated same-context region; NOT blood segmentation/forensic volume inference'})
result={'status':'PASS','retained_generated_versions':len(reports),'checks':reports,'selected_scene_replacements':6,'literal_detail_views':len(selected['details']),'catalog_references':'PASS','inspection_tool_override':'PASS','readability_color_checks':color_checks,'proof_limit':'Exact pixel lineage and color checks do not certify medical facts or every artistic pixel; see visual_review.json','nai_calls':0,'external_paid_calls':0,'runtime_integrated':False}
target=O/'technical_qa.json'
if cleanup_only:
 result['scope']='Cleanup image lineage only; original manuscript hashes retained, drift separately recorded'
 result['manuscript_drift']=manuscript_drift
 target=R/'_삭제대기_2026-10-29/forensic-integrity.json'
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('CLEANUP FORENSIC IMAGE PASS' if cleanup_only else 'FORENSIC PASS',len(reports),'retained versions;',len(selected['details']),'literal source views; manuscript drift',len(manuscript_drift),flush=True)
