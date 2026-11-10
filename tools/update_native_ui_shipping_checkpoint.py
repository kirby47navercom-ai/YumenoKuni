import json
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parents[1];saved=root/'Game/Saved';folder=root/'docs/analysis/v3_rebuild';read=lambda p:json.loads(p.read_text(encoding='utf8'));build=read(root/'Game/build-result.json');suffix=build['id'].rsplit('-',1)[1];p=folder/'UI_교정_재개점_20261030.md';s=p.read_text(encoding='utf8');a=s.index('## 현재 최우선 — 엔진 전체 교체 호환성 점검');b=s.index('## 이전 WebView 상태 — 보존 이력',a)
history=folder/'history/native_ui_shipping_20261102';history.mkdir(exist_ok=True)
if not (history/p.name).exists():(history/p.name).write_bytes(p.read_bytes())
section=f'''## 현재 최우선 — 새 네이티브 UI 패키지의 최종 회귀 검사

- 주인님 최신 “그러면 당장 해”에 따라 발견 오류를 수정했어요. 현재 실행본 `{build['id']}`. 원작접근/예약/목표/에이전트/staging/commit/push0. 기존219/779를 처음부터 재실행하지 않아요.
- **전수 실제 입력검사는 완료**: 기준빌드 `2026-11-01T13-56-29-441Z-0fce033a`에서219/219과제,779/779선택연결,별도변환5/5,정확한정상3복원,두실제엔딩/반복보상,연속8184.761초 통과. 원래보고서는 원래빌드ID를 유지해요. `Game/Saved/native-authored-coverage-final-20261101.json`, `native-stability-acceptance-20261101.json`, `native-whole-game-runs-20261101.json`.
- **추가 성능 결함 수정**: 단독 탐색58.36FPS/활성논스톱10.73FPS에서 UI PNG압축약50ms와전체위젯상태복제가 병목이었어요. 무손실premultiplied RGBA/Zstd전송,고정DIB재사용,동일 frozen상태/asset준비 재사용,검증된동일값재설정 생략으로 교정. 해상도/효과/게임타이머/게임C++/원고/에셋/음향변경0. 실제 shipping에서재판31.12FPS(`native-performance-1793555496171`),탐색58.36FPS(`native-performance-1793555622543`). 안정60FPS라고하지않아요.
- 근거: `Game/Saved/native-ui-performance-approved-latest.json`의원본backup/SHA/CPP외부hunk보존검사, `native-ui-package-delta-{suffix}.json`의6330개동일경로/두생성ID군외Content완전동일/런타임3파일과새module·license2개만변경. `source-identity-{suffix}.json`:56Source/345Data/정상3SHA동일. 이전전체입력근거는 이 불변성으로 재사용하고 새 UI 관련15방식/변환1/10선택지/스크롤·리사이즈/두엔딩은 실제재검사해요.
- 현재진행은 `Game/Saved/native-ui-focused-latest.json` → `native-ui-focused-1793555864065/report.json`. 실행기 `node tools/verify-native-ui-focused-suite.mjs --resume=Saved/native-ui-focused-1793555864065`(Game cwd). **실행중인자체프로세스를중복실행하지않고, 완료된 component는건너뛰어요.** 원래정상3T3-NS-A11로논파종료를검사하며15종에같은수의재판을추가하는작업이아니에요.
- 픽셀검사: `native-ui-frame-candidate/cpp-check.json`20case WIC/PBGRA정확일치, `native-widget-snapshot-1793555784959/report.json`162case frozen상태동일, `native-widget-paint-1793555784956/report.json`실제위젯4frame/선택속성생략까지raster/hit정확동일. 현재Game시간을5시간플레이증거로바꾸지않아요.
- `node tools/verify-flow.mjs`는 Legacy WebView/CDP 검사기라 native실행을의도적으로거부했어요. guard를풀거나이것을제품결함/실제native PASS로세지않고 위Win32검사도구를사용해요.
- 종료후원본/세이브/보고서/캡처는보존,닫힌own QA package는프로젝트바로안 `삭제 대기/`로이동. 현재+직전빌드만유지. 설치Versions/User·금지세파일·working CPP외부DPI/fit hunk 미변경. 정식서명release는인증서없음으로보류이고 현재검증은unsigned development실행본이에요.

'''
p.write_text(s[:a]+section+s[b:],encoding='utf8')
current={'status':'shipping-ui-focused-regression-running','build':build['id'],'executable':build['executable'],'baselineBuild':'2026-11-01T13-56-29-441Z-0fce033a','functionalCounts':{'tasks':219,'choiceEdges':779,'transformedOutcomes':5},'packageDelta':'Game/Saved/native-ui-package-delta-'+suffix+'.json','focused':'Game/Saved/native-ui-focused-latest.json','performance':{'trial':31.120750529607584,'world':58.36295352424385},'wholeGameAcceptance':False,'updatedAt':datetime.now(timezone.utc).isoformat()}
(folder/'native_ui_shipping_audit_20261102.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'build':build['id'],'status':current['status']}))
