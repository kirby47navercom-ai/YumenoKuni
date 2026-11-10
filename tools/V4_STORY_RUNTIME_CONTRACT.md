# V4 원고 실행 데이터 계약

2026-10-29. 기존 `data/flow`, `data/trials`, `data/evidence.json`과 독립된 생산 파이프라인이에요. 현재는 전편 통합 완료가 아니에요. `data/v4_story/manifest.json`의 `campaignReady:false`를 그대로 지켜야 해요.

생성은 `python -X utf8 tools/build_v4_story.py`, 검사는 `python -X utf8 tools/verify_v4_story.py`예요. `--strict`는 미완성 캠페인을 종료 코드2로 차단해요. `tools/v4_story_route_sources.json`의 검토한 원고 해시가 바뀌면 생성기가 멈춰요. 행 범위를 새 원고에 무조건 다시 적용하지 않아요. 저장은 의미 기반 노드ID를 사용하고 행 번호는 출처 표시에만 써요.

## 파일과 범위

- `chapters/P.json`: 두 실제 선택, 지연 콜백, 공통 규칙/개인 능력 문서까지 명시 그래프예요.
- `chapters/1..6.json`: 모든 장의 필수 생활·발견·수사·재판·최종 투표·결과가 다음 장과 실제 열린 결말까지 명시적으로 연결돼 있어요. 성공 모형은 실제 입력 완료가 아니에요. 현재 미확정 과제·선택 개인시간·3D배치는 각 파일과 manifest의 경계를 지켜요.
- `chapters/1.json`: 첫 장의 모든 개인시간 후보와 두 지연 도입까지 실제 소스 분기로 연결돼 있어요. 만난 적 없는 과거 선택에는 명시 missing gate가 있어요. 원문에 있는 모든 후보를 한 플레이에서 강제로 만나게 하지는 않아요.
- `freetime/index.json`: `manifest.authoredFreetimeMeetings`와 동일한 실제 그래프를 열거해요. 정본45회기(20~64), 숫자형 지연15개, 별도 시점 별칭13개의 총73개예요. `completePool`은 이 원고 풀의 명시 분기 컴파일 범위만 뜻하며 실제 플레이·분량·연출 합격과 달라요. 린35의 공개A는 새 발 공동작업 앞에서 끝나고 B/C만 별도 작업 선택을 해요. 카에데40의 비식용꽃과50의 식용상자는 다르게 보존돼요. 늦은152/153은 원래33/22의 도입을 대체하며 별도 시간창에서 다음 만남을 고르게 해요.
- `tasks.json`: 최신 활성 추가 과제150개와 **실제로 따로 컴파일한** 기존 기준 과제만 들어가요. `manifest.tasks.compiledBaseline`이 기준 과제 목록이에요. 기준 과제 전체를 제목만 복사한 것으로 세지 않아요. `runtimeReady`는 답안/바인딩 여부이며 실제 플레이·연출 합격을 뜻하지 않아요.
- `native_tasks.json`: `tools/v4_native_tasks.py`의 순수 네이티브 변환이에요. 미바인딩 과제에는 실행 stage가 없어요. 성공·오답 반응과 graph 복귀를 아래 규약대로 분리해요.
- `blocks.json`: 원고 위치/연출/대사를 찾는 비실행 인덱스예요. 상위·하위 절이 같은 이벤트ID를 공유하므로 전부 직렬 재생하면 안 돼요. 각 블록의 `executable:false`를 지켜요.

## 노드 처리

모든 그래프는 `{schemaVersion:1,contentVersion:'v4',chapter,entry,nodes:{[id]:node}}`예요.

| type | 실제 처리 |
|---|---|
| `say` | 한글 `speaker`, 원래 `text`, `mono`, actor slug를 대사창에 표시한 뒤 `next`로 가요. `delivery`는 원문 화자 부호예요. |
| `stage` | `direction`은 연기·연출·연속성 지시예요. 대사창에 그대로 표시하지 않아요. 명시한 presentation 동작을 처리하고 `next`로 가요. |
| `document` | `title/rows/private` 또는 실제 `image` 문서를 별도 창에 보여 준 뒤 `next`로 가요. `rows:[]`와 그림만 있는 조사 자료도 있어요. 다른 인물에게 사적 문서가 공개된 것으로 처리하지 않아요. |
| `menu` | `options[{id,label,to,set?,requires?}]`에서 하나만 선택해요. 해당 `set`만 저장하고 `to`로 가요. `requires`는 보유한 플래그와 정확히 비교하고 미보유 bool은 false로 취급해요. 조건 미충족 보기는 실행하지 않아요. |
| `branch` | `cases[{flag,equals,to}]` 중 현재 실제 플래그가 같은 첫 항목으로 가요. 없으면 `default`로 가요. 미열람 자유시간을 기본A로 대신하지 않아요. |
| `call` | `returnTo/onReturnSet`을 스택에 보관하고 `target`으로 가요. `onReturnSet`은 아직 적용하지 않아요. |
| `return` | 호출 스택의 `returnTo`로 돌아가며 그 프레임의 `onReturnSet`만 적용해요. 자유시간 완료/수사 지점 완료가 이때 남아요. |
| `evidence` | `evidenceId/name/text/revision`의 실제 카드만 보유 자료에 추가·갱신하고 `next`로 가요. 노드의 `id`와 카드의 `evidenceId`는 달라요. 지문의 카드 언급을 이 이벤트와 혼동하지 않아요. |
| `investigate` | `spots`의 실제 한 조사 지점을 선택해 그 `entry`로 호출해요. 끝에서 normal return으로 허브에 돌아와 해당 완료 플래그만 남겨요. `requiredSpotIds/requiredCards`를 모두 실제 충족한 뒤에만 `next`가 열려요. |
| `task` | `taskId`의 실제 입력을 실행하고 정답/오답 대사·지정 귀환을 지켜요. `runtimeReady:false`나 미획득 언령을 자동 정답으로 우회하지 않아요. |
| `gate` | 명시적 제작 미완성 경계예요. 다음을 자동 선택하거나 옛 flow로 떨어지지 않아요. |
| `end` | 해당 장의 실제 종료예요. P~5는 반드시 `chapterComplete:true`와 다음 장의 문자열 `nextChapter`를 함께 가져요. `nextChapter`만 보고 미완료 단계를 건너뛰지 않아요. 임의의 gate를 장 완료로 취급하지 않아요. |

일반 노드에 `set`이 있으면 실제 그 노드가 발생했을 때만 적용해요. 첫 시체 공개 상태도 그 장면에서만 바뀌어요.

## 수사와 좌표

지점은 `{id,label,space_id,entry,returnTo,completionFlag,onReturnSet,target_id,geometryReady}`예요. `target_id`는 world.json의 실제 타깃이에요. 이 파일의 좌표는 이미 glTF 축이므로 다시 Blender 변환하면 안 돼요. 이 생성기는 안전한 대상ID가 있으면 `world_pos`를 생략해요.

`v4_investigation_placements.py`의 검토한 원고·기존 공간 기반 제작 배치가109지점에 붙어요. 이 단계의 `geometryReady:true`는 native cook을 위한 선택 가능한 기존 target/명시적 marker 명세 준비를 뜻해요. `placementPolicy/sourceProof/runtimeVerified:false/objectMeshMatched:false/reaGeometryRecovered:false`를 함께 보존하며, 실제 물건 형상을 복원하거나 게임에서 검사했다는 뜻으로 쓰지 않아요. `world_pos`는 명시 `coordinate_system:'runtime-world-xyz'` 축을 지키고 Blender 좌표로 다시 변환하지 않아요. 실제3D 표시·충돌·NPC 시각 검사는 부모 런타임의 별도 검증이에요.

수사 원고는 직접 한 일·목격·뒤의 재질문에 정보 의존성이 있어 연속된15개 수사 범위로 나눴어요. 이는 임의 조사 순서의 모든 조합을 검증했다는 뜻이 아니에요. 기존 2D 조사 데이터나 옛 E1 카드로 채우지 않아요. 카드ID는 `v4:E1-01`처럼 분리돼 있어요.

## 재판 과제

각 과제는 `intro/lines/wrong/success`, `targets`, `return`, `retry`, `bindings`가 있어요. `lines`는 논의의 실제 순환이며 같은 내용을 intro로 한 번 더 읽지 않아요. 오답은 그때만 재생하고 같은 질문으로 돌아가요. `return.taskId`가 있으면 해당 다음 과제를 먼저 실행하고 부모 문장으로 뛰어넘지 않아요.

논스톱/패닉/쇼다운의 `answerEvidenceId`는 한 탄환/칼날이에요. `requiresEvidence`가 실제 획득되지 않았다면 성공하지 않아요. 현재 보유 카드 중에서만 선택해요. `answerScope`는 제작자가 범위를 확인하는 글이며 플레이어에게 정답 전에 표시하지 않아요.

인물/범인 지목은 `finalVote:false`이며 사망 인물도 후보로 남아요. 대표 선정도 최종 검정 투표와 다른 선택이에요. 섬광은 원고의 같은 글자 두 개 합치기 지시를 그대로 게임 규칙으로 쓰지 않고, 부모가 재확인한 REA e9550/e96c0의 단일 글자 선택→도착 판정을 사용해요. 대체 추리는 `reasoning`이며 택시·도로·승객 자산을 붙이지 않아요.

### 네이티브 입력과 정확한 복귀

변환 결과는 `{ready,stage,debate?,queues:{intro,wrong,success,wrongVariants},requiresEvidence,scopeOnlyEvidence,outcomes,transformation}`이에요. `stage.script=[]`이며 intro는 입력 전 한 번, wrong은 실패했을 때 실제 조건에 맞는 반응만, success는 판정 뒤 한 번 재생하고 graph task의 `success`로 돌아가요. graph 본문에 성공 문답이 이미 있으면 해당 과제의 success queue는 비어 있어요. 모든 오답 원문을 직렬 재생하지 않아요.

`outcomes.A/B.to`는 정상 반박과 의도적 위증의 서로 다른 graph 노드예요. `judgment:refute/lie` 판정 결과로 해당 한 경로만 고르고 B의 플래그만 적용해요. T2-LIE-01처럼 같은 발언의 정상·위증 약점 문구가 다르면 native line의 `weak/lieWeak`도 달라요. 평상시 normal weak, 카드 의도 반전 상태에는 lieWeak를 사용해요. 카드의 `transformation`은 미오가 내보내는 문장만 바꾸며 실제 과거·자료를 고치지 않아요.

`scopeOnlyEvidence:true`는 현재 논의에서 들은 전제에 대한 임시 선택지예요. 물리적 단서를 획득하는 사건이 아니며 현재 과제를 나가면 인벤토리에 남기지 않아요. `filterOwnedEvidence:true`는 catalogue 목록에 있더라도 실제 보유한 카드만 노출하라는 뜻이에요. task node의 `trialDead/seats`는 현재 공개된 사망과16석 메타데이터예요. 예전 이야기의 사망 목록을 섞지 않아요.

native 논의 문장은 Windows Main 위젯의 UTF-16 48칸 한도를 지켜요. `bounded_debate_lines`가 긴 실제 문장을 마침표 또는 안전한 단어 경계에서 나누며 공백까지 재연결하면 원문과 같아요. 분할 조각은 같은 actor/source와 `sourceLineId/sourceTextSpan/splitPart/splitCount`를 보존하고, `weak/lieWeak/agree/targets`는 해당 단어 전체가 들어 있는 조각에만 남겨요. 표적의 `start`는 그 조각 안의 UTF-16 오프셋이에요. 표적 없는 꼬리는 plain이고, 48칸을 넘는 단일 표적이나 자를 수 있는 경계가 없는 문장은 생성 오류로 막아요. 원문 tasks와 성공·오답·귀환은 바꾸지 않아요.

3장 두 인물 지목은 확인 전의 `켄의 몸`이고, 정체 지목·투표는 `켄(몸의 원래 주인)`과 `소라(현재 켄의 몸)`을 구별해요. `candidateOverrides`의 label/caption은 실제 공개 시점에만 붙고 정답ID는 바꾸지 않아요. 최종 정체 투표에서 켄 후보를 소라라고만 표시해 소라를 골랐다고 생각하는 입력을 ken 오답으로 만드는 혼동을 피해야 해요. 5장 뒤집은 카드의 고의 동의는 `lieWeak.requireAgreement:true/transformedJudgment:'agree'`를 지켜요.

개인시간 call 후보는 `onReturnSet`에서 실제 얻을 자기 회차 완료 플래그가 `requires:false`일 때만 선택할 수 있어요. 별도 일자·선행 조건도 함께 유지해요. 완료·지연도입 완료는 정상 return 뒤에만 확정해요. 원문에 없는 호감도·스킬 수치 보상은 생성하지 않았어요.

`v4_story_freetime_late.py`의 늦은 경로는 기본 그래프를 복제하고 기본 노드ID에 `:late:<회차ID>`를 붙여요. 같은 장에 정상 경로와 늦은 경로가 함께 들어가도 상대의 날짜·첫 대사·귀환 링크가 덮어써지지 않아요. `source`는 실제 원문을 유지하고 지정 대체만 늦은 원고 출처를 써요. 검토한 해시가 달라지면 멈추고 재독해야 해요. 그래프의 `requiresPriorFlags/conditionalPriorFlags`는 정적 검수용 선행 이력 규격이며 실제 후보 노출은 chapter menu의 `requires`와 call 반환 완료 상태로 판정해요.

늦은 아이01의 실제 첫배식은5일차 저녁이며 `AI01Dinner5A3`의 EAT/LEAVE와 각 원문 표지를 남겨요. 과거 `F-AI01-A3-LUNCH`를 부여하거나 다시 고르지 않아요. 늦은 아이02는 이 실제 저녁만 회수해요. 늦은 사츠키03은6일차 공연 뒤의 현재 약속·지각이어서 이미 지나간 점심에 후과를 삽입하지 않고7일차 저녁의 지정149 대면에서만 현재 책·엽서·지각 선택을 회수해요.

나나의 늦은01은12일차 아침88만, 늦은02는 다음13일차 이른 별도 창38-late만 실행해요. 88의 돌그림 대상은 린이며 정상29의 켄 문답을 바꾸어 붙이지 않아요. 38-late도 해당 린 그림만 회수하고57의 옛 판/고리 결과는 실제 A/B를 따로 지켜요. 57-A2만 나나가 앞장 거북이를 혼자 풀고, B1/B2의 다음 장 정답과 혼동하지 않아요. 62에서는 모든 선택에 사츠키가 수선되지 않은 자기 옷을 가져가고, 64에서는 A1만 미오의 새 사진이 한 장 추가되며 어떤 경로에도 인물 사진/사본/현재 삭제가 생기지 않아요.

### 실제 그림 영역

그림 입력의 `image`, `coordinateSystem:'normalized-image-uv'`, `regions[{id,label,polygon,correct,wrongVariant?}]`, `answerRegionId`를 소비해요. 정답의 이름·테두리는 지목 전에 표시하지 않아요. 지목 영역을 보기 순번에 따라 자동으로 배치하지 않아요. 보이는 B 보강판과 창은 기존 실제 그림 좌표이고, 없는 봉인 자리를 임의로 표시하지 않아요.

`tools/make_v4_case1_documents.py`가 별도 새 버전 폴더에 실제 확인한 문구의 대조 그림과 world.json의 기존 방/대상 위치를 투영한 도면을 만들어요. 16/17 원본은 보존해요. `v4_case1_picture_bindings.py`는 source 해시와 문구·world 해시를 확인하고, 해당 수사 자료를 실제 살피는 `document.image`가 증거 카드 획득 **앞**에 발생하도록 붙여요. 이 그림이 새 증거나 사적 질문 본문을 만들지는 않아요. 바닥 결빙을 책상·의자의 얼음으로 바꾸어 부르지는 않아요.

추가 원문 도판은 `v4_case2_6_picture_bindings.py`와 `v4_remaining_picture_bindings.py`가 같은 방식으로 최초 실제 수사 열람에 연결해요. 원문 관계 도판은 원작 실측 평면이나 새 역사 사진이 아니에요. 실제 바닥·옛 사진 CG는 별도 검수된 자산만 써요. 발굴의 실행 규칙은 REA의4인접 동색군 제거→경계색1회전·중력없음이며 원고의 중력 설명은 `sourceMechanic`에만 보존해요. AA3/4/5의 자체 tap/hold/mash chart는 원문 세 wave 문답을 보존하고, V3 곡별 원본 채보라고 주장하지 않아요.

## 음향과 저장

`v4_public_records.build_records(root=None)`는 실제 공개된 절차 안내29개를 `eventById/sourceRanges/records`로 제공해요. 시작 보유 목록은 빈 배열이며 실제 `acquireEventId`가 발생한 뒤에만 해당 `id/title/rows`를 저장해요. 범위 검색으로 같은 절의 다른 대사나 미래 조건까지 한꺼번에 넣지 않아요. 기존 document 창의 실제 열람 저장은 별도로 유지하며 개인 능력 페이지를 공개 교칙으로 바꾸지 않아요. 일반 공통 규칙과 공개 질의는 category가 다르고, 원고에 없는 옛19교칙을 채우지 않아요.

`v4:public-record:6-five-votes`만 `showOnAcquire:true`예요. 원문16a2:31의 실제 함께 읽기 stage에서33~37의 다섯 조건을 문서 창으로 보여 준 뒤 진행해요. 이는 앞으로의 범인/선택 결과를 미리 표시하는 목록이 아니라 그 장면에서 이미 공용으로 읽는 조건표예요. 과반·재논의·오답 처벌·정답 뒤 현재 통제 종료를 원문 그대로 보존해요.

`v4_presentation.score_graph_v4/score_tasks_v4`를 생성기가 직접 호출해 실제 JSON에 주석을 붙여요. 원고 인덱스의 중첩 이벤트 수를 효과음 재생 횟수로 쓰지 않아요. 현재 경로에서 발생한 이벤트만 재생하고, 복원 시 단발 공개음·충격 연출을 다시 틀지 않아요.

선택 플래그, 증거의 현재 개정 내용, 현재 그래프/노드, 호출 스택과 `onReturnSet`, 수사 지점 완료, 남은 개인시간, 실제 현재 음악/무음 상태를 함께 저장해야 해요. V4와 옛 저장은 다른 contentVersion으로 구분해요.

검사는 원문 해시·실제 분기·콜백·정오답 격리·획득 순서를 확인하는 정적 모의 진행이에요. 실제 플레이·목표 시간·3D 화면·음향 청취·전편 완성의 합격 근거가 아니에요.
