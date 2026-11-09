"""Original full-story environment expansion. Geometry is authored, never extracted.
Physical normal/state variants remain distinct from story facts and runtime acceptance.
"""
import math,json


def expand(g):
    bpy,rooms,M,ROOT,OUT=(g[k] for k in ('bpy','rooms','M','ROOT','OUT'))
    cube,cyl,bar,root,empty,instance,family=(g[k] for k in ('cube','cyl','bar','root','empty','instance','family'))
    mirror=bpy.data.materials.new('yk_mirror_surface');mirror.use_nodes=True
    shader=next(n for n in mirror.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value=(.62,.73,.79,1);shader.inputs['Metallic'].default_value=1;shader.inputs['Roughness'].default_value=.035;M['mirror_surface']=mirror

    def shell(name,w,d,mode='fixed_pan',height=3.5,outdoor=False,ports=None,source=''):
        r=root(name);ports=ports or [('south',0,1.18)]
        if name not in ('inspection_hall_normal','inspection_hall_changed','lower_stairway','pool_edge'):
            cube(name+'_floor',(0,0,-.11),(w,d,.22),'ink',r)
        if not outdoor:
            for side,length,origin,rotation in [('south',w,(0,-d/2,0),math.pi),('north',w,(0,d/2,0),0),('west',d,(-w/2,0,0),-math.pi/2),('east',d,(w/2,0,0),math.pi/2)]:
                group=empty('front' if side=='south' else side,r,origin);group.rotation_euler.z=rotation
                holes=[(off,width) for s,off,width in ports if s==side]
                cuts=sorted(set([-length/2,length/2]+[v for off,width in holes for v in (off-width/2,off+width/2)]))
                for lo,hi in zip(cuts,cuts[1:]):
                    if any(off-width/2<(lo+hi)/2<off+width/2 for off,width in holes):
                        cube('door_lintel',((lo+hi)/2,0,(height+2.5)/2),(hi-lo,.18,height-2.5),'paper',group,.008)
                    else:
                        cube('wall',((lo+hi)/2,0,height/2),(hi-lo,.18,height),'paper',group,.008)
                        cube('lower_panel',((lo+hi)/2,-.11,.55),(hi-lo,.04,1.1),'purple',group,.004)
                        cube('panel_rail',((lo+hi)/2,-.14,1.12),(hi-lo,.04,.045),'gold',group,.004)
                for off,width in holes:
                    if width<1.3:
                        instance('door_frame_1m',group,(off,0,0))
                        instance('door_hinged_1m',group,(off,0,0))
            ceiling=empty('ceiling',r)
            cube('ceiling',(0,0,height+.06),(w,d,.12),'ivory',ceiling,.004)
            for x in [-w*.3,w*.3]:
                instance('ceiling_lamp',r,(x,0,height-.05))
                bpy.ops.object.light_add(type='POINT',location=(0,0,0));lamp=bpy.context.object;lamp.parent=r;lamp.location=(x,0,height-.5);lamp.data.energy=160;lamp.data.shadow_soft_size=.6
        rec={'id':name,'mode':mode,'size_m':[w,d,height],'file':(OUT/(name+'.glb')).relative_to(ROOT).as_posix(),'source_axes':'Blender Z-up, glTF Y-up','runtime_integrated':False,'source':source,'targets':[],'portals':[],'state':'normal','camera':{'manual_translation':mode=='free_walk'}}
        if mode=='fixed_pan':rec['camera'].update(eye_blender=[0,-d*.34,1.6],center_blender=[0,0,1.35],radius=d*.34,rotation='yaw_pitch_about_fixed_eye',pitch_limits_degrees=[-22,18],yaw_limits_degrees=[-155,155])
        else:
            entry=next((off for side,off,width in ports if side=='south'),0)
            rec['camera'].update(eye_height=1.6,spawn_blender=[-entry,-d/2+1,0])
        for side,off,width in ports:
            pos={'south':[-off,-d/2,0],'north':[off,d/2,0],'west':[-w/2,off,0],'east':[w/2,-off,0]}[side]
            rec['portals'].append({'id':name+'_'+side,'side':side,'position_blender':pos,'clear_width_m':width,'height_m':2.5})
        rooms.append((r,rec));return r,rec

    def shelves(r,positions):
        for x,y in positions:
            instance('book_shelf',r,(x,y,0))
            for z in [.4,1.05,1.7]:
                for xx in [-.35,0,.35]:instance('archive_box',r,(x+xx,y-.12,z))

    def seats(r,xs,ys,facing=math.pi):
        for x in xs:
            for y in ys:instance('chair',r,(x,y,0),facing)

    def pipe(r,points):
        for a,b in zip(points,points[1:]):bar('utility_pipe',a,b,.055,'steel',r)

    # Hotel/service wing.
    r,m=shell('electrical_room',8,7,source='rewrite_v4/03_1장_사건원장: 관리실·전기점검실·휴게실')
    for x in [-2.6,-1.3,0,1.3,2.6]:
        cube('breaker_cabinet',(x,3.1,1.5),(1.05,.45,2.3),'steel',r)
        for z in [.7,1,1.3,1.6,1.9,2.2]:cube('breaker_switch',(x,2.85,z),(.14,.05,.1),'ink',r,.008)
    pipe(r,[(-3.7,-2.6,.25),(-3.7,2.7,.25),(-3.7,2.7,2.9),(3.7,2.7,2.9)])
    r,m=shell('supply_store',10,8,source='rewrite_v4/14a: 물품실 정상 방문')
    shelves(r,[(x,3.4) for x in [-3.7,-1.2,1.2,3.7]])
    instance('detail_medical_trolley',r,(2,-1,0));instance('storage_cabinet',r,(-4,-1,0),math.pi/2)
    r,m=shell('hotel_multiuse',12,10,source='rewrite_v4/12a7·12b1: 호텔 다목적실/소품함')
    instance('blue_props_chest',r,(1,1,0));instance('meeting_table',r,(-2,2,0));seats(r,[-3,-1,2,3],[-2])
    # Food/performance area. No extra pool-to-corridor door is introduced.
    r,m=shell('refreshment_store',10,8,source='rewrite_v4/12a: 매점과 재료 분배')
    for x in [-3,0,3]:instance('kitchen_counter',r,(x,2.8,0))
    shelves(r,[(-3,-1),(3,-1)])
    r,m=shell('cold_store',8,8,source='rewrite_v4/05_2장_사건원장: 냉장보관실')
    for x in [-2.8,0,2.8]:instance('detail_cold_storage',r,(x,3.2,0))
    shelves(r,[(-2.8,0),(2.8,0)])
    r,m=shell('staff_passage',3.2,18,'free_walk',ports=[('south',0,1.18),('north',0,1.18)],source='rewrite_v4/05: 준비실↔냉장보관실, 수영장과 울타리 분리')
    for y in range(-8,9,2):
        for z in [.35,1.3]:bar('fixed_pool_fence',(1.45,y,z),(1.45,y+1.9,z),.025,'ink',r)
        bar('fence_post',(1.45,y,0),(1.45,y,1.5),.035,'ink',r)
    m['forbidden_portals']=['pool shortcut'];m['targets']=[{'id':'fixed_fence','position_blender':[1.45,0,1.2]}]
    r,m=shell('performance_stage',16,18,'fixed_pan',height=5.8,ports=[('south',0,2.4),('north',0,1.18)],source='rewrite_v4/12a2·12a3·12a6: 무대/객석/스피커/별도 입력')
    cube('stage',(0,5.2,.28),(12,5,.56),'wood',r)
    for x in [-6.1,6.1]:
        cube('speaker',(x,3.8,1.25),(1.0,.7,2),'ink',r)
        for z in [.75,1.6]:o=cyl('speaker_cone',(x,3.42,z),.28,.025,'steel',r);o.rotation_euler.x=math.pi/2
    for x in [-5.7,5.7]:
        for i in range(9):cyl('curtain_fold',(x+i*.1,7.8,2.6),.105,4.8,'rose',r,12)
    instance('microphone_stand',r,(0,4.3,.56));seats(r,[-4,-2,0,2,4],[-4.5,-2.5,-.5])
    r,m=shell('pool_edge',18,12,'free_walk',outdoor=True,source='rewrite_v4/12a2·12b2: 울타리 밖 수영장 설비')
    for x in [-7.5,7.5]:cube('pool_deck',(x,0,-.1),(3,12,.2),'ink',r)
    for y in [-4.5,4.5]:cube('pool_deck',(0,y,-.1),(12,3,.2),'ink',r)
    cube('pool_bottom',(0,0,-1.65),(12,6,.1),'ivory',r)
    for x in [-6,6]:cube('pool_wall',(x,0,-.8),(.1,6,1.6),'ivory',r)
    for y in [-3,3]:cube('pool_wall',(0,y,-.8),(12,.1,1.6),'ivory',r)
    cube('water_surface',(0,0,-.45),(11.8,5.8,.04),'glass',r,.002)
    for x in [-6.3,6.3]:cube('pool_coping',(x,0,.06),(.6,7,.12),'paper',r)
    for y in [-3.3,3.3]:cube('pool_coping',(0,y,.06),(12,.6,.12),'paper',r)
    for y in [-5,5]:
        for x in range(-8,9):bar('fence_post',(x,y,0),(x,y,1.4),.025,'ink',r)
        for z in [.35,1.1]:bar('fence_rail',(-8,y,z),(8,y,z),.035,'ink',r)
    # Mirror area: physical partitions and an elbow prevent invented direct lines of sight.
    r,m=shell('mirror_maze',16,18,'free_walk',ports=[('south',-5,1.18),('north',5,1.18)],source='rewrite_v4/13a·13a8: 거울 미로/꺾인 작업 통로')
    for x,ys in [(-4,[-5,0,5]),(0,[-6,0,6]),(4,[-4,2,6])]:
        for y in ys:
            cube('mirror_partition',(x,y,1.4),(.18,3.2,2.8),'ink',r)
            for side in [-1,1]:cube('mirror_panel',(x+side*.1,y,1.4),(.025,3.0,2.55),'mirror_surface',r,.004)
    m['reflection']='PBR mirror candidate; actual reflected actors/rays need runtime support'
    r,m=shell('mirror_workbay',10,9,'fixed_pan',source='rewrite_v4/13a8·13a12: 工作 홈/거울/벽')
    cube('work_partition',(1,1.5,1.6),(.2,5.4,3.2),'ink',r)
    cube('elbow_wall',(2.7,-1.1,1.6),(3.6,.2,3.2),'paper',r)
    instance('meeting_table',r,(-2,2,0));cube('fixed_mirror',(-4.85,1.4,1.4),(.025,3.5,2.6),'mirror_surface',r,.002)
    m['targets']=[{'id':'mirror_surface','position_blender':[-4.8,1.4,1.4]},{'id':'partition_corner','position_blender':[1,-1.2,1.4]}]
    r,m=shell('mirror_waiting',9,9,'fixed_pan',source='rewrite_v4/13a11·13b1: 대기실, 제어실과 직통 문 없음')
    instance('park_bench',r,(-2.8,1.5,0),math.pi/2);instance('park_bench',r,(2.8,1.5,0),-math.pi/2)
    m['forbidden_portals']=['direct connection to central_control'];m['state']='normal before case'
    r,m=shell('ferris_platform',16,14,'free_walk',outdoor=True,source='rewrite_v4/13a: 대관람차 승강장/직원 계단')
    wheel=empty('wheel_rotor',r,(0,3,10));wheel['animation_axis']='local Y; cabins counter-rotate to remain upright'
    for i in range(48):
        a=i*math.tau/48;b=(i+1)*math.tau/48
        for y in [-.45,.45]:bar('rim',(8*math.cos(a),y,8*math.sin(a)),(8*math.cos(b),y,8*math.sin(b)),.09,'gold',wheel)
    for i in range(12):
        a=i*math.tau/12;bar('spoke',(0,0,0),(8*math.cos(a),0,8*math.sin(a)),.055,'steel',wheel)
        pivot=empty('cabin_pivot',wheel,(8*math.cos(a),0,8*math.sin(a)-.7))
        cube('cabin_body',(0,0,0),(1.35,1.3,1.15),'rose' if i%2 else 'purple',pivot,.07)
        cube('cabin_window',(0,-.67,.15),(1.1,.025,.6),'glass',pivot,.015)
        cube('cabin_roof',(0,0,.7),(1.5,1.45,.1),'ink',pivot)
    for x in [-3.6,3.6]:
        for y in [1.5,4.5]:bar('A_frame',(x,y,0),(0,3,10),.19,'ink',r)
    cube('platform',(0,-3,.35),(6,4,.7),'ivory',r)
    r,m=shell('ferris_cabin',3,3,'fixed_pan',height=2.7,source='rewrite_v4/13a: 관람차 관찰용 객실')
    for x in [-1.4,1.4]:cube('window',(x,0,1.6),(.04,2.2,1.4),'glass',r)
    for y in [-1.3,1.3]:cube('bench',(0,y,.45),(2.5,.35,.45),'rose',r)
    r,m=shell('dream_lobby',14,10,'free_walk',ports=[('south',0,2.4),('north',0,1.18),('east',0,1.18)],source='rewrite_v4/13a2: 드림시어터 로비/개방 시간 분리')
    instance('reception_counter',r,(0,2.8,0));instance('wall_notice_plate',r,(-4,4.8,1.7));seats(r,[-4,-2,2,4],[-1])
    r,m=shell('screening_room',14,18,'fixed_pan',height=5.5,source='rewrite_v4/13a4: 공용 상영실')
    cube('screen_frame',(0,8.5,3),(11,.25,5.4),'ink',r)
    cube('screen_surface',(0,8.33,3),(10.4,.03,4.8),'paper',r)
    seats(r,[-4.5,-2.2,0,2.2,4.5],[-5,-3,-1,1,3]);m['screen_content']='separate runtime layer; no plot video baked'
    r,m=shell('reading_room',12,10,'fixed_pan',ports=[('south',0,1.18),('west',0,1.18)],source='rewrite_v4/13a4·14a2: 자료 열람석')
    for x in [-3,0,3]:
        instance('meeting_table',r,(x,0,0),math.pi/2)
        for side in [-1,1]:seats(r,[x+side*.8],[0],-side*math.pi/2)
    shelves(r,[(-3.5,4.4),(0,4.4),(3.5,4.4)])
    r,m=shell('exhibition_room',14,12,'fixed_pan',source='rewrite_v4/14a2: 방문객 전시실/옛 공원 모형')
    cube('model_table',(0,0,.6),(7,5,1.2),'ink',r)
    cube('historical_model_base',(0,0,1.25),(6.8,4.8,.1),'ivory',r)
    miniature=instance('detail_fountain_dry',r,(0,-.3,1.32));miniature.scale=(.15,)*3
    for x,y,w,d in [(-2,1.2,1.2,.8),(1.8,1.1,1.4,1),(-2,-1.2,.7,.9),(2,-1.2,1,.7)]:cube('historical_building',(x,y,1.6),(w,d,.5),'purple',r)
    m['model_is_current_map']=False
    r,m=shell('record_room',14,12,'fixed_pan',source='rewrite_v4/14a·15a: 기록실/원본과 보관 목록')
    shelves(r,[(x,y) for x in [-4.8,-2.4,2.4,4.8] for y in [1.5,5.4]])
    instance('meeting_table',r,(0,-2,0));instance('storage_cabinet',r,(-5.5,-2,0),math.pi/2)
    # Maintenance area and the physical normal/changed-state contract.
    r,m=shell('coaster_platform',18,14,'free_walk',outdoor=True,source='rewrite_v4/14a: ローラー코스터 승강장/직원 출입')
    for y in [-1,1]:
        for i in range(32):
            x=-8+i*.5;bar('track_rail',(x,y,.85),(x+.5,y,.85+.12*math.sin(i*.2)),.06,'steel',r)
    for x in [-6,-3,0,3,6]:cube('track_sleeper',(x,0,.7),(.16,2.5,.18),'wood',r)
    for x in [-3,0,3]:cube('coaster_car',(x,0,1.35),(2.4,1.5,.8),'rose',r,.15)
    r,m=shell('maintenance_workshop',14,12,'free_walk',source='rewrite_v4/14a·15a2: 정상 부속 제작/수리 작업장')
    for x in [-4,0,4]:instance('meeting_table',r,(x,3,0))
    shelves(r,[(-5.3,-1),(5.3,-1)])
    for x in [-4,-2,0,2,4]:
        cube('tool_backboard',(x,5.8,1.8),(1.6,.08,1.2),'wood',r)
        for dx in [-.4,0,.4]:bar('ordinary_tool',(x+dx,5.72,1.4),(x+dx,5.72,2.1),.018,'steel',r)
    for state in ['normal','changed']:
        r,m=shell('inspection_hall_'+state,12,12,'fixed_pan',source='rewrite_v4/14a8·14a12·09_4장_사건원장')
        m['state']=state;m['logical_location']='inspection_hall';m['water_hatch_center_blender']=[0,2,0]
        # Real floor aperture, basin and hinged lid. Nothing is hidden below a solid floor.
        cube('floor_west',(-3.6,0,-.1),(4.8,12,.2),'ink',r)
        cube('floor_east',(3.6,0,-.1),(4.8,12,.2),'ink',r)
        cube('floor_south',(0,-2.45,-.1),(2.4,7.1,.2),'ink',r)
        cube('floor_north',(0,4.45,-.1),(2.4,3.1,.2),'ink',r)
        cube('tank_bottom',(0,2,-2.1),(2.4,1.8,.2),'steel',r)
        for x in [-1.22,1.22]:cube('tank_wall',(x,2,-1),(.08,1.9,2.1),'steel',r)
        for y in [1.06,2.94]:cube('tank_wall',(0,y,-1),(2.5,.08,2.1),'steel',r)
        cube('tank_water',(0,2,-1.3),(2.35,1.75,.025),'glass',r,.001)
        hinge=empty('hatch_hinge',r,(-1.2,2,.05));hinge.rotation_euler.y=math.radians(-75 if state=='normal' else 0)
        cube('metal_cover',(1.2,0,0),(2.4,1.8,.08),'steel',hinge,.01)
        for y in [-.5,.5]:bar('cover_handle',(1,y,.08),(1.5,y,.08),.03,'ink',hinge)
        for x in [-1.35,1.35]:
            for y in [1.4,2.6]:cube('external_fixing',(x,y,.1),(.22,.22,.18),'gold',r,.01)
        cube('fixed_mesh_window',(0,5.86,2.1),(3,.04,1.2),'glass',r)
        for x in [v*.2 for v in range(-7,8)]:bar('fixed_window_mesh',(x,5.81,1.55),(x,5.81,2.65),.008,'ink',r)
        if state=='changed':
            cube('generated_partition',(2.6,1.7,1.6),(.18,7.8,3.2),'ivory',r)
            # Actual opening into blind storage, never a frame painted on solid wall.
            cube('generated_return_left',(3.13,-2.2,1.6),(1.16,.18,3.2),'ivory',r)
            cube('generated_return_right',(5.37,-2.2,1.6),(.96,.18,3.2),'ivory',r)
            cube('generated_return_lintel',(4.3,-2.2,2.85),(1.18,.18,.7),'ivory',r)
            instance('door_frame_1m',r,(4.3,-2.25,0));instance('door_hinged_1m',r,(4.3,-2.25,0))
            cube('blind_exit_backstop',(4.3,-1.6,1.6),(3.4,.18,3.2),'ink',r)
        m['targets']=[{'id':'metal_hatch','position_blender':[0,2,.15]},{'id':'external_fixing','position_blender':[1.35,1.4,.2]},{'id':'fixed_mesh_window','position_blender':[0,5.8,2.1]}]
    # Lower reception/shelter/operating records and the non-celebratory outside threshold.
    r,m=shell('lower_stairway',4,12,'free_walk',height=6.4,outdoor=True,source='rewrite_v4/16a: 하부 좁은 계단')
    for i in range(32):cube('descending_step',(0,-4.5+i*.28,-i*.18-.09),(1.8,.28,.18),'ivory',r,.005)
    for x in [-1,1]:bar('descending_handrail',(x,-4.5,.9),(x,4.18,-4.68),.035,'gold',r)
    m['camera']['spawn_blender']=[0,-4.5,0];m['lower_landing_blender']=[0,4.46,-5.76]
    r,m=shell('lower_corridor',4,22,'free_walk',ports=[('south',0,1.18),('north',0,1.18),('east',-4,1.18),('west',4,1.18)],source='rewrite_v4/16a·16b1: 사람 통로와 설비 경로 구분')
    pipe(r,[(-1.7,-10,2.7),(-1.7,10,2.7),(1.7,10,2.7)])
    for y in [-7,0,7]:cube('vent_grille',(1.86,y,1.9),(.03,1.1,.7),'steel',r)
    r,m=shell('shelter_reception',14,12,'fixed_pan',ports=[('south',0,1.18),('north',0,1.18)],source='rewrite_v4/16a: 전실/접수대/의자·접이 침상')
    instance('reception_counter',r,(0,3.5,0));instance('control_console',r,(0,4.6,0));instance('detail_office_phone',r,(-1,3.4,1.15))
    for x in [-4.5,4.5]:
        instance('park_bench',r,(x,-1,0),-math.pi/2 if x>0 else math.pi/2)
        instance('single_bed',r,(x,2,0))
    r,m=shell('shelter_inner',14,12,'fixed_pan',source='rewrite_v4/16a: 대피소 안쪽 방')
    for x in [-4,0,4]:
        for y in [-2,3]:instance('single_bed',r,(x,y,0))
    r,m=shell('operating_archive',12,10,'fixed_pan',source='rewrite_v4/16b1·16b2: 과거 운용자료와 현재 설정')
    shelves(r,[(-4,4.3),(-1.4,4.3),(1.4,4.3),(4,4.3)])
    instance('control_console',r,(0,0,0));instance('meeting_table',r,(0,-2.8,0))
    r,m=shell('loading_gate',12,12,'free_walk',source='rewrite_v4/15a·16d: 반출문과 중앙 연동')
    for x in [-2.2,2.2]:cube('gate_jamb',(x,4,1.8),(.35,.6,3.6),'ink',r)
    for side in [-1,1]:
        pivot=empty('loading_leaf_hinge',r,(side*2,4,0));cube('loading_gate_leaf',(-side,0,1.7),(2,.18,3.4),'steel',pivot)
    instance('control_console',r,(-4,2.5,0));m['state']='closed; actual unlock is separate state'
    r,m=shell('outside_threshold',16,14,'free_walk',outdoor=True,source='rewrite_v4/16d1·16d2: 외부 대면/열린결말')
    for y in [-5,-2,1,4]:cube('pavement_joint',(0,y,.006),(15,.025,.012),'ivory',r,.001)
    for x in [-6,6]:
        bar('outside_fence_post',(x,0,0),(x,0,2.4),.055,'steel',r)
    m['ending']='no celebration, rescue result, family reunion or new outcome baked'
    # Garden is a real outdoor walkable space, not an illustrated backdrop.
    r,m=shell('park_garden',24,20,'free_walk',outdoor=True,source='rewrite_v4/27·45·58: 정원 옆 감상/개인 대화')
    cube('garden_path',(0,0,.01),(4,20,.02),'ivory',r,.002)
    for x in [-7,7]:
        for y in [-6,0,6]:instance('detail_planter',r,(x,y,0))
        instance('park_bench',r,(x,3,0),-math.pi/2 if x>0 else math.pi/2)
    r,m=shell('park_main_gate',16,10,'free_walk',outdoor=True,source='rewrite_v4/10_프롤로그: 정문 조의 접근/닫힌 외부 출구')
    for x in [-3.3,3.3]:
        cube('gate_column',(x,2,2.4),(.65,.65,4.8),'ink',r,.04)
        cube('column_cap',(x,2,4.9),(.9,.9,.2),'gold',r)
    for side in [-1,1]:
        gate=empty('gate_hinge',r,(side*3,2,0))
        for i in range(12):bar('gate_picket',(-side*i*.25,0,.15),(-side*i*.25,0,3.9),.025,'ink',gate)
        for z in [.3,1.6,3.5]:bar('gate_rail',(0,0,z),(-side*2.9,0,z),.045,'gold',gate)
    m['state']='closed; no unlocked escape path implied'
    r,m=shell('ticket_booth',5,6,'fixed_pan',source='rewrite_v4/98_3장_손님_없는_매표소_보강.md')
    instance('reception_counter',r,(0,1.8,0));instance('chair',r,(0,2.6,0));instance('wall_notice_plate',r,(-1.5,2.8,1.7))
    r,m=shell('trial_elevator',8,8,'fixed_pan',height=4.3,ports=[('south',0,2.4)],source='rewrite_v4/재판 진입: 원형 승강기/재판장 이동')
    cyl('cabin_floor',(0,0,.025),3.65,.05,'purple',r,64)
    for i in range(16):
        a=i*math.tau/16
        bar('cabin_rail',(3.5*math.cos(a),3.5*math.sin(a),1),(3.5*math.cos(a+.32),3.5*math.sin(a+.32),1),.025,'gold',r)
    m['transport']='scripted vertical travel; native animation/loading connection pending'
    for r,rec in rooms:
        if rec.get('source') and rec['id'] not in [a['id'] for a in g.get('asset_records',[])]:
            rec.setdefault('production_limits',['original geometry; no borrowed meshes','runtime movement/interaction/collision unverified','material and light final art acceptance separate'])
    print('Full-story space expansion:',len(rooms),'space/state candidates',flush=True)
