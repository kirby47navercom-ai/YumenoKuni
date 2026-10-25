# AGENTS.md

작업을 시작하기 전에 **`HANDOFF.md` 를 처음부터 끝까지 읽는다.** 사용자 규칙(§0), 엔진 제약(§2), 빌드·검증 명령(§4·§5), 남은 일(§6)이 모두 거기 있다.

핵심만 :
- 사용자 호칭 「주인님」, 존댓말, 한국어. 대화창에 스포일러 금지.
- 토큰·키를 파일에 쓰지 않는다(`NAI_TOKEN` 환경변수). Git LFS 금지.
- 『단간론파 V3』를 게임 전체에서 따라 하되 원작 파일은 추출하지 않는다.
- 혈액은 보라색, 미성년 성적 표현 금지.
- `Game/Assets` 는 생성물 — 원본(`data/`, `tools/`, `Game/tools/create-project.mjs`, `ui/`, `art/`, `bg/`)을 고친다.
- 고친 뒤 `cd Game && node tools/create-project.mjs && node tools/build.mjs` 로 빌드, `node tools/verify-flow.mjs` 로 검증.
