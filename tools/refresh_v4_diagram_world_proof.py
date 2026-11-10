"""Re-render into an isolated QA folder; refresh a world hash only for identical diagrams."""
from pathlib import Path
import copy
import hashlib
import importlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'Game/Saved/diagram-world-proof-20261101'
WORK.mkdir(parents=True, exist_ok=True)
rows = []
for module_name in ('make_v4_case1_documents', 'make_v4_investigation_diagrams'):
    module = importlib.import_module(module_name)
    original_out = module.OUT
    prior = json.loads((original_out / 'manifest.json').read_text(encoding='utf-8'))
    module.OUT = WORK / module_name
    module.OUT.mkdir(parents=True, exist_ok=True)
    module.make()
    newer = json.loads((module.OUT / 'manifest.json').read_text(encoding='utf-8'))
    identical = []
    for candidate in module.OUT.iterdir():
        if candidate.suffix not in ('.svg', '.webp'):
            continue
        old = original_out / candidate.name
        assert old.is_file(), candidate.name
        assert old.read_bytes() == candidate.read_bytes(), 'Projection changed: ' + candidate.name
        identical.append({'file': old.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(old.read_bytes()).hexdigest()})
    def normalized(value):
        if isinstance(value, str):
            return value.replace(module.OUT.relative_to(ROOT).as_posix(), original_out.relative_to(ROOT).as_posix())
        if isinstance(value, list):
            return [normalized(v) for v in value]
        if isinstance(value, dict):
            return {k: normalized(v) for k, v in value.items() if k not in ('worldSha256',)}
        return value
    assert normalized(prior) == normalized(newer), 'Semantic picture contract changed: ' + module_name
    if '--apply' in sys.argv:
        updated = copy.deepcopy(prior)
        if 'accessPlan' in updated:
            updated['accessPlan']['worldSha256'] = newer['accessPlan']['worldSha256']
        else:
            updated['worldSha256'] = newer['worldSha256']
        (original_out / 'manifest.json').write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    rows.append({'generator': module_name, 'identicalImages': identical, 'semanticContractUnchanged': True})
report = {'ok': True, 'applied': '--apply' in sys.argv, 'rows': rows,
          'scope': 'Current room projection regenerated in isolation and byte-compared with existing SVG/WebP; all source/region/answer contracts identical. Only unrelated whole-world hash may refresh. No original asset extraction, raw image replacement or native replay.'}
(WORK / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'ok': True, 'applied': report['applied'], 'identicalFiles': sum(len(r['identicalImages']) for r in rows)}))
