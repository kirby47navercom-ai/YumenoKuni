# V4 재구성 만화 표시 연결

담당 범위는 독립 metadata와 정적 검증이에요. Game/중앙 생성물/원고/원본 그림을 수정하거나 게임을 실행하지 않았어요.

```python
from v4_comic_presentation import build_comic, bind_task
comic = build_comic()                  # publisher당 한 번
native_bundle = bind_task(native_bundle, comic)  # 복사본 반환
```

`bind_task`는 해당하는 여섯 bundle의 `stage.comicPresentation`만 추가해요. 파일 경로를 native 이미지 경로로 바꾸는 기존 mapper **이전**에 호출해요. 이미 있는 `stage.slots`의 정답·후보 이미지·개별 response와 `queues`를 사용해요. annotation에는 그 대사를 다시 복사하지 않아요. bundle당 추가분은 6KB 미만으로 검증했어요.

`tools/v4_comic_presentation_index.json`은 전체 source/개별 문답을 대조하기 위한 오프라인 인덱스예요. 약563KB이므로 통째로 한 native asset에 게시하지 않아요.

## 보드와 입력

- `board.image`: 현재114후보 중 맞는38장을 합성한 완성 page예요. 옛 `archived_summary_pages_not_used_for_new_puzzle` 그림이 아니에요.
- `board.size`: 1~5장5760×2160/3×2칸,6장7680×2160/4×2칸이에요. `keepAspect=true`를 지켜요. 전체를16:9로 늘리지 않아요.
- `slots[].atlasRectPixels`: page 안의 `[x,y,width,height]`예요. 모든cell은1920×1080이에요. `atlasUv`는 `[left,top,right,bottom]`이에요. 실제padding과작은전후구획도cell 안에 포함돼요.
- 미완성 보드는 중립 종이·칸번호와 이미 맞춘 개별 후보만 보여요. **완성 page에는 모든 답이 그려져 있으므로 `revealOnCompleteOnly` 전에는 그대로 띄우지 않아요.** 빈칸 라벨에 정답 설명을 쓰지 않아요.
- 원고는 순서를 정했어요. 보드에 전체 빈칸을 보여 주되 현재 첫 미완성칸만 선택하고 그 칸의 실제3후보를 함께 보여요. 다음pack/보상/소모/오답횟수해금은 없어요. native `slot.options[].label`은 원고의 그림 설명이고 세 후보를 구분하는 데 필요해요.
- 오답은 선택한 보기의 `response`만 읽고 같은 칸으로 돌아가요. 앞서 맞춘 칸은 유지해요. 세계관 되감기·새 목격·새 증거 취득을 일으키지 않아요.
- 정답은 해당response를 한 번 읽고 다음 칸을 열어요. 앞 칸을 다시 눌러 정답 보상을 중복 지급하지 않아요. 전체 완성 전에는 task성공을 호출하지 않아요.

## 완료 후 원문 문답 소유권

정답response를 배치 때 읽은 뒤 완성 때 전부 다시 읽으면 원고의「한 번」「앞 심리 전체를 다시 재생하지 않는다」와 충돌해요. 새 단독 내레이션을 만들지 않아요. 완성 page 위에는 다음 **기존** 닫기만 이어가요.

|장|`completion.owner`|실제 소유 경로|
|---|---|---|
|1·2·6|`task-success-queue`|이미 있는 `bundle.queues.success`; 끝나면 기존 task귀환|
|3·4·5|`story-graph`|이미 있는 `task.success`→159/160/161의MG-08 say/stage들|

3~5장의 compact `completion.entry/nodeIds/returnTo`로 완성 page를 유지할 실제graph구간을 구분할 수 있어요. 이구간대사를 별도queue로 복사해서 재생하지 않아요. `nodeIds`를 벗어나면 원래 다음 장면·모드로 돌아가요. 완성대사 뒤의 투표·누가누른표·추가심리·지원선택을 미리 읽지 않아요.

intro 또한 이미 taskqueue에 있는1·2·6장/앞graph에 있는3~5장을 중복 재생하지 않아요. 전체 인덱스의 `introOwner`는 검토용이에요.

## 검증

```text
python -X utf8 tools/verify_v4_comic_presentation.py
python -X utf8 tools/v4_comic_presentation.py --output tools/v4_comic_presentation_index.json
```

6장38칸114후보의 현원고표/346선택문답/완료문답 source를 확인해요. 실제38pagecell과 현재정답candidate의 Lanczos축소픽셀이 같은지 검사해요. 순수복사·재호출동일·변조답거부·중앙native task파일불변도 검사해요. 잘못된그림전체의내용이나새nativecontroller동작·청취·수동플레이합격을 이정적검사로 선언하지 않아요. 6page는 직접 픽셀을 봤고, 틀린76후보전체를 이작업에서 다시 눈으로 본 것은 아니에요.

## 독립 native 위젯 생성 모듈

```js
import {emitV4ComicUI} from './v4-comic-ui.mjs';
await emitV4ComicUI({write, body, head});
```

신규 `Game/tools/v4-comic-ui.mjs`만 만들었어요. 기존생성기에 위호출을 연결하는 것은 루트담당이에요. 결과는 `Assets/UI/ComicV4.hbwidget.json`, instance명은 `comicv4`예요. 기존자체부품WebP4장을 `write(path, Buffer)`로 전달하므로 별도copy인자가 필요없어요.

- `Shade`는Panel, `Title/Hint`는Text, `CompletePage`는contain Image예요.
- `SlotP0..7/CandidateP0..2`는Image예요. `comicV4Textures`의 empty/focus/placed/wrong 경로를 SetTexture로 골라요. `SlotI/CandidateI`는contain Image, `SlotT/CandidateT`는Text예요.
- 정확히38노드(루트포함)이며 전부root직속이에요. 기본visible=false라 root가 현재필요한노드만 켜요. 그림과번호/설명을 다른사각형에두고, Text의zIndex30/그림20/plate10/제목·footer40을줘요.
- `comicV4Layout.slot(i,3|4)`와 `.candidate(i)` 또는 반환`layout`에 각각 `[x,y,w,h]`가있어요. 6장은0~7전부4열배치로 재배치해요. 처음부터숫자만있고정답그림·정답문구는없어요.
- 완료는slot/candidate를모두끄고CompletePage만켜요. 요청기본rectangle은 `[45,100,1190,450]`이에요. 기존본문프레임이y512부터라 완료문답을함께보일때는 page높이를400이하로줄이거나본문을재배치해요. 별도위젯의Shade가Main대사위에쌓이면문답까지어둡게가리므로 완료문답상태의Shade/위젯순서도루트가조정해요.

`node tools/verify_v4_comic_ui.mjs`는 기존부품과동일bytes/고정ID·type/3열·4열/그림과글자·후보와보드·제목과footer비겹침을 인메모리검사해요. `python -X utf8 tools/verify_v4_comic_ui_pixels.py`는 실제114caption을실제Pretendard17px로재어 엔진lineheight1.3에서142px안(최대5줄)에들어감을확인해요. `tools/v4_comic_ui_offline_preview.png`는답없는중립placeholder의오프라인부품배치증거이고게임캡처가아니에요. Game파일쓰기/빌드/실행은없어요.
