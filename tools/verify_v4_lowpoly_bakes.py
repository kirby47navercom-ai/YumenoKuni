"""Independent geometry, source identity, atlas and node preservation gate."""
from pathlib import Path
import sys,json,hashlib,io
import numpy as np
from PIL import Image
from v4_lowpoly_glb import read,array,keys,triangles
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/lowpoly_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
partial=[v.split('=',1)[1] for v in sys.argv[1:] if v.startswith('--partial=')]
published='--published'in sys.argv
if partial:rows=[json.loads((O/(name+'.json')).read_text()) for name in partial]
else:
 manifest=json.loads((O/'manifest.json').read_text());rows=manifest['assets']
 assert manifest['complete'] and len(rows)==len(json.loads((R/'art/space_v4/materials_v2/manifest.json').read_text())['assets'])
 assert manifest['sourceManifestSHA256']==sha(R/'art/space_v4/materials_v2/manifest.json')
results=[]
for row in rows:
 source=R/row['source'];dest=R/row['file'];assert sha(source)==row['sourceSHA256'];assert sha(dest)==row['sha256'];assert dest.stat().st_size<64*1024*1024
 if published:assert sha(R/'Game'/row['runtime'])==row['sha256']
 h,hb=read(source);l,lb=read(dest);names={n['name']:n for n in l['nodes']};hk=keys(h,hb);lk=keys(l,lb);changed={c['node']:c for c in row['changedMeshes']};extents=[]
 for old in h['nodes']:
  new=names[old['name']]
  for k in set(old)|set(new):
   if k not in ['mesh','children']:assert old.get(k)==new.get(k),(row['runtime'],old['name'],k)
  assert new.get('children',[])[:len(old.get('children',[]))]==old.get('children',[])
  if 'mesh'not in old:continue
  if old['name']not in changed:assert hk[old['mesh']]==lk[new['mesh']],(row['runtime'],old['name'],'unchanged mesh changed')
  else:
   changed_mesh=l['meshes'][new['mesh']]
   for p in changed_mesh['primitives']:
    assert all(k in p['attributes'] for k in ['POSITION','NORMAL','TANGENT','TEXCOORD_0'])
    mat=l['materials'][p['material']];assert 'normalTexture'in mat and 'baseColorTexture'in mat['pbrMetallicRoughness'] and 'metallicRoughnessTexture'in mat['pbrMetallicRoughness']
    pos=array(l,lb,p['attributes']['POSITION']);idx=array(l,lb,p['indices']).reshape(-1,3)
    assert np.isfinite(pos).all();assert idx.max()<len(pos)
    area=np.linalg.norm(np.cross(pos[idx[:,1]]-pos[idx[:,0]],pos[idx[:,2]]-pos[idx[:,0]]),axis=1)
    assert (area>1e-12).all(),(row['runtime'],old['name'],'degenerate')
   oldpos=np.concatenate([array(h,hb,p['attributes']['POSITION']) for p in h['meshes'][old['mesh']]['primitives']]);newpos=np.concatenate([array(l,lb,p['attributes']['POSITION']) for p in changed_mesh['primitives']])
   # Optical children retain their original bounds separately.
   for child in new.get('children',[])[len(old.get('children',[])):]:
    cn=l['nodes'][child]
    if 'mesh'in cn:newpos=np.concatenate([newpos]+[array(l,lb,p['attributes']['POSITION']) for p in l['meshes'][cn['mesh']]['primitives']])
   error=float(max(np.max(abs(oldpos.min(0)-newpos.min(0))),np.max(abs(oldpos.max(0)-newpos.max(0)))))
   tolerance=max(.003,float(np.linalg.norm(oldpos.max(0)-oldpos.min(0)))*.015)
   assert error<=tolerance,(row['runtime'],old['name'],'silhouette bounds',error,tolerance)
   extents.append(error)
 before=sum(triangles(h,n['mesh']) for n in h['nodes'] if 'mesh'in n);after=sum(triangles(l,n['mesh']) for n in l['nodes'] if 'mesh'in n)
 assert before==row['beforeTriangles'] and after==row['afterTriangles'] and after<=before
 assert len(l['nodes'])>=len(h['nodes'])
 results.append({'runtime':row['runtime'],'beforeTriangles':before,'afterTriangles':after,'changedMeshes':len(changed),'maxLocalBoundsError':max(extents,default=0),'originalNodeTransformsUnchanged':True,'unchangedMeshesAndMaterialsExact':True})
 print('LP_VERIFY',row['runtime'],before,after,flush=True)
proof={'ok':True,'models':len(results),'beforeTriangles':sum(r['beforeTriangles'] for r in results),'afterTriangles':sum(r['afterTriangles'] for r in results),'rows':results,'published':published,'scope':'Independent source/output SHA, fixed node transforms, exact unchanged mesh/material content, changed mesh topology/PBR/normal/tangent/UV, local bounds. Native appearance and performance are separate evidence.'}
if not partial:
 proof['manifestSHA256']=sha(O/'manifest.json');(R/'Game/Saved/sculpted-environment-20261103/lowpoly-static-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
else:(R/'Game/Saved/sculpted-environment-20261103/lowpoly-partial-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({k:v for k,v in proof.items() if k not in ['rows','scope']}))
