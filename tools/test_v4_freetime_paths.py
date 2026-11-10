import json
from copy import deepcopy
from pathlib import Path
from v4_dedicated_spaces import apply_world
from v4_freetime_paths import apply, LINKS

root = Path(__file__).resolve().parents[1]
world = json.loads((root/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf-8'))
apply_world(world)
original = deepcopy(world['connections'])
apply(world)
first = deepcopy(world)
apply(world)
assert first == world
assert world['connections'][:len(original)] == original
visited, pending = {'plaza'}, ['plaza']
while pending:
    here = pending.pop()
    for edge in world['connections']:
        if here not in (edge['a'], edge['b']): continue
        there = edge['b'] if edge['a'] == here else edge['a']
        if there not in visited:
            visited.add(there)
            pending.append(there)
for a, b, pa, pb in LINKS:
    assert a in visited and b in visited
    for room, point in ((a, pa), (b, pb)):
        spec = world['spaces'][world['instances'][room]['space']]
        x0, z0, x1, z1 = spec['bounds']
        assert x0 <= point[0] <= x1 and z0 <= point[2] <= z1, (room, point)
print('PASS: seven dedicated walking links; existing edges preserved; idempotent; bounded endpoints; plaza reachability')
