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
* **6차 완료**(2026-10-25 16시) : 새 PNG 569장(선물·얼굴·캡슐·코인·언령 147·교칙 20·처형 키프레임 1~5장·이벤트 39·막간 18·지도 8·장 카드·방송·발굴 6·클라이맥스 칸+조각). 기록 `art/BATCH6_FINAL_ASSETS.json`, `art/BATCH6_FINAL_QA.json`.

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

## 6. 2026-10-25 저녁에 끝낸 것 / 남은 일

### 6-1. 끝낸 것 (다시 하지 말 것)
* **이벤트·막간·사건·재판 CG 연결** : `tools/build_flow.py` 의 `EVENT_CG`(장면 UID → CG), `INTERLUDE_CG`(I_N_1/2/4), `INCIDENT_CG`(첫 수사 현장), 아침·밤 방송(`ui:broadcast_*`). 재판 CG 는 `TrialRunner.hpp trialCgs()`(단계 종류/번호 → CG, 대사 동안 화면 가득, 둘이면 절반에서 교체). 처형 첫 장 = `event_N_execution_keyart`.
* **범죄 현장 방 = 사망 CG** : `CRIME_ROOM`(현장 이름 낱말 → death CG). 시체가 보이는 그림에서 조사한다.
* **조사 지점 좌표** : `data/hotspots.json`(장면 ID → 대상 이름 앞부분 → [u,v]). 73개 전부 배경을 보고 정함. 배경 그림을 바꾸면 그 방 좌표도 다시 볼 것(격자 시트를 만들어 확인 — 방법은 §6-3).
* **조사 지점 나누기** : break 가 없는 수사 장면은 언령 하나 = 조사 지점 하나. 「○○의 증언」·「○○의 소매」 처럼 인물에 붙은 대상은 그 인물을 클릭해 조사(`who`).
* **방 배경 고르기** : 현장 이름에서 가장 긴 장소 낱말 → 배경, 없으면 장 기본(`CH_DEFAULT`).
* **지도·장 카드·발굴 그림·클라이맥스 칸 그림** 연결(패드 지도 첫 줄 = 장 지도, 클라이맥스 맞힌 칸 = 그림).
* **재판 V3 연출** : 패닉 논의 사선 3칸, 투표 얼굴 슬롯머신 → 결과, 스크럼 양편 얼굴, 이론 무장 마지막 일격 조각이 아래 줄에 색 글자로.
* **스킬** : `data/skills.json`(효과가 실제로 붙는 11종만). 인연 Lv 로 익히고 SP(6+장마다 2, 최대 16) 안에서 표 순서대로 자동 장착. 효과 코드는 `TrialRunner.hpp skillOn()` 사용처. 통신부 화면에 표시. **효과 없는 스킬은 넣지 말 것**(사용자는 가짜 기능을 싫어함).
* **재판 결과 화면** : 남은 발언력·다시 한 횟수 → 평가 S/A/B/C, 코인 30/20/15/10.
* **노트** : 「적는다」 보기를 고르면 노트에 기록, 보기에 (N…) 가 있으면 노트 카드로 언령에 추가.
* **소리** : 파일 이름을 큐 ID 로 해서 `audio/` 에 넣으면 자동 연결. 이름표 = `audio/CUES.md`(빌드 때 갱신, 들어간 것 ✓). 사용자가 직접 파일을 가져온다 — **원작 음원을 받아 오지 말 것**.
* 레이 얼굴 아이콘 얼룩 제거, 1장 낮 배경 색 보강(NAI).

* **수사 무한 반복 3가지 고침(2026-10-25 밤)** : ① 좌표 키가 앞부분이 겹칠 때(「시체」/「시체의 소지품」) 가장 긴 키가 이긴다 ② 인물에게 말을 걸어야 나오는 대상(`who`)인데 그 사람이 방에 없으면 일반 조사 지점으로 둔다(5장 나나) ③ `who` 대상의 번호를 방 안 순서(k)로 쓴다(`o.index` 는 장면 전체 번호). 논스톱 의논은 줄이 바뀌는 프레임에 글꼴·색만 보내고 글자는 다음 프레임(엔진 명령 1000개 한도, 5장 6단계에서 걸렸음).
* **verify-flow.mjs LOOP 검출** : 재판이 아닌 비트가 10분째 그대로면 `LOOP` 를 찍고 멈춘다(상태가 돌기만 해서 STALL 로 안 잡히던 경우).

* **소리 (2026-10-25 밤)** : 사용자가 준 V3 OST(`Downloads/dtd`, 루프 조사 `dtd/loop-research/`)·효과음(`Downloads/Danganropa Sound Effects`, 사용처 대조표 포함)을 `python tools/import_audio.py` 로 `audio/bgm`·`audio/sfx`(ogg, **git 에 안 올림**)와 `audio/cues.json`(큐→원곡·루프 지점)으로 만든다. 큐↔원곡 표는 그 스크립트 맨 위 BGM/JINGLE/SFX.
  * 루프 : 엔진은 파일 통째로만 반복 → 곡마다 `<큐>_intro`(한 번) + `<큐>`(반복)로 자르고 게임이 intro 끝나기 직전에 넘긴다(`Flow.hpp music/playCue/updateMusic`). 루프 지점 = 팬 BRSTM 수치를 파형 상관으로 다시 맞춤(23곡) / 앨범판이라 같은 소리가 안 되풀이되는 곡은 스펙트럼이 가장 닮은 두 지점(40곡, 이음매 30ms 섞음). 결과·상관값은 `audio/LOOPS.txt`.
  * 징글(`jingle_*`, 장 표지·시체 발견 A~E·래피 등장·투표 슬롯·회상) = 한 번 틀고 `len` 초 뒤 다음 곡. 대본에는 `"music":"jingle_x>bgm_y"`.
  * 장면 곡·이벤트 효과음 배치 = `tools/sound_design.py`(build_flow.py 가 부름). 장면 `bgm`, 이벤트 `music`/`sfx`(배열 가능). 재판 단계별 곡은 `TrialRunner.hpp enterStage`(장마다 재판 곡·이론 무장 곡, 논스톱은 뒤쪽에서 고조곡, 투표 징글 뒤 진상 곡).
  * **엔진 버그 우회** : 런타임 `prototype/audio-pcm-cache.js` 가 `this.fetch(url)` 로 불러 「Illegal invocation」 → 효과음(PCM 경로)이 하나도 안 났다. `create-project.mjs` 가 소리마다 `Assets/Audio/S_<큐>.hbaudioasset.json`(streaming:true, virtualize:false)을 만들어 그 경로로 튼다(HTMLAudio 스트림 경로라 버그를 안 지남). 엔진이 고쳐지면 되돌려도 된다. 엔진 설치본은 건드리지 않았다.
  * 재생 확인 : 런타임 보고서 `Saved/verification-flow-*/UserData/runtime-report.json` 의 `audio.voices`(peak)·`audio.errors`.
* **선물 110종** : 원래 24종(G01~G24) + StrategyWiki 「Trigger Happy Havoc/Presents」 아이콘 86종(P###, 사용자 지시) — `python tools/import_gifts.py`(아이콘 받기·256px 정사각, 한국어 이름·등급, 인물별 love/like/hate). 속옷·성적인 물건·1편 줄거리 기념품은 뺐다(인물이 미성년자). build_flow.py gifts() 가 마지막에 이것을 다시 합친다. 선물 화면은 15종 넘으면 쪽 넘김(14종 + 「다음 쪽」 + 「주지 않는다」), like = 인연 +2.

* **입상 키 비율·서는 자리** : `tools/game_sprites.py normalize()` — 대화 입상(카우보이 샷)을 머리 중심이 가운데(512)로 오게 옮기고, 아래 가운데를 기준으로 키(data/characters.json, 최대 188cm) 비율만큼 줄인다(래피 0.62). 탐색 전신은 480×1040 같은 캔버스에 발끝을 맞추고 키 비율. `NORM` 값을 올리면 전부 다시 변환.
* **포즈** : `tools/pose_design.py`(build_flow.py 가 부름) — 대사마다 `pose`(C01~C14·U1~U6·K, 래피 L). 표정 지시 → 대사 내용 → 기본·미소·버릇 포즈 순환(복선 포즈 sora U4·haruka U6·ken U6 제외). 재판 대본(data/trials script)도 `pose_design.trials()` 가 「slug_코드」로 덮어씀(T01 지목·T02 짚기·T03 동의·T04 몰림 우선).
* **재판 카메라(V3)** : `Courtroom.hpp SHOTS`(정면 밀기·좌우 돌아 들어가기·낮은 기운 샷·얼굴 가까이·높은 원경·논의용 큰 원호) + `TrialRunner.hpp focusSpeaker/updateCamera` — 같은 화자가 이어 말하면 컷, 다른 화자면 원을 따라 휩(0.38초, 속도선 `ui/whip.svg`), 대사 동안 드리프트·흔들림. 화자 밝은 입상(Portrait)·증언대(SpeakerPodium)는 매 프레임 3D 빌보드 투영 자리에 겹친다(`court::billboard`). 고르기 단계·패닉은 가운데에서 천천히 도는 원경(`courtWide`). 증언대 높이 1.2m(키 비율 입상 얼굴이 안 가리게). 확인 : `node tools/capture-trial-camera.mjs [단계] [fast]` → `Saved/camera/`.
* **「수사 종료」 띠가 재판 내내 남던 버그** : 띠 시계가 탐색 화면에서만 돌아서. startTrial 에서 끈다.

### 6-2. 남은 일
1. **소리** : 들어갔다(§6-1). 새 PC 에서는 원본 폴더 두 개를 받아 `python tools/import_audio.py <dtd> <효과음 폴더>` 를 먼저 돌린다(음원은 저장소에 없음). 곡 고르기를 바꾸려면 import_audio.py 표 → 다시 돌리기. 오르골·종·물소리·시계 초침은 받은 효과음에 없어 무음.
2. **Codex 와의 충돌 주의** : Codex 6차 마지막 단계가 「허락 없는 변경」이라며 Claude 가 NAI 로 바꾼 배경·사망 CG 47장을 자기 원본으로 되돌린 적이 있다. **배경(bg/)·사망 CG(art/cg/death_*)는 NAI 결과가 정본**(사용자 지시). Codex 에게 일을 줄 때 「bg/ 와 art/cg/death_* 는 건드리지 말 것」을 꼭 쓴다. NAI 후보 원본은 `art/_candidates/scene/`, 다시 만드는 법은 §4-1.
3. 남은 V3 차이(작음) : 반론 쇼다운의 「???」 위증 칼날 목록, 논스톱 발언이 화자 렌즈 안에서 더 크게.
4. 효과가 없어서 뺀 스킬 19종(표시·힌트형 : 거짓 증언 노란 마크, 증언 감정 표시 등)은 해당 기능을 만든 뒤에 `skills.json` 에 넣는다.
5. 노트 증거의 재판 효과(00 §3-3 : 거짓 증언 반박 시 무조건 유효, 미승격 시 쇼다운 난도 상승)는 아직 없다.

### 6-3. 배경을 보고 좌표 정하는 법
배경(1920×1080)을 640×360 으로 줄여 10×10 노란 격자를 그리고, 방의 조사 대상 이름을 옆에 적은 시트를 만든다(PIL + `C:/Windows/Fonts/malgunbd.ttf`). 대상이 있는 칸을 보고 u=가로/10, v=세로/10. 인물(전신)은 바닥 v≈0.98 에 자동 배치.

## 7. 자주 하는 실수 모음

* `Game/Assets` 를 손으로 고침 → 다음 create-project 에 지워진다. 원본(`data/`, `tools/create-project.mjs`, `ui/`, `art/`)을 고칠 것.
* 데이터에 `null` 이 들어감 → C++ `value("x","")` 가 type_error 302 로 터진다. 빌더에서 빈 문자열로.
* 새 위젯 노드를 Main 에 추가 → 256 한도 초과. 새 위젯에.
* 매 프레임 모든 노드 갱신 → 1000 명령 한도. 캐시.
* 새 화면에 `auto` 를 안 만듦 → 자동 검증 STALL.
* 같은 키를 두 번 `pressed` → 두 번째가 false.
* Korean 조사 : 이름 뒤 「와/과」「을/를」 은 `josa(word,"와","과")`(Explore.hpp).
* 장면·재판 대사는 인물 말투를 지킨다(01 문서). 선물 반응은 `data/reactions.json`.
