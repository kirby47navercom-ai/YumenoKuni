#!/usr/bin/env python3
"""
유메노쿠니 캐릭터 T자 일러스트 생성 스크립트 (NovelAI)

사용법
  1) pip install requests
  2) 토큰은 환경변수로만 전달 (코드/채팅에 직접 쓰지 마세요)
       Windows (PowerShell) : $env:NAI_TOKEN = "pst-..."
       macOS / Linux        : export NAI_TOKEN="pst-..."
  3) python generate_tpose_nai.py                 # 전원(17종) 1장씩
     python generate_tpose_nai.py --only mio rei  # 특정 캐릭터만
     python generate_tpose_nai.py --n 3           # 캐릭터당 3장
     python generate_tpose_nai.py --seed 12345    # 시드 고정(재현)

결과는 ./tpose_out/ 에 PNG 로 저장됨.
Anlas 를 소모하므로 처음엔 --only 로 1~2명만 테스트하는 것을 권장.
엔드포인트/모델명은 NovelAI 쪽 변경 가능성이 있으니 오류가 나면 공식 문서를 확인할 것.
"""
import argparse
import io
import os
import random
import sys
import time
import zipfile

import requests

API_URL = "https://image.novelai.net/ai/generate-image"
MODEL = "nai-diffusion-4-5-full"
WIDTH, HEIGHT = 832, 1216
STEPS = 28
SCALE = 5.0
SAMPLER = "k_euler_ancestral"
NOISE_SCHEDULE = "karras"

# ---- 사용자가 지정한 스타일 프롬프트 (그대로) --------------------------------
STYLE_POSITIVE = (
    "1.35::artist:shiun (siun 5513)::, 1.75::artist:zero (miraichizu)::, "
    "1::artist:healthyman::, 1.45::artist:samidare (hoshi)::, "
    "1.3::artist:kimhiro::, artist:doremi, 1.5::artist:aiamu iamu::, "
    "year 2025, year 2024, year 2023, blurry background, depth of field, "
    "incredibly absurdres, very aesthetic, highres, masterpiece, best quality, "
    "amazing quality, best illustration, digital art, "
    "-3::empty eyes, artist collaboration,doll::, dynamic angle, shiny skin, "
    "location, smooth coloring,"
)

NEGATIVE = (
    "text, logo, watermark, too many watermarks, reference, signature, artist name, "
    "dated, artistic error, scan artifacts, jpeg artifacts, upscaled, aliasing, "
    "film grain, heavy film grain, dithering, chromatic aberration, digital dissolve, "
    "halftone, screentones, artist:xinzoruo, artist:milkpanda, artist:kurukurumagical, "
    "2::artist:bkub ::, artist collaboration, one-hour drawing challenge, toon (style), "
    "1990s (style), 4koma, 2koma, mutation, deformed, distorted, disfigured, "
    "1.2::bad anatomy ::, unnatural hair, bad face,  mob face, bad eyes, empty eyes, "
    "bad proportions, bad limbs, amputee, bad arm, bad hands, bad hand structure, "
    "extra digits, fewer digits, bad leg, extra leg, distorted composition, "
    "bad perspective, multiple views, disorganized colors, unfinished, incomplete, "
    "displeasing, very displeasing, unsatisfactory, inadequate, deficient, subpar, "
    "poor, blurry, lowres, worst quality, bad quality, fewer details, bad portrait, "
    "bad illustration, dark skin, plants, grass, leaves, hot coloring, reddish lips, "
    "colored lips, cool tone, re:stage!, poptepipic, monochrome,"
)

# T자 기준 시트용 추가 지시. 스타일 프롬프트의 '구도를 흔드는' 태그와 충돌하므로
# 아래 제거 목록을 적용 (원문을 그대로 쓰고 싶으면 --verbatim)
POSE = (
    "t-pose, arms outstretched, standing, full body, straight-on, front view, "
    "symmetrical, looking at viewer, simple background, white background, "
    "character sheet, flat lighting"
)
DROP_FROM_STYLE = ["dynamic angle,", "blurry background,", "depth of field,", "location,"]
EXTRA_NEGATIVE = "dynamic angle, from above, from below, foreshortening, cropped, out of frame, "

BOY_UNI = "navy blazer, red necktie, grey slacks, school uniform"
GIRL_UNI = "navy blazer, red ribbon, plaid skirt, school uniform"

CHARACTERS = {
    "mio": f"1girl, solo, short black bob hair, outward flipped hair ends, olive brown eyes, {GIRL_UNI}, oversized blazer sleeves, small notebook strapped to wrist with rubber band, small worn animal keychain, ordinary look",
    "rei": f"1boy, solo, dark silver-grey hair, hair over one eye, cold blue-grey eyes, {BOY_UNI}, metal tie pin, black leather cuffs on both wrists, composed expression",
    "sora": f"1boy, solo, messy light brown hair, big bright eyes, {BOY_UNI}, orange hoodie under blazer, orange paracord bracelet, cheerful smile",
    "ken": f"1boy, solo, neat black hair, sharp eyes, {BOY_UNI}, blazer draped over shoulders, unbuttoned collar, large wristwatch, confident smirk",
    "nana": f"1girl, solo, long silver-white hair in low ponytail, light purple eyes, pale skin, slender, {GIRL_UNI}, white cardigan over uniform, small cross pin, white ribbon wrapped around left wrist like a bandage, gentle expression",
    "riku": f"1boy, solo, orange wavy hair, mischievous grin, vest with bow tie, white gloves, white shirt, grey slacks, school uniform",
    "akari": f"1girl, solo, dark brown high ponytail, round glasses, {GIRL_UNI}, long sleeves, silver wristwatch, neat posture",
    "yuu": f"1boy, solo, black hair, three piercings on one ear, headphones around neck, white shirt, rolled-up sleeves, wristband, grey slacks, school uniform, friendly smile",
    "koto": f"1girl, solo, light brown long hair half-up, gentle light brown eyes, {GIRL_UNI}, long cardigan, red armband on left arm, small gear-shaped pin, kind smile",
    "satsuki": f"1girl, solo, black low ponytail, sharp eyes, {GIRL_UNI}, worn khaki jacket over uniform, leather archery arm guards on both forearms, quiet expression",
    "taiga": f"1boy, solo, very tall, short black buzz cut, muscular, {BOY_UNI}, rolled-up sleeves, white athletic tape on fingers and wrists, earnest expression",
    "rin": f"1girl, solo, short blue-black bob, one light blue hair streak, {GIRL_UNI}, rolled-up sleeves, key chain on belt, key bracelet, playful wink",
    "sho": f"1boy, solo, neat black hair, glasses, gentle eyes, {BOY_UNI}, white shirt, penlight in chest pocket, thin wristwatch, calm expression",
    "ai": f"1girl, solo, petite, black bob with blunt bangs, big eyes, {GIRL_UNI}, apron over uniform, rolled-up sleeves, quiet expression",
    "haruka": f"1girl, solo, light brown short bob, blue hair clip, big brown eyes, bright smile, {GIRL_UNI}, many bracelets on both wrists",
    "kaede": f"1girl, solo, dark navy long straight hair, cool sharp eyes, {GIRL_UNI}, thin silver bracelet, expressionless",
    "lappy": "no humans, solo, rabbit mascot, bipedal, pink fur, large round eyes, one eye glowing red, sharp teeth smile, left ear torn and stitched with red thread, small ribbon at neck, cute but fierce",
}


def build_prompts(name: str, verbatim: bool):
    style = STYLE_POSITIVE
    if not verbatim:
        for token in DROP_FROM_STYLE:
            style = style.replace(token, "")
    positive = f"{CHARACTERS[name]}, {POSE}, {style}"
    negative = NEGATIVE if verbatim else f"{EXTRA_NEGATIVE}{NEGATIVE}"
    return positive, negative


def build_payload(positive: str, negative: str, seed: int):
    return {
        "input": positive,
        "model": MODEL,
        "action": "generate",
        "parameters": {
            "params_version": 3,
            "width": WIDTH,
            "height": HEIGHT,
            "scale": SCALE,
            "sampler": SAMPLER,
            "steps": STEPS,
            "n_samples": 1,
            "ucPreset": 2,
            "qualityToggle": False,
            "autoSmea": False,
            "dynamic_thresholding": False,
            "controlnet_strength": 1,
            "legacy": False,
            "add_original_image": True,
            "cfg_rescale": 0,
            "noise_schedule": NOISE_SCHEDULE,
            "legacy_v3_extend": False,
            "skip_cfg_above_sigma": None,
            "use_coords": False,
            "legacy_uc": False,
            "normalize_reference_strength_multiple": True,
            "inpaintImg2ImgStrength": 1,
            "seed": seed,
            "characterPrompts": [],
            "v4_prompt": {
                "caption": {"base_caption": positive, "char_captions": []},
                "use_coords": False,
                "use_order": True,
            },
            "v4_negative_prompt": {
                "caption": {"base_caption": negative, "char_captions": []},
            },
            "negative_prompt": negative,
            "deliberate_euler_ancestral_bug": False,
            "prefer_brownian": True,
        },
    }


def generate(token: str, positive: str, negative: str, seed: int):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = build_payload(positive, negative, seed)
    for attempt in range(4):
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=180)
        if resp.status_code == 200:
            return resp.content
        if resp.status_code == 429:
            wait = 5 * (attempt + 1)
            print(f"  429 (요청 과다) → {wait}초 후 재시도")
            time.sleep(wait)
            continue
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    raise RuntimeError("재시도 횟수 초과")


def save_zip(content: bytes, out_dir: str, name: str, seed: int):
    saved = []
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for i, member in enumerate(zf.namelist()):
            path = os.path.join(out_dir, f"{name}_{seed}_{i}.png")
            with open(path, "wb") as f:
                f.write(zf.read(member))
            saved.append(path)
    return saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", choices=list(CHARACTERS.keys()))
    parser.add_argument("--n", type=int, default=1, help="캐릭터당 장수")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--verbatim", action="store_true", help="스타일 프롬프트 원문 그대로 사용")
    parser.add_argument("--out", default="tpose_out")
    args = parser.parse_args()

    token = os.environ.get("NAI_TOKEN") or os.environ.get("NOVELAI_API_KEY")
    if not token:
        sys.exit("환경변수 NAI_TOKEN 에 토큰을 설정하세요.")

    os.makedirs(args.out, exist_ok=True)
    names = args.only or list(CHARACTERS.keys())
    for name in names:
        positive, negative = build_prompts(name, args.verbatim)
        for _ in range(args.n):
            seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
            print(f"[{name}] seed={seed}")
            try:
                content = generate(token, positive, negative, seed)
                for p in save_zip(content, args.out, name, seed):
                    print("  saved:", p)
            except Exception as e:
                print("  실패:", e)
            time.sleep(3)


if __name__ == "__main__":
    main()
