"""Index retained rules UI questions without touching the game or original files."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/analysis/v3_rebuild'
SPEC=ROOT/'docs/spec/18_V3_분석'
NATIVE=Path('C:/Users/kirby/Downloads/v3_re/native')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c=read(DOC/'rules_book_ui_contract.json')
parser=argparse.ArgumentParser();parser.add_argument('--native-report',type=Path);parser.add_argument('--pixel-review',type=Path);args=parser.parse_args()
records=[]
for b in c['supplements']:
 p=Path(b['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==b['sha256'];data=read(p)
 assert data['artifacts'][0]['digest']['sha256']==c['target_sha256'];assert len(data['records'])==b['records']
 for row in data['records']:
  profile=row['analysis_profile'];digest=profile.get('digest') if isinstance(profile,dict) else profile
  assert digest=='249564812a8d83b9b3f461098fc485ccde60c516d4497547a124081c91d654bf'
 records+=data['records']
index=read(SPEC/'evidence_index.json');by_id={r['evidence_id']:r for r in index['records']};before=len(by_id)
for r in records:
 if r['evidence_id'] not in by_id:by_id[r['evidence_id']]={k:r[k] for k in ['evidence_id','operation','parameters','confidence','authority','locations']}
index['records']=sorted(by_id.values(),key=lambda r:r['evidence_id']);paths={b['path'] for b in c['supplements']}
index['supplementary_bundles']=[b for b in index.get('supplementary_bundles',[]) if b['path'] not in paths]+c['supplements'];write(SPEC/'evidence_index.json',index)
checks=[]
widget_path=ROOT/'Game/Assets/UI/PadRulesV4.hbwidget.json'
if widget_path.exists():
 nodes={x['id']:x for x in read(widget_path)['nodes']}
 carriers=c['five_representative_carriers'];text=carriers['text_overlay']['leaves'];cover=carriers['cover_US']['leaves']
 def check(node,leaves,path):
  expected=next(x for x in leaves if x['path']==path)['rect_1280'];actual=nodes[node]['slot']['offset'];assert max(abs(a-b) for a,b in zip(expected,actual))<.002
  checks.append({'node':node,'source_rect':expected,'own_rect':actual})
 for node,path in [('KrCover','p_koushou/d1'),('KrCoverTitle','p_kousoku_title/_f_kousoku_title'),('KrCoverTitleBand','p_title_base/_a_title_base_000_DXT1/d1')]:check(node,cover,path)
 for node,path in [('KrBodyViewport','p_kousoku_text/_f_kousoku_text'),('KrNumberBase','d18'),('KrSlash','p_number_slash/d1')]:check(node,text,path)
 for i in range(4):check('KrNumber'+str(i),text,'p_number_'+str(i).zfill(3)+'/d1')
 for i,path in enumerate(['i_base/i_base_hasi_000/d1','i_base/d3','i_base/i_base_hasi_001/d1']):check('KrFrame'+str(i),text,path)
 for kind,source in [('Next','000'),('Prev','001')]:
  for i in range(2):check('Kr'+kind+str(i),text,'p_yazirusi_'+source+'/i_yazirusi_'+str(i).zfill(3)+'/d1')
finding={'target_sha256':c['target_sha256'],'contract':'rules_book_ui_contract.json','bundles':c['supplements'],'source_quads_checked':len(checks),'projection':checks,
 'normal_structure':'Shared background, upper current/total badge, central per-rule illustration, lower centered body. No split left/right text pages.',
 'body_rect_1280':[188,556.66667,900,73.33333],'body_font_1280':30,
 'behavior':'Only published rules after cover; bounded up/down, transition input gate. Cover excluded from total. Current/old body are separate; normal wait hides old text.',
 'figure_link':'Native cover/01/02_05-combined/remaining carrier routing and enter/leave actions retained. Compound illustration transitions are not independent page files.',
 'limits':c['limitations'],'own_implementation_status':'Source-layout reader implemented; native input/pixel checks remain pending unless explicitly attached.',
 'own_adaptations':['Authored29 public-record ids retain their committed order, but only actually acquired nonprivate canonical records appear. Unrelated documents and future rules do not enter the reader.',
 'Source cover/body/page badge/arrow carriers retained, without a generic list/right information card. Own long text scrolls inside the exact900x73.333 viewport at30px; selected page resets scroll.',
 'Supplied V3 menu emblem is adapted to the cover; approved own host is an illustration at the representative central carrier. These are not original cover/per-rule artwork or compound02_05 animation reconstruction.',
 'Own W/S and arrow mouse input, current-left/total-right digit pairing, .24s direction/fade transition. Input is gated while transitioning; source exact timing/material/digit DAT association remains unresolved.'],
 'original_runtime_observed':False,'behavior_progress_changed':False}
if args.native_report:
 report=read(args.native_report);assert report['ok'];finding['native_verification']={'path':str(args.native_report),'checks':report['checks'],'scope':report['scope'],'executable':report['executable']};finding['own_implementation_status']='Own native fixture input checks passed; pixel review is separate.'
if args.pixel_review:
 review=read(args.pixel_review);assert args.native_report and review['reviewed'] and review['accepted'];finding['pixel_review']=review;finding['own_implementation_status']='Own native input checks and listed PNG review passed within the explicit adaptation scope. Original per-rule illustrations/animation are not accepted.'
write(DOC/'pad_rules_ui_findings.json',finding);write(NATIVE/'pad_rules_ui_findings.json',finding)
numbers=read(SPEC/'numbers.json');numbers['coverage']['rea_evidence_records']=len(by_id)
numbers['ui']['pad_rules_followup_20261030']={'findings':str(NATIVE/'pad_rules_ui_findings.json'),'bundles':c['supplements'],'representative_static_carriers':5,'source_quads_checked':len(checks),'behavior_progress_changed':False};write(SPEC/'numbers.json',numbers)
print(json.dumps({'ok':True,'new_records':len(by_id)-before,'indexed_records':len(by_id),'behavior_progress_changed':False}))
