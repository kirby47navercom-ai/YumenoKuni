"""Authored surface and functional finishing over the existing park geometry.

No gameplay/door/collision changes. Decorative skins stay on their real fascia;
new ride parts stay inside existing closed ride envelopes.
"""
import bpy,math
from collections import Counter
from pathlib import Path
from mathutils import Vector
import v4_rebuilt_environment_kit as K
import theme_park_v2_kit as T
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/park_levels_v1/detail_v3'
THEMES=['fairytale','carnival','mirrors','clockwork','starlight']

def material(key,base,file,color=(1,1,1,1),rough=.55,normal=.12,metal=0):
    m=K.M[base].copy();m.name='theme_v2_'+key;m['surfaceTint']=list(color)
    bs=m.node_tree.nodes.get('Principled BSDF')
    for link in list(bs.inputs['Base Color'].links):m.node_tree.links.remove(link)
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(O/file),check_existing=True);tex.image.pack();tex.extension='REPEAT'
    # The compiler uses surfaceTint as glTF baseColorFactor. Show the same
    # multiplication in Blender; otherwise every painted variant looks ivory.
    mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=color
    m.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color'])
    bs.inputs['Metallic'].default_value=metal;bs.inputs['Specular IOR Level'].default_value=.24
    for link in list(bs.inputs['Roughness'].links):m.node_tree.links.remove(link)
    bs.inputs['Roughness'].default_value=rough
    for node in m.node_tree.nodes:
        if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=normal
    K.M[key]=m;return m

def setup():
    for name in ['coral','cobalt','violet','mint','gold','copper','steel']:
        old=K.M[name];color=tuple(old.get('surfaceTint',(1,1,1,1)))
        material(name,'lacquer','painted-enamel.png',color,.40 if name not in ['gold','copper','steel']else .48,.10,.22 if name in ['gold','copper','steel']else .035)
    material('cream_paint','lacquer','painted-enamel.png',(1,.96,.87,1),.43,.08)
    for key,color in [('canvas_ivory',(1,.97,.88,1)),('canvas_coral',(.66,.21,.30,1)),('canvas_cobalt',(.25,.31,.51,1))]:material(key,'linen','tent-canvas.png',color,.90,.28)
    material('ornament_print','lacquer','ornament-trims.png',rough=.68,normal=.06)
    K.M['ornament_print'].use_backface_culling=False

def reset(parent):
    for obj in list(parent.children):
        if obj.name.startswith('detail_finish_v3'):
            bpy.data.batch_remove(ids=[obj,*obj.children_recursive])
    return T.root('detail_finish_v3',parent)

def uvstrip(name,vertices,faces,coords,theme,parent):
    # Preserve the cylindrical UV seam. K.mesh welds coincident endpoints,
    # which would collapse the separate first/last texture coordinates.
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);obj.parent=parent
    data.materials.append(K.M['ornament_print']);data.uv_layers.new(name='UVMap')
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            u,v=coords[obj.data.loops[li].vertex_index];obj.data.uv_layers[0].data[li].uv=(u,1-(theme+.018+v*.964)/5)
    return obj

def panel(parent,x0,x1,y,z0,z1,theme,repeat=1):
    return uvstrip('attached_painted_fascia',[(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)],[(0,1,2,3)],[(0,1),(repeat,1),(repeat,0),(0,0)],theme,parent)

def band(parent,r0,r1,z0,z1,theme,repeat=4,skip_entry=False):
    n=128;v=[(rr*math.cos(i*T.TAU/n),rr*math.sin(i*T.TAU/n),z)for rr,z in [(r0,z0),(r1,z1)]for i in range(n+1)]
    f=[(i,i+1,n+2+i,n+1+i)for i in range(n)if not skip_entry or math.sin((i+.5)*T.TAU/n)>=-.965]
    uv=[(repeat*i/n,1-k)for k in range(2)for i in range(n+1)]
    return uvstrip('fitted_ornamental_drum_skin',v,f,uv,theme,parent)

def remap(owner):
    count=0
    for obj in owner.children_recursive:
        if obj.type!='MESH':continue
        for i,m in enumerate(obj.data.materials):
            if not m:continue
            key=m.name.split('.')[0].removeprefix('theme_v2_')
            if m.name.startswith('theme_v2_')and key in K.M:obj.data.materials[i]=K.M[key]
        if obj.name.startswith(('pony_carved_body','pony_continuous_neck','pony_leg','pony_ear','turned_pavilion_column','arcade_turned_column','swing_ride_tapered_mast','teacup_saucer','central_teapot','teapot_curved_spout','rocket_continuous_tapered_fuselage','pierced_mask_face','sculpted_mask_nose','prize_head','prize_body','prize_rabbit_ear','coherent_hollow_booth_case')):
            obj.data.materials.clear();obj.data.materials.append(K.M['cream_paint']);count+=1
        if obj.name.startswith(('sewn_big_top_canvas','enclosing_tent_side_canvas','continuous_fitted_tent_eave_valance','sewn_pennant')):
            for i,m in enumerate(obj.data.materials):
                key=m.name.split('.')[0].removeprefix('theme_v2_')
                target='canvas_'+key
                if target in K.M:obj.data.materials[i]=K.M[target]
            count+=1
    return count

def pony_finish(pony):
    p=reset(pony)
    for side in [-1,1]:
        T.ball('painted_pony_eye',p,(.94,side*.175,1.64),.044,'steel')
        T.ball('pony_eye_catchlight',p,(.95,side*.209,1.65),.012,'ivory')
        T.tube('fitted_pony_bridle',[(1.12,side*.12,1.49),(.94,side*.19,1.51),(.74,side*.17,1.65),(.66,side*.13,1.52)],.022,'coral',p,6)
        T.tube('pony_rein',[(1.10,side*.15,1.43),(.43,side*.35,.98),(.06,side*.31,.95)],.016,'gold',p,6)
        for x,bend in [(-.43,-.16),(.41,.22)]:T.lathe('painted_pony_hoof',[(.085,-.20),(.09,-.10),(.07,-.04)],'steel',p,8,(x+bend+.12,side*.21,0))
        T.tube('saddle_stirrup_leather',[(.03,side*.3,.91),(.01,side*.36,.46)],.021,'coral',p,6)
        T.tube('actual_stirrup_loop',[(.01+.11*math.cos(i*T.TAU/16),side*.37,.40+.10*math.sin(i*T.TAU/16))for i in range(17)],.018,'gold',p,6)
    K.tube('continuous_sculpted_pony_mane',[(.45,0,.80),(.54,0,1.12),(.53,0,1.48),(.67,0,1.72)],[.10,.09,.08,.025],'cobalt',p,8)

def booth_finish(booth,theme):
    p=reset(booth);panel(p,-2.34,2.34,-1.925,.20,.79,theme)
    for z in [.16,.84]:T.tube('counter_fitted_trim',[(-2.45,-1.945,z),(2.45,-1.945,z)],.035,'gold',p)
    panel(p,-2.5,2.5,-2.235,2.94,3.16,theme)
    for x in [-2.55,2.55]:
        T.lathe('canopy_post_ferrule',[(.13,.04),(.13,.18),(.10,.23)],'gold',p,12,(x,-1.9,0))
    for prize in [o for o in booth.children if o.name.startswith('shaped_fairground_prize')]:
        q=reset(prize)
        for x in [-.085,.085]:T.ball('sewn_prize_eye',q,(x,-.195,.04),.028,'steel')
        T.ball('sewn_prize_nose',q,(0,-.215,-.05),.026,'coral')
        T.tube('prize_ribbon_knot',[(-.13,-.23,-.18),(0,-.25,-.22),(.13,-.23,-.18)],.05,'coral',q,6)

def open_rocket(vehicle):
    # Closed inner/outer shell with a real passenger opening, not a painted
    # black oval on the former solid teardrop body.
    for obj in list(vehicle.children):
        if obj.name.startswith(('rocket_continuous_tapered_fuselage','formed_open_cockpit_rocket_hull')):bpy.data.objects.remove(obj,do_unlink=True)
    n=16;sections=[(-1.9,.025,0),(-1.4,.40,.1),(-.65,.58,.13),(.65,.55,.12),(1.35,.32,.07)]
    v=[(rr*factor*math.cos(i*T.TAU/n),y,z+rr*factor*math.sin(i*T.TAU/n))for factor in [1,.84]for y,rr,z in sections for i in range(n)];N=len(v)//2
    outer=[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i)for k in range(4)for i in range(n)if not(k==2 and 1<=i<=6)]
    edges=Counter(tuple(sorted(e))for f in outer for e in zip(f,(*f[1:],f[0])))
    faces=[*outer,*[tuple(i+N for i in reversed(f))for f in outer]]
    for f in outer:
        for a,b in zip(f,(*f[1:],f[0])):
            if edges[tuple(sorted((a,b)))]==1:faces.append((a,a+N,b+N,b))
    K.mesh('formed_open_cockpit_rocket_hull',v,faces,'cream_paint',vehicle,True,uv_scale=.55)
    p=reset(vehicle)
    for yy,rr,z in [sections[2],sections[3]]:
        T.tube('cockpit_real_painted_rim',[(rr*math.cos(i*T.TAU/n),yy,z+rr*math.sin(i*T.TAU/n))for i in range(1,8)],.028,'coral',p,6)
    for i in [1,7]:T.tube('cockpit_continuous_side_rim',[(rr*math.cos(i*T.TAU/n),y,z+rr*math.sin(i*T.TAU/n))for y,rr,z in sections[2:4]],.028,'coral',p,6)
    T.tube('rocket_control_yoke',[(-.18,-.35,.57),(0,-.37,.63),(.18,-.35,.57)],.024,'steel',p,6)
    T.ball('vehicle_nose_lamp',p,(0,-1.72,.13),.045)

def finish(row,root,owner):
    theme=THEMES.index(row['id']);painted=remap(owner);features=[]
    for obj in list(owner.children):
        name=obj.name
        if name.startswith('complete_royal_carousel'):
            p=reset(obj);band(p,7.095,7.095,5.43,6.04,0,4);band(p,6.708,6.708,.09,.25,0,4)
            for pony in [o for o in obj.children if o.name.startswith('carousel_pony')]:pony_finish(pony)
            for i in range(10):
                a=i*T.TAU/10;q=T.root('carousel_recessed_drum_mirror',p,(.925*math.cos(a),.925*math.sin(a),2.6),a+math.pi/2)
                K.frame_ring('mirror_shaped_gilt_frame',.48,2.6,.045,.06,'gold',q)
                K.mesh('drum_silver_mirror',[(-.19,-.04,-1.25),(.19,-.04,-1.25),(.19,-.04,1.25),(-.19,-.04,1.25)],[(0,1,2,3)],'mirror',q)
            features.append('painted_carousel_ponies_and_mirrored_drum')
        elif name.startswith('complete_teacup_attraction'):
            reset(obj)
            for cup in [o for o in obj.children if o.name.startswith('formed_teacup_vehicle')]:
                p=reset(cup);band(p,1.31,1.41,.96,1.28,0,1);T.ring('porcelain_fitted_gilt_rim',p,1.425,1.53,'gold',.028)
            features.append('enamel_porcelain_and_gilded_cup_rims')
        elif name.startswith('complete_suspended_chair_ride'):
            p=reset(obj);band(p,6.514,6.514,7.20,7.75,1,4)
            for i in range(8):
                a=i*T.TAU/8;T.tube('mast_fitted_gilded_flute',[(1.055*math.cos(a),1.055*math.sin(a),1.10),(.75*math.cos(a),.75*math.sin(a),5.90)],.026,'gold',p,6)
            for seat in [o for o in obj.children if o.name.startswith('suspended_swing_seat')]:
                q=reset(seat);T.tube('swing_seat_safety_restraint',[(-.25,.21,.48),(-.25,-.20,.42),(.25,-.20,.42),(.25,.21,.48)],.027,'gold',q,6)
            features.append('circus_crown_and_bucket_restraints')
        elif name.startswith('complete_big_top'):
            p=reset(obj);band(p,13.105,13.105,4.98,5.30,1,8);band(p,13.015,13.015,.12,.42,1,8,True);features.append('woven_canvas_and_fitted_circus_fascia')
        elif name.startswith('purpose_midway_booth_'):booth_finish(obj,theme)
        elif name.startswith('fantasy_resort_facade'):
            p=reset(obj);panel(p,-5.5,5.5,-6.065,3.07,3.38,0,2)
            for x,b,ww,h in [(x,1.0,1.05,1.75)for x in [-5.4,-3.5,3.5,5.4]]+[(x,4.1,1.05,1.85)for x in [-5.4,-3.5,-1.6,1.6,3.5,5.4]]:
                T.profile_extrude('fitted_window_stone_sill',[(-.02,b-.14),(-.28,b-.14),(-.32,b-.06),(-.02,b+.01)],ww+.16,'ivory',p,(x,-6.02,0))
                T.tube('resort_window_transom',[(x-.48,-6.025,b+h*.58),(x+.48,-6.025,b+h*.58)],.025,'gold',p,6)
            features.append('recessed_window_sills_transoms_and_façade_course')
        elif name.startswith('actual_mask_funhouse_front'):
            p=reset(obj)
            for x0,x1 in [(-7.7,-4.9),(4.9,7.7)]:panel(p,x0,x1,-9.425,3.48,3.94,2)
            features.append('art_deco_funhouse_fascia')
        elif name.startswith('open_mechanical_gear_tower'):
            p=reset(obj)
            for x,z in [(-.9,11),(1.65,8.25),(-.65,5.8)]:
                q=T.root('shaft_bearing_housing',p,(x,-1.22,z));q.rotation_euler.x=math.pi/2
                T.lathe('formed_bearing_cap',[(.34,-.10),(.39,0),(.35,.19),(.21,.25)],'steel',q,24)
                for i in range(4):
                    a=i*T.TAU/4;T.lathe('bearing_fastener',[(.045,.20),(.045,.26)],'gold',q,6,(.28*math.cos(a),.28*math.sin(a),0))
            features.append('mechanical_shafts_bearings_and_fasteners')
        elif name.startswith('complete_coaster_boarding_station'):
            p=reset(obj)
            for x in [-6.83,6.83]:
                q=T.root('station_riveted_eave_band',p,(x,0,0),math.pi/2);panel(q,-9.2,9.2,0,4.39,4.69,3,3)
            features.append('riveted_station_eaves')
        elif name.startswith('complete_retro_space_theatre'):
            p=reset(obj);band(p,10.025,10.025,2.68,3.04,4,6,True)
            # Both closed leaves formerly exposed an 8 cm vertical slit and
            # a bare gap above them. Fit actual joinery into the existing aperture.
            K.frame_ring('theatre_continuous_entry_reveal',4.48,3.18,.12,.16,'gold',p,(0,-9.845,1.56),inner_size=(4.24,2.94))
            K.rounded_solid('theatre_center_meeting_stile',.105,.13,2.95,'gold',p,.008,(0,-9.84,1.50))
            K.mesh('theatre_fitted_transom_glass',[(-2.16,-9.80,2.82),(2.16,-9.80,2.82),(2.16,-9.80,3.16),(-2.16,-9.80,3.16)],[(0,1,2,3)],'glass',p)
            K.rounded_solid('theatre_flush_door_threshold',4.46,.20,.085,'steel',p,.008,(0,-9.80,.025))
            features.append('orbital_theatre_fascia_and_sealed_door_joinery')
        elif name.startswith('complete_orbital_vehicle_attraction'):
            p=reset(obj);band(p,8.96,8.82,.10,.28,4,4)
            for vehicle in [o for o in obj.children if o.name.startswith('recognizable_rocket_vehicle')]:open_rocket(vehicle)
            globe=next(o for o in obj.children if o.name.startswith('suspended_ringed_planet'))
            for old in list(globe.children):
                if old.name.startswith(('planet_sphere','rounded_planet_sphere')):bpy.data.objects.remove(old,do_unlink=True)
            T.lathe('rounded_planet_sphere',[(max(.005,1.35*math.sin(i*math.pi/16)),-1.35*math.cos(i*math.pi/16))for i in range(17)],'mint',globe,32)
            features.append('real_open_rocket_cockpits_and_rounded_planet')
    # Each canopy follows the existing authored eave, not a floating sign board.
    site=__import__('json').loads((O.parent/'theme_park_v2/site-plan.json').read_text(encoding='utf8'))[row['id']]
    p=reset(owner)
    for spec in site.get('coveredWalks',[]):
        pts=[Vector(v)for v in spec['points']];width=spec.get('width',4.4)
        for side in [-1,1]:
            edge=[]
            for i,v in enumerate(pts):
                tangent=pts[min(len(pts)-1,i+1)]-pts[max(0,i-1)];tangent.normalize();n=Vector((-tangent.y,tangent.x));edge.append(v+n*side*(width/2+.015))
            vertices=[(v.x,v.y,z)for z in [3.10,3.44]for v in edge];count=len(edge);length=0;uv=[]
            distances=[0]
            for a,b in zip(edge,edge[1:]):length+=(b-a).length;distances.append(length/7)
            for k in range(2):uv.extend((u,1-k)for u in distances)
            uvstrip('continuous_themed_arcade_frieze',vertices,[(i,i+1,count+i+1,count+i)for i in range(count-1)],uv,theme,p)
    return {'revision':3,'paintedSurfaceObjects':painted,'features':features,'sourceTextures':['ornament-trims.png','painted-enamel.png','tent-canvas.png'],'navigationAndCaseGeometryUnchanged':True}
