"""Cross-check individual native proofs against the authored task and cue IDs."""
import json, re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
work = root/'Game/Saved/nonstop-all-20261106'
progress = json.loads((root/'Game/Saved/native-all-tasks-1793928979909/progress.json').read_text(encoding='utf-8'))
tasks = json.loads((root/'data/v4_story/native_tasks.json').read_text(encoding='utf-8'))['tasks']
direction = json.loads((root/'data/v4_story/trial_direction.json').read_text(encoding='utf-8'))
source = (root/'Game/Source/Courtroom.hpp').read_text(encoding='utf-8')
seats = re.findall(r'"([a-z]+)"', re.search(r'SEATS\[16\]\{([^}]+)', source)[1])
checked = []
camera_errors = []
results = list(progress['results'])
for name in ['native-all-tasks-ns23-20261106','native-all-tasks-ns45-20261106','native-all-tasks-ns6-host-20261106','native-all-tasks-ns-first-focus-20261106']:
    file = root/'Game/Saved'/name/'progress.json'
    if file.exists():
        other = json.loads(file.read_text(encoding='utf-8'))
        assert other['build'] == progress['build']
        results.extend(other['results'])
results = list({r['taskId']:r for r in results if r.get('ok')}.values())
seen = set()
for result in results:
    if not result.get('ok'):
        continue
    tid = result['taskId']
    if tid in seen:
        continue
    seen.add(tid)
    task = tasks[tid]
    rows = list(task['debate']['lines'])
    for extra in reversed(direction['extra'].get(tid, [])):
        rows.insert(extra.get('after', -1)+1, extra)
    proof = result['nonstopProof']
    assert len(proof['utterances']) == len(rows), tid
    for i, row in enumerate(rows):
        actual = proof['utterances'][str(i)]
        cue = direction['debate'][row['id']]
        kind = cue.get('decoy', {}).get('kind', row.get('kind', 'plain'))
        if tid.startswith('T1-') and kind == 'agree':
            kind = 'weak'
        assert actual['kind'] == kind, (tid, row['id'], kind, actual['kind'])
        expected_seat = -2 if row['actor']=='lappy' else seats.index(row['actor'])
        if actual['seat'] != expected_seat:
            camera_errors.append({'task':tid,'line':row['id'],'actor':row['actor'],'expected':expected_seat,'actual':actual['seat']})
        assert actual['capture'] and (proof['quiet'] or actual['pink']), (tid, row['id'])
    assert proof['loop']['restarted'] and proof['wrong']['restarted'], tid
    assert proof['wrong']['hp'] < proof['loop']['hp'], tid
    assert proof['turnSamples'] > 0 and proof['result'], tid
    checked.append({'task': tid, 'utterances': len(rows), 'judgment': result['outcome']['judgment'], 'fixture': result['checkpoint']['fixture']})
report = {'build': progress['build'], 'meetings': len(checked), 'utterances': sum(r['utterances'] for r in checked), 'checked': checked, 'cameraMismatches': camera_errors, 'verifiedMeetings': len(checked)-len({e['task'] for e in camera_errors}), 'complete': len(checked) == 71 and not camera_errors}
(work/'runtime-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'checked'}))
