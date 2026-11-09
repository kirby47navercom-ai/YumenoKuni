"""Author the separate park levels in background Blender; never touch the live file."""
import bpy,math,json,random,sys,hashlib,subprocess
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_rebuilt_environment_kit as K
import build_v4_rebuilt_environment as A
from v4_park_continuity import distant_tree
from v4_park_levels import plan,membership
O=R/'art/space_v4/park_levels_v1';(O/'raw').mkdir(parents=True,exist_ok=True);(O/'review').mkdir(exist_ok=True)
P=plan();BY={d['id']:d for d in P['districts']};GROUPS=membership(P)
WORLD=json.loads((R/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf8'))
BANK={Path(a['runtime']).stem:R/a['file']for a in json.loads((R/'art/space_v4/rebuild_v1/manifest.json').read_text(encoding='utf8'))['assets']}
LIB=R/'art/space_v4/facility_forms_v3/park-form-source.blend'
bpy.ops.wm.open_mainfile(filepath=str(O/'parks-authoring.blend'if(O/'parks-authoring.blend').exists()else LIB))
K.setup_materials()
for o in bpy.context.scene.objects:o.hide_render=True
only=next((set(v.split('=',1)[1].split(','))for v in sys.argv if v.startswith('--only=')),None)
manifest=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'))if(O/'raw-manifest.json').exists()else{'version':1,'levels':[]}
font_path=R/'Game/Assets/Fonts/pretendard/Pretendard-Medium.otf';FONT=bpy.data.fonts.load(str(font_path))if font_path.exists()else None

def children(o):return[o,*o.children_recursive]
def remove(o):
    for c in reversed(children(o)):
        if c.name in bpy.data.objects:bpy.data.objects.remove(c,do_unlink=True)
def copy_group(src,parent,delta):
    lookup={}
    for old in children(src):
        obj=old.copy();obj.data=old.data.copy()if old.data else None;bpy.context.scene.collection.objects.link(obj);lookup[old]=obj;obj.name='parkcopy_'+old.name
    for old,obj in lookup.items():obj.parent=lookup.get(old.parent,parent)
    obj=lookup[src];obj.location+=Vector(delta)
    return obj
def solid(name,w,d,h,mat,parent,at=(0,0,0),radius=.06):return K.rounded_solid(name,w,d,h,mat,parent,radius,at)
def lathe(name,profile,mat,parent,at=(0,0,0),segments=32):
    v=[(rr*math.cos(i*math.tau/segments)+at[0],rr*math.sin(i*math.tau/segments)+at[1],z+at[2])for rr,z in profile for i in range(segments)]
    f=[tuple(reversed(range(segments))),tuple(range((len(profile)-1)*segments,len(profile)*segments))]
    f +=[(k*segments+i,k*segments+(i+1)%segments,(k+1)*segments+(i+1)%segments,(k+1)*segments+i)for k in range(len(profile)-1)for i in range(segments)]
    return K.mesh(name,v,f,mat,parent,True,uv_scale=.3)
def arch(name,parent,at,width=7,height=5,mat='stone'):
    x,y,z=at
    for s in [-1,1]:lathe(name+'_pier',[(.42,0),(.42,.22),(.28,.35),(.28,height-.4),(.39,height)],mat,parent,(x+s*width/2,y,z),16)
    points=[(x+width/2*math.cos(i*math.pi/32),y,z+height+width*.24*math.sin(i*math.pi/32))for i in range(33)]
    K.tube(name+'_continuous_arch',points,[.26]*len(points),mat,parent,10)
def label(parent,text,at,size=.52,mat='ink'):
    # World labels are forbidden: attraction/building form carries identity.
    return None

def tinted(key,base,color):
    m=K.M[base].copy();m.name='park_'+key;m['surfaceTint']=[*color,1];bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1)
    image=next((n for n in m.node_tree.nodes if n.type=='TEX_IMAGE'and n.image and n.image.colorspace_settings.name!='Non-Color'),None)
    if image:
        mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*color,1);m.node_tree.links.new(image.outputs['Color'],mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color'])
    K.M[key]=m
for key,base,c in [('cream','plaster',(1,.87,.67)),('red','lacquer',(.68,.045,.09)),('blue','lacquer',(.08,.22,.47)),('violet','lacquer',(.27,.09,.40)),('enamel','stone',(.65,.79,.86)),('brick','plaster',(.48,.16,.09)),('ink','iron',(.08,.07,.11)),('gold','brass',(.85,.57,.21)),('teal','lacquer',(.06,.38,.36))]:tinted(key,base,c)

def canopy(parent,at,radius=7,height=7,palette=('cream','red'),lobes=16):
    x,y,z=at;segments=64;rings=[(.08,height),(radius*.25,height-.5),(radius*.70,height-1.9),(radius,height-3.3)]
    verts=[(x+r*math.cos(a*math.tau/segments),y+r*math.sin(a*math.tau/segments),z+h+.12*math.cos(a*math.tau*lobes/segments))for r,h in rings for a in range(segments)]
    for stripe in range(lobes):
        faces=[]
        for k in range(len(rings)-1):
            for a in range(stripe*segments//lobes,(stripe+1)*segments//lobes):faces.append((k*segments+a,k*segments+(a+1)%segments,(k+1)*segments+(a+1)%segments,(k+1)*segments+a))
        K.mesh('continuous_radial_canopy_panel',verts,faces,palette[stripe%len(palette)],parent,True,uv_scale=.25)
    for j in range(lobes):
        a=j*math.tau/lobes;K.tube('scalloped_canopy_edge',[(x+radius*math.cos(a+t/lobes),y+radius*math.sin(a+t/lobes),z+height-3.3-.35*math.sin(t/2))for t in [k*math.tau/12 for k in range(13)]],[.09]*13,'gold',parent,6)
    lathe('canopy_finial',[(.04,0),(.15,.4),(.06,.8),(0,1.3)],'gold',parent,(x,y,z+height),12)
def tower(parent,x,y,r=2.1,h=12):
    lathe('castle_continuous_round_tower',[(r*1.1,0),(r*1.1,.5),(r,.8),(r,h-2),(r*1.08,h-1.8),(r*1.08,h-1.3)],'cream',parent,(x,y,0),32)
    lathe('fitted_conical_turret_roof',[(r*1.2,h-1.35),(r*1.2,h-1.05),(r*.95,h-.3),(r*.12,h+3),(0,h+3.5)],'blue',parent,(x,y,0),32)
    for z in [3,6.5,9]:
        if z<h-2:solid('tower_inset_window',.65,.08,1.25,'glass',parent,(x,y-r-.015,z),.015)
def horse(parent,x,y,angle,scale=1):
    root=K.root('carved_carousel_pony',parent);root.location=(x,y,1.15);root.rotation_euler.z=angle;root.scale=(scale,)*3
    # Connected curved body/neck silhouettes, four shaped legs, mane and saddle.
    K.tube('carved_body',[(0,-.62,0),(0,-.25,.12),(0,.25,.18),(0,.55,.12)],[.26,.42,.39,.24],'cream',root,12)
    K.tube('curved_horse_neck',[(0,.45,.1),(0,.72,.48),(0,.63,.85),(0,.40,1.05)],[.26,.20,.17,.13],'cream',root,10)
    K.tube('horse_muzzle',[(0,.39,.98),(0,.05,.88)],[.17,.11],'cream',root,10)
    for side in [-1,1]:
        K.tube('horse_ear',[(side*.095,.45,1.08),(side*.13,.48,1.36)],[.06,.01],'cream',root,6)
        for fore in [-1,1]:K.tube('shaped_pony_leg',[(side*.19,fore*.35,-.08),(side*.22,fore*.43,-.5),(side*.22,fore*.43+.12,-.84)],[.11,.075,.09],'cream',root,8)
    K.tube('flowing_pony_tail',[(0,-.52,.13),(.12,-.82,-.10),(.22,-1.0,-.42)],[.12,.09,.01],'gold',root,8)
    solid('actual_pony_saddle',.5,.55,.12,'violet',root,(0,-.05,.48),.035)
    K.tube('carousel_pole',[(0,0,-1.1),(0,0,3.8)],[.04,.04],'gold',root,8)
def carousel(parent,at):
    x,y=at;lathe('carousel_round_boarding_plinth',[(6.5,0),(6.5,.25),(6.1,.48),(6.1,.58)],'wood',parent,(x,y,0),48)
    canopy(parent,(x,y,0),6.7,8,('cream','blue'))
    lathe('carousel_load_bearing_center',[(.75,.5),(.6,1),(.6,5),(.85,5.5)],'gold',parent,(x,y,0),24)
    for i in range(10):
        a=i*math.tau/10;horse(parent,x+4.35*math.cos(a),y+4.35*math.sin(a),a)
def planetarium(parent,at):
    x,y=at;radius=10;bands=12;segs=64;verts=[]
    for k in range(bands+1):
        t=k*math.pi/2/bands
        for j in range(segs):a=j*math.tau/segs;verts.append((x+radius*math.cos(t)*math.cos(a),y+radius*math.cos(t)*math.sin(a),3+radius*.82*math.sin(t)))
    faces=[(k*segs+j,k*segs+(j+1)%segs,(k+1)*segs+(j+1)%segs,(k+1)*segs+j)for k in range(bands)for j in range(segs)]
    K.mesh('planetarium_true_segmented_dome',verts,faces,'enamel',parent,True,uv_scale=.3)
    # Continuous cylindrical wall with a real front entrance, not a painted door.
    for j in range(segs):
        a=j*math.tau/segs;b=(j+1)*math.tau/segs;front=math.sin((a+b)/2)<-.96
        if front:continue
        v=[(x+radius*math.cos(t),y+radius*math.sin(t),z)for z in [0,3.05]for t in [a,b]];K.mesh('planetarium_curved_enclosing_wall',v,[(0,1,3,2)],'cream',parent,True,uv_scale=.3)
    for k in range(0,segs,8):
        a=k*math.tau/segs;K.tube('dome_meridian_rib',[(x+(radius+.05)*math.cos(t)*math.cos(a),y+(radius+.05)*math.cos(t)*math.sin(a),3+radius*.82*math.sin(t))for t in [j*math.pi/24 for j in range(13)]],[.06]*13,'gold',parent,8)
    arch('planetarium_entry',parent,(x,y-radius-.2,0),5,3.1,'enamel');label(parent,'천체관',(x,y-radius-.5,3.25),.7)
def wheel(parent,at):
    x,y=at;z=16;r=13.6
    for side in [-1,1]:
        for dx in [-8,8]:K.tube('wheel_real_load_bearing_A_frame',[(x+dx,y+side*3,0),(x,y+side*.9,z)],[.32,.23],'iron',parent,12)
        K.tube('wheel_connected_rim',[(x+r*math.cos(i*math.tau/96),y+side*.6,z+r*math.sin(i*math.tau/96))for i in range(97)],[.16]*97,'enamel',parent,10)
        for i in range(16):
            a=i*math.tau/16;K.tube('tensioned_wheel_spoke',[(x,y+side*.6,z),(x+r*math.cos(a),y+side*.6,z+r*math.sin(a))],[.055,.035],'iron',parent,6)
    for i in range(12):
        a=i*math.tau/12;px,pz=x+r*math.cos(a),z+r*math.sin(a)-1.3;root=K.root('wheel_upright_gondola',parent);root.location=(px,y,pz)
        lathe('gondola_enclosed_base',[(1,0),(1.12,.20),(1,.65)],'violet',root,segments=16)
        for side in [-1,1]:
            for dx in [-.75,.75]:K.tube('gondola_window_frame',[(dx,side*.75,.55),(dx,side*.75,2.0)],[.05,.05],'iron',root,6)
        lathe('gondola_fitted_cap',[(1.12,1.95),(.90,2.35),(.12,2.6)],'enamel',root,segments=16)
        K.tube('gondola_hanger',[(0,0,2.5),(0,0,2.9)],[.07,.07],'iron',root,6)
def clock_tower(parent,at):
    x,y=at;lathe('clockwork_tower_faceted_body',[(3.6,0),(3.6,.7),(2.8,1.2),(2.8,13),(3.5,13.5),(3.5,14.2)],'brick',parent,(x,y,0),8)
    lathe('clockwork_tower_roof',[(3.8,14.1),(3.8,14.5),(1,18),(0,18.7)],'teal',parent,(x,y,0),8)
    for z in [3,6.5,10]:
        for side in [-1,1]:solid('tower_recessed_lancet',.65,.10,1.5,'glass',parent,(x+side*1.25,y-2.83,z),.02)
    # Ornamental mechanical dial, deliberately not an evidentiary working clock.
    dial=K.root('ornamental_mechanism_dial',parent);dial.location=(x,y-3.2,13.6);dial.rotation_euler.x=math.pi/2
    lathe('mechanism_dial_ring',[(2.05,-.08),(2.05,.08),(1.7,.08),(1.7,-.08)],'gold',dial,segments=48)
    for i in range(16):
        a=i*math.tau/16;K.tube('radial_mechanical_tooth',[(1.55*math.cos(a),1.55*math.sin(a),0),(1.90*math.cos(a),1.90*math.sin(a),0)],[.075,.075],'gold',dial,6)
    label(parent,'태엽 광장',(x,y-3.5,9),.65,'gold')
def coaster(parent):
    pts=[(6,-25,1.2),(6,-15,1.2),(6,-5,1.2),(12,10,5),(18,28,12),(36,38,18),(52,22,12),(48,1,5),(32,-18,2),(14,-28,1.2)]
    # Catmull-Rom interpolation gives fitted, closed rails instead of disconnected poles.
    path=[]
    for i in range(len(pts)):
        a,b,c,d=[Vector(pts[j%len(pts)])for j in [i-1,i,i+1,i+2]]
        for k in range(12):
            t=k/12;path.append((b*2+(c-a)*t+(a*2-b*5+c*4-d)*t*t+(-a+b*3-c*3+d)*t*t*t)*.5)
    normals=[]
    for i,p in enumerate(path):
        tangent=path[(i+1)%len(path)]-path[(i-1)%len(path)];normal=Vector((-tangent.y,tangent.x,0));normal.normalize();normals.append(normal)
    for side in [-1,1]:
        rail=[tuple(p+n*(side*.62))for p,n in zip(path,normals)];K.tube('closed_coaster_rail',rail+[rail[0]],[.105]*(len(rail)+1),'iron',parent,8)
    for i in range(0,len(path),2):
        p=path[i];n=normals[i];K.tube('fitted_rail_cross_tie',[tuple(p-n*.85),tuple(p+n*.85)],[.09,.09],'brick',parent,6)
    for i in range(0,len(path),8):
        p=path[i];n=normals[i]
        for side in [-1,1]:
            foot=p+n*(side*1.3);K.tube('grounded_coaster_support',[(foot.x,foot.y,0),tuple(p+n*side*.62)],[.19,.14],'teal',parent,8)
    for i in range(3):
        y=-20+i*2.35;r=K.root('coaster_train_car',parent);r.location=(6,y,1.3)
        K.section('formed_train_body',[(-.8,.2),(-.8,.75),(-.5,1.1),(.5,1.1),(.8,.75),(.8,.2)],1.9,'red',r)
        for side in [-1,1]:K.tube('train_restraint_rail',[(side*.42,-.45,1.1),(side*.42,.25,1.45),(side*.42,.55,1.1)],[.055]*3,'iron',r,8)
def illusion_arcade(parent):
    for x,y,a in [(-31,-12,-.25),(-26,-1,-.1),(-24,10,.1),(-28,22,.25)]:
        r=K.root('illusion_arcade_bay',parent);r.location=(x,y,0);r.rotation_euler.z=a;arch('glass_arcade',r,(0,0,0),7,4,'violet')
        K.tube('continuous_arcade_roof_spine',[(-3.5,0,4),(0,0,5.7),(3.5,0,4)],[.11]*3,'gold',r,8)
    at=(14,3.5);canopy(parent,(*at,0),8,13.3,('violet','cream'),12)
    lathe('mask_observatory_real_upper_deck',[(6.7,5.65),(6.7,5.85)],'stone',parent,(*at,0),48)
    for i in range(1,12):
        a=i*math.tau/12;K.tube('rotunda_structural_column',[(at[0]+7*math.cos(a),at[1]+7*math.sin(a),0),(at[0]+7*math.cos(a),at[1]+7*math.sin(a),10)],[.16,.13],'violet',parent,10)
    for k in range(2,47):
        a=k*math.tau/48;b=(k+1)*math.tau/48
        K.tube('observatory_balustrade_top',[(14+6.45*math.cos(a),3.5+6.45*math.sin(a),6.9),(14+6.45*math.cos(b),3.5+6.45*math.sin(b),6.9)],[.045,.045],'gold',parent,6)
        K.tube('observatory_balustrade_upright',[(14+6.45*math.cos(a),3.5+6.45*math.sin(a),5.85),(14+6.45*math.cos(a),3.5+6.45*math.sin(a),6.9)],[.025,.025],'iron',parent,6)
    # One closed extruded stair profile, rather than stacked decorative boxes.
    profile=[(30,0),(20.4,0),(20.4,5.85)]
    for i in range(31,-1,-1):
        x=30-i*.30;z=(i+1)*5.85/32;profile +=[(x-.30,z),(x,z),(x,i*5.85/32)]
    vertices=[(x,3.5+y,z)for y in [-1.05,1.05]for x,z in profile];n=len(profile)
    faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]
    K.mesh('continuous_observatory_stair_flight',vertices,faces,'stone',parent,uv_scale=.35)
    for side in [-1,1]:K.tube('fitted_stair_handrail',[(30,3.5+side*1.05,1),(20.4,3.5+side*1.05,6.85)],[.05,.05],'gold',parent,8)

    for angle,y in [(2*math.tau/48,4.55),(47*math.tau/48,2.45)]:
        x0,y0=14+6.45*math.cos(angle),3.5+6.45*math.sin(angle)
        K.tube('connected_landing_handrail',[(x0,y0,6.9),(20.4,y,6.85)],[.05,.05],'gold',parent,8)
        K.tube('landing_handrail_support',[(20.4,y,5.85),(20.4,y,6.85)],[.04,.04],'gold',parent,8)

def lamp(parent,x,y):
    K.tube('walkway_lamp_tapered_post',[(x,y,0),(x,y,3.4)],[.08,.045],'iron',parent,8);lathe('weatherproof_lantern',[(.20,3.15),(.26,3.25),(.24,3.70),(.05,3.9)],'light',parent,(x,y,0),8)
def path(parent,name,points,width=5):
    # Public paving is united and routed around footprints once per level.
    return None

def ground(parent,ident):
    if ident=='carnival':
        x,y=14,8;outer=[(-2000,-2000),(2000,-2000),(2000,2000),(-2000,2000)];inner=[(x-6.01,y-3.01),(x+6.01,y-3.01),(x+6.01,y+3.01),(x-6.01,y+3.01)];v=[(x,y,-.04)for ring in [outer,inner]for x,y in ring];K.mesh('continuous_ground_with_real_pool_opening',v,[(i,(i+1)%4,(i+1)%4+4,i+4)for i in range(4)],'grass',parent,uv_scale=.2)
    else:K.mesh('continuous_ground_beyond_camera',[(-2000,-2000,-.04),(2000,-2000,-.04),(2000,2000,-.04),(-2000,2000,-.04)],[(0,1,2,3)],'grass',parent,uv_scale=.2)
    v=[];rings=[(110,-.05),(150,.1),(225,7),(340,18),(500,28),(800,20),(1300,35),(1900,22)]
    for k,(r,h)in enumerate(rings):
        for i in range(96):a=i*math.tau/96;v.append((r*math.cos(a),r*math.sin(a),h*(.7+.2*math.sin(a*3+k*.12))))
    K.mesh('layered_distant_park_landscape',v,[(k*96+i,k*96+(i+1)%96,(k+1)*96+(i+1)%96,(k+1)*96+i)for k in range(len(rings)-1)for i in range(96)],'grass',parent,True,uv_scale=.16)
    rng=random.Random(341104+list(BY).index(ident))
    for i in range(60):
        a=rng.uniform(0,math.tau);r=rng.uniform(120,175);tree=distant_tree(parent,r*math.cos(a),r*math.sin(a),82000+i);tree.location.z=max(0,(r-150)/75*5)

def import_local(ident,parent,position):
    src=BANK[ident];assert src.exists(),str(src)
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(src));made=set(bpy.data.objects)-before
    root=K.root('preserved_outdoor_'+ident,parent);root.location=position
    for o in made:
        if o.parent not in made:o.parent=root
    return root
def populate(d):
    ident=d['id'];name='park_level_'+ident;old=bpy.data.objects.get(name)
    if old:remove(old)
    root=K.root(name);root['parkDistrict']=ident;root['chapterGate']=d['chapter'];ground(root,ident);collision=[];placed={};ox,oy=d['originBlender']
    rooms=list(P['rooms'][ident])
    if ident=='fairytale':rooms+=P['residence']
    for room in rooms:
        if room not in WORLD['instances']:continue
        record=WORLD['instances'][room];p=record['p'];x,y=p[0]-ox,-p[2]-oy
        if room in P['placementsBlender']:x,y=P['placementsBlender'][room]
        placed[room]=[x,y];source=bpy.data.objects.get('facade_'+room)
        if source and room not in ['inspection_hall_changed','staff_passage']:
            original=source.matrix_world.translation;copy_group(source,root,(x-original.x,y-original.y,-original.z))
            size=WORLD['spaces'][record['space']]['bounds'];vertices=[o.matrix_world@Vector(c)for o in source.children_recursive if o.type=='MESH'for c in o.bound_box];height=max(v.z for v in vertices)-source.matrix_world.translation.z;collision.append([x+size[0],-y+size[1],x+size[2],-y+size[3],0,round(height,5)])
        if room in ['plaza','park_garden','park_main_gate','pool_edge','coaster_platform','ferris_platform','outside_threshold']:import_local(room,root,(x,y,p[1]));collision += [[x+c[0],-y+c[1],x+c[2],-y+c[3],*(c[4:]if len(c)>4 else[0,3])]for c in WORLD['spaces'][record['space']]['collision']]
    if ident=='fairytale':
        for x in [-9,9]:tower(root,x,-40,2.5,11)
        arch('main_fairy_castle_gateway',root,(0,-40,0),12,7,'cream');label(root,'동화 정원',(0,-40.5,7.3),.8,'gold');carousel(root,(-33,-24));collision.append([-40,17,-26,31,0,9])
        path(root,'garden_public_loop',[(-52,-5),(-52,-37),(0,-52),(37,-35),(42,0),(37,15),(0,16),(-52,-5)],5)
    elif ident=='carnival':
        canopy(root,(-29,-13,0),13,13,('cream','red'),20)
        for x,y in [(-41,-13),(-17,-13),(-29,-25),(-29,-1)]:K.tube('circus_canopy_load_pole',[(x,y,0),(x,y,8.4)],[.18,.13],'red',root,10)
        arch('festival_proscenium',root,(-29,-26,0),11,6,'gold');label(root,'축제의 거리',(-29,-26.4,6.4),.8,'gold');collision.append([-41,1,-17,25,0,13])
        path(root,'wide_parade_avenue',[(-30,-68),(-30,-40),(-50,-8),(-30,12),(-30,50)],8)
        path(root,'theatre_approach',[(-30,-40),(0,-38),(0,-29)],5)
    elif ident=='mirrors':
        illusion_arcade(root);label(root,'가면 전망대',(14,-4.9,8.3),.58,'gold')
        path(root,'offset_illusion_loop',[(-28,-50),(-46,-27),(-43,12),(-18,27),(18,23),(38,3),(38,-33),(-28,-50)],4.5)
    elif ident=='clockwork':
        clock_tower(root,(-39,-6));coaster(root);collision.append([-43,2,-35,10,0,19])
        path(root,'mechanical_public_prom',[(-30,-50),(-52,-25),(-54,10),(-30,48),(0,56),(40,44)],6)
    elif ident=='starlight':
        planetarium(root,(-34,-5));collision.append([-44,-5,-24,15,0,14])
        path(root,'curved_observatory_prom',[(-24,-52),(-54,-25),(-54,11),(-34,27),(2,44),(34,18),(34,-24),(-24,-52)],7)
    elif ident=='perimeter':
        path(root,'continuous_service_exit_road',[(0,-30),(0,20),(-4,42),(-18,70),(-36,88),(-44,120)],6)
    if ident!='perimeter':
        for room,(x,y)in placed.items():
            if room in ['inspection_hall_changed','ferris_cabin','hotel_corridor']or room.startswith('guest_'):continue
            b=WORLD['spaces'][WORLD['instances'][room]['space']]['bounds'];front=y-b[3]-.6
            # These are public approaches, not additional evidence targets.
            path(root,'public_approach_'+room,[(x-5,front-4),(x,front-4),(x,front+.1)],2.6)
        # Every open level has actual gate architecture and a walkable entry.
        sx,_,sz=d['spawn'];arch('themed_park_entrance',root,(sx,-sz-1,0),8,4.5,'gold');label(root,d['name'],(sx,-sz-1.3,4.9),.62,'gold')
        rng=random.Random(42000+list(BY).index(ident))
        for i in range(18):
            x=rng.choice([-1,1])*rng.uniform(58,77);y=rng.uniform(-60,65);tree=K.tree(i+120);tree.parent=root;tree.location=(x,y,0)
        for x,y in [(-53,-38),(-53,-3),(-53,33),(49,-36),(49,1),(49,38)]:lamp(root,x,y)
    if ident=='fairytale':
        for other,x,y in [('carnival',59,-1),('mirrors',64,42),('clockwork',-64,24),('starlight',24,-64)]:
            arch('chapter_boundary_'+other,root,(x,y,0),7,4.2,'gold');label(root,BY[other]['name'],(x,y-.35,4.7),.48,'gold')
    if ident!='perimeter':
        # Roads connect actual front approaches, not isolated pavement fragments.
        destinations=[]
        for room,(x,y)in placed.items():
            if room in ['inspection_hall_changed','hotel_corridor','theatre_preparation','mirror_workbay','screening_room','ferris_cabin']or room.startswith('guest_'):continue
            if not bpy.data.objects.get('facade_'+room)and room not in ['plaza','park_garden','park_main_gate','coaster_platform','ferris_platform','pool_edge']:continue
            b=WORLD['spaces'][WORLD['instances'][room]['space']]['bounds'];destinations.append([x,-y+b[3]+2.5])
        destinations += {'fairytale':[[59,1],[64,-42],[-64,-24],[24,64],[-22,24],[0,48]],'carnival':[[-30,-55],[-45,14]],'mirrors':[[-32,-18],[31,2]],'clockwork':[[-28,8],[34,44]],'starlight':[[-34,18],[2,-45]]}[ident]
        routefile=O/('paths-'+ident+'.json');routefile.write_text(json.dumps({'spawn':[d['spawn'][0],d['spawn'][2]],'destinations':destinations,'bounds':d['bounds'],'obstacles':[c for c in collision if c[4]<1.6 and c[5]>.34]}),encoding='utf8')
        subprocess.run(['C:/python/python.exe','-X','utf8',str(R/'tools/plan_v4_park_paths.py'),str(routefile)],check=True)
        paving=json.loads(routefile.with_suffix('.mesh.json').read_text());v=[(x,-z,.025)for t in paving['triangles']for x,z in t];K.mesh('one_connected_public_promenade',v,[(k,k+1,k+2)for k in range(0,len(v),3)],'paving',root,uv_scale=.3)
        for polygon in paving['polygons']:
            for ring in [polygon['outer'],*polygon['holes']]:
                line=[(x,-z,.065)for x,z in ring];K.tube('continuous_fitted_promenade_edging',line,[.055]*len(line),'stone',root,6)
    else:
        K.mesh('continuing_service_road', [(-3,-125,.02),(3,-125,.02),(3,35,.02),(-3,35,.02)],[(0,1,2,3)],'paving',root,uv_scale=.3)
    root['purpose']='Separate authored theme level, not the old shared full park';bpy.context.view_layer.update()
    # Player collision is intentionally separate from decorative geometry;
    # evidence-local interior collision and target transforms stay authoritative.
    walk=[[ *d['bounds'],0]]
    if ident=='mirrors':
        for i in range(32):walk.append([30-(i+1)*.30,-4.55,30-i*.30,-2.45,(i+1)*5.85/32])
        for ix in range(-6,6):
            for iz in range(-6,6):
                if max((ix+dx)**2+(iz+dz)**2 for dx in [0,1]for dz in [0,1])<6.35**2:walk.append([14+ix,-3.5+iz,15+ix,-2.5+iz,5.85])
    if ident=='mirrors':
        from v4_park_access_geometry import observatory
        observatory(collision,walk)
    return root,{'id':ident,'collision':collision if ident!='perimeter' else WORLD['spaces']['outside_threshold']['collision'],'walkSurfaces':walk,'placedFacilities':placed,'bounds':d['bounds'],'landmarks':d['landmarks']}

for d in P['districts']:
    if only and d['id']not in only:continue
    root,record=populate(d);objects=children(root)
    A.O=O;raw=A.export(objects,d['id']+'.glb','Assets/Art/park_levels/'+d['id']+'.glb',{'parkDistrict':d['id'],'chapter':d['chapter']});record.update(raw=raw,sourceObject=root.name)
    manifest['levels']=[row for row in manifest['levels']if row['id']!=d['id']]+[record]
    for o in objects:o.hide_render=True
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True)
    (O/'raw-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('THEMED_PARK_AUTHORED',d['id'],raw['triangles'],flush=True)
print('PARK_SOURCE_CHECKPOINT',len(manifest['levels']),flush=True)
