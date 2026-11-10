"""Blender composition guide for NAI CG; this render is never final 2D delivery."""
import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(ROOT/'art/space_v4/detail_v1/space_kit_source.blend'),link=False) as (src,dst):
    dst.objects=[name for name in src.objects if name=='detail_office_phone' or name.startswith(('phone_base','blank_key','receiver','coiled_cord'))]
root=next(o for o in dst.objects if o and o.name=='detail_office_phone')
family=[root]+list(root.children_recursive)
for o in family:
    if o.name.startswith('coiled_cord'):continue
    bpy.context.scene.collection.objects.link(o);o.hide_render=False
receiver=next(o for o in family if o.type=='EMPTY' and o.name=='receiver')
receiver.location=(.38,-.08,.07)
def material(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    shader=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');shader.inputs['Base Color'].default_value=(*color,1);shader.inputs['Roughness'].default_value=.8;return m
wood=material('guide_wood',(.18,.11,.08));wall=material('guide_wall',(.28,.31,.32));ink=material('guide_cord',(.02,.02,.025))
def cube(name,loc,size,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size;o.data.materials.append(mat);return o
cube('desk',(0,0,-.035),(1.6,1.15,.06),wood)
cube('wall',(0,.65,.45),(2,.05,1.2),wall)
for x in [-.11,.11]:cube('empty_cradle_rest',(x,.075,.16),(.045,.075,.04),root.children[0].data.materials[0])
curve=bpy.data.curves.new('cord','CURVE');curve.dimensions='3D';curve.bevel_depth=.008;curve.bevel_resolution=2
s=curve.splines.new('POLY');points=[]
for i in range(100):
    t=i/99;points.append((-.14+.35*t,-.17-.12*math.sin(t*math.pi)+.015*math.cos(t*math.tau*12),.025+.015*math.sin(t*math.tau*12)))
s.points.add(len(points)-1)
for p,co in zip(s.points,points):p.co=(*co,1)
o=bpy.data.objects.new('connected_cord',curve);bpy.context.collection.objects.link(o);o.data.materials.append(ink)
scene=bpy.context.scene
bpy.ops.object.camera_add(location=(.85,-1.1,.95));cam=bpy.context.object;cam.rotation_euler=(Vector((.1,0,.08))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=42;scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(-.6,-.5,1.4));bpy.context.object.data.energy=65;bpy.context.object.data.size=1.4
scene.world=bpy.data.worlds.new('guide_world');scene.world.color=(.25,.25,.25);scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1536;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';out=ROOT/'art/cg_v4/guides';out.mkdir(parents=True,exist_ok=True)
scene.render.filepath=str(out/'phone_off_hook_guide.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'phone_off_hook_guide.blend'))
