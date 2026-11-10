"""Close the empty descending stairwell around its exact existing 32 walk heights."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
import v4_rebuilt_environment_kit as K
import v4_facility_architecture as F
O=A.O;p=O/'room-assembly.json';m=json.loads(p.read_text());row=next(a for a in m['assets']if a['runtime'].endswith('/lower_stairway.glb'))
A.clean();bpy.ops.import_scene.gltf(filepath=str(R/row['file']));root=bpy.data.objects['lower_stairway'];A.erase(root.children_recursive)
w=json.loads((R/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf8'))['spaces']['lower_stairway'];steps=w['walk_surfaces'];profile=[]
for x,near,xx,far,z in steps:profile.extend([(-far,z),(-near,z)])
profile+=[(profile[-1][0],profile[-1][1]-.22),(profile[0][0],profile[0][1]-.22)]
body=K.section('continuous_descending_stair_flight',profile,1.8,'stone',root)
for side in [-1,1]:
    # One continuous structural side wall and a supported rail, not 32 boxes.
    low=[(-5.60,-.22),*[(y,z-.22)for y,z in profile[:-2]],(5.98,steps[-1][4]-.22)];outline=[*low,(low[-1][0],3.4),(low[0][0],3.4)]
    sidewall=K.section('continuous_stairwell_side_wall',outline,.16,'plaster',root);sidewall.location.x=side*.98
    pts=[(side*.82,(a+b)/2,z+.88)for a,b,z in [(profile[i*2][0],profile[i*2+1][0],steps[i][4])for i in range(len(steps))]];K.tube('supported_descending_handrail',pts,[.03]*len(pts),'brass',root,8)
    for i in range(0,len(steps),4):
        a,b=profile[2*i][0],profile[2*i+1][0];z=steps[i][4];K.tube('descending_rail_post',[(side*.82,(a+b)/2,z),(side*.82,(a+b)/2,z+.88)],[.022]*2,'iron',root,6)
    for y in [-3.4,-1,1.4,3.5]:
        lamp=K.sconce();lamp.parent=root;lamp.location=(side*.87,y,2.5);lamp.rotation_euler.z=-side*math.pi/2
K.rounded_solid('stairwell_overhead_slab',2.12,11.6,.16,'plaster',root,.006,(0,.19,3.48))
K.rounded_solid('upper_stair_landing',1.8,.96,.16,'paving',root,.01,(0,-5.12,-.08))
K.rounded_solid('lower_stair_landing',1.8,1.67,.16,'paving',root,.01,(0,5.155,steps[-1][4]-.08))
z=steps[-1][4];F.prism('closed_lower_stairwell_end',[(-2,z),(-.75,z),(-.75,z+2.52),(.75,z+2.52),(.75,z),(2,z),(2,3.4),(-2,3.4)],.16,'plaster',root,5.9)
K.frame_ring('lower_landing_door_reveal',1.66,2.72,.08,.20,'wood',root,(0,5.78,z+1.26),inner_size=(1.5,2.52))
# Preserve the actual metadata walk heights; use mesh rays to check each tread.
bpy.context.view_layer.update();tree=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());hits=[]
for x,near,xx,far,z in steps:
    hit=tree.ray_cast(Vector((0,-(near+far)/2,z+1)),Vector((0,0,-1)),2)[0];assert hit is not None and abs(hit.z-z)<1e-5;hits.append({'runtimeZ':(near+far)/2,'height':z})
sign=next(o for o in bpy.data.objects if o.name.startswith('facility_lower_stairway')and o.type=='EMPTY');sign.location=(.87,-3.8,2.65);sign.rotation_euler.z=-math.pi/2
A.freeze(list(bpy.data.objects));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'sources/lower_stairway.blend'),compress=True)
new=A.export(list(bpy.data.objects),Path(row['file']).name,row['runtime'],{k:v for k,v in row.items()if k not in ['file','runtime','triangles','meshParts','rawBytes']});m['assets']=[new if a['runtime']==new['runtime']else a for a in m['assets']];p.write_text(json.dumps(m,indent=2)+'\n')
(R/'Game/Saved/sculpted-environment-20261103/stairwell-tread-proof.json').write_text(json.dumps({'ok':True,'actualMeshRayTests':hits,'worldMetadataChanged':False},indent=2)+'\n');print('STAIRWELL_REBUILT_EXACT_TREADS',len(hits))
