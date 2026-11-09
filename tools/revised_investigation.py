"""Supplemental inspection interactions from the V5 manuscript."""

import re

from build_v4_story import SPEAKERS


CHOICE = re.compile(r'^- \*\*([^*]+)\*\*')
SPEECH = re.compile(r'^\s*\*\*[^*]+\*\*　')


def select_observation(graph, scene, start, end, question, responses, following, correct=None):
    offsets = [i for i in range(start, end) if CHOICE.match(scene.body[i])]
    assert len(offsets) == len(responses), scene.id
    resume = next((i for i in range(offsets[-1] + 1, end)
                   if SPEECH.match(scene.body[i])), end)
    common = graph.lines(scene, resume, end, following)
    menu = f'rev:{scene.id}:observation:{start}'
    options = []
    for index, (offset, (speaker, text, mono)) in enumerate(zip(offsets, responses, strict=True)):
        flag = chr(65 + index)
        reference = scene.source(scene.line + offset + 1)
        next_node = common if correct is None or index == correct else menu
        response = graph.add(f'{menu}:{flag}', type='say', actor=SPEAKERS[speaker], speaker=speaker,
                             text=text, mono=mono, source=reference, next=next_node)
        options.append({'id': flag, 'label': CHOICE.match(scene.body[offset])[1], 'to': response})
    choice = graph.add(menu, type='menu', q=question, options=options,
                       source=scene.source(scene.line + offsets[0] + 1))
    return graph.lines(scene, start, offsets[0], choice)


def examine_placements(graph, scene, following):
    split = scene.body.index('### 먼저 이어서 물을 것')
    following = select_observation(graph, scene, split, len(scene.body), '누구에게 무엇을 먼저 물을까?', [
        ('사츠키', '길을 내준 게 아니라 내가 밀었어. 그때 내가 무슨 생각이었는지까지 네가 봤다고 쓰지는 마.', False),
        ('쇼', '팔이 아팠어도 그때는 답하셨습니다. 나중에 확인한 반응과 따로 보시죠.', False),
    ], following)
    return select_observation(graph, scene, 0, split, '사진에서 어느 자리부터 볼까?', [
        ('쇼', '여기서는 팔을 확인했습니다. 그때 무엇을 드셨는지는 확인하지 않았습니다.', False),
        ('미오', '창가에서 잔을 내려놓는 쪽을 봤다. 팔을 다쳤던 때하고는 달라.', False),
        ('쇼', '제가 들어온 뒤 확인한 반응은 여기입니다. 잔을 준비한 자리를 이 사진으로 정할 수는 없습니다.', False),
    ], following)


COMPARISONS = {
    '01-I00c': ('촬영 직전 어느 위치부터 확인할까?', [
        ('미오', '코토가 나온 뒤 그 위치에서 사진을 찍었다. 그 전에 아무도 물건에 손대지 않았다는 뜻은 아니었다.', True),
        ('미오', '리쿠가 처음 섰던 벽 쪽을 도식에 표시했다. 그를 문 안으로 다시 들여보내지는 않았다.', True),
        ('나나', '제가 확인한 건 발견하고 나서 문이 열린 동안이에요. 그 전에 들어가신 분은 여기에서 적을 수 없어요.', False),
    ]),
    '01-I02d': ('책상이 움직였다는 가설에서 무엇을 대조할까?', [
        ('쇼', '걸렸다고 하려면 몸에 닿았던 물체가 있어야 합니다. 어느 면이 해당합니까?', False),
        ('하루카', '거기 아래로 내가 내려가서 찍었어. 그림의 높이 먼저 맞춰.', False),
        ('미오', '누가 눌렀다고 하려면 실제로 손이 닿을 수 있었는지 봐야 해. 아직 사람 이름부터 고르지는 않을게.', False),
    ]),
    '01-I03a': ('호출과 연결을 어느 상태부터 비교할까?', [
        ('미오', '응답이 멎었다. 창구에선 상대가 더 답하지 않는다는 데까지만 알 수 있었다.', True),
        ('미오', '레이는 수화기를 들고 있었지만 응답이 오지 않았다. 표시등이 꺼진 때와 방 안의 실제 상태는 따로 봤다.', True),
        ('미오', '바깥으로는 연결되지 않았다. 앞서 창구에 응답이 돌아온 기록까지 없어지지는 않았다.', True),
    ]),
    '01-I04f': ('실제로 확인한 손을 어디에 적을까?', [
        ('미오', '가려진 쪽의 빈 시간은 그대로 둘게. 누가 계속 같은 곳에 있었다는 답은 아직 없으니까.', False),
        ('쇼', '증상을 확인한 때와 실제 움직임을 구별하십시오. 가능한 동작은 소견과 따로 대조해야 합니다.', False),
        ('소라', '손 보여 달라고 내가 먼저 말했어. 그때 손 숨기고 간 건 아니야.', False),
        ('나나', '제가 처음 본 손은 제 이름으로 적을게요. 쇼 씨가 나중에 보신 줄은 따로 둬 주세요.', False),
    ]),
    '01-I05a': ('어느 관찰부터 이름을 맞춰 적을까?', [
        ('코토', '제가 이름을 놓을 곳은 공개판을 옮긴 때예요. 처음 종이를 본 곳에는 제가 없었고요.', False),
        ('하루카', '내 카메라로 찍은 순간까지만 답할게. 리쿠가 그 뒤에 본 거하고는 나눠 줘.', False),
    ]),
    '01-I05c': ('자료의 인계를 어디서 다시 확인할까?', [
        ('아카리', '제가 가져온 건 보고서 원본이에요. 조각 봉투는 나나 씨가 따로 가지고 오셨어요.', False),
        ('하루카', '사진은 여기, 원본은 여기야. 어느 걸 확인해 달라는 거야?', False),
        ('유우', '아카리는 가방을 받았다고 했고, 하루카는 그 자리에서 찍었다고 했어. 네가 나한테 어느 하나만 맞으라고 하면 안 할래.', False),
        ('아이', '지금 가방 드신 분이 사진을 찍던 때도 들고 계셨다는 말씀이에요?', False),
    ]),
    '02-I03b': ('누가 무엇을 본 위치부터 확인할까?', [
        ('아카리', '제가 받아 적은 건 이 줄이에요. 그때 바닥까지 보고 있었다고는 못 해요.', False),
        ('사츠키', '돌아올 때 문부터 봤어. 저 거리에서 반납판 글씨는 읽지 못했고.', False),
        ('쇼', '발견에 쓴 예비 열쇠 사진입니다. 이 사진으로 앞선 반납 시각에 누가 받았는지는 알 수 없습니다.', False),
    ]),
    '02-I05b': ('반환대에서 지금 확인할 것은?', [
        ('미오', '하루카가 있던 자리와 사츠키가 돌아본 길이 잠깐 겹쳤다. 그전에 누가 앞문에 있었는지는 모른다.', True),
        ('하루카', '저 안에서 찾은 건 네 손에 없잖아. 네 접시하고 같은 자리에서 얻었다고 쓰지는 마.', False),
        ('미오', '접시는 치우되 준비실 조사까지 마쳤다고 쓰지는 않았다. 사츠키는 안내를 탁자 옆에 뒀다.', True),
    ]),
    '02-I07n': ('같은 시각을 자료마다 억지로 넣지 않고 순서를 맞추려면?', [
        ('코토', '지금 계단에서 본 것과 그때 벽을 돌아가 읽은 건 달라요. 시계가 틀렸다고 정할 수도 없고요.', False),
        ('유우', '소매는 봤어. 그 사람이 창구에 안 왔다고 내가 본 건 아니잖아.', False),
        ('미오', '창구 사진, 앞문 교대, 실제 퇴실, 발견을 각각의 기록에 놓았다. 다른 자리에서 본 시계로 그 사이를 채우지 않았다.', True),
        ('아카리', '열쇠는 제가 직접 받았어요. 시간 표시가 모두의 움직임을 보증하지는 않아요.', False),
    ]),
    '03-I00f': ('이 자리에서 직접 확인할 수 있는 것은?', [
        ('하루카', '카메라는 내가 들고 왔어. 네가 옮겼다는 사진도 없어.', False),
        ('아카리', '천은 아직 방에 도착하지 않았어요. 제가 복도에서 붙들고 있었고요.', False),
        ('하루카', '카메라랑 천이 여기서 마주친 거야. 이걸로 다음 방에서 무슨 일 있었는지는 몰라.', False),
    ]),
    '03-I02b': ('두 방송과 직접 확인한 시점을 어디부터 대조할까?', [
        ('나나', '저는 그때 벤치에 있었어요. 첫 현장을 본 분과 같은 줄에 두지 말아 주세요.', False),
        ('쇼', '첫 방송 뒤 벤치에서 호흡을 확인했습니다. 두 번째 사망 확인보다 앞입니다.', False),
        ('미오', '그때 본 나나와 나, 상태를 확인한 쇼를 따로 적었다. 밖에서 들은 유우를 같은 자리에 넣지 않았다.', True),
        ('미오', '목소리가 같아도 현장에서 실제로 본 사람은 달랐어.', False),
    ]),
    '03-I03g': ('모퉁이에서 본 몸 옆에 어느 위치를 다시 놓을까?', [
        ('하루카', '나 저기까지 숙여서 찍지는 않았어. 바닥 사진에 가려진 데가 있어.', False),
        ('미오', '내가 얼굴을 본 자리와 사츠키가 몸을 돌린 자리를 따로 표시했다. 새로 건네준 사람이 보였던 것은 아니었다.', True),
        ('레이', '제가 처음 보았을 때 이미 손에 들고 있었습니다. 그 뒤로 벤치 쪽을 향했습니다.', False),
        ('사츠키', '이건 떨어진 걸 내가 발로 밀어 놓은 데야. 처음부터 저 위치에 있었던 건 아니야.', False),
    ]),
    '04-I05b': ('들린 위치와 갈 수 있는 길을 어떻게 대조할까?', [
        ('미오', '벽을 돌아 소리는 들렸지만 구획 끝은 막혀 있었다. 사츠키도 문에서 나온 사람을 새로 확인하지는 않았다.', True),
        ('미오', '앞문에서 지나가는 몸까지는 보였다. 닫힌 문 뒤에서 어디로 갔는지는 보이지 않았다.', True),
        ('쇼', '작은 소리가 지나가는 길과 사람이 통과할 폭은 따로 보십시오. 벽의 형상은 직접 확인한 자료에 남아 있습니다.', False),
    ]),
    '05-I05d': ('누가 직접 확인한 줄부터 읽을까?', [
        ('쇼', '잔을 받아 마신 일과 이후 불편하다고 하신 말은 양쪽에 있습니다. 그 뒤의 글은 한 장에만 남았습니다.', False),
        ('나나', '제가 놓은 건 빈 잔이었어요. 제가 기억하지 못해도 다른 분이 기억한다고 하신 말은 따로 적어 주세요.', False),
        ('미오', '내 글씨는 읽을 수 있어. 쓸 때 내가 어느 얼굴을 봤는지까지는 설명 못 해.', False),
    ]),
    '05-I06a': ('문턱을 사이에 두고 누구의 말을 먼저 맞출까?', [
        ('유우', '사츠키가 자기 이름 넣으라고 한 데까지 들었어. 그 뒤 답이 끝나기 전에는 다른 데 봤고.', False),
        ('아카리', '병을 건네신 일은 사츠키 씨가 말씀하세요. 저는 안감의 조각을 따로 보자고 했어요.', False),
        ('쇼', '지금 꺼내 보인 건 빈 봉투입니다. 보관 중인 물건을 더 열지는 않겠습니다.', False),
    ]),
    '06-I01a': ('어느 묶음부터 자료대에 놓을까?', [
        ('미오', '쇼가 받았다는 표시가 붙은 묶음을 자료대에 뒀다. 오늘 누가 꺼냈는지는 다시 물어야 했다.', True),
        ('사츠키', '이건 표지 아래 번호야. 바깥으로 보냈는지는 거기 쓰는 종이를 따로 봐.', False),
        ('유우', '나한테 처음 보인 건 이 면이야. 뒤 번호는 표지에 가려서 못 읽었어.', False),
    ]),
    '06-I03e': ('어디에서 먼저 확인할까?', [
        ('유우', '목소리는 들려. 네가 안에 있었는지는 몰라. 너라고 생각한 건 네가 미리 여기 있으라고 했으니까.', False),
        ('나나', '쇼 씨가 이름을 들은 자리와 제가 몸을 본 자리는 달라요. 저는 같은 때에 둘 다 보지는 못했어요.', False),
        ('미오', '사츠키가 먼저 도착한 발을 봤다. 지나온 문은 유우가 직접 가리킨 뒤에 따로 표시했다.', True),
    ]),
    '06-I05a': ('아직 실제로 시도하지 않은 전달을 어떻게 분류할까?', [
        ('나나', '제가 이름만 부르기만 해도 언제나 같은 일이 생겼다고 한 것은 아니에요. 지금 시험하지는 않을래요.', False),
        ('래피', '관찰한 이름과 행동을 알리려는 뜻이 남으면, 쪽지라고 바로 달라지지는 않아요.', False),
        ('쇼', '사진을 보고 스스로 판단한 것과 그 이름을 직접 전달받은 것은 따로 적으십시오.', False),
    ]),
}


def supplemental_inspection(graph, scenes, ids, following):
    for ident in reversed(ids):
        scene = scenes[ident]
        if ident == '05-I01b':
            following = examine_placements(graph, scene, following)
        elif ident in COMPARISONS:
            question, responses = COMPARISONS[ident]
            correct = {'02-I07n': 2, '03-I00f': 2}.get(ident)
            following = select_observation(graph, scene, 0, len(scene.body), question, responses, following, correct)
        elif ident == '04-I05a':
            following = graph.lines(scene, 2, len(scene.body), following)
            quotes = re.findall(r'“([^”]+)”', scene.body[1])
            assert len(quotes) == 3
            cases = []
            for flag, text in zip('ABC', quotes, strict=True):
                target = graph.add(f'rev:{ident}:memory:{flag}', type='say', actor='satsuki', speaker='사츠키',
                                   text=text, source=scene.source(scene.line + 2), next=following)
                cases.append({'flag': '04-F06', 'equals': flag, 'to': target})
            following = graph.add(f'rev:{ident}:memory', type='branch', cases=cases, default=following)
        else:
            following = graph.lines(scene, 0, len(scene.body), following)
    return following


def examine_document_bundles(graph, scene, following):
    labels = ('옛 공원 사진', '운영 승인 자료', '현재 운용 기록')
    starts = [scene.body.index('### ' + label) for label in labels]
    menu = 'rev:06:overview-bundles'
    flags = [f'{menu}:{i}' for i in range(3)]
    options = []
    for label, flag, start, end in zip(labels, flags, starts, [*starts[1:], len(scene.body)], strict=True):
        done = graph.add(flag + ':read', type='stage', set={flag: True}, next=menu)
        entry = graph.lines(scene, start + 1, end, done)
        options.append({'id': flag, 'label': label, 'requires': {flag: False}, 'to': entry})
    options.append({'id': 'continue', 'label': '세 묶음의 시점을 따로 기록한다',
                    'requires': {flag: True for flag in flags}, 'to': following})
    return graph.add(menu, type='menu', q='어느 자료부터 펼칠까?', options=options,
                     source=scene.source(scene.line))


def first_investigation_close(graph, scenes, following):
    scene = scenes['01-I06']
    following = graph.lines(scene, 0, len(scene.body), following)
    following = supplemental_inspection(graph, scenes, ['01-I05c'], following)
    scene = scenes['01-I05b']
    offsets = [i for i, row in enumerate(scene.body) if CHOICE.match(row)]
    assert len(offsets) == 4
    common = graph.lines(scene, offsets[-1] + 1, len(scene.body), following)
    menu = 'rev:01:final-evidence-custody'
    options = []
    for i, (at, (speaker, text)) in enumerate(zip(offsets, [
        ('하루카', '앞면을 받았던 때하고 원본을 발견한 때가 달라. 내가 찍었던 위치도 따로 봐.'),
        ('아카리', '객실에서 볼 수 있는 범위는 작아요. 공용 점검 자료와 현장에서 직접 확인한 물건은 이미 있어요.'),
        ('', ''),
        ('쇼', '부록을 열지 않아도 실제로 확인한 자료를 가져갈 수 있습니다. 누가 어디에서 얻었는지부터 읽으십시오.'),
    ], strict=True)):
        target = common if not speaker else graph.add(f'{menu}:retry:{i}', type='say', actor=SPEAKERS[speaker],
            speaker=speaker, text=text, source=scene.source(scene.line + at + 1), next=menu)
        options.append({'id': str(i), 'label': CHOICE.match(scene.body[at])[1], 'to': target})
    following = graph.add(menu, type='menu', q='지금 실제로 확인한 자료를 어떻게 가져갈까?', options=options,
                          source=scene.source(scene.line + offsets[0] + 1))
    following = graph.lines(scene, 0, offsets[0], following)
    following = supplemental_inspection(graph, scenes, ['01-I05a'], following)
    scene = scenes['01-I05']
    starts = [i for i, row in enumerate(scene.body) if row.startswith(('**A. ', '**B. '))]
    join = scene.body.index('#### 공통')
    following = graph.lines(scene, join + 1, len(scene.body), following)
    following = graph.add('rev:01:room-search-return', type='stage', scene={'space': 'hotel_lobby'},
                          source=scene.source(scene.line + join + 1), next=following)
    choice = graph.menu(scene, '지금 카에데의 객실을 살펴볼까?', [
        (scene.body[at][5:-2], at + 1, end, '') for at, end in zip(starts, [starts[1], join], strict=True)
    ], following)
    observe = graph.nodes[choice]['options'][0]
    observe['to'] = graph.add('rev:01:room-search-entry', type='stage', scene={'space': 'story_guest_room'},
                              source=scene.source(scene.line + starts[0] + 1), next=observe['to'])
    following = graph.lines(scene, 0, starts[0], choice)
    return graph.add('rev:01:document-handover', type='stage', scene={'space': 'hotel_lobby'},
                     source=scene.source(scene.line), next=following)


def first_photo_investigation(graph, scene, following):
    chronology = scene.body.index('#### 문 안으로 들어오기 전과 후')
    following = graph.lines(scene, chronology + 1, len(scene.body), following)
    steps = [
        ('복도에서 먼저 확인한 것은?', '문 밖에서 두 번 노크하고 응답을 기다렸다',
         '하루카가 사진을 찍을 때까지 아무도 안에 들어가지 않았다',
         '사진을 찍기 전에도 문을 열어 안을 봤어. 첫 번째와 두 번째 노크 사이에는 들어가지 않았고.'),
        ('처음 열린 문턱에서 직접 확인한 것은?', '미오가 바닥에 놓인 종이의 위치를 보았다',
         '미오가 바로 종이의 글을 전부 읽었다',
         '문턱에서 위치는 봤어. 그때 글 전체를 읽지는 못했어.'),
        ('먼저 현장을 본 뒤의 순서는?', '아카리가 뒤이어 확인하고 방송 뒤 하루카가 사진을 찍었다',
         '촬영한 사진을 보고 처음으로 문 안의 상태를 확인했다',
         '사진은 안을 보고 사람을 부른 뒤야. 그 전에 누가 다쳤는지까지 찍은 건 아니야.'),
    ]
    reference = scene.source(scene.line + chronology + 1)
    for index, (question, correct, wrong, reply) in reversed(list(enumerate(steps))):
        menu = f'rev:01:discovery-sequence:{index}'
        retry = graph.add(menu + ':retry', type='say', actor='mio', speaker='미오', text=reply,
                          source=reference, next=menu)
        following = graph.add(menu, type='menu', q=question, source=reference, options=[
            {'id': 'observe', 'label': correct, 'to': following}, {'id': 'assume', 'label': wrong, 'to': retry}])
    covered = next(i for i, row in enumerate(scene.body) if row.startswith('처음 기록이 끝난 뒤'))
    following = graph.add('rev:01:scene-covered', type='say', actor='mio', speaker='미오', mono=True,
        text='기록을 마치고 아이가 천을 펼쳤다. 바닥의 종이와 문턱에는 닿지 않도록 쇼가 옆에서 보았다.',
        source=scene.source(scene.line + covered + 1), next=following)
    shutter = next(i for i, row in enumerate(scene.body) if row.startswith('(하루카가 현재 몸과'))
    following = graph.lines(scene, shutter + 1, covered, following)
    following = graph.add('rev:01:first-shutter', type='stage', sfx='v4_camera_shutter',
                          source=scene.source(scene.line + shutter + 1), next=following)
    return graph.lines(scene, 0, shutter, following)
