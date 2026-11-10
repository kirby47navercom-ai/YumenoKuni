"""Retain the bounded system connection supplement without changing progress."""
import hashlib
import json
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/analysis/v3_rebuild';SPEC=ROOT/'docs/spec/18_V3_분석';NATIVE=Path('C:/Users/kirby/Downloads/v3_re/native')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
parser=argparse.ArgumentParser();parser.add_argument('--native-report',type=Path);parser.add_argument('--pixel-review',type=Path);args=parser.parse_args()
c=read(DOC/'pad_system_connection_contract.json');b=c['supplementary_evidence'];p=Path(b['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==b['sha256']
base=c['base_evidence_cache'];assert hashlib.sha256(Path(base['path']).read_bytes()).hexdigest()==base['sha256']
bundle=read(p);assert bundle['artifacts'][0]['digest']['sha256']==c['target_sha256'];assert len(bundle['records'])==b['records']
for r in bundle['records']:
 assert r['subject']['digest']['sha256']==c['target_sha256']
 profile=r['analysis_profile']
 if isinstance(profile,dict) and profile['provider']['id']=='rea-workflow':
  assert r['operation']=='batch_decompile' and profile['parameters']['workflow_revision']==2
  upstream=profile['parameters']['upstream_analysis_profile'];assert upstream['digest']==c['analysis_profile_digest'] and upstream['provider']['id']=='ghidra' and upstream['provider']['version']=='12.1.4'
 else:assert (profile.get('digest') if isinstance(profile,dict) else profile)==c['analysis_profile_digest']
index=read(SPEC/'evidence_index.json');records={r['evidence_id']:r for r in index['records']};before=len(records)
for r in bundle['records']:
 if r['evidence_id'] not in records:records[r['evidence_id']]={k:r[k] for k in ['evidence_id','operation','parameters','confidence','authority','locations']}
index['records']=sorted(records.values(),key=lambda r:r['evidence_id']);index['supplementary_bundles']=[x for x in index.get('supplementary_bundles',[]) if x['path']!=b['path']]+[b];write(SPEC/'evidence_index.json',index)
m=read(DOC/'pad_map_ui_contract.json');assert m['cache_identity']['sha256']==base['sha256']
finding={'contract':'pad_system_connection_contract.json','layout_contract':'pad_system_ui_contract.json','target_sha256':c['target_sha256'],'supplement':b,'original_execution':False,'source_connections':['Six system columns route independently. Main menu uses the shared confirmation; load delegates to its distinct save/load module.',
 'Shared confirmation defaults No for mainmenu, result1 Yes/result2 No or cancel; source body variants retained without assuming exact LF dispatch.',
 'Backlog is an independent fullscreen overlay with four rows, own character/name resources, fromPad return preserves existing pad/world/audio ownership.',
 'Theme selector retains38 rows, seven visible, unlock/NEW gates, preview and stable SaveNo persistence; changed selection refreshes top skin.',
 'Save/load source has six visible slots and an independent detail/confirmation resource. Total slot count and detail choice labels/controller binding remain unresolved.'],
 'map_contract':'pad_map_ui_contract.json','map_scope':'Six place rows,4x4 character cells, eight floor variants, resource readiness and destination validation, existing18 cache Evidence IDs. Native map coordinates are not own GLB coordinates.',
 'implementation_status':'Source system6 columns, separate source backlog4/save6/load detail/common confirmation/theme7 are wired. Native and pixel evidence must be supplied separately. Map and options screen are still awaiting correction.',
 'contrast_contract':'pad_theme_contrast_contract.json',
 'own_adaptations':['Thirty independently packed manual save slots; canonical and manual snapshot parts never alias. Source six visible rows are not interpreted as total capacity.',
 'All38 supplied theme backgrounds are available as own project policy; source table order and stable SaveNo are preserved, including first two rows1 then0. Native original unlock/NEW gates are not falsely claimed.',
 'Supplied background choice and default Korean menu header overlays are separate. Original complete theme palette/header/animation equality is unaccepted.',
 'Source six system icon/title carriers retain geometry; missing original rasters use own editable pictograms and Korean text. Missing source panel materials use explicitly own vectors.',
 'Source report local dark-panel geometry/alpha is retained. No invented whole-screen tint. Own independent completed-FTE pages reuse source first-record viewport rather than original cumulative rank pages.'],
 'limits':c['limits']+m['remaining_unknowns'],'behavior_progress_changed':False}
contrast=read(DOC/'pad_theme_contrast_contract.json');assert contrast['base_evidence_cache']['sha256']==base['sha256']
for ev in contrast['evidence_ids'].values():assert ev in records
if args.native_report:
 report=read(args.native_report);assert report['ok'];finding['native_verification']={'path':str(args.native_report),'checks':report['checks'],'executable':report['executable'],'scope':report['scope']}
 finding['implementation_status']='Listed own native source-layout/input/persistence checks passed; original pixel/animation/all UI/campaign acceptance remains separate.'
if args.pixel_review:
 review=read(args.pixel_review);assert args.native_report and review['reviewed'] and review['accepted'] and review['native_report']==str(args.native_report).replace('\\','/')
 finding['pixel_review']=review
write(DOC/'pad_system_connection_findings.json',finding);write(NATIVE/'pad_system_connection_findings.json',finding)
numbers=read(SPEC/'numbers.json');numbers['coverage']['rea_evidence_records']=len(records);numbers['ui']['pad_system_connections_20261030']={'findings':str(NATIVE/'pad_system_connection_findings.json'),'supplement':b,'map_existing_evidence_count':m['validation']['native_records_checked'],'behavior_progress_changed':False};write(SPEC/'numbers.json',numbers)
print(json.dumps({'ok':True,'new_records':len(records)-before,'indexed_records':len(records),'behavior_progress_changed':False}))
