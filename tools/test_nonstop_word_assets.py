"""All authored evidence and transformed names have real, packaged 3D letters."""
import json
import struct
from pathlib import Path

root = Path(__file__).resolve().parents[1]
tasks = json.loads((root / 'data/v4_story/native_tasks.json').read_text(encoding='utf8'))['tasks']
labels = {'거짓 · '}
for task in tasks.values():
    if task['stage']['kind'] != 'nonstop':
        continue
    labels.update(o['name'] for o in task['stage']['options'])
    labels.update(task.get('transformation', {}).get(k, '') for k in ['normalLabel', 'lieLabel'])
assert max(map(len, labels)) <= 48
characters = set(''.join(labels)) - set(' \r\n\t')
qa = root / 'Game/Saved/native-panic-views-1793690486425/package'
manifest = json.loads((qa / 'game.hbpack.json').read_text(encoding='utf8'))
entries = {r['path'] for r in manifest['entries']}
for char in characters:
    relative = f'Assets/Art/nonstop_solid_type/u_{ord(char):x}_w.glb'
    assert relative in entries, (char, 'resource index missing')
    data = (qa / 'Content' / relative).read_bytes()
    assert data[:4] == b'glTF'
    length, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4E4F534A
    gltf = json.loads(data[20:20 + length])
    primitives = gltf['meshes'][0]['primitives']
    assert len(primitives) >= 2, (char, 'front and contour walls required')
    assert all('NORMAL' in p['attributes'] and 'POSITION' in p['attributes'] for p in primitives)
print(f'{len(labels)} evidence/lie names, {len(characters)} closed glyph resources and package entries PASS')
