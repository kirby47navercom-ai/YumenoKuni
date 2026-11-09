"""Authored low-density whole-level recipes, metres/Z-up; established footprints."""
import math,bpy

def floor(K,r,w,d):return K.rounded_solid('continuous_floor',w,d,.16,'paving',r,.005,(0,0,-.08))
def ring(K,r,name,radius,z,mat='brass',n=64,thickness=.03):
    p=[(radius*math.cos(i*math.tau/n),radius*math.sin(i*math.tau/n),z)for i in range(n+1)];return K.tube(name,p,[thickness]*(n+1),mat,r,6)
def fence(K,r,y,width,h=1.4):
    for z in [.3,h-.18]:K.tube('continuous_fence_rail',[(-width/2,y,z),(width/2,y,z)],[.025,.025],'iron',r,6)
    for i in range(int(width)+1):K.tube('tapered_fence_pick',[(-width/2+i,y,.04),(-width/2+i,y,h)],[.018,.012],'iron',r,5)

def shell(K,name,w,d,h=3.5):
    r=K.house(w,d,h,'hip');r.name=name;floor(K,r,w,d);return r

def ferris(K):
    r=K.root('ferris_platform');floor(K,r,16,14);rotor=K.root('wheel_rotor',r);rotor.location=(0,3,10);rotor['animation_axis']='local Y; cabins counter-rotate to remain upright'
    for y in [-.45,.45]:
        p=[(8*math.cos(i*math.tau/64),y,8*math.sin(i*math.tau/64))for i in range(65)];K.tube('continuous_wheel_rim',p,[.09]*65,'brass',rotor,8)
    for i in range(12):
        a=i*math.tau/12;x,z=8*math.cos(a),8*math.sin(a)
        K.tube('tension_spoke',[(0,0,0),(x,0,z)],[.055,.035],'iron',rotor,6)
        pivot=K.root('cabin_pivot',rotor);pivot.location=(x,0,z-.7)
        K.rounded_solid('formed_cabin_lower_shell',1.35,1.3,.48,'lacquer',pivot,.13,(0,0,-.33))
        for side in [-1,1]:
            frame=K.frame_ring('single_cabin_window_frame',1.30,.70,.065,.06,'iron',pivot,(0,side*.64,.26))
            K.rounded_solid('recessed_cabin_glazing',1.15,.018,.55,'glass',pivot,.04,(0,side*.655,.26))
            for xside in [-1,1]:K.tube('curved_cabin_corner',[(xside*.63,side*.58,-.10),(xside*.61,side*.57,.60)],[.03,.03],'iron',pivot,6)
        K.soft_body('curved_weather_roof',1.5,1.45,.20,'roof',pivot,(0,0,.70))
    for x in [-3.6,3.6]:
        for y in [1.5,4.5]:K.tube('load_bearing_A_frame',[(x,y,0),(0,3,10)],[.21,.16],'iron',r,8)
    K.rounded_solid('boarding_platform',6,4,.7,'stone',r,.04,(0,-3,.35));return r

def coaster(K):
    r=K.root('coaster_platform');floor(K,r,18,14)
    for y in [-1,1]:
        p=[(-8+i*.25,y,.85+.12*math.sin(i*.1))for i in range(65)];K.tube('one_continuous_track_rail',p,[.06]*65,'iron',r,8)
    for x in [-6,-3,0,3,6]:K.rounded_solid('structural_track_sleeper',.16,2.5,.18,'wood',r,.015,(x,0,.7))
    for x in [-3,0,3]:
        car=K.root('coaster_car',r);car.location=(x,0,.95)
        # Open top trough with shaped side silhouette and distinct seating.
        vertices=[]
        for xx,half,lo,hi in [(-1.2,.45,.23,.56),(-1.05,.70,.12,.77),(.85,.72,.12,.78),(1.1,.64,.20,.66),(1.2,.44,.31,.45)]:
            profile=[(-half,lo),(half,lo),(half,hi-.10),(half-.08,hi),(half-.14,hi-.03),(half-.12,lo+.09),(-half+.12,lo+.09),(-half+.14,hi-.03),(-half+.08,hi),(-half,hi-.10)]
            vertices.extend((xx,y,z)for y,z in profile)
        K.mesh('continuous_curved_vehicle_shell',vertices,[tuple(reversed(range(10))),tuple(range(40,50))]+[(i*10+j,i*10+(j+1)%10,(i+1)*10+(j+1)%10,(i+1)*10+j)for i in range(4)for j in range(10)],'lacquer',car,True)
        for xx in [-.85,.85]:
            for side in [-1,1]:K.tube('actual_vehicle_wheel',[(xx,side*.86,.05),(xx,side*.98,.05)],[.12,.12],'iron',car,10)
        for side in [-1,1]:
            K.soft_body('padded_vehicle_seat',.8,.94,.16,'cloth',car,(side*.52,0,.37))
            K.soft_body('seat_back',.15,.96,.60,'cloth',car,(side*.52-.34,0,.66))
            K.tube('safety_lap_bar',[(side*.52+.18,-.50,.37),(side*.52+.18,-.50,.70),(side*.52+.18,.50,.70),(side*.52+.18,.50,.37)],[.024]*4,'brass',car,6)
    return r

def pool(K):
    r=K.root('pool_edge')
    # One perforated deck and closed basin, not water laid over a solid floor.
    p=K.frame_ring('continuous_pool_deck',18,12,.12,.18,'paving',r,(0,0,-.08),inner_size=(12,6));p.rotation_euler.x=math.pi/2
    K.rounded_solid('pool_bottom',12,6,.10,'stone',r,.01,(0,0,-1.65))
    basin=K.frame_ring('continuous_basin_walls',12.12,6.12,.12,1.60,'stone',r,(0,0,-.8),inner_size=(11.88,5.88));basin.rotation_euler.x=math.pi/2
    water=K.rounded_solid('water_surface',11.8,5.8,.04,'glass',r,.002,(0,0,-.45));water['water_height_unchanged']=-.45
    coping=K.frame_ring('continuous_pool_coping',12.6,6.6,.30,.12,'stone',r,(0,0,.06),inner_size=(12,6));coping.rotation_euler.x=math.pi/2
    for y in [-5,5]:fence(K,r,y,16)
    return r

def gate(K,loading=False):
    r=K.root('loading_gate'if loading else'park_main_gate');floor(K,r,12 if loading else 16,12 if loading else 10);y=4 if loading else 2;span=2 if loading else 3;h=3.4 if loading else 3.9
    for side in [-1,1]:
        K.rounded_solid('gate_masonry_pier',.65,.65,h+.9,'stone',r,.04,(side*(span+.3),y,(h+.9)/2))
        leaf=K.root('loading_leaf_hinge'if loading else'gate_hinge',r);leaf.location=(side*span,y,0)
        if loading:K.rounded_solid('folded_loading_gate_leaf',2,.18,h,'iron',leaf,.02,(-side,0,h/2))
        else:
            for i in range(12):K.tube('continuous_gate_picket',[(-side*i*.25,0,.15),(-side*i*.25,0,3.9)],[.025,.018],'iron',leaf,6)
            for z in [.3,1.6,3.5]:K.tube('continuous_gate_rail',[(0,0,z),(-side*2.9,0,z)],[.045,.045],'brass',leaf,6)
    if loading:c=K.console();c.parent=r;c.location=(-4,2.5,0)
    r['state']='closed; unlock remains game controlled';return r

def podium(K):
    r=K.root('MovablePodium')
    def arc(name,inner,outer,z0,z1,material):
        n=32;v=[]
        for i in range(n+1):
            a=math.radians(-225+270*i/n)
            v.extend((rad*math.cos(a),rad*math.sin(a),z)for rad,z in [(inner,z0),(outer,z0),(outer,z1),(inner,z1)])
        f=[(i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j)for i in range(n)for j in range(4)]+[(3,2,1,0),(n*4,n*4+1,n*4+2,n*4+3)]
        return K.mesh(name,v,f,material,r,True)
    arc('open_rear_foot',.4,.64,0,.14,'iron');arc('lower_light_band',.57,.65,.14,.18,'light');arc('one_curved_open_shell',.52,.59,.18,1.43,'lacquer');arc('lower_brass_reveal',.56,.63,.26,.32,'brass');arc('continuous_working_rim',.42,.65,1.42,1.52,'wood');arc('rolled_brass_lip',.65,.68,1.49,1.53,'brass')
    K.rounded_solid('control_inset',.44,.19,.012,'glass',r,.01,(0,-.49,1.535));r['rearOpeningDegrees']=90;r['heightMetres']=1.547;return r

def court(K):
    r=K.root('CourtRoom')
    # Keep the established actor ring, camera sightlines and stage dimensions.
    for name,rad,z,h,mat in [('outer_floor',13,-.14,.22,'iron'),('raised_stage',6.9,-.01,.18,'lacquer'),('centre_inlay',4.65,.095,.025,'iron')]:
        v=[(rad*math.cos(i*math.tau/64),rad*math.sin(i*math.tau/64),zz)for zz in [z-h/2,z+h/2]for i in range(64)]
        K.mesh(name,v,[tuple(reversed(range(64))),tuple(range(64,128))]+[(i,(i+1)%64,(i+1)%64+64,i+64)for i in range(64)],mat,r)
    for rad in [1.5,3.1,4.6,6.7,7.4,8.4,9.4,12.5]:ring(K,r,'inlaid_stage_ring',rad,.115 if rad<6.9 else .005,'brass',thickness=.026 if rad<7 else .045)
    for i in range(16):
        a=-i*math.tau/16;bay=K.root('coherent_wall_bay',r);bay.rotation_euler.z=a;bay.location=(12.85*math.sin(-a),12.85*math.cos(a),0)
        # One actual aperture frame with a recessed glass plane.
        K.frame_ring('structural_pierced_wall',5.15,10.4,.35,.35,'iron',bay,(0,0,5.2),inner_size=(3.5,6.5),inner_offset=(0,1.1))
        K.rounded_solid('recessed_tall_glazing',3.5,.035,6.5,'glass',bay,.01,(0,-.08,6.3))
        K.rounded_solid('lower_wall_panel',4.8,.12,2.3,'lacquer',bay,.02,(0,-.22,1.2))
        for x in [-.9,0,.9]:K.tube('structural_window_mullion',[(x,-.26,3.05),(x,-.26,9.55)],[.033,.033],'brass',bay,4)
        for z in [3,4.6,6.3,8,9.6]:K.tube('structural_window_transom',[(-1.9,-.24,z),(1.9,-.24,z)],[.035,.035],'iron',bay,4)
    for z,rad in [(.2,12.4),(2.5,12.4),(10,12.3),(10.5,12.4)]:ring(K,r,'continuous_architectural_course',rad,z,thickness=.07)
    K.rounded_solid('host_dais',3.6,2.1,2.8,'iron',r,.08,(0,8.8,1.4));chair=K.curved_family('chair');chair.parent=r;chair.location=(0,8.9,2.8);chair.scale=(3,2.6,2.5)
    return r

def build(ident,K):
    if ident=='ferris_platform':return ferris(K)
    if ident=='coaster_platform':return coaster(K)
    if ident=='pool_edge':return pool(K)
    if ident=='park_main_gate':return gate(K)
    if ident=='loading_gate':return gate(K,True)
    if ident=='trial_podium':return podium(K)
    if ident=='courtroom_stage':return court(K)
    if ident=='ticket_booth':
        r=shell(K,ident,5,6);c=K.reception_counter();c.parent=r;c.location=(0,1.8,0);c=K.curved_family('chair');c.parent=r;c.location=(0,2.6,0);return r
    if ident=='ferris_cabin':
        r=K.root(ident);floor(K,r,3,3)
        glass=K.M['glass'].copy();glass.name='rebuilt_cabin_clear_glass';bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.70,.85,.92,1);bs.inputs['Alpha'].default_value=.12;bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.10;K.M['cabin_glass']=glass
        # An enclosed gondola has a curved weather cap, wraparound glazing and
        # two facing bench seats, rather than the generic house/hip-roof recipe.
        K.soft_body('continuous_capsule_cabin_roof',3.08,3.08,.26,'roof',r,(0,0,2.70))
        for side in [-1,1]:
            x=side*1.42
            K.rounded_solid('formed_cabin_lower_side',.16,2.90,.75,'lacquer',r,.04,(x,0,.375))
            for y in [-1.38,1.38]:K.tube('curved_cabin_structural_corner',[(x,y,.10),(x,y,2.38),(x*.95,y*.95,2.63)],[.045]*3,'iron',r,8)
            panel=K.mesh('inset_cabin_side_glazing',[(x,yy,z)for yy,z in [(-1.32,.82),(1.32,.82),(1.32,2.42),(-1.32,2.42)]],[(0,1,2,3)],'cabin_glass',r);panel.data.materials[0].use_backface_culling=False
        K.frame_ring('rear_cabin_glazing_frame',2.92,2.45,.12,.12,'iron',r,(0,1.44,1.35),inner_size=(2.68,1.6),inner_offset=(0,.25))
        K.rounded_solid('rear_cabin_glazing',2.65,.025,1.58,'cabin_glass',r,.01,(0,1.43,1.60))
        for x in [-1.14,1.14]:K.rounded_solid('cabin_entry_side_panel',.50,.12,2.5,'lacquer',r,.03,(x,-1.44,1.25))
        K.frame_ring('actual_cabin_door_opening',1.64,2.64,.1,.14,'iron',r,(0,-1.44,1.26),inner_size=(1.44,2.52))
        for side in [-1,1]:
            K.soft_body('curved_cabin_bench',.44,2.48,.40,'cloth',r,(side*1.1,0,.46))
            K.soft_body('curved_cabin_bench_back',.13,2.48,.56,'cloth',r,(side*1.32,0,.83))
        return r
    if ident=='outside_threshold':
        r=K.root(ident)
        K.mesh('continuing_service_road_surface',[(-2.75,-20,.009),(2.75,-20,.009),(2.75,22,.009),(-2.75,22,.009)],[(0,1,2,3)],'paving',r)
        return r
    raise ValueError(ident)
