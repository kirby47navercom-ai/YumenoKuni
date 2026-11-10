"""거짓 탄환(우클릭 누르고 있기) 화면용 흰 실루엣 — Claude 2026-11-05.
근거 : V3 LP Ch1 거짓 논의(lparchive Danganronpa V3 Update 31, 「Nonstop Debate Lie」 화면) — 누르고 있는 동안 인물이 흰 실루엣, 배경은 보랏빛으로 가라앉는다.
입력 : Game/Assets/Art/court_figures/*.webp  →  출력 : Game/Assets/Art/court_figures_sil/<같은 이름>.webp (1/4 크기, 알파 그대로 흰색)
Game/Assets/Art 는 git 에 안 올라간다(.gitignore). 다시 만들려면 이 파일을 돌린다.
"""
import pathlib
from PIL import Image, ImageFilter
ROOT = pathlib.Path(__file__).resolve().parents[1] / 'Game/Assets/Art'
SRC, OUT = ROOT / 'court_figures', ROOT / 'court_figures_sil'


def main():
    OUT.mkdir(exist_ok=True)
    n = 0
    for f in sorted(SRC.glob('*.webp')):
        out = OUT / (f.stem + '.webp')
        if out.exists() and out.stat().st_mtime >= f.stat().st_mtime:
            continue
        im = Image.open(f).convert('RGBA')
        im = im.resize((max(1, im.width // 4), max(1, im.height // 4)), Image.LANCZOS)
        a = im.getchannel('A')
        rim = a.filter(ImageFilter.MaxFilter(3))  # 바깥 가장자리 연보라 테
        base = Image.new('RGBA', im.size, (196, 170, 236, 0)); base.putalpha(rim)
        body = Image.new('RGBA', im.size, (250, 248, 255, 0)); body.putalpha(a)
        Image.alpha_composite(base, body).save(out, 'WEBP', quality=90)
        n += 1
    print('silhouettes', n, 'in', OUT)


if __name__ == '__main__':
    main()
