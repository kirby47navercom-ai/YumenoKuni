"""Register bounded dialogue controller evidence; keep behavior score unchanged."""
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

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

parser = argparse.ArgumentParser()
parser.add_argument('--native-report', type=Path)
parser.add_argument('--pixel-review', type=Path)
args = parser.parse_args()
c = read(DOC / 'dialogue_window_ui_contract.json')
identity = c['cache_identity']
assert digest(Path(identity['path'])) == identity['sha256']
base = read(Path(identity['path']))
base_records = {r['evidence_id']: r for r in base['records']}
assert len(base_records) == identity['record_count']
supplement = c['focused_trial_native_evidence']['complete_external_bundle']
assert digest(Path(supplement['path'])) == supplement['sha256']
bundle = read(Path(supplement['path']))
assert len(bundle['records']) == supplement['record_count'] == 13
for record in bundle['records']:
    assert record['subject']['digest']['sha256'] == identity['subject_sha256']
    assert record['analysis_profile']['digest'] == identity['analysis_profile_digest']
    assert 'raw_result' in record and 'normalized_result' in record
all_records = {**base_records, **{r['evidence_id']: r for r in bundle['records']}}
for item in c['evidence'].values():
    record = all_records[item['evidence_id']]
    assert record['subject']['digest']['sha256'] == identity['subject_sha256']
    assert record['analysis_profile']['digest'] == identity['analysis_profile_digest']
for family in c['families'].values():
    assert digest(Path(family['metadata_path'])) == family['metadata_file_sha256']
    assert read(Path(family['metadata_path']))['sha256'] == family['sfl_source_sha256']
assert c['trial_dialogue_binding']['status'] == 'controller_resource_and_script_selection_binding_confirmed_statically'
index = read(SPEC / 'evidence_index.json')
indexed = {r['evidence_id']: r for r in index['records']}
before = len(indexed)
for record in bundle['records']:
    if record['evidence_id'] not in indexed:
        indexed[record['evidence_id']] = {k: record[k] for k in ['evidence_id', 'operation', 'parameters', 'confidence', 'authority', 'locations']}
index['records'] = sorted(indexed.values(), key=lambda x: x['evidence_id'])
index['supplementary_bundles'] = [x for x in index.get('supplementary_bundles', []) if x['path'] != supplement['path']] + [supplement]
finding = {
    'contract': 'dialogue_window_ui_contract.json', 'cache_identity': identity,
    'supplement': supplement,
    'source_ADV': 'Composed body/font scale; separate image-based name and current-protagonist branch, nameless cleanup, independent page indicator. No native first-codepoint overlay evidence.',
    'source_trial': '4366d0/4389c0: saved16ae0 uses separate t_kaiwa_fl name/icon frame and pl/cry/low body;1 uses event body and standalone event name. WIN selects panel/vertical/horizontal/entry with named parameter-table values. Separate next raster family and unresolved4ab210(80,10) external transform.',
    'own_mapping': 'Authored own protagonist identity from character0001. Missing WIN maps explicitly to Normal/Down/Center/in; not original implicit default. Actual font metrics/preserved original text/3ADV or2trial line pages; read and graph routing only after final page. Own full-name images and approved portrait inside source carriers; missing texture ink/glow/masks remain reconstruction.',
    'public_visual_reference': {
        'page': 'https://www.danganronpa.com/pages/v3/system/',
        'daily_image': 'https://titleimg.spike-chunsoft.co.jp/www.danganronpa.com/v3/images/system/img_08.png',
        'reviewed_by_root': True,
        'method': 'Read-only hidden browser screenshot of official1070x296 composite; no original execution or local media download.',
        'observed': 'Three ordinary ADV examples: low black text region, yellow slanted side ornament; selected free-time invitation strip yellow with dark text. Used for own ink impression, not texture or pixel equality.',
    },
    'implementation_status': 'Source and pure checks ready; native/pixel proof pending.',
    'unknowns': c['unknowns'], 'original_execution': False,
    'new_extraction': False, 'behavior_progress_changed': False,
}
if args.native_report:
    report = read(args.native_report)
    assert report['ok'] and report['fixture']
    finding['native_verification'] = {'path': str(args.native_report), 'executable': report['executable'], 'checks': report['checks'], 'scope': report['scope']}
    finding['implementation_status'] = 'Listed own native dialogue checks passed; full source missing-raster/timing/material equality remains unaccepted.'
if args.pixel_review:
    review = read(args.pixel_review)
    assert args.native_report and review['reviewed'] and review['accepted']
    assert review['native_report'] == str(args.native_report).replace('\\', '/')
    finding['pixel_review'] = review
write(SPEC / 'evidence_index.json', index)
write(DOC / 'dialogue_window_ui_findings.json', finding)
write(NATIVE / 'dialogue_window_ui_findings.json', finding)
numbers = read(SPEC / 'numbers.json')
numbers['coverage']['rea_evidence_records'] = len(indexed)
numbers['ui']['dialogue_window_ui_20261030'] = {
    'findings': str(NATIVE / 'dialogue_window_ui_findings.json'),
    'supplement': supplement, 'behavior_progress_changed': False,
}
write(SPEC / 'numbers.json', numbers)
print(json.dumps({'ok': True, 'new_records': len(indexed) - before, 'indexed_records': len(indexed), 'behavior_progress_changed': False}))
