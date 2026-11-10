"""Own brick high mesh -> low-plane color/normal/roughness; no painted shadows."""
import bpy,math,json,hashlib,random
from pathlib import Path
R=Path.cwd();O=R/'art/space_v4/park_levels_v1/architecture_v6/materials';O.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8
try:
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
    for d in p.devices:d.use=d.type=='OPTIX'
    if any(d.use for d in p.devices):scene.cycles.device='GPU'
except Exception:pass
def material(name,color,roughness):
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=roughness
    if name!='bake_output_only':
        nodes=m.node_tree.nodes;links=m.node_tree.links;noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=32;noise.inputs['Detail'].default_value=2
        ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.94,.94,.94,1);ramp.color_ramp.elements[1].color=(1.035,1.035,1.035,1);links.new(noise.outputs['Fac'],ramp.inputs[0])
        tint=nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[1].default_value=(*color,1);links.new(ramp.outputs[0],tint.inputs[2]);links.new(tint.outputs[0],bs.inputs['Base Color'])
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.003;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal'])
        rough=nodes.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=0;rough.inputs['From Max'].default_value=1;rough.inputs['To Min'].default_value=max(.6,roughness-.07);rough.inputs['To Max'].default_value=min(1,roughness+.07);links.new(noise.outputs['Fac'],rough.inputs['Value']);links.new(rough.outputs['Result'],bs.inputs['Roughness'])
    return m
brick=[material('actual_fired_brick_'+str(i),(.58+i*.019,.225+i*.008,.12+i*.005),.78+i*.009)for i in range(7)];mortar=material('actual_lime_mortar',(.47,.43,.34),.94)
high=[];random.seed(17)
for row in range(-1,11):
    for col in range(-1,7):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(col*.4+(.2 if row%2 else 0)+.2,row*.2+.1,.045));o=bpy.context.object;o.name='high_fired_brick';o.scale=(.382,.182,.065);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);mod=o.modifiers.new('actual_fired_edge_rounding','BEVEL');mod.width=.006;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name);o.data.materials.append(brick[((row%10)*3+(col%5)*5)%7]);high.append(o)
bpy.ops.mesh.primitive_cube_add(size=1,location=(1,1,-.005));o=bpy.context.object;o.name='high_continuous_mortar_bed';o.scale=(3,3,.04);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mortar);high.append(o)
d=bpy.data.meshes.new('low_tiling_plane');d.from_pydata([(0,0,0),(2,0,0),(2,2,0),(0,2,0)],[],[(0,1,2,3)]);d.update();uv=d.uv_layers.new(name='UVMap')
for li,co in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=co
low=bpy.data.objects.new('low_tiling_plane',d);scene.collection.objects.link(low);mat=material('bake_output_only',(.5,.5,.5),.8);low.data.materials.append(mat);node=mat.node_tree.nodes.new('ShaderNodeTexImage');mat.node_tree.nodes.active=node
scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.20;scene.render.bake.max_ray_distance=.40;scene.render.bake.margin=8;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
bpy.ops.object.select_all(action='DESELECT')
for o in high+[low]:o.select_set(True)
bpy.context.view_layer.objects.active=low;rows=[]
for key,kind,space in [('brick_color','DIFFUSE','sRGB'),('brick_normal','NORMAL','Non-Color'),('brick_roughness','ROUGHNESS','Non-Color')]:
    image=bpy.data.images.new(key,width=512,height=512,alpha=False);image.colorspace_settings.name=space;node.image=image;bpy.ops.object.bake(type=kind);image.filepath_raw=str(O/(key+'.png'));image.file_format='PNG';image.save();image.pack();rows.append({'id':key,'file':str(O/(key+'.png')),'sha256':hashlib.sha256((O/(key+'.png')).read_bytes()).hexdigest(),'colorSpace':space});print('REAL_MESH_BAKED',key,flush=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'brick-source.blend'),compress=True)
(O/'brick-bake.json').write_text(json.dumps({'ok':True,'technique':'Actual bevelled running-bond brick mesh selected-to-active bake','tileMetres':[2,2],'pixels':[512,512],'files':rows,'source':'brick-source.blend','bakedLighting':False,'normalConvention':'OpenGL tangent +Y','scope':'Original own material master and normal/roughness, not a photograph or source-game extraction.'},indent=2)+'\n',encoding='utf8')
