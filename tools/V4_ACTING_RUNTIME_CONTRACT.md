# V4 발화·포즈 바인딩

## 호출

```python
from v4_acting_bindings import build_acting, bind_node
acting = build_acting()                  # 게시 한 번당 한 번
with_pose = bind_node(original, acting) # graph/native bundle/queue 어느 JSON도 재귀 처리
```

source.file/line/선택적fileSha256가 남은 원래 JSON에 적용한 뒤 publisher compact를 해요. 입력 객체는 수정하지 않고 복사본을 돌려요. 모든 원래 id·actor·physicalActor·appearanceActor·표시이름·text·route·condition·judgment를 보존하고 확인된 객체에만 완전한 `pose='rin_C02'`와 `acting` 근거를 더해요. 이미 명시한 pose는 덮어쓰지 않아요.

Node publisher에서 Python을 그대로 호출하려면 `python -X utf8 tools/v4_acting_bindings.py --stdin-json`에 JSON 입력을 보내면 주석 없는 annotated JSON만 표준출력으로 받아요. 큰 graph라면 publisher의 maxBuffer를 입력 크기에 맞게 잡아요. 별도 CLI 인자 없이 실행하면 자체 `tools/v4_acting_index.json`(약434kB)에 source index/자산 선택을 저장해요. 이 authoring index 전체를 Game Data에 게시할 필요는 없어요. 기존Game/Assets를 새로 생성하거나 원작/그림을 추출하지 않아요.

## 허용과 금지

- source의 실제 현재 발화와 정규화 후 정확히 같은 문장만 연결해요. native 약점의【】·〔〕만 제거하고 비교해요. 시점 교체/별도 대사로 바뀐 문장은 새 근거 없으면 기본이에요. SHA가 있다면 현재 원고와 일치해야 해요.
- 같은 발화 바로 앞의 현재 지문에서 그 인물이 명시 주어인 절만 읽어요. 다른 인물의 웃음·과거·조건·미열람·연기·비웃음·부정형을 현재 표정으로 가져오지 않아요. 다른 화자 뒤까지 표정 지속을 자동 추측하지 않아요.
- 명시 동의/직접 강한 이의/실제 한숨 같은 좁은 현재 발화행위도 허용해요. 물음표=당황, 사과=울음, 거절=분노, 수락=미소 규칙은 없어요.
- 실제 native `kind=weak`의 실제 weak.word/answer가 있고 원문 전체 발화와 일치하는 행은 현재 증언 수행으로 T02를 선택할 수 있어요. 명시 agree+answer 행은 현재 지지 발화 T03이에요. 해당 과거 사실이 진실이라고 인증하는 것이 아니고, 약점·동의·위증의 판정/색축도 바꾸지 않아요. 이 보완은 현재 `native_tasks.json`에서 대조한105개 source행에만 있어요. 일반 say 전체를 T02로 바꾸지 않아요.
- native queue의 실제 선택/성공/오답 배열은 재귀 처리하지만 실행 순서나 분기를 합치지 않아요. 동일 event가 stage/debate 배열 양쪽에 있는 것을 추가 실연 횟수로 세지 않아요.
- physical actor가 원문 주체와 다른 경우는 원문의 명시 ‘소라·켄의몸’에 해당하는 현재 몸 외에는 바인딩하지 않아요. appearanceActor가 있으면 그 모습의 같은 C/T 자산을 고르고 actor/appearance 값을 바꾸지 않아요. U는 원래 인물/현재모습이 모두 같은 경우에만 가능해요.
- Ken C02는 진자를 실제 든 그림이라 단순 미소에 사용하지 않아요. Haruka C14는 카메라를 치운 모습이라 단순 한숨에 쓰지 않아요. Koto T02 교정본은 왼팔에 클립보드를 든 상태라 양손으로 증언대를 짚는 원문을 대신하지 않아요. 차/시계/노트/카드 등의 U는 해당 원문 동작과 소품이 직접 있는 경우만 허용해요.
- K/M/X는 자동선택하지 않아요. 5년 전/회상/복원/어린 목소리에서 아동입상이나 반전 입상을 자동 투입하지 않아요. spec12의 옛 장별범인/CG목록은 최신V4 사건 근거로 쓰지 않아요.

## Native 소비

say/queue/논의 line에 있는 pose는 이미 court_figures manifest에 존재하는 완전한 key예요. `courtPose(physicalSeat,poseKey)`나 같은 figure texture lookup에 전달해요. actor의 자리/appearance의 형태와 별개예요. pose는 판정이나 증거/사건 상태를 바꾸는 신호가 아니에요.

바인딩 없는 V4 발화는 physical/appearance의 중립 base를 유지해요. C02 미소나 weak 종류만 보고 자동 감정을 추정하지 않아요. 안전한 native T02/T03도 위의 실제 source 대조가 성공한 경우만 받은 pose를 써요. runtime의 위증 변환은 약점/색을 바꾸지만 새 인물 정체·마법 포즈를 이 모듈에서 생성하지 않아요.

## 확인 범위

`python -X utf8 tools/verify_v4_acting.py`가 현재384기존 export의 앞/뒤와 exact selected HD 정본 존재, source행/직접절, 부정·조건·과거·다른주체 거부, sourceSHA, 정체보존, 본문/노선 불변·멱등성을 검증해요. 최신 수치는 `tools/v4_acting_distribution.json`이에요.

현재35927 chapter say 중228개에 명시 원고 연기가 있고,35699개는 추정하지 않은 기본이에요. C02 170은 실제 원고의 자기 웃음 지문이며 자동 긍정 표정이 아니에요. T03 52/큰웃음4/곁눈질1/한숨1도 실제 자기 지문이에요. 장별 중복을 포함한31개 인물·포즈 key를 사용해요. native는 T02 149/T03 12의161개 배열 레코드(88개 event key)에 대응하며 stage/debate 복제를 포함해요.

이는384포즈 전부의 장면 연기 배치 완료나 실제 UI/3D 시각 합격이 아니에요. 나머지 원고의 연기는 실제 source 쇼트별 감독으로 보완해야 해요. 기존 전체그림을 새로 승인하거나 제작한 것도 아니에요. Game 컴파일·실행·중앙 graph 쓰기는 하지 않았어요.
