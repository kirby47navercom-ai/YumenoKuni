#!/usr/bin/env python3
"""
장 진행표 : data/scenes/*.json → data/flow/{P,1..6}.json  (docs/spec/09 비트 순서)
  python tools/build_flow.py
비트 종류 : card(장 제목) / scene(대본) / freetime(2슬롯, 이벤트 풀) / investigate(현장 목록) / trial / execution / ending / end
대본 이벤트 : say / stage / ui / card(언령 획득) / bg / menu(보기 → goto) / goto / flag
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = {"미오": "mio", "레이": "rei", "소라": "sora", "켄": "ken", "나나": "nana", "리쿠": "riku", "아카리": "akari", "유우": "yuu",
         "코토": "koto", "사츠키": "satsuki", "타이가": "taiga", "린": "rin", "쇼": "sho", "아이": "ai", "하루카": "haruka", "카에데": "kaede", "래피": "lappy"}
# 장이 끝날 때 퇴장하는 인물 (피해자 + 처형). 재판 때 영정은 그 장 피해자까지.
VICTIMS = {1: ["taiga"], 2: ["yuu"], 3: ["riku", "sora"], 4: ["haruka"], 5: ["nana"], 6: []}
EXECUTED = {1: ["sho"], 2: ["akari"], 3: ["ken"], 4: ["rei"], 5: ["satsuki"], 6: []}
TITLES = {"P": "프롤로그", 1: "개장", 2: "물놀이 시즌", 3: "거울의 밤", 4: "잠든 롤러코스터", 5: "드림 캐슬", 6: "드림 코어"}
# 장소 낱말 → 배경 이름 앞부분 (bg/ 에 있는 것 중 첫 번째)
PLACES = [("재판장", ["trial_room"]), ("엘리베이터", ["trial_elevator"]), ("정문", ["main_gate"]),
          ("미오의 방", ["mio_room"])] + [(f"{k}의 방", [f"{v}_room"]) for k, v in NAMES.items() if v not in ("mio", "lappy")] + [
          ("객실", ["mio_room"]), ("식당", ["hotel_dining"]), ("로비", ["hotel_lobby"]), ("라운지", ["hotel_lounge", "hotel_lobby"]),
          ("세탁", ["hotel_laundry", "hotel_corridor"]), ("옥상", ["roof_garden"]), ("별관", ["annex_hall"]), ("계단", ["hotel_stairs"]),
          ("505", ["vip_505"]), ("리넨", ["vip_linen"]), ("갤러리", ["vip_gallery"]), ("5층", ["vip_hall_a", "hotel_corridor"]),
          ("복도", ["hotel_corridor"]), ("호텔", ["hotel_lobby"]), ("인포메이션", ["info_center"]),
          ("파도 타이머", ["waterpark_pump"]), ("파도", ["waterpark_pump"]), ("엘리베이터 홀", ["vip_elevator", "hotel_elevator"]), ("비상 장비", ["theater_emergency", "hotel_lobby"]), ("제어반", ["carousel_control"]), ("매표소", ["carousel_ticket", "carousel_control"]), ("기계실", ["carousel_machine", "waterpark_machine"]),
          ("회전목마", ["carousel_day"]), ("탑승장", ["carousel_day"]), ("기념품", ["souvenir_shop"]), ("의상", ["shop_costume", "parade_costume"]),
          ("약품", ["clinic_pharmacy", "infirmary"]), ("의무실", ["infirmary"]), ("뒷문", ["food_backdoor"]), ("서비스 복도", ["food_service_corridor"]),
          ("주방", ["food_kitchen", "foodcourt"]), ("창고", ["food_storage"]), ("푸드코트", ["foodcourt"]),
          ("매점", ["waterpark_snack"]), ("자판기", ["waterpark_snack"]), ("펌프", ["waterpark_pump"]), ("탈의", ["waterpark_locker"]),
          ("워터파크", ["waterpark"]), ("풀", ["waterpark"]), ("퍼레이드", ["parade_street"]), ("소극장", ["parade_stage"]),
          ("거울 미로", ["mirror_maze_1", "mirror"]), ("거울", ["mirror_center", "mirror"]), ("곤돌라", ["ferris_gondola"]), ("관람차", ["ferris_boarding", "ferris"]),
          ("음향실", ["theater_sound"]), ("장치실", ["theater_rigging"]), ("분장실", ["theater_dressing"]), ("소품", ["theater_props"]),
          ("객석", ["theater_seats_1f"]), ("무대", ["theater_stage"]), ("극장", ["theater_lobby", "theater"]),
          ("정비동", ["rollercoaster_maintenance"]), ("발전기", ["rollercoaster_generator"]), ("점검", ["rollercoaster_inspection"]),
          ("롤러코스터", ["rollercoaster_platform"]), ("서고", ["castle_library"]), ("시계탑", ["castle_tower"]), ("연회장", ["castle_hall"]),
          ("갑옷", ["castle_armor"]), ("수장고", ["castle_vault"]), ("지하 체험관", ["castle_basement"]), ("플로트", ["castle_float"]),
          ("왕좌", ["castle_throne"]), ("캐슬", ["castle_hall", "castle"]), ("제어실", ["core_control"]), ("대피소", ["core_shelter"]),
          ("코어", ["core_hall", "core"]), ("광장", ["plaza"]), ("분수", ["plaza"]), ("벤치", ["plaza"])]
# 이벤트 CG (docs/spec/12 §5) : 장면 UID → art/cg 이름. 장면 첫 배경 바로 뒤에 넣는다.
EVENT_CG = {"10:P-01": "event_P_awakening", "10:P-02": "event_P_meeting", "10:2_1_순서대로_자기소개": "event_P_snacks", "10:4_2_반응_컷": "event_P_practice_parade",
            "11a:1-S2": "event_1_cooking", "11a:1-S3": "event_1_patrol", "12a:2-S2": "event_2_water_balloons", "12a:2-S3": "event_2_performance",
            "13a:3-S3": "event_3_gondola", "13a:3-S7-a": "event_3_rehearsal", "14a:4-S5": "event_4_gallery_photo", "14a:4-S6": "event_4_pillow_party",
            "15a:5-S3": "event_5_dress_code", "15a:5-S7": "event_5_clock_tower", "16a:6-S2": "event_6_last_breakfast", "16a:I_1_코어_홀_5년_전_사고_현장_": "event_6_past_night",
            "16b:C_A_엔딩_A_기본_체포_30분_": "event_6_ending_A", "16b:C_B_엔딩_B_어두운_분기_처형": "event_6_ending_B", "16b:C_C_에필로그_후_공통_5분_": "event_6_gate"}
# 막간 : I_N_1 식사 / I_N_2 서비스씬 / I_N_4 미오 혼자
INTERLUDE_CG = {0: ["dinner", "rooms", "room"], 1: ["breakfast", "laundry", "room"], 2: ["dinner", "cat", "room"], 3: ["lunch", "movie", "room"], 4: ["breakfast", "gondola", "room"], 5: ["kitchen", "feast", "room"]}
# 범죄 현장 방 = 사망 CG (현장 이름 낱말 → CG)
CRIME_ROOM = {1: {"탑승장": "death_1_taiga"}, 2: {"웨이브 풀": "death_2_yuu"}, 3: {"장치실": "death_3a_riku", "음향실": "death_3b_sora"},
              4: {"505": "death_4_haruka"}, 5: {"서고": "death_5_nana"}}
# 사건 CG : 그 장 첫 수사 현장에 들어갈 때
INCIDENT_CG = {1: "event_1_incident", 2: "event_2_headphones", 3: "event_3_theater_case", 4: "event_4_latch", 5: "event_5_crossbow"}
CARD = re.compile(r"(증거|증언|규칙|마법|메모|노트)\s*카드\s*[:：]?\s*(.*?)\s*\(?([ETMNR]\d?-\d+(?:-[a-z])?)\)?")
OPTION = re.compile(r"^-?\s*([A-F])\.\s*(.*)$")
REACT = re.compile(r"\[([^\]]+)\]\s*\"([^\"]+)\"(?:\s*\{([^}]*)\})?")

KOTO = json.load(open(os.path.join(ROOT, "data", "kotodama.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "data", "kotodama.json")) else {}  # build_trial.py 가 만든 언령 이름
backgrounds = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(ROOT, "bg")) if f.endswith(".webp"))


def background(text, night=False):
    """장소 낱말 → 배경. 여러 낱말이 맞으면 가장 긴(구체적인) 낱말, 같으면 앞에 나온 것."""
    found = sorted(((-len(w), text.index(w), w, prefixes) for w, prefixes in PLACES if w in text))
    for _, _, word, prefixes in found:
        for p in prefixes:
            hits = [b for b in backgrounds if b.startswith(p)]
            if hits:
                pick = [b for b in hits if ("night" in b) == night] or hits
                return pick[0]
    return None


def is_night(text):
    return any(w in text for w in ("밤", "저녁", "야간", "night"))


def convert(events, scene_id, title):
    """원본 이벤트 → 실행 이벤트(선택지는 menu + goto 로 펼침)"""
    out = []
    first = background(title, is_night(title))
    if first:
        out.append({"type": "bg", "bg": first})
    i = 0
    while i < len(events):
        e = events[i]
        t = e["type"]
        if t == "say":
            sp = e["speaker"].split("(")[0].strip()
            x = {"type": "say", "speaker": sp, "text": e["text"]}
            if e.get("kind") == "monologue":
                x["mono"] = True
            if e.get("emo"):
                x["emo"] = e["emo"]
            out.append(x)
        elif t == "stage":
            bg = background(e["text"], is_night(e["text"]) or is_night(title))
            if bg and (not out or out[-1].get("bg") != bg) and len(e["text"]) < 60:
                out.append({"type": "bg", "bg": bg})
            out.append({"type": "stage", "text": e["text"]})
        elif t == "ui":
            m = CARD.search(e["text"])
            if m and "획득" in e["text"]:
                seen_text = [x["text"] for x in out if x["type"] in ("stage", "say")][-2:]
                out.append({"type": "card", "id": m.group(3), "name": m.group(2).strip(" :") or m.group(3), "text": e["text"], "desc": " ".join(t.strip("()") for t in seen_text)})
            else:
                out.append({"type": "ui", "text": e["text"]})
        elif t == "break":
            out.append({"type": "break", "name": e["text"]})
            bg = background(e["text"], is_night(title))
            if bg:
                out.append({"type": "bg", "bg": bg})
        elif t == "choice":
            j = i + 1
            opts = []
            while j < len(events) and events[j]["type"] == "note" and OPTION.match(events[j]["text"]):
                opts.append(OPTION.match(events[j]["text"]))
                j += 1
            if opts:
                i = menu_from_notes(out, events, e["text"], opts, j, scene_id)
                continue
            # 보기가 이벤트로 나열된 경우 : "적는다…" / "적지 않는다"
            k = i
            labels = []
            while k < len(events) and events[k]["type"] == "choice":
                labels.append(events[k]["text"])
                k += 1
            if len(labels) >= 2:
                q = out[-1]["text"] if out and out[-1]["type"] == "ui" else "선택"
                out.append({"type": "menu", "q": q, "options": [{"label": l, "flag": f"{scene_id}:{n}"} for n, l in enumerate(labels)]})
                for n, o in enumerate(out[-1]["options"]):
                    o["to"] = len(out)  # 반응 없음 : 바로 다음
                i = k
                continue
        i += 1
    return out


def menu_from_notes(out, events, question, opts, j, scene_id):
    """A/B 보기. 뒤에 'A 선택' 'B 선택' 무대 표시가 있으면 그 구간이 분기."""
    letters = [m.group(1) for m in opts]
    marks = {}
    for k in range(j, len(events)):
        ev = events[k]
        if ev["type"] == "stage" and re.fullmatch(r"([A-F]) 선택", ev["text"].strip()):
            marks[ev["text"].strip()[0]] = k
    menu = {"type": "menu", "q": question if question not in ("선택", "선택지") else "어떻게 할까?", "options": []}
    out.append(menu)
    ends = []
    if marks and set(marks) >= set(letters):
        order = sorted(marks.items(), key=lambda kv: kv[1])
        for n, (letter, start) in enumerate(order):
            stop = order[n + 1][1] if n + 1 < len(order) else len(events)
            label = clean(opts[letters.index(letter)].group(2))
            menu["options"].append({"label": label, "to": len(out), "flag": f"{scene_id}:{letter}"})
            out.extend(convert(events[start + 1:stop], scene_id, "")[0:])
            ends.append(len(out))
            out.append({"type": "goto", "to": -1})
        for p in ends:
            out[p]["to"] = len(out)
        return len(events)
    for m in opts:
        label, _, after = m.group(2).partition("→")
        menu["options"].append({"label": clean(label), "to": len(out), "flag": f"{scene_id}:{m.group(1)}"})
        r = REACT.search(after)
        if r:
            x = {"type": "say", "speaker": r.group(1).split("(")[0], "text": r.group(2)}
            if r.group(3):
                x["emo"] = r.group(3)
            out.append(x)
        elif clean(label):
            out.append({"type": "say", "speaker": "미오", "text": clean(label)})
        ends.append(len(out))
        out.append({"type": "goto", "to": -1})
    for p in ends:
        out[p]["to"] = len(out)
    return j


def clean(s):
    s = s.strip().strip("-").strip()
    s = re.sub(r"\*\*", "", s)
    s = s.strip("\"“”")
    return s.strip()


def load(prefix):
    path = glob.glob(os.path.join(ROOT, "data", "scenes", prefix + "_*.json"))[0]
    return json.load(open(path, encoding="utf-8"))["scenes"]


def scene_beat(s, file_key):
    uid = f"{file_key}:{s['id']}"
    evs = convert(s["events"], uid, s["title"])
    cg = EVENT_CG.get(uid)
    if not cg and ("아침 방송" in s["title"] or "밤 방송" in s["title"]):  # 모니터 속 래피 방송 (V3 : 차임 → 모니터)
        evs.insert(1 if evs and evs[0]["type"] == "bg" else 0, {"type": "bg", "bg": "ui:broadcast_" + ("morning" if "아침" in s["title"] else "night")})
        shift(evs, 1 if evs and evs[0]["type"] == "bg" else 0)
    m = re.match(r"I_(\d)_([124])_", s["id"]) if file_key == "17" else None
    if m:
        cg = f"interlude_{m.group(1)}_" + INTERLUDE_CG[int(m.group(1))][{"1": 0, "2": 1, "4": 2}[m.group(2)]]
    if cg:
        at = 1 if evs and evs[0]["type"] == "bg" else 0
        evs.insert(at, {"type": "bg", "bg": "cg:" + cg})
        shift(evs, at)
    return {"t": "scene", "id": uid, "title": s["title"], "events": evs}


def shift(events, at):
    """at 위치에 하나 끼워 넣은 뒤 goto·보기 번호를 맞춘다"""
    for e in events:
        if e["type"] == "goto" and e["to"] > at:
            e["to"] += 1
        if e["type"] == "menu":
            for o in e["options"]:
                if o["to"] > at:
                    o["to"] += 1


def room_of(beat, ch):
    """수사 장면 → 방 : 들어갈 때 대사(첫 break 전) + 조사 대상들. 이벤트 번호는 장면 안 그대로라 goto 가 유지된다."""
    evs = beat["events"]
    # 현장 이름 → 배경. 이름에 장소가 없으면(증언 수집 등) 그 장 기본 장소
    CH_DEFAULT = {1: "hotel_lobby", 2: "hotel_lobby", 3: "theater_lobby", 4: "vip_lounge", 5: "castle_hall", 6: "core_shelter"}
    bg = background(beat.get("spot", "")) or CH_DEFAULT.get(ch)
    if any(w in beat.get("spot", "") for w in CRIME_ROOM.get(ch, {})):  # 범죄 현장 : 시체가 있는 사망 CG 를 방으로
        bg = "cg:" + next(v for w, v in CRIME_ROOM[ch].items() if w in beat["spot"])
    cuts = [i for i, e in enumerate(evs) if e["type"] == "break"]
    objects = []
    for n, at in enumerate(cuts):
        end = cuts[n + 1] if n + 1 < len(cuts) else len(evs)
        name = evs[at]["name"].strip()
        if not any(evs[k]["type"] in ("say", "stage", "card") for k in range(at, end)):
            continue
        head = name.split("(")[0].split("·")[0].strip().split(" ")[0]
        who = NAMES.get(head) or (NAMES.get(head[:-1]) if head.endswith("의") and "방" not in name else None)  # 「쇼의 소매」 → 쇼를 조사
        objects.append({"name": name, "from": at, "to": end, "who": who if who and who != "mio" else ""})
    cards = [i for i, e in enumerate(evs) if e["type"] == "card"]
    if len(objects) <= 1 and len(cards) >= 2:  # 나뉘지 않은 장면 : 언령 하나 = 조사 지점 하나(V3)
        objects, start = [], (cuts[0] if cuts else 0)
        for n, c in enumerate(cards):
            end = c + 1 if n + 1 < len(cards) else len(evs)
            nm = KOTO.get(evs[c]["id"], {}).get("name") or evs[c]["name"]
            who = NAMES.get(nm[:-4]) if nm.endswith("의 증언") else None  # 「코토의 증언」 → 코토에게 말을 걸어 듣는다
            objects.append({"name": nm, "from": start, "to": end, "who": who if who and who != "mio" else ""})
            start = end
        intro = cuts[0] if cuts else 0
    elif not objects:  # 장면 전체가 조사 대상 하나
        objects.append({"name": beat.get("spot", "조사"), "from": 0, "to": len(evs), "who": ""})
        intro = 0
    else:
        intro = cuts[0]
    people = sorted({NAMES[e["speaker"]] for e in evs if e["type"] == "say" and NAMES.get(e["speaker"]) not in (None, "mio", "lappy")})
    beat.update({"bg": bg or "hotel_lobby", "intro": intro, "objects": objects, "people": people})
    return beat


def place_of(title, night=False):
    """프리타임 이벤트 제목 (장소) → 장소 이름 · 배경"""
    m = re.search(r"\(([^)]+)\)\s*$", title)
    name = m.group(1) if m else "중앙 광장"
    return name, background(name, night or is_night(title)) or "plaza_day"


def who_of(title):
    m = re.match(r"[BCD]-\d+\s+(\S+)", title)
    return NAMES.get(m.group(1)) if m else None


def gone_before(ch):
    out = []
    for c in range(1, ch):
        out += VICTIMS[c] + EXECUTED[c]
    return out


def daily(ch, key):
    """1Na : 스토리 순서 + 프리타임 자리. B-*는 프리타임 이벤트 풀, C-*/D-*는 유품."""
    beats, pool, keepsakes = [], [], []
    for s in load(key):
        sid = s["id"]
        if sid.startswith("_프리타임"):
            b = scene_beat(s, key)
            beats.append(b)
            beats.append({"t": "freetime", "slots": 2})
        elif re.match(r"B-\d+$", sid):
            if sid != "B-0" and who_of(s["title"]):
                place, bg = place_of(s["title"])
                pool.append({"who": who_of(s["title"]), "place": place, "bg": bg, **scene_beat(s, key)})
        elif re.match(r"[CD]-\d+$", sid) and "유품" in s["title"]:
            b = scene_beat(s, key)
            b["need"] = {"who": who_of(s["title"]), "level": 3}
            keepsakes.append(b)
        else:
            beats.append(scene_beat(s, key))
    for b in beats:
        if b["t"] == "freetime":
            b["pool"] = pool
    return beats, keepsakes


def investigation(key, ch):
    """1Nb : 발견(B) → 수사(C, 현장 목록) → [재판] → 처형(X) → 에필로그(E/F)"""
    found, intro, spots, after, execution, epilogue = [], None, [], [], [], []
    for s in load(key):
        sid, title = s["id"], s["title"]
        if sid.startswith("B-"):
            b = scene_beat(s, key)
            for n, e in enumerate(b["events"]):
                if e["type"] == "stage" and any(w in e["text"] for w in ("시체", "쓰러", "엎드", "누워")):
                    b["events"].insert(n, {"type": "bg", "bg": f"cg:death_{ch}"})
                    shift(b["events"], n)
                    break
            found.append(b)
        elif sid.startswith("C_") or sid.startswith("6_I") :
            intro = scene_beat(s, key)
        elif re.match(r"(C|I)[-_]\d", sid):
            b = scene_beat(s, key)
            if any(w in title for w in ("노트 슬롯", "수사 종료", "증거 카드 정리", "노트 정리")):
                after.append(b)
            else:
                b["spot"] = re.sub(r"^(C-\d+(-b)?|I \d+)\s*", "", title)
                spots.append(room_of(b, ch))
        elif "-X-" in sid:
            execution.append(scene_beat(s, key))
        elif "-E-" in sid or sid.startswith("F_"):
            epilogue.append(scene_beat(s, key))
    if found and not any(e.get("bg", "").startswith("cg:") for b in found for e in b["events"]):
        evs = found[-1]["events"]
        at = 1 if evs and evs[0]["type"] == "bg" else 0
        evs.insert(at, {"type": "bg", "bg": f"cg:death_{ch}"})
        shift(evs, at)
    return found, intro, spots, after, execution, epilogue


def chapter(ch):
    beats = [{"t": "card", "chapter": str(ch), "title": TITLES[ch]}]
    if ch < 6:
        day, keepsakes = daily(ch, f"1{ch}a")
        beats += day
        found, intro, spots, after, execution, epilogue = investigation(f"1{ch}b", ch)
    else:
        found, intro, spots, after, execution, epilogue, keepsakes = [], None, [], [], [], [], []
        for s in load("16a"):
            sid = s["id"]
            if sid.startswith("6_I"):
                intro = scene_beat(s, "16a")
            elif re.match(r"I_\d", sid):
                b = scene_beat(s, "16a")
                if "수사_종료" in sid or "정리" in s["title"] and "증거" in s["title"]:
                    after.append(b)
                else:
                    b["spot"] = re.sub(r"^I \d+\s*", "", s["title"])
                    spots.append(room_of(b, 6))
            else:
                beats.append(scene_beat(s, "16a"))
    beats += found
    if intro:
        beats.append(intro)
    if spots and ch in INCIDENT_CG:  # 첫 현장 들어가는 대사 앞에 사건 CG
        evs = spots[0]["events"]
        at = 1 if evs and evs[0]["type"] == "bg" else 0
        evs.insert(at, {"type": "bg", "bg": "cg:" + INCIDENT_CG[ch]})
        shift(evs, at)
        spots[0]["intro"] = spots[0]["intro"] + 1 if spots[0]["intro"] >= at else at + 1  # 들어갈 때 CG 를 보인다
        for o in spots[0]["objects"]:
            o["from"] += o["from"] >= at
            o["to"] += 1
    beats.append({"t": "investigate", "spots": spots})
    beats += after
    dead = gone_before(ch) + VICTIMS[ch]
    beats.append({"t": "trial", "key": f"1{ch}c", "dead": dead})
    if ch < 6:
        for b in execution:
            b["t"] = "execution"
            b["chapter"] = ch
        beats += execution + epilogue + keepsakes
        beats += interlude(ch)
    else:
        ends = {s["id"]: s for s in load("16b")}
        beats.append({"t": "ending",
                      "q": "…살의를 버릴 수 있을까?",
                      "options": [{"label": "살의를 버린다", "beat": scene_beat(ends["C_A_엔딩_A_기본_체포_30분_"], "16b")},
                                  {"label": "살의를 버리지 않는다", "beat": scene_beat(ends["C_B_엔딩_B_어두운_분기_처형"], "16b")}]})
        beats.append(scene_beat(ends["C_C_에필로그_후_공통_5분_"], "16b"))
        beats.append({"t": "end"})
    return {"chapter": str(ch), "title": TITLES[ch], "gone": gone_before(ch), "beats": beats}


def interlude(n):
    return [scene_beat(s, "17") for s in load("17") if s["id"].startswith(f"I_{n}_")]


def prologue():
    beats = [{"t": "card", "chapter": "P", "title": TITLES["P"]}]
    beats += [scene_beat(s, "10") for s in load("10")]
    beats += interlude(0)
    return {"chapter": "P", "title": TITLES["P"], "gone": [], "beats": beats}


def check(flow):
    errors = []
    for b in flow["beats"]:
        evs = b.get("events", [])
        for n, e in enumerate(evs):
            if e["type"] == "goto" and not 0 <= e["to"] <= len(evs):
                errors.append(f"{b['id']} goto {e['to']}")
            if e["type"] == "menu":
                for o in e["options"]:
                    if not 0 <= o["to"] <= len(evs):
                        errors.append(f"{b['id']} menu → {o['to']}")
        if b["t"] == "freetime" and not b["pool"]:
            errors.append(f"{flow['chapter']} 프리타임 풀 비었음")
        if b["t"] == "investigate" and not b["spots"]:
            errors.append(f"{flow['chapter']} 수사 현장 없음")
    return errors


def gifts():
    """선물 24종(00 §4-3) + 인물별 호/비(01 문서 취향 줄) → data/gifts.json"""
    sys_doc = open(glob.glob(os.path.join(ROOT, "docs", "design", "00_*.md"))[0], encoding="utf-8").read()
    items = [{"id": m[0], "name": re.sub(r"\(.*?\)", "", m[1]).strip(), "tier": m[3].split()[0]}
             for m in re.findall(r"^\| (G\d\d) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|", sys_doc, re.M)]
    chars = open(glob.glob(os.path.join(ROOT, "docs", "design", "01_*.md"))[0], encoding="utf-8").read()
    likes, who = {}, None
    for line in chars.splitlines():
        h = re.match(r"^## \d+ \S+ (\S+)", line)
        if h:
            who = NAMES.get(h.group(1))
        m = re.search(r"취향\*\* : 호 (.*?) / 비 (.*)$", line)
        if m and who:
            likes[who] = {"love": re.findall(r"G\d\d", m.group(1)), "hate": re.findall(r"G\d\d", m.group(2))}
    assert len(items) == 24 and len(likes) == 15, (len(items), len(likes))
    with open(os.path.join(ROOT, "data", "gifts.json"), "w", encoding="utf-8") as f:
        json.dump({"items": items, "likes": likes}, f, ensure_ascii=False, indent=1)


def describe_cards(flows):
    """언령 설명이 비어 있으면 획득 직전 대사·무대 설명으로 채운다 (data/kotodama.json, build_trial.py 가 만든 것)"""
    path = os.path.join(ROOT, "data", "kotodama.json")
    cards = json.load(open(path, encoding="utf-8"))
    def walk(evs):
        for e in evs:
            if e["type"] == "card" and e["id"] in cards and not cards[e["id"]]["text"] and e.get("desc"):
                cards[e["id"]]["text"] = e["desc"]
    for f in flows:
        for b in f["beats"]:
            walk(b.get("events", []))
            for x in b.get("spots", []) + b.get("pool", []):
                walk(x["events"])
    json.dump(cards, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return sum(1 for c in cards.values() if not c["text"])


def main():
    gifts()
    os.makedirs(os.path.join(ROOT, "data", "flow"), exist_ok=True)
    errors, summary = [], []
    flows = [prologue()] + [chapter(c) for c in range(1, 7)]
    print("언령 설명 없음:", describe_cards(flows))
    for flow in flows:
        errors += check(flow)
        kinds = [b["t"] for b in flow["beats"]]
        summary.append(f"{flow['chapter']}: {len(kinds)} beats, freetime {kinds.count('freetime')}, spots {sum(len(b.get('spots', [])) for b in flow['beats'])}, cards {sum(1 for b in flow['beats'] for e in b.get('events', []) if e['type'] == 'card')}")
        with open(os.path.join(ROOT, "data", "flow", flow["chapter"] + ".json"), "w", encoding="utf-8") as f:
            json.dump(flow, f, ensure_ascii=False, indent=1)
    print("\n".join(summary))
    print("ERRORS:", errors or "none")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
