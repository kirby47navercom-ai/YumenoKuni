"""논스톱 함정 약점(노랑)·동의점(파랑) — 논의마다 직접 고른 자리(Claude 2026-11-04, 사양서 25).

근거 : V3 원본 대사 STX 색 태그(v3_re/script_analysis/decoded/partition_data_win_us/wrd_script/003/chap*_text_US/c0?_2??_00?.stx.json.gz)
  * 논스톱 86개 : 노란 약점(cltWEAK) 자리 1곳 26·2곳 22·3곳 6·4곳 8 …, 평균 2.7 — 정답 하나에 함정이 섞인다.
  * 노랑이 붙는 말 : 상대 주장 속 짧은 핵심 명사구(sliding door·hidden door·rolled-up projector screen·alibi·receiver·intervals)
    또는 짧은 주장(secretly moved it·rejoin everyone).
  * 파랑(cltAGREE) : 86개 중 57개는 없음. 있으면 본 사실·증언(hit his head on the bookcase·never went to the library·corpse moved).
값 : 과제 → [(발언 번호, 'weak'|'agree', 그 줄의 글자 그대로)]. 정답 약점 줄·미오·래피 줄은 고르지 않았다.
정답이 없으므로 어느 언령으로 쏴도 틀린다(Yumeno.cpp decoy). trial_direction_ch*.py 의 save() 뒤에 다시 돌린다.
"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
W, A = 'weak', 'agree'
PICK = {
 'T1-NS-A01': [(0, W, '바닥도 젖어'), (3, W, '가구')],
 'T1-NS-A02': [(0, W, '얼음'), (3, W, '막으려던')],
 'T1-NS-A03': [(1, W, '얼음부터 시작한 순서')],
 'T1-NS-A05': [(3, W, '기다리기 시작한 때'), (4, A, '합류한 때')],
 'T1-NS-A06': [(0, W, '전화가 급했지'), (2, W, '다음 사람')],
 'T1-NS-A07': [(1, W, '같이 한 일'), (3, A, '합류 시각이 다릅니다')],
 'T1-NS-A08': [(0, W, '상표'), (2, W, '다시 뽑으면')],
 'T1-NS-A09': [(0, W, '낮부터 나눠 가진 종이')],
 'T1-NS-A10': [(1, W, '안쪽도 본 거'), (0, W, '표찰')],
 'T1-PN-A02': [(3, W, '도우러 갔을')],
 'T1-PN-A03': [(0, W, '원래 고장 난 쪽'), (4, A, '확인하지 못했다는 기록')],
 'T1-NS-T05e': [(5, W, '처음에 안에 있던 사람')],
 'T1-PD-01': [(0, W, '둘 중에 하나')],
 'T1-LIE-01': [(2, W, '현장 갔다 왔잖아')],
 'T2-NS-A01': [(4, W, '추 같은 거')],
 'T2-NS-A02': [(1, W, '들어갈 크기'), (5, A, '밖의 걸쇠가 닫혀')],
 'T2-NS-A03': [(0, W, '받침대 닦다가')],
 'T2-NS-A04': [(2, W, '반대쪽')],
 'T2-NS-A05': [(0, W, '돌아오는 길'), (3, A, '닫힌 채로 받았어요')],
 'T2-NS-A06': [(0, W, '다른 문은 비었겠네'), (3, W, '아무 길')],
 'T2-NS-A07': [(0, W, '리쿠 혼자 카드')],
 'T2-NS-A08': [(0, W, '다 녹음'), (1, A, '직접 부른 것')],
 'T2-NS-A09': [(0, W, '주웠을'), (1, W, '같은 고리')],
 'T2-NS-A10': [(0, W, '받침대'), (2, A, '열었을 땐 없었어')],
 'T2-PN-A02': [(4, W, '얼굴도 못 봤을')],
 'T2-PN-A03': [(0, W, '카드 가져간 뒤')],
 'T2-LIE-01': [(0, W, '계속 들렸다며')],
 'T2-PD-01': [(2, W, '끝까지 몰랐다고')],
 'T2-NS-01': [(2, W, '같은 거')],
 'T3-NS-A01': [(0, W, '거울을 잘못 봤으면'), (2, A, '상대 눈을 바꾸는 경우')],
 'T3-NS-A02': [(0, W, '손잡이')],
 'T3-NS-A03': [(2, W, '내가 켄인 거지')],
 'T3-NS-A04': [(0, W, '쇼가 살리지 못했지'), (1, A, '소라는 살아 있었어')],
 'T3-NS-A05': [(1, W, '반대 손')],
 'T3-NS-A06': [(1, W, '같은 머리')],
 'T3-NS-A07': [(0, W, '몰래 알려 줬을'), (4, W, '가방')],
 'T3-NS-A08': [(0, W, '되돌리면 안 남겠네')],
 'T3-NS-A09': [(0, W, '나나가 지웠으면'), (1, A, '손댐을 받은 건')],
 'T3-NS-A10': [(1, W, '나중에 바뀌었다는')],
 'T3-NS-A11': [(0, W, '미오도 안 나오네'), (4, W, '다 안 하겠대')],
 'T3-PN-A02': [(0, W, '어디 갔는지 못 봤어')],
 'T3-PN-A03': [(0, W, '힘 빠졌잖아'), (2, A, '계속 저항했고')],
 'T3-NS-01': [(3, W, '켄 몸을 봤는데')],
 'T3-PN-01': [(0, A, '저녁7시40분')],
 'T4-NS-A01': [(1, W, '안쪽에서 새로 한 일')],
 'T4-NS-A02': [(1, W, '그 사이 손댄 사람')],
 'T4-NS-A03': [(0, W, '머리에도 상처'), (1, A, '제가 봤어요')],
 'T4-NS-A04': [(0, W, '자기가 했을 가능성')],
 'T4-NS-A05': [(0, W, '힘을 썼을'), (2, W, '원거리의 상태')],
 'T4-NS-A06': [(0, W, '구조를 아는 것')],
 'T4-NS-A07': [(1, W, '문이 여러 개'), (2, A, '안쪽 문인지 다시 물으셨어요')],
 'T4-NS-A08': [(0, W, '원래 있던 방'), (2, W, '친숙함')],
 'T4-NS-A09': [(0, W, '그림자'), (4, A, '벤치에 같이 앉아 있었어')],
 'T4-NS-A10': [(0, W, '더 일찍 되감았다면')],
 'T4-PN-A02': [(1, W, '그 상처')],
 'T4-PN-A03': [(1, W, '입구는 비었겠네'), (2, A, '사츠키가 밖에 있었어')],
 'T4-NS-01': [(0, W, '덮개가 닫혔을'), (3, W, '자기가 닫았다고 기억한')],
 'T4-PN-01': [(0, W, '되감은 뒤의 자리')],
 'T4-LIE-01': [(1, W, '나중 발견')],
 'T5-NS-A01': [(0, W, '내가 손댄 건')],
 'T5-NS-A02': [(0, W, 'D 내가 갖고 있었어'), (3, A, '죽고 난 뒤야')],
 'T5-NS-A03': [(0, W, '빈잔 가져온 건')],
 'T5-NS-A04': [(1, W, '치우려고 가져온 잔'), (2, A, '그 뒤 쓰러졌어')],
 'T5-NS-A05': [(0, W, '한 일도 남는 거고')],
 'T5-NS-A06': [(0, W, '더 전에 했어'), (3, A, '몸은 한 군데 있었고')],
 'T5-NS-A07': [(0, W, '자기 글만 골라 쓰고'), (1, W, '믿을 이유')],
 'T5-NS-A08': [(0, W, '딴 데 볼 때'), (4, A, '창가에 있던 건')],
 'T5-NS-A09': [(0, W, '기억 지운 사람'), (2, W, '나나 혼자 한 말')],
 'T5-NS-A10': [(1, W, '병 열고 닫는 건')],
 'T5-NS-A11': [(0, W, '미리 정했으면'), (2, A, '나나가 떠난 뒤는 못 봤지')],
 'T5-PN-A02': [(0, W, '바깥 상자')],
 'T5-PN-A03': [(0, W, '미리 다 넣었을')],
 'T5-NS-01': [(2, W, '물건도 내 손에')],
 'T5-PN-01': [(0, W, '얼굴 바꿀 수')],
 'T5-LIE-01': [(0, W, '나나가 먼저 썼다면')],
 'T6-NS-A01': [(0, W, '사실까지 고친')],
 'T6-NS-A03': [(0, W, '서류 고치는 일')],
 'T6-NS-A04': [(0, W, '늦게 전했어')],
 'T6-NS-A05': [(0, W, '혼자라는 요약')],
 'T6-NS-A06': [(0, W, '통로 쪽으로 둘이')],
 'T6-NS-A07': [(0, A, '이미 손을 잡고 다닌 뒤')],
 'T6-NS-A08': [(0, W, '코토하고 맺은 약속')],
 'T6-NS-A09': [(0, W, '처음부터 맞았다는')],
 'T6-NS-A10': [(0, W, '원래 있던 것처럼'), (1, W, '수 안 맞는 건')],
 'T6-PN-A02': [(1, W, '일정 정한 사람')],
 'T6-PN-A03': [(1, W, '원래 다 죽이는')],
 'T6-PD-01': [(1, W, '쟤 혼자 문서도')],
 'T6-NS-01': [(0, W, '코토 아버지')],
}

# Supported-looking statements that are true only in a narrower context, or
# whose observation is not established by the similarly named evidence.
BLUE = {
 'T2-NS-A03': (3, '그 손을 언제 봤는지'),
 'T2-NS-A04': (1, '이쪽 문으로 나온 건 못 봤어'),
 'T2-NS-A07': (3, '함이 우리 쪽에 있었어'),
 'T2-NS-A09': (4, '부러진 두 끝을 비교한 기록'),
 'T3-NS-A02': (3, '사진 찍은 때하고 미오가 본 때는 달라'),
 'T3-NS-A07': (3, '두 분이 이미 나가셨어요'),
 'T3-NS-A10': (4, '전후도 계속 보고 있었어요'),
 'T3-NS-A11': (1, '못 했다고 확인한 사람은 없어'),
 'T4-NS-A02': (3, '이미 물 안에 갇혀 있었어'),
 'T4-NS-A04': (5, '발견한 고정 상태는 수사에서 확인했어'),
 'T4-NS-A05': (6, '힘은 듣는 거잖아'),
 'T4-NS-A06': (3, '사진과 관찰은 같은 게 아니에요'),
 'T4-NS-A08': (4, '사진을 새로 찍은 건 아니야'),
 'T4-NS-A10': (4, '최초 구조 때 제가 본 구간'),
 'T5-NS-A01': (3, '첫째 했다는 걸로 둘째까지 고르는 건 아니야'),
 'T5-NS-A05': (3, '보호한 게 어느 문장'),
 'T6-NS-A01': (3, '말을 막던 조건과 말의 내용은 따로야'),
 'T6-NS-A10': (2, '친숙함은 모두에게 작용해요'),
 'T2-NS-01': (1, '자른 뒤의 축을 봤다고'),
 'T4-NS-01': (2, '덮개를 내린 것은 저'),
 'T2-LIE-01': (1, '소리는 들었어'),
 'T4-LIE-01': (2, '사진보다 먼저 제가 손을 봤어요'),
 'T5-LIE-01': (3, '새 잔 여섯 개를 씻었어요'),
 'T6-LIE-01': (2, '여기서는 같이 확인하시잖아요'),
}

def apply_chapter_progression(d, tasks):
    for tid, (i, word) in BLUE.items():
        rows = tasks[tid]['debate']['lines'] + d.get('extra', {}).get(tid, [])
        matches = [row for row in rows if row.get('kind', 'plain') == 'plain' and word in row['text']]
        assert len(matches) == 1, (tid, i, word)
        line = matches[0]
        d['debate'].setdefault(line['id'], {})['decoy'] = {'kind': A, 'word': word}
    sixth_lie = tasks['T6-LIE-01']['debate']['lines'][1]
    word = '안에서 하나로 정해 주겠다는'
    assert sixth_lie['kind'] == 'plain' and word in sixth_lie['text']
    d['debate'].setdefault(sixth_lie['id'], {})['decoy'] = {'kind': W, 'word': word}
    for tid, task in tasks.items():
        if not tid.startswith('T1-') or task.get('stage', {}).get('kind') != 'nonstop':
            continue
        for line in task['debate']['lines'] + d.get('extra', {}).get(tid, []):
            entry = d['debate'].get(line['id'], {})
            if entry.get('decoy', {}).get('kind') == A:
                entry['decoy']['kind'] = W
    # Preserve the evidence and the next authored dialogue. Change the claim
    # the player must answer from support to refutation in the tutorial chapter.
    row = next(l for l in tasks['T1-NS-A03']['debate']['lines'] if l['kind'] == A)
    d['debate'][row['id']]['openingRefutation'] = {
        'text': '문 동작 순서는 기록에 없어.',
        'word': '기록에 없어',
    }


def main():
    tasks = json.loads((ROOT / 'data/v4_story/native_tasks.json').read_text(encoding='utf-8'))['tasks']
    p = ROOT / 'data/v4_story/trial_direction.json'
    d = json.loads(p.read_text(encoding='utf-8'))
    for e in d['debate'].values():
        e.pop('decoy', None)
    counts = {W: 0, A: 0}; bad = []
    for tid, picks in PICK.items():
        lines = (tasks.get(tid, {}).get('debate') or {}).get('lines', [])
        for i, kind, word in picks:
            if i >= len(lines) or lines[i].get('kind') != 'plain' or word not in lines[i]['text'] or lines[i]['id'] not in d['debate']:
                bad.append((tid, i, word)); continue
            d['debate'][lines[i]['id']]['decoy'] = {'kind': kind, 'word': word}; counts[kind] += 1
    text = json.dumps(d, ensure_ascii=False, indent=1) + '\n'
    p.write_text(text, encoding='utf-8')
    print('yellow', counts[W], 'blue', counts[A], 'debates', len(PICK), 'bad', bad)

if __name__ == '__main__':
    main()
