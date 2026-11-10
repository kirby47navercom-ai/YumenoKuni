"""Register immutable source evidence and bounded own HUD checks, never behavior-score counts."""
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
c = read(DOC / 'exploration_hud_ui_contract.json')
identity = c['identity']
assert digest(Path(identity['base_cache_path'])) == identity['base_cache_sha256']
resolution = c['player_growth']['gauge_motion_followup']['setter_resolution']
bundle_meta = resolution['supplement']
assert digest(Path(bundle_meta['path'])) == bundle_meta['sha256']
bundle = read(Path(bundle_meta['path']))
assert len(bundle['records']) == bundle_meta['records'] == 12
for record in bundle['records']:
    assert record['subject']['digest']['sha256'] == identity['static_target_sha256']
    profile = record['analysis_profile']
    if profile['digest'] != identity['analysis_profile_digest']:
        assert record['operation'] == 'batch_decompile'
        assert profile['provider']['id'] == 'rea-workflow'
        assert profile['parameters']['workflow_revision'] == 2
        assert profile['parameters']['upstream_analysis_profile']['digest'] == identity['analysis_profile_digest']
    assert 'raw_result' in record and 'normalized_result' in record
index = read(SPEC / 'evidence_index.json')
records = {r['evidence_id']: r for r in index['records']}
before = len(records)
for record in bundle['records']:
    if record['evidence_id'] not in records:
        records[record['evidence_id']] = {k: record[k] for k in ('evidence_id', 'operation', 'parameters', 'confidence', 'authority', 'locations')}
index['records'] = sorted(records.values(), key=lambda r: r['evidence_id'])
index['supplementary_bundles'] = [m for m in index.get('supplementary_bundles', []) if m['path'] != bundle_meta['path']] + [bundle_meta]
finding = read(DOC / 'exploration_hud_ui_findings.json')
finding['contract_sha256'] = digest(DOC / 'exploration_hud_ui_contract.json')
finding['gaugeNativeLimit'] = 'p_guage key and XY extra-offset resolved; authored17+new(136*ratio-4), fixed mask150, not cumulative and not width stretch. Original renderer pixels remain separate.'
finding['gaugeSetterSupplement'] = bundle_meta
finding['implementation'] = {
    'source': 'Game/tools/v4-exploration-hud-ui.mjs',
    'status': 'Generation/build/native verification pending',
    'applied': ['fl_wait full affine/local shape geometry and supplied raster identities', 'source numbered chapter ordinals4/5 preserved', 'fixed gauge masked with source additive offset', 'independent source XP99 thresholds, Walk2/TalkCharacter10/CheckObject10', 'V4/Legacy persistent player progress separate from bonds', 'fixed lower-center target name geometry and cursor carrier'],
    'own_adaptations': ['readable12px level ink fit', 'immediate displayed level and1% gauge sampling', 'world meter-to-step phase using existing bob radians/stop settling', 'phase inferred from own known background; complete source phase overrides remain pending', 'own target backdrop/reticle ink because35 source texture PNGs are unavailable'],
    'not_accepted': ['full original levelup presentation and source skill-capacity coupling', 'all11 XP routes, original cadence meters', 'all phase visibility/tint overrides', 'original target/reticle raster and level font ink', 'whole UI/campaign acceptance'],
}
if args.native_report:
    report = read(args.native_report)
    assert report['ok'] and report['fixture']
    finding['implementation']['status'] = 'Listed actual own native checks passed; bounded scope only'
    finding['native_verification'] = {'path': str(args.native_report), 'executable': report['executable'], 'checks': report['checks'], 'scope': report['scope']}
if args.pixel_review:
    review = read(args.pixel_review)
    assert args.native_report and review['reviewed'] and review['accepted']
    assert review['native_report'] == str(args.native_report).replace('\\', '/')
    finding['pixel_review'] = review
write(SPEC / 'evidence_index.json', index)
write(DOC / 'exploration_hud_ui_findings.json', finding)
write(NATIVE / 'exploration_hud_ui_findings.json', finding)
numbers = read(SPEC / 'numbers.json')
numbers['coverage']['rea_evidence_records'] = len(records)
numbers['ui']['exploration_hud_source_20261030'].update({'gaugeSetterSupplement': bundle_meta, 'implementationAccepted': False, 'listedNativeChecksAccepted': bool(args.native_report), 'listedPixelScopeAccepted': bool(args.pixel_review), 'implementationScope': finding['implementation']})
write(SPEC / 'numbers.json', numbers)
print(json.dumps({'ok': True, 'new_records': len(records) - before, 'indexed_records': len(records), 'behavior_progress_changed': False}))
