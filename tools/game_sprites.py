#!/usr/bin/env python3
"""
게임용 스프라이트 : art/sprites/{slug}/*.webp (2048²) → Game/Assets/Art/sprites/{slug}/*.webp (1024²).
화면에는 700px 이하로만 나오므로 절반으로 줄여 WebView 텍스처 메모리를 1/4로 줄인다. 바뀐 것만 변환.
  python tools/game_sprites.py
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZE = 1024


def main():
    done = 0
    src_root = os.path.join(ROOT, "art", "sprites")
    for slug in sorted(os.listdir(src_root)):
        src_dir = os.path.join(src_root, slug)
        if not os.path.isdir(src_dir):
            continue
        dst_dir = os.path.join(ROOT, "Game", "Assets", "Art", "sprites", slug)
        os.makedirs(dst_dir, exist_ok=True)
        for f in os.listdir(src_dir):
            if not f.endswith(".webp") or f.startswith("sheet"):
                continue
            src, dst = os.path.join(src_dir, f), os.path.join(dst_dir, f)
            if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
                continue
            im = Image.open(src)
            if max(im.size) > SIZE:
                im.thumbnail((SIZE, SIZE), Image.LANCZOS)
            im.save(dst, "WEBP", quality=90, method=4)
            done += 1
    # 탐색 화면 전신(방 안에 작게 서 있는 인물) : art/standing_hd → Assets/Art/figure/{slug}.webp, 높이 720
    fig_dir = os.path.join(ROOT, "Game", "Assets", "Art", "figure")
    os.makedirs(fig_dir, exist_ok=True)
    for f in os.listdir(os.path.join(ROOT, "art", "standing_hd")):
        if not f.endswith(".webp"):
            continue
        src, dst = os.path.join(ROOT, "art", "standing_hd", f), os.path.join(fig_dir, f)
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            continue
        im = Image.open(src).convert("RGBA")
        im.thumbnail((1100, 1100), Image.LANCZOS)
        if im.getpixel((4, 4))[3] > 200:  # 흰 배경 원본 → 배경 제거(애니 모델)
            from rembg import new_session, remove
            global _rembg
            try:
                _rembg
            except NameError:
                _rembg = new_session("isnet-anime")
            im = remove(im.convert("RGB"), session=_rembg).convert("RGBA")
        im = im.crop(im.getbbox())
        im.thumbnail((720, 720), Image.LANCZOS)
        im.save(dst, "WEBP", quality=90, method=4)
        done += 1
    print(f"sprites converted: {done}")


if __name__ == "__main__":
    sys.exit(main())
