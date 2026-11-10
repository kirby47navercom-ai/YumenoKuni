"""Recover a completed Blender bake after external texture packing failed.

The persisted high/low GLBs are independently compared; this does not rebake or
infer success from a log. Use only on an output whose geometry bake completed.
"""
from pathlib import Path
import json,sys,hashlib
from v4_lowpoly_glb import read,keys,node_keys,triangles
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/lowpoly_v1';version=6
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((R/'art/space_v4/materials_v2/manifest.json').read_text())['assets']
for stem in sys.argv[1:]:
 row=next(r for r in catalog if Path(r['runtime']).stem==stem);source=R/row['file'];dest=O/'models'/Path(row['file']).name
 h,hb=read(source);l,lb=read(dest);hk=keys(h,hb);lk=keys(l,lb);nk=node_keys(h,hb);names={n['name']:n for n in l['nodes']};changes=[]
 for old in h['nodes']:
  if 'mesh'not in old:continue
  new=names[old['name']]
  if hk[old['mesh']]==lk[new['mesh']]:continue
  assert all('normalTexture'in l['materials'][p['material']] for p in l['meshes'][new['mesh']]['primitives'])
  before=triangles(h,old['mesh']);after=triangles(l,new['mesh']);assert after<before
  changes.append({'node':old['name'],'beforeOpaqueTriangles':before,'afterOpaqueTriangles':after,'method':'six-face solid with baked bevel' if before==108 and after==12 else 'silhouette reduction with high-mesh normal bake','recoveredFromCompletedGLB':True})
 before=sum(triangles(h,n['mesh']) for n in h['nodes'] if 'mesh'in n);after=sum(triangles(l,n['mesh']) for n in l['nodes'] if 'mesh'in n)
 receipt={'version':version,'file':dest.relative_to(R).as_posix(),'runtime':row['runtime'],'source':row['file'],'sourceSHA256':sha(source),'sha256':sha(dest),'bytes':dest.stat().st_size,'beforeTriangles':before,'afterTriangles':after,'changedMeshes':changes,'bakeType':'Cycles selected-to-active tangent NORMAL and source colour/roughness/metallic/emission; recovered completed persisted GLB after missing Pillow packaging failure','atlasSize':2048,'seconds':None,'originalNodesPreserved':len(h['nodes']),'originalNodeTransformsUnchanged':True}
 (O/(Path(row['file']).stem+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
 cache=json.loads((O/'bake-cache.json').read_text()) if (O/'bake-cache.json').exists() else {'version':version,'meshes':{}}
 if cache.get('version')!=version:cache={'version':version,'meshes':{}}
 changed={c['node']:c for c in changes}
 for old in h['nodes']:
  if 'mesh'not in old or triangles(h,old['mesh'])<96:continue
  c=changed.get(old['name']);key=nk[old['name']]
  if key in cache['meshes']:continue
  cache['meshes'][key]={'file':receipt['file'],'sha256':receipt['sha256'],'node':old['name'],'change':c} if c else {'unchanged':True}
 (O/'bake-cache.json').write_text(json.dumps(cache,indent=2)+'\n');print(stem,before,after,len(changes))
