"""Run with Blender --background --python; authors original meshes, never original-game data."""
import bpy, math, json, os
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/os.environ.get('V4_SPACE_OUT','art/space_v4');OUT.mkdir(parents=True,exist_ok=True)
PREVIEW=ROOT/os.environ.get('V4_SPACE_PREVIEW','Game/Saved/v4-space-assets');PREVIEW.mkdir(parents=True,exist_ok=True)
HOTEL_DOOR_Y=[-24.5,-17.5,-10.5,-3.5,3.5,10.5,17.5,24.5]
HOTEL_CORRIDOR_LENGTH=56
PREVIEW_ONLY=set(filter(None,os.environ.get('V4_SPACE_PREVIEW_ONLY','').split(',')))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
COLORS={'ink':(.035,.028,.055,1),'ivory':(.72,.65,.52,1),'paper':(.93,.89,.79,1),'rose':(.55,.13,.25,1),'purple':(.20,.10,.32,1),'gold':(.45,.31,.12,1),'steel':(.29,.34,.37,1),'glass':(.16,.29,.33,1),'blue':(.08,.25,.43,1),'wood':(.22,.12,.095,1),'light':(.9,.64,.32,1),'white':(.77,.8,.78,1)}
M={}
for name,c in COLORS.items():
    mat=bpy.data.materials.new('yk_'+name);mat.use_nodes=True
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=c;bs.inputs['Roughness'].default_value=.72
    if name in ('steel','gold'):bs.inputs['Metallic'].default_value=.65
    if name=='light':
        bs.inputs['Emission Color'].default_value=c;bs.inputs['Emission Strength'].default_value=1.5
    M[name]=mat

TEXTURED=os.environ.get('V4_SPACE_TEXTURED')=='1'
if TEXTURED:
    for material,identifier in [('paper','ivory_plaster'),('wood','walnut_ink'),('rose','wine_fabric')]:
        path=ROOT/'art/hd_v4/materials'/f'{identifier}.webp'
        if not path.is_file():raise RuntimeError('4x material must be exported first: '+str(path))
        tex=M[material].node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True);tex.extension='REPEAT'
        bs=next(n for n in M[material].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        M[material].node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        M[material]['original_material_source']=path.relative_to(ROOT).as_posix()

def author_uv(mesh):
    if not TEXTURED:return
    layer=mesh.uv_layers.new(name='UVMap')
    for polygon in mesh.polygons:
        dominant=max(range(3),key=lambda i:abs(polygon.normal[i]));axes=[i for i in range(3) if i!=dominant]
        for loop in polygon.loop_indices:
            point=mesh.vertices[mesh.loops[loop].vertex_index].co
            layer.data[loop].uv=(point[axes[0]]/2,point[axes[1]]/2)

def empty(name,parent=None,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;o.location=loc;return o

def cube(name,loc,size,mat='ivory',parent=None,bevel=.025):
    # Direct mesh creation avoids a full scene/operator update for every panel.
    x,y,z=[v/2 for v in size]
    vertices=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata(vertices,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update()
    author_uv(mesh);o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o)
    if bevel:
        mod=o.modifiers.new('edge_chamfer','BEVEL');mod.width=min(bevel,min(size)/4);mod.segments=2
        norm=o.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
    o.data.materials.append(M[mat]);o.parent=parent;o.location=loc
    return o

def cyl(name,loc,r,depth,mat='ink',parent=None,vertices=24):
    pts=[(r*math.cos(i*math.tau/vertices),r*math.sin(i*math.tau/vertices),z) for z in [-depth/2,depth/2] for i in range(vertices)]
    faces=[tuple(reversed(range(vertices))),tuple(range(vertices,vertices*2))]+[(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
    mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata(pts,[],faces);mesh.update()
    author_uv(mesh);o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.parent=parent;o.location=loc;o.data.materials.append(M[mat]);return o

def bar(name,a,b,r,mat,parent):
    a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,mat,parent,12)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def root(name):return empty(name)

def floor():
    r=root('floor_tile_4m');cube('slab',(0,0,-.1),(4,4,.2),'ink',r)
    for x in range(4):
        for y in range(4):cube('tile',(x-1.5,y-1.5,.012),(.986,.986,.025),'ivory' if (x+y)%2 else 'paper',r,.006)
    return r

def wall():
    r=root('wall_panel_4m');cube('wall',(0,0,1.6),(4,.18,3.2),'paper',r)
    cube('wainscot',(0,-.105,.55),(4,.04,1.1),'purple',r)
    for z in [.1,1.08,3.03]:cube('molding',(0,-.14,z),(4,.09,.065),'gold' if z==1.08 else 'ink',r)
    for x in [-1.94,0,1.94]:cube('pilaster',(x,-.13,1.65),(.065,.08,2.8),'ivory',r)
    return r

def doorframe():
    r=root('door_frame_1m')
    for x in [-.58,.58]:cube('jamb',(x,0,1.24),(.16,.32,2.48),'ink',r)
    cube('header',(0,0,2.45),(1.32,.32,.18),'ink',r)
    for x in [-.55,.55]:cube('gold_trim',(x,-.18,1.2),(.035,.035,2.35),'gold',r)
    cube('threshold',(0,0,.025),(1.32,.42,.05),'steel',r,.006)
    return r

def door():
    r=root('door_hinged_1m');pivot=empty('hinge',r,(-.5,0,0));pivot['interaction']='rotate local Z 0..95 degrees; origin is hinge'
    cube('leaf',(.5,0,1.18),(1,.1,2.36),'purple',pivot)
    for z in [.55,1.55]:
        cube('recessed_panel',(.5,-.056,z),(.72,.02,.65),'wood',pivot,.015)
        for x in [.12,.88]:cube('panel_trim',(x,-.075,z),(.025,.025,.7),'gold',pivot,.005)
    cube('handle_plate',(.85,-.08,1.08),(.09,.03,.22),'gold',pivot)
    bar('lever',(.85,-.16,1.1),(.65,-.16,1.1),.025,'steel',pivot)
    for z in [.25,1.2,2.15]:cyl('hinge_pin',(0,0,z),.035,.12,'gold',pivot,12)
    return r

def window():
    r=root('fixed_window_2m');cube('glass',(0,0,1.6),(1.85,.045,1.38),'glass',r,.003)
    for x in [-1,0,1]:cube('frame',(x,-.04,1.6),(.06,.14,1.55),'ink',r)
    for z in [.83,1.6,2.37]:cube('frame',(0,-.04,z),(2.08,.14,.06),'ivory',r)
    cube('sill',(0,-.12,.8),(2.18,.34,.1),'paper',r)
    r['fixed_glass']=True;return r

def table():
    r=root('meeting_table');cube('top',(0,0,.76),(2.6,1.12,.1),'wood',r,.05)
    cube('edge',(0,0,.7),(2.64,1.16,.035),'gold',r,.01)
    for x in [-1.05,1.05]:
        for y in [-.38,.38]:cube('leg',(x,y,.35),(.085,.085,.7),'ink',r)
    return r

def chair():
    r=root('chair');cube('seat',(0,0,.46),(.48,.5,.09),'rose',r,.04);cube('back',(0,.23,.81),(.48,.095,.62),'purple',r,.04)
    for x in [-.2,.2]:
        for y in [-.2,.2]:cube('leg',(x,y,.22),(.045,.045,.44),'ink',r,.008)
    bar('back_rail',(-.24,.27,1.09),(.24,.27,1.09),.022,'gold',r);return r

def bench():
    r=root('park_bench')
    for y in [-.2,-.07,.06,.19]:cube('seat_slats',(0,y,.48),(1.85,.105,.05),'wood',r,.012)
    for z in [.72,.85,.98]:cube('back_slats',(0,.25,z),(1.85,.065,.105),'wood',r,.012)
    for x in [-.7,.7]:
        bar('leg',(x,-.18,.05),(x,-.18,.47),.04,'ink',r);bar('back_leg',(x,.2,.05),(x,.27,1.04),.04,'ink',r)
        bar('armrest',(x,-.25,.7),(x,.25,.7),.035,'gold',r)
    return r

def shelf():
    r=root('book_shelf');cube('back',(0,.24,1.2),(1.6,.06,2.4),'wood',r)
    for x in [-.8,.8]:cube('side',(x,0,1.2),(.1,.55,2.4),'ink',r)
    for z in [.08,.55,1.02,1.49,1.96,2.38]:cube('shelf',(0,0,z),(1.6,.55,.06),'wood',r)
    for row in range(4):
        for j in range(10):
            h=.30+.045*((j+row)%3);o=cube('book',(-.67+j*.14,-.01,.58+row*.47+h/2),(.11,.35,h),['purple','rose','ivory','ink'][j%4],r,.005)
    return r

def podium():
    r=root('trial_podium');cube('plinth',(0,0,.08),(1.42,.95,.16),'ink',r,.055)
    cube('body',(0,0,.63),(1.16,.69,1.02),'purple',r,.05)
    cube('face',(0,-.36,.65),(.92,.025,.7),'wood',r,.025)
    for x in [-.51,.51]:cube('gold_vertical',(x,-.375,.65),(.045,.045,.9),'gold',r,.008)
    cube('top',(0,0,1.18),(1.42,.98,.13),'ink',r,.04)
    cube('top_inlay',(0,-.02,1.25),(1.2,.78,.012),'ivory',r,.01)
    bar('front_rail',(-.66,-.49,1.3),(.66,-.49,1.3),.027,'gold',r)
    r['actor_foot_anchor']=[0,.72,0];return r

def chest():
    r=root('blue_props_chest');cube('bottom',(0,0,.22),(1.85,.83,.1),'ink',r)
    for y in [-.43,.43]:cube('long_side',(0,y,.64),(1.85,.08,.8),'blue',r)
    for x in [-.93,.93]:cube('end',(x,0,.64),(.08,.85,.8),'blue',r)
    for x in [-.88,.88]:
        for y in [-.4,.4]:
            wheel=cyl('wheel',(x,y,.14),.12,.065,'ink',r,16);wheel.rotation_euler.x=math.pi/2
            cube('corner_guard',(x,y,.62),(.09,.09,.8),'steel',r,.008)
    lid=empty('lid_hinge',r,(0,.43,1.05));cube('lid',(0,-.43,.035),(1.95,.94,.09),'blue',lid)
    for x in [-.6,.6]:cube('outside_latch',(x,-.49,.96),(.1,.06,.18),'steel',r,.01)
    r['interior_dimensions_m']=[1.77,.77,.75];r['inner_lock']=False;r['outside_latches']=2
    r['lid_open_rotation_degrees']=[-105,0,0];return r

def printer():
    r=root('printer');cube('body',(0,0,.17),(.55,.43,.29),'white',r,.04)
    cube('top',(0,.04,.33),(.52,.36,.04),'ink',r,.012)
    cube('tray',(0,-.28,.11),(.4,.27,.025),'steel',r,.008)
    for z in [.125,.129,.133]:cube('paper',(0,-.28,z),(.27,.24,.003),'paper',r,.001)
    cube('screen',(.15,-.19,.27),(.12,.015,.045),'glass',r,.003);return r

def console():
    r=root('control_console');cube('base',(0,0,.45),(1.8,.7,.9),'ink',r)
    deck=cube('deck',(0,-.1,.96),(1.85,.8,.12),'steel',r);deck.rotation_euler.x=math.radians(12)
    for x in [-.5,0,.5]:
        cube('screen_case',(x,.15,1.24),(.43,.12,.36),'ink',r)
        cube('screen',(x,.08,1.24),(.36,.012,.27),'glass',r,.003)
        for y in [-.25,-.38]:
            for j in range(3):cyl('control',(x-.12+j*.12,y,1.04),.026,.016,'rose' if j==0 else 'ivory',r,12)
    return r

def clock():
    r=root('wall_clock');o=cyl('case',(0,0,0),.24,.07,'ink',r,48);o.rotation_euler.x=math.pi/2
    o=cyl('face',(0,-.041,0),.21,.012,'paper',r,48);o.rotation_euler.x=math.pi/2
    for i in range(12):
        a=i*math.tau/12;bar('tick',(.177*math.sin(a),-.052,.177*math.cos(a)),(.195*math.sin(a),-.052,.195*math.cos(a)),.006,'ink',r)
    bar('minute',(0,-.062,0),(.06,-.062,.145),.007,'ink',r);bar('hour',(0,-.064,0),(-.105,-.064,.03),.009,'ink',r)
    r['hands_are_static_art_not_time_evidence']=True;return r

def microphone():
    r=root('microphone_stand');cyl('weighted_base',(0,0,.055),.22,.11,'steel',r,32);cyl('pole',(0,0,.82),.022,1.5,'ink',r,16)
    bar('boom',(0,0,1.54),(.35,0,1.67),.017,'steel',r);bar('microphone',(.34,0,1.67),(.52,0,1.72),.032,'ink',r);return r

def mirror():
    r=root('mirror_panel');cube('reflective_panel',(0,0,1.35),(1.35,.07,2.5),'glass',r,.008)
    for x in [-.72,.72]:cube('side',(x,-.04,1.35),(.09,.16,2.68),'gold',r)
    for z in [.035,2.67]:cube('edge',(0,-.04,z),(1.52,.16,.09),'ink',r)
    r['requires_runtime_planar_reflection']=True;return r

def stairs():
    r=root('stairs_18');rise=3.2/18;run=.26
    for i in range(18):cube('step',(0,i*run,(i+1)*rise/2),(1.65,run,(i+1)*rise),'ivory',r,.008)
    for x in [-.85,.85]:
        for i in [0,3,6,9,12,15,17]:bar('baluster',(x,i*run,(i+1)*rise),(x,i*run,(i+1)*rise+.9),.025,'ink',r)
        bar('handrail',(x,0,rise+.9),(x,17*run,3.2+.9),.035,'gold',r)
    r['floor_rise_m']=3.2;r['steps']=18
    return r

def fixture(name):
    r=root(name)
    if name=='ceiling_lamp':
        cyl('stem',(0,0,-.17),.025,.34,'gold',r);cyl('shade',(0,0,-.37),.28,.12,'ink',r);cyl('diffuser',(0,0,-.44),.24,.02,'light',r)
    elif name=='door_sensor':
        cube('body',(0,0,0),(.07,.04,.12),'steel',r,.01);cube('indicator',(0,-.024,.025),(.025,.008,.02),'rose',r,.002)
    elif name=='reinforcement_bar':
        cube('bar',(0,0,0),(1.42,.12,.18),'steel',r,.015)
        for x in [-.6,.6]:
            cube('bracket',(x,0,0),(.14,.18,.32),'ink',r,.01)
            for z in [-.11,.11]:
                o=cyl('bolt',(x,-.105,z),.025,.02,'gold',r,6);o.rotation_euler.x=math.pi/2
    elif name=='wall_notice_plate':
        cube('frame',(0,0,0),(.44,.05,.30),'ink',r,.015);cube('blank_insert',(0,-.031,0),(.38,.01,.24),'paper',r,.002)
        r['text_baked']=False
    elif name=='kitchen_counter':
        cube('cabinet',(0,0,.43),(1.8,.65,.86),'white',r);cube('steel_top',(0,0,.9),(1.86,.7,.07),'steel',r,.018)
        for x in [-.44,.44]:
            cube('door',(x,-.34,.46),(.85,.035,.7),'ivory',r,.012);bar('handle',(x-.12,-.38,.65),(x+.12,-.38,.65),.015,'ink',r)
    elif name=='archive_box':
        cube('box',(0,0,.18),(.48,.36,.36),'ivory',r);cube('lid',(0,0,.38),(.5,.38,.05),'wood',r)
        cube('label',(0,-.19,.2),(.23,.015,.09),'paper',r,.004);r['text_baked']=False
    elif name=='fountain_nozzle':
        cyl('basin',(0,0,.22),1.7,.44,'ink',r,48);cyl('inside',(0,0,.46),1.48,.035,'glass',r,48)
        cyl('pedestal',(0,0,.72),.3,.5,'ivory',r);cyl('nozzle',(0,0,1),.1,.09,'gold',r)
        r['water_is_optional_separate_effect']=True
    return r

def bed():
    r=root('single_bed');cube('bed_base',(0,0,.27),(1.05,2.1,.38),'ink',r,.05)
    cube('mattress',(0,0,.54),(1.02,2.04,.24),'paper',r,.09)
    cube('blanket',(0,-.3,.68),(1.04,1.35,.09),'purple',r,.045)
    cube('pillow',(0,.71,.73),(.76,.42,.13),'white',r,.09)
    cube('headboard',(0,1.07,.65),(1.15,.12,1.2),'wood',r,.04)
    for x in [-.5,.5]:cube('head_trim',(x,1,.7),(.035,.035,1.05),'gold',r,.004)
    return r

def cabinet():
    r=root('storage_cabinet');cube('body',(0,0,.95),(1.3,.55,1.9),'wood',r,.03)
    for x in [-.32,.32]:
        cube('door',(x,-.3,.95),(.61,.06,1.72),'ivory',r,.025)
        bar('handle',(x+(-.2 if x>0 else .2),-.35,.8),(x+(-.2 if x>0 else .2),-.35,1.13),.015,'gold',r)
    return r

def medical_screen():
    r=root('privacy_screen')
    for x in [-.85,.85]:
        bar('post',(x,0,.1),(x,0,1.85),.022,'steel',r);bar('foot',(x,-.28,.1),(x,.28,.1),.025,'steel',r)
    bar('top',(-.85,0,1.83),(.85,0,1.83),.025,'steel',r)
    for j in range(17):cube('pleat',(-.8+j*.1,(-1 if j%2 else 1)*.025,1.03),(.11,.045,1.47),'ivory' if j%2 else 'paper',r,.008)
    return r

def reception():
    r=root('reception_counter');cube('base',(0,0,.55),(3.4,.9,1.1),'purple',r,.045)
    cube('top',(0,0,1.14),(3.6,1.06,.12),'wood',r,.04)
    for x in [-1.5,0,1.5]:cube('vertical_inlay',(x,-.47,.55),(.05,.025,.9),'gold',r,.006)
    cube('plinth',(0,0,.08),(3.5,.98,.16),'ink',r,.025);return r

def laundry():
    r=root('washing_machine');cube('body',(0,0,.47),(.68,.66,.94),'white',r,.04)
    for name,rad,dep,y,mat in [('rim',.24,.04,-.35,'steel'),('window',.195,.045,-.378,'glass')]:
        o=cyl(name,(0,y,.48),rad,dep,mat,r,40);o.rotation_euler.x=math.pi/2
    cube('controls',(0,-.34,.84),(.58,.025,.09),'ink',r,.008)
    for x in [-.2,0,.2]:
        o=cyl('knob',(x,-.37,.84),.025,.025,'ivory',r,12);o.rotation_euler.x=math.pi/2
    return r

def sconce():
    r=root('wall_sconce');cube('backplate',(0,0,0),(.18,.06,.42),'ink',r,.03)
    bar('arm',(0,-.03,-.06),(0,-.23,-.06),.02,'gold',r)
    cube('lantern',(0,-.24,.08),(.17,.17,.28),'light',r,.025)
    for x in [-.09,.09]:cube('guard',(x,-.24,.08),(.015,.2,.32),'ink',r,.004)
    return r

def key_rack():
    r=root('hotel_key_rack');cube('back',(0,0,.75),(1.7,.12,1.5),'wood',r,.025)
    for x in range(4):
        for y in range(4):
            xx=-.63+x*.42;zz=.18+y*.34
            cube('compartment',(xx,-.075,zz),(.34,.025,.25),'ink',r,.004)
            cube('label',(xx,-.09,zz-.085),(.19,.012,.055),'paper',r,.003)
            bar('hook',(xx,-.095,zz+.02),(xx,-.16,zz+.02),.011,'gold',r)
    r['slots']=16;r['labels_runtime_authored']=True;return r

ASSETS={}
for fn in [floor,wall,doorframe,door,window,table,chair,bench,shelf,podium,chest,printer,console,clock,microphone,mirror,stairs,bed,cabinet,medical_screen,reception,laundry,sconce,key_rack]:
    o=fn();ASSETS[o.name]=o
for n in ['ceiling_lamp','door_sensor','reinforcement_bar','wall_notice_plate','kitchen_counter','archive_box','fountain_nozzle']:
    ASSETS[n]=fixture(n)

def family(r):return [r]+list(r.children_recursive)

def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)

def export(r,path):
    select(family(r));bpy.context.view_layer.objects.active=r
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_extras=True,export_apply=True,export_lights=True)

asset_records=[]
for name,r in ASSETS.items():
    bpy.context.view_layer.update();export(r,OUT/(name+'.glb'))
    boxes=[]
    for o in r.children_recursive:
        if o.type=='MESH':boxes.append({'node':o.name,'center_blender':list(o.matrix_world.translation),'size_local':list(o.dimensions)})
    asset_records.append({'id':name,'file':(OUT/(name+'.glb')).relative_to(ROOT).as_posix(),'nodes':len(family(r)),'mesh_count':sum(o.type=='MESH' for o in family(r)),'inspection_bounds':boxes,'interaction':{k:r[k] for k in r.keys()},'runtime_integrated':False})

# Preserve authored kit separately from room instances; collections are independently exportable.
for r in ASSETS.values():
    for o in family(r):o.hide_render=True

def instance(asset,parent,loc=(0,0,0),rz=0):
    src=ASSETS[asset];mapping={}
    for old in family(src):
        new=old.copy();new.name=parent.name+'_'+old.name;scene.collection.objects.link(new);new.hide_render=False;mapping[old]=new
    for old,new in mapping.items():new.parent=mapping.get(old.parent,parent)
    newroot=mapping[src];newroot.location=loc;newroot.rotation_euler.z=rz;return newroot

rooms=[]
def room_shell(name,w,d,mode):
    r=root(name);height=6.6 if name=='hotel_lobby' else 3.2
    cube('floor',(0,0,-.12),(w,d,.24),'ink',r)
    def wall_parts(label,length,pos,angle,holes):
        group=empty(label,r,pos);group.rotation_euler.z=angle
        cuts=sorted(set([-length/2,length/2]+[v for h in holes for v in [h[0]-h[1]/2,h[0]+h[1]/2]]))
        for lo,hi in zip(cuts,cuts[1:]):
            mid=(lo+hi)/2;hole=next((h for h in holes if h[0]-h[1]/2<mid<h[0]+h[1]/2),None)
            spans=[(0,height)] if hole is None else [(0,hole[2]),(hole[2]+hole[3],height)]
            for z0,z1 in spans:
                if z1-z0>.001:cube(label+'_wall', (mid,0,(z0+z1)/2),(hi-lo,.18,z1-z0),'paper',group,.008)
            if hole is None:
                cube(label+'_wainscot',(mid,-.11,.5),(hi-lo,.04,1),'purple',group,.006)
                cube(label+'_rail',(mid,-.14,1.02),(hi-lo,.05,.055),'gold',group,.006)
                cube(label+'_skirt',(mid,-.14,.1),(hi-lo,.06,.12),'ink',group,.006)
                for k in range(max(1,int((hi-lo)/1.25))):
                    xx=lo+(k+.5)*(hi-lo)/max(1,int((hi-lo)/1.25))
                    cube(label+'_panel_strip',(xx,-.145,.53),(.025,.035,.72),'gold',group,.004)
                if hi-lo>1.7:
                    cube(label+'_upper_inset',(mid,-.105,2.05),(min(hi-lo-.4,2.3),.035,1.25),'ivory',group,.025)
                    for z in [1.42,2.68]:cube(label+'_inset_edge',(mid,-.13,z),(min(hi-lo-.4,2.3),.025,.025),'gold',group,.003)
                    instance('wall_sconce',group,(mid,-.14,2.05))
        return group
    back_holes=[(2.6,1.18,0,2.5),(0,2.08,.8,1.62)] if name=='service_lounge' else ([(-4,1.18,3.2,2.5)] if name=='hotel_lobby' else ([(2.6,1.18,0,2.5)] if name=='management_office' else []))
    if os.environ.get('V4_SPACE_FULL')=='1' and name=='theatre_preparation':back_holes=[(0,1.18,0,2.5)]
    wall_parts('back',w,(0,d/2,0),0,back_holes)
    side_holes=[(v,1.18,0,2.5) for v in HOTEL_DOOR_Y] if name=='hotel_corridor' else []
    wall_parts('left',d,(-w/2,0,0),-math.pi/2,side_holes)
    wall_parts('right',d,(w/2,0,0),math.pi/2,side_holes)
    wall_parts('front',w,(0,-d/2,0),math.pi,[(0,1.18,0,2.5)])
    cube('ceiling_surface',(0,0,height+.06),(w,d,.12),'ivory',r,.005)
    for y in range(-int(d/2)+1,int(d/2),3):cube('ceiling_beam',(0,y,height-.06),(w,.1,.14),'ink',r,.008)
    for x in [-w/2+.25,w/2-.25]:cube('ceiling_border',(x,0,height-.08),(.13,d,.17),'purple',r,.01)
    for y in [-d*.25,d*.25]:
        bpy.ops.object.light_add(type='POINT',location=(0,0,0));lamp=bpy.context.object;lamp.name=name+'_interior_light';lamp.parent=r;lamp.location=(0,y,min(height-.45,4));lamp.data.energy=280;lamp.data.shadow_soft_size=.9
    if name!='service_lounge':
        instance('door_frame_1m',r,(0,-d/2,0));instance('door_hinged_1m',r,(0,-d/2,0))
    for y in [-d/2+.2,d/2-.2]:cube('ceiling_trim',(0,y,3.08),(w,.14,.18),'purple',r)
    r['preview_cutaway_front']=True
    rec={'id':name,'mode':mode,'size_m':[w,d,height],'source_axes':'Blender Z-up, glTF exported Y-up','runtime_integrated':False,'front_wall':'included in GLB; temporarily hidden for inspection render only','targets':[]}
    if mode=='fixed_orbit':rec['camera']={'center_blender':[0,0,1.25],'radius':min(w,d)*.34,'pitch_limits_degrees':[-10,7],'manual_translation':False,'yaw_limits_degrees':[-155,155]}
    else:rec['camera']={'eye_height':1.55,'manual_translation':True,'spawn_blender':[0,-d/2+1,0]}
    rooms.append((r,rec));print('Authored room shell',name,flush=True);return r,rec

r,meta=room_shell('service_lounge',9,8,'fixed_orbit')
instance('meeting_table',r,(0,.2,0));instance('chair',r,(-1.4,.2,0),math.pi/2);instance('chair',r,(1.4,.2,0),-math.pi/2)
instance('printer',r,(-.6,.2,.82));instance('book_shelf',r,(-3.1,3.65,0));instance('fixed_window_2m',r,(0,3.83,0))
instance('door_frame_1m',r,(2.6,3.8,0));instance('door_hinged_1m',r,(2.6,3.8,0));instance('reinforcement_bar',r,(2.6,3.97,1.1))
instance('door_frame_1m',r,(0,-4,0));instance('door_hinged_1m',r,(0,-4,0));instance('door_sensor',r,(.6,-4.2,2.1))
instance('wall_notice_plate',r,(1,-4.02,1.55));instance('wall_clock',r,(-2.5,3.8,2.4))
meta['targets']=[{'id':'door_A','node_hint':'front door','position_blender':[0,-4,1.2]},{'id':'door_B','position_blender':[2.6,3.8,1.2],'external_bar':True},{'id':'printer','position_blender':[-.6,.2,1.1]},{'id':'fixed_window','position_blender':[0,3.8,1.6]}]
meta['source']='rewrite_v4/03 and 11b; candidate authored geometry, not final scene acceptance'

r,meta=room_shell('hotel_corridor',4.2,HOTEL_CORRIDOR_LENGTH,'free_walk')
for y in HOTEL_DOOR_Y:
    for side in [-1,1]:
        instance('door_frame_1m',r,(side*2.0,y,0),side*math.pi/2);instance('door_hinged_1m',r,(side*2.0,y,0),side*math.pi/2)
    instance('ceiling_lamp',r,(0,y,3.15))
cube('carpet',(0,0,.02),(2.6,HOTEL_CORRIDOR_LENGTH,.035),'rose',r,.003)
for x in [-1.22,1.22]:cube('runner_border',(x,0,.044),(.025,HOTEL_CORRIDOR_LENGTH,.008),'gold',r,.001)
for y in range(-26,27,2):
    marker=cube('runner_diamond',(0,y,.045),(.17,.17,.008),'ivory',r,.002);marker.rotation_euler.z=math.pi/4
meta['targets']=[{'id':f'door_{side}_{i}','position_blender':[side*2,y,1.2]} for i,y in enumerate(HOTEL_DOOR_Y) for side in [-1,1]]
meta['guest_room_pitch_m']=7
meta['layout_reason']='6m room frontage requires at least 6m pitch; 7m pitch avoids overlapping physical rooms'

r,meta=room_shell('courtroom',18,18,'scripted_court')
cyl('central_disc',(0,0,.025),6.6,.05,'purple',r,64)
for i in range(16):
    a=i*math.tau/16;x,y=5.5*math.sin(a),5.5*math.cos(a)
    instance('trial_podium',r,(x,y,0),-a)
    meta['targets'].append({'id':f'seat_{i:02}','podium_blender':[x,y,0],'actor_foot_blender':[6.22*math.sin(a),6.22*math.cos(a),0]})
cube('host_dais',(0,7.4,.3),(4,2,.6),'ink',r)
for x in [-7,-4,0,4,7]:instance('ceiling_lamp',r,(x,4,3.2))
meta['camera']={'manual_translation':False,'purpose':'authored speaker-relative shots; preserve 16 standing positions'}

r,meta=room_shell('dining_room',12,10,'fixed_orbit')
for x in [-2.3,2.3]:
    instance('meeting_table',r,(x,0,0),math.pi/2)
    for y in [-.8,.8]:
        for side in [-1,1]:instance('chair',r,(x+side*.85,y,0),-side*math.pi/2)
for x in [-4,0,4]:instance('kitchen_counter',r,(x,4.4,0))

r,meta=room_shell('theatre_preparation',10,8,'fixed_orbit')
instance('blue_props_chest',r,(-2.7,.5,0));instance('microphone_stand',r,(.7,.3,0));instance('book_shelf',r,(3.5,3.6,0));instance('control_console',r,(0,3.5,0))
for x in [-1.5,1.5]:instance('chair',r,(x,-.5,0),math.pi)
meta['source']='rewrite_v4/05; props chest and microphone are independent objects; no body/trace baked'

r,meta=room_shell('archive_room',12,10,'fixed_orbit')
for x in [-4,-1.6,1.6,4]:
    for y in [0,3]:instance('book_shelf',r,(x,y,0))
instance('meeting_table',r,(0,-3,0));instance('archive_box',r,(.5,-3,.82))

r,meta=room_shell('central_control',12,9,'fixed_orbit')
for x in [-4,-2,0,2,4]:instance('control_console',r,(x,3.5,0))
instance('meeting_table',r,(0,-1,0));instance('wall_clock',r,(0,4.3,2.6))

r,meta=room_shell('plaza',28,28,'free_walk')
# Exterior cutaway has no room walls; remove the temporary shell walls.
for o in list(r.children):
    if o.name.startswith(('back','left','right','front','ceiling','baseboard')):
        for child in list(o.children_recursive):bpy.data.objects.remove(child,do_unlink=True)
        bpy.data.objects.remove(o,do_unlink=True)
instance('fountain_nozzle',r,(0,0,0))
for x in [-5,5]:
    for y in [-5,5]:instance('park_bench',r,(x,y,0),math.pi if y<0 else 0)
meta['sky']='runtime environment, never a baked background panorama'

r,meta=room_shell('hotel_lobby',14,12,'free_walk')
instance('reception_counter',r,(0,4,0));instance('control_console',r,(0,5.1,0))
instance('hotel_key_rack',r,(3,5.8,1.12))
for x in [-4.5,4.5]:
    instance('park_bench',r,(x,0,0),-math.pi/2 if x>0 else math.pi/2)
    instance('fixed_window_2m',r,(x,5.8,0))
instance('stairs_18',r,(-4,-.2,0));instance('wall_clock',r,(0,5.8,2.6))
cube('upper_landing',(-4,5.15,3.12),(1.85,1.5,.16),'ivory',r,.012)
instance('door_frame_1m',r,(-4,5.9,3.2));instance('door_hinged_1m',r,(-4,5.9,3.2))
meta['upper_landing_blender']=[-4,5.15,3.2]

r,meta=room_shell('guest_room',6,7,'fixed_orbit')
instance('single_bed',r,(-1.8,1.1,0));instance('meeting_table',r,(1.35,1.6,0),math.pi/2)
instance('chair',r,(.6,1.6,0),math.pi/2);instance('storage_cabinet',r,(1.8,-2.2,0),math.pi/2)
instance('fixed_window_2m',r,(0,3.35,0));instance('ceiling_lamp',r,(0,0,3.1))

r,meta=room_shell('clinic',10,9,'fixed_orbit')
for x in [-3,0,3]:
    instance('single_bed',r,(x,2,0));instance('privacy_screen',r,(x-1.15,1,0),math.pi/2)
instance('storage_cabinet',r,(-3.8,-2,0),-math.pi/2);instance('meeting_table',r,(2.5,-2,0));instance('chair',r,(2.5,-3,0),math.pi)

r,meta=room_shell('kitchen',12,10,'fixed_orbit')
for x in [-4,-2,0,2,4]:instance('kitchen_counter',r,(x,4.3,0))
for x in [-2,2]:instance('kitchen_counter',r,(x,0,0))
instance('storage_cabinet',r,(-5.5,0,0),-math.pi/2)

r,meta=room_shell('laundry_room',8,8,'fixed_orbit')
for x in [-2.5,-1.5,-.5,.5,1.5,2.5]:instance('washing_machine',r,(x,3.3,0))
instance('meeting_table',r,(0,-.7,0));instance('storage_cabinet',r,(-3.3,0,0),-math.pi/2)

if os.environ.get('V4_SPACE_DETAIL')=='1':
    import sys
    sys.path.insert(0,str(ROOT/'tools'))
    from build_v4_space_detail import enrich
    enrich(globals())

if os.environ.get('V4_SPACE_FULL')=='1':
    import sys
    sys.path.insert(0,str(ROOT/'tools'))
    from build_v4_world_spaces import expand
    expand(globals())

for r,rec in rooms:
    bpy.context.view_layer.update()
    collisions=[]
    for o in r.children_recursive:
        if o.type!='MESH':continue
        pts=[o.matrix_world@Vector(c) for c in o.bound_box]
        lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
        collisions.append({'node':o.name,'min_blender':lo,'max_blender':hi,'candidate_only':True,'requires_interaction_filter':'hinge' in o.name or 'leaf' in o.name})
    rec['collision_candidates']=collisions
    export(r,OUT/(r.name+'.glb'));rec['file']=(OUT/(r.name+'.glb')).relative_to(ROOT).as_posix()
    for o in family(r):o.hide_render=True

# Render evidence is produced from the same geometry; it is never used as a walkable backdrop.
world=bpy.data.worlds.new('preview_world');world.use_nodes=True;scene.world=world
world.node_tree.nodes.get('Background').inputs[0].default_value=(.12,.13,.17,1)
world.node_tree.nodes.get('Background').inputs[1].default_value=.5
if os.environ.get('V4_SPACE_DETAIL')=='1':
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='Medium High Contrast'
    scene.view_settings.exposure=-1.2
    world.node_tree.nodes.get('Background').inputs[1].default_value=.25
bpy.ops.object.light_add(type='AREA',location=(0,-6,10));light=bpy.context.object;light.name='preview_key';light.data.energy=2400;light.data.shape='DISK';light.data.size=10
bpy.ops.object.light_add(type='AREA',location=(7,5,7));bpy.context.object.data.energy=1600;bpy.context.object.data.size=8
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='preview_camera';scene.camera=cam;cam.data.lens=33
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.render.resolution_x=960;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
for r,rec in rooms:
    if PREVIEW_ONLY and r.name not in PREVIEW_ONLY:continue
    for o in family(r):o.hide_render=False
    for o in r.children:
        if o.name.startswith(('front','ceiling')):
            for part in family(o):part.hide_render=True
    w,d,_=rec['size_m'];cam.location=(w*.8,-d*.92,max(w,d)*.65);target=Vector((0,0,1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(PREVIEW/(r.name+'.png'));bpy.ops.render.render(write_still=True)
    for o in family(r):o.hide_render=True
# Inside-camera renders prove perspective from the authored modes, not only cutaway views.
for r,rec in rooms:
    if PREVIEW_ONLY and r.name not in PREVIEW_ONLY:continue
    if rec['mode']=='scripted_court':continue
    for o in family(r):o.hide_render=False
    views=[('center',0),('left',-35),('right',35)] if rec['mode'] in ('fixed_orbit','fixed_pan') else [('entry',0),('turn',25)]
    for label,angle in views:
        a=math.radians(angle)
        if rec['mode']=='fixed_pan':
            cam.location=rec['camera']['eye_blender'];target=Vector((cam.location.x+math.sin(a)*5,cam.location.y+math.cos(a)*5,1.35))
        elif rec['mode']=='fixed_orbit':
            radius=rec['camera']['radius'];cam.location=(math.sin(a)*radius,-math.cos(a)*radius,1.6);target=Vector((0,0,1.35))
        else:
            cam.location=(0,-rec['size_m'][1]/2+1.4,1.6);target=Vector((math.sin(a)*5,cam.location.y+math.cos(a)*5,1.55))
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(70)
        scene.render.filepath=str(PREVIEW/(r.name+'_'+label+'.png'));bpy.ops.render.render(write_still=True)
    for o in family(r):o.hide_render=True
manifest={'status':'authored original mesh kit and room candidates; not game-integrated','units':'authored meters, not measured original-game meters','axes':'Blender Z-up; GLB standard Y-up','models':asset_records,'spaces':[rec for _,rec in rooms],'limits':['room preview front wall is cut away only in inspection render; GLB has segmented walls','mirror material needs runtime reflection','normal/incident states and original-world global topology not completed','not a reconstruction of original meshes']}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,default=list)+'\n',encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'space_kit_source.blend'))
print('V4_SPACE_COMPLETE',len(asset_records),'kit models',len(rooms),'space candidates')
