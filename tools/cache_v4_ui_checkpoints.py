"""Reuse a real native save at the corrected screen; never synthesize progress."""
import hashlib
import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / 'Game/Saved/v4-flow-1793290936476/chapter-1-savegames.json'
raw = json.loads(source.read_text(encoding='utf-8'))
heads = [json.loads(v) for k, v in raw['items'].items() if 'yumeno-progress-v4.project.' in k]
assert len(heads) == 1
head = heads[0]
assert head['chapter'] == '1' and head['node'] == 'v4:11a:1-01:e:c21e246163dd:1'
destination = root / 'Game/Saved/ui-checkpoints/adv-standing'
destination.mkdir(parents=True, exist_ok=True)
save = destination / 'savegames.json'
shutil.copyfile(source, save)
manifest = {'source': source.as_posix(), 'save': save.as_posix(), 'sha256': hashlib.sha256(save.read_bytes()).hexdigest(), 'chapter': head['chapter'], 'node': head['node'], 'speaker': '하루카', 'fixture': False, 'scope': 'Existing native chapter1 save at this exact ADV line; no synthetic flags, no replay from prologue/chapter entry to reach the screen. Reuse across UI-only builds while the node remains valid.'}
(destination / 'checkpoint.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'ok': True, 'checkpoint': save.as_posix(), 'node': head['node']}, ensure_ascii=False))
