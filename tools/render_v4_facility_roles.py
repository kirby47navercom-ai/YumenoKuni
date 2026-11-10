"""Render actual source buildings with identical neutral lighting and scale."""
import bpy,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/facility_architecture_v2/review';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'art/space_v4/rebuild_v1/sources/park-rebuilt.blend'));s=bpy.context.scene
s.world=bpy.data.worlds.new('neutral_architectural_review');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.52,.62,.75,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.1;sun.data.angle=.09;sun.rotation_euler=(.45,-.35,-.3)
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.lens=34;s.camera=cam
bpy.ops.mesh.primitive_plane_add(size=600,location=(0,0,-.14));floor=bpy.context.object
s.render.engine='CYCLES';s.cycles.samples=10;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=800;s.render.resolution_y=600;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.render.image_settings.file_format='PNG'
ids=next((v.split('=',1)[1].split(',')for v in sys.argv if v.startswith('--only=')),['clinic','maintenance_workshop','mirror_workbay','reading_room','performance_stage','ticket_booth','cold_store','electrical_room'])
for ident in ids:
    root=bpy.data.objects['facade_'+ident];building=next(o for o in root.children if o.get('architectureVersion')==2);w,d,h=building['nominalSize'];shown=set([root,*root.children_recursive,sun,cam,floor])
    for o in s.objects:o.hide_render=o not in shown or ('--without-labels'in sys.argv and (o.name.startswith('printed_facility_')or o.name.startswith('formed_sign_backing')))
    target=root.matrix_world@Vector((0,0,h*.45));cam.location=root.matrix_world@Vector((w*.85,-d/2-max(10,w*.95),h+5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();floor.location.z=root.matrix_world.translation.z-.14
    s.render.filepath=str(O/(ident+('-unlabelled'if '--without-labels'in sys.argv else'')+'.png'));bpy.ops.render.render(write_still=True)
    print('ROLE_SOURCE_RENDERED',ident,flush=True)
