"""Render the actual editable rebuilt exterior, no separate concept art."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/rebuild_v1';P=R/'Game/Saved/sculpted-environment-20261103'
bpy.ops.wm.open_mainfile(filepath=str(O/'sources/park-rebuilt.blend'));scene=bpy.context.scene;world=bpy.data.objects['park_exterior_level'];visible=set([world,*world.children_recursive])
for o in scene.objects:
    if o.type in ['LIGHT','CAMERA']:o.hide_render=True
    elif o.type=='MESH':o.hide_render=o not in visible
scene.world=bpy.data.worlds.new('rebuilt_review_day');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.56,.72,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
bpy.ops.object.light_add(type='SUN',location=(0,0,30));sun=bpy.context.object;sun.data.energy=2;sun.data.angle=.12;sun.rotation_euler=(.4,-.5,-.5)
bpy.ops.object.camera_add(location=(24,-24,17));cam=bpy.context.object;cam.rotation_euler=(Vector((0,5,2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=28;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.transparent_max_bounces=32;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(P/'rebuilt-exterior-source-review.png');bpy.ops.render.render(write_still=True)
print('REBUILT_EXTERIOR_SOURCE_RENDERED',flush=True)
