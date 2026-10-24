#!/usr/bin/env python3
"""
처형 동영상 조립 : docs/spec/05 §5 스토리보드 표 + 코덱스 키프레임 → MP4.
  python tools/make_execution_video.py 1            # 1장 → video/exec_1.mp4 (1920x1080 30fps)
  python tools/make_execution_video.py 1 --preview  # 640x360 15fps 빠른 확인
키프레임 : art/cg/exec_{장}_{번호}.png (있으면 _bg/_fg 레이어 우선). 없으면 컷 설명을 적은 자리 표시 화면.
BGM : audio/bgm_exec_{장}.ogg 가 있으면 깐다. ffmpeg 필요.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = glob.glob(os.path.join(ROOT, "docs", "spec", "05_*.md"))[0]
FONT = "C:/Windows/Fonts/malgunbd.ttf"


def storyboard(ch):
    """05 §5-{ch} 표 → [(번호, 설명, 초)]"""
    text = open(SPEC, encoding="utf-8").read()
    m = re.search(rf"### 5-{ch}\. .*?\n(.*?)(?=\n### |\n## |\Z)", text, re.S)
    if not m:
        sys.exit(f"05 문서에 5-{ch} 스토리보드가 없습니다.")
    cuts = []
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].isdigit() and cells[2].isdigit():
            cuts.append((int(cells[0]), cells[1], int(cells[2])))
    return cuts


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def keyframe(ch, no, desc, size):
    """레이어(bg+fg) > 단일 키프레임 > 자리 표시. 카메라 이동 여백을 위해 10% 크게 만든다."""
    W, H = int(size[0] * 1.1), int(size[1] * 1.1)
    base = os.path.join(ROOT, "art", "cg", f"exec_{ch}_{no}")
    if os.path.exists(base + "_bg.png"):
        img = Image.open(base + "_bg.png").convert("RGB").resize((W, H))
        if os.path.exists(base + "_fg.png"):
            fg = Image.open(base + "_fg.png").convert("RGBA").resize((W, H))
            img.paste(fg, (0, 0), fg)
        return img
    if os.path.exists(base + ".png"):
        return Image.open(base + ".png").convert("RGB").resize((W, H))
    img = Image.new("RGB", (W, H), (20, 12, 28))
    d = ImageDraw.Draw(img)
    d.text((W // 2, H // 2), f"{ch}장 #{no}\n{desc}", font=font(H // 22), fill=(230, 200, 230), anchor="mm", align="center")
    return img


def caption_of(desc):
    m = re.search(r'래피 "([^"]+)"', desc)
    return m.group(1) if m else None


def render(ch, size, fps, out):
    cuts = storyboard(ch)
    W, H = size
    ff = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
    bgm = os.path.join(ROOT, "audio", f"bgm_exec_{ch}.ogg")
    if os.path.exists(bgm):
        ff += ["-i", bgm, "-shortest", "-c:a", "aac"]
    ff += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out]
    proc = subprocess.Popen(ff, stdin=subprocess.PIPE)
    cap_font = font(H // 20)
    fade = int(fps * 0.3)
    for no, desc, sec in cuts:
        black = "암전" in desc
        src = None if black else keyframe(ch, no, desc, size)
        shake = any(k in desc for k in ("가속", "빨라", "폭주", "경고음", "터짐"))
        flash = any(k in desc for k in ("빛이 터", "빛으로", "번쩍", "빛 알갱이"))
        cap = caption_of(desc)
        n = sec * fps
        for i in range(n):
            t = i / max(n - 1, 1)
            if black:
                frame = Image.new("RGB", (W, H))
            else:
                # 느린 줌 인 + 약한 팬 (켄 번즈)
                z = 1.0 + 0.08 * t
                cw, ch_ = int(src.width / 1.1 / z), int(src.height / 1.1 / z)
                ox = int((src.width - cw) * (0.5 + 0.1 * (t - 0.5)))
                oy = (src.height - ch_) // 2
                if shake:
                    ox += int(6 * ((i * 7919) % 5 - 2))
                    oy += int(6 * ((i * 104729) % 5 - 2))
                frame = src.crop((ox, oy, ox + cw, oy + ch_)).resize((W, H))
                if flash and t > 0.8:
                    frame = Image.blend(frame, Image.new("RGB", (W, H), (255, 255, 255)), (t - 0.8) / 0.2)
            if cap and not black:
                d = ImageDraw.Draw(frame)
                d.rectangle((0, H * 0.82, W, H), fill=(0, 0, 0))
                d.text((W // 2, int(H * 0.91)), f"래피 「{cap}」", font=cap_font, fill=(255, 150, 200), anchor="mm")
            # 컷 사이 페이드 인/아웃
            a = min(1.0, i / fade if fade else 1, (n - 1 - i) / fade if fade else 1)
            if a < 1:
                frame = Image.blend(Image.new("RGB", (W, H)), frame, max(a, 0))
            proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait():
        sys.exit("ffmpeg 실패")
    return out, sum(c[2] for c in cuts), len(cuts)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", type=int)
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    size, fps = ((640, 360), 15) if a.preview else ((1920, 1080), 30)
    os.makedirs(os.path.join(ROOT, "video"), exist_ok=True)
    out = os.path.join(ROOT, "video", f"exec_{a.chapter}{'_preview' if a.preview else ''}.mp4")
    path, total, n = render(a.chapter, size, fps, out)
    print(f"saved: {path} ({n}컷, {total}초)")
