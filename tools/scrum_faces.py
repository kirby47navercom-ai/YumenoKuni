"""의논 스크럼 탭 속 얼굴(V3 1:18:36 : 탭 안에 배경 없는 얼굴만) — 재판 옆모습 입상(<slug>_SR/_SL)에서 머리만 오린다.
create-project.mjs 가 court_figures.py 다음에 부른다. 결과 : Game/Assets/Art/scrum_faces/<slug>_SR.webp·_SL.webp (정사각 256)."""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'Game/Assets/Art/court_figures'
DEST = ROOT / 'Game/Assets/Art/scrum_faces'
SLUGS = 'mio rin ken nana taiga ai rei sora haruka sho koto akari riku satsuki yuu kaede'.split()

def face(path):
    im = Image.open(path).convert('RGBA')
    a = np.asarray(im)[:, :, 3] > 32
    rows = np.flatnonzero(a.any(1))
    top, height = rows[0], rows[-1] - rows[0]
    size = int(height * .17)                         # 머리 한 개 ≈ 키의 1/7, 턱까지
    band = a[top + size // 3:top + size]  # 머리카락이 아니라 얼굴 폭 기준
    cols = np.flatnonzero(band.any(0))
    cx = (cols[0] + cols[-1]) // 2
    box = (cx - size // 2, top + size // 7, cx + size // 2, top + size + size // 7)  # 정수리 조금 잘라도 턱은 들어오게
    out = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]))
    out.paste(im.crop(box), (0, 0))
    return out.resize((256, 256), Image.LANCZOS)

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    made = 0
    for slug in SLUGS:
        for pose in ('SR', 'SL'):
            src = SRC / f'{slug}_{pose}.webp'
            if src.is_file():
                face(src).save(DEST / f'{slug}_{pose}.webp', quality=92)
                made += 1
    print('scrum faces', made)

if __name__ == '__main__':
    main()
