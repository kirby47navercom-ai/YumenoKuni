"""Reuse already decoded, authorized common HUD cache; never extract/run V3."""
from pathlib import Path
import hashlib
import json
import shutil
import build_v3_armament_layout as resolver

root = Path(__file__).resolve().parents[1]
cache = Path('C:/Users/kirby/Downloads/v3_re/ui_hr_20261105')
bank = root / 'ui/v3_authorized/nonstop_hud'
bank.mkdir(parents=True, exist_ok=True)
names = ['t_cylinder', 't_hr_cylinder', 't_status_base_US', 't_time', 't_speaker_US']
names += [f't_status_{kind}{n}' for n in [5, 7, 10] for kind in ['heart', 'star']]
manifest = {'authorization': 'Previously decoded supplied/authorized cache reuse; user2026-11-06 requests original Nonstop HUD fidelity.', 'textures': [], 'timelines': {}, 'newOriginalExtraction': False}
for name in names:
    folder = bank / name
    folder.mkdir(exist_ok=True)
    metadata = json.loads((cache / 'unpacked' / name / 'srd.json').read_text(encoding='utf8'))
    for index, row in enumerate(metadata['exports']):
        source = Path(row['output'])
        target = folder / source.name
        shutil.copyfile(source, target)
        manifest['textures'].append({'container': name, 'imageIndex': index, 'resource': row['name'], 'file': target.relative_to(root).as_posix(), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'size': [row['width'], row['height']]})
    target = folder / 'animation.json'
    shutil.copyfile(cache / 'sfl' / (name + '.json'), target)
    manifest['timelines'][name] = target.relative_to(root).as_posix()
(bank / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf8')
(bank / 'runtime-layout.json').write_text('{}', encoding='utf8')
resolver.BANK = bank
resolver.ANIMATED_NAMES = {"t_cylinder"}
resolver.build()
layout = json.loads((bank / 'layout.json').read_text(encoding='utf8'))
for name, entry in layout.items():
    rows = entry['states'].get('fl_wait', [])
    print(name, len(rows), [(r['resource'], [round(v, 2) for v in r['rect']]) for r in rows[:4]])
