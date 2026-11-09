#!/usr/bin/env python3
"""
게임용 스프라이트 : curated V4 delivery → 모든 runtime 인물 경로.
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
    # Compatibility command now publishes only the curated V4 art family.
    from export_v4_runtime_characters import main as publish
    return publish()


if __name__ == "__main__":
    sys.exit(main())
