# V4 재판 상세요소 — 실행 게시 전 어댑터

2026-10-29. 중앙 `data/v4_story`와 기존 Game 파일을 고치지 않는 별도 보강이에요. 기존 REA 문서와219개 묶음의 대조 스냅샷은 `v4_task_mechanics_review.json`이에요. typedReady219를 모든 V3 상세요소 구현 합격으로 읽지 않아요.

## 게시할 때

`v4_task_detail_bindings.apply_detail(bundle, task=None, root=None)`는 새 복사본을 반환해요. task를 주면 완전한 메모리 변환이며 생략하면 동결한 `data/v4_story/tasks.json`을 작업폴더별 한 번 읽어요. 호출은 기존 `taskv4::prepare`/native cook 앞에 두고, 결과의 기존 success/outcomes/queues/source/answer/보유 근거를 유지해요. 입력 원본·중앙 생성물은 변경하지 않아요. 다시 적용해도 같아요.

- 동의6개의 line.agreeTarget은 `{word,start,glyphStart,answer,source}`예요. `start`는 UTF-16, `glyphStart`는 Unicode 코드포인트예요. 실제 표시·명중 범위는 이 좁은 word이며 문장 전체로 바꾸지 않아요.
- 원고가 지정한 V포인트63개의 line.vpoint는 `{character,glyphIndex,glyphIndexUtf16,optional:true,coordinateSpace:'actual-glyph-projection'}`예요. 실제 글자 투영 위치를 쓰고 약점 중앙을 대신 고르지 않아요. 원고에 선택적이라고만 쓴 나머지에는 가짜 글자/좌표를 만들지 않아요.
- 애너그램은 원고에 있는 `distractors/wrongText/retryPolicy`만 stage에 복원해요. T3의 `wrongText`는 후보 단어별 원문이에요. 무관한 글자에 뜻을 추측해 붙이지 않고 대응되지 않는 입력은 `other`를 써요. 특별 수집물/소음 문장은 추가하지 않아요.

## 반론 묶음

stage.showdownV4에18개 반론의37개 실제 그룹이 있어요. `statementOrder`를 순서대로 읽어 C++ Statement 배열을 만들고 `statements[id]`에서 text/actor/speaker/source/role/requiredHits/durationFrames/gaugeGain/gaugeLoss를 가져와요. 그룹 entries는 아래 둘 중 하나예요.

- `{type:'statement',lineId,statementIndex}` → 그 실제 문장 조각을 베기/칼날 공간에 표시해요.
- `{type:'dialogue',events}` → 베기 입력과 시간을 멈추고 실제 화자 문답을 재생한 뒤 같은 entry에서 resumeDialogue를 해요.

`afterAdvance`는 해당 그룹을 실제 통과한 뒤 다음 그룹으로 가기 전에 한 번 재생해요. T2/T5의 중간 미오·타인 문답을 상대의 베기 문장으로 바꾸거나 뭉개지 않아요. sourceTextSpan이 있는 긴 문장 조각은 원문 순서·공백·sourceLineId를 지켜요.

실제 칼날 표적은 `weakRuntimeLineId/weakSourceLineId`예요. 첫 판정 행을 찾는 대신 배열 마지막에 정답을 붙이지 않아요. 실제 약점 뒤 평문이 있는3개 반론도 정확한 약점에서만 성공해요. 각 target의 word/answer/actor/source와 기존 graph 귀환은 변하지 않아요.

## 순수 C++ 상태

신규 `Game/Source/ShowdownV4.hpp`는 엔진/렌더/JSON에 의존하지 않아요. 스키마를 위의 배열/그룹 구조체로 옮겨 `State.reset(statements,groups,hp,timeFrames)`를 호출해요. 물리 입력·표현·source 문답과 원래 성공 귀환은 부모 컨트롤러가 소유해요.

1. Active에서 실제 보이는 glyph의 중심/반지름/visible/weak/vpoint를 전달해요. `intersects`는 유한 선분까지 최단거리의 원 경계를 포함해요. 가려진 글자·공중 베기는 실패 대본/고정 피해로 바꾸지 않아요.
2. `beginStroke`는 활성 슬롯이 이미 있으면 거절해요. `resolveStroke(actualLineId,a,b,glyphs)`는 일반 문장의 필요 횟수까지 PartialCut/StatementCut을 나누고 실제 약점은 일반 베기로 판정하지 않아요.
3. `blade(actualLineId,selectedEvidenceId,answerEvidenceId,a,b,glyphs)`는 현재 실제 weak 글자에 닿았을 때만 비교해요. WrongBlade일 때만 원래 오답 큐를 조건에 맞게 재생하고, Complete이면 성공 연출 뒤 원래 task 성공 경로로 한 번 귀환해요. plain-tail에는 맞는 근거여도 성공하지 않아요.
4. `tick(allowedScale)`는 일반 진행의 float 시간·게이지 보간·종료 대기를 분리해요. GroupAdvanced/TugSucceeded이면 해당 그룹 afterAdvance를 재생하고 acknowledge로 다음 그룹에 가요. GroupRepeated/GroupRetreated/WrongBlade도 각각 피드백 뒤 acknowledge로 현재/이전 그룹에 돌아가요. gauge 실패가 특정 거짓 주장을 했다는 뜻은 아니므로 원고 없는 반응 대사는 붙이지 않아요.
5. Dialogue는 해당 entry.events 뒤 resumeDialogue, Tug는 누름 에지마다 tugPress와 독립1틱마다 tick이에요. 다 채운 마지막 허용 틱은 성공 우선이고, 일반 집중 시간 감소를 힘겨루기에 복사하지 않아요. halfTug는 실제 장착된 대응 스킬이 있을 때 reset 뒤에만 켜요.
6. `inputAngle`은 패드 deadzone0.125/낮은 축의 마우스 반지름75 벡터/0~360 정규화를 제공해요. `clampArc`의 제한은 호스트가 전달해요. 기존 근거에서 각도 제한표의 생산 수치를 끝내지 않았으므로 gauge와 연결된 정확한 원작 수치표를 복원했다고 주장하지 않아요.

일반 필요횟수2,216/360프레임,초기50,그룹 임계50+일반 조각수×5는 **자체 V4 플레이 튜닝**이에요. 원고의 없는 스토리 사실이나 V3 원본 DAT 값으로 표시하지 않아요. REA는 반복피격1~5/게이지 분기/힘겨루기8회180틱 등의 기제를 뒷받침해요. 정확한 원작 카메라·글자 궤적·모든 스킬·모든 그룹 수치를 재현했다는 합격은 별도예요.

## 확인

`python -X utf8 tools/verify_v4_task_detail_bindings.py`:219개 원본 불변·멱등·표적/실제 문답/귀환·새 소음0을 검사해요. 독립 C++ `tools/test_v4_showdown.cpp`는 기하/입력/반복절단/실제약점/잘못된 칼날/전진후퇴/힘겨루기 마지막틱/시간실패/대화복귀41검사를 해요. 임시 경로의 콘솔 fixture만 컴파일·실행했으며 게임 빌드나 게임 실행은 하지 않았어요.
