"""Purpose-built park architecture. Blender meshes, not relabelled house prefabs.

Front door centres and the authored level footprints are stable. Profiled wall
shells have real apertures; roofs follow each building's own structural section.
Text, logo and colour are supplementary and can all be hidden for shape review.
"""
import bpy,math
from mathutils import Vector
import v4_rebuilt_environment_kit as K
import v4_facility_architecture as F

PLANS=F.PLANS
def palette():
    for name,base,tint,metal in [
        ('clinical','plaster',(.86,.94,.91,1),0),('sandstone','stone',(.77,.68,.52,1),0),
        ('terracotta','plaster',(.55,.26,.15,1),0),('ivory','plaster',(.90,.85,.70,1),0),
        ('utility','plaster',(.43,.49,.48,1),0),('slate','roof',(.18,.28,.32,1),.10),
        ('copper','roof',(.38,.47,.39,1),.25),('painted_steel','iron',(.42,.49,.53,1),.28),
        ('cream_trim','stone',(.94,.91,.79,1),0)]:
        m=K.M[base].copy();m.name='form_'+name;m['surfaceTint']=tint
        bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=metal
        mix=next((n for n in m.node_tree.nodes if n.type=='MIX_RGB'),None)
        if mix:mix.inputs[2].default_value=tint
        else:
            source=bs.inputs['Base Color'].links[0].from_socket;mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=tint;m.node_tree.links.new(source,mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color'])
        m['purposeSurface']=name;K.M[name]=m
    m=K.M['glass'].copy();m.name='form_display_glass';bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.45,.67,.71,1);bs.inputs['Alpha'].default_value=.20;bs.inputs['Metallic'].default_value=0;K.M['display_glass']=m

def profile(ident,w,h):
    a=w/2
    if ident=='hotel_lobby':return [(-a,h-.6),(-a+.7,h+.7),(-a+1.7,h+1.05),(-1.7,h+1.05),(0,h+2),(1.7,h+1.05),(a-1.7,h+1.05),(a-.7,h+.7),(a,h-.6)]
    if ident=='clinic':return [(-a,h-.4),(-a+.25,h-.1),(-w*.18,h-.1),(-w*.12,h+.22),(w*.20,h+.22),(w*.28,h-.25),(a,h-.25)]
    if ident in ['kitchen','laundry_room','mirror_workbay']:
        n={'kitchen':3,'laundry_room':2,'mirror_workbay':2}[ident];p=[]
        for i in range(n):x=-a+i*w/n;p.extend([(x,h),(x+w/n*.70,h+.85),(x+w/n,h+.85),(x+w/n,h)])
        return p
    if ident=='dining_room':return [(-a,h-.22),(-w*.27,h+.18),(0,h+2.1),(w*.27,h+.18),(a,h-.22)]
    if ident=='reading_room':return [(-a,h),(-w*.30,h+.78),(-w*.20,h),(-w*.14,h),(0,h+2.0),(w*.14,h),(w*.20,h),(w*.30,h+.78),(a,h)]
    if ident=='management_office':return [(-a,h),(-w*.16,h),(-w*.16,h+1.9),(w*.13,h+1.9),(w*.13,h+.20),(a,h+.20)]
    if ident=='electrical_room':return [(-a,h-.28),(-w*.22,h-.28),(-w*.22,h+1.08),(w*.24,h+1.08),(w*.24,h-.28),(a,h-.28)]
    if ident=='supply_store':return [(-a,h),(0,h+2.0),(a,h)]
    if ident=='cold_store':return [(-a,h),(-a+.35,h+.20),(a-.35,h+.20),(a,h)]
    if ident=='refreshment_store':return [(-a,h-.15),(-w*.22,h+.2),(w*.20,h+1.10),(a,h+.4)]
    if ident=='service_lounge':return [(-a,h-.35),(0,h+1.15),(a,h-.35)]
    if ident=='theatre_preparation':return [(-a,h-.1),(-a,h+.18),(w*.1,h+.8),(a,h+.8),(a,h-.1)]
    if ident=='dream_lobby':return [(-a,h),(-a+.4,h+.35),(-w*.26,h+.35),(-w*.26,h+1.1),(-w*.13,h+1.1),(-w*.13,h+1.8),(w*.13,h+1.8),(w*.13,h+1.1),(w*.26,h+1.1),(w*.26,h+.35),(a-.4,h+.35),(a,h)]
    if ident=='mirror_maze':return [(-a+i*w/8,h+(.95 if i%2 else .05))for i in range(9)]
    if ident=='central_control':return [(-a,h-.3),(-w*.23,h-.3),(-w*.23,h+2.65),(w*.23,h+2.65),(w*.23,h-.3),(a,h-.3)]
    if ident=='maintenance_workshop':return [(-a,h),(-w*.18,h+1.65),(w*.06,h+.45),(w*.30,h+1.20),(a,h+.35)]
    if ident=='inspection_hall_normal':return [(-a,h),(0,h+2.1),(a,h)]
    if ident=='archive_room':return [(-a,h+.10),(-w*.32,h+.10),(-w*.32,h+.7),(w*.32,h+.7),(w*.32,h+.10),(a,h+.10)]
    if ident=='record_room':return [(-a*math.cos(i*math.pi/24),.38+(h+1.55)*math.sin(i*math.pi/24))for i in range(25)]
    if ident=='ticket_booth':return [(-a,h-.25),(-a+.4,h+.25),(a-.4,h+.25),(a,h-.25)]
    if ident=='staff_passage':return [(-a,h-.3),(0,h+.25),(a,h-.3)]
    rise={'hotel_multiuse':1.65,'performance_stage':2.35,'screening_room':2.05,'exhibition_room':1.20,'mirror_waiting':1.10}[ident]
    return [(-a*math.cos(i*math.pi/20),h+rise*math.sin(i*math.pi/20))for i in range(21)]

def curve_wall(name,outline,holes,y,mat,parent,depth=.18):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='2D';c.fill_mode='BOTH';c.extrude=depth/2;c.resolution_u=1
    for pts in [outline,*holes]:
        s=c.splines.new('POLY');s.points.add(len(pts)-1)
        for p,(x,z)in zip(s.points,pts):p.co=(x,z,0,1)
        s.use_cyclic_u=True
    o=bpy.data.objects.new(name,c);bpy.context.scene.collection.objects.link(o);bpy.context.view_layer.update();data=bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()));bpy.data.objects.remove(o,do_unlink=True)
    for v in data.vertices:x,z,d=v.co;v.co=(x,y+d,z)
    o=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(o);o.parent=parent;data.materials.append(K.M[mat]);return o

def opening(x,width,bottom,top):return [(x-width/2,bottom),(x-width/2,top),(x+width/2,top),(x+width/2,bottom)]

def roof_band(p,thickness=.16):
    # Offset along the section normal, including vertical sawtooth risers.
    # A vertical-only offset self-overlaps at these risers.
    pp=[]
    for v in p:
        if not pp or math.dist(v,pp[-1])>1e-7:pp.append(v)
    normals=[]
    for a,b in zip(pp,pp[1:]):
        dx,dz=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dz);normals.append(Vector((dz/length,-dx/length)))
    inner=[]
    for i,(x,z)in enumerate(pp):
        if i==0:n=normals[0]
        elif i==len(pp)-1:n=normals[-1]
        else:n=(normals[i-1]+normals[i])/max(.25,1+normals[i-1].dot(normals[i]))
        if n.length>2.5:n=n.normalized()*2.5
        inner.append((x+n.x*thickness,z+n.y*thickness))
    return pp+list(reversed(inner))

def shell(ident,w,d,h,p,parent,wall,windows,open_front=False):
    doorwidth={'supply_store':3.6,'inspection_hall_normal':3.8,'maintenance_workshop':3.2,'cold_store':2.5,'theatre_preparation':2.4}.get(ident,1.56);doorheight=3.1 if ident in ['supply_store','inspection_hall_normal','maintenance_workshop','cold_store']else 2.62
    windows=[(x,min(ww,max(.1,2*(abs(x)-doorwidth/2-.15)))if b<doorheight else ww,b,t)for x,ww,b,t in windows]
    windows=[v for v in windows if v[1]>.25]
    outer=[(-w/2,0),(-doorwidth/2,0),(-doorwidth/2,doorheight),(doorwidth/2,doorheight),(doorwidth/2,0),(w/2,0),*reversed(p)]
    if not open_front:curve_wall('profiled_front_with_real_openings',outer,[opening(*win)for win in windows],-d/2,wall,parent)
    curve_wall('profiled_rear_structural_wall',[(-w/2,0),(w/2,0),*reversed(p)],[],d/2,wall,parent)
    for side in [-1,1]:
        z=p[0 if side<0 else -1][1]
        side_windows=[]if d<3.5 or z<1.3 else [(y,min(d*.26,2.5),.85,min(z-.30,2.55))for y in [-d*.25,d*.25]]
        if ident in ['archive_room','cold_store','inspection_hall_normal','maintenance_workshop','supply_store','theatre_preparation']and z>2.9:side_windows=[(y,min(d*.34,3),2.05,min(z-.25,2.82))for y in [-d*.25,d*.25]]
        if ident=='hotel_lobby'and z>5.9:side_windows +=[(y,min(d*.22,1.5),4.10,5.50)for y in [-d*.25,d*.25]]
        sidewall=curve_wall('pierced_load_bearing_side_wall',[(-d/2,0),(d/2,0),(d/2,z),(-d/2,z)],[opening(*a)for a in side_windows],0,wall,parent)
        for v in sidewall.data.vertices:xx,yy,zz=v.co;v.co=(side*(w/2-.09)+yy,xx,zz)
        for yy,ww,b,t in side_windows:
            frame=K.frame_ring('side_glazing_reveal',ww+.13,t-b+.13,.065,.22,'cream_trim',parent,(side*(w/2+.025),yy,(b+t)/2));frame.rotation_euler.z=math.pi/2
            K.mesh('recessed_side_glazing',[(side*(w/2-.06),yy+dx,zz)for dx,zz in [(-ww/2,b),(ww/2,b),(ww/2,t),(-ww/2,t)]],[(0,1,2,3)],'display_glass',parent).data.materials[0].use_backface_culling=False
    roof=F.prism('continuous_purpose_roof',roof_band(p),d+.46,'painted_steel'if ident in ['record_room','cold_store']else'slate'if ident in ['kitchen','electrical_room','supply_store','maintenance_workshop','inspection_hall_normal']else'copper'if ident in ['clinic','exhibition_room','mirror_waiting']else'roof',parent)
    K.rounded_solid('connected_building_floor',w-.1,d-.1,.12,'paving',parent,.01,(0,0,-.055))
    # Coping is a continuous roof edge sweep, not a row of fake block ornaments.
    for y in [-d/2-.24,d/2+.24]:K.tube('formed_roof_edge',[(x,y,z+.015)for x,z in p],[.035]*len(p),'painted_steel',parent,6)
    if not open_front:K.frame_ring('real_entrance_reveal',doorwidth+.26,doorheight+.22,.10,.28,'cream_trim',parent,(0,-d/2-.025,doorheight/2),inner_size=(doorwidth,doorheight))
    for x,ww,b,t in windows:
        K.frame_ring('recessed_window_reveal',ww+.13,t-b+.13,.065,.22,'cream_trim',parent,(x,-d/2-.02,(b+t)/2))
        pane=K.mesh('recessed_display_glazing',[(x-ww/2,-d/2+.07,b),(x+ww/2,-d/2+.07,b),(x+ww/2,-d/2+.07,t),(x-ww/2,-d/2+.07,t)],[(0,1,2,3)],'display_glass',parent);pane.data.materials[0].use_backface_culling=False
        for xx in [x-ww/6,x+ww/6]:K.tube('window_structural_mullion',[(xx,-d/2-.025,b),(xx,-d/2-.025,t)],[.018]*2,'wood',parent,5)
    parent['roofWallSealed']=True;parent['roofStyle']='purpose_profile_'+ident;parent['roofProfileXZ']=[list(a)for a in p]
    return roof

def spatial_shell(ident,w,d,h,parent,wall,windows,open_front):
    """Joined functional wings are actual enclosed rooms, not facade ornaments."""
    if ident not in ['hotel_lobby','clinic','dining_room','electrical_room','central_control','reading_room','screening_room','dream_lobby','hotel_multiuse','exhibition_room','archive_room','management_office']:
        return shell(ident,w,d,h,profile(ident,w,h),parent,wall,windows,open_front)
    if ident=='hotel_lobby':bays=[(0,w*.42,d*.65,h,0,'mansard'),(-w*.355,w*.29,d,h-.25,0,'bedroom'),(w*.355,w*.29,d,h-.25,0,'bedroom')]
    elif ident=='clinic':bays=[(0,w*.30,d*.65,h+.20,0,'clinic_entry'),(-w*.325,w*.35,d*.70,h-.25,.10,'treatment'),(w*.325,w*.35,d*.96,h-.25,.45,'treatment')]
    elif ident=='dining_room':bays=[(0,w*.50,d,h,0,'dining_hall'),(-w*.375,w*.25,d*.78,h-.45,.9,'glazed_dining'),(w*.375,w*.25,d*.78,h-.45,.9,'glazed_dining')]
    elif ident=='electrical_room':bays=[(0,w*.44,d,h+.15,0,'switchgear')]
    elif ident=='central_control':bays=[(0,w*.40,d*.70,h+2.25,0,'control_gallery'),(-w*.35,w*.30,d*.60,h-.25,.6,'work_room'),(w*.35,w*.30,d*.60,h-.25,.6,'work_room')]
    elif ident=='reading_room':bays=[(0,w*.46,d,h+.4,0,'reading_hall'),(-w*.365,w*.27,d*.70,h-.5,.6,'reading_bay'),(w*.365,w*.27,d*.70,h-.5,.6,'reading_bay')]
    elif ident=='screening_room':bays=[(0,w*.74,d*.25,3.25,0,'cinema_foyer'),(0,w,d*.72,h,d*.28,'auditorium')]
    elif ident=='dream_lobby':bays=[(0,w*.66,d*.70,h,0,'ticket_foyer'),(-w*.415,w*.17,d*.48,h+.85,.1,'box_office'),(w*.415,w*.17,d*.48,h+.85,.1,'box_office')]
    elif ident=='hotel_multiuse':bays=[(0,w*.66,d*.9,h+.2,0,'meeting_hall'),(-w*.415,w*.17,d*.6,h-.35,.65,'veranda'),(w*.415,w*.17,d*.6,h-.35,.65,'veranda')]
    elif ident=='exhibition_room':bays=[(0,w*.50,d*.8,h+.9,0,'exhibition_atrium'),(-w*.375,w*.25,d*.72,h-.25,.9,'gallery_wing'),(w*.375,w*.25,d*.72,h-.25,.9,'gallery_wing')]
    elif ident=='archive_room':bays=[(0,w*.65,d*.70,h+.3,0,'archive_stack'),(w*.35,w*.30,d,h+.2,0,'archive_stack')]
    else:bays=[(0,w*.62,d*.70,h,0,'public_office'),(w*.35,w*.30,d,h+.15,.2,'office_files')]
    roofs=[]
    for index,(x,bw,bd,bh,setback,kind)in enumerate(bays):
        bay=K.root('connected_functional_wing_'+kind,parent);bay.location=(x,-d/2+setback+bd/2,0)
        if kind in ['treatment','clinic_entry','work_room','control_gallery','switchgear','public_office','office_files','archive_stack','ticket_foyer','box_office','cinema_foyer']:p=[(-bw/2,bh),(-bw*.35,bh+.13),(bw*.35,bh+.13),(bw/2,bh)]
        elif kind in ['auditorium','exhibition_atrium','gallery_wing','meeting_hall']:p=[(-bw/2*math.cos(i*math.pi/16),bh+(1.65 if kind=='auditorium'else.9)*math.sin(i*math.pi/16))for i in range(17)]
        elif kind=='glazed_dining':p=[(-bw/2,bh+.25),(bw/2,bh)]if index==1 else[(-bw/2,bh),(bw/2,bh+.25)]
        else:p=[(-bw/2,bh),(0,bh+(1.5 if kind=='dining_hall'else .85)),(bw/2,bh)]
        if index==0:
            ww=max(.35,min(bw*.58-1.84,bw*.24));wins=[(-bw*.29,ww,.75,min(bh-.3,2.65)),(bw*.29,ww,.75,min(bh-.3,2.65))]if bw>4.3 else[]
        else:wins=[(0,bw*.72,.78,min(bh-.22,2.6))]
        if kind=='archive_stack':wins=[(x,bw*.21,2.12,bh-.18)for x in [-bw*.30,bw*.30]]
        if kind in ['exhibition_atrium','meeting_hall']:wins=[(-bw*.30,bw*.24,.35,bh-.20),(bw*.30,bw*.24,.35,bh-.20)]
        if ident=='hotel_lobby':wins +=[(xx,1.1,4.12,5.60)for xx in ([-bw*.25,bw*.25]if bw>5 else[0])]
        if kind=='control_gallery':wins.append((0,bw*.70,3.60,bh-.25))
        if kind=='veranda':
            roof=F.prism('continuous_purpose_roof',roof_band(p),bd+.3,'roof',bay)
            for xx in [-bw*.4,bw*.4]:
                for yy in [-bd*.42,bd*.42]:column(bay,xx,yy,bh,'wood',.065)
            K.rounded_solid('continuous_veranda_floor',bw,bd,.1,'paving',bay,.01,(0,0,-.04));roofs.append(roof);continue
        roof=shell(ident,bw,bd,bh,p,bay,wall,wins,False);roofs.append(roof)
        # Side wings do not sprout another public entrance behind their glass.
        if index:
            front=next(o for o in bay.children if o.name.startswith('profiled_front_with_real_openings'))
            bpy.data.objects.remove(front,do_unlink=True)
            curve_wall('continuous_wing_front_with_glazing',[(-bw/2,0),(bw/2,0),*reversed(p)],[opening(*a)for a in wins],-bd/2,wall,bay)
            for o in list(bay.children):
                if o.name.startswith('real_entrance_reveal'):bpy.data.objects.remove(o,do_unlink=True)
    if ident=='electrical_room':
        for side in [-1,1]:
            x=side*w*.35
            K.rounded_solid('transformer_service_yard',w*.28,d,.12,'paving',parent,.01,(x,0,-.03))
            for y in [-d/2,d/2]:column(parent,x,y,2.4,'painted_steel',.055)
            K.tube('overhead_substation_bus',[(x,-d/2,2.4),(x,d/2,2.4)],[.05]*2,'painted_steel',parent,6)
    parent['roofWallSealed']=True;parent['roofStyle']='joined_functional_wings';parent['roofProfileXZ']=[list(v)for v in profile(ident,w,h)]
    parent['functionalRoomWings']=len(bays);parent['footprintIsSharedHouseRectangle']=False
    return roofs[0]

def column(parent,x,y,z,mat='cream_trim',radius=.09):return K.tube('load_bearing_portico_column',[(x,y,0),(x,y,z)],[radius,radius*.84],mat,parent,10)

def curved_canopy(parent,width,y,z=2.8,depth=1.6,mat='copper'):
    p=[(-width/2+i*width/20,z+.24*math.sin(i*math.pi/20))for i in range(21)];F.prism('swept_structural_entrance_canopy',p+[(x,zz-.11)for x,zz in reversed(p)],depth,mat,parent,y-depth/2)
    for x in [-width/2+.15,width/2-.15]:column(parent,x,y-depth+.12,z)

def window_scene(ident,parent,w,d):
    """Recognizable actual furniture/equipment in a recessed glazed volume."""
    y=-d/2+{'dining_room':1.85,'reading_room':1.65,'clinic':1.22}.get(ident,.62)
    for side in [-1,1]:
        x=side*w*{'dining_room':.375,'reading_room':.365,'clinic':.325}.get(ident,.29)
        if ident in ['dining_room','service_lounge','hotel_multiuse','mirror_waiting']:
            table=K.curved_family('meeting_table');table.parent=parent;table.location=(x,y+.13,0);table.scale=(.42,.42,.78)
            for j in [-1,1]:o=K.curved_family('chair');o.parent=parent;o.location=(x+j*.64,y+.13,0);o.rotation_euler.z=-j*math.pi/2
        elif ident in ['reading_room','archive_room','record_room']:
            o=K.shelf();o.parent=parent;o.location=(x,y+.45,0);o.scale=(.85,.65,1.1)
        elif ident=='clinic':
            o=K.bed();o.parent=parent;o.location=(x,y+.48,0);o.scale=(.65,.65,.8)
            o=K.iv_stand();o.parent=parent;o.location=(x+.58,y+.18,0)
        elif ident=='kitchen':
            for f in [K.cooking_range,K.hood]:o=f();o.parent=parent;o.location=(x,y,.1 if f==K.cooking_range else 2.05);o.scale=(.7,.7,.7)
        elif ident=='laundry_room':
            o=K.wash_machine();o.parent=parent;o.location=(x,y+.06,0)
        elif ident in ['supply_store','refreshment_store','cold_store']:
            o=K.shelf();o.parent=parent;o.location=(x,y+.6,0);o.scale=(.8,.7,1)
        elif ident in ['management_office','central_control','electrical_room']:
            o=K.office_desk();o.parent=parent;o.location=(x,y+.4,0);o.scale=(.65,.65,1)

def radial_waiting_pavilion(parent,w,d,h):
    n=40;fractions=[.08,.25,.45,.65,.82,1];verts=[]
    for offset in [0,-.13]:
        for t in fractions:
            for i in range(n):
                a=i*math.tau/n;verts.append((w*.52*t*math.cos(a),d*.52*t*math.sin(a),h-.18+1.12*math.sqrt(max(0,1-t*t))+offset))
    count=n*len(fractions);faces=[tuple(range(n)),tuple(reversed(range(count,count+n)))]
    for layer in range(2):
        for j in range(len(fractions)-1):
            for i in range(n):
                a=layer*count+j*n+i;b=layer*count+j*n+(i+1)%n;faces.append((a,b,b+n,a+n)if layer==0 else(a,a+n,b+n,b))
    for i in range(n):a=count-n+i;b=count-n+(i+1)%n;faces.append((a,a+count,b+count,b))
    K.mesh('continuous_radial_pavilion_roof',verts,faces,'copper',parent,True)
    floor=[(w*.48*math.cos(i*math.tau/n),d*.48*math.sin(i*math.tau/n),-.01)for i in range(n)];K.mesh('oval_waiting_pavilion_floor',floor,[tuple(range(n))],'paving',parent)
    for i in range(10):
        a=i*math.tau/10;x=w*.43*math.cos(a);y=d*.43*math.sin(a)
        if abs(x)<1.2 and y<0:continue
        column(parent,x,y,h-.18,'wood',.085)
    for i in [0,1,2,3,4]:
        a=i*math.pi/4;bench=K.curved_family('park_bench');bench.parent=parent;bench.location=(w*.32*math.cos(a),d*.32*math.sin(a),0);bench.rotation_euler.z=a-math.pi/2
    parent['roofWallSealed']=True;parent['roofStyle']='radial_open_waiting_pavilion';parent['roofProfileXZ']=[]

def octagonal_ticket_pavilion(parent,w,d,h):
    a,b=w/2,d/2;c=.65;outline=[(-a+c,-b),(a-c,-b),(a,-b+c),(a,b-c),(a-c,b),(-a+c,b),(-a,b-c),(-a,-b+c)]
    for i,(p,q)in enumerate(zip(outline,outline[1:]+outline[:1])):
        tx,ty=q[0]-p[0],q[1]-p[1];length=math.hypot(tx,ty);tx/=length;ty/=length;nx,ny=-ty,tx;mx,my=(p[0]+q[0])/2,(p[1]+q[1])/2
        door=i==0;outer=[(-length/2,0),*([(-.78,0),(-.78,2.62),(.78,2.62),(.78,0)]if door else[]),(length/2,0),(length/2,h),(-length/2,h)]
        wins=[(-1.4,.65,.95,2.35),(1.4,.65,.95,2.35)]if i==0 else[(0,3.65,1.2,2.7)]if i==4 else[(0,2.7,.95,2.35)]if i in [2,6]else[]
        obj=curve_wall('octagonal_kiosk_wall_with_real_apertures',outer,[opening(*x)for x in wins],0,'ivory',parent)
        for v in obj.data.vertices:x,y,z=v.co;v.co=(mx+tx*x+nx*y,my+ty*x+ny*y,z)
        for x,ww,bot,top in wins:
            cx,cy=mx+tx*x,my+ty*x;fr=K.frame_ring('ticket_service_window_reveal',ww+.10,top-bot+.10,.05,.16,'wood',parent,(cx-nx*.025,cy-ny*.025,(bot+top)/2));fr.rotation_euler.z=math.atan2(ty,tx)
            K.mesh('ticket_service_glazing',[(cx+tx*dx+nx*.06,cy+ty*dx+ny*.06,z)for dx,z in [(-ww/2,bot),(ww/2,bot),(ww/2,top),(-ww/2,top)]],[(0,1,2,3)],'display_glass',parent).data.materials[0].use_backface_culling=False
            tray=K.rounded_solid('public_ticket_sill',ww+.1,.5,.08,'wood',parent,.025,(cx-nx*.18,cy-ny*.18,bot));tray.rotation_euler.z=math.atan2(ty,tx)
    verts=[(x*t,y*t,z)for t,z in [(1.06,h+.02),(.70,h+.42),(.70,h+.28),(1.06,h-.12)]for x,y in outline]
    faces=[tuple(range(8,16)),tuple(reversed(range(16,24)))]+[(ring*8+i,ring*8+(i+1)%8,((ring+1)%4)*8+(i+1)%8,((ring+1)%4)*8+i)for ring in [0,2,3]for i in range(8)]
    K.mesh('formed_octagonal_ticket_roof',verts,faces,'roof',parent)
    K.mesh('octagonal_kiosk_floor',[(x,y,-.01)for x,y in outline],[tuple(range(8))],'paving',parent)
    parent['roofWallSealed']=True;parent['roofStyle']='octagonal_service_kiosk';parent['roofProfileXZ']=[]

def build(ident,w,d,h,I):
    role,_=PLANS[ident];r=K.root('purpose_built_'+ident);r['facilityIdentity']=ident;r['architectureFamily']=role;r['architectureVersion']=3;r['nominalSize']=[w,d,h]
    if ident in ['loading_gate','outside_threshold']:
        import v4_rebuilt_landmarks as L
        o=L.build(ident,K);o.parent=r
        if ident=='loading_gate':
            for side in [-1,1]:
                for j in range(7):K.tube('folded_gate_reinforcing_rib',[(side*(.15+j*.28),3.88,.13),(side*(.15+j*.28),3.88,3.22)],[.025]*2,'painted_steel',r,5)
                K.tube('gate_leaf_diagonal_brace',[(side*.12,3.86,.20),(side*1.9,3.86,3.12)],[.045]*2,'painted_steel',r,6)
            F.prism('service_gate_overhead_truss',[(-2.65,4.35),(-2.65,4.65),(2.65,4.65),(2.65,4.35)],.6,'painted_steel',r,4)
        r['roofWallSealed']=True;r['roofStyle']='open_structure';r['purposeFeatures']=['actual_service_gate_structure'if ident=='loading_gate'else'continuing_outside_road'];return r
    if ident in ['mirror_waiting','ticket_booth']:
        (radial_waiting_pavilion if ident=='mirror_waiting'else octagonal_ticket_pavilion)(r,w,d,h)
        I.plate(ident,r,(0,-d/2-.1,h-.55),width=min(2.6,w*.55));r['purposeFeatures']=['radial_canopy_and_open_seating'if ident=='mirror_waiting'else'octagonal_counter_pavilion_with_multiple_real_service_windows'];r['door_clear_width']=1.56;r['door_clear_height']=2.62;r['originalHouseTemplateUsed']=False;return r
    p=profile(ident,w,h);wide=min(w*.30,3.5,w*.58-1.84);windows=[(-w*.29,wide,.75,min(2.65,h-.30)),(w*.29,wide,.75,min(2.65,h-.30))]
    if ident in ['archive_room','record_room','electrical_room','cold_store']:windows=[(-w*.31,1.45,1.85,min(h-.22,2.8)),(w*.31,1.45,1.85,min(h-.22,2.8))]
    if ident in ['supply_store','inspection_hall_normal','maintenance_workshop','theatre_preparation']:windows=[(-w*.32,w*.24,1.95,min(h-.2,2.9)),(w*.32,w*.24,1.95,min(h-.2,2.9))]
    if ident=='laundry_room':windows=[(-w*.29,wide,.22,2.65),(w*.29,wide,.22,2.65)]
    if ident=='hotel_lobby':windows+=[(x,1.48,4.12,5.60)for x in [-w*.34,-w*.15,w*.15,w*.34]]
    if ident in ['management_office','central_control']:windows.append((0,w*.24,h+.35,h+1.5))
    if ident=='mirror_maze':windows=[(-w*.30,w*.26,.20,2.90),(w*.30,w*.26,.20,2.90)]
    if ident=='staff_passage':windows=[]
    wall='clinical'if ident in ['clinic','cold_store']else'terracotta'if ident in ['dining_room','kitchen','maintenance_workshop','reading_room']else'utility'if ident in ['electrical_room','supply_store','central_control','inspection_hall_normal','theatre_preparation']else'ivory'
    open_front=ident in ['performance_stage','mirror_waiting','staff_passage']
    roof=spatial_shell(ident,w,d,h,r,wall,[]if open_front else windows,open_front)
    window_scene(ident,r,w,d)
    features=['profiled_structural_envelope_'+ident,'actual_door_and_glazing_apertures']
    if ident=='clinic':
        curved_canopy(r,w*.86,-d/2-.05,2.85,2.05,'clinical');F.accessible_clinic_porch(r,d)
        for x in [-w*.30,w*.30]:
            K.rounded_solid('medical_privacy_glazing_band',w*.28,.025,.43,'clinical',r,.002,(x,-d/2+.025,1.52))
        features+=['low_horizontal_treatment_wings','wide_step_free_covered_approach','visible_treatment_beds']
    elif ident=='dining_room':
        F.awning(r,w*.92,-d/2-.08,depth=2.35);F.terrace(r,w,d);features+=['high_dining_room_gable','full_width_dining_veranda','table_chair_groups']
    elif ident=='kitchen':
        for x in [-w*.22,w*.22]:
            K.tube('kitchen_ventilation_stack',[(x,d*.2,h-.1),(x,d*.2,h+2.35),(x,d*.2-.45,h+2.35)],[.20]*3,'painted_steel',r,12)
        F.canopy(r,3.6,-d/2,depth=1);features+=['triple_sawtooth_extraction_roof','paired_capped_flues','visible_cooking_line']
    elif ident=='hotel_lobby':
        curved_canopy(r,7.5,-d/2,3.55,3.4,'roof')
        for side in [-1,1]:
            F.prism('hotel_balcony_slab',[(side*w*.31-1.5,3.64),(side*w*.31+1.5,3.64),(side*w*.31+1.5,3.80),(side*w*.31-1.5,3.80)],.85,'cream_trim',r,-d/2-.32)
            K.tube('balcony_continuous_handrail',[(side*w*.31-1.45,-d/2-.70,4.65),(side*w*.31+1.45,-d/2-.70,4.65)],[.025]*2,'brass',r,6)
            for j in range(9):column(r,side*w*.31-1.4+j*.35,-d/2-.70,.82,'brass',.012).location.z=3.8
        features+=['two_storey_bedroom_wings','porte_cochere','accessible_entrance','balconies_under_mansard']
    elif ident=='electrical_room':
        for side in [-1,1]:
            x=side*w*.29;y=-d/2-1
            K.soft_body('substation_transformer_body',1.5,.8,1.40,'painted_steel',r,(x,y,.80))
            for j in range(7):K.section('transformer_cooling_fin',[(-.44,0),(.44,0),(.44,1.16),(-.44,1.16)],.035,'painted_steel',r).location=(x-.54+j*.18,y,.20)
            for dx in [-.36,.36]:
                K.tube('ceramic_power_bushing',[(x+dx,y,1.48),(x+dx,y,2.03)],[.07,.04],'linen',r,8)
        features+=['raised_busbar_house','outdoor_transformer_bays','ventilated_equipment_front']
    elif ident=='laundry_room':
        curved_canopy(r,w*.9,-d/2,2.85,1.4,'painted_steel');features+=['twin_daylight_sawtooth','visible_front_loading_washers','covered_washhouse_threshold']
    elif ident in ['supply_store','refreshment_store','cold_store']:
        curved_canopy(r,w*.80,-d/2,2.9,1.55,'painted_steel')
        if ident=='cold_store':
            for side in [-1,1]:
                x=side*w*.30
                K.rounded_solid('refrigeration_condenser_casing',1.30,.65,.95,'painted_steel',r,.08,(x,-d/2-.7,.62))
                for j in range(12):
                    a=j*math.tau/12;K.tube('condenser_guard_ring',[(x+.34*math.cos(i*math.tau/24),-d/2-1.04,.62+.34*math.sin(i*math.tau/24))for i in range(25)],[.015]*25,'iron',r,5)if j==0 else None
                for j in range(5):K.tube('condenser_fan_blade',[(x,-d/2-1.06,.62),(x+.29*math.cos(j*math.tau/5),-d/2-1.06,.62+.29*math.sin(j*math.tau/5))],[.035,.06],'iron',r,5)
        else:
            for side in [-1,1]:o=K.chest();o.parent=r;o.location=(side*w*.29,-d/2-.8,0);o.scale=(.7,.7,.7)
        features+=['loading_canopy','stock_storage_front'if ident!='cold_store'else'insulated_cold_room_with_real_condenser_units']
    elif ident in ['reading_room','archive_room','record_room']:
        curved_canopy(r,3.4,-d/2,2.92,1.7,'roof');features+=['shelved_book_bays'if ident=='reading_room'else'high_record_storage_glazing','purpose_profiled_archive_roof']
    elif ident in ['maintenance_workshop','inspection_hall_normal','mirror_workbay','theatre_preparation']:
        # The large bay is a recess with actual equipment, separate from the door.
        bx=-w*.29;bw=wide;yy=-d/2+.45
        for j in range(4):K.rounded_solid('partly_raised_service_shutter',bw,.08,.10,'painted_steel',r,.004,(bx,-d/2-.1,2.3+j*.12))
        if ident=='mirror_workbay':rack=F.glass_rack(r,(-w/2-.8,0,0));rack.rotation_euler.z=math.pi/2
        elif ident=='theatre_preparation':o=K.coat_rack();o.parent=r;o.location=(bx,yy,0)
        else:
            o=K.office_desk();o.parent=r;o.location=(bx,yy,0);o.scale=(.7,.7,.8)
            K.tube('workshop_jib_crane',[(w*.32,-d/2-.5,0),(w*.32,-d/2-.5,3.6),(w*.08,-d/2-.5,3.6)],[.075]*3,'painted_steel',r,8)
        features+=['real_service_bay_and_raised_shutter','purpose_equipment','large_workshop_roof_span']
    elif ident in ['performance_stage','hotel_multiuse','screening_room','dream_lobby','exhibition_room']:
        if ident=='performance_stage':
            for x in [-w*.43,w*.43]:column(r,x,-d/2,5.45,'sandstone',.25)
            rad=w*.42;pts=[(rad*math.cos(math.pi-i*math.pi/24),-d/2-.20,4.15+rad*.27*math.sin(i*math.pi/24))for i in range(25)];K.tube('structural_open_stage_proscenium',pts,[.18]*25,'cream_trim',r,10)
            for side in [-1,1]:
                xx=side*w*.36;verts=[(xx+u*.85,-d/2+.72+.12*math.cos(i*math.pi/2),z)for z in [.20,5.3]for i,u in enumerate([-1+j/16 for j in range(33)])];K.mesh('continuous_visible_stage_curtain',verts,[(i,i+1,i+34,i+33)for i in range(32)],'cloth',r).data.materials[0].use_backface_culling=False
            K.rounded_solid('public_performance_stage_deck',w*.88,3.0,.36,'wood',r,.04,(0,-d/2+.6,.18))
        else:curved_canopy(r,w*.75,-d/2,3.0,2.25,'roof')
        features+=['wide_public_assembly_volume','continuous_curved_hall_roof','open_proscenium_stage'if ident=='performance_stage'else'public_glazed_foyer']
    elif ident=='mirror_maze':
        for side in [-1,1]:
            x=side*w*.30
            for j in range(5):
                o=K.frame_ring('faceted_mirror_pavilion_fin',.62,3.1,.06,.18,'painted_steel',r,(x+(j-2)*.47,-d/2-.18,1.6));o.rotation_euler.z=(j-2)*.19
        features+=['prismatic_zigzag_mirror_roof','splayed_reflective_entrance_fins']
    elif ident in ['mirror_waiting','staff_passage','service_lounge']:
        for y in [-d/2,d/2]:
            for x in [-w/2+.12,w/2-.12]:column(r,x,y,h-.2,'wood',.11)
        if ident=='staff_passage':
            for y in [-d/2+i*d/6 for i in range(7)]:
                for x in [-w/2+.12,w/2-.12]:column(r,x,y,h-.2,'wood',.075)
        else:
            rear=K.root('rear_lounge_seating_terrace',r);rear.rotation_euler.z=math.pi;F.terrace(rear,w,d)
        features+=['structural_open_post_and_beam_pavilion','seating_and_shelter']
    elif ident in ['management_office','central_control']:
        curved_canopy(r,3.0,-d/2,2.9,1.5,'painted_steel')
        if ident=='central_control':
            for x in [-w*.18,w*.18]:K.tube('roof_communications_aerial',[(x,.8,h+2.60),(x,.8,h+4.1)],[.04,.018],'painted_steel',r,8)
        features+=['raised_glazed_control_gallery'if ident=='central_control'else'public_admin_counter_and_office_wing']
    elif ident=='ticket_booth':
        # Context and local booth both use this same aperture contract.
        wall=next(o for o in r.children if o.name.startswith('profiled_rear_structural_wall'))
        bpy.ops.mesh.primitive_cube_add(size=1,location=(0,d/2,1.95));cut=bpy.context.object;cut.dimensions=(3.65,.65,1.5);bpy.context.view_layer.update();mod=wall.modifiers.new('public_ticket_aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.context.view_layer.objects.active=wall;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
        F.awning(r,w*.94,-d/2,2.8,.8);features+=['twin_glazed_service_counters','small_ticket_pavilion_roof']
    I.plate(ident,r,(0,-d/2-.30,min(h-.28,3.10)),width=min(3.4,w*.52))
    r['purposeFeatures']=features;r['door_clear_width']=1.56;r['door_clear_height']=2.62;r['originalHouseTemplateUsed']=False
    return r
