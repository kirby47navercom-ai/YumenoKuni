import bpy,sys,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'art/space_v4/rebuild_v1/sources/park-rebuilt.blend'));scene=bpy.context.scene;visible=set(bpy.data.objects['park_exterior_level'].children_recursive)
for o in scene.objects:
    if o.type=='MESH':o.hide_set(o not in visible)
bpy.ops.object.camera_add(location=(24,-24,17));cam=bpy.context.object;cam.rotation_euler=(Vector((0,5,2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=28;scene.camera=cam;scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
f=cam.data.view_frame(scene=scene);out=[]
for x,y in [(440,480),(420,493),(430,510),(880,675),(520,488),(265,376)]:
    u=x/1600;v=1-y/1000;direction=cam.matrix_world.to_3x3()@((f[3]*(1-u)+f[0]*u)*v+(f[2]*(1-u)+f[1]*u)*(1-v));direction.normalize();ok,p,n,face,o,m=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),cam.location,direction)
    if ok:out.append({'pixel':[x,y],'object':o.name,'point':list(p),'normal':list(n),'material':o.data.materials[o.data.polygons[face].material_index].name})
(R/'Game/Saved/sculpted-environment-20261103/ground-ray-inspection.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
