"""Retain narrow static report questions and verify the own UI projection."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/analysis/v3_rebuild'
SPEC = ROOT / 'docs/spec/18_V3_분석'
NATIVE = Path('C:/Users/kirby/Downloads/v3_re/native')
def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
parser = argparse.ArgumentParser()
parser.add_argument('--native-report', type=Path)
parser.add_argument('--pixel-review', type=Path)
args = parser.parse_args()
c = read(DOC/'report_card_ui_contract.json')
bundles = [b for b in c['sources'] if 'supplement-' in b.get('path', '')]
assert len(bundles) == 3
records = []
for b in bundles:
    p = Path(b['path'])
    assert hashlib.sha256(p.read_bytes()).hexdigest() == b['sha256']
    data = read(p)
    assert data['artifacts'][0]['digest']['sha256'] == c['target_sha256']
    assert len(data['records']) == 1
    assert all((r['analysis_profile'].get('digest') if isinstance(r['analysis_profile'],dict) else r['analysis_profile']) == b['analysis_profile_digest'] for r in data['records'])
    records += data['records']
widgets = {key: {n['id']: n for n in read(ROOT/f'Game/Assets/UI/{name}.hbwidget.json')['nodes']} for key, name in [('report','PadReportV4'),('skill','PadSkillV4')]}
checks = []
def check(widget, node, expected):
    actual = widgets[widget][node]['slot']['offset']
    assert max(abs(a-b) for a,b in zip(actual,expected)) <= .002, (node, actual, expected)
    checks.append({'widget': widget, 'node': node, 'source_rect': expected, 'own_rect': actual})
for leaf in c['strip']['leaves']:
    if leaf['path'].startswith('p_kirikae_chara_'):
        index = int(leaf['path'].split('_')[-1].split('/')[0])
        check('report', 'PrActor'+str(index), leaf['rect_1280'])
for prefix, key in [('PrLabel','p_c_'),('PrValue','p_a_')]:
    for i in range(8):
        leaf = next(x for x in c['normal_pages'][0]['text_leaves'] if x['path'].startswith(key+str(i).zfill(3)+'/'))
        check('report', prefix+str(i), leaf['rect_1280'])
layout = c['skill_window_static']['derived_world_layout']
for side, prefix in [('catalog','PsRow'),('equipped','PsEquipped')]:
    for i,leaf in enumerate(layout[side]['text_leaves']):
        check('skill',prefix+str(i),leaf['rect_1280'])
check('skill','PsBody',[295,527.66667,800,100])
for side in ['catalog','equipped']:
    panel=c['skill_window_static']['panel_background_and_frames']['snapshots'][side]['leaves']
    check('skill','PsPanel'+side,next(x for x in panel if x['path']=='i_black_beta/d1')['rect_world_1280_derived'])
    for i,leaf in enumerate(x for x in panel if 'i_gra_line_000_' in x['path']):
        check('skill','PsFrame'+side+str(i),leaf['rect_world_1280_derived'])
assert widgets['report']['PrStanding']['slot']['zIndex']==10
assert widgets['report']['PrHint']['slot']['zIndex']==50
finding = {'target_sha256': c['target_sha256'], 'bundles': bundles, 'source_quads_checked': len(checks), 'projection': checks,
 'contract': 'report_card_ui_contract.json', 'original_runtime_observed': False, 'behavior_progress_changed': False,
 'own_policy': ['Sixteen nonuniform switch slots and full standing/name band; original own art pixels preserved with contain.',
 'Eight basic physical/preferences fields from existing character master. Magical abilities, old relationship memo and hidden family/history excluded. Blood/birthday parse only the public value, removing master editorial notes; measured source-font fitting stays at20..30px.',
 'Own three completed FTE encounters yield only their completed pages; body quotes come solely from actual read nodes in that completed encounter/alias, never an unchosen branch.',
 'Protagonist page1 is a separate skill entry; catalog and equipped lists are separate seven-row resources with full-width lower description.',
 'Original FP purchase/credit policy is not implemented by this UI change. Existing authored project SP/ownership/group rules remain; locked skills do not become owned by viewing.',
 'Native upper-bound/used totals are known, but their symbol-to-named-digit mapping is not. Own large-left used/small-right capacity pairing is explicitly a project display policy.',
 'Own PC keys, own sparse affinity/frame vectors and own digit/font rendering do not claim original raster, alpha, scroll text, full animation or Korean/US SFL hash equality.',
 'Source base/frame carriers use own translucent gradient and sparse line materials. The16px source tile is not proof of uniform opaque black; source per-row85px canvases are not painted as overlapping opaque cards.',
 'Selected row retains source full opacity even when project ownership is locked; unselected ownership dimming is an explicit project policy. Own hint is drawn above the standing, and the shared generic hint is hidden.'],
 'native_status': 'Pending own native input and pixel review; static projection is not visual acceptance.'}
if args.native_report:
    report = read(args.native_report)
    assert report['ok']
    finding['native_status'] = 'Own fixture passed; full scope and adaptations remain explicit.'
    finding['native_verification'] = {'path': str(args.native_report), 'checks': report['checks'], 'scope': report['scope'], 'executable': report['executable']}
if args.pixel_review:
    review=read(args.pixel_review)
    assert args.native_report and review['native_report']==str(args.native_report).replace('\\','/') and review['reviewed'] and review['accepted']
    finding['pixel_review']=review
    finding['native_status']='Own fixture input checks passed and listed native PNGs were directly reviewed. Original raster/full UI/campaign equality remains unaccepted.'
write(DOC/'pad_report_ui_findings.json',finding)
write(NATIVE/'pad_report_ui_findings.json',finding)
index = read(SPEC/'evidence_index.json')
by_id = {r['evidence_id']: r for r in index['records']}
before = len(by_id)
for r in records:
    if r['evidence_id'] not in by_id:
        by_id[r['evidence_id']] = {k: r[k] for k in ['evidence_id','operation','parameters','confidence','authority','locations']}
index['records'] = sorted(by_id.values(), key=lambda r:r['evidence_id'])
paths = {b['path'] for b in bundles}
index['supplementary_bundles'] = [b for b in index.get('supplementary_bundles',[]) if b['path'] not in paths]+bundles
write(SPEC/'evidence_index.json',index)
numbers = read(SPEC/'numbers.json')
numbers['coverage']['rea_evidence_records'] = len(by_id)
numbers['ui']['pad_report_followup_20261030'] = {'findings': str(NATIVE/'pad_report_ui_findings.json'), 'bundles': bundles, 'source_quads_checked': len(checks), 'behavior_progress_changed': False}
write(SPEC/'numbers.json',numbers)
print(json.dumps({'ok':True,'source_quads':len(checks),'new_records':len(by_id)-before,'indexed_records':len(by_id),'behavior_progress_changed':False}))
