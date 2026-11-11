#!/usr/bin/env python3
"""Compile explicitly routed parts of the revised manuscript for the native game."""

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

from build_v4_story import SPEAKERS
from build_revised_mine_assets import ART as MINE_ART, archive_package_comparison, archive_slot, corridor_sightlines, door_comparison, inspection_latch_section, inspection_mines, mirror_comparison, mirror_knife_sequence, paper_comparison, theatre_pedestal, theatre_ring, theatre_section
from revised_comic import chapter_two_comic_stage, chapter_three_comic_stage, chapter_four_comic_stage, chapter_five_comic_stage, chapter_six_comic_stage, comic_stage
from revised_life import life_route
from revised_investigation import checked_investigation, examine_document_bundles, first_investigation_close, first_photo_investigation, supplemental_inspection
from revised_voice_polish import speech_address
from revised_trial_bridges import apply_trial_bridges
from revised_dialogue_direction import apply_dialogue_direction


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / 'docs/design/rewrite_v5'
REVISED_CASE_ART = 'Assets/Art/revision_case/'
SCENE = re.compile(r'^#{2,3} .*?\b(P\d{2}[a-z]?|0[1-6]-[DFITR][0-9A-Z]{2}[a-z]?)　(.+)$')
SAY = re.compile(r'^\s*\*\*([^*]+)\*\*　(\S.*)$')
BULLET = re.compile(r'^- \*\*([^*]+)\*\*\s*(.*)$')
OPTION = re.compile(r'^\*\*[AB]\. ([^*]+)\*\*$')
STMT = re.compile(r'^\s*(\d+)[.)]\s+(?:\*\*)?([^　]+?)\s*　“(.*?)”\s*(.*)$')
MODES = (
    ('논스톱', 'nonstop'), ('패닉', 'panic'), ('쇼다운', 'showdown'),
    ('발굴', 'mindmine'), ('애너그램', 'anagram'), ('스크럼', 'scrum'),
    ('이론 무장 —', 'armament'), ('클라이맥스', 'climax'), ('투표', 'vote'),
    ('추리 연결', 'reasoning'), ('인물 지목', 'person'), ('지점 지목', 'spot'),
    ('위치 지목', 'spot'), ('증거 지목', 'bullet'), ('증거 제시', 'bullet'),
    ('정답 선택', 'choice'), ('우소다마', 'lie'), ('위증', 'lie'),
)
ANAGRAMS = {
    '01-T04': ('일련번호', '방문표찰서명', '두 서류가 다른 때에 나왔음을 확인하는 번호를 뭐라고 불렀지?'),
    '01-T05a': ('접수명의', '화자공동서신고', '통화 전에 신청서에 이미 기입된 이름의 칸은?'),
    '02-T06': ('음식창구', '의상실문고리대', '아이의 마지막 반응을 두 사람이 확인한 자리는 준비실의 어디였지?'),
    '02-T07b': ('퇴실시점', '폐막입장반납', '공연이 끝났다고 느낀 때와 구별해서 재판에서 표시해야 할 실제 사건의 순간은?'),
    '03-T01': ('빙의고정', '귀환소생잠금', '이미 완전한 빙의 상태에 들어간 뒤 본체가 사망했을 때, 점유가 지속되는 현상을 무엇이라고 하지?'),
    '03-T03': ('복귀확인', '기시간점', '시연에서 각자가 자기 몸으로 돌아왔다는 것을 무엇으로 확인했지?'),
    '04-T02j': ('수습직후', '입실전구조도중발견당시', '손목 고리를 확인할 수 있는 사진은 무엇을 하고 난 뒤에 찍혔나?'),
    '04-T03a': ('형체유지', '생존회복사진', '판정을 미루자는 말이 지금 남기려는 것은 무엇이지?'),
    '05-T01': ('사용횟수', '기억시각장소', '다른 시각에 두 번 썼다고 하려면 먼저 어느 조건을 대조해야 하지?'),
    '05-T03': ('전문공개', '첫열람사망확인부암기', '세 번째 쪽을 펴자 처음 이루어진 종료 조건은?'),
    '06-T00': ('인계목록', '서명승접수', '옛 문서가 다음 담당자에게 넘어갈 때, 어떤 목록이 그것을 받았는지 남겨 두었지?'),
    '06-T02h': ('재승인', '자동유지최초취소', '처음에 선택한 값이 그대로 보이는 것과 달리, 기원을 확인한 뒤 다시 실제로 한 동작은?'),
}


@dataclass
class Scene:
    id: str
    title: str
    file: str
    line: int
    body: list[str]

    def source(self, line):
        return {'file': self.file, 'location': self.id, 'line': line}


def manuscript():
    scenes = {}
    for path in sorted(MANUSCRIPT.glob('*.md')):
        scene = None
        for number, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
            if match := SCENE.match(line):
                ident, title = match.groups()
                if ident in scenes:
                    raise ValueError(f'Duplicate scene {ident} in {path.name}:{number}')
                scene = scenes[ident] = Scene(ident, title, path.name, number, [])
            elif scene is not None:
                scene.body.append(line)
    return scenes


def speech(raw, line, scene):
    match = SAY.match(raw)
    if match is None:
        return None
    name, text = match.groups()
    if scene.id=='03-T03' and name=='켄의 몸':
        name='소라(켄의 몸)'
    actor = re.split(r'[·(（/]', name)[0].strip()
    if body := re.search(r'[（(]([^）()]+)의 몸[）)]', name):
        actor = body[1]
    elif actor.endswith('의 몸'):
        actor = actor.removesuffix('의 몸')
    mono = actor in ('독백', '미오의 독백') or '독백' in name or '속말' in name
    slug = SPEAKERS.get('미오' if mono and actor not in SPEAKERS else actor, '')
    return {'type': 'say', 'speaker': name, 'actor': slug, 'text': text.replace('**', ''),
            'mono': mono, 'source': scene.source(line)}


def trial_inventory(scenes):
    inventory = []
    for scene in scenes.values():
        if '-T' not in scene.id and scene.id != '06-R00':
            continue
        task = None
        if scene.id == '02-T09':
            inventory.append({'kind': 'climax', 'title': scene.title, 'source': scene.source(scene.line),
                              'statements': [], 'referenceLines': []})
        for number, raw in enumerate(scene.body, scene.line + 1):
            if raw.startswith(('### ', '#### ', '##### ')):
                title = raw.lstrip('# ')
                kind = next((kind for label, kind in MODES if label in title), None)
                task = None
                if kind and not (kind == 'vote' and '투표 직전' in title):
                    task = {'kind': kind, 'title': title, 'source': scene.source(number),
                            'statements': [], 'referenceLines': []}
                    if kind == 'anagram':
                        answer, distractors, question = ANAGRAMS[scene.id]
                        tail = scene.body[number - scene.line:]
                        bounds = next((i for i, line in enumerate(tail) if line.startswith('#')), len(tail))
                        rule = re.sub(r'[^가-힣]', '', '\n'.join(tail[:bounds]))
                        if answer not in rule:
                            raise ValueError(f'Anagram answer differs from manuscript: {scene.id}')
                        task['authoredInput'] = {'kind': kind, 'question': question, 'answer': answer,
                                                 'distractors': list(distractors)}
                    inventory.append(task)
            elif task is not None and task['kind'] in ('nonstop', 'panic', 'showdown', 'lie'):
                if match := STMT.match(raw):
                    index, speaker, text, role = match.groups()
                    task['statements'].append({'index': int(index), 'speaker': speaker.strip('*'),
                                               'text': text, 'role': role, 'line': number})
                elif raw.startswith('|') and task['kind'] in ('nonstop', 'panic'):
                    cells = [cell.strip() for cell in raw.strip('|').split('|')]
                    if len(cells) == 4 and cells[0].isdigit() and task['kind'] == 'nonstop':
                        index, speaker, text, role = cells
                        task['statements'].append({'index': int(index), 'speaker': speaker, 'text': text,
                                                   'role': role, 'line': number})
                    elif task['kind'] == 'panic':
                        task.setdefault('laneTable', []).append({'line': number, 'cells': cells})
                elif raw.strip() and not SAY.match(raw):
                    task['referenceLines'].append({'line': number, 'text': raw.strip()})
    return inventory


def campaign_order(scenes):
    chapters = {'P': [ident for ident in scenes if ident.startswith('P')]}
    for chapter in range(1, 7):
        chapters[str(chapter)] = [ident for ident in scenes if ident.startswith(f'{chapter:02}-') and ident[3] != 'F']
    first = chapters['1']
    prefix = [ident for ident in first if scenes[ident].file.startswith('01_')]
    supplement = [ident for ident in first if scenes[ident].file.startswith('08_')]
    chapters['1'] = [ident for ident in prefix if ident[3] in 'DI'] + [ident for ident in supplement if ident[3] == 'I']
    chapters['1'] += [ident for ident in prefix if ident[3] == 'T'] + [ident for ident in supplement if ident[3] == 'T']
    chapters['1'] += [ident for ident in prefix if ident[3] == 'R']
    for chapter, ids in chapters.items():
        if len(ids) != len(set(ids)) or not ids:
            raise ValueError(f'Invalid manuscript sequence {chapter}')
    return chapters


PROLOGUE_SPACES = {
    'P01': ('park_garden', 'bgm_pro_arrival'), 'P02': ('park_main_gate', 'bgm_pro_intro'),
    'P02f': ('ticket_booth', ''), 'P02g': ('ticket_booth', ''),
    'P03': ('plaza', ''), 'P03b': ('plaza', ''), 'P03a': ('plaza', ''), 'P03c': ('hotel_lobby', ''),
    'P04': ('plaza', 'bgm_motive'), 'P04c': ('hotel_lobby', ''), 'P04a': ('park_garden', ''),
    'P04b': ('ticket_booth', ''), 'P04f': ('park_main_gate', ''), 'P04g': ('plaza', 'bgm_tense'),
    'P05': ('plaza', 'bgm_daily_pro'), 'P05i': ('can_toss_booth', ''), 'P05d': ('park_garden', ''),
    'P05f': ('can_toss_booth', ''), 'P05e': ('park_garden', ''), 'P05g': ('park_garden', ''),
    'P05h': ('hotel_lobby', ''), 'P06': ('dining_room', 'bgm_daily_pro'),
    'P06a': ('hotel_corridor', 'bgm_tense'), 'P06b': ('dining_room', ''),
    'P07': ('hotel_corridor', 'bgm_night'), 'P07a': ('hotel_corridor', ''),
    'P07b': ('hotel_corridor', ''), 'P07c': ('ticket_booth', ''), 'P07d': ('hotel_corridor', ''),
    'P07e': ('hotel_corridor', ''), 'P08': ('story_guest_room', 'bgm_night'),
}
HEADING_BRANCHES = {
    'P02g': ('함께 설 위치', '다시 모일 때'),
    'P03c': ('누구를 기다리는지 먼저 정한다', '처음으로 같이 들은 소리'),
    'P04g': ('불빛이 돌아오기 전에', '광장에 남은 빛'),
    'P05d': ('사진에 다 들어갈 필요는 없어', '서로를 같은 데에 적지 않기'),
    'P05e': ('분수 가까이 남을 수 있다', '먼저 물어보고 가는 사람'),
    'P05g': ('먼저 돌아갈 사람을 고른다', '호텔에 들어가기 직전'),
    'P07d': ('문 앞에 두고 갈 말', '다들 방으로 갈 때'),
    'P08': ('불을 끄기 전에 치운 것', '공통'),
}
NARRATION = {'P01': ('미오가 눈을 뜬 곳은',), 'P08': ('(창 밖을 한 번 더 보려다가',)}
INTRODUCTIONS = {
    'haruka': '하루카. 아사노 하루카.', 'sho': '저는 쇼입니다.',
    'kaede': '카에데가 선을 지우던 코토를 본다. 펜을 받아 들고 자기 이름을 쓴다.',
    'ai': '아이예요. 마실 분한테 저를', 'satsuki': '사츠키. 일단 이거 하나만',
    'akari': '아카리예요.', 'nana': '저는 나나예요.', 'yuu': '유우. 네가 나 찾을 일',
    'ken': '내 건 지금 써 줘. 켄.', 'riku': '리쿠. 내가 만난 건 아까',
    'lappy': '지금부터 여기 규칙을 안내할게요.', 'koto': '코토라고 적어 주세요.',
    'sora': '생수 더 가져온 건 나야. 소라.', 'taiga': '타이가. 나 찾을 때는',
    'rin': '린. 저쪽 문 손잡이도', 'rei': '저는 레이라고 부르시면',
}
PROLOGUE_CALLBACKS = {
    'P03': ('P02g', 'P02g에서 유리 앞까지', 'yuu', '유우'),
}
FREE_ACTORS = {
    1: ('kaede','sora','ai','taiga','nana','rin','taiga','kaede'),
    2: ('rin','ai','riku','sora','ai','rin','akari','ken','satsuki','koto'),
    3: ('yuu','ken','haruka','sora','riku','riku'),
    4: ('yuu','rei','haruka','rei','nana','satsuki'),
    5: ('sho','satsuki','koto','akari','sho','yuu'),
}
SCENE_PHASES = {
    'P06': 'evening', 'P07': 'night', 'P08': 'night',
    '01-D01b': 'evening', '01-D01f': 'night', '01-D01j': 'day',
    '01-D01h': 'day', '01-D02a': 'evening', '01-D02c': 'night',
    '01-D02d': 'day', '01-D02k': 'evening', '01-D03k': 'day',
    '01-D03d': 'evening', '01-D03h': 'night',
    '02-D02': 'evening', '02-D02f': 'evening', '02-D02a': 'evening',
    '02-D02h': 'night', '02-D02b': 'night', '02-D02c': 'day',
    '02-D03b': 'day', '02-D04b': 'day', '02-D04l': 'evening',
    '02-D06': 'evening', '05-D01a': 'day', '05-D02e': 'day',
    '05-D02k': 'day', '05-D04': 'day',
}


class CampaignGraph:
    def __init__(self):
        self.nodes = {}
        self.introductions = {}

    def add(self, ident, **node):
        if ident in self.nodes:
            raise ValueError(f'Duplicate native node {ident}')
        self.nodes[ident] = {'id': ident, **node}
        return ident

    def finish_free_time(self, scene, target):
        if '-F' not in scene.id:
            return target
        flag = f'rev:encounter:{scene.id}'
        return self.add(f'rev:{scene.id}:complete', type='stage', next=target,
                        set={flag: True}, growthEncounter=True,
                        source=scene.source(scene.line + len(scene.body)))

    def lines(self, scene, start, end, target):
        seen = Counter()
        events = []
        for offset in range(start, end):
            raw = scene.body[offset]
            event = speech(raw, scene.line + offset + 1, scene)
            if event is None and raw.startswith(NARRATION.get(scene.id, ())):
                event = {'type': 'say', 'actor': 'mio', 'speaker': '미오', 'mono': True,
                         'text': raw.strip('()'), 'source': scene.source(scene.line + offset + 1)}
            if event is None:
                continue
            reveal = self.introductions.get(event['actor'])
            if reveal is not None and event['source']['line'] < reveal:
                event['speaker'] = '???'
            address = speech_address(scene.id, raw)
            seen[address] += 1
            events.append((f'rev:{scene.id}:{start}:{address}:{seen[address]}', event))
        for ident, event in reversed(events):
            target = self.add(ident, **event, next=target)
        return target

    def menu(self, scene, question, alternatives, tail):
        options = []
        for index, (label, start, end, response) in enumerate(alternatives):
            flag = chr(ord('A') + index)
            to = self.lines(scene, start, end, tail)
            if response:
                to = self.add(f'rev:{scene.id}:response:{flag}', type='say', actor='mio',
                              speaker='미오', mono=True, text=response, next=to,
                              source=scene.source(scene.line + start))
            options.append({'id': flag, 'label': label, 'to': to, 'set': {scene.id: flag}})
        return self.add(f'rev:{scene.id}:choice', type='menu', q=question, options=options)

    def share_choice_tail(self, menu, end, first_shared_line):
        options = self.nodes[menu]['options']
        shared = options[-1]['to']
        while shared != end and self.nodes[shared]['source']['line'] < first_shared_line:
            shared = self.nodes[shared]['next']
        if shared == end:
            raise ValueError(f'Missing shared dialogue after {menu}')
        # Keep the existing final-option nodes so saves inside the shared dialogue still load.
        for option in options[:-1]:
            node = option['to']
            if node == end:
                option['to'] = shared
                continue
            while self.nodes[node]['next'] != end:
                node = self.nodes[node]['next']
            self.nodes[node]['next'] = shared

    def insert_before_source_line(self, entry, source, build, end_node=None):
        previous = None
        following = entry
        while following != end_node and self.nodes[following].get('source', {}).get('location') == source['location']:
            if self.nodes[following]['source']['line'] >= source['line']:
                break
            previous, following = following, self.nodes[following]['next']
        inserted = build(following)
        if previous is None:
            return inserted
        self.nodes[previous]['next'] = inserted
        return entry

    def scene(self, scene, next_scene):
        body = scene.body
        end = len(body)
        if scene.id in HEADING_BRANCHES:
            question, common = HEADING_BRANCHES[scene.id]
            boundaries = [i for i, line in enumerate(body) if line.lstrip('# ') == common]
            if len(boundaries) != 1:
                raise ValueError(f'{scene.id}: missing or repeated branch join')
            join = boundaries[0]
            depth = '### ' if scene.id == 'P05d' else '#### '
            choices = [(i, line[len(depth):]) for i, line in enumerate(body[:join]) if line.startswith(depth)]
            if len(choices) < 2:
                raise ValueError(f'{scene.id}: not enough alternatives')
            alternatives = [(label, i + 1, j, '') for (i, label), (j, _) in zip(choices, [*choices[1:], (join, '')])]
            target = self.menu(scene, question, alternatives, self.lines(scene, join + 1, end, next_scene))
            target = self.lines(scene, 0, choices[0][0], target)
        elif scene.id == 'P06':
            choices = [(i, m[1]) for i, line in enumerate(body) if (m := OPTION.match(line))]
            if len(choices) != 2:
                raise ValueError('P06: expected two distinct dinner paths')
            join = body.index('**합류.**')
            alternatives = [(label, i + 1, j, '') for (i, label), (j, _) in zip(choices, [choices[1], (join, '')])]
            target = self.menu(scene, '빈 의자', alternatives, self.lines(scene, join + 1, end, next_scene))
            target = self.lines(scene, 0, choices[0][0], target)
        else:
            choices = [(i, m[1], m[2]) for i, line in enumerate(body) if (m := BULLET.match(line))]
            if choices:
                if not 2 <= len(choices) <= 5:
                    raise ValueError(f'{scene.id}: choice list needs explicit routing')
                last = choices[-1][0]
                join = last + 1
                while join < end and body[join].startswith('  '):
                    join += 1
                if scene.id == 'P05h':
                    join = next(i for i in range(last + 1, end) if body[i].startswith('(아이는 안에서 상자를 내려놓는다.'))
                alternatives = [(label, i + 1, j, response) for (i, label, response), (j, *_) in zip(choices, [*choices[1:], (join,)])]
                target = self.menu(scene, scene.title, alternatives, self.lines(scene, join, end, next_scene))
                target = self.lines(scene, 0, choices[0][0], target)
            else:
                target = self.lines(scene, 0, end, next_scene)
        if scene.id in ('P04c', 'P08'):
            offset, = (i for i, row in enumerate(body) if row.startswith('> '))
            source = scene.source(scene.line + offset + 1)
            previous = None
            following = target
            while self.nodes[following]['source']['line'] < source['line']:
                previous, following = following, self.nodes[following]['next']
            if scene.id == 'P04c':
                menu = 'rev:P04c:rules'
                options = []
                read_flags = {}
                for index, rule in enumerate(body[offset][2:].split(' / '), 1):
                    title, row = rule.split(' — ', 1)
                    flag = f'{menu}:{index}'
                    read_flags[flag] = True
                    doc = self.add(flag, type='document', title=title, rows=[row], next=menu,
                                   source=source, set={flag: True})
                    options.append({'id': str(index), 'label': title, 'to': doc, 'requires': {flag: False}})
                options.append({'id': 'continue', 'label': '안내를 덮는다', 'to': following, 'requires': read_flags})
                inserted = self.add(menu, type='menu', q='어느 규칙부터 읽을까?', options=options, source=source)
            else:
                title, row = body[offset][2:].split(' — ', 1)
                inserted = self.add('rev:P08:private-note', type='document', title=title, rows=[row],
                                    private=True, source=source, next=following)
            if previous is None:
                target = inserted
            else:
                self.nodes[previous]['next'] = inserted
        space, music = PROLOGUE_SPACES[scene.id]
        if scene.id in PROLOGUE_CALLBACKS:
            earlier, anchor, actor, name = PROLOGUE_CALLBACKS[scene.id]
            offset = next(i for i, line in enumerate(body) if line.startswith(anchor))
            answers = re.findall(r'“([^”]+)”', body[offset])
            if len(answers) != 3:
                raise ValueError(f'{scene.id}: three earlier choices must have three responses')
            cases = []
            source = scene.source(scene.line + offset + 1)
            for flag, text in zip('ABC', answers):
                ident = self.add(f'rev:{scene.id}:recall:{flag}', type='say', actor=actor,
                                 speaker='???' if source['line'] < self.introductions[actor] else name,
                                 text=text, mono=False, source=source, next=target)
                cases.append({'flag': earlier, 'equals': flag, 'to': ident})
            target = self.add(f'rev:{scene.id}:recall', type='branch', cases=cases, default=target)
        node = {'type': 'stage', 'next': target, 'source': scene.source(scene.line),
                'scene': {'space': space, 'perspective': 'current-observation'}}
        if music:
            node['presentation'] = {'music': {'operation': 'play', 'cue': music}}
        if scene.id == 'P01':
            node['chapterEntryType'] = 0
        entry = self.add(f'rev:{scene.id}', **node)
        if scene.id != 'P02':
            return entry
        spots = []
        for ident, label, text, pos in (
            ('gate-plate', '철문 옆 표찰', '출입 표시등은 켜져 있다. 손잡이가 움직여도 문은 열리지 않는다.', [2.85, 1.34, -1.75]),
            ('service-board', '서비스동 보수판', '작은 판이 철문과 따로 붙어 있다. 판을 열거나 건드린 사람은 확인하지 못했다.', [-2.65, 1.32, -1.5]),
        ):
            done = self.add(f'rev:P02:return:{ident}', type='return')
            read = self.add(f'rev:P02:inspect:{ident}', type='document', title=label, rows=[text],
                            source=scene.source(scene.line + 2), next=done)
            spots.append({'id': ident, 'label': label, 'neutralLabel': label, 'space_id': space, 'world_pos': pos, 'entry': read})
        return self.add('rev:P02:walk-to-gate', type='investigate', space_id='park_garden', spots=spots,
                        investigationMusic=music, requiredSpotIds=[spot['id'] for spot in spots], next=entry)

    def compile_prologue(self, scenes):
        ids = [scene.id for scene in scenes.values() if scene.id.startswith('P')]
        if set(ids) != set(PROLOGUE_SPACES) or ids[0] != 'P01' or ids[-1] != 'P08':
            raise ValueError('Prologue scene map does not match manuscript')
        for actor, trigger in INTRODUCTIONS.items():
            matches = [scene.line + offset + 1 for ident in ids for scene in (scenes[ident],)
                       for offset, raw in enumerate(scene.body) if trigger in raw]
            if len(matches) != 1:
                raise ValueError(f'Unresolved first introduction: {actor}')
            self.introductions[actor] = matches[0]
        target = self.add('rev:P:end', type='end', chapterComplete=True, nextChapter='1')
        for ident in reversed(ids):
            target = self.scene(scenes[ident], target)
        return {'schemaVersion': 1, 'contentVersion': 'v4', 'campaignRevision': 'rewrite-v5',
                'chapter': 'P', 'entry': target, 'nodes': self.nodes}


def debate_statement(task, ident, speaker, raw, source, kind='plain', answer='', point=None):
    if source.get('location')=='03-T03' and speaker=='켄의 몸':
        speaker='소라(켄의 몸)'
    body = re.search(r'[（(]([^）()]+)의 몸[）)]', speaker)
    actor = SPEAKERS[body[1] if body else speaker.removesuffix('의 몸')]
    text = raw.replace('**', '').replace('[큰 소리]', '').strip()
    if kind in ('weak', 'agree'):
        text = text.removesuffix(' 약점.')
    row = {'id': f'{task}:{ident}', 'speaker': speaker, 'actor': actor,
           'text': text, 'kind': kind, 'source': source}
    if answer:
        word, = re.findall(r'\*\*([^*]+)\*\*', raw)
        weak = {'word': word, 'start': text.index(word), 'answer': answer, 'lie': False}
        row['weak'] = weak
        row['targets'] = [{'kind': kind, 'weak': weak, 'outcome': 'A'}]
        if point is not None:
            if word[point] != '혼':
                raise ValueError('The authored V-point shifted')
            row['vpoint'] = {'glyphIndex': weak['start'] + point}
    return row


def apply_authored_vpoints(scenes, tasks):
    rows_by_source = {}
    for task in tasks.values():
        if task['stage']['kind']!='nonstop':
            continue
        for rows in (task['stage']['lines'],task['debate']['lines']):
            for row in rows:
                if 'weak' in row:
                    ref = row['source']
                    rows_by_source.setdefault((ref['file'],ref['line']),[]).append(row)
    pattern = re.compile(r'^선택 V포인트는 (\d+)번 약점의 「([^」]+)」 안에 있는 ‘(.)’이다.*?(\d+)번째 글자')
    for scene in scenes.values():
        statements = {}
        for offset, raw in enumerate(scene.body):
            if raw.startswith('#'):
                statements.clear()
            if match := STMT.match(raw):
                statements[match[1]] = (scene.line+offset+1,match[3])
            if not (point := pattern.match(raw)):
                continue
            number, word, glyph, position = point.groups()
            line, marked = statements[number]
            weak, = re.findall(r'\*\*([^*]+)\*\*',marked)
            index = int(position)-1
            if word not in weak or weak[index]!=glyph:
                raise ValueError(f'Invalid authored V-point: {scene.file}:{scene.line+offset+1}')
            rows = rows_by_source.get((scene.file,line))
            if not rows:
                raise ValueError(f'Missing authored V-point target: {scene.file}:{line}')
            for row in rows:
                if row['weak']['word']!=weak:
                    raise ValueError(f'Compiled V-point target differs from manuscript: {scene.file}:{line}')
                row['vpoint'] = {'glyphIndex':row['weak']['start']+index}


def chapter_verdict(graph, scene, tail, chapter):
    art_dir = ROOT / f'art/revision_comic/chapter{chapter}'
    marks = {1: (
        ('(소라가 앞으로 움직인다.', 'verdict-01', 1.9, .025, 'sfx_bang_door'),
        ('(공원 입장 검사대 모양의 통로.', 'verdict-02', 2.7, .045, 'sfx_machine'),
        ('(타이가가 몸을 틀어 앞으로 가려 한다.', 'verdict-03', 2.5, .045, 'sfx_machine'),
        ('(마지막 출석등이 꺼진다.', 'verdict-04', 2.8, .015, 'sfx_bang_door'),
    ), 2: (
        ('린 뒤의 좁은 조명 하나가 켜지고', 'verdict-01', 2.6, .025, 'sfx_machine'),
        ('빈 앞치마가 작업대에 놓인다.', 'verdict-02', 2.7, .035, 'sfx_machine'),
        ('린이 미끄러지는 작업대 모서리를 딛고', 'verdict-03', 2.6, .025, 'sfx_bang_door'),
        ('카메라는 멎은 쪽을 멀리서 한 번 보여 준다.', 'verdict-04', 2.9, .01, 'sfx_bang_door'),
    ), 3: (
        ('(소라는 자기 뒤의 통로를 본다.', 'verdict-01', 2.6, .025, 'sfx_machine'),
        ('(다른 쪽에서 같은 요청이 겹친다.', 'verdict-02', 2.7, .035, 'sfx_machine'),
        ('(연기가 소라의 허리 쪽까지 차오른다.', 'verdict-03', 2.8, .025, 'sfx_bang_door'),
        ('(구조 요청 음성이 끊긴다.', 'verdict-04', 3.0, .01, 'sfx_machine'),
    ), 4: (
        ('(래피가 손을 든다.', 'verdict-01', 2.6, .025, 'sfx_machine'),
        ('(레이는 그 줄들을 읽으려 다가간다.', 'verdict-02', 2.7, .025, 'sfx_machine'),
        ('(그가 좌석 안에 밀려 들어간다.', 'verdict-03', 2.8, .04, 'sfx_machine'),
        ('(다시 보일 때 열차는 멎어 있다.', 'verdict-04', 3.0, .01, 'sfx_bang_door'),
    ), 5: (
        ('(재판장 화면이 켜진다.', 'verdict-01', 2.7, .025, 'sfx_machine'),
        ('(아카리가 도장 둘을 내려놓는다.', 'verdict-02', 2.7, .03, 'sfx_machine'),
        ('(상자가 거대한 포장 판 아래로 이동한다.', 'verdict-03', 2.8, .025, 'sfx_bang_door'),
        ('(상자 전면이 다시 보인다.', 'verdict-04', 3.0, .01, 'sfx_bang_door'),
    )}[chapter]
    if not all((art_dir/f'{key}.webp').is_file() for _,key,*_ in marks):
        return graph.lines(scene, 0, len(scene.body), tail)
    cuts = [next(i for i,row in enumerate(scene.body) if row.startswith(mark)) for mark,*_ in marks]
    shot_end = (scene.body.index('### 다시 켜진 재판장') if chapter == 5 else len(scene.body))
    tail = graph.lines(scene, shot_end, len(scene.body), tail)
    for index in range(len(cuts)-1, -1, -1):
        at = cuts[index]
        _, key, duration, push, cue = marks[index]
        end = cuts[index+1] if index+1<len(cuts) else shot_end
        shot = {'image': f'Assets/Art/revision_comic/chapter{chapter}/{key}.webp'}
        next_node = graph.lines(scene, at+1, end, tail)
        ident = next_node
        while ident != tail:
            graph.nodes[ident]['shot'] = shot
            ident = graph.nodes[ident]['next']
        music = {'music': {'operation': 'play', 'cue': 'bgm_punishment_time'}} if index == 0 else {}
        if index == len(cuts)-1:
            music = {'music': {'operation': 'stop'}}
        tail = graph.add(f'rev:{chapter:02}:{key}', type='stage', next=next_node, shot=shot,
                         holdSeconds=duration, shotPush=push, shotCue=cue, presentation=music,
                         source=scene.source(scene.line+at+1))
    return graph.lines(scene, 0, cuts[0], tail)


def compile_showdown(graph, tasks, dead, seats, node, ident, title, speaker, waves, cards, answer, source, wrong, next_node):
    opponent = SPEAKERS[speaker]
    rows = []
    groups = []
    for group, lines in enumerate(waves):
        final = group == len(waves) - 1
        entries = []
        for offset, line in enumerate(lines):
            index = len(rows)
            blade = final and offset == len(lines) - 1
            row = debate_statement(ident, index, speaker, f'**{line}**' if blade else line, source,
                                   'weak' if blade else 'plain', answer if blade else '')
            row.update(role='blade' if blade else 'ordinary', requiredHits=1 if blade else 2,
                       gaugeGain=5, gaugeLoss=-5, durationFrames=360 if blade else 216)
            if blade:
                row.update(bladeTarget=row['weak'])
            rows.append(row)
            entries.append({'type': 'statement', 'lineId': row['id'], 'statementIndex': index})
        groups.append({'id': f'{ident}:group:{group}', 'initialGauge': 50,
                       'advanceThreshold': 255 if final else 50 + len(lines) * 5, 'entries': entries,
                       'afterAdvance': [], 'finalBladeGroup': final, 'gaugeSettleFrames': 15, 'endDwellFrames': 10,
                       'tugRequired': 8, 'tugLimitFrames': 180, 'sourceRange': source})
    last = rows[-1]
    tasks[ident] = {'taskId': ident, 'ready': True, 'requiresEvidence': [card['id'] for card in cards],
                    'stage': {'id': ident, 'v4': True, 'kind': 'showdown', 'title': title,
                              'opponent': opponent, 'lines': rows, 'filterOwnedEvidence': True, 'options': cards,
                              'blade': {'word': last['weak']['word'], 'answer': answer},
                              'showdownV4': {'schemaVersion': 1, 'taskId': ident, 'opponent': opponent, 'groups': groups,
                                             'statements': {row['id']: row for row in rows},
                                             'statementOrder': [row['id'] for row in rows], 'answerEvidenceId': answer,
                                             'weakSourceLineId': last['id'], 'weakRuntimeLineId': last['id'],
                                             'timeFrames': 10800, 'wrongBladeDamage': 2000, 'groupFailureDamage': 1000}},
                    'queues': {'wrong': [{'id': ident + ':wrong', 'type': 'say', 'actor': SPEAKERS[wrong[0]],
                                          'speaker': wrong[0], 'text': wrong[1], 'source': source}]}}
    return graph.add(node, type='task', taskId=ident, trialDead=dead, seats=seats,
                     source=source, success=next_node, next=next_node)

def reviewed_trial(scenes, door_objects, paper_objects):
    """Route the first chapter's inspected records into its authored trial."""
    scene = scenes['01-T01']
    ns = scene.body.index('#### 논스톱 — 같은 줄에 있었다')
    pn = scene.body.index('#### 패닉 — 문이 보증하는 사람')
    ns_id, pn_id = 'T1-NS-REV01', 'T1-PN-REV01'
    evidence = {
        'v4:E1-07': {'id': 'v4:E1-07', 'name': '순찰표 원본과 공용 사본',
                     'text': '원본은 두 사람이 합류한 뒤 함께 움직였다고 적었다. 사본의 연속 동행 표현은 나중에 붙었다. 서명은 합류 이전의 동선을 보증하지 않는다.'},
        'v4:E1-02': {'id': 'v4:E1-02', 'name': '전면 문 센서',
                     'text': '전면 A 문의 개폐가 감지된다. 누가 손잡이를 잡았는지, 닫힌 문 안에 사람이 있었는지는 기록하지 않는다.'},
        'v4:E1-09': {'id': 'v4:E1-09', 'name': '외부 발신 장비 상태',
                     'text': '외부 발신에 실패했다. 내부 호출기의 연결과 별개이며 장비의 상태만으로 어느 사람이 커버를 열었는지 알 수 없다.'},
        'v4:E1-08': {'id': 'v4:E1-08', 'name': '보호대 지급 내역',
                     'text': '나나는 두 사람이 치료함 앞에 함께 섰을 때 새 보호대를 지급했다. 그보다 앞서 두 사람이 어디에 있었는지는 확인하지 못했다.'},
        'v4:E1-01': {'id': 'v4:E1-01', 'name': '래피 파일의 검안 소견',
                     'text': '목에 한 방향으로 지속된 압박이 있었다. 기록에는 넓은 사망 추정 범위가 있으며 정확한 시각이나 사람 이름은 없다.'},
        'v4:E1-11': {'id': 'v4:E1-11', 'name': '서리와 가구 위치의 사진 대조',
                     'text': '서리가 끝나는 선과 손상 위치는 이어지지 않는다. 긴 책상에는 발견 자세에서 목이 끼일 높이와 모양의 고정면이 없다.'},
        'v4:E1-03': {'id': 'v4:E1-03', 'name': '보수문 보강판과 고정 창',
                     'text': '바깥 고정 보강판과 창의 구조는 통과할 수 있는 개구부를 만들지 않는다. 안쪽의 손잡이가 움직이는 것과는 별개다.'},
        'v4:E1-13': {'id': 'v4:E1-13', 'name': '휴게실 내선과 창구의 응답',
                     'text': '외부 발신 실패와 달리 휴게실과 창구의 내선은 연결됐다. 아카리가 서로 다른 두 목소리를 듣다가 표시등이 꺼졌다. 방의 벽에서 분리된 선을 확인했다.'},
        'v4:E1-APP': {'id': 'v4:E1-APP', 'name': '외부 통화 공지와 접수 신청서',
                      'text': '래피는 신청한 사람에게 한 번을 주며 새 사람에게 넘겨주지 않는다고 말했다. 카에데가 자기 이름으로 신청서를 냈다.'},
        'v4:E1-DISC': {'id': 'v4:E1-DISC', 'name': '첫 입실과 촬영 순서의 대조',
                       'text': '미오는 첫 입실 때 바닥에 종이가 놓인 위치를 보았다. 아카리가 뒤이어 와서 발견이 성립한 후 하루카가 처음 사진을 찍었다. 첫 시야에서는 본문을 읽지 못했다.'},
        'v4:E1-PHOTO': {'id': 'v4:E1-PHOTO', 'name': '발견 뒤 남긴 첫 사진',
                        'text': '하루카의 카메라에 남은 첫 사진이다. 촬영할 때의 배치를 남겼으며 그전에 누가 무엇을 보았는지는 이 한 장으로 확인할 수 없다.'},
        'v4:E1-04': {'id': 'v4:E1-04', 'name': '출력 순서와 앞마당 사진',
                     'text': '앞선 점검 때 마지막 출력은 16번이었다. 하루카의 마당 사진에서 그때 두 사람이 함께 앞문으로 나온 모습이 확인된다. 사진 이후에도 둘이 같은 곳에 있었음을 보증하지 않는다.'},
        'v4:E1-05': {'id': 'v4:E1-05', 'name': '17번 보고서의 찢긴 모서리',
                     'text': '바닥에서 발견한 17번 보고서에는 작동 확인 불가라고 쓰여 있다. 같은 모서리가 온전한 16번은 앞선 점검의 사본이다.'},
        'v4:E1-06': {'id': 'v4:E1-06', 'name': '쓰던 보호대에서 회수한 조각',
                     'text': '나나가 발견 전에 쓰던 보호대를 벗겼을 때 안쪽에서 회수했다. 새 봉투를 뜯은 것은 그 뒤다.'},
        'v4:E1-PAPER': {'id': 'v4:E1-PAPER', 'name': '16번 출력과 17번 조각 대조',
                        'text': '회수 조각과 17번 보고서의 결손이 맞물린다. 앞선 점검에서 확인된 마지막 출력은 16번이다. 이 대조만으로 누가 인쇄하거나 찢었는지는 알 수 없다.'},
        'v4:E1-SIGHT': {'id':'v4:E1-SIGHT','name':'두 목격자의 위치와 보이는 끝',
                        'text':'나나는 다시 들어오는 카에데의 얼굴을 자기 위치에서 보았다. 아카리는 창구에서 앞문을 보았으나 벽 반대편 복도는 보지 못했다. 두 시야가 한 사람이 전후 복도를 계속 본 기록은 아니다.'},
    }
    assert any(line.startswith('정답 E1-07 → 4.') for line in scene.body[ns:pn])
    assert any('E1-02로 아래 열 약점' in line for line in scene.body[pn:])
    ns_rows = []
    for offset in range(ns + 1, pn):
        if m := STMT.match(scene.body[offset]):
            index, speaker, raw, role = m.groups()
            target = int(index) == 4
            assert ('약점' in role) == target
            ns_rows.append(debate_statement(ns_id, index, speaker, raw, scene.source(scene.line + offset + 1),
                                            'weak' if target else 'plain', 'v4:E1-07' if target else '', 8 if target else None))
    assert len(ns_rows) == 15
    pn_rows = []
    lanes = [{'id': lane, 'actor': SPEAKERS[speaker], 'speaker': speaker, 'lines': []}
             for lane, speaker in zip(('왼쪽', '가운데', '오른쪽'), ('타이가', '린', '코토'))]
    for offset in range(pn + 1, len(scene.body)):
        parts = [p.strip() for p in scene.body[offset].strip('|').split('|')]
        if len(parts) != 4 or not parts[0].isdigit():
            continue
        beat = int(parts[0])
        for index, (lane, raw) in enumerate(zip(lanes, parts[1:])):
            target = (beat, index) == (6, 2)
            loud = '[큰 소리]' in raw
            assert ('약점.' in raw) == target
            assert loud == ((beat, index) == (5, 0))
            source = scene.source(scene.line + offset + 1)
            spoken = raw.removesuffix(' 약점.')
            kind = 'weak' if target else 'plain'
            row = debate_statement(pn_id, f'{index}:{beat}', lane['speaker'], spoken, source,
                                    kind, 'v4:E1-02' if target else '')
            pn_rows.append(row)
            lane['lines'].append(row['id'])
            if loud:
                interruption = debate_statement(pn_id, 'noise', lane['speaker'], spoken, source, 'noise')
                interruption.update(noiseRole='loud', noiseDurability=2, hostStatement=row['id'])
                pn_rows.append(interruption)
    assert all(len(lane['lines']) == 7 for lane in lanes)

    def bundle(ident, kind, title, rows, answer, lanes):
        options = list(evidence.values())
        return {'taskId': ident, 'ready': True, 'bindings': [], 'requiresEvidence': [answer],
                'scopeOnlyEvidence': False, 'outcomes': {}, 'transformation': {},
                'stage': {'id': ident, 'v4': True, 'title': title, 'kind': kind, 'question': '', 'script': [],
                          'filterOwnedEvidence': True, 'lines': rows, 'options': options,
                          'presentation': {'music': {'operation': 'play', 'cue': 'bgm_trial_' + kind}}},
                'debate': {'id': ident, 'kind': kind, 'title': title, 'lines': rows, 'bullets': options, 'lanes': lanes},
                'queues': {'intro': [], 'wrong': [], 'success': [], 'wrongVariants': []}}

    tasks = {ns_id: bundle(ns_id, 'nonstop', '같은 줄에 있었다', ns_rows, 'v4:E1-07', []),
             pn_id: bundle(pn_id, 'panic', '문이 보증하는 사람', pn_rows, 'v4:E1-02', lanes)}
    tasks[ns_id]['stage']['authoredAmmo'] = ['v4:E1-07', 'v4:E1-02', 'v4:E1-09']
    tasks[pn_id]['stage']['options'] = tasks[pn_id]['debate']['bullets'] = [
        evidence[key] for key in tasks[ns_id]['stage']['authoredAmmo']]
    tasks[pn_id]['debate']['synchronizedBeats'] = True
    graph = CampaignGraph()
    dead = ['kaede']
    seats = [name for name in SPEAKERS.values() if name != 'lappy']
    tail = graph.add('rev:01:excerpt-end', type='end')
    hearing = scenes['01-T02']
    first = hearing.body.index('#### 논스톱 — 옆에 서 있었던 시간')
    timing = hearing.body.index('#### 시간대 지목 — 내가 못 본 시간에 어디 갔어')
    accident = hearing.body.index('#### 논스톱 B — 사고라는 설명')
    timeline = next(i for i in range(timing, accident) if hearing.body[i].startswith('플레이어는 순찰의'))

    def hearing_task(ident, start, stop, target, answer, ammo, wrong, next_node, precision=None, source_scene=None,
                     refute_instead=None):
        section = source_scene or hearing
        rows = []
        for offset in range(start + 1, stop):
            if match := STMT.match(section.body[offset]):
                index, speaker, raw, role = match.groups()
                weak = int(index) == target
                assert weak == ('약점' in role or '논파점' in role or (refute_instead is not None and '동의점' in role))
                if weak and refute_instead is not None:
                    speaker, raw = refute_instead
                row = debate_statement(ident, index, speaker, raw, section.source(section.line + offset + 1),
                                       'weak' if weak else 'plain', answer if weak else '')
                if weak and precision is not None:
                    at, glyph = precision
                    assert row['weak']['word'][at] == glyph
                    row['vpoint'] = {'glyphIndex': row['weak']['start'] + at}
                rows.append(row)
        assert sum('weak' in row for row in rows) == 1
        title = section.body[start].partition(' — ')[2]
        task = bundle(ident, 'nonstop', title, rows, answer, [])
        task['stage']['authoredAmmo'] = ammo
        task['stage']['options'] = task['debate']['bullets'] = [evidence[key] for key in ammo]
        wrong_at, wrong_card, wrong_actor, *authored_adaptation = wrong
        text, = authored_adaptation or re.findall(r'“([^”]+)”', section.body[wrong_at])
        task['stage']['wrongCards'] = {wrong_card: 'unmatched-record'}
        task['queues']['wrongVariants'] = [{'cause': 'unmatched-record', 'script': [
            {'id': ident + ':wrong', 'type': 'say', 'actor': SPEAKERS[wrong_actor], 'speaker': wrong_actor,
             'text': text, 'source': section.source(section.line + wrong_at + 1)}]}]
        tasks[ident] = task
        return graph.add('rev:01:' + ident, type='task', taskId=ident,
                         source=section.source(section.line + start + 1), trialDead=dead, seats=seats,
                         success=next_node, next=next_node)

    def mine_task(node, ident, title, question, image, regions, objects, requires, source, wrong, next_node):
        answer = regions[0][0]
        assert {key for key, _ in regions} == {obj['regionId'] for obj in objects}
        assert len(wrong) == len(regions) - 1
        tasks[ident] = {
            'taskId': ident, 'ready': True, 'requiresEvidence': requires,
            'stage': {'id': ident, 'kind': 'mindmine', 'v4': True, 'title': title, 'image': image,
                      'question': question, 'answerRegionId': answer, 'mineObjects': objects,
                      'regions': [{'id': key, 'label': label, 'correct': key == answer, 'wrongVariant': key}
                                  for key, label in regions]},
            'queues': {'wrongVariants': [
                {'cause': key, 'script': [{'id': f'{ident}:wrong:{key}', 'type': 'say', 'actor': SPEAKERS[speaker],
                  'speaker': speaker, 'text': text, 'source': source}]}
                for (key, _), (speaker, text) in zip(regions[1:], wrong)]},
        }
        return graph.add(node, type='task', taskId=ident, trialDead=dead, seats=seats,
                         source=source, success=next_node, next=next_node)

    def showdown_task(node, ident, title, waves, cards, answer, source, wrong, next_node):
        return compile_showdown(graph, tasks, dead, seats, node, ident, title, '타이가',
                                waves, cards, answer, source, wrong, next_node)

    signatures = scenes['01-T06']
    clash = signatures.body.index('#### 논의 스크럼 — 서명으로 확인할 수 있는 때')
    confrontation = signatures.body.index('#### 대면 — 그 자리에서 말해')
    revisions = signatures.body.index('#### 네가 먼저 들은 말')
    armament = signatures.body.index('#### 이론 무장 — 놓았다고 말하기까지')
    comic = signatures.body.index('#### 클라이맥스 추리 — 확인한 일을 실제 순서로 놓는다')
    final_rule = next(i for i in range(armament, comic) if signatures.body[i].startswith('마지막 네 자리를'))
    post_armament = comic_stage()
    comic_checkpoint = None
    vote_checkpoint = None
    result_task_id = None
    if post_armament:
        # The later chapter becomes reachable through the story's own vote,
        # verdict and aftermath. The paper-testimony flag is chapter-local.
        graph.nodes.pop(tail)
        tail = graph.add('rev:01:complete', type='end', chapterComplete=True, nextChapter='2')
        aftermath = scenes['01-R01']
        correction = next(i for i, row in enumerate(aftermath.body) if row.startswith('01-T04a에서'))
        common = next(i for i, row in enumerate(aftermath.body) if row.startswith('일반 경로에서는'))
        tail = graph.lines(aftermath, common + 1, len(aftermath.body), tail)
        revised = graph.lines(aftermath, correction + 1, common, tail)
        tail = graph.add('rev:01:aftermath-memory', type='branch',
                         cases=[{'flag': '01-T04a:perjury', 'equals': True, 'to': revised}], default=tail)
        tail = graph.add('rev:01:aftermath', type='stage', next=tail, scene={'space': 'hotel_rest_lounge', 'leaveCourt': True},
                         presentation={'music': {'operation': 'play', 'cue': 'bgm_daily_pro'}})
        verdict = scenes['01-R00']
        tail = chapter_verdict(graph, verdict, tail, 1)
        vote = signatures.body.index('#### 범인 투표 — 같이 있었다는 말의 끝')
        vote_source = signatures.source(signatures.line + vote + 1)
        result_task_id = 'T1-VOTE-REV01'
        vote_stage = {
            'id': result_task_id, 'kind': 'vote', 'v4': True, 'title': '같이 있었다는 말의 끝',
            'question': '이 사건의 검정은 누구인가?', 'answer': 'taiga', 'candidates': seats,
            'deadCandidatesSelectable': True, 'selectionRole': 'final-culprit-vote', 'finalVote': True,
            'presentation': {'music': {'operation': 'play', 'cue': 'bgm_trial_main_1'}},
        }
        tasks[result_task_id] = {'taskId': result_task_id, 'ready': True, 'stage': vote_stage,
                                 'queues': {'wrong': [{'id': result_task_id + ':retry', 'type': 'say', 'actor': 'mio',
                                                       'speaker': '미오', 'text': '같이 적힌 이름을 한 표로 세면 안 돼. 방 안에서 한 일을 다시 놓자.',
                                                       'source': vote_source}]}}
        tail = graph.add('rev:01:final-vote', type='task', taskId=result_task_id, trialDead=dead, seats=seats,
                         source=vote_source, success=tail, next=tail)
        tail = graph.lines(signatures, vote + 1, len(signatures.body), tail)
        vote_checkpoint = graph.add('rev:01:vote-court-entry',type='stage',enterCourt=True,next=tail)
        comic_id = post_armament['id']
        comic_source = signatures.source(signatures.line + comic + 1)
        tasks[comic_id] = {'taskId': comic_id, 'ready': True, 'stage': post_armament, 'queues': {},
                           'requiresEvidence': ['v4:E1-04', 'v4:E1-05', 'v4:E1-06', 'v4:E1-07', 'v4:E1-13']}
        tail = graph.add('rev:01:final-comic', type='task', taskId=comic_id, trialDead=dead, seats=seats,
                         source=comic_source, success=tail, next=tail)
        comic_checkpoint = graph.add('rev:01:comic-court-entry', type='stage', enterCourt=True, next=tail)
    final_phrase, = re.findall(r'\*\*([^*]+)\*\*', signatures.body[final_rule])
    final_fragments = final_phrase.split(' / ')
    assert len(final_fragments) == 4
    armament_id = 'T1-AA-REV01'
    waves, claims, feedback = [], [], []
    wave_text = [
        ('쇼', '지속 압박은 검안과 현장을 맞췄을 때 남는 손상입니다. 어느 쪽이 문에 서 있었는지는 그 손상으로 알 수 없습니다.'),
        ('나나', '처치하러 오신 때에는 다른 분이 도움이 필요하다는 말씀을 듣지 못했어요. 그전에 구조가 가능했는지는 다른 질문이에요.'),
        ('소라', '두 사람이 같이 적었다는 줄하고 내가 직접 만난 때는 달라. 맞는 순서대로 다시 적을 거야.'),
    ]
    for offset in range(armament + 1, final_rule):
        cols = [part.strip() for part in signatures.body[offset].strip('|').split('|')]
        if len(cols) != 3 or not cols[0].isdigit():
            continue
        phase = int(cols[0])
        source = signatures.source(signatures.line + offset + 1)
        lines = re.findall(r'“([^”]+)”', cols[1])
        assert len(lines) == 4
        wave = {'id': f'{armament_id}:wave:{phase}', 'pairs': []}
        for index, text in enumerate(lines):
            claim = {'id': f'{armament_id}:{phase}:{index}', 'type': 'say', 'actor': 'taiga',
                     'speaker': '타이가', 'text': text, 'source': source}
            claims.append(text)
            wave['pairs'].append({'claim': claim})
        waves.append(wave)
        speaker, text = wave_text[phase - 1]
        feedback.append([{'id': f'{armament_id}:wave:{phase}:evidence', 'type': 'say', 'actor': SPEAKERS[speaker],
                          'speaker': speaker, 'text': text, 'source': source}])
    assert len(waves) == 3
    armament_source = signatures.source(signatures.line + armament + 1)
    post_rhythm = next(i for i in range(armament, final_rule) if SAY.match(signatures.body[i]))
    tail = graph.lines(signatures, post_rhythm, final_rule, tail)
    tasks[armament_id] = {'taskId': armament_id, 'ready': True,
                          'requiresEvidence': ['v4:E1-01', 'v4:E1-07', 'v4:E1-11', 'v4:E1-13'],
                          'stage': {'id': armament_id, 'kind': 'armament', 'v4': True, 'title': '놓았다고 말하기까지',
                                    'chapter': 1, 'opponent': 'taiga', 'lines': claims, 'waves': waves, 'phaseTranscripts': True,
                                    'phaseFeedback': feedback[:2], 'question': '확인한 네 단서를 사건의 순서로 놓아라',
                                    'finalSubject': '남은 순서는', 'final': final_fragments},
                          'queues': {'success': feedback[-1]}}
    tail = graph.add('rev:01:pressure-armament', type='task', taskId=armament_id, trialDead=dead, seats=seats,
                     source=armament_source, success=tail, next=tail)
    armament_checkpoint = graph.add('rev:01:armament-court-entry', type='stage', enterCourt=True, next=tail)
    order_source = signatures.source(signatures.line + revisions + 1)
    tail = graph.lines(signatures, revisions + 2, armament, tail)
    order_id = 'T1-QA-REV05'
    tasks[order_id] = {'taskId': order_id, 'ready': True, 'requiresEvidence': ['v4:E1-07'],
                       'stage': {'id': order_id, 'kind': 'choice', 'v4': True,
                                 'question': '누가 어디에 쓴 문장인지 맞춰 놓으면?',
                                 'options': ['합류 → 둘이 같이 돌아옴 → 연속 동행',
                                             '합류 → 연속 동행 → 둘이 같이 돌아옴',
                                             '연속 동행 → 합류 → 둘이 같이 돌아옴'], 'answer': 1},
                       'queues': {'wrongVariants': [
                           {'optionIndex': index, 'script': [{'id': f'{order_id}:wrong:{index}', 'type': 'say',
                            'actor': SPEAKERS[speaker], 'speaker': speaker, 'text': text, 'source': order_source}]}
                           for index, speaker, text in [(0, '하루카', '마지막은 공용판이야. 미오가 쓴 글씨부터 찾아봐.'),
                                                        (2, '소라', '합류부터 썼어. 그 줄에 그 말이 처음부터 있었다고 읽지 마.')]]}}
    tail = graph.add('rev:01:patrol-writing-order', type='task', taskId=order_id, trialDead=dead, seats=seats,
                     source=order_source, success=tail, next=tail)
    tail = graph.lines(signatures, confrontation + 1, revisions, tail)
    scrum_id = 'T1-SD-REV01'
    topics = ('합류', '처치', '사본', '행위')
    claim_words = ('서명', '진료', '두 이름', '순찰표')
    response_words = ('함께 있었는지', '오셨을 때', '공용판', '행동')
    pairs = []
    for i in range(clash + 1, confrontation):
        parts = [part.strip() for part in signatures.body[i].strip('|').split('|')]
        if len(parts) != 2 or '“' not in parts[0]:
            continue
        them, claim = re.fullmatch(r'(\S+)\s+“([^”]+)”', parts[0]).groups()
        us, response = re.fullmatch(r'\S+\. (\S+)\s+“([^”]+)”', parts[1]).groups()
        index = len(pairs)
        ref = signatures.source(signatures.line + i + 1)
        pair_id = f'{scrum_id}:{index}'
        pair = {'id': pair_id, 'them': them, 'themActor': SPEAKERS[them], 'themText': claim, 'us': us,
                'usActor': SPEAKERS[us], 'usText': response, 'keyword': topics[index], 'claimKeyword': claim_words[index],
                'responseKeyword': response_words[index], 'duration': 10,
                'wrong': [{'id': pair_id + ':retry', 'type': 'say', 'actor': SPEAKERS[us], 'speaker': us,
                           'text': ['서명하기 전의 일까지 두 사람이 같이 본 것은 아니야. 합류를 다시 봐.',
                                    '두 분이 같이 계신 것을 확인한 때는 처치하러 오셨을 때입니다.',
                                    '공용판은 옮겨 적은 한 문장이에요. 두 증언을 대신할 수는 없어요.',
                                    '표에서 문장을 지워도 그 방에 있었던 행동이 사라지지 않습니다.'][index],
                           'source': ref}]}
        assert pair['claimKeyword'] in claim and pair['responseKeyword'] in response
        pairs.append(pair)
    assert len(pairs) == 4
    scrum_source = signatures.source(signatures.line + clash + 1)
    decoy_source = next(i for i in range(clash, confrontation) if signatures.body[i].startswith('방해 화제는'))
    decoy_response, = re.findall(r'“([^”]+)”', signatures.body[decoy_source])
    pairs[-1]['wrongByKeyword'] = {'출력 번호': [{'id': scrum_id + ':output-retry', 'type': 'say',
                                                 'actor': 'rei', 'speaker': '레이', 'text': decoy_response,
                                                 'source': signatures.source(signatures.line + decoy_source + 1)}]}
    tasks[scrum_id] = {'taskId': scrum_id, 'ready': True, 'requiresEvidence': ['v4:E1-07', 'v4:E1-08'],
                       'stage': {'id': scrum_id, 'kind': 'scrum', 'v4': True, 'title': '서명으로 확인할 수 있는 때',
                                 'pairs': pairs, 'teams': {'them': [pair['themActor'] for pair in pairs],
                                                           'us': [pair['usActor'] for pair in pairs]},
                                 'scrumDecoys': [{'keyword': name} for name in ('창구 소리', '출력 번호', '보수판')],
                                 'scrumPresentation': {'topic': '서명으로 어디까지 확인할 수 있나',
                                                       'them': '순찰표가 그 시간을 보증한다',
                                                       'us': '직접 함께한 구간만 보증한다'}},
                       'queues': {}}
    tail = graph.add('rev:01:signature-scrum', type='task', taskId=scrum_id, trialDead=dead, seats=seats,
                     source=scrum_source, success=tail, next=tail)
    registration = scenes['01-T05a']
    anagram = next(i for i, raw in enumerate(registration.body) if raw.startswith('#### 섬광 애너그램'))
    end_rule = next(i for i in range(anagram, len(registration.body)) if SAY.match(registration.body[i]))
    tail = graph.lines(registration, end_rule, len(registration.body), tail)
    registration_id = 'T1-AN-REV02'
    answer, decoys, question = ANAGRAMS['01-T05a']
    wrong_words = ('수화자', '공동서명', '신고자')
    lines = [re.findall(r'“([^”]+)”', raw)[0] for raw in registration.body[anagram:end_rule]
             if any(raw.startswith(f'- **{word}**') for word in wrong_words)]
    assert len(lines) == 3
    tasks[registration_id] = {'taskId': registration_id, 'ready': True, 'requiresEvidence': ['v4:E1-APP', 'v4:E1-13'],
                              'stage': {'id': registration_id, 'kind': 'anagram', 'v4': True,
                                        'question': question, 'answer': answer, 'distractors': list(decoys),
                                        'wrongText': {word: speaker + '  ' + text for word, speaker, text in
                                                      zip(wrong_words, ('나나', '소라', '미오'), lines)}}, 'queues': {}}
    tail = graph.add('rev:01:registration-anagram', type='task', taskId=registration_id, trialDead=dead, seats=seats,
                     source=registration.source(registration.line + anagram + 1), success=tail, next=tail)
    tail = graph.lines(registration, 0, anagram, tail)
    signature_checkpoint = graph.add('rev:01:signature-court-entry', type='stage', enterCourt=True, next=tail)

    rescue = scenes['01-T05']
    rescue_intro = next(i for i, raw in enumerate(rescue.body) if raw.startswith('#### 논스톱 동의'))
    rescue_duel = rescue.body.index('#### 반론 쇼다운 — 도움을 주러 갔다는 주장')
    rescue_ns = rescue.body.index('#### 논스톱 E — 사람보다 먼저 끊긴 전화')
    help_rule = next(i for i in range(rescue_intro, rescue_duel) if rescue.body[i].startswith('01-D04의 두 번 노크'))
    phone_rule = next(i for i in range(rescue_ns, len(rescue.body)) if rescue.body[i].startswith('E1-13 → 4.'))
    phone_end = next((i for i in range(phone_rule, len(rescue.body)) if rescue.body[i].startswith('#### ')), len(rescue.body))
    panic_heading = rescue.body.index('#### 패닉 — 창에 대고 밖에서 말했다면')
    witness_picker = rescue.body.index('#### 인물 지목 — 앞문 쪽에서 들을 수 있던 사람')
    statement_picker = rescue.body.index('#### 발언 지목 — 두 사람이 다퉜다는 말의 출처')
    reasoning_heading = rescue.body.index('#### 추리 연결 — 마지막으로 만난 사람')
    pressure_heading = rescue.body.index('#### 논스톱 — 종이보다 오래 남은 손')
    pressure_rule = next(i for i in range(pressure_heading, len(rescue.body)) if rescue.body[i].startswith('E1-01 검안과 E1-11'))
    pressure_end = rescue.body.index('#### 반론 쇼다운 — 다친 손으로 누른다면')
    hand_rule = next(i for i in range(pressure_end, len(rescue.body)) if rescue.body[i].startswith('플레이어가 생활 때의 실제 사용'))
    hand_source = rescue.source(rescue.line + hand_rule + 1)
    hand = {'id': 'v4:E1-HAND', 'name': '그날 손으로 했다고 인정한 행동',
            'text': '손목 통증이 있던 상태에서 타이가는 종이를 잡고 내선 연결을 직접 끊었다고 인정했다. 통증이나 손을 쓴 사실만으로 지속 압박이 입증되지는 않는다.'}
    hands_at = next(i for i in range(pressure_end, hand_rule) if rescue.body[i].startswith('첫 파에서'))
    ordinary_hand_claims = re.findall(r'‘([^’]+)’', rescue.body[hands_at])[:3]
    assert len(ordinary_hand_claims) == 3
    weak, = re.findall(r'“([^”]+)”', rescue.body[hands_at])
    hand_feedback, _ = re.findall(r'“([^”]+)”', rescue.body[hand_rule])
    hand_end = next((i for i in range(hand_rule + 1, len(rescue.body)) if rescue.body[i].startswith('#### ')), len(rescue.body))
    tail = graph.lines(rescue, hand_rule + 1, hand_end, tail)
    tail = showdown_task('rev:01:hand-use-showdown', 'T1-RS-REV02', '다친 손으로 누른다면',
                         (ordinary_hand_claims, ['손목이 아프면 오래 잡고 있을 수 없어.', weak]),
                         [evidence['v4:E1-08'], evidence['v4:E1-01'], hand], hand['id'], hand_source,
                         ('나나', hand_feedback), tail)
    tail = graph.add('rev:01:hand-use-record', type='evidence', evidenceId=hand['id'], name=hand['name'],
                     text=hand['text'], source=hand_source, next=tail)
    tail = graph.lines(rescue, pressure_end + 1, hand_rule, tail)
    tail = graph.lines(rescue, pressure_rule + 1, pressure_end, tail)
    pressure_correction, _ = re.findall(r'“([^”]+)”', rescue.body[pressure_rule])
    tail = hearing_task('T1-NS-REV14', pressure_heading, pressure_rule, 4, 'v4:E1-11',
                        ['v4:E1-06', 'v4:E1-13', 'v4:E1-11'], (pressure_rule, 'v4:E1-06', '타이가', pressure_correction),
                        tail, source_scene=rescue)
    start_reply = next(i for i in range(reasoning_heading, pressure_heading) if SAY.match(rescue.body[i]))
    tail = graph.lines(rescue, start_reply, pressure_heading, tail)
    reasoning_id = 'T1-RE-REV01'
    reasoning = [
        ('입실에서 마지막 퇴실까지를 좁히는 관찰은?', '앞문을 본 아카리와 문 움직임 기록', '인쇄 일련번호', '순찰표의 두 이름',
         '출력 순서나 순찰표의 이름으로 문에서 본 움직임을 대신할 수 없어.', '보수문과 앞문은 같은 출입로가 아니야. 실제 퇴실을 본 쪽부터 놓을게.'),
        ('누구의 현장 접촉을 물을 수 있나?', '발견 전 회수 조각이 붙었던 보호대를 건넨 사람', '새 용지를 확인한 사람', '마지막에 들어온 사람',
         '종이가 닿았다는 근거가 누구의 물건에 있었는지부터 찾아.', '나나가 보호대를 받아 조각을 확인한 시점은 발견 전이야.'),
        ('들어가기 전에 이미 쓰러졌다는 말과 함께 놓을 수 없는 기록은?', '입실 뒤 연결된 내선의 두 사람 대답', '17번 번호', '새 보호대 지급',
         '출력 번호나 처치 내역은 입실 뒤 방 안의 반응을 말해 주지 않아.', '입실 뒤에도 대답이 이어졌다는 사실을 시간판에 놓자.'),
        ('제삼자가 먼저 들어가 남아 있었다면 무엇을 함께 설명해야 하나?', '앞선 퇴실, 닫힌 문, 이어 받은 시야와 실내의 구조', '순찰 시작 시각', '문 닫힘 표찰만',
         '닫혔다는 표시만 보면 그전부터 어디에 있었는지는 안 나와.', '먼저 둘이 나온 뒤 다음 입실까지 열린 시야와 구조를 같이 봤어.'),
        ('두 사람이 만난 뒤의 행동을 확인할 자료는?', '검안과 현장을 대조한 손상 기록', '보고서의 찢긴 모서리', '손목 통증',
         '접촉의 흔적이나 아픈 손만으로 몸에 남은 손상을 설명할 수는 없어.', '이제 남은 압박이 어떤 힘을 필요로 했는지 별도로 읽을 수 있어.'),
        ('앞문을 나간 모습과 종이 접촉의 관찰은 어느 순서야?', '두 사람의 내선 → 관찰된 퇴실 → 처치 중 조각 확인',
         '순찰 서명 → 나나가 내선을 들음 → 아카리가 퇴실자의 이름을 씀', '17번 출력 → 센서가 퇴실자의 신원을 확인 → 손목 처치',
         '목소리를 들은 자리와 얼굴이 가려진 문턱에 같은 이름을 쓸 수는 없어.', '문에서 본 모습과 나중에 실제로 확인한 물건은 별개의 자료야.'),
        ('퇴실을 관찰한 것만으로 치명 행위까지 판단하려면 무엇이 더 필요해?', '실제 손상에 필요한 힘의 방향과 지속, 그리고 방의 구조',
         '손목이 아팠다는 말에서 감정을 추측', '퇴실자의 얼굴을 보지 못했으니 사건이 없다고 판단',
         '아팠다는 말과 얼굴을 못 봤다는 말은 실제로 어떤 힘이 남았는지를 설명하지 않아.', '검안과 최초 위치, 방 안의 실제 구조를 겹쳐 보자.'),
    ]
    questions = []
    for index, (q, right, wrong_a, wrong_b, correction, success) in enumerate(reasoning):
        line = next(i for i in range(reasoning_heading, start_reply) if rescue.body[i].startswith(f'{index+1}. '))
        ref = rescue.source(rescue.line + line + 1)
        choices = [('wrong-a', wrong_a), ('wrong-b', wrong_b)]
        choices.insert(index % 3, ('right', right))
        def feedback(event, text, speaker='미오'):
            return [{'type': 'say', 'id': f'{reasoning_id}:{index}:{event}', 'actor': SPEAKERS[speaker], 'speaker': speaker,
                     'text': text, 'source': ref}]
        corrections = [('미오', correction), ('미오', correction)]
        if index == 5:
            success, *wrong = re.findall(r'“([^”]+)”', rescue.body[line])
            corrections = list(zip(('나나', '린'), wrong))
        elif index == 6:
            wrong = re.findall(r'“([^”]+)”', rescue.body[line])
            corrections = list(zip(('타이가', '하루카'), wrong))
        assert len(corrections) == 2
        questions.append({'q': q, 'answer': right, 'options': [text for _, text in choices],
                          'optionIds': [key for key, _ in choices],
                          'success': feedback('success', success, '아카리' if index == 5 else '미오'),
                          'wrongVariants': [{'optionId': key, 'script': feedback(key, text, speaker)}
                                            for key, (speaker, text) in zip(('wrong-a', 'wrong-b'), corrections)]})
    tasks[reasoning_id] = {'taskId': reasoning_id, 'ready': True,
                           'requiresEvidence': ['v4:E1-02', 'v4:E1-03', 'v4:E1-06', 'v4:E1-11', 'v4:E1-13'],
                           'stage': {'id': reasoning_id, 'kind': 'reasoning', 'v4': True,
                                     'title': '마지막으로 만난 사람', 'questions': questions},
                           'queues': {}}
    tail = graph.add('rev:01:last-contact-reasoning', type='task', taskId=reasoning_id, trialDead=dead, seats=seats,
                     source=rescue.source(rescue.line + reasoning_heading + 1), success=tail, next=tail)
    phone_evidence_checkpoint = graph.add('rev:01:phone-evidence-court-entry', type='stage', enterCourt=True, next=tail)
    testimony_id = 'T1-PE-REV03'
    at = next(i for i in range(statement_picker, reasoning_heading) if SAY.match(rescue.body[i]))
    tail = graph.lines(rescue, at, reasoning_heading, tail)
    statement_source = rescue.source(rescue.line + statement_picker + 1)
    tasks[testimony_id] = {'taskId': testimony_id, 'ready': True, 'requiresEvidence': ['v4:E1-13'],
                           'stage': {'id': testimony_id, 'kind': 'person', 'v4': True,
                                     'question': '당시 누가 먼저 손을 댔다고 지금 주장하는 사람은?',
                                     'answer': 'taiga', 'candidates': ['rin', 'taiga', 'akari']},
                           'queues': {'wrongVariants': [{'optionIndex': option, 'script': [
                               {'id': f'{testimony_id}:wrong:{option}', 'type': 'say', 'actor': SPEAKERS[speaker],
                                'speaker': speaker, 'text': text, 'source': statement_source}]}
                               for option, speaker, text in [(0, '린', '다른 날 지적하는 건 봤어. 사건 날에 둘이 부딪친 건 못 봤고.'),
                                                             (2, '아카리', '두 목소리를 들었어요. 누가 먼저 손을 댔는지는 볼 수 없었습니다.')]]}}
    tail = graph.add('rev:01:claim-origin', type='task', taskId=testimony_id, trialDead=dead, seats=seats,
                     source=statement_source, success=tail, next=tail)
    at = next(i for i in range(witness_picker, statement_picker) if SAY.match(rescue.body[i]))
    tail = graph.lines(rescue, at, statement_picker, tail)
    exit_id = 'T1-PE-REV02'
    exit_source = rescue.source(rescue.line + witness_picker + 1)
    tasks[exit_id] = {'taskId': exit_id, 'ready': True, 'requiresEvidence': ['v4:E1-02', 'v4:E1-13'],
                      'stage': {'id': exit_id, 'kind': 'person', 'v4': True,
                                'question': '마당에서 앞문을 본 사람의 관찰을 누구에게 확인할까?',
                                'answer': 'akari', 'candidates': ['nana', 'akari', 'sora', 'rei']},
                      'queues': {'wrongVariants': [{'optionIndex': option, 'script': [
                          {'id': f'{exit_id}:wrong:{option}', 'type': 'say', 'actor': SPEAKERS[speaker],
                           'speaker': speaker, 'text': text, 'source': exit_source}]}
                          for option, speaker, text in [(0, '나나', '돌아오신 때는 보았어요. 앞문에 계속 있지는 않았습니다.'),
                                                        (2, '소라', '내가 본 건 순찰 뒤에 다시 만난 때야. 휴게실 앞이라고 말한 적 없어.'),
                                                        (3, '레이', '제가 확인한 것은 장치의 상태입니다. 그 뒤 앞문에 누가 있었는지는 다른 기록으로 보십시오.')]]}}
    tail = graph.add('rev:01:front-exit-witness', type='task', taskId=exit_id, trialDead=dead, seats=seats,
                     source=exit_source, success=tail, next=tail)
    panic_id = 'T1-PN-REV02'
    answer = 'v4:E1-03'
    rule = next(i for i in range(panic_heading, witness_picker) if rescue.body[i].startswith('정답은 **E1-03'))
    lanes = [{'id': label, 'actor': SPEAKERS[name], 'speaker': name, 'lines': []}
             for label, name in (('왼쪽', '타이가'), ('가운데', '코토'), ('오른쪽', '아카리'))]
    rows = []
    for offset in range(panic_heading + 1, rule):
        cells = [part.strip() for part in rescue.body[offset].strip('|').split('|')]
        if len(cells) != 4 or not cells[0].isdigit():
            continue
        beat = int(cells[0])
        for index, (lane, raw) in enumerate(zip(lanes, cells[1:])):
            source = rescue.source(rescue.line + offset + 1)
            weak = (beat, index) == (4, 1)
            row = debate_statement(panic_id, f'{index}:{beat}', lane['speaker'], raw.removesuffix(' 약점.'), source,
                                   'weak' if weak else 'plain', answer if weak else '')
            rows.append(row)
            lane['lines'].append(row['id'])
            if '[큰 소리]' in raw:
                assert (beat, index) == (3, 0)
                noise = debate_statement(panic_id, 'noise', lane['speaker'], raw, source, 'noise')
                noise.update(noiseRole='loud', noiseDurability=2, hostStatement=row['id'])
                rows.append(noise)
    assert len(rows) == 13
    task = bundle(panic_id, 'panic', '창에 대고 밖에서 말했다면', rows, answer, lanes)
    task['stage']['options'] = task['debate']['bullets'] = [evidence[key] for key in ('v4:E1-13', 'v4:E1-02', answer)]
    task['debate']['synchronizedBeats'] = True
    tasks[panic_id] = task
    tail = graph.lines(rescue, rule + 1, witness_picker, tail)
    tail = graph.add('rev:01:fixed-window-panic', type='task', taskId=panic_id, trialDead=dead, seats=seats,
                     source=rescue.source(rescue.line + panic_heading + 1), success=tail, next=tail)
    tail = graph.lines(rescue, panic_heading + 1, next(i for i in range(panic_heading, rule)
                       if rescue.body[i].startswith('세 목소리를')), tail)
    call_at = next(i for i in range(phone_end, panic_heading) if rescue.body[i].startswith('재현에서 **안쪽 수화기'))
    call_source = rescue.source(rescue.line + call_at + 1)
    tail = graph.lines(rescue, call_at + 1, panic_heading, tail)
    call_id = 'T1-QA-REV04'
    tasks[call_id] = {'taskId': call_id, 'ready': True, 'requiresEvidence': ['v4:E1-13', 'v4:E1-09'],
                      'stage': {'id': call_id, 'kind': 'choice', 'v4': True, 'question': '창구까지 소리가 도착한 경로는?',
                                'options': ['벽 창으로 직접 들음', '휴게실과 창구를 잇는 수화기', '바깥으로 거는 발신장치'],
                                'answer': 1},
                      'queues': {'wrongVariants': [{'optionIndex': index, 'script': [
                          {'id': f'{call_id}:wrong:{index}', 'type': 'say', 'actor': SPEAKERS[speaker],
                           'speaker': speaker, 'text': text, 'source': call_source}]}
                          for index, speaker, text in [(0, '아카리', '장치의 표시를 보고 수화기를 들었어요. 창을 열어서 들은 게 아니에요.'),
                                                       (2, '레이', '창구와 휴게실은 이어졌지만, 바깥으로 거는 시험에서는 연결되지 않았습니다.')]]}}
    tail = graph.add('rev:01:call-route', type='task', taskId=call_id, trialDead=dead, seats=seats,
                     source=call_source, success=tail, next=tail)
    tail = graph.lines(rescue, phone_end + 1, call_at, tail)
    phone_checkpoint = graph.add('rev:01:phone-court-entry', type='stage', enterCourt=True, next=tail)
    tail = graph.lines(rescue, phone_rule + 1, phone_end, tail)
    tail = hearing_task('T1-NS-REV13', rescue_ns, phone_rule, 4, 'v4:E1-13',
                        ['v4:E1-09', 'v4:E1-02', 'v4:E1-13'], (phone_rule, 'v4:E1-09', '레이'), tail,
                        source_scene=rescue)
    duel_rule = next(i for i in range(rescue_duel, rescue_ns) if rescue.body[i].startswith('상대 타이가.'))
    duel_source = rescue.source(rescue.line + duel_rule + 1)
    words = re.findall(r'“([^”]+)”', rescue.body[duel_rule])
    assert len(words) == 7
    weak_evidence = 'v4:E1-02'
    tail = graph.lines(rescue, duel_rule + 1, rescue_ns, tail)
    tail = showdown_task('rev:01:rescue-showdown', 'T1-RS-REV01', '도움을 주러 갔다는 주장',
                         (words[:3], words[3:6]), [evidence[key] for key in ('v4:E1-03', weak_evidence, 'v4:E1-13')],
                         weak_evidence, duel_source, ('타이가', words[-1]), tail)
    rescue_checkpoint = graph.add('rev:01:rescue-court-entry', type='stage', enterCourt=True, next=tail)
    rescue_support = STMT.match(next(raw for raw in rescue.body[rescue_intro:help_rule] if raw.startswith('4. ')))[3].replace('**', '')
    tail = graph.add('rev:01:discovery-call-scope', type='say', actor='haruka', speaker='하루카', text=rescue_support,
                     source=rescue.source(rescue.line + help_rule + 1), next=tail)
    tail = hearing_task('T1-NS-REV12', rescue_intro, help_rule, 4, 'v4:E1-DISC',
                        ['v4:E1-DISC', 'v4:E1-13', 'v4:E1-08'], (help_rule, 'v4:E1-13', '아카리'), tail,
                        source_scene=rescue, refute_instead=('유우', '부르는 소리가 있었다면 **문 열기 전부터 들었던 말이잖아.**'))
    report = scenes['01-T04d']
    report_round = report.body.index('#### 논스톱 — 종이에 쓰였던 말과 그다음 말')
    report_rule = next(i for i in range(report_round, len(report.body)) if report.body[i].startswith('4에 **E1-05'))
    tail = graph.lines(report, report_rule + 1, len(report.body), tail)
    tail = hearing_task('T1-NS-REV11', report_round, report_rule, 4, 'v4:E1-05',
                        ['v4:E1-06', 'v4:E1-13', 'v4:E1-05'], (report_rule, 'v4:E1-06', '리쿠',
                        '번호가 맞는 것하고 그 사람이 그때 무슨 말을 들었는지는 따로 봐야 돼.'), tail,
                        source_scene=report)
    tail = graph.lines(report, 0, report_round, tail)
    paper = scenes['01-T04']
    paper_round = paper.body.index('#### 논스톱 — 종이를 스쳤다는 설명')
    paper_rule = next(i for i in range(paper_round, len(paper.body)) if paper.body[i].startswith('4에는 E1-04'))
    lie_heading = next(i for i in range(paper_rule, len(paper.body)) if paper.body[i].startswith('#### 01-T04a'))
    regular_rule = next(i for i in range(lie_heading, len(paper.body)) if paper.body[i].startswith('일반 경로는'))
    lie_rule = next(i for i in range(regular_rule, len(paper.body)) if paper.body[i].startswith('위증 경로는'))
    lie_join = next(i for i in range(lie_rule, len(paper.body)) if paper.body[i].startswith('두 경로 모두'))
    brace_round = paper.body.index('#### 논스톱 D — 모른다고 한 시점')
    brace_rule = next(i for i in range(brace_round, len(paper.body)) if paper.body[i].startswith('E1-06 →'))
    brace_end = paper.body.index('#### 발굴 — 서로 다른 결손')
    paper_image = MINE_ART + 'report-torn-edge.webp'
    chronology = paper.body.index('#### 문서 순서 — 조각이 먼저 바닥에 떨어졌다면')
    chronology_rule = next(i for i in range(chronology, len(paper.body)) if paper.body[i].startswith('플레이어가 E1-06 확대'))
    anagram_at = paper.body.index('#### 섬광 애너그램 — 출력 순서만 가리키는 말')
    anagram_rule = paper.body[anagram_at + 2]
    question, wrong_room, wrong_plaque = re.findall(r'“([^”]+)”', anagram_rule)
    glyphs, distractors = re.findall(r'\*\*([^*]+)\*\*', anagram_rule)
    anagram_id = 'T1-AN-REV01'
    tasks[anagram_id] = {'taskId': anagram_id, 'ready': True, 'requiresEvidence': ['v4:E1-04', 'v4:E1-PAPER'],
                         'stage': {'id': anagram_id, 'v4': True, 'kind': 'anagram', 'question': question,
                                   'answer': glyphs.replace('·', ''), 'distractors': distractors.rstrip('.').split('·'),
                                   'wrongText': {'방번호': '나나  ' + wrong_room, '표찰': '레이  ' + wrong_plaque}}}
    tail = graph.lines(paper, anagram_at + 3, len(paper.body), tail)
    tail = graph.add('rev:01:number-comparison', type='document', title='두 출력물의 번호',
                     rows=['점검표의 마지막 확인 번호는 16번이다. 결손과 회수 조각은 17번 보고서에서만 맞물린다.',
                           '출력 시각과 인쇄한 사람은 기록으로 확인되지 않았다.'], image=paper_image,
                     source=paper.source(paper.line + anagram_at + 3), next=tail)
    tail = graph.add('rev:01:serial-anagram', type='task', taskId=anagram_id, trialDead=dead, seats=seats,
                     source=paper.source(paper.line + anagram_at + 3), success=tail, next=tail)
    chronology_id = 'T1-QA-REV03'
    chronology_source = paper.source(paper.line + chronology_rule + 1)
    answers = ['방 안에서 착용한 채 닿았을 때', '발견 전, 쓰던 보호대를 벗겼을 때',
               '발견 뒤 다른 사람이 넣었을 때', '처치 중 새 보호대로 옮겨 붙었을 때']
    corrections = [(0, '쇼', '조각만으로 접촉한 방을 정할 수는 없습니다. 언제 이미 있었는지부터 보십시오.'),
                   (2, '소라', '내가 치료함에 갔을 때부터 보자. 그때 방에서 사람들이 나오는 걸 봤다고 했어?'),
                   (3, '나나', '그건 새것을 준 기록이에요. 안쪽을 펼쳤던 것은 먼저 쓰던 보호대입니다.')]
    tasks[chronology_id] = {'taskId': chronology_id, 'ready': True, 'requiresEvidence': ['v4:E1-06', 'v4:E1-08'],
                            'stage': {'id': chronology_id, 'v4': True, 'kind': 'choice',
                                      'question': '조각이 이미 안쪽에 있었다는 사실은 언제 확인했어?',
                                      'options': answers, 'answer': 1},
                            'queues': {'wrongVariants': [
                                {'optionIndex': index, 'script': [{'id': f'{chronology_id}:wrong:{index}', 'type': 'say',
                                  'actor': SPEAKERS[speaker], 'speaker': speaker, 'text': text, 'source': chronology_source}]}
                                for index, speaker, text in corrections]}}
    tail = graph.lines(paper, chronology_rule + 1, anagram_at, tail)
    tail = graph.add('rev:01:paper-sequence', type='task', taskId=chronology_id, trialDead=dead, seats=seats,
                     source=chronology_source, success=tail, next=tail)
    paper_sequence_checkpoint = graph.add('rev:01:paper-sequence-court-entry', type='stage', enterCourt=True, next=tail)
    tail = graph.lines(paper, chronology + 1, chronology_rule, tail)
    tail = graph.lines(paper, brace_end + 1, chronology, tail)
    tail = graph.add('rev:01:torn-report-match', type='document', title='결손과 회수 조각',
                     rows=['인쇄선과 찢긴 모서리가 맞물린다. 누가 종이를 찢었는지는 이 대조로 확인할 수 없다.'],
                     image=paper_image, source=chronology_source, next=tail)
    tail = mine_task('rev:01:paper-mine', 'T1-MM-REV02', '서로 다른 결손', '찢긴 보고서의 빈자리를 채울 조각은?',
                     paper_image, [('torn-number', '17번의 일부와 긴 가장자리'), ('stored-number', '16번 보관 용지'),
                                   ('medical-strip', '의료용 봉투의 고정 띠'), ('check-cover', '공용 점검표 표지')],
                     paper_objects, ['v4:E1-05', 'v4:E1-06'], paper.source(paper.line + brace_end + 1),
                     [('리쿠', '번호가 찍혔어도 이쪽은 끝이 멀쩡하잖아. 찢긴 자리에 끼워 봐.'),
                      ('나나', '그건 봉투에서 나온 띠예요. 보고서에서 찢어진 종이는 아닙니다.'),
                      ('하루카', '이건 접은 표지야. 접힌 줄하고 찢긴 모서리를 같이 놓아 봐.')], tail)
    paper_mine_checkpoint = graph.add('rev:01:paper-mine-court-entry', type='stage', enterCourt=True, next=tail)
    tail = graph.lines(paper, brace_rule + 1, brace_end, tail)
    tail = hearing_task('T1-NS-REV10', brace_round, brace_rule, 4, 'v4:E1-06',
                        ['v4:E1-05', 'v4:E1-08', 'v4:E1-06'], (brace_rule, 'v4:E1-08', '나나',
                        '새 보호대를 낸 때만 적혀 있어요. 그 조각은 제가 쓰던 걸 벗겼을 때 봤습니다.'), tail,
                        source_scene=paper)
    truth_dialogue = graph.lines(paper, regular_rule + 1, lie_rule, tail)
    lie_dialogue = graph.lines(paper, lie_rule + 1, lie_join, tail)
    lie_id = 'T1-LI-REV01'
    statement_line = next(i for i in range(lie_heading, regular_rule) if paper.body[i].startswith('**타이가**'))
    lie_source = paper.source(paper.line + statement_line + 1)
    claim = speech(paper.body[statement_line], paper.line + statement_line + 1, paper)['text']
    weak_text = '내가 전에 끼던 건지 지금 거였는지'
    rows = [debate_statement(lie_id, 1, '타이가', claim.replace(weak_text, f'**{weak_text}**'), lie_source, 'weak', 'v4:E1-06'),
            debate_statement(lie_id, 2, '나나', speech(paper.body[statement_line + 2], paper.line + statement_line + 3, paper)['text'],
                             paper.source(paper.line + statement_line + 3)),
            debate_statement(lie_id, 3, '미오', '지금 찾는 건 봉투의 내용이 아니야. 벗긴 것과 건넨 것의 순서를 보자.', lie_source)]
    lie = bundle(lie_id, 'nonstop', '먼저 쓰던 것과 새 봉투', rows, 'v4:E1-06', [])
    lie['stage']['authoredAmmo'] = ['v4:E1-08', 'v4:E1-06']
    lie['stage']['options'] = lie['debate']['bullets'] = [evidence[key] for key in lie['stage']['authoredAmmo']]
    lie['transformation'] = {'sourceEvidenceId': 'v4:E1-06', 'lieLabel': '새 보호대에서 조각을 회수했다', 'intentionalHold': True}
    lie['requiresEvidence'].append('v4:E1-08')
    lie['stage']['wrongCards'] = {'v4:E1-08': 'issued-only'}
    lie['queues']['wrongVariants'] = [{'cause': 'issued-only', 'script': [{'id': lie_id + ':wrong:issued',
        'type': 'say', 'actor': 'nana', 'speaker': '나나', 'text': '봉투 안을 공개할 필요는 없어요. 어느 보호대를 먼저 벗겼는지부터 물으세요.',
        'source': paper.source(paper.line + lie_rule + 1)}]}]
    tasks[lie_id] = lie
    tail = graph.add('rev:01:brace-testimony', type='task', taskId=lie_id, trialDead=dead, seats=seats,
                     source=lie_source, success=truth_dialogue, next=truth_dialogue, outcomes={
                         'normal': {'judgment': 'refute', 'to': truth_dialogue},
                         'perjury': {'judgment': 'lie', 'to': lie_dialogue, 'sets': {'01-T04a:perjury': True}},
                     })
    tail = graph.lines(paper, lie_heading + 1, regular_rule, tail)
    tail = graph.lines(paper, paper_rule + 1, lie_heading, tail)
    issue_response, _ = re.findall(r'“([^”]+)”', paper.body[paper_rule])
    tail = hearing_task('T1-NS-REV09', paper_round, paper_rule, 4, 'v4:E1-PAPER',
                        ['v4:E1-08', 'v4:E1-04', 'v4:E1-PAPER'], (paper_rule, 'v4:E1-08', '나나', issue_response),
                        tail, source_scene=paper)
    paper_checkpoint = graph.add('rev:01:paper-court-entry', type='stage', enterCourt=True, next=tail)
    paper_entry = tail

    witness = scenes['01-T03']
    count = scenes['01-T03c']
    count_round = count.body.index('#### 논스톱 — 한 번 열리면 한 명인가')
    count_rule = next(i for i in range(count_round, len(count.body)) if count.body[i].startswith('정답은 E1-02'))
    count_resume = count.body.index('#### 문턱에서 본 둘을 나눠 보지 않는다')
    outside_response, _ = re.findall(r'“([^”]+)”', count.body[count_rule])
    tail = graph.lines(count, count_resume + 1, len(count.body), paper_entry)
    tail = hearing_task('T1-NS-REV08', count_round, count_rule, 4, 'v4:E1-02',
                        ['v4:E1-03', 'v4:E1-02', 'v4:E1-04'], (count_rule, 'v4:E1-03', '린', outside_response), tail,
                        source_scene=count)
    tail = graph.lines(count, 0, count_round, tail)
    boundary=scenes['01-T03b']
    tail=graph.lines(boundary,26,len(boundary.body),tail)
    ref=boundary.source(boundary.line+26)
    ident='T1-BU-REV01'
    keys=['v4:E1-PHOTO','v4:E1-07','v4:E1-02','v4:E1-03']
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':keys,
        'stage':{'id':ident,'kind':'bullet','v4':True,
            'question':'목격자가 이름을 확인하지 못해도 앞문의 개폐 순서를 확인할 자료는?',
            'options':[evidence[key] for key in keys],'answer':'v4:E1-02'},
        'queues':{'wrongVariants':[{'optionIndex':i,'script':[{'id':f'{ident}:wrong:{i}','type':'say',
            'actor':SPEAKERS[speaker],'speaker':speaker,'text':text,'source':ref}]} for i,speaker,text in [
                (0,'하루카','처음 찍었을 때는 이미 방을 열고 사람을 부른 뒤야. 그 전에 문이 몇 번 움직였는지는 안 찍혔어.'),
                (1,'소라','그건 우리가 합류한 표야. 문이 열리고 닫힌 줄까지 적은 건 아니고.'),
                (3,'린','그 문으로 못 나온다는 데까지 봤어. 앞문 몇 번 열었냐고 보수판한테 묻지 마.')]]}}
    tail=graph.add('rev:01:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    ident='T1-RE-REV02'
    checks=[
        ('앞쪽에서 사람이 보인 위치를 남기는 자료는?', ['나나와 아카리의 각 시야','문 센서의 열림·닫힘','발견 뒤 바닥의 종이'],0,
            '아카리','문이 움직인 기록에는 제가 어디에서 어느 쪽을 봤는지가 없어요.'),
        ('문 자체가 움직인 순서를 따로 확인할 자료는?', ['나나가 카에데 얼굴을 본 말','전면 문 센서','리쿠가 발견 뒤 종이를 본 말'],1,
            '리쿠','내가 안쪽 종이 본 건 발견 뒤야. 그 전에 누가 문 넘어간 걸 본 말은 아니고.'),
        ('되돌아오는 카에데가 들어가는 것을 직접 본 사람은?', ['센서가 이름을 확인했다','리쿠가 발견 전에 보았다','나나가 자기 위치에서 얼굴을 보았다'],2,
            '나나','제가 다시 들어오시는 모습을 보았어요. 문이 처음 움직인 때를 센서 대신 본 것은 아니고요.'),
    ]
    questions=[]
    for i,(question,options,correct,speaker,text) in enumerate(checks):
        questions.append({'q':question,'options':options,'optionIds':[str(j) for j in range(3)],'answer':options[correct],
            'success':[],'wrongVariants':[{'optionId':str(j),'script':[{'id':f'{ident}:wrong:{i}:{j}','type':'say',
                'actor':SPEAKERS[speaker],'speaker':speaker,'text':text,'source':ref}]} for j in range(3) if j!=correct]})
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':['v4:E1-SIGHT','v4:E1-02','v4:E1-DISC'],
        'stage':{'id':ident,'kind':'reasoning','v4':True,'title':'문 앞·문 전환·문 뒤의 관찰','questions':questions},'queues':{}}
    tail=graph.add('rev:01:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    tail=graph.lines(boundary,0,19,tail)
    scope=scenes['01-T03a'];rule=next(i for i,r in enumerate(scope.body) if r.startswith('01-I04b의 **'))
    tail=graph.lines(scope,rule+1,len(scope.body),tail)
    tail=hearing_task('T1-NS-REV15',27,rule,5,'v4:E1-SIGHT',
        ['v4:E1-03','v4:E1-04','v4:E1-SIGHT'],(rule,'v4:E1-03','리쿠',
        '그걸로 문 하나는 뺐어. 다른 데 선 사람이 더 오래 거기 서게 된 건 아니잖아.'),tail,source_scene=scope)
    tail=graph.lines(scope,0,27,tail)
    witness_boundaries_checkpoint=graph.add('rev:01:witness-boundaries-court-entry',type='stage',enterCourt=True,next=tail)
    witness_round = witness.body.index('#### 인물 지목 — 사인한 사람이 아닌 맞은편에 선 사람')
    rear_round = witness.body.index('#### 논스톱 C — 보수문으로 나오면')
    mine_round = witness.body.index('#### 발굴 이매지네이션 — 떼었다 다시 달았다면')
    mine_rule = next(i for i in range(mine_round, len(witness.body)) if witness.body[i].startswith('가려진 사진 위 블록을'))
    next_spot = next(i for i in range(mine_rule, len(witness.body)) if witness.body[i].startswith('#### 지점 지목'))
    after_comparison = witness.body.index('#### 지금 보여 준다고 표를 바꿀 건데')
    mine_source = witness.source(witness.line + mine_rule + 1)
    question, *corrections = re.findall(r'“([^”]+)”', witness.body[mine_rule])
    assert len(corrections) == 3
    round_after_spot = next(i for i in range(next_spot, len(witness.body)) if witness.body[i].startswith('#### 논스톱 동의'))
    exit_rule = next(i for i in range(round_after_spot, len(witness.body)) if witness.body[i].startswith('E1-04의 출력 순서'))
    confrontation = witness.body.index('#### 대면 — 건너편에 먼저 와 있던 사람')
    scope_update = next(i for i in range(next_spot, confrontation) if witness.body[i].startswith('정답 뒤 아카리의 증언'))
    sight_rule = next(i for i in range(next_spot, scope_update) if witness.body[i].startswith('미오는 E1-02 센서'))
    sight_source = witness.source(witness.line + sight_rule + 1)
    exit_statement = next(i for i in range(round_after_spot, exit_rule) if witness.body[i].startswith('4. 린'))
    statement = STMT.match(witness.body[exit_statement])[3].replace('**', '')
    tail = graph.lines(witness, exit_rule + 1, len(witness.body), tail)
    tail = graph.add('rev:01:exit-supported-statement', type='say', actor='rin', speaker='린', text=statement,
                     source=witness.source(witness.line + exit_statement + 1), next=tail)
    tail = hearing_task('T1-NS-REV07', round_after_spot, exit_rule, 4, 'v4:E1-04',
                        ['v4:E1-03', 'v4:E1-04', 'v4:E1-02'], (exit_rule, 'v4:E1-03', '린'), tail,
                        source_scene=witness, refute_instead=('켄', '16번까지 본 건 알아. 그래도 **둘이 앞문으로 같이 나온 건 아니잖아.**'))
    confrontation_options = []
    selected = [(i, BULLET.match(raw).groups()) for i, raw in enumerate(witness.body)
                if confrontation < i < round_after_spot and BULLET.match(raw)]
    assert len(selected) == 3
    for first_choice, (_, (label, _)) in enumerate(selected):
        next_node = tail
        order = [first_choice, *(i for i in range(3) if i != first_choice)]
        for i in reversed(order):
            offset, (_, text) = selected[i]
            replies = re.findall(r'(아카리|켄|미오|사츠키)\s+“([^”]+)”', text)
            assert len(replies) == 2
            for n, (speaker, answer) in reversed(list(enumerate(replies))):
                next_node = graph.add(f'rev:01:front-view:{first_choice}:{i}:{n}', type='say',
                                      actor=SPEAKERS[speaker], speaker=speaker, text=answer,
                                      source=witness.source(witness.line + offset + 1), next=next_node)
        confrontation_options.append({'id': str(first_choice), 'label': label, 'to': next_node})
    tail = graph.add('rev:01:front-view-menu', type='menu', q='어느 관찰부터 확인할까?',
                     source=sight_source, options=confrontation_options)
    tail = graph.lines(witness, confrontation + 1, selected[0][0], tail)
    tail = graph.add('rev:01:front-sensor-revision', type='evidence', evidenceId='v4:E1-02', revision=True,
                     name=evidence['v4:E1-02']['name'], source=witness.source(witness.line + scope_update + 1),
                     text=evidence['v4:E1-02']['text'] + ' 아카리는 창구 쪽에서 한 사람이 나가는 모습까지 보았으나, 문틀에 가린 얼굴이나 소지품은 확인하지 못했다.', next=tail)
    tail = graph.lines(witness, sight_rule + 1, scope_update, tail)
    sight_regions = [('door-leaf', '먼저 보인 문짝', [.18, .16, .31, .64]),
                     ('face-occlusion', '얼굴을 가린 문틀', [.397, .225, .474, .438]),
                     ('rear-opening', '창구와 별개의 보수문', [.746, .25, .88, .676])]
    spot_questions = ['앞문이 열릴 때 아카리에게 먼저 보인 것은 어디일까?',
                      '사람이 돌아 나올 때 얼굴을 가린 부분은 어디일까?',
                      '창구에서 본 앞문과 따로 확인한 보수문은 어디일까?']
    spot_corrections = re.findall(r'“([^”]+)”', witness.body[sight_rule])
    assert len(spot_corrections) == 2
    for index in reversed(range(len(sight_regions))):
        key, _, _ = sight_regions[index]
        task = f'T1-SP-REV0{index+1}'
        regions = [{'id': name, 'label': label, 'wrongVariant': name,
                    'polygon': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]}
                   for name, label, (x0, y0, x1, y1) in sight_regions]
        tasks[task] = {'taskId': task, 'ready': True, 'requiresEvidence': ['v4:E1-02', 'v4:E1-04'],
                       'stage': {'id': task, 'kind': 'spot', 'v4': True, 'question': spot_questions[index],
                                 'image': MINE_ART + 'witness-view.svg', 'regions': regions, 'answerRegionId': key},
                       'queues': {'wrongVariants': [
                           {'cause': wrong_key, 'script': [{'type': 'say', 'id': f'{task}:wrong:{wrong_key}',
                             'actor': SPEAKERS[speaker], 'speaker': speaker, 'text': text, 'source': sight_source}]}
                           for wrong_key, speaker, text in (
                               ('door-leaf', '린', spot_corrections[0]), ('face-occlusion', '하루카', spot_corrections[1]),
                               ('rear-opening', '아카리', '그 문은 창구에서 본 앞문과 달라요. 두 출입구를 같은 곳에 두시면 안 돼요.'))
                           if wrong_key != key]}}
        tail = graph.add(f'rev:01:witness-spot:{key}', type='task', taskId=task, trialDead=dead, seats=seats,
                         source=sight_source, success=tail, next=tail)
    tail = graph.lines(witness, next_spot + 1, sight_rule, tail)
    sight_checkpoint = graph.add('rev:01:sight-court-entry', type='stage', enterCourt=True, next=tail)
    voting_pressure = scenes['01-T03d']
    questions = [(i, BULLET.match(raw).groups()) for i, raw in enumerate(voting_pressure.body) if BULLET.match(raw)]
    assert len(questions) == 2
    common = graph.lines(voting_pressure, questions[-1][0] + 1, len(voting_pressure.body), tail)
    options = []
    for index, (offset, (label, detail)) in enumerate(questions):
        source = voting_pressure.source(voting_pressure.line + offset + 1)
        opening_reply, *later = re.findall(r'“([^”]+)”', detail)
        assert len(later) == (1 if index == 0 else 0)
        response = common
        if index == 0:
            for i, (actor, speaker, text) in reversed(list(enumerate([
                ('yuu', '유우', opening_reply),
                ('akari', '아카리', '문이 움직이는 걸 먼저 봤어요. 사람이 돌아 나올 때에는 저 문틀이 얼굴을 가렸고요.'),
                ('yuu', '유우', later[0]),
                ('mio', '미오', '각자 서 있던 자리부터 봐. 그래야 같은 걸 보고 한 말인지 알 수 있어.'),
            ]))):
                response = graph.add(f'rev:01:voting-pressure:{index}:{i}', type='say', actor=actor,
                                     speaker=speaker, text=text, source=source, next=response)
        else:
            response = graph.add('rev:01:voting-pressure:1:rin', type='say', actor='rin', speaker='린',
                                 text=opening_reply, source=source, next=response)
            response = graph.add('rev:01:voting-pressure:1:mio', type='say', actor='mio', speaker='미오',
                                 text='네가 지금 동의 안 해도 다음 얘기는 들을 거야.', source=source, next=response)
        options.append({'id': str(index), 'label': label, 'to': response})
    pressure_menu = graph.add('rev:01:voting-pressure-menu', type='menu', q='다음 질문을 어떻게 이어갈까?', options=options)
    tail = graph.lines(voting_pressure, 0, questions[0][0], pressure_menu)
    tail = graph.lines(witness, after_comparison + 1, next_spot, tail)
    tail = graph.add('rev:01:door-comparison-record', type='document', title='바깥 고정점의 전후 대조',
                     rows=['전날 사진과 현재 사진에서 양쪽 고정점과 오래 눌린 모서리가 같은 자리에 보인다. 문짝의 안쪽 걸쇠가 돌아가는 것만으로 바깥 판이 움직이지 않는다.'],
                     image=MINE_ART + 'rear-door.webp', source=mine_source, next=tail)
    tail = graph.lines(witness, mine_rule + 1, after_comparison, tail)
    mine_id = 'T1-MM-REV01'
    mine_regions = [('fixing', '바깥 판의 고정점과 오래 눌린 모서리'), ('latch', '풀린 손잡이'),
                    ('front-plate', '앞문의 바깥 표찰'), ('frost', '문 아래쪽 서리')]
    tail = mine_task('rev:01:door-mine', mine_id, '떼었다 다시 달았다면', question, MINE_ART + 'rear-door.webp',
                     mine_regions, door_objects, ['v4:E1-03'], mine_source,
                     list(zip(('레이', '린', '하루카'), corrections)), tail)
    tail = graph.lines(witness, mine_round + 1, mine_rule, tail)
    mine_checkpoint = graph.add('rev:01:mine-court-entry', type='stage', enterCourt=True, next=tail)
    rear_rule = next(i for i in range(rear_round, mine_round) if witness.body[i].startswith('E1-03 → 4.'))
    tail = graph.lines(witness, rear_rule + 1, mine_round, tail)
    tail = hearing_task('T1-NS-REV06', rear_round, rear_rule, 4, 'v4:E1-03',
                        ['v4:E1-02', 'v4:E1-03', 'v4:E1-09'],
                        (rear_rule, 'v4:E1-02', '린', '센서는 앞문 쪽에만 달렸어. 보수문 바깥은 그거에 안 나와.'), tail,
                        (13, '돌'), source_scene=witness)
    line_after_pick = next(i for i in range(witness_round, rear_round) if witness.body[i].startswith('**미오**'))
    tail = graph.lines(witness, line_after_pick, rear_round, tail)
    person_id = 'T1-PE-REV01'
    tasks[person_id] = {'taskId': person_id, 'ready': True, 'requiresEvidence': ['v4:E1-02'],
                        'stage': {'id': person_id, 'kind': 'person', 'v4': True,
                                  'question': '맞은편에서 앞문과 얼굴을 어디까지 봤는지 말해 줄 사람은?',
                                  'answer': 'akari', 'candidates': ['akari', 'satsuki', 'haruka', 'sora']},
                        'queues': {'wrongVariants': [
                            {'optionIndex': index, 'script': [{'type': 'say', 'id': f'{person_id}:wrong:{index}',
                              'actor': SPEAKERS[actor], 'speaker': actor, 'text': text,
                              'source': witness.source(witness.line + line_after_pick)}]}
                            for index, actor, text in ((1, '사츠키', '나중에 정리하러 마당에 나왔어. 그 전에 거기 서 있지는 않았어.'),
                                                       (2, '하루카', '내가 도착한 건 처음 발견했을 때야. 그전 앞문은 못 봤어.'),
                                                       (3, '소라', '내가 본 건 순찰 끝나고 다시 만난 자리야. 앞문 쪽 얼굴은 내가 말할 수 없어.'))]}}
    tail = graph.add('rev:01:witness-picker', type='task', taskId=person_id, trialDead=dead, seats=seats,
                     source=witness.source(witness.line + witness_round + 1), success=tail, next=tail)
    tail = graph.lines(witness, witness_round + 1, line_after_pick, tail)

    photo = scenes['01-T02b']
    photo_round = photo.body.index('#### 논스톱 — 카메라를 열 때까지 아무도 못 봤어')
    photo_rule = next(i for i in range(photo_round, len(photo.body)) if photo.body[i].startswith('정답은 **01-D04'))
    question_at = next(i for i in range(photo_rule, len(photo.body)) if photo.body[i].startswith('화면에서 카메라의'))
    tail = graph.lines(photo, question_at + 1, len(photo.body), tail)
    photo_choice_id = 'T1-QA-REV02'
    tasks[photo_choice_id] = {'taskId': photo_choice_id, 'ready': True, 'requiresEvidence': ['v4:E1-DISC'],
                              'stage': {'id': photo_choice_id, 'kind': 'choice', 'v4': True,
                                        'question': '처음 들어왔을 때 미오가 직접 확인한 것은?', 'answer': 0,
                                        'options': ['바닥에 종이가 있었음', '당시 읽은 본문의 정확한 글자', '처음 올 때 문을 통과한 사람']},
                              'queues': {'wrongVariants': [
                                  {'optionIndex': i, 'script': [{'type': 'say', 'id': f'{photo_choice_id}:wrong:{i}',
                                    'actor': SPEAKERS[actor], 'speaker': actor, 'text': text,
                                    'source': photo.source(photo.line + question_at + 1)}]}
                                  for i, actor, text in ((1, '미오', '본문은 실물을 비교할 때 읽었어. 처음 문 앞에서 본 건 종이가 놓인 자리였어.'),
                                                         (2, '아카리', re.findall(r'“([^”]+)”', photo.body[question_at])[0]))]}}
    tail = graph.add('rev:01:discovery-view-choice', type='task', taskId=photo_choice_id, trialDead=dead, seats=seats,
                     source=photo.source(photo.line + question_at + 1), success=tail, next=tail)
    tail = hearing_task('T1-NS-REV05', photo_round, photo_rule, 4, 'v4:E1-DISC',
                        ['v4:E1-01', 'v4:E1-PHOTO', 'v4:E1-DISC'],
                        (photo_rule, 'v4:E1-PHOTO', '하루카'), tail, source_scene=photo)
    tail = graph.lines(photo, 0, photo_round, tail)
    late_trial = graph.add('rev:01:later-court-entry', type='stage', enterCourt=True, next=tail)

    call = scenes['01-T02a']
    call_round = call.body.index('#### 논스톱 — 이름을 바꾸면 전화가 온다고')
    call_rule = next(i for i in range(call_round, len(call.body)) if call.body[i].startswith('정답은 01-D03에서'))
    assert '신청한 사람에게 주는 한 번' in call.body[call_rule]
    tail = graph.lines(call, call_rule + 1, len(call.body), tail)
    tail = hearing_task('T1-NS-REV04', call_round, call_rule, 4, 'v4:E1-APP',
                        ['v4:E1-09', 'v4:E1-APP', 'v4:E1-13'],
                        (call_rule, 'v4:E1-13', '아카리', '제가 들은 건 휴게실에서 창구로 온 호출이에요. 바깥에 누가 신청할 수 있는지는 그걸로 알 수 없어요.'), tail,
                        source_scene=call)
    tail = graph.lines(call, 0, call_round, tail)
    accident_rule = next(i for i in range(accident, len(hearing.body)) if hearing.body[i].startswith('E1-11 → 4.'))
    tail = graph.lines(hearing, accident_rule + 1, len(hearing.body), tail)
    tail = hearing_task('T1-NS-REV03', accident, accident_rule, 4, 'v4:E1-11',
                        ['v4:E1-03', 'v4:E1-11', 'v4:E1-01'], (accident_rule, 'v4:E1-03', '미오'), tail, (3, '끼'))
    tail = graph.lines(hearing, timeline + 1, accident, tail)
    choice_id = 'T1-QA-REV01'
    tasks[choice_id] = bundle(choice_id, 'choice', '목격이 보증하는 범위', [], 'v4:E1-07', [])
    choice = tasks[choice_id]
    choice.pop('debate')
    choice['stage'].update(question='순찰 중간의 빈 시간을 두고 지금 기록할 수 있는 사실은?',
                           answer=1, filterOwnedEvidence=False,
                           options=['치료함 앞에서 함께 있었으니 순찰 중에도 계속 함께 있었다',
                                    '다시 만난 뒤에는 두 사람을 함께 봤다',
                                    '타이가를 본 사람이 없었으니 그 시간에 방 안에 있었다'])
    choice['stage'].pop('presentation')
    choice['queues']['wrongVariants'] = [
        {'optionIndex': index, 'script': [{'type': 'say', 'id': f'{choice_id}:wrong:{index}',
          'actor': SPEAKERS[speaker], 'speaker': speaker, 'text': text, 'source': hearing.source(hearing.line + timeline + 1)}]}
        for index, speaker, text in ((0, '나나', '제가 두 분을 본 건 치료함까지 오셨을 때예요.'),
                                     (2, '리쿠', re.findall(r'“([^”]+)”', hearing.body[timeline])[0]))]
    tail = graph.add('rev:01:timeline-choice', type='task', taskId=choice_id, trialDead=dead, seats=seats,
                     source=hearing.source(hearing.line + timing + 1), success=tail, next=tail)
    tail = graph.lines(hearing, timing + 1, timeline, tail)
    first_rule = next(i for i in range(first, timing) if hearing.body[i].startswith('순찰 원본 E1-07'))
    tail = graph.lines(hearing, first_rule + 1, timing, tail)
    tail = hearing_task('T1-NS-REV02', first, first_rule, 3, 'v4:E1-07',
                        ['v4:E1-08', 'v4:E1-07', 'v4:E1-02'], (first_rule, 'v4:E1-08', '나나'), tail)
    source = scene.source(scene.line + pn + 1)
    tail = graph.add('rev:01:panic-result', type='say', actor='koto', speaker='코토',
                     text='닫혔다는 데까지만 알 수 있네요. 안에 누가 있었는지는 제가 읽은 표찰에 없었어요.',
                     mono=False, source=source, next=tail)
    panic = graph.add('rev:01:panic', type='task', taskId=pn_id, source=source,
                      trialDead=dead, seats=seats, success=tail, next=tail)
    response = graph.lines(scene, next(i for i in range(ns, pn) if SAY.match(scene.body[i])), pn, panic)
    ns_node = graph.add('rev:01:nonstop', type='task', taskId=ns_id, source=scene.source(scene.line + ns + 1),
                        trialDead=dead, seats=seats, success=response, next=response)
    entry = graph.lines(scene, 0, ns, ns_node)
    opening=scenes['01-T00']
    entry=graph.lines(opening,0,len(opening.body),entry)
    opening_round = opening.body.index('#### 첫 논의 — 앞과 뒤가 바뀐 증언')
    opening_rule = next(i for i, raw in enumerate(opening.body) if raw.startswith('수사에서 얻은 두 목격자의 시야 대조'))
    opening_source = opening.source(opening.line + opening_rule + 1)
    before, resume = None, entry
    while graph.nodes[resume]['source']['line'] < opening_source['line']:
        before, resume = resume, graph.nodes[resume]['next']
    verified = graph.add('rev:01:opening-observation-scope', type='document', title='목격 사이에 남은 빈 시간',
        rows=['입실은 나나가 보았다.', '입실과 발견 사이를 계속 본 사람은 확인되지 않았다.',
              '발견 때 미오와 하루카가 현장에 있었다.'], source=opening_source, next=resume)
    opening_id = 'T1-NS-REV00'
    # The revised investigation already gives the sightline card. The legacy E1-10 ID belongs to a TV record.
    patrol_reply, print_reply = re.findall(r'“([^”]+)”', opening.body[opening_rule])
    first_debate = hearing_task(opening_id, opening_round, opening_rule, 4, 'v4:E1-SIGHT',
        ['v4:E1-SIGHT', 'v4:E1-07', 'v4:E1-04'], (opening_rule, 'v4:E1-07', '소라', patrol_reply),
        verified, source_scene=opening)
    opening_task = tasks[opening_id]
    opening_task['stage']['wrongCards']['v4:E1-04'] = 'printed-record'
    opening_task['queues']['wrongVariants'].append({'cause': 'printed-record', 'script': [
        {'id': opening_id + ':wrong:print', 'type': 'say', 'actor': 'koto', 'speaker': '코토',
         'text': print_reply, 'source': opening_source}]})
    graph.nodes[before]['next'] = first_debate
    court_entry = graph.add('rev:01:court-entry', type='stage', enterCourt=True, next=entry)
    placements = (
        ('01-I04', 'v4:E1-07', 'staff_passage', '', [0, 1.25, 6]),
        ('01-I02f', 'v4:E1-02', 'service_lounge', 'door_A', None),
        ('01-I03b', 'v4:E1-09', 'management_office', '', [-1.65, 1.25, 1.9]),
        ('01-I04e', 'v4:E1-08', 'clinic', '', [0, 1.25, 1.06]),
        ('01-I02', 'v4:E1-11', 'service_lounge', '', [-0.6, 1.1, -0.2]),
        ('01-I02e', 'v4:E1-03', 'service_lounge', 'door_B', None),
        ('01-I03', 'v4:E1-13', 'management_office', '', [1.2, 1.25, .5]),
        ('01-I00', 'v4:E1-PHOTO', 'service_lounge', '', [0.9, 1.15, -0.4]),
        ('01-I02c', 'v4:E1-04', 'service_lounge', 'printer', None),
    )
    spots = []
    for source_id, evidence_id, space, target, world_pos in placements:
        section = scenes[source_id]
        card = evidence[evidence_id]
        done = graph.add('rev:01:return:'+evidence_id, type='return')
        if evidence_id == 'v4:E1-11':
            medical = evidence['v4:E1-01']
            done = graph.add('rev:01:record:'+medical['id'], type='evidence', evidenceId=medical['id'],
                             name=medical['name'], text=medical['text'], source=section.source(section.line), next=done)
        if evidence_id == 'v4:E1-PHOTO':
            chronology = evidence['v4:E1-DISC']
            done = graph.add('rev:01:record:'+chronology['id'], type='evidence', evidenceId=chronology['id'],
                             name=chronology['name'], text=chronology['text'], source=section.source(section.line), next=done)
        acquire = graph.add('rev:01:record:'+evidence_id, type='evidence', evidenceId=evidence_id,
                            name=card['name'], text=card['text'], source=section.source(section.line), next=done)
        supplemental={
            '01-I00':['01-I00b','01-I00c'],'01-I02':['01-I02a','01-I02d'],
            '01-I02e':['01-I01a','01-I02b'],'01-I03':['01-I01b','01-I03a'],
            '01-I04':['01-I04c','01-I04a','01-I04d'],'01-I04e':['01-I04g','01-I04f'],
        }
        if source_id=='01-I04':
            scope=scenes['01-I04b'];scope_card=evidence['v4:E1-SIGHT']
            acquire=graph.add('rev:01:record:'+scope_card['id'],type='evidence',evidenceId=scope_card['id'],name=scope_card['name'],
                text=scope_card['text'],source=scope.source(scope.line),next=acquire)
            acquire=graph.lines(scope,0,len(scope.body),acquire)
        acquire=supplemental_inspection(graph,scenes,supplemental.get(source_id,()),acquire)
        start = (first_photo_investigation(graph,section,acquire) if evidence_id=='v4:E1-PHOTO' else
                 graph.lines(section,0,len(section.body),acquire))
        spot = {'id': source_id, 'label': card['name'], 'neutralLabel': card['name'], 'space_id': space, 'entry': start}
        if target:
            spot['target_id'] = target
        if world_pos is not None:
            spot['world_pos'] = world_pos
        if evidence_id == 'v4:E1-13':
            spot['requiresCards'] = ['v4:E1-02', 'v4:E1-11']
        spots.append(spot)
    torn_report = scenes['01-I01']
    comparison_at = next(i for i, raw in enumerate(torn_report.body) if raw.startswith('실제 조작.'))
    report_source = torn_report.source(torn_report.line + comparison_at + 1)
    comparison = 'rev:01:report-comparison'
    report_return = graph.add('rev:01:return:paper', type='return')
    for key in ('v4:E1-PAPER', 'v4:E1-06', 'v4:E1-05'):
        report_card = evidence[key]
        report_return = graph.add('rev:01:record:' + key, type='evidence', evidenceId=key,
                                  name=report_card['name'], text=report_card['text'], source=report_source,
                                  next=report_return)
    compare_correct = graph.lines(torn_report, comparison_at + 1, len(torn_report.body), report_return)
    compare_wrong = graph.add('rev:01:report-wrong-corner', type='say', actor='mio', speaker='미오',
                              text='16번은 모서리가 남아 있어. 보호대에서 나온 조각을 끼울 자리가 없잖아.',
                              source=report_source, next=comparison)
    graph.add(comparison, type='menu', q='보호대에서 나온 종이 조각이 맞물리는 보고서는?', source=report_source,
              options=[{'id': '16', 'label': '16번 확인용 사본', 'to': compare_wrong},
                       {'id': '17', 'label': '17번 보고서', 'to': compare_correct}])
    inspect_report = graph.add('rev:01:report-inspection-sheet', type='document', title='발견된 보고서와 회수한 조각',
                               rows=['한쪽은 바닥에서 발견한 보고서다. 따로 놓인 조각은 먼저 쓰던 보호대에서 나왔다.',
                                     '점검 때 남긴 16번 사본에는 찢긴 자리가 없다.'],
                               image=MINE_ART + 'report-torn-edge.webp', source=report_source, next=comparison)
    spot_start = graph.lines(torn_report, 0, comparison_at, inspect_report)
    spots.append({'id': torn_report.id, 'label': '두 보고서와 회수 조각', 'neutralLabel': '두 보고서와 회수 조각',
                  'space_id': 'service_lounge', 'world_pos': [-1.24, 1.16, 0.45], 'entry': spot_start,
                  'requiresCards': ['v4:E1-04']})
    court_entry=first_investigation_close(graph,scenes,court_entry)
    investigation = graph.add('rev:01:investigate', type='investigate', space_id='service_lounge', spots=spots,
                              requiredSpotIds=[spot['id'] for spot in spots], requiredCards=list(evidence), next=court_entry)
    meeting = scenes['01-F01']
    inspection_sheet = scenes['01-D03']
    callback_at = next(i for i, raw in enumerate(inspection_sheet.body) if raw.startswith('01-F01에서 말한 것만'))
    callback_text = re.findall(r'“([^”]+)”', inspection_sheet.body[callback_at])
    if len(callback_text) != 2:
        raise ValueError('Free time: expected a later response for each choice')
    discovered = scenes['01-D04']
    doorstep = discovered.body.index('#### 휴게실 문 앞에서')
    opens = next(i for i in range(doorstep, len(discovered.body)) if discovered.body[i].startswith('두 번째 노크 뒤 문이'))
    discovery = graph.add('rev:01:discovery-announcement', type='stage', next=investigation,
                          presentation={'actions': ['body_announcement']})
    discovery = graph.lines(discovered, opens, len(discovered.body), discovery)
    discovery = graph.add('rev:01:discovery-observation', type='say', actor='mio', speaker='미오', mono=True,
                          text='문턱에서 바닥의 종이와 그 옆에 쓰러진 사람이 보였다. 여기서는 글씨까지 읽히지 않았다.',
                          source=discovered.source(discovered.line + opens + 1), next=discovery)
    discovery = graph.add('rev:01:discovery-reveal', type='stage', next=discovery,
                          source=discovered.source(discovered.line + opens + 1), presentation={'actions': ['body_reveal']})
    discovery = graph.add('rev:01:second-knock', type='stage', sfx='sfx_bang_door', next=discovery,
                          source=discovered.source(discovered.line + opens + 1))
    discovery = graph.add('rev:01:first-knock', type='say', actor='mio', speaker='미오', mono=True,
                          text='한 번 두드렸다. 안에서는 아무 대답도 오지 않았다.', sfx='sfx_bang_door',
                          source=discovered.source(discovered.line + opens - 2), next=discovery)
    alternatives = [(i, BULLET.match(raw)[1]) for i, raw in enumerate(discovered.body[:opens])
                    if i > doorstep and BULLET.match(raw)]
    assert len(alternatives) == 2
    discovery = graph.menu(discovered, '먼저 문을 두드릴 사람은?', [
        (label, start + 1, alternatives[index + 1][0] if index == 0 else opens, '')
        for index, (start, label) in enumerate(alternatives)], discovery)
    discovery = graph.add('rev:01:discovery', type='stage', next=discovery, source=discovered.source(discovered.line + doorstep + 1),
                          scene={'space': 'service_lounge', 'perspective': 'current-observation'})
    discovery = graph.lines(discovered, 0, doorstep, discovery)
    discovery = graph.add('rev:01:patrol-evening', type='stage', next=discovery,
                          source=discovered.source(discovered.line), scene={'space': 'hotel_corridor', 'perspective': 'current-observation'},
                          presentation={'music': {'operation': 'play', 'cue': 'bgm_tense'}})
    document_options = [i for i, line in enumerate(inspection_sheet.body) if BULLET.match(line)]
    assert len(document_options) == 2
    registration = evidence['v4:E1-APP']
    daily_ids = [ident for ident in scenes if ident.startswith('01-D')]
    application_following = life_route(graph,scenes,
        daily_ids[daily_ids.index('01-D03')+1:daily_ids.index('01-D04')],discovery)
    application = graph.add('rev:01:application', type='evidence', evidenceId=registration['id'], name=registration['name'],
                            text=registration['text'], source=inspection_sheet.source(inspection_sheet.line), next=application_following)
    tail = graph.lines(inspection_sheet, document_options[-1] + 1, len(inspection_sheet.body), application)
    options = []
    for flag, at in zip(('A', 'B'), document_options):
        label, body = BULLET.match(inspection_sheet.body[at]).groups()
        replies = re.findall(r'(미오|카에데)\s+“([^”]+)”', body)
        assert [name for name, _ in replies] == ['미오', '카에데']
        target = tail
        for index, (actor, text) in reversed(list(enumerate(replies))):
            target = graph.add(f'rev:01-D03:{flag}:{index}', type='say', speaker=actor, actor=SPEAKERS[actor],
                               text=text, source=inspection_sheet.source(inspection_sheet.line + at + 1), next=target)
        options.append({'id': flag, 'label': label, 'to': target, 'set': {'01-D03:scope': flag}})
    document_choice = graph.add('rev:01-D03:choice', type='menu', q='점검표를 어디까지 받을까?', options=options)
    second_memory = next(i for i,row in enumerate(inspection_sheet.body) if row.startswith('01-F08을 봤다면'))
    common = graph.lines(inspection_sheet,second_memory+1,document_options[0],document_choice)
    memories = re.findall(r'“([^”]+)”',inspection_sheet.body[second_memory])
    assert len(memories)==2
    remembered=common
    for index,(actor,text) in reversed(list(enumerate(zip(('미오','카에데'),memories,strict=True)))):
        remembered=graph.add(f'rev:01-F08:callback:{index}',type='say',actor=SPEAKERS[actor],speaker=actor,
            text=text,source=inspection_sheet.source(inspection_sheet.line+second_memory+1),next=remembered)
    common=graph.add('rev:01-F08:callback',type='branch',cases=[
        {'flag':'01-F08','equals':flag,'to':remembered} for flag in 'ABC'],default=common)
    common = graph.lines(inspection_sheet, callback_at + 1, second_memory, common)
    cases = []
    for flag, text in zip(('A', 'B'), callback_text):
        response = graph.add(f'rev:01-F01:callback:{flag}', type='say', actor='kaede', speaker='카에데', text=text,
                             mono=False, source=inspection_sheet.source(inspection_sheet.line + callback_at + 1), next=common)
        cases.append({'flag': '01-F01', 'equals': flag, 'to': response})
    callback = graph.add('rev:01-F01:callback', type='branch', cases=cases, default=common)
    callback = graph.lines(inspection_sheet, 0, callback_at, callback)
    callback = graph.add('rev:01-D03:entry', type='stage', next=callback,
                         source=inspection_sheet.source(inspection_sheet.line),
                         scene={'space': 'management_office', 'perspective': 'current-observation'})
    quotes = re.compile(r'(미오|카에데)\s+“([^”]+)”')
    reply = [i for i, raw in enumerate(meeting.body) if BULLET.match(raw)]
    if len(reply) != 2:
        raise ValueError('Free time: two authored responses required')
    join = graph.lines(meeting, reply[-1] + 1, len(meeting.body), graph.finish_free_time(meeting,callback))
    options = []
    for flag, offset in zip(('A', 'B'), reply):
        label, body = BULLET.match(meeting.body[offset]).groups()
        to = join
        dialogue = quotes.findall(body)
        if [actor for actor, _ in dialogue] != ['미오', '카에데']:
            raise ValueError(f'Free time: incomplete authored response {flag}')
        for n, (actor, text) in reversed(list(enumerate(dialogue))):
            to = graph.add(f'rev:01-F01:{flag}:{n}', type='say', actor=SPEAKERS[actor], speaker=actor,
                           text=text, mono=False, source=meeting.source(meeting.line + offset + 1), next=to)
        options.append({'id': flag, 'label': label, 'to': to, 'set': {'01-F01': flag}})
    choice = graph.add('rev:01-F01:choice', type='menu', q='어디까지 함께 기록할까?', options=options)
    talk = graph.lines(meeting, 0, reply[0], choice)
    meeting_entry = graph.add('rev:01-F01:entry', type='stage', next=talk,
                              source=meeting.source(meeting.line), scene={'space': 'staff_passage', 'perspective': 'current-observation'},
                              presentation={'music': {'operation': 'play', 'cue': 'bgm_freetime'}})
    entry = graph.add('rev:01:preview-entry', type='menu', q='자유행동', options=[
        {'id': 'meet', 'label': '카에데와 이야기한다', 'to': meeting_entry},
        {'id': 'skip', 'label': '다음 장면으로 간다', 'to': callback},
    ])
    following_meeting = life_route(graph,scenes,
        daily_ids[daily_ids.index('01-D02b'):daily_ids.index('01-D03')],callback)
    for node in graph.nodes.values():
        if node.get('source',{}).get('location')=='01-F01' and node.get('next')==callback:
            node['next']=following_meeting
    graph.nodes[entry]['options'][1]['to']=following_meeting
    entry = life_route(graph,scenes,daily_ids[:daily_ids.index('01-D02b')],entry)
    return ({'schemaVersion': 1, 'contentVersion': 'v4', 'campaignRevision': 'rewrite-v5', 'chapter': '1',
             **({'resultTaskId': result_task_id} if result_task_id else {}),
             'entry': entry, 'trialRoster': {'dead': dead, 'seats': seats}, 'nodes': graph.nodes,
             'qaCheckpoints': {'later-trial': {'entry': late_trial, 'evidence': list(evidence.values())},
                               'door-mine': {'entry': mine_checkpoint, 'evidence': [evidence[key] for key in ('v4:E1-03', 'v4:E1-02', 'v4:E1-04')]},
                               'witness-view': {'entry': sight_checkpoint, 'evidence': [evidence[key] for key in ('v4:E1-03', 'v4:E1-02', 'v4:E1-04','v4:E1-SIGHT')]},
                               'witness-boundaries':{'entry':witness_boundaries_checkpoint,'evidence':list(evidence.values())},
                               'paper-comparison': {'entry': paper_checkpoint, 'evidence': [evidence[key] for key in (
                                   'v4:E1-04', 'v4:E1-05', 'v4:E1-06', 'v4:E1-08', 'v4:E1-PAPER')]},
                               'paper-mine': {'entry': paper_mine_checkpoint, 'evidence': [evidence[key] for key in (
                                   'v4:E1-04', 'v4:E1-05', 'v4:E1-06', 'v4:E1-08', 'v4:E1-PAPER')]},
                               'paper-sequence': {'entry': paper_sequence_checkpoint, 'evidence': [evidence[key] for key in (
                                   'v4:E1-04', 'v4:E1-06', 'v4:E1-08', 'v4:E1-PAPER')]},
                               'rescue-hearing': {'entry': rescue_checkpoint, 'evidence': [evidence[key] for key in (
                                   'v4:E1-DISC', 'v4:E1-05', 'v4:E1-06', 'v4:E1-08', 'v4:E1-09', 'v4:E1-13',
                                   'v4:E1-02', 'v4:E1-03')]},
                               'phone-hearing': {'entry': phone_checkpoint, 'evidence': [evidence[key] for key in (
                                   'v4:E1-01', 'v4:E1-02', 'v4:E1-03', 'v4:E1-06', 'v4:E1-08', 'v4:E1-09',
                                   'v4:E1-11', 'v4:E1-13', 'v4:E1-APP')]},
                               'phone-evidence': {'entry': phone_evidence_checkpoint, 'evidence': [evidence[key] for key in (
                                   'v4:E1-01', 'v4:E1-02', 'v4:E1-03', 'v4:E1-06', 'v4:E1-08', 'v4:E1-11', 'v4:E1-13', 'v4:E1-APP')]},
                               'signature-hearing': {'entry': signature_checkpoint, 'evidence': [evidence[key] for key in (
                                   'v4:E1-07', 'v4:E1-08', 'v4:E1-APP', 'v4:E1-13')]},
                               'armament-hearing': {'entry': armament_checkpoint, 'evidence': [evidence[key] for key in (
                                   'v4:E1-01', 'v4:E1-04', 'v4:E1-05', 'v4:E1-06', 'v4:E1-07', 'v4:E1-11', 'v4:E1-13')]},
                               **({'comic-hearing': {'entry': comic_checkpoint, 'evidence': [evidence[key] for key in (
                                   'v4:E1-04', 'v4:E1-05', 'v4:E1-06', 'v4:E1-07', 'v4:E1-13')]},
                                   'vote-hearing': {'entry': vote_checkpoint, 'evidence': []}} if comic_checkpoint else {})}}, tasks)


def chapter_two_last_sighting(graph, scenes, tasks, records, dead, seats, tail, pedestal_objects):
    def task(ident, source, stage, evidence, next_node, wrongs=()):
        tasks[ident] = {'taskId': ident, 'ready': True, 'requiresEvidence': evidence,
                        'stage': {'id': ident, 'v4': True, **stage},
                        'queues': {'wrongVariants': [
                            {**selector, 'script': [{'id': f'{ident}:wrong:{index}', 'type': 'say',
                              'actor': SPEAKERS[speaker], 'speaker': speaker, 'text': reply, 'source': source}]}
                            for index, (selector, speaker, reply) in enumerate(wrongs)]}}
        return graph.add('rev:02:'+ident, type='task', taskId=ident, trialDead=dead, seats=seats,
                         source=source, success=next_node, next=next_node)

    def choice(ident, source, question, options, answer, evidence, next_node, wrongs):
        return task(ident, source, {'kind': 'choice', 'question': question, 'options': options, 'answer': answer},
                    evidence, next_node, [({'optionIndex': index}, speaker, reply) for index, speaker, reply in wrongs])

    def at(scene, prefix):
        return next(i for i, row in enumerate(scene.body) if row.startswith(prefix))

    def ref(scene, offset):
        return scene.source(scene.line + offset + 1)

    def hearing(ident, scene, start, end, target, ammo, next_node, wrongs, *, agree=False):
        answer = ammo[-1]
        rows = []
        for offset in range(start+1, end):
            if match := STMT.match(scene.body[offset]):
                index, speaker, raw, _ = match.groups()
                raw = raw.replace('【','**').replace('】','**')
                kind = 'weak' if index == target and not agree else 'plain'
                row = debate_statement(ident, index, speaker, raw, ref(scene, offset), kind,
                                       answer if kind == 'weak' else '')
                if agree and index == target:
                    word = row['text']
                    row.update(kind='agree', agree=answer, agreeTarget={'word':word,'glyphStart':0})
                rows.append(row)
        assert sum(row['kind']!='plain' for row in rows)==1
        cards = [{'id':key,'name':records[key][0],'text':records[key][1]} for key in ammo]
        title = scene.body[start].partition(' — ')[2]
        next_node = task(ident, ref(scene, end), {'kind':'nonstop','title':title,'lines':rows,
                         'options':cards,'authoredAmmo':list(ammo),'filterOwnedEvidence':True,
                         'wrongCards':{key:key for key,_,_ in wrongs}}, ammo, next_node,
                         [({'cause':key},speaker,reply) for key,speaker,reply in wrongs])
        tasks[ident]['debate'] = {'id':ident,'kind':'nonstop','lines':rows,'bullets':cards}
        return next_node

    e202, e204, e205, e206, e207, e208, e209, e210, e211 = (
        'v4:E'+key for key in ('202','204','205','206','207','208','209','210','211'))
    comic = chapter_two_comic_stage(scenes['02-T09'])
    if comic:
        graph.nodes.pop(tail)
        tail = graph.add('rev:02:complete',type='end',chapterComplete=True,nextChapter='3')
        aftermath = scenes['02-R01']
        disposition = next(i for i,row in enumerate(aftermath.body) if row.startswith('- **돌려준다.**'))
        disposition_end = next(i for i,row in enumerate(aftermath.body) if row.startswith('#### 누른 이름을'))
        tail = graph.lines(aftermath,disposition_end+1,len(aftermath.body),tail)
        disposition_source = ref(aftermath,disposition)
        choices = []
        for key,label,reply in (
            ('return','개인 명단은 본인이 요청하면 돌려준다','각자 고른 표식부터 확인할게. 공용 수량을 적은 쪽은 남겨 두자.'),
            ('keep','나나와 함께 보관하고 요청한 사람이 있을 때 연다','봉투를 같이 열 때 누가 무엇을 봤는지도 따로 적자. 숫자 옆에 이름부터 쓰지는 않을게.'),
        ):
            node = graph.add('rev:02:ledger-disposition:'+key,type='say',actor='mio',speaker='미오',
                             text=reply,source=disposition_source,next=tail)
            choices.append({'id':key,'label':label,'to':node,'set':{'02-R01:ledger':key}})
        tail = graph.add('rev:02:ledger-disposition',type='menu',q='아이의 개인 명단을 어떻게 보관할까?',
                         options=choices,source=disposition_source)
        tail = graph.lines(aftermath,0,disposition,tail)
        tail = graph.add('rev:02:aftermath',type='stage',next=tail,scene={'space':'dining_room','leaveCourt':True},
                         presentation={'music':{'operation':'play','cue':'bgm_daily_summer'}})
        execution = scenes['02-R00']
        tail = chapter_verdict(graph,execution,tail,2)
        vote = scenes['02-T10']
        vote_at = at(vote,'#### 범인 투표')
        memory_at = at(vote,'자유시간에서 아버지')
        remembered = graph.add('rev:02:remember-ring',type='say',actor='mio',speaker='미오',
                               text='네가 그걸 고치고 싶었던 건 기억해.',source=ref(vote,memory_at),next=tail)
        quiet = graph.add('rev:02:stop-ring',type='say',actor='mio',speaker='미오',mono=True,
                          text='탁자에서 굴러오는 고리를 손끝으로 멈췄다.',source=ref(vote,memory_at),next=tail)
        tail = graph.add('rev:02:ring-memory',type='branch',
                         cases=[{'flag':'02-F01:ring','equals':True,'to':remembered}],default=quiet)
        tail = graph.lines(vote,vote_at+3,memory_at,tail)
        tail = task('T2-VOTE-REV01',ref(vote,vote_at),{
            'kind':'vote','title':'같은 소매에서 시작한 판단','question':'이 사건의 검정은 누구인가?',
            'answer':'rin','candidates':seats,'deadCandidatesSelectable':True,
            'selectionRole':'final-culprit-vote','finalVote':True,
            'presentation':{'music':{'operation':'play','cue':'bgm_trial_main_2'}},
        }, [e206,e207,e208,e209],tail)
        tasks['T2-VOTE-REV01']['queues']['wrong'] = [{
            'type':'say','id':'T2-VOTE-REV01:retry','actor':'mio','speaker':'미오',
            'text':'겉옷이 지나간 문과 준비실의 앞문은 달랐어. 마지막에 살아 있는 아이와 같은 방에 남은 사람부터 다시 보자.',
            'source':ref(vote,vote_at)}]
        tail = graph.lines(vote,0,vote_at,tail)
        explanation = scenes['02-T09a']
        classification = at(explanation,'플레이어는 세 문장을')
        after = at(explanation,'**코토**　그럼 먼저 방에')
        tail = graph.lines(explanation,after,len(explanation.body),tail)
        decisions = (
            ('미리 정한 행동은?',['먼저 열쇠를 반납하고 안에서 열어 주기를 기다렸다','유우가 객석에서 문을 잘못 보게 정했다'],0,
             '유우','내가 어느 줄에 설지는 내가 정했어. 린이 나한테 여기 서 있으라고 한 게 아니야.'),
            ('그 자리에서 바뀐 행동은?',['공용 겉옷을 빌려줬다','사본을 놓지 않는 아이에게 받침을 들어 손댔다'],1,
             '리쿠','빌려줄 때 내가 어느 문으로 나오겠다고 약속한 건 아니야. 그걸 공격 계획으로 넣지는 마.'),
            ('나중에 바로잡지 않은 말은?',['체크 소매의 주인을 자신으로 부른 말을 그대로 뒀다','받침을 들어 물건을 움직였다'],0,
             '미오','받침이 움직인 건 방 안에서 실제로 남은 자료야. 나중에 고치지 않은 말하고 나눠 봐.'),
        )
        for index,(question,options,answer,speaker,reply) in reversed(list(enumerate(decisions))):
            tail = choice(f'T2-QA-REV15-{index}',ref(explanation,classification),question,options,answer,
                          ['v4:E203',e204,e208],tail,[(1-answer,speaker,reply)])
        tail = graph.lines(explanation,0,classification,tail)
        tail = task(comic['id'], ref(scenes['02-T09'], 0), comic, [e206,e207,e208,e209,e211], tail)
    scene = scenes['02-T08a']
    zone = at(scene, '#### 구역 지목')
    rhythm = at(scene, '#### 이론 무장')
    rhythm_rule = at(scene, '마지막 문제')
    follow = at(scene, '### 마지막 조각 앞')
    tail = graph.lines(scene, follow+1, len(scene.body), tail)
    waves, claims, replies = [], [], []
    ident = 'T2-AA-REV01'
    for offset in range(rhythm+1, rhythm_rule):
        cells = [cell.strip() for cell in scene.body[offset].strip('|').split('|')]
        if len(cells)!=3 or not cells[0].isdigit():
            continue
        source = ref(scene, offset)
        phase = len(waves)
        lines = re.findall(r'“([^”]+)”',cells[1])
        assert len(lines)==4
        claims.extend(lines)
        waves.append({'id':f'{ident}:wave:{phase}','pairs':[
            {'claim':{'id':f'{ident}:{phase}:{index}','type':'say','actor':'rin',
                      'speaker':'린','text':line,'source':source}} for index,line in enumerate(lines)]})
        replies.append([{'id':f'{ident}:wave:{phase}:reply:{index}','type':'say','actor':SPEAKERS[speaker],
                         'speaker':speaker,'text':line,'source':source} for index,(speaker,line) in
                        enumerate(re.findall(r'(미오|린) “([^”]+)”',cells[2]))])
    assert len(waves)==3 and all(replies)
    fragments, = re.findall(r'\*\*([^*]+)\*\*',scene.body[rhythm_rule])
    fragments = fragments.split(' → ')
    assert len(fragments)==4
    tail = task(ident, ref(scene, rhythm_rule),
                {'kind':'armament','chapter':2,'title':'어느 문으로 나갔어','opponent':'rin','lines':claims,
                 'waves':waves,'phaseTranscripts':True,'phaseFeedback':replies[:2],
                 'question':'마지막 생존 확인부터 발견까지 무슨 일이 있었지?',
                 'finalSubject':'그때의 순서는','final':fragments}, [e206,e207,e208,e209], tail)
    tasks[ident]['queues']['success'] = replies[-1]
    tail = graph.lines(scene, zone+3, rhythm, tail)
    tail = choice('T2-QA-REV14', ref(scene, zone), '도면의 표식을 실제로 따라가면 어디로 이어질까?',
                  ['직원 창구','도면 표식 앞의 별도 작업 통로','의상실 격자','준비실 앞문'], 1, [e205,e207,e211], tail,
                  [(0,'하루카','찍은 사람들 앞에 손을 내밀던 자리야. 그 높이로 사람이 걸어가지는 못해.'),
                   (2,'레이','격자는 두 실을 가릅니다. 작업 통로가 끝난 곳은 거기와 연결되지 않습니다.'),
                   (3,'미오','그 문은 이미 교대 자료에 있어. 도면을 따라가서 확인한 길은 따로야.')])
    tail = graph.lines(scene, 0, zone, tail)
    scene = scenes['02-T08l']
    tail = graph.lines(scene, 0, len(scene.body), tail)

    closing_hearings = (
        ('02-T08i','밖에 그대로','4에 맞힐 한 발은','4',(e205,e207,e211,e208),(
            (e205,'레이','창구에서 접시가 들어갈 수 있다는 점은 이미 확인했습니다.'),
            (e207,'켄','난 아예 앞문을 넘지 않았다고 가정했어. 창에서 실제로 어디까지 닿는지 봐.'),
            (e211,'사츠키','걸어서 찾아간 끝 말고 그 안쪽의 받침을 같이 봐.'))),
        ('02-T08g','아직 죽었다고','4에 **E208의 접시','4',('v4:E201',e209,e208),(
            ('v4:E201','쇼','돌아가신 시각을 좁힐 자료로 검안의 한계를 쓰지 마십시오.'),
            (e209,'나나','두 분이 가까이 계셨다는 자료입니다. 문을 닫으신 뒤는 따로 봐야 해요.'))),
        ('02-T08k','예비 열쇠로','사용은 **E208','5',('v4:E203',e209,e208),(
            ('v4:E203','아카리','예비 열쇠를 쓴 건 맞지만 그 뒤에 누가 받침을 움직였다는 기록은 아니에요.'),
            (e209,'켄','고리는 옮길 수 있잖아. 받침과 접시 아래쪽이랑 같이 봐.'))),
        ('02-T08f','숨길 수 있었던','4에는 **02-I07k','4',('v4:E203',e205,e211),(
            ('v4:E203','아카리','어느 곳에 문이 있는지부터 보세요. 열쇠 받은 때를 여기 넣을 수는 없어요.'),
            (e205,'쇼','그 격자의 방향과 도면이 이어진 쪽이 같은지 비교하십시오.'))),
    )
    for round_number, (scene_id, title, rule, target, ammo, wrongs) in enumerate(closing_hearings, 14):
        scene = scenes[scene_id]
        start = at(scene, '#### 논스톱 — '+title)
        stop = at(scene, rule)
        if scene_id=='02-T08g':
            tail = choice('T2-QA-REV13', ref(scene, stop), '치명상을 마지막 퇴실 뒤의 일로 옮길 수 없는 별도 근거는?',
                          ['앞문 교대와 발견 때 처음 다시 열린 문','공연 때 들린 박수','그 사람이 반납한 열쇠의 위치'],
                          0, [e208,e207], tail,
                          [(1,'유우','그 소리는 앞문에 있던 사람이 들었다고 한 게 아니야.'),
                           (2,'아카리','열쇠가 있는 데와 실제로 다시 열리는 문을 본 때는 달라요.')])
        tail = graph.lines(scene, stop+1, len(scene.body), tail)
        tail = hearing(f'T2-NS-REV{round_number}', scene, start, stop, target, ammo, tail, wrongs)
        tail = graph.lines(scene, 0, start, tail)
    scene = scenes['02-T08h']
    ledger_panic = at(scene,'#### 패닉')
    ledger_rule = at(scene,'정답은 **E210의 가명')
    tail = graph.lines(scene,ledger_rule+1,len(scene.body),tail)
    tail = choice('T2-QA-REV16',ref(scene,ledger_rule),'장부에 적히지 않은 실제 이동을 확인할 자료는?',
                  ['지급 수량만 반복해서 읽는다','벌어진 주머니 고리','도면의 끝과 실제 통로의 표식'],2,[e210,e211],tail,
                  [(0,'코토','몇 개가 나갔는지와 그 사람이 어느 쪽으로 걸었는지는 따로 보아야 해요.'),
                   (1,'쇼','부품의 소속은 통행자의 목록이 아닙니다.')])
    ident = 'T2-PN-REV03'
    lanes = [{'id':str(i),'actor':SPEAKERS[name],'speaker':name,'lines':[]}
             for i,name in enumerate(('코토','켄','린'))]
    rows = []
    for offset in range(ledger_panic+1,ledger_rule):
        cells = [cell.strip() for cell in scene.body[offset].strip('|').split('|')]
        if len(cells)!=4 or not cells[0].isdigit():
            continue
        for index,(lane,raw) in enumerate(zip(lanes,cells[1:])):
            raw = raw.replace('[약점] ','')
            weak = (cells[0],index)==('5',2)
            row = debate_statement(ident,f'{index}:{cells[0]}',lane['speaker'],raw,ref(scene,offset),
                                   'weak' if weak else 'plain',e210 if weak else '')
            rows.append(row)
            lane['lines'].append(row['id'])
            if '[큰 소리]' in raw:
                noise = debate_statement(ident,'noise',lane['speaker'],raw,ref(scene,offset),'noise')
                rows.append(dict(noise,noiseRole='loud',noiseDurability=2,hostStatement=row['id']))
    assert [len(lane['lines']) for lane in lanes]==[6,6,6] and len(rows)==19
    cards = [{'id':key,'name':records[key][0],'text':records[key][1]} for key in (e211,e209,e207,e210)]
    tail = task(ident,ref(scene,ledger_rule),{'kind':'panic','title':'찾아내는 이름과 써 둔 수량',
                'lines':rows,'options':cards,'filterOwnedEvidence':True,
                'wrongCards':{e211:'route',e209:'ring',e207:'door'}}, [card['id'] for card in cards],tail,[
                    ({'cause':'route'},'린','내가 그 길을 갔다는 것하고 누가 무엇을 받아 갔는지 네가 아는 건 다르잖아.'),
                    ({'cause':'ring'},'쇼','부품의 소속은 장부의 개인 이름이 아닙니다.'),
                    ({'cause':'door'},'사츠키','지금은 준비실 문을 나간 사람 말고 공개된 종이에 뭐가 적혔는지 묻고 있어.')])
    tasks[ident]['debate'] = {'id':ident,'kind':'panic','lines':rows,'bullets':cards,
                              'lanes':lanes,'synchronizedBeats':True}
    tail = graph.lines(scene,0,ledger_panic,tail)
    for scene_id in ('02-T08d','02-T08j'):
        scene = scenes[scene_id]
        tail = graph.lines(scene, 0, len(scene.body), tail)
    scene = scenes['02-T08e']
    hands_at = at(scene, '#### 논스톱')
    hands_rule = at(scene, 'E209의 **마지막 생존')
    tail = graph.lines(scene, hands_rule+1, len(scene.body), tail)
    tail = hearing('T2-NS-REV18', scene, hands_at, hands_rule, '4', (e204,e208,e209), tail,
                   [(e204,'하루카','빌려 준 건 공용 겉옷이야. 개인 주머니가 누가 손댈 때 뜯겼는지는 보여 주지 않아.'),
                    (e208,'리쿠','받침이 쓰였다는 건 이제 알았어. 내 말은 그 전에 누가 린한테 뭘 했냐는 거야.')])
    tail = graph.lines(scene, 0, hands_at, tail)
    scene = scenes['02-T08c']
    duel_at = at(scene, '#### 반론 쇼다운')
    first = at(scene, '상대는 린.')
    last = at(scene, '발전 이후 린은')
    close = at(scene, '#### 가설 재구성')
    reconstruct_at = at(scene,'첫 입력에서')
    reconstruct_end = at(scene,'**켄**　내가 그러면 아카리가')
    tail = graph.lines(scene,reconstruct_end,len(scene.body),tail)
    route_menu = 'rev:02:spare-key-hypotheses'
    complete = tail
    for key in ('before','during','after'):
        complete = graph.add(route_menu+':complete:'+key,type='branch',
                             cases=[{'flag':'02-T08c:'+key,'equals':True,'to':complete}],default=route_menu)
    routes = (
        ('before','마지막 생존 이전에 이미 들어와 있었다면?','사진 바깥의 관찰 범위와 숨을 수 있는 공간을 맞춘다',
         '아카리가 열쇠를 갖고 있었다는 말만 낸다','사츠키','그 전에 누가 안에서 들어오라고 했으면 그 열쇠는 필요 없었어. 지금 확인할 건 그 사람이 있을 자리야.'),
        ('during','창구에서 살아 있는 아이를 본 뒤 들어왔다면?','앞문을 보던 세 사람의 겹친 시야를 이어 본다',
         '객석에 있던 유우를 사츠키 자리에 놓는다','유우','나는 가까이 오기 전까진 다른 문을 보고 있었어. 내 눈으로 안 보였던 쪽이 비었다고는 하지 마.'),
        ('after','린이 닫고 나간 뒤 발견 전에 열었다면?','닫힌 앞문과 아카리가 처음 다시 연 순간을 맞춘다',
         '열쇠로 열 수 있다는 작동 실험만 낸다','쇼','열 수 있는지와 그 사이 실제로 열렸는지를 아직 구분하지 않으셨습니다.'),
    )
    options = []
    for key,label,correct,wrong,speaker,reply in routes:
        mark = graph.add(route_menu+':mark:'+key,type='stage',set={'02-T08c:'+key:True},next=complete,
                         source=ref(scene,reconstruct_at))
        again = graph.add(route_menu+':wrong:'+key,type='say',actor=SPEAKERS[speaker],speaker=speaker,
                          text=reply,source=ref(scene,reconstruct_at),next=route_menu+':compare:'+key)
        node = graph.add(route_menu+':compare:'+key,type='menu',q=label,source=ref(scene,reconstruct_at),
                         options=[{'id':'wrong','label':wrong,'to':again},{'id':'compare','label':correct,'to':mark}])
        options.append({'id':key,'label':label,'to':node})
    tail = graph.add(route_menu,type='menu',q='예비 열쇠를 쓸 수 있었다고 가정하고, 어느 시점부터 검토할까?',
                     options=options,source=ref(scene,reconstruct_at))
    tail = graph.lines(scene,close+1,reconstruct_at,tail)
    tail = graph.lines(scene, last+1, close, tail)
    duel_waves = [[text.replace('**','') for text in re.findall(r'“([^”]+)”',scene.body[index])[:3]]
                  for index in (first,last)]
    assert [len(wave) for wave in duel_waves]==[3,3]
    cards = [{'id':key,'name':records[key][0],'text':records[key][1]} for key in ('v4:E201',e208,e209)]
    tail = compile_showdown(graph,tasks,dead,seats,'rev:02:pedestal-duel','T2-RS-REV02','넘어졌을 때 받침이 움직였다면',
                            '린',duel_waves,cards,e208,ref(scene,last),
                            ('린','내 옷하고 가까이 있었다고 받침을 어떻게 썼는지 봤다는 말은 하지 마.'),tail)
    mine_at = at(scene, '#### 발굴 이매지네이션')
    mine = (
        ('pedestal-rim','받침의 윗모서리','',''),
        ('shelf-fixed-face','벽에 붙은 고정면','레이','저 면은 따로 움직일 수 없습니다. 여기에 부딪쳤다면 닿은 높이와 위치부터 맞아야 합니다.'),
        ('platter-underside','바닥의 접시 아래','하루카','접시가 들어온 뒤에 그 자리에 생긴 걸 본 건 맞아. 어느 모서리가 닿았는지는 저 위로 올려 봐.'),
        ('pouch-stitch','공구 주머니 봉제선','린','그게 내 거인 건 알았어. 그 옷에 붙었던 걸로 받침 잡은 손까지 보이냐고.'),
    )
    tail = graph.lines(scene, mine_at+1, duel_at, tail)
    tail = task('T2-MM-REV02', ref(scene,mine_at), {'kind':'mindmine','title':'물건이 닿았던 쪽',
                'question':'움직인 물건과 벽에 고정된 면을 가를 때 어느 흔적을 먼저 볼까?',
                'image':MINE_ART+'pedestal-board.svg','answerRegionId':mine[0][0],'mineObjects':pedestal_objects,
                'regions':[{'id':key,'label':label,'correct':not speaker,'wrongVariant':key} for key,label,speaker,_ in mine]},
                ['v4:E201',e208,e209], tail,
                [({'cause':key},speaker,reply) for key,_,speaker,reply in mine if speaker])
    tail = graph.lines(scene, 0, mine_at, tail)
    scene = scenes['02-T08b']
    tail = graph.lines(scene, 0, len(scene.body), tail)

    scene = scenes['02-T08']
    plant_at = at(scene, '#### 논스톱 — 어긋난 물건')
    plant_rule = at(scene, '02-I01에서 E209에 첨부한')
    plant_question = at(scene, '린은 곧장 대답하지 않는다.')
    ring_at = at(scene, '#### 논스톱 C')
    ring_rule = at(scene, 'E209 → 4.')
    tail = graph.lines(scene, ring_rule+1, len(scene.body), tail)
    tail = choice('T2-QA-REV10', ref(scene, ring_rule), '공구를 빌려준 뒤에도 고리가 붙어 있었음을 보여 주는 사진은?',
                  ['공연 준비 때 찍은 사진','마지막으로 창구에서 아이에게 접시를 건넨 사진','발견 뒤 고리만 확대해 찍은 사진'],
                  1, [e206,e209], tail,
                  [(0,'린','공구 빌려준 건 그 뒤야. 더 나중에 붙어 있었는지부터 봐.'),
                   (2,'하루카','그 장에는 이미 떨어져 있었어. 붙은 채로 보인 마지막 장을 열어.')])
    tail = hearing('T2-NS-REV13', scene, ring_at, ring_rule, '4', (e204,e210,e209), tail,
                   [(e204,'리쿠','내가 받은 옷에 저 주머니는 안 붙어 있었어. 빌려 간 것하고 나눠서 봐.'),
                    (e210,'소라','장부는 다른 종이가 있었다는 얘기야. 고리가 붙었던 때는 사진에 있잖아.')])
    tail = graph.lines(scene, plant_question+1, ring_at, tail)
    tail = choice('T2-QA-REV09', ref(scene, plant_question), '앞문을 떠났다는 인상은 어떤 순서로 굳어졌을까?',
                  ['반납판을 위조하고 유우가 그 판을 보았다','린이 유우의 위치와 소매를 본 시점을 정해 두었다',
                   '실제 반납 뒤 기록 밖에서 드나들었고 객석의 착각이 나중에 보태졌다'],
                  2, ['v4:E203',e204,e207], tail,
                  [(0,'아카리','제가 열쇠를 받아 보관했어요. 그 시각 자체가 위조된 건 아니에요.'),
                   (1,'유우','내가 그 줄에 서게 한 사람은 없었어. 옷 보고 이름 붙인 건 나였고.')])
    tail = graph.lines(scene, plant_rule+1, plant_question, tail)
    tail = hearing('T2-NS-REV12', scene, plant_at, plant_rule, '4', (e204,e210,e209), tail,
                   [(e204,'린','그건 여기 바닥이 아니야. 방에 들어가서 너희가 처음 찍은 걸 내 봐.'),
                    (e210,'리쿠','그 종이가 거기 있었다고 고리까지 같은 때 놓인 건 아니잖아.')])
    tail = graph.lines(scene, 0, plant_at, tail)

    scene = scenes['02-T07a']
    frame_at = at(scene,'#### 논스톱')
    frame_rule = at(scene,'정답은 E206의 마지막 사진')
    tail = graph.lines(scene, frame_rule+1, len(scene.body), tail)
    tail = hearing('T2-NS-REV11', scene, frame_at, frame_rule, '4', (e207,e208,e206), tail,
                   [(e207,'사츠키','내가 지켜본 건 문이야. 그 사람이 그릇 들고 있는 손을 계속 보지는 않았어.'),
                    (e208,'쇼','발견 당시의 접시 위치부터는 제가 보았습니다. 창구에서 보인 손은 먼저 다른 분에게 물으십시오.')])
    tail = graph.lines(scene, 0, frame_at, tail)

    scene = scenes['02-T07b']
    curtain_at = at(scene,'#### 논스톱')
    curtain_rule = at(scene,'(02-D05a에서 객석 사진')
    retreat_at = at(scene,'#### 섬광 애너그램')
    retreat_rule = at(scene,'질문은 “공연이 끝났다고')
    tail = graph.lines(scene, retreat_rule+1, len(scene.body), tail)
    answer, distractors, question = ANAGRAMS['02-T07b']
    tail = task('T2-AN-REV02', ref(scene, retreat_rule),
                {'kind':'anagram','chapter':2,'title':'마지막 박수가 시간을 정해 주지 않으면',
                 'question':question,'answer':answer,'distractors':list(distractors)}, [e207], tail)
    tail = graph.lines(scene, retreat_at+1, retreat_rule, tail)
    tail = graph.lines(scene, curtain_rule+1, retreat_at, tail)
    tail = hearing('T2-NS-REV10', scene, curtain_at, curtain_rule, '4', (e206,e207,e202), tail,
                   [(e206,'하루카','이건 그 뒤에 창구에서 찍었어. 리쿠가 막 뒤에서 본 자리를 먼저 확인해.'),
                    (e207,'사츠키','내가 본 건 나중의 준비실 앞문이야. 무대 막에서 누가 나왔느냐는 거기서 본 사람한테 물어.')])
    tail = graph.lines(scene, 0, curtain_at, tail)
    scene = scenes['02-T07c']
    tail = graph.lines(scene, 0, len(scene.body), tail)

    scene = scenes['02-T07']
    watch_at = at(scene, '#### 논스톱 E')
    watch_rule = at(scene, 'E207 → 4.')
    swing_at = at(scene, '#### 시야 대조')
    swing_rule = at(scene, '플레이어가 조사 때 만든 반환대')
    shelf_at = at(scene, '#### 논스톱 F')
    shelf_rule = at(scene, '동의는 6에 E206')
    diagram_at = at(scene, '#### 증거 지목 B')
    diagram_rule = at(scene, '질문은 ‘린이 확인하려던')
    tail = graph.lines(scene, diagram_rule+1, len(scene.body), tail)
    exits = ('v4:E205','v4:E210','v4:E211')
    tail = task('T2-BU-REV02', ref(scene, diagram_rule), {
        'kind':'bullet','question':'작업 통로의 끝을 실제 시설과 비교하려면 어떤 언령이 필요할까?',
        'answer':exits[2],'options':[{'id':key,'name':records[key][0],'text':records[key][1]} for key in exits],
    }, exits, tail, [({'optionIndex':0},'레이','그 격자가 이어지는 곳은 의상실입니다. 도면에서 표시한 바깥 통로를 보십시오.'),
                      ({'optionIndex':1},'소라','종이가 한 장 더 있었다고 그 종이 끝에 문이 생기지는 않잖아.')])
    tail = graph.lines(scene, diagram_at+1, diagram_rule, tail)
    tail = graph.lines(scene, shelf_rule+1, diagram_at, tail)
    tail = hearing('T2-NS-REV09', scene, shelf_at, shelf_rule, '6', ('v4:E205',e207,e206), tail,
                   [('v4:E205','쇼','격자가 고정되어 있다는 점은 선반 아래를 직접 보았는지와 별개입니다.'),
                    (e207,'사츠키','난 앞문을 봤어. 그전에 네가 선반 아래를 봤는지부터 물어.')], agree=True)
    tail = graph.lines(scene, swing_rule+1, shelf_at, tail)
    tail = choice('T2-QA-REV08', ref(scene, swing_rule), '발이 안 보이는 곳에서도 누가 앞문을 열었는지 어떻게 확인할까?',
                  ['발이 가려지니 문 전체도 가려진다','교대 시야에 걸치는 문짝의 회전 범위를 확인한다',
                   '앞서 창구에서 찍은 두 사람만 표시한다'], 1, [e207], tail,
                  [(0,'켄','발을 문 아래에 붙여 봐. 문판이 내 무릎만큼 돌면 어디까지 나오는지는 그쪽에서 봤잖아.'),
                   (2,'하루카','내가 안에 있던 사람을 같이 찍은 때하고, 종이를 받고 나서 내가 나간 때를 따로 보자.')])
    tail = graph.lines(scene, watch_rule+1, swing_at, tail)
    tail = hearing('T2-NS-REV08', scene, watch_at, watch_rule, '4', (e206,e202,e207), tail,
                   [(e206,'코토','사진에 두 분이 계신 건 보여요. 제가 물은 건 그 사진을 찍고 나온 다음이에요.'),
                    (e202,'유우','난 저 위에서 그전 소매를 봤어. 사진 찍은 뒤 누가 앞문에 남았는지는 모르는 일이고.')])
    # The optional conversation leads back to the same witness chronology.
    branch_start = at(scene, '##### A —')
    branch_end = at(scene, '##### 합류')
    tail = graph.lines(scene, branch_end+1, watch_at, tail)
    branches = (branch_start, at(scene,'##### B —'), at(scene,'##### C —'), branch_end)
    tail = graph.menu(scene, '유우가 한 문장을 더 말하고 싶어 한다. 어떻게 들을까?', [
        (label, start+1, stop, '') for label, start, stop in zip(
            ('끝까지 들어 준다','중간에 다시 물어 달라고 한다','그날 한 번 더 옆에 앉기로 한다'),
            branches, branches[1:])], tail)
    tail = graph.lines(scene, 0, branch_start, tail)

    scene = scenes['02-T06a']
    order_at = at(scene, '### 누가 먼저')
    order_end = at(scene, '**나나**　제가 누구 먼저')
    tail = graph.lines(scene, order_end, len(scene.body), tail)
    menu_id = 'rev:02:witness-order'
    routes = (
        ('yuu','유우에게 보았던 부분을 먼저 읽게 한다','유우','오른쪽 어깨부터 나왔어. 그 사람이 끝까지 보였다고 적는 건 빼.'),
        ('riku','리쿠에게 받은 옷과 나온 문을 나눠 말하게 한다','리쿠','빌린 옷은 여기 있어. 내가 어느 문에서 나왔는지는 네가 앉은 자리에서 다시 봐.'),
        ('sora','소라에게 함께 있던 때를 묻는다','소라','유우랑 무대에 같이 있었던 때도 있었어. 공연 끝날 때까지 계속 붙어 있지는 않았고.'),
    )
    options = []
    for key, label, speaker, reply in routes:
        node = graph.add(menu_id+':'+key, type='say', actor=SPEAKERS[speaker], speaker=speaker, text=reply,
                         source=ref(scene, order_at), next=tail)
        options.append({'id':key,'label':label,'to':node})
    tail = graph.add(menu_id, type='menu', q='사진을 돌려놓기 전에 누구에게 먼저 물을까?', options=options,
                     source=ref(scene, order_at))
    tail = graph.lines(scene, 0, order_at, tail)

    scene = scenes['02-T06']
    chain_at = at(scene, '#### 추리 연결')
    chain_end = at(scene, '**코토**　창구에서 두 분이 보였다는')
    tail = graph.lines(scene, chain_end, len(scene.body), tail)
    steps = (
        ('이 방에서 살아 있는 아이와 린이 동시에 확인된 기준점은?',
         ('19:30 반납판', '19:34 창구 문답과 사진', '19:33 체크 소매'), 1, (e206,),
         ((0,'하루카','반납판을 내가 찍은 것도 아니고, 옷 사진에는 아이가 없어. 창구에서 접시 받을 때라고.'),
          (2,'유우','내가 객석에서 본 건 옷이야. 아이가 살아 있는 걸 거기서 본 게 아니고.'))),
        ('그 뒤 실제 출입을 확인할 수 있는 곳은?',
         ('앞문','직원 창구','격자로 막힌 의상실 쪽'), 0, ('v4:E205',e207),
         ((1,'하루카','거기로 접시는 갔어도 사람은 지나갈 수 없었어.'),
          (2,'레이','격자 양쪽을 다시 보십시오. 이쪽에서는 통과할 수 없습니다.'))),
        ('마지막 생존과 발견 사이에 아직 대조할 것은?',
         ('예비 열쇠가 있는 곳만','리쿠의 앞선 퇴실 시각','앞문을 맡은 세 사람의 관찰 범위'), 2, (e207,),
         ((0,'아카리','열쇠를 어디에 뒀는지는 제가 말할게요. 제가 문을 계속 본 건 아니에요.'),
          (1,'리쿠','내가 나온 때하고 누가 나중에 문 앞에 있었는지는 다르잖아.'))),
        ('두 사람이 교대할 때 시야가 끊겼는지 무엇으로 확인할까?',
         ('사진 시간만 정렬한다','점검표를 건넨 자리와 남아 있던 미오를 대조한다','교대했다는 말만 함께 있었던 기록으로 적는다'), 1, (e207,),
         ((0,'코토','찍힌 시각으로 미오 씨가 계속 앞에 서 계셨는지 나오지는 않아요.'),
          (2,'사츠키','같이 서 있던 한 사람 이름부터 말해. 우리라고 하면 내가 뒤늦게 왔다고 쓰기 쉽잖아.'))),
        ('창구에서 건넨 접시로 공격 시각까지 정할 수 있을까?',
         ('당시 살아서 대답한 때까지만 정하고, 손상은 따로 대조한다','접시를 건넨 순간에 공격이 일어났다','발견 사진이 있으므로 마지막 생존 목격은 뺀다'), 0, (e206,e208),
         ((1,'미오','내가 잡던 손은 창구에 있었어. 공격이 일어났다고 할 장면까지 거기 넣지 마.'),
          (2,'쇼','발견 사진에 대답한 사람은 없습니다. 마지막 생존을 어디서 보셨는지부터 고르십시오.'))),
        ('앞문 관찰이 이어져도 어떤 경로를 따로 확인해야 할까?',
         ('열쇠를 받은 뒤 아카리가 무얼 봤나','마지막 생존 때 이미 방 안의 사각에 누가 있었나','객석에서 체크 소매가 지나갔나'), 1, (e206,e207),
         ((0,'아카리','열쇠 받은 때에는 준비실을 들여다보지 않았어요. 창구에서 보신 분은 저랑 달라요.'),
          (2,'리쿠','그 전에 내가 어느 문에서 나왔는지 이미 봤잖아. 지금 방 안에 내가 있었다는 말이면 새로 물어.'))),
    )
    for index, (question, options, answer, evidence, wrongs) in reversed(list(enumerate(steps, 1))):
        offset = at(scene, f'{index}. **질문**')
        tail = choice(f'T2-QA-REV06-{index}', ref(scene, offset), question, options, answer, evidence, tail, wrongs)
    anagram_at = at(scene, '#### 섬광 애너그램')
    anagram_rule = at(scene, '질문 “아이의 마지막 반응')
    tail = graph.lines(scene, anagram_rule+1, chain_at, tail)
    question, = re.findall(r'“([^”]+)”', scene.body[anagram_rule])
    answer, distractors = ANAGRAMS['02-T06'][:2]
    tail = task('T2-AN-REV01', ref(scene, anagram_rule),
                {'kind': 'anagram', 'chapter': 2, 'title': '살아 있었던 마지막 위치',
                 'question': question, 'answer': answer, 'distractors': list(distractors)}, [e206], tail)
    timing = at(scene, '래피 “지금 증거로')
    tail = graph.add('rev:02:medical-limit', type='say', actor='sho', speaker='쇼',
                     text='제가 사람 몸을 봤다고 해서 공격 시각까지 분 단위로 읽은 건 아닙니다.',
                     source=ref(scene, timing), next=tail)
    tail = choice('T2-QA-REV05', ref(scene, timing), '지금 증거로 정할 수 있는 건 어떤 시각이죠?',
                  ['받침이 바닥에 떨어진 정확한 분', '마지막으로 살아서 대답한 기준점',
                   '검정이 나가기로 마음먹은 순간', '예비 열쇠가 보관함에 처음 들어간 날'],
                  1, [e206], tail,
                  [(0,'쇼','검안 범위와 마지막 생존 관찰을 분리하십시오.'),
                   (2,'린','그 사람이 무슨 생각을 했는지는 이 사진에 없잖아.'),
                   (3,'아카리','그 열쇠가 언제 들어왔느냐와 누가 마지막에 대답했느냐는 별개예요.')])
    listening = at(scene, '재판판에서')
    tail = graph.lines(scene, listening+1, at(scene, '#### 정답 선택 — 지금'), tail)
    tail = choice('T2-QA-REV04', ref(scene, listening), '미리 틀어 둔 소리만으로 설명되지 않는 관찰은?',
                  ['낮에 기기로 다시 들은 노래','공연이 끝날 때 객석에서 들린 소리','창구에서 새 질문에 맞춰 접시를 받아 든 움직임'],
                  2, [e206], tail,
                  [(0,'유우','그때 다시 나온 건 내 노래야. 내가 바로 앞에 있어도 입 안 움직이고 다시 들렸어.'),
                   (1,'켄','내가 저기서 들었다고는 했는데 뭐라고 했는지까지 못 들었어.')])
    panic = at(scene, '#### 패닉 — 비슷한 소리')
    panic_rule = at(scene, '정답 E202 객석 시야 재현')
    tail = graph.lines(scene, panic_rule+1, listening, tail)
    ident = 'T2-PN-REV02'
    lanes = [{'id': str(index), 'speaker': name, 'actor': SPEAKERS[name], 'lines': []}
             for index, name in enumerate(('켄','유우','하루카'))]
    rows = []
    for offset in range(panic+1, panic_rule):
        cells = [cell.strip() for cell in scene.body[offset].strip('|').split('|')]
        if len(cells) != 4 or not cells[0].isdigit():
            continue
        for index, (lane, raw) in enumerate(zip(lanes, cells[1:])):
            targeted = (cells[0], index) == ('4', 1)
            row = debate_statement(ident, f'{index}:{cells[0]}', lane['speaker'], raw, ref(scene, offset),
                                   'weak' if targeted else 'plain', e202 if targeted else '')
            rows.append(row)
            lane['lines'].append(row['id'])
            if '[큰 소리]' in raw:
                noise = debate_statement(ident, 'noise', lane['speaker'], raw, ref(scene, offset), 'noise')
                rows.append(dict(noise, noiseRole='loud', noiseDurability=2, hostStatement=row['id']))
    cards = [{'id':key, 'name':records[key][0], 'text':records[key][1]} for key in (e204,e206,e202)]
    assert sum(row['kind']=='weak' for row in rows)==1 and sum(row['kind']=='noise' for row in rows)==1
    tail = task(ident, ref(scene, panic_rule),
                {'kind':'panic','title':'비슷한 소리, 다른 장소','lines':rows,'options':cards,
                 'filterOwnedEvidence':True,'wrongCards':{e204:'coat',e206:'lower'}}, [e204,e206,e202], tail,
                [({'cause':'coat'},'유우','누구 옷인지 바꿔도 내가 어느 문턱을 봤는지는 안 바뀌잖아.'),
                 ({'cause':'lower'},'하루카','이 장을 찍을 때는 객석이 아니라 아래였어.')])
    tasks[ident]['debate'] = {'id':ident,'kind':'panic','lines':rows,'bullets':cards,
                              'lanes':lanes,'synchronizedBeats':True}
    tail = graph.lines(scene, 0, panic, tail)

    scene = scenes['02-T05b']
    pick_at = at(scene, '### 말을 했던 자리')
    pick_end = at(scene, '**유우**　내가 공연장에서는')
    tail = graph.lines(scene, pick_end, len(scene.body), tail)
    tail = choice('T2-QA-REV07', ref(scene, pick_at), '창구를 통해 누군가 부탁해서 일어났다는 가설은 어떻게 확인할까?',
                  ['앞문에서 지나간 사람부터 목소리에 붙인다','누구도 창구에서 부탁할 수 없었다고 적는다',
                   '창구에서 확인한 요청과 방 안에서 확인한 움직임을 분리한다'], 2, [e206,e207,e208], tail,
                  [(0,'아카리','제 열쇠가 문을 열 때까지 안에 부탁드린 말이 있었다고도 쓰시나요?'),
                   (1,'레이','물건이 들어갈 수 없다는 판단에 목소리까지 넣지는 마십시오.')])
    tail = graph.lines(scene, 0, pick_at, tail)

    scene = scenes['02-T05a']
    ns_at = at(scene, '#### 논스톱 — 그림을')
    ns_end = at(scene, '4에는 **E206')
    spot_at = at(scene, '#### 지점 지목')
    tail = graph.lines(scene, spot_at+3, len(scene.body), tail)
    coords = (('front','준비실 앞문',(.137,.324,.241,.644)),
              ('shelf','안쪽 선반 앞',(.59,.53,.758,.644)),
              ('tray','창구 바깥에서 접시를 내민 자리',(.79,.55,.887,.661)))
    tail = task('T2-SP-REV02', ref(scene, spot_at),
                {'kind':'spot','question':'미오가 사진을 나중에 보기 전에 직접 접시를 건넨 곳은?',
                 'image':MINE_ART+'theatre-section.svg','answerRegionId':'tray',
                 'regions':[{'id':key,'label':label,'wrongVariant':key,'polygon':[[x,y],[a,y],[a,b],[x,b]]}
                            for key,label,(x,y,a,b) in coords]}, [e206], tail,
                [({'cause':'front'},'미오','저 문은 교대 기록으로 봐. 내가 접시를 건넨 곳은 창구야.'),
                 ({'cause':'shelf'},'하루카','안쪽에서 보인 위치야. 접시를 내민 미오는 벽 반대편에 있었어.')])
    tail = hearing('T2-NS-REV07', scene, ns_at, ns_end, '4', (e204,e207,e206), tail,
                   [(e204,'하루카','작업복을 빌려줄 때 찍은 장이야. 우리가 접시를 들고 내려간 때하고 달라.'),
                    (e207,'리쿠','그 앞문을 본 건 다음 일이잖아. 사진 말고 창구에서 직접 본 걸 물었어.')])
    return graph.lines(scene, 0, ns_at, tail)


def chapter_two_entry(scenes, ring_objects, pedestal_objects):
    graph = CampaignGraph()
    dead = ['kaede', 'taiga', 'ai']
    seats = [name for name in SPEAKERS.values() if name != 'lappy']
    finding = scenes['02-T00']
    view = scenes['02-T01']
    question_at = finding.body.index('#### 정답 선택 — 발견 표에 없는 것')
    round_at = view.body.index('#### 논스톱 A — 나온 문')
    stop = view.body.index('#### 시점 재현 — 내려가기 전의 한 걸음')
    rule = next(i for i in range(round_at, stop) if view.body[i].startswith('정답 E202 → 4'))
    records = {
        'v4:E201': ('래피 파일의 발견 기록', '19시 34분 무렵 서서 접시를 받았고, 19시 42분에 발견됐다. 파일의 손상 기록은 발견 당시의 상태를 남긴다.'),
        'v4:E202': ('객석에서 겹치는 두 문', '노란 줄 안쪽에서는 기둥 뒤로 준비실과 의상실의 문턱이 겹친다. 한 단 내려가면 두 문턱을 구별할 수 있다.'),
        'v4:E203': ('반납판과 앞문 잠금', '반납판에는 19시 30분의 열쇠 반환이 적혀 있다. 안에서 나갈 수 있지만, 닫힌 문으로 다시 들어가려면 열쇠가 필요하다.'),
        'v4:E204': ('대여 사진과 공용 작업복', '리쿠도 체크무늬 작업복을 입었다. 옷의 무늬와 대여 사진만으로 객석에서 본 사람이 누구인지 확정할 수 없다.'),
        'v4:E205': ('격자와 물류 덮개의 점검 띠', '두 방 사이의 격자는 양쪽에서 고정돼 있다. 물류 덮개의 사진을 같은 방향으로 맞추면 못 머리 아래에서 접힌 끝과 틀·덮개를 가로지른 띠의 경계가 이어진다. 번호만으로 같은 띠라고 판단하지 않는다.'),
        'v4:E206': ('음식 창구 사진과 대면 진술', '19시 34분, 창구 안 두 사람과 접시를 받는 손을 확인했다. 사본에서 얼굴은 뺐다. 사진의 사각과 그때 들은 말은 실제 목격자에게 별도로 확인한다.'),
        'v4:E207': ('앞문을 지켜본 세 사람의 교대', '미오가 반환대에 머무는 동안 하루카가 문을 보았고 사츠키가 자리를 이어 받았다. 19시 34분 이후의 연속 관찰이다. 객석의 유우가 그전 시각에 본 문턱은 별도다.'),
        'v4:E208': ('준비실의 낮은 받침과 접시 아래', '받침이 움직인 자리와 접시 아래 흔적을 따로 촬영했다. 접시가 넘어지기 전에 방 안에서 남은 흔적이다. 고정물에는 확인한 손상과 맞는 면이 없다.'),
        'v4:E209': ('벌어진 고리와 끊긴 주머니 봉제선', '발견 장소에 떨어진 고리의 벌어진 끝과 주머니의 봉제선이 맞는다. 준비 사진과 마지막 창구 사진 모두 고리가 붙어 있다. 떨어지는 장면과 공격 장면을 찍은 자료는 없다.'),
        'v4:E210': ('지급 장부와 밑장에 남은 눌림', '수량과 반환 표식은 남았으나 받는 사람 이름은 기호다. 별도 사본이 남았다는 근거로 쓴다. 사람을 다치게 한 때를 보여 주지는 않는다.'),
        'v4:E211': ('바깥 작업 통로 도면과 실제 표식', '도면 끝의 표식을 작업 통로의 실제 입구와 맞춰 봤다. 열린 끝은 공개 작업 통로이며 준비실과 연결되는 별도 문이 아니다.'),
    }
    ns_id, choice_id = 'T2-NS-REV01', 'T2-QA-REV01'
    rows = []
    for i in range(round_at + 1, rule):
        parts = [cell.strip() for cell in view.body[i].strip('|').split('|')]
        if len(parts) != 4 or not parts[0].isdigit():
            continue
        index, speaker, raw, role = parts
        weak = index == '4'
        assert weak == (role == '논파')
        rows.append(debate_statement(ns_id, index, speaker, raw, view.source(view.line + i + 1),
                                     'weak' if weak else 'plain', 'v4:E202' if weak else ''))
    assert len(rows) == 16
    ammo = ['v4:E202', 'v4:E203', 'v4:E204']
    cards = [{'id': key, 'name': records[key][0], 'text': records[key][1]} for key in ammo]
    ns_title = view.body[round_at].partition(' — ')[2]
    variants = []
    for index, (speaker, line) in enumerate(zip(('쇼', '나나'), re.findall(r'“([^”]+)”', finding.body[question_at + 2]))):
        variants.append({'optionIndex': index, 'script': [{'id': f'{choice_id}:wrong:{index}', 'type': 'say',
            'actor': SPEAKERS[speaker], 'speaker': speaker, 'text': line, 'source': finding.source(finding.line + question_at + 3)}]})
    assert len(variants) == 2
    wrong_line, = re.findall(r'“([^”]+)”', view.body[rule])
    tasks = {
        ns_id: {'taskId': ns_id, 'ready': True, 'requiresEvidence': ['v4:E202'],
                'stage': {'id': ns_id, 'v4': True, 'kind': 'nonstop', 'title': ns_title,
                          'lines': rows, 'options': cards, 'filterOwnedEvidence': True, 'authoredAmmo': ammo,
                          'wrongCards': {'v4:E203': 'returned-key'}},
                'debate': {'id': ns_id, 'kind': 'nonstop', 'title': ns_title, 'lines': rows, 'bullets': cards},
                'queues': {'wrongVariants': [{'cause': 'returned-key', 'script': [{'id': ns_id + ':wrong:0',
                    'type': 'say', 'actor': 'mio', 'speaker': '미오', 'text': wrong_line, 'source': view.source(view.line + rule + 1)}]}]}},
        choice_id: {'taskId': choice_id, 'ready': True, 'requiresEvidence': ['v4:E201'],
                    'stage': {'id': choice_id, 'v4': True, 'kind': 'choice', 'title': '발견 표에 없는 것',
                              'question': '래피 파일로 확인할 수 있는 사실은?', 'answer': 2,
                              'options': ['그 방에서 다쳤다', '문이 닫히기 전까지 움직일 수 있었다', '발견 당시 확인한 손상']},
                    'queues': {'wrongVariants': variants}},
    }
    tail = graph.add('rev:02:excerpt-end', type='end')
    tail = chapter_two_last_sighting(graph, scenes, tasks, records, dead, seats, tail, pedestal_objects)
    sighting_checkpoint = graph.add('rev:02:sighting-checkpoint',type='stage',enterCourt=True,next=tail)
    armament_checkpoint = graph.add('rev:02:armament-checkpoint',type='stage',enterCourt=True,next='rev:02:T2-AA-REV01')
    physical_checkpoint = graph.add('rev:02:physical-checkpoint',type='stage',enterCourt=True,next='rev:02:T2-MM-REV02')
    checkpoints = [('last-sighting',sighting_checkpoint),('theatre-armament',armament_checkpoint),
                   ('theatre-physical',physical_checkpoint)]
    if 'T2-CM-REV01' in tasks:
        for name,task_id in (('comic-hearing','T2-CM-REV01'),('vote-hearing','T2-VOTE-REV01')):
            point = graph.add('rev:02:'+name+'-checkpoint',type='stage',enterCourt=True,next='rev:02:'+task_id)
            checkpoints.append((name,point))
    panic_scene = scenes['02-T02']
    panic_heading = panic_scene.body.index('#### 패닉 A — 보증의 범위')
    grille = panic_scene.body.index('#### 지점 지목 — 물건을 돌려놓는 구멍')
    seal = panic_scene.body.index('#### 논스톱 D — 누가 봉인 안쪽에 서 있었어')
    seal_rule = next(i for i in range(seal, len(panic_scene.body)) if panic_scene.body[i].startswith('정답 E205'))
    seal_end = panic_scene.body.index('#### 발굴 — 찢긴 쪽')
    seal_source = panic_scene.source(panic_scene.line + seal_rule + 1)
    perjury = scenes['02-T04']
    lie_at = perjury.body.index('#### 우소다마 — 바깥에서 보인 문턱')
    lie_text = next(i for i,row in enumerate(perjury.body) if row.startswith('기본 E202'))
    lie_source = perjury.source(perjury.line+lie_text+1)
    lie_id = 'T2-LI-REV01'
    phrase, *others = re.findall(r'“([^”]+)”',perjury.body[lie_text])[2:]
    assert len(others)==4
    lie_rows = [debate_statement(lie_id,i,actor,text,lie_source)
                for i,(actor,text) in enumerate(zip(('유우','레이','코토','리쿠'),others))]
    line = debate_statement(lie_id,4,'리쿠',phrase,lie_source,'weak','v4:E202')
    line['weak']['lie'] = True
    lie_rows.insert(3,line)
    lie_cards = [{'id':key,'name':records[key][0],'text':records[key][1]} for key in ('v4:E202','v4:E204','v4:E205')]
    tasks[lie_id] = {'taskId':lie_id,'ready':True,'requiresEvidence':[card['id'] for card in lie_cards],
        'stage':{'id':lie_id,'kind':'nonstop','v4':True,'title':'바깥에서 보인 문턱','lines':lie_rows,
                 'options':lie_cards,'authoredAmmo':[card['id'] for card in lie_cards],'filterOwnedEvidence':True,
                 'wrongCards':{'v4:E202':'repeat','v4:E204':'coat'}},
        'transformation':{'sourceEvidenceId':'v4:E202','lieLabel':'객석에서도 그쪽 문턱을 구분했다','intentionalHold':True},
        'debate':{'id':lie_id,'kind':'nonstop','lines':lie_rows,'bullets':lie_cards},
        'queues':{'wrongVariants':[{'cause':key,'script':[{'id':f'{lie_id}:{key}','type':'say','actor':'riku',
                    'speaker':'리쿠','text':reply,'source':lie_source}]} for key,reply in (
                    ('repeat','네가 안 보였다고 그대로 말하면 내가 한 말이랑 같잖아.'),
                    ('coat','그건 내가 입었던 무늬고. 문턱이 보이는 자리부터 말해.'))]}}
    separation = 'rev:02:sort-perjury'
    separate_at = next(i for i,row in enumerate(perjury.body) if row.startswith('플레이어는 **유우가 실제로'))
    sort_ref = perjury.source(perjury.line+separate_at+1)
    chamber = scenes['02-T05']
    window_at = chamber.body.index('#### 논스톱 — 찍고 나서 다시 본 때')
    window_rule = next(i for i,row in enumerate(chamber.body) if row.startswith('E206 가운데'))
    scrum_at = chamber.body.index('#### 논의 스크럼 — 복도 쪽에서 들어왔나, 방 안에서 일어났나')
    experiment_at = chamber.body.index('#### 조작 가능 범위 — 밖에 서서 한 일이라는 설명')
    experiment_rule = next(i for i,row in enumerate(chamber.body) if row.startswith('플레이어는 02-I04b의 두 구조'))
    experiment_ref = chamber.source(chamber.line+experiment_rule+1)
    experiment = 'rev:02:outside-force'
    tail = graph.lines(chamber,experiment_rule+1,len(chamber.body),tail)
    picks = []
    for name,label,actor,reply in (
        ('grille','격자와 창구 너비만 비교한다','rei','통과할 수 있는 범위는 보입니다. 그 도구가 닿은 자리는 실측한 방의 위치도 보십시오.'),
        ('both','통과 너비와 방 안 받침·접시 위치를 같은 도면에서 대조한다','',''),
        ('floor','발견 장소의 흔적만 비교한다','sho','받침이 움직인 곳은 확인했습니다. 창의 너비와 도구가 닿는 범위를 함께 확인하십시오.'),
    ):
        destination = tail
        if actor:
            destination = graph.add(experiment+':'+name,type='say',actor=actor,
                                     speaker=next(k for k,v in SPEAKERS.items() if v==actor),
                                     text=reply,source=experiment_ref,next=experiment)
        picks.append({'id':name,'label':label,'to':destination})
    tail = graph.add(experiment,type='menu',q='바깥에서 같은 도구로 할 수 있었는지 어떻게 확인할까?',
                     options=picks,source=experiment_ref)
    tail = graph.lines(chamber,experiment_at+1,experiment_rule,tail)
    response_at = next(i for i,row in enumerate(chamber.body) if row.startswith('방향 단계가 끝난다.'))
    tail = graph.lines(chamber,response_at+1,experiment_at,tail)
    scrum_id = 'T2-SD-REV01'
    pairs, wrongs = [], {}
    keywords = (
        ('아무도 없던 시간','비었다는 때'),('반대편','문 두 개가 겹쳤어'),
        ('물류 개구부','양쪽 사진'),('예비 열쇠','언제 건너갔는지'),
        ('받침','접시 아래 흔적'),('어제 떨어졌으면','오늘 공연 준비 때'),
    )
    for offset in range(scrum_at+1,response_at):
        cells = [cell.strip() for cell in chamber.body[offset].strip('|').split('|')]
        if len(cells)==2 and cells[0] in SPEAKERS and cells[1].startswith('“'):
            wrongs[cells[0]] = cells[1].strip('“”')
        if len(cells)!=3 or '“' not in cells[0]:
            continue
        them,claim = re.fullmatch(r'(\S+)\s+“([^”]+)”',cells[0]).groups()
        us,reply = re.fullmatch(r'(\S+)\s+“([^”]+)”',cells[2]).groups()
        claim_word,reply_word = keywords[len(pairs)]
        assert claim_word in claim and reply_word in reply
        pairs.append({'id':f'{scrum_id}:{len(pairs)}','them':them,'themActor':SPEAKERS[them],'themText':claim,
                      'us':us,'usActor':SPEAKERS[us],'usText':reply,'keyword':cells[1],
                      'claimKeyword':claim_word,'responseKeyword':reply_word,'duration':11})
    assert len(pairs)==6 and len(wrongs)==6
    scrum_source = chamber.source(chamber.line+scrum_at+1)
    for pair in pairs:
        pair['wrong'] = [{'id':pair['id']+':retry','type':'say','actor':pair['themActor'],
                          'speaker':pair['them'],'text':wrongs[pair['them']],'source':scrum_source}]
    tasks[scrum_id] = {'taskId':scrum_id,'ready':True,'requiresEvidence':['v4:E205','v4:E206','v4:E207','v4:E208','v4:E209'],
        'stage':{'id':scrum_id,'kind':'scrum','v4':True,'title':'복도 쪽에서 들어왔나, 방 안에서 일어났나',
                 'pairs':pairs,'teams':{side:[pair[side+'Actor'] for pair in pairs] for side in ('them','us')},
                 'scrumPresentation':{'topic':'어느 쪽에서 사건의 시간을 좁힐까',
                                      'them':'복도 쪽에서 온 사람을 검토한다','us':'준비실 안의 시간을 좁힌다'}},
        'queues':{}}
    tail = graph.add('rev:02:inside-outside-scrum',type='task',taskId=scrum_id,trialDead=dead,seats=seats,
                     source=scrum_source,success=tail,next=tail)
    window_id = 'T2-NS-REV06'
    window_source = chamber.source(chamber.line+window_rule+1)
    window_rows = []
    for offset in range(window_at+1,window_rule):
        if match := STMT.match(chamber.body[offset]):
            index,speaker,raw,_ = match.groups()
            window_rows.append(debate_statement(window_id,index,speaker,raw,chamber.source(chamber.line+offset+1),
                                                'weak' if index=='4' else 'plain','v4:E206' if index=='4' else ''))
    assert len(window_rows)==14
    window_cards = [{'id':key,'name':records[key][0],'text':records[key][1]} for key in ('v4:E207','v4:E204','v4:E206')]
    tasks[window_id] = {'taskId':window_id,'ready':True,'requiresEvidence':[card['id'] for card in window_cards],
        'stage':{'id':window_id,'v4':True,'kind':'nonstop','title':'찍고 나서 다시 본 때','lines':window_rows,
                 'options':window_cards,'authoredAmmo':[card['id'] for card in window_cards],'filterOwnedEvidence':True,
                 'wrongCards':{'v4:E207':'watching'}},
        'debate':{'id':window_id,'kind':'nonstop','lines':window_rows,'bullets':window_cards},
        'queues':{'wrongVariants':[{'cause':'watching','script':[{'id':window_id+':watching','type':'say',
                   'actor':'haruka','speaker':'하루카','text':'내가 앞문을 본 때하고 셔터 누른 때를 나눠 보라고.',
                   'source':window_source}]}]}}
    tail = graph.lines(chamber,window_rule+1,scrum_at,tail)
    tail = graph.add('rev:02:window-time-nonstop',type='task',taskId=window_id,trialDead=dead,seats=seats,
                     source=window_source,success=tail,next=tail)
    tail = graph.lines(chamber,0,window_at,tail)
    tail = graph.lines(perjury,separate_at+1,len(perjury.body),tail)
    mistake = graph.add(separation+':witness',type='say',actor='yuu',speaker='유우',
                        text='내가 본 건 옷이야. 거기서 어느 문인지는 나도 못 봤어.',source=sort_ref,next=separation)
    mistake2 = graph.add(separation+':alibi',type='say',actor='riku',speaker='리쿠',
                         text='붙인 때랑 저녁에 나온 때를 왜 같이 쓰는 건데?',source=sort_ref,next=separation)
    tail = graph.add(separation,type='menu',q='위증 뒤 실제 사진과 비교해 남길 항목은?',source=sort_ref,
                     options=[{'id':'seen','label':'미오가 객석에서 문턱을 구분했다','to':mistake},
                              {'id':'tape','label':'리쿠가 설명한 낮은 테이프 위치','to':tail},
                              {'id':'waited','label':'리쿠는 저녁까지 같은 방만 지켰다','to':mistake2}])
    first_perjury = next(i for i,row in enumerate(perjury.body) if row.startswith('**미오**　나는 그 위치에서도'))
    tail = graph.lines(perjury,first_perjury,separate_at,tail)
    tail = graph.add('rev:02:costume-perjury',type='task',taskId=lie_id,trialDead=dead,seats=seats,
                     source=lie_source,success=tail,next=tail,
                     outcomes={'perjury':{'judgment':'lie','to':tail,'sets':{'02-T04:perjury':True}}})
    tail = graph.lines(perjury,0,lie_at,tail)
    second_agreement = scenes['02-T03b']
    second_at = second_agreement.body.index('#### 논스톱 동의 — 그때 다시 받을 필요가 있던 사람')
    second_rule = next(i for i,row in enumerate(second_agreement.body) if row.startswith('E203으로'))
    second_ref = second_agreement.source(second_agreement.line+second_rule+1)
    second_id = 'T2-NS-REV05'
    second_rows = []
    for offset in range(second_at+1,second_rule):
        if match := STMT.match(second_agreement.body[offset]):
            index,actor,raw,_ = match.groups()
            row = debate_statement(second_id,index,actor,raw,second_agreement.source(second_agreement.line+offset+1))
            if index=='4':
                word, = re.findall(r'\*\*([^*]+)\*\*',raw)
                row.update(kind='agree',agree='v4:E203',agreeTarget={'word':word,'glyphStart':row['text'].index(word)})
            second_rows.append(row)
    assert len(second_rows)==10
    second_cards = [{'id':key,'name':records[key][0],'text':records[key][1]} for key in ('v4:E204','v4:E205','v4:E203')]
    tasks[second_id] = {'taskId':second_id,'ready':True,'requiresEvidence':[card['id'] for card in second_cards],
        'stage':{'id':second_id,'kind':'nonstop','v4':True,'title':'그때 다시 받을 필요가 있던 사람','lines':second_rows,
                 'options':second_cards,'authoredAmmo':[card['id'] for card in second_cards],'filterOwnedEvidence':True,
                 'wrongCards':{'v4:E204':'coat','v4:E205':'grille'}},
        'debate':{'id':second_id,'kind':'nonstop','lines':second_rows,'bullets':second_cards},
        'queues':{'wrongVariants':[{'cause':key,'script':[{'id':f'{second_id}:{key}','type':'say',
                    'actor':SPEAKERS[actor],'speaker':actor,'text':reply,'source':second_ref}]} for key,actor,reply in (
                    ('coat','리쿠','옷을 갖고 있었던 사람이 열쇠까지 갖고 있던 건 아니야.'),
                    ('grille','아카리','격자와 앞문은 열 수 있는 방식부터 다릅니다. 지금은 앞문을 말씀드리는 거예요.'))]}}
    tail = graph.lines(second_agreement,second_rule+1,len(second_agreement.body),tail)
    tail = graph.add('rev:02:admission-agreement',type='task',taskId=second_id,trialDead=dead,seats=seats,
                     source=second_ref,success=tail,next=tail)
    tail = graph.lines(second_agreement,0,second_at,tail)
    theory = scenes['02-T03a']
    theory_at = theory.body.index('#### 시점 선택 — 처음부터 안에 있었을 가능성')
    theory_rule = next(i for i in range(theory_at,len(theory.body)) if theory.body[i].startswith('플레이어가 앞서'))
    theory_source = theory.source(theory.line+theory_rule+1)
    theory_id = 'T2-QA-REV03'
    tail = graph.lines(theory,theory_rule+1,len(theory.body),tail)
    tasks[theory_id] = {'taskId':theory_id,'ready':True,'requiresEvidence':['v4:E205','v4:E207'],
        'stage':{'id':theory_id,'v4':True,'kind':'choice','answer':2,
                 'question':'이미 들어가 있었을 가능성을 검토하려면 어느 때부터 볼까?',
                 'options':['옆방의 격자','앞문에서 두 사람을 본 뒤','앞문을 계속 보기 전']},
        'queues':{'wrongVariants':[{'optionIndex':index,'script':[{'id':f'{theory_id}:{index}','type':'say',
                  'actor':SPEAKERS[actor],'speaker':actor,'text':line,'source':theory_source}]}
                  for index,actor,line in (
                     (0,'소라','격자로 넘어오는 건 아까 뺐잖아. 이번엔 안에 처음부터 남았다고 했어.'),
                     (1,'사츠키','그때라면 둘 뒤에 따라 들어온 거야. 먼저 들어가 있었던 때부터 봐.'))]}}
    tail = graph.add('rev:02:prior-occupancy-choice',type='task',taskId=theory_id,trialDead=dead,seats=seats,
                     source=theory_source,success=tail,next=tail)
    tail = graph.lines(theory,0,theory_at,tail)
    returned = scenes['02-T03']
    agreement_at = returned.body.index('#### 논스톱 B — 기록 한 줄을 살린다')
    agreement_rule = next(i for i,row in enumerate(returned.body) if row.startswith('정답 E203 → 3'))
    duel_at = returned.body.index('#### 반론 쇼다운 — 바깥에서 같은 손잡이를 돌리면')
    first_wave = next(i for i,row in enumerate(returned.body) if row.startswith('**첫 국면.**'))
    later_wave = next(i for i,row in enumerate(returned.body) if row.startswith('**발전.**'))
    duel_source = returned.source(returned.line+later_wave+1)
    duel_id = 'T2-RS-REV01'
    waves = [re.findall(r'“([^”]+)”',returned.body[index]) for index in (first_wave,later_wave)]
    assert [len(lines) for lines in waves] == [4,4]
    cards = [{'id':key,'name':records[key][0],'text':records[key][1]} for key in ('v4:E203','v4:E205','v4:E206')]
    tail = graph.lines(returned,later_wave+1,len(returned.body),tail)
    tail = compile_showdown(graph,tasks,dead,seats,'rev:02:exterior-latch-duel',duel_id,'바깥에서 같은 손잡이를 돌리면',
                            '코토',(waves[0], [line.replace('**','') for line in waves[1][:3]]),
                            cards,'v4:E203',duel_source,('코토',waves[1][-1]),tail)
    tail = graph.lines(returned,duel_at+1,first_wave,tail)
    tail = graph.lines(returned,agreement_rule+1,duel_at,tail)
    agreement_id = 'T2-NS-REV04'
    agreement_rows = []
    for offset in range(agreement_at+1,agreement_rule):
        match = STMT.match(returned.body[offset])
        if not match:
            continue
        index,actor,raw,_ = match.groups()
        row = debate_statement(agreement_id,index,actor,raw,returned.source(returned.line+offset+1))
        if index == '3':
            word, = re.findall(r'\*\*([^*]+)\*\*',raw)
            row.update(kind='agree',agree='v4:E203',agreeTarget={'word':word,'glyphStart':row['text'].index(word)})
        agreement_rows.append(row)
    assert len(agreement_rows) == 14
    agreement_source = returned.source(returned.line+agreement_rule+1)
    tasks[agreement_id] = {'taskId':agreement_id,'ready':True,'requiresEvidence':['v4:E203','v4:E205','v4:E206'],
        'stage':{'id':agreement_id,'v4':True,'kind':'nonstop','title':'기록 한 줄을 살린다','lines':agreement_rows,
                 'options':cards,'authoredAmmo':[card['id'] for card in cards],'filterOwnedEvidence':True,
                 'wrongCards':{'v4:E206':'window-photo'}},
        'debate':{'id':agreement_id,'kind':'nonstop','lines':agreement_rows,'bullets':cards},
        'queues':{'wrongVariants':[{'cause':'window-photo','script':[{'id':agreement_id+':window-photo','type':'say',
                    'actor':'akari','speaker':'아카리','text':'그 사진으로 방 안의 분을 확인하세요. 지금은 제가 열쇠를 받은 때를 적은 행이에요.',
                    'source':agreement_source}]}]}}
    tail = graph.add('rev:02:returned-key-agreement',type='task',taskId=agreement_id,trialDead=dead,seats=seats,
                     source=agreement_source,success=tail,next=tail)
    tail = graph.lines(returned,0,agreement_at,tail)
    debate_scene = scenes['02-T02a']
    debate_at = debate_scene.body.index('#### 논스톱 — 숫자만 복사해도 같은 장면이라면')
    debate_rule = next(i for i,row in enumerate(debate_scene.body) if row.startswith('4에 **02-I04e'))
    compare_id = 'T2-NS-REV03'
    compare_rows = []
    for offset in range(debate_at+1, debate_rule):
        match = STMT.match(debate_scene.body[offset])
        if not match:
            continue
        index, speaker, raw, role = match.groups()
        weak = index == '4'
        row = debate_statement(compare_id,index,speaker,raw,debate_scene.source(debate_scene.line+offset+1),
                               'weak' if weak else 'plain','v4:E205' if weak else '')
        if weak:
            word = row['weak']['word']
            row['vpoint'] = {'glyphIndex': row['weak']['start']+word.index('끝 모양')}
        compare_rows.append(row)
    assert len(compare_rows) == 14
    compare_source = debate_scene.source(debate_scene.line+debate_rule+1)
    compare_cards = [
        {'id': key, 'name': records[key][0], 'text': records[key][1]}
        for key in ('v4:E205','v4:E202','v4:E207')]
    tasks[compare_id] = {'taskId': compare_id, 'ready': True,
        'requiresEvidence': [card['id'] for card in compare_cards],
        'stage': {'id':compare_id,'kind':'nonstop','v4':True,'title':'숫자만 복사해도 같은 장면이라면',
                  'lines':compare_rows,'options':compare_cards,'authoredAmmo':[card['id'] for card in compare_cards],'filterOwnedEvidence':True,
                  'wrongCards':{'v4:E202':'interior','v4:E207':'front-watch'}},
        'debate': {'id':compare_id,'kind':'nonstop','lines':compare_rows,'bullets':compare_cards},
        'queues': {'wrongVariants':[
            {'cause': key,'script':[{'id':compare_id+':'+key,'type':'say','actor':SPEAKERS[actor],
                                    'speaker':actor,'text':line,'source':compare_source}]}
            for key,actor,line in (
                ('interior','리쿠','지금은 바깥에서 띠를 어디에 붙였는지 묻는 거야. 안쪽 문 두 개 보이는 그림 말고.'),
                ('front-watch','사츠키','나는 앞문을 봤어. 바깥 덮개를 지켰다는 말은 안 했고.'))]}}
    pushback = scenes['02-T02b']
    tail = graph.lines(pushback, 0, len(pushback.body), tail)
    tail = graph.lines(debate_scene, debate_rule+1, len(debate_scene.body), tail)
    tail = graph.add('rev:02:seal-photo-nonstop',type='task',taskId=compare_id,trialDead=dead,seats=seats,
                     source=compare_source,success=tail,next=tail)
    tail = graph.lines(debate_scene, 0, debate_at, tail)
    mine_source = panic_scene.source(panic_scene.line + seal_end + 2)
    mine_id = 'T2-MM-REV01'
    question, = re.findall(r'“([^”]+)”', panic_scene.body[seal_end + 2])
    tail = graph.lines(panic_scene, seal_end + 3, len(panic_scene.body), tail)
    label, description = records['v4:E209']
    tail = graph.add('rev:02:ring-physical-match', type='document', title=label, rows=[description],
                     image=MINE_ART+'theatre-open-ring.svg', source=mine_source, next=tail)
    ring_regions = (
        ('theatre-open-ring', '봉제실이 붙은 벌어진 고리', '', ''),
        ('theatre-apron-buckle', '공용 앞치마의 버클', '리쿠', '여기로 끈을 넣는 거야. 끊긴 실이 붙는 자리가 아니잖아.'),
        ('theatre-washer', '도구통의 둥근 와셔', '나나', '이건 둘레가 닫혀 있어요. 주머니 사진에서는 끝이 벌어져요.'),
        ('theatre-tag-clip', '투명 받침이 있는 표찰 클립', '하루카', '밑에 붙은 투명판부터 봐. 확대 사진엔 저 판이 없어.'),
    )
    assert {row[0] for row in ring_regions} == {obj['regionId'] for obj in ring_objects}
    tasks[mine_id] = {'taskId': mine_id, 'ready': True, 'requiresEvidence': ['v4:E208', 'v4:E209'],
                      'stage': {'id': mine_id, 'kind': 'mindmine', 'v4': True, 'title': '찢긴 쪽', 'question': question,
                                'image': MINE_ART+'theatre-ring-board.svg', 'answerRegionId': ring_regions[0][0],
                                'mineObjects': ring_objects,
                                'regions': [{'id': key, 'label': name, 'correct': not actor, 'wrongVariant': key}
                                            for key, name, actor, _ in ring_regions]},
                      'queues': {'wrongVariants': [{'cause': key, 'script': [
                          {'id': f'{mine_id}:{key}', 'type': 'say', 'actor': SPEAKERS[actor], 'speaker': actor,
                           'text': text, 'source': mine_source}]} for key, _, actor, text in ring_regions if actor]}}
    tail = graph.add('rev:02:ring-mine', type='task', taskId=mine_id, trialDead=dead, seats=seats,
                     source=mine_source, success=tail, next=tail)
    ring_checkpoint = graph.add('rev:02:ring-court-entry', type='stage', enterCourt=True, next=tail)
    tail = graph.lines(panic_scene, seal_rule + 1, seal_end, tail)

    e205 = 'v4:E205'
    pool = [e205, 'v4:E202', 'v4:E203']
    exhibits = [{'id': key, 'name': records[key][0], 'text': records[key][1]} for key in pool]
    seal_id = 'T2-NS-REV02'
    rows = []
    for offset in range(seal + 1, seal_rule):
        if match := STMT.match(panic_scene.body[offset]):
            index, speaker, raw, role = match.groups()
            assert (index == '4') == ('약점' in role)
            answer = e205 if index == '4' else ''
            rows.append(debate_statement(seal_id, index, speaker, raw, panic_scene.source(panic_scene.line + offset + 1),
                                         'weak' if answer else 'plain', answer))
    assert len(rows) == 16
    tasks[seal_id] = {'taskId': seal_id, 'ready': True, 'requiresEvidence': pool,
                      'stage': {'id': seal_id, 'v4': True, 'kind': 'nonstop', 'title': '누가 봉인 안쪽에 서 있었어',
                                'lines': rows, 'options': exhibits, 'authoredAmmo': pool, 'filterOwnedEvidence': True,
                                'wrongCards': {'v4:E202': 'front-doors'}},
                      'debate': {'id': seal_id, 'kind': 'nonstop', 'lines': rows, 'bullets': exhibits},
                      'queues': {'wrongVariants': [{'cause': 'front-doors', 'script': [
                          {'id': seal_id + ':wrong', 'type': 'say', 'actor': 'rei', 'speaker': '레이',
                           'text': '그 자료는 객석에서 앞쪽 문을 구분한 것입니다. 지금 묻는 건 바깥쪽 덮개입니다.',
                           'source': seal_source}]}]}}
    tail = graph.add('rev:02:seal-nonstop', type='task', taskId=seal_id, trialDead=dead, seats=seats,
                     source=seal_source, success=tail, next=tail)
    grille_id = 'T2-SP-REV01'
    grille_source = panic_scene.source(panic_scene.line + grille + 1)
    grille_regions = [('door', '준비실 앞문 손잡이', (.205, .457, .24, .497), '앞문 손잡이는 복도에 있어. 두 방 사이의 막힌 자리를 골라.'),
                      ('grille', '두 방 사이의 격자', (.406, .33, .481, .521), ''),
                      ('seal', '물류 덮개의 점검 띠', (.705, .31, .769, .519), '그 띠는 바깥의 물류 덮개를 확인해. 의상실과 사이에 놓인 것은 따로 있어.'),
                      ('window', '직원 창구 받침', (.79, .551, .887, .661), '그곳에서는 물건을 받을 수 있어. 두 방을 가르는 격자는 거기 없고.')]
    tasks[grille_id] = {'taskId': grille_id, 'ready': True, 'requiresEvidence': [e205],
                        'stage': {'id': grille_id, 'v4': True, 'kind': 'spot',
                                  'question': '의상실과 면을 공유하지만 사람이 넘어올 수 없는 지점은?',
                                  'image': MINE_ART + 'theatre-section.svg', 'answerRegionId': 'grille',
                                  'regions': [{'id': key, 'label': label, 'wrongVariant': key,
                                               'polygon': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]}
                                              for key, label, (x0, y0, x1, y1), _ in grille_regions]},
                        'queues': {'wrongVariants': [{'cause': key, 'script': [
                            {'id': grille_id + ':' + key, 'type': 'say', 'actor': 'mio', 'speaker': '미오',
                             'text': text, 'source': grille_source}]} for key, _, _, text in grille_regions if text]}}
    tail = graph.add('rev:02:grille-scope', type='say', actor='mio', speaker='미오',
                     text='격자는 두 방 사이에 있지만 고정되어 있었어. 바깥 물류 덮개가 열렸는지는 이제 따로 보자.',
                     source=grille_source, next=tail)
    tail = graph.add('rev:02:grille-position', type='task', taskId=grille_id, trialDead=dead, seats=seats,
                     source=grille_source, success=tail, next=tail)
    panic_id = 'T2-PN-REV01'
    lanes = [{'id': label, 'actor': SPEAKERS[name], 'speaker': name, 'lines': []}
             for label, name in (('왼쪽', '코토'), ('가운데', '소라'), ('오른쪽', '아카리'))]
    panic_rows = []
    panic_rule = next(i for i in range(panic_heading, grille) if panic_scene.body[i].startswith('정답 E205 → A3'))
    for offset in range(panic_heading + 1, panic_rule):
        cols = [cell.strip() for cell in panic_scene.body[offset].strip('|').split('|')]
        if len(cols) != 4 or not cols[0].isdigit():
            continue
        beat = int(cols[0])
        for index, (lane, raw) in enumerate(zip(lanes, cols[1:])):
            source = panic_scene.source(panic_scene.line + offset + 1)
            target = (beat, index) == (3, 0)
            row = debate_statement(panic_id, f'{index}:{beat}', lane['speaker'], raw, source,
                                   'weak' if target else 'plain', e205 if target else '')
            lane['lines'].append(row['id'])
            panic_rows.append(row)
            if '[큰 소리]' in raw:
                assert (beat, index) == (2, 1)
                noise = debate_statement(panic_id, 'noise', lane['speaker'], raw, source, 'noise')
                noise.update(noiseRole='loud', noiseDurability=2, hostStatement=row['id'])
                panic_rows.append(noise)
    assert [len(lane['lines']) for lane in lanes] == [4, 4, 4] and len(panic_rows) == 13
    tasks[panic_id] = {'taskId': panic_id, 'ready': True, 'requiresEvidence': pool,
                       'stage': {'id': panic_id, 'v4': True, 'kind': 'panic', 'title': '보증의 범위',
                                 'lines': panic_rows, 'options': exhibits, 'filterOwnedEvidence': True},
                       'debate': {'id': panic_id, 'kind': 'panic', 'lines': panic_rows, 'bullets': exhibits,
                                  'lanes': lanes, 'synchronizedBeats': True},
                       'queues': {}}
    tail = graph.lines(panic_scene, panic_rule + 1, grille, tail)
    tail = graph.add('rev:02:lock-panic', type='task', taskId=panic_id, trialDead=dead, seats=seats,
                     source=panic_scene.source(panic_scene.line + panic_heading + 1), success=tail, next=tail)
    tail = graph.lines(panic_scene, 0, panic_heading, tail)
    witness_picker = view.body.index('#### 인물 지목 A — 지금 다시 물을 사람')
    sleeve_picker = view.body.index('#### 증거 지목 A — 누구의 소매')
    perspective_rule = next(i for i in range(stop, sleeve_picker) if view.body[i].startswith('플레이어는 같은 바닥을'))
    costume_flag = next(i for i in range(witness_picker, len(view.body)) if view.body[i].startswith('02-F03 A를'))
    costume_join = next(i for i in range(costume_flag, len(view.body)) if view.body[i].startswith('미오가 만나지 않았다면'))
    tail = graph.lines(view, costume_join + 1, len(view.body), tail)
    tail = graph.lines(view, witness_picker + 2, costume_flag, tail)
    witness_id = 'T2-PE-REV01'
    sleeve_id = 'T2-BU-REV01'
    perspective_id = 'T2-QA-REV02'
    def selection_task(ident, kind, question, answer, selections, wrong, offset, next_node, requires):
        source = view.source(view.line + offset + 1)
        stage = {'id': ident, 'v4': True, 'kind': kind, 'question': question, 'answer': answer}
        stage['candidates' if kind == 'person' else 'options'] = selections
        tasks[ident] = {'taskId': ident, 'ready': True, 'requiresEvidence': requires, 'stage': stage,
                        'queues': {'wrongVariants': [{'optionIndex': index, 'script': [
                            {'id': f'{ident}:wrong:{index}', 'type': 'say', 'actor': SPEAKERS[speaker], 'speaker': speaker,
                             'text': line, 'source': source}]} for index, speaker, line in wrong]}}
        return graph.add('rev:02:' + ident, type='task', taskId=ident, trialDead=dead, seats=seats,
                         source=source, success=next_node, next=next_node)
    tail = selection_task(witness_id, 'person', '사진 속 대여를 인정했고 출입을 직접 설명할 수 있는 사람은?',
                          'riku', ['rin', 'riku', 'yuu'],
                          [(0, '린', '내가 준 건 맞아. 그다음 어디서 입었는지는 계속 본 게 아니고.'),
                           (2, '유우', '난 객석에서 천을 봤어. 그 옷 받고 문에서 나온 사람이 나라는 말은 한 적 없어.')],
                          witness_picker, tail, ['v4:E204'])
    tail = graph.lines(view, sleeve_picker + 1, witness_picker, tail)
    sleeve_cards = [{'id': key, 'name': records[key][0], 'text': records[key][1]} for key in ('v4:E202', 'v4:E204', 'v4:E203')]
    tail = selection_task(sleeve_id, 'bullet', '그 무늬가 린 한 사람의 것이라는 추정을 무너뜨리는 자료는?',
                          'v4:E204', sleeve_cards, [(0, '미오', '문턱 위치를 찍었어. 체크무늬 겉옷을 누가 받아 입었는지 다시 봐.'),
                          (2, '아카리', '열쇠를 누가 보관했는지 나온 기록이에요. 겉옷을 받은 분은 따로 확인하세요.')],
                          sleeve_picker, tail, ['v4:E204'])
    sleeve_checkpoint = graph.add('rev:02:late-court-entry', type='stage', enterCourt=True, next=tail)
    tail = graph.lines(view, perspective_rule + 1, sleeve_picker, tail)
    wrong_position, = re.findall(r'“([^”]+)”', view.body[perspective_rule])
    tail = selection_task(perspective_id, 'choice', '유우가 공연이 끝나기 전에 실제로 섰던 곳은?',
                          1, ['계단을 한 단 내려간 자리', '객석의 노란 줄'],
                          [(0, '유우', wrong_position)], perspective_rule, tail, ['v4:E202'])
    tail = graph.lines(view, stop + 1, perspective_rule, tail)
    tail = graph.lines(view, rule + 1, stop, tail)
    tail = graph.add('rev:02:nonstop', type='task', taskId=ns_id, trialDead=dead, seats=seats, success=tail, next=tail)
    tail = graph.lines(view, 0, round_at, tail)
    tail = graph.lines(finding, question_at + 3, len(finding.body), tail)
    tail = graph.add('rev:02:discovery-choice', type='task', taskId=choice_id, trialDead=dead, seats=seats,
                     success=tail, next=tail, source=finding.source(finding.line + question_at + 1))
    tail = graph.lines(finding, 0, question_at, tail)
    court = graph.add('rev:02:court-entry', type='stage', enterCourt=True, next=tail)
    for ident in ('02-I09', '02-I08'):
        pretrial = scenes[ident]
        court = graph.lines(pretrial, 0, len(pretrial.body), court)
        court = graph.add(f'rev:{ident}:entry', type='stage', next=court,
                          source=pretrial.source(pretrial.line))

    sight = scenes['02-I02']
    first_choice = next(i for i, row in enumerate(sight.body) if row.startswith('선택 **함께 시야를'))
    riku_starts = next(i for i, row in enumerate(sight.body) if row.startswith('**리쿠**'))
    discovery = scenes['02-I01']
    examine_at = next(i for i,row in enumerate(discovery.body) if row.startswith('현장 조사.'))
    window = scenes['02-I05']
    window_observation = next(i for i,row in enumerate(window.body) if 'E206 획득.' in row)
    ledger = scenes['02-I07']
    ledger_end = next(i for i,row in enumerate(ledger.body) if row.startswith('E210 획득.'))
    route = scenes['02-I07k']
    placements = (
        ('02-I01', 'v4:E201', 'theatre_preparation', [0, 1.0, -.6], 0, examine_at),
        ('02-I02', 'v4:E202', 'performance_stage', [0, 1.2, 3.1], 0, first_choice),
        ('02-I03', 'v4:E203', 'theatre_preparation', [1.4, 1.2, .8], 0, len(scenes['02-I03'].body)),
        ('02-I02', 'v4:E204', 'theatre_preparation', [-1.4, 1.2, .8], riku_starts + 1, len(sight.body)),
        ('02-I04', e205, 'theatre_preparation', [0.2, 1.38, 2.5], 0, len(scenes['02-I04'].body)),
        ('02-I05', 'v4:E206', 'theatre_preparation', [1.1, 1.16, -2.1], 0, window_observation),
        ('02-I05', 'v4:E207', 'performance_stage', [-1.2, 1.16, 1.4], window_observation + 1, len(window.body)),
        ('02-I01', 'v4:E208', 'theatre_preparation', [-.85, .3, -.5], examine_at, len(discovery.body)),
        ('02-I06', 'v4:E209', 'theatre_preparation', [-1.45, .85, -1.6], 0, len(scenes['02-I06'].body)),
        ('02-I07', 'v4:E210', 'theatre_preparation', [-.85, 1.16, 2.08], 0, ledger_end),
        ('02-I07k', 'v4:E211', 'performance_stage', [1.4, 1.1, 1.9], 0, len(route.body)),
    )
    spot_prerequisites = {
        'v4:E203': ['v4:E202', 'v4:E204'], 'v4:E207': ['v4:E203', 'v4:E206'],
        'v4:E208': ['v4:E201'], 'v4:E209': ['v4:E206', 'v4:E208'], 'v4:E211': ['v4:E210'],
    }
    exhibit_art = {'v4:E205':'theatre-seal.webp','v4:E206':'theatre-window.webp','v4:E208':'theatre-floor.webp'}
    spots = []
    for source_id, key, space, pos, start, stop in placements:
        scene = scenes[source_id]
        label, description = records[key]
        done = graph.add('rev:02:return:' + key, type='return')
        file = exhibit_art.get(key)
        image = {'image':REVISED_CASE_ART+file} if file and (ROOT/'art/revision_case'/file).is_file() else {}
        acquire = graph.add('rev:02:record:' + key, type='evidence', evidenceId=key, name=label, text=description,
                            source=scene.source(scene.line + start + 1), next=done, **image)
        supplemental={
            'v4:E201':['02-I07c'],'v4:E203':['02-I03a','02-I03b','02-I04d'],
            'v4:E205':['02-I04a','02-I04c'],'v4:E206':['02-I05a','02-I07b','02-I07f','02-I07g'],
            'v4:E207':['02-I05b','02-I07d','02-I07m','02-I07n'],'v4:E208':['02-I07e'],'v4:E209':['02-I06a'],
            'v4:E210':['02-I07j','02-I07h','02-I07i'],'v4:E211':['02-I07a','02-I04b','02-I07l'],
        }
        acquire=supplemental_inspection(graph,scenes,supplemental.get(key,()),acquire)
        first = acquire
        if key == 'v4:E205':
            compare = scenes['02-I04e']
            comparison = next(i for i,row in enumerate(compare.body) if row.startswith('**글자만 포갠다'))
            correct = graph.lines(compare, comparison+1, len(compare.body), acquire)
            menu_id = 'rev:02:seal-overlay'
            ref = compare.source(compare.line+comparison+1)
            left = graph.add(menu_id+':number',type='say',actor='haruka',speaker='하루카',
                             text='글자는 맞아도 각도가 다르잖아. 접힌 끝이 같은지는 지금 안 보여.',source=ref,next=menu_id)
            right = graph.add(menu_id+':guess',type='say',actor='rei',speaker='레이',
                              text='아직 그 앞에 누가 서 있었는지 관찰한 기록이 없습니다.',source=ref,next=menu_id)
            menu = graph.add(menu_id,type='menu',q='사진과 지금의 점검 띠를 어떻게 맞출까?',source=ref,
                             options=[{'id':i,'label':label,'to':target} for i,label,target in (
                                 ('A','글자만 포갠다',left),('B','접힌 끝과 고정틀을 포갠다',correct),
                                 ('C','처음부터 바깥에서 당긴 것으로 그린다',right))])
            first = graph.lines(compare,0,comparison,menu)
        opening = graph.lines(scene, start, stop, first)
        if key == 'v4:E204':
            paths = []
            response_at = next(i for i in range(riku_starts + 1, len(sight.body))
                               if sight.body[i].startswith('리쿠를 먼저 만난 경로에서'))
            responses = [(i, re.findall(r'“([^”]+)”', sight.body[i])) for i in (response_at, first_choice)]
            for index, (i, quotes) in enumerate(responses):
                response = quotes[-1]
                paths.append(graph.add(f'rev:02:costume-reply:{index}', type='say', speaker='미오', actor='mio',
                                       text=response, source=scene.source(scene.line + i + 1), next=opening))
            assert len(paths) == 2
            opening = graph.add('rev:02:costume-order', type='branch', default=paths[0], cases=[
                {'flag': 'spot:v4:E202:complete', 'equals': True, 'to': paths[1]}])
            opening = graph.lines(scene, riku_starts, riku_starts + 1, opening)
        spot = {'id': key, 'neutralLabel': label, 'label': label, 'space_id': space, 'world_pos': pos, 'entry': opening}
        if key in spot_prerequisites:
            spot['requiresCards'] = spot_prerequisites[key]
        spots.append(spot)
    hub = graph.add('rev:02:investigate', type='investigate', space_id='theatre_preparation', spots=spots,
                    requiredSpotIds=list(records), requiredCards=list(records), next=court)
    discovery = scenes['02-D08']
    tail = graph.add('rev:02:body-announcement',type='stage',next=hub,
                     source=discovery.source(discovery.line+len(discovery.body)),
                     presentation={'actions':['body_announcement']})
    tail = graph.lines(discovery,0,len(discovery.body),tail)
    tail = graph.add('rev:02:discovery',type='stage',next=tail,source=discovery.source(discovery.line),
                     scene={'space':'theatre_preparation','perspective':'current-observation'},
                     presentation={'music':{'operation':'play','cue':'bgm_tense'}})
    daily_ids=[ident for ident in scenes if ident.startswith('02-D') and ident!='02-D08']
    # The supplementary supper belongs after the afternoon meeting it recalls.
    for ident in ('02-D04l','02-D04t'):
        daily_ids.remove(ident)
    evening=daily_ids.index('02-D04i')+1
    daily_ids[evening:evening]=['02-D04l','02-D04t']
    tail=life_route(graph,scenes,daily_ids[daily_ids.index('02-D03')+1:],tail)
    free = scenes['02-F01']
    completed = graph.finish_free_time(free,tail)
    joint = next(i for i,row in enumerate(free.body) if row.startswith('- **함께 연다.**'))
    check = next(i for i,row in enumerate(free.body) if row.startswith('- **확인만 맡긴다.**'))
    look_at = next(i for i,row in enumerate(free.body) if row.startswith('- **봐도 돼?**'))
    skip_at = next(i for i,row in enumerate(free.body) if row.startswith('- **다음에 보여 줘.**'))
    quote, = re.findall(r'“([^”]+)”',free.body[skip_at])
    skip = graph.add('rev:02-F01:leave-ring',type='say',actor='rin',speaker='린',text=quote,
                     source=free.source(free.line+skip_at+1),next=completed)
    memory = graph.lines(free,skip_at+1,len(free.body),completed)
    ask = graph.add('rev:02-F01:ring-choice',type='menu',q='린이 쥔 열쇠고리를 어떻게 할까?',
                    options=[{'id':'look','label':'봐도 돼?','set':{'02-F01:ring':True},'to':memory},
                             {'id':'later','label':'다음에 보여 줘','to':skip}])
    joint_path = graph.lines(free,joint+1,check,ask)
    check_path = graph.lines(free,check+1,look_at,ask)
    ask = graph.add('rev:02-F01:locker-choice',type='menu',q='린에게 어디까지 맡길까?',
                    options=[{'id':'joint','label':'함께 연다','to':joint_path},
                             {'id':'check','label':'확인만 맡긴다','to':check_path}])
    ask = graph.lines(free,0,joint,ask)
    free_entry = graph.add('rev:02-F01:entry',type='stage',next=ask,source=free.source(free.line),
                           scene={'space':'maintenance_workshop','perspective':'current-observation'},
                           presentation={'music':{'operation':'play','cue':'bgm_freetime'}})
    tail = graph.add('rev:02:free-time',type='menu',q='공연 준비까지 남은 시간에 어디로 갈까?',
                     options=[{'id':'rin','label':'공방에서 린을 만난다','to':free_entry},
                              {'id':'skip','label':'객석으로 돌아간다','to':tail}])
    entry=life_route(graph,scenes,daily_ids[:daily_ids.index('02-D03')+1],tail)
    prior_meeting=graph.add('rev:02:life-with-prior-meeting',type='stage',set={'01-F02':'A'},next=entry)
    return ({'schemaVersion': 1, 'contentVersion': 'v4', 'campaignRevision': 'rewrite-v5', 'chapter': '2',
             'entry': entry, 'trialRoster': {'dead': dead, 'seats': seats}, 'nodes': graph.nodes,
             'qaCheckpoints': {'life-with-prior-meeting':{'entry':prior_meeting,'evidence':[]},**{name: {'entry': entry, 'evidence': [
                 {'id': key, 'name': name, 'text': description} for key, (name, description) in records.items()]}
                 for name, entry in [('sleeve',sleeve_checkpoint),('theatre-ring',ring_checkpoint),*checkpoints]}}}, tasks)


def chapter_three_daily_conditions(graph,scenes,tail):
    daily_ids=[ident for ident in scenes if ident.startswith('03-D')]
    tail=life_route(graph,scenes,daily_ids[daily_ids.index('03-D01t')+1:daily_ids.index('03-D02')],tail)
    scene = scenes['03-D01t']
    choices = [(i,BULLET.match(row)[1]) for i,row in enumerate(scene.body) if BULLET.match(row)]
    assert len(choices)==3
    common = next(i for i in range(choices[-1][0],len(scene.body)) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,common,len(scene.body),tail)
    menu = 'rev:03-D01t:choice'
    responses = (
        [('소라','번호를 지금 주면 안 돼? 그다음에 내가 어디까지 할 건지 따로 말하면 되잖아.'),
         ('리쿠','확인 끝나면 알려 줄게. 아직 그 번호를 주겠다고 한 건 아니야.'),
         ('미오','내가 조건을 들었다고 해서 끝까지 하겠다고 승낙한 건 아니야.')],
        [('소라','조금만 더 볼게. 내가 멈추면 같이 멈춰 줘.'),
         ('미오','아이가 화면에서 멀어지기 전에 남자가 돌아본 데까지만 봤어. 그다음 기록은 아직 없어.')],
        [('미오','오늘은 밖에서 한 번 쉬자.'),('소라','다음에 다시 찾으러 올 수도 있어. 지금은 내가 끈 거야.')],
    )
    options = []
    for i,((at,label),lines) in enumerate(zip(choices,responses)):
        target = tail
        for index,(actor,text) in reversed(list(enumerate(lines))):
            target = graph.add(f'{menu}:{i}:{index}',type='say',actor=SPEAKERS[actor],speaker=actor,text=text,
                source=scene.source(scene.line+at+1),next=target)
        options.append({'id':chr(65+i),'label':label,'to':target,'set':{scene.id:chr(65+i)}})
    tail = graph.add(menu,type='menu',q='소라가 먼저 하려는 말',options=options,
                     source=scene.source(scene.line+choices[0][0]+1))
    # The unseen later footage is withheld; no cause of death is inferred here.
    first_clip = next(i for i,row in enumerate(scene.body) if row.startswith('(첫 조각.'))
    tail = graph.lines(scene,first_clip+1,choices[0][0],tail)
    tail = graph.add('rev:03:archive-first-fragment',type='document',title='소라가 멈춘 첫 조각',
        rows=['구조복을 입은 남자가 문에서 뒤를 돌아본다. 화면 뒤쪽에 어린 사람이 있다.',
              '소라가 정지를 눌렀다. 남자의 다음 행방은 이 조각에서 보이지 않는다.'],
        source=scene.source(scene.line+first_clip+1),next=tail)
    tail = graph.lines(scene,0,first_clip,tail)
    tail = graph.add('rev:03:archive-before-test',type='stage',scene={'space':'record_room','perspective':'current-observation'},
        source=scene.source(scene.line),next=tail)

    tail=life_route(graph,scenes,daily_ids[daily_ids.index('03-D0A')+1:daily_ids.index('03-D01t')],tail)

    scene = scenes['03-D0A']
    choices = [(i,BULLET.match(row)[1]) for i,row in enumerate(scene.body) if BULLET.match(row)]
    assert len(choices)==3
    after = next(i for i in range(choices[-1][0],len(scene.body)) if SAY.match(scene.body[i]))
    # Only the route with an actual card flip can recall that completed action.
    recalled = next(i for i,row in enumerate(scene.body) if row.startswith('**리쿠**　그러니까 내가 너무 잘'))
    tail = graph.lines(scene,recalled+4,len(scene.body),tail)
    flip_tail = graph.lines(scene,recalled,recalled+4,tail)
    tail = graph.add('rev:03:hypnosis-action-memory',type='branch',
        cases=[{'flag':scene.id,'equals':'A','to':flip_tail}],default=tail)
    tail = graph.lines(scene,after,recalled,tail)
    menu = 'rev:03-D0A:choice'
    responses = (
        [('리쿠','카드가 바닥을 보게 하면 돼. 내가 하기로 한 건 여기까지야.'),
         ('켄','리쿠. 흰 카드를 뒤집어 봐.'),
         ('미오','켄이 눈을 맞추고 이름을 부른 뒤 리쿠가 카드를 뒤집었다. 리쿠가 먼저 손을 뗐다.'),
         ('켄','그래. 여기까지. 네가 정말 하기 싫었으면 어땠을지는 이걸로 안 보여 줬어.'),
         ('리쿠','그냥 하는 게 더 좋겠다는 느낌은 있었어. 내가 일부러 했는지도 내 말로 남겨.')],
        [('리쿠','카드는 옆에 둘게. 오늘은 안 할래.'),('켄','아직 이름 안 불렀어. 여기서 멈출게.'),
         ('하루카','카드를 옮긴 건 리쿠야. 마법을 쓰기 시작했다는 장면은 없어. 실패한 걸로 쓰지 않을게.')],
        [('리쿠','내 이름 부르고 세 문장 넘게 말해 봐.'),('켄','세 문장 이내야. 그 이상 채우려고 하지는 않을게.'),
         ('리쿠','내가 거절할 수 있는 일을 더 만들지는 않을래.'),
         ('미오','목소리만 들었다고 카드가 움직였다는 관찰을 붙이지 않는다.')],
    )
    options = []
    for i,((at,label),lines) in enumerate(zip(choices,responses)):
        target = tail
        for index,(actor,text) in reversed(list(enumerate(lines))):
            target = graph.add(f'{menu}:{i}:{index}',type='say',actor=SPEAKERS[actor],speaker=actor,text=text,
                mono=actor=='미오',source=scene.source(scene.line+at+1),next=target)
        options.append({'id':chr(65+i),'label':label,'to':target,'set':{scene.id:chr(65+i)}})
    tail = graph.add(menu,type='menu',q='하기로 한 일을 먼저 고른다',options=options,
                     source=scene.source(scene.line+choices[0][0]+1))
    tail = graph.lines(scene,0,choices[0][0],tail)
    return graph.add('rev:03:hypnosis-conditions',type='stage',scene={'space':'mirror_maze','perspective':'current-observation'},
                     source=scene.source(scene.line),next=tail)


def chapter_three_waiting(graph, scenes, tail):
    scene = scenes['03-I01c']
    choices = [(i,BULLET.match(row)[1]) for i,row in enumerate(scene.body) if BULLET.match(row)]
    common = next(i for i,row in enumerate(scene.body) if row.startswith('(세 경로의 끝에서'))
    tail = graph.lines(scene,common+1,len(scene.body),tail)
    tail = graph.menu(scene,'누구에게 먼저 답할 차례를 줄까?',[
        (label,start+1,choices[index+1][0] if index+1<len(choices) else common,'')
        for index,(start,label) in enumerate(choices)],tail)
    tail = graph.lines(scene,0,choices[0][0],tail)
    scene = scenes['03-I01b']
    starts = [i for i,row in enumerate(scene.body) if row.startswith('#### ')]
    common = scene.body.index('### 공통 진행')
    labels = [scene.body[i].removeprefix('#### ') for i in starts]
    assert len(starts)==3
    tail = graph.lines(scene,common+1,len(scene.body),tail)
    tail = graph.menu(scene,'문턱에서 누구에게 먼저 말을 걸까?',[
        (label,start+1,starts[index+1] if index+1<len(starts) else common,'')
        for index,(start,label) in enumerate(zip(starts,labels))],tail)
    tail = graph.lines(scene,0,starts[0],tail)
    scene = scenes['03-I01a']
    starts = [i for i,row in enumerate(scene.body) if row.startswith('#### ')]
    common = scene.body.index('### 합류')
    labels = [scene.body[i].removeprefix('#### ')[3:] for i in starts]
    assert len(starts)==2
    tail = graph.lines(scene,common+1,len(scene.body),tail)
    tail = graph.menu(scene,'먼저 어느 자리를 확보할까?',[
        (label,start+1,starts[index+1] if index+1<len(starts) else common,'')
        for index,(start,label) in enumerate(zip(starts,labels))],tail)
    return graph.lines(scene,0,starts[0],tail)


def chapter_three_comic_and_vote(graph,scenes,tasks,records,dead,seats,tail):
    source_scene = scenes['03-T03']
    vote_at = source_scene.body.index('#### 범인 투표 — 초상과 이름이 어긋날 때')
    comic_at = source_scene.body.index('#### 클라이맥스 추리 — 두 번째 확인')
    def ref(at):
        return source_scene.source(source_scene.line+at+1)
    complete = graph.add('rev:03:complete',type='end',chapterComplete=True,nextChapter='4')
    aftermath = scenes['03-R01']
    theatre = aftermath.body.index('### 무대를 접으러 온 사람')
    after = graph.lines(aftermath,theatre+1,len(aftermath.body),complete)
    after = graph.add('rev:03:theatre-afterwards',type='stage',
        scene={'space':'performance_stage','perspective':'current-observation'},
        source=aftermath.source(aftermath.line+theatre+1),next=after)
    memory = next(i for i,row in enumerate(aftermath.body) if row.startswith('03-F01에서 먼저 물어보기로'))
    asked = graph.add('rev:03:meal-memory:ask',type='say',actor='yuu',speaker='유우',
        text='같이 먹을래? 나는 여기 앉아서 기다릴게.',source=aftermath.source(aftermath.line+memory+1),next=after)
    chair = graph.add('rev:03:meal-memory:chair',type='say',actor='mio',speaker='미오',mono=True,
        text='유우가 대답을 요구하지 않고 옆 의자만 빼 두었다.',source=aftermath.source(aftermath.line+memory+1),next=after)
    after = graph.add('rev:03:meal-memory',type='branch',
        cases=[{'flag':'03-F01','equals':'A','to':asked},{'flag':'03-F01','equals':'B','to':chair}],default=after)
    after = graph.lines(aftermath,0,memory,after)
    after = graph.add('rev:03:meal-afterwards',type='stage',scene={'space':'dining_room'},
        presentation={'music':{'operation':'play','cue':'bgm_night'}},source=aftermath.source(aftermath.line),next=after)
    elevator = scenes['03-R00a']
    after = graph.lines(elevator,0,len(elevator.body),after)
    after = graph.add('rev:03:leave-court',type='stage',scene={'space':'trial_elevator','leaveCourt':True},
        source=elevator.source(elevator.line),next=after)
    after = chapter_verdict(graph,scenes['03-R00'],after,3)
    after = graph.lines(source_scene,vote_at+1,len(source_scene.body),after)
    ident = 'T3-VOTE-REV01'
    stage = {'id':ident,'kind':'vote','v4':True,'title':'초상과 이름이 어긋날 때',
        'question':'몸의 외형과 구별해서, 이 두 공격의 검정으로 확인한 이름은?',
        'answer':'sora','candidates':seats,'selectionRole':'final-culprit-vote','finalVote':True,
        'candidateOverrides':{'sora':{'physicalActor':'ken','label':'소라'}},
        'presentation':{'music':{'operation':'play','cue':'bgm_trial_main_3'}}}
    wrongs = []
    for who,speaker,text in (
        ('ken','미오','지금 저 몸에서 말을 이어 간 사람과 돌아오지 못한 원래 주인을 나누었어. 몸의 얼굴이 표의 이름을 대신하지는 않아.'),
        ('riku','쇼','리쿠 씨는 첫 현장에서 사망을 확인했습니다. 마지막 발화자와 첫 피해자를 같은 이름으로 고르지 마십시오.'),
    ):
        wrongs.append({'optionIndex':seats.index(who),'script':[{'id':ident+':wrong:'+who,
            **speech(f'**{speaker}**　{text}',source_scene.line+vote_at+1,source_scene)}]})
    tasks[ident] = {'taskId':ident,'ready':True,
        'requiresEvidence':['v4:V5-3:continuity','v4:V5-3:new-sentence','v4:V5-3:condition'],
        'stage':stage,'queues':{'wrongVariants':wrongs,'wrong':[
            {'id':ident+':wrong','type':'say','actor':'mio','speaker':'미오',
             'text':'지금 고르는 이름은 두 공격의 연결과 공개 전에 한 대답으로 확인했어. 어느 몸이었는지와 누가 한 말인지를 다시 보자.',
             'source':ref(vote_at)}]}}
    vote = graph.add('rev:03:final-vote',type='task',taskId=ident,trialDead=dead,seats=seats,
        source=ref(vote_at),next=after,success=after)
    graph.add('rev:03:vote-court-entry',type='stage',enterCourt=True,next=vote)
    comic = chapter_three_comic_stage()
    if comic is None:
        return tail
    assert all((ROOT/f'art/revision_comic/chapter3/verdict-{i:02}.webp').is_file() for i in range(1,5)),\
        'Chapter 3 needs reviewed verdict shots before enabling its normal comic route'
    graph.nodes.pop(tail)
    after_book = graph.lines(source_scene,comic_at+1,vote_at,vote)
    ident = comic['id']
    tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':tasks['T3-VOTE-REV01']['requiresEvidence'],
                   'stage':comic,'queues':{}}
    entry = graph.add('rev:03:climax-comic',type='task',taskId=ident,trialDead=dead,seats=seats,
                      source=ref(comic_at),next=after_book,success=after_book)
    graph.add('rev:03:comic-court-entry',type='stage',enterCourt=True,next=entry)
    return entry


def chapter_three_final_hearing(graph,scenes,tasks,records,dead,seats,tail):
    scene = scenes['03-T03']
    def ref(at):
        return scene.source(scene.line+at+1)

    def say(key,actor,text,target,at):
        if actor=='소라':
            actor='소라(켄의 몸)'
        return graph.add('rev:03:'+key,**speech(f'**{actor}**　{text}',scene.line+at+1,scene),next=target)

    def task(ident,stage,target,at,requires,wrongs=()):
        tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':requires,
            'stage':{'id':ident,'v4':True,**stage},'queues':{'wrongVariants':[
                {'optionIndex':i,'script':[{'id':ident+':'+str(i),**speech(f'**{actor}**　{text}',scene.line+at+1,scene)}]}
                for i,actor,text in wrongs]}}
        return graph.add('rev:03:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                         source=ref(at),next=target,success=target)

    comic = scene.body.index('#### 클라이맥스 추리 — 두 번째 확인')
    rescue = scene.body.index('#### 구해 달라는 사람이 아직 있다면')
    rescue_after = next(i for i in range(rescue,len(scene.body)) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,rescue_after,comic,tail)
    menu = 'rev:03:address-after-return'
    answers = (
        ('켄에게 말을 건다',[('미오','켄.'),('소라','내가 대답하면 또 틀린 걸로 써?'),('미오','지금 대답한 사람이 누구라고 했는지는 알아.')]),
        ('소라에게 말을 건다',[('미오','소라.'),('소라','그럼 나 나가도 돼?'),('사츠키','얼굴 보고 부르지 말자고 했지, 이제 네가 걸어가도 된다고 한 거 아니야.')]),
        ('복귀 조건을 읽는다',[('쇼','정상 종료에서는 두 몸이 살아 있었습니다. 그때 본 눈과 대답을 지금의 상태와 나누어 보십시오.')]),
    )
    options = []
    for i,(label,replies) in enumerate(answers):
        target = tail
        for j,(actor,text) in reversed(list(enumerate(replies))):
            target = say(f'address-after-return:{i}:{j}',actor,text,target,rescue)
        options.append({'id':chr(65+i),'label':label,'to':target,'set':{'03-T03:address':chr(65+i)}})
    tail = graph.add(menu,type='menu',q='먼저 누구에게 말할까?',options=options,source=ref(rescue))
    anagram = scene.body.index('#### 섬광 애너그램 — 멈춘 시간이 돌아오려면')
    anagram_rule = next(i for i,row in enumerate(scene.body) if row.startswith('정답은 **복귀확인**'))
    tail = graph.lines(scene,anagram_rule+1,rescue,tail)
    ident = 'T3-AN-REV02'
    tail = task(ident,{'kind':'anagram','chapter':3,'title':'멈춘 시간이 돌아오려면',
        'question':'시연에서 각자가 자기 몸으로 돌아왔는지 무엇으로 확인했지?',
        'answer':'복귀확인','distractors':['기','시','간','점']},tail,anagram_rule,
        ['v4:V5-3:condition','v4:V5-3:clock-bench'])
    tail = graph.lines(scene,anagram+1,anagram_rule,tail)
    old_vote = scene.body.index('#### 그때부터 전부 거짓말이었나')
    old_vote_after = next(i for i in range(old_vote,len(scene.body)) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,old_vote_after,anagram,tail)
    alternatives = [(i,BULLET.match(row)[1],BULLET.match(row)[2]) for i,row in enumerate(scene.body[old_vote:old_vote_after],old_vote)
                    if BULLET.match(row)]
    assert len(alternatives)==3
    options = []
    for i,(at,label,raw) in enumerate(alternatives):
        replies = re.findall(r'(미오|소라|사츠키) “([^”]+)”',raw)
        assert len(replies)>=3
        target = tail
        for j,(actor,text) in reversed(list(enumerate(replies))):
            target = say(f'earlier-vote-question:{i}:{j}',actor,text,target,at)
        options.append({'id':chr(65+i),'label':label,'to':target,'set':{'03-T03:earlier-vote':chr(65+i)}})
    tail = graph.add('rev:03:earlier-vote-question',type='menu',q='지금 직접 묻고 싶은 말',options=options,source=ref(old_vote))
    person = scene.body.index('#### 인물 지목 — 돌아오지 못한 사람')
    person_after = next(i for i in range(person,len(scene.body)) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,person_after,old_vote,tail)
    tail = task('T3-PE-REV02',{'kind':'person','question':'두 번째 육체 사망 뒤, 사용되던 몸에서 돌아오지 못한 의식은?',
        'candidates':['ken','riku','sora','nana'],'answer':'ken','deadCandidatesSelectable':True},tail,person,
        ['v4:V5-3:condition','v4:V5-3:second-status'],[
            (1,'쇼','리쿠 씨가 숨을 쉬지 않는 것은 첫 현장에서 확인했습니다. 지금은 두 번째 사망 뒤에도 움직이던 몸을 보십시오.'),
            (2,'미오','지금 그 말을 하고 있는 사람과 죽은 본체를 같은 카드에 넣으려 했어. 그 몸의 원래 주인이 누구였지?'),
            (3,'나나','저는 벤치 옆에 있었어요. 저 몸이 처음에 누구 이름으로 대답했는지 다시 볼게요.')])
    down = scene.body.index('### 내려놓을 수 있던 때')
    tail = graph.lines(scene,down+1,person,tail)
    armament = scene.body.index('#### 이론 무장 — 그 이름이 남으면')
    between1 = scene.body.index('### 두 파 사이 — 네가 부른 이름')
    between2 = scene.body.index('### 두 번째 파가 끝난 뒤 — 다시 돌아온다고 하면')
    final = next(i for i,row in enumerate(scene.body) if row.startswith('마지막 네 조각은 **'))
    groups = []
    for prefix in ('1파 소라는','2파는','리듬은 세 단계로 진행한다.'):
        at = next(i for i,row in enumerate(scene.body[armament:between1],armament) if row.startswith(prefix))
        claims = re.findall(r'“([^”]+)”',scene.body[at])
        assert len(claims)==3
        groups.append((at,claims))
    ident = 'T3-AA-REV01'
    waves = [{'id':ident+':wave:'+str(phase),'pairs':[{'claim':{
        'id':f'{ident}:{phase}:{i}','type':'say','actor':'ken','speaker':'소라(켄의 몸)','text':text,'source':ref(at)}}
        for i,text in enumerate(claims)]} for phase,(at,claims) in enumerate(groups)]
    def feedback(start,end):
        return [{'id':f'{ident}:feedback:{i}',**event} for i,row in enumerate(scene.body[start:end],start)
                if (event:=speech(row,scene.line+i+1,scene))]
    fragments, = re.findall(r'\*\*([^*]+)\*\*',scene.body[final])
    fragments = [part.strip() for part in fragments.split('/')]
    assert len(fragments)==4
    return task(ident,{'kind':'armament','chapter':3,'title':'그 이름이 남으면','opponent':'ken',
        'opponentDisplay':'소라(켄의 몸)','lines':[text for _,group in groups for text in group],
        'waves':waves,'phaseTranscripts':True,'phaseFeedback':[feedback(between1+1,between2),feedback(between2+1,final)],
        'question':'몸의 모습과 실제로 남은 상태를 무엇으로 구별했지?',
        'finalSubject':'확인한 네 근거는','final':fragments},tail,armament,
        ['v4:V5-3:new-sentence','v4:V5-3:continuity','v4:V5-3:condition','v4:V5-3:second-status'])


def chapter_three_motives(graph,scenes,tail):
    scene = scenes['03-T03']
    first = scene.body.index('### 처음부터 알고 있던 일')
    first_choice = next(i for i,row in enumerate(scene.body) if row.startswith('플레이어는 세 가지를 나눈다.'))
    first_after = next(i for i in range(first_choice,len(scene.body)) if SAY.match(scene.body[i]))
    archive = scene.body.index('### 먼저 찾았던 화면의 끝')
    trade = scene.body.index('#### 거래가 없었을 때까지 고르려 한다면')
    trade_after = next(i for i in range(trade,len(scene.body)) if SAY.match(scene.body[i]))
    separate = scene.body.index('### 사정을 고른다고 같은 사건이 되는가')
    separate_choice = next(i for i in range(separate,len(scene.body)) if scene.body[i].startswith('플레이어는 **'))
    separate_after = next(i for i in range(separate_choice,len(scene.body)) if SAY.match(scene.body[i]))
    armament = scene.body.index('#### 이론 무장 — 그 이름이 남으면')
    tail = graph.lines(scene,separate_after,armament,tail)

    def event(key,actor,text,target,at):
        row = speech(f'**{actor}**　{text}',scene.line+at+1,scene)
        return graph.add('rev:03:'+key,**row,next=target)

    # Facts and the person's later explanation remain separate choices.
    menu = 'rev:03:record-or-admission'
    actual = event('record-admission-separate','미오',
        '현장에 간 이유와 지금 스스로 한 말은 다른 줄에 둘게. 영상에는 그 남자의 마지막이 없어.',tail,separate_choice)
    unsupported = event('record-last-frame','하루카',
        '그 뒤 장면은 없어. 저 화면 끝을 늘려서 아버지가 어떻게 됐는지 만들 수는 없어.',menu,separate_choice)
    tail = graph.add(menu,type='menu',q='자료와 지금의 진술을 어떻게 나눌까?',source=scene.source(scene.line+separate_choice+1),
        options=[{'id':'visit','label':'기록을 얻으려고 장소로 간 사실과 이후의 인정을 나눠 둔다','to':actual},
                 {'id':'final-event','label':'아버지의 사망 경위가 영상에 나온다고 적는다','to':unsupported}])
    tail = graph.lines(scene,trade_after,separate,tail)
    menu = 'rev:03:trade-hypotheses'
    counterfactual = event('trade-counterfactual','소라(켄의 몸)',
        '그랬으면 그때 먼저 보러 갔을 수도 있지. 내가 지금 여기서 그랬다고 말할 수는 없고.',menu,trade)
    consent = event('trade-consent','미오',
        '내가 조건을 들었다고 해서 죽이기로 합의한 건 아니야. 현장에 간 때와 실제로 해친 때를 나눠 보자.',menu,trade)
    options = [
        {'id':'early-number','label':'영상 번호를 먼저 얻었다고 가정한다','to':counterfactual},
        {'id':'one-decision','label':'거래를 말했으니 뒤 일도 한 사람이 모두 정했다고 둔다','to':consent},
        {'id':'actual-actions','label':'먼저 현장에 간 때와 실제로 해친 때를 나누어 제출한다','to':tail},
    ]
    tail = graph.add(menu,type='menu',q='실제로 확인한 사건 표에 남길 것은?',options=options,
                     source=scene.source(scene.line+trade+1))
    # The archive record is inspected before this playback request is available.
    viewed = graph.lines(scene,archive+1,trade,tail)
    tail = graph.add('rev:03:archive-pieces-review',type='document',title='두 조각에서 확인한 범위',
        rows=['앞 조각은 남자가 문에서 뒤돌아보는 곳에서 멎는다.',
              '이어지는 조각에서는 소라의 이름을 부른 뒤에도 남자가 안쪽에서 손짓하고 물건을 옮긴다.',
              '그 남자의 마지막 행방은 보이지 않는다. 번호를 가진 사람이 어떤 생각을 했는지도 영상으로 정하지 않는다.'],
        source=scene.source(scene.line+archive+1),next=viewed)
    tail = graph.lines(scene,first_after,archive,tail)
    menu = 'rev:03:first-plan-and-second-act'
    planning = event('plan-not-predetermined','소라(켄의 몸)',
        '처음 떠날 때는 너희가 살아 있는 내 몸을 옮기려는 걸 아직 못 봤어.',menu,first_choice)
    claim = event('return-claim-not-waking','미오',
        '돌아왔다고 말한 것과 두 몸이 실제로 깨어나는 것은 달라. 그때 계속 눈을 뜬 쪽을 따로 보자.',menu,first_choice)
    tail = graph.add(menu,type='menu',q='처음의 계획과 그 뒤에 고른 행동을 어떻게 놓을까?',
        source=scene.source(scene.line+first_choice+1),options=[
            {'id':'all-planned','label':'처음부터 두 번째 공격까지 정했다고 둔다','to':planning},
            {'id':'returned','label':'돌아왔다고 믿게 했으니 실제로 돌아갔어야 한다','to':claim},
            {'id':'later-act','label':'보호 인원을 본 뒤 돌아갈 길을 없애기로 한 행동을 따로 확인한다','to':tail}])
    return graph.lines(scene,first+1,first_choice,tail)


def chapter_three_paper_hearing(graph,scenes,tasks,records,dead,seats,tail):
    scene = scenes['03-T02']
    def source(offset, current=scene):
        return current.source(current.line+offset+1)

    def queue(ident,actor,text,ref):
        parsed = speech(f'**{actor}**　{text}',ref['line'],scenes[ref['location']])
        return {'id':ident,**parsed}

    def task(ident,stage,target,offset,requires,wrongs=(),current=scene):
        ref = source(offset,current)
        tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':requires,
            'stage':{'id':ident,'v4':True,**stage},
            'queues':{'wrongVariants':[{'optionIndex':index,'script':[
                queue(f'{ident}:wrong:{index}',actor,text,ref)]} for index,actor,text in wrongs]}}
        return graph.add('rev:03:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                         source=ref,success=target,next=target)

    def nonstop(current,ident,heading,rule,title,ammo,answer,wrongs,target,agree=False,vpoint=''):
        rows = []
        for offset in range(heading+1,rule):
            if match := STMT.match(current.body[offset]):
                index,actor,raw,role = match.groups()
                weak = any(mark in role for mark in ('논파점','동의점','약점'))
                row = debate_statement(ident,index,actor,raw,source(offset,current),
                    'weak' if weak and not agree else 'plain',answer if weak and not agree else '')
                if weak and agree:
                    word, = re.findall(r'\*\*([^*]+)\*\*',raw)
                    row.update(kind='agree',agree=answer,agreeTarget={'word':word,'glyphStart':row['text'].index(word)})
                if weak and vpoint:
                    row['vpoint'] = {'glyphIndex':row['text'].index(vpoint)}
                rows.append(row)
        assert len(rows)>=10 and sum('weak' in row or 'agree' in row for row in rows)==1
        cards = [records[key] for key in ammo]
        result = task(ident,{'kind':'nonstop','title':title,'lines':rows,'options':cards,
                            'authoredAmmo':ammo,'filterOwnedEvidence':True,
                            'wrongCards':{key:cause for key,cause,*_ in wrongs}},target,rule,ammo,current=current)
        tasks[ident]['debate'] = {'id':ident,'kind':'nonstop','lines':rows,'bullets':cards}
        tasks[ident]['queues']['wrongVariants'] = [
            {'cause':cause,'script':[queue(ident+':'+cause,actor,text,source(rule,current))]}
            for _,cause,actor,text in wrongs]
        return result

    continuity = scenes['03-T03']
    tail = chapter_three_final_hearing(graph,scenes,tasks,records,dead,seats,tail)
    tail = chapter_three_motives(graph,scenes,tail)
    ns1 = continuity.body.index('#### 논스톱 — 끝났다는 말에 대답한 사람')
    rule1 = next(i for i,row in enumerate(continuity.body) if row.startswith('03-D03의 시계와'))
    ns2 = continuity.body.index('#### 논스톱 — 늦게 바뀌었다면')
    rule2 = next(i for i,row in enumerate(continuity.body) if row.startswith('정답 첫 공격 이후 연속'))
    duel = continuity.body.index('#### 반론 쇼다운 — 내 사진의 빈 곳')
    point = continuity.body.index('#### 지점 지목 — 사진 사이에서 놓친 것')
    scrum = continuity.body.index('#### 논의 스크럼 — 본체가 쓰러지면 누구부터 깨어나나')
    next_topic = continuity.body.index('### 처음부터 알고 있던 일')
    after_scrum = next(i for i in range(scrum,next_topic) if SAY.match(continuity.body[i]))
    tail = graph.lines(continuity,after_scrum,next_topic,tail)
    ident = 'T3-SD-REV01'
    pairs = []
    fragments = [('돌아오는 때','체류가 끝났는지'),('몸이 죽으면','이미 들어가 있는 곳'),
                 ('그 얼굴이 그대로','얼굴은 처음부터'),('새로 들어오면','잠들거나 쓰러져야지')]
    for at in range(scrum+1,after_scrum):
        cells = [cell.strip() for cell in continuity.body[at].strip('|').split('|')]
        if len(cells)!=2 or '“' not in cells[0] or '“' not in cells[1]:
            continue
        opponent,claim = re.fullmatch(r'(\S+) “([^”]+)”',cells[0]).groups()
        keyword,ally,response = re.fullmatch(r'(\S+)\. (\S+) “([^”]+)”',cells[1]).groups()
        claim_keyword,response_keyword = fragments[len(pairs)]
        assert claim_keyword in claim and response_keyword in response
        pairid = ident+':'+str(len(pairs))
        pairs.append({'id':pairid,'them':opponent,'themActor':SPEAKERS[opponent],'themText':claim,
            'us':ally,'usActor':SPEAKERS[ally],'usText':response,'keyword':keyword,
            'claimKeyword':claim_keyword,'responseKeyword':response_keyword,'duration':11,
            'wrong':[queue(pairid+':retry',opponent,claim,source(at,continuity))]})
    assert len(pairs)==4
    pairs[2]['wrongByKeyword'] = {'대여':[queue(ident+':loan-retry','하루카',
        '누가 칼 빌렸냐고 안 물었어. 이 얼굴이 어떻게 남았느냐고.',source(scrum,continuity))]}
    tail = task(ident,{'kind':'scrum','title':'본체가 쓰러지면 누구부터 깨어나나','pairs':pairs,
        'teams':{side:list(dict.fromkeys(pair[side+'Actor'] for pair in pairs)) for side in ('them','us')},
        'scrumDecoys':[{'keyword':word} for word in ('대여','창구 사진','종료 시계')],
        'scrumPresentation':{'topic':'본체 사망 뒤의 점유 상태','them':'원래 주인에게 돌아간다','us':'조건을 충족한 체류는 고정된다'}},
        tail,scrum,['v4:V5-3:condition','v4:V5-3:continuity','v4:V5-3:second-status'],current=continuity)
    # Exact regions refer to the existing authored plan, not an arbitrary click.
    regions = (
        ('glass','마지막 반사면',(.096,.33,.263,.57),'하루카','내 사진은 거기까지야. 거기서부터 누가 걸어가는 걸 봤는지 물어.'),
        ('corner','복도 모퉁이와 대기실 입구가 겹치는 자리',(.46,.35,.568,.57),'',''),
        ('bench','대기실 벤치',(.71,.39,.896,.52),'레이','제가 본 것은 이 안에 들어온 뒤입니다. 오시는 길은 이 그림 밖입니다.'),
    )
    tail = task('T3-SP-REV02',{'kind':'spot','question':'카메라가 끊긴 뒤에도 두 사람이 이어서 직접 본 위치는?',
        'image':MINE_ART+'mirror-plan.svg','answerRegionId':'corner','regions':[
            {'id':key,'label':label,'wrongVariant':key,'polygon':[[x,y],[a,y],[a,b],[x,b]]}
            for key,label,(x,y,a,b),*_ in regions]},tail,point,['v4:V5-3:continuity'],current=continuity)
    tasks['T3-SP-REV02']['queues']['wrongVariants'] = [{'cause':key,'script':[
        queue('T3-SP-REV02:'+key,actor,text,source(point,continuity))]}
        for key,_,_,actor,text in regions if actor]
    tail = graph.lines(continuity,duel+1,point,tail)
    tail = compile_showdown(graph,tasks,dead,seats,'rev:03:camera-gap-duel','T3-RS-REV02',
        '내 사진의 빈 곳','하루카',[
            ['내가 찍은 건 미로까지만이야.','나간 뒤엔 카메라 내렸어.','카메라에 없는 동안을 내 사진으로 보증할 수는 없어.'],
            ['사진 앞뒤를 봐도 모퉁이는 없잖아.','레이가 본 건 대기실부터고.',
             '그럼 그 사이에 그 몸이 멈추거나 의식을 잃었는지 아무도 볼 수 없었어']],
        [records[key] for key in ('v4:V5-3:reflection','v4:V5-3:continuity','v4:V5-3:second-status')],
        'v4:V5-3:continuity',source(duel,continuity),
        ('하루카','딱 그 장 다음부터 내 사진에 없어. 그걸로 바깥을 또 봤다고 하지는 마.'),tail)
    tail = graph.lines(continuity,rule2+1,duel,tail)
    tail = nonstop(continuity,'T3-NS-REV14',ns2,rule2,'늦게 바뀌었다면',
        ['v4:V5-3:reflection','v4:V5-3:second-status','v4:V5-3:continuity'],
        'v4:V5-3:continuity',[
            ('v4:V5-3:reflection','mirror','소라(켄의 몸)','그래서 얼굴 말고 뭘 봤는데.'),
            ('v4:V5-3:second-status','body-only','레이','본체 쪽의 관찰만으로 다른 몸의 연속 각성을 대신하지 마십시오.')],tail,vpoint='들어올')
    tail = graph.lines(continuity,rule1+1,ns2,tail)
    tail = nonstop(continuity,'T3-NS-REV13',ns1,rule1,'끝났다는 말에 대답한 사람',
        ['v4:V5-3:condition','v4:V5-3:clock-bench','v4:V5-3:new-sentence'],
        'v4:V5-3:clock-bench',[
            ('v4:V5-3:condition','example','레이','그때는 먼저 돌아오기로 한 경우입니다. 이번의 최대 시간이 거기서 잰 숫자라고 적지 마십시오.'),
            ('v4:V5-3:new-sentence','identity','나나','그 문장을 아는 사람과 실제로 깨어난 때는 나누어서 봐 주세요.')],tail)
    tail = graph.lines(continuity,0,ns1,tail)
    reporting = scenes['03-T02b']
    at = reporting.body.index('### 대답이 도착한 순서')
    answer = next(i for i in range(at,len(reporting.body)) if SAY.match(reporting.body[i]))
    tail = graph.lines(reporting,answer,len(reporting.body),tail)
    tail = task('T3-QA-REV14',{'kind':'choice','question':'직접 발화와 뒤에 옮긴 말을 어떻게 놓을까?',
        'options':['말을 전달한 사람을 지금 발화자로 고른다','문 앞의 사람 전부 같은 응답을 들었다고 둔다',
                   '같은 몸이 이어 말한 것과 나중에 옮긴 말을 분리한다','내용을 아는 사람 모두 처음 문장을 말했다고 둔다'],
        'answer':2},tail,at,['v4:V5-3:continuity','v4:V5-3:sealed-route'],[
            (0,'하루카','처음 반사면에서 본 것과 대기실 밖에서 들은 것은 같은 카메라에 찍히지 않았어.'),
            (1,'사츠키','내가 말의 시작을 본 위치부터 내. 전부 같은 데 서 있지 않았어.'),
            (3,'코토','제가 들은 데부터 다시 말씀드릴게요. 내용을 알아도 처음 말한 사람이 되는 건 아니에요.')],current=reporting)
    tail = graph.lines(reporting,0,at,tail)
    refusal = scenes['03-T02c']
    at = refusal.body.index('### 시연에 실패한 사람이 있었나')
    answer = next(i for i in range(at,len(refusal.body)) if SAY.match(refusal.body[i]))
    tail = graph.lines(refusal,answer,len(refusal.body),tail)
    tail = task('T3-QA-REV13',{'kind':'choice','question':'아무도 새 시연에 동의하지 않았다. 지금 무엇으로 확인할까?',
        'options':['카드를 움직이지 않았으니 능력 사용에 실패했다고 적는다','켄의 설명만으로 지금 발화자를 정한다',
                   '당시 기록의 움직임과 봉투에 대한 답을 따로 비교한다'],'answer':2},tail,at,
        ['v4:V5-3:continuity','v4:V5-3:new-sentence'],[
            (0,'사츠키','그때 시작한 적이 없었어. 나는 앞에 안 나갔고.'),
            (1,'미오','설명해 준 조건과 실제로 움직인 사람을 따로 확인해야 해. 지금 새로 시켰다고 쓸 수는 없어.')],current=refusal)
    tail = graph.lines(refusal,0,at,tail)

    # The name changes only after the six actual access-path questions.
    recognition = scenes['03-T02a']
    heading = next(i for i,row in enumerate(recognition.body) if row.startswith('#### 논스톱'))
    rule = next(i for i,row in enumerate(recognition.body) if row.startswith('4에 **03-D01e'))
    tail = graph.lines(recognition,rule+1,len(recognition.body),tail)
    tail = nonstop(recognition,'T3-NS-REV12',heading,rule,'이름과 알게 된 문장',
        ['v4:V5-3:reflection','v4:V5-3:new-sentence','v4:V5-3:perception'],
        'v4:V5-3:perception',[
            ('v4:V5-3:reflection','photo','하루카','같은 몸이 찍혔다고 어느 문장을 읽었는지까지 나오지는 않아.'),
            ('v4:V5-3:new-sentence','paper','코토','글의 내용과 그걸 읽게 된 경로를 따로 보여 주세요.')],tail,vpoint='문장까지')
    tail = graph.lines(recognition,0,heading,tail)

    reason_at = scene.body.index('#### 추리 연결 — 알았음에서 첫 행위까지')
    first_reply = next(i for i in range(reason_at,len(scene.body)) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,first_reply,len(scene.body),tail)
    ident = 'T3-RE-REV01'
    authored = (
        ('처음 쓴 값을 실제로 읽은 사람은?',
         ['켄이 안대로 앞을 가린 뒤 종이를 본 소라','당시 눈을 가렸던 켄','봉투를 맡은 나나'],0,
         [('하루카','눈가리개 틈을 확인한 뒤에 미오가 썼어. 켄이 읽었던 것으로 바꾸지 마.'),('나나','제가 건넨 건 접힌 물건이었어요. 내용을 읽어 드리지는 않았어요.')],
         ('나나','제가 넘긴 것은 봉투였어요. 원문을 읽었다는 뜻으로 남기지는 말아 주세요.')),
        ('봉투를 받은 것만으로 값을 배울 수 있었나?',
         ['소지한 순간 알았다','열어 보거나 전달받은 사실이 있어야 한다','사진을 빌려 준 순간 알았다'],1,
         [('나나','접힌 채로 받은 것과 안을 본 것은 달라요.'),('하루카','카메라에는 그 글이 안 찍혔어. 빌린 물건이 뭔지부터 봐.')],
         ('미오','누가 가지고 있었는지와 누가 실제로 읽었는지를 다른 칸에 둘게.')),
        ('첫 공격 뒤에 새로 들어온 조종자라면 무엇이 필요했나?',
         ['소라 본체가 나중에 죽었다는 점만 필요하다','켄이 자기 이름을 말했다는 점만 필요하다','켄 몸이 그 사이 다시 진입 가능한 상태였어야 한다'],2,
         [('쇼','본체의 상태와 새로 들어갈 몸의 조건을 함께 확인하십시오.'),('레이','부른 이름으로 당시 의식 상태를 정하지 마십시오.')],
         ('레이','앞선 시연의 일반 조건에 실제로 관찰한 몸의 상태를 따로 놓겠습니다.')),
        ('두 번째 발견이 바꾼 것은?',
         ['본체 생존과 이전 조종 여부를 구분한 채 그 뒤 몸의 상태가 고정되는 이유','첫 살해 자체가 취소됨','켄에게 그 공격의 책임이 돌아감'],0,
         [('사츠키','두 번째로 가기 전 내가 앞에서 들은 말 다시 봐. 앞일이 뒤에 달라진 적은 없어.'),('레이','지금 눈을 뜨고 있다는 점으로 앞서 어느 분이 조종했는지 정하지 마십시오.')],
         ('미오','본체가 살아 있던 때와 그 뒤 같은 몸에 남는 조건은 따로 표시할게.')),
        ('새 문장에 접근했는지 알아보려면 무엇을 대조해야 하나?',
         ['첫 공개 실험에서 둘이 같은 대답을 한 것만 고름','안대 착용 뒤 작성·읽기·봉함 순서와 재판 전 열지 않은 경로','첫 공격 후 얼굴이 찍힌 장면만 고름'],1,
         [('미오','그 말은 둘 다 전에 들었어. 이번에 처음 적은 건 그다음이야.'),('하루카','찍을 때 옷하고 얼굴은 그대로였어. 누가 다른 종이를 봤는지 거기에 나오지는 않아.')],
         ('미오','처음 글을 만든 때와 봉투가 옮겨 간 때를 연결하되, 보지 못한 구간은 채우지 않을게.')),
        ('이 답에서 가장 좁게 확정할 것은?',
         ['그 사람이 첫 충돌 전에 먼저 칼을 쥐었는지','바깥에서 쓰러진 사람의 정확한 사망 분','현재 발언자가 새 문장에 접근한 방식'],2,
         [('사츠키','칼 든 손 하나 더 보라고 했지. 글 쓴 걸 다 알아도 그때 손은 다음에 봐.'),('쇼','두 검안 기록에는 확인한 범위가 있습니다. 정확한 사망 분을 여기서 더할 수는 없습니다.')],
         ('미오','지금 말한 사람을 먼저 부를게. 두 건의 행위자를 동시에 정한 건 아니야.')),
    )
    questions = []
    for i,(question,options,answer,wrongs,success) in enumerate(authored):
        at = next(j for j,row in enumerate(scene.body[reason_at:],reason_at) if row.startswith(f'{i+1}. '))
        ref = source(at)
        ids = [f'option-{n}' for n in range(3)]
        incorrect = [n for n in range(3) if n!=answer]
        questions.append({'q':question,'answer':options[answer],'options':options,'optionIds':ids,
            'success':[queue(f'{ident}:{i}:success',*success,ref)],
            'wrongVariants':[{'optionId':ids[n],'script':[queue(f'{ident}:{i}:{n}',*reply,ref)]}
                             for n,reply in zip(incorrect,wrongs)]})
    tail = task(ident,{'kind':'reasoning','title':'알았음에서 첫 행위까지','questions':questions},tail,
                reason_at,['v4:V5-3:new-sentence','v4:V5-3:sealed-route','v4:V5-3:condition'])

    consequence = scene.body.index('### 다음에도 네 말부터 기다려야 돼?')
    classification = next(i for i,row in enumerate(scene.body) if row.startswith('플레이어가 **원문을 열기'))
    callback = next(i for i,row in enumerate(scene.body) if row.startswith('01-T04에서 보호대'))
    after_callback = next(i for i in range(callback,len(scene.body)) if scene.body[i].startswith('**쇼**'))
    tail = graph.lines(scene,after_callback,reason_at,tail)
    recalled = graph.lines(scene,callback+1,after_callback,tail)
    tail = graph.add('rev:03:first-perjury-memory',type='branch',
        cases=[{'flag':'01-T04a:perjury','equals':True,'to':recalled}],default=tail)
    distinctions = (
        ('T3-QA-REV10','원문을 열기 전에 들은 말은?',
         ['지금 펼친 원문의 정확한 문장','미오가 일부러 틀리게 읽은 문장','사진 속 얼굴'],1,
         [(0,'쇼','원문을 펴기 전에 미오 씨가 말한 문장은 원문과 달랐습니다.'),(2,'하루카','얼굴이 찍힌 것과 그때 말한 내용을 같은 칸에 놓지 마.')]),
        ('T3-QA-REV11','원문에 실제로 있는 것을 무엇으로 확인하나?',
         ['나나가 지금 처음 펼친 종이','현재 증언대의 얼굴','미오가 방금 지어낸 문장'],0,
         [(1,'하루카','얼굴이 찍힌 일로 글을 미리 알았는지 정하면 안 돼.'),(2,'미오','내가 일부러 바꿔 말한 것을 원문 위에 올리지는 않을게.')]),
        ('T3-QA-REV12','작성할 때 실제로 글을 읽은 사람은?',
         ['접힌 봉투를 받은 나나','안대로 가린 켄','미오가 쓴 새 문장을 본 소라'],2,
         [(0,'나나','저는 접힌 것을 받아 옮겼어요. 쓰실 때 옆에서 읽었다고는 안 했어요.'),(1,'하루카','안대로 가린 뒤에 썼어. 그 조건까지 내가 확인했어.')]),
    )
    for tid,question,options,answer,wrongs in reversed(distinctions):
        tail = task(tid,{'kind':'choice','question':question,'options':options,'answer':answer},tail,
                    classification,['v4:V5-3:new-sentence'],wrongs)
    tail = graph.lines(scene,consequence+1,classification,tail)
    showdown = scene.body.index('#### 반론 쇼다운 — 거짓말 때문에 공모가 생긴다면')
    weak_at = next(i for i in range(showdown,consequence) if '방금 한 거짓말을 보면 우리 둘이 미리' in scene.body[i])
    tail = graph.lines(scene,weak_at+1,consequence,tail)
    tail = compile_showdown(graph,tasks,dead,seats,'rev:03:paper-collusion-duel','T3-RS-REV01',
        '거짓말 때문에 공모가 생긴다면','켄',[
            ['너 하나 때문에 다들 이 문장 제대로 알아내려는 척하고 있잖아.',
             '네가 나하고 미리 말 맞춘 다음에, 내가 다 안다는 것처럼 처음부터 하려고 했을 수도 있어.'],
            ['미오 네가 일부러 틀린 문장을 먼저 읽었지.',
             '방금 한 거짓말을 보면 우리 둘이 미리 짜고 네가 새 문장을 내게 줬다는 건 이미 증명됐어.']],
        [records[key] for key in ('v4:V5-3:new-sentence','v4:V5-3:sealed-route','v4:V5-3:reflection')],
        'v4:V5-3:sealed-route',source(weak_at),('나나','일부러 다르게 말씀하셨잖아요. 그 사실까지 지우라고 하신 적 없어요.'),tail)
    # Introductory spoken lines remain separate from the blade statement.
    tail = graph.lines(scene,showdown+1,weak_at,tail)

    agree_at = scene.body.index('#### 논스톱 동의 — 전에 있던 글을 읽어도')
    agree_rule = next(i for i,row in enumerate(scene.body) if row.startswith('03-D02에서 플레이어가'))
    tail = graph.lines(scene,agree_rule+1,showdown,tail)
    tail = nonstop(scene,'T3-NS-REV11',agree_at,agree_rule,'전에 있던 글을 읽어도',
        ['v4:V5-3:index','v4:V5-3:new-sentence','v4:V5-3:written-order'],
        'v4:V5-3:written-order',[
            ('v4:V5-3:index','index','하루카','작업대의 제목을 맞히는 문제가 아니야. 그 문장이 처음 생긴 데부터 봐.'),
            ('v4:V5-3:new-sentence','current','레이','정확한 문구는 알 수 있지만 언제 처음 쓰였는지는 그 한 장의 현재 상태에 나오지 않습니다.')],tail,agree=True)
    heard_at = scene.body.index('#### 논스톱 — 남에게 들은 말일 수도 있어')
    heard_rule = next(i for i,row in enumerate(scene.body) if row.startswith('03-D02의 접은 상태'))
    tail = graph.lines(scene,heard_rule+1,agree_at,tail)
    tail = nonstop(scene,'T3-NS-REV10',heard_at,heard_rule,'남에게 들은 말일 수도 있어',
        ['v4:V5-3:new-sentence','v4:V5-3:sealed-route','v4:V5-3:reflection'],
        'v4:V5-3:sealed-route',[
            ('v4:V5-3:new-sentence','current','나나','지금 보이는 접힌 선 하나로 제가 갖고 있던 동안까지 설명할 수는 없어요.'),
            ('v4:V5-3:reflection','photo','하루카','내 카메라가 찍은 건 이동하는 몸이야. 봉투의 앞뒤는 안 찍었어.')],tail)
    opened = graph.add('rev:03:opened-paper',type='evidence',evidenceId='v4:V5-3:new-sentence',
        name=records['v4:V5-3:new-sentence']['name'],text=records['v4:V5-3:new-sentence']['text'],
        source=source(heard_at),next=tail)
    tail = graph.add('rev:03:paper-first-open',type='document',title='여기서 처음 펼친 원문',
        rows=['낡은 구두 속 파란새는 설탕을 숨긴다','미오가 일부러 바꿔 읽은 말은 이 원문에 덧쓰지 않는다.'],
        source=source(heard_at),next=opened)
    custody = scene.body.index('### 누가 봉투를 꺼내는가')
    starts = [i for i,row in enumerate(scene.body[custody:heard_at],custody) if row.startswith(
        ('**조건을 말하고 코토에게','**미오가 가방을 들고','**코토의 의심을 직접'))]
    assert len(starts)==3
    routes = [graph.lines(scene,start+1,starts[i+1] if i<2 else heard_at,tail) for i,start in enumerate(starts)]
    tail = graph.add('rev:03:paper-custody-recall',type='branch',
        cases=[{'flag':'03-I03e','equals':chr(65+i),'to':route} for i,route in enumerate(routes)],
        default=graph.add('rev:03:paper-custody-unspecified',type='say',actor='nana',speaker='나나',
                         text='제가 닫았던 자리부터 같이 볼게요. 지금 이 자리에서 처음 펼칠게요.',
                         source=source(custody),next=tail))
    lie_at = scene.body.index('#### 우소다마 — 봉투 밖에 있는 말')
    lie_response = next(i for i in range(lie_at,custody) if scene.body[i].startswith('**미오**'))
    tail = graph.lines(scene,lie_response,custody,tail)
    ident = 'T3-LI-REV01'
    ammo = ['v4:V5-3:unread-sentence','v4:V5-3:reflection','v4:V5-3:loan']
    cards = [records[key] for key in ammo]
    rows = [debate_statement(ident,i,actor,raw,source(lie_at),role,answer) for i,(actor,raw,role,answer) in enumerate((
        ('하루카','빌려 준 카메라 안에 글이 찍힌 건 아니었어.','plain',''),
        ('나나','봉투가 접힌 뒤에 받았고, 제가 읽어 드리지는 않았어요.','plain',''),
        ('켄의 몸','**난 봉투 안의 말을 몰라.**','weak',ammo[0]),
        ('코토','받은 사람이 안을 본 때가 따로 있었는지 물어봐야 해요.','plain','')))]
    next(row for row in rows if 'weak' in row)['weak']['lie'] = True
    tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':ammo,
        'stage':{'id':ident,'v4':True,'kind':'nonstop','title':'봉투 밖에 있는 말','lines':rows,
                 'options':cards,'authoredAmmo':ammo,'filterOwnedEvidence':True,
                 'wrongCards':{ammo[0]:'repeat',ammo[1]:'photo',ammo[2]:'loan'}},
        'transformation':{'sourceEvidenceId':ammo[0],'lieLabel':'켄도 그 문장을 들었다','intentionalHold':True},
        'debate':{'id':ident,'kind':'nonstop','lines':rows,'bullets':cards},
        'queues':{'wrongVariants':[{'cause':cause,'script':[queue(ident+':'+cause,actor,text,source(lie_at))]}
            for cause,actor,text in (
                ('repeat','미오','전달되지 않았다는 근거로 모른다는 말은 깨지지 않아. 다르게 물어봐야 해.'),
                ('photo','하루카','그 글을 찍은 사진은 없었어. 기계와 봉투를 구별해.'),
                ('loan','나나','제가 가져간 건 카메라가 아니라 봉투였어요.'))]}}
    tail = graph.add('rev:03:paper-perjury',type='task',taskId=ident,trialDead=dead,seats=seats,
        source=source(lie_at),next=tail,success=tail,
        outcomes={'perjury':{'judgment':'lie','to':tail,'sets':{'03-T02:perjury':True}}})
    first_tabs = next(i for i,row in enumerate(scene.body) if row.startswith('첫 공격 전에 쓴 문장'))
    choices = [(i,BULLET.match(row)[1],BULLET.match(row)[2]) for i,row in enumerate(scene.body[first_tabs:lie_at],first_tabs) if BULLET.match(row)]
    assert len(choices)==3
    last = choices[-1][0]
    tail = graph.lines(scene,last+1,lie_at,tail)
    menu = 'rev:03:closed-envelope-facts'
    options = []
    for i,(at,label,response) in enumerate(choices):
        actor,text = re.findall(r'([^ “]+) “([^”]+)”',response)[0]
        flag = f'03-T02:fact:{i}'
        event = queue(menu+':say:'+str(i),actor,text,source(at))
        event.pop('id')
        reply = graph.add(menu+':'+str(i),**event,
                          set={flag:True},next=menu)
        options.append({'id':str(i),'label':label,'to':reply,'requires':{flag:False}})
    options.append({'id':'continue','label':'세 사실을 구분한 채 질문한다','to':tail,
                    'requires':{f'03-T02:fact:{i}':True for i in range(3)}})
    tail = graph.add(menu,type='menu',q='원문을 열지 않고 확인할 사실',options=options,source=source(first_tabs))
    first_rule = next(i for i,row in enumerate(scene.body) if row.startswith('03-D03에서 모퉁이를'))
    first_at = scene.body.index('#### 논스톱 — 찍은 것과 빌린 것')
    tail = nonstop(scene,'T3-NS-REV09',first_at,first_rule,'찍은 것과 빌린 것',
        ['v4:V5-3:reflection','v4:V5-3:loan','v4:V5-3:sealed-route'],
        'v4:V5-3:sealed-route',[
            ('v4:V5-3:reflection','lens','하루카','사진에 없는 게 없었던 건 아니야. 종이가 넘어간 자리까지 같이 보자.'),
            ('v4:V5-3:loan','loan','나나','제가 들고 간 건 카메라가 아니라 봉투였어요.')],tail)
    tail = graph.lines(scene,0,first_at,tail)
    restraint = scenes['03-T02d']
    at = restraint.body.index('### 손이 빠져나간 게 먼저일까')
    after = next(i for i in range(at,len(restraint.body)) if SAY.match(restraint.body[i]))
    tail = graph.lines(restraint,after,len(restraint.body),tail)
    menu = 'rev:03:restraint-claims'
    claims = (
        ('복도부터 레이가 계속 잡고 있었다','사츠키','내가 본 사람은 칼 든 채로 문턱을 넘었어. 레이가 안에서 붙든 뒤에 밖에서 끌고 온 게 아니야.'),
        ('붙들렸다 풀려난 동작을 첫 공격보다 앞에 둔다','하루카','내가 바깥에서 본 게 먼저야. 레이가 붙든 곳은 그 뒤에 도착한 방 안이고.'),
        ('도움을 요청했고 모두가 들었다고 놓는다','사츠키','내가 들은 건 비키라는 말이야. 손 잡아 달라는 부탁으로 바꾸지 마.'),
        ('다음 공격을 막는 일과 실제 공격한 일을 나눈다','미오','붙들 수 있었는지와 먼저 칼을 들거나 찌른 일을 대신 했는지는 같은 칸이 아니야.'),
    )
    options = []
    for i,(label,actor,text) in enumerate(claims):
        flag = '03-T02d:'+str(i)
        response = graph.add(menu+':'+str(i),type='say',actor=SPEAKERS[actor],speaker=actor,text=text,
            source=source(at,restraint),set={flag:True},next=menu)
        options.append({'id':str(i),'label':label,'to':response,'requires':{flag:False}})
    options.append({'id':'continue','label':'요청·제지·공격의 순서를 나눠 남긴다','to':tail,
                    'requires':{'03-T02d:'+str(i):True for i in range(4)}})
    tail = graph.add(menu,type='menu',q='붙들고 있던 손을 어느 시점에 둘까?',options=options,
                     source=source(at,restraint))
    return graph.lines(restraint,0,at,tail)


def chapter_three_cloth_hearing(graph,scenes,tasks,records,dead,seats,tail,knife_objects):
    def ref(scene,offset):
        return scene.source(scene.line+offset+1)

    def task(ident,scene,offset,stage,requires,target,wrongs):
        source = ref(scene,offset)
        tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':requires,
            'stage':{'id':ident,'v4':True,**stage},
            'queues':{'wrongVariants':[{'optionIndex':index,'script':[{
                'id':f'{ident}:wrong:{index}','type':'say','speaker':speaker,
                'actor':SPEAKERS['켄' if speaker=='켄의 몸' else speaker],'text':text,'source':source}]}
                for index,speaker,text in wrongs]}}
        return graph.add('rev:03:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                         source=source,success=target,next=target)

    scene = scenes['03-T01d']
    panic_at = next(i for i,row in enumerate(scene.body) if row.startswith('### 패닉 논의'))
    panic_rule = next(i for i,row in enumerate(scene.body) if row.startswith('**정답.**'))
    tail = graph.lines(scene,panic_rule+1,len(scene.body),tail)
    ident = 'T3-PN-REV02'
    ammo = ['v4:V5-3:blade-stop','v4:V5-3:loan','v4:V5-3:cloth-handover']
    cards = [records[key] for key in ammo]
    lanes = [{'id':str(i),'speaker':name,'actor':SPEAKERS[name],'lines':[]}
             for i,name in enumerate(('유우','사츠키','아카리'))]
    rows = []
    for offset in range(panic_at+1,panic_rule):
        cells = [cell.strip() for cell in scene.body[offset].strip('|').split('|')]
        if len(cells)!=4 or not cells[0].isdigit():
            continue
        for index,(lane,raw) in enumerate(zip(lanes,cells[1:])):
            raw = raw.replace('[약점] ','')
            weak = (cells[0],index)==('6',0)
            row = debate_statement(ident,f'{index}:{cells[0]}',lane['speaker'],raw,ref(scene,offset),
                                   'weak' if weak else 'plain',ammo[-1] if weak else '')
            rows.append(row)
            lane['lines'].append(row['id'])
            if '[큰 소리]' in raw:
                noise = debate_statement(ident,'noise',lane['speaker'],raw,ref(scene,offset),'noise')
                rows.append(dict(noise,noiseRole='loud',noiseDurability=2,hostStatement=row['id']))
    assert len(rows)==25 and [len(lane['lines']) for lane in lanes]==[8,8,8]
    tail = task(ident,scene,panic_rule,{'kind':'panic','title':'움직이는 게 먼저 보인 사람',
                'lines':rows,'options':cards,'filterOwnedEvidence':True,
                'wrongCards':{ammo[0]:'blade',ammo[1]:'loan'}},ammo,tail,[])
    tasks[ident]['debate'] = {'id':ident,'kind':'panic','lines':rows,'bullets':cards,
                              'lanes':lanes,'synchronizedBeats':True}
    tasks[ident]['queues']['wrongVariants'] = [
        {'cause':cause,'script':[{'id':ident+':'+cause,'type':'say','actor':SPEAKERS[speaker],
                                'speaker':speaker,'text':text,'source':ref(scene,panic_rule)}]}
        for cause,speaker,text in (
            ('blade','사츠키','내가 발 댄 건 몸을 떼어 놓은 뒤야. 천 누가 이어받았는지는 다른 데서 물어.'),
            ('loan','미오','첫 현장에서 칼을 빌린 기록이야. 두 번째 방에 들어간 구조 인원은 이걸로 못 정해.'))]
    tail = graph.lines(scene,0,panic_at,tail)

    scene = scenes['03-T01c']
    sort_at = scene.body.index('### 현장 순서 대조 — 부른 쪽과 들어간 쪽')
    answer_at = next(i for i,row in enumerate(scene.body) if row.startswith('**유우**　나나 소리 들으면'))
    tail = graph.lines(scene,answer_at,len(scene.body),tail)
    timeline = (
        ('T3-QA-REV09','나중에 문 쪽에서 본 칼의 위치로 확인할 수 있는 것은?',
         ['벤치에서 가장 먼저 칼을 쥔 몸의 신원','레이가 그전에 손을 댔는지','사츠키가 자기 쪽으로 온 날을 민 움직임'],2,[
             (0,'미오','가장 늦게 본 위치로 가장 먼저 움직인 몸부터 고르지는 마.'),
             (1,'레이','제가 문턱을 넘은 때와 붙들던 위치를 다시 보십시오.')]),
        ('T3-QA-REV08','칼이 앞으로 돌아가기 전, 옮길 준비를 하던 말은?',
         ['쇼가 살아 있는 사람을 옮기겠다고 한 말','나나가 두 번째 확인을 부탁한 외침','첫 현장의 종이에 관해 들은 말'],0,[
             (1,'나나','제가 두 번째로 확인해 달라고 부른 것은 그 뒤였어요.'),
             (2,'미오','그건 다른 방에서 들은 말이야. 여기의 외침 전후를 그 말로 잇지는 말자.')]),
    )
    for ident,question,options,answer,wrongs in timeline:
        tail = task(ident,scene,sort_at,{'kind':'choice','question':question,'options':options,'answer':answer},
                    ['v4:V5-3:movement','v4:V5-3:blade-stop'],tail,wrongs)
    tail = task('T3-PE-REV01',scene,sort_at,{
        'kind':'person','question':'먼저 문턱에서 물러나 길을 비우겠다고 했던 사람은?',
        'candidates':['nana','rei','yuu'],'answer':'rei'},['v4:V5-3:movement'],tail,[
            (0,'나나','저는 벤치 곁에서 손을 놓지 않았어요.'),
            (2,'유우','나는 안에 들어간 적이 없어. 안에서 나왔던 사람으로 놓지 마.')])
    tail = graph.lines(scene,0,sort_at,tail)

    scene = scenes['03-T01e']
    heading = next(i for i,row in enumerate(scene.body) if row.startswith('#### 논스톱'))
    rule = next(i for i,row in enumerate(scene.body) if row.startswith('4에 쏘는 대조'))
    viewpoint = scene.body.index('### 붙든 팔과 받치려던 어깨')
    tail = graph.lines(scene,rule+1,len(scene.body),tail)
    ident = 'T3-NS-REV08'
    ammo = ['v4:V5-3:blade-stop','v4:V5-3:first-injury','v4:V5-3:movement']
    rows = []
    for offset in range(heading+1,rule):
        if match := STMT.match(scene.body[offset]):
            index,speaker,raw,_ = match.groups()
            rows.append(debate_statement(ident,index,speaker,raw,ref(scene,offset),
                                         'weak' if index=='4' else 'plain',ammo[-1] if index=='4' else ''))
    assert len(rows)==16
    cards = [records[key] for key in ammo]
    tail = task(ident,scene,rule,{'kind':'nonstop','title':'붙잡힌 손이 먼저였다고 하면','lines':rows,
                'options':cards,'authoredAmmo':ammo,'filterOwnedEvidence':True,
                'wrongCards':{ammo[0]:'blade',ammo[1]:'first-room'}},ammo,tail,[])
    tasks[ident]['debate'] = {'id':ident,'kind':'nonstop','lines':rows,'bullets':cards}
    tasks[ident]['queues']['wrongVariants'] = [
        {'cause':cause,'script':[{'type':'say','id':ident+':'+cause,'actor':SPEAKERS[speaker],
          'speaker':speaker,'text':reply,'source':ref(scene,rule)}]} for cause,speaker,reply in (
            ('blade','사츠키','몸을 붙든 뒤에 내가 칼 보이는 위치만 고쳤어. 그 전에 안에서 본 손을 내.'),
            ('first-room','쇼','지금은 다른 몸이 있던 벤치 쪽 행동을 묻고 있습니다. 첫 검안과 나누십시오.'))]
    # Let each witness answer only for their own position before merging.
    views = (
        ('sho','쇼의 시점','쇼','제가 팔에 닿았을 때 날은 이미 벤치 쪽에 닿았습니다. 그 뒤 두 몸을 떼어 놓았습니다.'),
        ('nana','나나의 시점','나나','제가 볼 때에는 아직 칼을 들고 계신 쪽이 먼저 앞으로 왔어요.'),
        ('rei','레이의 시점','레이','제가 팔을 잡은 것은 쇼 씨가 먼저 두 몸을 떼어 놓은 뒤입니다.'),
        ('satsuki','사츠키의 시점','사츠키','처음부터 안에 있던 손은 못 봤어. 바닥에 온 칼을 내가 민 건 그다음이고.'),
    )
    menu = 'rev:03:restraint-witnesses'
    options = []
    for key,label,speaker,text in views:
        reply = graph.add(menu+':'+key,type='say',actor=SPEAKERS[speaker],speaker=speaker,text=text,
                          source=ref(scene,viewpoint),next=menu)
        options.append({'id':key,'label':label,'to':reply})
    options.append({'id':'compare','label':'제지와 되돌아간 팔의 순서를 함께 대조한다','to':tail})
    tail = graph.add(menu,type='menu',q='누가 직접 보았던 위치부터 확인할까?',options=options,
                     source=ref(scene,viewpoint))
    tail = graph.lines(scene,0,viewpoint,tail)

    scene = scenes['03-T01f']
    mine_at = next(i for i,row in enumerate(scene.body) if row.startswith('### 발굴'))
    after_mine = next(i for i,row in enumerate(scene.body) if row.startswith('**나나**　움직이는 걸'))
    tail = graph.lines(scene,after_mine,len(scene.body),tail)
    ident = 'T3-MM-REV02'
    candidates = (
        ('knife-at-threshold','문밖 바닥에 멈춘 칼','유우','내가 먼저 봤던 컷이 그거야. 전부터 놓였는지 보려면 한 칸 더 뒤를 열어.'),
        ('knife-from-bench','벤치에서 돌아온 팔과 그 뒤 바닥의 칼','',''),
        ('knife-carried-in','칼을 쥐고 문에서 들어오는 손','사츠키','내가 손잡이 잡았다는 사람을 먼저 데려와. 네 그림에 내 손 그리면 그게 목격이야?'),
    )
    tail = task(ident,scene,mine_at,{'kind':'mindmine','title':'칼을 숨긴 자리부터 여는 방법',
                'question':'문밖에 미리 있던 칼이라는 설명과 무엇을 대조할까?',
                'image':MINE_ART+'mirror-knife-board.svg','answerRegionId':'knife-from-bench',
                'mineObjects':knife_objects,'regions':[{'id':key,'label':label,'correct':not speaker,'wrongVariant':key}
                    for key,label,speaker,_ in candidates]},
                ['v4:V5-3:movement','v4:V5-3:blade-stop'],tail,[])
    tasks[ident]['queues']['wrongVariants'] = [{
        'cause':key,'script':[{'id':ident+':'+key,'type':'say','speaker':speaker,
                              'actor':SPEAKERS[speaker],'text':reply,'source':ref(scene,mine_at)}]}
        for key,_,speaker,reply in candidates if speaker]
    tail = graph.lines(scene,0,mine_at,tail)
    scene = scenes['03-T01b']
    positions = scene.body.index('#### 위치 고르기 — 붙든 쪽과 날이 떨어진 쪽')
    response = next(i for i,row in enumerate(scene.body) if row.startswith('**사츠키**　칼을 옆으로'))
    tail = graph.lines(scene,response,len(scene.body),tail)
    ident = 'T3-QA-REV06'
    tail = task(ident,scene,positions,{
        'kind':'choice','question':'두 번째 현장의 손과 칼을 어떤 순서로 확인했지?',
        'options':['바닥의 칼 → 붙든 팔 → 문턱','벤치로 돌아온 손 → 두 몸을 떼어 놓고 붙든 쪽 → 칼을 문밖으로 민 때',
                   '처음 칼을 빌린 이름 → 발견 방송 → 문턱의 칼'],'answer':1},
        ['v4:V5-3:movement','v4:V5-3:blade-stop'],tail,[
            (0,'나나','그림에서 제일 가까운 것부터 고르셨네요. 제가 처음 본 건 팔이 돌아오는 때였어요.'),
            (2,'미오','이름부터 고르면 그 사람이 칼을 쥔 때까지 한 장으로 붙이게 돼. 실제 보인 순서를 먼저 놓자.')])
    starts = [i for i,row in enumerate(scene.body[:positions]) if row.startswith(
        ('**코토에게 통로를','**칼을 둔 뒤 나갈','**나나에게 소리만'))]
    assert len(starts)==3
    routes = [graph.lines(scene,start+1,starts[index+1] if index+1<len(starts) else positions,tail)
              for index,start in enumerate(starts)]
    # The prior optional conversation is a memory, so skipped play cannot
    # imply that all three requests happened.
    tail = graph.add('rev:03:door-request-memory',type='branch',
                     cases=[{'flag':'03-I01b','equals':chr(65+i),'to':route} for i,route in enumerate(routes)],
                     default=tail)
    tail = graph.lines(scene,0,starts[0],tail)
    scene = scenes['03-T01a']
    heading = next(i for i,row in enumerate(scene.body) if row.startswith('#### 논스톱'))
    rule = next(i for i,row in enumerate(scene.body) if row.startswith('정답은 03-I02a의'))
    tail = graph.lines(scene,rule+1,len(scene.body),tail)
    ident = 'T3-NS-REV07'
    ammo = ['v4:V5-3:second-status','v4:V5-3:first-injury','v4:V5-3:cloth-handover']
    cards = [records[key] for key in ammo]
    rows = []
    for offset in range(heading+1,rule):
        if match := STMT.match(scene.body[offset]):
            index,speaker,raw,_ = match.groups()
            rows.append(debate_statement(ident,index,speaker,raw,ref(scene,offset),
                                         'weak' if index=='5' else 'plain',ammo[-1] if index=='5' else ''))
    assert len(rows)==11
    tail = task(ident,scene,rule,{'kind':'nonstop','title':'천을 주고받은 차례','lines':rows,'options':cards,
                'authoredAmmo':ammo,'filterOwnedEvidence':True,'wrongCards':{ammo[0]:'status',ammo[1]:'first'}},
                ammo,tail,[])
    tasks[ident]['debate'] = {'id':ident,'kind':'nonstop','lines':rows,'bullets':cards}
    tasks[ident]['queues']['wrongVariants'] = [{
        'cause':key,'script':[{'type':'say','id':ident+':'+key,'actor':'sho','speaker':'쇼',
                              'text':text,'source':ref(scene,rule)}]} for key,text in (
            ('status','제가 언제 호흡을 확인했는지와 천을 문가에서 받은 손을 따로 확인하십시오.'),
            ('first','첫 번째 발견 시각으로 이 방 안의 천을 앞당길 수는 없습니다.'))]
    return graph.lines(scene,0,heading,tail)


def chapter_three_investigations(scenes, mirror_objects, knife_objects):
    graph = CampaignGraph()
    first, interval, second = (scenes[key] for key in ('03-I00', '03-I01', '03-I02'))
    end = graph.add('rev:03:excerpt-end', type='end')
    tasks = {}
    dead = ['kaede', 'taiga', 'ai', 'rin', 'sora', 'riku']
    seats = [name for name in SPEAKERS.values() if name != 'lappy']

    def spot(scene, key, name, facts, room, pos, source_at, spoken):
        ref = scene.source(scene.line + source_at + 1)
        done = graph.add(f'rev:03:return:{key}', type='return')
        evidence_id = 'v4:' + key
        record = graph.add(f'rev:03:record:{key}', type='evidence', evidenceId=evidence_id,
                           name=name, text=facts, source=ref, next=done)
        supplemental={
            'V5-3:reflection':['03-I00b','03-I00c'],'V5-3:index':['03-I00d'],
            'V5-3:first-injury':['03-I00e'],'V5-3:movement':['03-I03h','03-I03g'],
            'V5-3:second-status':['03-I02a','03-I02b','03-I03b','03-I03c'],
        }
        record=supplemental_inspection(graph,scenes,supplemental.get(key,()),record)
        return {'id': key, 'label': name, 'neutralLabel': name, 'space_id': room, 'world_pos': pos,
                'entry': spoken(record), 'evidenceId': evidence_id}

    def hub(ident, room, spots, following):
        return graph.add(ident, type='investigate', space_id=room, spots=spots,
                         requiredSpotIds=[entry['id'] for entry in spots],
                         requiredCards=[entry['evidenceId'] for entry in spots], next=following)

    followup = [i for i, line in enumerate(second.body) if BULLET.match(line)]
    assert len(followup) == 3
    reports = (
        ('V5-3:movement', '붙잡기 전과 후의 움직임', '칼을 든 팔이 벤치 쪽으로 돌아온 뒤 쇼가 손을 뻗었다. 쇼가 두 몸을 떼어 놓은 다음 레이가 붙들었다. 사츠키는 그 뒤 문밖으로 칼을 밀었다. 레이는 문밖에 있던 동안의 동작을 직접 보지 못했다.', [1.6, 1.2, 1.5], '레이'),
        ('V5-3:blade-stop', '작업 칼이 멈춘 위치', '사츠키는 칼이 처음 떨어지는 순간을 보지 못했다. 굴러온 칼을 발끝으로 밀었으며, 밀기 전과 멈춘 위치가 다르다.', [0.8, .35, -.6], '사츠키'),
        ('V5-3:second-status', '대기실의 마지막 생존 기록', '나나가 먼저 호흡을 봤고, 쇼가 구조 전에 다시 확인했다. 이후 대기실에서 별도로 사망을 확인했다.', [-1.5, 1.1, -.1], '쇼'),
    )
    later_spots = []
    for offset, (key, name, facts, pos, speaker) in zip(followup, reports):
        line, = re.findall(r'“([^”]+)”', second.body[offset])
        def spoken(target, offset=offset, key=key, line=line, speaker=speaker):
            if key == 'V5-3:movement':
                physical = scenes['03-I03d']
                choice_at = next(i for i,row in enumerate(physical.body) if row.startswith('(플레이어는 비어 있는 손'))
                after = graph.lines(physical,choice_at+1,len(physical.body),target)
                menu = 'rev:03:three-observation-points'
                options = []
                observations = (
                    ('hand','붙든 뒤의 양손','레이','제가 붙들고 나서는 양손이 올라와 있었습니다. 바닥에 다시 손을 넣는 걸 막았습니다.'),
                    ('floor','바닥의 칼','사츠키','칼이 바닥에 와서 내가 발끝으로 밀었어. 그 전에 손에서 놓치는 때부터 봤다고는 안 할 거야.'),
                    ('threshold','천을 건넨 문턱','아카리','제가 천 받으러 돌아섰다가 다시 보니 문 쪽이었어요. 그 전에 어디에 있었는지는 모르겠어요.'),
                )
                for name,label,actor,text in observations:
                    flag = '03-I03d:'+name
                    response = graph.add(menu+':'+name,type='say',actor=SPEAKERS[actor],speaker=actor,
                                         text=text,set={flag:True},source=physical.source(physical.line+choice_at+1),next=menu)
                    options.append({'id':name,'label':label,'to':response,'requires':{flag:False}})
                options.append({'id':'compare','label':'세 위치의 관찰을 나란히 남긴다','to':after,
                                'requires':{'03-I03d:'+name:True for name,*_ in observations}})
                target = graph.add(menu,type='menu',q='직접 본 위치를 하나씩 확인한다',options=options,
                                   source=physical.source(physical.line+choice_at+1))
                target = graph.lines(physical,0,choice_at,target)
            return graph.add(f'rev:03:interview:{key}', type='say', actor=SPEAKERS[speaker], speaker=speaker,
                             text=line, source=second.source(second.line + offset + 1), next=target)
        later_spots.append(spot(second, key, name, facts, 'mirror_waiting', pos, offset, spoken))
    hearing = scenes['03-T00']
    opening = scenes['03-T0A']
    first_round = hearing.body.index('#### 논스톱 — 손이 두 번 보인 이유')
    mine_heading = hearing.body.index('#### 발굴 이매지네이션 — 반사면에서 실제 통로로')
    first_rule = next(i for i in range(first_round, mine_heading) if hearing.body[i].startswith('03-D03·I03의'))
    card_source = hearing.source(hearing.line + first_rule + 1)
    cards = [
        {'id': 'v4:V5-3:reflection', 'name': '반사면과 직접 관찰 방향',
         'text': '카메라 프레임에서 기둥이 가려졌다. 한 프레임 안에서 반사에 나타난 쪽과 직접 보인 방향은 다르다.'},
        {'id': 'v4:V5-3:loan', 'name': '공용 대여 행',
         'text': '공방에서 처음 가져갈 때 남긴 대여 기록이다. 첫 공격에서 누가 쥐었는지 확인한 기록은 아니다.'},
        {'id': 'v4:V5-3:camera-compare', 'name': '촬영 각도와 미로 통로의 대조',
         'text': '거울의 맞은편 실제 통로와 모퉁이의 직접 관찰 지점을 대응했다. 한 사람이 그 위치를 지나갈 때 손이 유리 안과 바깥에 겹쳐 보인다.'},
    ]
    task = 'T3-NS-REV01'
    rows = []
    for i in range(first_round + 1, first_rule):
        if match := STMT.match(hearing.body[i]):
            index, speaker, text, role = match.groups()
            assert (index == '4') == ('논파점' in role)
            answer = cards[2]['id'] if index == '4' else ''
            rows.append(debate_statement(task, index, speaker, text, hearing.source(hearing.line + i + 1),
                                         'weak' if answer else 'plain', answer))
    assert len(rows) == 15
    ammo = [card['id'] for card in cards]
    frame_response, = re.findall(r'“([^”]+)”', hearing.body[first_rule])
    tasks[task] = {'taskId': task, 'ready': True, 'requiresEvidence': ammo,
                   'stage': {'id': task, 'v4': True, 'kind': 'nonstop', 'title': '손이 두 번 보인 이유', 'lines': rows,
                             'options': cards, 'authoredAmmo': ammo, 'filterOwnedEvidence': True,
                             'wrongCards': {ammo[0]: 'frame-only', ammo[1]: 'loan-only'}},
                   'debate': {'id': task, 'kind': 'nonstop', 'title': '손이 두 번 보인 이유', 'lines': rows, 'bullets': cards},
                   'queues': {'wrongVariants': [
                       {'cause': cause, 'script': [{'id': task + ':' + cause, 'type': 'say', 'actor': SPEAKERS[speaker],
                                                   'speaker': speaker, 'text': text, 'source': card_source}]}
                       for cause, speaker, text in [('frame-only', '하루카', frame_response),
                                                    ('loan-only', '사츠키', '그건 처음에 빌려 간 사람 얘기야. 찍힌 손을 어디서 봤는지는 없잖아.')]]}}
    point_at = hearing.body.index('#### 지점 지목 — 화면의 오른팔')
    agree_at = hearing.body.index('#### 논스톱 동의 — 이름을 쓰고 건넨 칼')
    agree_rule = next(i for i,row in enumerate(hearing.body) if row.startswith('03-D01a 대여 표지와 직접 인계에'))
    next_round = hearing.body.index('#### 논스톱 — 종이를 찾은 손으로는')
    first_injury = scenes['03-T00a']
    injury_round = first_injury.body.index('#### 논스톱 — 바닥에서 혼자 부딪쳤다면')
    injury_rule = next(i for i,row in enumerate(first_injury.body) if row.startswith('03-I00a의 **첫 검안'))
    injury_choice = first_injury.body.index('#### 정답 선택 — 그때 이미 알고 있던 것은?')
    injury_ref = first_injury.source(first_injury.line+injury_rule+1)
    injury_card = {'id':'v4:V5-3:first-injury','name':'첫 검안과 작업대의 방향',
                   'text':'첫 발견의 날붙이 손상은 벽에만 부딪친 설명과 맞지 않는다. 직접 본 충돌과 마지막으로 종이를 찾은 손은 같은 순간이 아니다.'}
    status_card = {'id':'v4:V5-3:second-status','name':reports[2][1],'text':reports[2][2]}
    blade_card = {'id':'v4:V5-3:blade-stop','name':reports[1][1],'text':reports[1][2]}
    cloth_card = {'id':'v4:V5-3:cloth-handover','name':'천 전달과 벤치 쪽의 손',
                  'text':'유우는 문밖에서 받은 천을 아카리에게 돌려주었고 아카리가 안쪽의 쇼에게 가져갔다. 같은 때 나나는 벤치 옆에서 어깨를 받쳤고 쇼가 호흡을 다시 확인했다.'}
    later_records = {card['id']:card for card in [*cards,injury_card,status_card,blade_card,cloth_card]}
    later_records['v4:V5-3:index'] = {'id':'v4:V5-3:index','name':'작업대의 색인 위치',
        'text':'리쿠가 작업대에서 들어 올린 색인은 미오가 새로 쓴 문장과 별개다. 거울에 비친 종이에서 글을 읽을 수 없었다.'}
    later_records['v4:V5-3:movement'] = {
        'id':'v4:V5-3:movement','name':reports[0][1],
        'text':'칼을 든 팔이 벤치 쪽으로 돌아온 뒤 쇼가 손을 뻗었다. 쇼가 두 몸을 떼어 놓은 다음 레이가 붙들었다. 사츠키는 그 뒤 문밖으로 칼을 밀었다.'}
    paper_records = {
        'written-order':('새 문장의 작성 순서','하루카가 눈가리개의 틈과 각도를 확인한 뒤 미오가 처음 문장을 정해 썼다. 소라만 소리 없이 읽었고, 미오는 접은 뒤 나나에게 봉투에 넣어 맡겼다.'),
        'unread-sentence':('켄에게 전하지 않은 새 문장','켄은 눈가리개를 한 뒤 새 글을 보지 않았다. 봉투를 맡은 나나도 읽지 않았으며, 재판에서 펼치기 전에는 원문을 공개하지 않았다.'),
        'sealed-route':('접힌 봉투의 실제 인계','소라와 리쿠가 모퉁이 너머로 간 뒤 나나가 미오에게 접힌 봉투를 넘겼다. 미오가 가방 안쪽에 넣었다. 카메라는 이동하는 몸만 찍었으며 봉투와 원문은 찍지 않았다.'),
        'condition':('시연과 수첩의 점유 조건','새로 몸에 들어가는 조건, 정상 복귀, 본체 사망 뒤 이미 완전한 점유가 고정되는 조건을 구별한다. 같은 문구를 읽은 사실은 사건 당시 어느 조건이 충족됐는지 증명하지 않는다.'),
        'continuity':('몸의 연속 관찰과 진입 조건','하루카의 촬영 뒤 미오가 발언의 시작과 실제 이동을 직접 보았고, 사츠키가 같은 발언의 끝과 문턱을 이어 봤다. 레이는 입실 뒤부터 관찰했다. 힘이 빠진 것과 의식을 잃은 것은 다르며, 새 진입에 필요한 상태와 관찰을 함께 대조한다.'),
        'clock-bench':('기본 시간이 지난 시계와 벤치','벽시계는 기본 확인 시간을 지났지만 벤치의 몸은 일어나지 않았다. 나나가 어깨를 받쳤고, 첫 조사 뒤 쇼가 구조 전에 생존을 다시 확인했다. 시계가 지난 사실만으로 정상 복귀를 확인하지 못한다.'),
        'archive-pieces':('출동 기록 두 조각의 열람 번호','첫 조각 뒤의 다른 분류에서 같은 남자가 소라의 이름을 부른 뒤에도 안에서 움직이는 것을 확인했다. 그날 마지막 행방은 화면에 없다. 리쿠가 번호를 알고 있었다는 말과 영상을 모두 보고 무엇을 생각했는지는 별개다.'),
        'perception':('인식 시연과 글의 실제 열람','리쿠의 인식 효과 시연에서 몸과 사진은 그대로였다. 눈가리개 뒤 처음 작성된 문장을 실제로 읽은 위치는 따로 확인한다. 다른 이름으로 느끼는 효과만으로 새 문장의 내용을 얻었다고 할 수는 없다.'),
        'new-sentence':('지금 처음 공개한 원문','낡은 구두 속 파란새는 설탕을 숨긴다. 나나가 재판에서 처음 봉투를 펼쳤다. 미오가 먼저 거짓으로 읽은 문장은 이 원문에 포함되지 않는다.'),
    }
    for key,(name,text) in paper_records.items():
        ident = 'v4:V5-3:'+key
        later_records[ident] = {'id':ident,'name':name,'text':text}
    end = chapter_three_comic_and_vote(graph,scenes,tasks,later_records,dead,seats,end)
    end = chapter_three_paper_hearing(graph,scenes,tasks,later_records,dead,seats,end)
    paper_checkpoint = graph.add('rev:03:paper-court-entry',type='stage',enterCourt=True,next=end)
    continuity_checkpoint = graph.add('rev:03:continuity-court-entry',type='stage',enterCourt=True,
                                     next='rev:03:T3-QA-REV13')
    final_checkpoint = graph.add('rev:03:armament-court-entry',type='stage',enterCourt=True,
                                next='rev:03:T3-AA-REV01')
    victim_checkpoint = graph.add('rev:03:victim-court-entry',type='stage',enterCourt=True,
                                 next='rev:03:T3-PE-REV02')
    end = chapter_three_cloth_hearing(graph,scenes,tasks,later_records,dead,seats,end,knife_objects)
    later_checkpoint = graph.add('rev:03:cloth-court-entry',type='stage',enterCourt=True,next=end)
    timeline_checkpoint = graph.add('rev:03:timeline-court-entry',type='stage',enterCourt=True,next='rev:03:T3-PE-REV01')
    panic_checkpoint = graph.add('rev:03:handover-court-entry',type='stage',enterCourt=True,next='rev:03:T3-PN-REV02')

    def choice_section(scene, heading, line_at, stop, task_id, question, variants, records, target, *, prefix=0):
        ref = scene.source(scene.line+line_at+1)
        correct, = [index for index,(_,speaker,_) in enumerate(variants) if not speaker]
        tasks[task_id] = {'taskId':task_id,'ready':True,'requiresEvidence':[card['id'] for card in records],
            'stage':{'id':task_id,'v4':True,'kind':'choice','question':question,'answer':correct,
                     'options':[label for label,_,_ in variants]},
            'queues':{'wrongVariants':[{'optionIndex':i,'script':[{'id':f'{task_id}:{i}','type':'say',
                       'actor':SPEAKERS['켄' if speaker=='켄의 몸' else speaker],
                       'speaker':speaker,'text':reply,'source':ref}]}
                       for i,(_,speaker,reply) in enumerate(variants) if speaker]}}
        target = graph.lines(scene,line_at+1,stop,target)
        target = graph.add(f'rev:03:{task_id}',type='task',taskId=task_id,trialDead=dead,seats=seats,
                           source=ref,success=target,next=target)
        return graph.lines(scene,prefix,heading,target)

    second_hearing = scenes['03-T01']
    blade_at = second_hearing.body.index('#### 논스톱 — 칼이 멈춘 자리의 사람')
    blade_rule = next(i for i,row in enumerate(second_hearing.body) if row.startswith('03-I02의 실제 바닥 관찰'))
    anagram_at = second_hearing.body.index('#### 섬광 애너그램 — 두 번째 죽음 뒤에도')
    anagram_rule = next(i for i,row in enumerate(second_hearing.body) if row.startswith('질문 “이미 완전한'))
    anagram_id = 'T3-AN-REV01'
    anagram_source = second_hearing.source(second_hearing.line+anagram_rule+1)
    tasks[anagram_id] = {'taskId':anagram_id,'ready':True,'requiresEvidence':[status_card['id']],
        'stage':{'id':anagram_id,'v4':True,'kind':'anagram','chapter':3,'title':'두 번째 죽음 뒤에도',
                 'question':'이미 점유 중이던 몸에서 의식이 지속되는 상태는?',
                 'answer':'빙의고정','distractors':['귀','환','소','생','잠','금']},'queues':{}}
    target = graph.lines(second_hearing,anagram_rule+1,len(second_hearing.body),end)
    target = graph.add('rev:03:occupancy-anagram',type='task',taskId=anagram_id,trialDead=dead,seats=seats,
                       source=anagram_source,success=target,next=target)
    target = graph.lines(second_hearing,anagram_at+1,anagram_rule,target)
    joint_at = next(i for i,row in enumerate(second_hearing.body) if row.startswith('참가자들은 두 몸의 상태'))
    target = choice_section(second_hearing,joint_at,joint_at,anagram_at,'T3-QA-REV04',
        '두 몸의 상태가 함께 확인되는 구간은?',(
            ('첫 방송을 들은 직후','쇼','제 두 번째 확인은 방송을 들은 순간과 같지 않습니다.'),
            ('첫 사망 확인 이후, 두 번째 공격 전','',''),
            ('두 번째 공격 뒤','나나','제가 손을 놓은 건 호흡을 먼저 확인하고 난 뒤예요.')),
        [injury_card,status_card],target,prefix=blade_rule+1)
    blade_id = 'T3-NS-REV06'
    blade_source = second_hearing.source(second_hearing.line+blade_rule+1)
    blade_rows = []
    for offset in range(blade_at+1,blade_rule):
        if match := STMT.match(second_hearing.body[offset]):
            index,speaker,raw,_ = match.groups()
            blade_rows.append(debate_statement(blade_id,index,speaker,raw,second_hearing.source(second_hearing.line+offset+1),
                                               'weak' if index=='4' else 'plain',blade_card['id'] if index=='4' else ''))
    assert len(blade_rows)==14
    blade_cards = [cards[1],status_card,blade_card]
    tasks[blade_id] = {'taskId':blade_id,'ready':True,'requiresEvidence':[card['id'] for card in blade_cards],
        'stage':{'id':blade_id,'v4':True,'kind':'nonstop','title':'칼이 멈춘 자리의 사람','lines':blade_rows,
                 'options':blade_cards,'authoredAmmo':[card['id'] for card in blade_cards],'filterOwnedEvidence':True,
                 'wrongCards':{cards[1]['id']:'loan'}},
        'debate':{'id':blade_id,'kind':'nonstop','lines':blade_rows,'bullets':blade_cards},
        'queues':{'wrongVariants':[{'cause':'loan','script':[{'id':blade_id+':loan','type':'say','actor':'satsuki','speaker':'사츠키',
                   'text':'그건 처음 빌린 사람 얘기야. 내가 발로 밀기 전과 뒤를 같이 봐.','source':blade_source}]}]}}
    target = graph.add('rev:03:blade-stop-nonstop',type='task',taskId=blade_id,trialDead=dead,seats=seats,
                       source=blade_source,success=target,next=target)
    panic_at = second_hearing.body.index('#### 패닉 — 들어오는 사람, 들은 사람, 남은 사람')
    panic_rule = next(i for i,row in enumerate(second_hearing.body) if row.startswith('정답은 03-I02의 천 전달'))
    panic_id = 'T3-PN-REV01'
    lane_names = ('사츠키','레이','나나')
    lanes = [{'id':label,'actor':SPEAKERS[speaker],'speaker':speaker,'lines':[]}
             for label,speaker in zip(('왼쪽','가운데','오른쪽'),lane_names)]
    rows = []
    for offset in range(panic_at+1,panic_rule):
        cols = [part.strip() for part in second_hearing.body[offset].strip('|').split('|')]
        if len(cols)!=4 or not cols[0].isdigit():
            continue
        for index,(lane,raw) in enumerate(zip(lanes,cols[1:])):
            beat = int(cols[0])
            ref = second_hearing.source(second_hearing.line+offset+1)
            weak = (beat,index)==(4,1)
            row = debate_statement(panic_id,f'{index}:{beat}',lane['speaker'],raw.removesuffix(' 약점.'),ref,
                                   'weak' if weak else 'plain',cloth_card['id'] if weak else '')
            rows.append(row)
            lane['lines'].append(row['id'])
            if '[큰 소리]' in raw:
                noise = debate_statement(panic_id,'noise',lane['speaker'],raw,ref,'noise')
                noise.update(noiseRole='loud',noiseDurability=2,hostStatement=row['id'])
                rows.append(noise)
    assert len(rows)==13
    panic_cards = [injury_card,status_card,cloth_card]
    tasks[panic_id] = {'taskId':panic_id,'ready':True,'requiresEvidence':[card['id'] for card in panic_cards],
        'stage':{'id':panic_id,'v4':True,'kind':'panic','title':'들어오는 사람, 들은 사람, 남은 사람','lines':rows,
                 'options':panic_cards,'filterOwnedEvidence':True},
        'debate':{'id':panic_id,'kind':'panic','lines':rows,'bullets':panic_cards,'lanes':lanes,'synchronizedBeats':True},
        'queues':{}}
    target = graph.lines(second_hearing,panic_rule+1,blade_at,target)
    target = graph.add('rev:03:cloth-panic',type='task',taskId=panic_id,trialDead=dead,seats=seats,
                       source=second_hearing.source(second_hearing.line+panic_at+1),success=target,next=target)
    compare_at = second_hearing.body.index('#### 현장 대조 — 두 방에 적힌 같은 이름')
    compare_rule = next(i for i,row in enumerate(second_hearing.body) if row.startswith('플레이어는 03-I03b의 두 사진'))
    target = choice_section(second_hearing,compare_rule,compare_rule,panic_at,'T3-QA-REV03',
        '두 방의 기록을 서로 바꿔 놓지 않으려면?',(
            ('같은 서명이 있으므로 같은 시각에 놓는다','쇼','두 기록에 제가 썼다는 것 외에 시각까지 같은 것은 아닙니다.'),
            ('첫 검안과 방송 뒤 두 번째 방의 호흡을 놓는다','',''),
            ('두 번째 방송만 읽는다','나나','방송이 나오기 전에 누가 어느 방에 있었는지부터 보세요.')),
        [injury_card,status_card],target,prefix=compare_at+1)
    agree2_at = second_hearing.body.index('#### 논스톱 동의 — 두 번째로 확인한 몸')
    agree2_rule = next(i for i,row in enumerate(second_hearing.body) if row.startswith('정답 첫 수사 때의'))
    agree2_id = 'T3-NS-REV05'
    agree2_rows = []
    for offset in range(agree2_at+1,agree2_rule):
        if match := STMT.match(second_hearing.body[offset]):
            index,speaker,raw,_ = match.groups()
            row = debate_statement(agree2_id,index,speaker,raw,second_hearing.source(second_hearing.line+offset+1))
            if index=='4':
                word, = re.findall(r'\*\*([^*]+)\*\*',raw)
                row.update(kind='agree',agree=status_card['id'],agreeTarget={'word':word,'glyphStart':row['text'].index(word)})
            agree2_rows.append(row)
    assert len(agree2_rows)==14
    agree2_cards = [injury_card,cloth_card,status_card]
    agree2_source = second_hearing.source(second_hearing.line+agree2_rule+1)
    tasks[agree2_id] = {'taskId':agree2_id,'ready':True,'requiresEvidence':[card['id'] for card in agree2_cards],
        'stage':{'id':agree2_id,'v4':True,'kind':'nonstop','title':'두 번째로 확인한 몸','lines':agree2_rows,
                 'options':agree2_cards,'authoredAmmo':[card['id'] for card in agree2_cards],'filterOwnedEvidence':True,
                 'wrongCards':{injury_card['id']:'first-place'}},
        'debate':{'id':agree2_id,'kind':'nonstop','lines':agree2_rows,'bullets':agree2_cards},
        'queues':{'wrongVariants':[{'cause':'first-place','script':[{'id':agree2_id+':first-place','type':'say','actor':'nana',
                   'speaker':'나나','text':'처음 확인한 장소는 미로예요. 제가 숨을 확인한 곳은 대기실이고요.','source':agree2_source}]}]}}
    target = graph.lines(second_hearing,agree2_rule+1,compare_at,target)
    target = graph.add('rev:03:living-body-agreement',type='task',taskId=agree2_id,trialDead=dead,seats=seats,
                       source=agree2_source,success=target,next=target)
    picker_at = second_hearing.body.index('#### 증거 지목 — 검안표를 같은 사진에 붙이면')
    picker_rule = next(i for i,row in enumerate(second_hearing.body) if row.startswith('정답을 고르면 미로에서의 검안'))
    target = choice_section(second_hearing,picker_at,picker_rule,agree2_at,'T3-QA-REV05',
        '두 검안 기록을 구별할 때 먼저 대조할 자료는?',(
            ('각 기록의 장소와 실제 몸을 확인한 사람','',''),
            ('첫 발견 방송의 시각','미오','그때 확인한 건 첫 현장이야. 대기실에서 누가 살아 있었는지는 따로 봐.'),
            ('몸이 돌아왔다는 말','켄의 몸','내가 그렇게 말한다고 저기 누운 사람이 숨을 쉰 거야?'),
            ('대기실 사진 한 장','나나','멈춘 사진에서는 숨을 못 봐요. 쇼 씨가 오셨을 때 제 손이 있던 곳을 보세요.')),
        [injury_card,status_card],target)
    between = scenes['03-T00b']
    area_at = between.body.index('### 구역 지목 — 막는 동안 누가 안에 있나')
    area_rule = next(i for i,row in enumerate(between.body) if row.startswith('- **현재 재판석.**'))
    target = choice_section(between,area_at,area_rule,len(between.body),'T3-QA-REV02',
        '미로를 막아도 안전 여부를 따로 확인할 곳은?',(
            ('미로 밖 대기실','',''),
            ('작업대 쪽 실제 통로','하루카','미로를 막아도 대기실의 몸이 일어날 수 있는지는 안 바뀌어.'),
            ('현재 재판석','레이','여기 문을 닫는다고 그때 대기실 앞에 계신 분이 달라지지 않습니다.')),
        [status_card],target)
    task_id = 'T3-QA-REV01'
    tasks[task_id] = {'taskId':task_id,'ready':True,'requiresEvidence':[injury_card['id']],
        'stage':{'id':task_id,'v4':True,'kind':'choice','question':'검안과 현장 사진을 맞춰도 남는 사실은?',
                 'answer':0,'options':['실제 날붙이 손상이 있음','대여 뒤 손잡이를 누가 먼저 잡았는지 확정','공격 순간의 칼날 방향을 사진으로 확인']},
        'queues':{'wrongVariants':[{'optionIndex':index,'script':[{'id':f'{task_id}:{index}','type':'say',
                    'actor':SPEAKERS[actor],'speaker':actor,'text':line,'source':injury_ref}]}
                 for index,actor,line in ((1,'미오','팔이 부딪치는 건 봤어. 그때 손가락까지는 안 보였어.'),
                                          (2,'하루카','그 사진은 그 뒤에 찍었어. 처음에 어느 쪽으로 날이 갔는지는 거기 안 나와.'))]}}
    tail = graph.lines(first_injury,injury_choice+2,len(first_injury.body),target)
    tail = graph.add('rev:03:first-injury-choice',type='task',taskId=task_id,trialDead=dead,seats=seats,
                     source=injury_ref,success=tail,next=tail)
    tail = graph.lines(first_injury,injury_rule+1,injury_choice,tail)
    split = [
        (hearing,next_round,'03-I00a의 첫 충돌과', '종이를 찾은 손으로는','T3-NS-REV03',
         cards[1], '켄의 몸','걔가 들고 나왔다는 건 앞의 일이잖아. 여기서 내가 뭘 봤는지하고는 달라'),
        (first_injury,injury_round,'03-I00a의 **첫 검안','바닥에서 혼자 부딪쳤다면','T3-NS-REV04',
         cards[0],'하루카','종이에서 마지막으로 보인 건 위치였어. 처음 다친 때의 자료부터 봐.'),
    ]
    for scene,heading,rule_start,title,task_id,decoy,actor,reply in reversed(split):
        rule = next(i for i in range(heading,len(scene.body)) if scene.body[i].startswith(rule_start))
        ref = scene.source(scene.line+rule+1)
        shot_cards = [decoy, cards[2], injury_card]
        ids = [card['id'] for card in shot_cards]
        rows = []
        for offset in range(heading+1,rule):
            if match := STMT.match(scene.body[offset]):
                index,name,raw,_ = match.groups()
                rows.append(debate_statement(task_id,index,name,raw,scene.source(scene.line+offset+1),
                                             'weak' if index=='4' else 'plain',ids[-1] if index=='4' else ''))
        assert sum('weak' in row for row in rows)==1
        if task_id.endswith('04'):
            row = next(row for row in rows if 'weak' in row)
            row['vpoint'] = {'glyphIndex':row['weak']['start']+row['weak']['word'].index('벽에')}
        tasks[task_id] = {'taskId':task_id,'ready':True,'requiresEvidence':ids,
            'stage':{'id':task_id,'v4':True,'kind':'nonstop','title':title,'lines':rows,
                     'options':shot_cards,'authoredAmmo':ids,'filterOwnedEvidence':True,'wrongCards':{decoy['id']:'wrong-time'}},
            'debate':{'id':task_id,'kind':'nonstop','lines':rows,'bullets':shot_cards},
            'queues':{'wrongVariants':[{'cause':'wrong-time','script':[{'id':task_id+':wrong-time','type':'say',
                      'actor':SPEAKERS['켄' if actor=='켄의 몸' else actor],'speaker':actor,'text':reply,'source':ref}]}]}}
        if scene is hearing:
            tail = graph.lines(scene,rule+1,len(scene.body),tail)
        tail = graph.add(f'rev:03:{task_id}',type='task',taskId=task_id,trialDead=dead,seats=seats,
                         source=ref,success=tail,next=tail)
        if scene is first_injury:
            tail = graph.lines(scene,0,heading,tail)
    agree_id = 'T3-NS-REV02'
    agree_source = hearing.source(hearing.line+agree_rule+1)
    agree_rows = []
    for offset in range(agree_at+1,agree_rule):
        if match := STMT.match(hearing.body[offset]):
            index,actor,raw,_ = match.groups()
            row = debate_statement(agree_id,index,actor,raw,hearing.source(hearing.line+offset+1))
            if index == '5':
                word, = re.findall(r'\*\*([^*]+)\*\*',raw)
                row.update(kind='agree',agree=ammo[1],agreeTarget={'word':word,'glyphStart':row['text'].index(word)})
            agree_rows.append(row)
    assert len(agree_rows) == 14
    tasks[agree_id] = {'taskId':agree_id,'ready':True,'requiresEvidence':ammo,
        'stage':{'id':agree_id,'v4':True,'kind':'nonstop','title':'이름을 쓰고 건넨 칼','lines':agree_rows,
                 'options':cards,'authoredAmmo':ammo,'filterOwnedEvidence':True,
                 'wrongCards':{ammo[0]:'photo-only',ammo[2]:'sightline-only'}},
        'debate':{'id':agree_id,'kind':'nonstop','lines':agree_rows,'bullets':cards},
        'queues':{'wrongVariants':[{'cause':key,'script':[{'id':f'{agree_id}:{key}','type':'say',
                  'actor':'haruka','speaker':'하루카','text':line,'source':agree_source}]}
                 for key,line in (
                     ('photo-only','내가 처음 찍은 건 물건 빌린 자리보다 뒤야.'),
                     ('sightline-only','길에서 손을 본 건 그다음이야. 처음 건넬 때 같이 봤던 기록을 내야지.'))]}}
    trial = graph.lines(hearing,agree_rule+1,next_round,tail)
    trial = graph.add('rev:03:loan-agreement',type='task',taskId=agree_id,trialDead=dead,seats=seats,
                      source=agree_source,success=trial,next=trial)
    trial = graph.lines(hearing,point_at+2,agree_at,trial)
    point_id = 'T3-SP-REV01'
    point_source = hearing.source(hearing.line+point_at+2)
    image = MINE_ART+'mirror-plan.svg'
    spots = [('glass','카메라의 반사면',(.096,.33,.263,.57),'haruka','하루카','거기엔 유리만 있었어.'),
             ('corner','작업대 앞의 관찰 모퉁이',(.46,.35,.568,.57),'','',''),
             ('bench','대기실 벤치',(.71,.39,.896,.52),'nana','나나','제가 몸을 확인한 건 여기서 더 뒤의 일이에요.')]
    tasks[point_id] = {'taskId':point_id,'ready':True,'requiresEvidence':[ammo[2]],
        'stage':{'id':point_id,'v4':True,'kind':'spot','question':'화면과 달리 실제 어깨를 직접 본 쪽은?',
                 'image':image,'answerRegionId':'corner','regions':[
                     {'id':key,'label':label,'wrongVariant':key,'polygon':[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]}
                     for key,label,(x0,y0,x1,y1),*unused in spots]},
        'queues':{'wrongVariants':[{'cause':key,'script':[{'id':f'{point_id}:{key}','type':'say','actor':actor,
                 'speaker':speaker,'text':line,'source':point_source}]} for key,_,_,actor,speaker,line in spots if actor]}}
    trial = graph.add('rev:03:direct-right-arm',type='task',taskId=point_id,trialDead=dead,seats=seats,
                      source=point_source,success=trial,next=trial)
    mine_id = 'T3-MM-REV01'
    mine_source = hearing.source(hearing.line+mine_heading+2)
    mine_regions = [('mirror-corner','작업대 통로로 나오는 모퉁이','',''),
                    ('mirror-bench','대기실 안쪽 벤치','나나','제가 거기서 본 건 다른 때예요. 먼저 있었던 일을 제가 보았다는 말은 하지 않았어요.'),
                    ('mirror-wall','작업대 뒤 벽','레이','반사가 닿는 면은 있습니다. 그 면을 통과할 통로는 보이지 않습니다.'),
                    ('mirror-gate','미로 입구 밖','사츠키','그건 나온 뒤에 돌아보던 쪽이야. 어디서부터 얼굴을 유리 말고 직접 봤는지 골라.')]
    tasks[mine_id] = {'taskId':mine_id,'ready':True,'requiresEvidence':[ammo[0],ammo[2]],
        'stage':{'id':mine_id,'v4':True,'kind':'mindmine','title':'반사면에서 실제 통로로',
                 'question':'반사 속 모습과 실제 어깨를 함께 볼 수 있는 곳은?','image':image,'mineObjects':mirror_objects,
                 'answerRegionId':'mirror-corner','regions':[
                     {'id':key,'label':name,'correct':not actor,'wrongVariant':key} for key,name,actor,_ in mine_regions]},
        'queues':{'wrongVariants':[{'cause':key,'script':[{'id':f'{mine_id}:{key}','type':'say','actor':SPEAKERS[actor],
                 'speaker':actor,'text':line,'source':mine_source}]} for key,_,actor,line in mine_regions if actor]}}
    trial = graph.add('rev:03:mirror-physical-match',type='document',title='반사와 실제 관찰의 경계',
                      rows=['모퉁이에서 유리 속 옆모습이 남을 때 실제 어깨가 기둥 밖으로 나온다. 손에 쥔 물건과 몸을 움직인 사람은 여기서 확정되지 않는다.'],
                      image=image,source=mine_source,next=trial)
    trial = graph.add('rev:03:mirror-mine',type='task',taskId=mine_id,trialDead=dead,seats=seats,
                      source=mine_source,success=trial,next=trial)
    trial = graph.lines(hearing, first_rule + 1, mine_heading, trial)
    trial = graph.add('rev:03:reflection-nonstop', type='task', taskId=task, trialDead=dead, seats=seats,
                      source=card_source, success=trial, next=trial)
    classifications_end = next(i for i, raw in enumerate(hearing.body) if raw.startswith('세 관찰을 제대로 놓으면'))
    trial = graph.lines(hearing, classifications_end + 1, first_round, trial)
    classify_at = next(i for i, raw in enumerate(hearing.body) if raw.startswith('플레이어는 03-D01e'))
    recheck = scenes['03-I03']
    recheck_at = next(i for i, raw in enumerate(recheck.body) if raw.startswith('가방 쪽에서 첫 현장으로'))
    card = cards[2]
    observation = graph.add('rev:03:comparison-record', type='evidence', evidenceId=card['id'], name=card['name'],
                            text=card['text'], source=recheck.source(recheck.line + recheck_at + 1), next=trial)
    questions = [
        ('눈앞에서 다른 이름을 먼저 부른 장면은 무엇으로 설명할까?', '인식이 바뀐 사전 시연',
         '다른 몸으로 옮겨 간 결과', '미오', '오른쪽에 계속 서 있던 건 소라였어. 내가 다르게 불렀을 때도 거기 있었어.'),
        ('목소리의 주인이 그 말을 기억하지 못한 건 어느 관찰에서 나왔을까?', '몸을 빌린 시연과 복귀',
         '카메라가 가린 사각', '사츠키', '몸을 빌렸던 쪽부터 봐. 사진만 보고 그때 누가 말했는지 고를 수는 없어.'),
        ('같은 얼굴이 두 사진에 남았다면 무엇까지 확인할까?', '몸의 모습만 확인한다',
         '사진 속 몸을 움직인 사람을 확정한다', '하루카', '그 사진만 보면 누가 먼저 몸 안에서 말했는지 내가 그때 들은 말은 없잖아.'),
    ]
    for index, (q, correct, wrong, speaker, reply) in reversed(list(enumerate(questions))):
        ident = f'rev:03:classify:{index}'
        ref = hearing.source(hearing.line + classify_at + 1)
        retry = graph.add(ident + ':retry', type='say', actor=SPEAKERS[speaker], speaker=speaker, text=reply,
                          source=ref, next=ident)
        picks = [{'id': 'supported', 'label': correct, 'to': observation}, {'id': 'unsupported', 'label': wrong, 'to': retry}]
        if index != 1:
            picks.reverse()
        observation = graph.add(ident, type='menu', q=q, options=picks, source=ref)
    opening_entry = graph.lines(hearing, 0, classify_at, observation)
    opening_entry = graph.lines(opening, 0, len(opening.body), opening_entry)
    court_entry = graph.add('rev:03:court-entry', type='stage', enterCourt=True, next=opening_entry)
    cloth_at = next(i for i,row in enumerate(second.body) if '천' in row and '아카리' in row)
    later_spots.append(spot(second,'V5-3:cloth-handover',cloth_card['name'],cloth_card['text'],
                            'mirror_waiting',[.25,1.15,1.75],cloth_at,
                            lambda target: graph.add('rev:03:cloth-observation',type='say',actor='akari',
                               speaker='아카리',text='제가 천을 받은 건 문가였어요. 그때 나나 씨는 벤치에서 손을 떼지 않으셨고요.',
                               source=second.source(second.line+cloth_at+1),next=target)))
    custody = scenes['03-I03e']
    custody_choice = custody.body.index('### 앞으로 누가 봉투를 가지고 갈까')
    custody_join = custody.body.index('### 함께 가져갈 때')
    custody_starts = [i for i,row in enumerate(custody.body[custody_choice:custody_join],custody_choice)
                     if row.startswith(('**코토에게 맡기고','**가방은 미오가','**못 믿겠다고 직접'))]
    assert len(custody_starts)==3
    court_route = graph.lines(custody,custody_join+1,len(custody.body),court_entry)
    court_route = graph.menu(custody,'재판까지 봉투를 어떻게 가지고 갈까?',[
        (custody.body[at].strip('*'),at+1,custody_starts[i+1] if i<2 else custody_join,'')
        for i,at in enumerate(custody_starts)],court_route)
    court_route = graph.lines(custody,0,custody_choice,court_route)

    def paper_spot(scene,key,keys,name,pos,dialogue):
        origins = {
            'written-order':('03-D02','동의 뒤 켄은 눈가리개를'),
            'unread-sentence':('03-D02','동의 뒤 켄은 눈가리개를'),
            'sealed-route':('03-D03','소라와 리쿠가 문밖으로 나간 뒤'),
            'perception':('03-D02','리쿠는 앞에서 시연한 자신의 인식'),
            'continuity':('03-I03a','열지 않은 봉투, 각자'),
            'clock-bench':('03-D03','대기실 쪽에서 나나가 몸이 아직'),
            'condition':('03-I03i','- **문구를 래피의 답과'),
        }
        def read(target):
            for suffix in reversed(keys):
                card = later_records['v4:V5-3:'+suffix]
                source_scene,anchor = origins[suffix]
                current = scenes[source_scene]
                at = next(i for i,row in enumerate(current.body) if row.startswith(anchor))
                target = graph.add(f'rev:03:paper-record:{suffix}',type='evidence',evidenceId=card['id'],
                    name=card['name'],text=card['text'],source=current.source(current.line+at+1),next=target)
            return dialogue(target)
        card = later_records['v4:V5-3:'+keys[0]]
        return spot(scene,'V5-3:'+key,name,card['text'],'mirror_waiting',pos,0,read)

    original = scenes['03-D02']
    transfer = scenes['03-I03a']
    def compare_paper(target):
        compare = transfer.body.index('### 들을 수 있는 자리와 글을 볼 수 있는 자리')
        target = graph.lines(transfer,compare+1,len(transfer.body),target)
        menu = 'rev:03:paper-observation-separation'
        replies = (
            ('미오','사진이 끊긴 곳과 내가 보던 위치를 따로 놓자. 사츠키가 같은 발언을 이어 들은 때도 있어.'),
            ('코토','몸이 움직인 걸 보는 동안에도 사람이 옆에서 말할 수 있죠. 누가 가까이 갔는지를 보여 주세요.'),
        )
        options = []
        for i,(actor,text) in enumerate(replies):
            retry = graph.add(menu+':retry:'+str(i),type='say',actor=SPEAKERS[actor],speaker=actor,text=text,
                source=transfer.source(transfer.line+compare+1),next=menu)
            options.append({'id':str(i),'label':('카메라가 끝난 모퉁이에서 몸이 한동안 사라짐',
                                               '몸이 보였으니 봉투 내용을 알 길이 없음')[i],'to':retry})
        options.append({'id':'separate','label':'몸의 이동과 뒤에 전달된 말을 다른 표에서 확인','to':target})
        target = graph.add(menu,type='menu',q='시야와 내용을 어디까지 연결할까?',options=options,
            source=transfer.source(transfer.line+compare+1))
        target = graph.lines(transfer,0,compare,target)
        return graph.add('rev:03:experiment-order-review',type='document',title='새 문장을 쓴 순서',
            rows=[paper_records[key][1] for key in ('written-order','unread-sentence','sealed-route')],
            source=original.source(original.line),next=target)
    later_spots.append(paper_spot(original,'written-order',
        ['written-order','unread-sentence','sealed-route','perception','continuity','clock-bench'],
        '시연과 접힌 봉투의 경로',[-2.35,1.15,-1.3],compare_paper))
    notebook = scenes['03-I03i']
    notebook_choice = notebook.body.index('### 발견한 순서를 맞춘다')
    notebook_after = next(i for i in range(notebook_choice,len(notebook.body)) if SAY.match(notebook.body[i]))
    notebook_choices = [(i,BULLET.match(row)[1]) for i,row in enumerate(notebook.body[notebook_choice:notebook_after],notebook_choice)
                        if BULLET.match(row)]
    assert len(notebook_choices)==4
    def compare_condition(target):
        target = graph.lines(notebook,notebook_after,len(notebook.body),target)
        menu = 'rev:03:notebook-conditions'
        responses = (
            ('미오','현장에서 접혀 있던 모양과 펼쳐 읽은 뒤를 따로 남길게. 이걸로 누가 미리 계획했다고 하지는 않을게.'),
            ('쇼','정상 복귀와 조건부 고정은 다른 항목입니다. 사건에서 무엇이 충족됐는지는 두 몸의 상태와 대조하십시오.'),
            ('코토','여기서 읽으셔야 하는 건 같은 조건이 적힌 부분까지예요.'),
            ('나나','사진에는 사람이 나와 있지 않아요. 실제 공격을 본 분의 기록을 따로 봐 주세요.'),
        )
        options = []
        for i,((at,label),(actor,text)) in enumerate(zip(notebook_choices,responses)):
            flag = '03-I03i:'+str(i)
            reply = graph.add(menu+':'+str(i),type='say',actor=SPEAKERS[actor],speaker=actor,text=text,
                source=notebook.source(notebook.line+at+1),set={flag:True},next=menu)
            options.append({'id':str(i),'label':label,'to':reply,'requires':{flag:False}})
        options.append({'id':'continue','label':'현장과 조건을 구분해 기록한다','to':target,
                        'requires':{'03-I03i:0':True,'03-I03i:1':True}})
        target = graph.add(menu,type='menu',q='수첩에서 확인할 수 있는 것은?',options=options,
                           source=notebook.source(notebook.line+notebook_choice+1))
        return graph.lines(notebook,0,notebook_choice,target)
    later_spots.append(paper_spot(notebook,'condition',['condition'],'시연 조건이 적힌 수첩',[2.15,1.0,1.0],compare_condition))
    fragments = scenes['03-I03f']
    fragments_choice = fragments.body.index('### 다음에 읽을 항목을 고른다')
    fragments_after = next(i for i in range(fragments_choice,len(fragments.body)) if SAY.match(fragments.body[i]))
    fragments_choices = [(i,BULLET.match(row)[1]) for i,row in enumerate(fragments.body[fragments_choice:fragments_after],fragments_choice)
                         if BULLET.match(row)]
    assert len(fragments_choices)==3
    def compare_fragments(target):
        target = graph.lines(fragments,fragments_after,len(fragments.body),target)
        menu = 'rev:03:archive-fragment-boundaries'
        views = (
            ('하루카','소라가 멈춘 곳은 여기야. 그때 네가 못 본 다음 장면까지 봤다고 옮기지는 않을게.'),
            ('코토','남자가 다시 움직인 마지막 프레임은 여기예요. 아이가 화면 밖으로 간 뒤 어디에 있었는지까지 채우지는 않을게요.'),
            ('미오','같은 분류 안의 두 조각을 찾았어. 리쿠가 이 번호를 갖고 있었다고 나중 행동을 전부 안다고 할 수는 없어.'),
        )
        options = []
        for i,((at,label),(actor,text)) in enumerate(zip(fragments_choices,views)):
            flag = '03-I03f:'+str(i)
            reply = graph.add(menu+':'+str(i),type='say',actor=SPEAKERS[actor],speaker=actor,text=text,
                source=fragments.source(fragments.line+at+1),set={flag:True},next=menu)
            options.append({'id':str(i),'label':label,'to':reply,'requires':{flag:False}})
        options.append({'id':'continue','label':'두 조각과 번호의 범위를 따로 남긴다','to':target,
                        'requires':{'03-I03f:'+str(i):True for i in range(3)}})
        target = graph.add(menu,type='menu',q='기록에서 실제로 확인할 수 있는 범위',options=options,
            source=fragments.source(fragments.line+fragments_choice+1))
        return graph.lines(fragments,0,fragments_choice,target)
    archive_card = later_records['v4:V5-3:archive-pieces']
    later_spots.append(spot(fragments,'V5-3:archive-pieces',archive_card['name'],archive_card['text'],
        'record_room',[.2,1.2,1.4],0,compare_fragments))
    after = hub('rev:03:second-investigation', 'mirror_waiting', later_spots, court_route)
    second_announcement = next(i for i, line in enumerate(second.body) if line.startswith('쇼가 응급 확인을 멈추고'))
    after = graph.add('rev:03:second-announcement', type='say', actor='mio', speaker='미오', mono=True,
                      text='나나와 함께 그 몸을 보고 있었다. 쇼가 사망을 확인하고 나서 두 번째 발견 방송이 나왔다.',
                      source=second.source(second.line + second_announcement + 1),
                      presentation={'actions': ['body_announcement']}, next=after)
    impact = next(i for i, line in enumerate(second.body) if line.startswith('쇼가 숨이 여전히 이어짐을'))
    after = graph.lines(second, impact + 1, second_announcement, after)
    after = graph.add('rev:03:second-impact', type='say', actor='mio', speaker='미오', mono=True,
                      text='쇼가 어깨를 받으려는 순간, 켄의 몸이 다시 앞으로 돌았다. 칼이 벤치 위로 들어왔다.',
                      source=second.source(second.line + impact + 1), next=after)
    after = graph.lines(second, 0, impact, after)
    after = chapter_three_waiting(graph,scenes,after)
    first_question = [i for i, line in enumerate(interval.body) if BULLET.match(line)]
    assert len(first_question) == 2
    after = graph.lines(interval, first_question[-1] + 1, len(interval.body), after)
    responses = {}
    for offset, name in zip(first_question, ('쇼', '나나')):
        label, line = BULLET.match(interval.body[offset]).groups()
        text, = re.findall(r'“([^”]+)”', line)
        responses[name] = (label, text, interval.source(interval.line + offset + 1))
    options = []
    for code, order in zip(('A', 'B'), (('쇼', '나나'), ('나나', '쇼'))):
        to = after
        for name in reversed(order):
            _, text, source = responses[name]
            to = graph.add(f'rev:03:witness:{code}:{SPEAKERS[name]}', type='say', actor=SPEAKERS[name],
                           speaker=name, text=text, source=source, next=to)
        options.append({'id': code, 'label': responses[order[0]][0], 'to': to, 'set': {'03-I01:order': code}})
    after = graph.add('rev:03:living-observation-choice', type='menu', q='어느 확인부터 들을까?', options=options)
    after = graph.lines(interval, 0, first_question[0], after)
    after = supplemental_inspection(graph,scenes,['03-I00f','03-I01h'],after)
    after = graph.add('rev:03:separate-living-observation', type='stage', next=after,
                      scene={'space': 'mirror_waiting', 'perspective': 'current-observation'})

    inspections = [i for i, line in enumerate(first.body) if line.startswith('### 조사 지점 ')]
    assert len(inspections) == 3
    first_spots = []
    exhibits = (
        ('V5-3:reflection', '반사면과 직접 관찰 방향', '카메라 프레임에서 기둥 하나가 가려졌다. 반사에 나타난 쪽과 미오가 서서 직접 본 통로의 방향을 구별한다.', [-3.8, 1.3, -1.0]),
        ('V5-3:index', '작업대의 색인 위치', '색인의 끝을 당기는 것은 보였지만 뒤집힌 면에 손이 닿았는지는 확인되지 않았다. 거울에 비친 종이에서 글을 읽을 수 없다.', [1.0, 1.2, 1.2]),
        ('V5-3:loan', '공용 대여 행', '공방에서 처음 가져갈 때 남긴 표식과 대여 기록이다. 첫 현장에서는 칼을 회수하지 않았고, 거울 너머 손에서 같은 번호를 읽지 않았다.', [-1.2, 1.2, .4]),
    )
    for index, (key, name, facts, pos) in enumerate(exhibits):
        start = inspections[index]
        stop = inspections[index + 1] if index + 1 < len(inspections) else len(first.body)
        first_spots.append(spot(first, key, name, facts, 'mirror_workbay', pos, start,
                                lambda target, start=start, stop=stop: graph.lines(first, start + 1, stop, target)))
    first_exam = scenes['03-I00a']
    first_spots.append(spot(first_exam,'V5-3:first-injury',injury_card['name'],injury_card['text'],
                            'mirror_workbay',[2.15,1.18,-.65],0,
                            lambda target: graph.lines(first_exam,0,len(first_exam.body),target)))
    entry = hub('rev:03:first-investigation', 'mirror_workbay', first_spots, after)
    death = scenes['03-D04']
    entry = graph.add('rev:03:first-announcement', type='say', actor='mio', speaker='미오', mono=True,
                      text='레이와 나나가 대기실에 남았다. 첫 발견 방송을 듣고 미로로 돌아왔다.',
                      source=death.source(death.line + len(death.body)), presentation={'actions': ['body_announcement']}, next=entry)
    impact = next(i for i, line in enumerate(death.body) if line.startswith('미오가 서 있던 오른쪽 시야에서'))
    entry = graph.lines(death, impact + 1, len(death.body), entry)
    entry = graph.add('rev:03:first-impact', type='say', actor='mio', speaker='미오', mono=True,
                      text='오른쪽에서 두 팔이 부딪치는 게 보였다. 보라색이 번지고 나서야 칼끝이 전과 다른 데 있다는 걸 알아차렸다.',
                      source=death.source(death.line + impact + 1), next=entry)
    entry = graph.lines(death, 0, impact, entry)
    incident = graph.add('rev:03:incident', type='stage', next=entry,
                         scene={'space': 'mirror_workbay', 'perspective': 'current-observation'},
                         presentation={'music': {'operation': 'play', 'cue': 'bgm_tense'}})
    entry = incident
    for scene_id, space in reversed((('03-D02', 'mirror_maze'), ('03-D03', 'mirror_waiting'))):
        daily = scenes[scene_id]
        if scene_id=='03-D02':
            writing = next(i for i,row in enumerate(daily.body) if row.startswith('동의 뒤 켄은 눈가리개를'))
            entry = graph.lines(daily,writing+1,len(daily.body),entry)
            entry = graph.add('rev:03:write-after-blindfold',type='say',actor='mio',speaker='미오',mono=True,
                text='하루카가 눈가리개 아래의 틈을 확인했다. 그 뒤에 처음 문장을 정해 소라에게만 보여 주었다. 소리 내어 읽지는 않았다. 접은 종이를 나나가 봉투에 넣었다.',
                source=daily.source(daily.line+writing+1),next=entry)
            entry = graph.lines(daily,0,writing,entry)
        else:
            handover = next(i for i,row in enumerate(daily.body) if row.startswith('소라와 리쿠가 문밖으로 나간 뒤'))
            late = next(i for i,row in enumerate(daily.body) if row.startswith('대기실 쪽에서 나나가 몸이 아직'))
            entry = graph.lines(daily,late+1,len(daily.body),entry)
            entry = graph.add('rev:03:unreturned-body',type='say',actor='mio',speaker='미오',mono=True,
                text='기본 확인 시간이 지났는데 대기실의 몸이 일어나지 않았다. 나나가 부르는 쪽으로 대답할 자리를 옮겼다. 하루카는 거울 앞에 남았다.',
                source=daily.source(daily.line+late+1),next=entry)
            entry = graph.lines(daily,handover+1,late,entry)
            entry = graph.add('rev:03:unopened-handover',type='say',actor='mio',speaker='미오',mono=True,
                text='두 사람이 모퉁이를 돌아간 뒤 나나가 봉투를 건넸다. 접힌 채로 받아 가방에 넣었다. 카메라에는 이동하는 두 사람만 잡혔다.',
                source=daily.source(daily.line+handover+1),next=entry)
            entry = graph.lines(daily,0,handover,entry)
        entry = graph.add(f'rev:{scene_id}:entry', type='stage', next=entry, source=daily.source(daily.line),
                          scene={'space': space, 'perspective': 'current-observation'})
    entry = chapter_three_daily_conditions(graph,scenes,entry)
    entry=life_route(graph,scenes,['03-D01u'],entry)
    experiment = scenes['03-D01e']
    callback = experiment.body.index('### 아까 누구 차례였어')
    endings = [experiment.body.index(f'#### {branch} 경로') for branch in 'ABC']
    branches = []
    for branch, first, last in zip('ABC', endings, [*endings[1:], len(experiment.body)]):
        to = graph.lines(experiment, first + 1, last, entry)
        branches.append({'flag': '03-D01j', 'equals': branch, 'to': to})
    entry = graph.add('rev:03:card-game-callback', type='branch', default=entry, cases=branches)
    entry = graph.lines(experiment, 0, callback, entry)
    entry = graph.add('rev:03:experiment', type='stage', next=entry, source=experiment.source(experiment.line),
                      scene={'space': 'mirror_maze', 'perspective': 'current-observation'})
    entry=life_route(graph,scenes,['03-D01l'],entry)
    card_game = scenes['03-D01j']
    join = card_game.body.index('### 문이 열릴 때')
    paths = [(i, raw[8:]) for i, raw in enumerate(card_game.body[:join]) if re.match(r'^#### [ABC]\. ', raw)]
    assert len(paths) == 3
    common = card_game.body.index('**C.**') + 1
    # The join's three alternative recollections are replayed only by the selected branch.
    entry = graph.lines(card_game, common, len(card_game.body), entry)
    entry = graph.menu(card_game, '나나가 카드를 내기 전에 어떻게 할까?',
                       [(label, index + 1, end, '') for (index, label), (end, _) in zip(paths, [*paths[1:], (join, '')])],
                       entry)
    entry = graph.lines(card_game, 0, paths[0][0], entry)
    entry = graph.add('rev:03:card-table', type='stage', next=entry, source=card_game.source(card_game.line),
                      scene={'space': 'mirror_maze', 'perspective': 'current-observation'})
    daily_ids=[ident for ident in scenes if ident.startswith('03-D')]
    entry=life_route(graph,scenes,daily_ids[:daily_ids.index('03-D01j')],entry)
    before_open = [card for key,card in later_records.items() if key!='v4:V5-3:new-sentence']
    archive_end=graph.add('rev:03:archive-inspection-end',type='end')
    archive_checkpoint=hub('rev:03:archive-inspection','record_room',[later_spots[-1]],archive_end)
    return ({'schemaVersion': 1, 'contentVersion': 'v4', 'campaignRevision': 'rewrite-v5', 'chapter': '3',
             'entry': entry, 'nodes': graph.nodes, 'trialRoster': {'dead': dead, 'seats': seats},
             'qaCheckpoints': {'incident': {'entry': incident, 'evidence': []},
                               'archive-inspection':{'entry':archive_checkpoint,'evidence':[]},
                               'later-hearing': {'entry':later_checkpoint,'evidence':before_open},
                               'timeline-hearing': {'entry':timeline_checkpoint,'evidence':before_open},
                               'handover-hearing': {'entry':panic_checkpoint,'evidence':before_open},
                               'paper-hearing': {'entry':paper_checkpoint,'evidence':before_open},
                               'armament-hearing': {'entry':final_checkpoint,'evidence':list(later_records.values())},
                               'victim-hearing': {'entry':victim_checkpoint,'evidence':list(later_records.values())},
                               'vote-hearing': {'entry':'rev:03:vote-court-entry','evidence':list(later_records.values())},
                               **({'comic-hearing':{'entry':'rev:03:comic-court-entry','evidence':list(later_records.values())}}
                                  if 'T3-CM-REV01' in tasks else {}),
                               'continuity-hearing': {'entry':continuity_checkpoint,'evidence':list(later_records.values())}}}, tasks)


def chapter_four_book_checkpoints(graph,scenes,tasks,evidence,dead,seats):
    """The reviewed closing book is QA-accessible until the preceding hearing is routed."""
    comic=chapter_four_comic_stage()
    if comic is None:return {}
    assert all((ROOT/f'art/revision_comic/chapter4/verdict-{i:02}.webp').is_file() for i in range(1,5))
    complete=graph.add('rev:04:complete',type='end',chapterComplete=True,nextChapter='5')
    scene=scenes['04-R01'];personal=scene.body.index('### 사람이 나오는 사진')
    starts=[i for i,row in enumerate(scene.body) if row.startswith('04-D00o에서')]
    assert len(starts)==3
    join=next(i for i,row in enumerate(scene.body) if row.startswith('세 경로 모두 개인 사진'))
    after=graph.lines(scene,join+1,len(scene.body),complete)
    cases=[]
    for flag,at,stop in zip('BAC',starts,[*starts[1:],join]):
        cases.append({'flag':'04-D00o','equals':flag,'to':graph.lines(scene,at+1,stop,after)})
    after=graph.add('rev:04:personal-photo-memory',type='branch',cases=cases,default=after)
    after=graph.lines(scene,personal+1,starts[0],after)
    memory=next(i for i,row in enumerate(scene.body) if row.startswith('04-F01에서'))
    wait=next(i for i,row in enumerate(scene.body) if row.startswith('04-D01에서'))
    after=graph.lines(scene,wait+1,personal,after)
    waited=graph.add('rev:04:wait-memory:A',type='say',actor='mio',speaker='미오',mono=True,
        text='사진을 들고 하루카가 짚었던 자리에 서 보았다. 그 사람이 여기로 실제 나오는 것을 본 기억은 없었다.',
        source=scene.source(scene.line+wait+1),next=after)
    asked=graph.add('rev:04:wait-memory:B',type='say',actor='satsuki',speaker='사츠키',
        text='기다리겠다고 했을 땐 나가서 내 앞에 설 줄 알았어.',source=scene.source(scene.line+wait+1),next=after)
    after=graph.add('rev:04:wait-memory',type='branch',cases=[{'flag':'04-D01','equals':'A','to':waited},
        {'flag':'04-D01','equals':'B','to':asked}],default=after)
    asked=graph.add('rev:04:free-memory:A',type='say',actor='yuu',speaker='유우',
        text='그날 고개 돌린 이유는 직접 물어보려고 했어. 누가 대신 알아냈다고 쓰지 않을래.',source=scene.source(scene.line+memory+1),next=after)
    stayed=graph.add('rev:04:free-memory:B',type='say',actor='yuu',speaker='유우',
        text='사진 보고 있어도 돼. 나한테 말 안 해도 조금 여기 있을게.',source=scene.source(scene.line+memory+1),next=after)
    after=graph.add('rev:04:free-memory',type='branch',cases=[{'flag':'04-F01','equals':'A','to':asked},
        {'flag':'04-F01','equals':'B','to':stayed}],default=after)
    after=graph.lines(scene,0,memory,after)
    after=graph.add('rev:04:leave-court',type='stage',scene={'space':'inspection_hall_normal','leaveCourt':True},
                    source=scene.source(scene.line),next=after,presentation={'music':{'operation':'play','cue':'bgm_night'}})
    after=chapter_verdict(graph,scenes['04-R00'],after,4)
    ending=scenes['04-T03e'];vote_at=ending.body.index('### 최종 투표')
    after=graph.lines(ending,vote_at+1,len(ending.body),after)
    ident='T4-VOTE-REV01';ammo=['v4:E4-08','v4:E4-13','v4:V5-4:handover']
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':ammo,
        'stage':{'id':ident,'kind':'vote','v4':True,'title':'나오지 않았던 문','answer':'rei','candidates':seats,
            'question':'실제 덮개를 끝까지 고정한 행위의 검정은?','selectionRole':'final-culprit-vote','finalVote':True,
            'voteCounts':{'rei':7,'koto':1}},
        'queues':{'wrong':[{'id':ident+':wrong','type':'say','actor':'mio','speaker':'미오',
            'text':'문을 만든 사람이라는 이름만 고르는 게 아니야. 끝 고정과 손의 시야, 그 뒤에 한 말까지 맞춰 보자.',
            'source':ending.source(ending.line+vote_at+1)}]}}
    vote=graph.add('rev:04:final-vote',type='task',taskId=ident,trialDead=dead,seats=seats,
                   source=ending.source(ending.line+vote_at+1),success=after,next=after)
    vote_entry=graph.add('rev:04:vote-court-entry',type='stage',enterCourt=True,next=vote)
    after=graph.lines(ending,0,vote_at,vote)
    other=scenes['04-T03d'];after=graph.lines(other,0,len(other.body),after)
    closing=scenes['04-T03a'];anagram=closing.body.index('#### 섬광 애너그램 — 남길 수 있는 것')
    after_line=next(i for i in range(anagram+1,len(closing.body)) if SAY.match(closing.body[i]))
    after=graph.lines(closing,after_line,len(closing.body),after)
    ident='T4-AN-REV02';answer,distractors,question=ANAGRAMS[closing.id]
    ref=closing.source(closing.line+anagram+1)
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':['v4:V5-4:condition'],
        'stage':{'id':ident,'kind':'anagram','v4':True,'chapter':4,'title':'남길 수 있는 것','question':question,
                 'answer':answer,'distractors':list(distractors)},'queues':{}}
    after=graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=after,next=after)
    comic_at=closing.body.index('#### 클라이맥스 추리 — 나오지 않았던 문')
    after=graph.lines(closing,comic_at+1,anagram,after)
    ident=comic['id'];tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':ammo,'stage':comic,'queues':{}}
    entry=graph.add('rev:04:climax-comic',type='task',taskId=ident,trialDead=dead,seats=seats,
                    source=closing.source(closing.line+comic_at+1),success=after,next=after)
    entry=graph.add('rev:04:comic-court-entry',type='stage',enterCourt=True,next=entry)
    armament=closing.body.index('#### 이론 무장 — 부탁받은 일의 범위')
    final_intro=closing.body.index('### 그 말을 바깥까지 옮길 때')
    after=graph.lines(closing,final_intro+1,comic_at,entry)
    front=next(i for i,row in enumerate(closing.body) if row.startswith('레이가 지키려는 것은 두 주장이다.'))
    back=next(i for i,row in enumerate(closing.body) if row.startswith('후반에 “그 사람이 손을'))
    first=re.findall(r'“([^”]+)”',closing.body[front]);last=re.findall(r'“([^”]+)”',closing.body[back])
    assert len(first)==3 and len(last)==4
    groups=[(front,first),(back,last[:2]),(back,last[2:])]
    fragments,=re.findall(r'최종 조각 \*\*([^*]+)\*\*',closing.body[back]);fragments=[x.strip() for x in fragments.split('/')]
    assert len(fragments)==4
    ident='T4-AA-REV01';ref=closing.source(closing.line+armament+1)
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':['v4:V5-4:latch','v4:E4-13','v4:V5-4:continuous-rescue'],
        'stage':{'id':ident,'kind':'armament','v4':True,'chapter':4,'title':'부탁받은 일의 범위','opponent':'rei',
            'lines':[line for _,group in groups for line in group],
            'waves':[{'id':ident+':wave:'+str(phase),'pairs':[{'claim':{'id':f'{ident}:{phase}:{i}','type':'say',
                'actor':'rei','speaker':'레이','text':line,'source':closing.source(closing.line+at+1)}}
                for i,line in enumerate(group)]} for phase,(at,group) in enumerate(groups)],
            'phaseTranscripts':True,'question':'생성한 방과 구별해 실제로 확인한 조작의 네 근거는?',
            'finalSubject':'실제로 연결한 것은','final':fragments},'queues':{}}
    armament_entry=graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                            source=ref,success=after,next=after)
    duel=closing.body.index('#### 반론 쇼다운 — 기다려 달라는 말까지')
    feedback=next(i for i in range(duel,armament) if closing.body[i].startswith('첫 파의 일반 문장에는'))
    after=graph.lines(closing,feedback+1,armament,armament_entry)
    ident='T4-RS-REV05';ammo=['v4:V5-4:condition','v4:V5-4:photos','v4:V5-4:promise-comparison']
    final_entry=compile_showdown(graph,tasks,dead,seats,'rev:04:'+ident,ident,'기다려 달라는 말까지','레이',[
        ['자기 발로 들어왔습니다','처음에는 둘이 대화했습니다','밖에 기다리는 사람이 있었습니다'],
        ['밖에 기다려 달라고 했으니 안에서 답이 없어져도 아무도 오지 않기로 정해져 있었습니다']],
        [{'id':key,'name':evidence[key][0],'text':evidence[key][1]} for key in ammo],ammo[-1],
        closing.source(closing.line+feedback+1),('미오','내가 밖에서 기다린 건 맞아. 안에서 답이 없어져도 구조하지 않기로 약속한 것은 아니야.'),after)
    final_entry=graph.lines(closing,duel+1,feedback,final_entry)
    final_entry=graph.add('rev:04:final-hearing-entry',type='stage',enterCourt=True,next=final_entry)
    return {'comic-hearing':entry,'vote-hearing':vote_entry,'armament-hearing':armament_entry,'final-hearing':final_entry}


def chapter_four_context(graph,scenes,tail):
    closing=scenes['04-T03a'];head=closing.body.index('### 선택 — 구조에 늦었다는 말을 어떻게 묻나')
    starts=[i for i,row in enumerate(closing.body) if row.startswith(('### A —','### B —','### C —'))]
    common=closing.body.index('### 공통 — 한 번 더 하면 달랐을지')
    face=closing.body.index('### 그 얼굴로 말할 사람')
    compare=next(i for i,row in enumerate(closing.body) if row.startswith('플레이어가 ‘열 초 앞의 외부 고정’'))
    duel=closing.body.index('#### 반론 쇼다운 — 기다려 달라는 말까지')
    tail=graph.lines(closing,face+1,duel,tail)
    menu='rev:04:rewind-boundaries';ref=closing.source(closing.line+compare+1)
    wrong1=graph.add(menu+':both',type='say',actor='akari',speaker='아카리',
        text='제가 처음 달려갔을 때 이미 고정이 걸려 있었어요. 그 전의 닫힘까지 돌아간 건 아니에요.',source=ref,next=menu)
    wrong2=graph.add(menu+':unchanged',type='say',actor='nana',speaker='나나',
        text='제가 두 번째 시도에서 잡았던 손은 다른 자리에 있었어요. 처음 시도까지 제가 똑같이 보았다고는 하지 말아 주세요.',source=ref,next=menu)
    tail=graph.add(menu,type='menu',q='열 초 앞의 고정과 열 초 안의 구조를 어떻게 놓을까?',source=ref,
        options=[{'id':'both','label':'외부 고정과 구조 시도 모두 되돌아갔다','to':wrong1},
                 {'id':'separate','label':'이미 걸린 외부 고정 / 바뀐 구조 시도 분리','to':tail},
                 {'id':'unchanged','label':'구조가 바뀐 것도 없다','to':wrong2}])
    tail=graph.lines(closing,common+1,compare,tail)
    labels=[row.split('. ',1)[1] for row in closing.body[head:starts[0]] if re.match(r'^- [ABC]\. ',row)]
    assert len(labels)==3
    tail=graph.menu(closing,'구조에 늦었다는 말을 어떻게 물을까?',[
        (label,at+1,stop,'') for label,at,stop in zip(labels,starts,[*starts[1:],common])],tail)
    tail=graph.lines(closing,0,head,tail)

    scene=scenes['04-T03b'];place=next(i for i,row in enumerate(scene.body) if row.startswith('플레이어가 미오의 해석을 가리고'))
    tail=graph.lines(scene,place+1,len(scene.body),tail)
    for i,(question,correct,wrong,actor,reply) in reversed(list(enumerate([
        ('누가 고정했다는 인정을 어느 사람의 자리로 둘까?','레이가 직접 한 인정','미오가 대신 쓴 개인 노트','코토','제가 실제로 확인한 위치와 지금 읽은 도면부터 따로 놓아 주세요.'),
        ('구조 때 본 손은 누구의 관찰로 읽을까?','당시 손에 닿고 구조한 사람의 증언','3장에서 미오가 했던 위증','나나','제가 그때 화났다는 건 사실이에요. 지금 보았던 손을 알아내는 데에는 제 말을 따로 들어 주세요.'),
        ('실제 닫힌 끝점은 무엇과 맞출까?','직접 걸어 확인한 바닥과 기존 외벽','미오의 추측으로 그린 바깥 화살표','미오','내가 그린 길이 있었어도 실제로 걸은 끝은 벽이었어. 두 자료를 바꾸지 않을게.')]))):
        menu='rev:04:witness-source-match:'+str(i);ref=scene.source(scene.line+place+1)
        retry=graph.add(menu+':retry',type='say',actor=SPEAKERS[actor],speaker=actor,text=reply,source=ref,next=menu)
        picks=[{'id':'actual','label':correct,'to':tail},{'id':'borrowed','label':wrong,'to':retry}]
        if i!=1:picks.reverse()
        tail=graph.add(menu,type='menu',q=question,options=picks,source=ref)
    copy=next(i for i,row in enumerate(scene.body) if row.startswith('04-D01f에서 작업 사본'))
    tail=graph.lines(scene,copy+1,place,tail)
    actual=graph.add('rev:04:copy-memory:read',type='say',actor='koto',speaker='코토',
        text='제가 이쪽에서 돌아섰다고 미오 씨가 먼저 들으셨어요. 문이 열리는 것도 제가 보았다고 쓰면 제가 다시 말씀드릴게요.',
        source=scene.source(scene.line+copy+1),next=tail)
    left=graph.add('rev:04:copy-memory:left',type='say',actor='koto',speaker='코토',
        text='미오 씨가 제 표시를 미리 읽으신 적은 없어요. 제가 조사 때 걸음을 멈춘 곳을 다시 보여 드릴게요.',
        source=scene.source(scene.line+copy+1),next=tail)
    tail=graph.add('rev:04:copy-memory',type='branch',cases=[{'flag':'04-D01f','equals':'A','to':actual},
        {'flag':'04-D01f','equals':'B','to':left},{'flag':'04-D01f','equals':'C','to':left}],default=tail)
    conditional=next(i for i,row in enumerate(scene.body) if row.startswith('04-T03c에서 앞문에 관해 위증한'))
    join=next(i for i in range(conditional,len(scene.body)) if scene.body[i].startswith('일반 경로에서는'))
    tail=graph.lines(scene,join+1,copy,tail)
    remembered=graph.lines(scene,conditional+1,join,tail)
    tail=graph.add('rev:04:door-perjury-memory',type='branch',cases=[{'flag':'04-T03c:perjury','equals':True,'to':remembered}],default=tail)
    return graph.lines(scene,0,conditional,tail)


def chapter_four_last_hearing(graph,scenes,tasks,evidence,dead,seats,tail,nonstop):
    scene=scenes['04-T03']
    def ref(at):return scene.source(scene.line+at+1)
    def queued(ident,actor,text,at):return {'id':ident,'type':'say','actor':SPEAKERS[actor],'speaker':actor,'text':text,'source':ref(at)}
    def task(ident,stage,at,target,ammo,wrong=()):
        tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':ammo,'stage':{'id':ident,'v4':True,**stage},
            'queues':{'wrongVariants':[{'optionIndex':i,'script':[queued(ident+':'+str(i),actor,text,at)]} for i,actor,text in wrong]}}
        return graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref(at),success=target,next=target)
    if (ROOT/'art/revision_comic/chapter4/reviewed.json').is_file():
        tail=chapter_four_context(graph,scenes,'rev:04:final-hearing-entry')
        graph.nodes.pop('rev:04:excerpt-end')
    reason=scene.body.index('#### 추리 연결 — 보이는 자리에서 한 일')
    after=next(i for i in range(reason+1,len(scene.body)) if SAY.match(scene.body[i]))
    tail=graph.lines(scene,after,len(scene.body),tail)
    authored=[
        ('뒤쪽으로 빠져나왔다는 말이 성립하려면?', ['유우가 같은 말을 다시 해야 한다','기존 외벽 바깥까지 이어지는 실제 출구가 필요하다','사진의 날짜만 맞으면 된다'],1,'유우','내가 본 몸이 맞아도 벽 안에 길이 생기지는 않잖아'),
        ('우연히 닫힘과 바깥 끝 고정을 가를 조건은?', ['구조 뒤 사망 확인 시각','누가 생성한 방인지','두 폭의 눌림을 각각 만드는 받침과 끝 고정 동작'],2,'쇼','사망 시각과 닫는 동작은 다른 표에서 확인합니다. 끝 고정은 저 두 부품의 위치를 대조하십시오'),
        ('손을 보고도 고정했는지 무엇을 더 확인할까?', ['끝까지 닫는 작업자 위치와 손이 실제로 보인 범위','손을 먼저 본 사람을 검정으로 지목','같은 날짜 사진을 한 장소로 합침'],0,'나나','제가 들어가서 본 손은 제가 말할 수 있어요. 닫는 분이 어디 서야 했는지는 실험을 같이 보셔야 해요'),
        ('손이 보였다는 사실만으로 끝 고정까지 확정할까?', ['손을 먼저 본 구조자가 처음 고정했다','새 벽이 저절로 끝 고정까지 닫았다','실제 자국이 다른 두 위치의 동작을 별개로 확인한다'],2,'나나','제가 손을 뻗어 본 때는 문이 열린 뒤예요. 잡은 사람 이름으로 그 전에 저걸 잠갔다고 쓰면 다시 말할게요'),
        ('카메라 사진을 고정 동작에 쓰려면 무엇부터 읽을까?', ['사진에 밝은 줄이 있으니 항상 같은 면이다','실제 닿을 수 있던 면과 조사에서 본 기존 벽 길이','카메라를 가진 사람이 고정구에 손을 넣었다'],1,'쇼','손목에 있었던 끈과 덮개 아래에서 확인한 눌림은 다른 접촉입니다'),
        ('그다음 누구에게 무엇을 물을까?', ['실제 고정 위치까지 갈 수 있던 사람이 그때 무엇을 볼 수 있었는지','사진을 숨기고 싶었는지만','밖에 있던 사람에게 안의 일을 대신 묻는다'],0,'유우','나는 복도에서 봤다니까. 안에 가 보라고는 하지 마')]
    questions=[];ident='T4-RE-REV01'
    for i,(question,options,answer,actor,reply) in enumerate(authored):
        at=next(j for j in range(reason,after) if scene.body[j].startswith(f'{i+1}. '));ids=[f'option-{j}' for j in range(3)]
        questions.append({'q':question,'options':options,'optionIds':ids,'answer':options[answer],
            'wrongVariants':[{'optionId':ids[j],'script':[queued(f'{ident}:{i}:{j}',actor,reply,at)]} for j in range(3) if j!=answer],
            'success':[queued(f'{ident}:{i}:success','미오',options[answer]+'.',at)]})
    tail=task(ident,{'kind':'reasoning','title':'보이는 자리에서 한 일','questions':questions},reason,tail,
              ['v4:E4-08','v4:E4-13','v4:V5-4:hand-view'])
    scrum=scene.body.index('#### 논의 스크럼 — 빠져나간 자리인가, 숨긴 자리인가');ident='T4-SD-REV01';pairs=[]
    topics=[('벽','뒤쪽','바깥 벽'),('끝점','안쪽 문','끝'),('관찰','문 쪽','실제 나온'),('고정','그때','두 번')]
    for at in range(scrum+1,reason):
        match=re.fullmatch(r'\| ([^ ]+) “(.+)” \| ([^.]+)\. ([^ ]+) “(.+)” \|',scene.body[at])
        if not match:continue
        actor,claim,keyword,ally,response=match.groups();word,claim_word,response_word=topics[len(pairs)];assert keyword==word
        pairid=f'{ident}:{len(pairs)}';pairs.append({'id':pairid,'them':actor,'themActor':SPEAKERS[actor],'themText':claim,
            'us':ally,'usActor':SPEAKERS[ally],'usText':response,'keyword':keyword,'claimKeyword':claim_word,
            'responseKeyword':response_word,'duration':11,'wrong':[queued(pairid+':retry',actor,claim,at)]})
    assert len(pairs)==4
    pairs[3]['wrongByKeyword']={'사망 시각':[queued(ident+':death','사츠키','그때 같이 있던 사람이 물에 빠뜨린 게 아니라는 건 알잖아. 지금은 닫힐 때를 보고 있어',scrum)]}
    tail=task(ident,{'kind':'scrum','title':'빠져나간 자리인가, 숨긴 자리인가','pairs':pairs,
        'teams':{'them':['rei','koto','yuu'],'us':['mio','nana','satsuki','sho','akari']},
        'scrumDecoys':[{'keyword':word} for word in ('사망 시각','얼굴 사진','외부 전화')],
        'scrumPresentation':{'topic':'안쪽 문이 설명하는 실제 길','them':'바깥으로 나올 수 있다','us':'구획 뒤는 막힌 끝이다'}},scrum,tail,['v4:E4-08','v4:E4-13','v4:V5-4:handover'])
    shadow=scene.body.index('#### 논스톱 — 그림자가 먼저 닿았다면')
    tail=nonstop(scene,'T4-NS-REV14','그림자가 먼저 닿았다면','04-I05의 기본 효과',
        'v4:V5-4:light',['v4:E4-13','v4:V5-4:handover','v4:V5-4:light'],tail,
        ('사츠키','자국 두 개인 건 나도 봤어. 지금은 내가 저기서 손을 보낼 수 있었냐고 묻고 있잖아'),stop=scrum,prefix=shadow)
    second=scene.body.index('#### 논스톱 — 걸렸다가 지나간 덮개')
    rule=next(i for i in range(second,shadow) if scene.body[i].startswith('E4-13 → 3.'))
    tail=nonstop(scene,'T4-NS-REV13','걸렸다가 지나간 덮개','E4-13 → 3.',
        'v4:E4-13',['v4:V5-4:handover','v4:V5-4:condition','v4:E4-13'],tail,
        ('미오','그건 레이가 같이 걸은 뒤야. 지금은 닫고 걸쇠를 건 두 동작이 어떻게 달랐는지야'),'한꺼번에',stop=shadow,prefix=second)
    first=scene.body.index('#### 논스톱 — 뒤늦게 손이 거기에 들어왔다면')
    tail=nonstop(scene,'T4-NS-REV12','뒤늦게 손이 거기에 들어왔다면','04-I07의 종이 표시로',
        'v4:V5-4:closure-line',['v4:V5-4:condition','v4:V5-4:camera','v4:V5-4:closure-line'],tail,
        ('아카리','제가 연 때는 아는데, 닫아 둔 틈에서 끈이 움직였는지를 보려면 그 아래를 봐야 해요'),stop=second,prefix=first)
    tail=graph.add('rev:04:closure-line-record',type='evidence',evidenceId='v4:V5-4:closure-line',
        name=evidence['v4:V5-4:closure-line'][0],text=evidence['v4:V5-4:closure-line'][1],source=ref(first),next=tail)
    visibility=scene.body.index('#### 정답 선택과 증거 제시 — 안쪽에 있던 사람')
    granted=next(i for i in range(visibility,first) if SAY.match(scene.body[i]))
    tail=graph.lines(scene,granted,first,tail)
    ids=['v4:V5-4:latch','v4:V5-4:hand-view','v4:V5-4:condition']
    options=[{'id':key,'name':evidence[key][0],'text':evidence[key][1]} for key in ids]
    tail=task('T4-BU-REV01',{'kind':'bullet','question':'실제 안쪽 손이 끝 고정 위치에서 보이는 범위를 확인한 자료는?',
        'options':options,'answer':ids[1]},visibility,tail,ids,[(0,'나나','일반 구조는 확인했어요. 당시의 손 위치도 함께 놓아 주세요.'),
        (2,'쇼','생존을 확인한 시각만으로 작업자의 시야를 대신하지 않습니다.')])
    tail=task('T4-QA-REV07',{'kind':'choice','question':'바깥에서 고정한 사람이 안의 사람을 볼 수 있었을까?',
        'options':['고정 직전 손이 걸리는 부분은 바깥에서 보인다','생성된 벽이 모든 시야를 가린다','생존 시각만 알면 시야는 필요 없다'],'answer':0},
        visibility,tail,['v4:V5-4:hand-view'],[(1,'미오','그 자리에서 손이 가려지는지 이미 따로 맞췄어. 벽이 있다는 말만으로 시야 전부를 덮지 말자.'),
        (2,'쇼','시각과 시야는 별도 질문입니다. 실제 조작 위치와 손의 높이를 비교하십시오.')])
    guard=scene.body.index('#### 정답 선택 — 문을 봤다는 말의 시작')
    compare=next(i for i in range(guard,visibility) if scene.body[i].startswith('문이 감시되기 시작한 때를'))
    correction, = re.findall(r'“([^”]+)”', scene.body[compare])
    tail=graph.lines(scene,compare+1,visibility,tail)
    tail=task('T4-QA-REV06',{'kind':'choice','question':'앞문의 시야를 이어받은 기준은?',
        'options':['미오가 앞문을 봐 달라고 했을 때','덮개에 손이 있다고 부른 때','유우가 계단에서 레이와 만났을 때'],'answer':0},
        compare,tail,['v4:V5-4:handover'],[(1,'사츠키',correction),
        (2,'유우','나는 계단에서 만났어. 거기서 문 뒤까지 볼 수 있었던 건 아니야.')])
    tail=graph.lines(scene,guard+1,compare,tail)
    lie=scene.body.index('#### 04-T03c　우소다마 — 아무도 보지 않았다고 하면')
    common=next(i for i in range(lie,guard) if scene.body[i].startswith('두 경로 모두 실제 시야를'))
    tail=graph.lines(scene,common+1,guard,tail)
    normal=next(i for i in range(lie,guard) if scene.body[i].startswith('일반 경로는 **'))
    perjury=next(i for i in range(normal,guard) if scene.body[i].startswith('우소다마 경로는 **'))
    correct=graph.lines(scene,normal+1,perjury,tail)
    false=graph.lines(scene,perjury+1,common,tail)
    ident='T4-LI-REV01';ammo=['v4:V5-4:handover','v4:V5-4:latch'];options=[{'id':key,'name':evidence[key][0],'text':evidence[key][1]} for key in ammo]
    rows=[debate_statement(ident,0,'코토','**고개를 들었는지는 먼저 알 수 없어요.**',ref(lie),'weak',ammo[0]),
          debate_statement(ident,1,'아카리','제가 손 들었던 시점부터 물어보시면 돼요.',ref(lie)),
          debate_statement(ident,2,'유우','나는 계단에서 레이와 같이 걸었어. 문 앞에 있었던 건 아니고.',ref(lie))]
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':ammo,
        'stage':{'id':ident,'kind':'nonstop','v4':True,'title':'아무도 보지 않았다고 하면','lines':rows,'options':options,'authoredAmmo':ammo,
                 'filterOwnedEvidence':True,'wrongCards':{ammo[1]:'different-object'}},
        'transformation':{'sourceEvidenceId':ammo[0],'lieLabel':'고개 들기 전 이미 앞문은 비었다','intentionalHold':True},
        'debate':{'id':ident,'kind':'nonstop','lines':rows,'bullets':options},
        'queues':{'wrongVariants':[{'cause':'different-object','script':[queued(ident+':wrong','쇼','이것은 입실 전에 보던 앞문입니다. 덮개는 별도로 확인하십시오.',lie)]}]}}
    tail=graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref(lie),success=correct,next=correct,
        outcomes={'normal':{'judgment':'refute','to':correct},'perjury':{'judgment':'lie','to':false,'sets':{'04-T03c:perjury':True}}})
    before=next(i for i in range(lie+1,normal) if SAY.match(scene.body[i]))
    return graph.lines(scene,before,normal,tail)


def chapter_four_route_hearing(graph,scenes,tasks,evidence,dead,seats,tail,visibility_objects,end_objects,nonstop):
    """The existing door does not turn a gap in testimony into a physical exit."""
    current=scenes['04-T03'];mine=current.body.index('#### 발굴 이매지네이션 — 통로의 끝에 있는 것')
    duel=current.body.index('#### 반론 쇼다운 — 내가 본 건 같이 걸은 때야')
    discussion=current.body.index('#### 논스톱 — 나왔다고 들었어')
    lie=current.body.index('#### 04-T03c　우소다마 — 아무도 보지 않았다고 하면')
    tail=chapter_four_last_hearing(graph,scenes,tasks,evidence,dead,seats,tail,nonstop)
    tail=nonstop(current,'T4-NS-REV11','나왔다고 들었어','E4-08 → 4.',
        'v4:E4-08',['v4:V5-4:handover','v4:V5-4:photos','v4:E4-08'],tail,
        ('유우','그건 미오하고 나나가 들어가기 직전이잖아. 나는 그 전에 계단에서 레이 만났어'),stop=lie,prefix=discussion)
    after=next(i for i in range(duel,discussion) if SAY.match(current.body[i]))
    tail=graph.lines(current,after,discussion,tail)
    ident='T4-RS-REV04';ammo=['v4:V5-4:photos','v4:V5-4:handover','v4:E4-08']
    options=[{'id':key,'name':evidence[key][0],'text':evidence[key][1]} for key in ammo]
    tail=compile_showdown(graph,tasks,dead,seats,'rev:04:'+ident,ident,'내가 본 건 같이 걸은 때야','코토',[
        ['유우 씨는 계단에서 처음 레이 씨를 봤어요','두 분이 그 뒤에 같이 걸으셨어요','그때 레이 씨는 이미 홀 바깥에 계셨죠.'],
        ['유우 씨가 앞문 쪽을 다 보고 있지는 않았어요','하루카 씨는 그분 옆에 없었죠',
         '그럼 비어 있던 사이에 뒤쪽으로 나갔다는 말은 유우 씨 증언과 맞아요.']],
        options,'v4:E4-08',current.source(current.line+duel+1),
        ('코토','들어가는 장면에는 동의해요. 이후 안쪽 문이 어디까지 이어졌는지 보여 주세요'),tail)
    ident='T4-MM-REV02';ref=current.source(current.line+mine+1)
    variants=[('inspection-sealed-end','안쪽 구획의 막힌 끝과 기존 외벽','',''),
        ('inspection-hypothesis-arrow','바깥으로 이어진다는 가상선','미오','여기 화살표는 설명으로 넣었어. 가 보니까 거기에는 벽이 있었지. 화살표 끝에 새 문을 만들 수는 없어.'),
        ('inspection-rescue-floor','몸을 꺼낸 자리','아카리','그건 제가 들어온 뒤에 열었던 곳이에요. 앞에서 누가 나갈 때 썼던 길이라고는 안 했어요.'),
        ('inspection-stair-meeting','계단에서 만난 위치','유우','나는 거기에서 레이를 봤어. 문을 열면서 여기로 왔는지는 못 봤고.')]
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':['v4:E4-08','v4:V5-4:photos'],
        'stage':{'id':ident,'kind':'mindmine','v4':True,'title':'통로의 끝에 있는 것',
            'question':'다른 출입구로 나갔다는 설명을 확인하려면 어느 실제 끝을 찾을까?',
            'image':MINE_ART+'inspection-latch-section.svg','answerRegionId':'inspection-sealed-end','mineObjects':end_objects,
            'regions':[{'id':key,'label':label,'correct':not actor,'wrongVariant':key} for key,label,actor,_ in variants]},
        'queues':{'wrongVariants':[{'cause':key,'script':[{'id':ident+':'+key,'type':'say','actor':SPEAKERS[actor],
            'speaker':actor,'text':text,'source':ref}]} for key,_,actor,text in variants if actor]}}
    tail=graph.add('rev:04:sealed-end-document',type='document',title='안쪽 구획의 실제 끝',
        rows=['현재 확인한 막힌 끝과 기존 외벽을 맞췄다. 누가 그 문에서 나오는 장면을 보았다는 기록은 추가하지 않는다.'],
        image=MINE_ART+'inspection-latch-section.svg',source=ref,next=tail)
    tail=graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)

    view=scenes['04-T02h'];heading=view.body.index('#### 발굴 이매지네이션 — 아래에서 맞닿는 것')
    after=next(i for i in range(heading+1,len(view.body)) if SAY.match(view.body[i]))
    tail=graph.lines(view,after,len(view.body),tail)
    ref=view.source(view.line+heading+1)
    key='v4:V5-4:hand-view'
    tail=graph.add('rev:04:hand-view-record',type='evidence',evidenceId=key,name='끝 고정 위치와 안쪽 손의 시야 대조',
        text='정상 재현의 바깥 발 위치와 팔 길이, 실제 구조에서 잡은 손의 높이를 맞췄다. 그 위치에서 내려다볼 때 손이 가려지지 않는다. 그때 누가 실제 시선을 주었는지는 별도 질문이다.',source=ref,next=tail)
    # These three inputs compare existing observations; none registers a new eyewitness.
    for i,(question,correct,wrong,actor,reply) in reversed(list(enumerate([
        ('시야가 시작되는 위치는?','닫히기 전 바깥 조작자의 발 위치','구조 뒤 사진을 찍은 자리','유우','아래 보려면 어디에 먼저 서야 돼? 나중 사진 자리부터 놓지 마.'),
        ('끝 고정에 힘을 줄 수 있는 범위는?','바깥에서 고정구에 닿는 팔 길이','수납문 벽의 그림자 길이','아카리','문으로 몸을 넣은 것과 금속 부품을 움직인 곳을 나눠 주세요.'),
        ('어느 손 높이와 맞출까?','구조에서 실제로 잡아 옮긴 손의 높이','사진에 없는 얼굴의 위치','나나','제가 꺼낼 때 잡았던 데는 말씀드릴 수 있어요. 보이지 않은 얼굴을 더 만들지는 말아 주세요.')]))):
        ident='rev:04:visibility-match:'+str(i)
        retry=graph.add(ident+':retry',type='say',actor=SPEAKERS[actor],speaker=actor,text=reply,source=ref,next=ident)
        picks=[{'id':'actual','label':correct,'to':tail},{'id':'unobserved','label':wrong,'to':retry}]
        if i%2==0:picks.reverse()
        tail=graph.add(ident,type='menu',q=question,options=picks,source=ref)
    ident='T4-MM-REV01'
    variants=[('inspection-control-and-gap','고정구 바깥과 중간 받침 뒤의 틈','',''),
        ('inspection-lid-side','덮개 옆면만','유우','옆면 한 장이면 나는 고개가 얼마나 들어가는지 모르겠어. 아래 보려면 어디에 먼저 서야 돼?'),
        ('inspection-storage-wall','수납문 벽만','아카리','제가 먼저 손댄 것은 그 문짝이 아니에요. 저기서 몸을 넣은 것과 부품을 움직인 곳을 다시 나눠 주세요'),
        ('inspection-lamp-outline','작업등이 만든 윤곽','나나','같은 모양이 나왔다고 옛날에 누가 여기 서 있었다는 건 아니에요.')]
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':['v4:V5-4:latch','v4:V5-4:continuous-rescue'],
        'stage':{'id':ident,'kind':'mindmine','v4':True,'title':'아래에서 맞닿는 것','question':'끝 고정 위치의 시야와 실제 손의 높이를 함께 드러낼 부분은?',
            'image':MINE_ART+'inspection-latch-section.svg','answerRegionId':'inspection-control-and-gap','mineObjects':visibility_objects,
            'regions':[{'id':key,'label':label,'correct':not actor,'wrongVariant':key} for key,label,actor,_ in variants]},
        'queues':{'wrongVariants':[{'cause':key,'script':[{'id':ident+':'+key,'type':'say','actor':SPEAKERS[actor],
            'speaker':actor,'text':text,'source':ref}]} for key,_,actor,text in variants if actor]}}
    tail=graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    return graph.lines(view,0,heading,tail)


def chapter_four_identity_hearing(graph,scenes,tasks,evidence,dead,seats,tail,visibility_objects,end_objects):
    """Consent, continuous rescue, and remembered attempts are different claims."""
    evidence={**evidence,
        'v4:V5-4:hand-view':('끝 고정 위치와 안쪽 손의 시야 대조','바깥 발 위치와 팔 길이, 실제로 잡아 옮긴 손의 높이를 맞추면 조작 위치에서 손이 가려지지 않는다. 누가 그때 시선을 주었는지는 직접 답을 듣는다.'),
        'v4:V5-4:closure-line':('닫힘 선과 끝 고정 압착 대조','정상 재현의 종이 표시와 끝 고정에 눌린 끈 면을 맞췄다. 잡힌 끈 부분은 끝 동작 전에 고정 면 안에 있었다. 손의 자세나 조작자의 실제 시선은 이 대조만으로 정하지 않는다.')}
    def cards(keys):
        return [{'id':key,'name':evidence[key][0],'text':evidence[key][1]} for key in keys]
    def ns(current,ident,title,rule_start,answer,ammo,target,wrong,vpoint=None,stop=None,prefix=0):
        heading=current.body.index('#### 논스톱 — '+title)
        rule=next(i for i in range(heading,len(current.body)) if current.body[i].startswith(rule_start))
        target=graph.lines(current,rule+1,len(current.body) if stop is None else stop,target)
        rows=[]
        for at in range(heading+1,rule):
            if match:=STMT.match(current.body[at]):
                number,actor,raw,role=match.groups();weak='논파점' in role or '약점' in role
                row=debate_statement(ident,number,actor,raw,current.source(current.line+at+1),
                    'weak' if weak else 'plain',answer if weak else '')
                if weak and vpoint:row['vpoint']={'glyphIndex':row['text'].index(vpoint)}
                rows.append(row)
        assert sum('weak' in row for row in rows)==1
        ref=current.source(current.line+rule+1);options=cards(ammo)
        tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':ammo,
            'stage':{'id':ident,'kind':'nonstop','v4':True,'title':title,'lines':rows,'options':options,
                     'authoredAmmo':ammo,'filterOwnedEvidence':True,'wrongCards':{ammo[0]:'different-range'}},
            'debate':{'id':ident,'kind':'nonstop','lines':rows,'bullets':options},
            'queues':{'wrongVariants':[{'cause':'different-range','script':[{'id':ident+':wrong','type':'say',
                'actor':SPEAKERS[wrong[0]],'speaker':wrong[0],'text':wrong[1],'source':ref}]}]}}
        target=graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=target,next=target)
        return graph.lines(current,prefix,heading,target)

    tail=chapter_four_route_hearing(graph,scenes,tasks,evidence,dead,seats,tail,visibility_objects,end_objects,ns)

    practice=scenes['04-T02l']
    tail=ns(practice,'T4-NS-REV10','익숙한 사람이 덮개를 받치는 법','**04-I09a의 정상',
        'v4:V5-4:continuous-rescue',['v4:V5-4:handover','v4:V5-4:rescue-comparison','v4:V5-4:continuous-rescue'],tail,
        ('레이','나중에 함께 걸었던 사실은 부인하지 않습니다. 흔적이 어느 방향으로 남았는지와는 다른 기록입니다.'))

    attempt=scenes['04-T02i'];heading=attempt.body.index('#### 패닉 — 동시에 겪은 일처럼 읽을 때')
    rule=next(i for i,row in enumerate(attempt.body) if row.startswith('정답은 **04-I09에서'))
    tail=graph.lines(attempt,rule+1,len(attempt.body),tail)
    ident='T4-PN-REV02';lanes=[{'id':label,'actor':SPEAKERS[name],'speaker':name,'lines':[]}
        for label,name in zip(('왼쪽','가운데','오른쪽'),('나나','유우','아카리'))];rows=[]
    for at in range(heading+1,rule):
        cells=[cell.strip() for cell in attempt.body[at].strip('|').split('|')]
        if len(cells)!=4 or not cells[0].isdigit():continue
        beat=int(cells[0])
        for index,(lane,raw) in enumerate(zip(lanes,cells[1:])):
            weak=(beat,index)==(5,1);raw=raw.replace('[약점] ','').strip()
            row=debate_statement(ident,f'{index}:{beat}',lane['speaker'],raw,
                attempt.source(attempt.line+at+1),'weak' if weak else 'plain','v4:V5-4:continuous-rescue' if weak else '')
            rows.append(row);lane['lines'].append(row['id'])
            if '[큰 소리]' in raw:
                noise=debate_statement(ident,'noise',lane['speaker'],raw,attempt.source(attempt.line+at+1),'noise')
                noise.update(noiseRole='loud',noiseDurability=2,hostStatement=row['id']);rows.append(noise)
    assert len(rows)==19 and all(len(lane['lines'])==6 for lane in lanes)
    ammo=['v4:E4-13','v4:V5-4:handover','v4:V5-4:continuous-rescue'];options=cards(ammo)
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':ammo,
        'stage':{'id':ident,'kind':'panic','v4':True,'title':'동시에 겪은 일처럼 읽을 때','lines':rows,'options':options,'filterOwnedEvidence':True},
        'debate':{'id':ident,'kind':'panic','lines':rows,'bullets':options,'lanes':lanes,'synchronizedBeats':True},'queues':{}}
    ref=attempt.source(attempt.line+rule+1)
    tail=graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    tail=graph.lines(attempt,0,heading,tail)

    photo=scenes['04-T02j'];heading=photo.body.index('#### 섬광 애너그램 — 사진이 남긴 때')
    after=next(i for i in range(heading+1,len(photo.body)) if photo.body[i].startswith('### '))
    tail=graph.lines(photo,after+1,len(photo.body),tail)
    ident='T4-AN-REV01';answer,distractors,question=ANAGRAMS[photo.id]
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':['v4:V5-4:camera'],
        'stage':{'id':ident,'kind':'anagram','v4':True,'chapter':4,'title':'사진이 남긴 때',
                 'question':question,'answer':answer,'distractors':list(distractors)},'queues':{}}
    ref=photo.source(photo.line+heading+1)
    tail=graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    tail=graph.lines(photo,0,heading,tail)
    replacement=scenes['04-T02e']
    tail=ns(replacement,'T4-NS-REV09','물가에서 꺼낸 것은 어디로 갔어','4에는 **04-I09b',
        'v4:V5-4:continuous-rescue',['v4:V5-4:condition','v4:V5-4:photos','v4:V5-4:continuous-rescue'],tail,
        ('유우','쇼가 먼저 본 때부터의 상태라는 건 나도 알아. 그전에 어디서 왔는지는 아직 안 봤잖아'),'다른 몸')

    consent=scenes['04-T02c'];heading=consent.body.index('#### 반론 쇼다운 — 그 사람이 안으로 걸어갔으니까')
    starts=[i for i in range(heading,len(consent.body)) if consent.body[i].startswith(('**첫 교환.**','**둘째 교환.**','**셋째 교환.**'))]
    assert len(starts)==3
    for index,(at,stop) in reversed(list(enumerate(zip(starts,[*starts[1:],len(consent.body)])))):
        tail=graph.lines(consent,at+1,stop,tail)
        spoken=re.findall(r'“([^”]+)”',consent.body[at])[:3];assert len(spoken)==3
        spoken=[line.replace('**','') for line in spoken]
        ident=f'T4-RS-REV{index+1:02}';ammo=['v4:V5-4:photos','v4:V5-4:latch','v4:V5-4:promise-comparison']
        tail=compile_showdown(graph,tasks,dead,seats,'rev:04:'+ident,ident,
            ('들어간 선택과 다음 행위','해치지 않겠다는 실제 말','밖에서 기다림과 바깥 고정')[index],
            '레이',[spoken[:2],spoken[2:]],cards(ammo),ammo[-1],consent.source(consent.line+at+1),
            [('레이','방을 만들 수 있다는 말은 제가 무엇을 고정할지 설명한 말이 아닙니다.'),
             ('쇼','누가 어떻게 조작할지 면담 전에 공개했는지 구분하십시오.'),
             ('사츠키','네가 거기 있었던 것까지 빼 달라는 말은 아니잖아.')][index],tail)
    return graph.lines(consent,0,heading,tail)


def chapter_four_physical_hearing(graph,scenes,tasks,evidence,dead,seats,tail):
    """Keep the three physical alternatives separate from identifying an actor."""
    def say(ident,actor,text,ref,target):
        return graph.add(ident,type='say',actor=SPEAKERS[actor],speaker=actor,text=text,source=ref,next=target)
    def choice(ident,current,at,question,options,answer,ammo,target):
        ref=current.source(current.line+at+1)
        tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':ammo,
            'stage':{'id':ident,'kind':'choice','v4':True,'question':question,'options':[x[0] for x in options],'answer':answer},
            'queues':{'wrongVariants':[{'optionIndex':i,'script':[{'id':ident+':'+str(i),'type':'say',
                'actor':SPEAKERS[actor],'speaker':actor,'text':text,'source':ref}]}
                for i,(_,actor,text) in enumerate(options) if i!=answer]}}
        return graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                         source=ref,success=target,next=target)
    def tabs(current,heading,end,question,views,target,prefix):
        menu='rev:04:'+prefix
        options=[]
        for i,(label,first,last,actor,text) in enumerate(views):
            flag=prefix+':'+str(i)
            to=say(menu+':done:'+str(i),actor,text,current.source(current.line+first+1),menu)
            graph.nodes[to]['set']={flag:True}
            to=graph.lines(current,first,last,to)
            options.append({'id':str(i),'label':label,'to':to,'requires':{flag:False}})
        options.append({'id':'continue','label':'확인한 범위를 나누어 남긴다',
                        'to':target,'requires':{prefix+':'+str(i):True for i in range(len(views))}})
        return graph.add(menu,type='menu',q=question,options=options,source=current.source(current.line+heading+1))
    def nonstop(current,ident,title,rule_start,ammo,target,wrongs=(),vpoint=''):
        heading=current.body.index('#### 논스톱 — '+title)
        rule=next(i for i in range(heading,len(current.body)) if current.body[i].startswith(rule_start))
        rows=[]
        for at in range(heading+1,rule):
            if match:=STMT.match(current.body[at]):
                number,actor,raw,role=match.groups(); weak='논파점' in role or '약점' in role
                row=debate_statement(ident,number,actor,raw,current.source(current.line+at+1),
                                    'weak' if weak else 'plain',ammo[-1] if weak else '')
                if weak and vpoint:
                    word,letter=vpoint
                    row['vpoint']={'glyphIndex':row['text'].index(word)+word.index(letter)}
                rows.append(row)
        assert len(rows)>=10 and sum('weak' in row for row in rows)==1,ident
        cards=[{'id':key,'name':evidence[key][0],'text':evidence[key][1]} for key in ammo]
        ref=current.source(current.line+rule+1)
        tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':ammo,
            'stage':{'id':ident,'kind':'nonstop','v4':True,'title':title,'lines':rows,'options':cards,
                     'authoredAmmo':ammo,'filterOwnedEvidence':True,'wrongCards':{key:cause for key,cause,*_ in wrongs}},
            'debate':{'id':ident,'kind':'nonstop','lines':rows,'bullets':cards},
            'queues':{'wrongVariants':[{'cause':cause,'script':[{'id':ident+':'+cause,'type':'say',
                'actor':SPEAKERS[actor],'speaker':actor,'text':text,'source':ref}]} for _,cause,actor,text in wrongs]}}
        task=graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                       source=ref,success=target,next=target)
        return graph.lines(current,0,heading,task)

    photo=scenes['04-T02a']; at=photo.body.index('#### 관찰 부위 지목 — 손의 위치를 판단하는 두 항목')
    after=next(i for i in range(at+1,len(photo.body)) if SAY.match(photo.body[i]))
    tail=graph.lines(photo,after,len(photo.body),tail)
    tail=choice('T4-QA-REV05',photo,at,'수습 뒤 찍은 사진 한 장에서 직접 확인할 수 있는 것은?',[
        ('기구 안쪽에서 처음 걸려 있던 손','나나','그때는 손을 받치고 있었어요. 찍은 것은 다 꺼낸 뒤예요.'),
        ('수습 뒤 찍은 손목 고리','',''),
        ('실물 끈의 두 눌림이 형성된 순간','쇼','사진과 실물 압착은 별도 기록입니다. 고정 당시의 장면은 촬영하지 않았습니다.')],
        1,['v4:V5-4:camera','v4:E4-13'],tail)
    tail=graph.lines(photo,0,at,tail)

    sounds=scenes['04-T02b']; at=sounds.body.index('#### 가설 선택 — 둘 중 하나가 건너뛰어진 게 아닌가')
    after=next(i for i in range(at+1,len(sounds.body)) if SAY.match(sounds.body[i]))
    tail=graph.lines(sounds,after,len(sounds.body),tail)
    labels=[BULLET.match(row)[1] for row in sounds.body[at:after] if BULLET.match(row)]
    assert len(labels)==3
    explanations=[('쇼','중간 받침과 끝 고정은 두 동작입니다. 들린 횟수로 그 간격을 몇 초라고 정하지 않겠습니다.'),
        ('미오','한쪽 면이 아직 닿지 않은 때에 양쪽 자국이 같이 생겼다고 할 수는 없어. 두 접촉을 나누어 보자.'),
        ('아카리','제가 올리기 전에 이미 끝이 걸려 있었어요. 들린 소리가 같았는지와 그 상태를 본 것은 달라요.')]
    tail=tabs(sounds,at,after,'소리와 실제 동작을 어느 범위까지 연결할까?',
              [(label,after,after,actor,text) for label,(actor,text) in zip(labels,explanations)],tail,'sound-hypotheses')
    tail=graph.lines(sounds,0,at,tail)

    witness=scenes['04-T02g']; at=witness.body.index('#### 인물 지목 — 직접 보고 손을 댄 범위')
    after=next(i for i in range(at+1,len(witness.body)) if SAY.match(witness.body[i]))
    tail=graph.lines(witness,after,len(witness.body),tail)
    ref=witness.source(witness.line+at+1); ident='T4-PE-REV01'; candidates=['akari','nana','koto','yuu']
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':['v4:V5-4:mechanism-comparison'],
        'stage':{'id':ident,'kind':'person','v4':True,'question':'미오가 수납문을 먼저 열고 난 뒤 자신이 금속 받침을 잡았다는 순서를 직접 확인한 사람은?',
                 'candidates':candidates,'answer':'akari'},
        'queues':{'wrongVariants':[{'optionIndex':i,'script':[{'id':ident+':'+str(i),'type':'say','actor':actor,
            'speaker':name,'text':text,'source':ref}]} for i,actor,name,text in [
            (1,'nana','나나','제가 손을 잡았을 때는 뒤쪽을 계속 보지 못했어요.'),
            (2,'koto','코토','제가 안에서 움직인 문은 조사할 때였습니다. 처음 열 때 그 자리에 있었다고 보탤 수는 없어요.'),
            (3,'yuu','유우','저기는 들어가서 본 데가 아니야. 내가 거기까지 갔다고 다시 써야 돼?')]]}}
    tail=graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    tail=graph.lines(witness,0,at,tail)

    inside=scenes['04-T02k']; heading=inside.body.index('#### 논스톱 — 안에서도 끝까지 닫을 수 있다면')
    rule=next(i for i,row in enumerate(inside.body) if row.startswith('4에 **E4-04'))
    tail=graph.lines(inside,rule+1,len(inside.body),tail)
    tail=nonstop(inside,'T4-NS-REV08','안에서도 끝까지 닫을 수 있다면','4에 **E4-04',
        ['v4:V5-4:light','v4:V5-4:condition','v4:V5-4:mechanism-comparison'],tail,[
        ('v4:V5-4:light','visibility','유우','손이 잘 보인다고 그쪽에서 잠글 수는 없잖아. 그쪽이 볼 수 있는 데인지부터 골라'),
        ('v4:V5-4:condition','rescue','아카리','수습하는 동작은 그다음이에요. 처음에 뭘 잡으셨는지는 더 묻고요')])

    wall=scenes['04-T02f']; rule=next(i for i,row in enumerate(wall.body) if row.startswith('정답은 **04-I07b'))
    tail=graph.lines(wall,rule+1,len(wall.body),tail)
    tail=nonstop(wall,'T4-NS-REV07','벽이 생기면 받침도 따라왔나','정답은 **04-I07b',
        ['v4:V5-4:photos','v4:V5-4:handover','v4:V5-4:mechanism-comparison'],tail,[
        ('v4:V5-4:photos','date','레이','그것은 무엇이 생겼는지의 기록입니다. 어떤 힘으로 끝 고정이 됐는지는 아니죠.'),
        ('v4:V5-4:handover','watch','코토','제가 그때 본 분을 묻는 게 아닙니다. 저 문이 고정구에 닿을 수 있었는지 봐 주세요')],('눌렸다면','눌'))

    remote=scenes['04-T02d']; objects=remote.body.index('#### 물체 선택 — 아직 도면에 없는 것')
    after=next(i for i in range(objects+1,len(remote.body)) if SAY.match(remote.body[i]))
    tail=graph.lines(remote,after,len(remote.body),tail)
    tail=tabs(remote,objects,after,'당기는 가설에서 실제로 제시한 물체와 힘을 확인한다',[
        ('손잡이만 출입구 쪽으로 당긴다',after,after,'쇼','손잡이가 중간 받침에서 멎습니다. 끝 고정까지 향한 선은 여기서 끊깁니다.'),
        ('받침에 같은 방향의 당기는 힘만 붙인다',after,after,'사츠키','어느 쪽으로 들어 올렸는지부터 봐. 받침 드는 것하고 미는 걸 한 방향에 붙이지 마.'),
        ('별도의 줄을 가설 그림에 더한다',after,after,'미오','추가 장치가 필요한 가설로 남길게. 그림에 그린 줄을 현장에서 찾은 물건으로 등록하지는 않아.')],
        tail,'remote-pull-hypotheses')
    rule=next(i for i,row in enumerate(remote.body) if row.startswith('E4-04의 **중간'))
    tail=graph.lines(remote,rule+1,objects,tail)
    tail=nonstop(remote,'T4-NS-REV06','당겨서 닫히는 한 동작이라면','E4-04의 **중간',
        ['v4:V5-4:light','v4:V5-4:handover','v4:V5-4:mechanism-comparison'],tail,[
        ('v4:V5-4:light','visible','유우','내가 안 보고 닫았다는 말이 아니라, 여기 서서 보고 닫았는지가 궁금한 거야'),
        ('v4:V5-4:handover','stairs','쇼','가능한 조작과 특정 시간에 함께 걸은 기록은 다른 칸에 놓겠습니다.')])

    original=scenes['04-T02']; compare=original.body.index('#### 재현 대조 — 구조하는 손이 남긴 자국?')
    point=original.body.index('#### 지점 지목')
    after=next(i for i in range(point+1,len(original.body)) if SAY.match(original.body[i]))
    tail=graph.lines(original,after,len(original.body),tail)
    ident='T4-SP-REV01'; image=MINE_ART+'inspection-latch-section.svg'; ref=original.source(original.line+point+1)
    regions=[('latch','원래 덮개의 외부 고정',(.61,.45,.84,.72),'',''),
             ('wall','새 벽의 모서리',(.08,.08,.31,.34),'레이','제가 만든 공간의 모서리입니다. 원래 장비의 고정 조작부와 구별하십시오.'),
             ('door','생성된 수납실 문',(.33,.08,.52,.34),'미오','이건 들어가서 연 문이야. 밖에서 금속을 고정한 부분부터 찾아.'),
             ('hand','안쪽 손이 걸린 가장자리',(.15,.66,.48,.88),'나나','제가 손을 본 쪽이에요. 고정을 움직이는 곳은 바깥에 따로 있었어요.')]
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':['v4:V5-4:latch','v4:E4-13'],
        'stage':{'id':ident,'kind':'spot','v4':True,'question':'물속에 있던 사람이 혼자 완성할 수 없었던 조작이 남은 지점은?',
                 'image':image,'answerRegionId':'latch','regions':[{'id':key,'label':label,'wrongVariant':key,
                    'polygon':[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]} for key,label,(x0,y0,x1,y1),*unused in regions]},
        'queues':{'wrongVariants':[{'cause':key,'script':[{'id':ident+':'+key,'type':'say','actor':SPEAKERS[actor],
            'speaker':actor,'text':text,'source':ref}]} for key,_,_,actor,text in regions if actor]}}
    tail=graph.add('rev:04:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    match_at=next(i for i in range(compare,point) if original.body[i].startswith('플레이어는 E4-13'))
    after=next(i for i in range(match_at,point) if SAY.match(original.body[i]))
    tail=graph.lines(original,after,point,tail)
    choices=[('T4-QA-REV04','구조 동작의 힘은 어느 방향이었나?',[
        ('중간 받침을 들고 이미 걸린 고정을 위로 연다','',''),
        ('아래로 눌러 끝 고정을 새로 건다','아카리','구조 때 이미 걸린 장치를 위로 열었어요. 새로 끝 고정을 누른 것은 아니에요.')],0),
        ('T4-QA-REV03','고정을 올리기 전에 걸린 상태를 직접 본 사람은?',[
        ('미오와 아카리','',''),('앞문에 남은 사츠키까지 세 명','사츠키','나는 앞문에 있었어. 안으로 들어간 목격자 하나 더 넣지 마.')],0),
        ('T4-QA-REV02','나나가 수습 직후 찍은 사진으로 확인할 것은?',[
        ('두 번째 눌림의 형성 시각','나나','몸을 꺼내기 전에는 사진을 찍지 않았어요.'),
        ('수습 뒤 손목 고리의 연속','','')],1)]
    for ident,question,options,answer in choices:
        tail=choice(ident,original,match_at,question,options,answer,
                    ['v4:E4-13','v4:V5-4:rescue-comparison'],tail)
    tail=graph.lines(original,compare+1,match_at,tail)
    return tail


def chapter_four_daily(graph,scenes,tail):
    return life_route(graph,scenes,[ident for ident in scenes if ident.startswith('04-D00')],tail)


def chapter_four_entry(scenes,visibility_objects,end_objects):
    graph = CampaignGraph()
    tasks = {}
    dead = ['kaede', 'taiga', 'ai', 'rin', 'sora', 'riku', 'ken', 'haruka']
    seats = [name for name in SPEAKERS.values() if name != 'lappy']
    evidence = {
        'v4:V5-4:condition': ('발견·구조·사망 확인 기록', '발견 때는 물가의 손만 보였다. 쇼는 구조 뒤 마른 바닥에서 생존 반응을 확인했고, 응급 처치 중 다시 사망을 확인했다.'),
        'v4:V5-4:photos': ('전날 홀과 당일의 장소 사진', '전날 사진에는 넓은 홀, 당일에는 생긴 벽이 보인다. 두 사진의 정면만으로 벽 뒤의 구조를 확인할 수 없다.'),
        'v4:E4-13': ('카메라 끈의 두 눌림', '입실 때부터 손목에 걸렸던 끈에 서로 떨어진 두 눌림이 있다. 좁은 눌림은 첫 받침, 넓은 눌림은 바깥에서 다시 넘긴 위치에 대응한다.'),
        'v4:V5-4:handover': ('앞문과 계단의 관찰 교대', '미오와 나나가 앞문을 맡다가 벤치 쪽 두 사람이 일어나는 것을 본 뒤 입실했다. 유우는 계단에서 만났으며 앞문에서 나온 순간을 보지 않았다.'),
        'v4:E4-08': ('안쪽 문 뒤의 끝', '생긴 벽 안의 수납 구획은 바깥으로 이어지지 않는다. 안쪽의 막힌 바닥과 외벽의 고정 설비 위치를 같이 확인했다.'),
        'v4:V5-4:light': ('통로 조명과 차폐의 경계', '본체가 그늘에 있을 때 기본 그림자가 움직였고 밝은 선을 넘자 중단됐다. 래피는 힘이 커져도 빛의 조건이 없어지지 않는다고 답했다. 당시 벤치와 복도 교대는 별도 관찰로 대조한다.'),
        'v4:V5-4:latch': ('덮개의 첫 받침과 바깥 고정구', '덮개를 놓으면 첫 받침에서 멈춘다. 끝 고정까지 가려면 바깥에서 받침을 들어 넘겨야 한다. 안에서는 고정구까지 손이 닿지 않는다.'),
        'v4:V5-4:camera': ('젖은 카메라와 보관 사진', '젖은 카메라에서 확보한 두 사진은 서로 다른 때다. 젖었다는 사실만으로 끈의 눌림이 어떤 부품에서 났는지 확인할 수 없다.'),
    }
    end = graph.add('rev:04:excerpt-end', type='end')
    opening, trial = scenes['04-T0A'], scenes['04-T00']
    round_at = trial.body.index('#### 논스톱 — 사진이 같은 날짜라고 해도')
    rule = next(i for i in range(round_at, len(trial.body)) if trial.body[i].startswith('04-I01의 두 장소 사진'))
    geometry = trial.body.index('#### 공간 대조 — 같은 단어로 부른 두 문')
    source = trial.source(trial.line + rule + 1)
    timing = scenes['04-T01']
    timing_round = timing.body.index('#### 논스톱 — 같이 있었다는 말이 시작된 곳')
    timing_rule = next(i for i,row in enumerate(timing.body) if row.startswith('04-I03의 계단 시야'))
    panic_at = timing.body.index('#### 패닉 — 구조, 닫힘, 시각')
    panic_rule = next(i for i,row in enumerate(timing.body) if row.startswith('정답은 발견·구조·사망'))
    medical_at = timing.body.index('#### 기록 대조 — 이마의 상처를 먼저 놓으면')
    medical_rule = next(i for i,row in enumerate(timing.body) if row.startswith('플레이어가 E4-01에서'))
    bench_at = timing.body.index('#### 논스톱 동의 — 벤치에서 본 걸 서로에게 맡겼다면')
    panic_id = 'T4-PN-REV01'
    timing_cards = [{'id':key,'name':evidence[key][0],'text':evidence[key][1]}
                    for key in ('v4:V5-4:handover','v4:V5-4:photos','v4:V5-4:condition')]
    lanes = [{'id':label,'actor':SPEAKERS[speaker],'speaker':speaker,'lines':[]}
             for label,speaker in zip(('왼쪽','가운데','오른쪽'),('쇼','아카리','코토'))]
    panic_rows = []
    for offset in range(panic_at+1,panic_rule):
        cells = [cell.strip() for cell in timing.body[offset].strip('|').split('|')]
        if len(cells)!=4 or not cells[0].isdigit():
            continue
        for index,(lane,spoken) in enumerate(zip(lanes,cells[1:])):
            beat = int(cells[0])
            weak = (beat,index)==(3,2)
            ref = timing.source(timing.line+offset+1)
            row = debate_statement(panic_id,f'{index}:{beat}',lane['speaker'],spoken.removesuffix(' 약점.'),ref,
                                   'weak' if weak else 'plain','v4:V5-4:condition' if weak else '')
            panic_rows.append(row)
            lane['lines'].append(row['id'])
            if '[큰 소리]' in spoken:
                noise = debate_statement(panic_id,'noise',lane['speaker'],spoken,ref,'noise')
                noise.update(noiseRole='loud',noiseDurability=2,hostStatement=row['id'])
                panic_rows.append(noise)
    assert len(panic_rows)==13 and all(len(lane['lines'])==4 for lane in lanes)
    tasks[panic_id] = {'taskId':panic_id,'ready':True,'requiresEvidence':[card['id'] for card in timing_cards],
        'stage':{'id':panic_id,'kind':'panic','v4':True,'title':'구조, 닫힘, 시각','lines':panic_rows,
                 'options':timing_cards,'filterOwnedEvidence':True},
        'debate':{'id':panic_id,'kind':'panic','lines':panic_rows,'bullets':timing_cards,'lanes':lanes,'synchronizedBeats':True},
        'queues':{}}
    medical_id = 'T4-QA-REV01'
    medical_source = timing.source(timing.line+medical_rule+1)
    medical_options = (
        ('이마 손상이 사인이다','sho','접촉 손상과 주사인은 다릅니다. 익사를 확인한 기록을 펴십시오.'),
        ('구조 뒤에도 반응했고 사망 확인은 그다음이다','',''),
        ('구조자가 바로 치명 행위를 했다','akari','제가 도착했을 때 이미 잠겨 있었어요. 열었던 동작과 잠긴 때를 나눠 주세요.'),
        ('컵을 받을 때 다치지 않았음이 확인됐다','nana','제가 확인한 것은 그분과 대화한 일이에요. 상처가 없다고 살펴본 적은 없어요.'),
    )
    tasks[medical_id] = {'taskId':medical_id,'ready':True,'requiresEvidence':['v4:V5-4:condition'],
        'stage':{'id':medical_id,'kind':'choice','v4':True,'answer':1,
                 'question':'검안에서 확인된 순서는 어느 쪽인가?',
                 'options':[label for label,_,_ in medical_options]},
        'queues':{'wrongVariants':[{'optionIndex':index,'script':[{'id':f'{medical_id}:{index}','type':'say',
                 'actor':actor,'speaker':next(name for name,slug in SPEAKERS.items() if slug==actor),
                 'text':reply,'source':medical_source}]} for index,(_,actor,reply) in enumerate(medical_options) if actor]}}
    after_bench = next(i for i,row in enumerate(timing.body) if row.startswith('04-I03의 앞문과 벤치 자리'))
    latch = scenes['04-T02']
    latch_first = latch.body.index('#### 논스톱 — 물이 밀어 닫았다면')
    latch_first_rule = next(i for i,row in enumerate(latch.body) if row.startswith('04-D01 정상 점검과'))
    latch_second = latch.body.index('#### 논스톱 — 먼저 들어갔다는 말의 나머지')
    latch_second_rule = next(i for i,row in enumerate(latch.body) if row.startswith('04-I08에서 비교한'))
    latch_end = latch.body.index('#### 재현 대조 — 구조하는 손이 남긴 자국?')
    evidence.update({
        'v4:V5-4:mechanism-comparison':('새 벽과 두 고정 동작의 접촉 대조','새 문과 원래 금속 고정구는 닿지 않는다. 중간 받침을 바깥에서 들어 넘긴 뒤 끝 고정에 닿아야 두 접촉 자국을 설명할 수 있다. 추가 연결 부품은 확인되지 않았다.'),
        'v4:V5-4:rescue-comparison':('구조 방향과 두 압착의 대조','수습 사진은 손목 고리를 보여 준다. 미오와 아카리는 올리기 전 끝 고정이 걸린 것을 보았다. 마찰·단순 하강·뒤집기를 검토해도 두 압착을 구조 때 만들려면 별도의 바깥 끝 고정 동작이 필요하다.'),
        'v4:V5-4:promise-comparison':('면담 전 약속·밖의 대기·조작 조건','해치지 않겠다는 말은 레이의 말이며 강제 계약이 아니다. 하루카는 나오면 직접 말하고 안에 있을 때 물을 것이 있으면 큰 소리로 부르라고 했다. 미오와 나나는 밖에서 기다렸고 실제 응답도 들었다. 기다린 선택은 바깥 받침을 들어 넘겨 닫은 동작과 다르다.'),
        'v4:V5-4:continuous-rescue':('구조의 연속 관찰과 압흔 대조','나나는 손목을 물가에서 바닥까지 계속 받쳤고 아카리는 반대쪽을 받았다. 쇼의 반응 확인은 마른 바닥에서 시작됐다. 첫 시도의 기억은 아카리만 보고하며 현재 수습 사진과 별개다. 받치고 올리는 방향만으로 두 압착을 만들 수 없어 별도의 끝 고정 동작이 필요하다.'),
    })
    identity_checkpoint=chapter_four_identity_hearing(graph,scenes,tasks,evidence,dead,seats,end,visibility_objects,end_objects)
    physical_checkpoint=chapter_four_physical_hearing(graph,scenes,tasks,evidence,dead,seats,identity_checkpoint)
    tail = physical_checkpoint
    sections = (
        (timing,bench_at,after_bench,len(timing.body),'T4-NS-REV03','벤치에서 본 걸 서로에게 맡겼다면',
         '5','agree',('v4:V5-4:light','v4:V5-4:photos','v4:V5-4:handover'),
         '나나','그 빛이 언제 문 앞을 가로질렀는지는 여기서 얘기하지 않았어요.'),
        (latch,latch_first,latch_first_rule,latch_second,'T4-NS-REV04','물이 밀어 닫았다면',
         '4','weak',('v4:V5-4:camera','v4:V5-4:latch','v4:E4-13'),
         '쇼','두 자국이 어느 부품과 맞는지까지 비교하십시오.'),
        (latch,latch_second,latch_second_rule,latch_end,'T4-NS-REV05','먼저 들어갔다는 말의 나머지',
         '4','weak',('v4:V5-4:handover','v4:E4-13','v4:V5-4:latch'),
         '코토','같이 들어간 때를 다시 묻는 것이 아닙니다. 그 안에서 고정할 수 있었는지 보여 주세요.'),
    )
    for segment,heading,segment_rule,stop,task_id,title,answer_index,kind,ammo,actor,reply in reversed(sections):
        options = [{'id':key,'name':evidence[key][0],'text':evidence[key][1]} for key in ammo]
        rows = []
        for offset in range(heading+1,segment_rule):
            if match := STMT.match(segment.body[offset]):
                index,speaker,raw,_ = match.groups()
                weak = index==answer_index and kind=='weak'
                row = debate_statement(task_id,index,speaker,raw,segment.source(segment.line+offset+1),
                                       'weak' if weak else 'plain',ammo[-1] if weak else '')
                if index==answer_index and kind=='agree':
                    word, = re.findall(r'\*\*([^*]+)\*\*',raw)
                    row.update(kind='agree',agree=ammo[-1],agreeTarget={'word':word,'glyphStart':row['text'].index(word)})
                rows.append(row)
        assert sum(row['kind'] in {'weak','agree'} for row in rows)==1
        segment_source = segment.source(segment.line+segment_rule+1)
        tasks[task_id] = {'taskId':task_id,'ready':True,'requiresEvidence':list(ammo),
            'stage':{'id':task_id,'v4':True,'kind':'nonstop','title':title,'lines':rows,
                     'options':options,'authoredAmmo':list(ammo),'filterOwnedEvidence':True,
                     'wrongCards':{ammo[0]:'different-record'}},
            'debate':{'id':task_id,'kind':'nonstop','lines':rows,'bullets':options},
            'queues':{'wrongVariants':[{'cause':'different-record','script':[{'id':task_id+':different-record','type':'say',
                       'actor':SPEAKERS[actor],'speaker':actor,'text':reply,'source':segment_source}]}]}}
        tail = graph.lines(segment,segment_rule+1,stop,tail)
        tail = graph.add(f'rev:04:{task_id}',type='task',taskId=task_id,trialDead=dead,seats=seats,
                         source=segment_source,success=tail,next=tail)
        if task_id=='T4-NS-REV04':
            tail = graph.lines(segment,0,heading,tail)
            for key in ('04-T01a','04-T01b'):
                transition = scenes[key]
                tail = graph.lines(transition,0,len(transition.body),tail)
    tail = graph.lines(timing,medical_rule+1,bench_at,tail)
    tail = graph.add('rev:04:medical-sequence-choice',type='task',taskId=medical_id,trialDead=dead,seats=seats,
                     source=medical_source,success=tail,next=tail)
    tail = graph.lines(timing,medical_at+1,medical_rule,tail)
    tail = graph.lines(timing,panic_rule+1,medical_at,tail)
    tail = graph.add('rev:04:rescue-timing-panic',type='task',taskId=panic_id,trialDead=dead,seats=seats,
                     source=timing.source(timing.line+panic_at+1),success=tail,next=tail)
    tail = graph.lines(timing,timing_rule+1,panic_at,tail)
    timing_id = 'T4-NS-REV02'
    timing_rows = []
    for offset in range(timing_round+1,timing_rule):
        if match := STMT.match(timing.body[offset]):
            index,speaker,text,_ = match.groups()
            weak = index=='5'
            timing_rows.append(debate_statement(timing_id,index,speaker,text,timing.source(timing.line+offset+1),
                                                'weak' if weak else 'plain','v4:V5-4:handover' if weak else ''))
    assert len(timing_rows)==14
    timing_source = timing.source(timing.line+timing_rule+1)
    _, correction = re.findall(r'“([^”]+)”',timing.body[timing_rule])
    tasks[timing_id] = {'taskId':timing_id,'ready':True,'requiresEvidence':[card['id'] for card in timing_cards],
        'stage':{'id':timing_id,'kind':'nonstop','v4':True,'title':'같이 있었다는 말이 시작된 곳','lines':timing_rows,
                 'options':timing_cards,'authoredAmmo':[card['id'] for card in timing_cards],'filterOwnedEvidence':True,
                 'wrongCards':{'v4:V5-4:photos':'picture-only'}},
        'debate':{'id':timing_id,'kind':'nonstop','lines':timing_rows,'bullets':timing_cards},
        'queues':{'wrongVariants':[{'cause':'picture-only','script':[{'id':timing_id+':picture-only','type':'say',
                   'actor':'mio','speaker':'미오','text':correction,'source':timing_source}]}]}}
    tail = graph.add('rev:04:meeting-timing-nonstop',type='task',taskId=timing_id,trialDead=dead,seats=seats,
                     source=timing_source,success=tail,next=tail)
    tail = graph.lines(timing,0,timing_round,tail)
    link = scenes['04-T00b']
    tail = graph.lines(link,0,len(link.body),tail)
    link = scenes['04-T00a']
    tail = graph.lines(link,0,len(link.body),tail)
    photo_panic = link.body.index('#### 패닉 — 동시에 가리킨 사람')
    photo_rule = next(i for i,row in enumerate(link.body) if row.startswith('04-I01의 **하루카 카메라'))
    photo_ref = link.source(link.line + photo_rule + 1)
    photo_id = 'T4-PN-REV03'
    comparison = 'v4:V5-4:photo-limits'
    source_photo, wrist_photo = 'v4:V5-4:photos', 'v4:E4-13'
    cards = [{'id':key,'name':evidence[key][0],'text':evidence[key][1]} for key in (source_photo,wrist_photo)]
    cards.append({'id':comparison,'name':'장소 사진과 수습 사진',
                  'text':'하루카가 찍은 두 장소 사진과 나나가 수습 뒤 찍은 손목 사진은 촬영자와 시점이 다르다.'})
    lanes = [{'id':label,'actor':SPEAKERS[speaker],'speaker':speaker,'lines':[]}
             for label,speaker in zip(('왼쪽','가운데','오른쪽'),('유우','코토','나나'),strict=True)]
    rows = []
    for offset in range(photo_panic + 1, photo_rule):
        cells = [cell.strip() for cell in link.body[offset].strip('|').split('|')]
        if len(cells)!=4 or not cells[0].isdigit():
            continue
        for index,(lane,raw) in enumerate(zip(lanes,cells[1:],strict=True)):
            weak = '[약점]' in raw
            raw = raw.replace('[약점] ','')
            ref = link.source(link.line + offset + 1)
            row = debate_statement(photo_id,f'{index}:{cells[0]}',lane['speaker'],raw,ref,
                                   'weak' if weak else 'plain',comparison if weak else '')
            rows.append(row)
            lane['lines'].append(row['id'])
            if '[큰 소리]' in raw:
                noise = debate_statement(photo_id,'noise',lane['speaker'],raw,ref,'noise')
                rows.append(dict(noise,noiseRole='loud',noiseDurability=2,hostStatement=row['id']))
    assert all(len(lane['lines'])==7 for lane in lanes) and len(rows)==22
    wrongs = (
        (source_photo,'location-only','나나','제가 찍은 건 꺼낸 뒤 사진이에요. 장소가 같은지부터 묻는 건 아니에요.'),
        (wrist_photo,'wrist-only','코토','그 손목 사진은 알겠어요. 그전에 홀을 찍은 분은 누구예요?'),
    )
    tasks[photo_id] = {'taskId':photo_id,'ready':True,'requiresEvidence':[card['id'] for card in cards],
        'stage':{'id':photo_id,'kind':'panic','v4':True,'title':'동시에 가리킨 사람','lines':rows,
                 'options':cards,'filterOwnedEvidence':True,'wrongCards':{key:cause for key,cause,_,_ in wrongs}},
        'debate':{'id':photo_id,'kind':'panic','lines':rows,'bullets':cards,'lanes':lanes,'synchronizedBeats':True},
        'queues':{'wrongVariants':[{'cause':cause,'script':[{'id':photo_id+':'+cause,'type':'say',
            'actor':SPEAKERS[speaker],'speaker':speaker,'text':text,'source':photo_ref}]}
            for _,cause,speaker,text in wrongs]}}

    def compare_photos(following):
        discussion = graph.add('rev:04:'+photo_id,type='task',taskId=photo_id,trialDead=dead,seats=seats,
                               source=photo_ref,next=following,success=following)
        return graph.add('rev:04:photo-limits',type='evidence',evidenceId=comparison,
                         name=cards[-1]['name'],text=cards[-1]['text'],source=photo_ref,next=discussion)

    tail = graph.insert_before_source_line(tail,photo_ref,compare_photos)
    handover_at = trial.body.index('### 대면 — 앞문을 맡았던 순간')
    tail = graph.lines(trial,handover_at+1,len(trial.body),tail)
    for index,(question,answer_label,wrong_label,actor,reply) in reversed(list(enumerate((
        ('두 사진에서 같은 위치에 있던 출입구는?', '복도에서 들어오는 기존 출입구', '나중에 생긴 안쪽 문','rei','제가 만든 문은 오른쪽 안쪽 벽에 있습니다. 원래 출입구와 떨어져 있습니다.'),
        ('그날 사진에서 새로 생긴 것은?', '사진 오른쪽의 안쪽 문', '외벽의 원래 점검구','rei','제가 만든 것은 사진 오른쪽의 안쪽 벽입니다. 밖의 창은 그대로 있었습니다.'),
        ('외벽에서 처음부터 열리지 않던 점검구는?', '원래 외벽의 고정 점검구', '유우가 서 있던 계단','mio','그건 유우가 확인해 줄 수 있는 마지막 행이야. 여기에서 안쪽 문이 보이는지부터 보자.'),
        ('앞문의 시야를 언제 이어받았어?', '벤치의 두 사람이 고개를 들고 시야가 겹칠 때', '둘이 일어나기 전','akari','제가 문을 본 건 일어난 뒤예요. 그전에는 미오 씨와 나나 씨에게 물어보세요.'),
    )))):
        ident = f'rev:04:door-comparison:{index}'
        offset = handover_at if index==3 else geometry
        ref = trial.source(trial.line+offset+1)
        speaker = next(name for name,slug in SPEAKERS.items() if slug==actor)
        retry = graph.add(ident+':retry',type='say',actor=actor,speaker=speaker,text=reply,source=ref,next=ident)
        picks = [{'id':'supported','label':answer_label,'to':tail},{'id':'unsupported','label':wrong_label,'to':retry}]
        if index%2==0:
            picks.reverse()
        tail = graph.add(ident,type='menu',q=question,options=picks,source=ref)
    tail = graph.lines(trial, rule + 1, geometry, tail)
    task = 'T4-NS-REV01'
    answer = 'v4:E4-08'
    ammo = ['v4:V5-4:photos', 'v4:V5-4:handover', answer]
    options = [{'id': key, 'name': evidence[key][0], 'text': evidence[key][1]} for key in ammo]
    rows = []
    for i in range(round_at + 1, rule):
        if match := STMT.match(trial.body[i]):
            index, speaker, text, role = match.groups()
            weak = index == '4'
            assert weak == ('논파점' in role)
            rows.append(debate_statement(task, index, speaker, text, trial.source(trial.line + i + 1),
                                         'weak' if weak else 'plain', answer if weak else ''))
    assert len(rows) == 15
    correction, = re.findall(r'“([^”]+)”', trial.body[rule])
    tasks[task] = {'taskId': task, 'ready': True, 'requiresEvidence': ammo,
                   'stage': {'id': task, 'kind': 'nonstop', 'v4': True, 'title': '사진이 같은 날짜라고 해도',
                             'lines': rows, 'options': options, 'authoredAmmo': ammo, 'filterOwnedEvidence': True,
                             'wrongCards': {ammo[0]: 'photo-only'}},
                   'debate': {'id': task, 'kind': 'nonstop', 'lines': rows, 'bullets': options},
                   'queues': {'wrongVariants': [{'cause': 'photo-only', 'script': [
                       {'type': 'say', 'id': task + ':wrong', 'actor': 'mio', 'speaker': '미오', 'text': correction, 'source': source}]}]}}
    tail = graph.add('rev:04:location-nonstop', type='task', taskId=task, trialDead=dead, seats=seats,
                     source=source, success=tail, next=tail)
    first_read = [i for i, raw in enumerate(opening.body) if BULLET.match(raw)]
    assert len(first_read) == 3
    tail = graph.lines(opening, first_read[-1] + 1, len(opening.body), tail)
    answers = [('나나', '제가 손을 잡았을 때 반응하셨어요. 그 전에 어떤 몸이었는지와는 다른 때예요.'),
               ('레이', '제가 알았던 기억과 그분이 지금 결정한 일은 같은 줄에 둘 수 없습니다.'),
               ('쇼', '입실과 발견, 사망 확인의 세 줄을 펴겠습니다. 다른 질문까지 답을 얻은 것은 아닙니다.')]
    picks = []
    for index, (offset, (speaker, answer_line)) in enumerate(zip(first_read, answers)):
        reaction = graph.add(f'rev:04:first-reading:{index}', type='say', actor=SPEAKERS[speaker], speaker=speaker,
                             text=answer_line, source=opening.source(opening.line + offset + 1), next=tail)
        picks.append({'id': str(index), 'label': BULLET.match(opening.body[offset])[1], 'to': reaction})
    tail = graph.add('rev:04:first-reading-menu', type='menu', q='어느 기록부터 펼칠까?', options=picks)
    tail = graph.lines(opening, 0, first_read[0], tail)
    court = graph.add('rev:04:court-entry', type='stage', enterCourt=True, next=tail)
    placements = [('04-I00', 'v4:V5-4:condition', 'inspection_hall_changed', [0, 1.25, 2.08]),
                  ('04-I01', 'v4:V5-4:photos', 'inspection_hall_changed', [-1.2, 1.25, 2.08]),
                  ('04-I02', 'v4:E4-13', 'inspection_hall_changed', [1.2, 1.2, 2.08]),
                  ('04-I03', 'v4:V5-4:handover', 'lower_stairway', [0, 1.25, 2.08]),
                  ('04-I04', 'v4:E4-08', 'inspection_hall_normal', [0, 1.25, 2.08]),
                  ('04-I05', 'v4:V5-4:light', 'lower_stairway', [-1.15,1.22,.9]),
                  ('04-I06', 'v4:V5-4:camera', 'inspection_hall_changed', [-1.1,1.15,-1.1]),
                  ('04-I07', 'v4:V5-4:latch', 'inspection_hall_normal', [.95,1.2,-1.05]),
                  ('04-I07b','v4:V5-4:mechanism-comparison','inspection_hall_normal',[1.8,1.2,-1.5]),
                  ('04-I09a','v4:V5-4:rescue-comparison','maintenance_workshop',[-.8,1.2,1.2]),
                  ('04-I08c','v4:V5-4:promise-comparison','maintenance_workshop',[.8,1.2,1.2]),
                  ('04-I09b','v4:V5-4:continuous-rescue','maintenance_workshop',[1.5,1.2,-1.1])]
    spots = []
    for scene_id, key, room, position in placements:
        scene = scenes[scene_id]
        name, facts = evidence[key]
        done = graph.add('rev:04:return:' + key, type='return')
        record = graph.add('rev:04:record:' + key, type='evidence', evidenceId=key, name=name, text=facts,
                           source=scene.source(scene.line), next=done)
        supplemental={
            'v4:V5-4:condition':['04-I00a'],'v4:V5-4:handover':['04-I03a','04-I03b'],
            'v4:E4-08':['04-I04a','04-I08a','04-I08b'],'v4:V5-4:light':['04-I05a','04-I05b'],
            'v4:V5-4:camera':['04-I06a'],'v4:V5-4:latch':['04-I07a','04-I08'],
        }
        record=supplemental_inspection(graph,scenes,supplemental.get(key,()),record)
        if key == 'v4:E4-08':
            check = 'rev:04:verify-exterior-end'
            wrong = graph.add('rev:04:photo-does-not-show-end', type='say', actor='sho', speaker='쇼',
                              text='전날 사진은 기존 외벽의 모서리를 보여 줍니다. 그 뒤에 생긴 벽의 안쪽을 직접 확인하십시오.',
                              source=scene.source(scene.line), next=check)
            record = graph.add(check, type='menu', q='안쪽 문이 바깥으로 이어지는지 무엇으로 확인할까?',
                               options=[{'id': 'front-photo', 'label': '전날 홀 정면 사진만 본다', 'to': wrong},
                                        {'id': 'both-ends', 'label': '구획의 끝과 외벽 고정 설비를 대조한다', 'to': record}])
        if key=='v4:V5-4:rescue-comparison':
            select=scene.body.index('### 먼저 확인할 가설')
            branches=[i for i,row in enumerate(scene.body) if row.startswith('#### ')]
            join=scene.body.index('### 덮개를 다시 닫아 둔 뒤')
            assert len(branches)==3
            target=graph.lines(scene,join+1,len(scene.body),record)
            menu='rev:04:rescue-hypotheses'
            options=[]
            for i,(at,stop) in enumerate(zip(branches,[*branches[1:],join])):
                flag='04-I09a:'+str(i)
                checked=graph.add(menu+':checked:'+str(i),type='say',actor='mio',speaker='미오',
                    text=('마찰할 수 있는 것과 끝 고정에 새로 걸리는 동작을 나누어 남길게.',
                          '단순 하강의 중간 멈춤과 바깥에서 넘겨 닫는 끝 고정을 다른 칸에 둘게.',
                          '발견 때의 직접 관찰과 수습 사진, 실물의 눌림은 다른 자료야.')[i],
                    source=scene.source(scene.line+at+1),set={flag:True},next=menu)
                entry=graph.lines(scene,at+1,stop,checked)
                if i==1:
                    prompt=menu+':fall-direction'
                    retry=graph.add(prompt+':retry',type='say',actor='sho',speaker='쇼',
                        text='손을 놓아 중간에서 받치는 것과 바깥에 걸어 놓은 뒤 놓는 것은 다릅니다.',
                        source=scene.source(scene.line+at+1),next=prompt)
                    entry=graph.add(prompt,type='menu',q='단순 하강과 별도 끝 고정에 맞는 표지는?',source=scene.source(scene.line+at+1),
                        options=[{'id':'reversed','label':'단순 하강에 끝 고정, 추가 조작에 중간 멈춤','to':retry},
                                 {'id':'separate','label':'단순 하강에 중간 멈춤, 바깥 추가 조작에 끝 고정','to':entry}])
                if i==2:
                    prompt=menu+':photo-boundary'
                    retry=graph.add(prompt+':retry',type='say',actor='mio',speaker='미오',
                        text='사진에 없는 끈 끝을 그려 넣지 않을게. 발견 위치와 수습 사진, 물체를 나눠 놓자.',
                        source=scene.source(scene.line+at+1),next=prompt)
                    entry=graph.add(prompt,type='menu',q='사진과 실물로 확인한 범위는?',source=scene.source(scene.line+at+1),
                        options=[{'id':'photo-all','label':'수습 뒤 사진으로 고정 당시의 방향 전체 복원','to':retry},
                                 {'id':'object-photo','label':'실물 눌림을 구조 전 사진으로 분류','to':retry},
                                 {'id':'separate','label':'발견 직접 관찰 / 수습 뒤 사진 / 실물 눌림 분리','to':entry}])
                options.append({'id':str(i),'label':scene.body[at][5:],'to':entry,'requires':{flag:False}})
            options.append({'id':'continue','label':'세 비교를 마치고 기록한다','to':target,
                            'requires':{'04-I09a:'+str(i):True for i in range(3)}})
            entry=graph.add(menu,type='menu',q='구조 동작으로 두 자국을 설명할 수 있을까?',options=options,
                            source=scene.source(scene.line+select+1))
            entry=graph.lines(scene,0,select,entry)
            setup=scenes['04-I09']
            entry=graph.lines(setup,0,len(setup.body),entry)
        elif key=='v4:V5-4:promise-comparison':
            at=scene.body.index('### 세 줄에 놓을 것')
            after=next(i for i in range(at+1,len(scene.body)) if SAY.match(scene.body[i]))
            target=graph.lines(scene,after,len(scene.body),record)
            menu='rev:04:promise-boundaries'
            views=[('사츠키의 목격','satsuki','사츠키','그때 레이 쪽을 보고 있었어. 그 뒤 둘이 무슨 말을 했는지까지 본 건 아니고.'),
                   ('레이가 사용한 힘','rei','레이','공간이 생긴 때와 이미 존재하던 사람이 움직인 일은 따로 확인하십시오.'),
                   ('나나가 들은 문 앞의 말','nana','나나','밖으로 나오면 직접 알려 주시겠다는 말을 들었어요. 나중에 레이 씨가 대신 전한 말하고는 달라요.')]
            options=[]
            for i,(label,actor,name,text) in enumerate(views):
                flag='04-I08c:'+str(i)
                to=graph.add(menu+':'+str(i),type='say',actor=actor,speaker=name,text=text,
                    source=scene.source(scene.line+at+1),set={flag:True},next=menu)
                options.append({'id':str(i),'label':label,'to':to,'requires':{flag:False}})
            options.append({'id':'continue','label':'약속과 관찰과 구조를 다른 칸에 남긴다','to':target,
                            'requires':{'04-I08c:'+str(i):True for i in range(3)}})
            entry=graph.add(menu,type='menu',q='누가 어느 말을 직접 확인했는지부터 묻는다',options=options,
                            source=scene.source(scene.line+at+1))
            entry=graph.lines(scene,0,at,entry)
        else:
            entry = graph.lines(scene, 0, len(scene.body), record)
        spot = {'id': key, 'label': name, 'neutralLabel': name, 'space_id': room, 'world_pos': position, 'entry': entry}
        if key == 'v4:E4-08':
            spot['requiresCards'] = ['v4:V5-4:photos']
        if key=='v4:V5-4:mechanism-comparison':
            spot['requiresCards']=['v4:V5-4:latch','v4:E4-13']
        if key=='v4:V5-4:rescue-comparison':
            spot['requiresCards']=['v4:V5-4:mechanism-comparison','v4:V5-4:condition','v4:V5-4:camera','v4:V5-4:promise-comparison']
        if key=='v4:V5-4:promise-comparison':
            spot['requiresCards']=['v4:V5-4:mechanism-comparison','v4:V5-4:handover']
        if key=='v4:V5-4:continuous-rescue':
            spot['requiresCards']=['v4:V5-4:rescue-comparison','v4:V5-4:condition']
        spots.append(spot)
    court=supplemental_inspection(graph,scenes,['04-I0A'],court)
    investigation = graph.add('rev:04:investigate', type='investigate', space_id='inspection_hall_changed',
                              spots=spots, requiredSpotIds=list(evidence), requiredCards=list(evidence), next=court)
    rescue = scenes['04-D03']
    first_attempt = next(i for i, raw in enumerate(rescue.body) if raw.startswith('나나가 잘못 잡은'))
    confirm_death = next(i for i, raw in enumerate(rescue.body) if raw.startswith('(쇼가 실제로 사망을'))
    headings = [i for i, raw in enumerate(rescue.body) if raw.startswith('#### ')]
    join = rescue.body.index('### 처음과 다른 대답')
    assert len(headings) == 2
    tail = graph.add('rev:04:death-announcement', type='stage', next=investigation,
                     source=rescue.source(rescue.line + confirm_death + 1), presentation={'actions': ['body_announcement']})
    tail = graph.lines(rescue, join + 1, confirm_death, tail)
    tail = graph.menu(rescue, '쇼가 확인하는 동안 어디에 남을까?',
                      [(rescue.body[i][5:], i + 1, j, '') for i, j in zip(headings, [headings[1], join])], tail)
    tail = graph.lines(rescue, first_attempt + 1, headings[0], tail)
    tail = graph.add('rev:04:rewind-to-rescue', type='say', actor='mio', speaker='미오', mono=True,
                     text='안에서 손을 보았다. 복도 쪽에 사람을 더 불러 달라고 하려는 순간, 아카리가 나나부터 불렀다.',
                     source=rescue.source(rescue.line + first_attempt + 1), next=tail)
    tail = graph.add('rev:04:first-rescue-attempt', type='say', actor='akari', speaker='아카리', mono=True,
                     text='나나 씨의 팔이 끼였다. 손목을 붙잡았다. 다시 돌아가면 저 손을 가장자리에서 먼저 떼게 해야 한다.',
                     source=rescue.source(rescue.line + first_attempt + 1), next=tail)
    tail = graph.lines(rescue, 0, first_attempt, tail)
    waiting = scenes['04-D02']
    ask = next(i for i, raw in enumerate(waiting.body) if raw.startswith('미오가 직접 기다리기로'))
    handover=next(i for i,row in enumerate(waiting.body) if row.startswith('레이는 계단 쪽으로 걸어간다.'))
    reply=graph.add('rev:04:front-door-handover',type='say',actor='mio',speaker='미오',mono=True,
        text='레이가 계단 쪽으로 간 뒤 유우가 합류했다. 나는 아카리와 사츠키가 고개를 들고 일어나는 것을 본 뒤 나나와 안으로 들어갔다.',
        source=waiting.source(waiting.line+handover+1),next=tail)
    entry_at=next(i for i,row in enumerate(waiting.body) if row.startswith('레이가 먼저 안으로 들어간다.'))
    reply=graph.lines(waiting,entry_at+1,handover,reply)
    reply=graph.add('rev:04:last-living-reply',type='say',actor='mio',speaker='미오',mono=True,
        text='문 안에서 하루카가 아직 얘기 중이라고 대답했다. 나는 나나와 앞문 바깥에 서 있었다. 그 뒤 레이만 나왔다.',
        source=waiting.source(waiting.line+entry_at+1),next=reply)
    reply=graph.add('rev:04:meeting-entry-observation',type='say',actor='mio',speaker='미오',mono=True,
        text='레이가 먼저 들어가고 하루카도 문을 넘었다. 입실 사진에 손목 고리와 카메라의 짧은 검은 끈이 잡혔다. 아카리와 사츠키는 바깥 벤치로 갔다.',
        source=waiting.source(waiting.line+entry_at+1),next=reply)
    reply=graph.lines(waiting,ask+1,entry_at,reply)
    waiting_paths = []
    for branch, speaker, text in zip('AB', ('하루카', '사츠키'), re.findall(r'“([^”]+)”', waiting.body[ask])):
        to = graph.add(f'rev:04:wait-reply:{branch}', type='say', actor=SPEAKERS[speaker], speaker=speaker, text=text,
                       source=waiting.source(waiting.line + ask + 1), next=reply)
        waiting_paths.append({'flag': '04-D01', 'equals': branch, 'to': to})
    assert len(waiting_paths) == 2
    tail = graph.add('rev:04:wait-reply', type='branch', cases=waiting_paths, default=reply)
    tail = graph.lines(waiting, 0, ask, tail)
    cup_at=next(i for i,row in enumerate(waiting.body) if row.startswith('미오가 면담 전의 마지막 사진'))
    tail=graph.add('rev:04:pre-meeting-cup',type='say',actor='mio',speaker='미오',mono=True,
        text='하루카가 문밖으로 한 발 나와 나나에게 새 종이컵을 받았다. 손에 물이 흐르자 자기가 닦겠다고 했다.',
        source=waiting.source(waiting.line+cup_at+1),next=tail)
    tail = graph.add('rev:04-D02:entry', type='stage', next=tail, source=waiting.source(waiting.line),
                     scene={'space': 'inspection_hall_changed', 'perspective': 'current-observation'})
    tail=life_route(graph,scenes,[ident for ident in scenes if ident.startswith('04-D01')
        and ident not in ('04-D01','04-D01a','04-D01d','04-D01b')],tail)
    generation=scenes['04-D01b']
    created=next(i for i,row in enumerate(generation.body) if row.startswith('(빈 공간에 벽이 생긴다.'))
    tail=graph.lines(generation,created+1,len(generation.body),tail)
    tail=graph.add('rev:04:generated-room-observation',type='say',actor='mio',speaker='미오',mono=True,
        text='빈 홀에 벽과 문이 생겼다. 방금 없던 방인데 오래전부터 알던 곳처럼 느껴졌다. 앞서 그린 일반 메모와 하루카의 장소 사진을 다시 보았다.',
        source=generation.source(generation.line+created+1),next=tail)
    tail=graph.add('rev:04:created-room',type='stage',scene={'space':'inspection_hall_changed'},
        source=generation.source(generation.line+created+1),next=tail)
    tail=graph.lines(generation,0,created,tail)
    tail=graph.add('rev:04:before-room',type='stage',scene={'space':'inspection_hall_normal'},
        source=generation.source(generation.line),next=tail)
    tail=life_route(graph,scenes,['04-D01a','04-D01d'],tail)
    entrance = scenes['04-D01']
    replies = []
    first_option = next(i for i, raw in enumerate(entrance.body) if BULLET.match(raw))
    for branch, offset in zip('AB', (first_option, first_option + 1)):
        label, detail = BULLET.match(entrance.body[offset]).groups()
        current = tail
        for index, (speaker, text) in reversed(list(enumerate(re.findall(r'(하루카|사츠키)\s+“([^”]+)”', detail)))):
            current = graph.add(f'rev:04:wait-option:{branch}:{index}', type='say', actor=SPEAKERS[speaker],
                                speaker=speaker, text=text, source=entrance.source(entrance.line + offset + 1), next=current)
        replies.append({'id': branch, 'label': label, 'to': current, 'set': {'04-D01': branch}})
    tail = graph.add('rev:04:wait-option', type='menu', q='입구에서 어떻게 기다릴까?', options=replies)
    tail = graph.lines(entrance, 0, first_option, tail)
    tail = graph.add('rev:04-D01:entry', type='stage', next=tail, source=entrance.source(entrance.line),
                     scene={'space': 'inspection_hall_normal', 'perspective': 'current-observation'})
    tail = graph.add('rev:04:free-before-inspection',type='menu',q='점검이 시작되기 전에 어디로 갈까?',options=[
        {'id':'chair','label':'휴게실에서 유우를 만난다','to':optional_meeting(graph,scenes['04-F01'],
            'hotel_rest_lounge','빈 의자 옆에서 어떻게 할까?',tail)},
        {'id':'skip','label':'점검실 입구로 간다','to':tail}])
    tail=chapter_four_daily(graph,scenes,tail)
    checkpoint_cards=[{'id':key,'name':name,'text':text} for key,(name,text) in evidence.items()]
    book_checkpoints=chapter_four_book_checkpoints(graph,scenes,tasks,evidence,dead,seats)
    checkpoints={}
    for name,target in [('physical-hearing',physical_checkpoint),('identity-hearing',identity_checkpoint),
                        ('route-hearing','rev:04:T4-MM-REV01'),('last-hearing','rev:04:T4-LI-REV01'),
                        ('reasoning-hearing','rev:04:T4-RE-REV01'),*book_checkpoints.items()]:
        checkpoint=graph.add('rev:04:'+name+':court-entry',type='stage',enterCourt=True,next=target)
        current_cards=checkpoint_cards+([{'id':'v4:V5-4:hand-view','name':'끝 고정 위치와 안쪽 손의 시야 대조',
            'text':'조작 위치에서 내려다볼 때 실제 손이 가려지지 않는다. 그때 실제 시선을 준 사람은 직접 묻는다.'}]
            if name in {'last-hearing','reasoning-hearing'} else [])
        for card in reversed(current_cards):
            checkpoint=graph.add('rev:04:'+name+':seed:'+card['id'],type='evidence',evidenceId=card['id'],
                                 name=card['name'],text=card['text'],next=checkpoint)
        checkpoints[name]={'entry':checkpoint,'evidence':current_cards}
    return ({'schemaVersion': 1, 'contentVersion': 'v4', 'campaignRevision': 'rewrite-v5', 'chapter': '4',
             'entry': tail, 'nodes': graph.nodes, 'trialRoster': {'dead': dead, 'seats': seats},
             'qaCheckpoints':checkpoints}, tasks)


def late_case_trial(graph, scenes, chapter, scene_id, title, rule_start, target, records, ammo,
                    wrong_speaker, next_node, dead, seats, *, round_number=1, include_intro=False, correction=None,
                    include_conclusion=True):
    scene = scenes[scene_id]
    heading = scene.body.index('#### 논스톱 — ' + title)
    rule = next(i for i in range(heading, len(scene.body)) if scene.body[i].startswith(rule_start))
    stop = next((i for i in range(rule + 1, len(scene.body)) if scene.body[i].startswith(('### ', '#### '))), len(scene.body))
    ident = f'T{chapter}-NS-REV{round_number:02}'
    options = [{'id': key, 'name': records[key][2], 'text': records[key][3]} for key in ammo]
    statements = []
    for index in range(heading + 1, rule):
        if match := STMT.match(scene.body[index]):
            row, speaker, text, role = match.groups()
            answer = ammo[-1] if int(row) == target else ''
            assert bool(answer) == ('약점' in role or '논파점' in role)
            statements.append(debate_statement(ident, row, speaker, text, scene.source(scene.line + index + 1),
                                               'weak' if answer else 'plain', answer))
    assert sum('weak' in row for row in statements) == 1
    source = scene.source(scene.line + rule + 1)
    if correction is None:
        correction = re.findall(r'“([^”]+)”', scene.body[rule])[0]
    task = {'taskId': ident, 'ready': True, 'requiresEvidence': ammo,
            'stage': {'id': ident, 'kind': 'nonstop', 'v4': True, 'title': title, 'lines': statements,
                      'options': options, 'authoredAmmo': ammo, 'filterOwnedEvidence': True,
                      'wrongCards': {ammo[0]: 'different-observation'}},
            'debate': {'id': ident, 'kind': 'nonstop', 'lines': statements, 'bullets': options},
            'queues': {'wrongVariants': [{'cause': 'different-observation', 'script': [
                {'id': ident + ':wrong', 'type': 'say', 'actor': SPEAKERS[wrong_speaker],
                 'speaker': wrong_speaker, 'text': correction, 'source': source}]}]}}
    tail = graph.lines(scene, rule + 1, stop, next_node) if include_conclusion else next_node
    node_id = f'rev:0{chapter}:first-nonstop' if round_number==1 else f'rev:0{chapter}:{ident}'
    tail = graph.add(node_id, type='task', taskId=ident, trialDead=dead, seats=seats,
                     source=source, success=tail, next=tail)
    if round_number==1 or include_intro:
        tail = graph.lines(scene, 0, heading, tail)
    return tail, {ident: task}


def late_case_investigation(graph, scenes, chapter, room, records, following, *, routes=None, prerequisites=None,
                            supplemental=None):
    spots = []
    for key, (scene_id, space, name, facts, pos) in records.items():
        scene = scenes[scene_id]
        prefix = f'rev:0{chapter}'
        done = graph.add(prefix + ':return:' + key, type='return')
        record = graph.add(prefix + ':record:' + key, type='evidence', evidenceId=key, name=name, text=facts,
                           source=scene.source(scene.line), next=done)
        record = supplemental_inspection(graph, scenes, (supplemental or {}).get(key, ()), record)
        route = (routes or {}).get(key)
        entry = route(scene, record) if route else checked_investigation(graph, scene, 0, len(scene.body), record)
        spot = {'id': key, 'label': name, 'neutralLabel': name, 'space_id': space, 'world_pos': pos, 'entry': entry}
        if required := (prerequisites or {}).get(key):
            spot['requiresCards'] = required
        spots.append(spot)
    return graph.add(f'rev:0{chapter}:investigate', type='investigate', space_id=room, spots=spots,
                     requiredSpotIds=list(records), requiredCards=list(records), next=following)


def chapter_five_cup_hearing(graph, scenes, tasks, records, dead, seats, tail):
    scene = scenes['05-T01e']
    at = next(i for i,row in enumerate(scene.body) if row.startswith('플레이어는 **두 시 사용을'))
    menu = 'rev:05:rewind-claim-boundary'
    ref = scene.source(scene.line+at+1)
    options = [
        ('14시 사용을 먼저 확정한다','나나','제가 그때 같이 있었다고 한 것은 맞아요. 사용을 직접 보지는 못했어요.'),
        ('16:52 사용을 횟수 조건만으로 확정한다','쇼','같은 날에 두 번 쓸 수 없다는 설명과, 실제로 어느 쪽에서 썼는지는 다른 판단입니다.'),
        ('두 주장이 그날 한 번의 사용 기회를 공유한다고 정리한다','','')]
    picks = []
    for index,(label,speaker,text) in enumerate(options):
        to = tail if not speaker else graph.add(f'{menu}:retry:{index}',type='say',actor=SPEAKERS[speaker],
            speaker=speaker,text=text,source=ref,next=menu)
        picks.append({'id':str(index),'label':label,'to':to})
    tail = graph.add(menu,type='menu',q='횟수 조건만으로 어디까지 확인할까?',source=ref,options=picks)
    tail = graph.lines(scene,0,at,tail)

    scene = scenes['05-T01d']
    memory = scene.body.index('### 그때 둘이 나눈 말')
    common = next(i for i in range(memory,len(scene.body)) if scene.body[i].startswith('**아카리**　말할 때마다'))
    tail = graph.lines(scene,common,len(scene.body),tail)
    lines = [
        ('A','나도 계속 보고 싶지 않다고 했어. 네가 어디까지 생각했는지는 묻지 않았고.'),
        ('B','나는 오늘 안 돌아오면 찾겠다고 했어. 보기 싫었던 게 없어져서 그런 말 한 건 아니야.'),
        ('C','나는 네가 먼저 대답하라고 했어. 내가 생각한 건 그때 네 앞에서 말하지 않았어.'),
    ]
    ref = scene.source(scene.line+memory+1)
    paths = [{'flag':'05-D03a','equals':key,'to':graph.add('rev:05:hearing-corridor-memory:'+key,
        type='say',actor='mio',speaker='미오',text=text,source=ref,next=tail)} for key,text in lines]
    repeated = graph.add('rev:05:hearing-corridor-memory:acknowledged',type='say',actor='mio',speaker='미오',
        text='응. 내가 그때 골랐던 말까지 네가 한 것처럼 적지 않을게.',source=ref,next=tail)
    repeated = graph.add('rev:05:hearing-corridor-memory:asked',type='say',actor='akari',speaker='아카리',
        text='가져오신 종이보다 먼저 말씀하신 게 있었어요. 저한테 무슨 말을 이미 하셨는지 기억하세요?',source=ref,next=repeated)
    tail = graph.add('rev:05:hearing-corridor-memory',type='branch',cases=[
        {'flag':'05-I06b','equals':'C','to':repeated},*paths],default=tail)
    tail = graph.lines(scene,0,memory,tail)

    scene = scenes['05-T01c']
    at = scene.body.index('### 누구 손에 어떤 항목을 붙이는가')
    after = next(i for i in range(at+1,len(scene.body)) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,after,len(scene.body),tail)
    menu = 'rev:05:first-open-witness'
    ref = scene.source(scene.line+at+1)
    picks = []
    for index,(label,speaker,text) in enumerate([
        ('유우가 처음 개봉을 봤다','유우','내가 문밖에 있었을 때 아카리 가방이 보인다고 다 보이는 게 아니잖아.'),
        ('사츠키가 용기를 처음 열었다','사츠키','손에 있었던 게 이거지. 내가 처음부터 열고 있었으면 그때 어디에 있었는지부터 봐.'),
        ('회수 기록만으로는 처음 개봉을 본 사람을 정할 수 없다','','')]):
        to = tail if not speaker else graph.add(f'{menu}:retry:{index}',type='say',actor=SPEAKERS[speaker],
            speaker=speaker,text=text,source=ref,next=menu)
        picks.append({'id':str(index),'label':label,'to':to})
    tail = graph.add(menu,type='menu',q='가방과 회수 사진으로 알 수 있는 범위는?',source=ref,options=picks)
    tail = graph.lines(scene,0,at,tail)

    scene = scenes['05-T01b']
    heading = scene.body.index('#### 패닉 — 내 앞에 놓이기 전')
    rule = next(i for i,row in enumerate(scene.body) if row.startswith('6박자의 큰 소리를'))
    tail = graph.lines(scene,rule+1,len(scene.body),tail)
    ident = 'T5-PN-REV02'
    lanes = [{'id':label,'actor':SPEAKERS[name],'speaker':name,'lines':[]}
             for label,name in zip(('왼쪽','가운데','오른쪽'),('유우','나나','아카리'))]
    ammo = ['v4:V5-5:mark-window','v4:V5-5:package-pieces','v4:V5-5:pour-boundary']
    cards = [{'id':key,'name':records[key][2],'text':records[key][3]} for key in ammo]
    rows = []
    for at in range(heading+1,rule):
        cells = [cell.strip() for cell in scene.body[at].strip('|').split('|')]
        if len(cells)!=4 or not cells[0].isdigit():
            continue
        beat = int(cells[0])
        for lane_index,(lane,text) in enumerate(zip(lanes,cells[1:])):
            weak = (beat,lane_index)==(7,2)
            ref = scene.source(scene.line+at+1)
            row = debate_statement(ident,f'{lane_index}:{beat}',lane['speaker'],text.replace('[약점] ',''),ref,
                'weak' if weak else 'plain',ammo[-1] if weak else '')
            rows.append(row)
            lane['lines'].append(row['id'])
            if '[큰 소리]' in text:
                loud = debate_statement(ident,'noise',lane['speaker'],text,ref,'noise')
                loud.update(noiseRole='loud',noiseDurability=2,hostStatement=row['id'])
                rows.append(loud)
    assert len(rows)==25 and all(len(lane['lines'])==8 for lane in lanes)
    ref = scene.source(scene.line+rule+1)
    tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':ammo,
        'stage':{'id':ident,'kind':'panic','v4':True,'title':'내 앞에 놓이기 전','lines':rows,'options':cards,
                 'filterOwnedEvidence':True},
        'debate':{'id':ident,'kind':'panic','lines':rows,'bullets':cards,'lanes':lanes,'synchronizedBeats':True},'queues':{}}
    tail = graph.add('rev:05:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    tail = graph.lines(scene,0,heading,tail)

    scene = scenes['05-T01a']
    at = scene.body.index('#### 상황 선택 — 부른 사람은 무엇을 할 수 있었나')
    after = next(i for i in range(at+1,len(scene.body)) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,after,len(scene.body),tail)
    menu = 'rev:05:call-and-wait'
    ref = scene.source(scene.line+at+1)
    wrong_cup = graph.add(menu+':cup',type='say',actor='mio',speaker='미오',
        text='잔 앞에 있던 사람은 확인했어. 밖으로 나가서 부른 사람과 방향은 다른 기록이야.',source=ref,next=menu)
    wrong_route = graph.add(menu+':route',type='say',actor='sho',speaker='쇼',
        text='운영동에서 유우 씨와 함께 있던 것은 앞선 구간입니다. 라운지에서 호출한 방향을 보십시오.',source=ref,next=menu)
    tail = graph.add(menu,type='menu',q='누가 나가서 부르고 누가 남았는지 어느 위치에서 확인할까?',source=ref,options=[
        {'id':'cup','label':'잔의 손잡이','to':wrong_cup},{'id':'door','label':'라운지 문 안쪽','to':tail},
        {'id':'route','label':'운영동 계통표','to':wrong_route}])
    return graph.lines(scene,0,at,tail)


def chapter_five_timing(graph, scenes, tasks, records, dead, seats, tail):
    scene = scenes['05-T01']
    panic = scene.body.index('#### 패닉 — 같은 종이를 보았다고 하면')
    rule = next(i for i,row in enumerate(scene.body) if row.startswith('정답은 05-I03의'))
    duel = scene.body.index('#### 반론 쇼다운 — 되돌린 뒤 남는 것')
    anagram = scene.body.index('#### 섬광 애너그램 — 하루에 남는 제한')
    ref = scene.source(scene.line + anagram + 1)
    ident = 'T5-AN-REV01'
    answer, distractors, question = ANAGRAMS[scene.id]
    tasks[ident] = {'taskId':ident, 'ready':True, 'requiresEvidence':['v4:V5-5:rewind'],
        'stage':{'id':ident,'v4':True,'chapter':5,'kind':'anagram','title':'하루에 남는 제한',
                 'answer':answer,'distractors':list(distractors),'question':question}, 'queues':{}}
    tail = graph.add('rev:05:rewind-daily-limit',type='say',actor='mio',speaker='미오',
        text='하루에 한 번, 아침 일곱 시에 갱신. 두 시각을 말할 수는 있어도 같은 날 두 번 썼다는 기록은 아직 없어.',
        source=ref,next=tail)
    tail = graph.add('rev:05:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    after = next(i for i in range(duel,anagram) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,after,anagram,tail)
    ident = 'T5-RS-REV01'
    claims = [re.findall(r'“([^”]+)”',row) for row in scene.body[duel:after] if row.startswith(('1차 베기','2차는'))]
    assert [len(group) for group in claims] == [3,3]
    claims = [[line.replace('**','') for line in group] for group in claims]
    ammo = ['v4:V5-5:injury','v4:V5-5:drink-timing','v4:V5-5:rewind']
    cards = [{'id':key,'name':records[key][2],'text':records[key][3]} for key in ammo]
    tail = compile_showdown(graph,tasks,dead,seats,'rev:05:'+ident,ident,'되돌린 뒤 남는 것','아카리',claims,
        cards,ammo[-1],scene.source(scene.line+duel+1),
        ('쇼','음용을 확인한 시각과 열 초의 시작을 나란히 보십시오. 상처 기록만으로 시간의 경계를 정할 수 없습니다.'),tail)
    tail = graph.lines(scene,rule+1,duel,tail)
    ident = 'T5-PN-REV01'
    lanes = [{'id':label,'actor':SPEAKERS[name],'speaker':name,'lines':[]}
             for label,name in zip(('왼쪽','가운데','오른쪽'),('사츠키','나나','아카리'))]
    rows = []
    for at in range(panic+1,rule):
        cells = [cell.strip() for cell in scene.body[at].strip('|').split('|')]
        if len(cells)!=4 or not cells[0].isdigit():
            continue
        beat = int(cells[0])
        for lane_index,(lane,raw) in enumerate(zip(lanes,cells[1:])):
            weak = (beat,lane_index)==(4,1)
            ref = scene.source(scene.line+at+1)
            row = debate_statement(ident,f'{lane_index}:{beat}',lane['speaker'],raw.removesuffix(' 약점.'),ref,
                'weak' if weak else 'plain','v4:V5-5:rewind' if weak else '')
            rows.append(row)
            lane['lines'].append(row['id'])
            if '[큰 소리]' in raw:
                loud = debate_statement(ident,'noise',lane['speaker'],raw,ref,'noise')
                loud.update(noiseRole='loud',noiseDurability=2,hostStatement=row['id'])
                rows.append(loud)
    assert len(rows)==13 and all(len(lane['lines'])==4 for lane in lanes)
    ammo = ['v4:V5-5:archive-route','v4:V5-5:drink-timing','v4:V5-5:rewind']
    cards = [{'id':key,'name':records[key][2],'text':records[key][3]} for key in ammo]
    ref = scene.source(scene.line+rule+1)
    tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':ammo,
        'stage':{'id':ident,'kind':'panic','v4':True,'title':'같은 종이를 보았다고 하면','lines':rows,
                 'options':cards,'filterOwnedEvidence':True},
        'debate':{'id':ident,'kind':'panic','lines':rows,'bullets':cards,'lanes':lanes,'synchronizedBeats':True},
        'queues':{}}
    return graph.add('rev:05:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)


def chapter_five_rewind_reasoning(graph, scene, tasks, records, dead, seats, tail):
    ident = 'T5-RE-REV01'
    heading = scene.body.index('#### 추리 연결 — 시간을 돌려서 지킨 것')
    stop = scene.body.index('### 되돌리지 않은 쪽을 먼저 탓하면')
    questions = []
    authored = [
        ('같은 글이 한쪽에만 남은 이유는?',
         ['일반 종이를 사츠키가 찢었다','보호된 페이지와 일반 종이에는 다른 규칙이 적용된다','코토가 잔을 밀며 글씨를 지웠다'],1,
         ('사츠키','찢었으면 종이 끝부터 보여 줘. 그쪽 멀쩡하잖아.'),('미오','잔이 닿았다는 자국도 없어. 글씨가 없는 데부터 봐.')),
        ('14시의 주장과 두 종이의 차이가 함께 성립하려면?',
         ['모두가 차를 마신 일을 잊어야 한다','코토 잔이 공용 포트로 돌아가야 한다','같은 날 두 번째 사용이 필요하다'],2,
         ('나나','차를 마시는 걸 기억하는 분이 있어요. 그 기억이 없어야 성립하는 답인가요?'),('쇼','공용 포트는 잔의 성분을 비교할 자료입니다. 사용할 수 있었던 횟수는 그 자료에 없습니다.')),
        ('실제로 되감은 뒤 아카리가 먼저 바꾼 행동은?',
         ['가방 쪽에 손을 대고 잔은 두라고 했다','사츠키와 코토의 충돌을 막았다','나나와 보관실에서 나왔다'],0,
         ('사츠키','내가 밀친 건 낮이야. 잔 치우려던 때보다 훨씬 앞이잖아.'),('나나','제가 보관실에 같이 있었던 때는 이 장면보다 앞이에요. 라운지에는 제가 없었어요.')),
        ('되감기 안에서 없앨 수 없었던 것은?',
         ['사츠키의 잔 회수 시도','이미 준비된 잔을 코토가 마신 일','가방이 노출되기 직전의 움직임'],1,
         ('사츠키','잔은 그대로 뒀어. 치우려던 내 손부터 다시 봐.'),('미오','가방은 다시 손에 잡을 수 있었어. 그전부터 몸 안에 들어간 걸 찾아야 해.')),
        ('남은 글을 읽은 뒤 어떤 변화까지 확인할 수 있나?',
         ['두 종이 모두 새로 복사되었다','나나가 14시 사용을 기억해 직접 알려 줬다','보호 면에 남은 내용과 지금 빈 잔이 같은 자리에 돌아간 순서'],2,
         ('미오','지금 나란히 있다고 한쪽을 다른 데서 옮겨 썼다는 증거는 없어. 적어 둔 자리가 달라.'),('나나','그때 쓰셨다는 말은 들었지만 제가 직접 봤다고 하지는 않았어요.')),
        ('가방에서 찾은 물건으로 어디까지 설명할 수 있나?',
         ['회수한 D를 앞선 용기와 맞추고 음용 뒤 회수와 최초 전달을 나눈다','가방을 가진 사람은 그날 잔을 주지 않았다','가방을 먼저 열어 본 사람이 사망 뒤 잔을 준비했다'],0,
         ('아카리','제가 직접 놓았다고 말씀드렸어요. 가방에 무엇을 넣었는지는 다른 질문이고요.'),('사츠키','내가 그때 코토한테 줄 잔이 하나 더 있었다고 한 적 없어. 준비대 말고 그때의 가방부터 봐.'))]
    for index,(question,options,correct,*wrongs) in enumerate(authored):
        at = next(i for i in range(heading,stop) if scene.body[i].startswith(f'{index+1}. '))
        ref = scene.source(scene.line+at+1)
        option_ids = [f'option-{i}' for i in range(len(options))]
        def response(key, speaker, text):
            return {'id':f'{ident}:{index}:{key}','type':'say','actor':SPEAKERS[speaker],
                    'speaker':speaker,'text':text,'source':ref}
        questions.append({'q':question,'options':options,'optionIds':option_ids,'answer':options[correct],
            'success':[response('correct','미오',options[correct]+'.')],
            'wrongVariants':[{'optionId':option_ids[i],'script':[response(i,*wrong)]}
                for i,wrong in zip([i for i in range(len(options)) if i!=correct],wrongs)]})
    ref = scene.source(scene.line+heading+1)
    followup = scene.body.index('#### 반론 쇼다운 — 돌아가지 않아서 죽었다면')
    rule = next(i for i in range(followup,len(scene.body)) if scene.body[i].startswith('상대 쇼.'))
    tail = graph.lines(scene,rule+1,len(scene.body),tail)
    final_claim, = re.findall(r'\*\*“([^”]+)”\*\*',scene.body[rule])
    keys = ['v4:V5-5:package-pieces','v4:V5-5:rewind','v4:V5-5:rewind-timeboard']
    cards = [{'id':key,'name':records[key][2],'text':records[key][3]} for key in keys]
    duel = 'T5-RS-REV03'
    tail = compile_showdown(graph,tasks,dead,seats,'rev:05:'+duel,duel,'돌아가지 않아서 죽었다면','쇼',[
        ['사용을 감추셨습니다.','저는 그 설명을 듣고 조치의 순서를 정했습니다.','손을 댄 물건이 준비된 때를 보겠습니다.'],[final_claim]],
        cards,keys[-1],scene.source(scene.line+rule+1),
        ('쇼','사후 소지가 아니라 처음 음용에 닿을 수 있었던 구간을 묻고 있습니다.'),tail)
    tail = graph.lines(scene,stop+1,followup,tail)
    after = next(i for i in range(heading,stop) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,after,stop,tail)
    key = 'v4:V5-5:rewind-timeboard'
    tail = graph.add('rev:05:rewind-timeboard',type='evidence',evidenceId=key,name=records[key][2],
                     text=records[key][3],source=ref,next=tail)
    tasks[ident] = {'taskId':ident,'ready':True,
        'requiresEvidence':['v4:V5-5:rewind','v4:V5-5:drink-timing','v4:V5-5:fitting-edge'],
        'stage':{'id':ident,'v4':True,'kind':'reasoning','title':'시간을 돌려서 지킨 것','questions':questions},'queues':{}}
    return graph.add('rev:05:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                     source=ref,success=tail,next=tail)


def chapter_five_final_hearing(graph, scenes, tasks, records, dead, seats, tail):
    def task(ident, stage, scene, at, keys, target, wrong=()):
        ref = scene.source(scene.line+at+1)
        tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':keys,
            'stage':{'id':ident,'v4':True,**stage},
            'queues':{'wrongVariants':[{'optionIndex':index,'script':[{
                'id':f'{ident}:wrong:{index}','type':'say','actor':SPEAKERS[speaker],'speaker':speaker,
                'text':line,'source':ref}]} for index,speaker,line in wrong]}}
        return graph.add('rev:05:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                         source=ref,success=target,next=target)

    marked = 'v4:V5-5:mark-window'
    fitting = 'v4:V5-5:fitting-edge'
    rewind = 'v4:V5-5:rewind-timeboard'
    oath = 'v4:V5-5:oath-closure'
    comic = chapter_five_comic_stage()
    checkpoints = {}
    if comic is not None:
        assert all((ROOT/f'art/revision_comic/chapter5/verdict-{i:02}.webp').is_file() for i in range(1,5))
        graph.nodes.pop(tail)
        tail = graph.add('rev:05:complete',type='end',chapterComplete=True,nextChapter='6')
        scene = scenes['05-R01']
        memory = next(i for i,row in enumerate(scene.body) if row.startswith('05-F02에서'))
        tail = graph.lines(scene,memory+1,len(scene.body),tail)
        ref = scene.source(scene.line+memory+1)
        cases = []
        for key,line in [
            ('A','언제 받은 건지는 내가 적을게. 네가 찾아 준 날짜까지 받은 때로 쓰지는 마.'),
            ('B','지금 넣는다고 낮에 이미 맡겼다고 쓰면 틀려. 이건 지금 처음 넣는 거야.'),
        ]:
            target = graph.add('rev:05:envelope-memory:'+key,type='say',actor='satsuki',speaker='사츠키',
                               text=line,source=ref,next=tail)
            cases.append({'flag':'05-F02','equals':key,'to':target})
        tail = graph.add('rev:05:envelope-memory',type='branch',cases=cases,default=tail)
        tail = graph.lines(scene,0,memory,tail)
        tail = graph.add('rev:05:leave-court',type='stage',scene={'space':'hotel_rest_lounge','leaveCourt':True},
                         source=scene.source(scene.line),next=tail,presentation={'music':{'operation':'play','cue':'bgm_night'}})
        tail = chapter_verdict(graph,scenes['05-R00'],tail,5)
        scene = scenes['05-T04']
        vote = scene.body.index('### 범인 투표')
        at = scene.body.index('### 클라이맥스 추리')
        pre_vote = next(i for i in range(at,vote) if scene.body[i].startswith('플레이어는 ‘병을 증거대에'))
        tail = graph.lines(scene,vote+1,len(scene.body),tail)
        tail = task('T5-VOTE-REV01',{'kind':'vote','title':'내가 준 두 장','answer':'akari','candidates':seats,
            'question':'마지막 준비에서 개인 잔을 건넨 검정은?','selectionRole':'final-culprit-vote','finalVote':True,
            'voteCounts':{'akari':4,'satsuki':1,'nana':1}},scene,vote,[marked,fitting,rewind],tail,[
                (seats.index('satsuki'),'사츠키','내가 민 것도, 나중에 병을 들고 온 것도 맞아. 그 사람 손에 잔을 준 때도 나였어?'),
                (seats.index('nana'),'나나','제가 내려놓았을 때는 빈 잔이었어요. 표식이 언제 보였는지 다시 확인해 주세요.')])
        checkpoints['vote-hearing'] = tail
        tail = graph.lines(scene,pre_vote+1,vote,tail)
        tail = task('T5-QA-REV06',{'kind':'choice','question':'이미 나눈 세 역할은 어떤 순서로 남겨야 해?',
            'options':['사후 회수와 낮의 충돌은 사츠키, 마지막 잔의 준비와 인계는 아카리',
                       '사후 회수와 마지막 인계는 사츠키, 낮의 충돌은 아카리',
                       '처음 빈 잔을 놓은 나나가 마지막 인계까지 했다'],'answer':0},scene,pre_vote,[marked,fitting],tail,[
                           (1,'사츠키','증거대까지 내가 들었어. 준비대에서 그 잔을 골랐다고 한 적은 없어.'),
                           (2,'나나','제가 놓았을 때에는 비어 있었어요. 그 뒤 같은 잔을 계속 봤다는 말은 하지 않았고요.')])
        tail = graph.lines(scene,at+1,pre_vote,tail)
        tail = task(comic['id'],comic,scene,at,[marked,fitting,rewind,oath],tail)
        checkpoints['comic-hearing'] = tail

    scene = scenes['05-T03a']
    order = scene.body.index('### 순서 고르기 — 도움을 주겠다는 말을 놓을 때')
    alternatives = [i for i,row in enumerate(scene.body) if row.startswith('#### ')]
    join = scene.body.index('### 다른 결말을 원했다는 말')
    assert len(alternatives)==3
    tail = graph.lines(scene,join+1,len(scene.body),tail)
    questions = [
        ('실제로 되돌아간 끝의 상태는?',
         ['14시에 둘이 함께 있었다','16:52에 돌아갔을 때에는 이미 마신 뒤였다','정원에서 물을 권했다'],1,
         [(0,'나나','곁에 있었어요. 그때 시간을 쓰시는 걸 제가 본 것은 아니에요.'),(2,'유우','정원에서 준 잔을 마신 건 아니야.')]),
        ('바뀐 가방 쪽 움직임을 어떤 자료로 확인할까?',
         ['나중에 자료대로 옮긴 병만 본다','보호 페이지와 되감긴 뒤의 직접 관찰을 나란히 놓는다','14시 동석을 개봉 목격으로 쓴다'],1,
         [(0,'쇼','회수한 손의 기록으로 그보다 앞선 동작을 재구성하지 않습니다.'),(2,'나나','그 시각에 가방 안은 못 봤어요.')]),
        ('실제로 도움을 부른 때는?',
         ['처음부터 두 번 모두 같은 사람을 불렀다','최초 음용 전에 처치를 끝냈다','먼저 가방을 막았고 응급 확인은 그 뒤 별도 기록에 남는다'],2,
         [(0,'아카리','제가 언제 누구를 불렀다고 한 건지 그 말을 먼저 보여 주세요.'),(1,'미오','처치가 달랐다면 어땠을지와 실제로 확인한 때를 나누자.')]),
    ]
    for index in reversed(range(len(questions))):
        at = alternatives[index]
        end = alternatives[index+1] if index+1<len(alternatives) else join
        q,options,answer,wrongs = questions[index]
        tail = graph.lines(scene,at+1,end,tail)
        tail = task(f'T5-QA-REV{index+3:02}',{'kind':'choice','question':q,'options':options,'answer':answer},
                    scene,at,[rewind],tail,wrongs)
    tail = graph.lines(scene,0,order,tail)

    scene = scenes['05-T03']
    arming = scene.body.index('#### 이론 무장 — 두 손에 하나씩')
    end = scene.body.index('### 이론 무장 뒤 네 조각의 반응')
    tail = graph.lines(scene,end+1,len(scene.body),tail)
    raw = next(row for row in scene.body[arming:end] if row.startswith('상대 아카리.'))
    claims = re.findall(r'“([^”]+)”',raw)
    fragment_line = next(row for row in scene.body[arming:end] if row.startswith('마지막 네 조각은 '))
    fragments = [part.strip() for part in fragment_line.split('**')[1].split('/')]
    assert len(claims)==9 and len(fragments)==4
    ident = 'T5-AA-REV01'
    ref = scene.source(scene.line+arming+1)
    first = scene.body.index('### 첫 파 — 쟁반을 가져온 사람부터')
    second = scene.body.index('### 두 번째 파 — 보았다고 하면 지워 주실래요')
    third = scene.body.index('### 세 번째 파 — 손목의 선을 남긴 채')
    feedback = [[{'id':f'{ident}:feedback:{i}',**spoken} for i in range(start+1,stop)
        if (spoken:=speech(scene.body[i],scene.line+i+1,scene))] for start,stop in [(first,second),(second,third)]]
    tail = graph.lines(scene,third+1,end,tail)
    tail = task(ident,{'kind':'armament','chapter':5,'title':'두 손에 하나씩','opponent':'akari','lines':claims,
        'waves':[{'id':f'{ident}:wave:{phase}','pairs':[{'claim':{
            'id':f'{ident}:{phase}:{i}','type':'say','actor':'akari','speaker':'아카리','text':line,'source':ref}}
            for i,line in enumerate(claims[phase*3:phase*3+3])]} for phase in range(3)],
        'phaseTranscripts':True,'phaseFeedback':feedback,'question':'마지막 준비와 되감기 사이의 네 근거를 순서대로 놓자.',
        'finalSubject':'실제로 일어난 순서','final':fragments},scene,arming,[marked,fitting,rewind,oath],tail)
    checkpoints['armament-hearing'] = tail
    anagram = scene.body.index('#### 섬광 애너그램 — 같이 들을 수 있게 된 때')
    after = next(i for i in range(anagram+1,arming) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,after,arming,tail)
    answer, distractors, question = ANAGRAMS[scene.id]
    tail = task('T5-AN-REV02',{'kind':'anagram','chapter':5,'title':'같이 들을 수 있게 된 때',
        'question':question,'answer':answer,'distractors':list(distractors)},scene,anagram,[oath],tail)
    tail, more = late_case_trial(graph,scenes,5,scene.id,'사망 확인에 줄을 그으면',
        '05-D02의 명시 종료 조건',4,records,['v4:V5-5:death-confirmation','v4:V5-5:nana-line',oath],
        '쇼',tail,dead,seats,round_number=14)
    tasks.update(more)
    opening = next(i for i,row in enumerate(scene.body) if row.startswith('**사츠키**　복도에서 둘이 만난'))
    oath_open = next(i for i,row in enumerate(scene.body) if row.startswith('미오가 현재 맹세 사본을 다시'))
    tail = graph.lines(scene,opening,scene.body.index('#### 논스톱 — 사망 확인에 줄을 그으면'),tail)
    ref = scene.source(scene.line + oath_open + 1)

    def recall_stock_perjury(following):
        response = graph.add('rev:05:stock-perjury-memory:reply',type='say',actor='nana',speaker='나나',
            text='아까 보지 않은 걸 봤다고 하지 말아 달라고 했어요. 미오 씨가 적으신 줄에도 빼 주세요.',
            source=ref,next=following)
        return graph.add('rev:05:stock-perjury-memory',type='branch',
            cases=[{'flag':'05-T00:perjury','equals':True,'to':response}],default=following)

    tail = graph.insert_before_source_line(tail,ref,recall_stock_perjury)
    matches = []
    for i,row in enumerate(scene.body):
        if not (match := re.match(r'- \*\*05-D03a ([ABC])\.\*\* 아카리 “([^”]+)” 미오 “([^”]+)”',row)):
            continue
        flag,akari,mio = match.groups()
        ref = scene.source(scene.line+i+1)
        to = graph.add(f'rev:05:corridor-memory:{flag}:mio',type='say',actor='mio',speaker='미오',text=mio,source=ref,next=tail)
        to = graph.add(f'rev:05:corridor-memory:{flag}:akari',type='say',actor='akari',speaker='아카리',text=akari,source=ref,next=to)
        matches.append({'flag':'05-D03a','equals':flag,'to':to})
    assert len(matches)==3
    tail = graph.add('rev:05:corridor-memory',type='branch',cases=matches,default=tail)
    return tail, checkpoints


def chapter_five_late_hearing(graph, scenes, tasks, records, dead, seats, tail):
    root = 'v4:V5-5:'

    def contextual_choice(scene,target):
        controls = {
            '05-T02d':('#### 기록 고르기 — 부탁의 이름을 잘못 붙이면',[
                ('T5-QA-REV08','복도에 남겨야 하는 발언은?',0,[
                    ('유우','아직 말하지 않은 부탁'),('유우','코토가 특정한 개인 잔을 지정했다'),('미오','쇼를 불러 달라는 실제 요청')],
                 ['그 복도에서 아직 그 말을 하지는 않았어.','그 잔 이름은 내가 붙인 적 없어.','쇼를 부른 건 어지럽다는 말을 들은 뒤야.']),
                ('T5-QA-REV09','라운지에서 실제로 한 요청은?',2,[
                    ('미오','아직 말하지 않은 부탁'),('유우','코토가 특정한 개인 잔을 지정했다'),('미오','쇼를 불러 달라는 실제 요청')],
                 ['그때는 어떤 부탁을 할지 아직 듣지 못했어.','내가 본 글에 그 잔을 준비하라는 말은 없었어.','마신 뒤 어지럽다는 말을 듣고 쇼를 불렀어.'])]),
            '05-T02j':('#### 정답 선택 — 방을 비운다는 뜻이 있었던 데',[
                ('T5-QA-REV10','당시의 계획으로 확인할 수 있는 것은?',1,[
                    ('유우','다시는 돌아오지 않기로 했다'),('미오','그날 혼자 쓸 자리와 맡길 물건을 각각 골랐다'),
                    ('아카리','특정 잔을 미리 준비하라고 약속했다')],
                 ['그 말을 적어 놓은 게 아니야. 내가 안 와도 된다고 한 걸 그렇게 읽는 거잖아.','그날 고른 자리와 물건은 남아.','어떤 때 무엇을 건넸는지부터 다시 확인해 주세요.'])]),
            '05-T02c':('#### 선택 — 둘이 같은 말을 하면 어느 때를 먼저 묻나',[
                ('T5-QA-REV11','같은 말의 출처를 구별하려면 먼저 무엇을 물을까?',2,[
                    ('사츠키','무엇을 했다고 말했는지'),('나나','그 일을 직접 보았는지'),('사츠키','그 이야기를 처음 들은 때')],
                 ['그 말을 한 건 맞아. 어디서 처음 알았는지도 물어봐야지.','그분이 원래의 흐름을 기억한다고 먼저 정하지 말아 주세요.','내가 언제 알았는지는 남아 있잖아.'])]),
        }
        if scene.id not in controls:
            return graph.lines(scene,0,len(scene.body),target)
        anchor,questions = controls[scene.id]
        at = scene.body.index(anchor)
        after = next(i for i in range(at+1,len(scene.body)) if SAY.match(scene.body[i]))
        target = graph.lines(scene,after,len(scene.body),target)
        ref = scene.source(scene.line+at+1)
        for ident,question,answer,options,replies in reversed(questions):
            tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':[root+'mark-window',root+'rewind-timeboard'],
                'stage':{'id':ident,'kind':'choice','v4':True,'question':question,'options':[label for _,label in options],'answer':answer},
                'queues':{'wrongVariants':[{'optionIndex':i,'script':[{'id':f'{ident}:{i}','type':'say',
                    'actor':SPEAKERS[speaker],'speaker':speaker,'text':replies[i],'source':ref}]}
                    for i,(speaker,_) in enumerate(options) if i!=answer]}}
            target = graph.add('rev:05:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                               source=ref,success=target,next=target)
        if scene.id=='05-T02c':
            context = scene.body.index('### 읽어 주는 사람이 달랐을 때')
            entry = graph.lines(scene,0,at,target)
            source = scene.source(scene.line+context+1)

            def recall_reader(first):
                second = graph.nodes[first]['next']
                third = graph.nodes[second]['next']
                assert [graph.nodes[node]['actor'] for node in (first,second,third)]==['sho','nana','satsuki']
                assert graph.nodes[third]['next']==target
                cases = []
                for key, response in zip('ABC',(first,second,third),strict=True):
                    graph.nodes[response]['next'] = target
                    cases.append({'flag':'05-I05d','equals':key,'to':response})
                return graph.add('rev:05:reading-order-memory',type='branch',cases=cases,
                                 source=source,default=target)

            return graph.insert_before_source_line(entry,source,recall_reader,end_node=target)
        return graph.lines(scene,0,at,target)

    def paper_witness(target):
        scene = scenes['05-T02g']
        person_at = scene.body.index('#### 인물 지목 — 말 그대로 받은 것을 본 사람')
        choice_at = scene.body.index('#### 정답 선택 — 사진에는 없고 순서에는 들어갈 수 있는가')
        selected = next(i for i in range(person_at+1,choice_at) if SAY.match(scene.body[i]))
        tested = next(i for i in range(choice_at+1,len(scene.body)) if SAY.match(scene.body[i]))

        def question(ident, at, stage, wrongs, next_node):
            ref = scene.source(scene.line+at+1)
            tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':[root+'archive-route',root+'window-witness'],
                'stage':{'id':ident,'v4':True,**stage},'queues':{'wrongVariants':[{'optionIndex':i,'script':[{
                    'id':f'{ident}:wrong:{i}','type':'say','actor':SPEAKERS[speaker],'speaker':speaker,
                    'text':text,'source':ref}]} for i,speaker,text in wrongs]}}
            return graph.add('rev:05:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                             source=ref,success=next_node,next=next_node)

        target = graph.lines(scene,tested,len(scene.body),target)
        target = question('T5-QA-REV07',choice_at,{'kind':'choice','question':'이 가설이 실제 공모인지 확인하려면?',
            'options':['사후에 가방을 든 손을 확대한다','실제로 건네진 물건과 시점을 확인한다',
                       '유우가 들고 온 계통표를 이해했는지 묻는다'],'answer':1},[
            (0,'사츠키','그 사진을 앞으로 옮겨도 내가 준비대에 먼저 가 있지는 않았어.'),
            (2,'쇼','이해와 위치는 다른 진술입니다. 실제로 물건과 사람이 만난 시각을 확인하십시오.')],target)
        target = graph.lines(scene,selected,choice_at,target)
        target = question('T5-PE-REV01',person_at,{'kind':'person','question':'두 사람이 돌아오는 복도와 유우가 든 계통표를 직접 본 사람은?',
            'candidates':['sho','nana','satsuki','akari'],'answer':'nana'},[
            (0,'쇼','저는 유우 씨와 같이 움직였습니다. 복도에서 저희를 본 분에게 질문하십시오.'),
            (2,'사츠키','나는 창가에 있었어. 복도에서 뭐를 들고 왔는지는 그 사람한테 물어.'),
            (3,'아카리','제가 차를 건넨 자리에 그 복도에서 만난 사람을 넣지는 말아 주세요.')],target)
        return graph.lines(scene,0,person_at,target)

    rounds = [
        (9, '05-T02a', '잔 옆의 일이 한 사람 몫은 아니야', '05-I05 창가 동석의 시점', 4,
         ['package-pieces','window-witness','custody-sequence'], '유우',
         '나중에 병을 들었다는 건 알겠어. 내가 말한 때랑 같았는지 따로 맞춰 봐.',
         '창가 동석과 뒤늦은 회수', '잔을 받은 때에 미오와 사츠키는 창가에 있었다. 용기를 증거대로 옮긴 일은 음용 이후의 별도 동작이다.'),
        (10, '05-T02e', '검사 직전에 들어간 물질이라면', '05-I02b의 **음용 뒤에', 4,
         ['cup','package-pieces','late-cup-contact'], '아카리',
         '검사에서 잔 안쪽에 남은 건 저도 봤어요. 그 사람이 마신 뒤에는 몸 안에 무슨 변화가 있었죠?',
         '몸의 반응과 뒤늦은 잔 접촉', '표식 잔을 마시고 처음 어지럽다고 했다. 그 뒤 다른 손이 잔에 접근했다. 사후에 잔을 바꾸는 일만으로 앞선 체내 상태를 설명할 수 없다.'),
        (11, '05-T02f', '읽지 못한 쪽에서 보인 것', '4에 **05-D02n에서', 4,
         ['fitting-edge','cup','warning-match'], '쇼',
         '회수한 다음 확인한 표지를 그보다 먼저 읽은 사람의 진술과 구분하십시오.',
         '미리 읽은 경고와 실제 용기', '보관실 앞에서 아카리가 직접 읽은 R-7 경고와 회수한 D의 식별지를 비교했다. 창가에서 글자를 보았다는 뜻은 아니다.'),
        (12, '05-T02i', '남은 건 같은 크기였을 뿐', '4에 **D칸의 계수', 4,
         ['cup','warning-match','d-storage-match'], '유우',
         '포트 말고 다른 데서 들고 갔다는 말이야. 그러면 어떤 물건이 어디에서 나왔는지도 보여 줘.',
         '보관함 D칸과 회수된 봉함 띠', '공용 재료 선반과 별개인 보관함 D칸이 비었다. 회수 용기와 가방 조각이 실제로 맞물리므로 같은 크기만 보고 선반을 바꿀 수 없다.'),
        (13, '05-T02l', '전해 달라는 사람이 그 잔을 정했어', '**05-I02a·I02b의 준비대', 5,
         ['warning-match','rewind','marked-selection'], '나나',
         '경고는 저도 들었어요. 그런데 그분이 건네신 잔의 손잡이는 어느 자리에서 처음 보였나요?',
         '준비대와 창가의 표식 잔 대조', '준비대에서 선택된 개인 잔의 표식이 마지막 인계 때 창가에서도 확인됐다. 앞선 권유는 같은 잔을 선택하거나 소지했다는 관찰이 아니다.'),
    ]
    for _, scene_id, _, _, _, keys, _, _, name, facts in rounds:
        records[root+keys[-1]] = (scene_id,'',name,facts,[])
    for number, scene_id, title, prefix, weak, keys, speaker, correction, name, facts in reversed(rounds):
        if number == 9:
            for context in reversed(('05-T02k','05-T02d','05-T02b','05-T02j')):
                scene = scenes[context]
                tail = contextual_choice(scene,tail)
            tail = paper_witness(tail)
        elif number == 10:
            for context in reversed(('05-T02c','05-T02h')):
                scene = scenes[context]
                tail = contextual_choice(scene,tail)
        ammo = [root+key for key in keys]
        scene = scenes[scene_id]
        at = scene.body.index('#### 논스톱 — '+title)
        rule = next(i for i in range(at,len(scene.body)) if scene.body[i].startswith(prefix))
        stop = next((i for i in range(rule+1,len(scene.body)) if scene.body[i].startswith(('### ','#### '))),len(scene.body))
        tail = graph.lines(scene,stop,len(scene.body),tail)
        tail, more = late_case_trial(graph,scenes,5,scene_id,title,prefix,weak,records,ammo,speaker,tail,dead,seats,
                                     round_number=number,correction=correction)
        tasks.update(more)
        tail = graph.add(f'rev:05:late-comparison:{number}',type='evidence',evidenceId=ammo[-1],
                         name=name,text=facts,source=scene.source(scene.line+at+1),next=tail)
        tail = graph.lines(scene,0,at,tail)
    return tail


def chapter_five_package_hearing(graph, scenes, tasks, records, dead, seats, package_objects, tail):
    scene = scenes['05-T02']

    def source(at):
        return scene.source(scene.line + at + 1)

    def card(key):
        return {'id':key,'name':records[key][2],'text':records[key][3]}

    def reply(ident, speaker, text, at):
        return {'id':ident,'type':'say','actor':SPEAKERS[speaker],'speaker':speaker,'text':text,'source':source(at)}

    def task(ident, stage, at, evidence, target, queues=None):
        tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':evidence,
            'stage':{'id':ident,'v4':True,**stage},'queues':queues or {}}
        return graph.add('rev:05:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                         source=source(at),success=target,next=target)

    agree = scene.body.index('#### 논스톱 동의 — 두 종이와 한 사람의 기억')
    present = scene.body.index('#### 증거 제시 — 보인 조각과 실제 용기를 맞춘다')
    point = scene.body.index('#### 지점 지목 — 창가에 앉았을 때 손이 보인 곳')
    mine = scene.body.index('#### 발굴 이매지네이션 — 번호가 같아도 남아야 하는 것')
    duel = scene.body.index('#### 반론 쇼다운 — 내가 넣고 내가 꺼냈어')
    scrum = scene.body.index('#### 논의 스크럼 — 병을 먼저 잡은 사람을 찾는 데 충분한가')
    custody = scene.body.index('#### 논스톱 동의 — 누가 자료대에 넘겼는가')
    image = MINE_ART+'archive-preparation-view.svg'
    fitting = 'v4:V5-5:fitting-edge'
    tail = chapter_five_rewind_reasoning(graph,scene,tasks,records,dead,seats,tail)

    def agreement(ident, title, heading, end, rule_prefix, keys, wrong, target):
        rule = next(i for i in range(heading,end) if scene.body[i].startswith(rule_prefix))
        rows = []
        for at in range(heading+1,rule):
            if match := STMT.match(scene.body[at]):
                number,speaker,text,role = match.groups()
                row = debate_statement(ident,number,speaker,text,source(at))
                if '동의점' in role:
                    word, = re.findall(r'\*\*([^*]+)\*\*',text)
                    row.update(kind='agree',agree=keys[-1],agreeTarget={'word':word,'glyphStart':row['text'].index(word)})
                rows.append(row)
        assert sum(row['kind']=='agree' for row in rows)==1
        options = [card(key) for key in keys]
        target = graph.lines(scene,rule+1,end,target)
        target = task(ident,{'kind':'nonstop','title':title,'lines':rows,'options':options,'authoredAmmo':keys,
            'filterOwnedEvidence':True,'wrongCards':{keys[0]:'different-fact'}},heading,keys,target,
            {'wrongVariants':[{'cause':'different-fact','script':[reply(ident+':wrong',*wrong,rule)]}]})
        tasks[ident]['debate'] = {'id':ident,'kind':'nonstop','lines':rows,'bullets':options}
        return target

    reason = scene.body.index('#### 추리 연결 — 시간을 돌려서 지킨 것')
    tail = agreement('T5-NS-REV08','두 종이와 한 사람의 기억',agree,reason,'05-I03에서 받은',
        ['v4:V5-5:archive-route','v4:V5-5:drink-timing','v4:V5-5:rewind'],
        ('나나','기억나는 말을 읽어 드릴 수는 있지만 종이가 한 장이었는지까지 보증할 수는 없어요.'),tail)
    tail = graph.lines(scene,present+1,agree,tail)
    ident = 'T5-BU-REV02'
    keys = ['v4:V5-5:pour-boundary','v4:V5-5:stock',fitting]
    tail = task(ident,{'kind':'bullet','question':'창가에서 보인 띠와 실제 회수한 용기를 연결하는 자료는?',
        'options':[card(key) for key in keys],'answer':fitting},present,keys,tail,
        {'wrongVariants':[{'optionIndex':0,'script':[reply(ident+':0','아카리','차를 따라 놓은 일과 포장의 띠를 연 일부터 분리해 주세요.',present)]},
            {'optionIndex':1,'script':[reply(ident+':1','미오','빈 D칸은 원래 자리를 보여 줘. 지금 보인 조각이 어디에서 끊겼는지는 두 면을 대 봐야 해.',present)]}]})
    tail = graph.lines(scene,point+1,present,tail)
    ident = 'T5-SP-REV01'
    regions = [('edge','바깥 모서리 위 손과 띠',(.49,.34,.68,.48),'',''),
        ('label','준비대 안쪽 용기의 표지',(.77,.46,.88,.55),'아카리','제 쪽으로 돌아가 있던 글씨를 창가에서 보셨나요?'),
        ('inside','상판에 가려진 잔 안쪽',(.45,.61,.7,.81),'쇼','상판 너머의 내용물은 그 자리에서 보이지 않았습니다.'),
        ('cup','나중에 잔을 든 자리',(.18,.53,.33,.7),'미오','마신 건 봤어. 지금 묻는 때는 그보다 앞의 개봉이야.')]
    tail = task(ident,{'kind':'spot','question':'창가에서 끊어지는 띠를 직접 본 영역은?',
        'image':image,'answerRegionId':'edge','regions':[
            {'id':key,'label':label,'wrongVariant':key,'polygon':[[x,y],[x1,y],[x1,y1],[x,y1]]}
            for key,label,(x,y,x1,y1),*unused in regions]},point,['v4:V5-5:pour-boundary'],tail,
        {'wrongVariants':[{'cause':key,'script':[reply(ident+':'+key,speaker,text,point)]} for key,_,_,speaker,text in regions if speaker]})
    first_after = next(i for i in range(mine,point) if scene.body[i].startswith('**미오**　가방에서 가져온 조각은'))
    tail = graph.lines(scene,first_after,point,tail)
    tail = graph.add('rev:05:fitting-edge-record',type='evidence',evidenceId=fitting,
        name=records[fitting][2],text=records[fitting][3],source=source(mine),next=tail)
    ident = 'T5-MM-REV02'
    objects = [('archive-fitting-edge','몸체의 띠 끝과 안감 조각','',''),
        ('archive-printed-foil','다른 포장의 같은 인쇄','쇼','같은 글자 대신 맞물리는 끊긴 면을 보여 주십시오.'),
        ('archive-d-base','D칸 받침의 표식','나나','그건 물건이 있던 구획이에요. 마개에 남은 띠와는 달라요.'),
        ('archive-pot-lid','공용 포트 뚜껑의 이음새','아카리','제가 들었던 물건의 크기와 포트는 달라요.')]
    tail = task(ident,{'kind':'mindmine','title':'번호가 같아도 남아야 하는 것',
        'question':'회수한 용기에서 실제로 끊어진 조각임을 무엇과 맞춰 확인하지?',
        'image':MINE_ART+'archive-fitting-edge.svg','answerRegionId':objects[0][0],'mineObjects':package_objects,
        'regions':[{'id':key,'label':label,'correct':not speaker,'wrongVariant':key} for key,label,speaker,_ in objects]},
        mine,['v4:V5-5:package-pieces','v4:V5-5:stock'],tail,
        {'wrongVariants':[{'cause':key,'script':[reply(ident+':'+key,speaker,text,mine)]} for key,_,speaker,text in objects if speaker]})
    first = next(i for i in range(mine,first_after) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,first,first_after,tail)
    tail = graph.lines(scene,duel+1,mine,tail)
    ident = 'T5-RS-REV02'
    keys = ['v4:V5-5:stock','v4:V5-5:rewind','v4:V5-5:window-witness']
    tail = compile_showdown(graph,tasks,dead,seats,'rev:05:'+ident,ident,'내가 넣고 내가 꺼냈어','사츠키',[
        ['내가 그 가방 열었어','쇼는 내가 들고 있는 거 봤어','그 전에 들어 있던 건 아무도 못 봤잖아'],
        ['내가 나중에 들고 나온 건 맞아','준비할 때 내 손을 봤어?','차 준비할 때 내가 들고 가서 넣었어.']],
        [card(key) for key in keys],keys[-1],source(duel),
        ('사츠키','그 번호 내가 알아도 되잖아. 차를 준비할 때 어느 자리에 있었는지부터 대 봐.'),tail)
    ident = 'T5-SD-REV01'
    pairs = []
    keywords = [('갖고 나왔다','준비되던'),('넣었다가','창가'),('다 못 보셨어요','못 본 손'),('같은 번호','끊긴 면')]
    for at in range(scrum+1,duel):
        if match := re.fullmatch(r'\| ([^ ]+) “(.+)” \| ([^.]+)\. ([^ ]+) “(.+)” \|',scene.body[at]):
            speaker,claim,keyword,ally,response = match.groups()
            claim_word,response_word = keywords[len(pairs)]
            pair = f'{ident}:{len(pairs)}'
            pairs.append({'id':pair,'them':speaker,'themActor':SPEAKERS[speaker],'themText':claim,
                'us':ally,'usActor':SPEAKERS[ally],'usText':response,'keyword':keyword,
                'claimKeyword':claim_word,'responseKeyword':response_word,'duration':11,
                'wrong':[reply(pair+':retry',ally,'지금 확인할 말은 '+keyword+' 쪽이야. 준비 시점과 발견 이후를 나누어 보자.',at)]})
    assert len(pairs)==4
    tail = task(ident,{'kind':'scrum','title':'병을 먼저 잡은 사람을 찾는 데 충분한가','pairs':pairs,
        'teams':{'them':['akari','yuu','satsuki'],'us':['mio','sho','nana']},
        'scrumDecoys':[{'keyword':label} for label in ('공용 포트','팔꿈치 사진','맹세 서명')],
        'scrumPresentation':{'topic':'사후 소지와 준비 시점','them':'나중 소지로 앞선 준비를 설명한다','us':'준비 시점의 사람과 물건을 따로 본다'}},
        scrum,['v4:V5-5:package-pieces','v4:V5-5:window-witness'],tail)
    tail = agreement('T5-NS-REV07','누가 자료대에 넘겼는가',custody,scrum,'05-I06의 봉투 표기',
        ['v4:V5-5:stock','v4:V5-5:window-witness','v4:V5-5:package-pieces'],
        ('쇼','어떤 용기였는지를 비교할 수는 있습니다. 지금은 누가 제게 넘겼는지의 문제입니다.'),tail)
    return graph.lines(scene,0,custody,tail)


def daily_scene_route(graph,scene,space,tail):
    compact = {
        '05-D02g':('### 무슨 상이 있었어',[
            ('빈 칸을 눌러 본다','미오','버튼은 돌아왔지만 기계에서는 소리가 나지 않았다. 소리를 낸 건 웃고 있는 유우였다.',True),
            ('작은 종이를 접어 남긴다','미오','창구에서 찾은 빈 줄을 접어 안쪽에 놓았다. 받을 사람의 이름은 쓰지 않았다.',True),
            ('유우가 내민 표를 돌려준다','미오','유우가 내밀었던 표 하나를 다시 세웠다. 사츠키는 누가 가져온 표인지 유우에게 물었다.',True)]),
        '05-D02j':('### 먼저 함께 할 일',[
            ('유우 옆 낮은 의자에 앉는다','미오','먼저 앉을지 묻고 나서 유우 옆에 앉았다. 나나는 자리에 남고 쇼는 자판기 쪽으로 조금 물러났다.',True),
            ('나나에게 동전을 대신 찾지 말자고 한다','미오','나나가 바닥을 더 보고 싶은지 직접 물었다. 유우는 동전을 못 찾았다는 말을 남이 먼저 할까 걱정됐다고 했다.',True),
            ('쇼와 물을 받으러 간다','미오','쇼와 함께 물을 받으러 갔다. 돌아오자 유우는 의자에 있었다. 나나와 둘이 무슨 말을 나눴는지는 못 들었다.',True)]),
        '05-D02h':('### 옮겨 적을 정보',[
            ('의상 번호와 인수 표제를 적는다','미오','번호 옆에 인수 표제를 옮겼다. 누가 어떤 옷을 입었는지는 아직 알아보지 못했다.',True),
            ('어머니의 이름부터 적는다','미오','어머니 이름을 먼저 적었다. 글자를 알아보는 것과 그날 모습을 떠올리는 것은 달랐다.',True),
            ('원본을 다시 찾을 위치를 적는다','미오','번호와 이름이 나란히 있는 원본의 위치를 적었다. 나중에 다시 와서 내가 못 알아본 줄을 보고 싶었다.',True)]),
        '05-D02o':('### 누구에게 먼저 말을 건넬까',[
            ('아카리에게 부탁의 범위를 묻는다','아카리','제가 듣기 싫은 얘기까지 계속 들을 필요는 없잖아요.',False),
            ('코토가 거절한 뒤에도 옆에 있는다','미오','사츠키는 코토 곁에 남았다. 코토는 어제 같이 보자고 했던 사람에게도 오늘은 다시 물어봐 달라고 했다.',True),
            ('유우와 복도로 나가 기다린다','유우','내가 여기 안 들어가기로 했다는 말을 그 둘한테 해도 돼?',False)]),
        '05-D02q':('### 이름 옆에 남기려던 횟수',[
            ('오늘 부탁할 한 번만 적는다','사츠키','나중에 시간 없다고 하면 네가 거기 찾아오라고 할 거야?',False),
            ('이전에 했던 이름을 거두자고 한다','미오','코토는 종이를 바로 찢지 않았다. 직접 했던 일까지 없어지면 싫다고 해서 지난 기록과 남은 부탁을 따로 뒀다.',True),
            ('유우가 오늘 맡을지 직접 말할 때까지 기다린다','유우','내가 같이 있고 싶은데 또 누가 부탁한다고 하면 기다리기 싫어.',False)]),
        '05-D02p':('### 한 사람에게 열쇠를 맡겨 두려 할 때',[
            ('유우에게 오늘 밤의 문만 부탁한다','유우','그럼 내가 안으로 들어가고 싶을 때는?',False),
            ('나나가 먼저 고르도록 묻는다','나나','제가 가지고 있으면 먼저 묻기 편하세요? 안 들어가셔도 괜찮다고 제가 말씀드리는 자리면 안 가지고 있을래요.',False),
            ('코토가 잠깐 쓴 뒤 돌려놓도록 한다','미오','코토는 먼저 공용 공간에서 나와 자기 몫을 돌려놓았다. 그 뒤까지 안에 있었다고 표에 쓰지는 않았다.',True)]),
        '06-D02c':('### 사람을 기다릴 자리',[
            ('누가 먼저 웃었는지 묻는다','미오','사츠키는 자기 쪽에서 소리가 먼저 났다고 했다. 처음부터 그 말이 재미있었다고는 하지 않았다.',True),
            ('다음에 쓰기 전에 먼저 물어봐 달라고 한다','유우','내가 너무 기분 좋으면 먼저 말하면 싫다고 할 줄 알고 안 물었어.',False),
            ('말을 쉬고 잠시 걸어 본다','미오','나나가 먼저 걸었다. 유우도 옆에서 따라갔다. 지금 어떤 기분이어야 하는지 정하는 사람은 없었다.',True)]),
        '06-D03e':('플레이어는 모인 가방 사이에서',[
            ('표식 없는 작은 가방을 살핀다','미오','유우가 기다리는 자리를 남기려고 두었다고 했다. 내가 가방 주인 이름을 먼저 붙이지 않았다.',True),
            ('손잡이의 찢어진 천을 살핀다','미오','쇼는 자기가 쓰는 도구라고 했다. 다른 사람 짐까지 대신 넣어 달라는 말은 아니었다.',True),
            ('주인이 밀어 둔 가방을 살핀다','미오','사츠키가 봉투를 손에 들고 기다렸다. 가방이 열린 걸 보고 내가 먼저 가져갈 것을 고르지는 않았다.',True)]),
    }
    branch_sections = {
        '05-D01c':('#### 바퀴 두 쪽을 돌린다','### 운반대를 세우고 나서'),
        '05-D02l':('#### 실이 나온 한 땀만 고쳐 본다','### 돌아가는 복도'),
        '05-D03f':('#### 먼저 코토의 종이를 돌려준다','#### 문 앞을 떠날 때'),
        '06-D01d':('### 낮은 유리에 비치는 좌석을 살핀다','### 통로로 돌아온 뒤'),
    }
    shared_tails = {
        '05-D02n':'선택이 끝나면 쇼가 자기 열쇠를 주머니에 넣는다.',
        '05-D02m':'(유우는 자기 몫을 보이는 곳에서 챙긴다.',
        '05-D03h':'(라운지 입구에서 두 사람은 먼저 한쪽으로 비킨다.',
        '06-D03f':'(어느 자리를 골라도 다섯은 같은 자료를 읽는다.',
        '06-D03g':'합류 뒤 유우는 자신이 들은 말을 대신 전하지 않는다.',
    }
    if scene.id=='05-D02b':
        a = next(i for i,row in enumerate(scene.body) if row.startswith('05-F03 A라면'))
        b = next(i for i,row in enumerate(scene.body) if row.startswith('05-F03 B라면'))
        join = next(i for i,row in enumerate(scene.body) if row.startswith('미오가 코토를 만나지 않았다면'))
        tail = graph.lines(scene,join+1,len(scene.body),tail)
        cases = [{'flag':'05-F03','equals':key,'to':graph.lines(scene,at+1,stop,tail)}
                 for key,at,stop in [('A',a,b),('B',b,join)]]
        tail = graph.add('rev:05:paper-meeting-memory',type='branch',cases=cases,default=tail)
        tail = graph.lines(scene,0,a,tail)
    elif scene.id=='06-D01e':
        at = next(i for i,row in enumerate(scene.body) if row.startswith('06-D01d에서'))
        tail = graph.lines(scene,at+1,len(scene.body),tail)
        ref = scene.source(scene.line+at+1)
        cases = []
        for key,text in [('A','저쪽 벽은 비치는 게 있어서 다시 보려고. 아까 보이는 데하고 실제 발 놓는 데가 달랐어.'),
                         ('B','나 지금 돌아가는 길에 볼 거는 바닥이야. 아까 읽은 글은 반대쪽에서 안 보여.')]:
            to = graph.add(f'rev:06:return-path-memory:{key}',type='say',actor='yuu',speaker='유우',text=text,source=ref,next=tail)
            cases.append({'flag':'06-D01d','equals':key,'to':to})
        to = graph.add('rev:06:return-path-memory:C',type='say',actor='mio',speaker='미오',mono=True,
            text='유우가 모서리까지 걸어가 멈췄다. 사츠키가 방향을 알려 주기 전에 자기 쪽에서 한 번 손을 들었다.',source=ref,next=tail)
        cases.append({'flag':'06-D01d','equals':'C','to':to})
        tail = graph.add('rev:06:return-path-memory',type='branch',cases=cases,default=tail)
        tail = graph.lines(scene,0,at,tail)
    elif scene.id in compact:
        anchor,responses = compact[scene.id]
        at = next(i for i,row in enumerate(scene.body) if row.startswith(anchor))
        candidates = [i for i in range(at+1,len(scene.body)) if SAY.match(scene.body[i]) or scene.body[i].startswith('### ')]
        join = candidates[0] if candidates else len(scene.body)
        tail = graph.lines(scene,join,len(scene.body),tail)
        choices = []
        for i,(label,speaker,text,mono) in enumerate(responses):
            flag = chr(65+i)
            answer = graph.add(f'rev:{scene.id}:response:{flag}',type='say',actor=SPEAKERS[speaker],speaker=speaker,
                text=text,mono=mono,source=scene.source(scene.line+at+1),next=tail)
            choices.append({'id':flag,'label':label,'set':{scene.id:flag},'to':answer})
        tail = graph.add(f'rev:{scene.id}:choice',type='menu',q=scene.title,options=choices,source=scene.source(scene.line+at+1))
        tail = graph.lines(scene,0,at,tail)
    elif scene.id in branch_sections:
        head,common = branch_sections[scene.id]
        first = scene.body.index(head)
        join = scene.body.index(common)
        depth = head[:head.index(' ')+1]
        starts = [i for i in range(first,join) if scene.body[i].startswith(depth)]
        assert len(starts)==3
        tail = graph.lines(scene,join+1,len(scene.body),tail)
        tail = graph.menu(scene,scene.title,[(scene.body[at].removeprefix(depth),at+1,stop,'')
            for at,stop in zip(starts,[*starts[1:],join],strict=True)],tail)
        tail = graph.lines(scene,0,first,tail)
    elif scene.id in shared_tails:
        options = [i for i,row in enumerate(scene.body) if row.startswith('- **')]
        assert len(options) in (2,3)
        first = options[0]
        shared = next(i for i,row in enumerate(scene.body) if row.startswith(shared_tails[scene.id]))
        menu = graph.menu(scene,scene.title,[(scene.body[at].split('**')[1],at+1,stop,'')
            for at,stop in zip(options,[*options[1:],len(scene.body)],strict=True)],tail)
        graph.share_choice_tail(menu,tail,scene.line+shared+1)
        tail = graph.lines(scene,0,first,menu)
    else:
        tail = graph.lines(scene,0,len(scene.body),tail)
    if scene.id in ('06-D01a','06-D02a','06-D02b'):
        anchors = {
            '06-D01a':'05-D02l에서 한 땀만 만졌다면',
            '06-D02a':'쇼는 송화구를 가렸다가 손을 뗀다.',
            '06-D02b':'플레이어는 아직 송신하지 않은 세 문장 중',
        }
        at = next(i for i,row in enumerate(scene.body) if row.startswith(anchors[scene.id]))
        ref = scene.source(scene.line+at+1)
        previous, following = None, tail
        while graph.nodes[following]['source']['line'] < ref['line']:
            previous, following = following, graph.nodes[following]['next']
        if scene.id=='06-D02b':
            inserted = 'rev:06:unsent-contact-check'
            options = []
            for flag,label,speaker,text in [
                ('A','전화가 바깥에 연결됐다','쇼','안쪽에서 시험한 것뿐입니다. 바깥에서 대답한 사람은 없습니다.'),
                ('B','사츠키가 철문을 열었다','사츠키','여기, 문 아래 홈만 봤어. 아직 안 열었어.'),
                ('C','다섯 명이 이 관리 구역에 있다','미오','손 든 사람을 한 명씩 셌어. 지금 적을 수 있는 건 그 숫자야.'),
            ]:
                response = graph.add(inserted+':'+flag,type='say',actor=SPEAKERS[speaker],speaker=speaker,
                    text=text,source=ref,next=following if flag=='C' else inserted)
                options.append({'id':flag,'label':label,'to':response})
            graph.add(inserted,type='menu',q='지금 확인한 사실은 뭐지?',options=options,source=ref)
        else:
            if scene.id=='06-D01a':
                flag_key = '05-D02l'
                inserted = 'rev:06:stair-bag-memory'
                speaker = '미오'
                answers = [
                    '내 가방에 쇼가 눌러 둔 자리가 보였다. 그쪽을 손등으로 가리켰다.',
                    '가방 먼저 보여 주고 싶다고 했어. 지금까지 메고 내려왔네.',
                    '가방 끈을 당기니 끼워 둔 종이가 빠졌다. 주워서 내 가방에 다시 넣었다.',
                ]
            else:
                flag_key = '05-F06'
                inserted = 'rev:06:last-sound-memory'
                speaker = '유우'
                answers = re.findall(r'“([^”]+)”',scene.body[at])
                assert len(answers)==3,scene.id
            cases = []
            for flag,text in zip('ABC',answers,strict=True):
                next_node = following
                if scene.id=='06-D01a' and flag=='B':
                    next_node = graph.add(inserted+':B:reply',type='say',actor='sho',speaker='쇼',
                        text='그때는 실제로 만날 분의 상태까지는 몰랐습니다.',source=ref,next=following)
                response = graph.add(inserted+':'+flag,type='say',actor=SPEAKERS[speaker],speaker=speaker,
                    text=text,mono=scene.id=='06-D01a' and flag!='B',source=ref,next=next_node)
                cases.append({'flag':flag_key,'equals':flag,'to':response})
            graph.add(inserted,type='branch',cases=cases,default=following)
        if previous is None:
            tail = inserted
        else:
            graph.nodes[previous]['next'] = inserted
    if scene.id=='06-D03e':
        at = next(i for i,row in enumerate(scene.body) if row.startswith('05-F05에서'))
        before = None
        after = tail
        while graph.nodes[after]['source']['line']<scene.line+at+1:
            before = after
            after = graph.nodes[after]['next']
        ref = scene.source(scene.line+at+1)
        moved = graph.add('rev:06:toy-memory:moved',type='say',actor='sho',speaker='쇼',
            text='끌어 볼 수 있는 것과 그 안에 전부 넣는 건 다르죠.',source=ref,next=after)
        stayed = graph.add('rev:06:toy-memory:stayed',type='say',actor='sho',speaker='쇼',
            text='전에 아무것도 옮기지 않고 같이 앉은 적이 있었죠.',source=ref,next=after)
        callback = graph.add('rev:06:toy-memory',type='branch',cases=[
            {'flag':'05-F05','equals':'A','to':moved},{'flag':'05-F05','equals':'B','to':moved},
            {'flag':'05-F05','equals':'C','to':stayed}],default=after)
        if before is None:
            tail = callback
        else:
            graph.nodes[before]['next'] = callback
    return graph.add(f'rev:{scene.id}:entry',type='stage',next=tail,source=scene.source(scene.line),
                     scene={'space':space,'perspective':'current-observation'})


def optional_meeting(graph,scene,space,question,tail):
    tail = graph.finish_free_time(scene,tail)
    starts = [i for i,row in enumerate(scene.body) if row.startswith(('### A. ','### B. '))]
    assert len(starts)==2
    talk = graph.menu(scene,question,[(scene.body[start][7:],start+1,end,'')
        for start,end in zip(starts,[starts[1],len(scene.body)],strict=True)],tail)
    talk = graph.lines(scene,0,starts[0],talk)
    return graph.add(f'rev:{scene.id}:entry',type='stage',source=scene.source(scene.line),next=talk,
        scene={'space':space,'perspective':'current-observation'},
        presentation={'music':{'operation':'play','cue':'bgm_freetime'}})


def later_optional_meeting(graph,scenes,ident,space,tail):
    scene = scenes[ident]
    following = tail
    tail = graph.finish_free_time(scene,tail)

    def select(key,question,starts,join,target):
        options = []
        for i,(at,stop) in enumerate(zip(starts,[*starts[1:],join],strict=True)):
            flag = chr(65+i)
            response = graph.lines(scene,at+1,stop,target)
            options.append({'id':flag,'label':scene.body[at].removeprefix('### ').removeprefix(flag+'. '),
                            'set':{key:flag},'to':response})
        return graph.add('rev:'+key+':choice',type='menu',q=question,source=scene.source(scene.line+starts[0]+1),options=options)

    if ident=='05-F05':
        first = scene.body.index('### 선택 SHO-02A — 자동차를 어디로 보낼까')
        shared = scene.body.index('### 좋아하는 것을 묻는 질문')
        second = scene.body.index('### 선택 SHO-02B — 가져가는 이유')
        end = scene.body.index('### 끝 — 부르지 않은 노래')
        starts = [i for i,row in enumerate(scene.body) if row.startswith(('### A. ','### B. ','### C. '))]
        tail = graph.lines(scene,end+1,len(scene.body),tail)
        tail = select(ident+':reason','어떤 이유로 가져가고 싶을까?',starts[3:],end,tail)
        tail = graph.lines(scene,shared+1,second,tail)
        tail = select(ident,'차를 어떻게 움직여 볼까?',starts[:3],shared,tail)
        previous = scene.body.index('### 지난 만남 — 다시 맡기지 않는 것')
        join = scene.body.index('### 고치는 사람을 부를까')
        condition = next(i for i,row in enumerate(scene.body) if row.startswith('함께 읽을 곳만 물었던 경우'))
        tail = graph.lines(scene,join+1,first,tail)
        a = graph.lines(scene,previous+1,condition,tail)
        b = graph.lines(scene,condition+1,join,tail)
        tail = graph.add('rev:05:toy-previous-meeting',type='branch',cases=[
            {'flag':'05-F01','equals':'A','to':a},{'flag':'05-F01','equals':'B','to':b}],default=tail)
        tail = graph.lines(scene,0,previous,tail)
    else:
        starts = [i for i,row in enumerate(scene.body) if row.startswith('### ')]
        assert len(starts)==4
        tail = graph.lines(scene,starts[-1]+1,len(scene.body),tail)
        tail = select(ident,'어느 말을 먼저 건넬까?',starts[:3],starts[-1],tail)
        tail = graph.lines(scene,0,starts[0],tail)
    entry = graph.add(f'rev:{ident}:entry',type='stage',scene={'space':space},next=tail,source=scene.source(scene.line),
                      presentation={'music':{'operation':'play','cue':'bgm_freetime'}})
    menu = graph.add(f'rev:{ident}:visit',type='menu',q='이 사람을 다시 찾아갈까?',options=[
        {'id':'meet','label':('쇼가 있는 로비로 간다' if ident=='05-F05' else '창가의 유우를 찾아간다'),'to':entry},
        {'id':'skip','label':'다음 장소로 간다','to':following}])
    prerequisite = '05-F01' if ident=='05-F05' else '04-F01'
    return graph.add(f'rev:{ident}:available',type='branch',cases=[
        {'flag':prerequisite,'equals':flag,'to':menu} for flag in ('A','B')],default=following)


def chapter_five_entry(scenes, archive_objects, package_objects):
    graph = CampaignGraph()
    dead = ['kaede', 'taiga', 'ai', 'rin', 'sora', 'riku', 'ken', 'haruka', 'rei', 'koto']
    seats = [name for name in SPEAKERS.values() if name != 'lappy']
    records = {
        'v4:V5-5:injury': ('05-I01', 'hotel_rest_lounge', '음용 전 팔의 부상',
                           '쇼는 낮에 팔꿈치 상처를 확인했다. 그 뒤에도 말을 하고 직접 걸었다. 나중의 사인과는 별개다.', [-1.2, 1.25, 1.9]),
        'v4:V5-5:archive-route': ('05-I05', 'lower_stairway', '동시간대 운영동의 동선',
                                  '쇼와 유우는 운영동의 통로를 확인했다. 준비 시간에 라운지에 없었으며, 보관실 안을 계속 본 것도 아니다.', [0, 1.25, 1.9]),
        'v4:V5-5:cup': ('05-I02', 'hotel_rest_lounge', '개인 잔과 공용 재료의 잔류 대조',
                         '표식이 있는 잔의 안쪽에 남은 흔적은 공용 물과 찻잎에서 같게 확인되지 않았다. 처음의 빈 잔과 실제 마신 잔을 따로 기록했다.', [1.35, 1.25, 1.9]),
        'v4:V5-5:stock': ('05-I04a','operating_archive','처음 여섯 병과 남은 다섯 병',
                          '처음 여섯 칸과 현재 같은 자리에 남은 다섯 칸을 비교했다. 빈 칸의 번호만으로 용기를 꺼낸 손이나 개봉한 때를 확정할 수 없다.', [1.1,1.2,.9]),
        'v4:V5-5:mark-window': ('05-I02b','hotel_rest_lounge','손잡이 표식이 보이기 시작한 때',
                          '창가에 앉아 탁자에 잔이 놓일 때부터 손잡이 표식이 보였다. 다시 내려놓을 때도 같은 위치였다. 복도에서 처음 본 빈 잔과 공용 포트에는 같은 표식이 없다.', [.7,1.21,-1.1]),
        'v4:V5-5:drink-timing': ('05-I01a','hotel_rest_lounge','음용과 최초 어지럼의 순서',
                          '팔 처치 뒤에는 걸으며 말할 수 있었다. 미오는 표식 잔을 들어 마신 뒤 어지럽다는 말을 직접 들었다. 이전에 말하지 않은 증상까지 부정하는 기록은 아니다.',[-1.75,1.22,-.85]),
        'v4:V5-5:first-stock': ('05-I04b','operating_archive','문턱을 넘기 전 처음 실물 계수',
                          '나나와 아카리는 문 안에서 실제 여섯 용기를 함께 셌다. 나나가 문 밖으로 옮겨 간 뒤에는 선반 전체를 계속 보지 못했다. 현재의 빈 D칸과 시점을 구별한다.',[-1.2,1.2,.9]),
        'v4:V5-5:sealed-five': ('05-I04a','operating_archive','남은 다섯 용기의 봉함',
                          '나중 확인에서 남은 다섯 용기의 봉함이 모두 닫혀 있었다. 빈 칸과 실물 봉함은 다른 관찰이다. 사용 후 그대로 돌려놨다는 가설에는 닫힌 봉함을 설명할 추가 행동이 필요하다.',[.6,1.2,-1.4]),
        'v4:V5-5:package-pieces': ('05-I06','operating_archive','별도 봉투에 둔 용기와 띠 조각',
                          '사츠키가 건넨 용기와 아카리 가방 안감에서 확인한 띠 조각을 따로 보관했다. 파단면을 직접 맞추기 전에는 같은 물건에서 떨어졌는지 확정하지 않는다.',[1.6,1.2,-1.2]),
        'v4:V5-5:pour-boundary': ('05-I05c','hotel_rest_lounge','포트와 마지막 잔 인계의 대조',
                          '공용 포트와 개인 잔은 다른 위치다. 표식이 있는 잔이 마지막으로 건너간 방향은 보였지만 준비대 상판이 잔 안과 라벨을 가렸다. 개인 잔의 잔류와 공용 재료 검사, 인계를 별도로 놓는다.',[1.7,1.2,-.4]),
        'v4:V5-5:rewind': ('05-I03','hotel_rest_lounge','남은 두 종이와 되감기 범위',
                          '보호 페이지에 적힌 글은 남았고 일반 메모는 비었다. 나나는 14시 동석을 기억하지만 사용은 전해 들었다. 열 초 안의 물건 상태도 돌아가고 사용자는 기억을 보존한다. 하루 한 번, 아침 일곱 시 갱신이다.',[-.65,1.2,-1.45]),
        'v4:V5-5:window-witness': ('05-I05a','lower_stairway','준비 중 창가와 운영동의 동시 위치',
                          '준비 중 미오와 사츠키는 창가에 있었다. 쇼와 유우는 운영동에 있었다. 사츠키가 나중에 자료대에 용기를 내려놓은 일은 다른 시점이며, 두 기록을 하나의 연속 관찰로 보지 않는다.',[-1.15,1.2,1.75]),
        'v4:V5-5:oath-closure': ('05-I04','operating_archive','사망과 전문 공개 전후의 표시',
                           '이 맹세의 대가는 손목 통증이다. 17일 저녁 아홉 시가 오거나 제삼자에게 세 번째 쪽 전문을 직접 보여 주면 종료된다. 코토 사망 뒤 남았던 선은 사츠키가 전문을 본 뒤 사라졌다. 나나의 선은 그대로다.',[0,1.2,-1.4]),
        'v4:V5-5:conversation-scope': ('05-I06b','operating_archive','기록과 회수, 직접 나눈 말의 범위',
                           '남은 글, 별도로 보관한 두 조각, 미오가 복도에서 직접 한 말은 서로 다른 자료다. 먼저 대화를 시작한 묶음 외의 필수 관찰도 확인했지만 듣지 않은 사적인 문답까지 옮겨 적지 않았다.',[-1.45,1.2,-1.3]),
    }
    end = graph.add('rev:05:excerpt-end', type='end')
    case = scenes['05-T00']
    photo_at = case.body.index('#### 같은 물에서 나왔다고 하려면')
    lie_at = case.body.index('#### 우소다마 — 빈 칸에 다른 병을 세워 놓으면')
    mine_at = case.body.index('#### 발굴 — 여섯 가운데 없어진 것')
    next_at = case.body.index('#### 논스톱 — 비어 있던 잔도 같은 잔인가')
    mine_source = case.source(case.line+mine_at+2)
    mine_id = 'T5-MM-REV01'
    image = MINE_ART+'archive-slot-board.svg'
    alternatives = [
        ('archive-d','D 글자가 찍힌 봉함대','',''),
        ('archive-tape','공용 포장 띠','쇼','띠의 재질은 맞지만 이 물건에서 빠진 칸의 위치를 확인할 수 없습니다.'),
        ('archive-e','남아 있던 E 용기의 보호턱','아카리','그쪽에는 검사 때에도 용기가 있었어요. 빈 곳을 다시 보세요.'),
        ('archive-return','문밖에서 확인한 반납표','나나','저는 반납표를 확인했어요. 선반 안쪽에서 비어 있던 칸을 본 건 아니에요.'),
    ]
    later = {mine_id:{'taskId':mine_id,'ready':True,'requiresEvidence':['v4:V5-5:stock'],
        'stage':{'id':mine_id,'kind':'mindmine','v4':True,'title':'여섯 가운데 없어진 것','image':image,
                 'question':'처음 있었으나 검사 때 비어 있던 용기의 자리를 특정할 표식은?',
                 'answerRegionId':'archive-d','mineObjects':archive_objects,
                 'regions':[{'id':key,'label':label,'correct':not actor,'wrongVariant':key}
                            for key,label,actor,_ in alternatives]},
        'queues':{'wrongVariants':[{'cause':key,'script':[{'id':f'{mine_id}:{key}','type':'say','actor':SPEAKERS[actor],
                    'speaker':actor,'text':reply,'source':mine_source}]} for key,_,actor,reply in alternatives if actor]}}}
    hearing_records = {**records,
        'v4:V5-5:fitting-edge': ('05-T02','','두 파단면의 맞물림',
            '용기 몸체에 남은 띠의 끊긴 면과 가방 안감의 조각이 맞물린다. 인쇄 번호와 별개인 실물 대조이며, 목격하지 않은 투입 장면은 추가하지 않는다.',[]),
        'v4:V5-5:rewind-timeboard': ('05-T02','','음용과 열 초의 시작점',
            '확인한 음용과 첫 증상이 실제로 돌아간 열 초보다 앞에 있다. 되감은 뒤 아카리는 가방을 붙잡고 잔을 두라고 했다. 이전에 끝난 음용은 그 열 초 안에 들어오지 않는다.',[]),
        'v4:V5-5:death-confirmation': ('05-I04','','쇼가 남긴 사망 확인',
            '사망 확인은 전문을 공개하기 전의 별도 기록이다. 사망 판정만으로는 손목의 표시가 바뀌었는지 알 수 없다.',[]),
        'v4:V5-5:nana-line': ('05-I04','','그대로 남은 다른 맹세',
            '아카리가 전문을 보여 준 뒤에도 나나의 선은 그대로다. 다른 조건으로 맺은 약속이 함께 끝난 것은 아니다.',[]),
    }
    final, final_checkpoints = chapter_five_final_hearing(graph,scenes,later,hearing_records,dead,seats,end)
    late = chapter_five_late_hearing(graph,scenes,later,hearing_records,dead,seats,final)
    package = chapter_five_package_hearing(graph,scenes,later,hearing_records,dead,seats,package_objects,late)
    cup_hearing = chapter_five_cup_hearing(graph,scenes,later,records,dead,seats,package)
    timing = chapter_five_timing(graph,scenes,later,records,dead,seats,cup_hearing)
    tail = timing
    for number,scene_id,title,rule,ammo,speaker in reversed([
        (5,'05-T00a','겉에 적힌 글자만 남았다면','05-I04a의 **남아 있는',
         ['v4:V5-5:first-stock','v4:V5-5:stock','v4:V5-5:sealed-five'],'나나'),
        (6,'05-T00b','공용 포트만 나중에 씻었다면','4에 쏠 대조 언령은',
         ['v4:V5-5:cup','v4:V5-5:injury','v4:V5-5:pour-boundary'],'유우')]):
        tail, more = late_case_trial(graph,scenes,5,scene_id,title,rule,4,records,ammo,speaker,tail,dead,seats,
                                    round_number=number,include_intro=True,
                                    correction='앞에서 무엇을 셌는지로 나중 상태를 대신 확인할 수는 없어요.' if number==5 else None)
        later.update(more)
    selection = next(i for i,row in enumerate(case.body) if row.startswith('### 증거 선택 — 비었을 때와 뜯었을 때'))
    after = next(i for i in range(selection,len(case.body)) if SAY.match(case.body[i]))
    tail = graph.lines(case,after,len(case.body),tail)
    ident = 'T5-BU-REV01'
    ref = case.source(case.line+selection+1)
    ammo = ['v4:V5-5:stock','v4:V5-5:package-pieces','v4:V5-5:pour-boundary']
    cards = [{'id':key,'name':records[key][2],'text':records[key][3]} for key in ammo]
    later[ident] = {'taskId':ident,'ready':True,'requiresEvidence':ammo,
        'stage':{'id':ident,'v4':True,'kind':'bullet','options':cards,'answer':ammo[1],
                 'question':'반출과 개봉을 구분하기 위해 아직 맞춰 보지 않은 물증은?'},
        'queues':{'wrongVariants':[{'optionIndex':i,'script':[{'id':f'{ident}:{i}','type':'say',
            'actor':actor,'speaker':speaker,'text':reply,'source':ref}]} for i,actor,speaker,reply in [
            (0,'nana','나나','빈 칸은 조사 때 보았어요. 빠진 용기가 어디에서 처음 열렸는지는 안 보여요.'),
            (2,'sho','쇼','공용 포트의 상태는 준비 위치를 확인할 자료입니다. 용기의 봉함과는 다릅니다.')]]}}
    tail = graph.add('rev:05:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    for number,title,rule,ammo,speaker in reversed([
        (3,'증상은 먼저, 잔은 나중이었다면','05-D04의 음용과 최초',
         ['v4:V5-5:injury','v4:V5-5:cup','v4:V5-5:drink-timing'],'사츠키'),
        (4,'나나가 문 밖에 나가기 전','05-I04a의 공동 최초 계수',
         ['v4:V5-5:stock','v4:V5-5:archive-route','v4:V5-5:first-stock'],'아카리')]):
        tail, more = late_case_trial(graph,scenes,5,'05-T00',title,rule,4,records,ammo,speaker,tail,dead,seats,
                                    round_number=number)
        later.update(more)
    tail, more = late_case_trial(graph,scenes,5,'05-T00','비어 있던 잔도 같은 잔인가',
                                 '정답 05-D04의 잔 표식',4,records,
                                 ['v4:V5-5:cup','v4:V5-5:stock','v4:V5-5:mark-window'],'아카리',tail,dead,seats,
                                 round_number=2)
    later.update(more)
    tail = graph.lines(case,mine_at+1,next_at,tail)
    tail = graph.add('rev:05:stock-position-document',type='document',title='D 봉함대와 빈 칸',
                     rows=['처음 기록의 D 표식과 현재 빈 칸의 받침을 대조했다. 그 용기를 누가 들어 냈는지까지 본 것은 아니다.'],
                     image=MINE_ART+'archive-d.svg',source=mine_source,next=tail)
    tail = graph.add('rev:05:stock-mine',type='task',taskId=mine_id,trialDead=dead,seats=seats,
                     source=mine_source,success=tail,next=tail)
    lie_id = 'T5-LI-REV01'
    ref = case.source(case.line+lie_at+1)
    stock = 'v4:V5-5:stock'
    cup = 'v4:V5-5:cup'
    lie_cards = [{'id':key,'name':records[key][2],'text':records[key][3]} for key in (stock,cup)]
    lie_rows = [
        debate_statement(lie_id,1,'나나','제가 문턱 밖에 있을 때 선반 전체를 봤다고 말씀드린 적 없어요.',ref),
        debate_statement(lie_id,2,'아카리','**빠진 병이 어느 칸에 있었는지 누가 제대로 확인했어요?**',ref,'weak',stock),
        debate_statement(lie_id,3,'미오','처음 셌을 때와 지금 남은 자리를 맞춰 볼게.',ref),
    ]
    later[lie_id] = {'taskId':lie_id,'ready':True,'requiresEvidence':[stock,cup],
        'stage':{'id':lie_id,'kind':'nonstop','v4':True,'title':'빈 칸에 다른 병을 세워 놓으면','lines':lie_rows,
                 'options':lie_cards,'authoredAmmo':[stock,cup],'filterOwnedEvidence':True,
                 'wrongCards':{cup:'personal-cup'}},
        'transformation':{'sourceEvidenceId':stock,'lieLabel':'남은 병 하나도 이미 열려 있었다','intentionalHold':True},
        'debate':{'id':lie_id,'kind':'nonstop','lines':lie_rows,'bullets':lie_cards},
        'queues':{'wrongVariants':[{'cause':'personal-cup','script':[{'id':lie_id+':personal-cup','type':'say',
                  'actor':'nana','speaker':'나나','text':'잔에 남은 것과 선반에 남은 병의 수는 다른 기록이에요.',
                  'source':ref}]}]}}
    lied = graph.lines(case,lie_at+1,mine_at,tail)
    normal = graph.add('rev:05:stock-count-only',type='say',actor='mio',speaker='미오',
                       text='처음 여섯이었고 지금 다섯이야. 누가 빠진 칸의 표지를 봤는지는 아직 쓰지 않을게.',source=ref,next=tail)
    tail = graph.add('rev:05:stock-perjury',type='task',taskId=lie_id,trialDead=dead,seats=seats,source=ref,
                     success=normal,next=normal,outcomes={
                         'normal':{'judgment':'refute','to':normal},
                         'perjury':{'judgment':'lie','to':lied,'sets':{'05-T00:perjury':True}}})
    tail = graph.lines(case,photo_at+1,lie_at,tail)
    compare = 'rev:05:cup-separation'
    photo_ref = case.source(case.line+photo_at+1)
    wrong = graph.add(compare+':common',type='say',actor='sho',speaker='쇼',
                      text='같은 성분이 확인된 곳은 잔 안쪽입니다. 공용 재료와 한 줄에 놓지 마십시오.',source=photo_ref,next=compare)
    accusation = graph.add(compare+':accuse',type='say',actor='satsuki',speaker='사츠키',
                           text='표식부터 봐. 어떤 잔을 받았는지 확인했지 누가 약을 넣었는지는 아직 안 나왔어.',source=photo_ref,next=compare)
    tail = graph.add(compare,type='menu',q='같은 흔적을 확인한 용기는?',source=photo_ref,
                     options=[{'id':'shared','label':'모두가 쓴 공용 포트','to':wrong},
                              {'id':'marked','label':'나중에 마신 표식 있는 개인 잔','to':tail},
                              {'id':'actor','label':'준비대에 손을 댄 사람의 잔','to':accusation}])
    after_first = case.body.index('#### 재료를 갈라 놓고 읽는다')
    tail = graph.lines(case,after_first+1,photo_at,tail)
    tail, tasks = late_case_trial(graph, scenes, 5, '05-T00', '빈 잔을 가져오면',
                                  '정답 개인 잔과 공용 재료', 4, records,
                                  ['v4:V5-5:archive-route', 'v4:V5-5:injury', 'v4:V5-5:cup'], '아카리', tail, dead, seats)
    tasks.update(later)
    refusal=scenes['05-T0B'];offsets=[i for i,r in enumerate(refusal.body) if BULLET.match(r)]
    assert len(offsets)==3
    tail=graph.lines(refusal,offsets[-1]+1,len(refusal.body),tail)
    choices=[]
    responses=[('쇼','코토 씨께 직접 대답을 들었던 때와 그 뒤 운영동으로 갔던 때는 따로 말씀드리겠습니다.'),
        ('나나','제가 처음 놓은 빈 잔과 나중에 다른 분이 들고 가신 잔을 다른 줄에 둘게요.'),
        ('미오','대답하지 않은 걸 갖고 있었다는 칸에 놓을 수는 없어. 그 물건이 실제로 있던 쪽부터 보자.')]
    for flag,at,(speaker,text) in zip('ABC',offsets,responses,strict=True):
        to=graph.add('rev:05-T0B:response:'+flag,type='say',actor=SPEAKERS[speaker],speaker=speaker,
            text=text,source=refusal.source(refusal.line+at+1),next=tail)
        choices.append({'id':flag,'label':BULLET.match(refusal.body[at])[1],'set':{refusal.id:flag},'to':to})
    tail=graph.add('rev:05-T0B:choice',type='menu',q='유우를 다시 부르기 전에 어느 자료부터 볼까?',options=choices,
        source=refusal.source(refusal.line+offsets[0]+1))
    tail=graph.lines(refusal,0,offsets[0],tail)
    opening = scenes['05-T0A']
    tail = graph.lines(opening, 0, len(opening.body), tail)
    opening_rule = next(i for i,row in enumerate(opening.body) if row.startswith('현재 맹세의 대가와 검안'))
    opening_ref = opening.source(opening.line + opening_rule + 1)

    def compare_cause(following):
        menu = 'rev:05:opening-medical-check'
        options = []
        for key,label,speaker,reply in (
            ('injury','먼저 다친 팔을 사망 원인으로 놓는다','쇼',
             '팔을 살핀 뒤에도 직접 걸으셨습니다. 나중에 확인한 사인은 그 상처가 아닙니다.'),
            ('oath','손목의 맹세가 호흡 곤란을 일으켰다','나나',
             '조건 사본에는 손목이 아프다고만 돼 있어요. 숨을 못 쉬게 된다는 줄은 없어요.'),
            ('exam','검안에서 확인한 R-7과 앞서 확인한 부상을 나눈다','미오',
             '먼저 난 상처하고 죽게 만든 물질을 나눠 놓을게. 그게 어디서 들어왔는지는 이제부터 봐야 해.'),
        ):
            reply_id = graph.add(f'{menu}:{key}',type='say',actor=SPEAKERS[speaker],speaker=speaker,text=reply,
                                 source=opening_ref,next=following if key=='exam' else menu)
            options.append({'id':key,'label':label,'to':reply_id})
        verify = graph.add(menu,type='menu',q='검안에서 확인한 사망 원인을 어디에 놓을까?',
                           options=options,source=opening_ref)
        verify = graph.add('rev:05:opening-medical-record',type='document',title='검안과 맹세의 조건',
                           rows=['검안에서 사인으로 확인한 물질은 R-7이다. 앞선 팔 상처나 손목의 맹세 대가와 다르다.',
                                 '이 결과로 무엇을 통해 물질이 들어갔는지나 누가 건넸는지까지 확정할 수 없다.'],
                           source=opening_ref,next=verify)
        debate, more = late_case_trial(graph,scenes,5,opening.id,'쓰러진 장면부터 떠올리면',
            '현재 맹세의 대가와 검안',4,records,
            ['v4:V5-5:injury','v4:V5-5:cup','v4:V5-5:oath-closure'],'나나',verify,dead,seats,
            round_number=15,correction='그건 제가 말씀드린 호흡 곤란이 어떤 대가였는지 적은 종이가 아니에요.',
            include_conclusion=False)
        tasks.update(more)
        return debate

    tail = graph.insert_before_source_line(tail,opening_ref,compare_cause)
    tail = graph.add('rev:05:court-entry', type='stage', enterCourt=True, next=tail)

    def inspect_papers(scene, record):
        comparison = scenes['05-I03b']
        labels = ('같은 두 관찰','한쪽에만 있는 다음 줄','잔이 현재 자리로 돌아온 때')
        starts = [comparison.body.index('#### '+label) for label in labels]
        join = comparison.body.index('### 같은 글이 남았다는 말')
        following = graph.lines(comparison,join+1,len(comparison.body),record)
        menu = 'rev:05:paper-observations'
        options = []
        for i,(label,start,stop) in enumerate(zip(labels,starts,[*starts[1:],join])):
            flag = f'05-I03b:{i}'
            observed = graph.add(f'{menu}:read:{i}',type='say',actor='mio',speaker='미오',mono=True,
                text=('음용과 첫 반응은 두 면에 모두 남았다.','보호 면에만 다음 줄이 적혀 있다.',
                      '기억하는 잔의 자리와 종이에 남은 글을 나눠 뒀다.')[i],
                source=comparison.source(comparison.line+start+1),set={flag:True},next=menu)
            to = graph.lines(comparison,start+1,stop,observed)
            options.append({'id':str(i),'label':label,'requires':{flag:False},'to':to})
        options.append({'id':'continue','label':'두 종이와 지금 보이는 물건을 따로 기록한다','to':following,
                        'requires':{f'05-I03b:{i}':True for i in range(3)}})
        tail = graph.add(menu,type='menu',q='무엇이 앞뒤를 이어 주는지 확인한다',options=options,
                         source=comparison.source(comparison.line+starts[0]+1))
        tail = graph.lines(comparison,0,starts[0],tail)
        return graph.lines(scene,0,len(scene.body),tail)

    def inspect_packages(scene, record):
        at = next(i for i,row in enumerate(scene.body) if row.startswith('플레이어는 봉투 표기를'))
        after = graph.lines(scene,at+1,len(scene.body),record)
        menu = 'rev:05:package-custody'; ref = scene.source(scene.line+at+1)
        retry = graph.add(menu+':retry',type='say',actor='sho',speaker='쇼',
            text='사츠키 씨가 내려놓은 것은 용기입니다. 나중에 안감에서 확인한 조각과 보관 담당은 별도로 적으십시오.',
            source=ref,next=menu)
        after = graph.add(menu,type='menu',q='누가 무엇을 넘겼는지 어떻게 기록할까?',source=ref,options=[
            {'id':'same','label':'용기와 안감 조각 모두 사츠키가 직접 건넸다','to':retry},
            {'id':'separate','label':'사츠키가 건넨 용기 / 가방 안감에서 확인한 조각','to':after}])
        after = graph.lines(scene,0,at,after)
        recovery = scenes['05-I04c']
        first = recovery.body.index('#### 수사 — 찾기 전 사진과 찾은 뒤 사진')
        recovered = next(i for i in range(first,len(recovery.body)) if SAY.match(recovery.body[i]))
        after = graph.lines(recovery,recovered,len(recovery.body),after)
        menu = 'rev:05:recovery-photos'
        options = []
        for i,(label,text) in enumerate([
            ('열기 전 가방 바깥','바깥쪽만 찍혔다. 이때 안쪽의 조각을 읽은 사람은 없다.'),
            ('용기를 내려놓은 손','사츠키가 나중에 용기를 들었다. 처음 준비 때도 들었다고 이 사진에 쓸 수는 없다.'),
            ('용기가 나간 뒤 가방 안감','안감이 접힌 틈에 띠 조각이 남아 있었다. 같은 파단면인지는 다음에 확인한다.')]):
            flag = f'05-I04c:{i}'
            to = graph.add(f'{menu}:read:{i}',type='say',actor='mio',speaker='미오',mono=True,text=text,
                source=recovery.source(recovery.line+first+1),set={flag:True},next=menu)
            options.append({'id':str(i),'label':label,'requires':{flag:False},'to':to})
        options.append({'id':'continue','label':'사진의 확인 범위를 따로 남긴다','to':after,
                        'requires':{f'05-I04c:{i}':True for i in range(3)}})
        after = graph.add(menu,type='menu',q='회수 전에 보았던 것부터 구분한다',options=options,
                          source=recovery.source(recovery.line+first+1))
        return graph.lines(recovery,0,first,after)

    def stock_boundary(scene):
        return next(i for i,row in enumerate(scene.body) if row.startswith('(남은 다섯 용기의 봉함을 확인한다.'))

    def inspect_sealed_five(scene, record):
        at = stock_boundary(scene)
        after = graph.lines(scene,at+1,len(scene.body),record)
        return graph.add('rev:05:sealed-five-observation',type='say',actor='mio',speaker='미오',mono=True,
            text='남은 다섯 용기는 하나씩 표지를 맞추고 봉함이 닫혀 있는지 확인했다. 빈 D칸은 그중 하나가 아니다.',
            source=scene.source(scene.line+at+1),next=after)

    def inspect_oath(scene, record):
        ref = scene.source(scene.line)
        death = 'v4:V5-5:death-confirmation'
        other = 'v4:V5-5:nana-line'
        steps = [
            ('사망 확인 뒤 아카리의 손목','아직 아홉 시가 되지 않았다. 코토의 사망을 확인했지만 아카리의 손목에는 검은 선이 남아 있다.',death),
            ('사츠키가 처음 받은 두 쪽','먼저 건네받은 두 쪽에는 이번 약속을 끝내는 세 번째 쪽의 전문이 없다. 아카리가 그 쪽을 따로 펼친다.',None),
            ('전문 공개 뒤 두 사람의 손목','사츠키가 마지막 쪽 전체를 직접 읽었다. 아카리의 선은 사라졌고 나나의 선은 그대로였다.',other),
        ]
        tail = record
        for index,(label,observed,key) in reversed(list(enumerate(steps))):
            ident = f'rev:05:oath-observation:{index}'
            if key:
                _,_,name,facts,_ = hearing_records[key]
                tail = graph.add(ident+':card',type='evidence',evidenceId=key,name=name,text=facts,source=ref,next=tail)
            tail = graph.add(ident,type='document',title=label,rows=[observed],source=ref,next=tail)
            if index == 1:
                tail = graph.lines(scene,0,len(scene.body),tail)
        return tail

    def inspect_injury(scene, record):
        tail = graph.lines(scene,0,len(scene.body),record)
        at = next(i for i,row in enumerate(scene.body) if row.startswith('05-F01에서'))
        ref = scene.source(scene.line+at+1)
        responses = [
            ('A','mio','미오','들으신 말하고 보신 상태를 따로 적을게요.'),
            ('B','sho','쇼','말할 수 있었던 때의 줄부터 보시죠.'),
        ]
        cases = [{'flag':'05-F01','equals':flag,'to':graph.add('rev:05:aid-note:'+flag,
            type='say',actor=actor,speaker=speaker,text=text,source=ref,next=tail)} for flag,actor,speaker,text in responses]
        return graph.add('rev:05:aid-note',type='branch',cases=cases,default=tail)

    def inspect_conversations(scene,record):
        starts = [i for i,row in enumerate(scene.body) if row.startswith(('### A. ','### B. ','### C. '))]
        join = scene.body.index('### 세 묶음을 놓고 나갈 때')
        after = graph.lines(scene,join+1,len(scene.body),record)
        common = next(i for i,row in enumerate(scene.body) if row.startswith('**사츠키**　네가 앞에서 뭐 했다고'))
        third = graph.lines(scene,common,join,after)
        branches = [i for i,row in enumerate(scene.body) if row.startswith('- **')]
        assert len(branches)==3
        cases = [{'flag':'05-D03a','equals':flag,'to':graph.lines(scene,at+1,stop,third)}
                 for flag,at,stop in zip('ABC',branches,[*branches[1:],common],strict=True)]
        third = graph.add('rev:05:investigation-corridor-memory',type='branch',cases=cases,default=third)
        third = graph.lines(scene,starts[2]+1,branches[0],third)
        options = [
            {'id':'A','label':'남아 있는 글을 사츠키 앞으로 가져간다','set':{scene.id:'A'},
             'to':graph.lines(scene,starts[0]+1,starts[1],after)},
            {'id':'B','label':'병과 포장 조각을 별도로 둔다','set':{scene.id:'B'},
             'to':graph.lines(scene,starts[1]+1,starts[2],after)},
            {'id':'C','label':'분류대에서 내가 한 말을 먼저 적는다','set':{scene.id:'C'},'to':third},
        ]
        entry = graph.add('rev:05:investigation-record-order',type='menu',q='어느 묶음부터 대화를 시작할까?',
                         options=options,source=scene.source(scene.line+starts[0]+1))
        return graph.lines(scene,0,starts[0],entry)

    tail = late_case_investigation(graph,scenes,5,'hotel_rest_lounge',records,tail,
        routes={'v4:V5-5:rewind':inspect_papers,'v4:V5-5:package-pieces':inspect_packages,
                'v4:V5-5:stock':lambda scene,record:graph.lines(scene,0,stock_boundary(scene),record),
                'v4:V5-5:sealed-five':inspect_sealed_five,'v4:V5-5:oath-closure':inspect_oath,
                'v4:V5-5:injury':inspect_injury,'v4:V5-5:conversation-scope':inspect_conversations},
        supplemental={'v4:V5-5:drink-timing':['05-I01b'],'v4:V5-5:package-pieces':['05-I02a','05-I04d'],
            'v4:V5-5:rewind':['05-I03a','05-I05d'],'v4:V5-5:sealed-five':['05-I04e'],
            'v4:V5-5:pour-boundary':['05-I05b'],'v4:V5-5:conversation-scope':['05-I06a']},
        prerequisites={'v4:V5-5:drink-timing':['v4:V5-5:injury'],
            'v4:V5-5:first-stock':['v4:V5-5:stock'],'v4:V5-5:sealed-five':['v4:V5-5:stock'],
            'v4:V5-5:package-pieces':['v4:V5-5:stock'],'v4:V5-5:pour-boundary':['v4:V5-5:cup','v4:V5-5:mark-window'],
            'v4:V5-5:conversation-scope':['v4:V5-5:package-pieces','v4:V5-5:rewind','v4:V5-5:oath-closure'],
            'v4:V5-5:rewind':['v4:V5-5:drink-timing','v4:V5-5:mark-window']})
    event = scenes['05-D04']
    start = event.body.index('### 그 전에 함께 센 사람')
    back = event.body.index('### 다시 라운지의 창가')
    missing = next(i for i, raw in enumerate(event.body) if raw.startswith('사츠키가 문 쪽에 대고'))
    tail = graph.add('rev:05:announcement', type='stage', next=tail, presentation={'actions': ['body_announcement']})
    tail = graph.add('rev:05:medic-observation', type='say', actor='mio', speaker='미오', mono=True,
                     text='쇼가 마신 게 무엇인지 물었다. 나는 손잡이에 표식이 있는 잔을 가리켰다. 쇼는 잔을 옮기지 않고 사람을 살폈다.',
                     source=event.source(event.line + len(event.body)), next=tail)
    tail = graph.add('rev:05:cup-stays', type='say', actor='akari', speaker='아카리', text='잔은 두셔도 돼요.',
                     source=event.source(event.line + missing + 1), next=tail)
    drinking = next(i for i, raw in enumerate(event.body) if raw.startswith('16:45 무렵'))
    tail = graph.lines(event, drinking + 1, missing, tail)
    tail = graph.add('rev:05:marked-cup-observation', type='say', actor='mio', speaker='미오', mono=True,
                     text='손잡이에 표식이 붙은 잔을 코토가 들었다가 내려놓았다. 얼마 뒤 일어나려던 코토가 다시 자리에 앉았다.',
                     source=event.source(event.line + drinking + 1), next=tail)
    tail = graph.lines(event, back + 1, drinking, tail)
    tail = graph.add('rev:05:return-window', type='stage', next=tail,
                     scene={'space': 'hotel_rest_lounge', 'perspective': 'current-observation'})
    count = next(i for i, raw in enumerate(event.body) if raw.startswith('**나나**　여섯이에요.'))
    tail = graph.lines(event, count, back, tail)
    tail = graph.add('rev:05:initial-stock', type='say', actor='nana', speaker='나나', mono=True,
                     text='두 줄의 칸을 함께 확인했다. 각인과 빈칸을 구분해 표시하고 두 사람이 함께 있던 때만 적었다.',
                     source=event.source(event.line + count), next=tail)
    tail = graph.lines(event, start + 1, count, tail)
    tail = graph.add('rev:05:objective-stocktake', type='stage', next=tail,
                     scene={'space': 'operating_archive', 'perspective': 'objective-observation'})
    tail = graph.lines(event, 0, start, tail)
    tail = graph.add('rev:05:cup-preparation', type='stage', next=tail,
                     scene={'space': 'hotel_rest_lounge', 'perspective': 'current-observation'})
    for key,space in reversed([
        ('05-D03c','lower_stairway'),('05-D03d','garden_rest_area'),('05-D03e','hotel_rest_lounge'),
        ('05-D03f','operating_archive'),('05-D03g','hotel_corridor'),('05-D03h','lower_stairway'),
    ]):
        if key=='05-D03d':
            tail = daily_scene_route(graph,scenes[key],space,tail)
            tail = later_optional_meeting(graph,scenes,'05-F05','hotel_rest_lounge',tail)
            continue
        tail = daily_scene_route(graph,scenes[key],space,tail)
    corridor = scenes['05-D03a']
    cuts = [i for i,row in enumerate(corridor.body) if row.startswith(('#### A. ','#### B. ','#### C. '))]
    join = corridor.body.index('### 합류')
    assert len(cuts)==3
    tail = graph.menu(corridor,'복도에서 아카리에게 무슨 말을 할까?',[
        (corridor.body[at][8:],at+1,stop,'') for at,stop in zip(cuts,[*cuts[1:],join])],tail)
    tail = graph.lines(corridor,0,cuts[0],tail)
    for key,space in reversed([('05-D03','hotel_rest_lounge'),('05-D03b','operating_archive')]):
        tail = daily_scene_route(graph,scenes[key],space,tail)
    for key,space in reversed([
        ('05-D02f','operating_archive'),('05-D02g','garden_rest_area'),('05-D02i','garden_rest_area'),
        ('05-D02j','hotel_rest_lounge'),('05-D02h','operating_archive'),('05-D02l','hotel_corridor'),
        ('05-D02k','dining_room'),('05-D02m','dining_room'),('05-D02o','operating_archive'),
        ('05-D02q','hotel_rest_lounge'),('05-D02p','hotel_corridor'),
    ]):
        tail = daily_scene_route(graph,scenes[key],space,tail)
        if key=='05-D02o':
            tail = later_optional_meeting(graph,scenes,'05-F06','hotel_rest_lounge',tail)
    rules = scenes['05-D02']
    warning = scenes['05-D02n']
    tail = daily_scene_route(graph,warning,'operating_archive',tail)
    tail = daily_scene_route(graph,scenes['05-D02b'],'operating_archive',tail)
    tail = daily_scene_route(graph,scenes['05-D02d'],'dining_room',tail)
    duties = scenes['05-D02a']
    first = next(i for i,row in enumerate(duties.body) if row.startswith('05-F04 A를'))
    second = next(i for i,row in enumerate(duties.body) if row.startswith('B를 봤다면'))
    join = next(i for i,row in enumerate(duties.body) if row.startswith('만남을 지나쳤다면'))
    tail = graph.add('rev:05:free-before-case',type='menu',q='다음 점검 전 어디로 갈까?',options=[
        {'id':'envelope','label':'식당에 남은 사츠키와 이야기한다','to':optional_meeting(graph,scenes['05-F02'],
            'dining_room','빈 봉투를 어떻게 남길까?',tail)},
        {'id':'skip','label':'운영동으로 간다','to':tail}])
    tail = graph.lines(duties,join+1,len(duties.body),tail)
    paths = [{'flag':'05-F04','equals':key,'to':graph.lines(duties,at+1,end,tail)}
             for key,at,end in [('A',first,second),('B',second,join)]]
    tail = graph.add('rev:05:tea-memory',type='branch',cases=paths,default=tail)
    tail = graph.lines(duties,0,first,tail)
    tail = graph.add('rev:05:duties',type='stage',scene={'space':'dining_room'},next=tail,
                     presentation={'music':{'operation':'play','cue':'bgm_daily_mono'}})
    tail = graph.add('rev:05:free-before-duties',type='menu',q='잠깐 남은 시간을 어떻게 보낼까?',options=[
        {'id':'aid','label':'쇼와 빈 처치 기록을 살핀다','to':optional_meeting(graph,scenes['05-F01'],
            'hotel_rest_lounge','쇼에게 무엇을 부탁할까?',tail)},
        {'id':'skip','label':'다음 날 일 분담으로 간다','to':tail}])
    tail = daily_scene_route(graph,scenes['05-D02e'],'dining_room',tail)
    tail = graph.lines(rules,0,len(rules.body),tail)
    tail = graph.add('rev:05:free-before-agreement',type='menu',q='분류대가 비기 전 어디에 들를까?',options=[
        {'id':'paper','label':'분류대 옆 코토를 찾아간다','to':optional_meeting(graph,scenes['05-F03'],
            'operating_archive','남은 종이를 어떻게 둘까?',tail)},
        {'id':'tea','label':'창가에서 아카리를 만난다','to':optional_meeting(graph,scenes['05-F04'],
            'hotel_rest_lounge','아카리에게 어떻게 대답할까?',tail)},
        {'id':'skip','label':'다음 장면으로 간다','to':tail}])
    for key,space in reversed([('05-D01b','park_main_gate'),('05-D01c','park_main_gate'),('05-D01a','operating_archive')]):
        tail = daily_scene_route(graph,scenes[key],space,tail)
    daily = scenes['05-D01']
    entry = graph.lines(daily, 0, len(daily.body), tail)
    entry = graph.add('rev:05:daily', type='stage', next=entry,
                      scene={'space': 'operating_archive', 'perspective': 'current-observation'})
    checkpoint_cards = [{'id':key,'name':value[2],'text':value[3]} for key,value in records.items()]
    checkpoints = {}
    for name,target in [('timing-hearing','rev:05:T5-NS-REV03'),('package-hearing',package),
                        ('late-hearing',late),('final-hearing',final),*final_checkpoints.items()]:
        cards = checkpoint_cards
        if name not in ('timing-hearing','package-hearing'):
            cards = [{'id':key,'name':value[2],'text':value[3]} for key,value in hearing_records.items()]
        checkpoint = graph.add(f'rev:05:{name}:court-entry',type='stage',enterCourt=True,next=target)
        for card in reversed(cards):
            checkpoint = graph.add(f'rev:05:{name}:seed:'+card['id'],type='evidence',evidenceId=card['id'],
                                   name=card['name'],text=card['text'],next=checkpoint)
        checkpoints[name] = {'entry':checkpoint,'evidence':cards}
    return ({'schemaVersion': 1, 'contentVersion': 'v4', 'campaignRevision': 'rewrite-v5', 'chapter': '5',
             'entry': entry, 'nodes': graph.nodes, 'trialRoster': {'dead': dead, 'seats': seats},
             'qaCheckpoints':checkpoints}, tasks)


def chapter_six_document_hearing(graph,scenes,tasks,dead,seats,tail):
    def reasoning(scene,ident,at,checks,target):
        ref=scene.source(scene.line+at+1)
        questions=[]
        for i,(question,options,answer,speaker,text) in enumerate(checks):
            questions.append({'q':question,'options':options,'optionIds':[str(j) for j in range(3)],
                'answer':options[answer],'success':[],
                'wrongVariants':[{'optionId':str(j),'script':[{'id':f'{ident}:wrong:{i}:{j}','type':'say',
                    'actor':SPEAKERS[speaker],'speaker':speaker,'text':text,'source':ref}]} for j in range(3) if j!=answer]})
        tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':['v4:V5-6:document-order','v4:V5-6:document-edit'],
            'stage':{'id':ident,'kind':'reasoning','v4':True,'title':scene.title,'questions':questions},'queues':{}}
        return graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,
            success=target,next=target)
    scene=scenes['06-T0D']
    tail=graph.lines(scene,52,len(scene.body),tail)
    ident='T6-QA-REV08';ref=scene.source(scene.line+52)
    tasks[ident]={'taskId':ident,'ready':True,'requiresEvidence':['v4:V5-6:document-order'],
        'stage':{'id':ident,'kind':'choice','v4':True,'question':'미오의 노트가 다음 재현에서 확정할 수 있는 범위는?',
            'options':['그 뒤 미오가 멀리서 추락을 보았다','둘이 함께 통로 쪽으로 이동했다',
                       '요약이 혼자라고 하므로 함께 갔다는 글도 잘못됐다'],'answer':1},
        'queues':{'wrongVariants':[{'optionIndex':i,'script':[{'id':f'{ident}:wrong:{i}','type':'say',
            'actor':SPEAKERS[speaker],'speaker':speaker,'text':text,'source':ref}]} for i,speaker,text in [
                (0,'미오','그 글씨는 없어. 지금 이 그림을 본 거지 그때의 기억이 돌아온 게 아니야.'),
                (2,'쇼','같은 번호의 접수 원문을 먼저 펼치겠습니다. 요약과 다른 줄이 원문에 남아 있습니다.')]]}}
    tail=graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    tail=graph.lines(scene,28,49,tail)
    tail=reasoning(scene,'T6-RE-REV04',27,[
        ('당시 미오가 직접 적은 문장은 어디에 놓을까?', ['당시의 동행 기록','나중에 편집한 요약','지금 기억하지 못하는 여백'],0,
         '쇼','원문의 마지막 줄은 다른 분이 쓴 서명 진술입니다. 지금은 미오 씨 필기를 묻고 있습니다.'),
        ('사후에 혼자였다고 정리한 문장은?', ['현재 누가 읽는지의 기록','나중에 나간 요약','미오가 그다음에 본 기억'],1,
         '미오','내가 쓴 줄하고 나중에 정리한 말을 같은 문장으로 놓지는 않을게.'),
        ('노트 다음 구간의 빈칸으로 남겨 둘 것은?', ['다른 사람이 확인한 추락','원문에 남은 동행','지금 미오가 기억하지 못하는 뒤의 구간'],2,
         '미오','기억이 돌아온 게 아니야. 빈칸에 추락 그림을 놓으면 내가 본 일이 돼 버리잖아.'),
    ],tail)
    tail=graph.lines(scene,0,25,tail)
    scene=scenes['06-T0C']
    tail=graph.lines(scene,26,len(scene.body),tail)
    tail=reasoning(scene,'T6-RE-REV03',25,[
        ('당시 원문이 접수된 범위를 어디에 놓을까?', ['당시 접수된 원문의 행','나중에 나간 요약의 빠진 줄','지금 화면을 읽는 순서'],0,
         '사츠키','원문도 없어졌다고 하지 마. 앞에서 같은 번호의 그 쪽을 직접 봤잖아.'),
        ('나중 묶음에서 빠진 문장은 무엇과 비교할까?', ['현재 말하는 사람의 얼굴','당시 원문과 나중 요약의 서로 다른 줄','지금 화면을 켠 차례만'],1,
         '나나','원문이 남아 있는 것과 요약에서도 같은 줄을 읽을 수 있는지는 달라요.'),
        ('지금 재판 화면의 열람 순서는 어디에 놓을까?', ['옛날의 첫 승인 칸','원문을 처음 쓴 사람의 칸','현재 누가 어느 화면을 읽었는지'],2,
         '쇼','어느 날 누구 화면에 떠 있었는지부터 보십시오. 오늘 읽는 순서를 첫날 승인으로 쓰지 않습니다.'),
    ],tail)
    return graph.lines(scene,0,23,tail)


def chapter_six_opening_hearing(graph,scenes,tasks,records,dead,seats,tail):
    root = 'v4:V5-6:'
    for number,scene_id,title,rule,keys,speaker,correction in [
        (17,'06-T0B','아직 읽지 않은 문장','06-I03c의 **당시 접수',['signature','operation-screen','document-order'],'쇼',
         '서명을 받은 기록과 그 문서가 처음 접수됐는지는 따로 확인하십시오.'),
        (16,'06-T0E','전실 표의 마지막 칸','약점은 4다.',['entry-count','separate-connections','old-intake-scope'],'사츠키',None),
        (15,'06-T0F','날짜만 당긴 일이라면','4에 **06-I02a의 처음',['document-edit','safety-hold','inspection-order'],'유우',None),
    ]:
        tail,more = late_case_trial(graph,scenes,6,scene_id,title,rule,4,records,[root+key for key in keys],
            speaker,tail,dead,seats,round_number=number,include_intro=True,correction=correction)
        tasks.update(more)

    scene = scenes['06-T0A']
    point = scene.body.index('#### 지점 지목 — 보류 번호가 정상으로 옮겨 적힌 곳')
    reasoning = scene.body.index('#### 추리 연결 — 두 시계가 가리키는 곳')
    panic = scene.body.index('#### 패닉 — 옛 접수와 지금 접수')
    aftermath = scene.body.index('### 영향 범위 — 한 사람이 그 결과를 전부 냈나')

    def source(at):
        return scene.source(scene.line+at+1)

    def reply(ident,speaker,line,at):
        return {'id':ident,'type':'say','actor':SPEAKERS[speaker],'speaker':speaker,'text':line,'source':source(at)}

    def task(ident,stage,keys,at,target,queues=None):
        tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':[root+key for key in keys],
            'stage':{'id':ident,'v4':True,**stage},'queues':queues or {}}
        return graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=source(at),
                         success=target,next=target)

    tail = graph.lines(scene,aftermath+1,len(scene.body),tail)
    ident = 'T6-PN-REV02'
    keys = ['entry-count','railing','side-door']
    cards = [{'id':root+key,'name':records[root+key][2],'text':records[root+key][3]} for key in keys]
    lanes = [{'id':label,'actor':SPEAKERS[name],'speaker':name,'lines':[]} for label,name in zip(
        ('왼쪽','가운데','오른쪽'),('사츠키','유우','쇼'))]
    concise = {(3,1):'거기 네 이름 있었잖아. 그 아래 내 이름을 쓰기 전엔 누가 기다렸는데?',
               (3,2):'같은 장치의 앞뒤는 볼 수 있습니다. 다른 장치의 시각은 기준이 필요합니다.',
               (4,1):'빨리 나타난 사람과 늦게 적힌 사람을 같이 보자. 어디까지 갔는지도 볼게.',
               (4,2):'오늘은 위치만 봅니다. 그날 돌아온 분은 영상과 증언으로 확인하십시오.'}
    rows = []
    for i,row in enumerate(scene.body[panic+1:aftermath],panic+1):
        cells = [cell.strip() for cell in row.strip('|').split('|')]
        if len(cells)!=4 or not cells[0].isdigit():
            continue
        beat = int(cells[0])
        for lane_index,(lane,raw) in enumerate(zip(lanes,cells[1:])):
            weak = (beat,lane_index)==(6,1)
            line = concise.get((beat,lane_index),raw).removesuffix(' 약점.')
            row = debate_statement(ident,f'{lane_index}:{beat}',lane['speaker'],line,source(i),
                'weak' if weak else 'plain',root+keys[-1] if weak else '')
            rows.append(row)
            lane['lines'].append(row['id'])
            if '[큰 소리]' in raw:
                loud = debate_statement(ident,'noise',lane['speaker'],line,source(i),'noise')
                loud.update(noiseRole='loud',noiseDurability=2,hostStatement=row['id'])
                rows.append(loud)
    assert len(rows)==19 and all(len(row['text'])<=48 for row in rows)
    tail = task(ident,{'kind':'panic','title':'옛 접수와 지금 접수','lines':rows,'options':cards,
        'filterOwnedEvidence':True},keys,panic,tail)
    tasks[ident]['debate'] = {'id':ident,'kind':'panic','lines':rows,'bullets':cards,'lanes':lanes,'synchronizedBeats':True}
    after = next(i for i in range(reasoning,panic) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,after,panic,tail)
    ident = 'T6-RE-REV02'
    checks = [
        ('두 시계에서 같은 사건을 어떻게 비교할까?', ['오늘 입소 명단과 옛 승인표','주 통로 영상과 같은 구역의 경보','현재 난간 사진과 옛 서명'],1,
         '쇼','오늘의 날짜를 옮기지 마시고, 당시 두 장치가 같은 구역의 반응을 남긴 때를 확인하십시오.'),
        ('전실에 늦게 적힌 이름에서 확인할 수 있는 것은?', ['그날 공원 밖에 있었다','추락할 때 통로에 있었다','그때 전실에서 이름을 확인했다'],2,
         '나나','전실에서 적힌 이름으로 그 전에 어느 통로에 있었는지를 대신 쓰지 말아 주세요.'),
        ('주 통로 영상이 찍지 못한 경로는?', ['옆 출입구','지금의 교체 난간','현재 입소를 처리한 문'],0,
         '사츠키','앞만 찍은 영상이 가린 길을 봐. 지금의 입소 문을 옛날 지도에 붙이지 마.'),
        ('문턱에서 어느 쪽이 가렸는지 볼 자료는?', ['옛 도면과 입구 재현','난간의 교체 날짜','현재 단말의 통행 상태'],0,
         '쇼','교체 날짜나 통행 값으로 옛날 보이던 각도를 재지 않습니다.'),
        ('손이 이어 움직였는지 확인할 자료는?', ['접수 번호의 숫자','먼저 접촉이 끝난 때와 뒤에 힘이 생긴 때','동행을 인정한 서명만 확인'],1,
         '사츠키','이름 쓰기 전에 몇 번 움직였는지 봐. 접수 번호나 동행만으로는 안 나오잖아.'),
        ('지금 아직 부탁할 수 없는 증언은?', ['당시 기다린 위치','바깥쪽이 가려지는 지점','제약이 남은 채로 직접 본 주체의 이름이나 암시'],2,
         '나나','제가 확인해 드릴 수 있는 위치는 말씀드릴게요. 아직 누구였는지는 말할 수 없어요.'),
    ]
    questions = []
    for i,(question,options,correct,speaker,wrong) in enumerate(checks):
        at = next(j for j in range(reasoning+1,after) if scene.body[j].startswith(f'{i+1}. '))
        ids = [f'option-{j}' for j in range(len(options))]
        questions.append({'q':question,'options':options,'optionIds':ids,'answer':options[correct],
            'success':[reply(f'{ident}:{i}:correct','미오',options[correct]+'.',at)],
            'wrongVariants':[{'optionId':ids[j],'script':[reply(f'{ident}:{i}:wrong:{j}',speaker,wrong,at)]}
                             for j in range(len(options)) if j!=correct]})
    tail = task(ident,{'kind':'reasoning','title':'두 시계가 가리키는 곳','questions':questions},
        ['voice-window','side-door','motion','oath-rule'],reasoning,tail)
    tail = graph.lines(scene,point+1,reasoning,tail)
    regions = [
        ('item','항목 번호',(.14,.28,.34,.55),'쇼','앞의 미해결 행과 번호가 같다는 것부터 봤습니다. 이후 상태를 적은 칸은 옆입니다.'),
        ('status','점검 결과',(.35,.28,.66,.55),'',''),
        ('date','발행 날짜',(.67,.28,.86,.55),'나나','언제 그 종이를 보냈는지는 맞아요. 어떤 상태라고 쓰셨는지는 옆에 있어요.'),
        ('signature','별지 서명',(.14,.62,.86,.77),'사츠키','걔가 다시 서명한 건 지나고 나서야. 운영 서명 앞에 갖다 놓지 마.'),
    ]
    ident = 'T6-SP-REV01'
    tail = task(ident,{'kind':'spot','question':'받아 넘긴 항목의 실제 상태와 달라진 곳은?',
        'image':MINE_ART+'inspection-result-columns.svg','answerRegionId':'status','regions':[
            {'id':key,'label':label,'wrongVariant':key,'polygon':[[x,y],[x1,y],[x1,y1],[x,y1]]}
            for key,label,(x,y,x1,y1),_,_ in regions]},
        ['inspection-order','safety-hold'],point,tail,{'wrongVariants':[
            {'cause':key,'script':[reply(ident+':'+key,speaker,wrong,point)]}
            for key,_,_,speaker,wrong in regions if speaker]})
    return graph.lines(scene,0,point,tail)


def chapter_six_transition_hearing(graph,scenes,tasks,records,dead,seats,tail):
    root = 'v4:V5-6:'
    scene = scenes['06-T01']
    heading = scene.body.index('#### 논의 스크럼 — 자료의 이름으로 책임을 정해도 되나')
    ident = 'T6-SD-REV01'
    pairs = []
    responses = [
        '제가 물은 건 누가 승인했는지입니다.','기억을 바꾼 일까지 다른 사람이 했다고 적지는 말아 주세요.',
        '말한 사람 이름부터 정해 버리면 제가 밖에서 뭘 말할지 또 정해지잖아요.','문을 건너 본 분은 아직 없습니다.',
        '그 연결이 남는지를 물었어요. 문이 열리는지는 그다음에 봐도 돼요.','구조 요청만 하겠다는 분이 무엇에 동의했는지부터 들을게요.',
    ]
    anchors = [('승인','승인'),('누가 봤는지','방향'),('밖에 도착하면','밖에서'),
        ('나갈 수','직접'),('의식 지원','작동 조건'),('전원이 동의','동의했는지')]
    for i,row in enumerate(scene.body[heading+1:],heading+1):
        if match := re.fullmatch(r'\| ([^　]+)　“(.+)” \| ([^ ]+) \| ([^　]+)　“(.+)” \|',row):
            speaker,claim,topic,ally,response = match.groups()
            claim_word,response_word = anchors[len(pairs)]
            key = f'{ident}:{len(pairs)}'
            pairs.append({'id':key,'them':speaker,'themActor':SPEAKERS[speaker],'themText':claim,
                'us':ally,'usActor':SPEAKERS[ally],'usText':response,'keyword':topic,'claimKeyword':claim_word,
                'responseKeyword':response_word,'duration':11,'wrong':[{'id':key+':wrong','type':'say',
                    'actor':SPEAKERS[speaker],'speaker':speaker,'text':responses[len(pairs)],
                    'source':scene.source(scene.line+i+1)}]})
    assert len(pairs)==6
    ref = scene.source(scene.line+heading+1)
    tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':[root+key for key in ('past-confirmed','separate-connections','private-records')],
        'stage':{'id':ident,'kind':'scrum','v4':True,'title':'자료의 이름으로 책임을 정해도 되나','pairs':pairs,
            'teams':{'them':['sho','nana'],'us':['mio','satsuki','yuu']},'scrumDecoys':[{'keyword':word} for word in ('피해 집계','출석')],
            'scrumPresentation':{'topic':'확인된 책임을 어떻게 남길까','them':'밖에서 먼저 확인한다','us':'각자가 책임과 선택을 구분한다'}},'queues':{}}
    tail = graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    tail = graph.lines(scene,0,heading,tail)
    for number,scene_id,title,rule,keys,speaker in [
        (14,'06-T00e','열린 시각에 멈춘 것','4에는 **06-I06b의 비상',['side-door','first-approval','emergency-open'],'유우'),
        (13,'06-T00f','경보가 뒤에 울렸으니까','정답은 **06-I02a의 보류',['harm-separation','emergency-open','alarm-order'],'사츠키'),
    ]:
        tail,more = late_case_trial(graph,scenes,6,scene_id,title,rule,4,records,[root+key for key in keys],
            speaker,tail,dead,seats,round_number=number,include_intro=True,
            correction=('전실에 들어간 수는 읽었어. 그 숫자로 옆의 설비가 다 고쳐졌다고 읽지는 말자.' if number==14 else None))
        tasks.update(more)
    scene = scenes['06-T00a']
    heading = scene.body.index('#### 패닉 — 같은 줄로 옮겨진 피해')
    rule = next(i for i,row in enumerate(scene.body) if row.startswith('정답은 06-I06b의'))
    ident = 'T6-PN-REV01'
    actors = ('유우','사츠키','나나')
    lanes = [{'id':lane,'actor':SPEAKERS[name],'speaker':name,'lines':[]} for lane,name in zip(('왼쪽','가운데','오른쪽'),actors)]
    ammo = [root+key for key in ('side-door','first-approval','harm-separation')]
    cards = [{'id':key,'name':records[key][2],'text':records[key][3]} for key in ammo]
    rows = []
    condensed = {(3,2):'문 열릴 때 계셨던 분을 봤어요. 그전에 어디에 계셨는지는 몰라요.',
                 (4,2):'전실에서 이름을 확인했어요. 이상을 보고한 곳은 제가 못 봤어요.',
                 (5,1):'뒤에 다시 읽어. 들어가도 된다고 했던 때를 먼저 보고 있어.',
                 (5,2):'제가 기다린 문은 알아요. 저절로 열린 데가 더 있는지는 못 봤어요.'}
    for i,row in enumerate(scene.body[heading+1:rule],heading+1):
        cells = [cell.strip() for cell in row.strip('|').split('|')]
        if len(cells)!=4 or not cells[0].isdigit():
            continue
        beat = int(cells[0])
        for lane_index,(lane,claim) in enumerate(zip(lanes,cells[1:])):
            weak = (beat,lane_index)==(7,0)
            line = condensed.get((beat,lane_index),claim).replace('[약점] ','')
            ref = scene.source(scene.line+i+1)
            statement = debate_statement(ident,f'{lane_index}:{beat}',lane['speaker'],line,ref,
                                          'weak' if weak else 'plain',ammo[-1] if weak else '')
            rows.append(statement)
            lane['lines'].append(statement['id'])
            if '[큰 소리]' in claim:
                noise = debate_statement(ident,'noise',lane['speaker'],line,ref,'noise')
                noise.update(noiseRole='loud',noiseDurability=2,hostStatement=statement['id'])
                rows.append(noise)
    assert len(rows)==25 and all(len(row['text'])<=48 for row in rows),[(row['id'],len(row['text'])) for row in rows]
    tail = graph.lines(scene,rule+1,len(scene.body),tail)
    tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':ammo,
        'stage':{'id':ident,'kind':'panic','v4':True,'title':'같은 줄로 옮겨진 피해','lines':rows,'options':cards,
            'filterOwnedEvidence':True},'debate':{'id':ident,'kind':'panic','lines':rows,'bullets':cards,'lanes':lanes,
                'synchronizedBeats':True},'queues':{}}
    tail = graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                     source=scene.source(scene.line+heading+1),success=tail,next=tail)
    tail = graph.lines(scene,0,heading,tail)
    scene = scenes['06-T00d']
    return graph.lines(scene,0,len(scene.body),tail)


def hearing_insertion(graph, scene, heading, tail):
    at = scene.body.index(heading)
    after = next(i for i in range(at+1,len(scene.body)) if SAY.match(scene.body[i]))
    entry = graph.lines(scene,0,len(scene.body),tail)
    previous = graph.nodes[entry]
    while graph.nodes[previous['next']]['source']['line'] != scene.line+after+1:
        previous = graph.nodes[previous['next']]
    return at, entry, previous


def hearing_check(graph, tasks, scene, at, dead, seats, tail, ident, evidence, question, answers):
    ref = scene.source(scene.line+at+1)
    tasks[ident] = {
        'taskId':ident,'ready':True,'requiresEvidence':['v4:V5-6:'+key for key in evidence],
        'stage':{'id':ident,'kind':'choice','v4':True,'question':question,
                 'options':[label for label,_ in answers],
                 'answer':next(i for i,(_,reply) in enumerate(answers) if reply is None)},
        'queues':{'wrongVariants':[
            {'optionIndex':i,'script':[{'id':f'{ident}:wrong:{i}','type':'say',
                'actor':SPEAKERS[reply[0]],'speaker':reply[0],'text':reply[1],'source':ref}]}
            for i,(_,reply) in enumerate(answers) if reply is not None]},
    }
    return graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                     source=ref,next=tail,success=tail)


def chapter_six_post_operating(graph,scenes,tasks,records,dead,seats,tail):
    root = 'v4:V5-6:'
    scene = scenes['06-T02j']
    at = scene.body.index('### 같이 앉을 자리를 골랐을 때')
    after = next(i for i in range(at+1,len(scene.body)) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,after,len(scene.body),tail)
    ident = 'T6-QA-REV07'
    ref = scene.source(scene.line+at+1)
    tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':[root+'live-response',root+'separate-connections'],
        'stage':{'id':ident,'kind':'choice','v4':True,'question':'남은 대답을 기다리겠다는 말은 어디까지 정한 걸까?',
            'options':['현재 대화와 나중에 실행할 상태를 구분한다','나나는 이미 지원 유지를 약속했다',
                       '사츠키는 무조건 빨리 나가자는 말만 했다','말하고 싶지 않다면 아무것도 모른다고 적는다'],'answer':0},
        'queues':{'wrongVariants':[{'optionIndex':i,'script':[{'id':f'{ident}:{i}','type':'say',
            'actor':SPEAKERS[speaker],'speaker':speaker,'text':text,'source':ref}]} for i,speaker,text in [
                (1,'나나','나중에 다시 물어보겠다고 했어요. 그분이 계속 무엇을 하실지 제가 먼저 맞다고 하지 않았어요.'),
                (2,'사츠키','여기서 누구 없어지는 걸 보고도 빨리 가고 싶다고 내가 말한 적 있어?'),
                (3,'유우','내가 나중에 바꿀 수도 있다고 했어. 네가 하라는 쪽으로 간다는 말은 아니야.')]]}}
    tail = graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,next=tail,success=tail)
    tail = graph.lines(scene,0,at,tail)
    for key in reversed(('06-T02b','06-T02g','06-T02c','06-T02a')):
        scene = scenes[key]
        if key!='06-T02g':
            tail = graph.lines(scene,0,len(scene.body),tail)
            continue
        at, entry, previous = hearing_insertion(graph,scene,'### 나중에 다르게 할 수 있었던 일',tail)
        tail = previous['next']
        menu = 'rev:06:operating-decisions'
        options = []
        for i,(title,evidence,question,answers) in enumerate((
            ('입소 전 차폐',('first-approval',),'기본값과 별도로 운영자가 고른 일은?',[
                ('초기 설정이 그대로 실행됐다',('래피','안내에서 읽은 값과 제가 승인한 줄이 따로 있어요.')),
                ('입소 전에 관계 차폐를 승인했다',None),
                ('광장에 모인 참가자가 차폐를 승인했다',('쇼','광장에 모인 것은 승인 행이 남은 뒤입니다.'))]),
            ('첫 판정 뒤 집행',(),'판정이 끝난 뒤 운영자가 따로 한 일은?',[
                ('범행을 한 사람과 같은 행동을 했다',('사츠키','걔가 한 건 걔 일로 먼저 놔. 그 뒤에 네가 그 애한테 한 일도 있잖아.')),
                ('모든 참가자의 표를 대신 눌렀다',('유우','내가 낸 표는 내가 눌렀어. 네가 다음에 한 일하고 같이 쓰지 마.')),
                ('집계 뒤 집행 장치를 작동시켰다',None)]),
            ('마지막 구역 해금',('separate-connections',),'마지막 구역이 열린 일에서 무엇을 확인했지?',[
                ('운영자가 그때 구역과 자료를 열었다',None),
                ('앞선 죽음이 해금의 기술적 조건이었다',('미오','처음 받은 확장 설명에 그런 조건은 없었어. 열린 순서만으로는 몰라.')),
                ('방송 장치가 자료를 읽고 해금을 결정했다',('쇼','장치가 내보낸 말로 결정한 사람까지 특정할 수는 없습니다.'))]),
        )):
            flag = f'{menu}:{i}'
            done = graph.add(flag,type='stage',set={flag:True},next=menu)
            task_node = hearing_check(graph,tasks,scene,at,dead,seats,done,f'T6-QA-REV{12+i}',evidence,question,answers)
            options.append({'id':str(i),'label':title,'requires':{flag:False},'to':task_node})
        options.append({'id':'finish','label':'세 결정의 기록을 따로 남긴다','to':tail,
                        'requires':{f'{menu}:{i}':True for i in range(3)}})
        previous['next'] = graph.add(menu,type='menu',q='어느 때의 기록부터 대조할까?',options=options,
                                     source=scene.source(scene.line+at+1))
        tail = entry
    scene = scenes['06-T02h']
    at = scene.body.index('#### 섬광 애너그램 — 돌아가서 또 승인할 수 있었나')
    after = next(i for i in range(at+1,len(scene.body)) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,after,len(scene.body),tail)
    answer,decoys,question = ANAGRAMS[scene.id]
    ident = 'T6-AN-REV02'
    tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':[root+'reapprove'],
        'stage':{'id':ident,'kind':'anagram','v4':True,'chapter':6,'title':'다시 고를 수 있던 때',
            'question':question,'answer':answer,'distractors':list(decoys)},'queues':{}}
    tail = graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                     source=scene.source(scene.line+at+1),next=tail,success=tail)
    tail = graph.lines(scene,0,at,tail)
    scene = scenes['06-T02d']
    first = scene.body.index('### 세 사람의 행동을 한 칸에 넣었을 때')
    parts = [i for i,row in enumerate(scene.body) if row.startswith('#### ')]
    join = scene.body.index('### 남겨 둘 말')
    assert len(parts)==3
    tail = graph.lines(scene,join+1,len(scene.body),tail)
    menu = 'rev:06:past-verdict-actions'
    options = []
    for i,(at,stop,label) in enumerate(zip(parts,[*parts[1:],join],[
        '첫 재판의 순찰표와 집행을 나눠 본다','한 몸의 두 행위와 투표를 나눠 본다','마지막 준비와 사후의 소지를 나눠 본다'],strict=True)):
        flag = menu+':'+str(i)
        read = graph.add(flag,type='stage',set={flag:True},next=menu)
        read = graph.lines(scene,at+1,stop,read)
        options.append({'id':str(i),'label':label,'requires':{flag:False},'to':read})
    options.append({'id':'finish','label':'각자의 표와 운영자의 집행을 별도로 남긴다','to':tail,
                    'requires':{menu+':'+str(i):True for i in range(3)}})
    tail = graph.add(menu,type='menu',q='어느 재판부터 다시 펼칠까?',options=options,source=scene.source(scene.line+first+1))
    tail = graph.lines(scene,0,first,tail)
    scene = scenes['06-T02i']
    tail,more = late_case_trial(graph,scenes,6,scene.id,'그 사람이 지금 보여 주니까','4에 **06-I01a·I03f',4,records,
        [root+key for key in ('operation-screen','separate-connections','independent-records')],'유우',tail,dead,seats,
        round_number=19,include_intro=True,
        correction='내가 지금 네가 보여 준 걸 또 보는 거잖아. 다른 데서 확인한 건 어디 있어?')
    tasks.update(more)
    return tail


def chapter_six_personal_hearing(graph,scenes,tasks,records,dead,seats,tail):
    root = 'v4:V5-6:'
    scene = scenes['06-T01c']
    at = scene.body.index('#### 자료 선택 — 종료 전에 누구 목소리를 남겨야 해')
    first = next(i for i in range(at+1,len(scene.body)) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,first,len(scene.body),tail)
    ident = 'T6-QA-REV06'
    ref = scene.source(scene.line+at+1)
    tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':[root+'live-response'],
        'stage':{'id':ident,'kind':'choice','v4':True,'question':'누가 이 자리의 질문에 새 대답을 남길 수 있지?',
            'options':['옛 문서의 인수 내역','지금 래피에게 질문하고 답을 들은 사람','자동 반복 안내문'],'answer':1},
        'queues':{'wrongVariants':[{'optionIndex':i,'script':[{'id':f'{ident}:wrong:{i}','type':'say',
            'actor':SPEAKERS[speaker],'speaker':speaker,'text':text,'source':ref}]} for i,speaker,text in [
                (0,'쇼','지금 그 문장을 읽어도 과거의 작성자가 새로 답한 것은 아닙니다.'),
                (2,'유우','같은 말을 다시 들었어. 누가 방금 내 질문 듣고 바꾼 말인지도 봐야 해.')]]}}
    tail = graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
    tail = graph.lines(scene,0,at,tail)
    scene = scenes['06-T01d']
    at = scene.body.index('#### 반론 쇼다운 — 이름을 숨긴 약속과 만들어 낸 일')
    after = next(i for i in range(at+1,len(scene.body)) if scene.body[i].startswith('**유우**'))
    tail = graph.lines(scene,after,len(scene.body),tail)
    topics = [
        ('말하지 않은 경고','그날 경고를 말하지 않은 건 전부 약속이 시킨 거야',
         ['safety-hold','oath-rule','silence-boundaries'],'보류는 그 전에 남았다. 나중의 공개 제한이 앞선 점검 행동까지 만든 것은 아니다.'),
        ('형체를 만들기로 한 서명','공원에서 그 사람을 만들라고 약속한 데에도 서명이 있겠지',
         ['oath-rule','document-edit','entry-count'],'비밀을 먼저 전하지 않는 문구와 현재 내부 생성 행을 같이 보자. 둘이 같은 문장이 아니야.'),
        ('스스로 하지 않은 말','그 사람이 아무 말 안 하는 것도 전부 상대가 한 일',
         ['past-confirmed','entry-count','silence-boundaries'],'금지된 말과 그 밖에서 스스로 선택한 말을 나눠 줘. 지금 풀렸다고 어제부터 다 말한 건 아니야.'),
    ]
    for i,(title,claim,keys,wrong) in reversed(list(enumerate(topics))):
        row = next(j for j in range(at+1,after) if scene.body[j].startswith(f'{i+1}. '))
        ident = f'T6-RS-REV0{i+3}'
        cards = [{'id':root+key,'name':records[root+key][2],'text':records[root+key][3]} for key in keys]
        tail = compile_showdown(graph,tasks,dead,seats,'rev:06:'+ident,ident,title,'사츠키',[
            ['누가 그 조건을 받아들였는지 보자.','그 뒤에 누구한테 먼저 말을 못 했는지 물었어.'],[claim]],
            cards,root+keys[-1],scene.source(scene.line+row+1),('미오',wrong),tail)
    tail = graph.lines(scene,0,at,tail)
    scene = scenes['06-T01g']
    tail = graph.lines(scene,scene.body.index('### 다시 재생하지 않고 대답하는 사람')+1,len(scene.body),tail)
    tail,more = late_case_trial(graph,scenes,6,scene.id,'다시 말할 수 있으면 돌아온 거야?',
        '4번 약점에는 **옛 노트',4,records,[root+key for key in ('document-order','first-approval','memory-scope')],
        '래피',tail,dead,seats,round_number=18,include_intro=True,
        correction='그 글을 다시 읽었다는 건 맞아요. 지금 전해 들은 말이 자기 기억으로 돌아왔는지를 묻고 계시죠?')
    tasks.update(more)
    for key in reversed(('06-T01a','06-T01b','06-T01i','06-T01h','06-T01f','06-T01e')):
        scene = scenes[key]
        if key=='06-T01e':
            at, entry, previous = hearing_insertion(graph,scene,'### 같은 자리에 있었다는 세 가지',tail)
            tail = previous['next']
            for ident,evidence,question,answers in reversed((
                ('T6-QA-REV09',('old-intake-scope',),'나나가 미오를 처음 본 위치는 무엇으로 확인하지?',[
                    ('현재 재판장의 자리',('쇼','지금 서 계신 위치와 당시 전실에서 본 자리는 다릅니다.')),
                    ('전실 목격과 당시 위치를 대조한다',None),
                    ('이름이 적힌 모든 사람이 같은 자리였다',('유우','같은 표에 이름 올렸다고 같은 데 서 있었던 건 아니잖아.'))]),
                ('T6-QA-REV10',('memory-scope',),'나나가 그때 한 일을 무엇으로 확인하지?',[
                    ('방금 들은 나나의 직접 증언',None),
                    ('지금 나나에게 시험 발동을 부탁한다',('나나','저는 지금 하지 않을래요. 아까 말씀드린 것은 그때 제가 한 일이에요.')),
                    ('지금 닿은 손의 모습',('나나','지금 손이 닿는다고 그때 제가 잡았던 일이 다시 보이지는 않아요.'))]),
                ('T6-QA-REV11',('memory-scope',),'당시 미오가 돌아가려던 이유는 어디에 적을까?',[
                    ('전실에 갔으니 정해진 이유가 있었다고 적는다',('쇼','접수표는 당시 어디에 있었는지 대조할 수 있습니다. 이유를 대신 말해 주지는 않습니다.')),
                    ('손을 빼던 동작으로 이유까지 확정한다',('나나','손을 빼신 건 봤어요. 어디로 가려 하셨는지까지는 모르겠어요.')),
                    ('확인되지 않은 이유는 빈칸으로 둔다',None)]),
            )):
                tail = hearing_check(graph,tasks,scene,at,dead,seats,tail,ident,evidence,question,answers)
            previous['next'] = tail
            tail = entry
        elif key=='06-T01b':
            at = scene.body.index('#### 정답 선택 — 조용해진 사람을 세는 기준')
            after = next(i for i in range(at+1,len(scene.body)) if SAY.match(scene.body[i]))
            tail = graph.lines(scene,after,len(scene.body),tail)
            ident = 'T6-QA-REV05'
            ref = scene.source(scene.line+at+1)
            tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':[root+'memory-scope'],
                'stage':{'id':ident,'kind':'choice','v4':True,'question':'나나가 했다고 확인한 옛 개입의 범위는?',
                    'options':['첫 접수에 있던 14명 모두','먼저 함께 있던 다른 13명','이번에 입소한 15명 모두'],'answer':1},
                'queues':{'wrongVariants':[{'optionIndex':i,'script':[{'id':f'{ident}:wrong:{i}','type':'say',
                    'actor':SPEAKERS[speaker],'speaker':speaker,'text':text,'source':ref}]} for i,speaker,text in [
                        (0,'나나','저도 거기 있었어요. 제 손을 잡아 제가 잊었다고 말씀드리지는 않았어요.'),
                        (2,'쇼','옛 전실의 접수와 이번 실제 입소의 날짜를 따로 보십시오.')]]}}
            tail = graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,success=tail,next=tail)
            tail = graph.lines(scene,0,at,tail)
        else:
            tail = graph.lines(scene,0,len(scene.body),tail)
    return tail


def chapter_six_ending(graph, scenes):
    scene = scenes['06-R00']
    ref = lambda at: scene.source(scene.line+at+1)
    after = graph.add('rev:06:complete',type='end',campaignNarrativeEnd=True)
    after = graph.add('rev:06:last-record',type='stage',holdSeconds=3.0,shotPush=.01,
        shot={'image':'Assets/Art/revision_comic/chapter6/ending-record.webp'},next=after,
        source=ref(len(scene.body)-1))

    def illustrated(section,start,end,target,picture):
        entry = graph.lines(section,start,end,target)
        current = entry
        while current!=target:
            graph.nodes[current]['shot'] = {'image':'Assets/Art/revision_comic/chapter6/'+picture+'.webp'}
            current = graph.nodes[current]['next']
        return entry

    choices = []
    for support,scene_id,label in [
        ('held','06-R01','지금 지원을 유지한다'),('ended','06-R02','내 이름으로 지금 지원을 끊는다'),
    ]:
        branch = scenes[scene_id]
        start = 0
        outside = next(i for i,row in enumerate(branch.body) if row.startswith('문 바깥.' if support=='ended' else '### 밖에서 다시 불러 보는 사람'))
        tail = illustrated(branch,outside,len(branch.body),after,'ending-outside')
        if support=='ended':
            first_lie = next(i for i,row in enumerate(branch.body) if row.startswith('첫 재판에서 01-T04a의'))
            first_normal = next(i for i,row in enumerate(branch.body) if row.startswith('첫 재판에서 일반 대조를'))
            final_lie = next(i for i,row in enumerate(branch.body) if row.startswith('06-T02f에서 공개 합의를'))
            final_normal = next(i for i,row in enumerate(branch.body) if row.startswith('이 대화는 미오가 준비한'))
            # Keep the original confession nodes addressable by older saves.
            current = tail
            while graph.nodes[current]['source']['line'] < branch.line + first_lie + 1:
                before, current = current, graph.nodes[current]['next']
            previous_normal = None
            for key, flag, skip, replies in (
                ('first','01-T04a:perjury',first_normal,(
                    ('나나','쓰던 보호대에서 조각이 먼저 나왔어요. 새 봉투를 뜯은 건 그 뒤예요.'),
                    ('미오','저는 조각을 꺼낼 때 거기 없었어요. 그 순서는 나나한테 들었고요.'),
                )),
                ('final','06-T02f:perjury',final_normal,(
                    ('미오','안에서 같은 기록을 펼쳐 보기는 했어요. 제가 가져온 건 제 종이예요.'),
                )),
            ):
                last = current
                while graph.nodes[last]['source']['line'] < branch.line + skip + 1:
                    previous, last = last, graph.nodes[last]['next']
                ordinary = last
                for index, (speaker, line) in reversed(list(enumerate(replies))):
                    ordinary = graph.add(f'rev:06:ending-perjury:{key}:normal:{index}',type='say',
                        actor=SPEAKERS[speaker],speaker=speaker,text=line,
                        source=branch.source(branch.line+skip+1),next=ordinary,
                        shot={'image':'Assets/Art/revision_comic/chapter6/ending-outside.webp'})
                gate = graph.add(f'rev:06:ending-perjury:{key}',type='branch',
                                 cases=[{'flag':flag,'equals':True,'to':current}],default=ordinary)
                graph.nodes[before]['next'] = gate
                if previous_normal:
                    graph.nodes[previous_normal]['next'] = gate
                previous_normal = f'rev:06:ending-perjury:{key}:normal:{len(replies)-1}'
                before, current = previous, last
            assert first_normal < final_lie < final_normal
            confirmed = next(i for i,row in enumerate(branch.body) if row.startswith('미오가 확인을 누른다.'))
            tail = illustrated(branch,confirmed+1,outside,tail,'ending-ended')
            tail = graph.add('rev:06:support-ended',type='stage',set={'06:support':'ended'},
                             source=branch.source(branch.line+confirmed+1),next=tail,
                             holdSeconds=2.4,shotPush=.02,shotCue='sfx_machine',
                             shot={'image':'Assets/Art/revision_comic/chapter6/ending-ended.webp'},
                             presentation={'music':{'operation':'play','cue':'bgm_ending_b'}})
            tail = graph.add('rev:06:support-final-confirm',type='menu',q='지금 지원을 끊을까요?',options=[
                {'id':'return','label':'확인 전으로 돌아간다','to':'rev:06:support-choice'},
                {'id':'confirm','label':'내 이름으로 중단을 확인한다','to':tail}])
            tail = graph.lines(branch,start,confirmed,tail)
        else:
            tail = illustrated(branch,start,outside,tail,'ending-held')
            tail = graph.add('rev:06:support-held',type='stage',set={'06:support':'held'},next=tail,
                             holdSeconds=2.4,shotPush=.015,
                             shot={'image':'Assets/Art/revision_comic/chapter6/ending-held.webp'},
                             presentation={'music':{'operation':'play','cue':'bgm_ending_a'}})
        choices.append({'id':support,'label':label,'to':tail,'requires':{'06:outside-response':True,'06:gate-checked':True}})
    tail = graph.add('rev:06:support-choice',type='menu',q='창구의 의식 지원을 어떻게 할까?',options=choices)
    proof = graph.add('rev:06:support-notice',type='document',title='지원 상태와 종료의 범위',rows=[
        '중앙 통제는 끝났고, 외부 응답과 철문의 왕복은 각각 확인했다.',
        '지원은 창구의 현재 응답에만 해당한다. 유지하면 지금은 대답을 계속 들을 수 있다.',
        '중단 뒤에 같은 의식으로 다시 깨어날 수 있는지는 확인되지 않았다.'],next=tail)
    title = scene.body.index('### 두 이름을 전할 때')
    tail = graph.lines(scene,title+1,len(scene.body),proof)
    preference = next(i for i,row in enumerate(scene.body) if row.startswith('06-T02e의 선택에 따라'))
    callbacks = [
        ('A','nana','나나','제 쪽은 지금 제가 들고 있을게요. 미오 씨 것부터 읽으신다고 제 대답까지 들어 있지는 않아요.'),
        ('B','satsuki','사츠키','내가 읽고 싶은 때 읽을 거야. 네가 다시 알려 주지 않아도 돼.'),
        ('C','sho','쇼','먼저 통화하고 있는 사람과 현재 위치를 전달하겠습니다. 개인 기록은 아직 보내지 않았습니다.'),
    ]
    branch = [{'flag':'06-T02e','equals':key,'to':graph.add('rev:06:outside-record:'+key,
        type='say',actor=actor,speaker=speaker,text=text,source=ref(preference),next=tail)} for key,actor,speaker,text in callbacks]
    tail = graph.add('rev:06:outside-record',type='branch',cases=branch,default=tail)
    contact_memory = next(i for i,row in enumerate(scene.body) if row.startswith('06-I07d에서 사람 수를'))
    contact_cases = []
    for key, speaker, line in (
        ('A', '쇼', '여기서 직접 대답하실 수 있는 분부터 확인하겠습니다. 유우 씨, 잠시만 기다려 주십시오.'),
        ('B', '사츠키', '난 철문 옆이야. 유우, 다른 애들까지 나왔다고 하지 마.'),
    ):
        response = graph.add(f'rev:06:contact-order-memory:{key}', type='say', actor=SPEAKERS[speaker],
                             speaker=speaker, text=line, source=ref(contact_memory), next=tail)
        contact_cases.append({'flag':'06-I07d','equals':key,'to':response})
    tail = graph.add('rev:06:contact-order-memory', type='branch', cases=contact_cases,
                     source=ref(contact_memory), default=tail)
    control = scene.body.index('### 지금 끌 수 있는 것')
    desk = scene.body.index('### 창구에 가서 확인한다')
    manual = next(i for i,row in enumerate(scene.body) if row.startswith('사츠키가 철제 상자에서'))
    checked = next(i for i,row in enumerate(scene.body) if row.startswith('유우가 고개를 끄덕인다. 사츠키는 문턱을'))
    tail = illustrated(scene,checked+1,preference,tail,'ending-corner')
    tail = graph.add('rev:06:manual-verification',type='document',title='철문의 수동 개방과 왕복',rows=[
        '수동 부속을 홈에 맞춰 철문을 밀었다. 사츠키가 직접 건너갔다 돌아왔으며 유우가 문턱에서 확인했다.',
        '쇼가 바깥의 상대에게 별도로 이 결과를 전달했다. 상대의 소속을 직접 확인한 것은 아니다.'],
        set={'06:gate-checked':True},source=ref(checked),next=tail)
    tail = illustrated(scene,manual+1,checked,tail,'ending-gate')
    tail = graph.add('rev:06:manual-movement',type='stage',sfx='v4_door_hinge',source=ref(manual),next=tail)
    tail = graph.add('rev:06:manual-open',type='menu',q='사츠키가 어느 쪽을 먼저 확인할까?',source=ref(manual),
        options=[{'id':'manual','label':'수동 부속을 맞추고 철문을 민다','requires':{'06:outside-response':True},'to':tail}])
    tail = illustrated(scene,desk+1,manual,tail,'ending-phone')
    tail = graph.add('rev:06:outside-contact',type='document',title='창구의 외부 응답',rows=[
        '쇼가 관리 창구에서 외부의 사람에게 이름과 위치를 알렸다. 외부 사람이 수화기로 답했다.',
        '아직 철문을 손으로 열어 확인하지 않았다. 이 응답으로 문 상태를 대신 기록하지 않는다.'],
        set={'06:outside-response':True},source=ref(desk),next=tail)
    tail = graph.add('rev:06:desk',type='stage',scene={'space':'shelter_reception','leaveCourt':True},
                     presentation={'music':{'operation':'play','cue':'bgm_ending_choice'}},source=ref(desk),next=tail)
    transition = next(i for i,row in enumerate(scene.body) if row.startswith('미오가 왼쪽 행을'))
    tail = illustrated(scene,transition+1,desk,tail,'ending-control')
    tail = graph.add('rev:06:control-ended',type='stage',set={'06:control-ended':True},sfx='sfx_machine',
                     source=ref(transition),next=tail)
    menu = 'rev:06:control-choice'
    rejects = [
        ('support','지원까지 한 번에 끈다','nana','나나','아직 문이 열리는 걸 보지 못했어요. 그다음에 제가 대답할 일을 먼저 정하지 말아 주세요.'),
        ('verified','외부 통화와 문 개방을 이미 확인했다고 기록한다','sho','쇼','제 이름은 제가 실제로 수화기로 확인한 뒤에 쓰겠습니다.'),
    ]
    options = [{'id':'control','label':'현재 중앙 통제와 이번 관계 차폐만 종료한다','to':tail}]
    for key,label,actor,speaker,text in rejects:
        to = graph.add(menu+':'+key,type='say',actor=actor,speaker=speaker,text=text,source=ref(control),next=menu)
        options.append({'id':key,'label':label,'to':to})
    tail = graph.add(menu,type='menu',q='지금 운영 판에서 직접 종료할 항목은?',options=options,source=ref(control))
    return graph.lines(scene,control+1,transition,tail)


def chapter_six_closing(graph,scenes,tasks,records,dead,seats,tail):
    ending = chapter_six_ending(graph,scenes)
    checkpoints = {'ending':ending}
    comic = chapter_six_comic_stage()
    keys = ['v4:V5-6:'+key for key in ('past-confirmed','document-order','origin','reapprove')]
    if comic is not None:
        graph.nodes.pop(tail)
        scene = scenes['06-R00']
        ident = comic['id']
        tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':keys,'stage':comic,'queues':{}}
        tail = graph.add('rev:06:climax-comic',type='task',taskId=ident,trialDead=dead,seats=seats,
                         source=scene.source(scene.line),success=ending,next=ending)
        checkpoints['comic'] = tail
    scene = scenes['06-T02e']
    starts = [i for i,row in enumerate(scene.body) if row.startswith(('### A —','### B —','### C —'))]
    join = scene.body.index('### 합류')
    tail = graph.lines(scene,join+1,len(scene.body),tail)
    tail = graph.menu(scene,'어떤 자료를 먼저 남기고 싶어?',[
        (label,start+1,stop,'') for label,start,stop in zip([
            '원문과 내 해석을 따로 둔다','각자 가져갈 자료를 먼저 확인한다','외부에 전체 사본을 보내고 싶다고 말한다'
        ],starts,[*starts[1:],join],strict=True)],tail)
    callback = graph.lines(scene,0,starts[0],tail)
    tail = graph.add('rev:06:consent-callback',type='branch',
                     cases=[{'flag':'06-T02f:perjury','equals':True,'to':callback}],default=tail)
    scene = scenes['06-T02f']
    at = scene.body.index('#### 논스톱·우소다마 — 같은 말부터 약속해야 한다면')
    truth = scene.body.index('**일반 논파 후**')
    lie = scene.body.index('**우소다마 후**')
    join = scene.body.index('**합류**')
    tail = graph.lines(scene,join+1,len(scene.body),tail)
    honest = graph.lines(scene,truth+1,lie,tail)
    false = graph.lines(scene,lie+1,join,tail)
    ident = 'T6-LI-REV01'
    key = 'v4:V5-6:private-records'
    cards = [{'id':entry,'name':records[entry][2],'text':records[entry][3]} for entry in ('v4:V5-6:entry-count',key)]
    rows = []
    for i in range(at+1,truth):
        if match := STMT.match(scene.body[i]):
            number,speaker,claim,_ = match.groups()
            ref = scene.source(scene.line+i+1)
            if int(number)==4:
                lying,real = re.findall(r'\*\*([^*]+)\*\*',claim)
                row = debate_statement(ident,number,speaker,claim.replace('**'+lying+'**',lying),ref,'weak',key)
                row['lieWeak'] = {'word':lying,'start':row['text'].index(lying),'answer':key,'lie':True}
                assert row['weak']['word']==real
            else:
                row = debate_statement(ident,number,speaker,claim,ref)
            rows.append(row)
    ref = scene.source(scene.line+at+1)
    tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':[card['id'] for card in cards],
        'stage':{'id':ident,'kind':'nonstop','v4':True,'title':'같은 말부터 약속해야 한다면','lines':rows,'options':cards,
                 'authoredAmmo':[card['id'] for card in cards],'filterOwnedEvidence':True,
                 'wrongCards':{cards[0]['id']:'different-record'}},
        'transformation':{'sourceEvidenceId':key,'lieLabel':'다섯이 모든 원문 공개에 합의함','intentionalHold':True},
        'debate':{'id':ident,'kind':'nonstop','lines':rows,'bullets':cards},'queues':{'wrongVariants':[{
            'cause':'different-record','script':[{'id':ident+':wrong','type':'say','actor':'nana','speaker':'나나',
                'text':'지금 읽은 명단은 동의서가 아니에요. 원본을 누가 가졌는지와 제가 허락한 범위를 나눠 주세요.','source':ref}]}]}}
    tail = graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref,
        next=honest,success=honest,outcomes={'normal':{'judgment':'refute','to':honest},
            'perjury':{'judgment':'lie','to':false,'sets':{'06-T02f:perjury':True}}})
    tail = graph.lines(scene,0,at,tail)
    return tail,checkpoints


def chapter_six_operating_hearing(graph, scenes, tasks, records, dead, seats, tail):
    scene = scenes['06-T02']
    prefix = 'v4:V5-6:'

    def ref(at):
        return scene.source(scene.line+at+1)

    def say(ident, speaker, text, at):
        return {'id':ident,'type':'say','actor':SPEAKERS[speaker],'speaker':speaker,'text':text,'source':ref(at)}

    def task(ident, stage, at, keys, target, queues=None):
        tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':[prefix+key for key in keys],
            'stage':{'id':ident,'v4':True,**stage},'queues':queues or {}}
        return graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,source=ref(at),
                         success=target,next=target)

    reasoning = scene.body.index('#### 최종 추리 연결 — 일곱 줄의 제목')
    authored = [
        ('어떤 인원을 어느 표에 남길까?', ['광장의 16명이 전원 같은 경로로 들어왔다',
          '옛 행사 16 / 현재 요청 16 / 실제 입소 15와 생성 1','과거와 현재에 각각 생성된 사람만 센다'],1,
         ('유우','내가 광장에서 센 게 들어온 문까지 보여 주는 건 아니야.'),('쇼','요청 명단과 실제 입소 기록을 분리해 보십시오.')),
        ('이번 입소 전에 승인한 항목은?', ['현재의 관계 차폐','나나가 옛날에 지운 한 시간','광장 이후에 새로 일어난 일의 삭제'],0,
         ('나나','옛날 한 시간은 제가 손댔어요. 이번 기록은 다른 분에게 물어야 해요.'),('미오','여기서 서로 듣고 나서 한 일까지 지웠다는 행은 없어.')),
        ('서로 다른 세 기록을 어떻게 보관할까?', ['이름이 같으니 현재 행동도 모두 하나로 본다','지금 들은 대답으로 당시 몸의 행동을 입증한다',
          '당시 몸, 생성된 몸, 시제품에 남은 마음을 분리한다'],2,
         ('사츠키','그 이름부터 붙이지 말고 네 앞에서 움직인 사람이 누구였는지 봐.'),('래피','지금 말할 수 있다고 당시 제 손이 어디 있었는지는 모르겠어요.')),
        ('현재 운영의 책임을 확인할 기록은?', ['과거 통로에서 무슨 일을 겪었는지 하나만 고른다','기원을 알기 전 승인과 알게 된 뒤의 재승인',
          '문을 닫은 사람이 과거 통로에도 같은 행동을 했다고 적는다'],1,
         ('래피','그때 제가 겪은 것만으로 지금 어떤 줄을 눌렀는지 결정되지는 않아요.'),('미오','현재 문의 기록으로 과거에 본 손을 바꾸지 않을 거야.')),
        ('어떤 일을 참가자가 실제로 한 선택으로 남길까?', ['다른 사람이 적어 준 동기','차폐된 관계의 내용','광장에서 직접 듣고 내놓은 응답과 행동'],2,
         ('유우','내가 그랬을 것 같다는 건 네 말이야. 내가 뭐 했냐고 먼저 물어봐.'),('나나','그때는 서로를 아는 기억부터 없었어요. 지금 제가 답한 줄을 읽어 주세요.')),
        ('이번 종료에서 실제로 바뀔 항목은?', ['현재 중앙 통제와 이번 관계 차폐','수동 철문과 외부 연락, 의식 지원까지 자동 종료',
          '과거에 삭제된 기억도 한꺼번에 복원'],0,
         ('쇼','철문과 회선은 현장에서 별도로 확인해야 합니다. 지원도 별개입니다.'),('미오','이미 지운 기억은 지금 끄는 장치의 저장값이 아니야.')),
        ('각자 밖으로 가져갈 기록에 무엇을 남길까?', ['함께 읽었으니 모두 원문 공개에 동의했다',
          '확인 사실, 자기 해석, 당사자가 고른 공개 범위를 나눈다','지금 한 사람의 설명으로 모두의 기록을 대신한다'],1,
         ('유우','나도 읽었어. 내가 그걸 전부 보여 주겠다고 말한 적은 없어.'),('사츠키','내가 본 데는 내가 설명할 거야. 네 이름 밑에 전부 쓰지 마.')),
    ]
    ident = 'T6-RE-REV01'
    questions = []
    for i,(question,options,answer,*wrongs) in enumerate(authored):
        at = next(j for j in range(reasoning+1,len(scene.body)) if scene.body[j].startswith(f'{i+1}. '))
        ids = [f'option-{j}' for j in range(len(options))]
        questions.append({'q':question,'options':options,'optionIds':ids,'answer':options[answer],
            'success':[say(f'{ident}:{i}:correct','미오',options[answer]+'.',at)],
            'wrongVariants':[{'optionId':ids[j],'script':[say(f'{ident}:{i}:{j}',*response,at)]}
                for j,response in zip((j for j in range(len(options)) if j!=answer),wrongs,strict=True)]})
    tail = task(ident,{'kind':'reasoning','title':'일곱 줄의 제목','questions':questions},reasoning,
                ['entry-count','origin','reapprove','separate-connections','past-confirmed'],tail)
    arm = scene.body.index('#### 이론 무장 — 멈춘다는 말을 한 번만 쓰면')
    rule = next(i for i in range(arm,reasoning) if scene.body[i].startswith('마지막 네 조각은'))
    intro = [row for row in scene.body[arm:rule] if row.startswith(('상대는 래피다.','두 번째 파에 '))]
    claims = [line for row in intro for line in re.findall(r'“([^”]+)”',row)]
    assert len(claims)==6
    tail = graph.lines(scene,arm+1,rule,tail)
    fragments = [piece.strip() for piece in scene.body[rule].split('**')[1].split('/')]
    controller = [
        {'question':'당시의 안내값과 실제 처음 승인한 일의 관계는?','finalSubject':'',
         'final':['기본 안내값은','설치에 남은 항목이고','참가자 입소 전','직접 차폐를 승인했어']},
        {'question':'같은 상태가 다시 나타났을 때 실제로 확인된 것은?','finalSubject':'',
         'final':['기원을 확인한 뒤','다시 선택할 수 있었고','같은 상태로 운영하겠다고','한 번 더 눌렀어']},
        {'question':'같이 켜져 있던 두 연결은 어떻게 확인할까?','finalSubject':'',
         'final':['통제를 멈출 때','응답까지 끊지는 않아','문과 바깥 응답은','현장에서 따로 확인해']},
    ]
    streams = [claims[:3],['그 기록을 나중에 읽은 건 맞아요.','같은 상태가 떠 있었어요.','제가 다시 눌렀는지는 어느 줄을 보신 거예요?'],
        claims[3:],['문을 열어도 누가 밖에서 대답할지 모르잖아요.','창구에서 제가 답할 수 있는지는 따로 남아요.']]
    ident = 'T6-AA-REV01'
    tail = task(ident,{'kind':'armament','chapter':6,'title':'멈춘다는 말을 한 번만 쓰면',
        'opponent':'lappy','opponentDisplay':'래피','lines':[claim for wave in streams for claim in wave],
        'waves':[{'id':f'{ident}:wave:{i}','pairs':[{'claim':say(f'{ident}:{i}:{j}','래피',claim,arm)}
            for j,claim in enumerate(wave)]} for i,wave in enumerate(streams)],
        'phaseTranscripts':True,'controllerQuestions':controller,
        'question':'과거의 판정과 나누어 지금 실제로 할 일은?','finalSubject':'','final':fragments},arm,
        ['past-confirmed','first-approval','reapprove','separate-connections'],tail)
    for ident,title,ammo,boundary in reversed([
        ('T6-NS-REV10','그대로 둔 사람',['first-approval','origin','reapprove'],'#### 자료 선택 — 늦게 열어 준 이유'),
        ('T6-NS-REV12','문이 열린 뒤에야 생기는 확인',['operation-screen','origin','separate-connections'],'#### 이론 무장 — 멈춘다는 말을 한 번만 쓰면'),
    ]):
        at = scene.body.index('#### 논스톱 동의 — '+title)
        stop = scene.body.index(boundary)
        rows = []
        rule_start = stop
        for i in range(at+1,stop):
            if match := STMT.match(scene.body[i]):
                number,speaker,claim,role = match.groups()
                row = debate_statement(ident,number,speaker,claim,ref(i))
                if '동의점' in role:
                    word, = re.findall(r'\*\*([^*]+)\*\*',claim)
                    row.update(kind='agree',agree=prefix+ammo[-1],agreeTarget={'word':word,'glyphStart':row['text'].index(word)})
                rows.append(row)
            elif rows and scene.body[i].startswith(('06-I','현재 규칙 승인')):
                rule_start = i
                break
        assert sum(row['kind']=='agree' for row in rows)==1 and rule_start<stop
        cards = [{'id':prefix+key,'name':records[prefix+key][2],'text':records[prefix+key][3]} for key in ammo]
        tail = graph.lines(scene,rule_start+1,stop,tail)
        tail = task(ident,{'kind':'nonstop','title':title,'lines':rows,'options':cards,
            'authoredAmmo':[prefix+key for key in ammo],'filterOwnedEvidence':True,'wrongCards':{prefix+ammo[0]:'different-event'}},
            at,ammo,tail,{'wrongVariants':[{'cause':'different-event','script':[say(ident+':wrong','쇼',
                '지금 비교하는 것은 그때 별도로 확인해야 하는 행입니다. 같은 화면에 있다는 이유로 합치지 마십시오.',at)]}]})
        tasks[ident]['debate'] = {'id':ident,'kind':'nonstop','lines':rows,'bullets':cards}
        if ident=='T6-NS-REV12':
            tail,more = late_case_trial(graph,scenes,6,scene.id,'같은 칸에서 꺼야 하는가',
                '06-I02의 현재 운용 이력',4,records,[prefix+key for key in ('origin','first-approval','separate-connections')],
                '래피',tail,dead,seats,round_number=11)
            tasks.update(more)
            selection = scene.body.index('#### 자료 선택 — 늦게 열어 준 이유')
            tail = graph.lines(scene,selection+1,scene.body.index('#### 논스톱 — 같은 칸에서 꺼야 하는가'),tail)
    for number,title,prefix_line,keys,speaker in [
        (9,'다시 출력됐을 뿐이라면','06-I07a에서 가른',['document-order','first-approval','reapprove'],'쇼'),
        (8,'목소리가 돌아오면 기록도 돌아오나','시제품 인계의 전달 범위',['operation-screen','oath-rule','origin'],'래피'),
        (7,'안내서대로였다는 말','기본값 안내와 최초',['reapprove','operation-screen','first-approval'],'쇼'),
    ]:
        tail,more = late_case_trial(graph,scenes,6,scene.id,title,prefix_line,4,records,[prefix+key for key in keys],
                                   speaker,tail,dead,seats,round_number=number,include_intro=number==7)
        tasks.update(more)
        if number==8:
            follow = scene.body.index('#### 대면 — 누구의 목소리로 대답할 거야')
            origin = scene.body.index('#### 발굴 — 같은 이름 아래 들어간 물건')
            tail = graph.lines(scene,origin+1,scene.body.index('#### 논스톱 — 목소리가 돌아오면 기록도 돌아오나'),tail)
            assert origin<follow
            key = prefix+'origin'
            tail = graph.add('rev:06:prototype-origin',type='evidence',evidenceId=key,name=records[key][2],
                             text=records[key][3],source=ref(origin),next=tail)
            options = ['옛 시설의 출입 인원패','현재 내부 생성에 붙은 참가자 표지','시제품 인형의 인계표','출입 키 교체 기록']
            wrongs = [(0,'쇼','그 표에는 당시 입장한 사람이 있습니다. 이후 인계는 다른 표에 있습니다.'),
                      (1,'유우','그 표는 사람이 안에 나타났다는 거야. 인형을 받아 든 사람은 적혀 있지 않아.'),
                      (3,'래피','지금 문을 여는 열쇠를 바꾼 때와 제가 시작한 곳은 따로 있어요.')]
            ident = 'T6-QA-REV04'
            tail = task(ident,{'kind':'choice','question':'현재 안내자의 기원을 확인할 자료는?','options':options,'answer':2},
                origin,['entry-count','first-approval'],tail,
                {'wrongVariants':[{'optionIndex':i,'script':[say(f'{ident}:wrong:{i}',speaker,line,origin)]}
                                  for i,speaker,line in wrongs]})
            duel = scene.body.index('#### 반론 쇼다운 — 입구에서 셌던 사람')
            authored = re.findall(r'“([^”]+)”',scene.body[duel+2])
            assert len(authored)==6
            tail = graph.lines(scene,duel+1,origin,tail)
            keys = [prefix+key for key in ('document-order','side-door','entry-count')]
            cards = [{'id':key,'name':records[key][2],'text':records[key][3]} for key in keys]
            ident = 'T6-RS-REV02'
            tail = compile_showdown(graph,tasks,dead,seats,'rev:06:'+ident,ident,'입구에서 셌던 사람','래피',
                [authored[:3],authored[3:5]+[authored[5].strip('*')]],cards,keys[-1],ref(duel),
                ('유우','거기 있었던 건 맞아. 우리가 어느 길로 들어왔는지까지 그때 본 건 아니야.'),tail)
    return tail


def chapter_six_past_hearing(graph, scenes, tasks, records, dead, seats, sill_objects, motion_objects, tail):
    scene = scenes['06-T00']
    prefix = 'v4:V5-6:'
    board = MINE_ART+'corridor-sightline-board.svg'

    def source(at):
        return scene.source(scene.line+at+1)

    def reply(ident,speaker,text,at):
        return {'id':ident,'type':'say','actor':SPEAKERS[speaker],'speaker':speaker,'text':text,'source':source(at)}

    def task(ident,stage,at,keys,target,wrong=(),cause='optionIndex'):
        tasks[ident] = {'taskId':ident,'ready':True,'requiresEvidence':[prefix+key for key in keys],
            'stage':{'id':ident,'v4':True,**stage},'queues':{'wrongVariants':[
                {cause:index,'script':[reply(f'{ident}:wrong:{index}',speaker,text,at)]} for index,speaker,text in wrong]}}
        return graph.add('rev:06:'+ident,type='task',taskId=ident,trialDead=dead,seats=seats,
                         source=source(at),next=target,success=target)

    def mine(ident,title,question,at,objects,options,keys,target):
        return task(ident,{'kind':'mindmine','title':title,'question':question,'image':board,
            'answerRegionId':next(obj['regionId'] for obj,(_,speaker,_) in zip(objects,options,strict=True) if not speaker),
            'mineObjects':objects,'regions':[{'id':obj['regionId'],'label':label,'correct':not speaker,
                'wrongVariant':obj['regionId']} for obj,(label,speaker,_) in zip(objects,options,strict=True)]},at,keys,target,
            [(obj['regionId'],speaker,text) for obj,(_,speaker,text) in zip(objects,options,strict=True) if speaker],cause='cause')

    def record(name,at,target):
        _,_,label,text,_ = records[prefix+name]
        return graph.add('rev:06:past-record:'+name,type='evidence',evidenceId=prefix+name,name=label,text=text,source=source(at),next=target)

    vote = scene.body.index('#### 투표 — 먼저 확인한 과거의 직접 행위')
    tail = record('past-confirmed',vote,tail)
    tail = task('T6-VOTE-REV01',{'kind':'vote','title':'먼저 확인한 과거의 직접 행위','answer':'koto','candidates':seats,
        'question':'과거 통로에서 확인한 직접 행위자는?','deadCandidatesSelectable':True,
        'selectionRole':'historical-fact-intermediate-vote','finalVote':False,'voterCount':5,
        'majorityRequired':3,'voteCounts':{'koto':5}},vote,['continuous-view','witness-said','document-order'],tail,[
            (seats.index('nana'),'나나','제가 있던 곳을 확인해 주세요. 손을 뻗은 분과 그 손을 본 사람은 같은 자리에 없었어요.'),
            (seats.index('mio'),'미오','지금 기록하는 사람과 옛날 통로에서 손을 댄 사람을 다시 나눠 보자.')])
    tail = graph.lines(scene,vote+1,len(scene.body),tail)
    view = scene.body.index('#### 발굴 이매지네이션 — 바뀐 사람을 넣을 틈')
    after = next(i for i in range(view+1,vote) if SAY.match(scene.body[i]))
    tail = graph.lines(scene,after,vote,tail)
    tail = mine('T6-MM-REV02','바뀐 사람을 넣을 틈','얼굴과 달리 이어서 직접 본 범위는?',view,motion_objects,[
        ('영상이 끝난 곳','쇼','영상이 끝난 이후의 옆문은 영상으로 판단할 수 없습니다.'),
        ('얼굴이 가려지기 시작한 곳','나나','얼굴이 가려졌다고 몸까지 떠난 걸 봤다고 하지는 않았어요.'),
        ('같은 자리의 몸에서 손이 나간 곳','',''),
        ('등 뒤에서 힘을 느낀 기록','래피','그때는 힘을 느낀 곳만 알 수 있었어요.')],
        ['continuous-view','witness-said'],tail)
    duel = scene.body.index('#### 반론 쇼다운 — 말하는 사람이 얻게 되는 것')
    rule = next(i for i in range(duel,view) if scene.body[i].startswith('일반 파동에서'))
    tail = graph.lines(scene,rule+1,view,tail)
    keys = [prefix+key for key in ('signature','voice-window','witness-said')]
    cards = [{'id':key,'name':records[key][2],'text':records[key][3]} for key in keys]
    ident = 'T6-RS-REV01'
    tail = compile_showdown(graph,tasks,dead,seats,'rev:06:'+ident,ident,'말하는 사람이 얻게 되는 것','사츠키',[
        ['나나는 이제 자기 얘기 안 해도 되겠네.','래피도 오늘 일을 안 물어보면 편하겠지.','미오도 듣고 싶은 말이 있었잖아.'],
        ['너희 셋 다 그쪽이 편하니까, 실제로 그런 손을 본 사람도 없었다고 하면 돼.']],
        cards,keys[-1],source(rule),('사츠키','누구한테 편한 말인지 물었어. 실제로 본 위치랑 그 두 손을 같이 가져와.'),tail)
    tail = graph.lines(scene,duel+1,rule,tail)
    name = scene.body.index('#### 증언의 제약 해제와 인물 지목 — 그날 한 직접 행위')
    choose = next(i for i in range(name,duel) if scene.body[i].startswith('질문은 ‘그날 실제로'))
    tail = task('T6-QA-REV03',{'kind':'choice','question':'그날 두 손을 써서 직접 밀었던 사람은?',
        'options':['코토의 아버지','아카리의 아버지','코토','미오','래피'],'answer':2},choose,['witness-said','continuous-view'],tail,[
            (0,'쇼','수정한 문서와 실제로 몸을 민 행위를 같은 칸에 둘 수는 없습니다.'),
            (1,'사츠키','위험을 두고 승인한 사람은 뒤에서 물을 거야. 그 사람이 두 손을 내민 걸 봤어?'),
            (3,'미오','나는 지금 이 자료를 맞추고 있어. 그날 나나가 본 자세와 다시 대조하자.'),
            (4,'래피','지금의 운영과 그날 통로의 손은 따로 질문해 주세요.')])
    tail = record('witness-said',choose,tail)
    released = next(i for i in range(name,choose) if scene.body[i].startswith('**나나**　코토 씨가 그날'))
    tail = graph.lines(scene,released,choose,tail)
    tail = task('T6-QA-REV02',{'kind':'choice','question':'보호 페이지에 현재 상태를 쓴 뒤 어떤 효과를 겨눌까?',
        'options':['잊은 기억을 다시 만들어 낸다','나나의 현재 발언을 막는 오래된 맹세의 지속 효과','함께 썼던 다른 모든 맹세'],
        'answer':1},released,['oath-rule','continuous-view'],tail,[
            (0,'미오','지금 숨을 쉴 수 있다는 사실을 적었어. 지난 기억에 어떤 문장도 덧쓰지 않아.'),
            (2,'쇼','현재 숨을 막는 효과만 확인하십시오. 다른 조건은 여기 적힌 관찰과 충돌하지 않습니다.')])
    tail = graph.lines(scene,name+1,released,tail)
    anagram = scene.body.index('#### 섬광 애너그램 — 사본을 맡기며 남긴 말')
    answer,decoys,question = ANAGRAMS[scene.id]
    for number,title,rule,keys,speaker in [
        (6,'서명하고 고쳐 쓴 사람','정답은 원본 뒤에',['signature','safety-hold','document-edit'],'유우'),
        (5,'이름을 빼기 전에 써 놓은 것','06-I02의 동일 번호에',['signature','side-door','document-order'],'쇼'),
        (4,'얼굴이 가려지고 나서','06-I03b의 옆문 재현으로',['railing','side-door','continuous-view'],'쇼')]:
        tail,more = late_case_trial(graph,scenes,6,scene.id,title,rule,4,records,[prefix+key for key in keys],
                                   speaker,tail,dead,seats,round_number=number)
        tasks.update(more)
        if number==6:
            tail = task('T6-AN-REV01',{'kind':'anagram','title':'사본을 맡기며 남긴 말','chapter':6,
                'question':question,'answer':answer,'distractors':list(decoys)},anagram,['document-order'],tail)
        if number==5:
            compare = scene.body.index('#### 증거 지목 — 밖으로 나온 문장')
            keys = ['side-door','motion','document-order']
            cards = [{'id':prefix+key,'name':records[prefix+key][2],'text':records[prefix+key][3]} for key in keys]
            tail = task('T6-BU-REV01',{'kind':'bullet','question':'처음의 접수와 나중 인계의 본문이 다르다는 자료는?',
                'options':cards,'answer':prefix+'document-order'},compare,keys,tail,[
                    (0,'나나','접수대에 도착한 때와 문서에 남은 문장의 날짜는 달라요.'),
                    (1,'쇼','손의 동작으로 어느 판본이 접수됐는지는 결정할 수 없습니다.')])
            tail = graph.lines(scene,compare+1,scene.body.index('#### 논스톱 — 이름을 빼기 전에 써 놓은 것'),tail)
    sill = scene.body.index('#### 발굴 이매지네이션 — 그날의 가려진 경계')
    tail = record('continuous-view',sill,tail)
    return mine('T6-MM-REV01','그날의 가려진 경계','옛 통로에서 얼굴과 팔의 가림을 나누어 볼 구조는?',sill,sill_objects,[
        ('옛 개구부의 낮은 모서리','',''),
        ('지금 붙은 새 발판','유우','내가 지금 밟아 본 건 여기야. 네가 그때도 이 위에서 봤다고 말한 적은 없어.'),
        ('나중에 옮긴 접수대','사츠키','누가 늦게 온 건 저쪽에서 적었지. 손을 내민 그림하고 합치지 마.'),
        ('기존 시설의 표지판','미오','들어가는 방향은 맞아. 어디까지 가렸는지는 창 옆을 보자.')],['railing','motion'],tail)


def chapter_six_entry(scenes, sill_objects, motion_objects):
    graph = CampaignGraph()
    seats = [name for name in SPEAKERS.values() if name != 'lappy']
    dead = [name for name in seats if name not in {'mio', 'satsuki', 'nana', 'sho', 'yuu'}]
    records = {
        'v4:V5-6:signature': ('06-I02', 'operating_archive', '서명과 당시 보고서',
                               '서명한 진술은 동행과 팔에 닿은 일, 추락을 본 일을 남겼다. 첫 단편 음성의 화자는 이 서명으로 확인할 수 없다.', [0, 1.25, 2.1]),
        'v4:V5-6:side-door': ('06-I03', 'shelter_reception', '옆 출입구와 접수의 상대 순서',
                               '나나는 옆문에서 얼굴과 두 손의 움직임을 보았다. 이름이 확인된 전실 접수는 그 직접 관찰 이후의 별도 기록이다.', [0, 1.25, 2.1]),
        'v4:V5-6:voice-window': ('06-I06', 'lower_corridor', '첫 음성의 종료와 옆문 시야',
                                  '첫 단편의 두 목소리가 끝난 뒤, 옆 출입구에서 얼굴과 손을 본 별도 구간이 있다. 둘 사이의 빠진 시간을 같은 대화로 채울 수 없다.', [0, 1.25, 2.1]),
        'v4:V5-6:motion': ('06-I03b','shelter_reception','옆문에서 본 두 동작의 방향',
                          '얼굴이 보였을 때와 등을 돌린 뒤 손이 나간 때는 다르다. 앞서 잡던 팔을 놓았고, 몸이 이미 돈 뒤 손이 뒤쪽으로 나갔다. 그 뒤의 가림까지 채워 넣지는 않는다.', [1.35,1.25,1.85]),
        'v4:V5-6:railing': ('06-I03a','core_external_inspection','옛 사진과 교체 난간의 높이',
                            '옛 사진의 낮은 모서리를 현재 난간과 나란히 확인했다. 기둥 아래 교체 표찰과 새 발판 때문에 지금의 눈높이를 그대로 적용할 수 없다.', [-1.15,1.25,1.9]),
        'v4:V5-6:document-order': ('06-I03c','operating_archive','접수 원본에서 인계 요약으로',
                            '같은 번호라도 원본은 동행과 접촉을 인정한다. 나중에 인계된 요약에서는 혼자 갔다고 줄었다. 어느 판본을 먼저 받았는지와 원본의 진위를 구별한다.',[-1.2,1.24,-.9]),
        'v4:V5-6:document-edit': ('06-I02b','operating_archive','서명과 수정 승인·인계의 작성 칸',
                            '서명 당사자의 칸과 수정 접수·승인·인계의 작성자 칸이 별도로 남는다. 요약을 고치는 행위와 실제 통로에서 손을 댄 행위를 구분한다.',[1.25,1.24,-.9]),
        'v4:V5-6:safety-hold': ('06-I02a','operating_archive','위험 항목의 보류와 시설 개장',
                            '난간 점검에서 위험을 남겨 두고 보류 의견을 냈다. 뒤의 승인과 실제 개장은 별도다. 사고 뒤 본문을 바꾼 자료로 쓰지 않는다.',[1.3,1.24,1.3]),
        'v4:V5-6:oath-rule': ('06-I05b','shelter_inner','현재 호흡과 오래된 조건',
                            '오늘의 보호 페이지는 이미 사용했다. 같은 페이지의 남은 곳에 검증 가능한 현재 상태를 쓸 수 있다. 충돌하는 지속 효과를 겨눌 수 있어도 지워진 기억을 쓰는 기능은 아니다.',[.8,1.24,1.55]),
        'v4:V5-6:entry-count': ('06-I04','operating_archive','옛 접수·현재 요청·입소를 가른 수',
                            '옛 행사 접수 16명, 현재 초청 요청 16명, 현재 실제 입소 15명과 내부 생성 1명이다. 광장의 인원만으로 들어온 경로를 정하지 않는다.',[-.75,1.24,1.35]),
        'v4:V5-6:first-approval': ('06-I02','core_external_inspection','안내의 기본값과 실제 최초 승인',
                            '안내에는 초기값이 있다. 실제 입소 전 관계 차폐를 켜기 위해서는 별도 승인이 필요했고 승인 행이 남았다. 당시 운영자가 기원을 알고 있었다는 증거는 아니다.',[1.25,1.24,1.5]),
        'v4:V5-6:operation-screen': ('06-I07a','lower_corridor','반복 표시와 사용자의 선택 확인',
                            '같은 상태를 다시 전송한 행은 누구의 새 선택도 표시하지 않는다. 유지 버튼을 눌러 확인한 행은 다르다. 수사에서 화면을 읽어도 현재 상태는 바뀌지 않는다.',[1.3,1.24,1.55]),
        'v4:V5-6:reapprove': ('06-I07a','lower_corridor','기원을 읽고 나서 누른 유지',
                            '최초 승인과 이후 표시를 분리한다. 기원에 해당하는 자료가 열린 뒤 유지 응답이 다시 기록됐다. 화면의 반복 전송과 별개의 행이다.',[-1.15,1.24,-1.15]),
        'v4:V5-6:separate-connections': ('06-I07','lower_corridor','통행과 창구 응답의 분리',
                            '중앙 통행 연동과 관계 차폐, 응답 지원은 분리된다. 통제 종료는 실제 철문의 왕복 확인이나 외부 통화 성공을 자동 기록하지 않는다.',[.45,1.24,-1.55]),
        'v4:V5-6:private-records': ('06-I07f','shelter_reception','남은 원문과 공개의 범위',
                            '공용 원본과 개인 사본을 따로 확인했다. 함께 읽은 사람도 각자 무엇을 전할지 정한다. 전체 원문 공개에 합의한 기록은 없다.',[-1.35,1.24,-1.05]),
        'v4:V5-6:harm-separation': ('06-I06b','core_external_inspection','추락과 후속 시설 피해의 두 기록',
                            '첫 추락을 직접 일으킨 움직임과, 후속 비상 개방·피난·설비로 인한 피해는 다른 기록에 있다. 보류된 제한과 완충 항목을 두 번째 기록과 대조한다.',[.4,1.24,-1.6]),
        'v4:V5-6:emergency-open': ('06-I06b','shelter_reception','비상 개방 뒤 이어진 전실 접수',
                            '비상 개방과 뒤의 전실 접수는 확인했다. 실제 물리 조치와 여전히 남은 시설 피해를 같이 보므로 개방 한 줄을 전 구역 복구로 읽지 않는다.',[1.5,1.24,-.85]),
        'v4:V5-6:alarm-order': ('06-I06c','core_external_inspection','보류 항목과 경보 전환의 선후',
                            '위험 항목의 보류 의견이 작성되고 그 항목을 인수한 기록이 있다. 비상 상태는 그 뒤에 바뀌었다. 피해의 크기까지 미리 알았다는 말은 아니다.',[-.75,1.24,-1.6]),
        'v4:V5-6:inspection-order': ('06-I02c','operating_archive','일정 변경과 미해결 항목의 인계',
                            '일정은 당겨졌으나 같은 번호에 보류되었던 완충 항목을 마쳤다는 조치는 없다. 상태의 정상 표기는 나중에 붙었다. 날짜나 재확인 서명만으로 보류가 해결되지는 않는다.',[.3,1.24,-1.1]),
        'v4:V5-6:old-intake-scope': ('06-I06e','shelter_reception','집결·전실 접수·피해 구역',
                            '당시 전실에서 이름을 확인한 사람, 다른 통로에서 모인 사람, 별도 피해 기록은 범위가 다르다. 전실 기록의 빈칸은 통로에 없었다는 증명이 아니다.',[.9,1.24,-1.55]),
        'v4:V5-6:memory-scope': ('06-I05','shelter_inner','당시 사라진 기억과 현재 보호의 시험',
                            '나나는 먼저 모인 다른 13명에게 개입했다. 스스로와 늦게 온 사람을 같은 행에 두지 않는다. 오늘 보호 페이지로 한 그림자 효과를 끝낸 뒤 새 분리는 다시 작동했다. 사라진 기억 전체는 돌아오지 않았다.',[-1.1,1.24,-1.4]),
        'v4:V5-6:silence-boundaries': ('06-I04b','operating_archive','두 당사자의 금지 문구와 합의 종료',
                            '레이와 코토의 사본은 특정 사실을 먼저 전하지 않는 조건이다. 다시 합의해야 끝나며 날짜 자동 종료는 없다. 몸을 생성하라는 명령이나 다른 판단을 대신하는 문구는 없다.',[-1.4,1.24,.3]),
        'v4:V5-6:live-response': ('06-I07c','shelter_reception','이전 알림과 지금 새로 한 답',
                            '자동 반복 신호, 당시에 기록된 확인, 지금 질문을 듣고 래피가 답한 말은 서로 다르다. 질문한 사람과 들은 사람이 현재의 발화를 확인한다.',[-1.6,1.24,.85]),
        'v4:V5-6:independent-records': ('06-I03f','operating_archive','보관 사본과 서로 다른 확인자',
                            '실물 보관 사본과 공개 인계 범위를 대조했다. 점검판에서 같은 시각에 서로 다른 자리를 확인할 사람을 지정했지만, 아직 바깥 응답이나 문 개방의 실증은 없다.',[1.5,1.24,.3]),
    }
    hearing_records = {**records,
        'v4:V5-6:continuous-view': ('06-T00','','얼굴과 몸이 가려진 경계',
            '옆문의 낮은 개구부에서 얼굴은 먼저 가려졌지만 같은 자리에 남은 몸의 팔이 뒤로 나가는 범위는 보였다. 가림 뒤의 전체 모습을 관찰한 것은 아니다.',[]),
        'v4:V5-6:witness-said': ('06-T00','','나나가 말한 두 손과 자신의 자리',
            '제약이 끝난 뒤 나나가 옆문에서 본 코토의 두 손을 직접 증언했다. 진술은 시야와 힘이 닿은 위치를 대조하며, 기억을 복원하거나 진술을 자동 검증하지 않는다.',[]),
        'v4:V5-6:past-confirmed': ('06-T00','','과거의 직접 행위 확인',
            '다섯 사람의 중간 투표로 과거 통로의 직접 행위를 확인했다. 이 집계는 옛 문서 수정이나 현재 운영에 대한 최종 판정과 분리한다.',[]),
        'v4:V5-6:origin': ('06-T02','','시제품 인계표의 전달 범위',
            '시제품 인계표는 인형에 남은 마음과 나중 운용을 연결한다. 당시의 몸이나 현재 생성된 참가자의 행동으로 바꿔 읽지 않는다. 지워진 기억 전체는 인계되지 않았다.',[]),
    }
    end = graph.add('rev:06:excerpt-end', type='end')
    case = scenes['06-T00']
    tasks = {}
    closing, final_checkpoints = chapter_six_closing(graph,scenes,tasks,hearing_records,dead,seats,end)
    post_operating = chapter_six_post_operating(graph,scenes,tasks,hearing_records,dead,seats,closing)
    operating = chapter_six_operating_hearing(graph,scenes,tasks,hearing_records,dead,seats,post_operating)
    personal = chapter_six_personal_hearing(graph,scenes,tasks,hearing_records,dead,seats,operating)
    transition = chapter_six_transition_hearing(graph,scenes,tasks,hearing_records,dead,seats,personal)
    past = chapter_six_past_hearing(graph,scenes,tasks,hearing_records,dead,seats,sill_objects,motion_objects,transition)
    question_at = case.body.index('#### 정답 선택 — 그 사람이 늦었다는 건 어디에 늦었나')
    movement_at = case.body.index('#### 논스톱 — 떨어질 때의 움직임')
    question_id = 'T6-QA-REV01'
    question_source = case.source(case.line+question_at+1)
    tail, more = late_case_trial(graph,scenes,6,'06-T00','오늘 있는 난간으로 어제를 재면',
                                  '06-I01의 옛 공원 사진',4,records,
                                  ['v4:V5-6:side-door','v4:V5-6:motion','v4:V5-6:railing'],'쇼',past,dead,seats,
                                  round_number=3)
    tasks.update(more)
    tail, movement = late_case_trial(graph,scenes,6,'06-T00','떨어질 때의 움직임',
                                     '정답 당시 단편과',4,records,
                                     ['v4:V5-6:voice-window','v4:V5-6:signature','v4:V5-6:motion'],'미오',tail,dead,seats,
                                     round_number=2)
    tasks.update(movement)
    tail = graph.lines(case,question_at+1,movement_at,tail)
    options = [(i,BULLET.match(row).groups()) for i,row in enumerate(case.body[question_at+1:movement_at],question_at+1) if BULLET.match(row)]
    assert len(options)==3
    tasks[question_id] = {'taskId':question_id,'ready':True,'requiresEvidence':['v4:V5-6:side-door'],
        'stage':{'id':question_id,'kind':'choice','v4':True,'answer':1,
                 'question':'그 사람이 늦었다는 건 어디에 늦었다는 뜻일까?',
                 'options':[data[0] for _,data in options]},
        'queues':{'wrongVariants':[{'optionIndex':index,'script':[{'id':f'{question_id}:{index}','type':'say',
                  'actor':SPEAKERS[speaker],'speaker':speaker,'text':re.findall(r'“([^”]+)”',options[index][1][1])[0],
                  'source':case.source(case.line+options[index][0]+1)}]} for index,speaker in ((0,'나나'),(2,'쇼'))]}}
    tail = graph.add('rev:06:late-registration-choice',type='task',taskId=question_id,trialDead=dead,seats=seats,
                     source=question_source,success=tail,next=tail)
    tail, first_task = late_case_trial(graph, scenes, 6, '06-T00', '소리가 난 쪽을 알았다는 말',
                                  '06-I06의 첫 음성 단편의 종료', 4, records,
                                  ['v4:V5-6:signature', 'v4:V5-6:side-door', 'v4:V5-6:voice-window'], '쇼', tail, dead, seats)
    tasks.update(first_task)
    tail = chapter_six_document_hearing(graph,scenes,tasks,dead,seats,tail)
    tail = chapter_six_opening_hearing(graph,scenes,tasks,records,dead,seats,tail)
    tail = graph.add('rev:06:court-entry', type='stage', enterCourt=True, next=tail)
    order = scenes['06-I08']
    alternatives = [i for i,row in enumerate(order.body) if row.startswith(('### A. ','### B. ','### C. '))]
    join = order.body.index('### 합류')
    tail = graph.lines(order,join+1,len(order.body),tail)
    rest = {
        'A': (('쇼','접수된 진술과 공개 요약을 둘 다 가져갑니다. 안 나온 문장을 옛 진술에 넣지는 않겠습니다.'),
              ('사츠키','통제하고 지원은 따로 둘 거야. 실제로 문 건너 본 사람은 아직 없어.')),
        'B': (('나나','제가 본 건 몸이 돌고 난 다음이에요. 앞에서 팔을 잡았을 때는 제가 못 봤어요.'),
              ('쇼','통행 점검표와 응답 지원 점검표를 따로 가져가겠습니다.')),
        'C': (('나나','제가 본 손의 움직임은 제가 가져갈게요. 처음에 팔을 잡으신 때는 못 봤고요.'),
              ('미오','원본을 받은 행하고 보고서에서 빠진 행도 챙길게. 처음부터 혼자였다고 쓴 원본은 아니야.')),
    }
    cases = []
    for key, replies in rest.items():
        source = next(i for i,row in enumerate(order.body) if row.startswith(f'- **{key} 뒤.**'))
        target = tail
        for index,(speaker,line) in reversed(list(enumerate(replies))):
            target = graph.add(f'rev:06:unselected-records:{key}:{index}',type='say',actor=SPEAKERS[speaker],
                               speaker=speaker,text=line,source=order.source(order.line+source+1),next=target)
        cases.append({'flag':order.id,'equals':key,'to':target})
    tail = graph.add('rev:06:unselected-records',type='branch',cases=cases,default=tail)
    tail = graph.menu(order,'어느 기록부터 증언대에 놓을까?',[
        (order.body[at][7:],at+1,stop,'') for at,stop in zip(alternatives,[*alternatives[1:],join],strict=True)],tail)
    tail = graph.lines(order,0,alternatives[0],tail)
    def compare_documents(scene, target):
        at = scene.body.index('#### 수사 대조 — 표지, 본문, 요약을 따로 펼친다')
        target = graph.lines(scene,at+1,len(scene.body),target)
        ref = scene.source(scene.line+at+1)
        menu = 'rev:06:document-comparison'
        entries = [
            ('당시 접수 목록','같은 번호가 붙은 원본의 접수 행과 나중 요약의 인계 행을 따로 확인했다.'),
            ('서명 진술 원본','동행, 팔을 떼었다는 진술, 추락을 보았다는 진술이 모두 있다. 적혀 있다는 사실만 확인했다.'),
            ('공개 사고 요약','같은 번호에 혼자 이동했다는 문장만 남았다. 전달 이후 누가 읽었는지는 이 줄로 확인할 수 없다.'),
        ]
        options = []
        for i,(label,text) in enumerate(entries):
            flag = menu+':'+str(i)
            finished = graph.add(flag+':read',type='say',actor='mio',speaker='미오',mono=True,
                text=text,source=ref,set={flag:True},next=menu)
            doc = graph.add(flag+':document',type='document',title=label,rows=[text],source=ref,next=finished)
            options.append({'id':str(i),'label':label,'requires':{flag:False},'to':doc})
        options.append({'id':'finish','label':'세 문서의 열을 분리해 남긴다','to':target,
                        'requires':{menu+':'+str(i):True for i in range(len(entries))}})
        target = graph.add(menu,type='menu',q='어느 자료를 펼칠까?',options=options,source=ref)
        return graph.lines(scene,0,at,target)

    def initial_approval(scene):
        return next(i for i,row in enumerate(scene.body) if row.startswith('유우가 현재 입소 승인 목록을'))

    def approve_again(scene):
        return next(i for i,row in enumerate(scene.body) if row.startswith('**나나**　제가 이 화면을 읽었다는'))

    def emergency(scene):
        return next(i for i,row in enumerate(scene.body) if row.startswith('비상 개방 행은 저녁 경보 뒤'))

    def inspect_protection(scene,target):
        at = scene.body.index('### 같은 빛에서 세 번 움직이는 그림자')
        write = next(i for i,row in enumerate(scene.body) if row.startswith('미오는 오늘 활성화한 보호 페이지의'))
        first = next(i for i in range(write,len(scene.body)) if scene.body[i].startswith('**미오**　네가 멈춘 거야?'))
        second = next(i for i in range(first,len(scene.body)) if scene.body[i].startswith('세 번째 분리에서는'))
        ref = scene.source(scene.line+write+1)
        tail = checked_investigation(graph,scene,second+1,len(scene.body),target)
        tail = graph.add('rev:06:shadow-third-observation',type='say',actor='mio',speaker='미오',mono=True,
            text='새 글을 쓰지 않은 세 번째 시도에서는 그림자가 다시 발 앞으로 움직였다. 사츠키가 스스로 거뒀다.',
            source=scene.source(scene.line+second+1),next=tail)
        tail = graph.lines(scene,first,second,tail)
        tail = graph.add('rev:06:shadow-second-observation',type='say',actor='mio',speaker='미오',mono=True,
            text='사츠키가 두 번째 분리를 시도했다. 그림자는 한 번 어긋나다 발의 윤곽으로 돌아왔다. 빛과 발의 위치는 같았다.',
            source=ref,next=tail)
        correct = graph.add('rev:06:shadow-current-fact',type='document',title='현재 상태를 기록한 보호 페이지',rows=[
            '사츠키의 그림자는 그녀의 발에 붙어 있다.',
            '이미 활성화한 오늘의 페이지에 적었다. 충돌하는 그림자 분리의 한 효과만 지목한다.'],source=ref,next=tail)
        menu = 'rev:06:shadow-fact-choice'
        options = [{'id':'current','label':'그림자가 지금 발에 붙어 있다는 현재 상태를 적는다','to':correct}]
        for key,label,actor,speaker,text in [
            ('future','그림자가 다시는 발에서 떨어지지 않는다고 쓴다','satsuki','사츠키','내가 다음에 하려는 일을 현재 사실처럼 쓰지 마.'),
            ('body','사츠키가 몸을 움직일 수 없다고 쓴다','sho','쇼','현재 발을 움직일 수 있습니다. 몸의 구속과 이 효과는 다릅니다.'),
        ]:
            answer = graph.add(menu+':'+key,type='say',actor=actor,speaker=speaker,text=text,source=ref,next=menu)
            options.append({'id':key,'label':label,'to':answer})
        tail = graph.add(menu,type='menu',q='실제로 눈앞에서 확인한 문장은?',options=options,source=ref)
        tail = graph.lines(scene,at+1,write,tail)
        tail = graph.add('rev:06:shadow-first-observation',type='say',actor='mio',speaker='미오',mono=True,
            text='기록하기 전 사츠키가 발의 그림자를 떼어 보였다. 한 번 움직인 뒤 직접 거둬 제자리로 돌려놨다.',
            source=scene.source(scene.line+at+1),next=tail)
        return graph.lines(scene,0,at,tail)

    def inspect_silence(scene,target):
        at = next(i for i,row in enumerate(scene.body) if row.startswith('플레이어가 **레이의 조건'))
        menu = 'rev:06:silence-clauses'
        rows = []
        for i in range(at+1,len(scene.body)):
            match = re.fullmatch(r'\| (레이의 조건|코토의 조건|해제 문장) \| (.+) \| (.+) \|',scene.body[i])
            if match:
                label,fact,_ = match.groups()
                rows.append((i,label,fact))
        assert len(rows)==3
        options = []
        for index,(line,label,fact) in enumerate(rows):
            flag = f'{menu}:{index}'
            ref = scene.source(scene.line+line+1)
            back = graph.add(flag+':read',type='stage',set={flag:True},next=menu)
            read = graph.add(flag+':document',type='document',title=label,rows=[fact],source=ref,next=back)
            options.append({'id':str(index),'label':label,'requires':{flag:False},'to':read})
        options.append({'id':'finish','label':'두 조건과 합의 종료를 별도로 기록한다','to':target,
                        'requires':{f'{menu}:{index}':True for index in range(3)}})
        entry = graph.add(menu,type='menu',q='어느 조항을 직접 읽을까?',options=options,source=scene.source(scene.line+at+1))
        return graph.lines(scene,0,at,entry)

    def inspect_independent(scene,target):
        comparison = scenes['06-I07g']
        target = graph.lines(comparison,0,len(comparison.body),target)
        ref = comparison.source(comparison.line)
        menu = 'rev:06:separate-observers'
        checks = [
            ('실물 보관과 공개 인계','보관 사본을 가진 손과 공개 인계를 확인한 사람은 따로다. 현재 화면을 띄운 사람을 둘 다 본 증인으로 적지 않는다.'),
            ('창구에서 직접 받을 응답','창구의 확인자는 질문과 직접 온 대답을 읽는다. 아직 외부 사람이 받은 통화는 없다.'),
            ('철문에서 직접 볼 움직임','문을 보는 사람은 실제로 열고 왕복했는지를 확인한다. 창구의 응답 표시로 문 열림을 대신하지 않는다.'),
        ]
        options = []
        for index,(label,text) in enumerate(checks):
            flag = f'{menu}:{index}'
            record = graph.add(flag+':record',type='stage',set={flag:True},next=menu)
            record = graph.add(flag+':read',type='document',title=label,rows=[text],source=ref,next=record)
            options.append({'id':str(index),'label':label,'requires':{flag:False},'to':record})
        options.append({'id':'finish','label':'누가 어느 자리에서 확인할지 따로 둔다','to':target,
                        'requires':{f'{menu}:{index}':True for index in range(3)}})
        target = graph.add(menu,type='menu',q='어느 위치의 확인 범위를 볼까?',options=options,source=ref)
        return graph.lines(scene,0,len(scene.body),target)

    tail = late_case_investigation(graph, scenes, 6, 'lower_corridor', records, tail,
        routes={'v4:V5-6:document-order':compare_documents,
                'v4:V5-6:signature':lambda scene,target:checked_investigation(graph,scene,0,initial_approval(scene),target),
                'v4:V5-6:first-approval':lambda scene,target:graph.lines(scene,initial_approval(scene),len(scene.body),target),
                'v4:V5-6:operation-screen':lambda scene,target:checked_investigation(graph,scene,0,approve_again(scene),target),
                'v4:V5-6:reapprove':lambda scene,target:graph.lines(scene,approve_again(scene),len(scene.body),target),
                'v4:V5-6:harm-separation':lambda scene,target:graph.lines(scene,0,emergency(scene),target),
                'v4:V5-6:emergency-open':lambda scene,target:graph.lines(scene,emergency(scene),len(scene.body),target),
                'v4:V5-6:memory-scope':inspect_protection,'v4:V5-6:silence-boundaries':inspect_silence,
                'v4:V5-6:independent-records':inspect_independent},
        supplemental={'v4:V5-6:signature':['06-I01a'],'v4:V5-6:side-door':['06-I03d','06-I03e'],
            'v4:V5-6:entry-count':['06-I04a','06-I04c','06-I04d'],'v4:V5-6:memory-scope':['06-I05a'],
            'v4:V5-6:voice-window':['06-I06a'],'v4:V5-6:alarm-order':['06-I06d'],
            'v4:V5-6:separate-connections':['06-I07b'],'v4:V5-6:live-response':['06-I07d','06-I07e']},
        prerequisites={'v4:V5-6:document-order':['v4:V5-6:signature'],
                       'v4:V5-6:document-edit':['v4:V5-6:document-order'],
                       'v4:V5-6:operation-screen':['v4:V5-6:first-approval'],
                       'v4:V5-6:reapprove':['v4:V5-6:operation-screen','v4:V5-6:first-approval'],
                       'v4:V5-6:voice-window':['v4:V5-6:document-order','v4:V5-6:motion'],
                       'v4:V5-6:harm-separation':['v4:V5-6:safety-hold','v4:V5-6:voice-window'],
                       'v4:V5-6:emergency-open':['v4:V5-6:harm-separation'],
                       'v4:V5-6:alarm-order':['v4:V5-6:safety-hold','v4:V5-6:emergency-open'],
                       'v4:V5-6:inspection-order':['v4:V5-6:safety-hold','v4:V5-6:document-edit'],
                       'v4:V5-6:old-intake-scope':['v4:V5-6:emergency-open','v4:V5-6:side-door'],
                       'v4:V5-6:oath-rule':['v4:V5-6:memory-scope'],
                       'v4:V5-6:motion':['v4:V5-6:side-door']})
    tail=examine_document_bundles(graph,scenes['06-I01'],tail)
    for scene_id, space in reversed((
        ('06-D01','lower_corridor'),('06-D01b','lower_corridor'),('06-D01a','lower_stairway'),
        ('06-D01c','core_external_inspection'),('06-D01d','core_external_inspection'),('06-D01e','lower_corridor'),
        ('06-D02','core_external_inspection'),('06-D02a','shelter_reception'),('06-D02b','shelter_reception'),
        ('06-D02c','shelter_inner'),('06-D03','shelter_inner'),('06-D03c','lower_corridor'),
        ('06-D03a','operating_archive'),('06-D03b','operating_archive'),('06-D03e','lower_corridor'),
        ('06-D03d','lower_corridor'),('06-D03f','shelter_inner'),('06-D03g','lower_stairway'),
    )):
        tail = daily_scene_route(graph,scenes[scene_id],space,tail)
    checkpoints = {}
    for name,target in [('opening-hearing','rev:06:T6-SP-REV01'),('past-hearing',past),('transition-hearing',transition),
                        ('personal-hearing',personal),('operating-hearing',operating),('post-operating-hearing',post_operating),
                        ('closing-hearing',closing),*final_checkpoints.items()]:
        if name=='ending':
            checkpoints[name] = {'entry':target,'evidence':[]}
            continue
        evidence = records if name=='past-hearing' else hearing_records
        cards = [{'id':key,'name':value[2],'text':value[3]} for key,value in evidence.items()
                 if not (name=='operating-hearing' and key=='v4:V5-6:origin')]
        target = graph.add(f'rev:06:{name}:court-entry',type='stage',enterCourt=True,next=target)
        for card in reversed(cards):
            target = graph.add(f'rev:06:{name}:seed:'+card['id'],type='evidence',evidenceId=card['id'],
                               name=card['name'],text=card['text'],next=target)
        checkpoints[name] = {'entry':target,'evidence':cards}
    return ({'schemaVersion': 1, 'contentVersion': 'v4', 'campaignRevision': 'rewrite-v5', 'chapter': '6',
             'entry': tail, 'nodes': graph.nodes, 'trialRoster': {'dead': dead, 'seats': seats},
             'qaCheckpoints':checkpoints}, tasks)


def validate_roster_progression(chapters,tasks):
    for number in range(1,6):
        current,following = chapters[str(number)],chapters[str(number+1)]
        gone = set(current['trialRoster']['dead'])
        for node in current['nodes'].values():
            if node['type']=='task' and tasks[node['taskId']]['stage']['kind']=='vote':
                gone.add(tasks[node['taskId']]['stage']['answer'])
        missing = gone-set(following['trialRoster']['dead'])
        if missing:
            raise ValueError(f'Chapter {number+1} revives a prior casualty or verdict target: {sorted(missing)}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--projectile-labels', type=Path)
    args = parser.parse_args()
    scenes = manuscript()
    if args.inventory:
        inventory = trial_inventory(scenes)
        args.inventory.parent.mkdir(parents=True, exist_ok=True)
        args.inventory.write_text(json.dumps({'scenes': len(scenes), 'chapterOrder': campaign_order(scenes),
                                              'trialCandidates': inventory}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    door_objects, mine_assets = door_comparison()
    paper_objects, paper_assets = paper_comparison()
    mine_assets.update(paper_assets)
    mine_assets.update(theatre_section())
    mine_assets.update(inspection_latch_section())
    visibility_objects,end_objects,inspection_assets=inspection_mines()
    mine_assets.update(inspection_assets)
    ring_objects, ring_assets = theatre_ring()
    mine_assets.update(ring_assets)
    pedestal_objects, pedestal_assets = theatre_pedestal()
    mine_assets.update(pedestal_assets)
    mirror_objects, mirror_assets = mirror_comparison()
    mine_assets.update(mirror_assets)
    knife_objects, knife_assets = mirror_knife_sequence()
    mine_assets.update(knife_assets)
    archive_objects, archive_assets = archive_slot()
    mine_assets.update(archive_assets)
    package_objects, package_assets = archive_package_comparison()
    mine_assets.update(package_assets)
    sill_objects, motion_objects, corridor_assets = corridor_sightlines()
    mine_assets.update(corridor_assets)
    trial, tasks = reviewed_trial(scenes, door_objects, paper_objects)
    second, more_tasks = chapter_two_entry(scenes, ring_objects, pedestal_objects)
    tasks.update(more_tasks)
    third, more_tasks = chapter_three_investigations(scenes, mirror_objects, knife_objects)
    tasks.update(more_tasks)
    fourth, more_tasks = chapter_four_entry(scenes,visibility_objects,end_objects)
    tasks.update(more_tasks)
    fifth, more_tasks = chapter_five_entry(scenes, archive_objects, package_objects)
    tasks.update(more_tasks)
    sixth, more_tasks = chapter_six_entry(scenes,sill_objects,motion_objects)
    tasks.update(more_tasks)
    apply_authored_vpoints(scenes,tasks)
    chapters = {'P': CampaignGraph().compile_prologue(scenes), '1': trial, '2': second, '3': third,
                '4': fourth, '5': fifth, '6': sixth}
    apply_trial_bridges(chapters, tasks)
    apply_dialogue_direction(chapters, tasks, scenes)
    free_entries = {
        '1': ('rev:01-F02:visit', 'hotel_lobby', {'meet': ('sora', [1.35, 0, 2.2])}),
        '2': ('rev:02:free-after-breakfast', 'dining_room',
              {'02-F02': ('ai', [-1, 0, .9]), '02-F07': ('akari', [-1.45, 0, 2])}),
        '3': ('rev:03:free-before-screening', 'performance_stage',
              {'03-F02': ('ken', [1.4, 0, 3.3]), '03-F03': ('haruka', [1.7, 0, 6.5])}),
        '4': ('rev:04:free-before-inspection', 'hotel_rest_lounge', {'chair': ('yuu', [-2.3, 0, 1.6])}),
        '5': ('rev:05:free-before-duties', 'hotel_rest_lounge', {'aid': ('sho', [2.2, 0, 1.5])}),
    }
    for chapter, graph in chapters.items():
        nodes = graph['nodes']
        nodes[graph['entry']]['chapterEntryType'] = 0
        nodes[graph['entry']]['timeOfDay'] = 'day'
        for node in nodes.values():
            location = node.get('source', {}).get('location')
            if node['type'] == 'stage' and node.get('scene') and location in SCENE_PHASES:
                node['timeOfDay'] = SCENE_PHASES[location]
        if chapter == 'P':
            continue
        if chapter in ('1', '2', '3', '4', '5'):
            graph['resultTaskId'] = f'T{chapter}-VOTE-REV01'
        for node in nodes.values():
            if node['type'] == 'end' and (node.get('chapterComplete') or node.get('campaignNarrativeEnd')):
                node['xpReward'] = {'kind': 'Script', 'id': 'chapter-completion:' + chapter}
                if chapter == '6':
                    node['trialResultAtEnd'] = True
        if chapter in free_entries:
            ident, origin, actors = free_entries[chapter]
            menu = nodes[ident]
            menu.update(chapterEntryType=1, selectionRole='freetime', explorationStart=origin)
            for option in menu['options']:
                if option['id'] == 'skip':
                    continue
                room = nodes[option['to']]['scene']['space']
                actor, position = actors[option['id']]
                option['encounter'] = {'actor': actor, 'space': room, 'position': position}
        investigation = 'first-investigation' if chapter == '3' else 'investigate'
        nodes[f'rev:0{chapter}:{investigation}']['chapterEntryType'] = 2
        nodes[f'rev:0{chapter}:court-entry']['chapterEntryType'] = 3
    validate_roster_progression(chapters,tasks)
    for chapter, graph in chapters.items():
        nodes = graph['nodes']
        visited = set()
        pending = [graph['entry']]
        pending.extend(point['entry'] for point in graph.get('qaCheckpoints', {}).values())
        while pending:
            ident = pending.pop()
            if ident in visited:
                continue
            visited.add(ident)
            node = nodes[ident]
            if node['type'] == 'task':
                task = tasks.get(node['taskId'])
                if not task:
                    raise ValueError(f'Missing native task: {node["taskId"]}')
                stage = task['stage']
                if stage['kind'] not in {'nonstop', 'panic', 'choice', 'bullet', 'person', 'spot', 'mindmine', 'anagram', 'showdown',
                                        'reasoning', 'scrum', 'armament', 'climax', 'vote'}:
                    raise ValueError(f'Unsupported revised native stage: {stage["kind"]}')
                if stage['kind'] == 'choice' and not 0 <= stage['answer'] < len(stage['options']):
                    raise ValueError(f'Choice answer is outside its options: {node["taskId"]}')
                if stage['kind'] == 'bullet':
                    options = stage.get('options', [])
                    if len(options) < 2 or stage['answer'] not in {option['id'] for option in options}:
                        raise ValueError(f'Evidence picker lacks visible choices or its answer: {node["taskId"]}')
                if stage['kind'] == 'nonstop':
                    ammo = stage.get('authoredAmmo')
                    if not ammo or not set(ammo) <= {option['id'] for option in stage['options']}:
                        raise ValueError(f'Revised Nonstop lacks usable authored ammunition: {node["taskId"]}')
                if stage['kind'] in {'nonstop', 'panic'}:
                    options = {option['id'] for option in stage['options']}
                    for row in task['debate']['lines']:
                        if stage['kind'] == 'panic' and row['kind'] != 'noise' and len(row['text']) > 48:
                            raise ValueError(f'Panic speech exceeds its visible 48 glyphs: {row["id"]}')
                        if row['kind'] == 'weak':
                            answer = row['weak']['answer']
                        elif row['kind'] == 'agree':
                            answer = row.get('agree')
                        else:
                            continue
                        if answer not in options:
                            raise ValueError(f'Authored statement has no usable answer: {row["id"]}')
            pending.extend(node[key] for key in ('next', 'success', 'default') if key in node)
            pending.extend(option['to'] for option in node.get('options', []))
            pending.extend(spot['entry'] for spot in node.get('spots', []))
            pending.extend(case['to'] for case in node.get('cases', []))
            pending.extend(outcome['to'] for outcome in node.get('outcomes', {}).values())
        if visited != set(nodes):
            raise ValueError(f'Chapter {chapter} has unrouted nodes: {sorted(set(nodes) - visited)}')
    if args.projectile_labels:
        labels = sorted({option['name'] for task in tasks.values() if task['stage']['kind'] in ('nonstop', 'panic', 'lie')
                         for option in task['stage']['options']}
                        | {task['transformation']['lieLabel'] for task in tasks.values() if task.get('transformation')})
        args.projectile_labels.parent.mkdir(parents=True, exist_ok=True)
        args.projectile_labels.write_text(json.dumps(labels, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    encounters = []
    episodes = Counter()
    for chapter, actors in FREE_ACTORS.items():
        for index, actor in enumerate(actors, 1):
            ident = f'{chapter:02}-F{index:02}'
            scene = scenes[ident]
            assert f'rev:{ident}:complete' in chapters[str(chapter)]['nodes'], ident
            episodes[actor] += 1
            encounters.append({'actor': actor, 'episode': episodes[actor],
                               'title': scene.title, 'flag': f'rev:encounter:{ident}',
                               'source': scene.source(scene.line)})
    assert {item['source']['location'] for item in encounters} == {ident for ident in scenes if '-F' in ident}
    print(json.dumps({'chapters': chapters, 'tasks': tasks, 'mineAssets': mine_assets,
                      'encounters': encounters}, ensure_ascii=False))


if __name__ == '__main__':
    main()
