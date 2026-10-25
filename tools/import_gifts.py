# 선물 추가 : StrategyWiki 「Danganronpa: Trigger Happy Havoc/Presents」 아이콘(사용자 지시) → ui/gift/P###.png, data/gifts.json
# 속옷·성적인 물건·1편 줄거리 기념품(091~114)은 넣지 않는다(등장인물이 미성년자).
# 이름은 한국어로 옮기고, 좋아함(love)·호감(like)·싫어함(hate)은 우리 인물의 꿈·특기·좋아하는 것(data/characters.json)에 맞춰 정했다.
# python tools/import_gifts.py   (다시 돌려도 같은 결과. 이미 받은 아이콘은 건너뛴다)
import json, pathlib, urllib.request, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIKI = "https://cdn.wikimg.net/en/strategywiki/images/"
# 번호 : (위키 그림 경로, 한국어 이름, 등급)
P = {
 1: ("3/32/Danganronpa_present_Mineral_Water.png", "심층수 생수", "일반"),
 2: ("a/a8/Danganronpa_present_Cola_Cola.png", "콜라 콜라", "일반"),
 3: ("9/95/Danganronpa_present_Civet_Coffee.png", "사향고양이 커피", "좋은"),
 4: ("0/08/Danganronpa_present_Rose_Hip_Tea.png", "로즈힙 티", "일반"),
 5: ("f/f0/Danganronpa_present_Sea_Salt.png", "바다 소금", "일반"),
 6: ("6/62/Danganronpa_present_Potato_Chips.png", "감자칩", "일반"),
 7: ("8/89/Danganronpa_present_Prismatic_Hardtack.png", "칠색 건빵", "일반"),
 8: ("9/9c/Danganronpa_present_Black_Croissant.png", "블랙 크루아상", "일반"),
 9: ("d/d7/Danganronpa_present_Sonic_Cup-a-Noodle.png", "3초 컵라면", "일반"),
 10: ("f/f6/Danganronpa_present_Royal_Curry.png", "로열 카레", "일반"),
 11: ("0/08/Danganronpa_present_Ration.png", "전투 식량", "일반"),
 12: ("9/92/Danganronpa_present_Flotation_Donut.png", "튜브 도넛", "일반"),
 13: ("9/99/Danganronpa_present_Overflowing_Lunch_Box.png", "듬뿍 도시락", "좋은"),
 14: ("0/06/Danganronpa_present_Sunflower_Seeds.png", "해바라기씨", "일반"),
 15: ("4/48/Danganronpa_present_Birdseed.png", "새 모이", "일반"),
 16: ("7/73/Danganronpa_present_Kitty_Hairpin.png", "고양이 머리핀", "좋은"),
 17: ("e/ed/Danganronpa_present_Everlasting_Bracelet.png", "영원의 팔찌", "좋은"),
 18: ("c/c2/Danganronpa_present_Love_Status_Ring.png", "연애 상태 반지", "좋은"),
 19: ("0/09/Danganronpa_present_Zoles_Diamond.png", "모조 다이아몬드", "희귀"),
 20: ("1/19/Danganronpa_present_Hope%27s_Peak_Ring.png", "우정의 반지", "희귀"),
 21: ("4/43/Danganronpa_present_Blueberry_Perfume.png", "블루베리 향수", "일반"),
 22: ("8/8b/Danganronpa_present_Scarab_Brooch.png", "스카라베 브로치", "좋은"),
 23: ("8/80/Danganronpa_present_God_of_War_Charm.png", "무신의 부적", "일반"),
 24: ("9/9d/Danganronpa_present_Mac%27s_Gloves.png", "열혈 권투 장갑", "좋은"),
 25: ("0/02/Danganronpa_present_Glasses.png", "주문의 안경", "일반"),
 26: ("3/36/Danganronpa_present_G-Sick.png", "싸구려 손목시계", "일반"),
 27: ("7/70/Danganronpa_present_Roller_Slippers.png", "바퀴 달린 슬리퍼", "일반"),
 28: ("d/d6/Danganronpa_present_Red_Scarf.png", "영웅의 빨간 목도리", "좋은"),
 30: ("4/40/Danganronpa_present_Torneko%27s_Pants.png", "고딕 바지", "일반"),
 31: ("8/85/Danganronpa_present_Bunny_Earmuffs.png", "토끼 귀마개", "좋은"),
 32: ("7/73/Danganronpa_present_Fresh_Bindings.png", "새 무명 붕대", "일반"),
 33: ("3/31/Danganronpa_present_Jimmy_Decay_T-Shirt.png", "펑크 한정 티셔츠", "희귀"),
 36: ("8/8e/Danganronpa_present_Waterlover.png", "경영 수영복", "일반"),
 37: ("2/2b/Danganronpa_present_Demon_Angel_Princess_Figure.png", "마법소녀 피규어", "좋은"),
 38: ("c/cd/Danganronpa_present_Astral_Boy_Doll.png", "우주 소년 인형", "일반"),
 39: ("4/46/Danganronpa_present_Shears.png", "가위", "일반"),
 40: ("e/ed/Danganronpa_present_Layering_Shears.png", "숱가위", "일반"),
 41: ("8/86/Danganronpa_present_Quality_Chinchilla_Cover.png", "고급 시트 커버", "좋은"),
 42: ("e/e0/Danganronpa_present_Kirlian_Camera.png", "키를리안 카메라", "희귀"),
 43: ("0/08/Danganronpa_present_Adorable_Reactions_Collection.png", "감동 반응 모음 DVD", "일반"),
 44: ("e/ed/Danganronpa_present_Tumbleweed.png", "회전초", "일반"),
 45: ("f/f3/Danganronpa_present_Unending_Dandelion.png", "끝없는 민들레", "일반"),
 46: ("b/bf/Danganronpa_present_Rose_in_Vitro.png", "시험관 장미", "희귀"),
 47: ("a/a8/Danganronpa_present_Cherry_Blossom_Bouquet.png", "벚꽃 꽃다발", "희귀"),
 48: ("c/cf/Danganronpa_present_Rose_Whip.png", "장미 채찍", "좋은"),
 49: ("7/76/Danganronpa_present_Zantetsuken.png", "안 베이는 검", "일반"),
 50: ("5/5a/Danganronpa_present_Muramasa.png", "전설의 검", "좋은"),
 51: ("7/7e/Danganronpa_present_Raygun_Zurion.png", "광선총 장난감", "일반"),
 52: ("3/3f/Danganronpa_present_Golden_Gun.png", "황금 총 모형", "좋은"),
 53: ("2/2d/Danganronpa_present_Berserker_Armor.png", "광전사 갑옷", "희귀"),
 54: ("8/8f/Danganronpa_present_Self-Destructing_Cassette.png", "자폭 카세트", "일반"),
 55: ("4/43/Danganronpa_present_Silent_Receiver.png", "안 들리는 전화기", "일반"),
 56: ("2/28/Danganronpa_present_Pretty_Hungry_Caterpillar.png", "애벌레 장난감", "일반"),
 57: ("b/b5/Danganronpa_present_Old_Timey_Radio.png", "레트로 라디오", "좋은"),
 58: ("4/48/Danganronpa_present_Mr._Fastball.png", "구속 측정 공", "일반"),
 59: ("e/ea/Danganronpa_present_Antique_Doll.png", "앤티크 인형", "희귀"),
 60: ("e/ec/Danganronpa_present_Crystal_Skull.png", "수정 해골", "희귀"),
 61: ("1/12/Danganronpa_present_Golden_Airplane.png", "황금 비행기", "희귀"),
 62: ("c/ca/Danganronpa_present_Prince_Shotoku%27s_Globe.png", "오래된 지구본", "희귀"),
 63: ("0/0d/Danganronpa_present_Moon_Rock.png", "월석", "희귀"),
 64: ("7/71/Danganronpa_present_Asura%27s_Tears.png", "아수라의 눈물", "희귀"),
 65: ("b/bf/Danganronpa_present_Secrets_of_the_Omoplata.png", "관절기 비전서", "좋은"),
 66: ("e/ec/Danganronpa_present_Millennium_Prize_Problems.png", "밀레니엄 난제집", "좋은"),
 67: ("f/f2/Danganronpa_present_The_Funplane.png", "휴대용 게임기", "희귀"),
 68: ("6/60/Danganronpa_present_Project_Zombie.png", "좀비 게임 소프트", "일반"),
 69: ("3/39/Danganronpa_present_Pagan_Dancer.png", "신 게임 소프트", "일반"),
 70: ("5/5f/Danganronpa_present_Tips_and_Tips.png", "공략 대백과", "좋은"),
 71: ("a/a3/Danganronpa_present_Maiden%27s_Handbag.png", "소녀의 핸드백", "좋은"),
 72: ("3/31/Danganronpa_present_Kokeshi_Dynamo.png", "흔들 인형", "일반"),
 73: ("2/25/Danganronpa_present_The_Second_Button.png", "둘째 단추", "좋은"),
 74: ("4/49/Danganronpa_present_Someone%27s_Graduation_Album.png", "누군가의 졸업 앨범", "일반"),
 75: ("8/81/Danganronpa_present_Vise.png", "바이스", "일반"),
 76: ("f/fc/Danganronpa_present_Sacred_Tree_Sprig.png", "비쭈기나무 가지", "일반"),
 77: ("2/2e/Danganronpa_present_Pumice.png", "부석", "일반"),
 78: ("0/09/Danganronpa_present_Oblaat.png", "오블라토", "일반"),
 79: ("f/f6/Danganronpa_present_Water_Flute.png", "물피리", "일반"),
 80: ("9/94/Danganronpa_present_Bojobo_Dolls.png", "소원 인형", "좋은"),
 81: ("6/60/Danganronpa_present_Small_Light.png", "작은 손전등", "일반"),
 82: ("7/7e/Danganronpa_present_Voice-Changing_Bowtie.png", "변성 나비넥타이", "희귀"),
 83: ("0/0d/Danganronpa_present_Ancient_Tour_Tickets.png", "고대 여행 티켓", "일반"),
 84: ("7/7c/Danganronpa_present_Novelist%27s_Fountain_Pen.png", "문호의 만년필", "희귀"),
 85: ("c/ce/Danganronpa_present_If_Fax.png", "만약 팩스", "일반"),
 87: ("4/46/Danganronpa_present_Meteorite_Arrowhead.png", "운석 화살촉", "희귀"),
 88: ("c/cc/Danganronpa_present_Chin_Drill.png", "턱 드릴", "일반"),
 89: ("2/2c/Danganronpa_present_Green_Costume.png", "초록 공룡 옷", "좋은"),
 90: ("3/33/Danganronpa_present_Red_Costume.png", "빨간 설인 옷", "좋은"),
}
# 인물 → 새 선물 번호 (love / like / hate)
LIKES = {
 "rei":     ([62, 66], [4, 75, 83], [9]),
 "sora":    ([6, 12, 28], [13, 58, 27], [60]),
 "ken":     ([3, 89, 90, 82], [43, 50, 37], [55]),
 "nana":    ([4, 78], [32, 47, 76], [49]),
 "riku":    ([81, 45, 54], [51, 55, 56], [66]),
 "akari":   ([78, 76], [4, 14, 1], [44]),
 "yuu":     ([2, 33], [57, 79, 67], [55]),
 "koto":    ([20, 17, 74], [80, 73, 47], [48]),
 "satsuki": ([87, 23], [41, 44, 15], [27]),
 "taiga":   ([24, 65, 32], [11, 53, 9], [60, 72]),
 "rin":     ([70, 75], [7, 62, 54], [55]),
 "sho":     ([66, 84], [65, 25, 78], [88]),
 "ai":      ([5, 10, 13], [14, 8, 9], [77]),
 "haruka":  ([42, 16], [31, 12, 59], [55]),
 "kaede":   ([8, 26], [7, 46, 12], [44]),
}

def gid(n): return "P%03d" % n

def main():
    out = ROOT / "ui" / "gift"; out.mkdir(parents=True, exist_ok=True)
    for n, (path, _, _) in P.items():
        f = out / (gid(n) + ".png")
        if f.exists() and f.stat().st_size > 0: continue
        req = urllib.request.Request(WIKI + path, headers={"User-Agent": "YumenoKuni-asset-import/1.0"})
        f.write_bytes(urllib.request.urlopen(req, timeout=30).read()); time.sleep(.3)
        # 원본은 85px 안팎 : 정사각 투명 여백 → 256px (기존 G 아이콘과 같은 칸에 같은 크기로)
        from PIL import Image
        im = Image.open(f).convert("RGBA"); side = max(im.size) + 8
        sq = Image.new("RGBA", (side, side)); sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
        sq.resize((256, 256), Image.LANCZOS).save(f)
    gp = ROOT / "data" / "gifts.json"
    g = json.loads(gp.read_text(encoding="utf-8"))
    g["items"] = [x for x in g["items"] if not x["id"].startswith("P")] + [{"id": gid(n), "name": name, "tier": tier} for n, (_, name, tier) in P.items()]
    for who, (love, like, hate) in LIKES.items():
        e = g["likes"].setdefault(who, {"love": [], "hate": []})
        for k, ns in (("love", love), ("like", like), ("hate", hate)):
            e[k] = [x for x in e.get(k, []) if not x.startswith("P")] + [gid(n) for n in ns]
    gp.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    print("gifts", len(g["items"]))

if __name__ == "__main__":
    main()
