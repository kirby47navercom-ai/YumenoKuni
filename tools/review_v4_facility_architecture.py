"""Inspect and render the actual authored Blender buildings before packaging."""
import bpy,sys,math,json,bmesh,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/facility_architecture_v2'
bpy.ops.wm.open_mainfile(filepath=str(R/'art/space_v4/rebuild_v1/sources/park-rebuilt.blend'));scene=bpy.context.scene;graph=bpy.context.evaluated_depsgraph_get();rows=[]
for root in [o for o in scene.objects if o.get('architectureVersion')==2]:
    if root['roofStyle']=='open_structure':
        rows.append({'id':root['facilityIdentity'],'roof':'intentionally_open_boundary','features':list(root['purposeFeatures'])});continue
    w,d,h=root['nominalSize'];roof=next((o for o in root.children if o.name.startswith('continuous_')and o.name.endswith('_roof')),None)
    if roof is None:roof=next(o for o in root.children if o.name.startswith('continuous_')and '_roof.'in o.name)
    endwalls=[o for o in root.children if o.name.startswith('sealed_')and'end_wall'in o.name];assert len(endwalls)==2
    bm=bmesh.new();bm.from_mesh(roof.data);assert all(len(e.link_faces)==2 for e in bm.edges),(root.name,'roof has an open mesh edge');bm.free()
    roofBVH=BVHTree.FromObject(roof,graph);rays=[]
    for side in [-1,1]:
        wall=min(endwalls,key=lambda o:abs(sum(v.co.y for v in o.data.vertices)/len(o.data.vertices)-side*(d/2-.11)));wallBVH=BVHTree.FromObject(wall,graph)
        for x in [-w*.4,0,w*.4]:
            hit=roofBVH.ray_cast(Vector((x,side*(d/2-.05),h-.30)),Vector((0,0,1)),10)[0];assert hit is not None
            if hit.z<=h+.03:continue
            z=(h+hit.z)/2;loc,normal,index,dist=wallBVH.ray_cast(Vector((x,side*(d/2+.5),z)),Vector((0,-side,0)),1)
            assert loc is not None,(root.name,side,x,z,'open gable');rays.append({'side':side,'x':x,'z':z,'hitDistance':dist})
    rows.append({'id':root['facilityIdentity'],'roof':root['roofStyle'],'actualGableRayTests':rays,'features':list(root['purposeFeatures'])})
(O/'roof-closure-proof.json').write_text(json.dumps({'ok':True,'sourceBlendSHA256':hashlib.sha256((R/'art/space_v4/rebuild_v1/sources/park-rebuilt.blend').read_bytes()).hexdigest(),'buildings':rows,'scope':'Actual Blender mesh BVH rays through the previously empty gable and into the real roof, plus watertight roof-edge checks. Not metadata-only.'},indent=2)+'\n')
if '--no-render'in sys.argv:print('ACTUAL_ROOF_CLOSURE_CHECKED',len(rows),flush=True);raise SystemExit(0)
pair=[bpy.data.objects['facade_'+s]for s in ['dining_room','kitchen']];visible=set(o for r in pair for o in [r,*r.children_recursive])
for o in scene.objects:o.hide_render=o not in visible
bpy.ops.mesh.primitive_plane_add(size=200,location=(-30,24,-.12));floor=bpy.context.object;floor.data.materials.append(bpy.data.materials.new('review_ground'));floor.data.materials[0].diffuse_color=(.19,.22,.18,1)
scene.world=bpy.data.worlds.new('architecture_review_ambient');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.56,.66,.78,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.object.light_add(type='SUN',location=(-30,0,20));sun=bpy.context.object;sun.data.energy=2.2;sun.data.angle=.08;sun.rotation_euler=(math.radians(28),math.radians(-25),math.radians(-25))
bpy.ops.object.camera_add(location=(-15,3,9));cam=bpy.context.object;cam.rotation_euler=(Vector((-31,21,1.9))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=32;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=20;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(O/'food-pair-source-review.png');bpy.ops.render.render(write_still=True)
print('ARCHITECTURE_ROOF_AND_SOURCE_REVIEW_READY',len(rows),flush=True)
