"""Evidence completion, recoverable prior records, and the trial summons."""


def apply_investigation_flow(chapters):
    graph = chapters['1']
    nodes = graph['nodes']
    hub = nodes['rev:01:investigate']
    record = nodes['rev:01:application']
    hub['finishOnRequiredCards'] = True
    reminder = 'rev:01:application-reminder'
    reminder_flag = 'rev:01:application-reminded'
    hub['reminder'] = {'missingCard': 'v4:E1-APP', 'flag': reminder_flag, 'node': reminder}
    nodes[reminder] = {'id': reminder, 'type': 'say', 'actor': 'mio', 'speaker': '미오', 'mono': True,
                       'text': '관리 사무실에 있던 외부 통화 공지와 접수 신청서도 확인해 봐야겠어. 그 서류까지 챙겨 가자.',
                       'source': dict(record['source']), 'set': {reminder_flag: True}, 'next': hub['id']}
    # A save imported after the application scene must still be able to inspect it.
    done = 'rev:01:application-review:return'
    read = 'rev:01:application-review:record'
    nodes[done] = {'id': done, 'type': 'return'}
    nodes[read] = {**record, 'id': read, 'next': done}
    hub['spots'].append({'id': '01-I-application-review', 'label': record['name'],
                         'neutralLabel': record['name'], 'space_id': 'management_office',
                         'target_id': 'desk_drawer', 'entry': read,
                         'missingCards': ['v4:E1-APP']})
    court = 'rev:01:court-entry'
    first = 'rev:01:investigation-ended'
    second = 'rev:01:trial-summons'
    off = 'rev:01:trial-summons-off'
    gather = 'rev:01:trial-gather'
    enter = 'rev:01:trial-gather:enter'
    returned = 'rev:01:trial-gather:return'
    arrival = 'rev:01:trial-gather:arrival'
    boarded = 'rev:01:trial-gather:boarded'
    after_investigation = hub['next']
    hub['next'] = first
    boarding, = (n for n in nodes.values() if n.get('source', {}).get('location') == '01-I06'
                  and n.get('actor') == 'yuu' and n.get('text') == '이걸 타라고?')
    # Keep the farewell before walking and the cabin dialogue after arrival.
    for node in nodes.values():
        if node.get('next') == boarding['id']:
            node['next'] = gather
        elif node.get('next') == court and node.get('source', {}).get('location') == '01-I06':
            node['next'] = arrival
    source = dict(nodes[court].get('source', record['source']))
    nodes[first] = {'id': first, 'type': 'say', 'actor': 'lappy', 'speaker': '래피',
                    'text': '수사 시간이 끝났어요! 하던 조사는 여기까지예요.',
                    'source': source, 'presentation': {'actions': ['broadcast_on'],
                    'music': {'operation': 'stop', 'fade_seconds': .3}}, 'next': second}
    nodes[second] = {'id': second, 'type': 'say', 'actor': 'lappy', 'speaker': '래피',
                     'text': '모두 재판 엘리베이터로 모여 주세요. 엘리베이터에 탑승하면 학급재판장으로 내려갑니다.',
                     'source': source, 'next': off}
    nodes[off] = {'id': off, 'type': 'stage', 'presentation': {'actions': ['broadcast_off']}, 'next': after_investigation}
    nodes[gather] = {'id': gather, 'type': 'investigate', 'objectiveRole': 'trial-gather',
                     'keepCurrentRoom': True, 'space_id': 'hotel_lobby',
                     'investigationMusic': 'bgm_tense',
                     'requiredSpotIds': ['01-trial-call'],
                     'spots': [{'id': '01-trial-call', 'label': '재판 엘리베이터 탑승',
                                'neutralLabel': '재판 엘리베이터 탑승',
                                'space_id': 'trial_elevator', 'world_pos': [0, .9, 0],
                                'entry': enter}], 'next': court}
    nodes[enter] = {'id': enter, 'type': 'say', 'actor': 'mio', 'speaker': '미오', 'mono': True,
                    'text': '재판 엘리베이터 앞에 도착했다. 열린 문 너머로 안쪽을 들여다봤다.',
                    'source': source, 'set': {boarded: True}, 'next': boarding['id']}
    # Older saves can already be inside the cabin dialogue, without the new
    # exploration return frame. They continue directly into the trial.
    nodes[arrival] = {'id': arrival, 'type': 'branch', 'default': court,
                      'cases': [{'flag': boarded, 'equals': True, 'to': returned}]}
    nodes[returned] = {'id': returned, 'type': 'return'}
