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

# ---- 사망 CG : 분명히 죽어 있는 모습(자는 것처럼 보이지 않게). 피는 보라색, 상처 묘사 없음 ----
DEAD = ("1.6::dead body, corpse, lifeless::, 1.4::limp, collapsed, unnatural sprawled pose::, 1.3::blank lifeless eyes, half-open empty eyes, pale skin::, "
        "1.6::purple blood::, 1.4::pool of purple blood spreading on floor, purple blood splatter::, crime scene, murder scene, ominous dramatic lighting, "
        "high contrast shadows, danganronpa style body discovery, from above, cinematic wide shot")
DEAD_NEG = ("1.6::sleeping, asleep, peaceful, resting, closed eyes, smile::, red blood, 1.5::gore, guts, wound, injury, exposed organs::, "
            "nsfw, cleavage, panties, underwear, upskirt, 1.2::alive, standing, looking at viewer::, ")
DEATHS = {
    "death_1_taiga": ("taiga", "night, empty carousel platform under purple neon light, giant pink horse figure no.7 lowered and crushing down on him, "
                      "lying face down under the carousel horse, arm stretched out, whistle on red cord fallen on the floor, twisted horse statue"),
    "death_2_yuu": ("yuu", "evening poolside of an indoor water park, lying face down at the pool edge, half of the body in the water, "
                    "headphones floating on the water, soda can rolled away, wet tiles"),
    "death_3a_riku": ("riku", "theater rigging room, huge fallen sandbag on the floor, lying crushed beneath the sandbag, white gloved hand sticking out, "
                      "scattered playing cards around, a single joker card, black mini top hat fallen"),
    "death_3b_sora": ("sora", "dark theater sound control room with mixing consoles, slumped sitting against the wall, head drooping, red headband fallen, "
                      "purple blood stain on wall behind him, shadow of an axe on the wall"),
    "death_4_haruka": ("haruka", "luxury hotel room no.505, collapsed on the floor in front of the closed locked door, one hand still raised against the door, "
                       "scratch marks on the door, camera dropped on the carpet, no injury, deathly pale skin, bluish lips"),
    "death_5_nana": ("nana", "narrow aisle between tall bookshelves in a castle library, lying on her side on the floor, a crossbow bolt lying beside her, "
                     "scattered herb leaves, fallen books, table clock visible on a nearby shelf"),
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


def run(token, name, positive, negative, dst, n):
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
                    fit(p, dst)
                    print("  →", os.path.relpath(dst, ROOT), flush=True)
        except Exception as e:
            print("  실패:", e, flush=True)
        time.sleep(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--death", nargs="*", default=None)
    ap.add_argument("--bg", nargs="*", default=None)
    ap.add_argument("--n", type=int, default=1)
    a = ap.parse_args()
    token = os.environ.get("NAI_TOKEN") or os.environ.get("NOVELAI_API_KEY")
    if not token:
        sys.exit("환경변수 NAI_TOKEN 에 토큰을 설정하세요.")
    if a.death is not None:
        for name in a.death or DEATHS:
            who, scene = DEATHS[name]
            look = nai.CHARACTERS[who].replace("solo, ", "")
            positive = f"{STYLE} {look}, {DEAD}, {scene}, {PARK}"
            negative = DEAD_NEG + (nai.MALE_NEG if "1boy" in look else "") + NEG
            os.makedirs(os.path.join(ROOT, "art", "cg"), exist_ok=True)
            run(token, name, positive, negative, os.path.join(ROOT, "art", "cg", name + ".png"), a.n)
    if a.bg is not None:
        for name in a.bg or BG:
            positive = f"{STYLE} 1.5::no humans, scenery::, {BG[name]}, {PARK}, wide angle, stage set like 3d background"
            negative = "1.5::1girl, 1boy, people, person, character::, " + NEG
            run(token, name, positive, negative, os.path.join(ROOT, "bg", name + ".png"), a.n)


if __name__ == "__main__":
    main()
