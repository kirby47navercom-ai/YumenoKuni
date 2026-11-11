"""Remove the shared Korean facility atlas from authored 3D environments.

Work on the selected runtime meshes after the other art publishers finish.
Keep room portraits, evidence materials, collision and gameplay text intact.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from v4_lowpoly_glb import Copier, array, digest, read, write


# Baked clock centers in glTF metres, and corrected wall mount centers. The
# original bezels, dials and hands are already vertical and face the room.
CLOCK_MOUNTS = {
    'hotel_lobby': ((0, 2.60, -5.80), (0, 2.71, -5.886)),
    'central_control': ((0, 2.60, -4.30), (1.53, 2.61, -4.386)),
    'service_lounge': ((-2.50, 2.40, -3.80), (-1.73, 2.53, -3.8535)),
}
SIGN = 'identity_facility_sign'


def add_accessor(doc, blob, values, kind, target, bounds=False):
    offset = len(blob)
    raw = values.tobytes()
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset,
                               'byteLength': len(raw), 'target': target})
    accessor = {'bufferView': len(doc['bufferViews']) - 1,
                'componentType': 5126 if kind == 'VEC3' else 5125,
                'count': len(values), 'type': kind}
    if bounds:
        accessor.update(min=values.min(axis=0).tolist(), max=values.max(axis=0).tolist())
    doc['accessors'].append(accessor)
    return blob + raw, len(doc['accessors']) - 1


def finish(file, mount_clock):
    doc, blob = read(file)
    names = [m.get('name', '') for m in doc.get('materials', [])]
    sign_ids = {i for i, name in enumerate(names) if name.startswith(SIGN)}
    loose_clock = next((n for n in doc.get('nodes', [])
                        if n.get('name')=='set_wall_clock' and 'translation' in n), None)
    if not sign_ids and not mount_clock and not loose_clock:
        return None
    clock = CLOCK_MOUNTS.get(file.stem) if mount_clock else None
    previous = digest(file.read_bytes())
    removed = moved = 0
    loose_moved = False
    if loose_clock and file.stem=='hotel_rest_lounge':
        current = loose_clock['translation']
        if abs(current[2]+5.35)<.001:
            loose_clock['translation'] = [.60, 2.75, -5.394]
            loose_moved = True
    for mesh in doc.get('meshes', []):
        if mesh.get('extras', {}).get('wallClockMountAdjusted'):
            clock = None
        sign_faces = []
        for primitive in mesh['primitives']:
            if primitive.get('material') in sign_ids:
                pos = array(doc, blob, primitive['attributes']['POSITION'])
                indices = array(doc, blob, primitive['indices']).ravel()
                sign_faces.append(pos[indices])
        # Look for the actual backing near each plate. Keeping per-plate
        # bounds avoids deleting iron objects in between separate signs.
        sign_bounds = [(p.min(axis=0)-.08, p.max(axis=0)+.08) for p in sign_faces]
        kept = []
        for primitive in mesh['primitives']:
            material = primitive.get('material')
            if material in sign_ids:
                removed += doc['accessors'][primitive['indices']]['count']//3
                continue
            tag = names[material] if material is not None else ''
            if 'iron' not in tag and not (clock and tag.startswith(('rebuilt_brass','rebuilt_linen'))):
                kept.append(primitive)
                continue
            pos = array(doc, blob, primitive['attributes']['POSITION'])
            indices = array(doc, blob, primitive['indices']).reshape(-1, 3)
            triangles = pos[indices]
            is_clock = np.zeros(len(indices), dtype=bool)
            if clock:
                center, mount = map(np.asarray, clock)
                is_clock = (np.abs(triangles-center)<[.256,.256,.035]).all(axis=(1,2))
            backing = np.zeros(len(indices), dtype=bool)
            if 'iron' in tag:
                for lo, hi in sign_bounds:
                    backing |= ((triangles>=lo)&(triangles<=hi)).all(axis=(1,2))
                backing &= ~is_clock
            if is_clock.any():
                selected = np.unique(indices[is_clock])
                assert not np.intersect1d(selected, indices[~is_clock]).size, file
                adjusted = pos.copy()
                adjusted[selected] += mount-center
                blob, accessor = add_accessor(doc, blob, adjusted, 'VEC3', 34962, bounds=True)
                primitive['attributes']['POSITION'] = accessor
                moved += int(is_clock.sum())
            if backing.any():
                removed += int(backing.sum())
                if backing.all():
                    continue
                blob, primitive['indices'] = add_accessor(
                    doc, blob, indices[~backing].astype('<u4').ravel(), 'SCALAR', 34963)
            kept.append(primitive)
        mesh['primitives'] = kept
        if moved:
            mesh.setdefault('extras', {})['wallClockMountAdjusted'] = True
    if clock:
        assert moved == 480, (file, moved)
    if not removed and not moved and not loose_moved:
        return None
    copier = Copier(doc)
    for i, mesh in enumerate(doc['meshes']):
        assert mesh['primitives'], file
        assert copier.copy(doc, blob, 'meshes', i, file.name) == i
    assert not any(m.get('name', '').startswith(SIGN) for m in copier.j['materials']), file
    output = write(file, copier.j, bytes(copier.b))
    return {'removedTriangles': removed, 'clockTriangles': moved, 'clockNodeMoved': loose_moved,
            'before': previous, 'after': digest(output)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('game', type=Path)
    game = parser.parse_args().game
    art = game/'Assets/Art'
    results = {}
    for folder in ('explore3d', 'park_levels'):
        for file in sorted((art/folder).rglob('*.glb')):
            change = finish(file, folder=='explore3d' and file.parent==art/folder and file.stem in CLOCK_MOUNTS)
            if change:
                results[file.relative_to(game).as_posix()] = change
    print(json.dumps({'models': results, 'count': len(results)}))


if __name__ == '__main__':
    main()
