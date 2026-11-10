"""Verify new trial dialogue placement without replaying completed campaign QA."""
import copy
import json
from pathlib import Path
from build_v4_story import Graph, Source, ROOT
from v4_story_trial1 import compile_first_half


def compile_part(skip=False):
    sources = {p.name: Source(p) for p in (ROOT/'docs/design/rewrite_v4').glob('*.md')}
    tasks = json.loads((ROOT/'data/v4_story/tasks.json').read_text(encoding='utf-8'))
    graph = Graph('1')
    sequence = graph.sequence
    if skip:
        graph.sequence = lambda source, start, end, target: target if source.prefix == '189' else sequence(source, start, end, target)
    graph.entry = compile_first_half(graph, sources, tasks, 'test:next-half')
    return graph, tasks


graph, tasks = compile_part()
before, old_tasks = compile_part(True)
assert tasks == old_tasks  # No new forensic facts, answers, rewards or rules.
added = set(graph.nodes)-set(before.nodes)
assert added and all(graph.nodes[k].get('source', {}).get('file', '').startswith('189_') for k in added)
entry_edges = []
for ident, old in before.nodes.items():
    current = copy.deepcopy(graph.nodes[ident])
    if current != old:
        assert current['next'] in added
        entry_edges.append((ident, current['next'], old['next']))
        current['next'] = old['next']
    assert current == old, ident
assert len(entry_edges) == 1
parent, first, returned = entry_edges[0]
at = first
visited = []
while at != returned:
    assert at in added and at not in visited
    visited.append(at)
    node = graph.nodes[at]
    assert node['type'] in ('say', 'stage')
    assert not any(key in node for key in ('set', 'evidenceId', 'taskId', 'outcomes'))
    at = node['next']
assert set(visited) == added
assert graph.nodes[parent]['source']['file'].startswith('11c1_')
assert 904 <= graph.nodes[parent]['source']['line'] <= 908
assert graph.nodes[returned]['source']['location'] == 'T-08'
says = [graph.nodes[k] for k in visited if graph.nodes[k]['type'] == 'say']
report = {'ok': True, 'newSource': '189', 'newDialogueRows': len(says),
          'newSelectedDialogueCharacters': sum(len(''.join(n['text'].split())) for n in says),
          'previousNodesPreservedExceptOneEntryEdge': len(before.nodes),
          'sameTasksAnswersAndEvidence': True, 'exclusiveEarlierFreetimePathsPreserved': True,
          'entryAfterT07BeforeT08': True, 'newFlagOrSpellUseOrEvidenceGrant': False,
          'nativePlayed': False, 'fiveHoursCertified': False,
          'resume': {'parent': parent, 'entry': first, 'return': returned},
          'scope': 'New notebook confrontation only, all its authored dialogue once; no inferred timing or literary-quality certification.'}
chapter_one = copy.deepcopy(report)
from v4_story_case2 import Router, _trial_middle


def compile_middle(skip=False):
    sources = {p.name: Source(p) for p in (ROOT/'docs/design/rewrite_v4').glob('*.md')}
    tasks = json.loads((ROOT/'data/v4_story/tasks.json').read_text(encoding='utf-8'))['tasks']
    graph = Graph('2')
    graph.taskDefinitions = tasks
    router = Router(graph, sources, {})
    seq, branch = router.seq, router.required_branch
    if skip:
        router.seq = lambda p, a, b, target: target if p == '190' else seq(p, a, b, target)
        router.required_branch = lambda key, flag, cases, p, line: cases[0][1] if key == 'T2-C01:role-aftereffect' else branch(key, flag, cases, p, line)
    graph.entry = _trial_middle(router, tasks, 'test:contact-comparison')
    return graph, tasks


graph, tasks = compile_middle()
before, old_tasks = compile_middle(True)
assert tasks == old_tasks
added = set(graph.nodes)-set(before.nodes)
entry_edges = []
for ident, old in before.nodes.items():
    node = copy.deepcopy(graph.nodes[ident])
    if node != old:
        assert node['next'] in added
        entry_edges.append((ident, node['next'], old['next']))
        node['next'] = old['next']
    assert node == old, ident
assert len(entry_edges) == 1
parent, entry, target = entry_edges[0]
paths = []
for letter in 'ABC':
    at = entry
    visited = []
    while at != target:
        assert at in added and at not in visited
        visited.append(at)
        node = graph.nodes[at]
        assert not node.get('set')
        if node['type'] == 'branch':
            assert {c['flag'] for c in node['cases']} == {'T2-C01'}
            at = next(c['to'] for c in node['cases'] if c['equals'] == letter)
        else:
            assert node['type'] in ('say', 'stage') and node['source']['file'].startswith('190_')
            at = node['next']
    locations = {graph.nodes[k].get('source', {}).get('location') for k in visited}
    assert {loc for loc in locations if loc in ('T2-QA01', 'T2-QB01', 'T2-QC01')} == {'T2-Q'+letter+'01'}
    says = [graph.nodes[k] for k in visited if graph.nodes[k]['type'] == 'say']
    text = '\n'.join(n['text'] for n in says)
    assert ('그 평가를 쓴 건 나라고 했지' in text) == (letter == 'B')
    paths.append({'earlierChoice': letter, 'newDialogueRows': len(says),
                  'newSelectedDialogueCharacters': sum(len(''.join(n['text'].split())) for n in says),
                  'exclusiveEarlierChoiceResponseOnly': True, 'sameReturn': at})
branch_node = next(n for n in graph.nodes.values() if n['type'] == 'branch' and any(c['flag'] == 'T2-C01' for c in n['cases']) and n['id'] not in before.nodes)
assert graph.nodes[branch_node['default']]['type'] == 'gate'
report = {'ok': True, 'chapters': {'1': chapter_one, '2': {
    'newSource': '190', 'paths': paths, 'sameTasksAnswersAndEvidence': True,
    'previousNodesPreservedExceptOneEntryEdge': len(before.nodes),
    'newFlagOrSpellUseOrEvidenceGrant': False, 'missingEarlierChoiceStopsExplicitly': True,
    'resume': {'parent': parent, 'entry': entry, 'return': target}}},
    'nativePlayed': False, 'fiveHoursCertified': False,
    'scope': 'Only the added first/second trial scenes and their exact source order/earlier-choice callbacks. Existing successful campaign tests are not replayed.'}
import v4_story_case3 as case3
sources = {p.name: Source(p) for p in (ROOT/'docs/design/rewrite_v4').glob('*.md')}
freetime = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'data/v4_story/freetime').glob('*.json') if p.stem != 'index'}


def compile_three(skip=False):
    tasks = json.loads((ROOT/'data/v4_story/tasks.json').read_text(encoding='utf-8'))
    actual = case3._trial_ops
    try:
        if skip:
            case3._trial_ops = lambda: [op for op in actual() if not (op[0] == 'span' and op[1] == '191')]
        graph = case3.compile_chapter_three(sources, freetime, tasks)
    finally:
        case3._trial_ops = actual
    return graph, tasks


graph, tasks = compile_three()
before, old_tasks = compile_three(True)
assert tasks == old_tasks
added = set(graph['nodes'])-set(before['nodes'])
edges = []
for ident, old in before['nodes'].items():
    node = copy.deepcopy(graph['nodes'][ident])
    if node != old:
        assert node['next'] in added
        edges.append((ident, node['next'], old['next']))
        node['next'] = old['next']
    assert node == old, ident
assert len(edges) == 1
parent, at, target = edges[0]
seen = []
while at != target:
    assert at in added and at not in seen
    seen.append(at)
    node = graph['nodes'][at]
    assert node['type'] in ('say', 'stage') and node['source']['file'].startswith('191_')
    assert not node.get('set')
    if node.get('authorSpeaker') == '소라':
        assert node['actor'] == node['physicalActor'] == node['voiceActor'] == 'ken'
        assert node['speaker'] == '소라(켄의 몸)'
    if node['type'] == 'say':
        assert node['actor'] not in ('sora', 'riku', 'yuu', 'ai', 'taiga', 'kaede')
    at = node['next']
assert set(seen) == added
says = [graph['nodes'][k] for k in seen if graph['nodes'][k]['type'] == 'say']
report['chapters']['3'] = {'newSource': '191', 'newDialogueRows': len(says),
    'newSelectedDialogueCharacters': sum(len(''.join(n['text'].split())) for n in says),
    'sameTasksAnswersAndEvidence': True, 'sameExistingEvidenceCatalogue': graph['evidenceCatalog'] == before['evidenceCatalog'],
    'previousNodesPreservedExceptOneEntryEdge': len(before['nodes']),
    'controllerRevealedOnlyAtExistingPostIdentityPosition': True, 'physicalPortraitAndVoiceRemainKen': True,
    'newFlagOrSpellUseOrEvidenceGrant': False, 'resume': {'parent': parent, 'entry': edges[0][1], 'return': target}}
report['scope'] = 'Only added first/second/third trial scenes, exact earlier-choice response, physical identity and original returns. Earlier campaign QA is not replayed.'
import v4_story_case4 as case4
import v4_story_case5_trial as case5


def verify_linear(module, chapter, prefix, alive):
    def compile_once(skip):
        tasks = json.loads((ROOT/'data/v4_story/tasks.json').read_text(encoding='utf-8'))
        ops = module._trial_ops
        try:
            if skip:
                module._trial_ops = lambda: [op for op in ops() if not (op[0] == 'span' and op[1] == prefix)]
            if chapter == '4':
                graph = module.compile_chapter_four(sources, freetime, tasks)
            else:
                g = Graph(chapter)
                entry = module.compile_trial_five(g, sources, tasks, 'test:next-result')
                graph = {'nodes': g.nodes, 'entry': entry}
        finally:
            module._trial_ops = ops
        return graph, tasks
    graph, tasks = compile_once(False)
    before, old_tasks = compile_once(True)
    assert tasks == old_tasks
    added = set(graph['nodes'])-set(before['nodes'])
    edges = []
    for ident, old in before['nodes'].items():
        n = copy.deepcopy(graph['nodes'][ident])
        if n != old:
            assert n['next'] in added
            edges.append((ident, n['next'], old['next']))
            n['next'] = old['next']
        assert n == old, ident
    assert len(edges) == 1
    parent, at, target = edges[0]
    seen = []
    while at != target:
        assert at in added and at not in seen
        seen.append(at)
        n = graph['nodes'][at]
        assert n['type'] in ('say', 'stage') and n['source']['file'].startswith(prefix+'_')
        assert not n.get('set')
        if n['type'] == 'say':
            assert n['actor'] in alive
        at = n['next']
    assert set(seen) == added
    says = [graph['nodes'][k] for k in seen if graph['nodes'][k]['type'] == 'say']
    return {'newSource': prefix, 'newDialogueRows': len(says),
        'newSelectedDialogueCharacters': sum(len(''.join(n['text'].split())) for n in says),
        'sameTasksAnswersAndEvidence': True,
        'previousNodesPreservedExceptOneEntryEdge': len(before['nodes']),
        'newFlagOrSpellUseOrEvidenceGrant': False,
        'allCurrentSpeakersAlive': True,
        'resume': {'parent': parent, 'entry': edges[0][1], 'return': target}}


report['chapters']['4'] = verify_linear(case4, '4', '192', {'mio','rei','nana','akari','koto','satsuki','rin','sho'})
report['chapters']['5'] = verify_linear(case5, '5', '193', {'mio','nana','akari','satsuki','rin','sho'})
report['scope'] = 'Only added trial dialogue1–5, exact earlier-choice response, source order, living speakers, physical identity and original returns. Previous full campaign QA is not replayed.'
(ROOT/'Game/Saved/trial-expansion-20261101.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
summary = {'ok': report['ok'], 'chapters': {k: {p:v for p,v in r.items() if p not in ('resume', 'scope')} for k,r in report['chapters'].items()}}
print(json.dumps(summary, ensure_ascii=False))
