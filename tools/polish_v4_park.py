"""Original park architecture and landscape detail on the authored full-world assembly.
Blender only. No network, borrowed meshes, or substituted baked walkable backgrounds.
"""
import bpy,math,json,os,random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'art/space_v4/full_v2'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'park_exterior_source.blend'));scene=bpy.context.scene
world=bpy.data.objects['park_exterior_level'];random.seed(20261028)
M={k:bpy.data.materials['yk_'+k] for k in ['ink','paper','ivory','purple','gold','wood','rose','glass','light']}
def mat(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.9
    M[name]=m;return m
mat('sage',(.23,.31,.25));mat('leaf_light',(.34,.42,.29));mat('leaf_dark',(.12,.21,.18));mat('paving',(.52,.49,.43))
texpath=ROOT/'art/hd_v4/materials/park_cobble.webp'
if texpath.exists():
    m=M['paving'];t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(texpath),check_existing=True);t.extension='REPEAT';m.node_tree.links.new(t.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
def mesh_obj(name,vertices,faces,material,parent=world):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        axes=[i for i in range(3) if i!=max(range(3),key=lambda i:abs(p.normal[i]))]
        for li in p.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]/2,v[axes[1]]/2)
    o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.parent=parent;o.data.materials.append(M[material]);return o
def box(name,loc,size,material='paper',parent=world):
    x,y,z=[s/2 for s in size]
    o=mesh_obj(name,[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material,parent);o.location=loc;return o
def rod(name,a,b,r,material='ink',parent=world,n=10):
    a,b=Vector(a),Vector(b);h=(b-a).length
    v=[(r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for z in [-h/2,h/2] for i in range(n)]
    f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh_obj(name,v,f,material,parent);o.location=(a+b)/2;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def arch(name,center,rise,width,depth,material,parent=world):
    cx,cy,cz=center;n=16
    points=[(cx+width/2*math.cos(i*math.pi/n),cy,cz+rise*math.sin(i*math.pi/n)) for i in range(n+1)]
    for a,b in zip(points,points[1:]):rod(name,a,b,depth,material,parent)
def roof(parent,w,d,h):
    # Actual pitched mesh; broad dark edge trims read as ink at player height.
    pts=[(-w/2-.35,-d/2-.35,h),(w/2+.35,-d/2-.35,h),(w/2+.35,d/2+.35,h),(-w/2-.35,d/2+.35,h),(0,-d/2-.35,h+1.35),(0,d/2+.35,h+1.35)]
    mesh_obj('pitched_cel_roof',pts,[(0,1,4),(3,5,2),(0,4,5,3),(4,1,2,5)],'purple',parent)
    for a,b in [(pts[0],pts[4]),(pts[1],pts[4]),(pts[4],pts[5]),(pts[0],pts[3]),(pts[1],pts[2])]:rod('roof_ink_edge',a,b,.055,'ink',parent)
    for i in range(1,int(d/1.2)+1):
        y=-d/2+i*1.2
        for side in [-1,1]:rod('roof_seam',(side*(w/2+.3),y,h+.02),(0,y,h+1.37),.018,'gold',parent)
layout=json.loads((OUT/'world_layout.json').read_text(encoding='utf8'));specs={s['id']:s for s in json.loads((OUT/'manifest.json').read_text(encoding='utf8'))['spaces']}
for inst in layout['instances']:
    name='facade_'+inst['id'];p=bpy.data.objects.get(name)
    if not p:continue
    w,d,h=specs[inst['asset_id']]['size_m'];front=-d/2-.19
    roof(p,w,d,h+.22)
    for z in [.2,.7,h-.14]:box('front_cornice',(0,front,z),(w+.25,.22,.12),'gold' if z==.7 else 'ink',p)
    for x in [-w/2+.18,w/2-.18,-w*.18,w*.18]:
        if abs(x)<1:continue
        box('front_pilaster',(x,front,h/2),(.16,.25,h),'ivory',p)
        for z in [.2,h-.2]:box('pilaster_cap',(x,front-.025,z),(.3,.31,.14),'gold',p)
    arch('entry_arch',(0,front-.1,2.5),.75,1.7,.06,'gold',p)
    for side in [-1,1]:
        x=side*w*.3;ww=min(2,w*.22)
        for xx in [x-ww/2,x,x+ww/2]:box('window_mullion',(xx,front-.02,1.65),(.055,.05,1.38),'ink',p)
        for z in [1,1.65,2.3]:box('window_crossbar',(x,front-.02,z),(ww+.1,.06,.055),'ink',p)
        box('window_sill',(x,front-.06,.92),(ww+.3,.35,.12),'ivory',p)
    box('blank_signboard',(0,front-.04,h-.35),(min(w*.6,4),.16,.5),'wood',p)
    p['sign_text']='not baked; localized runtime text owner'
# Replace vast unbroken blank ground with actual planting beds outside walks.
for o in world.children_recursive:
    if o.name=='terrain':o.data.materials.clear();o.data.materials.append(M['sage'])
    if o.name.startswith('walkway'):
        o.data.materials.clear();o.data.materials.append(M['paving'])
        # Separate raised kerbs, kept away from the traversable center.
        length=o.dimensions.x;width=o.dimensions.y
        for side in [-1,1]:
            k=box('walk_kerb',(0,side*(width/2+.06),.035),(length,.13,.11),'ivory',o);k.location.z=.055
# Articulated real 3D trees. Deterministic placement leaves entrance and path centerlines clear.
tree_positions=[(-20,-24),(20,-24),(-18,8),(20,10),(28,25),(28,42),(58,38),(62,46),(82,46),(124,48),(124,64),(124,88),(88,87),(56,82),(-36,30),(-36,48),(-45,67),(-90,65),(-96,45),(-96,0),(-80,-14),(-60,-15)]
for ti,(x,y) in enumerate(tree_positions):
    rod('tree_trunk',(x,y,0),(x+.15,y,4.4),.16,'wood')
    for side in [-1,1]:rod('tree_branch',(x,y,2.5),(x+side*1.2,y+.3,4.8),.085,'wood')
    box('tree_planter',(x,y,.23),(3.3,3.3,.46),'ivory');box('planter_soil',(x,y,.47),(2.95,2.95,.035),'wood')
    for j in range(5):
        a=j*math.tau/5;loc=(x+1.0*math.cos(a),y+.8*math.sin(a),4.5+random.random()*.8)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=loc);o=bpy.context.object;o.name='ink_leaf_crown';o.parent=world;o.scale=(1.4,1.3,1.6);o.data.materials.append(M['leaf_light' if j%2 else 'leaf_dark'])
    for dx in [-1.4,1.4]:box('planter_seat',(x+dx,y,.53),(.32,3.1,.1),'wood')
# Decorative gateway flags and roofs use authored meshes, no borrowed artwork.
for x in [-3.3,3.3]:
    base=(x,-40,5.2);rod('gate_finial',base,(x,-40,6.7),.055,'gold')
    pts=[(x,-40,6.65),(x+1.4,-40,6.1),(x,-40,5.6)];mesh_obj('gate_pennant',pts,[(0,1,2)],'rose')
# Visible sky is authored environment lighting, not an empty black preview void.
scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.43,.55,.66,1);bg.inputs[1].default_value=.8
scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=-.6
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1920;scene.render.resolution_y=1080
scene.render.resolution_percentage=100
for o in scene.objects:
    if o.type=='LIGHT' and o.data.type=='SUN':o.data.energy=2.0
cam=scene.camera;cam.data.type='PERSP';cam.data.lens=25
pre=ROOT/'Game/Saved/v4-world-full-v2';pre.mkdir(parents=True,exist_ok=True)
for name,pos,target in [('park_walk_plaza',(0,-12,1.65),(0,20,3)),('park_walk_east',(38,43,1.65),(90,60,3)),('park_walk_west',(-38,11,1.65),(-75,20,3))]:
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(pre/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT')
for o in [world]+list(world.children_recursive):o.select_set(True)
bpy.context.view_layer.objects.active=world
bpy.ops.export_scene.gltf(filepath=str(OUT/'park_exterior_r2.glb'),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'park_exterior_r2_source.blend'))
(OUT/'exterior_art_review.json').write_text(json.dumps({'source':'park_exterior_source.blend + tools/polish_v4_park.py','output':'park_exterior_r2.glb','original_meshes':True,'walk_height_previews':3,'runtime_integrated':False,'limits':['geometry/render QA is not engine collision or runtime visual acceptance','landscape placements are authored, not measured V3 topology']},indent=2)+'\n',encoding='utf8')
print('PARK_ART_DETAIL_COMPLETE',flush=True)
