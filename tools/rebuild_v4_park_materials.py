import bpy,json,sys,shutil,hashlib
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R/'tools'));import park_material_finish as M
O=R/'art/space_v4/park_levels_v1';W=R/'Game/Saved/park-materials-20261104';backup=R/'삭제 대기/공원재질5_이전_de2_20261104';backup.mkdir(exist_ok=True)
for n in ['parks-authoring.blend','manifest.json','raw-manifest.json']:
 if not(backup/n).exists():shutil.copy2(O/n,backup/n)
bpy.ops.wm.open_mainfile(filepath=str((backup if '--from-backup'in sys.argv else O)/'parks-authoring.blend'))
def enable(c):
 c.exclude=False
 for x in c.children:enable(x)
enable(bpy.context.view_layer.layer_collection)
raw=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'));rows=[]
only=next((set(a.split('=',1)[1].split(','))for a in sys.argv if a.startswith('--only=')),None)
previous=json.loads((W/'source.json').read_text(encoding='utf8'))if(W/'source.json').exists()else None
if '--export-only'not in sys.argv:
 for row in raw['levels']:
  if only and row['id']not in only:continue
  root=bpy.data.objects['park_level_'+row['id']];r=M.apply(root,row['id']);rows.append(r);print('MATERIALS_APPLIED',row['id'],r['materialCopies'],r['uvFacesRepaired'],flush=True)
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True)
 if only:
  rows.extend(r for r in previous['rows']if r['theme']not in only)
 (W/'source.json').write_text(json.dumps({'ok':True,'before':str(backup),'sourceSHA256':hashlib.sha256((O/'parks-authoring.blend').read_bytes()).hexdigest(),'rows':rows,'palette':M.PALETTES,'scope':'Six-park material/UV finish only; no shape/topology/navigation/story edit.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
import build_v4_rebuilt_environment as A;A.O=O
# Material/UV edits start from an already frozen triangulated master. Running
# the generic BMesh weld again changes tiny split normals; preserve topology.
A.freeze=lambda objects:None
for row in raw['levels']:
 ident=row['id']
 if only and ident not in only:continue
 # Separate source collections can overlap physically in the authoring file.
 for c in bpy.context.view_layer.layer_collection.children:
  if c.name.startswith('THEME_SOURCE_'):c.exclude=c.name!='THEME_SOURCE_'+ident
 root=bpy.data.objects['park_level_'+ident];extra={k:v for k,v in row['raw'].items()if k not in ['file','runtime','triangles','meshParts','rawBytes']};extra['surfaceMaterialRevision']=5
 tri=row['raw']['triangles'];row['raw']=A.export([root,*root.children_recursive],ident+'.glb','Assets/Art/park_levels/'+ident+'.glb',extra);assert row['raw']['triangles']==tri
 (O/'raw-manifest.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('MATERIAL_CHUNK_CHECKPOINT',ident,flush=True)
# Export freeze may normalize the mesh serialization; preserve the actual source.
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True)
p=W/'source.json';d=json.loads(p.read_text(encoding='utf8'));d['sourceSHA256']=hashlib.sha256((O/'parks-authoring.blend').read_bytes()).hexdigest();p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('ALL_MATERIAL_SOURCES_EXPORTED',flush=True)
