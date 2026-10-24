# 유메노쿠니 (夢の国)

단간론파식 추리 데스게임 오리지널 시나리오 / 게임 프로젝트.

- `docs/` 설정집(스포일러 주의), 공원·캐릭터·진행 설계서
- `tools/generate_tpose_nai.py` NovelAI T자 일러스트 생성
- `art/standing/` 기준 입상 일러스트 17장(16명 + 래피)
- `docs/design/` 게임 기획서(시스템 + 프롤로그~6장 시나리오, ⚠ 전체 스포일러)
- `HANDOFF.md` 인수인계서

## T자 일러스트 생성
```
pip install requests
$env:NAI_TOKEN = "pst-..."   # 토큰은 절대 커밋 금지
python tools/generate_tpose_nai.py --only mio rei --out art/tpose
```

> 설정집에 전체 스포일러 포함. 저장소는 private 권장.

## docs/design 목차
| 파일 | 내용 |
|---|---|
| 00_시스템_기획서.md | 1인칭 탐색, 코인·캡슐, 인연·스킬, 재판 미니게임, 시간표 |
| 01_캐릭터_스토리_자유시간.md | 16명 + 래피 스토리, 선물 취향, 이벤트 ①②③ |
| 10_프롤로그.md ~ 16_6장_드림코어.md | 장면별 대사·증거·증언·재판 스크립트 |
| 99_v2_보정사항.md | 설정집 v2와 달라진 점 |
