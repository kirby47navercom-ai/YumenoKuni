"""Check the actual new graph routes and preserve every pre-existing node."""
import json
import itertools
from pathlib import Path
import v4_story_case6_extension as extension
from build_v4_story import Source, ROOT, load
from v4_story_case6 import compile_chapter_six

sources = {p.name: Source(p) for p in (ROOT / 'docs/design/rewrite_v4').glob('*.md')}
freetime = {p.stem: load(p) for p in (ROOT / 'data/v4_story/freetime').glob('*.json') if p.stem != 'index'}
tasks = load(ROOT / 'data/v4_story/tasks.json')
graph = compile_chapter_six(sources, freetime, tasks)
original = extension.compile_arrival
try:
    extension.compile_arrival = lambda r, after: after
    prior = compile_chapter_six(sources, freetime, tasks)
finally:
    extension.compile_arrival = original
for key, node in prior['nodes'].items():
    assert graph['nodes'][key] == node, key
reports = []
for corridor_choice, choice in itertools.product('ABC', repeat=2):
    at, flags, nodes = graph['entry'], {}, []
    while at != prior['entry']:
        node = graph['nodes'][at]
        nodes.append(node)
        assert node['type'] in ('say', 'stage', 'menu', 'branch')
        if node['type'] != 'branch':
            assert node['source']['file'].startswith(('187_', '188_'))
        if node['type'] == 'menu':
            assert node['selectionRole'] in ('shared-arrival-boundaries', 'current-corridor-speaking-boundary')
            selected = next(o for o in node['options'] if o['id'] == (corridor_choice if node['selectionRole'] == 'current-corridor-speaking-boundary' else choice))
            flags.update(selected['set'])
            at = selected['to']
        elif node['type'] == 'branch':
            at = next((row['to'] for row in node['cases'] if flags.get(row['flag']) == row['equals']), node['default'])
        else:
            at = node['next']
        assert len(nodes) < 1000
    locations = {n.get('source', {}).get('location', '') for n in nodes}
    assert {'6-L01', '6-L02', '6-L03', '6-L04', '6-L06'}.issubset(locations)
    assert {loc for loc in locations if loc.startswith('6-LR01')} == {'6-LR01' + choice}
    expected = {'A': '6-LA01', 'B': '6-LB01', 'C': '6-LC01C'}[choice]
    assert {loc for loc in locations if loc in ('6-LA01', '6-LB01', '6-LC01C')} == {expected}
    assert {loc for loc in locations if loc.startswith('6-DR01')} == {'6-DR01' + corridor_choice}
    assert {loc for loc in locations if loc in ('6-DA01', '6-DB01', '6-DC01C')} == {{'A': '6-DA01', 'B': '6-DB01', 'C': '6-DC01C'}[corridor_choice]}
    assert flags == {'6-LC01': choice, '6-DC01': corridor_choice}
    says = [n for n in nodes if n['type'] == 'say']
    assert {n['actor'] for n in says} == {'mio', 'rin', 'nana', 'sho', 'satsuki'}
    reports.append({'corridorChoice': corridor_choice, 'choice': choice, 'nodes': len(nodes), 'dialogueRows': len(says),
                    'dialogueCharacters': sum(len(''.join(n['text'].split())) for n in says),
                    'ownResponseOnly': True, 'ownDelayedCallbackOnly': True,
                    'sameOriginalEntry': at, 'flagsChanged': flags})
report = {'ok': True, 'paths': reports, 'allPreviousNodesPreserved': len(prior['nodes']),
          'newTaskOrEvidenceOrAbilityOrSupportFlag': False, 'nativePlayed': False,
          'scope': 'Actual compiled extension paths A/B/C with exact response and callback, no exclusive alternatives concatenated. Existing graph nodes, end flags, tasks and evidence unchanged. No playtime or literary-quality certificate.'}
destination = ROOT / 'Game/Saved/story-extension-6-arrival-20261101.json'
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
