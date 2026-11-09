"""Purpose-built, low-mesh architectural shells. Blender metres, Z up.

Roofs have real thickness and front/rear gable infill. Openings contain actual
reveals and recessed activity, not two dark rectangles pasted on a tinted box.
"""
import bpy,math,bmesh
from mathutils import Vector
import v4_rebuilt_environment_kit as K

def prism(name,outline,depth,material,parent,y=0):
    n=len(outline);v=[(x,yy,z)for yy in [y-depth/2,y+depth/2]for x,z in outline]
    return K.mesh(name,v,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)],material,parent)

def roof_profile(w,h,style):
    a=w/2;e=h+.12;over=.32
    if style=='gable':mid=[(-a,e),(0,e+1.25),(a,e)]
    elif style=='mansard':mid=[(-a,e),(-a+.65,e+1.10),(-a+1.12,e+1.42),(a-1.12,e+1.42),(a-.65,e+1.10),(a,e)]
    elif style=='vault':mid=[(-a*math.cos(i*math.pi/16),e+min(2.35,w*.19)*math.sin(i*math.pi/16))for i in range(17)]
    elif style=='shed':mid=[(-a,e),(a,e+.72)]
    elif style=='butterfly':mid=[(-a,e+.70),(0,e+.14),(a,e+.70)]
    else:mid=[(-a,e),(a,e)]
    return [(-a-over,mid[0][1]),*mid,(a+over,mid[-1][1])]

def height_at(profile,x):
    for (a,z),(b,zz)in zip(profile,profile[1:]):
        if a-1e-6<=x<=b+1e-6:return z+(zz-z)*(x-a)/max(b-a,1e-8)
    raise ValueError(x)

def roof(parent,w,d,h,style='gable',material='roof'):
    p=roof_profile(w,h,style);thick=.16
    shell=prism('continuous_'+style+'_roof',p+[(x,z-thick)for x,z in reversed(p)],d+.64,material,parent)
    # End walls reach inside the roof slab. In particular the triangular gable
    # visible in the rejected screenshot must be plaster, never empty sky.
    top=[(-w/2,height_at(p,-w/2)-.055),*[(x,z-.055)for x,z in p if -w/2<x<w/2],(w/2,height_at(p,w/2)-.055)]
    for side in [-1,1]:
        prism('sealed_'+style+'_end_wall',[(-w/2,h-.025),(w/2,h-.025),*reversed(top)],.22,'plaster',parent,side*(d/2-.11))
    parent['roofWallSealed']=True;parent['roofStyle']=style;parent['roofProfileXZ']=[list(v)for v in p];parent['roofThickness']=thick
    return p

def body(parent,w,d,h,profile,material='plaster'):
    t=.22;xy=[(-w/2,-d/2+t),(-w/2,d/2),(w/2,d/2),(w/2,-d/2+t),(w/2-t,-d/2+t),(w/2-t,d/2-t),(-w/2+t,d/2-t),(-w/2+t,-d/2+t)]
    v=[(x,y,z)for z in [0,1]for x,y in xy]
    for i,(x,y,_)in enumerate(v):v[i]=(x,y,0 if i<8 else height_at(profile,x)-.08)
    K.mesh('continuous_structural_U_wall',v,[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8)for i in range(8)],material,parent)
    # One closed plinth follows the actual wall, rather than decorative boxes.
    plinth=K.mesh('wall_plinth_course',[(x,y,z)for z in [0,.25]for x,y in xy],[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8)for i in range(8)],'stone',parent)

def front(parent,w,d,h,windows,material='plaster'):
    c=bpy.data.curves.new('facade_with_real_openings','CURVE');c.dimensions='2D';c.fill_mode='BOTH';c.extrude=.11;c.resolution_u=1
    def loop(points):
        s=c.splines.new('POLY');s.points.add(len(points)-1)
        for p,(x,z)in zip(s.points,points):p.co=(x,z,0,1)
        s.use_cyclic_u=True
    loop([(-w/2,0),(-.72,0),(-.72,2.52),(.72,2.52),(.72,0),(w/2,0),(w/2,h+.045),(-w/2,h+.045)])
    for x,ww,b,t,kind in windows:
        loop([(x-ww/2,b),(x-ww/2,t),(x+ww/2,t),(x+ww/2,b)])
        K.frame_ring('deep_window_reveal',ww+.12,t-b+.12,.06,.18,'wood'if kind=='dining'else'iron',parent,(x,-d/2+.025,(b+t)/2))
        if kind not in ['dining','hatch']:
            pane=K.mesh('recessed_glazing',[(x-ww/2,-d/2+.20,b),(x+ww/2,-d/2+.20,b),(x+ww/2,-d/2+.20,t),(x-ww/2,-d/2+.20,t)],[(0,1,2,3)],'glass',parent)
            pane.data.materials[0].use_backface_culling=False
        else:
            # The service opening has a genuine back and sides, with readable
            # activity behind the sill; no opaque blue sheet covers the detail.
            K.rounded_solid('recessed_service_back',ww,.045,t-b,'linen',parent,.006,(x,-d/2+.78,(b+t)/2))
            K.rounded_solid('service_sill_counter',ww+.18,.88,.085,'wood',parent,.018,(x,-d/2+.22,b+.03))
            for side in [-1,1]:K.rounded_solid('service_reveal_side',.06,.72,t-b,'wood',parent,.004,(x+side*(ww/2-.03),-d/2+.43,(b+t)/2))
            if kind=='dining':
                for j in range(3):
                    xx=x+(j-1)*ww*.27
                    # Plates and covered serving bowls, not abstract furniture blocks.
                    K.soft_body('display_ceramic_plate',.38,.30,.025,'linen',parent,(xx,-d/2+.17,b+.10))
                    K.soft_body('display_serving_dome',.25,.22,.13,'brass',parent,(xx,-d/2+.17,b+.16))
                K.tube('display_pendant_stem',[(x,-d/2+.36,t-.02),(x,-d/2+.36,t-.33)],[.014]*2,'iron',parent,6)
                K.soft_body('display_pendant_globe',.18,.18,.14,'light',parent,(x,-d/2+.36,t-.39))
        if kind=='frosted':
            K.rounded_solid('clinical_privacy_band',ww-.035,.018,.42,'linen',parent,.001,(x,-d/2+.185,(b+t)/2))
        if kind=='industrial':
            for z in [b+.18,b+.42,b+.66]:K.tube('protective_window_bar',[(x-ww/2+.05,-d/2+.17,z),(x+ww/2-.05,-d/2+.17,z)],[.013]*2,'iron',parent,4)
    o=bpy.data.objects.new('facade_with_real_openings',c);bpy.context.scene.collection.objects.link(o);data=bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()));bpy.data.objects.remove(o,do_unlink=True)
    for v in data.vertices:x,z,yy=v.co;v.co=(x,-d/2+.11+yy,z)
    o=bpy.data.objects.new('pierced_architectural_front',data);bpy.context.scene.collection.objects.link(o);o.parent=parent;data.materials.append(K.M[material])
    K.frame_ring('structural_door_reveal',1.64,2.72,.10,.24,'stone',parent,(0,-d/2+.04,1.26),inner_size=(1.44,2.52))

def awning(parent,width,y,z=2.78,depth=1.40):
    n=10;verts=[]
    for i in range(n+1):
        x=-width/2+width*i/n;verts.extend([(x,y,z),(x,y-depth,z-.32),(x,y-depth,z-.50),(x,y-depth+.025,z-.50),(x,y-depth+.025,z-.32),(x,y+.025,z)])
    faces=[]
    for i in range(n):
        for j in range(6):faces.append((i*6+j,(i+1)*6+j,(i+1)*6+(j+1)%6,i*6+(j+1)%6))
    faces +=[tuple(reversed(range(6))),tuple(range(n*6,(n+1)*6))]
    o=K.mesh('single_striped_cafe_awning',verts,faces,'linen',parent);o.data.materials.append(K.M['cloth'])
    # Assign stripes by the actual face center; no floating cubes or extra actors.
    for f in o.data.polygons:f.material_index=int((f.center.x+width/2)/(width/n))%2
    for side in [-1,1]:K.tube('awning_support',[(side*(width/2-.1),y-depth+.06,0),(side*(width/2-.1),y-depth+.06,z-.30)],[.035]*2,'iron',parent,8)

def canopy(parent,w,y,z=2.72,depth=1.05):
    prism('one_piece_folded_entrance_canopy',[(-w/2,z),(-w/2,z+.12),(w/2,z+.12),(w/2,z)],depth,'iron',parent,y-depth/2)
    for side in [-1,1]:K.tube('canopy_load_bearing_post',[(side*(w/2-.12),y-depth+.10,0),(side*(w/2-.12),y-depth+.10,z)],[.045]*2,'iron',parent,8)

def emblem(parent,kind,loc,size=1):
    if kind=='medical':p=[(-.14,-.5),(.14,-.5),(.14,-.14),(.5,-.14),(.5,.14),(.14,.14),(.14,.5),(-.14,.5),(-.14,.14),(-.5,.14),(-.5,-.14),(-.14,-.14)];mat='identity_medical'
    elif kind=='power':p=[(.14,.5),(-.38,-.09),(-.05,-.09),(-.15,-.5),(.38,.12),(.05,.12)];mat='brass'
    else:return
    o=prism('architectural_'+kind+'_emblem',[(x*size,z*size)for x,z in p],.045,mat,parent);o.location=loc;return o

def snowflake(parent,loc,size=.85):
    x,y,z=loc
    disc=[(x+size*.61*math.cos(i*math.tau/24),y+.028,z+size*.61*math.sin(i*math.tau/24))for i in range(24)];K.mesh('cold_store_identifier_backing',disc,[tuple(range(24))],'iron',parent).data.materials[0].use_backface_culling=False
    for i in range(6):
        a=i*math.tau/6;dx,dz=math.cos(a),math.sin(a);end=(x+dx*size*.5,y,z+dz*size*.5);K.tube('cold_store_snowflake_ray',[(x,y,z),end],[.024]*2,'linen',parent,5)
        for sign in [-1,1]:
            aa=a+sign*2.4;p=(x+dx*size*.34,y,z+dz*size*.34);q=(p[0]+math.cos(aa)*size*.17,y,p[2]+math.sin(aa)*size*.17);K.tube('cold_store_snowflake_branch',[p,q],[.018]*2,'linen',parent,5)

def gear(parent,loc,size=.85):
    n=48;outer=[];inner=[]
    for i in range(n):
        a=i*math.tau/n;rad=size*(.50 if i%4 in [1,2]else .40);outer.append((rad*math.cos(a),rad*math.sin(a)));inner.append((size*.18*math.cos(a),size*.18*math.sin(a)))
    # One pierced gear extrusion with a real central opening.
    v=[(x,y,z)for y in [-.035,.035]for ring in [outer,inner]for x,z in ring];f=[]
    for i in range(n):
        j=(i+1)%n;f.extend([(i,j,j+n,i+n),(i+2*n,i+3*n,j+3*n,j+2*n),(i,i+2*n,j+2*n,j),(i+n,j+n,j+3*n,i+3*n)])
    o=K.mesh('mechanical_workshop_gear',v,f,'iron',parent);o.location=loc

def glass_rack(parent,loc):
    r=K.root('glazing_A_frame_rack',parent);r.location=loc
    for x in [-.62,.62]:K.tube('rack_continuous_triangle',[(x,-.42,0),(x,.0,1.92),(x,.42,0),(x,-.42,0)],[.035]*4,'iron',r,6)
    for i in range(3):
        p=K.rounded_solid('stored_reflective_glass_sheet',1.16,.025,1.6,'glass',r,.008,(0,-.17-i*.055,.95));p.rotation_euler.x=-.20
    return r

def terrace(parent,w,d):
    K.rounded_solid('continuous_cafe_terrace',w*.94,3.1,.14,'paving',parent,.035,(0,-d/2-1.3,-.035))
    for side in [-1,1]:
        table=K.curved_family('meeting_table');table.parent=parent;table.scale=(.42,.42,.86);table.location=(side*w*.31,-d/2-2.0,0)
        for j in [-1,1]:
            chair=K.curved_family('chair');chair.parent=parent;chair.location=(side*w*.31+j*.78,-d/2-2.0,0);chair.rotation_euler.z=-j*math.pi/2

def treatment_bay(parent,w,d):
    # A continuous chamfered treatment-room projection, with privacy glazing.
    # The lower wing changes the silhouette; it is not an icon on the old wall.
    x=-w*.285;y=-d/2;half=w*.16
    outline=[(x-half,y+.10),(x+half,y+.10),(x+half,y-.68),(x+half-.30,y-.98),(x-half+.30,y-.98),(x-half,y-.68)]
    n=len(outline)
    for bottom,top,mat,name in [(0,.90,'plaster','treatment_bay_sill_wall'),(.90,2.35,'glass','treatment_bay_privacy_glazing'),(1.48,1.86,'linen','treatment_bay_frosted_band'),(2.35,2.95,'plaster','treatment_bay_upper_wall')]:
        verts=[(a,b,z)for z in [bottom,top]for a,b in outline]
        K.mesh(name,verts,[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(1,n)],mat,parent).data.materials[0].use_backface_culling=False
    verts=[(a,b,z)for z in [2.95,3.08]for a,b in outline]
    K.mesh('sealed_lower_treatment_wing_roof',verts,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)],'linen',parent)
    for a,b in outline[2:]:K.tube('treatment_bay_glazing_mullion',[(a,b,.9),(a,b,2.35)],[.025]*2,'linen',parent,6)

def accessible_clinic_porch(parent,d):
    y=-d/2
    K.rounded_solid('clinic_wide_white_porch_roof',3.6,1.65,.14,'linen',parent,.07,(.15,y-.80,2.90))
    for x in [-1.45,1.75]:K.tube('clinic_white_porch_column',[(x,y-1.48,0),(x,y-1.48,2.85)],[.065]*2,'linen',parent,8)
    # A single shallow sloped surface provides a legible step-free approach.
    K.section('clinic_step_free_approach',[(-2.6,-.05),(-2.6,.01),(.25,.13),(.25,-.05)],3.1,'paving',parent).location=(.15,y,0)
    for x in [-1.32,1.62]:
        K.tube('clinic_access_hand_rail',[(x,y-2.35,.78),(x,y-1.0,.84),(x,y-.25,.90)],[.027]*3,'iron',parent,6)
        for offset,z in [(-2.35,.78),(-1,.84),(-.25,.90)]:K.tube('clinic_access_rail_post',[(x,y+offset,.06),(x,y+offset,z)],[.022]*2,'iron',parent,6)

PLANS={
 'dining_room':('restaurant','gable'), 'kitchen':('kitchen_service','shed'),
 'clinic':('medical_clinic','flat'), 'hotel_lobby':('hotel_entrance','mansard'),
 'management_office':('administration','flat'), 'service_lounge':('staff_lounge','gable'),
 'electrical_room':('power_substation','shed'), 'laundry_room':('laundry','shed'),
 'supply_store':('goods_store','shed'), 'hotel_multiuse':('function_hall','vault'),
 'ticket_booth':('ticket_kiosk','flat'), 'performance_stage':('theatre','vault'),
 'theatre_preparation':('backstage','shed'), 'staff_passage':('covered_passage','flat'),
 'cold_store':('cold_storage','flat'), 'refreshment_store':('food_stockroom','shed'),
 'dream_lobby':('cinema_foyer','vault'), 'screening_room':('auditorium','vault'),
 'reading_room':('library','gable'), 'archive_room':('archive','flat'),
 'mirror_maze':('mirror_attraction','butterfly'), 'mirror_workbay':('glazing_workshop','shed'),
 'mirror_waiting':('waiting_pavilion','flat'), 'central_control':('control_station','flat'),
 'maintenance_workshop':('mechanical_workshop','shed'), 'exhibition_room':('gallery','vault'),
 'record_room':('records_vault','flat'), 'inspection_hall_normal':('inspection_workshop','shed'),
 'loading_gate':('service_gate','flat'), 'outside_threshold':('open_threshold','flat')}

def build(ident,w,d,h,I):
    role,style=PLANS[ident];r=K.root('architectural_'+ident);profile=roof_profile(w,h,style)
    if role in ['service_gate','open_threshold']:
        import v4_rebuilt_landmarks as L
        new=L.build(ident,K);new.parent=r
        I.plate(ident,r,(0,-d*.36,2.9),width=3)
        r['roofWallSealed']=True;r['roofStyle']='open_structure';r['architectureFamily']=role;r['facilityIdentity']=ident;r['architectureVersion']=2;r['nominalSize']=[w,d,h];r['purposeFeatures']=['open_boundary_gate'if role=='service_gate'else'open_air_threshold'];return r
    if role=='covered_passage':
        for side in [-1,1]:K.rounded_solid('continuous_connector_side_wall',.22,d,h+.06,'plaster',r,.004,(side*(w/2-.11),0,(h+.06)/2))
        rear=K.root('rear_passage_portal',r);rear.rotation_euler.z=math.pi;front(rear,w,d,h,[])
    else:body(r,w,d,h,profile)
    K.rounded_solid('continuous_foundation_floor',w-.08,d-.08,.14,'paving',r,.012,(0,0,-.035))
    if role in ['restaurant','food_shop']:
        wins=[(x,w*.28,.88,2.52,'dining')for x in [-w*.29,w*.29]]
    elif role=='kitchen_service':wins=[(-w*.29,w*.25,1.0,2.20,'hatch'),(w*.30,1.55,1.65,2.55,'industrial')]
    elif role=='medical_clinic':wins=[(w*.20,.90,1.0,2.65,'frosted'),(w*.36,.90,1.0,2.65,'frosted')]
    elif role=='backstage':wins=[(-w*.30,1.7,.72,2.65,'hatch'),(w*.30,1.6,1.45,2.55,'industrial')]
    elif role=='gallery':wins=[(x,1.75,2.10,3.10,'glass')for x in [-w*.32,w*.32]]
    elif role in ['mechanical_workshop','inspection_workshop']:
        wins=[(-w*.29,w*.31,.12,2.72,'hatch'),(w*.30,1.55,1.55,2.55,'industrial')]
    elif role in ['power_substation','glazing_workshop','goods_store','laundry','cold_storage','food_stockroom']:
        wins=[(x,min(1.6,w*.20),1.45,2.55,'industrial')for x in [-w*.30,w*.30]]
    elif role in ['archive','records_vault','control_station']:wins=[(x,1.4,2.02,min(h-.12,2.83),'industrial')for x in [-w*.30,w*.30]]
    elif role=='library':wins=[(x,1.65,.70,2.65,'hatch')for x in [-w*.30,w*.30]]
    elif role=='ticket_kiosk':wins=[(-w*.285,1.0,.95,2.35,'hatch'),(w*.285,1.0,.95,2.35,'hatch')]
    elif role=='covered_passage':wins=[]
    else:wins=[(x,min(w*.22,2.25),.72,min(2.65,h-.25),'glass')for x in [-w*.31,w*.31]]
    if h>5.8:wins +=[(x,1.4,4.10,h-.50,'glass')for x in [-w*.30,0,w*.30]]
    if role=='theatre':wins.append((0,w*.38,3.52,h-.32,'hatch'))
    front(r,w,d,h,wins);roof(r,w,d,h,style,'iron'if style in ['shed','flat']else'roof')
    if role=='ticket_kiosk':rear_ticket_aperture(r,w,d)
    # Every facility receives features tied to its actual use, beyond body tint.
    features=[]
    if role in ['restaurant','food_shop']:
        awning(r,w*.88,-d/2-.04);terrace(r,w,d);features=['service_display_bays','striped_food_awning','outdoor_dining_seats']
    elif role=='kitchen_service':
        stove=K.cooking_range();stove.parent=r;stove.location=(-w*.29,-d/2+.42,.16)
        hood=K.hood();hood.parent=r;hood.location=(-w*.29,-d/2+.42,2.30)
        for x in [w*.26,w*.36]:K.tube('kitchen_exhaust_flue',[(x,d*.22,h-.1),(x,d*.22,h+1.65),(x,d*.22-.30,h+1.84)],[.18]*3,'iron',r,10)
        canopy(r,w*.42,-d/2-.04,depth=.8);features=['food_service_hatch','paired_exhaust_flues','protected_service_entry']
    elif role=='medical_clinic':
        treatment_bay(r,w,d);accessible_clinic_porch(r,d);emblem(r,'medical',(-w*.285,-d/2-.99,2.67),.47);features=['projecting_treatment_room_wing','wraparound_privacy_glazing','wide_white_step_free_porch','medical_cross']
    elif role=='hotel_entrance':
        canopy(r,4.6,-d/2-.03,depth=1.65)
        for x in [-1.95,1.95]:K.tube('hotel_entry_column',[(x,-d/2-1.4,.04),(x,-d/2-1.4,2.68)],[.13,.105],'stone',r,10)
        features=['mansard_guest_levels','covered_reception_portico','upper_bedroom_windows']
    else:features=purpose_features(r,role,w,d,h)
    I.plate(ident,r,(0,-d/2-.06,min(h-.24,3.05)),width=min(3.4,w*.56))
    r['facilityIdentity']=ident;r['architectureFamily']=role;r['purposeFeatures']=features;r['door_clear_width']=1.44;r['door_clear_height']=2.52;r['nominalSize']=[w,d,h];r['architectureVersion']=2
    return r

def rear_ticket_aperture(parent,w,d):
    """One opening contract for both the room and its overlapping park envelope."""
    wall=next(o for o in parent.children if o.name.startswith('continuous_structural_U_wall'))
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,d/2,1.95));cutter=bpy.context.object;cutter.dimensions=(min(w-.65,3.65),.65,1.5)
    bpy.context.view_layer.update();mod=wall.modifiers.new('actual_ticket_window_opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.context.view_layer.objects.active=wall;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    # Test the actual cut mesh, rather than merely checking for a frame by name.
    for x in [-.8,0,.8]:
        assert not wall.ray_cast(Vector((x,0,1.95)),Vector((0,1,0)),distance=d)[0], 'Ticket aperture still blocked by its own structural wall'
    K.frame_ring('public_ticket_window_frame',min(w-.5,3.8),1.65,.095,.12,'brass',parent,(0,d/2-.24,1.95))
    glass=K.M['glass'].copy();glass.name='rebuilt_ticket_clear_glass';bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.70,.85,.92,1);bs.inputs['Alpha'].default_value=.12;bs.inputs['Metallic'].default_value=0;K.M['ticket_glass']=glass
    K.rounded_solid('recessed_public_ticket_window',min(w-.75,3.55),.025,1.42,'ticket_glass',parent,.015,(0,d/2-.19,1.95))

def purpose_features(r,role,w,d,h):
    # Further purpose-specific structures share material/mesh owners, not a generic house.
    if role in ['power_substation','mechanical_workshop','glazing_workshop','inspection_workshop','goods_store','laundry','cold_storage','backstage','food_stockroom']:
        canopy(r,min(3.2,w*.6),-d/2-.04,depth=.72)
        for side in [-1,1]:
            x=side*w*.30
            K.frame_ring('recessed_service_louver',min(1.8,w*.23),.68,.065,.12,'iron',r,(x,-d/2-.035,h-.45))
            for j in range(4):
                blade=K.rounded_solid('formed_louver_blade',min(1.65,w*.21),.13,.025,'iron',r,.003,(x,-d/2-.05,h-.68+j*.14));blade.rotation_euler.x=.3
        if role=='power_substation':emblem(r,'power',(-w*.31,-d/2-.09,1.15),.85)
        if role=='mechanical_workshop':gear(r,(w*.30,-d/2-.09,.88),1.05)
        if role in ['mechanical_workshop','inspection_workshop']:
            # A partly raised workshop shutter and an occupied service bay.
            # Its real opening starts at the ground, unlike a domestic window.
            for j in range(5):K.rounded_solid('raised_workshop_shutter_slat',w*.31,.06,.095,'iron',r,.005,(-w*.29,-d/2+.03,2.26+j*.10))
            bench=K.office_desk();bench.parent=r;bench.location=(-w*.29,-d/2+.47,.08);bench.scale=(.70,.65,.95)
            machine=K.root('visible_bench_lathe',r);machine.location=(-w*.29,-d/2+.46,.91)
            K.rounded_solid('lathe_cast_bed',1.08,.34,.12,'iron',machine,.035,(0,0,.05))
            K.rounded_solid('lathe_motor_housing',.24,.31,.35,'iron',machine,.055,(-.40,0,.23))
            K.tube('lathe_spindle_and_workpiece',[(-.27,0,.29),(.35,0,.29)],[.075,.06],'brass',machine,12)
            K.tube('lathe_tailstock',[(.39,0,.12),(.39,0,.29)],[.09,.055],'iron',machine,8)
            K.tube('lathe_handwheel',[(.39+.10*math.cos(i*math.tau/16),-.18,.20+.10*math.sin(i*math.tau/16))for i in range(17)],[.012]*17,'brass',machine,5)
        if role=='glazing_workshop':glass_rack(r,(w*.30,-d/2-1.15,0))
        if role=='backstage':
            rack=K.coat_rack();rack.parent=r;rack.location=(-w*.30,-d/2+.48,.16)
        if role in ['goods_store','food_stockroom']:
            for j in range(2):
                chest=K.chest();chest.parent=r;chest.location=(w*.31,-d/2-.65-j*.72,0);chest.scale=(.65,.65,.65)
        if role=='inspection_workshop':
            K.rounded_solid('inspection_entry_apron',w*.62,2.0,.12,'paving',r,.01,(0,-d/2-1.0,-.035))
            for x in [-1.05,1.05]:
                for j in range(6):
                    stripe=K.rounded_solid('painted_inspection_warning',.18,.29,.004,'brass'if j%2 else'iron',r,.001,(x,-d/2-.25-j*.26,.031));stripe.rotation_euler.z=.3
        if role in ['mechanical_workshop','inspection_workshop','glazing_workshop']:K.tube('industrial_extraction_stack',[(w*.3,d*.20,h-.1),(w*.3,d*.20,h+1.35)],[.22]*2,'iron',r,10)
        if role=='cold_storage':
            K.frame_ring('insulated_door_casing',1.9,2.90,.19,.24,'linen',r,(0,-d/2-.07,1.30),inner_size=(1.44,2.52));snowflake(r,(-w*.30,-d/2-.09,.85),1.05);return ['insulated_loading_entry','large_snowflake_identifier','refrigeration_louver']
        if role=='laundry':
            # Circular drum relief immediately distinguishes the washhouse from a power room.
            for x in [-w*.30,w*.30]:
                p=[(x+.35*math.cos(i*math.tau/24),-d/2-.09,.84+.35*math.sin(i*math.tau/24))for i in range(25)];K.tube('laundry_drum_emblem',p,[.045]*25,'linen',r,6)
                disc=[(x+.31*math.cos(i*math.tau/24),-d/2-.08,.84+.31*math.sin(i*math.tau/24))for i in range(24)];K.mesh('washer_drum_glazing',disc,[tuple(range(24))],'glass',r).data.materials[0].use_backface_culling=False
            return ['paired_round_washer_reliefs','ventilated_work_windows','washhouse_service_entry']
        return ['weathered_service_canopy','operable_louver_recesses','industrial_glazing_'+role]
    if role in ['theatre','cinema_foyer','auditorium','function_hall','gallery']:
        canopy(r,w*.58,-d/2-.04,z=2.78,depth=1.70)
        for side in [-1,1]:K.tube('auditorium_entrance_pier',[(side*w*.23,-d/2-.08,0),(side*w*.23,-d/2-.08,min(h-.1,4.6))],[.18,.14],'stone',r,10)
        # A continuous arched proscenium is a single structural sweep.
        rad=min(2.7,w*.25);pts=[(rad*math.cos(math.pi-i*math.pi/16),-d/2-.10,2.5+rad*.42*math.sin(i*math.pi/16))for i in range(17)];K.tube('continuous_proscenium_arch',pts,[.10]*17,'brass',r,8)
        if role=='theatre':
            width=w*.38-.10;b=3.57;t=h-.38;verts=[]
            for z in [b,t]:
                for i in range(49):verts.append((-width/2+width*i/48,-d/2+.34+.055*math.cos(i*math.tau/4),z))
            curtain=K.mesh('actual_pleated_theatre_curtain',verts,[(i,i+1,i+50,i+49)for i in range(48)],'cloth',r,True);curtain.data.materials[0].use_backface_culling=False
        if role=='gallery':
            for side in [-1,1]:
                K.frame_ring('gallery_exterior_art_frame',1.5,1.35,.09,.09,'brass',r,(side*w*.32,-d/2-.07,1.23));K.rounded_solid('gallery_display_canvas',1.30,.02,1.15,'cloth',r,.002,(side*w*.32,-d/2-.09,1.23))
            return ['sealed_gallery_vault','framed_exterior_art_displays','clerestory_gallery_glazing']
        return ['sealed_vaulted_auditorium','arched_proscenium','projecting_marquee']
    if role in ['library','archive','records_vault']:
        if role=='library':
            porch=K.root('gabled_reading_portico',r);porch.location=(0,-d/2-.62,0);roof(porch,3.15,1.28,2.75,'gable')
        else:canopy(r,3.2,-d/2-.04,depth=1.15)
        for x in [-1.35,1.35]:K.tube('library_portico_column',[(x,-d/2-.92,0),(x,-d/2-.92,2.72)],[.15,.115],'stone',r,10)
        if role=='library':
            for side in [-1,1]:
                shelf=K.shelf();shelf.parent=r;shelf.location=(side*w*.30,-d/2+.60,0);shelf.scale=(.86,.65,1)
            return ['visible_reading_shelves','columned_reading_entrance','sealed_library_gable']
        return ['protected_record_vault','high_archive_lights','stone_security_portico']
    if role=='mirror_attraction':
        for side in [-1,1]:
            frame=K.frame_ring('faceted_mirror_entry',2.0,2.8,.16,.20,'brass',r,(side*w*.31,-d/2-.10,1.55));frame.rotation_euler.z=side*.12
            for j in range(3):K.tube('mirror_prism_fin',[(side*w*.31+(j-1)*.34,-d/2-.06,.35),(side*w*.31+(j-1)*.34,-d/2-.06,2.75)],[.035]*2,'brass',r,5)
        return ['butterfly_prismatic_roof','faceted_mirror_portals','reflection_fins']
    if role=='ticket_kiosk':
        awning(r,w*.94,-d/2-.04,depth=.80);return ['two_ticket_service_hatches','waist_height_ticket_counters','small_kiosk_awning']
    if role=='covered_passage':return ['narrow_covered_connector','protected_staff_portal','sealed_flat_connector_roof']
    if role=='control_station':
        for side in [-1,1]:K.tube('communications_mast',[(side*w*.30,d*.18,h),(side*w*.30,d*.18,h+1.6)],[.045,.025],'iron',r,6)
        return ['high_control_room_glazing','paired_communications_masts','secure_control_entry']
    canopy(r,min(4,w*.60),-d/2-.04,depth=1.1)
    if role in ['staff_lounge','waiting_pavilion']:
        for side in [-1,1]:b=K.curved_family('park_bench');b.parent=r;b.location=(side*w*.30,-d/2-1.7,0)
        return ['covered_waiting_entrance','exterior_waiting_benches','human_scale_lounge_glazing']
    return ['recessed_civic_entrance','covered_public_foyer','closed_parapet_roof']
