"""Correct planar road winding after the engine-XZ to Blender-XY reflection."""
import bpy,bmesh,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
O=R/'art/space_v4/park_levels_v1';bpy.ops.wm.open_mainfile(filepath=str(O/'parks-authoring.blend'));m=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'));changed=[]
for row in m['levels']:
    root=bpy.data.objects[row['sourceObject']];fixed=[]
    for o in root.children_recursive:
        if o.type!='MESH'or not o.name.startswith('one_connected_public_promenade'):continue
        if sum(p.normal.z*p.area for p in o.data.polygons)>=0:continue
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update();fixed.append(o.name)
    if not fixed:continue
    A.O=O;row['raw']=A.export([root,*root.children_recursive],row['id']+'.glb','Assets/Art/park_levels/'+row['id']+'.glb',{'parkDistrict':row['id']});changed.append({'id':row['id'],'fixed':fixed})
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True);(O/'raw-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(O/'paving-repair.json').write_text(json.dumps({'rows':changed},indent=2)+'\n');print('PARK_PAVING_UPWARD',changed,flush=True)
