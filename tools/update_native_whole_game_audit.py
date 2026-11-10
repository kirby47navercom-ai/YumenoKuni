"""Persist exact native task/branch resume points without promoting partial work."""
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SAVED=ROOT/'Game/Saved'
FOLDER=ROOT/'docs/analysis/v3_rebuild'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
build=read(ROOT/'Game/build-result.json')
pointer=SAVED/'native-whole-game-runs-20261101.json'
if not pointer.exists():
    pointer.write_text(json.dumps({'tasks':'native-all-tasks-1793541469758','choices':'native-all-choices-1793541482068','alternate':None},indent=2)+'\n',encoding='utf8')
runs=read(pointer)
def evidence(kind,total,key):
    name=runs.get(kind)
    if not name:return {'passed':0,'total':total,'complete':False,'run':None}
    folder=SAVED/name
    progress=read(folder/'progress.json')
    assert progress['build']==build['id'], 'Explicit inheritance decision required after a build change'
    valid=lambda r:r.get('ok') and (kind!='alternate' or r.get('outcome',{}).get('judgment')=='lie')
    passed={r[key] for r in progress['results'] if valid(r)}
    unresolved=[r for r in progress['results'] if not valid(r) and r.get(key) not in passed]
    return {'run':folder.relative_to(ROOT).as_posix(),'passed':len(passed),'total':total,'complete':len(passed)==total and not unresolved,'unresolved':[{key:r.get(key),'error':r.get('error')} for r in unresolved],'progress':(folder/'progress.json').relative_to(ROOT).as_posix(),'session':progress['session'],'closed':progress.get('closed',False)}
tasks=evidence('tasks',219,'taskId');choices=evidence('choices',779,'key');alternate=evidence('alternate',5,'taskId')
sessions=[]
for kind in ('tasks','choices','alternate'):
    if not runs.get(kind):continue
    for session in sorted((SAVED/runs[kind]).glob('session-*')):
        data=session/'telemetry.jsonl'
        if not data.exists():continue
        rows=[json.loads(line) for line in data.read_text(encoding='utf8').splitlines() if line.strip()]
        if not rows:continue
        runtime=session/'runtime.json'
        sessions.append({'session':session.relative_to(ROOT).as_posix(),'kind':kind,'seconds':(rows[-1]['time']-rows[0]['time'])/1000,'samples':len(rows),'firstRSS':rows[0]['memory']['rss'],'lastRSS':rows[-1]['memory']['rss'],'peakRSS':max(r['memory']['rss'] for r in rows),'runtimeReport':runtime.relative_to(ROOT).as_posix() if runtime.exists() else None,'scope':'Node/V8 process memory sampled every second; native/GPU counters require the runtime report. Sample duration alone is not a memory-budget pass.'})
normal=SAVED/'ui-checkpoints/normal-ch3-latest/savegames.json'
result={'build':build['id'],'status':'actual-native-full-coverage-in-progress','wholeGameAcceptance':False,'tasks':tasks,'choices':choices,'alternateTaskOutcomes':alternate,'sessions':sessions,'stabilityAcceptance':False,'stabilityRequired':'At least2hours continuous native process, varied scenes/modes and transitions, no runtime/audio failure, bounded memory after warm-up; evaluate telemetry and runtime counters before acceptance.','confirmedEngineFix':'Game/Saved/native-transform-approved-20261101/receipt.json','packageDelta':'Game/Saved/native-transform-package-delta-0fce033a.json','priorCompatibilityProof':'Game/Saved/native-engine-final-verification-20261101.json','canonicalSaveSHA256':hashlib.sha256(normal.read_bytes()).hexdigest(),'scope':'Authored precondition fixtures are explicit. Actual Win32 input must produce each current task/choice outcome. Fast unread dialogue skipping is not a human5hour timing proof. Historical failed attempts remain preserved and are not retroactively passed.','continue':'Resume the linked current-build progress files; do not replay passed cases, schedule work, create goals or commit.'}
result['updatedAt']=datetime.now(timezone.utc).isoformat()
for kind,required in (('ending',2),('canonical',1)):
    report=SAVED/runs[kind]/'report.json' if runs.get(kind) else None
    proof=read(report) if report and report.exists() else {}
    result[kind+'Replay']={'complete':proof.get('ok') is True and proof.get('build')==build['id'] and len([r for r in proof.get('results',[]) if r.get('ok')])==required,'report':report.relative_to(ROOT).as_posix() if report else None,'required':required}
result['nativeWin32MemorySamples']='Game/Saved/native-win32-memory-20261101.jsonl'
stable_file=SAVED/'native-stability-acceptance-20261101.json'
stable=read(stable_file) if stable_file.exists() else {}
result['stabilityAcceptance']=stable.get('ok') is True and stable.get('build')==build['id'] and stable.get('continuousSeconds',0)>=7200
result['stabilityProof']=stable_file.relative_to(ROOT).as_posix() if result['stabilityAcceptance'] else None
final_file=SAVED/'native-authored-coverage-final-20261101.json'
final=read(final_file) if final_file.exists() else {}
if final.get('build')==build['id']:
    result['authoredCoverageProof']=final_file.relative_to(ROOT).as_posix()
    result['status']=final['status']
    result['wholeGameAcceptance']=final['wholeGameAcceptance']
    result['performanceBaselines']=final.get('performance',[])
assert result['canonicalSaveSHA256']=='d43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7'
name='native_whole_game_audit_20261101.json'
(FOLDER/name).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(Path('C:/Users/kirby/Downloads/v3_re/native')/name).write_bytes((FOLDER/name).read_bytes())
audit=read(FOLDER/'native_engine_audit_20261101.json')
audit.update(build=build['id'],executable=build['executable'],status=result['status'],compatibilityAcceptance=False,wholeGameAcceptance=False,shippingAcceptance=False,fullNativeAudit='docs/analysis/v3_rebuild/'+name,remainingProductFailures=tasks.get('unresolved',[]),next=result['continue'])
audit['compatibilityAcceptance']=audit['wholeGameAcceptance']=result['wholeGameAcceptance']
audit['currentPackageDelta']=result['packageDelta']
audit['sourceIdentity']='Game/Saved/source-identity-'+build['id'].rsplit('-',1)[1]+'.json'
(FOLDER/'native_engine_audit_20261101.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
ledger_path=FOLDER/'editorial_followup_20261101.json'
ledger=read(ledger_path)
ledger.update(latestBuild=build['id'],executable=build['executable'],currentRuntimeStatus=result['status'],currentNativeFullAudit='docs/analysis/v3_rebuild/'+name)
ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for mirror in ('native_engine_audit_20261101.json','editorial_followup_20261101.json'):
    (Path('C:/Users/kirby/Downloads/v3_re/native')/mirror).write_bytes((FOLDER/mirror).read_bytes())
resume=FOLDER/'UI_교정_재개점_20261030.md'
text=resume.read_text(encoding='utf8')
a=text.index('## 현재 최우선 — 엔진 전체 교체 호환성 점검');b=text.index('## 이전 WebView 상태 — 보존 이력',a)
archive=FOLDER/'history/native_whole_start_20261101_2310'
if not archive.exists():
    archive.mkdir(parents=True)
    (archive/'UI_교정_재개점_20261030.md').write_bytes(resume.read_bytes())
stability_state=(f"연속{stable['continuousSeconds']:.1f}초 실제 실행/종료와메모리검토통과. {result['stabilityProof']}. 단독성능측정은별도상태를따라요." if result['stabilityAcceptance'] else '장시간 메모리 판정은 아직 미완료예요.')
section=f'''## 현재 최우선 — 엔진 전체 교체 호환성 점검

- 주인님 최신 **“그러면 당장 해”**에 따라 이전 대표검사 뒤 남았던 전219과제·779선택지·장시간 안정성 검증을 실제 Win32 입력으로 계속하고 있어요. 중간보고로 종료/예약/목표/commit을 하지 않아요. 현재 빌드 `{build['id']}`, native/D3D11+V8/AOT C+++Skia예요.
- 정확한 현재 근거: `docs/analysis/v3_rebuild/{name}`. 현재 실제 과제 성공 **{tasks['passed']}/219**, 선택지 응답 연결 **{choices['passed']}/779**, 별도 변환 분기 **{alternate['passed']}/5**. 부분 통과를 전체 완료라고 하지 않아요. {stability_state}
- 정상3정확SHA의추가재개검사: {result['canonicalReplay']['report']}, 두실제엔딩 재개/타이틀/500지갑으로cap을피한중복보상검사: {result['endingReplay']['report']}. 각complete와실제보존원본을구분해요. 변환검사가실행중이면기다리고, 재개할때는 `--only=T1-LIE-01,T2-LIE-01,T4-LIE-01,T5-LIE-01,T6-LIE-01 --judgment=lie`를반드시유지해요. normal/refute통과를변환분기통과로세지않아요.
- 재개는 `node tools/verify-native-all-tasks.mjs --resume=Saved/{runs['tasks']}` 및 `node tools/verify-native-choice-branches.mjs --resume=Saved/{runs['choices']}`(Game cwd). **이미 성공한 case는 progress.json으로 건너뛰어요. 실행 중이면 새 프로세스를 중복 실행하지 않아요.** 각 session의 stats/telemetry/failure와 현재 프로세스 종료 여부를 먼저 확인해요.
- 전편 구조도달 fixture `Game/Saved/native-coverage-fixtures-1793540307302/choice-route-coverage.json` PASS: 779선택지 precondition/219과제 precondition을 export. 이 생성기에서 상류 과제성공은 주입했으며 native검사의 현재 과제성공·선택결과는 주입하지 않아요. 원래 저장이 있는148과제는 변경없는 복사, 나머지는 지원되는 optional 초기값을 쓴 명시적 도달상태 fixture예요. 자연 전편 체류시간·5시간 플레이 증거가 아니에요.
- **이번 실제 결함/수정**: 정상3장 T3-NS-A11 논파 성공 뒤 결과연출에서 `C++ 변환 데이터 범위 오류`로 script exit1. `.01f`→0.009999999776482582를 JS의엄격한0.01 하한이 거부했어요. `engineCreate/tools/run-project.mjs::validNativeTransform`을 float32동일하한으로 교정, 유한성/shape/10000범위 유지. 실제이전실패로그/backup/SHA/10case PASS/수정뒤동일정상저장 실제성공은 `Game/Saved/native-transform-approved-20261101/receipt.json`에 있어요.
- 현재패키지6335경로 중6332동일. 다른세파일은 위 run-project와 생성기 private IDs의BP/MainScene뿐이에요. `Game/Saved/native-transform-package-delta-0fce033a.json`. 이전핵심호환성검사 `Game/Saved/native-engine-final-verification-20261101.json`는원래빌드 범위를보존해요. 이전글꼴/모델/음향/저장/휠/glTF14case의 source owner와불변bytes에따라재사용하고 옛CDP를진짜native근거로바꾸지않아요.
- 검사도구초기실패는구분해요: F1한번에cold시작하면1000명령상한을넘어 지원되는C staged restore로교체; title저장가용캐시refresh와복원2phase대기; 물리키가한frame중간에소실될수있어메뉴는2frame; 쇼다운은긴다중move가발언시간을소모해빠른정상drag로교체후T6-RS-01실제성공. 게임타이머/성공조건/명령상한완화0.
- 원래정상3저장 SHA `d43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7` 보존. 엔진수정은“확인된 호환성 결함 수정 허용”범위, 설치Versions/User·금지세파일·외부DPI hunk미변경. 현재+직전빌드유지, 닫힌own QA package만루트삭제대기로이동. 보고서·캡처·State/Saves는보존하고실제삭제/공간회수0이에요.
- 현재생성도구 `tools/update_native_whole_game_audit.py`로수치/정본을갱신해요. 옛 `update_native_engine_audit.py`는이전대표검사문구생성용이므로현전편검사를덮어쓰지않아요. 이전상세현재절은 `docs/analysis/v3_rebuild/history/native_whole_start_20261101_2310/UI_교정_재개점_20261030.md`에보존했어요.

'''
resume.write_text(text[:a]+section+text[b:],encoding='utf8')
print(json.dumps({'tasks':tasks['passed'],'choices':choices['passed'],'alternate':alternate['passed'],'longestSeconds':max((s['seconds'] for s in sessions),default=0)},ensure_ascii=False))
