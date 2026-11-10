"""Keep current native compatibility proof separate from historical WebView/candidate evidence."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT/'docs/analysis/v3_rebuild'
SAVED = ROOT/'Game/Saved'
NAME = 'native_engine_audit_20261101.json'
read = lambda p: json.loads(p.read_text(encoding='utf8'))
write = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
built = read(ROOT/'Game/build-result.json')
build = Path(built['executable']).parent.name
audit = read(FOLDER/NAME)
receipt = SAVED/'native-engine-additional-approved-20261101/receipt.json'
bundle_file = SAVED/'native-engine-final-verification-20261101.json'
bundle = read(bundle_file) if bundle_file.exists() else {}
verified = bundle.get('ok') is True and bundle.get('build') == build
if 'newConfirmedFailures' in audit:
    audit['historicalReproducedFailures'] = audit.pop('newConfirmedFailures')
if 'originalEngineScopeProof' in audit:
    audit['preAdditionalApprovalScopeProof'] = audit.pop('originalEngineScopeProof')
audit.update(
    build=build, executable=built['executable'], runtime='native/d3d11',
    status='confirmed-native-compatibility-fixes-packaged-and-regression-verified' if verified else 'approved-native-fixes-applied-runtime-verification-in-progress',
    engineOriginalsModified=True, installedVersionsModified=False,
    additionalEngineWriteAuthorization='Human reply: 확인된 호환성 결함 수정 허용. Reproduced defects in this compatibility audit may be repaired; installed Versions/User remain unchanged.',
    additionalApprovedFixReceipt=receipt.relative_to(ROOT).as_posix(),
    currentPackageDelta='Game/Saved/native-engine-sampler-only-delta-'+build.rsplit('-',1)[1]+'.json',
    sourceIdentity='Game/Saved/source-identity-'+build.rsplit('-',1)[1]+'.json',
    compatibilityAcceptance=verified,
    shippingAcceptance=False,
    wholeGameAcceptance=False,
    currentVerification=bundle_file.relative_to(ROOT).as_posix() if bundle else None,
    remainingProductFailures=[] if verified else ['Actual packaged regression evidence still being collected.'],
    remainingRisks=[
        'Representative compatibility evidence is not all219 tasks, every save/branch,5hour timing or every device acceptance.',
        'The authored high-resolution outdoor scene has a large observed script RSS; no whole-game memory/performance-budget pass is claimed.',
        'Installed editor Versions/User were not updated; this source runtime and the linked game build contain the fixes.'
    ],
    next='Use the latest linked build and nearest checkpoint for any newly observed issue. Preserve passed proof; no repeated whole-campaign replay, automation, goals, staging or commits.'
)
audit['historicalCandidateEvidenceNote'] = 'Candidate-labelled reports predate approval/application. Current packaged validation and inheritance boundaries are in currentVerification.'
audit['base64PerformanceCandidate']['status'] = 'Applied under the additional defect-fix permission; see receipt/currentVerification.'
audit['additionalFindings'] = [
    'Old packet-reader exit0 failure is historical; the actual4d package exits1 on injected packet overflow.',
    'Actual packaged migration imports the old flat save automatically before VM startup. Manual QA slot conversion is still distinguished.',
    'Old DOM/CDP reports remain WebView evidence. New reports use Win32 input, D3D11 and native Skia.',
    'Packaging cleanup fix preserves source build/current pointer and quarantines only matching prior exports.'
]
audit['samplerFix'] = {
    'owner':'tools/headless-model.mjs',
    'report':'Game/Saved/native-sampler-test-1793538644397/report.json',
    'cause':'Native DataTexture defaults are nearest-filtered; the headless loader omitted glTF min/mag filters and mip-generation policy.',
    'scope':'14 actual loader fixtures cover PNG/WebP, all6 glTF minification filters plus defaults, magnification/wrap/mips. Original image pixels remain unchanged.'
}
audit['cleanupReceipts'] = [p.relative_to(ROOT).as_posix() for p in sorted(SAVED.glob('native-qa-retention-*.json'))]
write(FOLDER/NAME, audit)
ledger_path = FOLDER/'editorial_followup_20261101.json'
ledger = read(ledger_path)
ledger.update(latestBuild=build, executable=built['executable'], nativeEngineAudit='docs/analysis/v3_rebuild/'+NAME,
              currentRuntimeStatus=audit['status'], currentPackageIdentity=audit['sourceIdentity'])
write(ledger_path, ledger)
external = Path('C:/Users/kirby/Downloads/v3_re/native')
for p in (FOLDER/NAME, ledger_path):
    (external/p.name).write_bytes(p.read_bytes())
resume = FOLDER/'UI_교정_재개점_20261030.md'
text = resume.read_text(encoding='utf8')
a = text.index('## 현재 최우선 — 엔진 전체 교체 호환성 점검')
b = text.index('## 이전 WebView 상태 — 보존 이력', a)
state = '확인된 호환성 결함 반영·해당 실제 회귀검사 완료' if verified else '승인된 결함 반영 완료·실제 패키지 확인 중'
section = f"""## 현재 최우선 — 엔진 전체 교체 호환성 점검

- **현재 상태: {state}**. 최신 빌드 `{build}`는 Win32/D3D11 + Node/V8 + C++ + Skia UI예요. 아래 옛 native/CDP 기록은 WebView 근거이며 새 엔진 합격으로 재명명하지 않아요.
- 주인님이 처음 두 수정에 이어 **“확인된 호환성 결함 수정 허용”**을 명시하셨어요. 추가 허용 질문은 해결됐으며 다시 묻지 않아요. 원본 변경 전후SHA·백업: `Game/Saved/native-engine-additional-approved-20261101/receipt.json`. 설치Versions/User 변경0, SDK 변경0, 외부DPI/fit hunks 보존, staging/commit/push0.
- 적용한 엔진 수정: WebP native texture hook / 초기GPU자원 개별 순서 전송 / 동적MeshRenderer·가시성 동기화와 모델 자원 정리 / native ScrollBox와 Win32휠 / 기존flat저장 자동 이전 / packet-reader 실패exit1 / native Buffer base64 / glTF min·mag필터와 mip생성 정책이에요.
- glTF 필터 누락은 실제 loader에서1003(Nearest)≠1008(LinearMipmapLinear)로 재현했고, PNG/WebP·6min필터+default·mag/wrap/mip **14case PASS** `native-sampler-test-1793538644397/report.json`. 이 수정은 모델·그림 원본이나 해상도/픽셀을 바꾸지 않아요.
- 처음 추가 수정 빌드4d2e76a1은 네 runtime JS/새migration모듈/네이티브PE 코드section 일치, 나머지 game source/Data/UI/art/audio 불변 PASS `native-engine-package-delta-4d2e76a1.json`. 최종 빌드는4d 대비 **headless-model.mjs 한 파일만 변경** `native-engine-sampler-only-delta-{build.rsplit('-',1)[1]}.json`. 전원고·판정·선택·저장형식·음원·그림·모델 bytes는 그대로예요.
- 실제 수정된 패키지 검증 묶음: `Game/Saved/native-engine-final-verification-20261101.json`. 엔진 후보 주입 없이 Stats 관찰만 넣었어요. 최신 실내/야외 이미지를 확인하고, sampler만 바뀐 최종 빌드에서는 동일 bytes의 migration/scroll/CPP/input 근거를 이전4d에서 재사용해요. 처음부터 전편을 다시 돌리지 않아요.
- 검증 범위: 실내geometry·이동/시점·Pad지도·수동multipart저장/완전종료복원, 원래정상3 flat저장52슬롯의 실제 자동이전/정확C재개/새옵션 우선 재시작, 실제244자설명 휠48px/drag307px, 실제packet오버플로exit1, 야외하늘/구름/주변건물/인물/대화창, 논스톱·lie대표입력이에요. **모든219과제/모든분기/정상5시간/다른PC/전체성능을 인증한 것은 아니에요.**
- 야외64MiB 제한은 runtime26GLB의 내장PNG를 무손실WebP로 포장해 해결했어요. 픽셀/해상도·비이미지bufferView·scene/mesh/accessor/material/sampler 불변 PASS `native-glb-compat-1793524239573/report.json`. 원본art 보존. 생성기 `tools/optimize_native_glb.py`+`optimize_assets.py`, 실제야외 출력 근거는 최종 묶음에 있어요.
- 자체 소스 교정은 native/d3d11 빌드,229음향 buffered decode, standalone lie 질문/안내 겹침과 종료후위치복구, 안전한배포정리예요. 원래정상3 SHA d43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7 유지. source56/Data345/skills43 일치 `source-identity-{build.rsplit('-',1)[1]}.json`.
- 과거 실패는 보존해요. `native-world-save-1793519108431/report.json`의state-only PASS는0draw 회색화면이므로 시각FAIL이며 같은폴더visual-review 우선. 예전20초 야외heartbeat/garden call-node 조건/partial stats 읽기는 QA 조건오류로 구분해요. 원래제품실패를 소급PASS하지 않아요.
- 배포도구는dist전체삭제 대신 해당 이전export만 루트삭제대기 이동, source build/build-result/unrelated파일 보존. 실제작은ZIP fixture PASS `package-output-test-1793522496000/report.json`. 실제release/export는 이번 점검에서 하지 않았어요. 인증서옛차단은WORK3408에서해제됐으니 반복하지 않아요.
- 정리는 `Game/tools/archive-native-qa.ps1`의닫힌소유package와prune-builds의옛build만 루트삭제대기로 이동해요. 현재+직전build/실행중PID/원본/State·Saves/보고서/캡처 보호. 삭제0·공간회수주장0. 영수증 native-qa-retention/build-retention JSON을 확인해요.
- 정확한 근거와 한계: `docs/analysis/v3_rebuild/{NAME}`. 고해상도 야외의 큰 메모리 사용과 설치형편집기 미배포는 구별해요. 전체게임 완벽/전체엔진 분석 완료로 확대하지 않아요. 예약/목표/에이전트0.

"""
resume.write_text(text[:a]+section+text[b:], encoding='utf8')
debug = ROOT/'DEBUG_HANDOFF.md'
text = debug.read_text(encoding='utf8')
if text.startswith('## 2026-11-01 새 엔진'):
    text = text[text.index('## 2026-11-01 배포 검증'):]
debug.write_text('## 2026-11-01 새 엔진 — '+state+'\n\n추가 호환성 수정 명시허용으로 원본·dist와 게임 패키지에 반영했어요. 현재 재개점과 native-engine-final-verification-20261101.json이 정본이에요. 예전후보/두번째허용대기는 역사기록이에요. 외부DPI hunk/설치Versions/User/금지파일 보존. 그림필터14case와 최신 실제실내/야외검사, 동일소유모듈의이전4d 근거를 구분해요. 전체5시간/전과제 인증은 아니에요.\n\n'+text, encoding='utf8')
print(NAME)
