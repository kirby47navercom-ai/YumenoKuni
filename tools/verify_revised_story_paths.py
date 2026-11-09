#!/usr/bin/env python3
"""Trace two normal V5 campaign paths with authored successful trial inputs.

This verifies the story graph, evidence prerequisites, and carryover choices.
It does not run the game or simulate the minigame timing and input rules.
"""

import json
import argparse
from collections import defaultdict
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world', type=Path, help='Also validate walking paths using the packaged exploration catalog')
    args = parser.parse_args()
    source = Path(__file__).with_name('build_revised_campaign.py')
    campaign = json.loads(subprocess.check_output([sys.executable, '-X', 'utf8', str(source)]))
    for reverse in (False, True):
        print(json.dumps(trace(campaign, reverse), ensure_ascii=False))
    if args.world:
        world = json.loads(args.world.read_text(encoding='utf-8'))
        print(json.dumps({'reachableFreeTimeEncounters': validate_encounter_routes(campaign, world)}))
