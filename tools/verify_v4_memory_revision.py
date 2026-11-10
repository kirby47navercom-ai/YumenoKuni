"""First encounter, late recognition, stable saves and final-hearing regression."""
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/v4_story'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
graphs = {p.stem: read(p) for p in (DATA/'chapters').glob('*.json')}
tasks = read(DATA/'tasks.json')['tasks']
baseline = read(ROOT/'docs/analysis/story_memory_20261103/before_routes.json')
checked = 0
for name, old in baseline.items():
    graph = read(DATA/name)
    assert set(old['nodes']) <= set(graph['nodes']), name
    assert all(n['type'] == graph['nodes'][key]['type'] for key,n in old['nodes'].items()), name
    checked += len(old['nodes'])

p = graphs['P']
known = {'mio'}
at = p['entry']
while p['nodes'][at]['type'] != 'menu':
    n = p['nodes'][at]
    if n['type']=='say':
        if n.get('introducesActor'):
            assert n['introducesActor']==n['actor']
            assert n['actor'] not in known
            known.add(n['actor'])
        assert (n['speaker']=='???') == (n['actor'] not in known and not n.get('mono'))
    at = n['next']
assert len(known)==16
assert not any('학원에서도 저 둘' in n.get('text','') or '다 아는 얼굴인데' in n.get('text','') for n in p['nodes'].values())

# A changed opening must not silently move public-rule acquisition to unrelated
# lines, or remove either choice and its mutually exclusive callbacks.
from verify_v4_story import walk
from v4_public_records import build_records
records = build_records()
for choices in itertools.product('AB', repeat=2):
    trace, flags = walk(p, {'v4:10:P-C01':choices[0], 'v4:10:P-C02':choices[1]})
    assert not any(n.get('text')=='다 아는 사람이야.' for n in trace)
    if choices[0]=='B':
        assert any(n.get('text')=='나 말고도 이름은 다 들었잖아.' for n in trace)
    acquired = {key for node in trace for key in records['eventById'].get(node['id'],[])}
    assert acquired == {'v4:public-record:P-graduation','v4:public-record:P-no-deadline','v4:public-record:P-disclosure'}

from test_v4_story_case6 import walk as final_walk
for support in 'AB':
    end, trace, flags, cards = final_walk({'E6-C01':support})
    assert end['type']=='end' and end['id']=='v4:6:end:'+support
    ids = [n['taskId'] for n in trace if n['type']=='task']
    assert ids[-1] == graphs['6']['resultTaskId'] == 'T6-RL-FINAL'
    assert ids.index('T6-VOTE-01') < ids.index('T6-RL-FINAL')
    reveal = next(i for i,n in enumerate(trace) if n.get('source',{}).get('file','').startswith('194_'))
    # Personal accusations may consume the unredacted list only after the
    # actual disclosure; a later "already read" sentence cannot supply it.
    first_personal = next(i for i,n in enumerate(trace) if n.get('source',{}).get('file','').startswith('16a_') and n.get('source',{}).get('location')=='6-07')
    identity = next(i for i,n in enumerate(trace) if n.get('source',{}).get('file','').startswith('194_') and '그 열세 분 안에' in n.get('text',''))
    assert reveal < identity < first_personal
    visible_docs={n.get('title') for n in trace[:first_personal] if n['type']=='document'}
    assert {'옛 행사 준비물 인계표','옛 성명면·인형 인계 대조',
            '옛 접수·개입·맹세 서명 대조','이번 입소 처리 이력'} <= visible_docs
    # Moving the relationship reveal earlier must not also move the guide's
    # distinct identity disclosure (6-61/62) into the entrance reaction.
    entrance='\n'.join(n.get('text','') for n in trace if n.get('source',{}).get('file','').startswith('194_'))
    assert '지금 네가 그 이름으로 대답하면' not in entrance
    hearing = next(i for i,n in enumerate(trace) if n.get('taskId')=='T6-RL-FINAL')
    release = next(i for i,n in enumerate(trace) if n.get('set',{}).get('public:game:control-ended'))
    assert reveal < hearing < release
    assert flags['public:intake:relationship-mask-ended'] is True
    assert any(n['type']=='document' and n.get('title')=='이번 입소 처리 이력' for n in trace)
    assert end['humanSurvivors'] == ['mio','rin','nana','sho','satsuki']

from v4_native_tasks import convert_task
hearing = tasks['T6-RL-FINAL']
assert len(hearing['questions'])==7
assert len(hearing['closesMysteries'])==7 and len(set(hearing['closesMysteries']))==7
for q in hearing['questions']:
    assert len(q['options'])==3 and q['retryPolicy']=='currentLinkOnly'
    assert {v['optionId'] for v in q['wrongVariants']} == {o['id'] for o in q['options']} - {q['answer']}
    assert q['success'] and all(v['script'] for v in q['wrongVariants'])
    assert all(e['source']['file'].startswith('195_') for e in q['success'])
    assert all(e['source']['file'].startswith('195_') for v in q['wrongVariants'] for e in v['script'])
bundle = convert_task(hearing)
assert bundle['ready'] and len(bundle['stage']['questions'])==7
assert tasks['T6-VOTE-01']['finalVote'] is False

# Catch the actual old-source leaks that structural path checks missed.
five_text='\n'.join(n.get('text','') for n in graphs['5']['nodes'].values())
for premature in ['코토 씨하고 맺은 약속이요','제가 그날 여러분 기억을 없앴어요','코토 씨는 늦게 오셨어요','네가 진짜 우리 기억 건드렸다고',
                  '너는 이미 나한테 한 적 있었네.','예전에는 안 했는데 네가 했고.',
                  '그때는 내가 부탁 안 했잖아.이번에는','네가 우리가 조용해진 걸 좋아했냐고.',
                  '너는 내가 모르는 나를 알고 있잖아.','내가 풀면 네가 나나가 하는 말을']:
    assert premature not in five_text, premature
assert '그날 아이들 기억을 없앴어요' in five_text
assert '이 선도 코토 씨가 거신 거예요?' in five_text
assert '린 씨인지는 아직 몰라요.' in five_text
assert '그때도 우리를 알아보고 손잡았다는 말이야?' in '\n'.join(n.get('text','') for n in graphs['6']['nodes'].values())
assert any('원본 분류 공개' in o['label'] for n in graphs['5']['nodes'].values() for o in n.get('options',[]))
six_text='\n'.join(n.get('text','') for n in graphs['6']['nodes'].values())
assert '맞히면 지금 통제가 끝나.' not in six_text
assert '우리를 여기에 모은 일은 오늘이고' not in six_text
assert '레이한테 종이 받던 거, 지금 조금 생각났어.' in six_text
answer=tasks['T6-ANSWER-A01']
assert '최종 지목을 맞히면 곧바로' not in json.dumps(answer,ensure_ascii=False)
assert '남은 쟁점' in json.dumps(answer,ensure_ascii=False)
for file,missing in [('21','아까 광장에서 나눠 줬던'),('26','아까 광장에서 노래 얘기'),('25','타이가 씨가 식판 겹쳐 주시기 전에')]:
    for p in (DATA/'freetime').glob('*.json'):
        g=read(p)
        assert missing not in '\n'.join(n.get('text','') for n in g.get('nodes',{}).values()),(file,p)
# First-day events cannot recall a previous shared day. The public complaint
# must quote an interaction that actually precedes the submitted form.
prologue=graphs['P']
assert not any('그 말도 어제 했어.' in n.get('text','') for n in prologue['nodes'].values())
meal_response = '네 것까지 받아 놨는데 이제 가는 거야?'
for intro,meal in itertools.product('AB',repeat=2):
    trace,_=walk(prologue,{'v4:10:P-C01':intro,'v4:10:P-C02':meal})
    assert any(n.get('text')==meal_response for n in trace)==(meal=='B')
public=graphs['2']['nodes']['v4:2:document:ai-request']
assert public['title']=='첫날 조 편성 의견'
assert '오늘 저녁' in public['rows'][0]
assert '그냥 같이 먹으면 안 되냐' in public['rows'][0]
assert any('그냥 같이 먹으면 안 되냐' in n.get('text','') for n in prologue['nodes'].values())
two_text='\n'.join(n.get('text','') for n in graphs['2']['nodes'].values())
for missing in ('앞에 행사 날짜가 잘렸어요.','케이크를 식혀야 한다고 말했어요.','세 번이요.'):
    assert missing not in two_text,missing
assert '그런데 그 한마디가 싫었어요.' in two_text
assert '방금 왔어. 그때 일은 몰라.' not in two_text
assert '그때 식당에는 나도 있었어. 네가 한 말은 들었고.' in two_text
second_stages='\n'.join(n.get('direction','') for n in graphs['2']['nodes'].values() if n['type']=='stage')
assert '미오가 의견서 내용을 미리 알고 있지는 않았다는 말에' in second_stages
assert '첫날 광장에서 미오가 물통을 연 목격자를 물었던 일을 근거로' in second_stages
assert '실제로 함께 응급 처치를 맡았다가 지체한 적이 있다는 기록은 아니다.' in second_stages
assert '첫날 광장에서 물통 여는 걸 누가 봤냐고 물었을 때.' in two_text
assert '응급 일을 같이 해 보고 쓴 건 아니야.' in two_text
assert any(n.get('source',{}).get('file','').startswith('155_') and n.get('source',{}).get('line')==115 and n.get('text')=='네가 가져오기로 한 건 아니잖아. 오늘은 내가 꺼냈고.' for n in graphs['2']['nodes'].values())
assert '뒤에서는 아이가 계단을 내려오다 바구니를 보고 멈춘다.' in second_stages
assert not any(n.get('source',{}).get('file','').startswith('12a2_') and n.get('text')=='두 분 일찍 왔네. 우수 직원.' for n in graphs['2']['nodes'].values())
fte37=read(DATA/'freetime/37.json');fte64=read(DATA/'freetime/64.json')
fte20=read(DATA/'freetime/20.json')
assert any(n.get('text')=='쟤가 그걸 어떻게 알아.발 접어 준 손이 네 손이었는데.' for n in fte20['nodes'].values())
assert not any('발 달아 준 손이 네 손' in n.get('text','') for n in fte20['nodes'].values())
fte23=read(DATA/'freetime/23.json')
assert any(n.get('text')=='첫 장까지만. 제목 읽었다고 벌써 책 읽은 건 아니잖아.' for n in fte23['nodes'].values())
assert not any('왜 읽으면 화난다는 것부터 팔아.' in n.get('text','') for n in fte23['nodes'].values())
fte29=read(DATA/'freetime/29.json');fte30=read(DATA/'freetime/30.json');fte33=read(DATA/'freetime/33.json')
assert any(n.get('text')=='막히면 안심해도 되는 거네. 이상하다.' for n in fte29['nodes'].values())
assert not any(n.get('text')=='안 막는 게 도와주는 거네. 이상하다.' for n in fte29['nodes'].values())
assert any(n.get('text')=='누구한테 배웠어? 일부러냐고 물으면 말 돌리는 것도.' for n in fte30['nodes'].values())
assert any(n.get('text','').startswith('아버지. 마술사였거든.') for n in fte30['nodes'].values())
assert not any(n.get('text','').startswith('아버지도 그렇게 했어?') for n in fte30['nodes'].values())
assert any(n.get('text','').startswith('나는 집에 있으면 쉬는 건데.') for n in fte33['nodes'].values())
assert not any('네가 나서서 체육관 온 건' in n.get('text','') or '너희가 보기엔 맨날 내가 가르치는' in n.get('text','') for n in fte33['nodes'].values())
fte34=read(DATA/'freetime/34.json')
fte56=read(DATA/'freetime/56.json')
assert any(n.get('text','').startswith('네가 안 본 걸 봤을 거라고 말해서. 방금 네가 들려준 얘기로') for n in fte56['nodes'].values())
assert not any('그건 내가 그날 본 게 있어서.' in n.get('text','') or '내가 그날 왜 지루했는지' in n.get('text','') for n in fte56['nodes'].values())
assert any(n.get('text')=='미오, 여기 오기 전에 찍은 네 사진은 집에 있어?' for n in fte34['nodes'].values())
assert not any('우리 전에 찍은 사진들은' in n.get('text','') for n in fte34['nodes'].values())
assert any(n.get('text')=='전에 혼자 자르고 웃은 적은 있어.' for n in fte37['nodes'].values())
assert not any('전에 잘랐을 때 미오가 웃었던' in n.get('text','') or '그런 얘기 했던 것 같기도' in n.get('text','') for n in fte37['nodes'].values())
assert any('아까 거울 들어 달라고 한 것도' in n.get('text','') for n in fte37['nodes'].values())
assert not any('그때는 지금 잘 모르겠어.' in n.get('text','') for n in fte37['nodes'].values())
assert any('내가 네가 본 대로 봤다고 하지는 않을게.' in n.get('text','') for n in fte64['nodes'].values())
# Dialogue causality must survive both ordinary nodes and task feedback.
assert '종이에 네 이름이 있다고 손댄 장면까지 봤다고 하지는 마.' not in five_text
assert '종이에 사츠키 이름이 있다고, 내가 뭘 넣는 손까지 본 건 아니잖아.' in five_text
assert '너도 우리한테 그랬잖아.' not in five_text
assert '너는 진짜 했잖아.우리한테.' not in five_text
assert '그 아이들한테 제가 한 일은 맞아요.' in five_text
assert '돌아간 열 초는 기억 안 나. 차 마시고 어지럽다고 한 건 나도 기억해.' in five_text
assert any(n.get('source',{}).get('file','').startswith('15a8_') and n.get('source',{}).get('line')==259 and '나나는 이 확인 자리에 없다.' in n.get('direction','') for n in graphs['5']['nodes'].values())
assert any(n.get('source',{}).get('file','').startswith('15d_') and n.get('source',{}).get('line')==191 and n.get('text')=='이건 아카리 씨가 골랐다고 하셨죠.' for n in graphs['5']['nodes'].values())
assert any(n.get('source',{}).get('file','').startswith('15d_') and n.get('source',{}).get('line')==195 and n.get('text','').startswith('저는 코토 씨께 갔을 때 사츠키 씨 손부터 봤어요.') for n in graphs['5']['nodes'].values())
def nested_objects(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():yield from nested_objects(child)
    elif isinstance(value,list):
        for child in value:yield from nested_objects(child)
assert any(isinstance(n.get('source'),dict) and n['source'].get('file','').startswith('167_') and n['source'].get('line')==182 and n.get('text','').startswith('손으로 들고 마신 건 미오가 봤어.') for n in nested_objects(tasks))
assert '처음 호텔에서 봤으니까.' not in six_text
assert '광장에서 이름을 듣고 열여섯을 셌으니까.' in six_text
assert '맞으면 지금 게임 끝나는 거.' not in six_text
assert '그걸 맞힌 뒤 남은 쟁점까지 확인하고 마지막에 통제를 끝내는 거.' in six_text
assert any(n.get('text','').startswith('과거 지목 뒤 남은 쟁점까지 확인하고 마지막에 끝내기로 하면 출입 통제가 끝나.') for n in nested_objects(tasks))
four_nodes=graphs['4']['nodes']
for graph in list(graphs.values())+[read(p) for p in (DATA/'freetime').glob('*.json')]:
    assert not any(n.get('type')=='menu' and n.get('q','').startswith('#') for n in graph.get('nodes',{}).values())
    assert not any(n.get('type')=='menu' and n.get('q','').startswith('선택 ') for n in graph.get('nodes',{}).values())
assert graphs['1']['nodes']['v4:176:W1-C02:menu']['q']=='전화 연습에 답할까'
assert fte37['nodes']['v4:37:F-HA02-B:menu']['options'][2]['label']=='「아까 부탁을 서로 다르게 들은 걸까」'
assert {'린과 늦은 첫 만남','켄과 늦은 첫 만남'} <= {o['label'] for o in graphs['2']['nodes']['v4:2:window:F2-A']['options']}
door_answer=[n for n in four_nodes.values() if n.get('source',{}).get('file','').startswith('14a6_') and n.get('source',{}).get('line')==271 and n['type']=='say']
assert len(door_answer)==1 and door_answer[0]['text']=='응. 네가 문 열고 나가는 데까지 봤어.'
assert any(n.get('source',{}).get('file','').startswith('14a6_') and n.get('source',{}).get('line')==137 and n.get('text')=='머리카락 넘겨 준 건 생각나.' for n in four_nodes.values())
opening_text='\n'.join(n.get('text','') for n in prologue['nodes'].values())
assert '야, 이름부터 듣자.' not in opening_text
assert '그럼 적은 이름을 불러 봐.' in opening_text
assert '너 지금도 그 얘기 하냐?' not in opening_text
first_stages='\n'.join(n.get('direction','') for n in graphs['1']['nodes'].values() if n['type']=='stage')
assert '미오는 봉투를 연다. 카에데가 남긴 종이의 빈 부분이 옆에 있다.' not in first_stages
assert '미오가 종이 조각의 봉투에서 손을 뗀다.' not in first_stages
assert '나나가 자기 증언대의 조각 봉투를 열 준비를 한다.' in first_stages
assert '실물 봉투는 나나의 증언대에 그대로 있다.' in first_stages
assert '실물은 각각 맡은 사람이 계속 보관한다.' in first_stages
assert '아이는 아직 여기서 수거한 천을 들고 있다.' not in first_stages
assert '아이는 운반할 때 쓰려고 깨끗한 천 한 장을 따로 가져왔다.' in first_stages
for intro,meal in itertools.product('AB',repeat=2):
    trace,_=walk(prologue,{'v4:10:P-C01':intro,'v4:10:P-C02':meal})
    texts=[n.get('text','') for n in trace]
    assert '내 노래는 듣지도 않았잖아.' in texts
    assert ('밥 먹고 나서도 계속 있을지는 아직 모르니까.' in texts)==(meal=='A')
print(json.dumps({'passed':True,'preservedNodeIds':checked,'introducedActors':len(known),
                  'prologueChoicePaths':4,'finalEndings':2,'finalHearingLinks':7,
                  'runtimeTested':False},ensure_ascii=False))
