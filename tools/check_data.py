#!/usr/bin/env python3
"""
data/ 의 무결성 검사.
  1) 재판 표(스트림·쇼다운 등)가 참조하는 증거·증언·노트·마법 카드 ID 가 정의되어 있는가
  2) 장면 UID 중복
  3) 마크다운 코드 펜스(```) 균형
  4) 질의(Q) 번호가 장당 5개 이하인가
사용 : python tools/check_data.py   (오류가 있으면 종료 코드 1)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
SRC = os.path.join(ROOT, "docs", "design")
errors = []
warns = []

cards = {c["id"] for c in json.load(open(os.path.join(D, "evidence.json"), encoding="utf-8"))}
# 노트 후보는 일상 장면에서 "N1-01" 형태로 본문에 정의되므로 본문 전체에서 수집
body_ids = set()
for f in glob.glob(os.path.join(SRC, "1*.md")):
    body_ids |= set(re.findall(r"\b[ETMN]\d-\d+(?:-[a-z])?\b", open(f, encoding="utf-8").read()))

ID = re.compile(r"\b([ETMN]\d-\d+)(?:-[a-z])?\b")

# 1) 표 참조
for f in sorted(glob.glob(os.path.join(D, "tables", "*.json"))):
    data = json.load(open(f, encoding="utf-8"))
    for t in data["tables"]:
        if t["kind"] not in ("stream", "showdown", "timeline"):
            continue
        for row in t["rows"]:
            for cell in row:
                for m in ID.finditer(cell):
                    cid = m.group(0)
                    base = m.group(1)
                    if cid not in cards and base not in cards and cid not in body_ids and base not in body_ids:
                        errors.append(f"{os.path.basename(f)} [{t['section'][:20]}] 정의되지 않은 카드 {cid}")

# 2) 장면 UID 중복
seen = {}
for f in sorted(glob.glob(os.path.join(D, "scenes", "*.json"))):
    for sc in json.load(open(f, encoding="utf-8"))["scenes"]:
        u = sc["uid"]
        if u in seen:
            warns.append(f"중복 UID {u} ({os.path.basename(f)})")
        seen[u] = 1

# 3) 코드 펜스 균형
for f in sorted(glob.glob(os.path.join(SRC, "*.md"))):
    n = open(f, encoding="utf-8").read().count("```")
    if n % 2:
        errors.append(f"{os.path.basename(f)} 코드 펜스 홀수({n})")

# 4) 질의 번호
for f in sorted(glob.glob(os.path.join(SRC, "1[1-6]b_*.md"))):
    txt = open(f, encoding="utf-8").read()
    qs = set(re.findall(r"\bQ([1-9])\b", txt))
    if len(qs) > 5:
        errors.append(f"{os.path.basename(f)} 질의 번호 5개 초과 {sorted(qs)}")

print("ERRORS:" if errors else "ERRORS: none")
for e in errors:
    print(" -", e)
print("WARNINGS:" if warns else "WARNINGS: none")
for w in warns[:20]:
    print(" -", w)
sys.exit(1 if errors else 0)
