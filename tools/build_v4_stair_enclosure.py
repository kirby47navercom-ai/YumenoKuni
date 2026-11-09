"""Add an original stairwell shell to the existing own stair GLB, without Blender/engine mutation."""
from pathlib import Path
import hashlib
import json
import struct
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art/space_v4/stair_enclosure_v1'
BASE = ROOT / 'art/space_v4/full_v2/lower_stairway.glb'


def main():
    source = BASE.read_bytes()
    magic, version, size = struct.unpack_from('<III', source)
    assert magic == 0x46546c67 and version == 2 and size == len(source)
    at, document, binary = 12, None, b''
    while at < len(source):
        length, kind = struct.unpack_from('<II', source, at)
        data = source[at + 8:at + 8 + length]
        if kind == 0x4e4f534a:
            document = json.loads(data)
        elif kind == 0x004e4942:
            binary = data
        at += 8 + length
    assert document and len(document['buffers']) == 1 and not document['buffers'][0].get('uri')
    data = bytearray(binary[:document['buffers'][0]['byteLength']])
    faces = [
        ((1,0,0),[(.5,-.5,-.5),(.5,.5,-.5),(.5,.5,.5),(.5,-.5,.5)]),
        ((-1,0,0),[(-.5,-.5,.5),(-.5,.5,.5),(-.5,.5,-.5),(-.5,-.5,-.5)]),
        ((0,1,0),[(-.5,.5,-.5),(-.5,.5,.5),(.5,.5,.5),(.5,.5,-.5)]),
        ((0,-1,0),[(-.5,-.5,.5),(-.5,-.5,-.5),(.5,-.5,-.5),(.5,-.5,.5)]),
        ((0,0,1),[(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]),
        ((0,0,-1),[(.5,-.5,-.5),(-.5,-.5,-.5),(-.5,.5,-.5),(.5,.5,-.5)]),
    ]
    positions, normals, indices = [], [], []
    for normal, vertices in faces:
        first = len(positions) // 3
        for vertex in vertices:
            positions.extend(vertex)
            normals.extend(normal)
        indices.extend(first + i for i in (0,1,2,0,2,3))

    def accessor(values, component, count, kind, **bounds):
        data.extend(b'\0' * (-len(data) % 4))
        offset = len(data)
        data.extend(struct.pack('<' + ('f' if component == 5126 else 'H') * len(values), *values))
        view = len(document.setdefault('bufferViews', []))
        document['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(data)-offset})
        index = len(document.setdefault('accessors', []))
        document['accessors'].append({'bufferView': view, 'componentType': component, 'count': count, 'type': kind, **bounds})
        return index

    position = accessor(positions, 5126, 24, 'VEC3', min=[-.5]*3, max=[.5]*3)
    normal = accessor(normals, 5126, 24, 'VEC3')
    index = accessor(indices, 5123, 36, 'SCALAR')
    meshes = {}
    palette = {'wall': [.56,.53,.61,1], 'ink': [.045,.035,.09,1], 'gold': [.48,.36,.16,1],
               'floor': [.36,.34,.4,1], 'light': [.83,.78,.59,1]}
    for name, color in palette.items():
        material = len(document.setdefault('materials', []))
        record = {'name': 'yk_stair_' + name, 'pbrMetallicRoughness': {'baseColorFactor': color,
                  'metallicFactor': .35 if name == 'gold' else 0, 'roughnessFactor': .8}}
        if name == 'light':
            record['emissiveFactor'] = [.55,.5,.3]
        document['materials'].append(record)
        meshes[name] = len(document.setdefault('meshes', []))
        document['meshes'].append({'name': 'stair-shell-unit-' + name,
                                   'primitives': [{'attributes': {'POSITION': position, 'NORMAL': normal},
                                                   'indices': index, 'material': material}]})
    added, collision, surfaces = [], [], []
    # The old left rail crossed the already-authored workshop opening.
    left_rail = next(node for node in document['nodes'] if node.get('name') == 'descending_handrail')
    left_rail.pop('mesh')

    def box(name, center, extent, color, solid=False, walk=None):
        node = len(document['nodes'])
        document['nodes'].append({'name': name, 'mesh': meshes[color], 'translation': center, 'scale': extent})
        document['scenes'][document.get('scene', 0)].setdefault('nodes', []).append(node)
        low = [c-s/2 for c,s in zip(center, extent)]
        high = [c+s/2 for c,s in zip(center, extent)]
        added.append({'id': name, 'p': center, 'box': [low, high]})
        if solid:
            collision.append([low[0],low[2],high[0],high[2],low[1],high[1]])
        if walk is not None:
            surfaces.append([low[0],low[2],high[0],high[2],walk])

    for side in (-1,1):
        if side == -1:
            # Preserve the existing workshop portal beside the middle of the flight.
            for z in (-3.3,3.3):
                box('stairwell_side_-1_' + str(z), [-1.94,-1.3,z], [.16,8.8,5.4], 'wall', True)
            box('stairwell_workshop_lintel', [-1.94,1.3,0], [.16,3.6,1.2], 'wall', True)
            box('stairwell_workshop_threshold', [-1.36,-2.96,0], [1,.16,1.2], 'floor', walk=-2.88)
        else:
            box('stairwell_side_' + str(side), [side*1.94,-1.3,0], [.16,8.8,12], 'wall', True)
        for z in (-4,-1,2,5):
            floor = min(0, max(-5.76, (z-4.5)*.18/.28))
            box('stairwell_lamp_' + str(side) + '_' + str(z), [side*1.835,floor+2.05,z], [.035,.45,.18], 'light')
            box('stairwell_lamp_frame_' + str(side) + '_' + str(z), [side*1.86,floor+2.05,z], [.055,.53,.26], 'ink')
        for z in (-3,0,3):
            box('stairwell_upper_panel_' + str(side) + '_' + str(z), [side*1.844,1.15,z], [.025,1.25,2.4], 'ink')
            box('stairwell_upper_light_' + str(side) + '_' + str(z), [side*1.817,1.84,z], [.035,.075,1.15], 'light')
    box('stairwell_ceiling', [0,3.18,0], [4,.16,12], 'ink')
    box('stairwell_lower_end', [0,-1.3,-5.94], [4,8.8,.16], 'wall', True)
    box('stairwell_upper_landing', [0,-.08,5.18], [3.72,.16,1.64], 'floor', walk=0)
    box('stairwell_lower_landing', [0,-5.84,-5.1], [3.72,.16,1.64], 'floor', walk=-5.76)
    # Frame the far landing. This visual doorway does not add a new usable route.
    box('stairwell_lower_door', [0,-4.59,-5.845], [1.2,2.3,.025], 'ink')
    for x in (-.65,.65):
        box('stairwell_lower_door_frame_' + str(x), [x,-4.56,-5.81], [.07,2.43,.07], 'gold')
    box('stairwell_lower_door_lintel', [0,-3.34,-5.81], [1.37,.07,.07], 'gold')
    box('stairwell_upper_table', [1.32,.78,5.05], [.74,.09,.64], 'ink', True)
    for low, high in [(-4.1989,-.6),(.6,4.5189)]:
        z=(low+high)/2
        box('stairwell_left_rail_'+str(low), [-1,(z-4.5)*.18/.28+.9,z],
            [.07,.07,math.hypot(high-low,(high-low)*.18/.28)], 'gold')
        angle=-math.atan(.18/.28)
        document['nodes'][-1]['rotation']=[math.sin(angle/2),0,0,math.cos(angle/2)]
        added[-1]['box']=[[-1.035,(low-4.5)*.18/.28+.865,low],[-.965,(high-4.5)*.18/.28+.935,high]]
    for x in (1.04,1.6):
        for z in (4.82,5.28):
            box('stairwell_table_leg_' + str(x) + '_' + str(z), [x,.36,z], [.045,.72,.045], 'gold', True)
    # The original rail prevents stepping into the unsupported side of the flight.
    # Keep that whole region blocked rather than allowing fallback-floor air walking.
    collision += [[.92,-4.3,1.86,4.34,-6,3], [-1.86,-4.3,-.92,-.6,-6,3],
                  [-1.86,.6,-.92,4.34,-6,3]]
    document['buffers'][0]['byteLength'] = len(data)
    raw_json = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    raw_json += b' ' * (-len(raw_json) % 4)
    data.extend(b'\0' * (-len(data) % 4))
    output = struct.pack('<III', magic, version, 12+8+len(raw_json)+8+len(data))
    output += struct.pack('<II', len(raw_json), 0x4e4f534a) + raw_json
    output += struct.pack('<II', len(data), 0x004e4942) + data
    OUT.mkdir(parents=True, exist_ok=True)
    file = OUT / 'lower_stairway.glb'
    file.write_bytes(output)
    manifest = {'version': 1, 'builder': Path(__file__).relative_to(ROOT).as_posix(),
                'builderSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'source': BASE.relative_to(ROOT).as_posix(), 'sourceSHA256': hashlib.sha256(source).hexdigest(),
                'file': file.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(output).hexdigest(),
                'addedNodes': added, 'collision': collision, 'walk_surfaces': surfaces, 'spawn': [0,1.6,5.25],
                'entryPitch': -28, 'pitchLimits': [-50,35],
                'portalPositions': {'maintenance_workshop__lower_stairway': {'b_p': [-1.78,-1.68,0]},
                                    'lower_stairway__lower_corridor': {'a_p': [0,-4.56,-5.78]}},
                'originalStairStepsAndRightRailPreserved': True, 'leftRailSplitAtExistingPortal': True, 'storyConnectionsAdded': 0,
                'scope': 'Own enclosed stairwell/landings and upper table around existing own descending steps. Visual lower door is existing-route dressing, no new clue/unlock/access.'}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'addedNodes': len(added), 'baseBytes': len(source), 'newBytes': len(output)}))


if __name__ == '__main__':
    main()
