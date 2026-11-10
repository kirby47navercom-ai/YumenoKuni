"""Historical functional UI evidence; FPS measurements do not accept whole-game performance."""
import hashlib,json,statistics,sys
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parents[1];saved=root/'Game/Saved';folder=root/'docs/analysis/v3_rebuild';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));write=lambda p,r:p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
build=read(root/'Game/build-result.json');suffix=build['id'].rsplit('-',1)[1];baseline_id='2026-11-01T13-56-29-441Z-0fce033a';base_file=saved/'native-authored-coverage-final-20261101.json';base=read(base_file)
assert base['build']==baseline_id and base['tasks']==219 and base['choiceEdges']==779 and base['transformedAlternativeOutcomes']==5 and base['canonicalNormalSave']
stable=read(saved/'native-stability-acceptance-20261101.json');assert stable['ok'] and stable['build']==baseline_id and stable['continuousSeconds']>=7200
delta=read(saved/('native-ui-package-delta-'+suffix+'.json'));assert delta['ok'] and delta['build']==build['id'] and delta['baselineBuild']==baseline_id and delta['gameCppDataArtAudioAllUnchanged']
identity=read(saved/('source-identity-'+suffix+'.json'));assert identity['status']=='PASS' and identity['normalCheckpointUnchanged'] and identity['allSourceFilesExact']==56 and identity['allGeneratedDataJSONExact']==345
def healthy(r):
 assert r['webview'] is False and r['frames']>0 and not r['audio']['errors']
 s=r['renderer'].get('shaderPreparation',{});assert not s.get('error') and not s.get('pending') and not s.get('queue',{}).get('failed',0)
focused_pointer=read(saved/'native-ui-focused-latest.json');focus_file=Path(focused_pointer['work'])/'report.json';focus=read(focus_file);assert focus['ok'] and focus['build']==build['id']
plan=read(saved/'native-ui-focused-plan-20261102.json');proofs={key:read(Path(row['report'])) for key,row in focus['results'].items()};assert set(proofs)=={'tasks','transformed','menus','canonical','scrollResize','endings'}
restoration=read(saved/'native-ui-wheel-package-delta-20261102.json');assert restoration['ok'] and restoration['build']==build['id'] and restoration['allOtherPackageBytesExact'] and restoration['sourceOnlyRestoresApprovedColdBranches']
for key,p in proofs.items():
 assert p['ok']
 if p['build']!=build['id']:
  row=focus['results'][key];assert key in {'tasks','transformed','menus'} and row['validatedBuild']==p['build']==restoration['baselineBuild'] and Path(row['inheritedThrough']).resolve()==(saved/'native-ui-wheel-package-delta-20261102.json').resolve()
tasks=proofs['tasks'];healthy(tasks['runtime']);good={r['taskId']:r for r in tasks['results'] if r.get('ok')};assert set(good)==set(plan['taskIds']);assert len({r['kind'] for r in good.values()})==15
canonical_proof=proofs['canonical'];assert canonical_proof['build']==build['id'];healthy(canonical_proof['runtime']);canonical=next(r for r in canonical_proof['results'] if r.get('ok') and r['taskId']=='T3-NS-A11');assert canonical['checkpoint']['sourceSHA256']=='d43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7' and not canonical['checkpoint']['fixture']
for key,row in good.items():assert row['actions']>0 and row['outcome']['taskId']==key and row['outcome']['target']
transformed=proofs['transformed'];healthy(transformed['runtime']);alt=[r for r in transformed['results'] if r.get('ok') and r['taskId']==plan['transformedTask'] and r['outcome']['judgment']=='lie'];assert len(alt)==1 and alt[0]['actions']>0
menus=proofs['menus'];healthy(menus['runtime']);menu_good={r['key']:r for r in menus['results'] if r.get('ok')};assert set(menu_good)==set(plan['choiceKeys']) and len(menu_good)==10
scroll=proofs['scrollResize'];assert scroll['shippingEngine'] and scroll['realWin32Wheel'] and scroll['dragOffset']>scroll['scrollOffset']>0 and len(scroll['resizeProof'])==3 and not scroll['audioErrors']
for r in scroll['resizeProof']:assert r['nativePixelsUploaded'] and r['client']==r['requested'] and r['resources'][0]<=r['beforeResources'][0]+4
end=proofs['endings'];assert len(end['results'])==2
for r in end['results']:assert r['ok'] and r['normalLoaded']['coins']==999 and r['loaded']['coins']==500 and r['normalLoaded']['mode']==r['loaded']['mode']=='credits';healthy(r['runtime'])
cpp=read(saved/'native-ui-frame-candidate/cpp-check.json');assert cpp['ok'] and cpp['tests']==20 and cpp['exactWICPBGRA']
unit_sources={'snapshot':'native-widget-snapshot-1793555784959','raster':'native-widget-paint-1793555784956'}
for key,name in unit_sources.items():
 u=read(saved/name/'report.json');assert u['ok'];package=saved/name/'package/game.hbpack.json';m=read(package if package.exists() else saved/name/'package-manifest.json');owner='prototype/ui-runtime.js' if key=='snapshot' else 'tools/native-widget-layer.mjs';current=Path(build['output'])/owner;assert hashlib.sha256(current.read_bytes()).hexdigest()==next(f['sha256'] for f in m['files'] if f['path']==owner)
packet_candidates=[p for p in sorted(saved.glob('native-packet-exit-*/report.json')) if read(p).get('build')==build['id']];assert packet_candidates
packet_file=packet_candidates[-1];packet=read(packet_file);assert packet['ok'] and packet['shippingEngine'] and len(packet['rows'])==1 and packet['rows'][0]['code']==1 and packet['rows'][0]['packetBudgetExceptionLogged']
performances=[]
for case in ['active-nonstop','world']:
 candidates=[(p,read(p)) for p in sorted(saved.glob('native-performance-*/report.json')) if read(p).get('build')==build['id'] and read(p).get('case')==case];assert candidates
 file,p=candidates[-1];owned=read(file.parent/'owned-package.json');assert owned['source']==build['output'] and all(r['name']=='Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json' for r in owned['alterations'])
 assert p['ok'] and p['seconds']>=58 and p['fps']>0;healthy(p['runtime']);performances.append({'case':case,'fps':p['fps'],'seconds':p['seconds'],'report':str(file.relative_to(root))})
progress=read(Path(focus['results']['tasks']['report']).with_name('progress.json'));assert progress['closed'];session=Path(progress['session']);samples=[json.loads(line) for line in (session/'telemetry.jsonl').read_text(encoding='utf8').splitlines() if line];assert len(samples)>30
assert '--reviewed-ui-memory' in sys.argv,'Read the current UI telemetry and native GDI resize trace before acceptance'
memory={'session':str(session.relative_to(root)),'seconds':(samples[-1]['time']-samples[0]['time'])/1000,'samples':len(samples),'peakLiveRSS':max(r['memory']['rss'] for r in samples),'lastLiveRSS':samples[-1]['memory']['rss'],'lastNativeGPUTextureBytes':tasks['runtime']['renderer']['textureResourceBytes'],'nativeGDIResizeTrace':focus['results']['scrollResize']['report'],'scope':'Current UI observation across15 actual task families; not relabelled as a second2hour run. Prior2hour core/logic proof is inherited only through exact source/data/native-module and lossless UI proof.'}
result={'build':build['id'],'executable':build['executable'],'status':'functional-ui-evidence-performance-not-accepted','compatibilityAcceptance':True,'wholeGameAcceptance':False,'performanceAcceptance':False,'shippingAcceptance':False,'signedReleaseReady':False,'baselineBuild':baseline_id,'inheritedAuthoredCoverage':{'tasks':219,'choiceEdges':779,'normalAlternativeOutcomes':5,'transformedAlternativeOutcomes':5,'endingSaves':2,'canonicalNormalSave':True,'proof':'Game/Saved/native-authored-coverage-final-20261101.json','reports':base['reports']},'inheritanceProof':'Game/Saved/native-ui-package-delta-'+suffix+'.json','currentFocused':{'report':str(focus_file.relative_to(root)),'taskFamilies':15,'transformed':1,'choiceEdges':10,'longestMenuEligible':13,'resizeCases':3,'endingSaves':2,'reports':{k:str(Path(v['report']).relative_to(root)) for k,v in focus['results'].items()}},'currentSourceIdentity':'Game/Saved/source-identity-'+suffix+'.json','currentUIUnits':{'nativePixelCases':20,'stateSnapshotCases':162,'rasterFrames':4,'baseline':'0fce033a, not the modified engine originals'},'performance':performances,'inheritedStability':{'build':baseline_id,'seconds':stable['continuousSeconds'],'proof':'Game/Saved/native-stability-acceptance-20261101.json'},'currentUIObservation':memory,'remainingProductFailures':[],'limits':['Current authored-game native compatibility on this PC; hidden Win32 input and declared precondition fixtures. Not every possible action order or other-device certification.','Trial scene observed about31FPS; stable60FPS is not asserted.','Human5hour chapter timing and universal literary/art perfection are not inferred.','Release signing remains unavailable because the human has no certificate; current executable is development/unsigned.'],'legacyFlowGuard':'verify-flow.mjs intentionally rejects native; actual Win32 proof replaces its WebView/CDP scope, guard unchanged.','installedVersionsAndUserProfileModified':False,'stagingCommitPush':False,'updatedAt':datetime.now(timezone.utc).isoformat()}
result['currentFocused']['componentBuilds']={k:p['build'] for k,p in proofs.items()}
result['currentFocused']['inheritanceProof']='Game/Saved/native-ui-wheel-package-delta-20261102.json'
result['currentFocused']['currentCanonicalRestore']=True
result['currentUIObservation']['validatedBuild']=tasks['build']
result['currentUIObservation']['inheritedThrough']='Game/Saved/native-ui-wheel-package-delta-20261102.json'
result['protocolFailureExitProof']=str(packet_file.relative_to(root))
result['closedRebuildRegression']={'wheel':'Actual wheel/drag and three resize cases passed after restoring the missing approved handler.','reader':'Actual packaged host exits1 on the injected128MiB protocol line overflow.','sourceReceipt':'Game/Saved/native-ui-wheel-restoration-20261102/receipt.json'}
retention_file=sorted(saved.glob('native-qa-retention-*.json'))[-1];retention=read(retention_file);assert not retention['dryRun'] and retention['deleted']==0 and retention['physicalBytesReclaimed']==0
result['cleanup']={'receipt':str(retention_file.relative_to(root)),'closedOwnedPackagesMoved':sum(bool(x['moved']) for x in retention['records']),'deleted':0,'physicalBytesReclaimed':0,'scope':'Reports, captures, saves and package hash inventories remain. Move-only to the project-root 삭제 대기 folder; shared hardlinks are not claimed as disk reclaimed.'}
write(saved/'native-ui-compatibility-final-20261102.json',result);write(folder/'native_ui_shipping_audit_20261102.json',result)
print(json.dumps({'status':result['status'],'build':build['id'],'focusFamilies':15,'inheritedTasks':219,'inheritedChoices':779,'memory':memory,'performance':performances}))
