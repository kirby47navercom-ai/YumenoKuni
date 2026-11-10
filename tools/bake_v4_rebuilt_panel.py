"""Isolated real sculpted trim -> one flat panel tangent normal, no room atlas."""
import bpy,sys,json,hashlib,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_rebuilt_environment_kit as K
O=R/'art/space_v4/rebuild_v1';bpy.ops.wm.read_factory_settings(use_empty=True);K.setup_materials()
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.threads_mode='FIXED';scene.render.threads=4
# A physical moulding cross-section swept around a continuous rectangular frame.
root=K.root('original_high_panel');K.rounded_solid('recessed_wood_field',1,1,.012,'wood',root,.005,(0,0,-.003))
profile=[(.35,.004),(.37,.004),(.38,.013),(.39,.018),(.405,.020),(.42,.014),(.44,.013),(.45,.025),(.465,.030),(.48,.024),(.49,.007)]
verts=[(sx*r,sy*r,z)for r,z in profile for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
K.mesh('carved_continuous_frame',verts,[(j*4+i,j*4+(i+1)%4,(j+1)*4+(i+1)%4,(j+1)*4+i)for j in range(len(profile)-1)for i in range(4)],'wood',root,True)
high=[o for o in root.children_recursive if o.type=='MESH']
bpy.ops.mesh.primitive_plane_add(size=1);low=bpy.context.object;low.name='low_panel_bake_target'
mat=bpy.data.materials.new('panel_bake_target');mat.use_nodes=True;low.data.materials.append(mat);target=mat.node_tree.nodes.new('ShaderNodeTexImage');normal=bpy.data.images.new('panel_geometry_normal',512,512,alpha=False);normal.colorspace_settings.name='Non-Color';target.image=normal;mat.node_tree.nodes.active=target
bpy.ops.object.select_all(action='DESELECT')
for o in high+[low]:o.select_set(True)
bpy.context.view_layer.objects.active=low;scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.08;scene.render.bake.max_ray_distance=.12;scene.render.bake.margin=0
bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT');normal.filepath_raw=str(O/'maps/panel_geometry_normal.png');normal.file_format='PNG';normal.save()
bpy.ops.wm.save_as_mainfile(filepath=str(O/'panel-high-low-bake-source.blend'),compress=True)
out={'method':'Blender Cycles selected-to-active tangent normal; isolated physical moulding/frame -> flat target','size':[512,512],'highTriangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons)for o in high),'lowTriangles':2,'cageMetres':.08,'maxRayDistanceMetres':.12,'output':'maps/panel_geometry_normal.png','sha256':hashlib.sha256((O/'maps/panel_geometry_normal.png').read_bytes()).hexdigest()}
(O/'panel-bake-manifest.json').write_text(json.dumps(out,indent=2)+'\n');print('PANEL_GEOMETRY_BAKED',flush=True)
