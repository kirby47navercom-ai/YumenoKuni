"""Close the whole current 3D revision; preserve newer parallel build metadata."""
from pathlib import Path
import json,hashlib,sys
from PIL import Image
R=Path(__file__).resolve().parents[1];W=R/'Game/Saved/sculpted-environment-20261103'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
args={x.split('=',1)[0]:x.split('=',1)[1]for x in sys.argv[1:]if '='in x}
build=load(W/'build-result.json');base=load(W/'rebuilt-baseline-build.json');coverage=load(W/'whole-3d-package-proof.json');identity=load(W/'final-package-identity.json');inventory=load(W/'whole-3d-inventory.json');static=load(W/'rebuilt-static-verification.json')
assert coverage['ok']and coverage['build']==build['id']and coverage['uniqueRoomViewpoints']==54
assert identity['ok']and identity['build']==build['id']and identity['engineAndNativeModuleIdentical']and identity['storyAndOtherContentIdentical']
assert inventory['ok']and inventory['models']==72 and inventory['rebuiltCommon']==61 and inventory['rebuiltLateSets']==6
assert static['ok']and static['manifestSHA256']==sha(R/'art/space_v4/rebuild_v1/manifest.json')
printed=load(R/'art/space_v4/facility_identity_v1/static-verification.json');assert printed['ok']and printed['environmentManifestSHA256']==static['manifestSHA256']
roof=load(R/'art/space_v4/facility_architecture_v2/roof-closure-proof.json');assert roof['ok']and roof['sourceBlendSHA256']==sha(R/'art/space_v4/rebuild_v1/sources/park-rebuilt.blend')
stairs=load(W/'stairwell-tread-proof.json');assert stairs['ok']and len(stairs['actualMeshRayTests'])==32
proofs=[]
for name in ['--outdoor','--court']:
    p=R/args[name];d=load(p);assert d['ok']and d['measurementValid']and d['build']==build['id']and d['seconds']>=30
    assert not d['profile']and not d['gameModule']and not d['gameContentOverrides'];assert d['renderSurface']['width']==3840 and d['renderSurface']['height']==2160
    proofs.append({'mode':d['mode'],'path':p.relative_to(R).as_posix(),'build':d['build'],'fps':d['fps'],'seconds':d['seconds'],'sourceFixture':d['sourceFixture'],'width':3840,'height':2160,'performanceAcceptance':False})
gen=R/'art/space_v4/rebuilt_dedicated_v2/panel-generation.json';g=load(gen);asset=R/g['projectFile'];g.update(sha256=sha(asset),actualDimensions=list(Image.open(asset).size),mode='built-in image_gen');save(gen,g)
current_path=R/'Game/build-result.json';previous_raw=current_path.read_bytes();current=json.loads(previous_raw);published=False
if current['id']==base['id']:
    save(W/'whole-3d-before-publish-build.json',current);current.update(build)
    assert current_path.read_bytes()==previous_raw,'Parallel build pointer advanced; do not roll it back'
    temp=current_path.with_suffix('.whole-3d.tmp');save(temp,current);temp.replace(current_path);published=True
elif current['id']==build['id']:published=True
else:raise RuntimeError('Newer parallel build is current; rebase art before publishing')
report={'ok':True,'scope':'Current 3D art revision and its evidence, not entire-game completion or every camera angle/PC performance acceptance.','build':build,'publishedAsCurrent':published,'baseline':base['id'],'models':72,'rebuiltCommon':61,'rebuiltLateSets':6,'retainedSpecialModels':[r['runtime']for r in inventory['rows']if r.get('retentionReason')],'purposeBuildings':30,'sharedHotelWing':1,'trees':22,'physicalSigns':46,'pixelFaceDoors':16,'actualNativeViewpoints':54,'packageProof':'Game/Saved/sculpted-environment-20261103/whole-3d-package-proof.json','packageIdentity':'Game/Saved/sculpted-environment-20261103/final-package-identity.json','sourceManifestSHA256':static['manifestSHA256'],'commonBankTriangles':static['decodedTriangles'],'commonBankBytes':static['totalBytes'],'stairMeshRayTests':32,'protectedNamedStateTransformsVerified':True,'nativeReports':['Game/Saved/native-generated-surfaces-1793711443601/report.json','Game/Saved/native-generated-surfaces-1793713272535/report.json','Game/Saved/native-generated-surfaces-1793713945646/report.json','Game/Saved/native-generated-surfaces-1793714781895/report.json','Game/Saved/native-generated-surfaces-1793714971055/report.json'],'visualCorrections':['six omitted dedicated rooms','ticket room and overlapping exterior both share actual window aperture','staircase side walls meet exact 32 treads and landings','transparent gondola cabin','electrical cabinet texture with separate real switches','continuous stage curtain, formed maintenance tools and glass rack','no invented books in toy shop','chairs face their own tables and curved lounge seating'],'drawCallsSameViewBeforeAfter':{'hotel_indoor_garden':[285,9],'hotel_rest_lounge':[212,12],'hotel_washroom':[140,10],'souvenir_shop':[292,75]},'performance':proofs,'liveMirrorReflectionsImplemented':False,'mirrorScope':'Silver surface material; no new live character/environment reflection renderer.','engineModified':False,'storyModified':False,'imageGeneration':g,'cleanupReceipt':'Game/Saved/sculpted-environment-20261103/whole-3d-cleanup-receipt.json'}
save(W/'whole-3d-final-review.json',report)
print(json.dumps({'ok':True,'build':build['id'],'published':published,'models':72,'nativeViewpoints':54,'fps':[p['fps']for p in proofs]}))
