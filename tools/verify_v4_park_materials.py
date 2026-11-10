"""Current six-park material pass, mesh identity and all catalogued groups."""
import json,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from park_material_geometry import fingerprint
from v4_lowpoly_glb import read
O=R/'art/space_v4/park_levels_v1';W=R/'Game/Saved/park-materials-20261104';load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=load(W/'before.json');source=load(W/'source.json');bank=load(O/'manifest.json');raw=load(O/'raw-manifest.json');priorRaw=load(Path(source['before'])/'raw-manifest.json');catalog=load(R/'Game/Saved/building-catalog-20261104/catalog.json');rows=[]
assert source['sourceSHA256']==sha(O/'parks-authoring.blend')
checked=set(n for r in source['rows']for n in r['checkedObjects'])
for c in catalog['rows']:assert set(c['meshNames'])<=checked,('Unchecked exterior group',c['id'])
for a in bank['assets']:
 ident=a['id'];old=next(p for p in before['bank']['assets']if p['id']==ident);current=fingerprint(R/a['file']);prior=before['rows'][ident]
 assert current['triangles']==prior['triangles']and current['triangleCornerPositionNormalHash1e5']==prior['triangleCornerPositionNormalHash1e5'],('Geometry changed',ident,current,prior)
 row=next(r for r in raw['levels']if r['id']==ident);p=next(r for r in priorRaw['levels']if r['id']==ident)
 assert {k:v for k,v in row.items()if k!='raw'}=={k:v for k,v in p.items()if k!='raw'},ident
 assert row['raw']['surfaceMaterialRevision']==5 and a['bytes']<64*1024*1024
 j,b=read(R/a['file']);used={p['material']for m in j['meshes']for p in m['primitives']};normals=sum('normalTexture'in j['materials'][i]for i in used);rough=sum('metallicRoughnessTexture'in j['materials'][i].get('pbrMetallicRoughness',{})for i in used)
 assert normals>=int(len(used)*.65),(ident,normals,len(used))
 for i in used:
  m=j['materials'][i];p=m.get('pbrMetallicRoughness',{});assert m['name']and len(p.get('baseColorFactor',[1,1,1,1]))==4
  if m.get('extras',{}).get('surfaceMaterialRevision')==5:
   assert m.get('extras',{}).get('finish5Role')
   assert 'baseColorTexture'in p and 'normalTexture'in m,(ident,m['name'])
   if m['extras']['finish5Role']not in ['wood','cloth']:assert 'metallicRoughnessTexture'in p,(ident,'roughness texture not restored',m['name'])
 if ident=='fairytale':
  from_before=next(x for x in before['bank']['assets']if x['id']==ident)
  # Source hotel material factors are intentionally preserved; only surrounding
  # older facade palettes and UV defects were corrected.
  hotel=[m for m in j['materials']if m['name'].startswith('architecture_hotel_')];assert len(hotel)==7
 rows.append({'id':ident,'geometryExactAt1e5':True,'navigationAndCaseMetadataExact':True,'beforeUV':prior['degenerateUVTriangles'],'afterUV':current['degenerateUVTriangles'],'triangles':a['triangles'],'usedMaterials':len(used),'normalMapped':normals,'roughnessMapped':rough,'bytes':a['bytes']})
result={'ok':True,'geometryManifestSHA256':sha(O/'manifest.json'),'sourceSHA256':source['sourceSHA256'],'rows':rows,'catalogGroupsChecked':len(catalog['rows']),'geometryUnchangedDistricts':[r['id']for r in rows],'scope':'All65 exterior/structure groups covered by source material/UV pass. Canonical quantized triangle position/normal identity and authored navigation/case data preserved. Actual renders/runtime remain separate; this is not architectural reconstruction completion.'}
(W/'static.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(result,ensure_ascii=False))
