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
    "standing, feet together, arms at sides, relaxed pose, full body, straight-on, front view, "
    "looking at viewer, simple background, white background, "
    "character sheet, flat lighting"
)
DROP_FROM_STYLE = ["dynamic angle,", "blurry background,", "depth of field,", "location,"]
EXTRA_NEGATIVE = "t-pose, arms outstretched, arms up, dynamic angle, from above, from below, foreshortening, cropped, out of frame, "

BOY_UNI = "navy blazer, red necktie, grey slacks, long trousers, school uniform"
GIRL_UNI = "navy blazer, red ribbon, plaid skirt, school uniform"
MALE = "male focus, masculine body, broad shoulders, flat chest, narrow hips, long legs"
MALE_NEG = "androgynous, feminine body, wide hips, curvy, breasts, thick thighs, 1girl, "
STAND_NEG = "glasses, eyewear, hand on hip, hands on hips, hand in pocket, hands in pockets, walking, one leg forward, wind, windblown, "
NO_STREAK_NEG = "multicolored hair, streaked hair, colored inner hair, gradient hair, colored tips, "

CHARACTERS = {
    "mio": f"1girl, solo, short black bob hair, outward flipped hair ends, olive brown eyes, small and slight, {GIRL_UNI}, oversized blazer sleeves covering hands, 2::small notebook strapped to left wrist with rubber band::, hands at sides, small worn rabbit keychain with red-stitched ear hanging from blazer pocket, pen tucked behind ear, ink-stained fingertips, bookmark ribbon sticking out of blazer pocket, black knee socks, plain ordinary look, shy faint smile",
    "rei": f"1boy, solo, tall slender, {MALE}, short dark ash-grey hair with bluish tint, 1.5::long bangs covering right eye, hair over one eye::, cold blue-grey eyes, {BOY_UNI}, grey vest under blazer, 1.3::metal tie pin::, 1.4::black leather wrist cuffs on both wrists::, black leather shoes, antique pocket watch with silver chain on vest, upright posture, expressionless, aristocratic",
    "sora": f"1boy, solo, athletic build, {MALE}, messy spiky golden-blonde hair, ahoge, red headband around forehead, big bright orange eyes, {BOY_UNI}, 1.4::orange hoodie under blazer::, 1.3::orange paracord bracelet::, small fire-department badge on blazer, white sneakers, 1.3::standing still, legs straight and together, symmetrical stance::, both feet flat on ground, hands at sides, reflective stripe armband, carabiner clipped to belt, energetic wide grin",
    "ken": f"1boy, solo, lean, {MALE}, wavy dark wine-red hair swept to one side, sharp amber eyes, 1.3::blazer draped over shoulders, not wearing sleeves::, white shirt, unbuttoned collar, loosened black necktie, grey slacks, 1.2::large gold wristwatch::, silver ring, small beauty mark under eye, 1.2::five-yen coin on string necklace like a hypnosis pendulum::, small half theatre mask hanging at belt, confident smirk, theatrical, 1.3::both arms straight down at sides::, standing straight, feet together",
    "nana": f"1girl, solo, slender, silver-white hair in a low ponytail resting over shoulder, chest-length hair, white hair ribbon, light purple eyes, pale skin, {GIRL_UNI}, 1.3::white cardigan over uniform::, small cross pin, 1.5::short white ribbon bandage wrapped around left wrist, ribbon tied in small bow::, hands at sides, white knee socks, forget-me-not flower hairpin, herbal tea sachet charm on cardigan, gentle soft smile",
    "riku": f"1boy, solo, slim, {MALE}, short wavy orange hair, golden eyes, 1.2::mischievous grin::, 1.2::tiny mini top hat clipped to hair::, grey vest, 1.2::black bow tie::, 1.3::white gloves::, white shirt, 1.3::long grey trousers::, playing card tucked in vest pocket, joker playing card in vest pocket, coin between fingers, magician style, standing still, hands at sides, legs together",
    "akari": f"1girl, solo, tidy, auburn red-brown high ponytail with dark green scrunchie, green eyes, {GIRL_UNI}, 1.2::long sleeves buttoned at wrists::, 1.3::silver wristwatch on left wrist::, white knee socks, straight neat posture, clock-shaped hair pin, small hourglass charm on watch, medical cross tag on blazer, serious expression, pen in blazer pocket",
    "yuu": f"1boy, solo, slim, {MALE}, short messy bright teal hair, 1.2::masculine face, defined jaw, adam's apple::, purple eyes, 1.3::three silver piercings on one ear::, 1.4::big headphones around neck::, white shirt untucked, no blazer, rolled-up sleeves, black wristband, 1.3::loose baggy straight-leg grey trousers::, guitar pick necklace, red sneakers, music note earring, sound wave pin on shirt, friendly open smile, hands at sides",
    "koto": f"1girl, solo, caramel brown long hair half-up with small flower hair ornament, gentle light brown eyes, {GIRL_UNI}, 1.3::long beige cardigan under blazer, long sleeves::, 1.4::red armband on left arm::, small gear-shaped pin, beige loafers, small rule notebook and clipboard pin, red thread tied around ring finger, kind smile, class representative",
    "satsuki": f"1girl, solo, athletic, dark forest-green hair in short low ponytail with braided cord, sharp violet eyes, {GIRL_UNI}, 1.3::worn khaki jacket over uniform::, 1.4::brown leather archery arm guards on both forearms::, black ankle boots, black shadow-colored scarf, feather charm on cord, arms straight at sides, quiet stern expression",
    "taiga": f"1boy, solo, very tall, huge, {MALE}, short black buzz cut, handsome sharp face, muscular arms, tall strong build, earnest eyes, {BOY_UNI}, 1.2::rolled-up sleeves::, 1.4::white athletic tape on fingers and wrists::, whistle on cord around neck, patrol armband, black judo belt tied around waist over uniform, determined expression",
    "rin": f"1girl, solo, small, short blue-black bob, 1.3::one single light blue hair streak::, hazel eyes, {GIRL_UNI}, oversized yellow hoodie under blazer, rolled-up sleeves, 1.3::ring of keys on belt::, 1.3::key-shaped bracelet::, mismatched socks, lockpick tools tucked in hair, small cat-eye mask pushed up on head, playful wink, tongue out",
    "sho": f"1boy, solo, tall slender, {MALE}, neat short dark chocolate-brown hair, gentle teal eyes, {BOY_UNI}, grey knit vest, white shirt, 1.3::penlight in chest pocket::, thin wristwatch, adhesive bandage on cheek, bandaged knuckles, calm composed expression",
    "ai": f"1girl, solo, petite, short, mint-green bob with blunt bangs, big rose-pink eyes, {GIRL_UNI}, 1.4::white apron over uniform::, 1.2::small white kerchief on head::, rolled-up sleeves, small ladle in apron pocket, large name tag pinned on apron, kitchen timer pendant, quiet expression",
    "haruka": f"1girl, solo, strawberry pink short bob, 1.4::blue hair clip::, big brown eyes, cat paw charm on bracelets, bright cheerful open smile, {GIRL_UNI}, 1.3::many colorful bracelets on both wrists::, cardigan tied around waist, small camera on strap, loose white socks",
    "kaede": f"1girl, solo, tall, dark navy long straight hair with silver hairpin, snowflake hairpin, pale ice-blue ribbon accents, stopwatch pendant, cool sharp grey-blue eyes, {GIRL_UNI}, black tights, 1.3::thin silver bracelet::, 1.2::wristwatch::, expressionless, elegant posture",
    "lappy": "no humans, solo, 1.3::tiny cute pink rabbit mascot plushie::, chibi, small short body, big round head, standing upright on two legs, stubby arms, one eye glowing red, other eye dark, 1.2::angry eyebrows::, sharp fangs grin, 1.3::left ear torn and stitched with red thread::, small ribbon at neck, cute but fierce, stuffed toy",
}

# earlier exit from the story -> more attractive design (player attachment)
TOP = "1.3::extremely beautiful face::, extremely detailed beautiful eyes, sparkling eyes, long eyelashes, glamorous, elegant, striking charm, eye-catching design"
TOP_BOY = "bishounen, handsome, "
TOP_SET = {"taiga", "sho", "yuu", "akari", "riku", "sora", "ken"}
MID = "pretty face, detailed beautiful eyes"
MID_SET = {"rei", "haruka", "satsuki", "nana"}
MALES = {"rei", "sora", "ken", "riku", "yuu", "taiga", "sho"}


def build_prompts(name: str, verbatim: bool):
    style = STYLE_POSITIVE
    if not verbatim:
        for token in DROP_FROM_STYLE:
            style = style.replace(token, "")
    tier = ""
    if name in TOP_SET:
        tier = (TOP_BOY if name in MALES else "") + TOP + ", "
    elif name in MID_SET:
        tier = MID + ", "
    positive = f"{CHARACTERS[name]}, {tier}{POSE}, {style}"
    if verbatim:
        return positive, NEGATIVE
    extra = EXTRA_NEGATIVE + STAND_NEG
    if name in MALES:
        extra += MALE_NEG
    if name not in ("rin", "lappy"):
        extra += NO_STREAK_NEG
    if name == "lappy":
        extra += "realistic, quadruped, on all fours, sitting, large, huge, fur detail, horror, gore, "
    return positive, extra + NEGATIVE


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
