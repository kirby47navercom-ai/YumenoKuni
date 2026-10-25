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
NORM = "2"  # 키 비율·머리 중심 맞춤 규칙이 바뀌면 올린다(전부 다시 변환)


def heights():
    """data/characters.json 의 키(cm) → slug. 래피는 대화 입상만 0.62 배(V3 모노쿠마처럼 작지만 보이게)"""
    import json, re
    names = {"미오": "mio", "레이": "rei", "소라": "sora", "켄": "ken", "나나": "nana", "리쿠": "riku", "아카리": "akari", "유우": "yuu",
             "코토": "koto", "사츠키": "satsuki", "타이가": "taiga", "린": "rin", "쇼": "sho", "아이": "ai", "하루카": "haruka", "카에데": "kaede", "래피": "lappy"}
    out = {}
    for c in json.load(open(os.path.join(ROOT, "data", "characters.json"), encoding="utf-8")):
        words = c["heading"].split()
        slug = names.get(words[1] if len(words) > 1 and words[1] in names else words[0])
        m = re.search(r"(\d+)cm", " ".join(c["fields"].values()))
        if slug and m:
            out[slug] = int(m.group(1))
    return out


def normalize(im, scale):
    """대화 입상 : 머리 중심을 가운데(512)로, 아래 가운데를 기준으로 키 비율만큼 줄인다 → 모두 같은 자리에 서고 키 차이가 보인다"""
    im = im.convert("RGBA")
    a = im.getchannel("A")
    bb = a.getbbox()
    if not bb:
        return im
    import numpy as np
    head = np.asarray(a.crop((0, bb[1], im.width, min(im.height, bb[1] + 120)))) > 128
    cols = np.flatnonzero(head.any(0))
    hx = (cols[0] + cols[-1]) / 2 if len(cols) else im.width / 2
    w, h = round(im.width * scale), round(im.height * scale)
    small = im.resize((w, h), Image.LANCZOS)
    out = Image.new("RGBA", im.size)
    out.paste(small, (round(im.width / 2 - hx * scale), im.height - h), small)
    return out


def main():
    done = 0
    tall = heights(); top = max(v for k, v in tall.items() if k != "lappy")
    src_root = os.path.join(ROOT, "art", "sprites")
    for slug in sorted(os.listdir(src_root)):
        src_dir = os.path.join(src_root, slug)
        if not os.path.isdir(src_dir):
            continue
        dst_dir = os.path.join(ROOT, "Game", "Assets", "Art", "sprites", slug)
        os.makedirs(dst_dir, exist_ok=True)
        scale = .62 if slug == "lappy" else tall.get(slug, top) / top
        stamp = os.path.join(dst_dir, ".norm")
        fresh = os.path.exists(stamp) and open(stamp).read() == f"{NORM} {scale:.4f}"
        for f in os.listdir(src_dir):
            if not f.endswith(".webp") or f.startswith("sheet"):
                continue
            src, dst = os.path.join(src_dir, f), os.path.join(dst_dir, f)
            if fresh and os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
                continue
            im = Image.open(src)
            if max(im.size) > SIZE:
                im.thumbnail((SIZE, SIZE), Image.LANCZOS)
            normalize(im, scale).save(dst, "WEBP", quality=90, method=4)
            done += 1
        open(stamp, "w").write(f"{NORM} {scale:.4f}")
    # 탐색 화면 전신(방 안에 작게 서 있는 인물) : art/standing_hd → Assets/Art/figure/{slug}.webp, 높이 720
    fig_dir = os.path.join(ROOT, "Game", "Assets", "Art", "figure")
    os.makedirs(fig_dir, exist_ok=True)
    for f in os.listdir(os.path.join(ROOT, "art", "standing_hd")):
        if not f.endswith(".webp"):
            continue
        src, dst = os.path.join(ROOT, "art", "standing_hd", f), os.path.join(fig_dir, f)
        fstamp = os.path.join(fig_dir, ".norm")
        if os.path.exists(fstamp) and open(fstamp).read() == NORM and os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
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
        # 같은 캔버스(위젯 240×520 의 두 배), 발끝 = 아래, 키 비율로 (래피는 실제 키 80cm)
        slug = f[:-5]
        hh = round(1000 * tall.get(slug, top) / top)
        im = im.resize((max(1, round(im.width * hh / im.height)), hh), Image.LANCZOS)
        if im.width > 480:
            im = im.resize((480, round(im.height * 480 / im.width)), Image.LANCZOS)
        canvas = Image.new("RGBA", (480, 1040))
        canvas.paste(im, ((480 - im.width) // 2, 1040 - 10 - im.height), im)
        canvas.save(dst, "WEBP", quality=90, method=4)
        done += 1
    open(os.path.join(fig_dir, ".norm"), "w").write(NORM)
    print(f"sprites converted: {done}")


if __name__ == "__main__":
    sys.exit(main())
