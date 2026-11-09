"""Bounded presentation repair, independent of dialogue identity comparisons."""
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'Game/Saved/editorial-before-scene-repair-20261101.json'
BASE_SHA = 'e6d1014f89043d84f6514d6951ada09ed464510cea15b5e8254808ec868c7d39'
SCENES = [
    ('11a', '1-04L1', 'plaza', '푸드코트의 작은 탁자.'),
    ('11a', '1-05G', 'park_main_gate', '쇼가 광장 밖 정문 쪽으로 걸어간다.'),
    ('11a', '1-07k', 'clinic', '나나는 의무실에서 보관함을 닫고 있다.'),
    ('11a2', '1-17-F-SA02', 'hotel_corridor', '호텔 복도.아카리가 앞서 가고 사츠키는 미오와 같은 속도로 걷는다.'),
    ('65', '1-07a', 'dining_room', '호텔의 식사 공간.'),
    ('154', '1-09a-01', 'hotel_lobby', '미오는 로비 선반 앞에서 수건을 정리하던 카에데를 만난다.'),
]
TIMES = {
    '11a': {'1-07k': 'night'},
    '11a2': {'1-17g': 'evening', '1-18': 'night'},
    '11a3': {'1-26': 'evening', '1-28': 'night'},
    '65': {'1-07a': 'evening'},
    '120': {'1-07g': 'night'},
    '154': {'1-09a-01': 'day'},
}


def source(prefix):
    p, = (ROOT/'docs/design/rewrite_v4').glob(prefix+'_*.md')
    raw = p.read_bytes()
    return p, raw, raw.decode('utf-8-sig').splitlines()


def heading(lines, location):
    matches = [(i+1, line) for i, line in enumerate(lines)
               if re.match(r'^#{2,3}\s+'+re.escape(location)+r'\s', line)]
    assert len(matches) == 1, (location, matches)
    return matches[0]


def refresh_hashes(expected, actual):
    """Only live Markdown raw/normalized hashes may change as wording changes."""
    if isinstance(expected, list) and isinstance(actual, list):
        assert len(expected) == len(actual)
        for a, b in zip(expected, actual): refresh_hashes(a, b)
    elif isinstance(expected, dict) and isinstance(actual, dict):
        assert expected.keys() == actual.keys()
        if 'fileSha256' in expected and expected.get('file', '').endswith('.md'):
            assert expected['file'] == actual['file']
            p = ROOT/'docs/design/rewrite_v4'/expected['file']
            valid = {hashlib.sha256(p.read_bytes()).hexdigest(),
                     hashlib.sha256(p.read_text(encoding='utf-8-sig').encode()).hexdigest()}
            assert actual['fileSha256'] in valid, expected['file']
            expected['fileSha256'] = actual['fileSha256']
        for key in expected:
            if key != 'fileSha256': refresh_hashes(expected[key], actual[key])


def verify_and_normalize(current):
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
    before = json.loads(BASE.read_text(encoding='utf-8'))
    expected = copy.deepcopy(before)
    world = json.loads((ROOT/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf-8'))
    added = []
    for prefix, location, space, quote in SCENES:
        p, raw, lines = source(prefix)
        line, title = heading(lines, location)
        assert space in world['spaces'] and any(quote in value for value in lines)
        key = p.name+':'+location
        assert key not in before['sections']
        expected['sections'][key] = {
            'space': space, 'entry': 'section-entry-only',
            'source': {'file': p.name, 'location': location, 'line': line,
                       'fileSha256': hashlib.sha256(raw).hexdigest(), 'heading': title},
            'geometryPolicy': 'Reuse the authored room geometry; do not infer a room number, eyewitness or exact actor position.',
        }
        added.append({'file': p.name, 'location': location, 'space': space, 'sourceQuote': quote})
    groups = {}
    for row in before['timeRanges']: groups.setdefault(row['source']['file'], []).append(copy.deepcopy(row))
    for prefix, anchors in TIMES.items():
        p, raw, lines = source(prefix)
        old = groups.get(p.name, [])
        starts = {row['startLine']: row['timeOfDay'] for row in old}
        if prefix == '120': starts[1] = 'night'  # Explicit "체류2일차 밤" in its header.
        starts.update({heading(lines, loc)[0]: time for loc, time in anchors.items()})
        points = sorted(starts)
        groups[p.name] = [{'source': {'file': p.name, 'fileSha256': hashlib.sha256(raw).hexdigest()},
                          'startLine': start, 'endLineExclusive': points[i+1] if i+1<len(points) else len(lines)+1,
                          'timeOfDay': starts[start], 'policy': before['timeRanges'][0]['policy']}
                         for i, start in enumerate(points)]
    expected['timeRanges'] = [row for file in sorted(groups) for row in groups[file]]
    refresh_hashes(expected, current)
    assert expected == current, 'Unreviewed scene/time/CG/prop/public-record change'
    normalized = copy.deepcopy(current)
    for row in added: del normalized['sections'][row['file']+':'+row['location']]
    normalized['timeRanges'] = copy.deepcopy(before['timeRanges'])
    for row in normalized['timeRanges']:
        p = ROOT/'docs/design/rewrite_v4'/row['source']['file']
        row['source']['fileSha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
    report = {'ok': True, 'sourceOnly': True, 'nativePlayed': False,
              'addedSceneEntries': added, 'timeAnchors': TIMES,
              'beforeSections': len(before['sections']), 'afterSections': len(current['sections']),
              'beforeTimeRanges': len(before['timeRanges']), 'afterTimeRanges': len(current['timeRanges']),
              'allOtherPresentationFieldsExact': True,
              'scope': 'Six explicitly read scene entries and eight authored day-part anchors only; no new geometry, event, evidence, CG or task.'}
    (ROOT/'Game/Saved/editorial-scene-repair-proof-20261101.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return normalized
