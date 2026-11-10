"""Publish context-specific ammunition for the native Nonstop Debate rounds."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'data/v4_story'

# The alternatives concern the same objects, timings, records, or witnesses.
# Required evidence is included independently of the alternatives below.
ALTERNATIVES = {
    1: {
        'A01': '11 12', 'A02': '03 02 01', 'A03': '03 11 10', 'A05': '07 12',
        'A06': '10 07 12', 'A07': '09 10', 'A08': '08 04', 'A09': '05 06 09',
        'A10': '03 11 09', 'T05e': '03 09', 'LIE': '08 04',
    },
    2: {
        'A01': '08 05', 'A02': '03 10', 'A03': '07 05', 'A04': '03 05 08',
        'A05': '08 10 03', 'A06': '03 02 06', 'A07': '05 07', 'A08': '09 07',
        'A09': '02 04 10', 'A10': '05 08', '01': '04 03', 'LIE': '09 07',
    },
    3: {
        'A01': 'riku-index memory-rule reflection-geometry', 'A02': 'file-first knife-work',
        'A03': 'private-notebook private-phrase memory-rule', 'A04': 'file-first possession-rules',
        'A05': 'camera-timing reflection-geometry knife-work', 'A06': 'riku-function private-phrase',
        'A07': 'camera-preparation camera-timing', 'A08': 'current-nonattempt father-record',
        'A09': 'envelope-route restraint-awake camera-timing',
        'A10': 'restraint-awake alive-confirmation file-second',
        'A11': 'morning-use possession-rules memory-rule', '01': 'file-first first-attack',
    },
    4: {
        'A01': 'last-alive entry-observers', 'A02': 'injury-order life-vs-form',
        'A03': 'rewind-scope injury-order first-hand', 'A04': 'rei-close closed-photo pipe-boundary',
        'A05': 'waiting-request entry-observers', 'A06': 'entry-observers closed-photo injury-order',
        'A07': 'no-rear-exit photo-comparison old-record', 'A08': 'old-record life-vs-form',
        'A09': 'life-vs-form last-alive', 'A10': 'injury-order creation-rule death-file',
        '01': 'rei-close pipe-boundary', 'LIE': 'entry-observers closed-photo',
    },
    5: {
        'A01': '02 20 14', 'A02': '16 14', 'A03': '12 18 04', 'A04': '02 12',
        'A05': '05 12', 'A06': '11 13 18', 'A07': '07 11', 'A08': '11 07',
        'A09': '07 15 11', 'A10': '17 16', 'A11': '02 06 01', '01': '14 17',
        'LIE': '10 16',
    },
    6: {
        'A01': '16 10 08', 'A03': '12 13 09', 'A04': '09 04', 'A05': '06 04 16',
        'A06': '09 08', 'A07': '07 02 11', 'A08': '03 02 12', 'A09': '03 08',
        'A10': '02 03 12', '01': '03 13', 'LIE': '09 14 06',
    },
}


def apply(direction, tasks):
    rounds = {}
    catalog = {card['id'] for task in tasks.values() for card in task.get('stage', {}).get('options', []) if isinstance(card, dict) and 'id' in card}
    for task_id, task in tasks.items():
        stage = task.get('stage', {})
        if stage.get('kind') != 'nonstop':
            continue
        chapter = int(task_id[1])
        key = 'LIE' if '-LIE-' in task_id else task_id.rsplit('-', 1)[1]
        prefix = f'v4:{chapter}:knowledge:' if chapter in (3, 4) else f'v4:E{chapter}-'
        options = {option['id'] for option in stage['options']}
        required = dict.fromkeys(task['requiresEvidence'])
        transformation = task.get('transformation', {}).get('sourceEvidenceId')
        if transformation:
            required[transformation] = None
        for row in task['debate']['lines']:
            for target in (row.get('weak'), row.get('lieWeak')):
                if target and target.get('answer'):
                    required[target['answer']] = None
            if row.get('agree'):
                required[row['agree']] = None
        if not required or not required.keys() <= options:
            raise ValueError(f'{task_id} required ammunition missing from task options')
        # An explicitly scoped task can intentionally be limited to its authored inventory.
        choices = [prefix + token for token in ALTERNATIVES[chapter][key].split()]
        if not set(choices) <= catalog:
            raise ValueError(f'{task_id} alternative ammunition missing from catalog')
        choices = list(dict.fromkeys(evidence for evidence in choices if evidence not in required))
        insert_at = (sum(map(ord, task_id)) % (len(choices) + 1))
        choices[insert_at:insert_at] = required
        rounds[task_id] = choices
    direction['nonstopAmmo'] = rounds


if __name__ == '__main__':
    file = ROOT / 'trial_direction.json'
    direction = json.loads(file.read_text(encoding='utf-8'))
    tasks = json.loads((ROOT / 'native_tasks.json').read_text(encoding='utf-8'))['tasks']
    apply(direction, tasks)
    file.write_text(json.dumps(direction, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(len(direction['nonstopAmmo']), 'rounds')
