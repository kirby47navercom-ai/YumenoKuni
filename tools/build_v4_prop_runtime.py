"""Lossless, minimal subsets of our authored GLBs and official import sidecars.

Only art/space_v4/prop_runtime_v1 is written. Source models and engine stay intact.
This deliberately supports the reviewed static, untextured prop primitives only.
Unexpected skin/animation/compression/texture dependencies fail closed.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = 'art/space_v4/prop_runtime_v1'
TOP_CAN = {'can_2_0', 'can_metal_rim.010', 'can_metal_rim.011'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_glb(path):
    raw = Path(path).read_bytes()
    if struct.unpack_from('<4sII', raw) != (b'glTF', 2, len(raw)):
        raise ValueError('Invalid GLB header: ' + str(path))
    chunks = {}; offset = 12
    while offset < len(raw):
        length, kind = struct.unpack_from('<II', raw, offset)
        if length % 4 or kind in chunks or offset + 8 + length > len(raw):
            raise ValueError('Invalid GLB chunks')
        chunks[kind] = raw[offset + 8:offset + 8 + length]
        offset += 8 + length
    return json.loads(chunks[0x4e4f534a]), chunks.get(0x004e4942, b''), raw


def encode_glb(document, binary):
    j = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    j += b' ' * (-len(j) % 4); binary += b'\0' * (-len(binary) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(j) + len(binary))
            + struct.pack('<II', len(j), 0x4e4f534a) + j
            + struct.pack('<II', len(binary), 0x004e4942) + binary)


def subset(document, binary, node_names):
    """Keep source local transforms/ancestor chains and exact accessor bytes."""
    g = document; names = set(node_names)
    if g.get('animations') or g.get('skins') or g.get('extensionsRequired'):
        raise ValueError('Unreviewed animated/compressed model')
    selected = {i for i, n in enumerate(g['nodes']) if n.get('name') in names}
    if len(selected) != len(names):
        raise ValueError('Missing/duplicate selected node names')
    parents = {}
    for i, n in enumerate(g['nodes']):
        for child in n.get('children', []):
            if child in parents: raise ValueError('Multiple node parents')
            parents[child] = i
    keep = set(selected)
    for i in selected:
        while i in parents:
            i = parents[i]; keep.add(i)
    node_ids = sorted(keep); node_map = {old: new for new, old in enumerate(node_ids)}
    mesh_ids = sorted({g['nodes'][i]['mesh'] for i in selected})
    mesh_map = {old: new for new, old in enumerate(mesh_ids)}
    accessor_ids = set(); material_ids = set()
    for i in mesh_ids:
        mesh = g['meshes'][i]
        if set(mesh) - {'name', 'primitives', 'extras'}: raise ValueError('Unreviewed mesh fields')
        for p in mesh['primitives']:
            if set(p) - {'attributes', 'indices', 'material', 'mode', 'extras'}:
                raise ValueError('Unreviewed primitive dependency')
            accessor_ids.update(p['attributes'].values())
            if 'indices' in p: accessor_ids.add(p['indices'])
            if 'material' in p: material_ids.add(p['material'])
    accessor_ids = sorted(accessor_ids); material_ids = sorted(material_ids)
    accessor_map = {old: new for new, old in enumerate(accessor_ids)}
    material_map = {old: new for new, old in enumerate(material_ids)}
    view_ids = set()
    for i in accessor_ids:
        a = g['accessors'][i]
        if 'sparse' in a or 'bufferView' not in a: raise ValueError('Unreviewed sparse accessor')
        view_ids.add(a['bufferView'])
    materials = [deepcopy(g['materials'][i]) for i in material_ids]
    def contains_texture(value):
        if isinstance(value, dict):
            return any('texture' in k.lower() or contains_texture(v) for k, v in value.items())
        return isinstance(value, list) and any(contains_texture(v) for v in value)
    if any(contains_texture(m) for m in materials):
        raise ValueError('Selected prop unexpectedly depends on texture')
    views = []; data = bytearray(); view_ids = sorted(view_ids)
    view_map = {old: new for new, old in enumerate(view_ids)}
    for i in view_ids:
        v = deepcopy(g['bufferViews'][i])
        if v.get('buffer', 0) != 0 or 'extensions' in v: raise ValueError('Unreviewed buffer view')
        start = v.get('byteOffset', 0); end = start + v['byteLength']
        if end > len(binary): raise ValueError('Buffer view out of bounds')
        data.extend(b'\0' * (-len(data) % 4))
        v['buffer'] = 0; v['byteOffset'] = len(data)
        data.extend(binary[start:end]); views.append(v)
    accessors = [deepcopy(g['accessors'][i]) for i in accessor_ids]
    for a in accessors: a['bufferView'] = view_map[a['bufferView']]
    meshes = [deepcopy(g['meshes'][i]) for i in mesh_ids]
    for m in meshes:
        for p in m['primitives']:
            p['attributes'] = {k: accessor_map[v] for k, v in p['attributes'].items()}
            if 'indices' in p: p['indices'] = accessor_map[p['indices']]
            if 'material' in p: p['material'] = material_map[p['material']]
    nodes = []
    for i in node_ids:
        n = deepcopy(g['nodes'][i])
        if 'skin' in n or 'camera' in n or 'extensions' in n: raise ValueError('Unreviewed node dependency')
        if 'children' in n:
            n['children'] = [node_map[j] for j in n['children'] if j in keep]
            if not n['children']: del n['children']
        if i in selected: n['mesh'] = mesh_map[n['mesh']]
        else: n.pop('mesh', None)
        nodes.append(n)
    result = {'asset': deepcopy(g['asset']), 'scene': 0,
              'scenes': [{'name': 'Exact authored prop subset', 'nodes': [node_map[i] for i in node_ids if i not in parents]}],
              'nodes': nodes, 'meshes': meshes, 'materials': materials,
              'accessors': accessors, 'bufferViews': views, 'buffers': [{'byteLength': len(data)}]}
    # Preserve only extensions actually referenced by the selected materials.
    extensions = sorted({k for m in materials for k in m.get('extensions', {})})
    if extensions: result['extensionsUsed'] = extensions
    proof = {'nodeIndices': sorted(selected), 'ancestorIndices': sorted(keep - selected),
             'meshIndices': mesh_ids, 'accessorIndices': accessor_ids,
             'bufferViewIndices': view_ids, 'materialIndices': material_ids,
             'nodeNames': sorted(names)}
    return result, bytes(data), proof


def generate(root=None):
    from v4_prop_states import build as prop_states
    root = Path(root) if root else ROOT; folder = root / OUTPUT
    folder.mkdir(parents=True, exist_ok=True)
    (folder/'actors').mkdir(exist_ok=True); (folder/'base_sidecars').mkdir(exist_ok=True)
    states = prop_states(root); groups = {k: v for k, v in states['catalog'].items() if v['meshNodes']}
    actors = []; sources = {}; copies = []; sidecars = []; total_bytes = 0
    for index, (prop, item) in enumerate(groups.items()):
        basename = Path(item['mesh']).name; src = 'art/space_v4/dedicated_v1/' + basename
        if src not in sources:
            g, binary, raw = read_glb(root/src)
            sources[src] = {'document': g, 'binary': binary, 'sha256': sha(raw),
                            'bytes': len(raw), 'runtimeMesh': item['mesh'], 'hiddenNodes': []}
        source = sources[src]; g = source['document']; source['hiddenNodes'].extend(item['meshNodes'])
        actor = {'id': 'V4PropRuntime' + str(index), 'prop': prop, 'sourceMesh': item['mesh'],
                 'sourceFile': src, 'sourceHash': source['sha256'], 'meshNodes': item['meshNodes'],
                 'defaultVisible': item['defaultVisible'], 'identityPolicy': item['identityPolicy'],
                 'spaces': [sid for sid, mesh in states['spaceMeshes'].items() if mesh == item['mesh']],
                 'coordinateSystem': 'runtime-world-xyz', 'transformPolicy': 'same-origin-as-base-ExploreModel',
                 'localPosition': [0, 0, 0], 'localRotation': [0, 0, 0], 'localScale': [1, 1, 1],
                 'collider': False, 'animationBound': False, 'runtimeVerified': False, 'variants': {}}
        variants = {'full': item['meshNodes']}
        if prop == 'booth.cans': variants['without-top'] = [n for n in item['meshNodes'] if n not in TOP_CAN]
        for variant, names in variants.items():
            short = prop.replace('.', '_') + '_' + variant + '.glb'
            out, data, proof = subset(g, source['binary'], names)
            raw = encode_glb(out, data); rel = OUTPUT + '/actors/' + short
            (root/rel).write_bytes(raw); total_bytes += len(raw)
            dest = 'Assets/Art/explore3d/props/' + short
            copies.append({'from': rel, 'to': dest})
            actor['variants'][variant] = {'mesh': dest, 'file': rel, 'sha256': sha(raw),
                                          'bytes': len(raw), 'visibleNodes': sorted(names), 'proof': proof}
        actor['mesh'] = actor['variants']['full']['mesh']; actors.append(actor)
    for src, record in sources.items():
        g = record['document']; names = set(record['hiddenNodes']); rows = []
        for ni, node in enumerate(g['nodes']):
            if node.get('name') not in names: continue
            mi = node['mesh']
            if sum(n.get('mesh') == mi for n in g['nodes']) != 1:
                raise ValueError('Mesh index is shared with an unselected node')
            rows.append({'id': 'v4prop-mesh-' + str(mi), 'kind': 'mesh',
                         'name': g['meshes'][mi].get('name', ''), 'sourceKey': 'gltf:mesh:' + str(mi),
                         'sourceIndex': mi, 'identity': 'explicit', 'overrides': {'visible': False}})
        if len(rows) != len(names): raise ValueError('Incomplete sidecar selection')
        metadata = {'version': 2, 'source': record['runtimeMesh'], 'sourceHash': record['sha256'],
                    'sourceId': 'v4-authored-' + Path(src).stem, 'name': Path(src).stem,
                    'subassets': sorted(rows, key=lambda r: r['sourceIndex']), 'unresolvedSubassets': []}
        rel = OUTPUT + '/base_sidecars/' + Path(src).name + '.import.json'
        (root/rel).write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        dest = record['runtimeMesh'] + '.import.json'; copies.append({'from': rel, 'to': dest})
        sidecars.append({'file': rel, 'to': dest, 'sourceFile': src,
                         'sourceMesh': record['runtimeMesh'], 'sourceHash': record['sha256'],
                         'hiddenNodeNames': sorted(names), 'hiddenMeshIndices': [r['sourceIndex'] for r in metadata['subassets']],
                         'sha256': sha((root/rel).read_bytes())})
    manifest = {'schemaVersion': 1, 'actors': actors, 'sidecars': sidecars, 'copies': copies,
                'sourceFiles': [{'file': src, 'sha256': r['sha256'], 'bytes': r['bytes']} for src, r in sources.items()],
                'stats': {'actors': len(actors), 'glbs': sum(len(a['variants']) for a in actors),
                          'sidecars': len(sidecars), 'hiddenMeshes': sum(len(s['hiddenMeshIndices']) for s in sidecars),
                          'subsetBytes': total_bytes, 'sourceBytes': sum(r['bytes'] for r in sources.values())},
                'originalModelsChanged': False, 'newPosesAuthored': False, 'runtimeVerified': False,
                'resetPolicy': 'restore seven defaults on scene/source occurrence change; apply actual after-shown prop-state nodeVisibility',
                'unboundPropIds': sorted(k for k,v in states['catalog'].items() if not v['meshNodes'])}
    (folder/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    print(json.dumps(generate()['stats']))
