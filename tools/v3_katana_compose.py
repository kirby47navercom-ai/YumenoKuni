"""반론 쇼다운 칼 판 — V3 원본 조각을 원래 틀(128x256·512x256) 그대로 맞춰 조립한다. Claude 2026-11-05.
주인님 지적(조각을 잘라 엇붙임) : 칼집 왼끝(saya_000)·가운데(001, 가로로 늘림)·오른끝 매듭(002)을 같은 높이 틀에 잇고,
손잡이(tuka)는 칼집 끝 **밑으로** 넣어 손잡이 앞 칼날 토막이 칼집 속에 가려지게 한다. 뽑은 칼은 칼날(toushin 000 끝·001 몸통) + 손잡이.
수국(t_hr_cylinder mask 모양 + 줄무늬)은 칼집 왼끝 위에 얹는다(HUD 판만).
입력 : C:/Users/kirby/Downloads/v3_re/ui_hr_20261105/png (V3 설치본 추출, 주인님 허락 UI)
출력 : Game/Assets/Art/ui/v3_hr/{hud_,}katana_{sheathed,sheathed_off,drawn,drawn_glow}.webp
"""
import pathlib
from PIL import Image
SRC = pathlib.Path('C:/Users/kirby/Downloads/v3_re/ui_hr_20261105/png')
OUT = pathlib.Path(__file__).resolve().parents[1] / 'Game/Assets/Art/ui/v3_hr'
BODY = 620          # 칼집(칼날) 길이 px : 이름이 들어가는 몸통
HILT_TUCK = 104     # 손잡이 틀 왼쪽에서 코등이(가드)까지 — 이만큼 칼집 밑으로 들어간다


def img(name):
    return Image.open(SRC / name / (name + '.png.png')).convert('RGBA')


def unblack(im):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]; m = max(r, g, b)
            px[x, y] = (0, 0, 0, 0) if m == 0 else (min(255, r * 255 // m), min(255, g * 255 // m), min(255, b * 255 // m), min(a, m))
    return im


def flower(size):
    mask = img('t_hr_cylinder_mask'.replace('_mask', '')) if False else Image.open(SRC / 't_hr_cylinder/t_hr_cylinder_mask.png.png').convert('RGBA')
    stripe = Image.open(SRC / 't_hr_cylinder/t_hr_cylinder_stripe_DXT1.png.png').convert('RGBA')
    a = mask.getchannel('A')
    body = Image.new('RGBA', mask.size, (60, 170, 255, 255)); body.alpha_composite(unblack(stripe.copy()))
    body.putalpha(a)
    return body.resize((size, size), Image.LANCZOS)


def build(state, drawn, glow):
    W = 128 + BODY + 512 - HILT_TUCK; c = Image.new('RGBA', (W, 256))
    hilt = img(f'kotodama_sword_tuka_{"ef" if glow else state}_000')
    x0 = BODY + 8  # 코등이(손잡이 틀 x≈100)가 칼집 끝(매듭 틀 x≈108)에 바로 닿게 — 손잡이 앞 칼날 토막은 칼집 밑으로
    if drawn:   # 뽑은 칼 : 칼날 끝 + 몸통을 먼저 깔고, 손잡이(코등이)가 그 위 — 칼날은 코등이에서 끝난다
        tip = img(f'kotodama_toushin_{"ef" if glow else state}_000'); mid = img(f'kotodama_toushin_{"ef" if glow else state}_001')
        c.alpha_composite(tip, (0, 0)); c.alpha_composite(mid.resize((x0 + 100 - 128, 256)), (128, 0)); c.alpha_composite(hilt, (x0, 0))
    else:
        c.alpha_composite(hilt, (x0, 0))
    if drawn:
        pass
    else:       # 칼집 : 왼끝 + 늘린 가운데 + 매듭 끝(손잡이 앞을 덮는다)
        l, m, r = (img(f'kotodama_sword_saya_{state}_00{i}') for i in range(3))
        c.alpha_composite(l, (0, 0)); c.alpha_composite(m.resize((BODY - 128 + 4, 256)), (128, 0)); c.alpha_composite(r, (BODY, 0))
    return c.crop(c.getchannel('A').getbbox())


def main():
    jobs = {'katana_sheathed': ('on', False, False), 'katana_sheathed_off': ('off', False, False),
            'katana_drawn': ('on', True, False), 'katana_drawn_glow': ('on', True, True)}
    for name, (st, dr, gl) in jobs.items():
        k = build(st, dr, gl); k.save(OUT / (name + '.webp'), 'WEBP', lossless=True)
        f = flower(int(k.height * 1.25)); hud = Image.new('RGBA', (k.width + f.width // 2, max(k.height, f.height)))
        hud.alpha_composite(k, (f.width // 2, (hud.height - k.height) // 2)); hud.alpha_composite(f, (0, (hud.height - f.height) // 2))
        hud.save(OUT / ('hud_' + name + '.webp'), 'WEBP', lossless=True); print(name, k.size, hud.size)


if __name__ == '__main__':
    main()
