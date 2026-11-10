"""Record this art revision without overwriting a newer parallel code build."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];W=R/'Game/Saved/sculpted-environment-20261103';O=R/'art/space_v4/facility_architecture_v2'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=load(W/'build-result.json');base=load(W/'rebuilt-baseline-build.json');bank=load(R/'art/space_v4/rebuild_v1/manifest.json')
assert build['baseline']==base['output']
visual=load(R/'Game/Saved/native-generated-surfaces-1793708532324/report.json');perf=load(R/'Game/Saved/native-performance-1793708631816/report.json');identity=load(W/'final-package-identity.json');printed=load(R/'art/space_v4/facility_identity_v1/static-verification.json')
assert visual['ok']and len(visual['rows'])==8 and visual['unchangedPackedResources']and visual['sourceSaveUnchanged']
assert perf['ok']and perf['measurementValid']and perf['renderSurface']['width']==3840 and perf['renderSurface']['height']==2160 and perf['seconds']>=30
assert not perf['gameModule']and not perf['gameContentOverrides']and not perf['profile']
assert all(x['build']==build['id']for x in [visual,perf,identity])and identity['engineAndNativeModuleIdentical']and identity['storyAndOtherContentIdentical']
assert printed['ok']and printed['environmentManifestSHA256']==sha(R/'art/space_v4/rebuild_v1/manifest.json')
current=load(R/'Game/build-result.json');published=False
if current['id']==base['id']:
    (W/'architecture-before-publish-build.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    current.update(build);(R/'Game/build-result.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf8');published=True
elif current['id']==build['id']:published=True
summary={'ok':True,'build':build,'publishedAsCurrent':published,'baselinePreserved':base['id'],'environmentManifestSHA256':sha(R/'art/space_v4/rebuild_v1/manifest.json'),'purposeBuildings':30,'sharedHotelWing':1,'actualRoofGeometryProof':'roof-closure-proof.json','sourceUnlabelledReviews':['review/'+n+'-unlabelled.png'for n in ['clinic','reading_room','maintenance_workshop','dining_room']],'nativeReport':'Game/Saved/native-generated-surfaces-1793708532324/report.json','nativeViewCount':8,'fpsReport':'Game/Saved/native-performance-1793708631816/report.json','measuredOutdoorFPS':perf['fps'],'measurementSeconds':perf['seconds'],'renderSurface':perf['renderSurface'],'nativeAndStoryIdentity':'Game/Saved/sculpted-environment-20261103/final-package-identity.json','architectureSourceSHA256':sha(R/'art/space_v4/rebuild_v1/sources/park-rebuilt.blend'),'scope':'Architecture and identity art revision. Neutral Blender label-hidden renders reviewed separately from actual native fixture views. No normal full-game-route, all-PC, all-room or all-mode performance acceptance.'}
(O/'final-review.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'ok':True,'build':build['id'],'published':published,'fps':perf['fps']}))
