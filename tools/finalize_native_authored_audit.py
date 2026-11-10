"""Validate actual case identities and reviewed stability before acceptance."""
import hashlib, json, statistics, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SAVED=ROOT/'Game/Saved'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=read(ROOT/'Game/build-result.json'); runs=read(SAVED/'native-whole-game-runs-20261101.json')
tasks=read(ROOT/'data/v4_story/native_tasks.json')['tasks']; assert len(tasks)==219
def healthy(runtime):
    assert runtime['webview'] is False and runtime['frames']>0
    assert not runtime['audio']['errors']
    shader=runtime['renderer'].get('shaderPreparation',{})
    assert not shader.get('error') and not shader.get('pending')
    assert not shader.get('queue',{}).get('failed',0)
def case_source(row):
    p=Path(row['source']).resolve(); assert p.is_relative_to(SAVED.resolve())
    if p not in hashes:hashes[p]=sha(p)
    assert hashes[p]==row['sourceSHA256'],str(p)
hashes={}
pdir=SAVED/runs['tasks']; p=read(pdir/'report.json'); progress=read(pdir/'progress.json')
assert p['ok'] and p['build']==build['id'] and p['completeAuthoredCoverage'] and progress['closed']
healthy(p['runtime']); good={r['taskId']:r for r in p['results'] if r.get('ok')}
assert set(good)==set(tasks)
for key,row in good.items():
    assert row['actions']>0 and row['outcome']['taskId']==key and row['outcome']['target']
    case_source(row['checkpoint'])
forks=[key for key,t in tasks.items() if t.get('outcomes')]; assert len(forks)==5
altProgress=read(SAVED/runs['alternate']/'progress.json')
alt={r['taskId']:r for r in altProgress['results'] if r.get('ok') and r['outcome']['judgment']=='lie'}
assert set(alt)==set(forks)
for key in forks:
    for row,label in ((good[key],'A'),(alt[key],'B')):
        expected=tasks[key]['outcomes'][label]
        assert row['outcome']['judgment']==expected['judgment']
        assert row['outcome']['target']==expected['to'] and row['outcome']['sets']==expected.get('sets',{})
        assert row['actions']>0
        case_source(row['checkpoint'])
cdir=SAVED/runs['choices']; c=read(cdir/'report.json')
assert c['ok'] and c['complete'] and c['build']==build['id'] and read(cdir/'progress.json')['closed']
healthy(c['runtime'])
fixture=read(SAVED/'native-coverage-fixtures-latest.json')
menu=[json.loads(line) for line in (ROOT/fixture['work']/'menu-fixtures.jsonl').read_text(encoding='utf8').splitlines() if line]
expected={r['node']+'#'+str(r['option']):r for r in menu}; actual={r['key']:r for r in c['results'] if r.get('ok')}
assert len(expected)==779 and set(actual)==set(expected)
for key,row in actual.items():
    assert row['resultNode'] in expected[key]['trail'] and row['setsStructurallyVerified']==expected[key]['sets']
    case_source(row['fixture'])
canonical=read(SAVED/runs['canonical']/'report.json'); healthy(canonical['runtime'])
assert canonical['ok'] and canonical['build']==build['id']
assert canonical['results'][0]['checkpoint']['sourceSHA256']=='d43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7'
assert not canonical['results'][0]['checkpoint']['fixture']
ending=read(SAVED/runs['ending']/'report.json'); assert ending['ok'] and ending['build']==build['id'] and len(ending['results'])==2
for row in ending['results']:
    assert row['ok'] and row['normalLoaded']['coins']==999 and row['loaded']['coins']==500
    assert row['normalLoaded']['mode']==row['loaded']['mode']=='credits' and row['walletProbe']['fixture']
    healthy(row['runtime']); case_source(row)
identity=read(SAVED/('source-identity-'+build['id'].rsplit('-',1)[1]+'.json'))
assert identity['status']=='PASS' and identity['build']==build['id'] and identity['normalCheckpointUnchanged']
assert identity['allSourceFilesExact']==56 and identity['allGeneratedDataJSONExact']==345
session=Path(progress['session']).resolve(); assert session.is_relative_to(pdir.resolve())
samples=[json.loads(line) for line in (session/'telemetry.jsonl').read_text(encoding='utf8').splitlines() if line]
seconds=(samples[-1]['time']-samples[0]['time'])/1000; assert seconds>=7200
peak=max(r['memory']['rss'] for r in samples); last=samples[-1]['memory']['rss']
assert '--reviewed-memory' in sys.argv,'Review the memory trace; duration alone is not acceptance'
assert last<peak*.95,'A new or flat trace needs its own memory review criteria'
windows=[]; end=samples[-1]['time']
for low,high in ((45,60),(30,45),(15,30),(0,15)):
    rows=[r for r in samples if end-high*60000<=r['time']<end-low*60000]
    if rows:windows.append({'fromMinutesAgo':high,'toMinutesAgo':low,'samples':len(rows),'medianRSS':statistics.median(r['memory']['rss'] for r in rows),'medianExternal':statistics.median(r['memory']['external'] for r in rows)})
stable={'ok':True,'build':build['id'],'continuousSeconds':seconds,'session':session.relative_to(ROOT).as_posix(),'runtimeReport':(session/'runtime.json').relative_to(ROOT).as_posix(),'frames':p['runtime']['frames'],'peakLiveRSS':peak,'lastLiveRSS':last,'memoryWindows':windows,'lastGPUTextureBytes':p['runtime']['renderer']['textureResourceBytes'],'lastGPUTextureCount':p['runtime']['renderer']['memory']['textures'],'nativeAudioErrors':p['runtime']['audio']['errors'],'nativeExit':0,'review':'More than2hours and all15 mode families with many actual input/scene/UI transitions. Live resident memory ended below its earlier peak; final GPU resource counts and asset-cache growth are recorded. No universal leak-free, device or total-memory-budget claim.','reviewedAt':datetime.now(timezone.utc).isoformat()}
write(SAVED/'native-stability-acceptance-20261101.json',stable)
result={'build':build['id'],'status':'authored-native-functional-and-stability-verified-performance-pending','wholeGameAcceptance':False,'tasks':len(good),'tasksByKind':dict(Counter(r['kind'] for r in good.values())),'choiceEdges':len(actual),'normalAlternativeOutcomes':len(forks),'transformedAlternativeOutcomes':len(alt),'endingSaves':2,'canonicalNormalSave':True,'stability':'Game/Saved/native-stability-acceptance-20261101.json','sourceIdentity':'Game/Saved/source-identity-'+build['id'].rsplit('-',1)[1]+'.json','reports':{k:'Game/Saved/'+runs[k]+'/report.json' for k in ('tasks','choices','alternate','ending','canonical')},'scope':'Actual native authored interactions from explicit preconditions, checked against current source/data. Structural upstream task injection is separate. Human story timing and other-device acceptance are not inferred.','updatedAt':datetime.now(timezone.utc).isoformat()}
if '--stability-only' not in sys.argv:
    a=read(SAVED/runs['alternate']/'report.json'); assert a['ok'] and a['build']==build['id']; healthy(a['runtime'])
    assert '--reviewed-performance' in sys.argv
    performances=[]
    for key in ('worldPerformance','trialPerformance'):
        perf=read(SAVED/runs[key]/'report.json'); assert perf['ok'] and perf['build']==build['id'] and perf['seconds']>=58
        healthy(perf['runtime']); assert perf['fps']>0
        performances.append({'case':perf['case'],'fps':perf['fps'],'seconds':perf['seconds'],'report':'Game/Saved/'+runs[key]+'/report.json'})
    result.update(status='current-native-compatibility-verification-complete',wholeGameAcceptance=True,performance=performances,acceptanceScope='Current authored-game native compatibility on this PC. All219 tasks,779 option edges, five additional transformed routes, exact normal restore, both ending restores, repeated paid-ending checks and reviewed continuous stability. Single-scene performance observations retain their limits.')
write(SAVED/'native-authored-coverage-final-20261101.json',result)
print(json.dumps({'status':result['status'],'tasks':len(good),'choices':len(actual),'alternate':len(alt),'continuousSeconds':seconds,'peakLiveRSS':peak,'lastLiveRSS':last,'gpuBytes':stable['lastGPUTextureBytes']}))
