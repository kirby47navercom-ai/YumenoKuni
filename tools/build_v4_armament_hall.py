"""Background Blender: a separate original 3D rhythm-mode hall.

Vanishing corridor/windows/curtains are based on the observed composition,
not extracted original geometry. Material groups keep GPU draws bounded.
"""
import bpy
import math
import json
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art/space_v4/armament_hall_v1'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
colors={'ink':(.018,.016,.025,1),'wall':(.09,.075,.10,1),
        'gold':(.43,.29,.12,1),'ivory':(.66,.61,.46,1),
        'floor':(.035,.045,.055,1),'red':(.35,.018,.042,1),
        'window':(.75,.82,.91,1)}
mats={}
for key,color in colors.items():
    m=bpy.data.materials.new('armament_'+key);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color
    bs.inputs['Roughness'].default_value=.63
    if key=='gold':bs.inputs['Metallic'].default_value=.55
    if key=='window':
        bs.inputs['Emission Color'].default_value=color;bs.inputs['Emission Strength'].default_value=1.4
    mats[key]=m


def box(name,p,s,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p)
    o=bpy.context.object;o.name=name;o.scale=s;o.data.materials.append(mats[material])
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o


def surface(name,verts,faces,material):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(mats[material])
    return obj


# Real floor and recessed coffers, rather than a perspective baked background.
box('floor foundation',(0,17,-.12),(12,38,.24),'floor')
for x in range(-5,6):box('floor long inlay',(x,17,.009),(.022,38,.012),'gold')
for y in range(-2,37,2):box('floor cross inlay',(0,y,.012),(12,.025,.012),'gold')
for x in [-4.5,-1.5,1.5,4.5]:
    for y in range(0,36,4):box('floor ivory tile',(x,y+.9,.014),(2.94,1.74,.015),'ivory')
box('ceiling',(0,17,8.05),(12,38,.18),'ink')
box('distant wall',(0,36,4),(12,.2,8),'ink')
for side in [-1,1]:
    x=side*5.7
    box('wall backing',(x,17,4),(.3,38,8),'wall')
    box('lower wainscot',(x-side*.20,17,.8),(.15,38,1.6),'ink')
    for z in [.12,1.63,7.55]:box('continuous wall molding',(x-side*.28,17,z),(.17,38,.09),'gold')
    for y in range(1,35,5):
        # Tall arched aperture, each with a true curved top and mullion relief.
        inner=x-side*.22;w=1.55;base=1.75;spring=5.9;r=w
        verts=[(inner,y-w,base),(inner,y+w,base),(inner,y+w,spring)]
        for i in range(1,17):
            a=i*math.pi/16;verts.append((inner,y+math.cos(a)*r,spring+math.sin(a)*r))
        surface('arched luminous glazing',verts,[tuple(range(len(verts)))],'window')
        box('window central mullion',(inner-side*.04,y,4.2),(.08,.06,4.9),'ivory')
        box('window horizontal mullion',(inner-side*.05,y,4.15),(.08,3.1,.08),'ivory')
        for offset in [-w,w]:box('window jamb',(inner-side*.08,y+offset,3.83),(.16,.13,4.2),'gold')
        arch=[]
        for i in range(17):
            a=i*math.pi/16
            arch.extend([(inner-side*.08,y+math.cos(a)*(r-.06),spring+math.sin(a)*(r-.06)),
                         (inner-side*.08,y+math.cos(a)*(r+.07),spring+math.sin(a)*(r+.07))])
        surface('arched gold frame',arch,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(16)],'gold')
        # Drapery is a folded cloth mesh, with a curved lower edge and tie-in.
        for wing in [-1,1]:
            verts=[];rows=14;cols=10
            for row in range(rows+1):
                t=row/rows;z=7.35-t*5.5
                width=.95*(1-.50*math.sin(t*math.pi))
                for col in range(cols+1):
                    u=col/cols
                    yy=y+wing*(w-.08-width*u)
                    depth=.13+.12*math.sin(u*math.pi*8)*(0.5+t*.5)
                    verts.append((inner-side*depth,yy,z-.14*math.sin(u*math.pi)))
            faces=[]
            for row in range(rows):
                for col in range(cols):
                    a=row*(cols+1)+col;faces.append((a,a+1,a+cols+2,a+cols+1))
            surface('folded wine curtain',verts,faces,'red')
            box('curtain tie',(inner-side*.28,y+wing*(w-.33),3.45),(.13,.53,.075),'gold')
        for dy in [-2.25,2.25]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.18,depth=7.8,location=(x-side*.38,y+dy,3.9))
            bpy.context.object.name='fluted pilaster';bpy.context.object.data.materials.append(mats['ivory'])
            for zz in [.35,1.6,7.3]:box('pilaster collar',(x-side*.38,y+dy,zz),(.48,.48,.12),'gold')
for y in range(0,37,5):box('ceiling crossbeam',(0,y,7.75),(11.5,.15,.24),'gold')

# One mesh per material: all perspective/depth remains real, with seven groups.
for material in mats.values():
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.materials and o.data.materials[0]==material]
    if not objects:continue
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();objects[0].name=material.name
mesh_path=OUT/'armament_hall.glb'
bpy.ops.export_scene.gltf(filepath=str(mesh_path),export_format='GLB',export_apply=True)
triangles=sum(len(o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH')
(OUT/'manifest.json').write_text(json.dumps({'builder':'tools/build_v4_armament_hall.py',
    'mesh':str(mesh_path.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
    'materialGroups':7,'polygons':triangles,'axes':'Blender Z-up to glTF Y-up',
    'reference':'https://www.youtube.com/watch?v=rCdH6oF6b60&t=218s',
    'originalProductionGeometry':True,'recoveredV3Geometry':False,'runtimeVerified':False},indent=2)+'\n',encoding='utf-8')
print('Separate armament hall exported',triangles,'polygons')
