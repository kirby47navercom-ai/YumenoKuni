"""Use actual authored facade height instead of the draft eight-metre envelope."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/park_levels_v1';bpy.ops.wm.open_mainfile(filepath=str(O/'parks-authoring.blend'));m=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'));world=json.loads((R/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf8'));proof=[]
for a in m['levels']:
    for room,(x,y)in a['placedFacilities'].items():
        src=bpy.data.objects.get('facade_'+room)
        if not src or room not in world['instances']:continue
        vertices=[o.matrix_world@Vector(c)for o in src.children_recursive if o.type=='MESH'for c in o.bound_box]
        if not vertices:continue
        height=max(v.z for v in vertices)-src.matrix_world.translation.z;s=world['spaces'][world['instances'][room]['space']];b=s['bounds'];rect=[x+b[0],-y+b[1],x+b[2],-y+b[3]]
        for c in a['collision']:
            if c[:4]!=rect or c[4:]!=[0,8]:continue
            c[5]=round(height,5);proof.append({'level':a['id'],'room':room,'height':c[5],'actualAuthoredFacade':src.name})
(O/'raw-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(O/'facility-height-proof.json').write_text(json.dumps({'rows':proof,'renderGeometryChanged':False},indent=2)+'\n');print('PARK_FACADE_HEIGHTS',len(proof),flush=True)
