"""Checked source-owned stair shell; leaves story routes and original world catalogue intact."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def apply_world(world):
    folder = ROOT / 'art/space_v4/stair_enclosure_v1'
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    for path_key, hash_key in [('builder','builderSha256'), ('source','sourceSHA256'), ('file','sha256')]:
        assert hashlib.sha256((ROOT / manifest[path_key]).read_bytes()).hexdigest() == manifest[hash_key]
    spec = world['spaces']['lower_stairway']
    if spec.get('enclosedStairShell'):
        assert spec['stairShellSHA256'] == manifest['sha256']
        return [{'from': manifest['file'], 'to': spec['mesh']}]
    spec['spawn'] = manifest['spawn']
    spec['entry_pitch'] = manifest['entryPitch']
    spec['pitch_limits'] = manifest['pitchLimits']
    # Split only the existing left handrail blocker at the authored side door.
    old = next(c for c in spec['collision'] if c[0] < -1 and c[2] < 0 and c[1] < -4 and c[3] > 4)
    spec['collision'].remove(old)
    spec['collision'] += [old[:3]+[-.6]+old[4:], [old[0],.6]+old[2:]]
    spec['walk_surfaces'] += manifest['walk_surfaces']
    spec['collision'] += manifest['collision']
    spec['nodes'] += manifest['addedNodes']
    spec['enclosedStairShell'] = True
    spec['stairShellSHA256'] = manifest['sha256']
    for link in world['connections']:
        for key, position in manifest['portalPositions'].get(link['id'], {}).items():
            # Only the Y coordinate changes, to match each existing landing floor.
            assert link[key][0] == position[0] and link[key][2] == position[2]
            link[key] = position
    return [{'from': manifest['file'], 'to': spec['mesh']}]
