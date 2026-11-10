"""논의 스크럼 V3 원본 그림 — Claude 2026-11-06, 사양서 27a.
입력 : C:/Users/kirby/Downloads/v3_re/ui_scrum_20261106/png (V3 설치본 partition_data_win(_us) + 한국어 패치 _JP, 주인님 허락 UI 2026-10-29)
       C:/Users/kirby/Downloads/v3_re/ui_endings_20261106 의 한국어 완전논파(t_zenronpa_cutin_0N_JP)는 tools/v3_hr_* 처럼 따로 쓴다.
DXT1 은 알파가 없는 검은 바탕이라 밝기(가장 큰 채널)를 알파로 바꾼다(더하기 섞기와 같게 보인다).
같은 그림이 _JP(한국어)·_US 둘 다 있으면 _JP 만 쓴다.
출력 : Game/Assets/Art/ui/v3_scrum/<원래 이름>.webp (git 밖)
"""
import pathlib
from PIL import Image
SRC = pathlib.Path('C:/Users/kirby/Downloads/v3_re/ui_scrum_20261106/png')
OUT = pathlib.Path(__file__).resolve().parents[1] / 'Game/Assets/Art/ui/v3_scrum'
SKIP = ('t_scm_chara_pl_l_0', 't_scm_chara_pl_r_0', 'topic_loop', 't_scm_topic_tx', '_CN', '_FR', '_ZH', 't_scrum_topic_', 't_zenronpa_', 'xone', '_az', 'circle.png', 'cross.png', 'square.png', 'triangle.png', 'circle_miss.png', 'cross_miss.png', 'square_miss.png', 'triangle_miss.png', 'chara_body')


def unblack(im):
    im = im.convert('RGB'); px = im.load(); out = Image.new('RGBA', im.size); po = out.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = px[x, y]; a = max(r, g, b)
            po[x, y] = (0, 0, 0, 0) if a == 0 else (min(255, r * 255 // a), min(255, g * 255 // a), min(255, b * 255 // a), a)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True); n = 0
    files = sorted(SRC.glob('*/*.png'))
    jp = {f.name.replace('_JP', '') for f in files if '_JP' in f.name}
    for f in files:
        name = f.name.replace('.png.png', '').replace('.png', '')
        if any(s in f.name for s in SKIP): continue
        if '_US' in f.name and f.name.replace('_US', '') in jp: continue
        im = Image.open(f)
        im = unblack(im) if 'DXT1' in name else im.convert('RGBA')
        key = name.replace('_JP', '').replace('_US', '').replace('_DXT1', '')
        im.save(OUT / (key + '.webp'), 'WEBP', lossless=True); n += 1
    print(n, 'files ->', OUT)


if __name__ == '__main__':
    main()
