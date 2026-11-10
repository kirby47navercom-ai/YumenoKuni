"""Retain the bounded PC options source question; behavior progress stays fixed."""
import hashlib
import json
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/analysis/v3_rebuild';SPEC=ROOT/'docs/spec/18_V3_분석';NATIVE=Path('C:/Users/kirby/Downloads/v3_re/native')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
parser=argparse.ArgumentParser();parser.add_argument('--native-report',type=Path);parser.add_argument('--pixel-review',type=Path);args=parser.parse_args()
c=read(DOC/'options_ui_contract.json');base=c['base_cache'];b=c['supplement']
for source in [base,b]:assert hashlib.sha256(Path(source['path']).read_bytes()).hexdigest()==source['sha256']
bundle=read(Path(b['path']));assert len(bundle['records'])==1
r=bundle['records'][0];assert r['evidence_id']==b['evidence_id'] and r['subject']['digest']['sha256']==c['target_sha256']
profile=r['analysis_profile'];assert (profile.get('digest') if isinstance(profile,dict) else profile)==c['analysis_profile_digest']
assert len(c['provided_rasters']['resources'])==19
for resource in c['provided_rasters']['resources']:assert Path(resource['path']).is_file()
assert c['observed']['row_count_and_order']['without_optional_voice']==list(range(10))+[12]
assert c['main_geometry']['visible_rowcount']==8
index=read(SPEC/'evidence_index.json');records={r['evidence_id']:r for r in index['records']};before=len(records)
if r['evidence_id'] not in records:records[r['evidence_id']]={k:r[k] for k in ['evidence_id','operation','parameters','confidence','authority','locations']}
index['records']=sorted(records.values(),key=lambda r:r['evidence_id']);index['supplementary_bundles']=[x for x in index.get('supplementary_bundles',[]) if x['path']!=b['path']]+[b];write(SPEC/'evidence_index.json',index)
finding={'contract':'options_ui_contract.json','target_sha256':c['target_sha256'],'supplement':b,'source_geometry':'Eight attached row clones; four gauge/slowfast/binary/execute templates; source19 provided rasters mapped by matching SFL hash and image table order/dimensions.',
 'native_behavior':c['observed'],'implementation_status':'Source contract ready. Current own ten-row options UI is not original layout acceptance; integration remains pending.',
 'unknown':c['unknown'],'original_execution':False,'new_extraction':False,'behavior_progress_changed':False}
finding['rgba_contract']='Composed multiply/add and original PNG alpha are separate from geometry. Selected static gauge black/dynamic white; unselected static102/dynamic152 gray. Act_ef/tab translucent pixels are retained. Complete native theme overrides remain unknown.'
finding['own_ui_scope']='The eight source clones and four row forms are generated from retained RGBA/raster evidence. Existing ten project settings plus default restore keep their real backend/order/ranges and version1 compatibility; this is not original13-kind consumer reconstruction.'
if args.native_report:
 report=read(args.native_report);assert report['ok'];finding['native_verification']={'path':str(args.native_report),'checks':report['checks'],'executable':report['executable'],'scope':report['scope']};finding['implementation_status']='Listed own native eight-row layout/input/persistence checks passed. Original setting-kind semantics/full UI equality remains unaccepted.'
 if report.get('kind_consumers'):
  kinds=read(DOC/'options_kind_consumers_contract.json')
  for provenance in [kinds['provenance']['base_cache'],kinds['provenance']['retained_options_supplement'],*kinds['provenance']['cached_text_tables'].values()]:
   with Path(provenance['path']).open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==provenance['sha256']
  finding['consumer_contract']='options_kind_consumers_contract.json'
  finding['own_ui_scope']='Source PC kinds0..9,12 in8 visible rows, original numeric ranges/defaults and supplied Korean raster replacements. Actual native mixer/read reveal/reticle/bob/inversion/own PC presets/map rotation and version1->2 persistence are tested. Voice bus exists but no actor clips/preview or JP+EN packs; no native vibration claim. Own reveal timebase, pixel units, bob amplitude, PC bindings, mixer normalization and disk policy remain explicit.'
  finding['implementation_status']='Listed own native PC setting consumer/layout/migration checks passed. Voice playback/preview/language packs, original hardware/pad mapping and complete source material/timing remain unaccepted.'
if args.pixel_review:
 review=read(args.pixel_review);assert args.native_report and review['reviewed'] and review['accepted'] and review['native_report']==str(args.native_report).replace('\\','/');finding['pixel_review']=review
write(DOC/'options_ui_findings.json',finding);write(NATIVE/'options_ui_findings.json',finding)
numbers=read(SPEC/'numbers.json');numbers['coverage']['rea_evidence_records']=len(records);numbers['ui']['options_ui_20261030']={'findings':str(NATIVE/'options_ui_findings.json'),'supplement':b,'source_visible_rows':8,'provided_row_rasters':19,'behavior_progress_changed':False};write(SPEC/'numbers.json',numbers)
print(json.dumps({'ok':True,'new_records':len(records)-before,'indexed_records':len(records),'behavior_progress_changed':False}))
