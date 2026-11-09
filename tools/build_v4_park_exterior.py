"""Author a true 3D exterior level from the exact world catalogue. Interiors stream separately."""
import bpy,math,json,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/os.environ.get('V4_SPACE_OUT','art/space_v4/full_v1')
layout=json.loads((OUT/'world_layout.json').read_text(encoding='utf8'))
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf8'));spaces={s['id']:s for s in manifest['spaces']}
bpy.ops.wm.open_mainfile(filepath=str(OUT/'space_kit_source.blend'));scene=bpy.context.scene
for o in scene.objects:o.hide_render=True
world=bpy.data.objects.new('park_exterior_level',None);scene.collection.objects.link(world)
materials={name:bpy.data.materials.get('yk_'+name) for name in ['ink','ivory','paper','rose','purple','gold','steel','glass','wood','light']}
def empty(name,parent=world,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;o.location=loc;return o
def cube(name,loc,size,color='ink',parent=world):
    x,y,z=[v/2 for v in size];mesh=bpy.data.meshes.new(name+'_mesh')
    mesh.from_pydata([(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update()
    layer=mesh.uv_layers.new(name='UVMap')
    for polygon in mesh.polygons:
        dominant=max(range(3),key=lambda i:abs(polygon.normal[i]));axes=[i for i in range(3) if i!=dominant]
        for loop in polygon.loop_indices:
            v=mesh.vertices[mesh.loops[loop].vertex_index].co;layer.data[loop].uv=(v[axes[0]]/2,v[axes[1]]/2)
    o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.parent=parent;o.location=loc;o.data.materials.append(materials[color]);return o
def copy_tree(source,parent,loc):
    src=bpy.data.objects[source];mapping={}
    for old in [src]+list(src.children_recursive):
        new=old.copy();new.name='exterior_'+old.name;scene.collection.objects.link(new);new.hide_render=False;mapping[old]=new
    for old,new in mapping.items():new.parent=mapping.get(old.parent,parent)
    r=mapping[src];r.location=loc;return r
cube('terrain',(15,35,-.24),(280,190,.4),'ink')
def walkway(points,width=4):
    for a,b in zip(points,points[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length<.01:continue
        o=cube('walkway',((a[0]+b[0])/2,(a[1]+b[1])/2,-.015),(length,width,.045),'ivory');o.rotation_euler.z=math.atan2(dy,dx)
walkway([(0,-42),(0,-14),(0,18)],6)
walkway([(-14,0),(-24,0),(-24,17),(-45,17)],5)
walkway([(-24,17),(-24,54)],4)
walkway([(14,0),(42,0),(61,-10),(70,-10)],6)
walkway([(42,0),(42,53),(70,53),(112,53),(112,69)],5)
walkway([(85,53),(98,43),(98,5),(103,5)],4)
walkway([(-14,0),(-50,0),(-50,16),(-50,46),(-70,46),(-70,84)],5)
walkway([(-70,96),(-70,105)],5)
walkway([(-50,16),(-81,16)],4)
walkway([(-81,16),(-81,32)],4)
special={'plaza','park_garden','pool_edge','ferris_platform','coaster_platform','park_main_gate'}
for inst in layout['instances']:
    ident=inst['id'];pos=inst['position_blender']
    if inst['tier']!='surface' or ident=='inspection_hall_changed':continue
    spec=spaces[inst['asset_id']];w,d,h=spec['size_m']
    if ident in special:
        copy_tree(inst['asset_id'],world,pos);continue
    group=empty('facade_'+ident,loc=pos);group['interior_asset']=inst['asset'];group['portal_load']='matching interior scene; not baked into this facade'
    # Walls separated around a real south doorway instead of a door painted on a solid box.
    for side in [-1,1]:cube('facade_front',(side*(w/4+.35),-d/2,h/2),(w/2-.7,.2,h),'paper',group)
    cube('facade_lintel',(0,-d/2,(h+2.5)/2),(1.4,.2,max(.1,h-2.5)),'paper',group)
    cube('facade_back',(0,d/2,h/2),(w,.2,h),'paper',group)
    for x in [-w/2,w/2]:cube('facade_side',(x,0,h/2),(.2,d,h),'paper',group)
    cube('roof',(0,0,h+.12),(w+.4,d+.4,.24),'purple',group)
    for x in [-w/2,w/2]:cube('corner_column',(x,-d/2-.05,h/2),(.2,.3,h),'ink',group)
    cube('front_awning',(0,-d/2-.6,2.7),(min(w-1,5),1.2,.15),'rose',group)
    for side in [-1,1]:cube('front_window',(side*w*.3,-d/2-.12,1.65),(min(2,w*.22),.035,1.3),'glass',group)
    group['readable_signs']='separate runtime text layer'
# Hotel upper wing matches corridor + sixteen guest footprints.
cube('hotel_upper_wing',(-4,58,3.2),(18.2,56,6.4),'paper')
cube('hotel_upper_roof',(-4,58,6.55),(18.6,56.4,.3),'purple')
for i in range(8):
    for x in [-13.22,5.22]:cube('upper_room_window',(x,33.5+i*7,4.8),(.035,1.8,1.5),'glass')
# Park perimeter deliberately leaves the two actual gate openings.
for x in [-110,140]:
    cube('boundary_base',(x,30,.25),(.35,140,.5),'purple')
    for y in range(-40,102,2):cube('boundary_pick',(x,y,1.4),(.09,.09,2.8),'ink')
for y,segments in [(-40,[(-110,-3),(3,140)]),(101,[(-110,-75),(-65,140)])]:
    for lo,hi in segments:
        cube('boundary_base',((lo+hi)/2,y,.25),(hi-lo,.35,.5),'purple')
        for x in range(math.ceil(lo),math.floor(hi)+1,2):cube('boundary_pick',(x,y,1.4),(.09,.09,2.8),'ink')
for x,y in [(-15,-18),(15,-18),(35,15),(40,48),(-45,10),(-45,40),(95,50),(120,55),(-80,60)]:
    cube('site_lamp_post',(x,y,2),(.12,.12,4),'ink');cube('site_lamp',(x,y,4.2),(.4,.4,.5),'light')
world['source_layout']='world_layout.json';world['runtime_integrated']=False
bpy.ops.object.select_all(action='DESELECT')
for o in [world]+list(world.children_recursive):o.select_set(True)
bpy.context.view_layer.objects.active=world
bpy.ops.export_scene.gltf(filepath=str(OUT/'park_exterior.glb'),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
scene.world=bpy.data.worlds.new('park_daylight');scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.6
bpy.ops.object.light_add(type='SUN',location=(0,0,100));sun=bpy.context.object;sun.data.energy=1.7;sun.rotation_euler=(.35,-.5,-.4)
bpy.ops.object.camera_add(location=(180,-160,160));cam=bpy.context.object;cam.rotation_euler=(Vector((10,32,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=310;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1920;scene.render.resolution_y=1280;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
folder=ROOT/os.environ.get('V4_SPACE_PREVIEW','Game/Saved/v4-world-full-v2');folder.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(folder/'park_exterior.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'park_exterior_source.blend'))
print('Authored exterior GLB/Blender and same-geometry review render; no runtime claim')
