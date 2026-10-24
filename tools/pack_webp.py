#!/usr/bin/env python3
"""
큰 작업용 PNG → 저장소용 WebP (같은 폴더, 같은 이름 .webp).
PNG 원본은 로컬에만 두고(.gitignore), 게임·저장소는 WebP를 쓴다.
  python tools/pack_webp.py            # 바뀐 것만 변환
대상 : art/standing_hd, art/sprites, art/cg, art/cutin, bg, inspect  (검수용 sheet/preview 제외)
"""
import glob
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = ["art/standing_hd", "art/sprites", "art/cg", "art/cutin", "bg", "inspect"]
SKIP = ("sheet", "preview")


def main():
    done = before = after = 0
    for d in DIRS:
        for png in glob.glob(os.path.join(ROOT, d, "**", "*.png"), recursive=True):
            if os.path.basename(png).startswith(SKIP):
                continue
            webp = png[:-4] + ".webp"
            if os.path.exists(webp) and os.path.getmtime(webp) >= os.path.getmtime(png):
                continue
            Image.open(png).save(webp, "WEBP", quality=90, method=6, alpha_quality=100)
            done += 1
            before += os.path.getsize(png)
            after += os.path.getsize(webp)
    print(f"변환 {done}개 : {before / 1e6:.1f}MB → {after / 1e6:.1f}MB")


if __name__ == "__main__":
    main()
