"""Register existing static map evidence and bounded own native UI proof."""
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
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

parser = argparse.ArgumentParser()
parser.add_argument('--native-report', type=Path, required=True)
parser.add_argument('--pixel-review', type=Path)
args = parser.parse_args()
c = read(DOC / 'pad_map_ui_contract.json')
identity = c['cache_identity']
with Path(identity['path']).open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == identity['sha256']
index = read(SPEC / 'evidence_index.json')
ids = {r['evidence_id'] for r in index['records']}
assert len(c['evidence']) == 18
for item in c['evidence'].values():
    assert item['evidence_id'] in ids
    assert item['subject_sha256'] == c['target_sha256']
    assert item['analysis_profile_digest'] == identity['analysis_profile_digest']
report = read(args.native_report)
assert report['ok'] and report['fixture']
finding = {
    'contract': 'pad_map_ui_contract.json', 'cache_identity': identity,
    'target_sha256': c['target_sha256'],
    'evidence_ids': [r['evidence_id'] for r in c['evidence'].values()],
    'native_verification': {'path': str(args.native_report), 'executable': report['executable'],
                            'checks': report['checks'], 'scope': report['scope']},
    'source_layout': 'Six place rows; separate4x4 character finder; area and floor controls. Source8 floor visual variants retained in data, not treated as8 navigable own floors.',
    'own_world': 'Five groups,61 actual authored instances collapsed to60 physical polygons,56 same-group schematic links. Runtime world bounds/origin/rotation and actor/player local points projected into map space. Links denote authored adjacency, not recovered corridor collision geometry.',
    'own_policies': 'Visited/current/eligible discovery; actual hub condition/reachability checks; PC keys and tab hit areas; drag limits, theme-matched clip mask, caption contrast and scrollbar fraction. Explicit UI fixture seeds discovery poses; it is not a normal campaign proof.',
    'source_fixes': 'Hub route insertion now uses the existing spot flags/cards conditions. Fresh chapter reset clears prior world identity before new begin so previous poses cannot leak into discovery.',
    'remaining_unknowns': c['remaining_unknowns'],
    'original_execution': False, 'new_extraction': False,
    'new_evidence_records': 0, 'behavior_progress_changed': False,
}
if args.pixel_review:
    review = read(args.pixel_review)
    assert review['reviewed'] and review['accepted']
    assert review['native_report'] == str(args.native_report).replace('\\', '/')
    finding['pixel_review'] = review
write(DOC / 'pad_map_ui_findings.json', finding)
write(NATIVE / 'pad_map_ui_findings.json', finding)
numbers = read(SPEC / 'numbers.json')
numbers['ui']['pad_map_ui_20261030'] = {
    'findings': str(NATIVE / 'pad_map_ui_findings.json'),
    'source_place_rows': 6, 'source_character_cells': 16,
    'own_map_groups': 5, 'own_instances': 61,
    'native_report': str(args.native_report), 'behavior_progress_changed': False,
}
write(SPEC / 'numbers.json', numbers)
print(json.dumps({'ok': True, 'existing_evidence_records_checked': 18,
                  'indexed_records': len(ids), 'behavior_progress_changed': False}))
