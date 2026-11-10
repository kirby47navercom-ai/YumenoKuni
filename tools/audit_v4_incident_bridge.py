"""Read-only content audit of discovery -> investigation -> trial boundaries.

This does not run the game, change a graph, or certify camera/audio playback.
In particular a production asset and a script action are not a displayed shot.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/analysis/v3_rebuild/사건_수사_재판_연결_20261103.json'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shots_at(node, bindings):
    source = node.get('source', {})
    return [r for r in bindings.get('cgRanges', [])
            if source.get('file') == r['source']['file']
            and r['startLine'] <= source.get('line', 0) < r['endLineExclusive']]


def automatic_chain(node, nodes, bindings):
    """Only literal stage.next edges: do not invent branch/call state."""
    result, visited = [], set()
    while node and node['id'] not in visited:
        visited.add(node['id'])
        result.append({'id': node['id'], 'type': node['type'],
                       'shots': [r['logical_id'] for r in shots_at(node, bindings)]})
        if node['type'] != 'stage' or node.get('showRecord'):
            break
        node = nodes.get(node.get('next'))
    return result


def audit(root=ROOT):
    binding_path = root / 'data/presentation/v4_scenes.json'
    bindings = read(binding_path)
    selected_path = root / 'art/v4_production/forensic_repair/selected.json'
    selected = read(selected_path)['overrides']
    output = {'status': 'source-audit-not-runtime-acceptance',
              'scope': 'Current authored discovery, physical inspection gates and trial approach. The findings inspect cgRanges before publisher overrides; consult sourceCookOverrideProof separately. No original-V3 completeness claim.',
              'sourceCookOverrideProof': 'docs/analysis/v3_rebuild/사건_CG_연결_소스검증_20261103.json',
              'inputs': {str(p.relative_to(root)).replace('\\', '/'): fingerprint(p)
                         for p in [binding_path, selected_path]},
              'chapters': [], 'findings': [],
              'runtimeAcceptanceComplete': False}
    for path in sorted((root / 'data/v4_story/chapters').glob('[1-6].json')):
        graph = read(path)
        output['inputs'][str(path.relative_to(root)).replace('\\', '/')] = fingerprint(path)
        nodes = graph['nodes']
        chapter = {'chapter': path.stem, 'discoveries': [], 'investigationHubs': [],
                   'evidenceNodes': [], 'trialApproachSections': []}
        for node in nodes.values():
            actions = node.get('presentation', {}).get('actions', [])
            if 'body_reveal' in actions:
                chain = automatic_chain(node, nodes, bindings)
                row = {'node': node['id'], 'source': node.get('source'),
                       'actions': actions, 'automaticChain': chain,
                       'hasBoundFullFrameShot': any(r['shots'] for r in chain),
                       'runtimeVerified': False}
                chapter['discoveries'].append(row)
                if not row['hasBoundFullFrameShot']:
                    output['findings'].append({'kind': 'discovery-without-bound-shot',
                                              'chapter': path.stem, 'node': node['id'],
                                              'meaning': 'The reveal action and immediately following held node have no cgRanges shot; this does not prove that every possible world renderer is blank.'})
            if node['type'] == 'investigate':
                spots = node.get('spots', [])
                required = set(node.get('requiredSpotIds', []))
                row = {'node': node['id'], 'next': node.get('next'),
                       'requiredSpotIds': sorted(required),
                       'requiredCards': node.get('requiredCards', []),
                       'spots': [], 'runtimeVerified': False}
                for spot in spots:
                    positioned = bool(spot.get('world_pos') or spot.get('target_id'))
                    row['spots'].append({'id': spot['id'], 'space': spot.get('space_id'),
                                         'entryExists': spot.get('entry') in nodes,
                                         'hasWorldBinding': positioned,
                                         'required': spot['id'] in required,
                                         'interviewActors': spot.get('interviewActors', []),
                                         'objectMeshMatched': spot.get('objectMeshMatched', False)})
                    if spot.get('entry') not in nodes or not positioned:
                        output['findings'].append({'kind': 'inspection-binding-gap',
                                                  'chapter': path.stem, 'node': node['id'],
                                                  'spot': spot['id']})
                if not required and not row['requiredCards']:
                    output['findings'].append({'kind': 'hub-without-completion-gate',
                                              'chapter': path.stem, 'node': node['id']})
                chapter['investigationHubs'].append(row)
            if node['type'] == 'evidence':
                chapter['evidenceNodes'].append({'node': node['id'],
                                                'evidenceId': node.get('evidenceId'),
                                                'revision': node.get('revision', False)})
            source = node.get('source', {})
            section = source.get('file', '') + ':' + source.get('location', '')
            binding = bindings.get('sections', {}).get(section, {})
            if binding.get('space') in ['trial_elevator', 'trial_entrance']:
                if section not in chapter['trialApproachSections']:
                    chapter['trialApproachSections'].append(section)
        output['chapters'].append(chapter)
    output['selectedIncidentArt'] = [
        {'logicalId': key, 'image': value['delivery'],
         'exists': (root / value['delivery']).is_file(),
         'boundByCgRanges': any(r.get('image', '').replace('\\', '/') == value['delivery'].replace('\\', '/')
                               for r in bindings.get('cgRanges', []))}
        for key, value in selected.items()]
    output['summary'] = {
        'discoveryEvents': sum(len(c['discoveries']) for c in output['chapters']),
        'discoveriesWithoutBoundShot': sum(f['kind'] == 'discovery-without-bound-shot' for f in output['findings']),
        'investigationHubs': sum(len(c['investigationHubs']) for c in output['chapters']),
        'evidenceNodes': sum(len(c['evidenceNodes']) for c in output['chapters']),
        'inspectionBindingGaps': sum(f['kind'] == 'inspection-binding-gap' for f in output['findings']),
        'unguardedHubs': sum(f['kind'] == 'hub-without-completion-gate' for f in output['findings'])}
    return output


if __name__ == '__main__':
    result = audit()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['summary'], ensure_ascii=False))
