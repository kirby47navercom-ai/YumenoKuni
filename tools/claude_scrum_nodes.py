"""논의 스크럼 V3 화면 위젯 Game/Assets/UI/ScrumV3.hbwidget.json (UI id "scv3") — Claude 2026-11-06, 사양서 27a.
노드 틀은 ShowdownV3 위젯의 그림(SdV3Dim)·글(SdV3KataT0) 노드를 본뜬다.
그림 : Game/Assets/Art/ui/v3_scrum/ (tools/v3_scrum_assets.py, V3·한국어판 UI 주인님 허락 2026-10-29)
"""
import copy, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'Game/Assets/UI/ShowdownV3.hbwidget.json'
OUT = ROOT / 'Game/Assets/UI/ScrumV3.hbwidget.json'
V = 'Assets/Art/ui/v3_scrum/'


def main():
    w = json.loads(SRC.read_text(encoding='utf-8')); nodes = w['nodes']
    img = next(n for n in nodes if n['id'] == 'SdV3Dim'); txt = next(n for n in nodes if n['id'] == 'SdV3KataT0')
    root = copy.deepcopy(next(n for n in nodes if n['parent'] == '')); root['properties']['visible'] = True
    keep = [root]

    def add(base, nid, rect, texture='', z=40, extra=None):
        n = copy.deepcopy(base); n['id'] = n['name'] = nid; n['parent'] = root['id']
        n['slot']['offset'] = rect; n['slot']['zIndex'] = z
        n['properties'].update({'texture': texture, 'visible': False, 'imageFit': 'contain', 'rotation': 0, 'opacity': 1})
        if extra: n['properties'].update(extra)
        keep.append(n)
    add(img, 'ScDim', [0, 0, 1280, 720], 'Assets/Art/ui/v3_hr/black.webp', 20, {'imageFit': 'fill'})
    add(img, 'ScLockBg', [0, 0, 1280, 720], 'Assets/Art/ui/v3_hr/black.webp', 18, {'imageFit': 'fill'})
    add(img, 'ScLock', [0, 0, 1280, 720], V + 'lock/0001.webp', 19, {'imageFit': 'fill'})
    add(img, 'ScLockPre', [0, 0, 2, 2], V + 'lock/0001.webp', 17, {'imageFit': 'fill'})  # 다음 장을 미리 읽어 둔다  # 열쇠·원판 장면(tools/blender_scrum_lock.py, 78장 30fps)
    # 1. 「의견대립」(영상 1번 4.5~7.5초) : 의(파랑 칸)·견·대(먹)·립(분홍 칸) 세로, 번개 금
    for i, t in enumerate(['t_scrum_cutin_l_tx_000', 't_scrum_cutin_s_tx_000', 't_scrum_cutin_l_tx_001', 't_scrum_cutin_s_tx_001']):
        add(img, f'ScOp{i}', [0, 0, 180, 180], V + t + '.webp', 52)
    for i in range(4):
        add(img, f'ScHibi{i}', [0, 0, 400, 400], V + f't_scrum_cutin_hibi_00{i % 2}.webp', 51)
    # 2. 주제·두 팀(33.5~39.5초) : 가운데 주제 글, 아래 붉은·푸른 띠 + 팀 주장, 가운데 문양
    add(img, 'ScTopicBand', [0, 0, 1280, 120], V + 't_scrum_check_bg_000.webp', 44, {'imageFit': 'fill'})
    add(txt, 'ScTopic', [0, 0, 1180, 70], '', 45, {'fontSize': 46, 'color': '#ffffff', 'text': '', 'align': 'center'})
    for s, c in (('L', 'l'), ('R', 'r')):  # V3 t_scm_team_pl : 붉은(왼쪽)·푸른(오른쪽) 물고기 모양 띠 + 테
        add(img, f'ScArrow{s}', [0, 0, 680, 105], V + f't_scm_team_pl_{c}_000.webp', 46, {'imageFit': 'fill'})
        add(img, f'ScArrowTail{s}', [0, 0, 680, 105], V + f't_scm_team_pl_{c}_frame_ef.webp', 46, {'imageFit': 'fill'})
        add(txt, f'ScArrowT{s}', [0, 0, 520, 40], '', 47, {'fontSize': 24, 'color': '#ffffff', 'text': '', 'align': 'center'})
    add(img, 'ScEmblem', [0, 0, 150, 150], V + 't_scm_topic_fl_bg_000.webp', 48)  # V3 t_scm_topic_fl : 십각 판 + 분홍·파랑 날개 + 테
    add(img, 'ScEmblemDecoL', [0, 0, 150, 150], V + 't_scm_topic_fl_deco_left.webp', 49)
    add(img, 'ScEmblemDecoR', [0, 0, 150, 150], V + 't_scm_topic_fl_deco_right.webp', 49)
    add(img, 'ScEmblemFrame', [0, 0, 150, 150], V + 't_scm_topic_fl_line_000.webp', 49)
    add(txt, 'ScEmblemT', [0, 0, 120, 50], '', 50, {'fontSize': 34, 'color': '#ffffff', 'text': '', 'align': 'center'})
    # 3. 「논의 스크럼 시작」(40.3~42초)
    add(img, 'ScStartEf', [0, 0, 560, 90], V + 't_scrum_start_tx_ef.webp', 53)
    add(img, 'ScStart', [0, 0, 520, 80], V + 't_scrum_start_tx.webp', 54)
    add(img, 'ScStartLine', [0, 0, 1280, 18], V + 't_scrum_start_line_tail_bl.webp', 52, {'imageFit': 'fill'})
    # 4. 진행 : 시간판(위 가운데) · 큰 발언 글
    add(img, 'ScTimeBase', [0, 0, 340, 64], V + 't_time_base_l_000.webp', 46, {'imageFit': 'fill'})
    add(img, 'ScTimeIco', [0, 0, 40, 40], V + 't_time_ico_play.webp', 47)
    for i in range(9):
        add(img, f'ScTimeD{i}', [0, 0, 30, 40], V + 't_time_num_000.webp', 47)
    add(img, 'ScHit', [0, 0, 1280, 160], V + 't_scrum_push_line_l_rd.webp', 47, {'imageFit': 'fill'})
    # 5. 확인 · 「잠깐!」
    add(img, 'ScCheckBg', [0, 0, 1280, 90], V + 't_scrum_check_bg_000.webp', 55, {'imageFit': 'fill'})
    add(img, 'ScCheck', [0, 0, 380, 60], V + 't_scrum_check_tx_000.webp', 56)
    add(img, 'ScMattaBg', [0, 0, 1280, 720], V + 't_scrum_bg.webp', 57, {'imageFit': 'fill'})
    add(img, 'ScMattaEf', [0, 0, 1280, 720], V + 't_scrum_ef.webp', 58, {'imageFit': 'fill'})
    for i, t in enumerate(['t_scrum_pl_000_000', 't_scrum_pl_000_001', 't_scrum_pl_001_000', 't_scrum_pl_001_001']):
        add(img, f'ScMattaPl{i}', [0, 0, 300, 600], V + t + '.webp', 59)
    add(img, 'ScMattaChara', [0, 0, 520, 620], 'Assets/Art/ui/v3_hr/black.webp', 60)
    add(img, 'ScMattaTxEf', [0, 0, 560, 300], V + 't_scrum_matta_ef_tx.webp', 61)
    add(img, 'ScMattaTx', [0, 0, 520, 280], V + 't_scrum_matta_tx.webp', 62)
    # 6. 밀기 : CROUCH · BIND · SET! + 단추
    add(img, 'ScPushPl', [0, 0, 1280, 180], V + 't_scrum_push_cutin_pl.webp', 63, {'imageFit': 'fill'})
    for nid, t in (('ScCrouch', 't_scrum_push_cutin_l_tx_000'), ('ScBind', 't_scrum_push_cutin_s_tx_000'), ('ScSetEf', 't_scrum_push_cutin_go_ef_tx_000'), ('ScSet', 't_scrum_push_cutin_go_tx_000')):
        add(img, nid, [0, 0, 640, 160], V + t + '.webp', 64)
    add(img, 'ScJet', [0, 0, 520, 520], V + 't_scm_jet_ef_ray_l_000.webp', 61)  # 141.5초 : 미는 쪽 화면 끝 보라 분사(t_scm_jet_ef)
    add(img, 'ScBtnEf', [0, 0, 260, 260], V + 't_scrum_push_button_ef_000.webp', 65)
    add(img, 'ScBtnRing', [0, 0, 200, 200], V + 't_scrum_push_button_ef_001.webp', 65)
    add(img, 'ScBtn', [0, 0, 128, 128], V + 't_scrum_push_button_circle_win.webp', 66)
    add(img, 'ScPushTx', [0, 0, 200, 70], V + 't_scrum_push_tx_000.webp', 66)
    for i in range(6):
        add(img, f'ScPushLine{i}', [0, 0, 120, 260], V + 't_scrum_push_line_l_bl.webp', 62)
    w2 = {**w, 'nodes': keep}
    # 진행 중 말하는 사람 판(V3 : 어두워진 법정 위에 2D 큰 인물, 발언 글은 인물 뒤) — UI id "scv3cut", scrumv4·scv3 보다 아래에 먼저 띄운다
    keep2 = [copy.deepcopy(root)]
    def add2(base, nid, rect, texture, z, extra=None):
        n = copy.deepcopy(base); n['id'] = n['name'] = nid; n['parent'] = root['id']; n['slot']['offset'] = rect; n['slot']['zIndex'] = z
        n['properties'].update({'texture': texture, 'visible': False, 'imageFit': 'fill', 'rotation': 0, 'opacity': 1});
        if extra: n['properties'].update(extra)
        keep2.append(n)
    add2(img, 'ScBgDim', [0, 0, 1280, 720], 'Assets/Art/ui/v3_hr/black.webp', 10)
    add2(img, 'ScClaim', [0, 0, 700, 330], 'Assets/Art/ui/v3_hr/black.webp', 20, {'imageFit': 'contain'})
    add2(img, 'ScCut0', [0, 0, 800, 2460], 'Assets/Art/ui/v3_hr/black.webp', 30)
    add2(img, 'ScCut1', [0, 0, 800, 2460], 'Assets/Art/ui/v3_hr/black.webp', 31)
    (ROOT / 'Game/Assets/UI/ScrumV3Cut.hbwidget.json').write_text(json.dumps({**w, 'nodes': keep2}, ensure_ascii=False, indent=1), encoding='utf-8')
    OUT.write_text(json.dumps(w2, ensure_ascii=False, indent=1), encoding='utf-8'); print(len(keep), 'nodes ->', OUT)


if __name__ == '__main__':
    main()
