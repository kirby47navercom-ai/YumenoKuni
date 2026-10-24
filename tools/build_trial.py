#!/usr/bin/env python3
"""
재판 표(data/tables/*.json 의 stream) → 논스톱 논의 데이터(data/trials/{접두}.json).
  python tools/build_trial.py      (build_data.py 다음에 실행)
약점 단어 : 각본 표의 문장 안 【...】. 정답 언령 : 「필요」 열의 첫 카드 ID.
문장 종류 : 노란 + 【】 = weak / 동의 = agree / 잡담 = noise / 그 외 = plain
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARD = re.compile(r"\b[ETMN]\d-\d+(?:-[a-z])?\b")
WEAK = re.compile(r"【([^】]+)】")


def card_names():
    names = {}
    for c in json.load(open(os.path.join(ROOT, "data", "evidence.json"), encoding="utf-8")):
        label = c.get("label") or (c.get("cells") or [c["id"]])[0]
        names[c["id"]] = re.sub(r"\s*\(" + re.escape(c["id"]) + r"\)\s*$", "", label).strip()
    return names


def line_of(row):
    _, speaker, text, verdict, need = (row + [""] * 5)[:5]
    text = text.strip().strip('"')
    m = WEAK.search(text)
    item = {"speaker": speaker.strip(), "text": WEAK.sub(r"\1", text)}
    if m and "노란" in verdict:
        answer = CARD.search(need)
        if not answer:
            raise ValueError(f"약점 정답 카드 없음 : {row}")
        pre = text[:m.start()]
        item["weak"] = {"start": len(WEAK.sub(r"\1", pre)), "word": m.group(1), "answer": answer.group(0)}
        item["kind"] = "weak"
    elif "동의" in verdict:
        item["kind"] = "agree"
    elif "잡담" in verdict:
        item["kind"] = "noise"
    else:
        item["kind"] = "plain"
    return item


def build(path, names):
    chapter = os.path.basename(path).split("_")[0]
    debates = []
    for t in json.load(open(path, encoding="utf-8"))["tables"]:
        if t["kind"] != "stream":
            continue
        lines = [line_of(r) for r in t["rows"]]
        weak = [l for l in lines if l["kind"] == "weak"]
        if not weak:
            continue
        answers = [l["weak"]["answer"] for l in weak]
        # 장전 탄환 : 정답 + 같은 장 카드 중 앞쪽 몇 장(헷갈림용), 최대 5발
        same = [c for c in names if c[1] == chapter[0] and c[0] in "ET" and c not in answers]
        bullets = (answers + same)[:5]
        sid = t["section"].split()[0]
        debates.append({"id": f"{chapter}:{sid}", "title": t["section"], "lines": lines,
                        "bullets": [{"id": b, "name": names.get(b, b)} for b in bullets]})
    return chapter, debates


def main():
    names = card_names()
    out = os.path.join(ROOT, "data", "trials")
    os.makedirs(out, exist_ok=True)
    total = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "tables", "1*b_*.json"))):
        chapter, debates = build(f, names)
        if debates:
            json.dump({"debates": debates}, open(os.path.join(out, chapter + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            total += len(debates)
            print(chapter, len(debates), "논의")
    print("total", total)


if __name__ == "__main__":
    main()
