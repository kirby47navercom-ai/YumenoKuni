# 소리 연출 : 장면마다 BGM(bgm), 이벤트마다 곡 전환(music)·효과음(sfx)을 붙인다. build_flow.py main() 이 부른다.
# 기준 = V3 의 소리 문법(docs/spec/16 §5) :
#   일상은 장마다 정해진 일상 곡, 아침 방송은 차임 → 모니터 → 래피 아침 곡, 아침 모임은 상쾌한 곡, 저녁·밤은 조용한 곡.
#   래피가 끼어들면 등장 징글(+효과음) → 래피 곡, 래피가 빠지면 원래 곡으로. 동기 발표는 래피 곡 → 불안곡.
#   사건 전야는 긴장곡. 시체 발견 = 충격음 + 장마다 다른 「Dead Body Found」 징글 → 긴장곡, 발견 방송은 전용 차임.
#   수사 = 수사 곡, 수사 종료 = 재판 준비 곡. 재판 곡은 Source/TrialRunner.hpp(단계별).
#   재판 뒤(에필로그) = 장마다 다른 피아노, 유품·소멸 = 슬픈 곡, 막간 = 가벼운 곡(장 끝 징글로 시작), 미오 혼자 = 밤 곡.
#   인물 대사 : 표정(emo)이 튀는 순간 강조 효과음(호통·놀람·흥분·침울), 무대 설명의 문·발소리·노크 등은 그 소리.
import re

DAILY = {"P": "bgm_daily_pro", "1": "bgm_daily_pastel", "2": "bgm_daily_summer", "3": "bgm_daily_night", "4": "bgm_daily_grey", "5": "bgm_daily_mono", "6": "bgm_core"}
# 사건 전야 : 동기 뒤 사건까지 (장면 UID)
TENSE = {"12a:2-S8-a", "12a:2-S8-b", "12a:2-S8-c", "14a:4-S9", "14a:4-S10-a", "14a:4-S10-b", "14a:4-S10-c", "15a:5-S8-a", "15a:5-S8-b", "13a:3-M-02", "13a:3-M-03"}
PROLOGUE = [("00_1", "bgm_pretitle"), ("00_2", "bgm_night"), ("00_3", "bgm_pro_arrival"), ("P-01", "bgm_pro_arrival"),
            ("P-02", "bgm_pro_intro"), ("2_1", "bgm_pro_intro"), ("2_2", "bgm_pro_intro"), ("2_3", "bgm_pro_intro"),
            ("P-03", "bgm_killing_game"), ("4_1", "bgm_killing_game"), ("4_2", "bgm_tense"),
            ("7_1", "bgm_night"), ("7_2", "bgm_night"), ("7_3", "bgm_night"), ("7_4", "bgm_tense"), ("7_5", "bgm_rappy_after")]
FINAL = {"16a:6-S2": "bgm_warm", "16a:코토와_미오의_약속_강제_이벤트_": "bgm_warm", "16b:C_C_에필로그_후_공통_5분_": "bgm_warm"}
# 래피가 끼어들면 곡을 바꾸는 장면 곡(일상 쪽). 사건·수사·재판 쪽은 곡을 유지한다
RAPPY_SWITCH = set(DAILY.values()) | {"bgm_morning_calm", "bgm_night", "bgm_comedy", "bgm_pro_intro", "bgm_pro_arrival"}
EMO = {"단호": "emo_angry", "주먹": "emo_angry", "놀람": "emo_surprise", "당황": "emo_surprise", "고개를 갸웃": "emo_basic",
       "환호": "emo_excited", "신남": "emo_excited", "활기": "emo_excited", "결의": "emo_excited", "손뼉": "emo_excited", "극적": "sfx_shock",
       "걱정": "emo_gloomy", "눈물": "emo_gloomy", "말끝이 흐려짐": "emo_gloomy", "시선 회피": "emo_gloomy", "소극": "emo_gloomy"}
STAGE = [(r"노크", "sfx_knock"), (r"문을 (세게|쾅)|쾅", "sfx_door_slam"), (r"두드", "sfx_bang_door"), (r"문이 열|문을 열|문이 닫|문을 닫", "sfx_door"),
         (r"달려|뛰어", "sfx_run"), (r"발소리|걸어", "sfx_footstep"), (r"쓰러|넘어", "sfx_fall"), (r"엘리베이터", "sfx_elevator"),
         (r"기계|레버|스위치", "sfx_machine"), (r"딩동", "sfx_ding"), (r"모니터.*(켜|켜지)|화면이 켜", "sfx_tv"), (r"심장|두근", "sfx_heart_slow"),
         (r"깨지|깨진|와장창", "sfx_glass"), (r"폭발", "sfx_explode"), (r"총성|총소리", "sfx_gunshot"), (r"회상", "sfx_flashback"), (r"타이핑|키보드", "sfx_typing")]


def scene_bgm(ch, b, first_interlude):
    uid, title = b["id"], b.get("title", "")
    if b["t"] == "execution":
        return "bgm_sad" if "소멸" in title else "bgm_punishment_time"
    if uid.startswith("17:"):
        base = "bgm_night" if "미오 혼자" in title else "bgm_comedy"
        return "jingle_chapter_end>" + base if first_interlude else base
    if ch == "P":
        for key, cue in PROLOGUE:
            if f":{key}" in uid:
                return cue
        return DAILY["P"]
    if uid in FINAL:
        return FINAL[uid]
    if uid in TENSE:
        return "bgm_tense"
    if "아침 방송" in title:
        return "bgm_morning"
    if "밤 방송" in title:
        return "bgm_rappy_after"
    if "-M-01" in uid:
        return DAILY[ch]  # 래피가 나오면 래피 곡 → 래피가 빠지면 불안곡(아래 rappy)
    if "-M-" in uid:
        return "bgm_motive"
    if "-E-" in uid or "에필로그" in title:
        return f"bgm_epilogue_{ch}" if ch in "12345" else "bgm_warm"
    if b.get("need"):
        return "bgm_sad"  # 유품
    if "수사 종료" in title or "증거 카드 정리" in title:
        return "bgm_trial_prep"
    if "수사 파트" in title or "노트 슬롯" in title:
        return "bgm_investigation_final" if ch == "6" else "bgm_investigation"
    if uid[2:3] == "b":
        return "bgm_tense"  # 사건 쪽(B-…)
    if "아침 모임" in title:
        return "bgm_morning_calm"
    if re.search(r"저녁|밤|호텔의 밤", title):
        return "bgm_night"
    return DAILY[ch]


def rappy(evs, bgm, after):
    """래피 첫 대사 : 등장 징글 → 래피 곡, 마지막 대사 뒤 : 원래 곡(동기 발표면 불안곡)"""
    idx = [i for i, e in enumerate(evs) if e["type"] == "say" and e.get("speaker") == "래피"]
    if not idx:
        return
    first, last = idx[0], idx[-1]
    evs[first].setdefault("sfx", "sfx_rappy")
    evs[first]["music"] = "jingle_rappy>bgm_rappy_theme"
    nxt = next((i for i in range(last + 1, len(evs)) if evs[i]["type"] in ("say", "stage", "ui")), None)
    if nxt is not None:
        evs[nxt]["music"] = after
        evs[nxt].setdefault("sfx", "sfx_rappy")


def body(evs, ch):
    """사망 CG : 충격음 + 시체 발견 징글 → 긴장곡. 그 뒤 래피 첫 대사 = 시체 발견 방송 차임"""
    for i, e in enumerate(evs):
        if e["type"] == "bg" and e.get("bg", "").startswith("cg:death"):
            e["sfx"] = "sfx_shock"
            e["music"] = f"jingle_body_{ch}>bgm_tense" if ch in "12345" else "bgm_tense"
            for x in evs[i + 1:]:
                if x["type"] == "say" and x.get("speaker") == "래피":
                    x["sfx"] = ["sfx_body_chime", "sfx_tv"]
                    x.pop("music", None)
                    break
            return True
    return False


def lines(evs):
    """대사 표정 강조음 · 무대 설명 소리. 같은 사람의 같은 표정이 이어지면 처음 한 번만"""
    prev = None
    for e in evs:
        if "sfx" in e:
            continue
        if e["type"] == "say":
            emo = e.get("emo", "")
            cue = EMO.get(emo)
            if not cue and re.search(r"[?？][!！]|[!！][?？]", e.get("text", "")):
                cue = "emo_shout"
            key = (e.get("speaker"), emo)
            if cue and key != prev:
                e["sfx"] = cue
            prev = key
        elif e["type"] == "stage":
            for pat, cue in STAGE:
                if re.search(pat, e.get("text", "")):
                    e["sfx"] = cue
                    break
        elif e["type"] == "bg" and e.get("bg", "").startswith("ui:broadcast"):
            e["sfx"] = ["sfx_ding", "sfx_tv"]


def score(flow):
    ch = flow["chapter"]
    first_interlude = True
    for b in flow["beats"]:
        for x in b.get("spots", []) + b.get("pool", []):  # 수사 현장·자유행동 이벤트 : 효과음만(곡은 수사 곡·자유행동 곡 유지)
            lines(x["events"])
        if b["t"] not in ("scene", "execution"):
            continue
        bgm = scene_bgm(ch, b, first_interlude and b["id"].startswith("17:"))
        if b["id"].startswith("17:"):
            first_interlude = False
        b["bgm"] = bgm
        evs = b["events"]
        lines(evs)
        found = body(evs, ch) if b["t"] == "scene" else False
        base = bgm.split(">")[-1]
        if not found and base in RAPPY_SWITCH | {"bgm_morning", "bgm_rappy_after"}:
            after = "bgm_motive" if "-M-01" in b["id"] else base
            if base in ("bgm_morning", "bgm_rappy_after"):
                after = DAILY[ch] if base == "bgm_morning" else "bgm_night"
                # 방송 장면은 래피 곡이 장면 곡 : 래피가 빠지면 일상 곡으로만
                idx = [i for i, e in enumerate(evs) if e["type"] == "say" and e.get("speaker") == "래피"]
                if idx:
                    nxt = next((i for i in range(idx[-1] + 1, len(evs)) if evs[i]["type"] in ("say", "stage", "ui")), None)
                    if nxt is not None:
                        evs[nxt]["music"] = after
            else:
                rappy(evs, base, after)
    # 스포일러 없는 집계 : 장면 곡 분포
    return {c: sum(1 for b in flow["beats"] if b.get("bgm", "").split(">")[-1] == c) for c in sorted({b.get("bgm", "").split(">")[-1] for b in flow["beats"] if b.get("bgm")})}
