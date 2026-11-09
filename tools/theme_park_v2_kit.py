"""Text-free, connected fairground architecture, Blender metres / Z-up.

Large forms are authored meshes; existing own PBR maps supply surface detail.
No downloaded park models or typography is used.
"""
import bpy,math
from mathutils import Vector
import v4_rebuilt_environment_kit as K
from v4_facility_forms import curve_wall,roof_band
TAU=math.tau
def palette():
    K.setup_materials()
    for name,color,metal in [('ivory',(.86,.81,.74),0),('coral',(.66,.21,.30),0),('cobalt',(.25,.31,.51),.03),('violet',(.40,.26,.48),.03),('mint',(.29,.49,.43),.03),('gold',(.78,.62,.37),.20),('copper',(.56,.34,.22),.25),('steel',(.25,.30,.37),.20)]:
        base='iron' if name=='steel' else 'brass' if name in ['gold','copper'] else 'plaster' if name=='ivory' else 'lacquer'
        m=K.M[base].copy();m.name='theme_v2_'+name;m['surfaceTint']=[*color,1];m.diffuse_color=(*color,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=.48
        inp=bs.inputs['Base Color'];old=next(iter(inp.links),None)
        if name in ['coral','cobalt','violet','mint']:
            tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=next(n.image for n in K.M['plaster'].node_tree.nodes if n.type=='TEX_IMAGE'and n.image and n.image.colorspace_settings.name!='Non-Color');mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*color,1);m.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],inp)
        elif old:
            source=old.from_socket;mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*color,1);m.node_tree.links.new(source,mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],inp)
        else:inp.default_value=(*color,1)
        K.M[name]=m
    m=K.M['light'].copy();m.name='theme_v2_warm_bulb';bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Strength'].default_value=.65;K.M['bulb']=m
    m=K.M['glass'].copy();m.name='form_display_glass';bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Alpha'].default_value=.2;bs.inputs['Metallic'].default_value=0;K.M['window_clear']=m
    m=K.M['grass'].copy();m.name='theme_v2_clipped_hedge';m['surfaceTint']=[.52,.62,.53,1];K.M['clipped_hedge']=m
    for name,tint in [('guest_paving',(.39,.36,.44,1)),('main_paving',(.75,.68,.67,1)),('planting_soil',(.32,.29,.35,1))]:
        m=K.M['paving'if name!='planting_soil'else'wood'].copy();m.name='theme_v2_'+name;m['surfaceTint']=list(tint);bs=m.node_tree.nodes.get('Principled BSDF')
        for link in list(bs.inputs['Roughness'].links):m.node_tree.links.remove(link)
        bs.inputs['Roughness'].default_value=.94;bs.inputs['Metallic'].default_value=0
        for node in m.node_tree.nodes:
            if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.18
        K.M[name]=m
def root(name,parent,at=(0,0,0),yaw=0):
    o=K.root(name,parent);o.location=at;o.rotation_euler.z=yaw;return o
def tube(name,pts,r,mat,p,n=8):return K.tube(name,pts,[r]*len(pts),mat,p,n)
def lathe(name,profile,mat,p,n=32,at=(0,0,0)):
    v=[(at[0]+r*math.cos(i*TAU/n),at[1]+r*math.sin(i*TAU/n),at[2]+z)for r,z in profile for i in range(n)]
    faces=[tuple(reversed(range(n))),tuple(range((len(profile)-1)*n,len(profile)*n))]+[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i)for k in range(len(profile)-1)for i in range(n)]
    return K.mesh(name,v,faces,mat,p,True,uv_scale=.35)
def ball(name,p,at,r,mat='bulb'):
    return lathe(name,[(r*.015,-r),(r*.65,-r*.65),(r,0),(r*.65,r*.65),(r*.015,r)],mat,p,8,at)
def ring(name,p,r,z,mat='gold',thickness=.045,center=(0,0),steps=64):
    return tube(name,[(center[0]+r*math.cos(i*TAU/steps),center[1]+r*math.sin(i*TAU/steps),z)for i in range(steps+1)],thickness,mat,p)
def bulbs(p,pts,spacing=.45):
    for a,b in zip(pts,pts[1:]):
        a,b=Vector(a),Vector(b);count=max(1,math.ceil((b-a).length/spacing))
        for i in range(count):ball('sealed_fairground_lamp',p,tuple(a+(b-a)*i/count),.055)
def profile_extrude(name,profile,length,mat,p,at=(0,0,0),yaw=0):
    obj=K.section(name,profile,length,mat,p);obj.location=at;obj.rotation_euler.z=yaw;return obj
def arch_points(cx,bottom,w,h,steps=20):
    return [(cx-w/2,bottom),(cx-w/2,bottom+h-w/2)]+[(cx+w/2*math.cos(math.pi-i*math.pi/steps),bottom+h-w/2+w/2*math.sin(math.pi-i*math.pi/steps))for i in range(steps+1)]+[(cx+w/2,bottom)]
def arched_window(p,x,y,z,w=1.0,h=1.8):
    outline=arch_points(x,z,w,h);o=curve_wall('recessed_arch_window',outline,[],y,'window_clear',p,.035)
    frame=[(a,y-.06,b)for a,b in outline+[outline[0]]];tube('continuous_window_reveal',frame,.06,'ivory',p)
    tube('arched_window_mullion',[(x,y-.075,z+.1),(x,y-.075,z+h-.1)],.025,'steel',p)
    return o
def roof(p,w,d,h,mat='cobalt',rise=2.0):
    # Fitted hip/mansard shell with continuous eaves, no intersecting roof blocks.
    v=[]
    for ww,dd,z in [(w+.6,d+.6,h),(w*.78,d*.78,h+rise*.73),(w*.60,d*.60,h+rise)]:v +=[(-ww/2,-dd/2,z),(ww/2,-dd/2,z),(ww/2,dd/2,z),(-ww/2,dd/2,z)]
    f=[(k*4+i,k*4+(i+1)%4,(k+1)*4+(i+1)%4,(k+1)*4+i)for k in range(2)for i in range(4)]+[(8,9,10,11)]
    o=K.mesh('fitted_mansard_roof_shell',v,f,mat,p,uv_scale=.45);o.modifiers.new('actual_roof_thickness','SOLIDIFY').thickness=.13
    tube('continuous_roof_eaves',[*v[:4],v[0]],.09,'gold',p);return o
def turret(p,x,y,r,h,mat='cobalt'):
    lathe('connected_turret_masonry',[(r*1.08,0),(r*1.08,.25),(r,.45),(r,h-.35),(r*1.12,h-.20),(r*1.12,h)],'ivory',p,24,(x,y,0))
    lathe('fitted_bell_turret_roof',[(r*1.30,h-.05),(r*1.30,h+.18),(r*.94,h+.50),(r*.72,h+1.05),(r*.62,h+1.75),(r*.20,h+2.25),(.025,h+2.5)],mat,p,24,(x,y,0))
    ball('turret_crown_finial',p,(x,y,h+2.6),.13,'gold')
    for z in [h*.42,h*.71]:arched_window(p,x,y-r-.025,z,.48,1.0)
def fence(p,points,mat='steel',height=1.0):
    tube('continuous_safety_top_rail',[(x,y,height)for x,y in points],.045,mat,p)
    tube('continuous_safety_low_rail',[(x,y,.25)for x,y in points],.028,mat,p)
    for a,b in zip(points,points[1:]):
        a,b=Vector(a),Vector(b);n=max(1,math.ceil((b-a).length/.75))
        for i in range(n):
            q=a+(b-a)*i/n;tube('fixed_safety_upright',[(q.x,q.y,.02),(q.x,q.y,height+.04)],.027,mat,p,6)
def round_enclosure(p,r,gate_width=2.2):
    gap=math.asin(gate_width/(2*r));pts=[(r*math.cos(-math.pi/2+gap+(TAU-2*gap)*i/96),r*math.sin(-math.pi/2+gap+(TAU-2*gap)*i/96))for i in range(97)]
    fence(p,pts,'gold');fence(p,[(-gate_width/2,-r),(gate_width/2,-r)],'steel')
def queue(p,at,width=4.6,length=7.2,lanes=3,yaw=0):
    q=root('separated_queue_and_exit',p,(*at,0),yaw)
    for i in range(lanes+1):
        x=-width/2+width*i/lanes;y0=-length/2+(0 if i in [0,lanes]else (1.1 if i%2 else 0));y1=length/2-(0 if i in [0,lanes]else (1.1 if not i%2 else 0));fence(q,[(x,y0),(x,y1)])
    fence(q,[(-width/2,length/2),(width/2,length/2)]);return q
def bunting(p,pts,matrices=('coral','ivory','cobalt')):
    tube('suspended_festoon_wire',pts,.016,'steel',p,6)
    for a,b in zip(pts,pts[1:]):
        a,b=Vector(a),Vector(b);n=max(1,math.floor((b-a).length/.85))
        for i in range(n):
            v=a+(b-a)*(i+.5)/n;K.mesh('sewn_pennant',[tuple(v+Vector((-.26,0,0))),tuple(v+Vector((.26,0,0))),tuple(v+Vector((0,0,-.5)))],[(0,1,2)],matrices[i%len(matrices)],p,uv_scale=1)
def booth(p,at,yaw=0,kind='rings',mat='coral'):
    r=root('purpose_midway_booth_'+kind,p,(*at,0),yaw);w=5.1;d=3.8
    # Continuous U-shaped casework, deep counter, fitted barrel canopy.
    profile_extrude('coherent_hollow_booth_case',[(-d/2,0),(-d/2,.95),(-d/2+.22,.95),(-d/2+.22,.10),(d/2-.16,.10),(d/2-.16,2.5),(d/2,2.5),(d/2,0)],w,'wood',r)
    profile_extrude('booth_countertop',[(-2.1,.95),(-1.45,.95),(-1.45,1.03),(-2.1,1.03)],w+.14,'gold',r)
    for x in [-w/2,w/2]:tube('booth_canopy_support',[(x,-d/2,0),(x,-d/2,3.4)],.095,'gold',r)
    points=[(-w/2*math.cos(i*math.pi/32),3.15+.8*math.sin(i*math.pi/32))for i in range(33)]
    profile_extrude('booth_fitted_barrel_roof',roof_band(points,.10),d+.65,mat,r,yaw=math.pi/2)
    for i in range(10):
        x=-w/2+(i+.5)*w/10;K.mesh('scalloped_booth_valance',[(x-w/20,-d/2-.33,3.16),(x+w/20,-d/2-.33,3.16),(x+w/20,-d/2-.33,2.96),(x,-d/2-.33,2.82),(x-w/20,-d/2-.33,2.96)],[(0,1,2,3,4)],'ivory'if i%2 else mat,r,uv_scale=.5)
    bulbs(r,[(-2.5,-2.12,3.18),(2.5,-2.12,3.18)],.4)
    if kind=='rings':
        for row in range(2):
            for col in range(7):
                x=(col-3)*.48;y=.8+row*.36;lathe('ring_game_bottle',[(.10,.98),(.10,1.21),(.055,1.28),(.05,1.48),(.07,1.51)],'mint',r,10,(x,y,0))
        for i in range(3):ring('wooden_toss_ring',r,.21,1.01,'gold',.022,(-1+i*.55,-1.5),24)
    elif kind=='cans':
        for row in range(3):
            for i in range(3-row):lathe('stacked_midway_can',[(.19,.98+row*.42),(.20,1.01+row*.42),(.20,1.36+row*.42),(.19,1.40+row*.42)],'ivory'if row%2 else'mint',r,12,((i-(2-row)/2)*.44,1,0))
        for x in [-.8,-.3,.2]:ball('toss_ball',r,(x,-1.5,1.12),.10,'coral')
    elif kind=='masks':
        for x in [-1.3,0,1.3]:mask(r,(x,1.35,2.0),.52,x<0)
    elif kind=='clockwork':
        for x in [-1.35,0,1.35]:gear(r,(x,1.2,1.9),.48,12,'gold',.12)
    elif kind=='orbit':
        for x in [-1.35,0,1.35]:
            lathe('formed_space_midway_collectible',[(.40,0),(.48,.12),(.46,.2),(.25,.28),(.13,.52),(.025,.62)],'mint',r,20,(x,1.1,1.08))
    else:
        for i in range(3):
            c=root('shaped_fairground_prize',r,((i-1)*1.1,1.45,1.95));ball('prize_head',c,(0,0,0),.22,'ivory');ball('prize_body',c,(0,0,-.35),.27,'ivory')
            for side in [-1,1]:tube('prize_rabbit_ear',[(side*.10,0,.15),(side*.16,0,.55)],.075,'ivory',c,8)
    return r

def carousel(p,at):
    r=root('complete_royal_carousel',p,(*at,0));radius=6.7
    lathe('carousel_boarding_deck',[(radius,0),(radius,.18),(radius-.2,.33)],'wood',r,64)
    lathe('carousel_central_mirrored_drum',[(.95,.3),(1.12,.5),(.9,.7),(.9,4.8),(1.25,5.1)],'gold',r,32)
    for i in range(12):
        a=i*TAU/12;x,y=5.1*math.cos(a),5.1*math.sin(a)
        lathe('turned_pavilion_column',[(.20,.3),(.20,.5),(.11,.75),(.11,4.8),(.19,5.0),(.19,5.3)],'ivory',r,12,(x,y,0))
    for i in range(10):
        a=i*TAU/10;pony=root('carousel_pony',r,(4.0*math.cos(a),4.0*math.sin(a),1.0),a+math.pi/2)
        # Connected shaped body and a rising neck, with muzzle, ears and saddle.
        K.tube('pony_carved_body',[(-.7,0,.5),(-.25,0,.68),(.35,0,.7),(.65,0,.65)],[.20,.32,.30,.20],'ivory',pony,14)
        K.tube('pony_continuous_neck',[(.48,0,.63),(.77,0,1.05),(.71,0,1.50),(.94,0,1.59),(1.18,0,1.43)],[.25,.20,.15,.18,.11],'ivory',pony,12)
        for side in [-1,1]:
            K.tube('pony_ear',[(.84,side*.1,1.67),(.80,side*.13,1.95)],[.06,.014],'ivory',pony,6)
            for x,bend in [(-.43,-.16),(.41,.22)]:K.tube('pony_leg',[(x,side*.18,.5),(x+bend,side*.21,.12),(x+bend+.12,side*.21,-.14)],[.09,.065,.075],'ivory',pony,8)
        K.tube('pony_tail',[(-.66,0,.65),(-1.0,.05,.48),(-1.14,.16,.18)],[.12,.09,.02],'gold',pony,8)
        lathe('curved_saddle',[(.28,.86),(.31,.91),(.25,.98)],'coral',pony,16)
        tube('carousel_brass_mounting_pole',[(0,0,-.6),(0,0,4.2)],.035,'gold',pony)
    # Complete ornate drum/fascia and bell roof; ridge and eaves are fitted.
    lathe('carved_carousel_fascia',[(6.9,5.25),(7.08,5.38),(7.08,6.1),(6.9,6.25)],'coral',r,64)
    lathe('continuous_carousel_bell_roof',[(7.0,6.17),(6.6,6.45),(5.2,6.9),(3.5,7.25),(1.4,7.8),(.2,8.5),(.025,8.75)],'cobalt',r,64)
    for z in [5.4,6.08]:ring('carousel_continuous_gilded_course',r,7.1,z)
    for i in range(24):
        a=i*TAU/24;ball('fascia_embedded_lamp',r,(7.12*math.cos(a),7.12*math.sin(a),5.76),.075)
        b=root('sculpted_fascia_medallion',r,(7.12*math.cos(a),7.12*math.sin(a),5.77),a);ball('fascia_raised_flower_center',b,(0,0,0),.12,'gold')
    round_enclosure(r,8.1);queue(r,(-10.1,-4),3.3,6.0,2)
    return r
def teacups(p,at):
    r=root('complete_teacup_attraction',p,(*at,0));lathe('tea_ride_rotating_floor',[(7.3,0),(7.3,.22),(7.1,.34)],'cobalt',r,64)
    for i in range(6):
        a=i*TAU/6;c=root('formed_teacup_vehicle',r,(4.6*math.cos(a),4.6*math.sin(a),.34),a)
        lathe('teacup_saucer',[(1.9,0),(1.95,.10),(1.7,.19),(.55,.22)],'ivory',c,32)
        lathe('hollow_teacup_body',[(.75,.2),(.90,.32),(1.25,.8),(1.45,1.45),(1.40,1.56),(1.25,1.50),(1.10,.8),(.45,.50)],'coral'if i%2 else'mint',c,32)
        tube('teacup_continuous_handle',[(1.38+.57*math.sin(k*math.pi/20),0,.98+.55*math.cos(k*math.pi/20))for k in range(21)],.11,'gold',c)
        tube('teacup_central_wheel_support',[(0,0,.5),(0,0,1.12)],.045,'steel',c);ring('teacup_steering_wheel',c,.35,1.12,'gold',.035)
    lathe('central_teapot',[(.7,.34),(1.0,.45),(1.5,1.1),(1.3,2.0),(.9,2.4),(.8,2.55)],'ivory',r,32)
    tube('teapot_curved_spout',[(1.0,0,1.2),(1.9,0,1.4),(2.25,0,2.2),(2.4,0,2.35)],.23,'ivory',r,12)
    tube('teapot_handle',[(-1.05-.8*math.sin(k*math.pi/24),0,1.5+.7*math.cos(k*math.pi/24))for k in range(25)],.15,'gold',r,10)
    lathe('teapot_fitted_lid',[(.86,2.5),(.9,2.6),(.25,2.86),(.12,3.1)],'coral',r,32)
    round_enclosure(r,8.1);queue(r,(-10,-3),3.3,5.5,2);return r
def swing_ride(p,at):
    r=root('complete_suspended_chair_ride',p,(*at,0));lathe('swing_ride_boarding_platform',[(7.6,0),(7.6,.18),(7.45,.3)],'wood',r,64)
    lathe('swing_ride_tapered_mast',[(1.5,.3),(1.6,.6),(1.05,1.0),(.72,6.1),(1.1,6.6)],'ivory',r,32)
    lathe('swing_ride_decorated_crown',[(2.0,6.5),(5.6,6.7),(6.5,7.15),(6.5,7.85),(5.5,8.0),(3.2,8.25),(.35,9.2),(.04,9.35)],'coral',r,64)
    for z,rr in [(7.15,6.55),(7.8,6.55),(8.1,5.0)]:ring('swing_crown_gilded_rim',r,rr,z)
    for i in range(20):
        a=i*TAU/20;x,y=5.35*math.cos(a),5.35*math.sin(a);seat=root('suspended_swing_seat',r,(x,y,.75),a+math.pi/2)
        profile_extrude('formed_swing_bucket',[(-.28,0),(.3,0),(.34,.55),(.25,.59),(.20,.12),(-.28,.12)],.55,'cobalt',seat)
        for side in [-1,1]:tube('actual_seat_suspension_chain',[(x+side*.23*math.cos(a),y+side*.23*math.sin(a),7.05),(x+side*.23*math.cos(a),y+side*.23*math.sin(a),1.2)],.016,'steel',r,6)
        ball('crown_inset_light',r,(6.58*math.cos(a),6.58*math.sin(a),7.5),.075)
    round_enclosure(r,8.2);queue(r,(-10.3,-3),3.3,6,2);return r
def gear(p,at,radius=2,teeth=20,mat='gold',depth=.20):
    n=teeth*4;v=[]
    for y in [-depth/2,depth/2]:
        for outer in [True,False]:
            for i in range(n):
                a=i*TAU/n;rr=(radius if i%4 in [1,2]else radius*.88)if outer else radius*.52;v.append((at[0]+rr*math.cos(a),at[1]+y,at[2]+rr*math.sin(a)))
    f=[]
    for i in range(n):
        j=(i+1)%n;f.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    K.mesh('continuous_meshing_gear',v,f,mat,p,uv_scale=.5)
    for i in range(6):
        a=i*TAU/6;tube('gear_real_spoke',[(at[0],at[1],at[2]),(at[0]+radius*.57*math.cos(a),at[1],at[2]+radius*.57*math.sin(a))],radius*.045,mat,p)
def mask(p,at,scale=1,smile=True):
    r=root('sculpted_theatre_mask',p,at);r.scale=(scale,)*3
    outline=[(1.05*math.cos(i*TAU/48),1.4*math.sin(i*TAU/48))for i in range(48)]
    eyes=[[(cx+.26*math.cos(-i*TAU/20),.40+.14*math.sin(-i*TAU/20))for i in range(20)]for cx in [-.45,.45]]
    curve_wall('pierced_mask_face',outline,eyes,0,'ivory',r,.12)
    K.tube('sculpted_mask_nose',[(0,-.08,.28),(.12,-.4,-.1),(0,-.25,-.22)],[.14,.12,.06],'ivory',r,10)
    pts=[(x,-.12,-.60+(.55*x*x if smile else-.45*x*x))for x in [-.6+i*.06 for i in range(21)]];tube('sculpted_mask_mouth',pts,.055,'coral',r)
    for side in [-1,1]:tube('mask_raised_eyebrow',[(side*.45+x,-.13,.69+.15*(1-(x/.30)**2))for x in [-.30+i*.03 for i in range(21)]],.04,'gold',r)
    return r
def hotel(p,at,w=14,d=12):
    import dream_hotel_architecture as H
    assert w==14 and d==12,'The authored hotel has a fixed room envelope'
    return H.build(p,at)

def hedge(p,points,height=.90):
    pts=[Vector(v)for v in points];closed=(pts[0]-pts[-1]).length<1e-6
    if closed:pts=pts[:-1]
    profile=[(-.35,.08),(-.35,height-.22),(-.26,height-.05),(0,height),(.26,height-.05),(.35,height-.22),(.35,.08)];v=[]
    for i,pt in enumerate(pts):
        tangent=pts[(i+1)%len(pts)if closed else min(i+1,len(pts)-1)]-pts[(i-1)%len(pts)if closed else max(0,i-1)]
        if tangent.length<1e-7:tangent=Vector((1,0))
        tangent.normalize();normal=Vector((-tangent.y,tangent.x))
        v.extend((pt.x+normal.x*x,pt.y+normal.y*x,z)for x,z in profile)
    n=len(profile);faces=[]if closed else[tuple(reversed(range(n))),tuple(range((len(pts)-1)*n,len(pts)*n))];faces +=[(i*n+j,i*n+(j+1)%n,((i+1)%len(pts))*n+(j+1)%n,((i+1)%len(pts))*n+j)for i in range(len(pts)if closed else len(pts)-1)for j in range(n)]
    return K.mesh('grounded_clipped_planting_edge',v,faces,'clipped_hedge',p,True,uv_scale=2.4)

def covered_walk(p,points,width=4.4,mat='cobalt'):
    r=root('continuous_covered_visitor_walk',p);pts=[Vector(v)for v in points];roof=[];left=[];right=[];profile=[(-width/2,3.45),(-width*.28,4.05),(0,4.35),(width*.28,4.05),(width/2,3.45)]
    for i,pt in enumerate(pts):
        tangent=pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)];tangent.normalize();n=Vector((-tangent.y,tangent.x));roof.extend((pt.x+n.x*x,pt.y+n.y*x,z)for x,z in profile)
        for side,out in [(-1,left),(1,right)]:out.append((pt.x+n.x*side*(width/2-.15),pt.y+n.y*side*(width/2-.15)))
    o=K.mesh('continuous_fitted_arcade_roof',roof,[(i*5+j,i*5+j+1,(i+1)*5+j+1,(i+1)*5+j)for i in range(len(pts)-1)for j in range(4)],mat,r,uv_scale=.28);o.modifiers.new('fitted_arcade_roof_thickness','SOLIDIFY').thickness=.13
    for side in [left,right]:
        tube('arcade_continuous_eave',[(x,y,3.45)for x,y in side],.075,'gold',r)
        for a,b in zip(side,side[1:]):
            a,b=Vector(a),Vector(b);steps=max(1,math.ceil((b-a).length/6.5))
            for i in range(steps):
                pt=a+(b-a)*i/steps;lathe('arcade_turned_column',[(.26,0),(.26,.18),(.15,.4),(.15,3.15),(.28,3.4)],'ivory',r,12,(pt.x,pt.y,0))
        x,y=side[-1];lathe('arcade_turned_column',[(.26,0),(.26,.18),(.15,.4),(.15,3.15),(.28,3.4)],'ivory',r,12,(x,y,0))
    for i in range(len(pts)):
        tube('arcade_curved_load_truss',roof[i*5:(i+1)*5],.055,'gold',r);ball('arcade_practical_lamp',r,(pts[i].x,pts[i].y,3.95),.10)
    return r

def low_tree_parts():
    # Two shared LOD meshes replace hundreds of separately evaluated leaf parts.
    proto=K.tree(58461);out=[]
    for o in list(proto.children):
        if o.type=='MESH'and 'leaf_cluster'not in o.name:bpy.data.objects.remove(o,do_unlink=True)
    tube('lod_tapered_backdrop_trunk',[(0,0,0),(.05,0,.3),(.04,.015,1.5),(.12,.03,2.8),(.18,0,4.1),(.14,.05,5.4)],.13,'bark',proto,6)
    for i in range(8):
        a=i*2.399963;z=2.5+(i%4)*.58;start=(.12,.03,2.8)if z<3.6 else(.18,0,4.1)
        K.tube('lod_tapered_backdrop_branch',[start,(math.cos(a)*.9,math.sin(a)*.9,z+.55),(math.cos(a)*1.5,math.sin(a)*1.5,z+1.3)],[.065,.04,.012],'bark',proto,5)
    for leaf in [False,True]:
        objects=[o for o in proto.children_recursive if o.type=='MESH'and('leaf_cluster'in o.name)==leaf]
        if leaf:objects=objects[::3]
        vertices=[];faces=[];uvs=[]
        for obj in objects:
            offset=len(vertices);vertices.extend(tuple(obj.matrix_local@v.co)for v in obj.data.vertices)
            for face in obj.data.polygons:
                faces.append(tuple(offset+i for i in face.vertices));uvs.extend(tuple(obj.data.uv_layers[0].data[i].uv)for i in face.loop_indices)
        data=bpy.data.meshes.new('shared_backdrop_foliage'if leaf else'shared_backdrop_branch');data.from_pydata(vertices,[],faces);data.update();uv=data.uv_layers.new(name='UVMap')
        for d,co in zip(uv.data,uvs):d.uv=co
        data.materials.append(K.M['foliage'if leaf else'bark']);out.append(data)
    assert sum(len(p.vertices)-2 for d in out for p in d.polygons)<600,'Background tree LOD must stay bounded'
    bpy.data.batch_remove(ids=[proto,*proto.children_recursive]);return out

def return_threshold(p,at,theme):
    r=root('purpose_park_return_threshold',p,(*at,0));mat={'carnival':'coral','mirrors':'violet','clockwork':'copper','starlight':'cobalt'}[theme]
    outline=[(-6.5,0),(-5.8,0),(-5.8,3.6),(-4,5),(0,5.8),(4,5),(5.8,3.6),(5.8,0),(6.5,0),(6.5,4),(4.5,5.8),(0,6.7),(-4.5,5.8),(-6.5,4)]
    curve_wall('joined_open_return_gateway',outline,[],0,mat,r,.6)
    tube('gateway_continuous_arch_trim',[(-6.1,0,3.7),(-4.2,0,5.4),(0,0,6.2),(4.2,0,5.4),(6.1,0,3.7)],.10,'gold',r)
    if theme=='mirrors':mask(r,(0,-.38,6.25),.55,True)
    elif theme=='clockwork':gear(r,(0,-.38,6.2),.8,16)
    elif theme=='starlight':
        globe=root('gateway_ringed_orb',r,(0,-.38,6.4));ball('gateway_planet',globe,(0,0,0),.42,'mint');ring('gateway_orbit',globe,.76,0,'gold',.055)
    else:
        star=[((.75 if i%2==0 else .32)*math.sin(i*math.pi/5),6.1+(.75 if i%2==0 else .32)*math.cos(i*math.pi/5))for i in range(10)];curve_wall('circus_gateway_sculptural_star',star,[],-.38,'gold',r,.10)
    return r

def big_top(p,at):
    r=root('complete_big_top',p,(*at,0));radius=13;n=96;rings=[(.045,12.8),(3.0,11.7),(8.0,8.0),(13.1,5.2)]
    vertices=[(rr*math.cos(i*TAU/n),rr*math.sin(i*TAU/n),z+.08*math.cos(i*TAU/8))for rr,z in rings for i in range(n)]
    for stripe in range(24):
        f=[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i)for k in range(3)for i in range(stripe*4,stripe*4+4)]
        o=K.mesh('sewn_big_top_canvas',vertices,f,'coral'if stripe%2 else'ivory',r,True,uv_scale=.26);o.modifiers.new('canvas_thickness','SOLIDIFY').thickness=.025
    lathe('big_top_central_mast',[(.30,.02),(.26,1),(.18,12.9),(.06,13.5)],'gold',r,16)
    # Side canvas encloses the show, leaving one generous real entrance.
    for i in range(48):
        a=i*TAU/48;b=(i+1)*TAU/48;mid=(a+b)/2
        if math.sin(mid)<-.965:continue
        v=[(radius*math.cos(t),radius*math.sin(t),z)for z in [.08,4.7,5.2]for t in [a,b]]
        o=K.mesh('enclosing_tent_side_canvas',v,[(0,1,3,2),(2,3,5,4)],'coral'if i%4<2 else'ivory',r,True,uv_scale=.3);o.modifiers.new('side_canvas_thickness','SOLIDIFY').thickness=.025
    v=[(13.08*math.cos(i*TAU/96),13.08*math.sin(i*TAU/96),z)for z in [4.95,5.36]for i in range(96)]
    K.mesh('continuous_fitted_tent_eave_valance',v,[(i,(i+1)%96,(i+1)%96+96,i+96)for i in range(96)],'coral',r,uv_scale=.35)
    for i in range(12):
        a=i*TAU/12
        if math.sin(a)<-.94:continue
        x,y=radius*math.cos(a),radius*math.sin(a);tube('fitted_tent_perimeter_pole',[(x,y,.03),(x,y,5.3)],.08,'gold',r)
        tube('tensioned_tent_guy_rope',[(x,y,5.1),(16*math.cos(a),16*math.sin(a),.1)],.017,'linen',r,6)
    lathe('big_top_complete_boarded_floor',[(12.95,.015),(12.95,.085)],'wood',r,64)
    lathe('raised_circular_show_ring',[(4.5,.09),(4.5,.22),(4.35,.30)],'coral',r,64);ring('show_ring_fitted_coping',r,4.5,.25)
    # Sculptural star crest and tied-back entry curtains, no place-name text.
    star=[((1.05 if i%2==0 else .43)*math.sin(i*math.pi/5),5.7+(1.05 if i%2==0 else .43)*math.cos(i*math.pi/5))for i in range(10)]
    curve_wall('relief_circus_star',star,[],-13.15,'gold',r,.10)
    for side in [-1,1]:
        pts=[(side*(3.65-.85*math.sin(i*math.pi/20)),-12.9,4.9-i*4.65/20)for i in range(21)]
        K.tube('tied_back_canvas_entry_drape',pts,[.16+.19*math.sin(i*math.pi/20)for i in range(21)],'violet',r,10)
        tube('curtain_tie_rope',[(side*2.8,-13.02,2.5),(side*3.8,-13.02,2.5)],.045,'gold',r)
    bulbs(r,[(-3.4,-13.15,5.10),(0,-13.15,5.1),(3.4,-13.15,5.1)],.36)
    # Continuous curved audience banks leave a front-to-ring aisle.
    for rr in [7.3,9.1,10.8]:
        for a0,a1 in [(0.05,1.3),(1.85,3.09)]:
            v=[(rad*math.cos(a0+(a1-a0)*i/24),rad*math.sin(a0+(a1-a0)*i/24),z)for rad,z in [(rr-.3,.50),(rr+.3,.50),(rr+.3,1.03)]for i in range(25)]
            o=K.mesh('curved_show_audience_bank',v,[(i,i+1,26+i,25+i)for i in range(24)]+[(25+i,26+i,51+i,50+i)for i in range(24)],'wood',r,uv_scale=.35);o.modifiers.new('audience_timber_thickness','SOLIDIFY').thickness=.07
            for a in [a0,a1]:tube('bank_metal_support',[(rr*math.cos(a),rr*math.sin(a),.07),(rr*math.cos(a),rr*math.sin(a),.51)],.055,'steel',r)
    return r
def funhouse_facade(p,at,w=16,d=18):
    r=root('actual_mask_funhouse_front',p,(*at,0));y=-d/2-.18
    # A whole pierced, undulating gable with sculptural mask pair, a mouth-like
    # entry arch, deep window recesses and an overhanging curved canopy.
    top=[(-w/2,4.0),(-6,4.6),(-4,6.9),(-2,6.0),(0,5.5),(2,6.0),(4,6.9),(6,4.6),(w/2,4.0)]
    outline=[(-w/2,0),(-1.45,0),(-1.45,2.5),(-.9,3.5),(0,3.9),(.9,3.5),(1.45,2.5),(1.45,0),(w/2,0),*reversed(top)]
    holes=[list(reversed(arch_points(x,1.1,1.2,2.2)))for x in [-5.7,5.7]]
    curve_wall('continuous_pierced_funhouse_front',outline,holes,y,'violet',r,.22)
    for x in [-5.7,5.7]:arched_window(r,x,y+.02,1.1,1.2,2.2)
    for side in [-1,1]:
        mask(r,(side*3.75,y-.2,4.6),1.25,side<0)
        tube('funhouse_twisted_entry_column',[(side*(1.65+.18*math.sin(i*TAU/24)),y-.25,i*4.25/24)for i in range(25)],.13,'gold',r,10)
    profile_extrude('funhouse_scalloped_entry_roof',roof_band([(-2.3,3.8),(-1.7,4.2),(0,4.6),(1.7,4.2),(2.3,3.8)],.12),2.1,'coral',r,(0,y-.45,0),math.pi/2)
    funhouse_entry(r,y)
    bulbs(r,[(x,y-.24,z+.12)for x,z in top],.40);return r

def funhouse_entry(r,y=-9.18):
    # A closed recessed entrance belongs to the exterior. The separate room
    # opens through the existing E/click transition; the old open mouth exposed
    # the back of the retained facade and its incomplete roof junction.
    outline=arch_points(0,.03,2.84,3.82)
    curve_wall('recessed_closed_funhouse_arch',outline,[],y+.14,'glass',r,.06)
    tube('continuous_funhouse_door_reveal',[(x,y-.035,z)for x,z in outline],.055,'gold',r)
    tube('funhouse_door_centre_stile',[(0,y+.08,.07),(0,y+.08,3.78)],.035,'steel',r)
    tube('funhouse_door_transom',[(-1.37,y+.08,2.65),(1.37,y+.08,2.65)],.035,'steel',r)
    for side in [-1,1]:tube('funhouse_entry_pull',[(side*.16,y-.025,1.05),(side*.16,y-.09,1.10),(side*.16,y-.09,1.65),(side*.16,y-.025,1.70)],.035,'gold',r)
    r['recessedEntryRevision']=1
def coaster_station(p,at):
    r=root('complete_coaster_boarding_station',p,(*at,0));half=6.8;length=18
    # Spatial trusses, not flat beams pretending to be a roof.
    for y in [-length/2,length/2]:
        for side in [-1,1]:
            x=side*half;lathe('coaster_column_socket',[(.38,0),(.38,.20),(.23,.32)],'copper',r,16,(x,y,0));tube('load_bearing_station_column',[(x,y,.2),(x,y,4.7)],.14,'steel',r)
        points=[(-half,y,4.7),(0,y,6.35),(half,y,4.7)];tube('station_roof_top_chord',points,.11,'copper',r);tube('station_roof_bottom_chord',[(-half,y,4.65),(half,y,4.65)],.10,'steel',r)
        for i in range(10):
            x=-half+2*half*i/10;xn=-half+2*half*(i+1)/10;topx=x if i%2 else xn;z=6.35-1.65*abs(topx)/half;tube('triangulated_station_web',[(x,y,4.65),(topx,y,z)],.055,'steel',r)
    for side in [-1,1]:tube('station_eave_load_member',[(side*half,-length/2,4.7),(side*half,length/2,4.7)],.11,'copper',r)
    tube('station_continuous_ridge_purlin',[(0,-length/2,6.4),(0,length/2,6.4)],.10,'copper',r)
    profile_extrude('station_fitted_roof_skin',roof_band([(-half-.35,4.7),(0,6.5),(half+.35,4.7)],.10),length+.8,'mint',r,yaw=math.pi/2)
    queue(r,(-13,-1),4.0,12,3);fence(r,[(10.6,-8),(10.6,8)],'copper')
    for y in [-7,-2,3]:
        for side in [-1,1]:ball('station_canopy_light',r,(side*5.8,y,4.55),.10)
    return r
def mechanical_tower(p,at):
    r=root('open_mechanical_gear_tower',p,(*at,0))
    for side in [-1,1]:
        outline=[(-2.2,0),(-1.4,0),(-1.25,10.8),(0,14.1),(1.25,10.8),(1.4,0),(2.2,0),(2.2,11.4),(0,15.8),(-2.2,11.4)]
        curve_wall('pierced_tower_side_housing',outline,[],side*.85,'copper',r,.18)
    for x in [-1.75,1.75]:tube('tower_lateral_brace',[(x,-.85,.4),(x,.85,.4)],.15,'steel',r)
    for z in [1,4,7,10]:
        for y in [-.85,.85]:tube('exposed_engine_frame_brace',[(-1.75,y,z),(1.75,y,z+2)],.065,'steel',r)
    for x,z,rr in [(-.9,11,2.1),(1.65,8.25,1.7),(-.65,5.8,1.8)]:gear(r,(x,-1.05,z),rr,20,'gold')
    for x,y in [(-2.5,0),(2.5,0)]:lathe('turned_engine_foundation',[(.65,0),(.65,.30),(.48,.60),(.35,1.3)],'stone',r,24,(x,y,0))
    return r
def retro_theatre(p,at):
    r=root('complete_retro_space_theatre',p,(*at,0));radius=10.0;n=64;bands=14;v=[]
    for k in range(bands+1):
        t=k*(math.pi/2-.005)/bands
        v +=[(radius*math.cos(t)*math.cos(i*TAU/n),radius*math.cos(t)*math.sin(i*TAU/n),3.1+8.2*math.sin(t))for i in range(n)]
    K.mesh('joined_planetarium_segmented_dome',v,[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i)for k in range(bands)for i in range(n)],'mint',r,True,uv_scale=.3)
    for i in range(12):
        a=i*TAU/12;tube('actual_meridian_roof_rib',[(10.04*math.cos(t)*math.cos(a),10.04*math.cos(t)*math.sin(a),3.1+8.2*math.sin(t))for t in [k*math.pi/28 for k in range(15)]],.055,'gold',r)
    # Radial masonry panels and recessed circular windows; front is an actual door.
    for i in range(32):
        a=i*TAU/32;b=(i+1)*TAU/32;mid=(a+b)/2
        if math.sin(mid)<-.96:continue
        verts=[(10*math.cos(t),10*math.sin(t),z)for z in [0,3.1]for t in [a,b]];K.mesh('radial_theatre_enclosing_wall',verts,[(0,1,3,2)],'ivory',r,uv_scale=.4)
        if i%2==0:
            window=root('recessed_porthole',r,(10.03*math.cos(mid),10.03*math.sin(mid),1.7),mid-math.pi/2);lathe('porthole_curved_glazing',[(.59,-.04),(.59,.04)],'glass',window,24).rotation_euler.x=math.pi/2
            tube('porthole_metal_reveal',[(.65*math.cos(j*TAU/32),-.07,.65*math.sin(j*TAU/32))for j in range(33)],.055,'gold',window)
    for side in [-1,1]:
        K.rounded_solid('theatre_glazed_entry_leaf',2.12,.08,2.8,'glass',r,.04,(side*1.1,-9.8,1.45));tube('theatre_entry_pull',[(side*.2,-9.94,1.0),(side*.2,-9.94,1.65)],.035,'gold',r)
    # Cantilevered fan canopy is an integrated shell, with four fitted ribs.
    pts=[(-4.3,-10.8,2.9),(-2.8,-14.2,3.15),(0,-15.4,3.4),(2.8,-14.2,3.15),(4.3,-10.8,2.9)]
    verts=[(0,-9.7,4.9),*pts];o=K.mesh('continuous_fan_entry_shell',verts,[(0,i+1,i+2)for i in range(4)],'cobalt',r,True,uv_scale=.4);o.modifiers.new('entry_shell_real_thickness','SOLIDIFY').thickness=.16
    for end in pts:tube('shell_structural_rib',[(0,-9.7,4.94),end],.06,'gold',r)
    tube('theatre_entry_load_arch',[(-3.6,-9.65,3.0),(-1.8,-9.65,4.3),(0,-9.65,4.9),(1.8,-9.65,4.3),(3.6,-9.65,3.0)],.14,'steel',r)
    for side in [-1,1]:lathe('theatre_grounded_canopy_column',[(.28,0),(.28,.16),(.16,.4),(.16,2.8),(.26,2.95)],'ivory',r,16,(side*4.3,-10.8,0))
    bulbs(r,pts,.50);return r

def orbit_ride(p,at):
    r=root('complete_orbital_vehicle_attraction',p,(*at,0))
    lathe('orbiter_boarding_deck',[(9,0),(9,.18),(8.8,.30)],'steel',r,64)
    lathe('orbiter_central_housing',[(1.9,.3),(2.1,.6),(1.6,1.3),(1.2,4.5),(.8,5.1)],'cobalt',r,32)
    globe=root('suspended_ringed_planet',r,(0,0,5.8));ball('planet_sphere',globe,(0,0,0),1.35,'mint');tilt=root('tilted_planet_ring',globe);tilt.rotation_euler.x=.35;ring('planet_continuous_orbit',tilt,2.0,0,'gold',.10)
    for i in range(8):
        a=i*TAU/8;x,y=6.4*math.cos(a),6.4*math.sin(a)
        tube('orbiter_structural_radial_arm',[(1.4*math.cos(a),1.4*math.sin(a),1.8),(x,y,.95)],.14,'gold',r,10)
        vehicle=root('recognizable_rocket_vehicle',r,(x,y,1.05),a+math.pi/2)
        # Open passenger well with a curved nose, rear fins and restraints.
        K.tube('rocket_continuous_tapered_fuselage',[(0,-1.9,0),(0,-1.4,.1),(0,-.65,.13),(0,.7,.12),(0,1.35,.07)],[.035,.40,.58,.55,.32],'ivory',vehicle,16)
        for side in [-1,1]:
            K.mesh('rocket_swept_tail_fin',[(side*.4,.65,.1),(side*1.0,1.5,-.18),(side*.3,1.35,.65)],[(0,1,2)],'coral',vehicle,uv_scale=.8)
            tube('rocket_passenger_safety_bar',[(side*.37,-.5,.55),(side*.37,.3,.75),(side*.37,.55,.40)],.035,'steel',vehicle)
        profile_extrude('rocket_bucket_seat',[(-.4,.33),(.4,.33),(.4,1.0),(.30,1.0),(.27,.48),(-.4,.48)],.72,'cobalt',vehicle,(0,.1,0))
        ball('rocket_position_lamp',vehicle,(0,-1.5,.35),.075)
    round_enclosure(r,9.7);queue(r,(-11.8,-3),3.5,7,2);return r

def planter(p,at,r=1.3):
    q=root('integrated_promenade_planter',p,(*at,0))
    lathe('planter_fitted_stone_bowl',[(r*.8,0),(r*.8,.15),(r,.7),(r,.81),(r-.12,.81),(r-.15,.65)],'stone',q,24)
    lathe('planter_soil',[(r-.18,.66),(r-.18,.69)],'wood',q,24)
    # Broad planted tufts and restrained flower clusters, separate from trees.
    for i in range(11):
        a=i*2.39996;rr=r*.63*math.sqrt(i/11);x,y=rr*math.cos(a),rr*math.sin(a)
        tube('planted_flower_stem',[(x,y,.68),(x+.06,y,.98+(i%3)*.08)],.024,'mint',q,6)
        ball('promenade_flower_cluster',q,(x+.06,y,1.0+(i%3)*.08),.12,'coral'if i%2 else'ivory')
    return q

def tree_seating_bed(p,at):
    q=root('visitor_grove_seating_bed',p,(*at,0))
    lathe('rounded_tree_bed_coping',[(1.52,.02),(1.58,.12),(1.58,.42),(1.44,.46),(1.32,.44),(1.32,.20)],'stone',q,32)
    lathe('inset_tree_bed_soil',[(1.31,.18),(1.31,.22)],'planting_soil',q,24)
    # Real segmented curved seats and structural legs surround the planting.
    # Four breaks keep the object readable as seating instead of a solid drum.
    for sector in range(4):
        start=sector*TAU/4+.16;end=(sector+1)*TAU/4-.16;n=9
        vertices=[(rr*math.cos(start+(end-start)*i/n),rr*math.sin(start+(end-start)*i/n),z)for z in [.43,.51]for rr in [1.65,2.08]for i in range(n+1)]
        stride=n+1;faces=[]
        for i in range(n):faces.extend([(i,i+1,stride+i+1,stride+i),(2*stride+i,3*stride+i,3*stride+i+1,2*stride+i+1),(i,2*stride+i,2*stride+i+1,i+1),(stride+i,stride+i+1,3*stride+i+1,3*stride+i)])
        faces.extend([(0,stride,3*stride,2*stride),(n,2*stride+n,3*stride+n,stride+n)])
        K.mesh('formed_curved_public_seat',vertices,faces,'wood',q,uv_scale=.7)
        for a in [start+.1,end-.1]:tube('seating_grounded_steel_leg',[(1.86*math.cos(a),1.86*math.sin(a),.03),(1.86*math.cos(a),1.86*math.sin(a),.44)],.055,'steel',q,6)
    return q
