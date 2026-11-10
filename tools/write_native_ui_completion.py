"""Publish the completed native audit without rewriting historical run IDs."""
import json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];saved=root/'Game/Saved';folder=root/'docs/analysis/v3_rebuild';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));write=lambda p,r:p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
r=read(saved/'native-ui-compatibility-final-20261102.json');assert r['compatibilityAcceptance'] and r['wholeGameAcceptance'];history=folder/'history/native_ui_final_20261102';history.mkdir(parents=True,exist_ok=True)
for name in ['native_engine_audit_20261101.json','native_whole_game_audit_20261101.json','UI_교정_재개점_20261030.md']:
 if not (history/name).exists():shutil.copyfile(folder/name,history/name)
r['acceptanceScope']='Current authored-game native compatibility on this PC with explicit exact-byte inheritance and actual native UI/input regressions. Not a blanket perfection, stable60FPS or signed-release assertion.'
r['priorCompatibilityProof']='Game/Saved/native-engine-final-verification-20261101.json'
for name in ['native_engine_audit_20261101.json','native_whole_game_audit_20261101.json','native_ui_shipping_audit_20261102.json']:write(folder/name,r)
work_path=saved/'native-performance-work-20261102.json';work=read(work_path);work.update(status='complete',productionBuild=r['build'],finalProof='Game/Saved/native-ui-compatibility-final-20261102.json',next='Native compatibility verification closed. Resume only at a newly reproduced symptom; do not restart completed219/779.');write(work_path,work)
receipt_path=saved/'native-ui-wheel-restoration-20261102/receipt.json';receipt=read(receipt_path);receipt.update(status='verified-current-shipping',verifiedBuild=r['build'],verification='Game/Saved/native-ui-compatibility-final-20261102.json');write(receipt_path,receipt)
pointer_path=saved/'native-ui-performance-approved-latest.json';pointer=read(pointer_path);pointer.update(finalBuild=r['build'],finalProof='Game/Saved/native-ui-compatibility-final-20261102.json',correctedPlayerReceipt='Game/Saved/native-ui-wheel-restoration-20261102/receipt.json');write(pointer_path,pointer)
ledger_path=folder/'editorial_followup_20261101.json';ledger=read(ledger_path);ledger.update(latestBuild=r['build'],executable=r['executable'],currentRuntimeStatus=r['status'],currentNativeFullAudit='docs/analysis/v3_rebuild/native_ui_shipping_audit_20261102.json',compatibilityAcceptance=True,wholeGameAcceptance=True,shippingAcceptance=False);write(ledger_path,ledger)
for name in ['native_engine_audit_20261101.json','native_whole_game_audit_20261101.json','native_ui_shipping_audit_20261102.json','editorial_followup_20261101.json']:shutil.copyfile(folder/name,Path('C:/Users/kirby/Downloads/v3_re/native')/name)
performance={x['case']:x for x in r['performance']};trial=performance['active-nonstop'];world=performance['world'];s=(folder/'UI_교정_재개점_20261030.md').read_text(encoding='utf8');a=s.index('## 현재 ');b=s.index('## 이전 WebView 상태 — 보존 이력',a)
section=f'''## 현재 완료 — 새 엔진 호환성 점검과 발견 오류 수정

- **현재 실행본 `{r['build']}`. 이번 새 엔진 호환성 수정·검증은 완료했어요.** 정본 `docs/analysis/v3_rebuild/native_ui_shipping_audit_20261102.json`, 기계 검증 `Game/Saved/native-ui-compatibility-final-20261102.json`. 검사 완료를 중간보고/예약/목표로 바꾸지 않았고 staging/commit/push0이에요.
- 전수 동작 근거는 원래빌드를 유지해요: `0fce033a`에서219/219과제(15종),779/779선택연결,별도변환5/5,정확한정상3저장,두엔딩/반복보상,연속8184.761초. `native-authored-coverage-final-20261101.json` 및 `native-stability-acceptance-20261101.json`은 덮어쓰지 않았어요.
- 재판 정상3 논파후 `.01f` 최소scale를JS가잘못거부하던 crash를교정했어요. 기존 WebP/동적맵·자원전송/glTF샘플러/휠·긴설명/저장52slot이관과 함께 새 패키지에 유지해요. 해당 원본 수정/SHA는 기존 approved receipts와 최종 package delta로 추적해요.
- 성능 추가수정: PNG압축약50ms를 무손실premultiplied RGBA/Zstd전송으로 교체,고정DIB재사용,동일frozen위젯/asset준비/같은값재설정 재사용. **현재실제단독측정 재판{trial['fps']:.2f}FPS,탐색{world['fps']:.2f}FPS**, 각각약60초. 원래재판10.73FPS에서개선했고 안정60FPS라하지않아요. 해상도·효과·원고·게임C++·게임시간·정답·에셋·음향변경0이에요.
- 첫 UI 재빌드a1f에서23a기준의기존승인휠/reader패치를빠뜨렸고 이 회귀를 실제로 발견·수정했어요. `native-ui-wheel-restoration-20261102/receipt.json`의CPP 역대조로 두branch만복원, working CPP의타인DPI/fit수정은보존. 현재빌드에서휠48/drag307,1024×768→1600×900→1280×720실제리사이즈/GDI6→8→8→8,128MiB프로토콜fault의exit1 모두통과했어요. 실패시도를지우거나옛잘못된실행본을합격으로바꾸지않았어요.
- 새UI15방식/변환1/13행메뉴페이지포함10선택은a1f의실제Win32결과를유지하고, 그뒤변경은exe의위두기존입력/실패branch뿐임을hash/CPP대조했어요. 현재실행본에서정확한정상3재논파·스크롤/drag/3리사이즈·두실제엔딩재개/999→격리지갑500의중복보상없음·오류exit1·단독FPS를추가완료했어요. `native-ui-focused-1793555864065/report.json`의componentBuilds/개별validatedBuild와 `native-ui-wheel-package-delta-20261102.json`로재사용범위를명시해요.
- `native-ui-package-delta-{r['build'].rsplit('-',1)[1]}.json`:6330동일경로/두generated private ID군외Content정확동일,56Source/345Data/기존원고·모델·음향·native게임모듈동일. 원래정상3SHA `d43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7` 그대로예요. 예전검사본을현재빌드실행이라고바꾸지않아요.
- 래스터/상태: actual C++WIC/PBGRA20case정확일치,고정위젯상태162case/실제trial위젯4frame(선택속성생략포함)pixel/hit동일. 최종credits PNG는0fce정본/현재두엔딩모두SHA동일,현재한장직접시각확인. 본편5시간자연체류/모든입력순열/다른PC/문학·미술완벽의증거라고확장하지않아요. 새UI메모리는15방식의별도관찰이고옛2시간을새빌드2시간으로재표기하지않아요.
- `verify-flow.mjs`는LegacyWebView/CDPguard라native를의도적으로거부해요. 이를해제하지않고실제Win32검사로대체했어요. 정식서명release는주인님이인증서를보유하지않아별도로남았고현재는unsigned development실행본이에요. 설치Versions/User·금지세파일·원작V3·원본세이브미변경이에요.
- 재개규칙: **이번호환성점검을미완료로간주하고219/779나전편을처음부터돌리지않아요.** 새증상이있을때해당저장/화면에서만이어가요. 재생성QA package는종료후루트 `삭제 대기/`로이동하고report/캡처/세이브/패키지hash명세를남겨요. 현재+직전빌드유지,삭제/실제공간회수0이에요.

'''
section=section.replace('`native-ui-focused-1793555864065/report.json`의componentBuilds/개별validatedBuild','최종JSON의currentFocused.componentBuilds 및 `native-ui-focused-1793555864065/report.json`의results별validatedBuild')
(folder/'UI_교정_재개점_20261030.md').write_text(s[:a]+section+s[b:],encoding='utf8')
engine_note=root.parent/'engineCreate/CODEX_HANDOFF.md';e=engine_note.read_text(encoding='utf8');marker='<!-- YUMENO_NATIVE_UI_20261102 -->';note=f'''{marker}
유메노쿠니 native UI 호환성 수정·검증 완료: `{r['build']}`. `tools/native-ui-frame.mjs`의손실없는premultiplied RGBA/Zstd전송,`native/desktop/NativeWidgetWindow.hpp`의고정DIB/검증된base64/decode,`prototype/ui-runtime.js`의detached frozen node재사용,`tools/native-widget-layer.mjs`의asset준비재사용. `tools/build-native-player.mjs`는static zstd/link·BSD notice복사를포함해요. 기존wheel/reader처리를누락한첫후보는폐기하고23a+두기존승인패치+UI전송만컴파일; working CPP의타인DPI/fit hunk보존. 실제정상3/휠·drag/리사이즈/GDI/오류exit1/엔딩/단독재판{trial['fps']:.2f}FPS·탐색{world['fps']:.2f}FPS 통과. Game C++·Data·Art·Audio미변경,219/779및2h근거는원래빌드ID로한정재사용. 주인님승인“확인된호환성결함수정허용”,설치Versions/User·금지3파일/staging/commit/push미변경. 상세 `../YumenoKuni/Game/Saved/native-ui-compatibility-final-20261102.json`.
<!-- /YUMENO_NATIVE_UI_20261102 -->

'''
if marker not in e:
 i=e.find('\n');e=e[:i+1]+'\n'+note+e[i+1:];engine_note.write_text(e,encoding='utf8')
print(json.dumps({'status':r['status'],'build':r['build'],'trialFPS':trial['fps'],'worldFPS':world['fps']}))
