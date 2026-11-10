# V4 성장·수동 장착·신규 선택 선물 연결

## 소유권과 근거

`GrowthV4.hpp`는 엔진 호출·UI·대사 실행 없이 상태를 판정하는 독립 모듈이에요. `tools/v4_growth_bindings.py`의45회기는 V4 연속원장12의 인물별01/02/03에 대응하고15지연판은 같은 회기의 별칭이에요. 실제 successful return이 남긴 완료flag만 인정해요. 신규 선택 선물은 루트의 명시 위임으로 `docs/design/rewrite_v4/선물_추가대본_V4.md`에 따로 작성했어요. 기존 원고/기존 FTE/기존 생성기/data는 수정하지 않았어요.

완료 +2인연/+2코인, Lv임계0/4/10/18/28, 선호품 수락 +3, SP6/장별+2/최대16은 기존 자체 시스템00:167·199~205·216~221의 수치예요. V3 원본 수치라고 주장하지 않아요. 관계의 좋고 나쁨, 화해·용서·증거·마법해금·본편 가용 조건을 이 수치로 고치지 않아요. 기존 원고의 회기 자격을 Lv로 다시 잠그지 않아요. 소유/장착/효과 소비 분리는 REA19·21을 따라요. 프로젝트의 등가 효과 그룹(회복빈도 두종 포함) 동시 장착 거부는 명시적 자체 정책이며 원작 Skill 라벨별 group을 복원했다는 주장이 아니에요.

## 성장과 장착

- 멤버 `growthv4::State growthV4;`, include `GrowthV4.hpp`.
- 시작 초기화 `growthv4::Init(growthV4,growthContract,skillData);` 뒤 `growthV4.contract["giftOffers"]=giftContract["offers"];`를 넣어요. 새게임만 이력을 비우고 장 전환은 상태를 유지해요.
- 실제 `storyv4::setFlags`가 완료flag를 적용한 성공 return/menu 경계 뒤 `auto r=growthv4::Observe(growthV4,v4.flags,bonds,coins);`. 같은 원회기와 늦은판을 함께 보거나 반복 표시해도 다시 지급하지 않아요. 단순 begin/say/stage/취소에는 호출하지 않아요. Observe가 반환한 새 획득 목록만 알림에 쓰고 실제 동의/화해 대사를 발명하지 않아요.
- V4의 `equippedSkills()`는 `growthv4::Equipped(growthV4)`만 반환해요. 옛 표순서 자동장착은 V4에서 사용하지 않아요. `Unlock`은 소유만 갱신하고 장착을 바꾸지 않아요.
- 통신부에서 선택한 인물의 `Pages(state,actor)`는 실제 본 회기 목록이에요. 페이지 제목을 친밀함/비밀공개로 바꾸지 않아요. 보지 않은 사생활을 자동 요약하지 않아요.
- 통신부→스킬 전체목록/장착목록에서 `owned`/`equipped`/`Used`/`Capacity`를 별도로 표시해요. Enter의 `Toggle(state,id,chapter,editable)`가 소유·SP·동일효과 그룹을 검사해요. 해제는 구매 환불이 아니에요. 현재 재판/수사 모드에서는 `editable=false`; 패드를 열었다고 이 금지를 풀지 않아요.
- 사용처가 실제 존재하는11항목만 사용해요. 새30스킬 효과/FP가격/MP효과/감쇠효과를 표시만 구현하지 않아요. 현재 프로젝트 데이터에는 FP가격이 없어 FP 구매 화면은 이 계약에서 만들지 않았어요.

## 선택 선물

현재 기존 FTE에는 인벤토리 선물 제시/소모 경계가 없었어요. 새 독립 context를 작성했으므로 앞으로 영구 미구현으로 두는 것은 아니에요.

1. 다음 별도 자유시간 창에서, 실제 현재 후보로 원래 본인이 현장에 있고 이미 해당 인물01을 실제 완료한 경우에만 새 제안을 열어요. 기존 회기 진행 중/수사/재판/발견·방송/강제작업 중에는 금지해요. 원래의 ‘선물 없음’ 장면 직후에 강제 삽입하지 않아요. 본인의 영정·부재, 다른 정체가 사용하는 몸은 전달 대상이 아니에요.
2. `GiftContext{actor,window,freeWindow,busy,present,originalIdentity}`를 구성하고, `GiftEligible(state,offer,v4.flags,context)`를 검사해요. window는 실제 하나의 자유시간 창의 안정ID예요. 화면을 다시 열거나 save/load해도 같은ID를 써요.
3. 독립 제안 `intro`→소지품 목록(실제110ID 중 수량>0)→개별품목 제시로 가요. UI에 내부 `allowedGifts`/disposition을 정답색·별·좋아함 표시로 노출하지 않아요. 증거·공용품·차용품은 이 인벤토리에 자동등록하지 않아요.
4. disposition reject이면 `rejected`만 읽고 목록/그만두기 선택으로 돌아가요. accept이면 먼저 `willing`을 읽고 플레이어의 「건넨다/보류한다」를 다시 받아요. 보류는 `deferred`, 플레이어 철회는 `withdrawn`으로 돌아가며 소모0이에요.
5. 마지막 확정에서 현재 mode/상대/presence/원정체/창/소지 수량을 다시 검사하고 `CommitGift(state,gifts,offer,giftId,v4.flags,context,confirmed,true)`를 호출해요. 성공일 때만 수량1을 빼고 transaction을 기록해요. 실패면 accepted 대사를 재생하지 않고 목록으로 돌아가요. 다른 곳에 보낸 것을 원래 사람이 받았다는 대사는 없어요.
6. 성공 결과의 `r.bonds`만 `bonds[actor]`에 더한 뒤 `Unlock`을 갱신해요. `acceptedByGift[giftId]`만 읽어요(공통 accepted와 item을 따로 중복 재생하지 않아요). +3은 게임 수치이며 다른 신뢰/화해flag는 쓰지 않아요. receipt에 실제 ID/대상/창이 남으며 수락1회/대상/창 중복은 막아요.
7. 각 선택 큐 종료는 같은 독립 context/원래 freewindow로 복귀해요. `fte:*:complete`를 쓰거나 다른 개인회차를 자동으로 완료하지 않아요. 신규 선물 자체가 기존 FTE 슬롯 두 개를 동시에 소비했다고 해석하지 않아요. 실제 가용창과 소요처리는 루트의 freewindow 소유자가 결정해요.

15인×110품목=1650 disposition, 수락45종 조합, 각 품목별45개 추가 반응을 작성했어요. 모든 공식 ID는 새 자체 선물 그림110개와 대조해요. 각 인물03의 실제 거절/선퇴실/사생활 경계를 말투 참고로 읽었지만 미열람 과거를 회상시키지 않아요.

## 저장과 원본 계약 게시

- 성장/선물 상태는 `save["growth"]=growthv4::Save(state)`와 기존 bonds/gifts/coins를 같은 payload에 넣어요. 불러오기 전에 Init 및 giftOffers 병합을 먼저 하고 `Restore(temp,savedGrowth,chapter)`로 원자적으로 검증한 뒤 live에 반영해요. 선물 receipt/회기claim/소유/장착은 모두 저장해요. 로드에서 reward 함수를 다시 호출하지 않아요.
- 신규 schema 전 저장에서 성장필드가 없으면 `Observe(...,false)`로 실제완료flag의 이력만 prime하고 기존 bonds/coins는 보존해요. 이 마이그레이션은 과거 기록을 지급되지 않은 보상으로 몰래 재정산하지 않아요. 소유는 기존 실제bonds와 지원효과로만 열어요.
- 자체 JSON 산출물은 `tools/v4_growth_contract.json`, `tools/v4_gift_contract.json`이에요. 큰 gift JSON은 authoring 계약이라 그대로 nativebounded asset으로 넣지 말고 items/header와 인물별 scenes/offers를 분할하고 source를 compact해 게시해요. Game 생성기/Assets는 루트 소유라 여기서 실행하지 않았어요.
- 검증: `python -X utf8 tools/verify_v4_growth.py`, `python -X utf8 tools/verify_v4_gifts.py`. 45회기/60flag,11실효스킬,314독립say,1650품목판정,90불가context 검증이에요.
- 네이티브 순수 fixture `tools/tests/v4_growth_fixture.cpp`는 중복 별칭/무자동장착/SP/중복효과/금지모드/저장/수락1회소모/거절·부재0소모를 assert해요. g++ -fsyntax-only만 통과했고 실행은 루트가 직렬로 해요. 이 정적 결과를 실제 게임 메뉴/청취/전달 합격으로 부르지 않아요.
