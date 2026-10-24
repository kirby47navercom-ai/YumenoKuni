# 유메노쿠니 (夢の国)

단간론파식 추리 데스게임 오리지널 시나리오 / 게임 프로젝트.

- `docs/` 설정집(스포일러 주의), 공원·캐릭터·진행 설계서
- `tools/generate_tpose_nai.py` NovelAI T자 일러스트 생성
- `art/tpose/` 생성된 T자 기준 일러스트
- `HANDOFF.md` 인수인계서

## T자 일러스트 생성
```
pip install requests
$env:NAI_TOKEN = "pst-..."   # 토큰은 절대 커밋 금지
python tools/generate_tpose_nai.py --only mio rei --out art/tpose
```

> 설정집에 전체 스포일러 포함. 저장소는 private 권장.
