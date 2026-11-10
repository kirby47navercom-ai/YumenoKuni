# 원고 소품 상태 연결 계약

`v4_prop_states.py`는 전용 6세트와 직접 검토한 해당 개인시간 소품의 순수 메타데이터 어댑터예요. 원본 모델·원고·중앙 데이터·Game을 쓰거나 실행하지 않아요. 모든 원고 소품의 제작 완료를 뜻하지 않아요.

```python
import v4_prop_states as props
bundle = props.build(root)
report = props.apply_scene_bindings(scene_data, root)
# scene_data에 propCatalog, propDefaults, propStateRanges,
# propStateLifecycle, conditionalSceneRanges만 추가
```

renderer의 최소 소비 단위는 다음과 같아요.

```json
{
  "prop": "haruka.handMirror",
  "source": {"file": "원고파일.md", "fileSha256": "정규화된 실제 원고 hash", "line": 207},
  "startLine": 207,
  "endLineExclusive": 355,
  "when": [{"flag": "F-HA02-A", "equals": "A1"}],
  "space_id": "hotel_washroom",
  "mesh": "Assets/Art/explore3d/dedicated/hotel_washroom.glb",
  "meshNodes": [],
  "nodeVisibility": {},
  "state": {"visible": true, "custodian": "mio", "owner": "haruka", "placement": "held"},
  "applyAt": "after-fully-shown",
  "needsAsset": true,
  "poseBound": false,
  "animationBound": false,
  "knowledgeGrant": false,
  "inventoryGrant": false
}
```

실행된 노드의 실제 `source.file`, `fileSha256`, 한 줄 기준 `source.line`을 써요. 범위는 시작 포함·끝 제외예요. `source.line`과 `quote`는 상태의 근거 지점이며 범위 시작과 다를 수 있어요. 갈래에 쓰인 원문 줄은 그 노드가 실제 실행될 때만 소비해요. `when`의 모든 조건도 맞아야 해요. 조건을 맞히려고 새 flag를 쓰지 않아요. 모든 flag 이름은 현존 73개 실행 그래프의 실제 조건/선택에서 검증해요.

한 대사·지문 안에 여러 행동이 있으면 `state`는 그 지문이 끝난 상태예요. 따라서 글이 전부 나오기 전에는 적용하지 않아요. `resolve(..., fully_shown=False)`는 가시성 변경 없이 deferred를 반환해요. 지문 중간 동작이나 휘는 자동차의 궤적, 공의 비행, 인물의 손 위치·거울 반사는 만들지 않아요.

현재 mesh와 일치하는 `mesh`의 정확한 `meshNodes`에만 `nodeVisibility`를 적용해요. 기본값은 `propDefaults`에 있어요. 다른 장면/만남/그래프 진입·복귀·저장 불러오기에서는 우선 기본값을 복구한 뒤 현재 원문을 다시 평가해요. 소품 하나가 다른 방으로 이동해도 자산 원래 방에 붙어 있지 않도록 원고의 실제 장면 전환에서 범위를 잘라 두었어요.

`state.visible`은 원문 속 실제 소품의 현재 노출 상태예요. `nodeVisibility`는 이미 있는 GLB의 표시 명령이에요. 둘은 구별해요. 예를 들어 펼쳐진 머리 손질 수건은 원문에 있어도 현재 모델은 접힌 수건뿐이므로, 접힌 모델은 숨기고 실제 수건은 `needsAsset:true`로 남아요. 진열용 차·금붕어와 소파 뒤 닫힌 상자도 개인 장난감·실제 책·오목판으로 바꾸어 부르지 않아요.

`custodian`은 지금 물건을 들고 있거나 맡고 있는 사람이고 `owner`는 원문에서 확인된 귀속이에요. 소유자가 불명이면 null이에요. 이 값들은 설명용 상태이며 실제 저장 인벤토리·증거·호감도·지식 flag를 쓰지 않아요. 레이의 원본은 모든 경로에서 레이 소유이고, 미오가 직접 그린 별지는 따로 유지해요. 그림을 게시해도 공동 소유가 되지 않아요. 반납하러 가겠다는 말만 있으면 반납 완료로 기록하지 않아요.

깡통의 `outside`와 `fallen`은 다른 수예요. 각자 매번 여섯 개를 다시 세우는 교대 경기의 4 대 7은 같은 판에 일곱 통이 있다는 뜻이 아니에요. 새 세 사람 경기도 앞 경기 결과와 합치지 않아요. 어느 통이 넘어졌는지 원문에 없으면 특정 색·ID를 골라 쓰러뜨리지 않아요. 그 경우에는 잘못된 여섯 통 직립 모델을 숨기고 실제 수와 미바인딩 pose를 함께 반환해요. 원문의 현재 상태를 재현할 올바른 pose·자산을 renderer가 마련하기 전까지 시각 구현 완료로 계산하지 않아요. 59의 각자 세 번 던지기는 바구니에 공이 정확히 세 개 있다는 증거가 아니므로 물리 개수는 null이에요.

`perspective:objective-unseen-by-mio`는 퇴실 뒤 레이 시점의 원고 장면이에요. 미오가 본 것으로 저장하지 않아요. 부스를 떠난 뒤 혼자 정리했거나 추가 놀이를 했는지도 새로 확정하지 않아요.

43의 공통 마지막 인사는 source 줄이 같아도 현재 B 선택에 따라 장소가 달라요. `conditionalSceneRanges`를 일반 source range보다 먼저 현재 flag로 평가해야 해요. B1은 주방 갈림길의 공용 세트, B2는 휴게실 퇴실 통로, B3는 퇴실 전 휴게실이에요. `resolve_scene(bundle, source, flags)`의 `handled:true, space:null`이면 선택 조건이 없으므로 미바인딩이에요. 이때 휴게실 하나로 고정하지 않아요. 실제로 존재하는 선택으로만 장소를 고르며 새 분기나 새 방 번호를 만들지 않아요.

```powershell
python tools/test_v4_prop_states.py
python tools/test_v4_scene_bindings_more.py
python tools/test_v4_dedicated_spaces.py
```

이 검사는 원고 hash·실제 node ID·분기별 소품/보유/경기 상태·사이드이펙트 없음·정확 퇴실 범위를 검증해요. native renderer의 실제 가시성·애니메이션·반사 검증은 포함하지 않아요.
