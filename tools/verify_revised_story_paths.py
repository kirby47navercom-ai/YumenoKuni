#!/usr/bin/env python3
"""Trace two normal V5 campaign paths with authored successful trial inputs.

This verifies the story graph, evidence prerequisites, and carryover choices.
It does not run the game or simulate the minigame timing and input rules.
"""

import json
import argparse
from collections import defaultdict
from itertools import permutations, product
from pathlib import Path
import subprocess
import sys


def trace(campaign, reverse):
    flags, cards = {}, set()
    visited = set()
    spoken_scenes, completed_encounters = set(), set()
    encounters = {item['flag']: item for item in campaign['encounters']}
    chapter = 'P'
    summary = []
    while chapter:
        graph = campaign['chapters'][chapter]
        current = graph['entry']
        nodes = graph['nodes']
        stack, inspected, tried = [], set(), set()
        observations = set()
        task_count = 0
        scored_tasks = set()
        settled_at_vote = False
        for _ in range(30000):
            node = nodes[current]
            observations.add(current)
            visited.add(current)
            kind = node['type']
            scene = node.get('source', {}).get('location')
            if kind == 'say':
                spoken_scenes.add(scene)
            if node.get('growthEncounter'):
                flag, value = next(iter(node['set'].items()))
                assert value and flag not in completed_encounters, flag
                assert encounters[flag]['source']['location'] == scene and scene in spoken_scenes, flag
                completed_encounters.add(flag)
            flags.update(node.get('set', {}))
            if kind == 'end':
                assert node.get('chapterComplete') or node.get('campaignNarrativeEnd'), current
                if chapter not in ('P', '6'):
                    assert settled_at_vote, (chapter, 'result task never reached')
                if chapter == '6':
                    assert node.get('trialResultAtEnd'), 'Final results must follow the ending dialogue'
                for ident, entry in nodes.items():
                    if 'chapterEntryType' in entry:
                        assert ident in observations, (chapter, ident, 'chapter selection entry unreachable')
                summary.append({'chapter': chapter, 'normalEnd': current,
                                'observedNodes': len(observations), 'tasks': task_count})
                chapter = node.get('nextChapter')
                break
            if kind == 'branch':
                current = next((case['to'] for case in node['cases']
                                if flags.get(case['flag'], False) == case['equals']), node['default'])
                continue
            if kind == 'menu':
                signature = current, json.dumps(flags, sort_keys=True)
                options = node['options'][::-1] if reverse else node['options']
                option = next((option for option in options if (signature, option['id']) not in tried
                               and all(flags.get(key, False) == value
                                       for key, value in option.get('requires', {}).items())), None)
                assert option is not None, (chapter, current, signature[1])
                tried.add((signature, option['id']))
                flags.update(option.get('set', {}))
                current = option['to']
                continue
            if kind == 'investigate':
                spot = next((spot for spot in node['spots'] if (current, spot['id']) not in inspected
                             and set(spot.get('requiresCards', [])) <= cards), None)
                if spot:
                    inspected.add((current, spot['id']))
                    stack.append((current, {f"spot:{spot['id']}:complete": True}))
                    current = spot['entry']
                    continue
                assert set(node.get('requiredCards', [])) <= cards, current
                assert all((current, spot) in inspected for spot in node.get('requiredSpotIds', [])), current
            if kind == 'call':
                stack.append((node['returnTo'], node.get('onReturnSet', {})))
                current = node['target']
                continue
            if kind == 'return':
                current, returned = stack.pop()
                flags.update(returned)
                continue
            if kind == 'evidence':
                cards.add(node['evidenceId'])
            if kind == 'task':
                bundle = campaign['tasks'][node['taskId']]
                missing = set(bundle.get('requiresEvidence', [])) - cards
                assert not missing, (node['taskId'], sorted(missing))
                if bundle['stage']['kind'] in ('nonstop', 'showdown', 'reasoning', 'anagram',
                                               'mindmine', 'armament', 'scrum', 'climax', 'panic'):
                    scored_tasks.add(node['taskId'])
                    assert len(scored_tasks) <= 50, (chapter, 'native score/save capacity exceeded')
                if node['taskId'] == graph.get('resultTaskId'):
                    assert bundle['stage']['kind'] == 'vote', 'Results must follow the chapter vote'
                    settled_at_vote = True
                task_count += 1
                current = node.get('success', node.get('next'))
                continue
            current = node['next']
        else:
            raise AssertionError(f'No normal chapter end reached: {chapter}, {current}')
    assert [entry['chapter'] for entry in summary] == ['P', '1', '2', '3', '4', '5', '6']
    if not reverse:
        for ident in ('rev:02-F04:choice', 'rev:02-F05:choice', 'rev:03-F05:choice',
                      'rev:03-F06:choice', 'rev:04-F04:choice', 'rev:05-F06:choice'):
            assert ident in visited, ident
    else:
        for ident in ('rev:02-F04:choice', 'rev:02-F05:choice', 'rev:03-F05:choice',
                      'rev:03-F06:choice', 'rev:04-F04:choice', 'rev:05-F06:choice'):
            assert ident not in visited, ident
    assert flags.get('06:support') in ('held', 'ended')
    if reverse:
        assert not completed_encounters
    else:
        assert 'rev:encounter:01-F02' in completed_encounters
    return {'choiceOrder': 'last-first' if reverse else 'first-last', 'chapters': summary,
            'support': flags['06:support'], 'completedEncounters': len(completed_encounters)}


def validate_encounter_routes(campaign, world):
    levels = world['parkLevels']['minimumChapter']
    instances = world['instances']
    total = 0
    for chapter, graph in campaign['chapters'].items():
        if chapter == 'P':
            continue
        number = int(chapter)
        neighbours = defaultdict(set)
        for edge in world['connections']:
            a, b = edge['a'], edge['b']
            minimum = max(edge.get('minimumChapter', 0), *(
                levels.get(instances[room].get('district', 'residence'), 0) for room in (a, b)))
            if minimum <= number:
                neighbours[a].add(b)
                neighbours[b].add(a)
        for node in graph['nodes'].values():
            if not (start := node.get('explorationStart')):
                continue
            assert start in instances, start
            seen, pending = set(), [start]
            while pending:
                room = pending.pop()
                if room not in seen:
                    seen.add(room)
                    pending.extend(neighbours[room] - seen)
            for option in node['options']:
                if (encounter := option.get('encounter')):
                    assert encounter['space'] in seen, (chapter, start, encounter)
                    total += 1
    return total


def validate_revised_choices(campaign):
    chapters = campaign['chapters']
    prologue = chapters['P']['nodes']
    rules = prologue['rev:P04c:rules']
    options = rules['options'][:-1]
    finish = rules['options'][-1]
    assert len(options) == 3 and finish['id'] == 'continue'
    for order in permutations(options):
        flags = {}
        for option in order:
            assert all(flags.get(key, False) == value for key, value in option['requires'].items())
            assert not all(flags.get(key, False) == value for key, value in finish['requires'].items())
            document = prologue[option['to']]
            assert document['type'] == 'document' and document['next'] == rules['id']
            flags.update(document['set'])
            assert not all(flags.get(key, False) == value for key, value in option['requires'].items())
        assert all(flags.get(key, False) == value for key, value in finish['requires'].items())
    assert prologue['rev:P08:private-note']['private']

    shared_paths = 0
    for scene, common_line in (
        ('05-D02n', '네가 손에 들고 있던 건 봤어.'),
        ('05-D02m', '네가 먼저 갖고 싶다고 해도'),
        ('05-D03h', '아래까지 왔어. 나 이제 들어갈게.'),
        ('06-D03f', '유우 씨. 거기 아까 갖다 주겠다고 한 거요.'),
        ('06-D03g', '다 오셨으니 이제 같이 시작해도 되겠습니까?'),
    ):
        nodes = chapters[str(int(scene[:2]))]['nodes']
        options = nodes[f'rev:{scene}:choice']['options']
        starts = {option['to'] for option in options}
        for option in options:
            current = option['to']
            seen = set()
            lines = []
            while nodes[current].get('source', {}).get('location') == scene:
                assert current not in seen and (current == option['to'] or current not in starts), (scene, option['id'])
                seen.add(current)
                lines.append(nodes[current].get('text', ''))
                current = nodes[current]['next']
            assert sum(line.startswith(common_line) for line in lines) == 1, (scene, option['id'], lines)
            shared_paths += 1

    nodes = chapters['6']['nodes']
    for ident in ('rev:06:overview-bundles', 'rev:06-I03e:observation:0'):
        menu = nodes[ident]
        combined = menu['options'][-1]
        assert combined['id'] == 'continue' and len(combined['requires']) == 3
        for order in permutations(menu['options'][:-1]):
            flags = {}
            for option in order:
                assert not all(flags.get(key, False) == value for key, value in combined['requires'].items())
                current = option['to']
                seen = set()
                while current != ident:
                    assert current != combined['to'] and current not in seen
                    seen.add(current)
                    flags.update(nodes[current].get('set', {}))
                    current = nodes[current]['next']
            assert flags == combined['requires']

    recalls = (('05-D02l', 'stair-bag-memory', 'ABC'), ('05-F06', 'last-sound-memory', 'ABC'),
               ('06-I07d', 'contact-order-memory', 'AB'))
    for flag, name, choices in recalls:
        branch = nodes[f'rev:06:{name}']
        options = chapters[str(int(flag[:2]))]['nodes'][f'rev:{flag}:choice']['options']
        assert [case['equals'] for case in branch['cases']] == list(choices)
        assert [option['set'][flag] for option in options] == list(choices)
        for case in branch['cases']:
            assert case['flag'] == flag
            current = case['to']
            seen = set()
            while current != branch['default']:
                assert current not in seen and current.startswith(case['to'])
                seen.add(current)
                current = nodes[current]['next']

    contact = nodes['rev:06:unsent-contact-check']
    for option in contact['options']:
        assert (nodes[option['to']]['next'] == contact['id']) == (option['id'] != 'C')

    opening = campaign['tasks']['T1-NS-REV00']
    statements = opening['stage']['lines']
    assert len(statements) == 6 and statements[3]['weak']['answer'] == 'v4:E1-SIGHT'
    assert opening['stage']['authoredAmmo'] == ['v4:E1-SIGHT', 'v4:E1-07', 'v4:E1-04']
    assert set(opening['stage']['wrongCards'].values()) == {
        variant['cause'] for variant in opening['queues']['wrongVariants']}
    return {'sharedChoicePaths': shared_paths, 'ruleReadingOrders': 6, 'archiveReadingOrders': 6,
            'sideDoorObservationOrders': 6, 'recallBranches': len(recalls)}


def validate_investigation_and_ending(campaign):
    nodes = campaign['chapters']['6']['nodes']
    gates = ('01-T04a:perjury', '06-T02f:perjury')
    first = nodes['rev:06:ending-perjury:first']
    final = nodes['rev:06:ending-perjury:final']
    assert [first['cases'][0]['flag'], final['cases'][0]['flag']] == list(gates)
    for used in product((False, True), repeat=2):
        state = dict(zip(gates, used, strict=True))
        current = first['id']
        visited = set()
        while current != 'rev:06:complete':
            assert current not in visited
            visited.add(current)
            node = nodes[current]
            if node['type']=='branch':
                current = next((row['to'] for row in node['cases'] if state.get(row['flag'])==row['equals']),
                               node['default'])
            else:
                current = node['next']
        for gate, authored in zip((first, final), used, strict=True):
            assert (gate['cases'][0]['to'] in visited)==authored
            assert (gate['default'] in visited)!=authored

    # Check that all of the new prompts gate their spot's actual evidence, including both wrong routes.
    checked = set()
    for spot in nodes['rev:06:investigate']['spots']:
        current = spot['entry']
        visited = set()
        while current not in visited:
            visited.add(current)
            node = nodes[current]
            if node.get('evidenceId')==spot['id']:
                break
            if node['type']=='menu' and ':check:' in current:
                responses = [nodes[option['to']] for option in node['options']]
                retry = [answer for answer in responses if answer['next']==current]
                assert len(retry)==2 and retry[0]['text']!=retry[1]['text']
                current, = (answer['next'] for answer in responses if answer['next']!=current)
                checked.add(node['id'])
            elif 'next' in node:
                current = node['next']
            elif node['type']=='menu':
                finish = [option for option in node['options'] if option['id'] in ('continue','finish')]
                current = (finish or node['options'])[0]['to']
            else:
                break
    expected = {node['id'] for node in nodes.values() if node['type']=='menu' and ':check:' in node['id']}
    assert checked==expected and len(checked)==11, sorted(expected-checked)
    tasks = campaign['tasks']
    assert len(tasks['T4-PN-REV03']['debate']['lanes'])==3
    assert len(tasks['T4-PN-REV03']['debate']['lines'])==22
    assert len(tasks['T5-NS-REV15']['stage']['lines'])==13
    for number in range(9, 15):
        ident = f'T6-QA-REV{number:02}'
        task = tasks[ident]
        stage = task['stage']
        replies = task['queues']['wrongVariants']
        assert {reply['optionIndex'] for reply in replies} == set(range(3)) - {stage['answer']}
        assert len({reply['script'][0]['text'] for reply in replies}) == 2
    for number in (9, 10):
        assert nodes[f'rev:06:T6-QA-REV{number:02}']['success'] == f'rev:06:T6-QA-REV{number+1:02}'
    menu = nodes['rev:06:operating-decisions']
    finish = menu['options'][-1]
    for order in permutations(menu['options'][:3]):
        flags = {}
        for option in order:
            assert flags != finish['requires']
            assert all(flags.get(key, False) == value for key, value in option['requires'].items())
            done = nodes[nodes[option['to']]['success']]
            assert done['next'] == menu['id']
            flags.update(done['set'])
            assert not all(flags.get(key, False) == value for key, value in option['requires'].items())
        assert flags == finish['requires']
    fifth = campaign['chapters']['5']['nodes']
    reader = fifth['rev:05:reading-order-memory']
    assert [option['set']['05-I05d'] for option in fifth['rev:05-I05d:observation:0']['options']]==list('ABC')
    assert [fifth[case['to']]['actor'] for case in reader['cases']]==['sho','nana','satsuki']
    assert all(fifth[case['to']]['next']==reader['default'] for case in reader['cases'])
    meeting = campaign['chapters']['2']['nodes']['rev:02-F06:first-visit-memory']
    assert [case['equals'] for case in meeting['cases']]==list('ABC')
    assert meeting['default'].endswith(':new')
    second = campaign['chapters']['2']['nodes']
    bowl = second['rev:02-F05:previous-bowl']
    for case in bowl['cases']:
        current = case['to']
        for _ in range(3):
            current = second[current]['next']
        assert current==bowl['default']
    assert [case['equals'] for case in bowl['cases']]==list('AB')
    closing = second['rev:02-F05:closing-activity']
    assert closing['cases']==[{'flag':'02-F05','equals':'B','to':'rev:02-F05:book-end:0'}]
    assert second['rev:02-F05:book-end:2']['next']=='rev:02-F05:complete'
    third = campaign['chapters']['3']['nodes']
    audience = third['rev:03-F02:audience-memory']
    assert [(case['flag'],case['equals']) for case in audience['cases']]==[('02-F08','A'),('02-F08','B')]
    assert all(third[case['to']]['next']==audience['default'] for case in audience['cases'])
    fourth = campaign['chapters']['4']['nodes']
    bench = fourth['rev:04-D00j:bench-memory']
    a,b = (fourth[case['to']] for case in bench['cases'])
    assert [(case['flag'],case['equals']) for case in bench['cases']]==[('04-F02','A'),('04-F02','B')]
    assert a['next']==fourth[b['next']]['next']==bench['default']
    assert (a['actor'],b['actor'],fourth[b['next']]['actor'])==('rei','mio','rei')
    for ident, letter in (
        ('T2-NS-REV15','뒤'),('T5-NS-REV09','같'),('T5-NS-REV10','더'),('T5-NS-REV11','경'),
        ('T6-NS-REV17','접'),('T6-NS-REV13','안'),('T6-NS-REV14','해'),
    ):
        row, = (row for row in tasks[ident]['stage']['lines'] if 'vpoint' in row)
        assert row['text'][row['vpoint']['glyphIndex']]==letter
    return {'endingHistoryCombinations':4,'sixthChapterEvidenceChecks':len(checked),
            'sixthChapterHearingChecks':6,'operatingDecisionOrders':6,'restoredVpoints':7}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world', type=Path, help='Also validate walking paths using the packaged exploration catalog')
    args = parser.parse_args()
    source = Path(__file__).with_name('build_revised_campaign.py')
    campaign = json.loads(subprocess.check_output([sys.executable, '-X', 'utf8', str(source)]))
    for reverse in (False, True):
        print(json.dumps(trace(campaign, reverse), ensure_ascii=False))
    print(json.dumps(validate_revised_choices(campaign)))
    print(json.dumps(validate_investigation_and_ending(campaign)))
    if args.world:
        world = json.loads(args.world.read_text(encoding='utf-8'))
        print(json.dumps({'reachableFreeTimeEncounters': validate_encounter_routes(campaign, world)}))
