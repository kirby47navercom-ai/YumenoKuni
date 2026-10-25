# 포즈 연출 : 대사마다 입상 포즈(pose = C01~C14 / U1~U6 / K01~K03, 래피 L01~L12)를 정한다. build_flow.py main() 이 부른다.
# 포즈 뜻 = docs/spec/12 §1·§2. V3 처럼 대사마다 표정이 바뀌게 :
#   ① 표정 지시(emo) 낱말 → 그 포즈  ② 지시가 없으면 대사 내용(!? · 하하 · 미안 · 무서 · … 등)  ③ 그래도 없으면 기본·미소와
#   그 인물의 버릇 포즈(U)를 번갈아(같은 사람이 같은 포즈로 계속 서 있지 않게). 회상 장면은 어린 시절(K).
import re

NAMES = {"미오": "mio", "레이": "rei", "소라": "sora", "켄": "ken", "나나": "nana", "리쿠": "riku", "아카리": "akari", "유우": "yuu",
         "코토": "koto", "사츠키": "satsuki", "타이가": "taiga", "린": "rin", "쇼": "sho", "아이": "ai", "하루카": "haruka", "카에데": "kaede", "래피": "lappy"}
# 표정 지시 → 포즈 (앞에 있는 것이 먼저)
EMO = [("통곡|오열|엉엉", "C07"), ("눈물|울", "C06"), ("공포|떨|겁|움츠", "C11"), ("놀람|깜짝|화들짝", "C04"), ("당황|식은땀|허둥", "C09"),
       ("부끄|볼이|귀가 붉|수줍", "C10"), ("화남|화를|화내|짜증|버럭|단호|노려|주먹", "C05"), ("의심|곁눈|흘겨|시선|팔짱", "C13"), ("결의|진지|낮은 톤|낮은 목소리|낮게|극적", "C12"),
       ("고민|생각|갸웃|망설", "C08"), ("한숨|지침|피곤|말끝이 흐려", "C14"), ("작게|소극|조용", "C08"),
       ("활짝|환호|신남|크게 웃|폭소|손뼉|활기", "C03"), ("웃|미소|온화|윙크|장난|다정", "C02")]
TEXT = [(r"[?？][!！]|[!！][?？]|에엣|헉|뭐[?!]", "C04"), (r"(하하|후후|히히|ㅋ|ㅎㅎ).*[!~]|[!~].*(하하|히히)", "C03"), (r"미안|죄송|잘못했", "C06"),
        (r"무서|싫어[!…]|살려", "C11"), (r"그만|시끄|뭐야[!]|용서 못", "C05"), (r"고마워|다행|좋아[!~]", "C02"), (r"반드시|꼭 |할 거야|하자[!.]", "C12"),
        (r"^…+$|^…[가-힣]{0,3}…", "C14"), (r"설마|정말[?]|이상해|수상", "C13"), (r"글쎄|어떻게|왜[?]|뭘까", "C08")]
# 버릇 포즈 중 복선이라 아무 때나 쓰면 안 되는 것
NO_U = {("sora", "U4"), ("haruka", "U6"), ("ken", "U6")}
LAPPY = [("화남|화를|화내|버럭|짜증", "L02"), ("비웃|깔깔|크크|푸핫", "L06"), ("우쭐|자랑|흥흥", "L04"), ("시무룩|슬", "L05"), ("웃|하하|히히|신나", "L03")]


def pose_of(slug, e, count, flashback):
    emo, text = e.get("emo", ""), e.get("text", "")
    if slug == "lappy":
        for pat, code in LAPPY:
            if re.search(pat, emo + " " + text):
                return code
        return ["L01", "L03", "L04", "L01", "L12"][count % 5]
    if flashback and slug != "mio":
        return f"K0{count % 3 + 1}"
    for pat, code in EMO:
        if emo and re.search(pat, emo):
            return code
    for pat, code in TEXT:
        if re.search(pat, text):
            return code
    cycle = ["C01", "C02", "U1", "C01", "U2", "C02", "U3", "C01", "U5", "C02", "U4", "U6"]
    code = cycle[count % len(cycle)]
    return "C01" if (slug, code) in NO_U else code


def place(evs, flashback=False, counts=None):
    counts = {} if counts is None else counts
    last = {}
    for e in evs:
        if e["type"] != "say" or e.get("mono") or "pose" in e:
            continue
        slug = NAMES.get(e.get("speaker", ""))
        if not slug or slug == "mio":
            continue  # 미오는 화면에 입상이 안 나온다(1인칭)
        n = counts.get(slug, 0)
        code = pose_of(slug, e, n, flashback)
        if code == last.get(slug) and code in ("C01", "C02"):  # 같은 기본 포즈가 이어지면 다음 것으로
            n += 1
            code = pose_of(slug, {"text": ""}, n, flashback)
        e["pose"] = code
        last[slug] = code
        counts[slug] = n + 1


def score(flow):
    counts = {}
    for b in flow["beats"]:
        title = b.get("title", "")
        flash = bool(re.search(r"회상|5년 전", title))
        place(b.get("events", []), flash, counts)
        for x in b.get("spots", []) + b.get("pool", []):
            place(x["events"], False, counts)


# 재판 대본(data/trials/*.json script) : 재판 포즈(T01 지목 · T02 증언대 짚기 · T03 동의 · T04 몰림)를 먼저, 나머지는 위와 같이.
# build_trial.py 가 만든 파일 위에 덮어쓴다(다시 돌려도 같은 결과). 엔진은 pose 를 「slug_코드」로 읽는다(TrialRunner.hpp poseTexture).
TRIAL = [(r"틀렸어|그건 아니|아니야[!]|거짓말|네가 범인|당신이 범인|그 말은", "T01"), (r"으윽|그, 그건|그럴 리|아니, 나는|억울", "T04"),
         (r"맞아|그래[,.!]|동의|찬성|나도 그렇게", "T03"), (r"[!！]$", "T02")]


def trials():
    import glob, json, os
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "trials")
    for f in glob.glob(os.path.join(root, "*.json")):
        t = json.load(open(f, encoding="utf-8"))
        counts = {}
        for st in t["stages"]:
            for l in st.get("script", []):
                slug = NAMES.get(l.get("speaker", ""))
                l.pop("pose", None)
                if not slug or slug == "mio":
                    continue
                code = None
                if slug != "lappy":
                    for pat, c in TRIAL:
                        if re.search(pat, l.get("text", "")):
                            code = c
                            break
                n = counts.get(slug, 0)
                code = code or pose_of(slug, l, n, False)
                counts[slug] = n + 1
                l["pose"] = f"{slug}_{code}"
        json.dump(t, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
