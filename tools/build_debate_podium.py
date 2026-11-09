"""Original curved discussion station, shared mesh; no extracted source assets."""
import bpy,math,json
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'art/space_v4/court_intro_v1'
bpy.ops.wm.read_factory_settings(use_empty=True)
mats={}
for name,c,metal,emission in [('navy',(.025,.055,.11,1),.5,0),('violet',(.14,.055,.19,1),.4,0),('gold',(.44,.29,.12,1),.7,0),('cyan',(.03,.7,.85,1),.3,1),('screen',(.035,.16,.23,1),.3,.5)]:
    m=bpy.data.materials.new('podium_'+name);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=c;p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.4;p.inputs['Emission Color'].default_value=c;p.inputs['Emission Strength'].default_value=emission;mats[name]=m
def arc(name,inner,outer,z0,z1,material,begin=-225,end=45,n=64):
    verts=[];faces=[]
    for i in range(n+1):
        a=math.radians(begin+(end-begin)*i/n)
        for r,z in [(inner,z0),(outer,z0),(outer,z1),(inner,z1)]:verts.append((r*math.cos(a),r*math.sin(a),z))
    for i in range(n):
        for j in range(4):faces.append((4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j))
    faces.extend([(3,2,1,0),(4*n,4*n+1,4*n+2,4*n+3)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.data.materials.append(mats[material])
arc('foot',.4,.64,0,.14,'navy')
arc('base light',.57,.65,.14,.18,'cyan')
arc('curved shell',.52,.59,.18,1.43,'violet')
arc('lower band',.56,.63,.26,.32,'gold')
# Meet the gold lip at .65; coincident outer faces at .68 caused visible z-fighting.
arc('top working rim',.42,.65,1.42,1.52,'navy')
arc('top gold lip',.65,.68,1.49,1.53,'gold')
arc('front glow',.586,.6,.65,.68,'cyan')
for i in range(9):
    angle=-210+i*30
    arc('upright trim',.587,.61,.34,1.42,'gold',angle-1.5,angle+1.5,2)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-.49,1.535));o=bpy.context.object;o.name='small control inset';o.scale=(.44,.19,.012);o.data.materials.append(mats['screen']);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
for m in mats.values():
    group=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.materials[0]==m]
    bpy.ops.object.select_all(action='DESELECT')
    for o in group:o.select_set(True)
    bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'debate_podium.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'debate_podium.glb'),export_format='GLB',export_apply=True)
(OUT/'podium_manifest.json').write_text(json.dumps({'mesh':'debate_podium.glb','source':'tools/build_debate_podium.py','original_geometry':True,'outer_radius':.68,'height':1.547,'rear_opening_degrees':90,'runtime_scale':[1,.82,1],'ring_radius':3.95,'actor_radius':4.08,'slot_degrees':22.5,'neighbor_center_distance':2*3.95*math.sin(math.pi/16),'minimum_static_circular_clearance':2*3.95*math.sin(math.pi/16)-1.36},indent=2),encoding='utf-8')
