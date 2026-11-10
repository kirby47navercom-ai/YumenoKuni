"""Retain bounded adv_choices evidence and own native reconstruction proof."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/analysis/v3_rebuild'
SPEC = ROOT / 'docs/spec/18_V3_분석'
NATIVE = Path('C:/Users/kirby/Downloads/v3_re/native')

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

parser = argparse.ArgumentParser()
parser.add_argument('--native-report', type=Path, required=True)
parser.add_argument('--pixel-review', type=Path, required=True)
args = parser.parse_args()
c = read(DOC / 'dialogue_choice_ui_contract.json')
identity = c['cache_identity']
cache_path = Path(identity['path'])
with cache_path.open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == identity['sha256']
cache = read(cache_path)
records = {r['evidence_id']: r for r in cache['records']}
assert len(records) == identity['record_count']
index = read(SPEC / 'evidence_index.json')
indexed = {r['evidence_id'] for r in index['records']}
for item in c['evidence'].values():
    r = records[item['id']]
    assert r['evidence_id'] in indexed
    assert r['subject']['digest']['sha256'] == item['subject_sha256'] == identity['subject_sha256']
    assert r['analysis_profile']['digest'] == item['analysis_profile_digest'] == identity['analysis_profile_digest']
    assert r['operation'] == item['operation']
assert read(Path(c['source_choice']['metadata_path']))['sha256'] == c['source_choice']['sfl_sha256']
for item in c['provenance_reports']:
    assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() == item['sha256']
assert c['validation']['normal_navigation_motion_tracks'] == 9
assert c['validation']['confirmation_records_audited'] == 221
assert c['validation']['count4_index0_active_filter_fixed']
report = read(args.native_report)
review = read(args.pixel_review)
assert report['ok'] and report['fixture']
assert review['reviewed'] and review['accepted']
assert review['native_report'] == str(args.native_report).replace('\\', '/')
finding = {
    'contract': 'dialogue_choice_ui_contract.json', 'cache_identity': identity,
    'evidence_ids': [r['id'] for r in c['evidence'].values()],
    'source_sfl': c['source_choice'],
    'source_layout': 'Ordinary WRD adv_choices: right-bottom 2/3/4 strips, original count slots, 40design font,9 individual base/text/active focus paths. Confirmation retains the actual selected terminal coordinates; no universal1040 alignment.',
    'source_semantics': 'Original conditional cancel field0x1028==1 and visual-ready return gate are separated from own M/gift cancel. Source intro/out/full child blend and original physical keys are unobserved.',
    'own_adaptations': 'Editable off/on/check because3 source BC7 rasters unavailable; yellow/black selected strip redrawn from official public system img_08, own contrast/fonts/60Hz projection/12update confirm gate; measured full-label windows and4-visible long-list scrolling. Questions use existing dialogue body with all previous name/Next layers hidden. No rewritten or dropped authored choices.',
    'native_verification': {'path': str(args.native_report), 'executable': report['executable'], 'checks': report['checks'], 'scope': report['scope']},
    'pixel_review': review, 'unknowns': c['unknowns'],
    'original_execution': False, 'new_extraction': False,
    'new_evidence_records': 0, 'behavior_progress_changed': False,
}
write(DOC / 'dialogue_choice_ui_findings.json', finding)
write(NATIVE / 'dialogue_choice_ui_findings.json', finding)
numbers = read(SPEC / 'numbers.json')
numbers['ui']['dialogue_choice_ui_20261030'] = {
    'findings': str(NATIVE / 'dialogue_choice_ui_findings.json'),
    'source_counts': [2, 3, 4], 'focus_tracks': 9,
    'native_report': str(args.native_report), 'behavior_progress_changed': False,
}
write(SPEC / 'numbers.json', numbers)
print(json.dumps({'ok': True, 'existing_evidence_records_checked': len(c['evidence']),
                  'indexed_records': len(indexed), 'behavior_progress_changed': False}))
