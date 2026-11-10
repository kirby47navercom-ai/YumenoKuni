"""반론 쇼다운 마무리 「참격」 그림 — Claude 2026-11-05, 사양서 26.
근거 : V3 영상(Hs3Y7uyOAQk 194.5~196.6초) — 칼날 적중 → 흰·파란 충돌 빛 → 어두워진 화면에 초록 원 + 「Cut!」(한국어판 「참격」) + 초록 사선 → 주황 글자 파편 → 반론 컷인.
입력 : 한국어판 t_hr_break_JP.spc (주인님 허락 UI 2026-10-29, ui_authorized_20261029/manifest.json), V3 t_hr_ef_hit_ok (ui_hr_20261105).
DXT1 은 알파가 없고 검은 바탕이라, 밝기(가장 큰 채널)를 알파로 바꾸고 색은 알파로 나눠 되살린다(더하기 섞기와 같게 보인다).
출력 : Game/Assets/Art/ui/v3_hr/break_*.png (git 밖).
"""
import json, pathlib
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'Game/Assets/Art/ui/v3_hr'
AUTH = pathlib.Path('C:/Users/kirby/Downloads/v3_re/ui_authorized_20261029/manifest.json')
HR = pathlib.Path('C:/Users/kirby/Downloads/v3_re/ui_hr_20261105/png')


def unblack(src, dst, size=None):
    im = Image.open(src).convert('RGB')
    if size: im = im.resize(size, Image.LANCZOS)
    px = im.load(); out = Image.new('RGBA', im.size); po = out.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = px[x, y]; a = max(r, g, b)
            po[x, y] = (0, 0, 0, 0) if a == 0 else (min(255, r * 255 // a), min(255, g * 255 // a), min(255, b * 255 // a), a)
    out.save(dst)


def main():
    m = json.loads(AUTH.read_text(encoding='utf-8'))
    tex = {t['resource']: t['path'] for t in m['textures'] if t['container'].endswith('t_hr_break_JP.spc')}
    jobs = {'break_tx.png': (tex['t_hr_break_zen_tx_000_DXT1_JP.png'], (512, 512)),
            'break_circle.png': (tex['t_hr_break_circle_000_DXT1.png'], (512, 512)),
            'break_slash.png': (tex['t_hr_break_slash_000_DXT1.png'], (512, 512)),
            'break_line.png': (tex['t_hr_break_line_000_DXT1.png'], (1024, 64)),
            'break_hit.png': (HR / 't_hr_ef_hit_ok/t_hr_ef_hit_ok_000_DXT1.png.png', (512, 512))}
    for name, (src, size) in jobs.items():
        unblack(src, OUT / name, size); print(name)
    Image.new('RGBA', (64, 64), (6, 10, 30, 255)).save(OUT / 'break_dim.png')  # V3 t_hr_break_bg : 판을 어둡게 덮는 바탕
    assert all((OUT / n).exists() for n in jobs)


def to_webp():  # 빌드 최적화(optimize_assets)가 png 를 webp 로 바꾸므로 처음부터 webp 로 둔다
    for f in OUT.glob('*.png'):
        Image.open(f).save(f.with_suffix('.webp'), 'WEBP', lossless=True); f.unlink()


if __name__ == '__main__':
    main(); to_webp()
