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
import json
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
    "standing, full body, straight-on, front view, "
    "looking at viewer, simple background, white background, "
    "character sheet, flat lighting"
)
DROP_FROM_STYLE = ["dynamic angle,", "blurry background,", "depth of field,", "location,"]
EXTRA_NEGATIVE = "t-pose, arms outstretched, arms up, dynamic angle, from above, from below, foreshortening, cropped, out of frame, "

BOY_UNI = "navy blazer, red necktie, grey slacks, long trousers, school uniform"
GIRL_UNI = "navy blazer, red ribbon, plaid skirt, school uniform"
MALE = "male focus, masculine body, broad shoulders, flat chest, narrow hips, long legs"
MALE_NEG = "androgynous, feminine body, wide hips, curvy, breasts, thick thighs, 1girl, "
STAND_NEG = "glasses, eyewear, school blazer, plaid skirt, walking, running, jumping, wind, windblown, "
NO_STREAK_NEG = "multicolored hair, streaked hair, colored inner hair, gradient hair, colored tips, "

# v3 : 인물마다 고유 의상(V3식 개인 복장) · 체형 · 시그니처 포즈 · 겹치지 않는 머리색
CHARACTERS = {
    "mio": f"1girl, solo, protagonist, main character, slim average height, glossy blue-black short bob hair, 1.3::big ahoge::, one long side lock tied with red thread, 1.2::bright amber eyes, determined eyes::, 1.3::oversized black hooded short coat with red lining::, white sailor collar blouse, red neckerchief, dark pleated skirt, black thighhighs, 2::small notebook strapped to left wrist with rubber band::, worn pink rabbit keychain with red-stitched ear on coat zipper, pen behind ear, slight confident smile",
    "rei": f"1boy, solo, very tall, slender, {MALE}, platinum silver hair, 1.5::long bangs covering right eye, hair over one eye::, cold blue-grey eyes, 1.3::long black high-collar frock coat with silver buttons::, grey waistcoat, white cravat, black gloves, 1.4::black leather wrist cuffs::, antique pocket watch chain on waistcoat, black dress trousers, polished boots, aloof cold expression, aristocrat",
    "sora": f"1boy, solo, athletic muscular build, {MALE}, spiky sunny golden blonde hair, ahoge, red headband, big bright orange eyes, 1.4::orange firefighter turnout jacket with yellow reflective stripes, sleeves tied around waist::, black fitted t-shirt, cargo pants, heavy boots, carabiner on belt, huge energetic grin, sunny",
    "ken": f"1boy, solo, tall lean, {MALE}, wavy deep wine-red hair swept to one side, half-lidded sharp amber eyes, beauty mark under eye, 1.3::burgundy stage tailcoat draped over shoulders like a cape::, open-collar black shirt, loose red cravat, white gloves, half theatre mask at belt, black slacks, smirk, one corner of mouth raised, theatrical",
    "nana": f"1girl, solo, short, slender fragile frame, soft lilac lavender hair in low side ponytail over shoulder, white hair ribbon, pale violet eyes, pale skin, 1.3::long white nurse-style one-piece dress with pale blue collar::, cream knit cardigan, 1.5::white ribbon wrapped like bandage around left wrist::, forget-me-not hairpin, gentle shy smile, slightly sad eyes",
    "riku": f"1boy, solo, short, slim boyish frame, {MALE}, curly tangerine orange hair, golden cat-like eyes, 1.2::tiny black mini top hat on head::, 1.3::short black magician tailcoat::, red vest, black bow tie, white gloves, checkered shorts over black tights, ankle boots, mischievous grin, sticking tongue out, trickster",
    "akari": f"1girl, solo, average height, neat slim figure, chestnut auburn high ponytail with dark green scrunchie, green eyes, 1.3::white pharmacist lab coat over green turtleneck::, long sleeves buttoned at wrists, dark green pencil skirt, clock-shaped hairpin, 1.3::silver wristwatch::, hourglass charm, clipboard tucked under arm, serious earnest expression, slight blush",
    "yuu": f"1boy, solo, lanky, {MALE}, 1.2::masculine face, defined jaw::, messy bright cyan-teal hair, purple eyes, 1.3::three silver piercings on one ear::, 1.4::big headphones around neck::, 1.3::black leather jacket over white band t-shirt::, ripped black jeans, chain wallet, red high-top sneakers, guitar pick necklace, wide friendly grin",
    "koto": f"1girl, solo, tall, mature calm figure, long honey caramel brown hair half-up with flower ornament, gentle light brown eyes, 1.3::traditional long navy sailor uniform with long skirt::, long beige cardigan, 1.4::red armband on left arm::, small gear-shaped pin, red thread tied on ring finger, kind warm smile, class president, motherly",
    "satsuki": f"1girl, solo, tall, toned athletic build, deep moss green hair in short low ponytail with braided cord, sharp violet eyes, 1.3::worn khaki hunting jacket::, black turtleneck, cargo trousers, laced combat boots, 1.4::brown leather archery arm guards::, black scarf around neck, feather charm, quiet stern expression",
    "taiga": f"1boy, solo, 1.4::very tall, huge, muscular, broad body::, {MALE}, short black buzz cut, thick eyebrows, rugged handsome face, earnest eyes, 1.4::white judo gi jacket open over black t-shirt::, black belt, athletic tape on fingers, whistle around neck, patrol armband, sweatpants, loud confident grin",
    "rin": f"1girl, solo, 1.3::petite, small and short, slim::, short deep violet purple bob with messy bangs, hazel eyes, 1.3::oversized lemon yellow hoodie::, denim shorts, black tights, mismatched socks, sneakers, 1.3::ring of many keys on belt::, key bracelet, cat-eye mask pushed up on head, playful wink, tongue out",
    "sho": f"1boy, solo, tall, broad shoulders, {MALE}, tousled ash brown hair, tired gentle teal eyes, 1.3::navy medical scrub shirt under long grey cardigan::, stethoscope around neck, penlight in chest pocket, adhesive bandage on cheek, bandaged knuckles, dark slacks, calm awkward faint smile",
    "ai": f"1girl, solo, 1.4::petite, very short, tiny frame::, mint green bob with blunt bangs, big rose-pink eyes, 1.4::white double-breasted chef coat::, 1.2::small white kerchief on head::, short apron, rolled-up sleeves, quiet expressionless face, sleepy eyes",
    "haruka": f"1girl, solo, average height, soft round face, strawberry pink short bob, 1.4::blue hair clip::, big brown eyes, 1.3::pastel pink oversized cardigan::, white blouse, denim overall skirt, loose white socks, sneakers, 1.3::many colorful bracelets::, cat paw charm, bright cheerful open smile",
    "kaede": f"1girl, solo, tall, slender model-like long legs, very long straight deep navy blue hair, snowflake hairpin, cool grey-blue eyes, 1.3::long navy coat over white turtleneck::, black pleated long skirt, black tights, ankle boots, thin silver bracelet, cool expressionless face, elegant",
    "lappy": "no humans, solo, 1.3::tiny cute pink rabbit mascot plushie::, chibi, small short body, big round head, standing upright on two legs, stubby arms, one eye glowing red, other eye dark, 1.2::angry eyebrows::, sharp fangs grin, 1.3::left ear torn and stitched with red thread::, small ribbon at neck, cute but fierce, stuffed toy",
}

SIGNATURE = {
    "mio": "1.2::right hand holding pen against notebook::",
    "rei": "1.3::arms crossed::",
    "sora": "1.3::thumbs up, other hand on hip::",
    "ken": "1.4::holding five-yen coin on string like hypnosis pendulum in raised hand::",
    "nana": "1.2::hands clasped in front of chest::",
    "riku": "1.4::fanning playing cards in one hand, joker card on top::",
    "akari": "1.2::one hand touching hairpin::",
    "yuu": "1.2::hands in jacket pockets::",
    "koto": "1.3::holding clipboard against chest::",
    "satsuki": "1.3::arms crossed::",
    "taiga": "1.3::pumping fist, flexing arm::",
    "rin": "1.3::twirling key ring on finger, peace sign::",
    "sho": "1.2::one hand rubbing back of neck::",
    "ai": "1.3::holding ladle with both hands::",
    "haruka": "1.3::holding camera up, peace sign::",
    "kaede": "1.4::holding stopwatch near chin::"
}

# earlier exit from the story -> more attractive design (player attachment)
TOP = "1.3::extremely beautiful face::, extremely detailed beautiful eyes, sparkling eyes, long eyelashes, glamorous, elegant, striking charm, eye-catching design"
TOP_BOY = "bishounen, handsome, "
HERO = "1.3::striking protagonist presence::, beautiful face, detailed beautiful eyes"
TOP_SET = {"taiga", "sho", "yuu", "akari", "riku", "sora", "ken"}
MID = "pretty face, detailed beautiful eyes"
MID_SET = {"rei", "haruka", "satsuki", "nana"}
MALES = {"rei", "sora", "ken", "riku", "yuu", "taiga", "sho"}


POSES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art", "poses.json")
SPRITE_FRAME = "cowboy shot, upper body to thighs, front view, looking at viewer, simple background, white background, flat lighting"


def pose_tags(name: str, pose: str):
    """C01 = 시그니처, 그 외는 art/poses.json 의 common / 인물별 태그."""
    if pose in (None, "", "C01"):
        return SIGNATURE.get(name, "")
    data = json.load(open(POSES_PATH, encoding="utf-8"))
    tags = data.get(name, {}).get(pose) or data["common"].get(pose)
    if tags is None:
        sys.exit(f"포즈 {pose} 가 {name} 에 정의되어 있지 않습니다.")
    return tags


def build_prompts(name: str, verbatim: bool, pose: str = None):
    style = STYLE_POSITIVE
    if not verbatim:
        for token in DROP_FROM_STYLE:
            style = style.replace(token, "")
    tier = ""
    if name in TOP_SET:
        tier = (TOP_BOY if name in MALES else "") + TOP + ", "
    elif name == "mio":
        tier = HERO + ", "
    elif name in MID_SET:
        tier = MID + ", "
    frame = POSE if pose is None else SPRITE_FRAME
    act = pose_tags(name, pose)
    positive = f"{CHARACTERS[name]}, {act + ', ' if act else ''}{tier}{frame}, {style}"
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
    parser.add_argument("--pose", nargs="*", default=None, help="포즈 ID (예: C02 T01 U3 M X1). 없으면 전신 기준 입상")
    args = parser.parse_args()

    token = os.environ.get("NAI_TOKEN") or os.environ.get("NOVELAI_API_KEY")
    if not token:
        sys.exit("환경변수 NAI_TOKEN 에 토큰을 설정하세요.")

    os.makedirs(args.out, exist_ok=True)
    names = args.only or list(CHARACTERS.keys())
    jobs = [(name, pose) for name in names for pose in (args.pose or [None])]
    for name, pose in jobs:
        positive, negative = build_prompts(name, args.verbatim, pose)
        tag = name if pose is None else f"{name}_{pose}"
        for _ in range(args.n):
            seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
            print(f"[{tag}] seed={seed}")
            try:
                content = generate(token, positive, negative, seed)
                for p in save_zip(content, args.out, tag, seed):
                    print("  saved:", p)
            except Exception as e:
                print("  실패:", e)
            time.sleep(3)


if __name__ == "__main__":
    main()
