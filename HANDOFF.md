# 유메노쿠니 — 인수인계서 (Codex · Claude 공용, 2026-10-25 기준)

> 이 문서만 읽고 바로 이어서 작업할 수 있게 쓴 것이다. **처음부터 끝까지 읽고 시작할 것.**
> 스포일러가 들어 있다(범인·사인). 사용자에게 대화창으로 요약·인용하지 않는다(§0).

---

## 0. 사용자 규칙 (어기면 안 됨)

| 항목 | 규칙 |
|---|---|
| 호칭·말투 | 사용자는 **주인님**. 항상 **존댓말**. 한국어. 짧고 바로 쓸 수 있는 결과 위주. |
| 스포일러 | 사용자는 범인·트릭·결말 스포를 원하지 않는다. 대화창에는 스포 없는 내용만. 스포는 파일에만. |
| 비밀값 | 토큰·API 키를 코드·문서·커밋·로그에 **절대 쓰지 않는다**. NovelAI 토큰은 환경변수 `NAI_TOKEN`으로만 읽는다(사용자가 채팅에 붙여 준 적이 있으나 저장 금지). |
| Git | **Git LFS 금지**(사용자가 다른 데 아껴 씀). 큰 PNG는 `.gitignore`, 저장소에는 WebP(`tools/pack_webp.py`). 원격 : `github.com/kirby47navercom-ai/YumenoKuni`(비공개). 커밋 메시지는 한국어. |
| 엔진 설치본 | `C:/Users/kirby/HBEngine/Versions` 와 `%LOCALAPPDATA%/HBEngine/User` 는 **수정 금지**. 엔진 원본 `../engineCreate` 는 읽기만. |
| 원작 | 『단간론파 V3』를 **게임 전체(재판만이 아니라 일상·수사·자유행동·패드·연출·소리 배치·UI 글씨 위치/간격까지)** 거의 그대로 따라 한다(약 90%). 원작 그림·폰트·소리 **파일을 추출해 쓰지 않는다**(배치·움직임·타이밍만 따라 함). 사용자가 원작 게임/스크린샷을 주면 **참고 화면으로만** 쓴다. |
| 지어내기 금지 | 원작에 없는 장치(빈칸 채우기 같은 꼼수, 빈 곳에 갑자기 안내 글씨 넣기)를 만들지 않는다. 모르면 V3 화면을 먼저 조사한다(`docs/spec/15`, `16`). |
| 캐릭터 | 재판 중 인물은 자리에 **항상 서 있다**(사라졌다 뿅 나타나면 안 됨). 증언대(책상)와 인물 그림은 **별개**(스프라이트에 책상 금지). |
| 그림 수위 | 혈액은 **보라색**. 사망 CG는 **분명히 죽은 모습** + **사인에 맞는 상처 부위가 보이게**(조사 단서). 고어(장기·절단) 금지. 등장인물은 미성년 포함 → **성적 표현·노출 금지**, 체형 차이는 키·골격·실루엣으로만. |
| 그림 도구 | 배경·사망 CG는 **NovelAI V5**(`nai-diffusion-5-full`), 사망 CG는 **배경 판과 인물을 따로 뽑아 합성**. 포즈 변형·UI·아이콘 등 대량 작업은 Codex. |
| 톤 | 어두운 이야기지만 해피엔딩 지향. 인물마다 말투가 뚜렷(01 문서). 서비스씬·막간은 길고 느긋하게. |
| 배포 | 엔진 패키징(release 빌드) 결과를 그대로 준다. **cmd 실행기·추가 안내 파일을 만들지 않는다**(`Game/tools/package.mjs`). |

---

## 1. 폴더 지도

```
YumenoKuni/
├─ AGENTS.md            Codex 자동 지침(이 문서를 먼저 읽으라는 안내)
├─ HANDOFF.md           ← 이 문서
├─ docs/design/         시나리오·재판 대본 (⚠ 스포)
│   10_프롤로그 · 1Na_일상·프리타임 · 1Nb_수사·재판(옛 형식) · 1Nc_재판_V3(현재 재판 대본) · 16a/16b(6장) · 17_막간
│   01_캐릭터_스토리_자유시간(말투·취향·이벤트) · 00_시스템_기획서(코인·선물·인연·스킬·노트)
├─ docs/spec/           제작 사양 00~16. 특히
│   04 재판 미니게임 · 05 연출(장별 채도, 처형 스토리보드) · 06 에셋 목록 · 09 장 플로우
│   11 래피패드 교칙 · 12 포즈/CG 목록 · 14 코덱스 에셋 작업지시서 · 15 V3 재판 레퍼런스 · 16 V3 일상·수사 레퍼런스
├─ data/                빌드 산출 데이터(도구가 만든다 — 손으로 고치지 말 것)
│   scenes/*.json(대본 이벤트) · flow/{P,1..6}.json(장 진행표) · trials/1Nc.json(재판 단계)
│   evidence.json(언령 원본) · kotodama.json(언령 이름·설명) · gifts.json(선물·취향) · reactions.json(선물 반응 대사, 손으로 쓴 것)
├─ tools/               파이썬 도구 (§4)
├─ art/                 standing(NAI 입상 원본) · standing_hd(4배) · sprites/{slug}/(포즈 WebP) · cutin · cg(사망·처형·이벤트) · trial3d(재판장 소품)
│   _candidates/ (NAI 후보 원본, git 제외) · _work/ (Codex 작업 기록, git 제외) · MANIFEST.md(에셋 진행표) · PROVENANCE.json · QA.json
├─ bg/                  배경 1920×1080 (PNG 로컬, WebP 저장소)
├─ ui/                  UI 원본 PNG (kotodama 카드 그림·틀, gift 선물 아이콘, pad 얼굴·캡슐·코인, common 타이틀·장 카드, dialog, trial HUD)
├─ fonts/               OFL 글꼴 18종 (+ LICENSE)
├─ audio/cues.json      BGM·효과음 큐 이름 → 파일(비어 있으면 무음). 파일은 git 제외
└─ Game/                HBEngine 프로젝트
    ├─ YumenoKuni.hbproject
    ├─ Source/          C++ 게임 코드 (§3)
    ├─ Assets/          create-project.mjs 가 **매번 새로 만든다**(손으로 고치지 말 것)
    ├─ tools/           create-project.mjs(에셋·위젯·장면 생성) · build.mjs · package.mjs · verify-flow.mjs · verify-trial-full.mjs
    ├─ Builds/          빌드 출력(git 제외, 커지면 지워도 됨 — 최신 하나는 build-result.json 이 가리킴)
    └─ Saved/           검증 기록(git 제외, 지워도 됨)
```
`dist/`(git 제외) : 배포본. `dist/YumenoKuni/HBGame_<ID>.exe` 실행, `dist/YumenoKuni-날짜.zip`.

---

## 2. 엔진 (HBEngine) — 꼭 알아야 할 제약

* 엔진 원본 : `C:/Users/kirby/OneDrive/바탕 화면/git/engineCreate` (C++ 네이티브 모듈 + WebView2 UI/3D). 문서 `engineCreate/docs/AI_ENGINE_API.md`.
* 게임 코드는 블루프린트 `BP_Yumeno`의 부모 C++ 클래스 `Yumeno`(Source/Yumeno.h). Tick → `Yumeno.Update(delta)`. `.cpp` 하나에 `.hpp`들을 끝에서 include 한다(Yumeno.cpp → TrialRunner.hpp → Flow.hpp → Explore.hpp → Pad.hpp).
* 주요 API : `UI::Show/SetText/SetVisible/SetPosition/SetSize/SetScale/SetRotation/SetColor/SetTexture/SetFont/SetFontSize/SetOpacity`, `Scene::FindActorById/SetPosition/SetRotation`, `Components::Set/SetString`, `Data::Get("Assets/...json")`, `Save::Write/ReadText`, `Input::IsKeyDown/GetMousePosition`, `Audio::Play(asset,vol,pitch,"sfx")/PlayMusic`.
* **위젯 하나당 노드 256개 한도.** 지금 : Main 250, Stage 203, Flow ~80, Explore ~120, Pad ~70. Main 은 꽉 찼다 → 새 UI는 다른 위젯에.
* **Update 한 번에 엔진 명령 1000개 한도**("engine operation limit" 예외). 매 프레임 SetPosition/SetScale 을 무조건 보내지 말고 **바뀐 값만**(Yumeno.cpp `drawGlyphs`의 GlyphCache 참고).
* `UI::SetColor` 는 Text 는 글자색, Panel 은 배경색. Image 색을 바꾸려면 텍스처 교체.
* `UI::SetFont` 는 글꼴 로딩을 기다리며 위젯 전체를 다시 그린다 → 글꼴은 바뀔 때만.
* 텍스트 외곽선·그림자 속성 없음 → 그림자 사본 층(논의 글자 `MS0..47`)으로 흉내.
* **입력 눈금 소모** : `pressed(key)` 는 읽으면 사라진다. 한 프레임에 같은 키를 두 군데서 읽으면 뒤쪽은 false. Update 맨 앞에서 `enterNow` 로 한 번 읽어 공유한다(Enter 가 안 먹던 버그 2번 있었음).
* 3D 재판장 : 증언대 16개 반지름 5.5 원, 빌보드 입상, 원근 카메라(FOV 43.6, 초점 900px). 화자는 3D 자리와 **같은 사각형**에 UI Portrait 를 겹쳐 글자층이 앞뒤로 지나가게 한다(Courtroom.hpp). SpriteRenderer `color` 는 무시됨 → 어둡게 하려면 `CourtDim` 패널.
* 빌드 : `cd Game && node tools/create-project.mjs && node tools/build.mjs` (출력 끝에 「완료」). C++ 오류는 `grep " error"`.
* **파이썬 heredoc 으로 C++ 패치할 때 `"\n"` 이 진짜 줄바꿈이 되는 사고**가 여러 번 있었다 → 패치 스크립트는 파일로 쓰고 실행하거나 `std::endl`/raw 문자열 사용.

---

## 3. 게임 코드 구조 (Game/Source)

| 파일 | 내용 |
|---|---|
| `Yumeno.h` | 모든 멤버·선언. Mode : Title, Story, Pad, Trial, Menu, Grid, Card, Credits, Explore, Map, Confirm, Popup |
| `Yumeno.cpp` | 위젯 띄우기(ready), Update 분배, 대화창, 논의(논스톱·패닉) 글자 그리기·스타일, Stats(검증용 상태 JSON), DebugJump/DebugChapter |
| `Debate.hpp` | 논의 문장 3D 배치 : 12가지 움직임(Slide·Fly·Swirl·Slam·Wave·Shake·Assemble·Zoom·Rise·Type·Bounce·Spiral), motionOf(이름>문장부호>성격>종류, 직전과 다르게), 약점·V포인트·소음 |
| `Courtroom.hpp` | 재판장 좌표 상수, 카메라 샷, 화자/증언대 화면 사각형 |
| `TrialRunner.hpp` | 재판 단계 실행 : 대사·논의·객관식·언령 고르기·지점·인물 지목·투표·클라이맥스·반론 쇼다운·스크럼·이론 무장·애너그램·발굴·브레인 드라이브. `autoAction()` = 검증용 정답 입력 |
| `Flow.hpp` | 장 진행 : 비트(card·scene·freetime·investigate·trial·execution·ending·end) 실행, 대본 이벤트(say·stage·ui·card·bg·menu·goto·break), 저장/이어하기, 인연·코인·선물·캡슐, 선물 화면, 엘리베이터·처형 연출, 효과음 `sfx()`·BGM `music()` |
| `Explore.hpp` | 1인칭 탐색 : 지도(장소 목록+얼굴 아이콘+미리보기) → 방(넓은 배경 좌우 팬, 서 있는 전신, 조사 대상, 조준점·이름표·미니맵) → 조사/말 걸기. 자유행동 「함께 시간을 보낼까?」, 언령 획득 연출, 띠(자유행동·수사 개시·수사 종료·시체 발견) |
| `Pad.hpp` | V3 모노패드 : 아이콘 6(지도·언령·선물·통신부·교칙·설정), 머리 띠, 오른쪽 띠, 하위 화면 |

### 3-1. 진행 데이터 → 화면
* `data/flow/N.json` 의 `beats[]` 를 차례로. 비트 안 `events[]` 는 선형이고 선택지는 `menu{options:[{label,to,flag}]}` + `goto{to}` 로 펼쳐져 있다(분기 = 번호 점프).
* 수사 비트 `spots[]` = 방. 방마다 `bg`, `intro`(첫 break 전까지 = 들어갈 때 대사), `objects[{name,from,to,who}]`(장면 안 break 구간 = 조사 대상, `who` 가 있으면 그 인물에게 말 거는 대상), `people[]`(방에 서 있는 인물).
  조사 대상을 다 보면 그 장 언령을 모두 수첩에 정리하고 「수사 종료」 → 엘리베이터 → 재판.
* 자유행동 비트 `pool[{who,place,bg,events}]` : 인물별 이벤트. 이벤트가 없는 인물은 `exui::PLACES` 의 기본 장소에 선다. 이벤트 후 → 선물 화면 → 슬롯 차감.
* 언령 이벤트 `card{id,name,desc}` : 새 카드면 획득 연출(클릭으로 닫음).
* 배경 이벤트 `bg{bg}` : `cg:death_N` 은 사망 CG + 「시체 발견」 띠·붉은 번쩍.
* 처형 비트 : `art/cg/exec_{장}_{번호}.webp` 를 한 줄마다 다음 장, 천천히 확대.
* 엔딩(6장) : 「살의를 버린다/버리지 않는다」 → C-A/C-B → 공통 후일담 → 크레딧.

### 3-2. 검증용 상태 `Stats()` / 자동 입력
`window.hbPlayerDebug.call("Driver","Yumeno.Stats",{})` → `{mode, chapter, beat, beatKind, event, line, coins, cards, stage{index,kind,hearts}, auto{kind:key|click|drag|wait|debate,...}, error}`.
`auto` 는 지금 넣어야 할 정답 입력. 새 화면을 만들면 **반드시 auto 도 만든다**(안 그러면 자동 검증이 멈춤 — STALL).

---

## 4. 데이터·에셋 파이프라인 (순서대로)

```bash
python -X utf8 tools/build_data.py        # docs/design/*.md → data/scenes, tables, evidence 등
python -X utf8 tools/build_trial.py       # docs/design/1Nc_*.md → data/trials/1Nc.json + data/kotodama.json(이름) — ERRORS: none 이어야 함
python -X utf8 tools/build_flow.py        # data/scenes → data/flow/*.json + gifts.json + 언령 설명 채우기 — ERRORS: none
python tools/pack_webp.py                 # 새 PNG(art/sprites, cg, cutin, standing_hd, bg) → 같은 이름 .webp
cd Game && node tools/create-project.mjs  # data·그림·글꼴 → Game/Assets, 위젯·장면·블루프린트 생성 (스프라이트는 tools/game_sprites.py 로 1024px 축소, 전신 figure 는 rembg 로 배경 제거)
node tools/build.mjs                      # 개발 빌드 → build-result.json
node tools/package.mjs                    # release 빌드(엔진 패키징) → ../dist/YumenoKuni + zip
```
* `build_trial.py` 대본 형식 : `### T-NN 종류 : 제목`, 논의 표 `| # | 화자 | 문장 | 판정 | 필요 |`(+연출 열), 약점 【】, 판정 노란/동의/잡담/거짓/일반, 선택형 `- 질문/보기/정답/그림/조각/마지막 일격`, 투표 `[UI] 투표 → 이름`, 포즈 `← ken_P03`.
* 사망자 목록 : `tools/build_flow.py` 의 `VICTIMS`, `EXECUTED`(⚠ 스포).
* 장소 → 배경 : `tools/build_flow.py` 의 `PLACES`(낱말 → 배경 이름 앞부분, 위에서부터 먼저 맞는 것).

### 4-1. 그림 도구
| 도구 | 용도 |
|---|---|
| `tools/generate_tpose_nai.py` | 인물 입상/포즈(NAI V5). `CHARACTERS` = 인물 외형 태그(정본) |
| `tools/generate_scene_nai.py` | `--death [이름…] --n 3` 사망 CG(배경 판 `_bg` + 인물 후보 `_fg` → rembg → 합성, 출혈 사인만 피), `--compose 이름 후보.png` 고른 후보로 다시 합성, `--replate` 판 다시, `--bg [이름…]` 배경(`BG` 표 + 장별 `MOOD`) |
| `tools/pack_webp.py` | PNG → WebP |
| `tools/game_sprites.py` | 게임용 스프라이트 1024px, 전신 figure(배경 제거) |
| `tools/make_execution_video.py` | 처형 영상 조립(엔진은 영상 재생이 없어 게임은 키프레임 슬라이드를 씀) |
* NAI 실행 : PowerShell `$env:NAI_TOKEN="..."` 후 실행(토큰은 사용자에게 받는다, 파일에 쓰지 않음). Anlas 소모 → 후보는 `--n` 으로 필요한 만큼만.
* 사망 CG 사인(래피 파일과 일치해야 함, ⚠ 스포) : 1장 흉부 압좌+목 옆 압박흔 / 2장 익사(외상 없음, 젖음) / 3장 리쿠 샌드백 압좌 · 소라 머리·상체 도끼 타격 / 4장 질식(외상 없음, 손톱 끝 피·문 긁힌 자국, 문 앞) / 5장 석궁 화살 관통(책장 사이 통로).

### 4-2. Codex 에셋 작업
* 작업지시서 : `docs/spec/14_코덱스_에셋_작업지시서.md`(§0 공통 규칙). 진행표 : `art/MANIFEST.md`(「6차」 표 = 현재 묶음).
* 6차 지시(선물·패드 부속·언령 아이콘·배경·사망·처형·이벤트·지도·공통 화면·발굴·클라이맥스) 원문은 Claude 의 임시 폴더에 있었다. 요지 : 기존 파일 덮어쓰지 말 것, 직접 열어 검수, git commit 은 하지 않음, PNG 로 만들고 WebP 변환은 따로.
* **현재 상태(2026-10-25 12시)** : 선물 24·얼굴 17·캡슐·코인·언령 아이콘 147·처형 키프레임 1~5장 완료, 이벤트 CG(event_P_*) 진행 중, 지도·장 카드 2~6·방송 화면·발굴 그림·클라이맥스 패널 미완.

---

## 5. 검증

```bash
cd Game
node tools/verify-flow.mjs 0 6        # 새 게임 → 프롤로그~6장 끝까지 자동 플레이 (장 범위 지정 가능 : 2 4)
node tools/verify-trial-full.mjs 2    # 2장 재판만. 셋째 인수 = 시작 단계 번호(DebugJump)
```
* 결과 : `Game/Saved/verification-flow-*/`(장면 캡처 png + report.json). 처음 보는 비트·모드마다 캡처한다.
* **플레이어 `--smoke-test` 는 180초 뒤 스스로 꺼진다** → 스크립트가 `HB_PLAYER_SOAK_HOURS=3` 을 넣는다(이걸 모르고 「멈춤」으로 오해해서 하루를 썼다).
* 플레이어는 하나만 : 검증 두 개를 동시에 돌리지 말 것(끝날 때 `taskkill HBGame*` 로 모두 죽인다).
* 멈춘 것 같으면 실행 중 게임 상태를 엿본다 : `msedgewebview2.exe` 명령줄의 `--remote-debugging-port=N` → `/json/list` 의 page 에 WebSocket 으로 `Runtime.evaluate` 로 `Yumeno.Stats`.
* 「STALL」 = 같은 상태로 3000번 → 그 화면의 `auto` 가 잘못됐거나 정답이 데이터에 없음(예 : 투표 정답이 영정, 애너그램 글자 수 > 구슬 수, 정답 카드가 null).
* 마지막 전체 통과 : 프롤로그~6장(엔딩·크레딧) 2026-10-25.

---

## 6. 남은 일 (우선순위 순, 각 항목 끝 = 완료 조건)

1. **이벤트·막간 CG 연결** : `art/cg/event_{장}_{이름}.webp`, `interlude_{번호}_{장면}.webp` 가 오면 `tools/build_flow.py` 에 표(장면 ID → CG 이름)를 두고 해당 장면 첫 `bg` 앞에 `{"type":"bg","bg":"cg:이름"}` 을 넣는다(사망 CG 넣는 `found` 처리 참고). 12 문서 §5 / 17 문서 [CG] 표기가 원본. → 장면에서 CG 가 보이고 verify-flow 통과.
2. **지도 그림** : `ui/pad/map_park.png`, `map_A0~A6.png` 가 오면 패드 지도 화면(Pad.hpp padShowPage 0번)과 탐색 지도(Explore.hpp showMap 왼쪽)에 쓴다. 지금 탐색 지도 왼쪽은 「가리킨 장소 배경 미리보기」. V3 는 아이소메트릭 층 평면도(16 문서 §5-2).
3. **조사 지점 좌표** : 지금 방의 조사 대상은 배경 가로로 고르게 흩어 둔 자리(Explore.hpp enterRoom) → 그림 속 물건과 안 맞는다. `data/hotspots.json` = `{ "방 장면 ID": { "조사 대상 이름": [u, v] } }`(배경 1600×900 기준 0~1) 를 **배경 그림을 보고** 만들고, enterRoom 에서 있으면 그 좌표를 쓴다. 사람 서는 자리도 같은 방식. → 조준점을 물건에 대면 이름표가 뜬다.
4. **레이 얼굴 아이콘**(`ui/pad/face_rei.png`) 뺨의 검은 얼룩 → 다시 그리기.
5. **장 제목 카드** `ui/common/chapter_2~6.png`, `chapter_E.png` → create-project 가 자동 복사, Flow 의 card 비트가 자동 사용.
6. **아침·밤 방송** : 장면 제목에 「방송」이 있으면 모니터 속 래피 화면(`ui/common/broadcast_{morning,night,body}.png`) 을 배경으로(V3 : 「딩동댕동」 차임 → 모니터). build_flow.py 에서 bg 이벤트로 넣으면 된다.
7. **클라이맥스 추리 만화 칸 그림** `art/cg/climax_{장}_{번호}` → TrialRunner climaxOptions 의 `PanP/PanT`(지금 글자 칸) 를 그림 칸으로. 빈칸은 흑백 + 「?」.
8. **발굴 이매지네이션 그림** `ui/minigame/mindmine_{장}.png` → TrialRunner mindmine 의 `MineBg`(지금 재판장 배경).
9. **재판 연출 더 V3 로** (15·16 문서 §5-2 스크린샷 관찰 참고) : 패닉 논의는 3명이 화면 3분할로 동시에 말함, 논의 스크럼은 양편 얼굴이 좌우로 맞서는 화면, 반론 쇼다운의 「???」 위증 칼날 목록, 이론 무장의 「KILL THE MASTERMIND」 식 색 글자 마지막 일격, 투표는 얼굴 슬롯머신.
10. **아직 없는 시스템** (00 문서) : 노트 승격(하루 1회, 노트 증거), 스킬(Lv2/Lv4 획득, SP 장착, 재판 효과), MP, 재판 결과 화면·등급, 유품 이벤트 Lv 조건(코드는 있음 : need.level 3).
11. **소리** : `audio/cues.json` 의 `file` 칸에 파일 이름을 적고 `audio/` 에 파일을 넣으면 create-project 가 복사한다. 큐 자리는 이미 연결(16 문서 §5 표).
12. 1장 낮 배경이 조금 담백(회색)함 → 필요하면 `generate_scene_nai.py` MOOD 의 기본값에 색을 조금 더.

---

## 7. 자주 하는 실수 모음

* `Game/Assets` 를 손으로 고침 → 다음 create-project 에 지워진다. 원본(`data/`, `tools/create-project.mjs`, `ui/`, `art/`)을 고칠 것.
* 데이터에 `null` 이 들어감 → C++ `value("x","")` 가 type_error 302 로 터진다. 빌더에서 빈 문자열로.
* 새 위젯 노드를 Main 에 추가 → 256 한도 초과. 새 위젯에.
* 매 프레임 모든 노드 갱신 → 1000 명령 한도. 캐시.
* 새 화면에 `auto` 를 안 만듦 → 자동 검증 STALL.
* 같은 키를 두 번 `pressed` → 두 번째가 false.
* Korean 조사 : 이름 뒤 「와/과」「을/를」 은 `josa(word,"와","과")`(Explore.hpp).
* 장면·재판 대사는 인물 말투를 지킨다(01 문서). 선물 반응은 `data/reactions.json`.
