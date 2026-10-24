#!/usr/bin/env python3
"""data/scene_index.json 으로 docs/spec/10_장면_인덱스.md 를 만든다 (배경·BGM 자동 배정 포함)."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
idx = json.load(open(os.path.join(ROOT, "data", "scene_index.json"), encoding="utf-8"))

BG_RULES = [
    ("분수", "bg_plaza_fountain"), ("광장", "bg_plaza"), ("인포메이션", "bg_info_center"),
    ("호텔 로비", "bg_hotel_lobby"), ("로비", "bg_hotel_lobby"), ("라운지", "bg_hotel_lounge"),
    ("식당", "bg_hotel_dining"), ("객실", "bg_hotel_room"), ("복도", "bg_hotel_hall"), ("뒤뜰", "bg_hotel_yard"), ("마당", "bg_hotel_yard"),
    ("푸드코트", "bg_foodcourt"), ("주방", "bg_kitchen"), ("회전목마", "bg_carousel"), ("제어반", "bg_carousel_control"),
    ("기념품샵", "bg_shop"), ("의무실", "bg_clinic"), ("워터파크", "bg_waterpark"), ("웨이브 풀", "bg_wave_pool"), ("매점", "bg_snack"),
    ("퍼레이드", "bg_parade"), ("거울 미로", "bg_mirror_maze"), ("중앙 홀", "bg_mirror_hall"), ("대관람차", "bg_ferris_wheel"),
    ("극장", "bg_theater"), ("시어터", "bg_theater"), ("음향실", "bg_sound_room"), ("장치실", "bg_rigging"),
    ("롤러코스터", "bg_coaster"), ("정비동", "bg_maintenance"), ("VIP", "bg_vip_floor"), ("5층", "bg_vip_floor"), ("갤러리", "bg_gallery"),
    ("대연회장", "bg_ballroom"), ("서고", "bg_library"), ("시계탑", "bg_clock_tower"), ("갑옷", "bg_armor_hall"), ("수장고", "bg_vault"),
    ("대피소", "bg_shelter"), ("점검 통로", "bg_inspection_b"), ("코어 홀", "bg_core_hall"), ("제어실", "bg_core_control"), ("코어", "bg_core"),
    ("재판", "bg_court"), ("정문", "bg_gate"), ("산책로", "bg_walkway"), ("시계탑", "bg_clock_tower"),
]


def bg_of(r):
    text = (r["location"] or "") + " " + r["title"]
    for k, v in BG_RULES:
        if k in text:
            return v
    return "bg_plaza"


def chapter_of(file):
    m = re.match(r"(\d)(\d)?", file)
    n = int(file[1]) if file.startswith("1") and len(file) > 1 and file[1].isdigit() else 0
    return file[:3]


def bgm_of(r):
    f = r["file"]
    t = r["title"]
    ch = {"10": "P", "11": "1", "12": "2", "13": "3", "14": "4", "15": "5", "16": "6"}.get(f[:2], "?")
    daily = {"P": "bgm_pro_arrival", "1": "bgm_daily_pastel", "2": "bgm_daily_summer", "3": "bgm_daily_night",
             "4": "bgm_daily_grey", "5": "bgm_daily_mono", "6": "bgm_core"}[ch]
    if "프리타임" in t or re.match(r"^B-\d+ .*[①②③]", t):
        return "bgm_freetime"
    if "동기" in t or "-M-" in r["uid"]:
        return "bgm_motive"
    if "처형" in t or "-X-" in r["uid"]:
        return "bgm_execution_" + (ch if ch.isdigit() else "a")
    if "에필" in t or "-E-" in r["uid"]:
        return "bgm_epilogue"
    if "래피 등장" in t or "규칙 선언" in t:
        return "bgm_rappy_theme"
    if "발견" in t:
        return "bgm_discovery"
    if "수사" in t or t.startswith("C-"):
        return "bgm_investigation"
    if t.startswith("D-") or ch == "6" and t.startswith("B-"):
        if "스트림" in t:
            return "bgm_trial_stream"
        if "쇼다운" in t:
            return "bgm_trial_showdown"
        if "피날레" in t or "투표" in t:
            return "bgm_trial_finale"
        return "bgm_trial_main"
    if t.startswith("00-"):
        return "bgm_title"
    return daily


rows = []
cur = None
out = ["# 제작 사양서 10 — 장면 인덱스 (자동 생성)", "",
       "> `tools/make_index_md.py`가 `data/scene_index.json`에서 생성한다. 배경·BGM은 **자동 배정 초안**이며 장면별로 수정 가능.",
       "> 장면 UID = `파일접두:장면ID` (예 `11a:1-S2`). 총 %d개 장면." % len(idx), ""]
for r in idx:
    if r["file"] != cur:
        cur = r["file"]
        out += ["", "## " + cur, "", "| UID | 제목 | 위치 | 출연 | 대사수 | 분 | 배경 | BGM |", "|---|---|---|---|---|---|---|---|"]
    cast = ", ".join(r["cast"][:6]) + (" 외" if len(r["cast"]) > 6 else "")
    out.append("| `%s` | %s | %s | %s | %d | %s | `%s` | `%s` |" % (
        r["uid"], r["title"].replace("|", "/"), (r["location"] or "").replace("|", "/"), cast,
        r["events"], r["minutes"] or "", bg_of(r), bgm_of(r)))

path = os.path.join(ROOT, "docs", "spec", "10_장면_인덱스.md")
open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
print("rows", len(idx))
