"""Register just the trial answer family and its bounded native proof."""
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
contract_path = DOC / 'trial_answer_choice_ui_contract.json'
c = read(contract_path)
identity = c['cache_identity']
assert digest(Path(identity['path'])) == identity['sha256']
bundle = c['external_evidence']
assert digest(Path(bundle['path'])) == bundle['sha256']
evidence = read(Path(bundle['path']))['records']
assert len(evidence) == bundle['record_count'] == 17
for record in evidence:
    assert record['subject']['digest']['sha256'] == identity['subject_sha256']
    assert record['analysis_profile']['digest'] == identity['analysis_profile_digest']
    assert 'raw_result' in record and 'normalized_result' in record
for family in c['families'].values():
    assert digest(Path(family['metadata_path'])) == family['metadata_file_sha256']
index = read(SPEC / 'evidence_index.json')
records = {r['evidence_id']: r for r in index['records']}
before = len(records)
for record in evidence:
    if record['evidence_id'] not in records:
        records[record['evidence_id']] = {k: record[k] for k in ['evidence_id', 'operation', 'parameters', 'confidence', 'authority', 'locations']}
index['records'] = sorted(records.values(), key=lambda r: r['evidence_id'])
index['supplementary_bundles'] = [b for b in index.get('supplementary_bundles', []) if b['path'] != bundle['path']] + [bundle]
finding = {'contract': str(contract_path), 'contract_sha256': digest(contract_path), 'identity': identity, 'supplement': bundle,
           'source': '426ed0/427020 general trial2/3/4 answer controller, input wrap/no generic cancel, confirmed-index history, visual exit before WRDChoiceN judgment;225actual source records retain geometry/color chains.',
           'implementation': 'Separate source geometry/blue-gray choice family; original ADV/person/evidence/reasoning code paths are not relabeled as this family.',
           'own_adaptations': ['flat/notched missing-raster strip/number/check ink; confirmed check replaces overlapping numeral ink; suppress dormant cursor decorations beyond authored answer count because original raster alpha is unavailable', 'black frame and localized title ink inside source carriers; original palette unknown', '60Hz source-record admission', 'long labels reuse existing measured text window at600px', 'confirmed history clears per own task/stage context and is saved explicitly'],
           'unknowns': c['unknowns'], 'originalExecution': False, 'newExtraction': False, 'behaviorProgressChanged': False}
if args.native_report:
    report = read(args.native_report)
    assert report['ok'] and report['fixture'] and report['taskId'] == 'T1-ANSWER-A01'
    finding['native_verification'] = {'path': str(args.native_report), 'executable': report['executable'], 'checkpoint': report['checkpoint'], 'checks': report['checks'], 'scope': report['scope']}
if args.pixel_review:
    review = read(args.pixel_review)
    assert args.native_report and review['reviewed'] and review['accepted']
    assert review['native_report'] == str(args.native_report).replace('\\', '/')
    finding['pixel_review'] = review
write(SPEC / 'evidence_index.json', index)
write(DOC / 'trial_answer_choice_ui_findings.json', finding)
write(NATIVE / 'trial_answer_choice_ui_findings.json', finding)
numbers = read(SPEC / 'numbers.json')
numbers['coverage']['rea_evidence_records'] = len(records)
numbers['ui']['trial_answer_choice_20261030'] = {'findings': str(NATIVE / 'trial_answer_choice_ui_findings.json'), 'source_tracks': 9, 'source_records': 225, 'providedRasterCount': 0, 'listedNativeChecksAccepted': bool(args.native_report), 'listedPixelScopeAccepted': bool(args.pixel_review), 'wholeUIAccepted': False, 'behavior_progress_changed': False}
write(SPEC / 'numbers.json', numbers)
print(json.dumps({'ok': True, 'new_records': len(records) - before, 'indexed_records': len(records), 'behavior_progress_changed': False}))
