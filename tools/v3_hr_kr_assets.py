"""반론 쇼다운 한국어판 그림 — Claude 2026-11-05, 사양서 26.
근거 : 주인님이 준 한국어판 V3 영상(유튜브 Uba6XjXj8OU 2929~3168초, 1장 쇼다운) — 제목은 「반론 / 쇼다운 / 진타」 세로 3줄, 형세 「발전!」, 마무리 「V」.
입력 : 한국어판 spc(주인님 허락 UI 2026-10-29, ui_authorized_20261029/manifest.json). DXT1 은 검은 바탕이라 밝기를 알파로 바꾼다.
출력 : Game/Assets/Art/ui/v3_hr/ (git 밖).
"""
import json, pathlib
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'Game/Assets/Art/ui/v3_hr'
AUTH = pathlib.Path('C:/Users/kirby/Downloads/v3_re/ui_authorized_20261029/manifest.json')


def unblack(im):
    im = im.convert('RGB'); out = Image.new('RGBA', im.size); px, po = im.load(), out.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = px[x, y]; a = max(r, g, b)
            po[x, y] = (0, 0, 0, 0) if a == 0 else (min(255, r * 255 // a), min(255, g * 255 // a), min(255, b * 255 // a), a)
    return out


def main():
    m = json.loads(AUTH.read_text(encoding='utf-8'))
    tex = {t['resource']: t['path'] for t in m['textures']}
    def load(name):
        im = Image.open(tex[name]); return unblack(im) if 'DXT1' in name else im.convert('RGBA')
    # 제목 「진」「타」(t_hr_st_tx_007/008) — 기존 title_0..4(반론쇼다운)와 같은 방식 : 글자 테두리로 자르고 빛은 같은 가운데로 넓게
    for i, k in ((5, '007'), (6, '008')):
        g = load(f't_hr_st_tx_{k}_JP.png'); box = g.getchannel('A').getbbox(); g.crop(box).save(OUT / f'title_{i}.png')
        cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2; w, h = box[2] - box[0] + 100, box[3] - box[1] + 100
        load(f't_hr_st_tx_{k}_ef_DXT1_JP.png').crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)).save(OUT / f'title_{i}_ef.png')
    one = {'petal.png': 't_hr_st_deco_piece_DXT1.png', 'st_line.png': 't_hr_st_line_DXT1.png',
           'advance_kr.png': 't_hr_hatten_tx_000_DXT1_JP.png', 'retreat_kr.png': 't_hr_gyaku_hatten_tx_000_DXT1_JP.png',
           'advance_line.png': 't_hr_hatten_line_000_DXT1.png', 'v_mark.png': 't_ef_ronpa_hit_tx_vpoint_DXT1_JP.png',
           'v_ef.png': 't_ef_ronpa_hit_ef_vpoint_DXT1.png'}
    for out, name in one.items():
        im = load(name); box = im.getchannel('A').getbbox(); (im.crop(box) if box else im).save(OUT / out); print(out, im.size, box)
    # 상대의 「반론」 컷인(영상 2934.6~2937.8초 : 노란 띠 + 상대 얼굴 + 검은 붓 「반론」 → 초록 별빛 깨짐) — 글자 없는 그림은 V3 원본(언어 무관)
    HR = pathlib.Path('C:/Users/kirby/Downloads/v3_re/ui_hr_20261105/png')
    for out, src in {'hanron_bg.png': 't_ronpa_hanron_cutin_US/t_hanron_bg.png.png', 'hanron_ef.png': 't_ronpa_hanron_cutin_US/t_hanron_ef.png.png',
                     'hanron_pl.png': 't_ronpa_hanron_cutin_US/t_hanron_pl_001_000.png.png', 'crack_burst.png': 't_ronpa_hanron_crack/t_hr_break_ef_000_DXT1.png.png'}.items():
        im = Image.open(HR / src); im = unblack(im.resize((1024, 1024))) if 'DXT1' in src else im.convert('RGBA'); im.save(OUT / out); one[out] = src
    # 시간판·숫자(t_time, 한국어판 3105.6초 오른쪽 아래 「02:51:324」) · 꽃 커서(t_hr_zan_pointer_ico bg_mask 모양 + 파란 줄무늬)
    for k in range(11): Image.open(HR / f't_time/t_time_num_{k:03d}.png.png').convert('RGBA').save(OUT / f'time_{k}.png'); one[f'time_{k}.png'] = 't_time'
    Image.open(HR / 't_time/t_time_base_l_000.png.png').convert('RGBA').save(OUT / 'time_base.png'); one['time_base.png'] = 't_time'
    mask = Image.open(HR / 't_hr_zan_pointer_ico/t_hr_zan_pointer_bg_mask.png.png').convert('RGBA')
    stripe = unblack(Image.open(HR / 't_hr_zan_pointer_ico/t_hr_zan_pointer_bg_stripe_DXT1.png.png'))
    fl = Image.new('RGBA', mask.size, (60, 150, 255, 0)); a_m = mask.getchannel('A') if mask.getchannel('A').getextrema()[0] < 255 else mask.convert('L')
    fl = Image.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', mask.size, (40, 120, 235)).split(), a_m)), stripe); fl.putalpha(a_m); fl.save(OUT / 'pointer_flower.png'); one['pointer_flower.png'] = 'zan_pointer'
    unblack(Image.open(HR / 't_hr_ef_hit_ok/t_hr_ef_hit_ok_002_DXT1.png.png')).save(OUT / 'hit_ring.png'); one['hit_ring.png'] = 'hit_ok_002'  # 3099.2초 파란 원 충격파
    Image.new('RGBA', (8, 8), (255, 255, 255, 255)).save(OUT / 'white.png'); one['white.png'] = 'tint base'  # 색을 입히는 바탕(청록 화면·붉은 X)
    for n, c in {'teal.png': (30, 235, 190), 'red.png': (255, 70, 40), 'black.png': (0, 0, 0)}.items(): Image.new('RGBA', (8, 8), (*c, 255)).save(OUT / n); one[n] = 'flat colour'  # 이 위젯은 그림 색 입히기가 안 먹어 색 그림을 따로 둔다
    st = Image.open(OUT / 'st_line.png').convert('RGBA')  # 3092.5초 여러 색 칼선 : 푸른 칼선의 밝기를 다른 색으로
    for n, c in {'line_red': (255, 60, 60), 'line_pink': (255, 110, 210), 'line_orange': (255, 150, 40), 'line_yellow': (255, 230, 60)}.items():
        o = Image.new('RGBA', st.size); ps, po = st.load(), o.load()
        for y in range(st.height):
            for x in range(st.width):
                r, g, b, a = ps[x, y]; l = max(r, g, b) / 255; po[x, y] = (*(int(v * l + 255 * (1 - l) * l) for v in c), a)
        o.save(OUT / (n + '.png')); one[n + '.png'] = 'st_line tint'
    for f in ['title_5.png', 'title_6.png', *one]: assert (OUT / f).exists()


def to_webp():  # 빌드 최적화(optimize_assets)가 png 를 webp 로 바꾸므로 처음부터 webp 로 둔다
    for f in OUT.glob('*.png'):
        Image.open(f).save(f.with_suffix('.webp'), 'WEBP', lossless=True); f.unlink()


if __name__ == '__main__':
    main(); to_webp()
