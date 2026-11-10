"""Offline render of the existing own screening-room screen_frame mesh only."""
import bpy,sys,json,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'ui/v4/vote_tv_source';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
model=ROOT/'art/space_v4/sculpted_v1/screening_room.glb';bpy.ops.import_scene.gltf(filepath=str(model))
frame=next(o for o in bpy.data.objects if o.name=='screen_frame')
for o in list(bpy.data.objects):
 if o!=frame:bpy.data.objects.remove(o,do_unlink=True)
frame.location=(0,0,0);frame.rotation_euler=(0,0,0);frame.scale=(11.52/11,1,6.4/5.4)
# Repaint the existing own-world metal surface, not a new vector UI frame and
# not pixels copied from the original game's television/world photograph.
mat=bpy.data.materials.new('Own TV metal surface');mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.35,.37,.4,1);p.inputs['Metallic'].default_value=.62;p.inputs['Roughness'].default_value=.31;frame.data.materials.clear();frame.data.materials.append(mat)
for loc,power,size in [((-3,-7,3),750,5),((4,-6,-2),500,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(math.pi/2,0,0)
bpy.ops.object.camera_add(location=(0,-20,0));cam=bpy.context.object;cam.rotation_euler=(math.pi/2,0,0);cam.data.type='ORTHO';cam.data.ortho_scale=12.8;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=2560;scene.render.resolution_y=1440;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='Standard';scene.render.filepath=str(OUT/'own_tv_model.png');bpy.ops.render.render(write_still=True)
(OUT/'own_tv_model.json').write_text(json.dumps({'ownWorldAdapter':True,'originalGamePixels':False,'sourceModel':model.relative_to(ROOT).as_posix(),'sourceSHA256':hashlib.sha256(model.read_bytes()).hexdigest(),'mesh':'screen_frame','adaptation':'Existing own screen_frame mesh resized/repainted as television enclosure. The original UI black64 tile is a mask, not a silver bezel.'},indent=2),encoding='utf-8')
