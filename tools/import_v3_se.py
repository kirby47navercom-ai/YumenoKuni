# V3 원작 효과음(주인님 허락 2026-11-02) : Downloads/v3_se/<묶음>/V3_SE_NNN.ogg → audio/v3se/ + audio/cues.json sfx 「v3se_NNN」
# Downloads/v3_se 는 v3_re/resources/*_resident/*.acb 를 큐 이름별로 푼 것(HCA → ogg).
# 용도는 V3 실행 파일이 그 번호를 부르는 자리(docs/spec/18_V3_분석, v3_re/native 함수)로 정했다. 표는 USE.
# 원본 소리라 audio/**/*.ogg 규칙으로 저장소에 올리지 않는다. 다시 만들 때 이 스크립트를 돌린다(import_audio.py·v4_presentation.py --register-cues 뒤에).
import json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads/v3_se"
BANKS = ["trial_resident", "minigame_resident", "game_resident"]  # 앞쪽이 먼저(같은 번호가 여러 묶음에 있을 때)

# 번호 : 쓰는 자리 (근거 함수 / 연출 라벨)
USE = {
    "000": "고를 수 없음", "001": "결정", "003": "대사 넘김", "004": "취소", "005": "커서 이동",
    "007": "클라이맥스 쪽 넘김", "010": "후보 목록 펼침", "011": "후보 목록 접기", "015": "패드 열기", "016": "패드 top 닫기 (4208b0)",
    "050": "탐색 조준 대상 바뀜 (8tick 간격)", "051": "말 걸기·조사 시작 (40a6a0)", "052": "말 걸기 끝·복귀 (40a6a0)",
    "021": "이론 무장 조각 등장", "032": "이론 무장 마지막 조각 완성",
    "302": "언령·칼 바꾸기 (3f0500·3f69c0)", "305": "발사·인물 결정 (3f0500 case10·3c44c0)",
    "307": "발언에 맞음(약점 아님) (3efcf0)", "308": "위증 탄환 약점 명중 (3f0500)",
    "309": "논파 약점 명중 + Ronpa (3f0500)", "310": "동의 명중·정답 (3f0500·38d970)",
    "311": "틀린 명중·오답 (3f0500·38d970)", "315": "반론 헛베기 Hanron_Miss (3f6510)",
    "316": "피해 (공통 Damage)", "317": "반론 피해 (3f6510)", "318": "반론 칼 맞물림 시작 (3f7e10)",
    "327": "깨짐 (정답 컷인 뒤 파괴 단계)", "330": "논파 정답 컷인", "331": "동의 정답 컷인",
    "332": "시간 끝", "339": "소음 맞음(안 깨짐) (3efcf0)", "341": "집중 시작", "342": "집중 반복",
    "343": "패닉 발언 끼어듦 (48b350)", "345": "패닉 큰소리 깨기 Panic_OgoeBreak (3efcf0)",
    "346": "위증 정답 컷인", "347": "스크럼 전원 논파 Sc_AllRonpa (3fa430)", "348": "패닉 깨짐",
    "349": "위증 정답 마무리", "351": "사일런서 반복 (3efcf0)",
    "356": "스크럼 시작 4", "359": "스크럼 시작 5", "360": "스크럼 짝 결정·마지막 통과",
    "361": "스크럼 정답", "362": "스크럼 오답", "363": "스크럼 시작 1", "364": "스크럼 시작 2·단계 통과",
    "365": "스크럼 시작 3", "366": "스크럼 마지막 단계 시작",
    "367": "투표 커서", "368": "투표 결정", "369_d": "투표 결과",
    "374": "반론 시작 (3f69c0 case9)", "375": "반론 베기 명중 Hanron_Hit (3f6000)",
    "376": "반론 마무리 Hanron_Finish (3f69c0)", "377": "반론 발언 넘어감 (3f69c0)", "378": "반론 칼 맞물림 반복 Hanron_Tsuba (3f7e10)",
    "384": "애너그램 글자 날아감", "394": "발굴 잘 지움", "395": "발굴 실패", "400": "발굴 정답",
    "402": "이론 무장 누르기", "403": "이론 무장 명중", "404": "이론 무장 놓침",
    "064": "걷기 발소리 (40b000 index0)", "064_1": "걷기 발소리 변형", "064_2": "걷기 발소리 변형",
    "442": "이론 무장 마지막 크리티컬", "443": "이론 무장 마지막 명중", "447": "클라이맥스 시작", "448": "클라이맥스 완성",
}

# 1편 효과음으로 만든 공통 큐(import_audio.py)를 V3 번호로 바꾼다 — UI 는 V3 공통(09_시스템 : 커서 005·결정 001·취소 004·불가 000, 패드 420b40 : 015)
OVERRIDE = {"ui_select": "005", "ui_confirm": "001", "ui_cancel": "004", "ui_locked": "000", "ui_pad": "015", "ui_pad_close": "016",
            "sfx_talk_in": "051", "sfx_inspect": "051", "sfx_hotspot": "050", "sfx_hover_person": "050", "sfx_talk_out": "052"}  # 말 걸기 : interaction_presentation 40a6a0

def length(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return round(float(out), 3) if out else None

def main():
    cues_path = ROOT / "audio/cues.json"
    cues = json.loads(cues_path.read_text(encoding="utf-8"))
    dst = ROOT / "audio/v3se"; dst.mkdir(parents=True, exist_ok=True)
    missing = []
    for num, use in USE.items():
        src = next((SRC / b / f"V3_SE_{num}.ogg" for b in BANKS if (SRC / b / f"V3_SE_{num}.ogg").is_file()), None)
        if not src:
            missing.append(num); continue
        to = dst / src.name
        if not to.is_file() or to.stat().st_size != src.stat().st_size:
            shutil.copyfile(src, to)
        cues["sfx"]["v3se_" + num] = {"src": f"V3 {src.parent.name}/{src.name}", "file": f"v3se/{src.name}",
                                      "use": use, "len": length(to)}
    for cue, num in OVERRIDE.items():
        v = cues["sfx"].get("v3se_" + num)
        if v: cues["sfx"][cue] = {**cues["sfx"].get(cue, {}), "src": v["src"], "file": v["file"], "len": v["len"]}
    cues_path.write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(len(USE) - len(missing), "cues", "missing:", missing)
    if missing:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
