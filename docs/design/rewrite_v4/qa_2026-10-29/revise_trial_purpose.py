"""One-shot manuscript edit. No game data, timing claims, or count quotas."""
from pathlib import Path
import hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
Q=Path(__file__).resolve().parent
LP=Q/'trial_input_reedit.json'
ledger=json.loads(LP.read_text(encoding='utf-8'))
assert not ledger.get('purpose_revision'), 'already applied; do not regenerate'
before={p.name:p.read_text(encoding='utf-8') for p in ROOT.glob('*.md')}
retired=[]

def digest(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
def retire(ident,reason,dialogue):
    e=next(e for e in ledger['entries'] if e['id']==ident)
    f=ROOT/e['file'];s=f.read_text(encoding='utf-8')
    m=re.search(r'^## '+re.escape(ident)+r' [^\n]+\n',s,re.M);assert m,ident
    a=m.start();n=re.search(r'^## ',s[m.end():],re.M)
    b=m.end()+n.start() if n else len(s)
    block=s[a:b];f.write_text(s[:a]+s[b:],encoding='utf-8')
    f=ROOT/e['parent'];s=f.read_text(encoding='utf-8')
    pat=r'^> \*\*필수 입력 '+re.escape(ident)+r':\*\*[^\n]+\n\n'
    s,n=re.subn(pat,lambda m:dialogue.strip()+'\n\n',s,flags=re.M)
    assert n==1,(ident,n);f.write_text(s,encoding='utf-8')
    retired.append({'entry':e,'reason':reason,'former_block':block,'replacement_dialogue':dialogue.strip()})
    ledger['entries'].remove(e)

retire('T1-NS-A04','카에데의 퇴실을 물은 문답의 주어 정정.새 물증 판정이 아니며 원래 대면이 곧바로 질문 누락의 책임을 다룬다.', '''[유우] 잠깐.아카리 처음엔 아무도 못 봤다고 했잖아.지금은 한 사람 봤다고 하고.

[아카리] 아무도요?제 말을 그렇게 기억하세요?

[유우] 지금 내가 말을 만들었다는 거야?

[사츠키] 둘 다 소리부터 키우지 마.누구 나오는 걸 물었는지 읽어.

(미오는 수사 문답을 편다.질문을 잘못 줄여 적은 자리가 자기 메모에도 있다.다른 사람의 거짓말을 찾듯 넘기던 손을 멈춘다.)''')
retire('T6-NS-A02','뒤의 유보 인수와 최종 정상 표시를 같은 구간에서 연달아 판정했다.직접 대면을 복원하고 실제 판정은 항목을 대조하는 A03에 둔다.', '''[사츠키] 정상으로 바꾼 사람이 넘기고 나서 또 고장 났을 수도 있어.

(미오가 사츠키를 본다.사츠키는 아카리 이름이 있는 쪽이 아니라 다음 인수 항목을 가리킨다.)

[사츠키] 걔 아버지라서 안 믿어 주자는 말 하지 말고.네가 그렇게 물었어도 봤을 거잖아.

[린] 지금 그쪽 집 편 들었다고 한 사람 없어.

[사츠키] 네가 안 했으면 됐어.미오한테 물었어.

(미오는 두 사람 사이에 끼워 넣을 대답을 고르다가 자료를 자기 앞으로 당긴다.사츠키가 원한 건 어느 편이라는 말이 아니었다.)''')
retire('T4-PERSON-A02','레이에게 인지 여부를 직접 묻는 질문이다.이미 고정 주체가 제시된 상태에서 누구에게 물을지 얼굴을 고르는 것은 정체 추리가 아니다.', '''[린] 또 다른 사람한테 네가 본 걸 대신 말하게 하지 마.

[레이] 제가 답할 차례라는 건 알고 있습니다.

[린] 그럼 미오 봐.종이 말고.

(레이가 미오를 본다.미오는 질문을 나나에게 넘기지 않는다.알았는지 몰랐는지 레이가 직접 말해야 한다.)''')
retire('T6-PERSON-A01','나나의 최초 망각 개입은 앞서 공개됐고 바로 앞 A08에서 선후를 판정한다.동일 인물을 곧바로 다시 고르게 하지 않는다.', '''[사츠키] 지금도 나중 약속 얘기할 거야?

[나나] 아니요.그전에 제가 한 일을 말씀드리고 있어요.

[사츠키] 그럼 지금은 그쪽 봐.래피 말고 우리.

(나나는 시선을 돌린다.숨이 막혀서 대답하지 못하는 장면은 아니다.미오는 그가 편하게 말하게 된 것을 용서의 근거로 적지 않는다.)''')
retire('T1-FA-A02','기존 통증의 이름 맞히기가 바로 다음 손목 쇼다운의 전제를 되묻는다.의료 사실은 남기되 힘의 불능 주장을 실제 반박 대상으로 둔다.', '''[리쿠] 아팠다면서.그 말부터 안 믿을 거야?

[나나] 아프셨던 건 알아요.처음 보호대 드릴 때도요.

[타이가] 그럼 그 얘기도 해.종이 얘기할 때만 내 손 보고 있지 말고.

(나나가 보호대 봉투를 자기 쪽으로 옮긴다.통증을 인정하는 말이 타이가가 원하는 다음 대답까지 약속한 건 아니다.)''')
retire('T2-FA-A02','바로 앞 MM-A03에서 파단면을 직접 고르고 법정에서 실물을 대조했다.같은 연결부의 명칭을 다시 맞히는 입력을 없앤다.', '''[유우] 내 거였어.그건 말했잖아.이제 같은 물건인지 묻는 건 끝났지?

[리쿠] 나는 네가 어디서 찢었는지가 남았는데.

[유우] 다 모른다면서 자꾸 내 쪽에 쌓아 두네.

(리쿠는 고리 사진 대신 도구에 걸린 옷감 쪽을 당긴다.미오가 그 손을 잠깐 막았다가 놓는다.다음 반론은 다른 물증의 시간을 묻는 말이다.)''')
retire('T3-FA-A03','A06에서 조종 경험 미공유를 판정했다.원래 소유자라는 단어를 다시 맞히지 않고,100% 예외 주장을 실제 문답에서 검토한다.', '''[하루카] 아까 기억 안 넘어간다고 했잖아.그 답을 또 들으면 달라져?

[소라·켄의몸] 아까는 십오 분 지나면 돌아온다고도 했지.그건 달라졌고.

[하루카] 그러니까 다른 것도 다 바뀌었을 거라고?

[코토] 유지가 달라진 조건을 기억 쪽에도 붙일 수 있는지 묻는 거야.거기만 다시 확인하자.

(미오는 원문 봉투를 닫지 않는다.같은 이름을 한 번 더 말해 확신하는 대신,상대가 바꾸어 붙인 조건을 듣는다.)''')
retire('T6-RL-A03','다음 A09가 요청·도착·생성 뒤 인원을 실제 대조한다.그 직전에 세 숫자와 결론을 모두 알려 주는 연결판을 제거한다.', '''[린] 같은 얼굴 얘기는 잠깐 놔 봐.이 숫자 언제 적힌 건데.

[래피] 어느 열여섯을 말씀하시나요?

[린] 네가 왜 그렇게 묻는지부터 보고 있어.

[쇼] 요청 쪽하고 도착 쪽을 따로 놔.지금 종이 겹쳤어.

(미오는 겹친 두 기록을 나눈다.처음부터 모두 도착했다는 설명과 나중에 숫자가 맞았다는 설명을 아직 같은 답으로 쓰지 않는다.)''')

def add_ns(ch,num,parent,start,end,title,dialogue,evidence,answer,wrong,wrong_reply,correct):
    ident=f'T{ch}-NS-A{num:02d}';name=f'{180+ch}_{ch}장_재판_반복논의와_지목_연속대본.md'
    f=ROOT/parent;s=f.read_text(encoding='utf-8')
    assert s.count(start)==s.count(end)==1,(ident,'ambiguous anchor')
    a=s.index(start);b=s.index(end,a+len(start));removed=s[a:b]
    weak=re.search('【([^】]+)】',dialogue);assert weak
    slug=re.sub(r'[^\w -]','',(f'{ident} {title} — NS').lower()).replace(' ','-')
    link=f'> **필수 입력 {ident}:** [{title}]({name}#{slug}).해당 블록의 정답 뒤 지정된 다음 진입을 따라가요.\n\n'
    f.write_text(s[:a]+link+s[b:],encoding='utf-8')
    body=f'''## {ident} {title} — NS

진입: `{parent}`의 `{start}`부터 `{end}` 직전까지를 대체해요.앞에서 답한 결론을 다시 제출하는 구간이 아니라,상대가 방금 바꾼 주장에 답해요.

(다이나믹 논스톱.아래가 한 순환이에요.약점은 【】,다른 발언은 판정 대상이 아니에요.집중·소음 제거는 선택·발사를 대신하지 않아요.)

{dialogue.strip()}

### 입력과 판정

- 선택·발사 언령 한 개: **{evidence}**.
- 선택적 V포인트: 약점 첫 글자 「{weak[1][0]}」 내부 지정점.놓쳐도 정상 약점 정답은 진행해요.
- 정답 판정과 범위: {answer}
- 구체적 오답: {wrong}
- 시간·발언력 전체 실패는 같은 공개 상태로 이 논의를 재개해요.취소·미선택은 정답이 아니에요.

### 오답 반응 → 같은 논의

{wrong_reply.strip()}

(같은 질문으로 돌아가요.오답 때 새로운 목격이나 능력을 얻지 않아요.)

### 정답 → 바뀐 주장에 답한 뒤

{correct.strip()}

(자백·살의·신원 확정은 위에 판정한 범위를 넘기지 않아요.부모의 실제 다음 대면으로 돌아가요.)

'''
    with (ROOT/name).open('a',encoding='utf-8') as h:h.write('\n'+body)
    ledger['entries'].append({'id':ident,'chapter':ch,'kind':'NS','file':name,'parent':parent,'return_first':end,'answer':answer,'success_next':None,'selected_evidence':evidence,'judgment':'refute','vpoint_character':weak[1][0],'vpoint_optional':True})
    ledger['changes'].append({'id':ident,'source':parent,'before_sha256':digest(s),'after_sha256':digest(s[:a]+link+s[b:]),'removed_text':removed,'removed_sha256':digest(removed)})

add_ns(3,11,'13c1_3장_재판_몸의_이름_초고.md',
    '[미오] 이걸로는 못 나눠。'.replace('。','.'),
    '[소라·켄의몸] 질문 참 많이 준비했네.',
    '시연하지 않은 사람의 승리',
    '''[소라·켄의몸] 미오도 안 나오네.그럼 내가 못 했다는 말은 못 하지?

[코토] 못 했다고 확인한 사람은 없어.

[소라·켄의몸] 됐네.【켄이라는 확인은 끝났어】.이번에는 누가 못 믿는 건데.

[린] 미오가 거절한 걸 네가 성공한 걸로 쳐?

[소라·켄의몸] 해 보라던 애들이 다 안 하겠대.다음은 무슨 시험인데.

[나나] 제가 도와드릴 수 있다고 한 말도 시연이 이루어졌다는 뜻은 아니에요.

[미오] 아무도 앞으로 안 갔어.그런데 이름은 언제 확인한 거야?''',
    '현재 재시연 미실시',
    '【켄이라는 확인은 끝났어】를 논파해요.참가자 거절로 시전 자체가 없었으므로 최면의 성공·실패 어느 쪽도 관찰되지 않았어요.시연하지 않은 것을 현재 신원 증명으로 사용할 수 없다는 결론이며,소라라는 반대 신원을 여기서 확정하지 않아요.',
    '상대가 시전하지 않았으니 소라로 바로 확정한다.',
    '''[소라·켄의몸] 내가 안 했다는 말은 들었네.그다음 이름은 네가 쓰고.

[린] 미오.그 이름 쓰려고 네가 앞으로 안 간 건 아니잖아.''',
    '''[미오] 네가 못 했다는 증명은 아니야.성공했다는 증명도 아니고.내가 앞으로 가야만 네가 설명하게 되는 질문은 그만할 거야.

[코토] 조건을 다 맞추면 구별할 수 있을 거라고 생각했어.

[린] 조건에 사람도 넣었잖아.지금 누가 하겠다고 했는데.

[미오] 상대가 하고 싶어 하는지도 우리가 대신 맞출 수 없어.처음에는 같은 조건을 앞뒤로 확인했고,돌아온 뒤에 물었어.지금 또 하게 만들어서 같은 결과를 얻는다고,그 사이에 있었던 모든 일을 다 보는 것도 아니고.''')

add_ns(5,11,'15c2_5장_재판_열었던_손_초고.md',
    '[아카리] 그걸 자기가 골라 놓고 갔을 수도 있잖아.',
    '[미오] 나나가 네 손을 못 본 걸로 코토가 고른 손이 생기지는 않아.',
    '골랐던 손을 지우는 말',
    '''[아카리] 코토가 어느 잔 쓸지 미리 정했으면?나는 그걸 가져갔을 수도 있잖아.

[나나] 저는 새 잔 여섯 개를 씻어서 뒀어요.그런 부탁은 못 들었고요.

[사츠키] 나나가 떠난 뒤는 못 봤지.그건 맞아.

[린] 아카리한테도 물어.아까 자기 손으로 골랐다고 했어.

[아카리] 나는【내가 고르지는 않았어】.시키는 잔만 옮긴 거면 얘기가 달라지잖아.

[쇼] 그건 코토가 뭘 알았느냐 말고,네가 한 일을 바꾸는 말이야.

[사츠키] 아카리.그때 누가 시켰다는 건데.나나한테 말했을 수도 있다는 거 말고.''',
    '아카리의 잔 선택 진술',
    '【내가 고르지는 않았어】를 앞선 본인 선택 진술과 대조해 논파해요.나나의 미목격을 코토의 지정 증거로 바꿀 수 없고,아카리가 자기 선택이라고 말한 사실이 남아요.어떤 잔을 고를지 숨은 부탁이 절대 없었다거나,코토의 내심·독 인지가 확인됐다고 확장하지 않아요.',
    '나나는 공용 포트와 다른 잔이 음성이므로 과거 모든 순간을 보았다고 한다.',
    '''[나나] 제가 떠난 다음에 고르셨어요.보았다고 하시면 제 말도 달라져요.

[아카리] 들었지?나나가 안 봤다는 건 네가 없앨 수 없어.''',
    '''[미오] 네가 골랐다고 했어.지금은 코토가 정했을 수도 있다고 하고.그 사람이 뭘 시켰다는 건지 네가 들은 말부터 해.

[아카리] 너희는 내가 말 바꾸는 것만 기다려.

[사츠키] 지금 바꿨잖아.안 봤다는 사람 말 빌리지 말고 네가 들은 거 말해.

(아카리는 나나를 보지만 나나는 대신 가능성을 완성해 주지 않는다.현재 새 지정 부탁이나 코토의 인지를 사실로 채우지 않는다.)''')

# Repair queues after removing tasks sharing an existing return anchor.
by={e['id']:e for e in ledger['entries']}
retired_by={r['entry']['id']:r['entry'] for r in retired}
for e in ledger['entries']:
    nxt=e.get('success_next')
    if nxt in retired_by:
        # A retired selection has become live dialogue: do not jump past it.
        r=next(r for r in retired if r['entry']['id']==nxt)
        e['return_first']=r['replacement_dialogue'].splitlines()[0]
    while nxt in retired_by:nxt=retired_by[nxt].get('success_next')
    e['success_next']=nxt
    s=(ROOT/e['parent']).read_text(encoding='utf-8')
    if nxt:
        n=by[nxt];t=(ROOT/n['file']).read_text(encoding='utf-8')
        head=re.search(r'^## '+re.escape(nxt)+r' (.+)$',t,re.M)[1]
        slug=re.sub(r'[^\w -]','',(nxt+' '+head).lower()).replace(' ','-')
        tail=f'**정답의 다음 진입:** [{nxt}]({n["file"]}#{slug})을 진행해요.부모 문장을 먼저 읽어 이 과제를 건너뛰지 않아요.'
        e.pop('success_parent_line',None)
    else:
        lines=s.splitlines();matches=[i+1 for i,line in enumerate(lines) if line.startswith(e['return_first'])]
        assert len(matches)==1,(e['id'],e['return_first'],matches)
        e['success_parent_line']=matches[0]
        tail=f'**정답의 다음 진입:** `{e["parent"]}`의 {matches[0]}행,`{e["return_first"]}`부터 이어가요.이 블록의 부모 진입 마커를 다시 실행하지 않아요.'
    f=ROOT/e['file'];t=f.read_text(encoding='utf-8')
    m=re.search(r'^## '+re.escape(e['id'])+r' [^\n]+\n',t,re.M);a=m.start();n=re.search(r'^## ',t[m.end():],re.M);b=m.end()+n.start() if n else len(t)
    block=t[a:b]
    if '**정답의 다음 진입:**' in block:block=re.sub(r'^\*\*정답의 다음 진입:\*\*[^\n]+',lambda m:tail,block,flags=re.M)
    else:block=block.rstrip()+'\n\n'+tail+'\n\n'
    f.write_text(t[:a]+block+t[b:],encoding='utf-8')

names=set(ledger['final_sources'])|{e['file'] for e in ledger['entries']}|{e['parent'] for e in ledger['entries']}
ledger['final_sources']={name:digest((ROOT/name).read_text(encoding='utf-8')) for name in sorted(names)}
ledger['purpose_revision']={'reason':'Scene purpose and unanswered dispute, not unequal-number targets','retired':retired,'new_ids':['T3-NS-A11','T5-NS-A11'],'normal_dialogue_preserved':True}
LP.write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf-8')
changed=[]
for name,s in before.items():
    now=(ROOT/name).read_text(encoding='utf-8')
    if s!=now:changed.append({'file':name,'before_sha256':digest(s),'after_sha256':digest(now)})
(Q/'trial_purpose_changes.json').write_text(json.dumps({'retired_ids':[r['entry']['id'] for r in retired],'new_ids':ledger['purpose_revision']['new_ids'],'source_changes':changed,'original_installation_or_game_data_touched':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'retired':len(retired),'new':2,'active_new_inputs':len(ledger['entries']),'changed_manuscripts':len(changed)},ensure_ascii=False))
