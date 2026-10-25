# 소리 가져오기 : 사용자가 준 V3 OST(Downloads/dtd)·효과음(Downloads/Danganropa Sound Effects) → audio/bgm·audio/sfx + audio/cues.json
# 음원은 저장소에 올리지 않는다(.gitignore). 이 스크립트와 표만 올린다.
#
# BGM 루프 : 엔진(HTMLAudio)은 파일 전체만 반복한다. 그래서 곡마다 「들어가는 부분(<큐>_intro)」과 「반복 부분(<큐>)」 두 파일로 자른다.
#   게임은 _intro 를 한 번 틀고 끝나기 직전에 반복 부분으로 넘긴다(Source/Flow.hpp playCue).
#   루프 길이 = dtd/loop-research/matched_results.json(팬 BRSTM 수치)의 끝-시작. 그 수치는 MP3 와 시각이 어긋날 수 있어
#   파형 상관으로 길이를 ±80ms 안에서 다시 맞추고, 상관이 낮으면 곡 자체에서 반복 구간을 찾는다(그것도 안 되면 통째로 반복).
# 한 번만 나는 곡(징글) : jingle_* — 끝나면 다음 곡으로(길이는 cues.json len).
#
# python tools/import_audio.py [음원 폴더] [효과음 폴더]
import json, pathlib, subprocess, sys, shutil
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
DTD = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path.home() / "Downloads" / "dtd")
SE = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else pathlib.Path.home() / "Downloads" / "Danganropa Sound Effects")

# 큐 → (원곡 파일 앞부분, 쓰는 곳). V3 에서 그 곡이 나오는 자리에 맞춰 고른 것(docs/spec/16 §5).
# 단간론파답지 않은 곡(클래식 「Clair de Lune」, 성가풍 「Spirit, Praise, and Beauty」, 삽입곡 「Caged Child」, 「Pretitle」)은 쓰지 않는다(사용자 지시).
BGM = {
 "bgm_title": ("1-01. DANGANRONPA V3.mp3", "타이틀"),
 "bgm_pretitle": ("2-01. Danganronpa V3 (Loop Version)", "오프닝 타이틀 장면(00-1)"),
 "bgm_pro_arrival": ("1-11. Nightmare in the Locker", "프롤로그 : 눈뜨기·정문"),
 "bgm_pro_intro": ("1-03. Rise of the Ultimates", "프롤로그 : 자기소개"),
 "bgm_killing_game": ("2-18. Let's Start the Killing Game", "프롤로그 : 래피 등장·규칙 선언"),
 "bgm_rappy_theme": ("2-10. Mr. Monokuma's Lesson V3", "래피가 나와 떠드는 동안"),
 "bgm_rappy_after": ("2-15. Mr. Monokuma After Class V3", "밤 방송"),
 "bgm_morning": ("1-07. Rise and Shine, Ursine!", "아침 방송(모니터)"),
 "bgm_morning_calm": ("1-18. Cool Morning", "아침 모임"),
 "bgm_daily_pro": ("1-04. Beautiful Lie (Ver.B)", "프롤로그 일상·탐색"),
 "bgm_daily_pastel": ("1-12. Beautiful Lie.mp3", "1장 일상"),
 "bgm_daily_summer": ("1-16. Living in a Lazy Parallel World.mp3", "2장 일상"),
 "bgm_daily_night": ("3-05. Beautiful Lie in the Virtual World", "3장 일상"),
 "bgm_daily_grey": ("2-13. Heartless Journey", "4장 일상"),
 "bgm_daily_mono": ("1-12. Beautiful Lie.mp3", "5장 일상(V3 도 일상은 대부분 Beautiful Lie)"),
 "bgm_core": ("2-14. Real - Fiction", "6장"),
 "bgm_freetime": ("1-10. Become Friends", "자유행동"),
 "bgm_comedy": ("2-03. Finding Peace Party", "막간 식사·서비스 장면"),
 "bgm_night": ("2-04. Hope of Autumn", "저녁·밤·혼자 있는 장면"),
 "bgm_tense": ("1-21. Darkness Time", "사건 직전·시체 발견 뒤"),
 "bgm_sad": ("2-12. Moon on the Water", "유품·소멸"),
 "bgm_warm": ("2-17. Wonderful Story", "마지막 대화·약속"),
 "bgm_motive": ("1-23. Heaven of Almost Hell", "동기 발표 뒤"),
 "bgm_investigation": ("1-17. Despair Searching.mp3", "수사"),
 "bgm_investigation_final": ("2-08. Hope Searching", "6장 수사"),
 "bgm_trial_prep": ("3-04. Trial Preparation", "수사 종료 → 재판 준비"),
 "bgm_elevator": ("1-07. Our Class Trial", "재판장 엘리베이터"),
 "bgm_trial_main_1": ("1-13. Class Trial - Sun Edition V3.mp3", "1장 재판"),
 "bgm_trial_main_2": ("1-09. Class Trial - Space Edition", "2장 재판"),
 "bgm_trial_main_3": ("1-08. Class Trial - Dawn Edition", "3장 재판"),
 "bgm_trial_main_4": ("1-10. Class Trial - Resurrection Edition.mp3", "4장 재판"),
 "bgm_trial_main_5": ("1-19. Class Trial - Sun Edition V3 (Ver.B)", "5장 재판"),
 "bgm_trial_main_6": ("2-09. Class Trial - Resurrection Edition (No Intro)", "6장 재판"),
 "bgm_trial_nonstop": ("1-11. V3 Argument -Break-", "논스톱 의논(재판 앞쪽)"),
 "bgm_trial_nonstop_b": ("1-14. V3 Argument -Turn Up the Heat-", "논스톱 의논(재판 뒤쪽)"),
 "bgm_trial_nonstop_lie": ("1-20. V3 Argument -Perjury-", "논스톱 의논(4·5장 뒤쪽)"),
 "bgm_trial_nonstop_final": ("1-16. V3 Argument -Hope vs Despair-", "6장 의논"),
 "bgm_trial_panic": ("1-15. V3 Argument -Panic-", "패닉 의논"),
 "bgm_trial_scrum": ("1-12. Debate Scrum", "의논 스크럼"),
 "bgm_trial_showdown": ("1-18. V3 Argument -Blade Lock-", "반론 쇼다운"),
 "bgm_trial_armament_1": ("2-14. Hyper Ultra New a.A.", "1장 이론 무장"),
 "bgm_trial_armament_2": ("1-14. New a.A.", "2장 이론 무장"),
 "bgm_trial_armament_3": ("2-19. Hyper New a.A.", "3장 이론 무장"),
 "bgm_trial_armament_4": ("1-21. Final a.A.", "4장 이론 무장"),
 "bgm_trial_armament_5": ("2-10. Hyper Final a.A.", "5장 이론 무장"),
 "bgm_trial_armament_6": ("2-17. Hyper Final Ultra a.A.", "6장 이론 무장"),
 "bgm_trial_mindmine": ("2-05. Mind Mine", "발굴 이매지네이션"),
 "bgm_trial_taxi": ("1-20. Psyche Taxi", "브레인 드라이브"),
 "bgm_trial_anagram": ("1-17. Hangman's Gambit", "섬광 애너그램"),
 "bgm_trial_climax": ("2-22. Closing Argument V3", "클라이맥스 추리"),
 "bgm_trial_truth": ("2-15. Sing the Empty Truth", "투표 뒤 진상"),
 "bgm_trial_end": ("3-16. Trial END", "재판 결과"),
 "bgm_punishment_time": ("2-18. Destruction Of", "처형"),
 "bgm_epilogue_1": ("1-26. Hope of Spring", "1장 재판 뒤"),
 "bgm_epilogue_2": ("2-09. Hope of Summer", "2장 재판 뒤"),
 "bgm_epilogue_3": ("2-04. Hope of Autumn", "3장 재판 뒤"),
 "bgm_epilogue_4": ("2-05. Hope of Winter", "4장 재판 뒤"),
 "bgm_epilogue_5": ("2-12. Moon on the Water", "5장 재판 뒤"),
 "bgm_ending_choice": ("1-22. New World Order V3", "마지막 선택"),
 "bgm_ending_a": ("2-12. New Space Journey", "엔딩·크레딧"),
 "bgm_ending_b": ("2-21. Immersive Picture Scrolls", "엔딩 B"),
}
JINGLE = {
 "jingle_chapter": ("1-08. Chapter A", "장 시작 표지"),
 "jingle_chapter_p": ("1-25. Chapter C", "프롤로그 표지"),
 "jingle_chapter_end": ("1-03. Chapter B", "장 끝(막간 들어갈 때)"),
 "jingle_body_1": ("1-13. Dead Body Found A", "1장 시체 발견"),
 "jingle_body_2": ("2-20. Dead Body Found B", "2장 시체 발견"),
 "jingle_body_3": ("2-13. Dead Body Found C", "3장 시체 발견"),
 "jingle_body_4": ("1-05. Dead Body Found D", "4장 시체 발견"),
 "jingle_body_5": ("2-07. Dead Body Found E", "5장 시체 발견"),
 "jingle_rappy": ("1-09. Mr. Monokuma Appearance", "래피 등장"),
 "jingle_vote": ("3-03. Vote Slot", "투표 슬롯"),
 "jingle_flashback": ("3-02. Flashback Light", "회상"),
}
# 효과음 큐 → HS_SE 번호 (Danganropa Sound Effects/효과음_133개_사용처_대조표.txt)
SFX = {
 "ui_select": (5, "커서 이동"), "ui_confirm": (1, "결정"), "ui_cancel": (4, "취소·돌아가기"), "ui_locked": (0, "고를 수 없음"),
 "ui_pad": (15, "패드 열기"), "ui_pad_close": (16, "패드 닫기"), "ui_page": (7, "패드 쪽 넘김"), "ui_page_b": (236, "지도·층 넘김"),
 "sfx_ding": (156, "방송 차임"), "sfx_body_chime": (157, "시체 발견 방송 차임"), "sfx_tv": (164, "모니터 켜짐"), "sfx_tv_off": (165, "모니터 꺼짐"), "sfx_tv_noise": (257, "방송 잡음"),
 "sfx_door": (145, "방 문"), "sfx_door_slam": (146, "문 세게 닫기"), "sfx_door_creak": (233, "문 삐걱"), "sfx_knock": (150, "노크"), "sfx_bang_door": (151, "문 두드리기"), "sfx_locked": (153, "잠긴 문"),
 "sfx_footstep": (141, "걷는 발소리"), "sfx_run": (142, "달리는 발소리"), "sfx_room_move": (140, "장소 이동"),
 "sfx_hover_person": (18, "인물 위 커서"), "sfx_talk_in": (19, "말 걸기"), "sfx_talk_out": (20, "대화 끝"), "sfx_hotspot": (126, "조사 대상 표시"), "sfx_inspect": (116, "조사"),
 "sfx_card": (21, "언령·교칙 획득"), "sfx_note": (7, "노트에 적기"),
 "sfx_coin": (102, "코인"), "sfx_capsule": (103, "캡슐 레버"), "sfx_capsule_open": (105, "캡슐 열림"),
 "sfx_bond_up": (122, "인연 상승"), "sfx_wrong": (123, "오답·싫어하는 선물"), "sfx_correct": (2, "정답·제출"), "sfx_band": (23, "자유행동·수사 개시 띠"),
 "sfx_rappy": (133, "래피 등장·퇴장"), "sfx_shock": (31, "충격(시체 발견·결정적 발언)"), "sfx_flashback": (30, "회상 전환"),
 "emo_angry": (25, "호통"), "emo_basic": (26, "강조"), "emo_surprise": (27, "놀람·깨달음"), "emo_excited": (28, "주장·흥분"), "emo_shout": (29, "깜짝 외침"), "emo_gloomy": (37, "침울·난감"),
 "sfx_fall": (216, "쓰러짐"), "sfx_glass": (217, "유리 깨짐"), "sfx_punch": (210, "주먹"), "sfx_slap": (224, "뺨"), "sfx_explode": (214, "폭발"), "sfx_gunshot": (35, "총성"),
 "sfx_machine": (166, "기계 조작"), "sfx_elevator": (161, "엘리베이터 작동"), "sfx_elevator_stop": (162, "엘리베이터 정지"), "sfx_elevator_door": (163, "엘리베이터 문"), "sfx_typing": (208, "타이핑"),
 "sfx_break": (32, "논파"), "sfx_timeup": (160, "제한 시간 끝"), "sfx_heart_slow": (33, "느린 심장"), "sfx_heart_fast": (34, "빠른 심장"), "sfx_slash": (229, "베기"), "sfx_climax_flip": (6, "클라이맥스 칸 넘김"), "sfx_flash": (202, "흰 섬광"),
 "sfx_chapter_end": (251, "장 끝"), "sfx_prologue": (244, "프롤로그 시작"),
}
SR = 44100

def ffmpeg(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)

def decode(f, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)

def corr(x, a, b, w):
    if a < 0 or b < 0 or a + w > len(x) or b + w > len(x): return -1
    p, q = x[a:a + w], x[b:b + w]
    d = np.linalg.norm(p) * np.linalg.norm(q)
    return float(p @ q / d) if d else -1

def refine(x, s, L, sr):
    """s 에서 시작해 L 뒤에 같은 소리가 반복되는지. L 을 ±80ms 안에서 다시 맞춘다 → (s, L, 상관)"""
    w = int(sr * 2)
    best = (-1, L)
    for dl in range(-int(.08 * sr), int(.08 * sr) + 1, 4):
        c = corr(x, s, s + L + dl, w)
        if c > best[0]: best = (c, L + dl)
    c0, L0 = best
    fine = max(((corr(x, s, s + L0 + dl, w), L0 + dl) for dl in range(-6, 7)))  # 표본 단위
    return s, fine[1], fine[0]

def self_loop(x, sr):
    """루프 자료가 없을 때 : 곡 뒤쪽 한 토막이 앞쪽 어디와 같은지 FFT 상관으로 찾는다(OST 는 보통 두 번 돌고 페이드)"""
    small = x[::8].astype(np.float64); ssr = sr // 8; w = int(ssr * 3)
    p = int(len(small) * .55); lo, hi = int(ssr * 3), p - int(ssr * 15)
    if hi <= lo or p + w > len(small): return None
    seg, area = small[p:p + w], small[:hi + w]
    n = 1 << int(np.ceil(np.log2(len(area) + w)))
    xc = np.fft.irfft(np.fft.rfft(area, n) * np.conj(np.fft.rfft(seg, n)), n)[:hi]
    e = np.concatenate([[0], np.cumsum(area ** 2)]); norms = np.sqrt(e[w:hi + w] - e[:hi]) * np.linalg.norm(seg)
    c = np.where(norms > 0, xc / np.maximum(norms, 1e-9), -1); c[:lo] = -1
    q = int(np.argmax(c))
    if c[q] < .9: return None
    return refine(x, q * 8, (p - q) * 8, sr)

def music_loop(x, sr):
    """같은 소리가 반복되지 않는 앨범판 : 스펙트럼(4초 창)이 가장 닮은 두 지점 q<p 를 고른다(p-q ≥ 40초, p 는 끝 페이드 앞)
    → 그 사이를 반복하고 이음매는 30ms 섞는다. 음악적으로 같은 마디로 돌아가는 것이지 원작 루프와 같은 지점은 아니다."""
    hop, nfft = 1024, 4096
    win = np.hanning(nfft)
    frames = np.lib.stride_tricks.sliding_window_view(x, nfft)[::hop] * win
    mag = np.abs(np.fft.rfft(frames, axis=1))[:, 4:1024]
    bands = np.log1p(np.add.reduceat(mag, np.unique(np.geomspace(1, mag.shape[1] - 1, 56).astype(int)), axis=1))
    rms = np.sqrt((frames ** 2).mean(1)); loud = rms > .35 * np.median(rms)
    end = len(rms) - 1
    while end > 0 and not loud[end]: end -= 1  # 끝 페이드·무음 제외
    k = int(4 * sr / hop); fps = sr / hop
    f = bands - bands.mean(1, keepdims=True); f /= np.linalg.norm(f, axis=1, keepdims=True) + 1e-9
    best = (-1, 0, 0)
    for p in range(int(end * .6), end - k, 4):
        lo, hi = int(2 * fps), p - int(40 * fps)
        if hi <= lo: continue
        sim = np.zeros(hi - lo)
        for j in range(0, k, 8): sim += f[lo + j:hi + j] @ f[p + j]
        q = int(np.argmax(sim)) + lo
        if sim[q - lo] > best[0]: best = (sim[q - lo], q, p)
    score, q, p = best[0] / len(range(0, k, 8)), best[1] * hop, best[2] * hop
    # 이음매 : ±25ms 안에서 파형이 가장 맞는 자리
    w, r = int(.05 * sr), int(.025 * sr)
    dq = max(range(-r, r + 1, 2), key=lambda d: corr(x, q + d, p, w))
    return q + dq, p - (q + dq), score

def loop_points(name, x, sr, research):
    r = research.get(name, {})
    src = r.get("source") or {}
    if r.get("status") == "루프 수치 공개" and src.get("end_seconds") and "Loops Normally" in (src.get("loop_type") or ""):
        s0 = int((src.get("start_seconds") or 0) * sr); L0 = int(src["end_seconds"] * sr) - s0
        for s in (max(s0, int(.5 * sr)) + int(sr * k) for k in (0, 1, 3, 6)):  # MP3 가 BRSTM 보다 늦게 시작하면 조금 뒤에서 맞는다
            if s + L0 + 2 * sr < len(x):
                s, L, c = refine(x, s, L0, sr)
                if c > .9: return s, L, c, "자료"
    found = self_loop(x, sr)
    if found and found[2] > .9: return found[0], found[1], found[2], "파형"
    q, L, score = music_loop(x, sr)
    return (q, L, score, "곡조") if score >= .9 else None  # 덜 닮은 이음매는 튀어서 이상하게 들린다 → 통째로 반복

def decode_stereo(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)

def encode(pcm, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "libvorbis", "-q:a", "4", str(out)], input=np.ascontiguousarray(pcm, np.float32).tobytes(), check=True)

def write_loop(st, s, L, out_body, out_intro):
    """반복 부분 st[s:s+L] : 끝 30ms 를 st[s-N:s] 와 섞어 끝→처음이 이어지게"""
    N = int(.03 * SR); body = st[s:s + L].copy()
    if s >= N:
        t = np.linspace(0, 1, N, dtype=np.float32)[:, None]
        body[-N:] = body[-N:] * (1 - t) + st[s - N:s] * t
    encode(body, out_body); encode(st[:s], out_intro)

def find(prefix):
    for f in sorted(DTD.glob("*.mp3")):
        if f.name.startswith(prefix): return f
    raise SystemExit("곡 없음: " + prefix)

def main():
    research = {e["file"]: e for e in json.load(open(DTD / "loop-research" / "matched_results.json", encoding="utf-8"))}
    bgm_dir, sfx_dir = ROOT / "audio" / "bgm", ROOT / "audio" / "sfx"
    for d in (bgm_dir, sfx_dir): shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    cues = {"_doc": "tools/import_audio.py 가 만든다. bgm = 반복(들어가는 부분은 <큐>_intro), jingle = 한 번(len 초 뒤 다음 곡), sfx = 효과음. src = 원본 파일.", "bgm": {}, "jingle": {}, "sfx": {}}
    report = []
    for cue, (prefix, use) in BGM.items():
        f = find(prefix); st = decode_stereo(f); x = st.mean(1)
        lp = loop_points(f.name, x, SR, research)
        if lp:
            s, L, c, how = lp
            write_loop(st, s, L, bgm_dir / f"{cue}.ogg", bgm_dir / f"{cue}_intro.ogg")
            cues["bgm"][cue] = {"use": use, "src": f.name, "file": f"bgm/{cue}.ogg", "intro": f"bgm/{cue}_intro.ogg", "introLen": round(s / SR, 3), "loop": [round(s / SR, 3), round((s + L) / SR, 3)]}
            report.append(f"{cue}: {how} 루프 {s / SR:.2f}~{(s + L) / SR:.2f}s 상관 {c:.3f}")
        else:
            ffmpeg("-i", str(f), "-c:a", "libvorbis", "-q:a", "4", str(bgm_dir / f"{cue}.ogg"))
            cues["bgm"][cue] = {"use": use, "src": f.name, "file": f"bgm/{cue}.ogg"}
            report.append(f"{cue}: 루프 못 찾음 → 통째로 반복")
    for cue, (prefix, use) in JINGLE.items():
        f = find(prefix)
        ffmpeg("-i", str(f), "-c:a", "libvorbis", "-q:a", "4", str(bgm_dir / f"{cue}.ogg"))
        cues["jingle"][cue] = {"use": use, "src": f.name, "file": f"bgm/{cue}.ogg", "len": round(len(decode(f, 8000)) / 8000, 2)}
    for cue, (no, use) in SFX.items():
        f = next(SE.rglob(f"HS_SE_{no:03d}*.wav"))
        ffmpeg("-i", str(f), "-c:a", "libvorbis", "-q:a", "5", str(sfx_dir / f"{cue}.ogg"))
        cues["sfx"][cue] = {"use": use, "src": f.name, "file": f"sfx/{cue}.ogg"}
    (ROOT / "audio" / "cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "audio" / "LOOPS.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))

if __name__ == "__main__":
    main()
