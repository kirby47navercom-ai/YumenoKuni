"""Keep authored public tallies distinct from private individual ballots."""
import json
from copy import deepcopy
from pathlib import Path
from v4_native_tasks import convert_task

ROOT = Path(__file__).resolve().parents[1]
tasks = json.loads((ROOT / 'data/v4_story/tasks.json').read_text(encoding='utf-8'))['tasks']
expected = {2: {'yuu': 11, 'mio': 2}, 3: {'sora': 9, 'ken': 1},
            4: {'rei': 7, 'koto': 1}, 5: {'akari': 4, 'satsuki': 1, 'nana': 1}, 6: {'koto': 5}}
rows = {}
for chapter in range(1, 7):
    task = tasks[f'T{chapter}-VOTE-01']
    before = deepcopy(task)
    stage = convert_task(task)['stage']
    assert task == before
    assert stage['answer'] == task['answer'] and stage['candidates'] == task['candidates']
    if chapter == 1:
        assert isinstance(stage['voteCounts'], str) and 'not authored' in stage['voteCounts']
    else:
        counts = stage.get('voteCounts', stage.get('authoredResult'))
        public = {who: counts[who] for who in stage['candidates'] if who in counts}
        assert public == expected[chapter]
        assert all(type(n) is int and n >= 0 for n in public.values())
        if 'total' in counts:
            assert sum(public.values()) == counts['total']
    assert stage['finalVote'] == (chapter != 6)
    assert 'individualBallots' not in stage
    rows[stage['id']] = {key: stage[key] for key in ('finalVote', 'voteCounts', 'authoredResult') if key in stage}
print(json.dumps({'ok': True, 'tasks': rows, 'unknownCountsInvented': False}, ensure_ascii=False))
