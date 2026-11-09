"""Blender CLI: source-constrained original production sets; no game execution.

Run: blender --background --python tools/build_v4_dedicated_spaces.py
All outputs are separate from the approved common meshes. Coordinates are our
game's authored layout, never recovered original-game or historical measurements.
"""
from pathlib import Path
import hashlib
import html
import json
import math
import os
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art/space_v4/dedicated_v1'
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'maps').mkdir(exist_ok=True)
(OUT/'preview').mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
SCENE=bpy.context.scene
SCENE.unit_settings.system='METRIC'
M={};ROOMS=[];TEMPLATES={};TEMPLATE_OBJECTS=[]
PALETTE={'paper':(.79,.73,.62,1),'ivory':(.55,.49,.38,1),'wood':(.17,.075,.047,1),
 'purple':(.13,.046,.21,1),'wine':(.40,.055,.12,1),'ink':(.024,.019,.036,1),
 'gold':(.47,.28,.075,1),'steel':(.18,.25,.29,1),'green':(.052,.19,.10,1),
 'leaf':(.10,.30,.14,1),'blue':(.035,.17,.34,1),'red':(.58,.055,.085,1),
 'light':(1,.64,.25,1),'white':(.82,.83,.78,1),'rubber':(.025,.032,.048,1),
 'glass':(.35,.58,.61,.22),'mirror':(.68,.77,.82,1)}
for name,color in PALETTE.items():
    mat=bpy.data.materials.new('dedicated_'+name);mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color
    bs.inputs['Roughness'].default_value=.67
    if name in ['steel','gold']:bs.inputs['Metallic'].default_value=.7;bs.inputs['Roughness'].default_value=.3
    if name=='mirror':bs.inputs['Metallic'].default_value=1;bs.inputs['Roughness'].default_value=.055
    if name=='glass':bs.inputs['Alpha'].default_value=.22;bs.inputs['Roughness'].default_value=.12
    if name=='light':bs.inputs['Emission Color'].default_value=color;bs.inputs['Emission Strength'].default_value=2.3
    M[name]=mat


def xyz(v):return [round(v[0],4),round(v[2],4),round(-v[1],4)]
def write(name,value):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')


def empty(name,parent=None,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);SCENE.collection.objects.link(o);o.parent=parent;o.location=loc;return o


def cube(name,loc,size,mat,parent,solid=False,bevel=.018):
    x,y,z=[a/2 for a in size]
    mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata([(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for face in mesh.polygons:
        axes=[i for i in range(3) if i!=max(range(3),key=lambda j:abs(face.normal[j]))]
        for li in face.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]/2,v[axes[1]]/2)
    o=bpy.data.objects.new(name,mesh);SCENE.collection.objects.link(o);o.parent=parent;o.location=loc;o.data.materials.append(M[mat])
    if bevel:
        mod=o.modifiers.new('rounded_ink_edge','BEVEL');mod.width=min(bevel,min(size)/4);mod.segments=2
        o.modifiers.new('weighted_cel_normals','WEIGHTED_NORMAL')
    o['production_collider']=solid
    return o


def cylinder(name,loc,radius,depth,mat,parent,solid=False,vertices=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=(0,0,0))
    o=bpy.context.object;o.name=name;o.parent=parent;o.location=loc;o.data.materials.append(M[mat]);o['production_collider']=solid
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o


def bar(name,a,b,r,mat,parent,solid=False):
    a,b=Vector(a),Vector(b);o=cylinder(name,(a+b)/2,r,(b-a).length,mat,parent,solid,12)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def sphere(name,loc,scale,mat,parent):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=(0,0,0))
    o=bpy.context.object;o.name=name;o.parent=parent;o.location=loc;o.scale=scale;o.data.materials.append(M[mat]);return o


def family(o):return [o]+list(o.children_recursive)


def imported(asset,parent,loc=(0,0,0),angle=0,scale=1,solid=True,omit_books=False):
    if asset not in TEMPLATES:
        path=ROOT/'art/space_v4/full_v2'/(asset+'.glb')
        if not path.exists():raise FileNotFoundError(path)
        before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));items=list(set(bpy.data.objects)-before)
        TEMPLATES[asset]=items;TEMPLATE_OBJECTS.extend(items)
        for o in items:o.hide_render=True;o.hide_set(True)
    group=empty('set_'+asset,parent,loc);group.rotation_euler.z=angle;group.scale=(scale,)*3
    mapping={o:o.copy() for o in TEMPLATES[asset] if not (omit_books and o.name.split('.')[0]=='book')}
    for old,new in mapping.items():
        SCENE.collection.objects.link(new);new.name='set_'+old.name;new.parent=mapping.get(old.parent,group)
        new.hide_render=False;new.hide_set(False)
        # Object names remain precise and editable; collision uses a single
        # furniture envelope rather than every book/page as a separate blocker.
        new['production_collider']=False
    group['production_furniture_collider']=solid
    return group


def light(parent,loc,energy=250,color=(1,.73,.42),size=3):
    data=bpy.data.lights.new('warm_set_light','AREA');data.energy=energy;data.color=color;data.shape='DISK';data.size=size
    o=bpy.data.objects.new('set_light',data);SCENE.collection.objects.link(o);o.parent=parent;o.location=loc
    return o


def room(sid,label,w,d,h=3.4,spawn=(0,-3.5,1.6),open_front=False,glass_roof=False,mode='free_walk',floor_hole=None):
    r=empty(sid);rec={'id':sid,'label':label,'mode':mode,'size_m':[w,d,h],'spawn_blender':list(spawn),
        'targets':[],'walk_surfaces_blender':[[-w/2,-d/2,w/2,d/2,0]],'portals':[],
        'source_constraints':[],'historicalGeometryRecovered':False,'runtime_tested':False}
    ROOMS.append((r,rec))
    if floor_hole:
        ax,ay,bx,by=floor_hole
        for lo,hi in [((-w/2,-d/2),(w/2,ay)),((-w/2,by),(w/2,d/2)),((-w/2,ay),(ax,by)),((bx,ay),(w/2,by))]:
            if hi[0]>lo[0] and hi[1]>lo[1]:cube('segmented_floor',((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,-.11),(hi[0]-lo[0],hi[1]-lo[1],.22),'ink',r)
    else:cube('floor',(0,0,-.11),(w,d,.22),'ink',r)
    for x in range(math.ceil(w)):
        for y in range(math.ceil(d)):
            if floor_hole and -w/2+x+1>floor_hole[0] and -w/2+x<floor_hole[2] and -d/2+y+1>floor_hole[1] and -d/2+y<floor_hole[3]:continue
            cube('ivory_floor_tile',(-w/2+x+.5,-d/2+y+.5,.012),(.988,.988,.024),'ivory' if (x+y)%3 else 'paper',r,False,.003)
    # Warm ivory above violet panelling and walnut/brass trim is the existing
    # authored environment style; no original-game material is imported.
    for side,length,origin,angle in [('north',w,(0,d/2,0),0),('west',d,(-w/2,0,0),math.pi/2),('east',d,(w/2,0,0),-math.pi/2)]:
        wall=empty('wall_'+side,r,origin);wall.rotation_euler.z=angle
        cube('structural_wall',(0,0,h/2),(length,.18,h),'paper',wall,True)
        cube('violet_wainscot',(0,-.11,.54),(length,.05,1.08),'purple',wall)
        for z,t in [(.12,.09),(1.1,.06),(h-.15,.08)]:cube('walnut_moulding',(0,-.15,z),(length,.07,t),'wood',wall)
        cube('brass_midrail',(0,-.19,1.16),(length,.035,.027),'gold',wall)
        for x in [(-length/2+.7)+i*1.6 for i in range(max(1,int((length-1)/1.6)))]:
            for z,hh in [(.58,.72),(h-.85,.85)]:
                for xx in [x-.62,x+.62]:cube('brass_panel_frame',(xx,-.145,z),(.018,.035,hh),'gold',wall,False,.003)
                for zz in [z-hh/2,z+hh/2]:cube('brass_panel_frame',(x,-.145,zz),(1.26,.035,.018),'gold',wall,False,.003)
    if not open_front:
        # Real segmented doorway; no frame painted on a solid wall.
        for x in [-w/4-.38,w/4+.38]:cube('front_wall',(x,-d/2,h/2),(w/2-.76,.18,h),'paper',r,True)
        cube('front_lintel',(0,-d/2,(h+2.5)/2),(1.52,.18,h-2.5),'paper',r,True)
        for x in [-.76,.76]:cube('door_brass_jamb',(x,-d/2,1.25),(.1,.32,2.5),'gold',r,True)
        cube('threshold',(0,-d/2,.035),(1.45,.4,.07),'steel',r)
        rec['portals']=[{'id':'entry','p':xyz((0,-d/2,1.2)),'clear_width_m':1.4}]
    if glass_roof:
        cube('glass_roof',(0,0,h+.05),(w,d,.06),'glass',r)
        for x in [-w/2,-w/4,0,w/4,w/2]:cube('roof_brass_rib',(x,0,h+.08),(.06,d,.08),'gold',r)
        for y in [-d/2,0,d/2]:cube('roof_cross_rib',(0,y,h+.08),(w,.06,.08),'wood',r)
    elif not open_front:cube('ceiling',(0,0,h+.05),(w,d,.1),'paper',r)
    for x in [-w*.28,w*.28]:
        light(r,(x,0,h-.18),380,size=4)
        if not glass_roof:imported('ceiling_lamp',r,(x,0,h-.1),solid=False)
    return r,rec


def target(rec,id,p,label):rec['targets'].append({'id':id,'p':xyz(p),'label':label})


# 1. Current core exterior inspection deck, main entry and separate side entry.
r,m=room('core_external_inspection','코어 홀 바깥 점검 구역',12,11,4,spawn=(-1.5,-4.1,1.6),open_front=True,floor_hole=(-5.15,2.15,2.6,5.25))
# Two physically separate current approaches. A single painted/labelled doorway
# must not stand in for the source's main inspection vs side management entry.
for left,right in [(-6,-2.2),(-.8,3.55),(4.95,6)]:
    cube('core_front_segment',((left+right)/2,-5.5,2),(right-left,.18,4),'paper',r,True)
for x in [-1.5,4.25]:
    cube('core_entry_lintel',(x,-5.5,3.25),(1.4,.18,1.5),'paper',r,True)
    for xx in [x-.7,x+.7]:cube('core_entry_jamb',(xx,-5.5,1.25),(.1,.24,2.5),'gold',r,True)
cube('core_ceiling',(0,0,4.05),(12,11,.1),'paper',r)
m['portals']=[{'id':'main_inspection','p':xyz((-1.5,-5.5,1.2)),'clear_width_m':1.3},{'id':'side_management','p':xyz((4.25,-5.5,1.2)),'clear_width_m':1.3}]
# Partition gives the management approach its own lane; the opening is real.
for y,depth in [(-1.15,4.7),(4.05,2.1)]:cube('side_management_partition',(2.8,y,1.7),(.2,depth,3.4),'steel',r,True)
cube('side_management_lintel',(2.8,2.05,3),(.2,1.7,.8),'steel',r,True)
for y in [1.2,2.9]:cube('side_door_frame',(2.8,y,1.3),(.24,.12,2.6),'gold',r,True)
hinge=empty('current_side_door_hinge',r,(2.85,2.83,0));hinge.rotation_euler.z=math.radians(72)
cube('current_replacement_door_leaf',(0,-.76,1.23),(.11,1.52,2.46),'steel',hinge,True)
cube('current_side_door_plate',(-.065,-.7,1.15),(.025,.35,.2),'gold',hinge)
# A guarded utility drop is current production geometry, not an old fall height.
cube('service_well_lower_floor',(-1.275,3.7,-1.4),(7.75,3.1,.16),'rubber',r)
cube('service_well_vertical_edge',(-1.275,2.2,-.7),(7.75,.12,1.4),'steel',r)
for x in [-5.05,-3.8,-2.5,-1.2,.1,1.4,2.5]:
    cube('current_guardrail_post',(x,2.03,.61),(.075,.075,1.22),'steel',r,True)
bar('current_replacement_toprail',(-5.05,2.03,1.25),(2.5,2.03,1.25),.048,'steel',r,True)
bar('current_replacement_midrail',(-5.05,2.03,.58),(2.5,2.03,.58),.025,'steel',r,True)
cube('guardrail_collision_barrier',(-1.275,2.03,.6),(7.7,.04,1.2),'steel',r,True)
# Transparent collision plate carries no visible fantasy barrier: hide only its
# mesh in render/export via a dedicated non-render collider record below.
invisible=bpy.data.objects.get('guardrail_collision_barrier');invisible.hide_render=True
invisible['metadata_collision_only']=True
for x in [-5.12,2.6]:
    for y in [2.03,3.15,4.3,5.35]:cube('well_side_rail_post',(x,y,.61),(.075,.075,1.22),'steel',r,True)
    for z,rr in [(1.25,.048),(.58,.025)]:bar('well_side_rail',(x,2.03,z),(x,5.35,z),rr,'steel',r,True)
    plate=cube('well_side_collision',(x,3.69,.6),(.04,3.36,1.2),'steel',r,True)
    plate.hide_render=True;plate['metadata_collision_only']=True
cube('replacement_identification_plaque',(-2.4,1.93,1.02),(.42,.05,.23),'ivory',r)
for x in [-2.55,-2.25]:cylinder('plaque_rivet',(x,1.9,1.02),.018,.02,'gold',r).rotation_euler.x=math.pi/2
for x in [-5.5,5.5]:
    bar('service_pipe',(x,-4,3.35),(x,4.5,3.35),.055,'steel',r)
    for y in [-3,0,3]:cube('pipe_wall_clip',(x,y,3.35),(.18,.08,.18),'gold',r)
cube('maintenance_ceiling_strip',(0,0,3.85),(4,.22,.08),'light',r)
target(m,'current_replacement_label',(-2.4,1.86,1.02),'현재 표찰과 당시 자료')
target(m,'side_management_entry',(2.72,2,1.2),'현재 관리 출입 비교')
target(m,'main_inspection_entry',(-1.5,-4.8,1.2),'주 점검 출입')
m['source_constraints']=['16b1:I6-03 현재 난간은 사고 후 교체','16b1:I6-05..08 주 통로와 나나의 옆 관리 출입은 별도','나나는 과거 홀 안에 들어가지 않고 문틈에서 보았다는 진술','현재 문/가림과 옛 도면·사진의 차이를 대조; 과거 각도·추락 높이는 미확정']
m['historicalSightVerified']=False
m['walk_surfaces_blender']=[[-5.8,-5.3,2.6,1.8,0],[2.95,-5.3,5.8,5.2,0],[-5.8,-5.3,5.8,-3.6,0]]

# 2. Glass-roof indoor garden and an adjacent rest/drawing corner.
r,m=room('hotel_indoor_garden','호텔 실내 정원',14,11,4.1,spawn=(-1.8,-4.2,1.6),glass_roof=True)
door=empty('garden_glass_door_hinge',r,(-.7,-5.5,0));door.rotation_euler.z=math.radians(68)
cube('garden_entry_glass_leaf',(.7,0,1.25),(1.4,.045,2.5),'glass',door,True)
for x in [0,1.4]:cube('garden_glass_door_stile',(x,0,1.25),(.055,.075,2.5),'gold',door,True)
for z in [.04,2.46]:cube('garden_glass_door_rail',(.7,0,z),(1.4,.075,.07),'gold',door,True)
cube('garden_door_handle',(1.19,-.08,1.15),(.035,.12,.3),'gold',door)
for x in [-5.2,-2.5]:
    for y in [-1.4,1.2,3.7]:
        imported('detail_planter',r,(x,y,0),solid=True)
        # Broad, individually modelled leaves give actual parallax, not a flat
        # backdrop or inaccessible foliage collision encompassing the path.
        for dx,dy,dz in [(-.27,0,.1),(.25,.1,.25),(0,-.22,.45)]:
            sphere('broad_garden_leaf',(x+dx,y+dy,1+dz),(.38,.12,.56),'leaf',r).rotation_euler.y=dx
imported('park_bench',r,(-.5,1.7,0),solid=True)
imported('meeting_table',r,(3.6,.6,0),solid=True)
for p,a in [((3.6,-.4,0),0),((3.6,1.6,0),math.pi)]:imported('chair',r,p,a,solid=True)
cube('rest_notice_board',(6.85,1.4,1.7),(.08,2.5,1.25),'wood',r)
cube('blank_drawing_mount',(6.79,1.4,1.72),(.03,1.6,.9),'paper',r)
target(m,'garden_bench',(-.5,1.4,.95),'벤치와 식물')
target(m,'garden_drawing_table',(3.6,.6,.86),'정원 옆 탁자')
target(m,'drawing_notice_board',(6.7,1.4,1.7),'게시판')
m['source_constraints']=['27/147 유리문·유리지붕·화분 줄·벤치','45/58 정원을 볼 수 있는 휴게 탁자와 그림 게시판','그림 속 벤치/기둥은 현장 신규 구조가 아니며 원본 그림은 별도 현재 상태']

# 3. Gift/toy shop: actual shelf recess, decorative keys, table and forecourt.
r,m=room('souvenir_shop','기념품·완구점',12,15,3.8,spawn=(0,-2.8,1.6),open_front=True)
# The front apron is physically outside the shop facade, rather than another
# label on an interior camera. The same editable mesh preserves the real entry.
for x in [-3.4,3.4]:cube('shop_front_facade',(x,-3.5,1.9),(5.2,.18,3.8),'paper',r,True)
cube('shop_entry_lintel',(0,-3.5,3.2),(1.6,.18,1.2),'wood',r,True)
for x in [-.8,.8]:cube('shop_entry_jamb',(x,-3.5,1.3),(.09,.23,2.6),'gold',r,True)
cube('shop_interior_ceiling',(0,2,3.85),(12,11,.1),'paper',r)
cube('shop_front_awning',(0,-5.45,3.5),(12,3.9,.12),'purple',r)
light(r,(0,-5.7,3.3),220,size=4)
imported('meeting_table',r,(-3.4,-5.45,0),solid=True)
for x in [-4.35,-2.45]:imported('chair',r,(x,-6.4,0),solid=True)
cube('plain_forecourt_mascot_board',(4.6,-4.05,1.2),(1.2,.12,2.4),'purple',r,True)
sphere('mascot_head_relief',(4.6,-4.16,1.88),(.36,.06,.34),'ivory',r)
target(m,'forecourt_game_table',(-3.4,-5.45,.86),'가게 앞 공용 탁자')
m['portals']=[{'id':'shop_entry','p':xyz((0,-3.5,1.2)),'clear_width_m':1.5}]
for x in [-4.7,-1.8,1.2,4.2]:imported('book_shelf',r,(x,4.7,0),solid=True,omit_books=True)
imported('meeting_table',r,(-2.9,.4,0),solid=True)
for x in [-3.8,-2]:imported('chair',r,(x,-.65,0),solid=True)
cube('checkout_counter',(4.2,-.1,.56),(2.7,1.15,1.12),'wood',r,True)
cube('checkout_cream_top',(4.2,-.1,1.15),(2.85,1.25,.1),'paper',r)
# An intentionally raised display has an actual open under-shelf recess.
for x in [.5,2.5]:cube('display_support',(x,2.6,.6),(.12,.7,1.2),'purple',r,True)
cube('raised_display_shelf',(1.5,2.6,1.24),(2.2,.75,.12),'wood',r,True)
cube('display_wall_key_board',(-5.85,.2,1.65),(.1,2.3,1.4),'purple',r)
for y in [-.65,-.1,.45,1.0]:
    ring=empty('decorative_key',r,(-5.72,y,1.85))
    bpy.ops.mesh.primitive_torus_add(major_radius=.085,minor_radius=.018,major_segments=16,minor_segments=6)
    o=bpy.context.object;o.name='decorative_key_ring';o.parent=ring;o.location=(0,0,0);o.rotation_euler.y=math.pi/2;o.data.materials.append(M['gold'])
    bar('decorative_key_shaft',(0,0,-.06),(0,0,-.35),.022,'gold',ring)
    cube('decorative_key_bit',(0,.035,-.3),(.045,.1,.06),'gold',ring)
for x in [-4.7,-1.8,1.2,4.2]:
    for y in [4.6]:
        for dx in [-.45,0,.45]:
            cube('toy_display_mount',(x+dx,y,.63),(.3,.25,.1),'purple',r)
            sphere('toy_goldfish_body',(x+dx,y,.775),(.14,.1,.095),'gold',r)
            sphere('toy_goldfish_tail',(x+dx+.15,y,.775),(.06,.04,.13),'wine',r)
            sphere('toy_eye',(x+dx-.1,y-.09,.805),(.015,.015,.015),'ink',r)
for x in [-4.7,-1.8,1.2,4.2]:
    car=empty('windup_display_car',r,(x,4.65,1.545))
    cube('toy_car_body',(0,0,.08),(.38,.22,.12),'blue',car)
    for xx in [-.12,.12]:
        for yy in [-.13,.13]:cylinder('toy_car_wheel',(xx,yy,.04),.065,.04,'rubber',car).rotation_euler.x=math.pi/2
target(m,'open_display_recess',(1.5,2.15,.45),'진열장 아래')
target(m,'decorative_keys',(-5.65,.2,1.55),'장식 진열')
target(m,'shop_game_table',(-2.9,.4,.86),'공용 탁자')
target(m,'checkout_display',(4.2,-.8,1.15),'진열대')
m['source_constraints']=['20/143 진열장 아래 실제 틈과 별도 장식용 열쇠','28/150 금붕어 인형과 계산대','30/90 카드놀이 탁자; 41 태엽차와 낮은 탁자','장식 열쇠는 객실·공구·약품 열쇠 아님; 상태별 수리·보유는 별도 대본']

# 4. Hotel rest space, distinct from the employee crime-scene lounge.
r,m=room('hotel_rest_lounge','호텔 공용 휴게실',13,11,3.6,spawn=(0,-3.8,1.6),mode='fixed_pan')
for x in [-3.5,3.5]:
    cube('sofa_plinth',(x,2,.18),(2.8,1.1,.36),'wood',r,True)
    cube('sofa_seat',(x,1.9,.48),(2.65,.95,.24),'wine',r)
    cube('sofa_back',(x,2.45,.92),(2.8,.22,.96),'purple',r,True)
    for dx in [-1.32,1.32]:cube('sofa_arm',(x+dx,1.9,.72),(.22,1.08,.48),'wood',r,True)
    imported('meeting_table',r,(x,.2,0),scale=.8,solid=True)
    imported('chair',r,(x,-1,0),solid=True)
for x in [-4.9,4.9]:imported('book_shelf',r,(x,4.75,0),solid=True)
cube('play_materials_shelf',(0,4.5,.6),(2.3,.55,1.2),'wood',r,True)
for z in [.33,.65,.97]:
    cube('plain_closed_game_box',(0,4.15,z),(1.7,.55,.17),'purple' if z<.8 else 'ivory',r)
imported('wall_clock',r,(0,5.35,2.65),solid=False)
target(m,'rest_table_left',(-3.5,.2,.73),'휴게 탁자')
target(m,'rest_table_right',(3.5,.2,.73),'휴게 탁자')
target(m,'play_book_shelf',(0,4.15,1.05),'놀이·도서 선반')
m['source_constraints']=['29/38/43/48/52/57 호텔 휴게실·놀이 선반·책','21/31/54/55/60/61/62 현재 대화의 공용 탁자와 소파','직원 휴게실/현장 방과 별개; 객실 번호나 새 회의실 이름 없음','판/책/찻잔/줄자 실제 사용·반납과 다른 사람 잔류는 source 분기로 처리']

# 5. Open common washroom with two sinks and a separate vanity surface.
r,m=room('hotel_washroom','호텔 공용 세면실',9,8,3.4,spawn=(0,-2.6,1.6),mode='fixed_pan')
for x in [-2.2,1.2]:
    imported('detail_sink_unit',r,(x,2.75,0),solid=True)
    cube('vanity_wall_mirror',(x,3.84,1.9),(2.3,.035,1.15),'mirror',r)
    for xx in [x-1.19,x+1.19]:cube('mirror_brass_border',(xx,3.8,1.9),(.045,.04,1.23),'gold',r)
    for zz in [1.28,2.52]:cube('mirror_brass_border',(x,3.8,zz),(2.43,.04,.045),'gold',r)
imported('meeting_table',r,(-2.4,-.25,0),scale=.65,solid=True)
cube('folded_shared_towel',(-2.4,-.25,.82),(.6,.35,.07),'white',r)
imported('storage_cabinet',r,(3.8,-.2,0),math.pi/2,scale=.7,solid=True)
target(m,'vanity_mirror',(-2.2,3.7,1.9),'거울과 세면대')
target(m,'vanity_work_surface',(-2.4,-.25,.86),'공용 작업면')
m['source_constraints']=['37 호텔 작은 공용 세면실·열린 문·거울 앞 수건','가위집/빗의 실제 사용과 반납은 대본 소유; 범행 도구로 새 의미 부여 금지','거울 PBR 표면은 원본 메시이며 실제 인물 반사 지원은 런타임 별도 확인']

# 6. A covered, open-front can-toss stall, not a ticket office or an exit gate.
r,m=room('can_toss_booth','공원 깡통 놀이부스',10,12,3.8,spawn=(0,-4.3,1.6),open_front=True)
cube('booth_counter',(0,3.1,.52),(6,1.1,1.04),'purple',r,True)
cube('booth_counter_top',(0,3.1,1.08),(6.2,1.24,.12),'wood',r)
for x in [-4.7,4.7]:cube('canopy_post',(x,0,1.9),(.15,.15,3.8),'wood',r,True)
for x in [-4.6+i*.5 for i in range(19)]:cube('striped_canopy',(x,0,3.8),(.5,12,.12),'wine' if int((x+4.6)*2)%2 else 'paper',r)
for row,(count,z) in enumerate([(3,1.3),(2,1.67),(1,2.04)]):
    for i in range(count):
        x=(i-(count-1)/2)*.42;o=cylinder(f'can_{row}_{i}',(x,2.95,z),.17,.33,'red' if row==2 or (row+i)%2 else 'blue',r)
        for zz in [-.15,.15]:cylinder('can_metal_rim',(x,2.95,z+zz),.176,.025,'steel',r)
        o['runtime_stateful_object']='six cans: source-specific remaining/knocked state, not a new victory condition'
for x in [-1.1,-.65,-.2]:sphere('soft_throw_ball',(x,-2.35,.13),(.13,.13,.13),'white',r)
cube('ordinary_throw_line',(0,-2.45,.045),(4.5,.07,.025),'ivory',r)
for x in [-3.7,3.7]:
    cube('prize_side_shelf',(x,4.85,1.45),(1.2,.65,.1),'wood',r)
    for dx in [-.3,.3]:sphere('ordinary_display_toy',(x+dx,4.85,1.75),(.2,.15,.25),'ivory',r)
target(m,'can_stack',(0,2.7,1.68),'놀이대')
target(m,'throwing_line',(0,-2.25,.25),'출발선')
target(m,'soft_balls',(-.65,-2.2,.25),'공 바구니 자리')
m['source_constraints']=['42/59 깡통 여섯(빨강·파랑 각셋),부드러운 공셋,같은 출발선','현재 각 판의 실제 승패/남은 깡통 수와 참가자는 별도 대본 상태','기념품·돈·통행권 자동 보상이나 새 출구 해금 없음']
m['stateful_render_limit']='Editable separate can/ball objects are present in GLB/.blend. Per-source knockdown/ball animation is a renderer integration channel, not proven by this static set.'


def bounds_of(objects):
    points=[o.matrix_world@Vector(c) for o in objects if o.type=='MESH' for c in o.bound_box]
    if not points:return None
    return [min(v[k] for v in points) for k in range(3)],[max(v[k] for v in points) for k in range(3)]


def runtime_record(r,rec):
    bpy.context.view_layer.update();boxes=[];nodes=[]
    for o in r.children_recursive:
        if o.type=='MESH':
            b=bounds_of([o]);lo,hi=b
            nodes.append({'id':o.name,'p':xyz((Vector(lo)+Vector(hi))/2),'box':[xyz(lo),xyz(hi)]})
            if o.get('production_collider'):boxes.append([lo[0],-hi[1],hi[0],-lo[1],lo[2],hi[2]])
        elif o.get('production_furniture_collider'):
            b=bounds_of(o.children_recursive)
            if b:
                lo,hi=b;boxes.append([lo[0],-hi[1],hi[0],-lo[1],lo[2],hi[2]])
    w,d,h=rec['size_m'];spawn=xyz(rec['spawn_blender'])
    result={'id':rec['id'],'label':rec['label'],'mode':rec['mode'],'mesh':'Assets/Art/explore3d/dedicated/'+rec['id']+'.glb',
      'bounds':[-w/2,-d/2,w/2,d/2],'floor':0,'eye_height':1.6,'spawn':spawn,'yaw':0,
      'pitch_limits':[-25,25],'yaw_limits':[-180,180] if rec['mode']=='free_walk' else [-155,155],
      'walk_surfaces':[[a,-dd,c,-b,z] for a,b,c,dd,z in rec['walk_surfaces_blender']],
      'footstep_surface':'metal' if rec['id']=='core_external_inspection' else 'tile',
      'collision':[[round(x,4) for x in box] for box in boxes],'targets':rec['targets'],'nodes':nodes,
      'map':'Assets/Art/explore3d/dedicated/map_'+rec['id']+'.svg',
      'coordinateSystem':'runtime-world-xyz','productionLayout':True,'reaGeometryRecovered':False,
      'portals':rec['portals'],
      'source_constraints':rec['source_constraints'],'runtime_tested':False}
    return result


def map_svg(spec):
    a,b,c,d=spec['bounds'];sx=600/(c-a);sz=600/(d-b)
    body=[]
    for x,z,xx,zz,lo,hi in spec['collision']:
        body.append(f'<rect x="{20+(x-a)*sx:.2f}" y="{20+(z-b)*sz:.2f}" width="{max(1,(xx-x)*sx):.2f}" height="{max(1,(zz-z)*sz):.2f}" fill="#665369" stroke="#be9b5a" stroke-width=".7"/>')
    for t in spec['targets']:
        x,y,z=t['p'];body.append(f'<circle cx="{20+(x-a)*sx:.1f}" cy="{20+(z-b)*sz:.1f}" r="6" fill="#a8d9d7"/>')
    x,y,z=spec['spawn'];body.append(f'<path d="M{20+(x-a)*sx:.1f},{12+(z-b)*sz:.1f}l-6,13h12z" fill="#f3d38b"/>')
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1360" viewBox="0 0 640 680"><rect width="640" height="680" fill="#21152d"/><rect x="20" y="20" width="600" height="600" fill="#35263d" stroke="#ad8b50"/>'+''.join(body)+'<text x="20" y="650" fill="#eee0c4" font-family="Malgun Gothic,sans-serif" font-size="20">'+html.escape(spec['label'])+'</text></svg>'


def export_room(r,rec):
    bpy.ops.object.select_all(action='DESELECT')
    for o in family(r):o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=r
    # Collision-only slab is metadata, not an opaque rendered wall/asset.
    hidden=[o for o in family(r) if o.get('metadata_collision_only')]
    for o in hidden:o.select_set(False)
    dest=OUT/(rec['id']+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_extras=True,export_apply=True,export_lights=True)
    return dest


# Existing furniture's 5016-square PNGs are source assets. Our dedicated output
# uses 2048-square copies: do not re-embed the unchanged ~70 MiB texture package
# into every small room. No original full_v2 material/image file is written.
for im in bpy.data.images:
    if im.size[0] and max(im.size)>2048:
        ratio=2048/max(im.size);im.scale(max(1,round(im.size[0]*ratio)),max(1,round(im.size[1]*ratio)))
        im.pack()

specs={};copies=[]
for r,rec in ROOMS:
    spec=runtime_record(r,rec);specs[rec['id']]=spec
    dest=export_room(r,rec);write('maps/map_'+rec['id']+'.svg',map_svg(spec))
    rec.update(file=dest.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),runtime=spec)
    copies.extend([{'from':rec['file'],'to':spec['mesh']},{'from':(OUT/'maps'/('map_'+rec['id']+'.svg')).relative_to(ROOT).as_posix(),'to':spec['map']}])
    for o in family(r):o.hide_render=True

# Same mesh, explicit alternative source viewpoints; these are not new story
# rooms or duplicates in the world topology.
variants={
 'garden_rest_area':{'base':'hotel_indoor_garden','label':'실내 정원 옆 휴게공간','spawn':xyz((3.6,-2.1,1.6)),'mode':'fixed_pan'},
 'souvenir_forecourt':{'base':'souvenir_shop','label':'기념품점 앞','spawn':xyz((0,-5.7,1.6)),'mode':'free_walk'},
}
for id,v in variants.items():
    spec=json.loads(json.dumps(specs[v['base']]));spec.update(id=id,label=v['label'],spawn=v['spawn'],mode=v['mode'],sharedMeshOf=v['base'])
    if id=='souvenir_forecourt':
        spec['bounds']=[-6,3.75,6,7.5];spec['walk_surfaces']=[[-6,3.75,6,7.5,0]]
        spec['targets']=[t for t in spec['targets'] if t['id']=='forecourt_game_table']
        spec['source_constraints']=spec['source_constraints']+['This outside viewpoint has only the actual front apron as its walk/NPC staging bounds. Entering the shop occurs on the explicit source transition, not by relabelling the indoor table.']
    specs[id]=spec

world=bpy.data.worlds.new('dedicated_preview_world');world.use_nodes=True;SCENE.world=world
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.24,.27,.34,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
bpy.ops.object.camera_add();cam=bpy.context.object;SCENE.camera=cam;cam.name='dedicated_qa_camera';cam.data.angle=math.radians(73)
SCENE.render.engine='CYCLES';SCENE.cycles.samples=20;SCENE.cycles.use_denoising=True
SCENE.render.resolution_x=1920;SCENE.render.resolution_y=1080;SCENE.render.resolution_percentage=100
SCENE.render.image_settings.file_format='PNG';SCENE.view_settings.view_transform='AgX'
previews=[]
if os.environ.get('V4_DEDICATED_SKIP_RENDER')!='1':
    for r,rec in ROOMS:
        only=set(filter(None,os.environ.get('V4_DEDICATED_RENDER_ONLY','').split(',')))
        if only and rec['id'] not in only:
            previews.extend(p.relative_to(ROOT).as_posix() for p in sorted((OUT/'preview').glob(rec['id']+'_*.png')))
            continue
        for o in family(r):o.hide_render=bool(o.get('metadata_collision_only'))
        w,d,h=rec['size_m'];cam.location=rec['spawn_blender'];target_point=Vector((0,1,1.35))
        if rec['id']=='hotel_indoor_garden':target_point=Vector((.1,1.2,1.5))
        if rec['id']=='souvenir_shop':target_point=Vector((1,2.5,1.25))
        if rec['id']=='hotel_washroom':target_point=Vector((-.5,2.5,1.6))
        cam.rotation_euler=(target_point-cam.location).to_track_quat('-Z','Y').to_euler()
        dest=OUT/'preview'/(rec['id']+'_entry.png');SCENE.render.filepath=str(dest)
        bpy.ops.render.render(write_still=True);previews.append(dest.relative_to(ROOT).as_posix())
        # A second actual inside-camera view exposes corner/side entrance/roof.
        if rec['id'] in ['core_external_inspection','hotel_indoor_garden','hotel_rest_lounge']:
            cam.location=(4.2,1.5,1.6) if rec['id']=='core_external_inspection' else (3.6,-2.1,1.6) if rec['id']=='hotel_indoor_garden' else (2.2,-3.5,1.6)
            target_point=Vector((-.2,2.1,1.15)) if rec['id']=='core_external_inspection' else Vector((-.8,1.7,1.7)) if rec['id']=='hotel_indoor_garden' else Vector((-3,1,1.3))
            cam.rotation_euler=(target_point-cam.location).to_track_quat('-Z','Y').to_euler()
            dest=OUT/'preview'/(rec['id']+'_side.png');SCENE.render.filepath=str(dest);bpy.ops.render.render(write_still=True);previews.append(dest.relative_to(ROOT).as_posix())
        if rec['id']=='souvenir_shop':
            cam.location=(2,-6.7,1.6);target_point=Vector((-1.5,-4.8,1.15))
            cam.rotation_euler=(target_point-cam.location).to_track_quat('-Z','Y').to_euler()
            dest=OUT/'preview'/'souvenir_shop_forecourt.png';SCENE.render.filepath=str(dest);bpy.ops.render.render(write_still=True);previews.append(dest.relative_to(ROOT).as_posix())
        for o in family(r):o.hide_render=True

for o in TEMPLATE_OBJECTS:o.hide_render=True;o.hide_set(True)
for r,rec in ROOMS:
    show=rec['id']=='core_external_inspection'
    for o in family(r):o.hide_render=not show or bool(o.get('metadata_collision_only'));o.hide_set(not show)
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file:
        try:image.pack()
        except RuntimeError:pass
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'dedicated_spaces_source.blend'))
write('world_extension.json',{'version':1,'spaces':specs,'coordinateSystem':'runtime-world-xyz','productionLayout':True,'reaGeometryRecovered':False})
write('copy_manifest.json',copies)
write('manifest.json',{'version':1,'status':'original dedicated production sets; native runtime not yet tested','builder':'tools/build_v4_dedicated_spaces.py','builderSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_blend':(OUT/'dedicated_spaces_source.blend').relative_to(ROOT).as_posix(),'spaces':[rec for _,rec in ROOMS],'variants':variants,'previews':previews,'existing_asset_sources':sorted(TEMPLATES),'originalGameExecuted':False,'originalAssetsExtracted':False,'paidCalls':0,'coordinateSystem':'runtime-world-xyz','limitations':['Original source does not specify measured room dimensions; all sizes are authored production choices.','Current core deck and door layout do not prove historical sight, fall height or an unseen action.','Mirror actor reflections and per-source toy/can state animations still require native renderer verification.']})
print('V4_DEDICATED_SPACES_READY',len(ROOMS),len(specs),len(previews),flush=True)
