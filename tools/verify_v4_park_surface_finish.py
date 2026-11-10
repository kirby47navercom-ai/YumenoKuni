"""Check decorative-only changes, embedded original pixels and bounded detail."""
import json,hashlib,io,sys
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from v4_lowpoly_glb import read,array
O=R/'art/space_v4/park_levels_v1';W=R/'Game/Saved/park-levels-20261104'
old=json.loads((R/'삭제 대기/테마공원_디테일_이전_d2_20261104/raw-manifest.json').read_text(encoding='utf8'))
oldAssets=json.loads((R/'삭제 대기/테마공원_디테일_이전_d2_20261104/manifest.json').read_text(encoding='utf8'))
raw=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'));bankBytes=(O/'manifest.json').read_bytes();bank=json.loads(bankBytes)
proof=json.loads((O/'theme_park_v2/authoring.json').read_text(encoding='utf8'))
materialProof=json.loads((R/'Game/Saved/park-materials-20261104/static.json').read_text(encoding='utf8'))if any(r['raw'].get('surfaceMaterialRevision')==5 for r in raw['levels'])else None
if materialProof:assert materialProof['ok']and materialProof['geometryManifestSHA256']==hashlib.sha256(bankBytes).hexdigest()and len(materialProof['rows'])==6
themes=['fairytale','carnival','mirrors','clockwork','starlight'];rows=[]
def pixels(im):
    im=im.convert('RGBA');return im.size,hashlib.sha256(im.tobytes()).hexdigest()
generated={name:pixels(Image.open(O/'detail_v3'/name))for name in ['ornament-trims.png','painted-enamel.png','tent-canvas.png']}
for row in raw['levels']:
    ident=row['id'];before=next(r for r in old['levels']if r['id']==ident)
    assert {k:v for k,v in row.items()if k!='raw'}=={k:v for k,v in before.items()if k!='raw'},ident+' gameplay metadata changed'
    asset=next(a for a in bank['assets']if a['id']==ident);prior=next(a for a in oldAssets['assets']if a['id']==ident)
    if ident=='perimeter':
        if asset['sha256']!=prior['sha256']:assert materialProof and next(r for r in materialProof['rows']if r['id']==ident)['geometryExactAt1e5']
        continue
    assert row['raw']['surfaceDetailRevision']==3
    details=proof['districts'][ident]['surfaceDetail'];assert details['features']and details['navigationAndCaseGeometryUnchanged']
    j,b=read(R/asset['file']);images=[]
    for im in j['images']:
        view=j['bufferViews'][im['bufferView']];off=view.get('byteOffset',0);images.append(pixels(Image.open(io.BytesIO(b[off:off+view['byteLength']]))))
    for name in ['ornament-trims.png','painted-enamel.png']+(['tent-canvas.png']if ident=='carnival'else[]):assert generated[name]in images,(ident,name)
    ornament={i for i,m in enumerate(j['materials'])if m.get('name','').startswith('theme_v2_ornament_print')};assert ornament
    count=0;theme=themes.index(ident)
    for mesh in j['meshes']:
        for p in mesh['primitives']:
            if p['material']not in ornament:continue
            uv=array(j,b,p['attributes']['TEXCOORD_0']);assert np.isfinite(uv).all()
            assert uv[:,1].min()>=theme/5-.0001 and uv[:,1].max()<=(theme+1)/5+.0001,(ident,uv[:,1].min(),uv[:,1].max())
            count+=len(uv)
    architectureTriangles=architectureMaterials=0
    if row['raw'].get('hotelArchitectureRevision')==4:
        hotel=json.loads((O/'dream_hotel_v4/integration.json').read_text(encoding='utf8'))
        geometry=json.loads((O/'dream_hotel_v4/geometry.json').read_text(encoding='utf8'))
        assert ident=='fairytale'and hotel['ok']and geometry['ok']
        assert hotel['newHotelTriangles']==geometry['triangles']<85000
        assert hotel['sourceSHA256']==hashlib.sha256((O/'dream_hotel_v4/hotel-source.blend').read_bytes()).hexdigest()
        assert asset['triangles']==hotel['currentFairytaleTriangles']==hotel['previousFairytaleTriangles']-hotel['removedHotelTriangles']+hotel['newHotelTriangles']
        architectureTriangles=hotel['newHotelTriangles']-hotel['removedHotelTriangles']
        architectureMaterials=sum(m.get('name','').startswith('architecture_hotel_')for m in j['materials'])
        assert architectureMaterials==7
    assert count>0 and asset['triangles']-prior['triangles']-architectureTriangles<75000 and asset['materialPrimitives']-prior['materialPrimitives']-architectureMaterials<=12
    assert asset['bytes']<64*1024*1024
    rows.append({'id':ident,'navigationAndCaseMetadataExact':True,'embeddedGeneratedPixelsExact':True,'ornamentUVBand':theme,'ornamentVertices':count,'trianglesAdded':asset['triangles']-prior['triangles'],'separatelyVerifiedArchitectureTriangles':architectureTriangles,'separatelyVerifiedArchitectureMaterials':architectureMaterials,'materialPrimitivesAdded':asset['materialPrimitives']-prior['materialPrimitives'],'bytes':asset['bytes'],'features':details['features']})
result={'ok':True,'geometryManifestSHA256':hashlib.sha256(bankBytes).hexdigest(),'rows':rows,'unchangedConnectorExact':not bool(materialProof),'unchangedConnectorGeometry':True,'materialRevision':5 if materialProof else None,'scope':'Surface finish and fitted decorative geometry only; pixel/UV/metadata/budget evidence, not aesthetic approval.'}
(W/'detail-surface-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
