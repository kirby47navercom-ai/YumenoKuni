import json
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parents[1];saved=root/'Game/Saved'
attempts=[]
for p in sorted(saved.glob('native-performance-*/report.json')):
    r=json.loads(p.read_text(encoding='utf8'))
    attempts.append({'work':p.parent.name,'build':r['build'],'case':r['case'],'fps':r['fps'],'seconds':r['seconds'],'candidatePackage':(p.parent/'owned-package.json').relative_to(root).as_posix()})
build=json.loads((root/'Game/build-result.json').read_text(encoding='utf8'))
result={'status':'shipping-native-ui-regression','productionBuild':build['id'],'attempts':attempts,'functionalCoverageAlreadyComplete':{'baselineBuild':'2026-11-01T13-56-29-441Z-0fce033a','tasks':219,'choiceEdges':779,'alternativeOutcomes':5,'seconds':8184.761},'provenCandidateChecks':{'pixelDecode':'Game/Saved/native-ui-frame-candidate/cpp-check.json:20 exact WIC/PBGRA checks','stateSnapshots':'Game/Saved/native-widget-snapshot-1793554577543/report.json','raster':'Game/Saved/native-widget-paint-1793554784146/report.json'},'applied':'Game/Saved/native-ui-performance-approved-latest.json','delta':'Game/Saved/native-ui-package-delta-'+build['id'].rsplit('-',1)[1]+'.json','next':'Run current shipping single-process scene FPS and focused actual regressions across15 task families, paged menu choices, transformed route, endings, resize/scroll. Logic/data/art/audio/native gameplay module bytes are proven unchanged; do not replay219/779 or relabel old reports.','updatedAt':datetime.now(timezone.utc).isoformat()}
(saved/'native-performance-work-20261102.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
p=root/'docs/analysis/v3_rebuild/UI_교정_재개점_20261030.md';s=p.read_text(encoding='utf8');marker='## 이전 WebView 상태 — 보존 이력'
text='''### 성능 결함 수정 재개점 — 2026-11-02

- 위219/779/변환5/정확정상3/두엔딩/8184초 연속검사는 **모두 종료·통과**했어요. 옛 resume 명령으로 처음부터 반복하지 않아요. 현재 남은 항목은 단독 실제 성능이에요.
- shipping0fce의 실제 탐색58.36FPS, 활성 논스톱10.73FPS를 확인해 이 상태를 완료로 처리하지 않았어요. UI PNG압축약50ms가 첫 병목이고, 전체 UI snapshot 복제·전송도 측정했어요.
- 후보는 frozen node snapshot 재사용, 반복 asset 준비 생략, 무손실 premultiplied RGBA전송+Zstd, 고정 DIB 재사용이에요. 원작프로세스 접근0, 해상도/효과/게임타이머/정답/원고변경0. 픽셀15case C++/WIC일치, snapshot162case, 실제widget반복 raster4frame 정확일치 통과. 현재까지는 격리된 QA package 후보이며 shipping원본 적용 전이에요.
- 상세시도/현재다음일은 `Game/Saved/native-performance-work-20261102.json`, 마지막 FPS실행의 live PID/완료 report를 먼저 확인해요. 후보 도구 `Game/tools/*candidate*`, 컴파일은 기존 narrow shipping CPP base를 쓰며 working CPP의 타인DPI/fit수정은 보존해요.

'''
if '### 성능 결함 수정 재개점 — 2026-11-02' not in s:s=s.replace(marker,text+marker)
p.write_text(s,encoding='utf8');print(json.dumps({'attempts':len(attempts),'status':result['status']}))
