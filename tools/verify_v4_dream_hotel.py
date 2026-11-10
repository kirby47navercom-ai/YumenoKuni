"""Prove one structural hotel replacement; native rendering remains separate."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from v4_lowpoly_glb import read
O=R/'art/space_v4/park_levels_v1';H=O/'dream_hotel_v4';W=R/'Game/Saved/park-levels-20261104/hotel-architecture'
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
integration=load(H/'integration.json');geometry=load(H/'geometry.json');renders=load(H/'render-review.json')
source=sha(H/'hotel-source.blend');assert integration['ok']and geometry['ok']
assert source==integration['sourceSHA256']==renders['sourceSHA256']
assert not renders['aestheticReviewPending']and set(renders['reviewedViews'])=={'front','side','rear','quarter','window-close','roof-close'}
assert len(renders['actualBlenderRenders'])==6
for r in renders['actualBlenderRenders']:assert Path(r['image']).stat().st_size>10000
assert geometry['triangles']==integration['newHotelTriangles']<85000
assert all(r['nonManifoldEdges']==0 for r in geometry['meshChecks'])
assert geometry['actualWallSection']=={'pierSolid':True,'upperWindowCut':True,'entryCut':True,'nominalThickness':.32}
before=load(Path(integration['previousBank']));bank=load(O/'manifest.json')
raw=load(O/'raw-manifest.json');oldRaw=load(Path(integration['previousBank']).with_name('raw-manifest.json'))
unchanged=[]
materialProofPath=R/'Game/Saved/park-materials-20261104/static.json'
materialProof=load(materialProofPath)if any(r['raw'].get('surfaceMaterialRevision')==5 for r in raw['levels'])else None
if materialProof:assert materialProof['ok']and materialProof['geometryManifestSHA256']==sha(O/'manifest.json')and len(materialProof['rows'])==6
for a in bank['assets']:
    prior=next(p for p in before['assets']if p['id']==a['id'])
    r=next(p for p in raw['levels']if p['id']==a['id']);old=next(p for p in oldRaw['levels']if p['id']==a['id'])
    assert {k:v for k,v in r.items()if k!='raw'}=={k:v for k,v in old.items()if k!='raw'}
    assert sha(R/a['file'])==a['sha256']
    if a['id']!='fairytale':
        if a!=prior:assert materialProof and next(r for r in materialProof['rows']if r['id']==a['id'])['geometryExactAt1e5']
        unchanged.append(a['id']);continue
    assert a['triangles']==integration['currentFairytaleTriangles']==prior['triangles']-integration['removedHotelTriangles']+geometry['triangles']
    assert r['raw']['hotelArchitectureRevision']==4 and a['bytes']<64*1024*1024
    j,b=read(R/a['file']);materials=[m for m in j['materials']if m['name'].startswith('architecture_hotel_')];assert len(materials)==7
    opaque=[m for m in materials if m['name']!='architecture_hotel_glass']
    assert len(opaque)==6 and all(m.get('pbrMetallicRoughness',{}).get('baseColorTexture')is not None for m in opaque)
    assert all('normalTexture'in m for m in opaque)
    glass=next(m for m in materials if m['name']=='architecture_hotel_glass')
    assert glass['pbrMetallicRoughness']['roughnessFactor']<.25 and 'normalTexture'not in glass
assert len(unchanged)==5
result={'ok':True,'geometryManifestSHA256':sha(O/'manifest.json'),'sourceSHA256':source,'triangles':geometry['triangles'],'closedMeshObjects':geometry['closedMeshObjects'],'unchangedGeometryDistricts':unchanged,'materialRevision':5 if materialProof else None,'navigationAndCaseMetadataExact':True,'actualBlenderRenders':renders['actualBlenderRenders'],'renderSHA256':{r['view']:sha(Path(r['image']))for r in renders['actualBlenderRenders']},'scope':'Actual closed geometry, cut apertures, six rendered/model-reviewed views and one-asset replacement. Native rendering, entry and frame pacing require separate actual player proofs.'}
(W/'static.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items()if k not in ['actualBlenderRenders','renderSHA256']},ensure_ascii=False))
