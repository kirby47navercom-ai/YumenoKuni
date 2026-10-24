#!/usr/bin/env python3
"""
docs/design/*.md 의 각본을 게임이 읽는 JSON 으로 변환한다.

  python tools/build_data.py            # data/ 아래에 scenes, evidence, characters 생성

출력
  data/scenes/<파일명>.json    장면 목록. 각 장면 = {id, title, events[]}
  data/evidence.json          증거·증언·마법·노트 카드(표의 행 그대로 + 챕터)
  data/characters.json        02_전자수첩_UI_인적사항.md 의 인물 데이터
  data/_report.txt            변환 통계

이벤트 타입
  say         {speaker, kind(normal|monologue|broadcast|voice), text, emo}
  stage       (지문)  연출 지시. 사양서 01 의 명령으로 후처리
  ui          [UI] 안내 문구 / 시스템 메시지
  choice      ▶ 선택지
  break       ── 전환 ──
  note        [복선] 등 제작 메모(게임에서는 숨김)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "design")
OUT = os.path.join(ROOT, "data")

SAY = re.compile(r'^\[([^\]]+)\]\s*"(.*?)"\s*(\{[^}]*\})?\s*(←.*)?$')
SAY_NOQUOTE = re.compile(r'^\[([^\]]+)\]\s*(.+?)\s*(\{[^}]*\})?\s*(←.*)?$')
STAGE = re.compile(r'^\((.*)\)\s*$')
UI = re.compile(r'^\[UI\]\s*(.*)$')
BREAK = re.compile(r'^──\s*(.*?)\s*──$')
HEAD = re.compile(r'^(#{1,4})\s+(.*)$')
ID_IN_HEAD = re.compile(r'^((?:P-\d+)|(?:\d-[A-Z]-?\d+(?:-[a-z])?)|(?:\d-[A-Z]{1,2}-\d+)|(?:[A-F]-\d+(?:-[a-z])?))\b')
CARD = re.compile(r'^\|\s*([ETMN]\d-\d+(?:-[a-z])?)\s*\|(.*)\|\s*$')


def kind_of(speaker):
    if "(독백)" in speaker:
        return "monologue", speaker.replace("(독백)", "")
    if "(방송)" in speaker or "(머신 음성)" in speaker:
        return "broadcast", re.sub(r"\(.*?\)", "", speaker)
    if "(음성)" in speaker or "(영상)" in speaker:
        return "voice", re.sub(r"\(.*?\)", "", speaker)
    return "normal", speaker


def parse_events(lines):
    ev = []
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        m = UI.match(s)
        if m:
            ev.append({"type": "ui", "text": m.group(1)})
            continue
        m = BREAK.match(s)
        if m:
            ev.append({"type": "break", "text": m.group(1)})
            continue
        if s.startswith("▶") or s.startswith("▶"):
            ev.append({"type": "choice", "text": s.lstrip("▶ ").strip()})
            continue
        m = SAY.match(s)
        if m and not s.startswith("[UI]"):
            kind, who = kind_of(m.group(1))
            e = {"type": "say", "speaker": who, "kind": kind, "text": m.group(2)}
            if m.group(3):
                e["emo"] = m.group(3).strip("{}").strip()
            if m.group(4):
                e["note"] = m.group(4).strip()
            ev.append(e)
            continue
        m = STAGE.match(s)
        if m:
            ev.append({"type": "stage", "text": m.group(1)})
            continue
        m = SAY_NOQUOTE.match(s)
        if m and s.startswith("[") and "]" in s:
            kind, who = kind_of(m.group(1))
            e = {"type": "say", "speaker": who, "kind": kind, "text": m.group(2).strip('"')}
            if m.group(3):
                e["emo"] = m.group(3).strip("{}").strip()
            ev.append(e)
            continue
        # 나머지는 제작 메모로 보존
        ev.append({"type": "note", "text": s})
    return ev


def convert_file(path):
    scenes = []
    cur = {"id": "_root", "title": os.path.basename(path), "events": []}
    in_code = False
    buf = []
    for raw in open(path, encoding="utf-8").read().split("\n"):
        if raw.strip().startswith("```"):
            if in_code:
                cur["events"].extend(parse_events(buf))
                buf = []
            in_code = not in_code
            continue
        if in_code:
            buf.append(raw)
            continue
        h = HEAD.match(raw)
        if h:
            if cur["events"]:
                scenes.append(cur)
            title = h.group(2).strip()
            m = ID_IN_HEAD.match(title)
            cur = {"id": m.group(1) if m else re.sub(r"\W+", "_", title)[:40], "title": title, "events": []}
            continue
        s = raw.strip()
        if s.startswith("▶"):
            cur["events"].append({"type": "choice", "text": s.lstrip("▶ ").strip()})
        elif "장소" in s and ":" in s and "location" not in cur:
            loc = s.split(":", 1)[1].strip().strip("*").strip()
            cur["location"] = re.sub(r"\*\*|\(.*?\)$", "", loc).strip()
    if cur["events"]:
        scenes.append(cur)
    return scenes


UI_CARD = re.compile(r"(증거 카드|증언 카드|메모 카드|마법 카드|규칙 카드)\s*:\s*(.+)")
CARD_ID = re.compile(r"\b([ETMN]\d-\d+(?:-[a-z])?)\b")


def parse_cards(files):
    cards = {}
    for path in files:
        base = os.path.basename(path)
        for raw in open(path, encoding="utf-8").read().split("\n"):
            m = CARD.match(raw)
            if m:
                cells = [c.strip() for c in m.group(2).split("|")]
                cards.setdefault(m.group(1), {"id": m.group(1), "source": base})["cells"] = cells
                continue
            m = UI_CARD.search(raw)
            if m:
                ids = CARD_ID.findall(m.group(2))
                if ids:
                    c = cards.setdefault(ids[0], {"id": ids[0], "source": base})
                    c["kind"] = m.group(1)
                    c["label"] = re.sub(r"\s*획득\.?.*$", "", m.group(2)).strip()
    return sorted(cards.values(), key=lambda c: c["id"])


def parse_characters(path):
    chars = []
    cur = None
    for raw in open(path, encoding="utf-8").read().split("\n"):
        h = re.match(r"^###\s+(\d{4})\s+(.*)$", raw)
        if h:
            cur = {"id": h.group(1), "heading": h.group(2).strip(), "fields": {}}
            chars.append(cur)
            continue
        if cur is None:
            continue
        if raw.startswith("## "):
            cur = None
            continue
        m = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", raw)
        if m and m.group(1) not in ("항목", "---") and not m.group(1).startswith("-"):
            cur["fields"][m.group(1)] = m.group(2)
    return chars


EXPR_RULES = [
    ("anger", ["분노", "적의", "격앙", "소리침", "외침"]),
    ("surprise", ["놀람", "숨을 삼킴", "당황", "흠칫", "움찔", "눈이 커", "숨이 멈춤", "눈을 크게", "민망", "뒷걸음", "놀라"]),
    ("smile", ["웃음", "미소", "활짝", "환호", "신남", "장난", "윙크", "씩", "밝", "활기", "박수", "손뼉", "감동", "당당", "씩씩", "팔짝", "환"]),
    ("sad", ["눈물", "울음", "눈가", "주저앉", "오열", "침울", "흐느", "떨림", "떨리"]),
    ("worry", ["걱정", "불안", "소극", "조심", "경계", "작게", "소심", "말끝", "흔들림"]),
    ("serious", ["단호", "결의", "차분", "정리", "정중", "단정", "확인", "설명", "진지", "담백", "무표정", "낮게", "낮은", "담담", "탄환", "침묵", "조용"]),
    ("closed", ["눈을 감", "눈감"]),
    ("whisper", ["속삭임"]),
]


def map_emotion(tag):
    t = tag.replace(" ", "")
    for expr, keys in EXPR_RULES:
        if any(k.replace(" ", "") in t for k in keys):
            return expr
    return "neutral"


def build_emotion_map(all_tags):
    return {tag: map_emotion(tag) for tag in sorted(all_tags)}


def build_scene_index(files):
    rows = []
    for f in files:
        data = json.load(open(os.path.join(OUT, "scenes", os.path.splitext(os.path.basename(f))[0] + ".json"), encoding="utf-8"))
        for sc in data["scenes"]:
            speakers = []
            for e in sc["events"]:
                if e["type"] == "say" and e["speaker"] not in speakers:
                    speakers.append(e["speaker"])
            dur = re.search(r"\((\d+)분\)", sc["title"])
            rows.append({
                "file": data["source"], "id": sc["id"], "uid": sc.get("uid", sc["id"]), "title": sc["title"],
                "location": sc.get("location", ""), "cast": speakers,
                "events": len(sc["events"]), "minutes": int(dur.group(1)) if dur else None,
            })
    return rows


def extract_tables(path):
    """마크다운 표를 섹션별로 추출한다. 재판 데이터(스트림·질의·시간표·그리드) 용."""
    out = []
    sec = ""
    lines = open(path, encoding="utf-8").read().split("\n")
    i = 0
    in_code = False
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            in_code = not in_code
        h = HEAD.match(ln)
        if h and not in_code:
            sec = h.group(2).strip()
        if (not in_code and ln.startswith("|") and i + 1 < len(lines)
                and re.match(r"^\|\s*:?-{2,}", lines[i + 1])):
            header = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            hs = "".join(header)
            if "화자" in hs and "문장" in hs:
                kind = "stream"
            elif ("발언" in hs) and "대응" in hs:
                kind = "showdown"
            elif "질문" in hs and "답" in hs:
                kind = "query"
            elif "카드" in hs and ("정답" in hs):
                kind = "timeline"
            elif "인물" in hs and ("~" in hs):
                kind = "grid"
            elif header and header[0] in ("ID", "번호"):
                kind = "cards"
            else:
                kind = "table"
            out.append({"section": sec, "kind": kind, "header": header, "rows": rows})
            i = j
            continue
        i += 1
    return out


def main():
    os.makedirs(os.path.join(OUT, "scenes"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "tables"), exist_ok=True)
    files = sorted(glob.glob(os.path.join(SRC, "1*.md")))
    report = []
    total = 0
    for f in files:
        scenes = convert_file(f)
        n = sum(len(s["events"]) for s in scenes)
        total += n
        prefix = os.path.basename(f).split("_")[0]
        for sc in scenes:
            sc["uid"] = prefix + ":" + sc["id"]
        tb = extract_tables(f)
        with open(os.path.join(OUT, "tables", os.path.splitext(os.path.basename(f))[0] + ".json"), "w", encoding="utf-8") as fh:
            json.dump({"source": os.path.basename(f), "tables": tb}, fh, ensure_ascii=False, indent=1)
        report.append(f"  tables={len(tb)} (stream={sum(1 for t in tb if t['kind']=='stream')}, showdown={sum(1 for t in tb if t['kind']=='showdown')}, query={sum(1 for t in tb if t['kind']=='query')}, timeline={sum(1 for t in tb if t['kind']=='timeline')}, grid={sum(1 for t in tb if t['kind']=='grid')})")
        out = os.path.join(OUT, "scenes", os.path.splitext(os.path.basename(f))[0] + ".json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"source": os.path.basename(f), "scenes": scenes}, fh, ensure_ascii=False, indent=1)
        report.append(f"{os.path.basename(f)}: scenes={len(scenes)} events={n}")
    cards = parse_cards(files)
    with open(os.path.join(OUT, "evidence.json"), "w", encoding="utf-8") as fh:
        json.dump(cards, fh, ensure_ascii=False, indent=1)
    report.append(f"cards={len(cards)}")
    chars = parse_characters(os.path.join(SRC, "02_전자수첩_UI_인적사항.md"))
    with open(os.path.join(OUT, "characters.json"), "w", encoding="utf-8") as fh:
        json.dump(chars, fh, ensure_ascii=False, indent=1)
    report.append(f"characters={len(chars)}")
    tags = set()
    for f in files:
        d = json.load(open(os.path.join(OUT, "scenes", os.path.splitext(os.path.basename(f))[0] + ".json"), encoding="utf-8"))
        for sc in d["scenes"]:
            for e in sc["events"]:
                if e["type"] == "say" and "emo" in e:
                    tags.add(e["emo"])
    emap = build_emotion_map(tags)
    with open(os.path.join(OUT, "emotion_map.json"), "w", encoding="utf-8") as fh:
        json.dump(emap, fh, ensure_ascii=False, indent=1)
    report.append(f"emotion_tags={len(emap)}")
    idx = build_scene_index(files)
    with open(os.path.join(OUT, "scene_index.json"), "w", encoding="utf-8") as fh:
        json.dump(idx, fh, ensure_ascii=False, indent=1)
    report.append(f"scene_index={len(idx)}")
    report.append(f"total_events={total}")
    with open(os.path.join(OUT, "_report.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(report))
    print("\n".join(report))


if __name__ == "__main__":
    sys.exit(main())
