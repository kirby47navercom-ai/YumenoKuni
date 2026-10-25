#!/usr/bin/env python3
"""
사망 CG · 배경 생성 (NovelAI V5, 가로 1216×832 → 1920×1080 으로 맞춤)
  $env:NAI_TOKEN = "..."   (토큰은 환경변수로만)
  python tools/generate_scene_nai.py --death            # 사망 CG 6장 → art/cg/death_*.png
  python tools/generate_scene_nai.py --bg               # 배경 전부 → bg/{이름}.png
  python tools/generate_scene_nai.py --bg plaza_day vip_505   # 일부만
  --n 2  후보 수(같은 이름_후보번호 로 art/_candidates/scene 에 저장, 첫 장은 본 경로에도)
인물 생김새는 generate_tpose_nai.CHARACTERS 를 그대로 쓴다. 사인·현장은 각 장 1Nb 수사 문서(래피 파일)와 맞춘다.
"""
import argparse
import os
import random
import sys
import time

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_tpose_nai as nai  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
nai.WIDTH, nai.HEIGHT = 1216, 832
STYLE = nai.STYLE_POSITIVE.replace("-3::empty eyes, artist collaboration,doll::,", "-3::artist collaboration,doll::,")
NEG = nai.NEGATIVE.replace("plants, grass, leaves, ", "").replace("empty eyes, ", "")
PARK = "pastel pink and mint amusement park theme, rabbit motif decorations, danganronpa style background, highly detailed interior"

# ---- 사망 CG : 배경 판(현장·보라 피 웅덩이, 사람 없음) + 인물(쓰러진 자세, 흰 배경) 을 따로 뽑아 합성 ----
# 인물은 분명히 죽어 있는 모습(자는 것처럼 보이지 않게). 피는 보라색, 상처 묘사 없음.
DEAD = ("1.8::corpse, dead, death::, 1.6::lying on back on the floor, motionless, arms limp, body sprawled flat::, "
        "1.5::expressionless, slack face, mouth slightly open, dull glassy unfocused eyes, no highlight in eyes::, pale grey skin, "
        "1.7::purple blood::, 1.6::purple blood on face, purple blood on clothes, purple blood pool under body::, purple blood splatter, "
        "1.6::full body, whole body visible, head to toe::, 1.4::from directly above, overhead view, wide shot::, simple background, white background")
DEAD_NEG = ("2::multiple people, 2boys, 2girls, multiple bodies, duplicate, another person, bystander::, 1.6::sleeping, asleep, peaceful, resting, closed eyes, smile, grimace, angry, teeth, clenched teeth, frown, alive expression::, 1.6::crawling, all fours, kneeling, sitting, reaching, fighting, action pose::, 2::red blood::, 1.5::cropped, out of frame, cut off legs, close-up::, red blood, 1.5::gore, guts, exposed organs, dismemberment::, "
            "nsfw, cleavage, panties, underwear, upskirt, 1.2::alive, standing, looking at viewer::, scenery, background objects, ")
PLATE = "1.5::no humans, scenery::, 1.5::large pool of purple blood on the floor in the center::, purple blood splatter, crime scene, ominous dramatic lighting, high contrast shadows, from above, cinematic wide shot"
# 이름 : (인물, 인물 자세, 현장, 합성 위치 cx·cy(0~1) · 폭 비율)
DEATHS = {  # 이름 : (인물, 자세·상처(사인과 일치), 현장, 합성 위치, 피 웅덩이)
    "death_1_taiga": ("taiga", "lying on back, 1.5::crushed chest, purple blood from mouth, purple bloodstain spreading on chest::, small red pressure mark on side of neck below ear",
                      "night, empty carousel platform under purple neon light, giant pink horse figure no.7 lowered to the floor, whistle on red cord on the floor, twisted horse statue", (.52, .64, .5), True),
    "death_2_yuu": ("yuu", "lying face down, 1.5::soaking wet clothes and hair, water dripping, bluish lips::, no wound, headphones missing",
                    "evening poolside of an indoor water park, pool edge, headphones floating on the water, soda can rolled away, wet tiles, puddle of water", (.46, .64, .48), False),
    "death_3a_riku": ("riku", "lying on back, 1.5::purple blood pool spreading under body, purple blood from head::, limbs bent, white gloved hand reaching out",
                      "theater rigging room, huge fallen sandbag on the floor, scattered playing cards, a single joker card, black mini top hat fallen", (.5, .64, .46), True),
    "death_3b_sora": ("sora", "1.4::slumped sitting against a wall, head drooping::, 1.6::head wound with purple blood running down face, purple blood on shoulder and chest::, legs out",
                      "dark theater sound control room with mixing consoles, purple blood splatter on the wall, shadow of an axe on the wall, red headband on the floor", (.62, .6, .34), True),
    "death_4_haruka": ("haruka", "collapsed on the floor on her side, one hand raised toward a door, 1.4::broken fingernails with purple blood on fingertips::, deathly pale, bluish lips, no other wound",
                       "luxury hotel room no.505, closed locked door with purple-stained scratch marks, camera dropped on the carpet", (.46, .66, .46), False),
    "death_5_nana": ("nana", "lying on her side, 1.7::crossbow bolt stuck in chest, purple blood around the wound, purple bloodstain on cardigan::, arm stretched",
                     "narrow aisle between tall bookshelves in a castle library, scattered herb leaves, fallen books, table clock on a shelf", (.5, .64, .46), True),
}

# ---- 배경 : 사람 없음, V3 「무대 세트」 같은 실내외 ----
BG = {
    "plaza_day": "central plaza of an amusement park, fountain, pink rabbit statue, capsule toy machine, daytime",
    "plaza_night": "central plaza of an amusement park at night, fountain lit up, pink rabbit statue, neon lights",
    "plaza_dawn": "central plaza of an amusement park at dawn, fountain, pink rabbit statue, pale morning light",
    "main_gate": "grand entrance gate of an abandoned amusement park, closed iron gate, rabbit emblem",
    "hotel_lobby": "lobby of a fancy theme park hotel, reception desk, key cabinet, chandelier",
    "hotel_lounge_day": "hotel lounge with big windows overlooking the park, sofas, bookshelves, daytime",
    "hotel_dining": "hotel dining hall, long table with white cloth, buffet counter",
    "hotel_corridor": "hotel guest floor corridor, row of room doors, carpet, wall lamps",
    "hotel_laundry_day": "hotel laundry room, washing machines, laundry baskets",
    "hotel_stairs_day": "hotel staircase, landing, emergency light",
    "mio_room_day": "small hotel guest room, single bed, desk with notebook, window, daytime",
    "mio_room_night": "small hotel guest room at night, single bed, desk lamp on, moonlight through window",
    "info_center_day": "information center of an amusement park, reception counter, lost and found shelves, park map",
    "foodcourt": "amusement park food court named sweet palette, counters, tables, pastel decorations",
    "food_kitchen_day": "commercial kitchen behind a food court, stoves, steel counters",
    "food_backdoor_day": "back door of a food court, service corridor, trash bins, staff only sign",
    "food_storage_day": "food storage room, shelves of boxes, locked cage",
    "carousel_day": "merry-go-round platform, pink and gold carousel horses, numbered horses",
    "carousel_control": "carousel control booth, control panel with levers, log printer, ticket booth key box",
    "carousel_machine_day": "carousel machine room underneath, gears, central pillar mechanism",
    "carousel_ticket_day": "carousel ticket booth, key card box",
    "souvenir_shop": "amusement park souvenir shop, plush toys, rabbit dolls, costume corner",
    "shop_costume_day": "costume corner of a souvenir shop, costumes on racks, mirrors",
    "infirmary": "park infirmary, beds with curtains, medicine cabinet",
    "clinic_pharmacy_day": "infirmary pharmacy room, locked medicine shelves, inventory clipboard",
    "waterpark_day": "indoor water park, wave pool, water slides, daytime",
    "waterpark_night": "indoor water park at night, wave pool lit by underwater lights",
    "waterpark_snack_day": "water park snack bar, vending machine, trash bin, plastic tables",
    "waterpark_pump_day": "water park pump room, pipes, valves, wave timer panel",
    "parade_street_day": "parade street of an amusement park, parade floats, flags, small stage",
    "mirror_maze_1": "mirror maze interior, endless reflections, pink neon",
    "mirror_center": "central hall of a mirror maze, circular room of mirrors",
    "ferris_boarding": "ferris wheel boarding platform at dusk, gondolas",
    "ferris_gondola": "inside a ferris wheel gondola, seats, view of the park at night",
    "theater_lobby": "lobby of a dream theater, red carpet, posters, ticket counter",
    "theater_stage": "theater stage seen from the seats, red curtains, spotlights",
    "theater_seats_1f": "theater auditorium seats, aisle, dim lights",
    "theater_rigging": "theater rigging room above the stage, ropes, pulleys, sandbags, lever with safety pin",
    "theater_sound": "theater sound control room, mixing console, monitors, heavy door",
    "rollercoaster_platform": "roller coaster boarding platform, sleeping coaster train, night",
    "rollercoaster_maintenance": "roller coaster maintenance building, tools, visitor log on clipboard",
    "rollercoaster_generator": "generator room, big generator, cables, warning signs",
    "rollercoaster_inspection": "coaster inspection track walkway, rails, lamps",
    "vip_hall_a": "luxury hotel fifth floor VIP corridor with four room doors and a linen storage door, posters",
    "vip_hall_b": "luxury hotel fifth floor VIP corridor with five room doors, posters",
    "vip_505": "luxury hotel room no.505, bed, window, door with outside latch",
    "vip_linen": "hotel linen storage room, shelves of folded sheets",
    "vip_gallery": "hotel gallery hall with framed photographs on walls",
    "castle_hall": "grand banquet hall inside a dream castle, chandeliers, long table, screen for a film showing",
    "castle_library": "castle library, tall bookshelves, narrow aisles, reading desks, table clock",
    "castle_tower": "clock tower interior, big clock mechanism, bell",
    "castle_vault": "castle treasure vault, display cases, entry log device",
    "core_hall": "underground core hall, glowing blue core, railing, cold industrial dream machine",
    "core_control": "core control room, monitors, old terminals, dust",
    "core_shelter": "underground shelter room, cots, emergency supplies",
    "trial_elevator": "descending elevator cage to a courtroom, red light, iron bars",
}


def fit(src, dst):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    tw, th = 1920, 1080
    scale = max(tw / w, th / h)
    im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    l, t = (im.width - tw) // 2, (im.height - th) // 2
    im.crop((l, t, l + tw, t + th)).save(dst)


def cutout(src):
    """흰 배경 인물 → 투명 (rembg, 애니 모델)"""
    from rembg import new_session, remove
    global _session
    try:
        _session
    except NameError:
        _session = new_session("isnet-anime")
    im = remove(Image.open(src).convert("RGB"), session=_session).convert("RGBA")
    # 반투명 잔여(바닥 그림자·흰 테두리)를 걷어 낸다
    a = im.getchannel("A").point(lambda v: 0 if v < 120 else min(255, int((v - 120) * 255 / 100)))
    im.putalpha(a)
    return im


def composite(plate, figure, place, dst, bleed=True):
    """판 위에 인물 : 크기·위치, 판 평균색으로 살짝 물들이고, 바닥 접촉 그림자"""
    from PIL import ImageFilter, ImageEnhance, ImageChops
    bg = Image.open(plate).convert("RGB")
    W, H = bg.size
    fg = cutout(figure)
    box = fg.getbbox()
    fg = fg.crop(box)
    cx, cy, frac = place
    w = int(W * frac)
    fg = fg.resize((w, int(fg.height * w / fg.width)), Image.LANCZOS)
    if fg.height > H * .8:
        fg = fg.resize((int(fg.width * H * .8 / fg.height), int(H * .8)), Image.LANCZOS)
    x, y = int(W * cx - fg.width / 2), int(H * cy - fg.height / 2)
    # 조명 맞추기 : 판 주변 평균색과 25% 섞고 밝기를 판에 맞춘다
    region = bg.crop((max(0, x), max(0, y), min(W, x + fg.width), min(H, y + fg.height))).resize((1, 1), Image.BOX).getpixel((0, 0))
    rgb, alpha = fg.convert("RGB"), fg.getchannel("A")
    tint = Image.new("RGB", rgb.size, region)
    rgb = Image.blend(rgb, ImageChops.multiply(rgb, tint), .35)
    rgb = ImageEnhance.Brightness(rgb).enhance(.85)
    # 그림자 : 알파를 흐리게 해 아래로 조금 민다
    shadow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    sa = alpha.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * .6))
    shadow.paste(Image.new("RGBA", fg.size, (20, 0, 30, 255)), (x + 10, y + 18), sa)
    out = Image.alpha_composite(bg.convert("RGBA"), shadow)
    # 보라 피 웅덩이 : 몸 실루엣을 넓히고 흐리게 해 몸 아래로 번지게
    rnd = random.Random(hash(dst) & 0xffff)
    pool = alpha.filter(ImageFilter.MaxFilter(41)).filter(ImageFilter.GaussianBlur(14))
    blobs = Image.new("L", fg.size, 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(blobs)
    for _ in range(14):
        r = rnd.randint(fg.width // 14, fg.width // 6)
        px, py = rnd.randint(fg.width // 5, fg.width * 4 // 5), rnd.randint(fg.height // 3, fg.height)
        d.ellipse((px - r, py - r * .55, px + r, py + r * .55), fill=235)
    pool = ImageChops.multiply(pool, blobs.filter(ImageFilter.GaussianBlur(10)).point(lambda v: min(255, v * 2)))
    if bleed:
        out.paste(Image.new("RGBA", fg.size, (118, 22, 150, 255)), (x + 6, y + 14), pool.point(lambda v: int(v * .92)))
        gloss = pool.filter(ImageFilter.GaussianBlur(6)).point(lambda v: 60 if v > 200 else 0)
        out.paste(Image.new("RGBA", fg.size, (210, 150, 255, 255)), (x + 2, y + 8), gloss)
    edge = alpha.filter(ImageFilter.GaussianBlur(1.2))  # 가장자리를 부드럽게
    out.paste(rgb, (x, y), edge)
    out.convert("RGB").save(dst)


def run(token, name, positive, negative, dst, n, raw=False):
    cand = os.path.join(ROOT, "art", "_candidates", "scene")
    os.makedirs(cand, exist_ok=True)
    for k in range(n):
        seed = random.randint(0, 2**32 - 1)
        print(f"[{name}] seed={seed}", flush=True)
        try:
            for p in nai.save_zip(nai.generate(token, positive, negative, seed), cand, name, seed):
                with open(p[:-4] + ".txt", "w", encoding="utf-8") as f:
                    f.write(f"model: {nai.MODEL}\nsize: {nai.WIDTH}x{nai.HEIGHT}\nseed: {seed}\n\n[positive]\n{positive}\n\n[negative]\n{negative}\n")
                if k == 0:
                    (Image.open(p).save(dst) if raw else fit(p, dst))
                    print("  →", os.path.relpath(dst, ROOT), flush=True)
        except Exception as e:
            print("  실패:", e, flush=True)
        time.sleep(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--death", nargs="*", default=None)
    ap.add_argument("--bg", nargs="*", default=None)
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--compose", nargs=2, metavar=("NAME", "FIGURE_PNG"), help="고른 인물 후보로 다시 합성(생성 없음)")
    ap.add_argument("--replate", action="store_true", help="사망 CG 배경 판도 다시 뽑는다(기본 : 있으면 재사용)")
    a = ap.parse_args()
    if a.compose:
        name, fig = a.compose
        d = DEATHS[name]
        composite(os.path.join(ROOT, "art", "cg", name + "_bg.png"), fig, d[3], os.path.join(ROOT, "art", "cg", name + ".png"), d[4])
        return
    token = os.environ.get("NAI_TOKEN") or os.environ.get("NOVELAI_API_KEY")
    if not token:
        sys.exit("환경변수 NAI_TOKEN 에 토큰을 설정하세요.")
    if a.death is not None:
        cg = os.path.join(ROOT, "art", "cg")
        os.makedirs(cg, exist_ok=True)
        for name in a.death or DEATHS:
            who, pose, scene, place, bleed = DEATHS[name]
            look = nai.CHARACTERS[who]  # solo 유지 : 시체가 둘 생기지 않게
            plate = os.path.join(cg, name + "_bg.png")
            if a.replate or not os.path.exists(plate):
                tags = PLATE if bleed else PLATE.replace("1.5::large pool of purple blood on the floor in the center::, purple blood splatter, ", "")
                plate_neg = "1.5::1girl, 1boy, people, person, character::, red blood, " + ("" if bleed else "2::blood, purple blood, blood pool, blood splatter::, ")
                run(token, name + "_bg", f"{STYLE} {tags}, {scene}, {PARK}", plate_neg + NEG, plate, 1)
            fig = os.path.join(ROOT, "art", "_candidates", "scene", name + "_fg_src.png")
            dead = DEAD if bleed else DEAD.replace("1.7::purple blood::, 1.6::purple blood on face, purple blood on clothes, purple blood pool under body::, purple blood splatter, ", "")
            fig_neg = DEAD_NEG + ("" if bleed else "2::blood pool, blood splatter, bloodstain on clothes::, ") + (nai.MALE_NEG if "1boy" in look else "") + NEG
            run(token, name + "_fg", f"{STYLE} {look}, {pose}, {dead}", fig_neg, fig, a.n, raw=True)
            if os.path.exists(plate) and os.path.exists(fig):
                composite(plate, fig, place, os.path.join(cg, name + ".png"), bleed)
                print("  합성 →", name, flush=True)
    if a.bg is not None:
        for name in a.bg or BG:
            positive = f"{STYLE} 1.5::no humans, scenery::, {BG[name]}, {PARK}, wide angle, stage set like 3d background"
            negative = "1.5::1girl, 1boy, people, person, character::, " + NEG
            run(token, name, positive, negative, os.path.join(ROOT, "bg", name + ".png"), a.n)


if __name__ == "__main__":
    main()
