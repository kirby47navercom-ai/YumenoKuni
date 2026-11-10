"""Material bindings/geometry preservation and seating-direction regression gate."""
from pathlib import Path
import json,hashlib,sys,math
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from build_v4_surface_materials import read,arr,rotation,family
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/materials_v2';manifest=json.loads((O/'manifest.json').read_text(encoding='utf8'));copies=json.loads((R/'art/space_v4/runtime_v1/copy_manifest.json').read_text(encoding='utf8'));report=[]
for row in manifest['assets']:
 path=R/row['file'];raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];assert len(raw)<64*1024*1024
 published=R/'Game'/row['runtime'];assert published.read_bytes()==raw,row['runtime']
 if '/explore3d/' in row['runtime']:assert next(r['from'] for r in copies if r['to']==row['runtime'])==row['file']
 j,b=read(path);normals=0;families=set()
 for material in j.get('materials',[]):
  key=material.get('extras',{}).get('generatedSurfaceFamily')
  if key:
   families.add(key);assert 'baseColorTexture'in material['pbrMetallicRoughness'];assert 'metallicRoughnessTexture'in material['pbrMetallicRoughness'];assert 'normalTexture'in material
  if 'normalTexture'in material:normals+=1
 for mesh in j['meshes']:
  for p in mesh['primitives']:
   if 'normalTexture'in j['materials'][p['material']]:assert all(k in p['attributes'] for k in ['NORMAL','TEXCOORD_0'])
   key=j['materials'][p['material']].get('extras',{}).get('generatedSurfaceFamily');name=mesh.get('name','')
   if 'screen_surface' in name:assert key=='linen','Projection screen must not inherit wall plaster'
   if 'blanket' in name:assert key in ['velvet','linen'],'Bed covers need textile response, not painted metal'
 if row.get('geometryAccessorsUnchanged') is not None:
  before,bb=read(R/row['source']);assert len(before['accessors'])==len(j['accessors'])
  for i in range(len(j['accessors'])):assert np.array_equal(arr(before,bb,i),arr(j,b,i)),(row['runtime'],i)
  allowed={r['node'] for r in row['seatCorrections']};newnodes={n.get('name'):n for n in j['nodes']}
  for old,new in zip(before['nodes'],j['nodes']):
   assert old.get('translation')==new.get('translation') and old.get('scale')==new.get('scale')
   if old.get('name') not in allowed:assert old==new
  for c in row['seatCorrections']:
   n=newnodes[c['node']];forward=rotation(n['rotation'])@np.array([0,0,1.]);assert float(forward[[0,2]]@np.array(c['desiredDirectionXZ']))>.9999
 else:assert row['positionNormalIndexBytesUnchanged'] and len(j['materials'])==len(j['meshes'][0]['primitives'])==1
 report.append({'runtime':row['runtime'],'bytes':len(raw),'normalMappedMaterials':normals,'families':sorted(families),'seatCorrections':len(row['seatCorrections'])})
for m in json.loads((O/'generation-manifest.json').read_text(encoding='utf8'))['materials']:
 assert hashlib.sha256((R/m['master']).read_bytes()).hexdigest()==m['sha256']
result={'ok':True,'manifestSHA256':hashlib.sha256((O/'manifest.json').read_bytes()).hexdigest(),'models':len(report),'seatCorrections':sum(r['seatCorrections'] for r in report),'exteriorJoinedBenchCorrections':len(json.loads((R/'art/space_v4/sculpted_v1/exterior-manifest.json').read_text()).get('seatCorrections',[])),'rows':report,'scope':'Source/master hashes, published model bytes, PBR/UV contracts, exact environment accessor preservation, only declared root yaw changes; separate native visual/performance evidence required.'}
(R/'Game/Saved/sculpted-environment-20261103/surface-static-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ['rows','scope']}))
