#!/usr/bin/env python3
"""
유메노쿠니 캐릭터 입상·포즈 생성 스크립트 (NovelAI V5)

사용법
  1) pip install requests
  2) 토큰은 환경변수로만 전달 (코드/채팅에 직접 쓰지 마세요)
       Windows (PowerShell) : $env:NAI_TOKEN = "pst-..."
       macOS / Linux        : export NAI_TOKEN="pst-..."
  3) python generate_tpose_nai.py                 # 전원(17종) 1장씩
     python generate_tpose_nai.py --only mio rei  # 특정 캐릭터만
     python generate_tpose_nai.py --n 3           # 캐릭터당 3장
     python generate_tpose_nai.py --seed 12345    # 시드 고정(재현)

결과는 art/_candidates/ 에 PNG + 같은 이름의 .txt(모델·시드·프롬프트)로 저장됨.
고른 것은 art/standing/{slug}.png / {slug}.txt 로 옮긴다.
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
MODEL = "nai-diffusion-5-full"
WIDTH, HEIGHT = 832, 1216
STEPS = 28
SCALE = 5.0
SAMPLER = "k_euler_ancestral"
NOISE_SCHEDULE = "karras"

# ---- 사용자가 지정한 스타일 프롬프트 (v5) ----------------------------------
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

# 입상은 흰 배경 단독 컷이 필요하므로 구도를 흔드는 태그는 뺀다(원문 그대로는 --verbatim)
POSE = "standing, full body, front view, looking at viewer, simple background, white background"
DROP_FROM_STYLE = ["dynamic angle,", "blurry background,", "depth of field,", "location,"]
EXTRA_NEGATIVE = "t-pose, arms outstretched, dynamic angle, from above, from below, foreshortening, cropped, out of frame, "

MALE = "male focus, 1.5::masculine face, sharp jawline, adam's apple, thick eyebrows::, masculine body, broad shoulders, flat chest, narrow hips, long legs, short hair"
MALE_NEG = "androgynous, feminine face, girly, effeminate, makeup, long eyelashes, blush, feminine body, wide hips, curvy, breasts, thick thighs, bare legs, shorts, skirt, 1girl, "
STAND_NEG = "glasses, eyewear, walking, running, jumping, wind, windblown, "
NO_STREAK_NEG = "multicolored hair, streaked hair, colored inner hair, gradient hair, colored tips, "

# v4 : 학원 교복을 인물마다 색·형태를 바꿔 개조(단간론파식) · 체형 · 시그니처 포즈 · 머리색 비중복
CHARACTERS = {
    "mio": f"1girl, solo, protagonist, slim average height, 1.7::black hair::, glossy short bob, dark blue hair highlights, 1.3::big ahoge::, one long side lock tied with red thread, 1.2::bright amber eyes, determined eyes::, 1.5::neat fitted black school blazer with red piping, buttoned, white collared shirt, red ribbon tie::, black pleated skirt, black knee socks, brown loafers, 2::small notebook strapped to left wrist with rubber band::, worn pink rabbit keychain with red-stitched ear on blazer pocket, pen in breast pocket, 1.3::tidy, neat, well-groomed, upright posture::, calm confident smile, main heroine",
    "rei": f"1boy, solo, very tall, slender, {MALE}, platinum silver hair, 1.5::long bangs covering right eye, hair over one eye::, cold blue-grey eyes, handsome young man, 1.4::white long gakuran school uniform with black trim and silver buttons, high collar::, black gloves, 1.4::black leather wrist cuffs::, antique pocket watch chain, black trousers, polished boots, aloof cold expression, aristocrat",
    "sora": f"1boy, solo, athletic muscular build, {MALE}, spiky sunny golden blonde hair, ahoge, red headband, big bright orange eyes, 1.4::bright orange school blazer with yellow reflective stripes on sleeves, sleeves rolled up::, black t-shirt underneath, black school trousers, red sneakers, carabiner on belt, huge energetic grin",
    "ken": f"1boy, solo, tall lean, {MALE}, wavy deep wine-red hair swept to one side, sharp amber eyes, beauty mark under eye, handsome young man, 1.4::burgundy school blazer with gold piping worn draped over shoulders like a cape::, open-collar black shirt, loose red ribbon tie, white gloves, half theatre mask at belt, black slacks, black leather shoes, 1.4::full body, feet visible::, smirk, theatrical",
    "nana": f"1girl, solo, short, slender fragile frame, 1.7::lavender hair, light purple hair::, low side ponytail over shoulder, white hair ribbon, pale violet eyes, pale skin, 1.4::white sailor school uniform with pale lavender collar and long white skirt::, cream knit cardigan, 1.5::white ribbon wrapped like bandage around left wrist::, forget-me-not hairpin, gentle shy smile",
    "riku": f"1boy, solo, short, slim but masculine frame, {MALE}, curly tangerine orange hair, golden cat-like eyes, 1.2::tiny black mini top hat on head::, 1.4::black gakuran school uniform with gold buttons, short red-lined cape::, black bow tie, white gloves, 1.3::long black school trousers::, checkered cuffs, black shoes, mischievous grin, trickster",
    "akari": f"1girl, solo, average height, neat slim figure, 1.8::auburn hair, chestnut brown hair::, high ponytail with dark green scrunchie, green eyes, 1.4::dark green school blazer with white trim, buttoned neatly::, white shirt, green plaid skirt, white knee socks, brown loafers, 1.4::full body, feet visible::, long sleeves buttoned at wrists, clock-shaped hairpin, 1.3::silver wristwatch::, hourglass charm, serious earnest expression",
    "yuu": f"1boy, solo, lanky, {MALE}, messy bright cyan-teal hair, purple eyes, 1.3::three silver piercings on one ear::, 1.4::big headphones around neck::, 1.4::open navy gakuran school jacket over white band t-shirt::, loose navy trousers, chain wallet, red high-top sneakers, guitar pick necklace, wide friendly grin",
    "koto": f"1girl, solo, tall, calm graceful figure, long honey caramel brown hair half-up with flower ornament, gentle light brown eyes, 1.4::classic navy sailor school uniform with long navy skirt::, long beige cardigan, 1.4::red armband on left arm::, small gear-shaped pin, red thread tied on ring finger, kind warm smile, class president",
    "satsuki": f"1girl, solo, tall, toned athletic build, 1.7::dark green hair::, short low ponytail with braided cord, sharp violet eyes, 1.4::khaki military-style school blazer with brass buttons::, black skirt, black tights, laced boots, 1.4::brown leather archery arm guards::, black scarf around neck, feather charm, quiet stern expression",
    "taiga": f"1boy, solo, 1.5::very tall, muscular, athletic, broad shoulders, fit::, {MALE}, short black buzz cut, thick eyebrows, rugged handsome face, earnest eyes, 1.4::black gakuran school uniform unbuttoned, white t-shirt underneath::, black judo belt tied over uniform, athletic tape on fingers, whistle around neck, patrol armband, white sneakers, loud confident grin",
    "rin": f"1girl, solo, 1.3::petite, small and short, slim::, 1.7::purple hair, violet hair::, short bob with messy bangs, hazel eyes, 1.4::sky blue sailor school uniform with oversized lemon yellow hoodie underneath::, sky blue skirt, mismatched socks, sneakers, 1.3::ring of many keys on belt::, key bracelet, cat-eye mask pushed up on head, playful wink, tongue out",
    "sho": f"1boy, solo, tall, broad shoulders, {MALE}, tousled ash brown hair, tired gentle teal eyes, 1.4::grey school blazer with teal necktie, knitted sweater vest::, white shirt, penlight in chest pocket, adhesive bandage on cheek, bandaged knuckles, grey slacks, calm awkward faint smile",
    "ai": f"1girl, solo, 1.4::petite, very short, tiny frame::, 1.7::mint green hair, light green hair::, bob cut with blunt bangs, big rose-pink eyes, 1.4::pastel pink school blazer with white frilled apron over it::, 1.2::small white kerchief on head::, white skirt, rolled-up sleeves, quiet expressionless face, sleepy eyes",
    "haruka": f"1girl, solo, average height, soft round face, strawberry pink short bob, 1.4::blue hair clip::, big brown eyes, 1.4::cream yellow school blazer, pink ribbon, cardigan tied around waist::, red plaid skirt, loose white socks, 1.3::many colorful bracelets::, small camera on strap, bright cheerful open smile",
    "kaede": f"1girl, solo, tall, slender model-like long legs, very long straight deep navy blue hair, snowflake hairpin, cool grey-blue eyes, 1.4::ice blue long coat-style school uniform with silver snowflake buttons::, long white pleated skirt, black tights, thin silver bracelet, cool expressionless face, elegant",
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

# 전원 미형. 일찍 퇴장하는 인물은 한 단계 더(플레이어 애착)
BEAUTY = "beautiful face, detailed beautiful eyes"
TOP = "1.3::extremely attractive::, sparkling eyes, striking charm"
TOP_BOY = "bishounen, handsome, "
HERO = "1.4::striking protagonist presence, beautiful heroine::"
TOP_SET = {"taiga", "sho", "yuu", "akari", "riku", "sora", "ken"}
MALES = {"rei", "sora", "ken", "riku", "yuu", "taiga", "sho"}


POSES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art", "poses.json")
SPRITE_FRAME = "cowboy shot, upper body to thighs, front view, looking at viewer, simple background, white background"


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
    tier = "" if name == "lappy" else ("handsome face, detailed eyes, " if name in MALES else BEAUTY + ", ")
    if name in TOP_SET:
        tier += (TOP_BOY if name in MALES else "") + TOP + ", "
    elif name == "mio":
        tier += HERO + ", "
    frame = POSE if pose is None else SPRITE_FRAME
    act = pose_tags(name, pose)
    positive = " ".join(f"{CHARACTERS[name]}, {act + ', ' if act else ''}{tier}{frame}, {style}".split())
    if verbatim:
        return positive, NEGATIVE
    extra = EXTRA_NEGATIVE + STAND_NEG
    if name in MALES:
        extra += MALE_NEG
    if name not in ("rin", "lappy"):
        extra += NO_STREAK_NEG
    if name == "taiga":
        extra += "fat, chubby, obese, barefoot, "
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
    parser.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art", "_candidates"))
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
                    with open(p[:-4] + ".txt", "w", encoding="utf-8") as f:
                        f.write(f"model: {MODEL}\nsize: {WIDTH}x{HEIGHT}  steps: {STEPS}  scale: {SCALE}  sampler: {SAMPLER}\nseed: {seed}\n\n[positive]\n{positive}\n\n[negative]\n{negative}\n")
                    print("  saved:", p)
            except Exception as e:
                print("  실패:", e)
            time.sleep(3)


if __name__ == "__main__":
    main()
