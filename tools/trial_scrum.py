"""논의 스크럼 라운드 늘리기(Claude 2026-11-05, 사양서 25).

까닭 : 스크럼 선택지는 그 스크럼의 라운드 수만큼 나온다(TrialRunner.hpp 902). T5-SD-02·03 은 1라운드라 고를 게 하나뿐이었다.
  V3 논의 스크럼은 한 판에 5~8 대치(위키·영상 A). 인물의 처지대로 주장과 반박을 더 썼다 — 새 사실·정답은 넣지 않는다.
값 : 스테이지 → [(them actor, them 글, keyword, us actor, us 글, responseKeyword, 틀렸을 때 them 의 말)]
결과 : trial_direction.json scrum[스테이지] → TrialRunner.hpp 가 stage.pairs 뒤에 붙인다.
"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
NAME = {'riku': '리쿠', 'yuu': '유우', 'sora': '소라', 'rin': '린', 'koto': '코토', 'akari': '아카리', 'nana': '나나', 'satsuki': '사츠키',
        'rei': '레이', 'sho': '쇼', 'mio': '미오', 'haruka': '하루카', 'taiga': '타이가', 'ken': '켄'}
S = {
 'T4-SD-01': [
  ('koto', '구조가 늦었다면 늦은 사람한테도 책임이 있지 않을까.', '늦은 사람한테도 책임',
   'nana', '저희는 듣자마자 갔어요.늦게 한 게 아니라 늦게 안 거예요.', '늦게 한 것과 늦게 안 것',
   '누가 늦었냐가 아니라 책임을 나누자는 거예요.'),
  ('rei', '제가 닫지 않았어도 결과는 같았을지 모릅니다.', '결과는 같았을지',
   'rin', '같았을지 모른다는 말이 네가 닫은 걸 없애 주진 않아.', '가정과 이미 한 행동',
   '제 말을 그렇게 받으시면 곤란합니다.')],
 'T5-SD-02': [
  ('akari', '잔은 다 똑같았어.누가 어느 잔을 받든 운이었던 거야.', '누가 어느 잔을 받든 운',
   'sho', '모양이 같아도 양성은 코토 잔 하나야.운이었다면 다른 잔에서도 나왔겠지.', '양성이 나온 잔은 하나',
   '운 얘기를 하는 게 아니야. 잔이 같았다는 거지.'),
  ('satsuki', '나나가 씻었으면 나나가 넣을 수도 있었잖아.', '나나가 넣을 수도',
   'mio', '씻을 때는 어느 잔이 누구 건지 정해지지 않았어.고른 건 그 뒤야.', '잔이 정해지기 전',
   '누가 손댔냐를 묻는 거야.'),
  ('akari', '난 아무 잔이나 들고 갔을 뿐이야.고른 게 아니라고.', '고른 게 아니라고',
   'rin', '아까 네 입으로 직접 골랐다고 했어.그 말은 남아.', '아카리가 직접 골랐다는 말',
   '그건 그냥 말이 그렇게 나온 거야.')],
 'T5-SD-03': [
  ('akari', '코토가 자기 잔을 정했으면 코토가 다 계획한 거야.', '코토가 다 계획한 거',
   'rin', '잔을 정한 것과 그 안에 뭘 넣은 건 달라.넣은 손을 묻는 거야.', '잔을 정한 것과 넣은 손',
   '계획한 사람이 제일 나쁜 거 아니야?'),
  ('satsuki', '마신 사람이 아무 말 안 했으면 알고 마신 거야.', '알고 마신 거',
   'nana', '말씀이 없으셨다고 아셨다는 뜻은 아니에요.몰라도 말은 안 할 수 있어요.', '침묵과 앎의 구별',
   '말 안 했다는 게 중요하다고.'),
  ('akari', 'D는 누구나 열 수 있었어.나만 의심할 이유 없잖아.', '누구나 열 수 있었어',
   'sho', '열 수 있었던 사람과 열었다는 기록이 남은 사람은 달라.', '가능성과 남은 기록',
   '기록이 다 맞는다는 보장은 없잖아.')],
}


def main():
    tasks = json.loads((ROOT / 'data/v4_story/native_tasks.json').read_text(encoding='utf-8'))['tasks']
    p = ROOT / 'data/v4_story/trial_direction.json'
    d = json.loads(p.read_text(encoding='utf-8'))
    out, n = {}, 0
    for sid, rows in S.items():
        st = tasks[sid]['stage']; assert st['kind'] == 'scrum'
        base = len(st['pairs']); out[sid] = []
        for m, (ta, tt, kw, ua, ut, rk, wrong) in enumerate(rows, 1):
            assert kw.replace('.', '') in tt.replace('.', '') or kw in tt, (sid, kw)
            pid = f'{sid}:round:claude{base + m}'
            out[sid].append({'id': pid, 'them': NAME[ta], 'themActor': ta, 'themText': tt, 'keyword': kw,
                             'us': NAME[ua], 'usActor': ua, 'usText': ut, 'responseKeyword': rk,
                             'wrong': [{'type': 'say', 'speaker': NAME[ta], 'actor': ta, 'text': wrong, 'mono': False, 'delivery': NAME[ta], 'id': pid + ':wrong'}]})
            n += 1
    d['scrum'] = out
    text = json.dumps(d, ensure_ascii=False, indent=1) + '\n'
    p.write_text(text, encoding='utf-8')
    (ROOT / 'Game/Assets/Data/v4_story/trial_direction.json').write_text(text, encoding='utf-8')
    print('scrum rounds', n, {k: len(v) for k, v in out.items()})


if __name__ == '__main__':
    main()
