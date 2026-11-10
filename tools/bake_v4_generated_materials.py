"""Bake shallow surface normals/roughness from the approved generated albedos.

Blender shader baking, not painted light/shadow or geometry displacement. Source
albedo images are immutable. Runtime copies use mipmapped lossless WebP later.
"""
import bpy,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/materials_v2'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_plane_add(size=1)
plane=bpy.context.object
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.bake.use_clear=True;scene.render.bake.margin=0
settings={'walnut':(.006,.48),'limestone':(.009,.78),'plaster':(.004,.86),'velvet':(.002,.91),'paving':(.016,.81),'metal':(.0007,.36),'carpet':(.003,.95),'leaf':(.001,.68),'lacquer':(.003,.42),'linen':(.0015,.92)}
if '--rebuild-natural' in sys.argv:
    O=R/'art/space_v4/rebuild_v1';settings={'bark':(.018,.84),'roof':(.012,.79),'grass':(.005,.93)}
(O/'maps').mkdir(parents=True,exist_ok=True)
rows=[]
for key,(depth,rough) in settings.items():
    mat=bpy.data.materials.new('generated_'+key);mat.use_nodes=True
    plane.data.materials.clear();plane.data.materials.append(mat)
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(O/'masters'/(key+'.png')))
    tex.extension='REPEAT';tex.interpolation='Linear'
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.25;bump.inputs['Distance'].default_value=depth
    links.new(tex.outputs['Color'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    target=nodes.new('ShaderNodeTexImage');normal=bpy.data.images.new(key+'_normal',512,512,alpha=False);normal.colorspace_settings.name='Non-Color';target.image=normal;nodes.active=target
    bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT')
    normal.filepath_raw=str(O/'maps'/(key+'_normal.png'));normal.file_format='PNG';normal.save()
    # Roughness is a deliberately restrained material response, with texture nap
    # variation. No claim that image luminance recovers real measured depth.
    bw=nodes.new('ShaderNodeRGBToBW');links.new(tex.outputs['Color'],bw.inputs['Color'])
    scale=nodes.new('ShaderNodeMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=.09;links.new(bw.outputs[0],scale.inputs[0])
    add=nodes.new('ShaderNodeMath');add.operation='ADD';add.inputs[1].default_value=rough-.045;links.new(scale.outputs[0],add.inputs[0])
    emit=nodes.new('ShaderNodeEmission');links.new(add.outputs[0],emit.inputs['Color']);links.new(emit.outputs[0],nodes.get('Material Output').inputs['Surface'])
    roughimg=bpy.data.images.new(key+'_roughness',512,512,alpha=False);roughimg.colorspace_settings.name='Non-Color';target.image=roughimg;nodes.active=target
    bpy.ops.object.bake(type='EMIT');roughimg.filepath_raw=str(O/'maps'/(key+'_roughness.png'));roughimg.file_format='PNG';roughimg.save()
    rows.append({'family':key,'normal':'maps/'+key+'_normal.png','roughness':'maps/'+key+'_roughness.png','bumpDistanceMetres':depth,'bumpStrength':.25,'roughnessCentre':rough})
    print('BAKED_GENERATED_SURFACE',key,flush=True)
(O/'bake-manifest.json').write_text(json.dumps({'method':'Blender Cycles tangent-normal and scalar roughness shader bake; shallow authored microrelief, not recovered physical scan','materials':rows},indent=2),encoding='utf8')
