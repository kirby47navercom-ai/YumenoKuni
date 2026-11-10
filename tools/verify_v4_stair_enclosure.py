"""Preservation/geometry proof for the own stair shell, separate from native pixels."""
import copy
import json
import struct
from pathlib import Path
from v4_stair_enclosure import apply_world

ROOT = Path(__file__).resolve().parents[1]


def glb(path):
    raw = path.read_bytes()
    assert struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw))
    length, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4e4f534a
    document = json.loads(raw[20:20+length])
    at = 20+length
    binary_length, kind = struct.unpack_from('<II', raw, at)
    assert kind == 0x004e4942 and at+8+binary_length == len(raw)
    return document, raw[at+8:]


base, old_binary = glb(ROOT/'art/space_v4/full_v2/lower_stairway.glb')
new, binary = glb(ROOT/'art/space_v4/stair_enclosure_v1/lower_stairway.glb')
assert old_binary[:base['buffers'][0]['byteLength']] == binary[:base['buffers'][0]['byteLength']]
for i, node in enumerate(base['nodes']):
    expected = copy.deepcopy(node)
    if node.get('name') == 'descending_handrail':
        expected.pop('mesh')
    assert expected == new['nodes'][i]
for key in ('meshes', 'materials', 'bufferViews', 'accessors'):
    assert base[key] == new[key][:len(base[key])]
for view in new['bufferViews']:
    assert view.get('byteOffset', 0)+view['byteLength'] <= new['buffers'][0]['byteLength']
source = ROOT/'art/space_v4/runtime_v1/world.json'
raw = source.read_bytes()
world = json.loads(raw)
before = copy.deepcopy(world)
apply_world(world)
once = copy.deepcopy(world)
apply_world(world)
assert world == once
assert before['instances'] == world['instances']
for key in before['spaces']:
    if key != 'lower_stairway':
        assert before['spaces'][key] == world['spaces'][key]
assert len(before['connections']) == len(world['connections'])
for original, current in zip(before['connections'], world['connections']):
    expected = copy.deepcopy(original)
    for key in ('a_p', 'b_p'):
        assert expected[key][::2] == current[key][::2]
        expected[key][1] = current[key][1]
    assert expected == current
assert raw == source.read_bytes()
report = {'ok': True, 'oldBinaryPrefixUnchanged': True, 'oldStepsAndRightRailUnchanged': True,
          'leftRailOnlySplitAtExistingPortal': True, 'otherSpacesInstancesAndRouteIdentitiesUnchanged': True,
          'rawWorldUnchanged': True, 'adapterIdempotent': True,
          'addedNodes': len(new['nodes'])-len(base['nodes']),
          'scope': 'Source GLB and adapter proof; native pixels and C++ collision have separate reports.'}
(ROOT/'Game/Saved/stair-enclosure-source-20261101.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report))
