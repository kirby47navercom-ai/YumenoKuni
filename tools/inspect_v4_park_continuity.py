import bpy,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];W=R/'Game/Saved/facility-form-20261104';W.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'art/space_v4/rebuild_v1/sources/park-rebuilt.blend'));bpy.context.view_layer.update();rows=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not any(k in o.name.lower()for k in ['terrain','walkway','path','boundary','fence','road']):continue
    p=[o.matrix_world@Vector(v)for v in o.bound_box];rows.append({'name':o.name,'lo':[min(v[i]for v in p)for i in range(3)],'hi':[max(v[i]for v in p)for i in range(3)],'parent':o.parent.name if o.parent else None})
(W/'old-ground-path-bounds.json').write_text(json.dumps(rows,indent=2)+'\n');print('CONTINUITY_OBJECTS',len(rows))
