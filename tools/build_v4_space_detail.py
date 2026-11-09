"""Original reusable environment props and detail pass, called by Blender space builder.
No plot states or borrowed geometry. Art candidates, not engine collision acceptance.
"""
import math


def enrich(g):
    cube,cyl,bar,empty,root=(g[k] for k in ('cube','cyl','bar','empty','root'))
    rooms,assets,instance,family,export=(g[k] for k in ('rooms','ASSETS','instance','family','export'))
    bpy,OUT,ROOT,records=(g[k] for k in ('bpy','OUT','ROOT','asset_records'))
    added=[]

    def prop(name):
        r=root(name);added.append(r);return r

    r=prop('detail_office_phone')
    cube('phone_base',(0,0,.065),(.28,.23,.13),'ivory',r,.025)
    for row in range(4):
        for col in range(3):cube('blank_key',(-.055+col*.055,-.055+row*.037,.139),(.038,.027,.018),'paper',r,.005)
    receiver=empty('receiver',r,(0,.075,.19))
    bar('receiver_bridge',(-.14,0,0),(.14,0,0),.035,'ink',receiver)
    for x in [-.145,.145]:cube('receiver_earpiece',(x,-.02,-.015),(.075,.085,.065),'ink',receiver,.025)
    # Separate segmented coiled cord, no open cable ends implying an invented fault.
    points=[(-.19-.04*i/35,-.02+.013*math.cos(i*math.tau/4),.09+.013*math.sin(i*math.tau/4)) for i in range(36)]
    for a,b in zip(points,points[1:]):bar('coiled_cord',a,b,.004,'ink',r)
    receiver['off_hook_local_translation']=[.34,-.15,.03]
    r['display']='none';r['dial_tone_state']='script controlled, not inferred from geometry'

    r=prop('detail_office_desk')
    cube('top',(0,0,.79),(2.6,1.1,.09),'wood',r,.025)
    for x in [-1.06,1.06]:cube('leg',(x,0,.37),(.13,.88,.74),'ink',r,.012)
    cube('drawer_case_top',(.5,0,.69),(1.1,.85,.06),'wood',r)
    for x in [-.06,1.06]:cube('drawer_case_side',(x,0,.58),(.045,.85,.22),'wood',r)
    drawer=empty('drawer_slide',r,(.5,-.15,.5))
    cube('drawer_bottom',(0,0,0),(1.05,.8,.035),'wood',drawer)
    for x in [-.515,.515]:cube('drawer_side',(x,0,.095),(.03,.8,.18),'wood',drawer)
    for y in [-.4,.4]:cube('drawer_end',(0,y,.095),(1.06,.035,.18),'wood',drawer)
    bar('drawer_handle',(-.18,-.45,.11),(.18,-.45,.11),.015,'gold',drawer)
    for i in range(5):cube('blank_contact_sheet',(0,-.02,.035+i*.002),(.62,.42,.002),'paper',drawer,.0001)
    drawer['open_translation_local']=[0,-.35,0];r['readable_contacts']='runtime text, never baked';r['state']='half-open candidate'

    r=prop('detail_refreshment_kiosk')
    cube('base',(0,0,.55),(3.6,1.8,1.1),'purple',r,.04)
    cube('counter',(0,-.05,1.13),(3.8,2,.12),'wood',r,.035)
    for x in [-1.75,1.75]:bar('roof_support',(x,.65,1.2),(x,.65,3),.055,'ink',r)
    cube('roof',(0,0,3.05),(4.1,2.4,.15),'ink',r,.025)
    for i in range(12):cube('awning',(-1.88+i*.34,-1.12,2.83),(.33,.16,.42),'rose' if i%2 else 'paper',r,.008)
    r['sign_text_baked']=False

    # New script location: the office is distinct from its neighboring printer lounge.
    office,office_meta=g['room_shell']('management_office',10,8,'fixed_orbit')
    office_meta['source']='docs/design/rewrite_v4/10_프롤로그_초고.md#P-04'
    # The paired lounge owns the single shared door frame; no coplanar duplicate.
    office_meta['targets']=[{'id':'interior_lounge_door','position_blender':[2.6,4,1.2],'destination':'service_lounge'}, {'id':'office_phone','position_blender':[-.65,0,1]}, {'id':'desk_drawer','position_blender':[.5,-.55,.62]}]

    # Open basin built from separate walls: not a solid slab pretending to be a sink.
    r=prop('detail_sink_unit')
    cube('cabinet',(0,0,.42),(1.7,.68,.84),'white',r)
    cube('basin_bottom',(0,0,.77),(.92,.44,.025),'steel',r,.008)
    for x in [-.47,.47]:cube('basin_side',(x,0,.86),(.025,.46,.18),'steel',r,.006)
    for y in [-.23,.23]:cube('basin_end',(0,y,.86),(.96,.025,.18),'steel',r,.006)
    for x in [-.67,.67]:cube('counter_wing',(x,0,.95),(.34,.72,.05),'steel',r,.01)
    for y in [-.31,.31]:cube('counter_rim',(0,y,.95),(.96,.1,.05),'steel',r,.008)
    cyl('drain',(0,0,.788),.045,.008,'ink',r)
    for a,b in [((.22,.27,.96),(.22,.27,1.28)),((.22,.27,1.28),(.22,.02,1.28)),((.22,.02,1.28),(.22,.02,1.17))]:bar('faucet',a,b,.024,'steel',r)
    for x in [-.25,.1]:bar('tap',(x,.27,.98),(x,.27,1.04),.025,'gold',r)
    r['interaction']='water off by default; state and sound authored separately'

    r=prop('detail_cooking_range')
    cube('oven',(0,0,.44),(1.65,.75,.88),'steel',r)
    cube('hob',(0,0,.92),(1.72,.8,.06),'ink',r,.015)
    for x in [-.45,.45]:
        for y in [-.2,.2]:
            cyl('burner',(x,y,.96),.13,.035,'steel',r)
            for a in [0,math.pi/2]:
                o=cube('grate',(x,y,.99),(.34,.025,.025),'ink',r,.004);o.rotation_euler.z=a
    cube('oven_door',(0,-.39,.43),(1.4,.045,.53),'ink',r,.02)
    cube('oven_window',(0,-.419,.43),(1.04,.012,.32),'glass',r,.015)
    bar('oven_handle',(-.6,-.46,.72),(.6,-.46,.72),.025,'steel',r)
    for x in [-.55,-.18,.18,.55]:
        o=cyl('dial',(x,-.42,.83),.035,.04,'gold',r,16);o.rotation_euler.x=math.pi/2
    r['heat_enabled']=False

    r=prop('detail_extraction_hood')
    cube('canopy',(0,0,0),(2.1,.95,.18),'steel',r,.04)
    cube('chimney',(0,.1,.55),(.65,.55,1.02),'steel',r)
    for x in [-.65,-.32,0,.32,.65]:cube('filter',(x,0,-.1),(.22,.65,.025),'ink',r,.004)

    r=prop('detail_cold_storage')
    cube('body',(0,0,1.04),(1.25,.85,2.08),'white',r,.035)
    pivot=empty('fridge_hinge',r,(-.62,-.44,0))
    for z,h in [(.7,1.28),(1.72,.62)]:
        cube('door',(.62,0,z),(1.22,.08,h),'steel',pivot,.025)
        bar('handle',(.98,-.09,z-.2),(.98,-.09,z+.2),.024,'ink',pivot)
    for x in [-.4,-.2,0,.2,.4]:cube('vent',(x,-.435,.11),(.025,.015,.1),'ink',r,.002)
    pivot['animation']='local Z rotation; inspection prop only, not gameplay-ready inventory'

    r=prop('detail_vanity_station')
    cube('desk',(0,0,.79),(1.8,.65,.12),'wood',r)
    for x in [-.72,.72]:cube('pedestal',(x,0,.36),(.32,.57,.72),'purple',r)
    cube('mirror_back',(0,.29,1.52),(1.45,.07,1.2),'ink',r)
    cube('mirror_surface',(0,.245,1.52),(1.29,.012,1.04),'glass',r,.004)
    for x in [-.7,.7]:
        for z in [1.08,1.38,1.68,1.98]:cyl('bulb',(x,.17,z),.055,.07,'light',r,12).rotation_euler.x=math.pi/2
    r['reflection']='runtime mirror reflection pending; tinted surface only in preview'

    r=prop('detail_costume_rack')
    for x in [-1,1]:
        bar('upright',(x,0,.08),(x,0,1.9),.035,'steel',r)
        bar('foot',(x,-.35,.08),(x,.35,.08),.04,'ink',r)
    bar('rail',(-1.05,0,1.9),(1.05,0,1.9),.04,'steel',r)
    for i,x in enumerate([-.7,-.35,0,.35,.7]):
        bar('hanger_left',(x,0,1.78),(x-.15,0,1.64),.012,'gold',r)
        bar('hanger_right',(x,0,1.78),(x+.15,0,1.64),.012,'gold',r)
        cube('costume_cover',(x,.02,1.1),(.26,.1,1.04),'rose' if i%2 else 'purple',r,.04)

    r=prop('detail_medical_trolley')
    for z in [.25,.8]:cube('tray',(0,0,z),(.75,.5,.04),'steel',r,.018)
    for x in [-.32,.32]:
        for y in [-.2,.2]:
            bar('upright',(x,y,.12),(x,y,.89),.018,'steel',r)
            o=cyl('caster',(x,y,.1),.065,.045,'ink',r,12);o.rotation_euler.x=math.pi/2
    for i in range(3):cube('sealed_pack',(-.22+i*.2,0,.85),(.16,.24,.045),'paper',r,.009)
    r['contents']='generic sealed packs; no story evidence assigned'

    r=prop('detail_iv_stand')
    cyl('pole',(0,0,1.0),.022,1.8,'steel',r)
    for a in range(5):
        t=a*math.tau/5;bar('base',(0,0,.12),(.31*math.cos(t),.31*math.sin(t),.05),.025,'steel',r)
    bar('crossbar',(-.22,0,1.93),(.22,0,1.93),.018,'steel',r)
    r['bag_attached']=False

    r=prop('detail_planter')
    cube('container',(0,0,.32),(1.3,1.3,.64),'ivory',r,.08)
    cube('soil',(0,0,.65),(1.12,1.12,.035),'wood',r,.015)
    for i in range(9):
        a=i*2.4;rr=.2+.06*(i%3);x,y=rr*math.cos(a),rr*math.sin(a)
        bar('branch',(0,0,.68),(x,y,1.1+.05*(i%3)),.018,'wood',r)
        o=cube('leaf_cluster',(x,y,1.1+.05*(i%3)),(.42,.32,.24),'glass',r,.1);o.rotation_euler.z=a

    r=prop('detail_fountain_dry')
    # Annular bowl is physically empty. Keep water/audio as separate story state.
    cyl('foundation',(0,0,.06),2.2,.12,'ink',r,64)
    cyl('dry_basin_floor',(0,0,.14),1.94,.06,'ivory',r,64)
    for i in range(48):
        a=i*math.tau/48
        o=cube('basin_rim',(2.04*math.cos(a),2.04*math.sin(a),.35),(.29,.24,.46),'paper',r,.025);o.rotation_euler.z=a+math.pi/2
    cyl('center_plinth',(0,0,.43),.48,.54,'ink',r,32)
    cyl('center_column',(0,0,.95),.2,.55,'ivory',r)
    for a in range(8):
        t=a*math.tau/8;bar('nozzle',(.22*math.cos(t),.22*math.sin(t),.7),(.37*math.cos(t),.37*math.sin(t),.88),.025,'gold',r)
    r['water_enabled']=False;r['audio_source']='separate speaker; no running water mesh'
    from v4_fountain_art import add_tiers
    add_tiers(bpy,r)

    for r in added:
        assets[r.name]=r;bpy.context.view_layer.update();export(r,OUT/(r.name+'.glb'))
        records.append({'id':r.name,'file':(OUT/(r.name+'.glb')).relative_to(ROOT).as_posix(),'nodes':len(family(r)),'mesh_count':sum(o.type=='MESH' for o in family(r)),'interaction':{k:r[k] for k in r.keys()},'runtime_integrated':False})
        for o in family(r):o.hide_render=True

    def remove_tree(o):
        for child in list(o.children):remove_tree(child)
        bpy.data.objects.remove(o,do_unlink=True)

    for r,rec in rooms:
        name=rec['id'];rec['detail_revision']='detail_v1';rec['detail_props']=[]
        if rec['mode']=='fixed_orbit':
            rec['mode']='fixed_pan'
            rec['camera'].update(eye_blender=[0,-rec['camera']['radius'],1.6],rotation='yaw_pitch_about_fixed_eye',manual_translation=False)
            rec['camera']['legacy_radius_role']='initial framing distance only; never orbit eye position'
        def place(asset,loc,angle=0):
            o=instance(asset,r,loc,angle);rec['detail_props'].append({'asset':asset,'node':o.name,'position_blender':list(loc)})
        if name=='kitchen':
            # Replace overlapping generic counters at these workstations.
            for o in list(r.children):
                if 'kitchen_counter' in o.name and o.location.y>4 and abs(o.location.x)<2.1:remove_tree(o)
            place('detail_sink_unit',(-2,4.2,0))
            place('detail_cooking_range',(0,4.2,0))
            place('detail_extraction_hood',(0,4.15,2.15))
            place('detail_cold_storage',(4.8,-2.8,0),-math.pi/2)
        elif name=='management_office':
            place('detail_office_desk',(0,0,0));place('detail_office_phone',(-.65,0,.84))
            for x in [-1.8,1.8]:
                for y in [-.85,.85]:instance('chair',r,(x,y,0),-math.pi/2 if x<0 else math.pi/2)
            rec['seating_capacity']=4
        elif name=='theatre_preparation':
            place('detail_vanity_station',(-2.5,3.3,0));place('detail_costume_rack',(-3.9,-1,0),math.pi/2)
            for x in [-4.5,4.5]:
                for i in range(7):cyl('curtain_fold',(x+i*.07,3.75,1.6),.075,3.0,'rose',r,12)
        elif name=='clinic':
            place('detail_medical_trolley',(1.6,0,0));place('detail_iv_stand',(-2.1,2.1,0));place('detail_iv_stand',(.9,2.1,0))
        elif name=='dining_room':
            for o in list(r.children):
                if 'meeting_table' in o.name or 'chair' in o.name:remove_tree(o)
            for x in [-2.6,2.6]:
                for y in [-2,1.6]:
                    instance('meeting_table',r,(x,y,0),math.pi/2)
                    for dy in [-.75,.75]:
                        for side in [-1,1]:instance('chair',r,(x+side*.9,y+dy,0),side*math.pi/2)
            rec['seating_capacity']=16
        elif name=='plaza':
            for o in list(r.children):
                if any(v in o.name for v in ['fountain_nozzle','door_frame_1m','door_hinged_1m']):remove_tree(o)
            place('detail_fountain_dry',(0,0,0))
            place('detail_refreshment_kiosk',(-9,5,0),-.35)
            for x in [-3,3]:
                cube('entry_pillar',(x,-13.6,2.1),(.55,.55,4.2),'ink',r,.06)
                cube('pillar_cap',(x,-13.6,4.25),(.8,.8,.15),'gold',r,.03)
            bar('arch_header',(-3,-13.6,4.0),(3,-13.6,4.0),.09,'gold',r)
            for side in [-1,1]:
                for x in [side*(3.5+i*.45) for i in range(23)]:
                    bar('boundary_picket',(x,-13.6,.1),(x,-13.6,1.8),.025,'ink',r)
                for z in [.4,1.35]:bar('boundary_rail',(side*3.25,-13.6,z),(side*13.7,-13.6,z),.04,'ink',r)
            for x in [-10,10]:
                for y in [-8,8]:place('detail_planter',(x,y,0))
            for i in range(-13,14):
                for x in [-.85,.85]:cube('path_tile',(x,i,.025),(1.65,.96,.045),'ivory' if i%2 else 'paper',r,.005)
            for x in [-11,11]:
                for y in [-11,-4,4,11]:
                    cyl('lamp_post',(x,y,1.65),.055,3.3,'ink',r)
                    cube('lamp_head',(x,y,3.4),(.3,.3,.42),'light',r,.04)
        elif name=='hotel_lobby':
            place('detail_planter',(-5.7,3,0));place('detail_planter',(5.7,3,0))
        elif name=='laundry_room':
            for x in [-2,0,2]:
                cube('folded_linen',(x,-.7,.86),(.65,.45,.08),'paper',r,.025)
                for z in [.91,.97]:cube('folded_linen',(x,-.7,z),(.63,.44,.055),'white',r,.02)
            for x in [-2.5,2.5]:
                cube('linen_cart',(x,-2.4,.47),(.9,.6,.75),'ivory',r,.04)
                cube('cart_open_top',(x,-2.4,.86),(.78,.48,.025),'ink',r,.01)
        elif name=='archive_room':
            for x in [-4,-1.6,1.6,4]:
                for y in [0,3]:
                    for z in [.45,1.1,1.75]:
                        for k in [-.35,0,.35]:instance('archive_box',r,(x+k,y-.12,z))
        if name!='plaza':
            w,d,_=rec['size_m']
            # Readable room-specific floor construction, not a baked flat backdrop.
            if name in ('kitchen','clinic','laundry_room','dining_room'):
                for x in range(math.ceil(w)):
                    for y in range(math.ceil(d)):
                        material=('paper' if (x+y)%2 else ('ink' if name=='kitchen' else 'ivory'))
                        cube('floor_tile',(-w/2+x+.5,-d/2+y+.5,.006),(.982,.982,.012),material,r,.001)
            elif name in ('theatre_preparation','archive_room'):
                for x in range(math.ceil(w*3)):
                    for y in range(math.ceil(d/2)):
                        cube('floor_board',(-w/2+(x+.5)/3,-d/2+1+y*2,.007),(.322,1.98,.014),'wood' if x%3 else 'gold',r,.002)
            elif name=='hotel_lobby':
                cube('lobby_runner',(0,0,.012),(3.4,d-.4,.025),'rose',r,.004)
                for x in [-1.58,1.58]:cube('runner_trim',(x,0,.028),(.035,d-.5,.01),'gold',r,.002)
            # Vertical structural accents stop every interior becoming the same white box.
            for x in [-w/2+.13,w/2-.13]:
                for y in [-d/2+.25,d/2-.25]:
                    cube('corner_pilaster',(x,y,1.6),(.22,.32,3.2),'ink',r,.015)
                    for z in [.16,3.0]:cube('pilaster_collar',(x,y,z),(.3,.4,.14),'gold',r,.008)
        rec['limits_detail']=['authored props, no incident state baked','collision candidates require engine filtering','visual art candidate, no runtime QA']
    layout={'status':'own authored adjoining spaces; runtime transition pending','coordinate_system':'Blender Z-up meters','instances':[{'id':'management_office','position_blender':[0,0,0]},{'id':'service_lounge','position_blender':[2.6,8,0]}],'portal_pair':{'office_local':[2.6,4,0],'lounge_local':[0,-4,0],'world':[2.6,4,0],'door_geometry_owner':'service_lounge'},'limits':['fixed camera room transition, not free passage implementation','geometry doorway alignment only; gameplay flags and return camera pending']}
    import json
    (OUT/'service_layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
