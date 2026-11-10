"""Validate existing static gift evidence and own projected widget; no target execution."""
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
def write(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

parser = argparse.ArgumentParser()
parser.add_argument('--native-report', type=Path)
args = parser.parse_args()
source = read(DOC / 'pad_gift_icon_scale_followup.json')
for b in source['bundle_identity'] + [source['supplement']]:
    p = Path(b['path'])
    assert hashlib.sha256(p.read_bytes()).hexdigest() == b['sha256'], p
bundle = read(Path(source['supplement']['path']))
assert bundle['artifacts'][0]['digest']['sha256'] == source['target_sha256']
nodes = {n['id']: n for n in read(ROOT / 'Game/Assets/UI/PadGiftV4.hbwidget.json')['nodes']}
projections = []
for cell in source['actual_initialized_grid']:
    for node, key in [('PgBase', 'base'), ('PgFrame', 'frame'), ('PgImage', 'image'), ('PgTimes', 'times'), ('PgDigit', 'ones')]:
        name = node + str(cell['slot']) + ('_0' if node == 'PgDigit' else '')
        expected = cell[key + '_quad_1280']
        actual = nodes[name]['slot']['offset']
        assert max(abs(a-b) for a, b in zip(actual, expected)) <= .002, name
        projections.append({'node': name, 'source_rect': expected, 'own_rect': actual})
finding = {
    'target_sha256': source['target_sha256'], 'analysis_profile': source['required_profile'],
    'bundle': source['supplement'], 'projection_count': len(projections), 'projection': projections,
    'source_geometry': '27 external clones, root scale1, design pitch190x193, exact image/base/frame/count quads. Not placeholder64x64.',
    'own_state': '110 authored items; separate persisted discovery/NEW/inventory. NEW begins on first own acquisition and clears when selection leaves; browsing never consumes gifts.',
    'compatibility': 'Old saves migrate extant inventory keys and V4 gift receipts to discovery. Legacy previously erased spent items with no ledger cannot be recovered. Old saves never fabricate NEW.',
    'adaptations': [
        'Source base/frame/unknown999 rasters absent; editable sparse own marks preserve source canvases without an opaque256 square.',
        'Own gift art uses exact128x128 source picture quad with contain; own font digits replace unavailable source digit rasters.',
        'Own WASD grid and Q/E paging are PC mappings, not recovered original physical keys.',
        'Own first-discovery NEW award policy and three-digit display cap999 are explicit adaptations; source acquisition setters/cap were not recovered.',
        'Authored gift catalogue has names and tiers only; no invented descriptions or claim that missing source prose is present.',
    ],
    'original_runtime_observed': False, 'behavior_progress_changed': False,
}
if args.native_report:
    runtime = read(args.native_report)
    assert runtime['ok'] and 'v4-pad-gift-' in str(args.native_report)
    finding['own_native_verification'] = {'path': str(args.native_report), 'executable': runtime['executable'], 'checks': runtime['checks'], 'scope': runtime['scope']}
else:
    old = DOC / 'pad_gift_ui_findings.json'
    if old.exists() and 'own_native_verification' in read(old):
        finding['own_native_verification'] = read(old)['own_native_verification']
write(DOC / 'pad_gift_ui_findings.json', finding)
write(NATIVE / 'pad_gift_ui_findings.json', finding)
index = read(SPEC / 'evidence_index.json')
by_id = {r['evidence_id']: r for r in index['records']}
before = len(by_id)
for r in bundle['records']:
    if r['evidence_id'] not in by_id:
        by_id[r['evidence_id']] = {k: r[k] for k in ['evidence_id', 'operation', 'parameters', 'confidence', 'authority', 'locations']}
index['records'] = sorted(by_id.values(), key=lambda r: r['evidence_id'])
index['supplementary_bundles'] = [b for b in index.get('supplementary_bundles', []) if b['path'] != source['supplement']['path']] + [source['supplement']]
write(SPEC / 'evidence_index.json', index)
numbers = read(SPEC / 'numbers.json')
numbers['coverage']['rea_evidence_records'] = len(by_id)
numbers['ui']['pad_gift_clone_followup_20261030'] = {'findings': str(NATIVE / 'pad_gift_ui_findings.json'), 'bundle': source['supplement'], 'source_quads_checked': len(projections), 'behavior_progress_changed': False}
write(SPEC / 'numbers.json', numbers)
print(json.dumps({'ok': True, 'projection_count': len(projections), 'new_records': len(by_id)-before, 'indexed_records': len(by_id), 'behavior_progress_changed': False}))
