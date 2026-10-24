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
          ("미오의 방", ["mio_room"]), ("객실", ["mio_room"]), ("식당", ["hotel_dining"]), ("로비", ["hotel_lobby"]),
          ("라운지", ["hotel_lounge", "hotel_lobby"]), ("세탁", ["hotel_laundry", "hotel_corridor"]), ("복도", ["hotel_corridor"]),
          ("5층", ["vip_hall", "hotel_corridor"]), ("505", ["vip_505", "vip_hall"]), ("갤러리", ["vip_gallery", "vip_hall"]),
          ("호텔", ["hotel_lobby"]), ("제어반", ["carousel_control"]), ("매표소", ["carousel_control"]), ("회전목마", ["carousel"]),
          ("탑승장", ["carousel"]), ("기념품", ["souvenir_shop"]), ("의무실", ["infirmary"]), ("푸드코트", ["foodcourt"]),
          ("주방", ["foodcourt"]), ("워터파크", ["waterpark"]), ("풀", ["waterpark"]), ("퍼레이드", ["parade"]),
          ("거울", ["mirror"]), ("관람차", ["ferris"]), ("극장", ["theater"]), ("음향실", ["theater_sound", "theater"]),
          ("장치실", ["theater_rigging", "theater"]), ("롤러코스터", ["coaster"]), ("정비동", ["coaster_maintenance", "coaster"]),
          ("발전기", ["coaster_generator", "coaster"]), ("서고", ["castle_library", "castle"]), ("시계탑", ["castle_tower", "castle"]),
          ("연회장", ["castle_hall", "castle"]), ("캐슬", ["castle"]), ("코어", ["core"]), ("제어실", ["core_control", "core"]),
          ("광장", ["plaza"]), ("분수", ["plaza"]), ("벤치", ["plaza"])]
CARD = re.compile(r"(증거|증언|규칙|마법|메모|노트)\s*카드\s*[:：]?\s*(.*?)\s*\(?([ETMNR]\d?-\d+(?:-[a-z])?)\)?")
OPTION = re.compile(r"^-?\s*([A-F])\.\s*(.*)$")
REACT = re.compile(r"\[([^\]]+)\]\s*\"([^\"]+)\"(?:\s*\{([^}]*)\})?")

backgrounds = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(ROOT, "bg")) if f.endswith(".webp"))


def background(text, night=False):
    for word, prefixes in PLACES:
        if word in text:
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
                out.append({"type": "card", "id": m.group(3), "name": m.group(2).strip(" :") or m.group(3), "text": e["text"]})
            else:
                out.append({"type": "ui", "text": e["text"]})
        elif t == "break":
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
    return {"t": "scene", "id": f"{file_key}:{s['id']}", "title": s["title"], "events": convert(s["events"], f"{file_key}:{s['id']}", s["title"])}


def shift(events, at):
    """at 위치에 하나 끼워 넣은 뒤 goto·보기 번호를 맞춘다"""
    for e in events:
        if e["type"] == "goto" and e["to"] > at:
            e["to"] += 1
        if e["type"] == "menu":
            for o in e["options"]:
                if o["to"] > at:
                    o["to"] += 1


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
                pool.append({"who": who_of(s["title"]), **scene_beat(s, key)})
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
                spots.append(b)
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
                    spots.append(b)
            else:
                beats.append(scene_beat(s, "16a"))
    beats += found
    if intro:
        beats.append(intro)
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


def main():
    gifts()
    os.makedirs(os.path.join(ROOT, "data", "flow"), exist_ok=True)
    errors, summary = [], []
    for flow in [prologue()] + [chapter(c) for c in range(1, 7)]:
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
