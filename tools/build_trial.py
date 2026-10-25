#!/usr/bin/env python3
"""
V3 재판 대본(docs/design/1Nc_*.md) → 재판 데이터(data/trials/{접두}.json).
  python tools/build_trial.py
단계 : `### T-번호 종류 : 제목`. 형식 규칙은 11c 머리말.
출력 : {"stages":[…], "debates":[…]}  — debates 는 논스톱·패닉 논의만 뽑은 것(게임의 논의 모드가 읽는다).
검사 : 정답 카드 ID 가 evidence.json·본문에 정의되어 있는지, 약점 【】 이 있는지. 오류가 있으면 종료 코드 1.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARD = re.compile(r"\b(?:[ETMN]\d-\d+(?:-[a-z])?|R-\d+)\b")
WEAK = re.compile(r"【([^】]+)】")
HEAD = re.compile(r"^### T-(\d+) (.+?)(?: [①-⑨])? : (.+)$", re.M)
SAY = re.compile(r'^\[([^\]]+)\] "(.*?)"(?: \{([^}]*)\})?')
GENERIC_SPOTS = ["바닥의 얼룩", "창문 틈", "천장 구석", "벽의 그림"]
KINDS = {"개정": "opening", "논스톱 논의": "nonstop", "패닉 논의": "panic", "객관식": "choice", "언령 고르기": "bullet",
         "지점 고르기": "spot", "인물 지목": "person", "인터럽트": "interrupt", "반론 쇼다운": "showdown", "논의 스크럼": "scrum",
         "섬광 애너그램": "anagram", "발굴 이매지네이션": "mindmine", "브레인 드라이브": "taxi", "이론 무장": "armament",
         "클라이맥스 추리": "climax", "투표": "vote", "휴정": "intermission", "장면": "scene"}
SLUG = {"미오": "mio", "레이": "rei", "소라": "sora", "켄": "ken", "나나": "nana", "리쿠": "riku", "아카리": "akari", "유우": "yuu",
        "코토": "koto", "사츠키": "satsuki", "타이가": "taiga", "린": "rin", "쇼": "sho", "아이": "ai", "하루카": "haruka", "카에데": "kaede"}
errors = []
MOTIONS = {"흐름": "slide", "날아듦": "fly", "회전": "swirl", "쾅": "slam", "일렁임": "wave", "떨림": "shake", "모임": "assemble", "돌진": "zoom", "솟음": "rise", "한 글자씩": "type", "통통": "bounce", "나선": "spiral"}
NAME = {v: k for k, v in SLUG.items()} if "SLUG" in globals() else {}


def card_name(c):
    """evidence.json 한 장 → 화면에 쓸 짧은 이름. (ID) 꼬리·「해금」 같은 원문 메모를 걷어 낸다."""
    cid, label = c["id"], (c.get("label") or "").strip()
    m = re.search(r"「([^」]+)」", label)
    if cid.startswith("M") and m:
        return "마법 「" + m.group(1) + "」"
    m = re.match(re.escape(cid) + r"\s*\(([^)]+)\)", label)
    if m:
        inner = m.group(1).strip()
        return inner + "의 증언" if cid.startswith("T") and len(inner) <= 4 else inner
    label = re.sub(r"\s*\(" + re.escape(cid) + r"\)\s*$", "", label).strip()
    if label and not label.startswith(cid):
        return label
    cells = c.get("cells") or []
    return (cells[0] + "의 증언") if cid.startswith("T") and cells else (cells[0] if cells else cid)


def card_text(c):
    cells = c.get("cells") or []
    return cells[1].strip('"') if len(cells) > 1 else ""


def known_cards():
    ids, names = set(), {}
    for c in json.load(open(os.path.join(ROOT, "data", "evidence.json"), encoding="utf-8")):
        names[c["id"]] = card_name(c)
        ids.add(c["id"])
    for f in glob.glob(os.path.join(ROOT, "docs", "design", "1*.md")):
        ids |= set(CARD.findall(open(f, encoding="utf-8").read()))
    for m in re.finditer(r"^\| 교칙 (\d+) \| ([^|]+) \| (R-\d+)", open(glob.glob(os.path.join(ROOT, "docs", "spec", "11_*.md"))[0], encoding="utf-8").read(), re.M):
        names[m.group(3)] = "교칙 " + m.group(1)
    return ids, names


def tables(body):
    """마크다운 표 → [헤더, 행…] 목록"""
    out, cur = [], []
    for line in body.splitlines() + [""]:
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                cur.append(cells)
        elif cur:
            out.append(cur)
            cur = []
    return out


def script(body):
    lines = []
    for block in re.findall(r"```\n(.*?)```", body, re.S):
        for raw in block.splitlines():
            m = SAY.match(raw.strip())
            pose = re.search(r"← ?([a-z]+_[A-Z]\w*)", raw)
            if m:
                lines.append({"speaker": m.group(1), "text": m.group(2), "emo": m.group(3) or ""} | ({"pose": pose.group(1)} if pose else {}))
            elif raw.strip().startswith("[UI] 투표 →"):
                continue
            elif raw.strip().startswith(("(", "[UI]")):
                lines.append({"speaker": "", "text": raw.strip()})
    return lines


def field(body, name):
    m = re.search(rf"^- {name} : (.+)$", body, re.M)
    return m.group(1).strip() if m else None


def debate_line(row, where):
    num, speaker, text, verdict, need, direction = (row + [""] * 6)[:6]
    text = text.strip().strip('"')
    item = {"speaker": speaker, "text": WEAK.sub(r"\1", text)}
    if direction:
        item["motion"] = MOTIONS.get(direction.strip(), "")
    m = WEAK.search(text)
    if verdict in ("노란", "거짓"):
        answer = CARD.search(need)
        if not m or not answer:
            errors.append(f"{where} #{num} : 약점 【】 또는 정답 카드 없음")
            return item | {"kind": "plain"}
        item["kind"] = "weak"
        item["weak"] = {"start": len(WEAK.sub(r"\1", text[:m.start()])), "word": m.group(1), "answer": answer.group(0), "lie": verdict == "거짓"}
        if verdict == "거짓":
            item["weak"]["lieText"] = need.split("거짓 :", 1)[-1].strip()
    elif verdict == "동의":
        item["kind"] = "agree"
        a = CARD.search(need)
        if a:
            item["agree"] = a.group(0)
    elif verdict == "잡담":
        item["kind"] = "noise"
    else:
        item["kind"] = "plain"
    return item


def stage(num, kind_ko, title, body, chapter):
    kind = KINDS.get(kind_ko)
    where = f"{chapter} T-{num}"
    if not kind:
        errors.append(f"{where} : 모르는 단계 종류 「{kind_ko}」")
        kind = "scene"
    s = {"id": f"{chapter}:T-{num}", "kind": kind, "title": title, "script": script(body)}
    if kind in ("showdown", "armament"):
        who = next((SLUG[n] for n in sorted(SLUG, key=len, reverse=True) if n in title), None)
        if who:
            s["opponent"] = who
    t = tables(body)
    if kind in ("nonstop", "panic"):
        rows = t[0][1:] if t else []
        s["lines"] = [debate_line(r, where) for r in rows]
        if not any(l["kind"] == "weak" for l in s["lines"]):
            errors.append(f"{where} : 논파할 약점이 없음")
    elif kind == "choice":
        s["question"] = field(body, "질문")
        s["options"] = [re.sub(r"^[A-D]\) ", "", o.strip()) for o in (field(body, "보기") or "").split("|")]
        s["answer"] = "ABCD".index((field(body, "정답") or "A")[0])
    elif kind in ("bullet", "person", "spot", "anagram", "mindmine"):
        s["question"] = field(body, "질문")
        s["answer"] = field(body, "정답")
        if field(body, "그림"):
            s["image"] = field(body, "그림")
        if kind == "bullet" and not CARD.fullmatch(s["answer"] or ""):
            errors.append(f"{where} : 언령 고르기 정답이 카드 ID 가 아님")
        if kind == "person" and s["answer"] not in SLUG.values():
            errors.append(f"{where} : 인물 지목 정답 slug 오류")
        if kind == "mindmine":
            a = CARD.search(s["answer"] or "")
            s["card"] = a.group(0) if a else s["answer"]  # 카드가 아닌 물건(그림 속 정답)은 이름 그대로
    elif kind == "showdown":
        rows = t[0][1:] if t else []
        s["lines"] = [{"text": r[1].strip('"'), "action": r[2]} for r in rows]
        last = rows[-1] if rows else ["", "", ""]
        m, a = WEAK.search(last[1]), CARD.search(last[2])
        if not m or not a:
            errors.append(f"{where} : 마지막 발언의 약점·언령의 칼 없음")
        else:
            s["blade"] = {"word": m.group(1), "answer": a.group(0)}
            s["lines"][-1]["text"] = WEAK.sub(r"\1", last[1].strip('"'))
    elif kind == "scrum":
        rows = t[0][1:] if t else []
        s["pairs"] = []
        for r in rows:
            them, us = WEAK.search(r[2]), WEAK.search(r[4])
            if not them or not us or them.group(1) != us.group(1):
                errors.append(f"{where} 합{r[0]} : 키워드 【】 가 양쪽에 같지 않음")
                continue
            s["pairs"].append({"them": r[1], "themText": WEAK.sub(r"\1", r[2].strip('"')), "us": r[3], "usText": WEAK.sub(r"\1", r[4].strip('"')), "keyword": them.group(1)})
    elif kind == "taxi":
        rows = t[0][1:] if t else []
        s["questions"] = [{"q": r[0], "options": [o.strip() for o in r[1].split("·")], "answer": r[2].strip()} for r in rows]
        for q in s["questions"]:
            if q["answer"] not in q["options"]:
                errors.append(f"{where} : 택시 정답 「{q['answer']}」 이 보기에 없음")
    elif kind == "armament":
        rows = t[0][1:] if t else []
        s["lines"] = [r[1].strip('"') for r in rows]
        s["final"] = [w.strip() for w in (field(body, "마지막 일격") or "").split("|")]
        if len(s["final"]) != 4:
            errors.append(f"{where} : 마지막 일격은 4조각")
    elif kind == "vote":
        m = re.search(r"\[UI\] 투표 → ([^\s(]+)", body)
        s["answer"] = SLUG.get(m.group(1)) if m else None
        if not s["answer"]:
            errors.append(f"{where} : 투표 정답(「[UI] 투표 → 이름」) 없음")
    elif kind == "climax":
        rows = t[0][1:] if t else []
        s["panels"] = [{"no": int(r[0]), "caption": r[1], "blank": r[2] == "빈칸"} for r in rows]
        s["pieces"] = [p.strip() for p in (field(body, "조각") or "").split("/")]
    return s


def build(path, ids, names):
    chapter = os.path.basename(path).split("_")[0]
    text = open(path, encoding="utf-8").read()
    heads = list(HEAD.finditer(text))
    stages = []
    for i, h in enumerate(heads):
        body = text[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        stages.append(stage(h.group(1), h.group(2), h.group(3), body, chapter))
    chapter_cards = [c for c in sorted(names) if c[:2] in (f"E{chapter[1]}", f"T{chapter[1]}", f"M{chapter[1]}")]
    spots = [x["answer"] for x in stages if x["kind"] == "spot"]
    for x in stages:
        if x["kind"] in ("bullet", "mindmine", "showdown"):
            ans = {"bullet": x.get("answer"), "mindmine": x.get("card"), "showdown": (x.get("blade") or {}).get("answer")}[x["kind"]]
            others = [c for c in chapter_cards if c != ans]
            k = int(x["id"].split("-")[-1])
            pick = [others[(k * 3 + j * 5) % len(others)] for j in range(2 if x["kind"] == "mindmine" else 4)] if others else []
            opts = list(dict.fromkeys([ans] + pick))
            opts = opts[k % len(opts):] + opts[:k % len(opts)]
            x["options"] = [{"id": o, "name": names.get(o, o)} for o in opts]
        elif x["kind"] == "spot":
            others = [a for a in spots if a != x["answer"]] + GENERIC_SPOTS
            k = int(x["id"].split("-")[-1])
            opts = [x["answer"], others[k % len(others)], others[(k + 1) % len(others)]]
            x["options"] = opts[k % 3:] + opts[:k % 3]
    for s in stages:
        for ref in CARD.findall(json.dumps({k: v for k, v in s.items() if k != "script"}, ensure_ascii=False)):
            if ref not in ids and ref not in names:
                errors.append(f"{s['id']} : 정의되지 않은 카드 {ref}")
    # 논의 모드용 : 언령은 정답 + 같은 장의 다른 증거(최대 5)
    debates = []
    for s in stages:
        if s["kind"] not in ("nonstop", "panic"):
            continue
        answers = list(dict.fromkeys(l["weak"]["answer"] for l in s["lines"] if l["kind"] == "weak"))
        same = [c for c in sorted(names) if c[:2] in (f"E{chapter[1]}", f"T{chapter[1]}") and c not in answers]
        bullets = (answers + same)[:5]
        debates.append({"id": s["id"], "title": s["title"], "kind": s["kind"], "lines": s["lines"],
                        "bullets": [{"id": b, "name": names.get(b, b)} for b in bullets]})
    return chapter, stages, debates


def write_kotodama():
    out = {}
    for c in json.load(open(os.path.join(ROOT, "data", "evidence.json"), encoding="utf-8")):
        out[c["id"]] = {"name": card_name(c), "text": card_text(c), "kind": c.get("kind", "")}
    with open(os.path.join(ROOT, "data", "kotodama.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


def main():
    write_kotodama()
    ids, names = known_cards()
    out = os.path.join(ROOT, "data", "trials")
    os.makedirs(out, exist_ok=True)
    for old in glob.glob(os.path.join(out, "*.json")):
        os.remove(old)
    for f in sorted(glob.glob(os.path.join(ROOT, "docs", "design", "1[1-6]c_*.md"))):
        chapter, stages, debates = build(f, ids, names)
        json.dump({"stages": stages, "debates": debates}, open(os.path.join(out, chapter + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        counts = {}
        for s in stages:
            counts[s["kind"]] = counts.get(s["kind"], 0) + 1
        print(chapter, len(stages), "단계", counts)
    print("ERRORS:" if errors else "ERRORS: none")
    for e in errors:
        print(" -", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
