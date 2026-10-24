#!/usr/bin/env python3
"""
NovelAI 업스케일(4배)로 입상 화질을 올린다.
  python tools/upscale_nai.py art/standing/mio_123_0.png [...]   # 결과 : 같은 폴더 *_x4.png
토큰은 환경변수 NAI_TOKEN 으로만 받는다. 입력은 약 1M 픽셀 이하(832x1216 OK).
"""
import base64
import io
import os
import sys
import zipfile

import requests
from PIL import Image

URL = "https://image.novelai.net/ai/upscale"


def upscale(token, path, scale=4):
    w, h = Image.open(path).size
    body = {"image": base64.b64encode(open(path, "rb").read()).decode(), "width": w, "height": h, "scale": scale}
    r = requests.post(URL, json=body, headers={"Authorization": f"Bearer {token}"}, timeout=300)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    data = r.content
    if data[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            data = zf.read(zf.namelist()[0])
    out = os.path.splitext(path)[0] + f"_x{scale}.png"
    open(out, "wb").write(data)
    return out


if __name__ == "__main__":
    token = os.environ.get("NAI_TOKEN")
    if not token:
        sys.exit("환경변수 NAI_TOKEN 에 토큰을 설정하세요.")
    for p in sys.argv[1:]:
        try:
            print("saved:", upscale(token, p))
        except Exception as e:
            print("실패:", p, e)
