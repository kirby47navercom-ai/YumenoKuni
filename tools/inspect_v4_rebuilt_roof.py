import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'art/space_v4/rebuild_v1/sources/park-rebuilt.blend'))
world=bpy.data.objects['park_exterior_level'];out=[]
for o in world.children_recursive:
    if o.type!='MESH' or 'roof'not in o.name:continue
    p=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(v[i]for v in p)for i in range(3)];hi=[max(v[i]for v in p)for i in range(3)]
    if lo[0]>10 or hi[0]<-15 or hi[1]<20 or lo[1]>90:continue
    out.append({'name':o.name,'parent':o.parent.name if o.parent else None,'lo':lo,'hi':hi,'downwardFaces':sum(f.normal.z<-.5 for f in o.data.polygons),'negativeScale':o.matrix_world.determinant()<0})
(R/'Game/Saved/sculpted-environment-20261103/roof-inspection.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
