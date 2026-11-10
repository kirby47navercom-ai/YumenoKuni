"""Same-geometry Blender review of the whole-environment rebuild foundations."""
import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_rebuilt_environment_kit as K
O=R/'art/space_v4/rebuild_v1';P=R/'Game/Saved/sculpted-environment-20261103';(O/'prototypes').mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);K.setup_materials();scene=bpy.context.scene
items=[('building_mansard',K.house(5,4,3.2,'mansard'),(-4,2,0)),('landscape_tree',K.tree(11),(2.3,2.3,0)),('storage_cabinet',K.storage_cabinet(),(5,-.3,0)),('detail_office_desk',K.office_desk(),(1.4,-2.4,0))]
rows=[]
for name,root,position in items:
    root.location=(0,0,0);bpy.ops.object.select_all(action='DESELECT')
    for o in [root,*root.children_recursive]:o.select_set(True)
    bpy.context.view_layer.objects.active=root;file=O/'prototypes'/(name+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(file),export_format='GLB',use_selection=True,export_apply=True,export_tangents=True,export_extras=True)
    rows.append({'name':name,'file':file.relative_to(R).as_posix(),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'bytes':file.stat().st_size,'meshParts':sum(o.type=='MESH'for o in root.children_recursive),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons)for o in root.children_recursive if o.type=='MESH')})
    root.location=position
bpy.ops.mesh.primitive_plane_add(size=200);bpy.context.object.name='review_ground';bpy.context.object.data.materials.append(K.M['paving'])
scene.world=bpy.data.worlds.new('neutral_review_world');scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.35,.42,.52,1);scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.6
for pos,energy,size in [((1,-6,10),2200,8),((-8,4,8),1600,6)]:
    bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(10,-15,8));camera=bpy.context.object;camera.rotation_euler=(Vector((0,1,2))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=42;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.render.threads_mode='FIXED';scene.render.threads=6
scene.cycles.transparent_max_bounces=32
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.render.filepath=str(P/'rebuilt-foundations.png');bpy.ops.wm.save_as_mainfile(filepath=str(O/'whole-environment-foundations.blend'),compress=True);bpy.ops.render.render(write_still=True)
(O/'prototype-manifest.json').write_text(json.dumps({'completeEnvironment':False,'scope':'First authored house/tree/casework/drawer foundations; not yet runtime replacements or full environment completion.','assets':rows},indent=2)+'\n')
print('REBUILD_FOUNDATIONS_READY',flush=True)
