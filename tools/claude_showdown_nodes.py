"""반론 쇼다운 V3 HUD 위젯 Game/Assets/UI/ShowdownV3.hbwidget.json 을 만든다(Claude 2026-11-05, 사양서 26).
Stage 위젯은 이미 255노드라 위젯 한도(256, prototype/ui-assets.js validWidgetAsset)에 걸려 따로 띄운다(UI id "sdv3").
노드 틀은 Stage 의 SdDivider·BladeName 을 본뜬다. create-project 뒤에도 그대로 남는다.
그림 : Game/Assets/Art/ui/v3_hr/ (주인님 허락 V3·한국어판 UI, 2026-10-29) — 시작 글자·장식·칼날 목록·칼 커서·띠·Advance·SLASH.
"""
import copy, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
P = ROOT / 'Game/Assets/UI/Stage.hbwidget.json'
OUT = ROOT / 'Game/Assets/UI/ShowdownV3.hbwidget.json'


def main():
    w = json.loads(P.read_text(encoding='utf-8'))
    nodes = w['nodes']
    img = next(n for n in nodes if n['id'] == 'SdDivider')
    txt = next(n for n in nodes if n['id'] == 'BladeName')
    root = copy.deepcopy(next(n for n in nodes if n['parent'] == '')); root['properties']['visible'] = True
    keep = [root]
    if any(n['id'].startswith('SdV3') for n in nodes): P.write_text(json.dumps({**w, 'nodes': [n for n in nodes if not n['id'].startswith('SdV3')]}, ensure_ascii=False, indent=1), encoding='utf-8')  # Stage 에 넣었던 것은 걷어낸다

    def add(base, nid, rect, texture='', z=40, extra=None):
        n = copy.deepcopy(base); n['id'] = n['name'] = nid; n['parent'] = root['id']
        n['slot']['offset'] = rect; n['slot']['zIndex'] = z
        n['properties'].update({'texture': texture, 'visible': False, 'imageFit': 'contain', 'rotation': 0, 'opacity': 1})
        if extra: n['properties'].update(extra)
        keep.append(n)
    V = 'Assets/Art/ui/v3_hr/'
    for i in range(7):  # 한국어판 제목 「반론 / 쇼다운 / 진타」(Uba6XjXj8OU 3089~3090초)
        add(img, f'SdV3TitleEf{i}', [0, 0, 220, 230], V + f'title_{i}_ef.webp', 41)
        add(img, f'SdV3Title{i}', [0, 0, 150, 160], V + f'title_{i}.webp', 42)
    add(img, 'SdV3DecoL', [0, 0, 260, 260], V + 'deco_ring_orange.webp', 39)
    add(img, 'SdV3DecoR', [0, 0, 300, 300], V + 'deco_ring_blue.webp', 39)
    add(img, 'SdV3Sakura', [0, 0, 120, 120], V + 'deco_sakura.webp', 39)
    add(img, 'SdV3Start0', [0, 0, 220, 270], V + 'start_0.webp', 43)
    add(img, 'SdV3Start1', [0, 0, 250, 270], V + 'start_1.webp', 43)
    for i in range(6):
        add(img, f'SdV3Kata{i}', [0, 0, 470, 99], V + 'katana_sheathed.webp', 44, {'imageFit': 'fill'})
        add(txt, f'SdV3KataT{i}', [0, 0, 300, 30], '', 45, {'fontSize': 20, 'color': '#ffffff', 'text': '', 'align': 'left'})
    add(img, 'SdV3Arc', [0, 0, 700, 392], V + 'pointer_arc.webp', 31)
    add(img, 'SdV3Pointer', [0, 0, 156, 48], V + 'pointer_ico.webp', 32)
    add(img, 'SdV3Band', [0, 0, 40, 720], V + 'band_danger.webp', 33, {'imageFit': 'fill'})
    add(img, 'SdV3Adv', [0, 0, 820, 276], V + 'advance.webp', 46)
    add(img, 'SdV3SlashN', [0, 0, 90, 128], V + 'slash_2.webp', 46)
    add(img, 'SdV3SlashT', [0, 0, 180, 92], V + 'slash_tx.webp', 46)
    # 마무리 「참격」(V3 t_hr_break, 영상 Hs3Y7uyOAQk 194.5~196.6초) — tools/v3_hr_break_assets.py
    add(img, 'SdV3BrkDim', [0, 0, 1280, 720], V + 'break_dim.webp', 60, {'imageFit': 'fill'})
    add(img, 'SdV3BrkHit', [0, 0, 512, 512], V + 'break_hit.webp', 61)
    add(img, 'SdV3BrkLine', [0, 0, 1600, 100], V + 'break_line.webp', 62, {'imageFit': 'fill'})
    add(img, 'SdV3BrkCircle', [0, 0, 520, 520], V + 'break_circle.webp', 62)
    add(img, 'SdV3BrkSlash', [0, 0, 560, 560], V + 'break_slash.webp', 63)
    add(img, 'SdV3BrkTx', [0, 0, 520, 520], V + 'break_tx.webp', 64)
    for i in range(8):  # 「시작」 둘레 벚꽃·꽃잎(3091초)
        add(img, f'SdV3Petal{i}', [0, 0, 60, 60], V + ('deco_sakura.webp' if i < 3 else 'petal.webp'), 43)
    for i, c in enumerate(['st_line', 'st_line', 'line_red', 'line_pink', 'line_orange', 'line_yellow']):  # 칼선(3090.6초 파랑 한 줄, 3092.5~3093초 여러 색 여러 줄)
        add(img, f'SdV3Line{i}', [0, 0, 40, 1500], V + c + '.webp', 44, {'imageFit': 'fill'})
    add(img, 'SdV3ListRing', [0, 0, 640, 640], V + 'deco_ring_blue.webp', 40)  # 칼날 목록 뒤 큰 수국(3095.6초)
    add(img, 'SdV3Streak', [0, 0, 70, 1700], V + 'st_line.webp', 66, {'imageFit': 'fill'})  # 3160.8초 : 진실의 칼날 흰 칼줄기
    add(img, 'SdV3HitRing', [0, 0, 400, 400], V + 'hit_ring.webp', 47)  # 보통 베기 : 별빛(SdV3BrkHit) + 파란 원
    add(img, 'SdV3Dim', [0, 0, 1280, 720], V + 'white.webp', 30, {'imageFit': 'fill'})  # 3088.6~3093 제목 동안 화면 어둡게(글자보다 아래)
    for i in range(2):  # 3159.8초 : 칼을 뽑으면 약점 글자에 붉은 X
        add(img, f'SdV3X{i}', [0, 0, 150, 34], V + 'white.webp', 48, {'imageFit': 'fill'})
    for i in range(10):  # 3159.9초 : 칼을 뽑은 동안 바탕에 흐린 「정신집중」 글자가 깔린다
        add(txt, f'SdV3Zen{i}', [0, 0, 420, 110], '', 31, {'fontSize': 84, 'color': '#d8fff2', 'text': '', 'align': 'left'})
    add(img, 'SdV3CutDim', [0, 0, 1280, 720], V + 'break_dim.webp', 76, {'imageFit': 'fill'})  # 2937.8~2938.6 깨진 뒤 검게
    # 상대 「반론」 컷인(2934.6~2937.8초)
    add(img, 'SdV3CiBg', [0, 0, 1000, 720], V + 'hanron_bg.webp', 70, {'imageFit': 'fill'})
    add(img, 'SdV3CiEf', [0, 0, 1000, 720], V + 'hanron_ef.webp', 71, {'imageFit': 'fill'})
    add(img, 'SdV3CiPl', [0, 0, 700, 700], V + 'hanron_pl.webp', 72)
    add(img, 'SdV3CiFace', [0, 0, 640, 720], '', 73)
    add(img, 'SdV3CiTx0', [0, 0, 200, 200], V + 'title_0.webp', 74)  # 한국어판 붓글씨 「반」(t_hanron_start_JP)
    add(img, 'SdV3CiTx1', [0, 0, 200, 200], V + 'title_1.webp', 74)  # 「론」
    add(img, 'SdV3CiBurst', [0, 0, 1280, 1280], V + 'crack_burst.webp', 75)
    add(img, 'SdV3AdvLine', [0, 0, 1400, 90], V + 'advance_line.webp', 45, {'imageFit': 'fill'})
    add(img, 'SdV3VMark', [0, 0, 300, 400], V + 'v_mark.webp', 65)
    for i in range(4):  # 벨 때마다 「+0.2 sec.」(3126.8초)
        add(txt, f'SdV3Bonus{i}', [0, 0, 200, 32], '', 47, {'fontSize': 24, 'color': '#ffe14a', 'text': '', 'align': 'left'})
    # 시간판(한국어판 3105.6초 오른쪽 아래, V3 t_time) · 꽃 커서(t_hr_zan_pointer_ico)
    add(img, 'SdV3TimeBase', [960, 652, 310, 44], V + 'time_base.webp', 35, {'imageFit': 'fill'})
    for i in range(9):
        add(img, f'SdV3TimeD{i}', [0, 660, 40, 40], V + 'time_0.webp', 36)
    add(img, 'SdV3Flower', [0, 0, 96, 96], V + 'pointer_flower.webp', 31)
    # V3 영상 175초 : Advance 뒤 주인공 발언은 대화창 없이 주인공 화면 가득 하늘색 큰 글
    for i in range(16):  # 한국어판 3115.6~3117.2초 : 주인공 반박은 낱말마다 크게(뜻)·작게(조사) 하늘색으로 흐른다
        add(txt, f'SdV3TW{i}', [0, 0, 700, 80], '', 50, {'fontSize': 52, 'color': '#8ff7ff', 'text': '', 'align': 'left'})
        add(txt, f'SdV3TP{i}', [0, 0, 200, 44], '', 50, {'fontSize': 26, 'color': '#8ff7ff', 'text': '', 'align': 'left'})
    OUT.write_text(json.dumps({**w, 'name': 'W_ShowdownV3', 'nodes': keep}, ensure_ascii=False, indent=1), encoding='utf-8')
    print('nodes', len([n for n in keep if n['id'].startswith('SdV3')]))


if __name__ == '__main__':
    main()
