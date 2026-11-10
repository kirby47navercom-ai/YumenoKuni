"""Render the actual Blender exteriors without any nameplates, at common scale."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/facility_forms_v3';m=json.loads((O/'manifest.json').read_text(encoding='utf8'))
(O/'review').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(O/'park-form-source.blend'));scene=bpy.context.scene
for o in list(scene.objects):o.hide_render=True
bpy.ops.mesh.primitive_plane_add(size=250,location=(0,0,-.10));ground=bpy.context.object;ground.name='review_ground';mat=bpy.data.materials.new('review_ground');mat.diffuse_color=(.26,.29,.27,1);ground.data.materials.append(mat)
scene.world=bpy.data.worlds.new('form_review_ambient');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.64,.72,.79,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.object.light_add(type='SUN',location=(0,0,30));sun=bpy.context.object;sun.data.energy=2.1;sun.data.angle=.10;sun.rotation_euler=(math.radians(28),math.radians(-24),math.radians(-25))
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=10;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=960;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
only=next((set(a.split('=',1)[1].split(','))for a in sys.argv if a.startswith('--only=')),None);rows=[]
for row in m['rows']:
    ident=row['id']
    if only and ident not in only:continue
    root=bpy.data.objects[row['sourceObject']];selected=[root,*root.children_recursive];hidden=[]
    for o in selected:o.hide_render=False
    for o in selected:
        if o.get('facilityLabel'):
            for child in [o,*o.children_recursive]:child.hide_render=True;hidden.append(child.name)
    p=root.matrix_world.translation;w,d,h=row['size'];ground.location=(p.x,p.y,-.10)
    cam.location=(p.x+w*.85,p.y-d*.95-8,max(6,h+3));target=Vector((p.x,p.y-.6,h*.43));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=max(w*1.45,d*1.30,h*1.95)
    file=O/'review'/(ident+'-unlabelled.png');scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
    rows.append({'id':ident,'image':file.relative_to(R).as_posix(),'nameplatesHidden':hidden,'actualSourceObject':row['sourceObject'],'runtimeScreenshot':False})
    for o in selected:o.hide_render=True
    (O/'review/progress.json').write_text(json.dumps(rows,indent=2)+'\n');print('UNLABELLED_ACTUAL_MODEL_RENDERED',ident,flush=True)
(O/'review/manifest.json').write_text(json.dumps({'rows':rows,'scope':'Actual new Blender geometry with physical nameplates hidden, not concept art and not native runtime.'},indent=2)+'\n')
