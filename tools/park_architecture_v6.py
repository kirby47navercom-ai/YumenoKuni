"""Purpose-designed park architecture; real wall sections and apertures.

Blender metres, Z-up. Reuse construction operations, never a generic house body.
"""
import bpy,bmesh,math
from mathutils import Vector
import v4_rebuilt_environment_kit as K
import dream_hotel_architecture as H

def palette(tag='clinic',overrides=None):
    specs=[('ivory','plaster',(.94,.87,.70,1),.84,0,.20),('mint','plaster',(.52,.77,.70,1),.79,0,.18),('stone','stone',(.91,.83,.68,1),.82,0,.24),('roof','roof',(.45,.68,.66,1),.72,.06,.40),('iron','iron',(.15,.25,.29,1),.44,.28,.16),('wood','wood',(.67,.48,.29,1),.61,0,.24),('copper','plaster',(.41,.66,.61,1),.44,.25,.16),('glass','plaster',(.39,.64,.69,1),.26,.15,0),('frost','plaster',(.71,.85,.84,1),.64,.03,.10)]
    for key,base,tint,rough,metal,strength in specs:
        tint=(overrides or{}).get(key,tint)
        m=K.M[base].copy();m.name='architecture6_'+tag+'_'+key;m['surfaceTint']=tint
        bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=metal
        old=bs.inputs['Base Color'].links[0].from_socket if bs.inputs['Base Color'].links else None
        if old:
            t=m.node_tree.nodes.new('ShaderNodeMixRGB');t.blend_type='MULTIPLY';t.inputs[0].default_value=1;t.inputs[2].default_value=tint;m.node_tree.links.new(old,t.inputs[1]);m.node_tree.links.new(t.outputs[0],bs.inputs['Base Color'])
        else:bs.inputs['Base Color'].default_value=tint
        if not bs.inputs['Roughness'].links:bs.inputs['Roughness'].default_value=rough
        for n in m.node_tree.nodes:
            if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=strength
        if key in ['glass','frost']:
            for input in ['Base Color','Roughness','Normal']:
                for link in list(bs.inputs[input].links):m.node_tree.links.remove(link)
            bs.inputs['Base Color'].default_value=tint;bs.inputs['Roughness'].default_value=rough
        # Shared section tools address materials through these temporary aliases.
        K.M['v6_'+key]=m;K.M['hotel_'+key]=m

def mesh(name,v,f,mat,parent,bevel=.01):
    o=H.mesh(name,v,f,None,parent)
    if mat:o.data.materials.append(K.M['v6_'+mat])
    return H.finish(o,bevel)

def prism(name,outline,at,tangent,normal,depths,mat,parent,bevel=.008):
    o=H.prism(name,outline,at,tangent,normal,depths,None,parent)
    if mat:o.data.materials.append(K.M['v6_'+mat])
    H.finish(o,bevel)
    if mat=='roof':surface_uv(o)
    return o

def surface_uv(o):
    uv=o.data.uv_layers[0]
    for face in o.data.polygons:
        normal=face.normal;u=Vector((0,0,1)).cross(normal)
        if u.length<.001:u=Vector((1,0,0))
        u.normalize();vaxis=normal.cross(u).normalized()
        for li in face.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co.dot(u)*.55,co.dot(vaxis)*.55)

def shell(name,poly,z0,z1,thickness,mat,parent):
    o=H.shell(name,poly,[(z0,0),(z0+.13,-.016),(z1-.12,0),(z1,0)],thickness,None,parent);o.data.materials.append(K.M['v6_'+mat]);return o

def hip_roof(name,poly,z,rise,inset,parent):
    inset=min(max(x for x,y in poly)-min(x for x,y in poly),max(y for x,y in poly)-min(y for x,y in poly))/2-.06
    inner=H.offset(poly,inset);n=len(poly);v=[]
    for ring,height in [(poly,z),(inner,z+rise),(poly,z-.14),(inner,z+rise-.14)]:v.extend((x,y,height)for x,y in ring)
    f=[]
    for i in range(n):
        j=(i+1)%n;f.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j)])
    f.extend([tuple(range(n,2*n)),tuple(reversed(range(3*n,4*n)))])
    roof=mesh(name,v,f,'roof',parent,.012)
    # Use true surface metres on each sloping plane, rather than squashing
    # hip tiles into the dominant world-axis projection.
    uv=roof.data.uv_layers[0]
    for face in roof.data.polygons:
        normal=face.normal;u=Vector((0,0,1)).cross(normal)
        if u.length<.001:u=Vector((1,0,0))
        u.normalize();vaxis=normal.cross(u).normalized()
        for li in face.loop_indices:
            co=roof.data.vertices[roof.data.loops[li].vertex_index].co;uv.data[li].uv=(co.dot(u)*.55,co.dot(vaxis)*.55)
    H.bar(name+'_continuous_eave',[(x,y,z-.04)for x,y in poly+[poly[0]]],.07,.10,'copper',parent)
    return roof

def column(name,x,y,z,height,parent):
    profile=[(.145,z),(.145,z+.10),(.09,z+.18),(.075,z+.30),(.075,z+height-.22),(.12,z+height-.12),(.145,z+height-.10),(.145,z+height)];n=12
    return mesh(name,[(x+r*math.cos(i*math.tau/n),y+r*math.sin(i*math.tau/n),h)for r,h in profile for i in range(n)],[tuple(reversed(range(n))),tuple(range((len(profile)-1)*n,len(profile)*n)),*[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i)for k in range(len(profile)-1)for i in range(n)]],'iron',parent,0)

def window(name,at,tangent,normal,width,bottom,top,parent,privacy=False,door=False):
    outer=H.rectangle(width+.19,bottom-.09,top+.09);inner=H.rectangle(width-.012,bottom+.008,top-.008)
    H.ring(name+'_profiled_stone_jamb',outer,inner,at,tangent,normal,(-.045,.16),'stone',parent)
    H.ring(name+'_recessed_metal_sash',H.rectangle(width-.02,bottom+.02,top-.02),H.rectangle(width-.13,bottom+.075,top-.075),at,tangent,normal,(.20,.255),'iron',parent)
    zsplit=bottom+(top-bottom)*.64 if privacy else top
    prism(name+'_actual_glass_depth',H.rectangle(width-.14,bottom+.075,zsplit-.025),at,tangent,normal,(.248,.274),'frost'if privacy else'glass',parent,0)
    if privacy:
        prism(name+'_clear_upper_glazing',H.rectangle(width-.14,zsplit+.025,top-.075),at,tangent,normal,(.248,.274),'glass',parent,0)
        H.bar(name+'_privacy_transom',[(at[0]+tangent[0]*x+normal[0]*.228,at[1]+tangent[1]*x+normal[1]*.228,zsplit)for x in [-width/2+.06,width/2-.06]],.035,.045,'iron',parent)
    def point(x,z,s=.225):return(at[0]+tangent[0]*x+normal[0]*s,at[1]+tangent[1]*x+normal[1]*s,z)
    H.bar(name+'_meeting_stile',[point(0,bottom+.075),point(0,top-.075)],.035,.045,'iron',parent)
    # Sloped sill with a genuine lower drip, rather than a pasted rectangle.
    section=[(-.10,bottom-.09),(-.10,bottom-.015),(.30,bottom+.025),(.34,bottom-.025),(.34,bottom-.09)];v=[point(x,z,s)for x in [-width/2-.12,width/2+.12]for s,z in section];n=len(section)
    mesh(name+'_sloped_sill',v,[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'stone',parent,0)
    if door:
        for x in [-.16,.16]:H.bar(name+'_pull_handle',[point(x,bottom+.94,.13),point(x,bottom+1.50,.13)],.025,.035,'copper',parent)

def cut_windows(body,specs,parent,cutDepth=.43):
    cutters=[]
    for name,at,tan,normal,w,b,t,privacy,door in specs:
        # Door voids continue through the bottom course. A 10 mm masonry lip
        # below a 12 mm bevel creates collapsing triangles during export.
        cutters.append(H.prism(name+'_construction_void',H.rectangle(w,-.10 if door else b,t),at,tan,normal,(-.10,cutDepth),None,parent))
    H.difference(body,cutters,body.name+'_true_apertures');H.finish(body,.012)
    for name,at,tan,normal,w,b,t,privacy,door in specs:window(name,at,tan,normal,w,b,t,parent,privacy,door)

def clinic():
    palette();r=K.root('designed_clinic_architecture_v6')
    # One contiguous U-shaped wall, with a real recessed central entrance.
    poly=[(-4.70,-4.5),(-1.65,-4.5),(-1.65,-3.6),(1.65,-3.6),(1.65,-4.5),(4.70,-4.5),(4.70,4.3),(-4.70,4.3)]
    wall=shell('clinic_continuous_thick_recessed_wall',poly,.025,3.12,.28,'ivory',r)
    specs=[('step_free_double_door',(0,-3.6),(1,0),(0,1),2.08,.035,2.62,False,True)]
    for x in [-3.18,3.18]:specs.append(('treatment_privacy_window',(x,-4.5),(1,0),(0,1),2.14,1.0,2.56,True,False))
    for x in [-4.7,4.7]:
        for y in [-1.9,1.15]:specs.append(('treatment_side_aperture',(x,y),(0,1),(1 if x<0 else-1,0),1.82,1.10,2.54,True,False))
    for x in [-3.1,0,3.1]:specs.append(('rear_treatment_window',(x,4.3),(1,0),(0,-1),1.85,1.14,2.54,True,False))
    cut_windows(wall,specs,r)
    # Three joined roof sections have different levels, not three copied houses.
    for a,b in [(-4.88,-1.55),(1.55,4.88)]:hip_roof('treatment_hipped_roof',[(a,-4.69),(b,-4.69),(b,4.48),(a,4.48)],3.17,.64,.73,r)
    upperPoly=[(-1.69,-3.62),(1.69,-3.62),(1.69,4.3),(-1.69,4.3)]
    upper=shell('raised_central_daylight_lantern_wall',upperPoly,3.10,3.86,.18,'mint',r)
    upperSpecs=[]
    for x in [-1.69,1.69]:
        for y in [-1.8,.9,3.1]:upperSpecs.append(('clerestory_actual_slot',(x,y),(0,1),(1 if x<0 else-1,0),1.72,3.29,3.69,False,False))
    cut_windows(upper,upperSpecs,r)
    hip_roof('central_clerestory_hip_roof',[(-1.88,-3.81),(1.88,-3.81),(1.88,4.49),(-1.88,4.49)],3.91,.63,.75,r)
    # Shaped single copper canopy, attached into the recessed wall and columns.
    xx=[-1.82+i*3.64/24 for i in range(25)];n=len(xx)
    def height(x):return 2.88+.34*(1-(x/1.82)**2)
    verts=[(x,y,height(x)+k*.065)for k in range(2)for y in [-6.24,-3.49]for x in xx];faces=[]
    for i in range(n-1):faces +=[(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),(i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)]
    faces +=[(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)]
    canopy=mesh('single_curved_copper_entry_canopy',verts,faces,'copper',r,.008)
    for face in canopy.data.polygons:
        if abs(face.normal.z)>.6 and face.area>.02:face.use_smooth=True
    for y in [-6.10,-3.56]:H.bar('canopy_structural_segmental_beam',[(x,y,height(x)-.045)for x in xx],.09,.12,'iron',r)
    for x in [-1.5,1.5]:
        column('clinic_canopy_profiled_column',x,-6.1,.025,height(x)-.08,r)
        H.bar('canopy_back_to_wall_tie',[(x,-6.1,height(x)-.06),(x,-3.56,height(x)-.06)],.07,.08,'iron',r)
        for s in [-1,1]:H.bar('column_curved_knee_brace',[(x+s*.28*t,-6.1,2.51+(.36)*t+.05*t*(1-t))for t in [i/8 for i in range(9)]],.035,.045,'iron',r)
    # No outside beds or text signs. Small recessed medical emblem belongs to
    # the actual lintel; the plan itself carries the treatment/arrival functions.
    cross=[(-.10,.20),(.10,.20),(.10,.10),(.20,.10),(.20,-.10),(.10,-.10),(.10,-.20),(-.10,-.20),(-.10,-.10),(-.20,-.10),(-.20,.10),(-.10,.10)]
    prism('inset_medical_emblem',[(x,z+3.50)for x,z in cross],(0,-3.62),(1,0),(0,1),(-.035,-.015),'frost',r,.006)
    r['architectureRevision']=6;r['purpose']='Single contiguous treatment pavilion with recessed step-free arrival and raised daylight lantern';r['wallThicknessMetres']=.28;r['apertureCount']=len(specs)+len(upperSpecs);r['preservedDoorLocal']=[0,-3.6,.035]
    return r

def dining_room():
    palette('dining',{'ivory':(.96,.72,.61,1),'mint':(.75,.45,.38,1),'roof':(.48,.62,.83,1),'copper':(.78,.42,.39,1)})
    r=K.root('designed_garden_dining_architecture_v6')
    poly=[(-5.65,-3.9),(-4.6,-4.95),(-2.409,-4.95),(-1.4,-4.95),(-1.4,-4.45),(0,-4.45),(1.4,-4.45),(1.4,-4.95),(2.409,-4.95),(4.6,-4.95),(5.65,-3.9),(5.65,4.8),(2.409,4.8),(0,4.8),(-2.409,4.8),(-5.65,4.8)]
    body=shell('dining_continuous_bay_and_recess_wall',poly,.025,3.24,.27,'ivory',r)
    # Edit the actual continuous wall top into the roof's whole cross-section.
    # The tall centre and lean-to wings cannot leave open black wedges.
    for v in body.data.vertices:
        if v.co.z>3.23:
            x=abs(v.co.x);v.co.z=(5.22-1.67*x/2.48 if x<2.409 else 3.62-(x-2.23)*.45/3.65)+.02
    body.data.update();body.data.materials.append(K.M['v6_mint'])
    for face in body.data.polygons:
        if min(body.data.vertices[i].co.z for i in face.vertices)>3.11:face.material_index=1
    specs=[('dining_wide_arrival',(0,-4.45),(1,0),(0,1),2.16,.035,2.86,False,True)]
    for x in [-3,3]:specs.append(('dining_front_conservatory_glazing',(x,-4.95),(1,0),(0,1),2.45,.54,2.94,False,False))
    a=math.sqrt(.5)
    specs +=[('diagonal_dining_bay',(-5.125,-4.425),(a,-a),(a,a),1.04,.54,2.94,False,False),('diagonal_dining_bay',(5.125,-4.425),(a,a),(-a,a),1.04,.54,2.94,False,False)]
    for x in [-5.65,5.65]:
        for y in [-1.65,1.1,3.6]:specs.append(('dining_side_casement',(x,y),(0,1),(1 if x<0 else-1,0),1.85,.65,2.91,False,False))
    for x in [-3.9,0,3.9]:specs.append(('dining_rear_casement',(x,4.8),(1,0),(0,-1),1.8,.85,2.88,False,False))
    for y,normal in [(-4.45,(0,1)),(4.8,(0,-1))]:specs.append(('dining_gable_window',(0,y),(1,0),normal,1.18,3.81,4.62,False,False))
    cut_windows(body,specs,r)
    profile=[(-2.48,3.69),(0,5.36),(2.48,3.69),(2.41,3.55),(0,5.20),(-2.41,3.55)]
    prism('one_continuous_central_gabled_roof',profile,(0,0),(1,0),(0,1),(-5.12,5.05),'roof',r,.012)
    for y in [-5.12,5.05]:H.bar('dining_roof_profiled_fascia',[(x,y,z)for x,z in profile[:3]],.085,.11,'stone',r)
    for side in [-1,1]:
        section=[(side*2.23,3.76),(side*5.88,3.31),(side*5.88,3.17),(side*2.23,3.62)]
        prism('connected_conservatory_lean_to_roof',section,(0,0),(1,0),(0,1),(-5.15,5.05),'roof',r,.012)
    # One projecting segmented entrance hood, with thrust resolved into columns.
    for x in [-1.25,1.25]:column('dining_arrival_column',x,-6.25,.025,2.96,r)
    outline=[(-1.58,3.04),(0,3.57),(1.58,3.04),(1.54,2.94),(0,3.45),(-1.54,2.94)]
    prism('dining_supported_entry_pediment',outline,(0,0),(1,0),(0,1),(-6.40,-4.36),'copper',r,.008)
    for y in [-6.25,-4.45]:H.bar('dining_entrance_roof_beam',[(-1.5,y,2.98),(0,y,3.49),(1.5,y,2.98)],.07,.10,'iron',r)
    for cx in [-3.8,3.8]:
        table=K.curved_family('meeting_table');table.parent=r;table.location=(cx,-6.1,.015);table.scale=(.52,.80,1)
        for side in [-1,1]:
            chair=K.curved_family('chair');chair.parent=r;chair.location=(cx+side*1.05,-6.1,.015)
            # The existing sculpted chair's back is +Y; the seat faces -Y.
            # Left/right seats therefore turn inward toward their own table.
            chair.rotation_euler.z=-side*math.pi/2
    r['architectureRevision']=6;r['purpose']='Garden restaurant with canted conservatory bays, high gabled dining hall, deep arrival and fitted lean-to roofs';r['wallThicknessMetres']=.27;r['apertureCount']=len(specs)+2
    return r

def brick_material():
    from pathlib import Path
    folder=Path(__file__).resolve().parents[1]/'art/space_v4/park_levels_v1/architecture_v6/materials'
    m=bpy.data.materials.new('architecture6_fired_brick');m.use_nodes=True;m['surfaceTint']=[1,1,1,1];bs=m.node_tree.nodes.get('Principled BSDF')
    for key,target,color in [('color','Base Color','sRGB'),('roughness','Roughness','Non-Color'),('normal','Normal','Non-Color')]:
        t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(folder/('brick_'+key+'.png')),check_existing=True);t.image.colorspace_settings.name=color;t.image.pack();t.extension='REPEAT'
        if key=='normal':n=m.node_tree.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.55;m.node_tree.links.new(t.outputs['Color'],n.inputs['Color']);m.node_tree.links.new(n.outputs[0],bs.inputs[target])
        else:m.node_tree.links.new(t.outputs['Color'],bs.inputs[target])
    K.M['v6_brick']=m;K.M['hotel_brick']=m

def zinc_material(tint=(.62,.71,.72,1)):
    m=K.M['v6_copper'].copy();m.name='architecture6_painted_zinc';m['surfaceTint']=tint;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=.55
    for n in m.node_tree.nodes:
        if n.type=='MIX_RGB'and n.blend_type=='MULTIPLY':n.inputs[2].default_value=tint
    if bs.inputs['Roughness'].links:
        old=bs.inputs['Roughness'].links[0].from_socket;n=m.node_tree.nodes.new('ShaderNodeMath');n.operation='MULTIPLY';n.inputs[1].default_value=.55;m.node_tree.links.new(old,n.inputs[0]);m.node_tree.links.new(n.outputs[0],bs.inputs['Roughness'])
    K.M['v6_zinc']=m;K.M['hotel_zinc']=m

def kitchen():
    palette('kitchen');brick_material();zinc_material();r=K.root('designed_sawtooth_kitchen_architecture_v6')
    poly=[(-5.75,-4.8),(-1.25,-4.8),(-1.25,-4.48),(1.25,-4.48),(1.25,-4.8),(5.75,-4.8),(5.75,4.8),(-5.75,4.8)]
    body=shell('continuous_kitchen_brick_shell',poly,.025,3.16,.30,'brick',r)
    specs=[('kitchen_service_entry',(0,-4.48),(1,0),(0,1),1.90,.035,2.69,False,True),('actual_food_service_hatch',(-3.35,-4.8),(1,0),(0,1),2.40,.96,2.36,False,False),('front_preparation_glazing',(3.55,-4.8),(1,0),(0,1),1.85,1.15,2.48,True,False)]
    for x in [-5.75,5.75]:
        for y in [-2.9,.4,3.3]:specs.append(('kitchen_high_hygiene_window',(x,y),(0,1),(1 if x<0 else-1,0),1.50,1.72,2.76,True,False))
    specs +=[('rear_preparation_window',(-3.35,4.8),(1,0),(0,-1),2.10,1.35,2.61,True,False)]
    cut_windows(body,specs,r)
    # Three genuinely folded north-light roof bays with open glazed risers.
    for bay in range(3):
        a=-4.8+bay*3.2;b=a+3.2
        xs=[]
        for k in range(9):
            x=-5.96+k*1.49
            xs.extend([(x,0),(x+.025,.022),(x+.055,.022),(x+.08,0)]if k<8 else[(x,0)])
        n=len(xs);v=[]
        for bottom in [False,True]:
            for y in [a-.10,b+.055]:
                z=3.20+(y-a)*.25
                v.extend((x,y,z+fold-(.12 if bottom else 0))for x,fold in xs)
        faces=[]
        for i in range(n-1):faces.extend([(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),(i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)])
        faces.extend([(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)])
        mesh('continuous_folded_standing_seam_roof',v,faces,'zinc',r,0)
        for x,normal in [(-5.75,(1,0)),(5.75,(-1,0))]:prism('actual_sawtooth_masonry_end',[(a,3.10),(b,3.10),(b,3.88)],(x,0),(0,1),normal,(0,.30),'brick',r,.008)
        # The glass itself closes each daylight riser; no solid wall hides it.
        for k in range(6):
            x=-4.75+k*1.90
            prism('sawtooth_recessed_daylight_glass',H.rectangle(1.78,3.23,3.89),(x,b),(1,0),(0,-1),(.01,.045),'glass',r,0)
            H.ring('sawtooth_steel_glazing_frame',H.rectangle(1.88,3.19,3.93),H.rectangle(1.78,3.23,3.89),(x,b),(1,0),(0,-1),(-.025,.06),'zinc',r)
    # A continuous tapered extraction stack: real hollow duct/neck and cowl.
    chimneyPoly=[(3.4+.47*math.cos(i*math.tau/8),2.6+.47*math.sin(i*math.tau/8))for i in range(8)]
    duct=H.shell('hollow_octagonal_kitchen_extraction_stack',chimneyPoly,[(3.0,0),(4.6,.05),(5.55,.05)],.07,None,r);duct.data.materials.append(K.M['v6_zinc']);H.finish(duct,.008)
    cowlProfile=[(0,5.74),(.70,5.48),(.70,5.40),(0,5.65),(-.70,5.40),(-.70,5.48)]
    prism('formed_extraction_rain_cowl',cowlProfile,(3.4,2.6),(1,0),(0,1),(-.50,.50),'zinc',r,.009)
    for x in [3.05,3.75]:H.bar('cowl_load_support',[(x,2.6,5.42),(x,2.6,5.66)],.035,.045,'iron',r)
    # A genuine food handoff sill, not a named sign on a house wall.
    prism('projecting_food_handoff_counter',[(-1.32,.88),(1.32,.88),(1.32,.98),(-1.32,.98)],(-3.35,-4.8),(1,0),(0,1),(-.43,.22),'stone',r,.018)
    r['architectureRevision']=6;r['purpose']='Working kitchen: continuous brick body, three structural sawtooth daylight bays, folded metal roof and hollow extraction stack';r['wallThicknessMetres']=.30;r['apertureCount']=len(specs)+18
    return r

def arched_apertures(body,specs,parent,wallBevel=.01):
    # The sixth field is opening HEIGHT above bottom, not an absolute top Z.
    cutters=[H.prism('arched_construction_void',H.arch(w,b,h,20),at,tan,normal,(-.1,.46),None,parent)for at,tan,normal,w,b,h,kind in specs]
    H.difference(body,cutters,'functional_arched_openings');H.finish(body,wallBevel)
    for at,tan,normal,w,b,h,kind in specs:
        H.ring('continuous_curved_masonry_reveal',H.arch(w+.22,b-.09,h+.19,20),H.arch(w-.01,b+.01,h-.02,20),at,tan,normal,(-.05,.19),'stone',parent)
        H.ring('recessed_arched_steel_frame',H.arch(w-.03,b+.02,h-.04,20),H.arch(w-.14,b+.075,h-.15,20),at,tan,normal,(.22,.28),'iron',parent)
        prism('arched_recessed_backing',H.arch(w-.14,b+.075,h-.15,20),at,tan,normal,(.29,.32),'iron'if kind=='vent'else'glass',parent,0)
        if kind=='vent':
            radius=w/2-.08;spring=b+h-w/2
            for i in range(int((h-.22)/.15)):
                z=b+.13+i*.15;half=radius if z<=spring else math.sqrt(max(.001,radius*radius-(z-spring)**2))
                # Each folded blade sits inside the actual open masonry reveal.
                prism('formed_ventilation_louvre_blade',[(-.055,z-.025),(.065,z+.035),(.075,z+.02),(-.045,z-.04)],at,normal,tan,(-half,half),'zinc',parent,0)
        else:
            H.bar('arched_double_door_meeting_stile',[(at[0]+normal[0]*.26,at[1]+normal[1]*.26,z)for z in [b+.08,b+h-.08]],.035,.045,'iron',parent)
            if kind=='door':
                for x in [-.16,.16]:H.bar('arched_door_pull',[(at[0]+tan[0]*x+normal[0]*.12,at[1]+tan[1]*x+normal[1]*.12,z)for z in [b+.95,b+1.48]],.025,.04,'copper',parent)

def electrical_room():
    palette('electrical',{'stone':(.94,.85,.67,1),'roof':(.30,.47,.53,1),'copper':(.27,.42,.36,1)});brick_material();zinc_material();r=K.root('designed_arched_power_house_architecture_v6')
    poly=[(-3.7,-3.35),(-1.15,-3.35),(-1.15,-3.10),(1.15,-3.10),(1.15,-3.35),(3.7,-3.35),(3.7,3.35),(-3.7,3.35)]
    body=shell('electrical_thick_brick_enclosure',poly,.025,3.66,.30,'brick',r)
    specs=[((0,-3.10),(1,0),(0,1),1.82,.035,2.96,'door')]
    specs +=[((x,-3.35),(1,0),(0,1),1.45,.55,2.63,'vent')for x in [-2.45,2.45]]
    specs +=[((x,y),(0,1),(1 if x<0 else-1,0),1.36,.75,2.42,'vent')for x in [-3.7,3.7]for y in [-1.3,1.3]]
    arched_apertures(body,specs,r)
    # A continuous masonry plinth and fitted hipped roof, rather than a house
    # with equipment pasted to its facade. Tall louvres express heat rejection.
    hip_roof('power_house_fitted_slate_roof',[(-3.93,-3.57),(3.93,-3.57),(3.93,3.57),(-3.93,3.57)],3.71,1.02,1,r)
    band=H.shell('continuous_power_house_masonry_cornice',poly,[(3.40,-.035),(3.48,-.09),(3.62,-.09),(3.68,-.02)],.20,'stone',r);H.finish(band,.008)
    for x in [-3.73,3.73]:
        for y in [-3.38,3.38]:
            prism('bonded_corner_masonry_pier',H.rectangle(.28,.025,3.40),(x,y),(1,0),(0,1),(-.12,.12),'stone',r,.012)
    r['architectureRevision']=6;r['purpose']='Garden utility power house: actual arched ventilation openings, recessed service doors, thick brick enclosure and fitted hipped slate roof';r['wallThicknessMetres']=.30;r['apertureCount']=len(specs)
    return r

def laundry_room():
    palette('laundry',{'ivory':(.91,.81,.68,1),'mint':(.46,.75,.80,1),'copper':(.38,.64,.70,1)});zinc_material();r=K.root('designed_barrel_vault_laundry_architecture_v6')
    poly=[(-3.75,-3.75),(-1.15,-3.75),(-1.15,-3.38),(1.15,-3.38),(1.15,-3.75),(3.75,-3.75),(3.75,3.75),(-3.75,3.75)]
    body=shell('laundry_continuous_barrel_end_walls',poly,.025,3.10,.26,'ivory',r)
    def crown(x):return 3.18+1.02*math.sqrt(max(0,1-(x/4.02)**2))
    # Add curve samples to both actual end walls before Boolean cuts. This
    # produces a fitted masonry roof closure, not a separate floating cap.
    bm=bmesh.new();bm.from_mesh(body.data)
    top=[e for e in bm.edges if all(v.co.z>3.09 for v in e.verts)and abs(e.verts[0].co.y-e.verts[1].co.y)<.01 and e.calc_length()>.6]
    if top:bmesh.ops.subdivide_edges(bm,edges=top,cuts=12,use_grid_fill=False)
    for v in bm.verts:
        if v.co.z>3.09:v.co.z=crown(v.co.x)-.055
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();body.data.update()
    specs=[('laundry_recessed_entry',(0,-3.38),(1,0),(0,1),1.82,.035,2.80,False,True)]
    specs +=[('laundry_front_workroom_window',(x,-3.75),(1,0),(0,1),1.76,.32,2.82,False,False)for x in [-2.48,2.48]]
    specs +=[('laundry_high_privacy_window',(x,y),(0,1),(1 if x<0 else-1,0),1.56,1.58,2.84,True,False)for x in [-3.75,3.75]for y in [-1.6,1.4]]
    specs +=[('laundry_rear_daylight',(x,3.75),(1,0),(0,-1),1.80,1.28,2.85,True,False)for x in [-2.3,0,2.3]]
    cut_windows(body,specs,r)
    xs=[-3.96+i*7.92/40 for i in range(41)];section=[(x,crown(x))for x in xs]+[(x,crown(x)-.12)for x in reversed(xs)]
    roof=prism('continuous_thick_barrel_vault_roof',section,(0,0),(1,0),(0,1),(-3.97,3.97),'zinc',r,.005);surface_uv(roof)
    for y in [-3.97,3.97]:H.bar('curved_vault_end_flashing',[(x,y,crown(x)-.03)for x in xs],.075,.10,'copper',r)
    for y in [-3,-1.5,0,1.5,3]:H.bar('barrel_roof_folded_seam',[(x,y,crown(x)+.012)for x in xs],.018,.025,'zinc',r)
    clear=bpy.data.materials.new('architecture6_laundry_clear_glass');clear.use_nodes=True;clear['surfaceTint']=[.70,.85,.92,.12];bs=clear.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.70,.85,.92,1);bs.inputs['Alpha'].default_value=.12;bs.inputs['Roughness'].default_value=.10;clear.surface_render_method='DITHERED'
    for o in r.children_recursive:
        if o.type=='MESH'and o.name.startswith('laundry_front_workroom_window_actual_glass_depth'):
            o.data.materials.clear();o.data.materials.append(clear)
    # A shallow, closed display of the actual laundry workroom is visible
    # through clear front glazing. Machines remain indoors, at floor level.
    prism('laundry_continuous_internal_floor',H.rectangle(7.42,.025,.09),(0,0),(1,0),(0,1),(-3.72,3.72),'stone',r,.004)
    for x in [-2.48,2.48]:
        at=(x,-2.73);outer=[(.29*math.cos(i*math.tau/32),.67+.29*math.sin(i*math.tau/32))for i in range(32)];inner=[(.225*math.cos(i*math.tau/32),.67+.225*math.sin(i*math.tau/32))for i in range(32)]
        prism('rounded_indoor_washer_housing',H.rectangle(.88,.09,1.22),(x,-2.73),(1,0),(0,1),(0,.72),'mint',r,.035)
        H.ring('inset_laundry_drum_steel_rim',outer,inner,at,(1,0),(0,1),(-.025,.04),'zinc',r)
        prism('dark_washing_drum_glass',inner,at,(1,0),(0,1),(-.02,-.01),'iron',r,0)
        prism('washer_recessed_control_strip',H.rectangle(.70,1.04,1.13),at,(1,0),(0,1),(-.025,-.01),'iron',r,.005)
    r['architectureRevision']=6;r['purpose']='Low vaulted laundry pavilion: fitted curved masonry ends, continuous metal barrel roof, privacy side lights and recessed workroom glazing';r['wallThicknessMetres']=.26;r['apertureCount']=len(specs)
    return r

def mansard_cap(poly,z,parent):
    n=len(poly);v=[];rings=[(z,0),(z+.13,-.025),(z+1.02,.85),(z+1.16,1.15)]
    for height,inset in rings:v.extend((x,y,height)for x,y in H.offset(poly,inset))
    count=len(v)
    for height,inset in rings:v.extend((x,y,height-.12)for x,y in H.offset(poly,inset))
    faces=[]
    for k in range(len(rings)-1):
        for i in range(n):
            a=k*n+i;b=k*n+(i+1)%n;c=(k+1)*n+(i+1)%n;d=(k+1)*n+i;faces.extend([(a,b,c,d),(a+count,d+count,c+count,b+count)])
    for i in range(n):j=(i+1)%n;faces.append((i,i+count,j+count,j))
    faces +=[tuple(range(3*n,4*n)),tuple(reversed(range(count+3*n,count+4*n)))]
    o=mesh('continuous_civic_mansard_roof',v,faces,'roof',parent,.008);surface_uv(o)
    H.bar('civic_continuous_eave',[(x,y,z+.02)for x,y in poly+[poly[0]]],.08,.10,'stone',parent)
    return o

def management_office():
    palette('management',{'ivory':(.88,.66,.52,1),'stone':(.96,.87,.70,1),'roof':(.28,.45,.62,1),'copper':(.40,.65,.63,1)})
    r=K.root('designed_civic_reception_office_architecture_v6')
    poly=[(-4.7,-3.65),(-1.55,-3.65),(-1.55,-3.96),(1.55,-3.96),(1.55,-3.65),(4.7,-3.65),(4.7,3.65),(-4.7,3.65)]
    body=shell('civic_office_continuous_reception_wall',poly,.025,4.10,.29,'ivory',r)
    specs=[((0,-3.96),(1,0),(0,1),2.12,.035,3.48,'door')]
    # A tall central public reception portal, flanked by two wide office bays.
    arched_apertures(body,specs,r)
    windows=[('reception_side_workroom_window',(x,-3.65),(1,0),(0,1),2.10,.78,3.16,False,False)for x in [-3.10,3.10]]
    windows +=[('office_long_side_casement',(x,y),(0,1),(1 if x<0 else-1,0),1.62,1.10,3.02,False,False)for x in [-4.7,4.7]for y in [-1.5,1.2]]
    windows +=[('office_rear_casement',(x,3.65),(1,0),(0,-1),1.82,1.15,3.08,False,False)for x in [-3.0,0,3.0]]
    cut_windows(body,windows,r)
    # The public entrance is a constructed portico, not a pasted roof card.
    for x in [-1.48,1.48]:
        column('civic_portico_profiled_column',x,-5.05,.025,3.28,r)
    pediment=[(-1.84,3.39),(0,4.12),(1.84,3.39),(1.84,3.23),(0,3.96),(-1.84,3.23)]
    prism('civic_portico_continuous_pediment',pediment,(0,0),(1,0),(0,1),(-5.22,-3.62),'stone',r,.008)
    H.bar('civic_portico_rear_tie',[(-1.65,-3.79,3.27),(1.65,-3.79,3.27)],.13,.17,'stone',r)
    mansard_cap([(-4.93,-3.88),(-1.79,-3.88),(-1.79,-4.19),(1.79,-4.19),(1.79,-3.88),(4.93,-3.88),(4.93,3.88),(-4.93,3.88)],4.15,r)
    # Bonded horizontal courses and a real stepped cornice establish civic
    # proportions without adding a fake second floor or arbitrary ornament.
    for lo,hi,inset in [(.10,.27,-.025),(3.64,3.78,-.035),(3.95,4.13,-.07)]:
        band=H.shell('continuous_civic_stone_course',poly,[(lo,inset),(hi,inset)],.16,'stone',r)
        if lo<.5:H.difference(band,[H.prism('civic_plinth_actual_door_clearance',H.rectangle(2.12,-.1,.5),(0,-3.96),(1,0),(0,1),(-.2,.43),None,r)],'plinth_opened_at_public_door')
        H.finish(band,.006)
    r['architectureRevision']=6;r['purpose']='Civic park management reception: high arched public portal, profiled column portico, broad workroom windows, continuous mansard and bonded stone courses';r['wallThicknessMetres']=.29;r['apertureCount']=len(specs)+len(windows)
    return r

def ticket_booth():
    palette('ticket',{'ivory':(.91,.72,.50,1),'mint':(.69,.39,.42,1),'roof':(.39,.69,.67,1),'copper':(.85,.61,.30,1)});zinc_material((.34,.76,.69,1))
    r=K.root('designed_octagonal_transaction_pavilion_v6')
    poly=[(-1.65,-2.82),(1.65,-2.82),(2.32,-2.15),(2.32,2.15),(1.65,2.82),(-1.65,2.82),(-2.32,2.15),(-2.32,-2.15)]
    body=shell('ticket_booth_continuous_chamfered_wall',poly,.025,3.02,.22,'mint',r)
    a=math.sqrt(.5)
    specs=[('front_ticket_handoff',(0,-2.82),(1,0),(0,1),2.60,1.02,2.57,False,False),('ticket_side_transaction',(-2.32,-.9),(0,1),(1,0),1.58,1.02,2.57,False,False),('ticket_side_transaction',(2.32,-.9),(0,1),(-1,0),1.58,1.02,2.57,False,False),('ticket_staff_rear_entry',(0,2.82),(1,0),(0,-1),1.05,.035,2.61,False,True)]
    specs +=[('ticket_chamfered_corner_glazing',(-1.985,-2.485),(a,-a),(a,a),.60,1.02,2.57,False,False),('ticket_chamfered_corner_glazing',(1.985,-2.485),(a,a),(-a,a),.60,1.02,2.57,False,False)]
    cut_windows(body,specs,r)
    for o in r.children_recursive:
        if o.type=='MESH'and 'actual_glass_depth'in o.name and 'staff_rear_entry'not in o.name:
            for v in o.data.vertices:
                if v.co.z<1.24:v.co.z=1.24
            o.data.update()
    # A cut handoff slot and projecting counter beneath deep glazed frames.
    prism('front_transaction_counter',[(-1.46,.94),(1.46,.94),(1.46,1.035),(-1.46,1.035)],(0,-2.82),(1,0),(0,1),(-.40,.28),'stone',r,.018)
    for x in [-2.32,2.32]:prism('side_transaction_counter',[(-.92,.94),(.92,.94),(.92,1.035),(-.92,1.035)],(x,-.9),(0,1),(1 if x<0 else-1,0),(-.35,.26),'stone',r,.015)
    # The pavilion roof is one watertight, elliptical bell profile with a
    # returned soffit; it fits the kiosk rather than being intersected boxes.
    profile=[(1.12,3.03),(1.16,3.16),(1.02,3.28),(.92,3.68),(.67,4.23),(.22,4.60),(.055,4.64)];n=32;v=[]
    for inner in [False,True]:
        for radius,z in profile:v.extend((2.32*radius*math.cos(i*math.tau/n),2.82*radius*math.sin(i*math.tau/n),z-(.10 if inner else 0))for i in range(n))
    count=len(profile)*n;f=[]
    for k in range(len(profile)-1):
        for i in range(n):a=k*n+i;b=k*n+(i+1)%n;c=(k+1)*n+(i+1)%n;d=(k+1)*n+i;f.extend([(a,b,c,d),(a+count,d+count,c+count,b+count)])
    for i in range(n):j=(i+1)%n;f.append((i,i+count,j+count,j))
    f.extend([tuple(range(count-n,count)),tuple(reversed(range(2*count-n,2*count)))])
    roof=mesh('single_formed_bell_ticket_pavilion_roof',v,f,'zinc',r,.006);surface_uv(roof)
    for face in roof.data.polygons:face.use_smooth=True
    for i in range(8):
        angle=i*math.tau/8;H.bar('bell_roof_constructed_rib',[(2.32*radius*math.cos(angle),2.82*radius*math.sin(angle),z+.012)for radius,z in profile],.025,.035,'copper',r)
    base=H.shell('continuous_ticket_stone_plinth',poly,[(.025,-.01),(.18,-.015)],.18,'stone',r);H.difference(base,[H.prism('ticket_plinth_staff_door_clearance',H.rectangle(1.05,-.1,.3),(0,2.82),(1,0),(0,-1),(-.1,.43),None,r)],'plinth_opened_at_staff_door');H.finish(base,.008)
    r['architectureRevision']=6;r['purpose']='Octagonal park ticket pavilion with front and side transaction windows, deep return counter, rear staff entrance and fitted formed bell roof';r['wallThicknessMetres']=.22;r['apertureCount']=len(specs)
    return r

def supply_store():
    palette('supply',{'ivory':(.73,.66,.46,1),'wood':(.64,.45,.29,1),'copper':(.38,.47,.50,1)});brick_material();zinc_material((.46,.56,.58,1));r=K.root('designed_rail_door_supply_store_v6')
    poly=[(-4.7,-3.7),(-1.65,-3.7),(-1.65,-3.46),(0,-3.46),(1.65,-3.46),(1.65,-3.7),(4.7,-3.7),(4.7,3.7),(0,3.7),(-4.7,3.7)]
    body=shell('supply_store_thick_gabled_brick_walls',poly,.025,3.35,.28,'brick',r)
    for v in body.data.vertices:
        if v.co.z>3.34:v.co.z=4.75-abs(v.co.x)*1.45/4.88
    body.data.update()
    specs=[('wide_sliding_goods_door',(0,-3.46),(1,0),(0,1),2.92,.035,3.02,False,True)]
    specs +=[('store_high_daylight_slot',(x,y),(0,1),(1 if x<0 else-1,0),1.64,1.92,2.85,False,False)for x in [-4.7,4.7]for y in [-1.5,1.6]]
    specs +=[('rear_stock_daylight',(x,3.7),(1,0),(0,-1),1.70,1.62,2.85,False,False)for x in [-2.7,2.7]]
    cut_windows(body,specs,r)
    for o in r.children_recursive:
        if o.type=='MESH'and o.name.startswith('wide_sliding_goods_door_actual_glass_depth'):o.data.materials.clear();o.data.materials.append(K.M['v6_wood'])
    profile=[(-4.94,3.38),(0,4.88),(4.94,3.38),(4.90,3.23),(0,4.72),(-4.90,3.23)]
    roof=prism('supply_continuous_folded_metal_gable',profile,(0,0),(1,0),(0,1),(-3.94,3.94),'zinc',r,.008);surface_uv(roof)
    for y in [-3.94,3.94]:H.bar('supply_roof_structural_fascia',[(-4.94,y,3.34),(0,y,4.84),(4.94,y,3.34)],.07,.10,'zinc',r)
    H.bar('actual_sliding_door_overhead_track',[(-2.35,-3.75,3.19),(2.35,-3.75,3.19)],.08,.10,'iron',r)
    for x in [-1.1,-.35,.35,1.1]:H.bar('sliding_leaf_track_hanger',[(x,-3.67,2.80),(x,-3.75,3.19)],.045,.045,'iron',r)
    for x in [-.74,.74]:H.bar('goods_door_diagonal_brace',[(x-.55,-3.23,.24),(x+.55,-3.23,2.76)],.055,.045,'iron',r)
    r['architectureRevision']=6;r['purpose']='Functional stock store: tall clear-span gabled shell, broad rail-hung timber loading doors, recessed high stockroom windows and fitted folded metal roof';r['wallThicknessMetres']=.28;r['apertureCount']=len(specs)
    return r

def service_lounge():
    palette('lounge',{'ivory':(.89,.81,.58,1),'mint':(.54,.73,.57,1),'roof':(.41,.64,.59,1),'copper':(.33,.56,.46,1)});r=K.root('designed_sheltered_staff_loggia_v6')
    poly=[(-4.20,-2.32),(-1.2,-2.32),(-1.2,-2.08),(1.2,-2.08),(1.2,-2.32),(4.2,-2.32),(4.2,3.7),(-4.2,3.7)]
    body=shell('staff_lounge_actual_recessed_enclosure',poly,.025,3.13,.26,'ivory',r)
    specs=[('staff_lounge_step_free_entry',(0,-2.08),(1,0),(0,1),1.82,.035,2.80,False,True)]
    specs +=[('loggia_broad_seating_window',(x,-2.32),(1,0),(0,1),1.98,.55,2.82,False,False)for x in [-2.75,2.75]]
    specs +=[('lounge_side_window',(x,y),(0,1),(1 if x<0 else-1,0),1.65,.92,2.79,False,False)for x in [-4.2,4.2]for y in [-.3,2.1]]
    specs +=[('lounge_rear_window',(x,3.7),(1,0),(0,-1),1.82,1.0,2.79,False,False)for x in [-2.7,0,2.7]]
    cut_windows(body,specs,r)
    # A continuous fitted hip roof covers the occupied room AND a real deep
    # outdoor loggia; the front edge has resolved posts and horizontal ties.
    hip_roof('single_staff_loggia_overall_roof',[(-4.45,-5.27),(4.45,-5.27),(4.45,3.95),(-4.45,3.95)],3.22,1.12,1,r)
    for x in [-4.05,-1.18,1.18,4.05]:column('sheltered_loggia_profiled_column',x,-5.02,.025,3.15,r)
    H.bar('continuous_loggia_front_head_beam',[(-4.24,-5.02,3.13),(4.24,-5.02,3.13)],.15,.16,'wood',r)
    for x in [-4.05,4.05]:H.bar('loggia_return_head_beam',[(x,-5.02,3.13),(x,-2.26,3.13)],.13,.15,'wood',r)
    for x in [-2.65,2.65]:
        table=K.curved_family('meeting_table');table.parent=r;table.location=(x,-3.75,.025);table.scale=(.42,.60,1)
        for side in [-1,1]:
            chair=K.curved_family('chair');chair.parent=r;chair.location=(x+side*.82,-3.75,.025);chair.rotation_euler.z=-side*math.pi/2
    r['architectureRevision']=6;r['purpose']='Recessed staff sitting room with genuinely deep covered outdoor loggia, resolved timber ties and columns, seating around tables and continuous fitted roof';r['wallThicknessMetres']=.26;r['apertureCount']=len(specs)
    return r

def hotel_multiuse():
    palette('gathering_hall',{'ivory':(.92,.81,.69,1),'stone':(.96,.88,.75,1),'copper':(.79,.58,.31,1)});zinc_material((.57,.77,.73,1));r=K.root('designed_clear_span_garden_gathering_hall_v6')
    poly=[(-5.7,-3.6),(-5.2,-4.5),(-4.4,-4.8),(4.4,-4.8),(5.2,-4.5),(5.7,-3.6),(5.7,3.6),(5.2,4.5),(4.4,4.8),(-4.4,4.8),(-5.2,4.5),(-5.7,3.6)]
    body=shell('gathering_hall_continuous_chamfered_masonry',poly,.025,3.72,.29,'ivory',r)
    specs=[((0,-4.8),(1,0),(0,1),2.48,.035,3.43,'door')]
    specs +=[((x,-4.8),(1,0),(0,1),1.98,.58,2.92,'window')for x in [-3.37,3.37]]
    specs +=[((x,y),(0,1),(1 if x<0 else-1,0),2.12,.58,2.92,'window')for x in [-5.7,5.7]for y in [-2.20,1.95]]
    specs +=[((x,4.8),(1,0),(0,-1),2.12,.58,2.92,'window')for x in [-3.2,0,3.2]]
    arched_apertures(body,specs,r)
    # Loft a constant-thickness broad-span roof with a deliberate domed
    # section. All rings follow this hall's own chamfered footprint.
    profile=[(1.035,3.74),(1.055,3.91),(.86,4.64),(.60,5.39),(.25,5.92),(.055,6.04)];n=len(poly);v=[]
    for inner in [False,True]:
        for scale,z in profile:v.extend((x*scale,y*scale,z-(.14 if inner else 0))for x,y in poly)
    count=n*len(profile);faces=[]
    for k in range(len(profile)-1):
        for i in range(n):a=k*n+i;b=k*n+(i+1)%n;c=(k+1)*n+(i+1)%n;d=(k+1)*n+i;faces.extend([(a,b,c,d),(a+count,d+count,c+count,b+count)])
    for i in range(n):j=(i+1)%n;faces.append((i,i+count,j+count,j))
    faces.extend([tuple(range(count-n,count)),tuple(reversed(range(count*2-n,count*2)))])
    roof=mesh('single_fitted_gathering_hall_dome_shell',v,faces,'zinc',r,.008);surface_uv(roof)
    for p in roof.data.polygons:p.use_smooth=True
    for x,y in poly:H.bar('gathering_hall_structural_roof_rib',[(x*scale,y*scale,z+.012)for scale,z in profile],.045,.055,'copper',r)
    H.bar('gathering_hall_continuous_cornice',[(x*1.015,y*1.015,3.68)for x,y in poly+[poly[0]]],.14,.16,'stone',r)
    # Broad arrival canopy responds to a gathering venue, with a 2.48 m door
    # and clear central approach rather than a domestic single doorway.
    xs=[-1.8+i*3.6/16 for i in range(17)];section=[(x,3.03+.29*(1-(x/1.8)**2))for x in xs]+[(x,2.94+.29*(1-(x/1.8)**2))for x in reversed(xs)]
    prism('gathering_hall_formed_arrival_canopy',section,(0,0),(1,0),(0,1),(-6.36,-4.65),'zinc',r,.006)
    for x in [-1.62,1.62]:column('gathering_hall_arrival_column',x,-6.15,.025,3.03,r)
    r['architectureRevision']=6;r['purpose']='Hotel gathering pavilion with broad clear-span domed roof, continuous chamfered wall, deep arched glazing and wide sheltered public arrival';r['wallThicknessMetres']=.29;r['apertureCount']=len(specs)
    return r

def cold_store():
    palette('cold_store',{'ivory':(.74,.84,.87,1),'stone':(.84,.86,.78,1),'copper':(.31,.49,.56,1),'frost':(.76,.83,.84,1)});zinc_material((.49,.65,.69,1));r=K.root('designed_insulated_carnival_cold_store_v6')
    poly=[(-3.7,-3.35),(-3.35,-3.7),(3.35,-3.7),(3.7,-3.35),(3.7,3.35),(3.35,3.7),(-3.35,3.7),(-3.7,3.35)]
    body=shell('cold_store_continuous_chamfered_insulated_enclosure',poly,.025,3.56,.24,'ivory',r)
    cutters=[H.prism('thermal_service_door_actual_void',H.rectangle(1.92,-.1,2.91),(0,-3.7),(1,0),(0,1),(-.1,.44),None,r)]
    for y,normal in [(-3.7,(0,1)),(3.7,(0,-1))]:
        for x in [-2.4,-1.2,0,1.2,2.4]:
            if y<0 and abs(x)<1:continue
            cutters.append(H.prism('actual_insulated_panel_joint',H.rectangle(.018,.13,3.43),(x,y),(1,0),normal,(-.015,.014),None,r))
    for x,normal in [(-3.7,(1,0)),(3.7,(-1,0))]:
        for y in [-2.4,-1.2,0,1.2,2.4]:cutters.append(H.prism('actual_insulated_side_joint',H.rectangle(.018,.13,3.43),(x,y),(0,1),normal,(-.015,.014),None,r))
    H.difference(body,cutters,'actual_thermal_door_and_panel_rebates');H.finish(body,.008)
    H.ring('thermal_door_deep_compression_frame',H.rectangle(2.12,-.015,3.02),H.rectangle(1.86,.045,2.87),(0,-3.7),(1,0),(0,1),(-.045,.22),'zinc',r)
    H.ring('thermal_door_continuous_compression_gasket',H.rectangle(1.86,.045,2.87),H.rectangle(1.78,.085,2.83),(0,-3.7),(1,0),(0,1),(.08,.15),'iron',r)
    prism('thick_bevelled_thermal_service_door',H.rectangle(1.77,.09,2.825),(0,-3.7),(1,0),(0,1),(.10,.25),'frost',r,.032)
    H.bar('thermal_door_compression_lever',[(.55,-3.66,1.22),(.63,-3.78,1.22),(.63,-3.78,1.56),(.55,-3.66,1.56)],.045,.05,'iron',r)
    for z in [.62,2.22]:H.bar('thermal_door_structural_hinge',[(-.98,-3.73,z),(-.72,-3.73,z)],.10,.065,'zinc',r)
    cap=H.shell('continuous_cold_store_returned_roof_coping',poly,[(3.50,-.07),(3.62,-.10),(3.72,-.04)],.28,'zinc',r);H.finish(cap,.008)
    # Roof is a real shallow pitched sheet inside the returned parapet.
    prism('cold_store_sealed_fall_roof',[(-3.7,3.55),(3.7,3.65),(3.7,3.77),(-3.7,3.67)],(0,0),(0,1),(1,0),(-3.7,3.7),'zinc',r,.006)
    # Model the refrigeration condenser as a housing with an actual fan recess,
    # folded rotor blades and guard. No fan disc is pasted onto a solid box.
    at=(4.43,1.2);tan=(0,1);normal=(-1,0);zmid=1.45
    housing=prism('formed_refrigeration_condenser_housing',H.rectangle(1.46,.72,2.18),at,tan,normal,(-.04,.56),'frost',r,.045)
    circle=[(.52*math.cos(i*math.tau/32),zmid+.52*math.sin(i*math.tau/32))for i in range(32)]
    H.difference(housing,[H.prism('condenser_actual_fan_pocket',circle,at,tan,normal,(-.12,.42),None,r)],'actual_condenser_fan_recess');H.finish(housing,.004)
    for k in range(3):
        angle=k*math.tau/3;shape=[(.04,.04),(.08,.36),(.22,.45),(.32,.34),(.19,.07)];outline=[(x*math.cos(angle)-z*math.sin(angle),zmid+x*math.sin(angle)+z*math.cos(angle))for x,z in shape]
        prism('curved_refrigeration_fan_rotor_blade',outline,at,tan,normal,(.30,.34),'iron',r,.006)
    for radius in [.19,.34,.48]:H.bar('condenser_continuous_fan_guard',[(at[0]-.04,at[1]+radius*math.cos(i*math.tau/32),zmid+radius*math.sin(i*math.tau/32))for i in range(33)],.015,.018,'iron',r)
    for angle in [0,math.pi/2]:H.bar('condenser_radial_guard_tie',[(at[0]-.04,at[1]+d*math.cos(angle),zmid+d*math.sin(angle))for d in [-.49,.49]],.016,.018,'iron',r)
    for y in [.68,1.72]:H.bar('condenser_wall_mounting_bracket',[(3.67,y,.68),(4.40,y,.68),(4.40,y,.91)],.055,.07,'zinc',r)
    r['architectureRevision']=6;r['purpose']='Carnival back-of-house cold storage: continuous insulated panel rebates, thick gasketed compression door, sealed low roof and actual recessed condenser fan/guard';r['wallThicknessMetres']=.24;r['apertureCount']=1
    return r

def elliptical_arch(width,bottom,spring,top,n=32):
    return[(-width/2,bottom),(width/2,bottom),(width/2,spring)]+[(width/2*math.cos(i*math.pi/n),spring+(top-spring)*math.sin(i*math.pi/n))for i in range(1,n+1)]

def performance_stage():
    palette('festival_stage',{'ivory':(.88,.72,.55,1),'stone':(.96,.84,.60,1),'copper':(.78,.51,.27,1)});zinc_material((.62,.74,.70,1));r=K.root('designed_festival_proscenium_stage_v6')
    floorMaterial=K.M['v6_wood'].copy();floorMaterial.name='architecture6_stage_matte_wood';bs=floorMaterial.node_tree.nodes.get('Principled BSDF')
    for link in list(bs.inputs['Roughness'].links):floorMaterial.node_tree.links.remove(link)
    bs.inputs['Roughness'].default_value=.76;K.M['v6_wood']=floorMaterial;K.M['hotel_wood']=floorMaterial
    # Continuous thick auditorium walls follow a fitted barrel section. The
    # entire proscenium is an actual opening into the covered performance deck.
    xs=[-7.60+i*15.2/24 for i in range(25)];poly=[(x,-8.60)for x in xs]+[(x,8.60)for x in reversed(xs)]
    def crown(x):return 5.68+1.80*math.sqrt(max(0,1-(x/7.90)**2))
    body=shell('stage_continuous_barrel_end_and_side_walls',poly,.025,5.68,.32,'ivory',r)
    for v in body.data.vertices:
        if v.co.z>5.67:v.co.z=crown(v.co.x)-.14
    body.data.update()
    outer=elliptical_arch(13.05,.02,3.12,6.30);inner=elliptical_arch(11.20,.12,3.12,5.72)
    cutters=[H.prism('whole_stage_proscenium_void',elliptical_arch(11.20,-.1,3.12,5.72),(0,-8.60),(1,0),(0,1),(-.18,.55),None,r),H.prism('rear_stage_service_door_void',H.rectangle(1.40,-.1,2.78),(0,8.60),(1,0),(0,-1),(-.15,.55),None,r)]
    H.difference(body,cutters,'actual_stage_proscenium_and_rear_access');H.finish(body,.008)
    H.ring('thick_elliptical_proscenium_structural_arch',outer,inner,(0,-8.60),(1,0),(0,1),(-.20,.20),'stone',r)
    window('stage_rear_service_door',(0,8.60),(1,0),(0,-1),1.40,.035,2.78,r,False,True)
    roofXs=[-7.84+i*15.68/48 for i in range(49)];profile=[(x,crown(x))for x in roofXs]+[(x,crown(x)-.18)for x in reversed(roofXs)]
    roof=prism('single_closed_barrel_performance_roof',profile,(0,0),(1,0),(0,1),(-8.87,8.87),'zinc',r,.006);surface_uv(roof)
    for p in roof.data.polygons:p.use_smooth=True
    for y in [-8.87,-4.45,0,4.45,8.87]:H.bar('stage_roof_structural_barrel_rib',[(x,y,crown(x)+.012)for x in roofXs],.055,.07,'copper',r)
    prism('continuous_covered_stage_deck',H.rectangle(15.10,.025,.12),(0,0),(1,0),(0,1),(-8.65,8.54),'wood',r,.012)
    velvet=K.M['cloth'].copy();velvet.name='architecture6_festival_stage_velvet';velvet['surfaceTint']=[.42,.055,.08,1];K.M['v6_velvet']=velvet
    # A solid dyed textile uses its actual fibre normal/roughness maps. The
    # previous very dark albedo multiplied by a second dye hid every fold.
    bs=velvet.node_tree.nodes.get('Principled BSDF')
    for link in list(bs.inputs['Base Color'].links):velvet.node_tree.links.remove(link)
    bs.inputs['Base Color'].default_value=(.42,.055,.08,1)
    for side in [-1,1]:
        # Closed thin folded cloth, with a curved bottom and tucked return.
        n=24;v=[]
        for back in [False,True]:
            for top in [False,True]:
                for i in range(n+1):
                    u=i/n;x=side*(4.72+u*1.85);y=-8.10+.11*math.sin(u*math.tau*5)+(.025 if back else 0);z=5.74 if top else .14+.12*math.sin(u*math.pi)**2;v.append((x,y,z))
        k=n+1;f=[]
        for i in range(n):f.extend([(i,i+1,k+i+1,k+i),(2*k+i,3*k+i,3*k+i+1,2*k+i+1),(i,2*k+i,2*k+i+1,i+1),(k+i,k+i+1,3*k+i+1,3*k+i)])
        f +=[(0,k,3*k,2*k),(k-1,3*k-1,4*k-1,2*k-1)];curtain=mesh('actual_folded_stage_wing_curtain',v,f,'velvet',r,0)
        for p in curtain.data.polygons:p.use_smooth=True
    H.bar('proscenium_curtain_track',[(-6.58,-8.10,5.78),(6.58,-8.10,5.78)],.045,.055,'iron',r)
    # A transverse lighting bar and two resolved diagonal structural braces
    # retain a readable theatre section without dense decorative objects.
    H.bar('stage_performance_lighting_bridge',[(-7.22,-3.0,5.42),(7.22,-3.0,5.42)],.12,.14,'iron',r)
    for side in [-1,1]:H.bar('stage_lighting_bridge_structural_brace',[(side*7.22,-3.0,5.42),(side*5.7,-3.0,6.70)],.07,.08,'iron',r)
    # A stage reads as a performance space through its actual hanging cloth
    # and mounted luminaires; a blank dark garage opening is insufficient.
    xx=[-6.4+i*12.8/96 for i in range(97)];n=len(xx);v=[]
    for back in [False,True]:
        for z in [.13,5.50]:v.extend((x,5.75+.12*math.sin(i*math.tau/6)+(.025 if back else 0),z)for i,x in enumerate(xx))
    f=[]
    for i in range(n-1):f.extend([(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),(i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)])
    f +=[(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)];backdrop=mesh('continuous_folded_performance_backdrop',v,f,'velvet',r,0)
    for p in backdrop.data.polygons:p.use_smooth=True
    xx=[-5.5+i*11/64 for i in range(65)];upper=[(x,3.12+2.60*math.sqrt(max(0,1-(x/5.6)**2))-.075)for x in xx];lower=[(x,z-.44-.055*math.cos(i*math.pi/4)**2)for i,(x,z)in enumerate(upper)]
    prism('fitted_scalloped_proscenium_valance',upper+list(reversed(lower)),(0,-8.05),(1,0),(0,1),(0,.025),'velvet',r,0)
    K.M['v6_stage_light']=K.M['light']
    for x in [-5,-2.5,0,2.5,5]:
        lamp=K.root('actual_stage_luminaire',r);lamp.location=(x,-3,5.25);lamp.rotation_euler.x=math.radians(35)
        poly=[(.17*math.cos(i*math.tau/16),.17*math.sin(i*math.tau/16))for i in range(16)]
        head=H.shell('hollow_tapered_stage_lamp_housing',poly,[(0,0),(.29,.02)],.06,'iron',lamp);H.finish(head,.004)
        for name,z0,z1,radius,mat in [('recessed_stage_lamp_lens',.012,.027,.107,'stage_light'),('closed_stage_lamp_rear',.275,.30,.13,'iron')]:
            points=[(radius*math.cos(i*math.tau/16),radius*math.sin(i*math.tau/16),z)for z in [z0,z1]for i in range(16)];faces=[tuple(reversed(range(16))),tuple(range(16,32)),*[(i,(i+1)%16,(i+1)%16+16,i+16)for i in range(16)]];mesh(name,points,faces,mat,lamp,0)
        H.bar('stage_lamp_bridge_yoke',[(x,-3,5.25),(x,-3,5.48)],.025,.035,'iron',r)
    r['architectureRevision']=6;r['purpose']='Festival theatre: actual open elliptical proscenium, continuous fitted barrel shell, covered wooden stage deck, folded wing curtains, rear service access and resolved roof/lighting structure';r['wallThicknessMetres']=.32;r['apertureCount']=2
    import json
    r['presentationLights']=json.dumps([{'id':'StageKey'+str(i),'position':[x,-3,5.12],'target':[x*.35,3.8,1.15],'color':[1,.78,.59,1],'intensity':32,'radius':15,'angle':55,'penumbra':.5,'decay':2,'castShadow':False}for i,x in enumerate([-5,0,5])])
    return r

def dyed_cloth(name,color):
    m=K.M['cloth'].copy();m.name='architecture6_'+name;m['surfaceTint']=color
    bs=m.node_tree.nodes.get('Principled BSDF')
    for link in list(bs.inputs['Base Color'].links):m.node_tree.links.remove(link)
    bs.inputs['Base Color'].default_value=color;K.M['v6_'+name]=m
    return m

def refreshment_store():
    palette('concession',{'ivory':(.94,.81,.63,1),'mint':(.70,.22,.16,1),'stone':(.96,.90,.76,1),'copper':(.35,.64,.60,1)});zinc_material((.36,.62,.57,1));r=K.root('designed_carnival_service_counter_pavilion_v6')
    paper=dyed_cloth('service_paper',(.92,.85,.67,1))
    for node in paper.node_tree.nodes:
        if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.07
    # A low concession frontage: wide genuinely open transaction bays and a
    # centre staff entrance, rather than a dwelling with a name on its wall.
    poly=[(-4.7,-3.6),(4.7,-3.6),(4.7,3.6),(-4.7,3.6)]
    body=shell('concession_continuous_thick_wall',poly,.025,3.28,.26,'mint',r)
    # Match the wall's actual top vertices to the underside of the one-fall
    # roof; a horizontal wall would leave a dark open slot at the rear.
    for v in body.data.vertices:
        if v.co.z>3.279:v.co.z=3.29+(v.co.y+3.76)*.13/7.52
    body.data.update()
    cut_windows(body,[('concession_centre_staff_door',(0,-3.6),(1,0),(0,1),1.40,.035,2.72,False,True),*[( 'concession_side_daylight',(x,1.1),(0,1),(1 if x<0 else-1,0),1.80,1.30,2.62,False,False)for x in [-4.7,4.7]]],r)
    cutters=[H.prism('actual_concession_service_void',H.rectangle(2.5,1.03,2.76),(x,-3.6),(1,0),(0,1),(-.10,.45),None,r)for x in [-2.85,2.85]]
    H.difference(body,cutters,'wide_open_concession_service_bays');H.finish(body,.008)
    for x in [-2.85,2.85]:
        at=(x,-3.6);H.ring('deep_concession_service_jamb',H.rectangle(2.70,.94,2.85),H.rectangle(2.48,1.05,2.74),at,(1,0),(0,1),(-.04,.19),'stone',r)
        # Raised sash leaves an unobstructed 0.8 m service gap. It is not
        # simulated by a glass plane painted across a wall.
        H.ring('raised_concession_sash',H.rectangle(2.45,1.91,2.73),H.rectangle(2.32,1.98,2.66),at,(1,0),(0,1),(.19,.25),'iron',r)
        prism('raised_concession_upper_glass',H.rectangle(2.32,1.98,2.66),at,(1,0),(0,1),(.23,.25),'glass',r,0)
        prism('sloped_service_counter_with_drip',[( - .49,1.00),(-.49,1.11),(.46,1.14),(.46,1.00)],at,(0,1),(1,0),(-1.42,1.42),'stone',r,.012)
        # A formed beverage dispenser sits inside the service bay, with a real
        # recessed drip tray, formed taps and open cups visible through it.
        machine=prism('formed_internal_beverage_dispenser',[(-.38,1.13),(.38,1.13),(.38,1.77),(.30,1.86),(-.30,1.86),(-.38,1.77)],(x, -2.86),(1,0),(0,1),(-.12,.31),'frost',r,.025)
        for dx in [-.17,.17]:
            H.bar('beverage_tap_curved_spout',[(x+dx,-3.0,1.64),(x+dx,-3.13,1.64),(x+dx,-3.13,1.51)],.027,.030,'iron',r)
            cupPoly=[(.095*math.cos(i*math.tau/12),.095*math.sin(i*math.tau/12))for i in range(12)]
            cup=H.shell('actual_open_service_paper_cup',cupPoly,[(1.14,.015),(1.32,0)],.013,None,r);cup.data.materials.append(paper);cup.location=(x+dx,-3.12,0);H.finish(cup,0)
            points=[(x+dx+.078*math.cos(i*math.tau/12),-3.12+.078*math.sin(i*math.tau/12),z)for z in [1.141,1.152]for i in range(12)]
            mesh('closed_paper_cup_bottom',points,[tuple(reversed(range(12))),tuple(range(12,24)),*[(i,(i+1)%12,(i+1)%12+12,i+12)for i in range(12)]],'service_paper',r,0)
        tray=prism('dispenser_recessed_drip_tray',H.rectangle(.75,1.12,1.16),(x,-3.16),(1,0),(0,1),(-.10,.25),'iron',r,.006)
        H.difference(tray,[H.prism('actual_drip_tray_recess',H.rectangle(.65,1.145,1.20),(x,-3.16),(1,0),(0,1),(-.06,.20),None,r)],'drip_tray_pocket');H.finish(tray,0)
    # A thick continuously bent awning is made from one shared mesh. Stripe
    # boundaries are material faces, so no floating plane or overlapping trim.
    dyed_cloth('awning_cream',(.91,.80,.60,1));dyed_cloth('awning_coral',(.72,.15,.12,1))
    xx=[-4.87+i*9.74/24 for i in range(25)];yy=[-3.48-i*1.80/12 for i in range(13)];nx=len(xx);ny=len(yy)
    def height(y):u=(-y-3.48)/1.8;return 3.06-.59*u+.22*math.sin(u*math.pi)
    verts=[(x,y,height(y)-(.045 if lower else 0))for lower in [False,True]for y in yy for x in xx];q=nx*ny;faces=[];bands=[]
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i;faces.extend([(a,a+1,a+nx+1,a+nx),(q+a,q+a+nx,q+a+nx+1,q+a+1)]);bands.extend([(i//2)%2]*2)
    border=list(range(nx))+[j*nx+nx-1 for j in range(1,ny)]+list(range((ny-1)*nx+nx-2,(ny-1)*nx-1,-1))+[j*nx for j in range(ny-2,0,-1)]
    for i,a in enumerate(border):b=border[(i+1)%len(border)];faces.append((a,q+a,q+b,b));bands.append((a%nx//2)%2)
    awning=mesh('single_closed_bent_striped_service_awning',verts,faces,'awning_cream',r,0);awning.data.materials.append(K.M['v6_awning_coral'])
    for p,band in zip(awning.data.polygons,bands):p.material_index=band;p.use_smooth=True
    surface_uv(awning)
    H.bar('concession_awning_front_structural_rail',[(-4.8,-5.23,2.47),(4.8,-5.23,2.47)],.055,.065,'iron',r)
    for x in [-4.65,-.98,.98,4.65]:H.bar('concession_wall_anchored_awning_bracket',[(x,-3.59,2.05),(x,-5.16,2.45),(x,-3.59,2.95)],.045,.055,'iron',r)
    # One shallow fall roof, with a real stepped front parapet. The wall and
    # roof meet; no oversized domestic gable is balanced on this facade.
    prism('concession_sealed_fall_roof',[(-3.76,3.29),(3.76,3.42),(3.76,3.55),(-3.76,3.42)],(0,0),(0,1),(1,0),(-4.86,4.86),'zinc',r,.006)
    outline=[(-4.70,3.22),(4.70,3.22),(4.70,3.65),(1.35,3.65),(1.12,3.87),(-1.12,3.87),(-1.35,3.65),(-4.70,3.65)]
    prism('actual_stepped_concession_front_parapet',outline,(0,-3.6),(1,0),(0,1),(-.02,.27),'stone',r,.012)
    H.bar('concession_returned_parapet_coping',[(x,-3.66,z+.025)for x,z in outline[2:]],.09,.09,'copper',r)
    r['architectureRevision']=6;r['purpose']='Carnival beverage concession with two real open transaction bays, raised sashes, counter service equipment, a single bent striped awning and low parapet roof';r['wallThicknessMetres']=.26;r['apertureCount']=5
    return r

def theatre_preparation():
    palette('scenic_workshop',{'ivory':(.85,.74,.59,1),'stone':(.94,.84,.67,1),'copper':(.37,.63,.58,1),'wood':(.54,.32,.22,1)});brick_material();zinc_material((.35,.57,.58,1));r=K.root('designed_backstage_scenic_workshop_v6')
    poly=[(-4.7,-3.7),(4.7,-3.7),(4.7,3.7),(-4.7,3.7)]
    wall=shell('scenic_workshop_continuous_brick_enclosure',poly,.025,3.30,.29,'brick',r)
    specs=[('scenic_workshop_staff_entry',(-3.25,-3.7),(1,0),(0,1),1.18,.035,2.63,False,True)]
    specs +=[('wardrobe_high_privacy_window',(x,y),(0,1),(1 if x<0 else-1,0),1.90,1.64,2.94,True,False)for x in [-4.7,4.7]for y in [-1.65,1.62]]
    cut_windows(wall,specs,r)
    aperture=H.rectangle(3.45,-.10,3.07);H.difference(wall,[H.prism('scenery_transfer_full_height_void',aperture,(.45,-3.7),(1,0),(0,1),(-.12,.53),None,r)],'actual_scenery_transfer_portal');H.finish(wall,.006)
    H.ring('deep_scenery_loading_portal',H.rectangle(3.76,-.02,3.23),H.rectangle(3.44,.025,3.08),(.45,-3.7),(1,0),(0,1),(-.06,.25),'stone',r)
    # Broad four-leaf folding set doors fit a full-height scenery route. Actual
    # recessed fields are cut into the door leaves, not pasted on the facade.
    for k in range(4):
        x=.45+(k-1.5)*.853
        leaf=prism('folding_scenery_transfer_door_leaf',H.rectangle(.835,.045,3.055),(x,-3.7),(1,0),(0,1),(.13,.255),'wood',r,.014)
        H.difference(leaf,[H.prism('door_leaf_true_panel_rebate',H.rectangle(.665,.28,2.81),(x,-3.7),(1,0),(0,1),(.10,.17),None,r)],'recessed_scenery_door_field');H.finish(leaf,.004)
        for z in [.43,1.52,2.65]:H.bar('scenery_door_resolved_hinge',[(x-.421,-3.61,z-.045),(x-.421,-3.61,z+.045)],.024,.025,'iron',r)
    H.bar('folding_door_upper_suspension_track',[(-1.52,-3.8,3.12),(2.43,-3.8,3.12)],.085,.08,'iron',r)
    for x in [.30,.61]:H.bar('scenery_transfer_door_pull',[(x,-3.61,1.17),(x,-3.61,1.67)],.03,.035,'iron',r)
    # Asymmetric northlight is the working volume's silhouette. Upper wall
    # infill and two closed pitched sheets meet the real vertical glazing.
    for y,normal in [(-3.7,(0,1)),(3.7,(0,-1))]:
        prism('scenic_workshop_upper_wall_infill',[(-4.7,3.29),(4.7,3.29),(4.7,3.345),(-.70,3.43),(-.70,4.11),(-4.7,3.375)],(0,y),(1,0),normal,(0,.29),'brick',r,.003)
    prism('scenic_workshop_northlight_upper_roof',[(-4.88,3.34),(-.68,4.10),(-.68,4.23),(-4.88,3.47)],(0,0),(1,0),(0,1),(-3.92,3.92),'zinc',r,.005)
    prism('scenic_workshop_northlight_lower_roof',[(-.70,3.43),(4.88,3.34),(4.88,3.47),(-.70,3.56)],(0,0),(1,0),(0,1),(-3.92,3.92),'zinc',r,.005)
    H.ring('workshop_northlight_continuous_frame',H.rectangle(7.40,3.48,4.16),H.rectangle(7.25,3.56,4.08),(-.70,0),(0,1),(1,0),(-.04,.08),'iron',r)
    prism('scenic_workshop_real_vertical_daylight_glass',H.rectangle(7.25,3.56,4.08),(-.70,0),(0,1),(1,0),(.025,.05),'glass',r,0)
    for y in [-2.40,-1.20,0,1.20,2.40]:H.bar('northlight_glazing_mullion',[(-.65,y,3.54),(-.65,y,4.10)],.035,.04,'iron',r)
    for y in [-3.90,0,3.90]:
        H.bar('northlight_upper_roof_fold',[(-4.88,y,3.48),(-.68,y,4.24)],.035,.04,'copper',r)
        H.bar('northlight_lower_roof_fold',[(-.68,y,3.57),(4.88,y,3.48)],.035,.04,'copper',r)
    r['architectureRevision']=6;r['purpose']='Backstage scenic and wardrobe workshop: wide full-height folding scenery doors, separate staff door, high privacy workroom windows and fitted asymmetric northlight section';r['wallThicknessMetres']=.29;r['apertureCount']=6
    return r

BUILDERS={'clinic':clinic,'dining_room':dining_room,'kitchen':kitchen,'electrical_room':electrical_room,'laundry_room':laundry_room,'management_office':management_office,'ticket_booth':ticket_booth,'supply_store':supply_store,'service_lounge':service_lounge,'hotel_multiuse':hotel_multiuse,'cold_store':cold_store,'performance_stage':performance_stage,'refreshment_store':refreshment_store,'theatre_preparation':theatre_preparation}

def dream_lobby():
    palette('illusion_foyer',{'ivory':(.77,.66,.83,1),'mint':(.48,.25,.58,1),'stone':(.92,.85,.93,1),'copper':(.61,.43,.69,1),'glass':(.36,.51,.66,1)});zinc_material((.61,.55,.74,1));r=K.root('designed_faceted_illusion_arrival_foyer_v6')
    # Two canted glazed wings lead into a single recessed public arrival.
    # Every turn is part of the actual thick wall, not an added front panel.
    poly=[(-6.9,-4.8),(-3.2,-4.8),(-3.0,-4.8),(-1.9,-4.0),(0,-4.0),(1.9,-4.0),(3.0,-4.8),(3.2,-4.8),(6.9,-4.8),(6.9,4.8),(3.2,4.8),(0,4.8),(-3.2,4.8),(-6.9,4.8)]
    roofLine=[(-7.15,3.82),(-3.20,4.50),(0,4.02),(3.20,4.50),(7.15,3.82)]
    def roofHeight(x):
        for (a,za),(b,zb)in zip(roofLine,roofLine[1:]):
            if a<=x<=b:return za+(zb-za)*(x-a)/(b-a)
        raise ValueError('Foyer roof section outside designed span')
    wall=shell('illusion_foyer_continuous_canted_wall',poly,.025,3.70,.29,'ivory',r)
    # The footprint explicitly includes every roof section breakpoint on
    # both front and back courses, including the offset inner wall surface.
    for v in wall.data.vertices:
        if v.co.z>3.69:v.co.z=roofHeight(v.co.x)-.14
    wall.data.update()
    specs=[((0,-4.0),(1,0),(0,1),2.62,.035,3.345,'door')]
    specs +=[((x,-4.8),(1,0),(0,1),2.50,.55,2.73,'window')for x in [-4.95,4.95]]
    specs +=[((x,y),(0,1),(1 if x<0 else-1,0),2.25,.72,2.48,'window')for x in [-6.9,6.9]for y in [-2.15,1.85]]
    specs +=[((x,4.8),(1,0),(0,-1),2.2,.82,2.34,'window')for x in [-4.2,0,4.2]]
    arched_apertures(wall,specs,r,wallBevel=.004)
    # Shaped jambs follow the two angled reveal walls. They carry the roof
    # edge into the recessed portal rather than floating in front of it.
    for side in [-1,1]:
        H.bar('foyer_canted_arrival_reveal_top',[(side*3,-4.8,roofHeight(side*3)-.17),(side*1.9,-4,roofHeight(side*1.9)-.17)],.10,.13,'copper',r)
        H.bar('foyer_recessed_arrival_jamb',[(side*1.83,-4.01,.025),(side*1.83,-4.01,roofHeight(side*1.9)-.18)],.10,.13,'copper',r)
    outline=roofLine+[(x,z-.14)for x,z in reversed(roofLine)]
    roof=prism('single_closed_folded_illusion_foyer_roof',outline,(0,0),(1,0),(0,1),(-5.14,5.14),'zinc',r,.006);surface_uv(roof)
    for y in [-5.14,5.14]:H.bar('continuous_folded_foyer_eave',[(x,y,z-.06)for x,z in roofLine],.08,.09,'copper',r)
    for x,z in roofLine[1:-1]:H.bar('folded_foyer_resolved_roof_joint',[(x,-5.14,z+.015),(x,5.14,z+.015)],.035,.045,'copper',r)
    r['architectureRevision']=6;r['purpose']='Illusion-quarter public foyer with continuous canted wings, recessed broad arched arrival, deep glazing and a roof folded to its actual wall section';r['wallThicknessMetres']=.29;r['apertureCount']=len(specs)
    return r

BUILDERS['dream_lobby']=dream_lobby

def mirror_workbay():
    palette('glass_workbay',{'ivory':(.72,.67,.79,1),'stone':(.89,.85,.91,1),'frost':(.67,.79,.81,1),'copper':(.45,.39,.58,1)});zinc_material((.47,.52,.64,1));r=K.root('designed_diffuse_light_glass_workshop_v6')
    # The workroom's shallow butterfly section gives a high diffuse side wall
    # and a real low central drainage line, rather than a domestic tiled hip.
    poly=[(-4.7,-4.2),(0,-4.2),(4.7,-4.2),(4.7,4.2),(0,4.2),(-4.7,4.2)]
    body=shell('glass_workshop_continuous_sectioned_enclosure',poly,.025,3.46,.27,'ivory',r)
    def roofHeight(x):return 3.60+abs(x)*.50/4.95
    for v in body.data.vertices:
        if v.co.z>3.459:v.co.z=roofHeight(v.co.x)-.14
    body.data.update()
    specs=[('rear_workshop_staff_door',(-2.85,4.2),(1,0),(0,-1),1.16,.035,2.65,False,True)]
    specs +=[('diffuse_glasscraft_workroom_window',(x,y),(0,1),(1 if x<0 else-1,0),2.85,1.03,3.12,True,False)for x in [-4.7,4.7]for y in [-1.94,1.94]]
    cut_windows(body,specs,r)
    H.difference(body,[H.prism('full_height_glass_sheet_transfer_void',H.rectangle(2.92,-.10,3.12),(0,-4.2),(1,0),(0,1),(-.12,.48),None,r)],'actual_glass_transfer_opening');H.finish(body,.004)
    H.ring('deep_glass_transfer_loading_jamb',H.rectangle(3.18,-.015,3.25),H.rectangle(2.90,.025,3.13),(0,-4.2),(1,0),(0,1),(-.055,.22),'stone',r)
    for x in [-.733,.733]:
        door=prism('formed_glass_workshop_sliding_door',H.rectangle(1.44,.045,3.09),(x,-4.2),(1,0),(0,1),(.12,.25),'frost',r,.015)
        H.difference(door,[H.prism('sliding_door_deep_stiffened_field',H.rectangle(1.20,z,z+.99),(x,-4.2),(1,0),(0,1),(.09,.16),None,r)for z in [.23,1.56]],'real_formed_door_panel_rebates');H.finish(door,.004)
        H.bar('glasscraft_sliding_door_vertical_pull',[(x+(.40 if x<0 else-.40),-4.1,1.10),(x+(.40 if x<0 else-.40),-4.1,1.67)],.035,.04,'iron',r)
    H.bar('glass_transfer_continuous_door_rail',[(-3.0,-4.35,3.20),(3.0,-4.35,3.20)],.09,.10,'iron',r)
    for x in [-1.16,-.3,.3,1.16]:H.bar('sliding_glass_door_supported_hanger',[(x,-4.34,3.23),(x,-4.08,2.98)],.04,.045,'iron',r)
    # One sealed V-shaped roof, with physically formed central gutter and a
    # resolved drain at the rear; all meet the sectioned masonry below.
    section=[(-4.95,4.10),(0,3.60),(4.95,4.10),(4.95,3.96),(0,3.46),(-4.95,3.96)]
    roof=prism('single_closed_butterfly_glass_workshop_roof',section,(0,0),(1,0),(0,1),(-4.45,4.45),'zinc',r,.005);surface_uv(roof)
    gutter=[(-.12,3.64),(-.12,3.56),(.12,3.56),(.12,3.64),(.09,3.64),(.09,3.59),(-.09,3.59),(-.09,3.64)]
    prism('formed_open_central_rain_gutter',gutter,(0,0),(1,0),(0,1),(-4.45,4.54),'iron',r,0)
    H.bar('glass_workshop_rear_rainwater_pipe',[(0,4.52,3.58),(0,4.52,.25),(.25,4.52,.15)],.055,.06,'iron',r)
    for x in [-4.9,4.9]:H.bar('butterfly_roof_resolved_side_fascia',[(x,-4.45,roofHeight(x)-.055),(x,4.45,roofHeight(x)-.055)],.055,.075,'copper',r)
    for y in [-4.45,4.45]:H.bar('butterfly_roof_continuous_end_fascia',[(-4.95,y,4.04),(0,y,3.54),(4.95,y,4.04)],.06,.085,'copper',r)
    r['architectureRevision']=6;r['purpose']='Glasscraft service workshop with wide sliding transfer doors, deep diffuse side glazing, actual butterfly roof section, formed central gutter and resolved rear drain';r['wallThicknessMetres']=.27;r['apertureCount']=6
    return r

BUILDERS['mirror_workbay']=mirror_workbay

def record_room():
    palette('record_vault',{'ivory':(.68,.65,.76,1),'stone':(.88,.84,.87,1),'frost':(.52,.61,.68,1),'copper':(.46,.44,.62,1),'wood':(.49,.35,.24,1)});zinc_material((.43,.51,.63,1));r=K.root('designed_climate_record_vault_with_reading_bays_v6')
    for name,color in [('record_paper',(.76,.67,.52,1)),('record_cloth',(.34,.27,.46,1))]:
        material=dyed_cloth(name,color)
        for node in material.node_tree.nodes:
            if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.08
    poly=[(-6.6,-5.6),(-2.3,-5.6),(-2.3,-4.5),(2.3,-4.5),(2.3,-5.6),(6.6,-5.6),(6.6,5.6),(-6.6,5.6)]
    xx=[-6.82+i*13.64/32 for i in range(33)]
    def crown(x):return 3.70+1.32*math.sqrt(max(0,1-(x/6.9)**2))
    # Form the thick recessed enclosure first, then intersect it with the
    # exact underside section. This resolves both wall surfaces and their
    # roof contact without collapsing short polygon offsets at corners.
    wall=shell('record_vault_continuous_recessed_thick_enclosure',poly,.025,5.10,.34,'ivory',r)
    section=[(xx[0],-.50),(xx[-1],-.50)]+[(x,crown(x)-.14)for x in reversed(xx)]
    clip=H.prism('construction_exact_curved_vault_section',section,(0,0),(1,0),(0,1),(-6,6),None,r)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=wall;modifier=wall.modifiers.new('actual_curved_vault_wall_intersection','BOOLEAN');modifier.operation='INTERSECT';modifier.solver='EXACT';modifier.object=clip;bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(clip,do_unlink=True)
    specs=[('secure_archive_centre_entry',(0,-4.5),(1,0),(0,1),1.90,.035,2.93,False,True)]
    specs +=[('archive_front_reading_bay',(x,-5.6),(1,0),(0,1),2.30,.72,3.22,False,False)for x in [-4.43,4.43]]
    specs +=[('archive_high_climate_daylight_slot',(x,y),(0,1),(1 if x<0 else-1,0),2.55,2.24,3.27,True,False)for x in [-6.6,6.6]for y in [-2.55,1.95]]
    specs +=[('archive_rear_high_slot',(x,5.6),(1,0),(0,-1),2.50,2.25,3.25,True,False)for x in [-3.8,3.8]]
    cut_windows(wall,specs,r)
    clear=K.M['v6_glass'].copy();clear.name='architecture6_archive_clear_glass';bs=clear.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.70,.85,.92,.12);bs.inputs['Alpha'].default_value=.12;bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.10
    floorPlan=H.offset(poly,.34);n=len(floorPlan);vertices=[(x,y,z)for z in [-.025,.035]for x,y in floorPlan]
    mesh('actual_archive_interior_wood_floor',vertices,[tuple(reversed(range(n))),tuple(range(n,n*2)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'wood',r,0)
    # Only the two supervised reading bays are transparent. The record
    # storage walls retain high diffused slots and a protected recessed entry.
    for o in r.children_recursive:
        if o.type=='MESH'and o.name.startswith('archive_front_reading_bay_actual_glass_depth'):o.data.materials.clear();o.data.materials.append(clear)
    for centre in [-4.43,4.43]:
        # Proper indoor filing joinery, visible through the real opening.
        at=(centre,-4.78);outline=H.rectangle(1.90,.12,2.89)
        cabinet=prism('archive_indoor_record_cabinet_body',outline,at,(1,0),(0,1),(0,.38),'wood',r,.012)
        for bottom in [.37,1.16,1.95]:
            H.difference(cabinet,[H.prism('filing_joinery_actual_open_shelf',H.rectangle(1.70,bottom,bottom+.63),at,(1,0),(0,1),(-.07,.29),None,r)],'actual_recessed_record_shelves');H.finish(cabinet,.003)
            for k in range(5):
                x=centre+(k-2)*.295;prism('indoor_record_storage_folio',H.rectangle(.24,bottom+.018,bottom+.53),(x,-4.78),(1,0),(0,1),(.03,.23),'record_paper'if k%2 else'record_cloth',r,.006)
    section=[(x,crown(x))for x in xx]+[(x,crown(x)-.14)for x in reversed(xx)]
    roof=prism('single_sealed_record_vault_barrel_roof',section,(0,0),(1,0),(0,1),(-5.86,5.86),'zinc',r,.004);surface_uv(roof)
    for p in roof.data.polygons:p.use_smooth=True
    for y in [-5.86,0,5.86]:H.bar('archive_vault_resolved_roof_joint',[(x,y,crown(x)+.012)for x in xx],.035,.045,'copper',r)
    r['architectureRevision']=6;r['purpose']='Climate-protected record vault with thick continuous barrel enclosure, recessed secure entry, high diffused slots and two supervised glazed reading bays with actual indoor filing joinery';r['wallThicknessMetres']=.34;r['apertureCount']=len(specs)
    return r

BUILDERS['record_room']=record_room

def screening_room():
    palette('picture_palace',{'ivory':(.68,.55,.73,1),'mint':(.38,.22,.49,1),'stone':(.91,.83,.85,1),'copper':(.55,.37,.63,1)});zinc_material((.42,.38,.54,1));r=K.root('designed_windowless_picture_hall_and_arrival_foyer_v6')
    # The hall section grows towards the projection end. A low glazed foyer
    # serves the tall, mostly windowless screening volume behind it.
    east=[(6.60,-8.60),(6.60,-6.60),(6.18,-5.50),(6.18,-3.90),(6.60,-2.82),(6.60,-1.10),(6.18,0),(6.18,1.75),(6.60,2.85),(6.60,4.50),(6.18,5.60),(6.18,7.00),(6.60,8.10),(6.60,8.60)]
    # The long, blind acoustic walls are themselves folded into deep bays.
    # This is a single thick wall section, not repeated attached pilasters.
    poly=east+[(-x,y)for x,y in reversed(east)]
    hall=shell('cinema_continuous_acoustic_hall_wall',poly,.025,5.40,.32,'ivory',r)
    def underside(y):return 5.40+(y+8.60)*1.30/17.2
    for v in hall.data.vertices:
        if v.co.z>5.399:v.co.z=underside(v.co.y)
    hall.data.update()
    H.difference(hall,[H.prism('foyer_to_hall_full_height_actual_passage',H.rectangle(3.12,-.10,3.12),(0,-8.6),(1,0),(0,1),(-.15,.50),None,r),H.prism('cinema_rear_technical_access_void',H.rectangle(1.24,-.10,2.78),(-4.65,8.6),(1,0),(0,-1),(-.10,.49),None,r)],'actual_cinema_foyer_and_technical_doorways');H.finish(hall,.006)
    window('cinema_rear_technical_access',(-4.65,8.6),(1,0),(0,-1),1.24,.035,2.78,r,False,True)
    # Two real high louvres express the mechanically ventilated projection
    # room. They are not domestic windows pasted onto an auditorium wall.
    for x in [-1.4,2.4]:
        H.difference(hall,[H.prism('projection_vent_actual_wall_void',H.rectangle(1.72,4.72,5.63),(x,8.6),(1,0),(0,-1),(-.10,.49),None,r)],'projection_vent_cut');H.finish(hall,.003)
        H.ring('deep_projection_vent_frame',H.rectangle(1.86,4.65,5.70),H.rectangle(1.69,4.75,5.61),(x,8.6),(1,0),(0,-1),(-.035,.20),'stone',r)
        for z in [4.84,5.00,5.16,5.32,5.48]:prism('folded_projection_room_louvre',[(-.04,z-.025),(.10,z+.025),(.11,z+.01),(-.03,z-.04)],(x,8.6),(0,-1),(1,0),(-.82,.82),'iron',r,0)
    foyer=shell('picture_hall_continuous_low_glazed_foyer',[(-4.7,-10.4),(4.7,-10.4),(4.7,-8.59),(-4.7,-8.59)],.025,3.24,.22,'mint',r)
    cut_windows(foyer,[('public_picture_hall_double_entry',(0,-10.4),(1,0),(0,1),2.56,.035,2.91,False,True),*[( 'picture_hall_foyer_window',(x,-10.4),(1,0),(0,1),2.35,.54,2.90,False,False)for x in [-3.13,3.13]]],r)
    H.difference(foyer,[H.prism('continuous_foyer_to_auditorium_opening',H.rectangle(3.12,-.10,3.12),(0,-8.59),(1,0),(0,-1),(-.16,.50),None,r)],'foyer_actual_rear_passage');H.finish(foyer,.004)
    section=[(-8.86,underside(-8.86)),(8.86,underside(8.86)),(8.86,underside(8.86)+.15),(-8.86,underside(-8.86)+.15)]
    roof=prism('single_sealed_raked_cinema_hall_roof',section,(0,0),(0,1),(1,0),(-6.85,6.85),'zinc',r,.006);surface_uv(roof)
    for x in [-6.82,0,6.82]:H.bar('raked_cinema_roof_resolved_standing_joint',[(x,-8.86,underside(-8.86)+.165),(x,8.86,underside(8.86)+.165)],.035,.04,'copper',r)
    # A single closed rounded marquee canopy is shaped in plan, with actual
    # depth and fascia. It shelters arrival without a floating sign board.
    canopy=[]
    for cx,cy,start in [(4.72,-10.65,-math.pi/2),(4.72,-8.40,0),(-4.72,-8.40,math.pi/2),(-4.72,-10.65,math.pi)]:
        canopy.extend((cx+.45*math.cos(start+i*math.pi/16),cy+.45*math.sin(start+i*math.pi/16))for i in range(9))
    n=len(canopy);verts=[(x,y,z)for z in [3.23,3.43]for x,y in canopy];faces=[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]]
    mesh('single_formed_rounded_picture_hall_marquee',verts,faces,'copper',r,.006)
    r['architectureRevision']=6;r['purpose']='Picture hall with a tall raked acoustic screening volume, high projection-room ventilation, lower glazed public foyer and one formed rounded arrival marquee with real connecting passage';r['wallThicknessMetres']=.32;r['apertureCount']=8
    return r

BUILDERS['screening_room']=screening_room

def archive_room():
    palette('clockwork_archive',{'stone':(.86,.79,.62,1),'frost':(.43,.49,.45,1),'copper':(.50,.45,.27,1)});brick_material();zinc_material((.47,.51,.40,1));r=K.root('designed_industrial_archive_strongroom_v6')
    poly=[(-5.6,-3.8),(-4.8,-4.6),(4.8,-4.6),(5.6,-3.8),(5.6,3.8),(4.8,4.6),(-4.8,4.6),(-5.6,3.8)]
    wall=shell('archive_continuous_chamfered_heavy_masonry',poly,.025,3.55,.36,'brick',r)
    def roofBase(y):return 3.55+(y+4.6)*.20/9.2
    for v in wall.data.vertices:
        if v.co.z>3.549:v.co.z=roofBase(v.co.y)
    wall.data.update()
    specs=[('archive_narrow_supervised_front_lite',(x,-4.6),(1,0),(0,1),.86,1.36,3.10,True,False)for x in [-3.45,3.45]]
    specs +=[('archive_protected_side_lite',(x,y),(0,1),(1 if x<0 else-1,0),.85,1.54,3.13,True,False)for x in [-5.6,5.6]for y in [-1.95,1.95]]
    cut_windows(wall,specs,r)
    H.difference(wall,[H.prism('archive_secure_entry_actual_void',H.rectangle(2.04,-.10,2.95),(0,-4.6),(1,0),(0,1),(-.10,.52),None,r)],'secure_archive_entry');H.finish(wall,.004)
    H.ring('archive_deep_stone_security_portal',H.rectangle(2.32,-.025,3.12),H.rectangle(2.03,.025,2.96),(0,-4.6),(1,0),(0,1),(-.055,.31),'stone',r)
    for x in [-.505,.505]:
        leaf=prism('archive_formed_metal_security_door',H.rectangle(.985,.045,2.93),(x,-4.6),(1,0),(0,1),(.23,.35),'frost',r,.016)
        H.difference(leaf,[H.prism('archive_security_door_recess',H.rectangle(.78,.27,2.72),(x,-4.6),(1,0),(0,1),(.19,.265),None,r)],'formed_archive_door_field');H.finish(leaf,.004)
    for x in [-.15,.15]:H.bar('archive_secure_entry_pull',[(x,-4.42,1.05),(x,-4.42,1.57)],.03,.04,'iron',r)
    section=[(-4.83,roofBase(-4.83)),(4.83,roofBase(4.83)),(4.83,roofBase(4.83)+.14),(-4.83,roofBase(-4.83)+.14)]
    roof=prism('archive_sealed_fall_roof',section,(0,0),(0,1),(1,0),(-5.82,5.82),'zinc',r,.004)
    # The daylight monitor opens through the real roof into the storage
    # volume. It is not a decorative box perched on an unbroken roof.
    H.difference(roof,[H.prism('archive_daylight_monitor_roof_aperture',H.rectangle(2.20,3.20,4.20),(0,0),(1,0),(0,1),(-3.20,3.20),None,r)],'actual_archive_monitor_roof_opening');H.finish(roof,.003);surface_uv(roof)
    monitor=shell('archive_raised_diffused_daylight_monitor',[(-1.12,-3.24),(1.12,-3.24),(1.12,3.24),(-1.12,3.24)],3.60,4.55,.12,'stone',r)
    cut_windows(monitor,[('archive_monitor_actual_diffused_slot',(x,y),(0,1),(1 if x<0 else-1,0),1.65,4.04,4.39,True,False)for x in [-1.12,1.12]for y in [-1.72,1.72]],r)
    prism('archive_monitor_fitted_metal_cap',H.rectangle(2.55,4.55,4.69),(0,0),(1,0),(0,1),(-3.43,3.43),'zinc',r,.012)
    H.bar('archive_continuous_front_cornice',[(-4.79,-4.63,3.42),(4.79,-4.63,3.42)],.10,.14,'stone',r)
    r['architectureRevision']=6;r['purpose']='Clockwork-quarter archive strongroom: continuous chamfered brick envelope, protected narrow lights, deep metal security entry and a true roof-opening diffuse daylight monitor';r['wallThicknessMetres']=.36;r['apertureCount']=11
    return r

BUILDERS['archive_room']=archive_room

def loading_gate():
    palette('clockwork_loading',{'stone':(.83,.76,.61,1),'copper':(.56,.43,.25,1),'iron':(.20,.27,.27,1)});brick_material();zinc_material((.45,.51,.42,1));r=K.root('designed_covered_industrial_freight_transfer_gate_v6')
    def crown(x):return 4.39+.48*(1-(x/5.65)**2)
    # Formed masonry piers have a load-bearing profile, bevelled boot and
    # cap. Their upper beams actually meet the closed metal canopy section.
    for x in [-4.85,4.85]:
        for y in [-4.40,4.40]:
            shape=[(-.35,.035),(.35,.035),(.35,.31),(.25,.46),(.25,crown(x)-.30),(.32,crown(x)-.24),(.32,crown(x)-.14),(-.32,crown(x)-.14),(-.32,crown(x)-.24),(-.25,crown(x)-.30),(-.25,.46),(-.35,.31)]
            prism('freight_canopy_profiled_structural_pier',shape,(x,y),(1,0),(0,1),(-.33,.33),'brick',r,.012)
    xs=[-5.65+i*11.3/32 for i in range(33)];section=[(x,crown(x))for x in xs]+[(x,crown(x)-.14)for x in reversed(xs)]
    roof=prism('single_closed_covered_loading_canopy',section,(0,0),(1,0),(0,1),(-5.47,5.47),'zinc',r,.006);surface_uv(roof)
    for p in roof.data.polygons:p.use_smooth=True
    for y in [-4.40,4.40]:
        H.bar('freight_canopy_fitted_transverse_beam',[(x,y,crown(x)-.20)for x in xs],.13,.15,'iron',r)
        H.bar('freight_canopy_lower_tension_tie',[(-4.86,y,4.02),(4.86,y,4.02)],.09,.10,'iron',r)
        for x in [-3.25,0,3.25]:H.bar('freight_canopy_tied_roof_web',[(x-.43,y,4.02),(x,y,crown(x)-.21)],.06,.075,'iron',r)
    for x in [-4.85,4.85]:H.bar('freight_canopy_longitudinal_eave_beam',[(x,-4.42,crown(x)-.21),(x,4.42,crown(x)-.21)],.14,.16,'iron',r)
    # Two actual framed sliding gates retain clear views through their bars.
    # The ceiling, supports and rail belong to the loading shed's load path.
    for x in [-1.73,1.73]:
        at=(x,0);H.ring('freight_sliding_gate_closed_perimeter_frame',H.rectangle(3.40,.13,3.63),H.rectangle(3.10,.29,3.46),at,(1,0),(0,1),(-.075,.075),'iron',r)
        for k in range(11):
            xx=x+(k-5)*.27;H.bar('freight_sliding_gate_steel_infill',[(xx,0,.28),(xx,0,3.47)],.038,.04,'iron',r)
        H.bar('freight_sliding_gate_diagonal_brace',[(x-1.56,-.038,.30),(x+1.56,-.038,3.46)],.075,.08,'copper',r)
    for x in [-3.68,3.68]:
        prism('deep_freight_gate_track_pilaster',[(-.27,.035),(.27,.035),(.24,3.91),(-.24,3.91)],(x,0),(1,0),(0,1),(-.34,.34),'brick',r,.012)
        H.bar('freight_gate_track_top_structure_tie',[(x,0,3.86),(x,0,crown(x)-.14)],.13,.15,'iron',r)
    H.bar('freight_sliding_gate_load_rail',[(-3.95,0,3.72),(3.95,0,3.72)],.14,.13,'iron',r)
    H.bar('freight_sliding_gate_floor_guide',[(-3.67,0,.085),(3.67,0,.085)],.025,.045,'iron',r)
    deck=[(-5.73,-5.16),(5.73,-5.16),(5.73,5.16),(-5.73,5.16)];verts=[(x,y,z)for z in [-.035,.065]for x,y in deck]
    mesh('continuous_freight_transfer_deck',verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'stone',r,.006)
    prism('flush_freight_vehicle_entry_ramp',[(-5.85,.025),(-5.16,.065),(-5.16,-.03),(-5.85,-.03)],(0,0),(0,1),(1,0),(-5.73,5.73),'stone',r,0)
    r['architectureRevision']=6;r['purpose']='Covered freight transfer gateway with full clearance, profile-built piers, actual tied roof beams, thick canopy, framed and braced sliding gate, shared load rail and flush vehicle ramp';r['apertureCount']=1
    return r

BUILDERS['loading_gate']=loading_gate

def exhibition_room():
    palette('clockwork_exhibit',{'stone':(.94,.85,.66,1),'copper':(.63,.45,.20,1),'wood':(.64,.47,.25,1)});brick_material();zinc_material((.34,.56,.49,1));r=K.root('designed_clockwork_exhibition_hall_v6')
    roofLine=[(-6.85,3.92),(-4.10,4.70),(-1.40,5.35),(0,4.20),(2.80,4.78),(6.85,3.92)]
    def height(x):
        for (a,za),(b,zb)in zip(roofLine,roofLine[1:]):
            if a<=x<=b:return za+(zb-za)*(x-a)/(b-a)
        raise ValueError('Exhibition wall outside roof section')
    xs=[-6.64,*[x for x,z in roofLine[1:-1]],6.64];poly=[(x,-5.56)for x in xs]+[(x,5.56)for x in reversed(xs)]
    wall=shell('exhibition_continuous_profile_fitted_brick_enclosure',poly,.025,3.70,.29,'brick',r)
    for v in wall.data.vertices:
        if v.co.z>3.699:v.co.z=height(v.co.x)-.14
    wall.data.update()
    specs=[('exhibit_public_double_entry',(0,-5.56),(1,0),(0,1),2.55,.035,3.13,False,True)]
    specs +=[('exhibit_large_front_display_bay',(x,-5.56),(1,0),(0,1),3.25,.54,3.29,False,False)for x in [-4.35,4.35]]
    specs +=[('exhibit_deep_side_daylight',(x,y),(0,1),(1 if x<0 else-1,0),2.58,1.03,3.13,False,False)for x in [-6.64,6.64]for y in [-2.65,2.58]]
    cut_windows(wall,specs,r)
    glass=K.M['v6_glass'].copy();glass.name='architecture6_exhibit_clear_glass';bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.70,.85,.92,.12);bs.inputs['Alpha'].default_value=.12;bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.10
    for o in r.children_recursive:
        if o.type=='MESH'and o.name.startswith('exhibit_large_front_display_bay_actual_glass_depth'):o.data.materials.clear();o.data.materials.append(glass)
    floorPlan=H.offset(poly,.29);n=len(floorPlan);vertices=[(x,y,z)for z in [-.025,.035]for x,y in floorPlan]
    mesh('actual_exhibit_indoor_floor',vertices,[tuple(reversed(range(n))),tuple(range(n,n*2)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'stone',r,0)
    # Neutral, non-interactive mechanical exhibits sit indoors behind the
    # real display apertures. Teeth, open hub and supports are actual mesh.
    for x,radius in [(-4.35,.83),(4.35,.72)]:
        y=-4.55;z=1.78;count=56;angles=[i*math.tau/count for i in range(count)];ring=[radius*(1 if i%4 in [1,2]else .88)for i in range(count)]
        outer=[(rr*math.cos(a),z+rr*math.sin(a))for rr,a in zip(ring,angles)];inner=[(.38*math.cos(a),z+.38*math.sin(a))for a in angles]
        H.ring('actual_indoor_tooth_cut_mechanical_exhibit',outer,inner,(x,y),(1,0),(0,1),(-.065,.065),'copper',r)
        for a in [0,math.pi/3,math.tau/3]:H.bar('mechanical_exhibit_structural_spoke',[(x+d*math.cos(a),y,z+d*math.sin(a))for d in [-.42,.42]],.074,.085,'iron',r)
        for dx in [-.35,.35]:H.bar('mechanical_exhibit_stand',[(x+dx,y,.22),(x+dx,y,z-.51)],.095,.12,'iron',r)
        prism('formed_indoor_exhibit_plinth',[(-.94,.035),(.94,.035),(.94,.14),(.83,.25),(-.83,.25),(-.94,.14)],(x,y),(1,0),(0,1),(-.44,.44),'stone',r,.012)
    section=roofLine+[(x,z-.14)for x,z in reversed(roofLine)];roof=prism('one_closed_asymmetric_folded_exhibition_roof',section,(0,0),(1,0),(0,1),(-5.83,5.83),'zinc',r,.006);surface_uv(roof)
    for y in [-5.83,5.83]:H.bar('exhibition_continuous_folded_roof_edge',[(x,y,z-.055)for x,z in roofLine],.07,.085,'copper',r)
    for x,z in roofLine[1:-1]:H.bar('exhibition_formed_standing_seam',[(x,-5.83,z+.012),(x,5.83,z+.012)],.035,.04,'copper',r)
    prism('formed_exhibition_arrival_canopy',[(-1.70,3.22),(0,3.40),(1.70,3.22),(1.70,3.33),(0,3.51),(-1.70,3.33)],(0,0),(1,0),(0,1),(-6.70,-5.42),'zinc',r,.006)
    for x in [-1.59,1.59]:H.bar('exhibition_wall_borne_canopy_tie',[(x,-5.56,2.86),(x,-6.61,3.23),(x,-5.56,3.28)],.045,.055,'iron',r)
    r['architectureRevision']=6;r['purpose']='Public clockwork exhibition hall: genuine deep display glazing with indoor mechanical exhibits, broad foyer, sectioned brick envelope and one fitted asymmetrical folded roof';r['wallThicknessMetres']=.29;r['apertureCount']=len(specs)
    return r

BUILDERS['exhibition_room']=exhibition_room

def inspection_hall_normal():
    palette('clockwork_inspection',{'stone':(.86,.79,.61,1),'frost':(.61,.72,.65,1),'copper':(.63,.49,.25,1),'iron':(.21,.30,.28,1)});brick_material();zinc_material((.40,.56,.46,1));r=K.root('designed_clockwork_inspection_transfer_hall_v6')
    roofLine=[(-5.96,3.56),(-3.13,3.56),(-2.74,4.95),(2.74,4.95),(3.13,3.56),(5.96,3.56)]
    xs=[-5.72,*[x for x,z in roofLine[1:-1]],5.72];poly=[(x,-5.65)for x in xs]+[(x,5.65)for x in reversed(xs)]
    def zRoof(x):
        for (a,za),(b,zb)in zip(roofLine,roofLine[1:]):
            if a<=x<=b:return za+(zb-za)*(x-a)/(b-a)
        raise ValueError('Inspection hall outside structural roof section')
    body=shell('inspection_continuous_raised_central_bay_masonry',poly,.025,3.40,.32,'brick',r)
    for v in body.data.vertices:
        if v.co.z>3.399:v.co.z=zRoof(v.co.x)-.15
    body.data.update()
    specs=[('inspection_staff_access',(3.85,5.65),(1,0),(0,-1),1.22,.035,2.68,False,True)]
    specs +=[('inspection_side_worklight',(x,y),(0,1),(1 if x<0 else-1,0),2.36,1.54,2.91,True,False)for x in [-5.72,5.72]for y in [-2.4,2.22]]
    cut_windows(body,specs,r)
    H.difference(body,[H.prism('whole_inspection_vehicle_bay_void',elliptical_arch(4.45,-.1,2.92,4.29,24),(0,-5.65),(1,0),(0,1),(-.14,.50),None,r)],'actual_inspection_bay_arch');H.finish(body,.005)
    H.ring('inspection_vehicle_bay_structural_arch',elliptical_arch(4.85,-.01,2.92,4.51,24),elliptical_arch(4.43,.035,2.92,4.28,24),(0,-5.65),(1,0),(0,1),(-.09,.23),'stone',r)
    # Partly raised shutter leaves the work lane visible. Its rolled profile
    # sits inside the real arch rather than covering a solid facade wall.
    prism('inspection_raised_formed_shutter',elliptical_arch(4.32,2.65,2.92,4.23,24),(0,-5.65),(1,0),(0,1),(.15,.20),'zinc',r,.003)
    for z in [2.71,2.91,3.11,3.31,3.51,3.71,3.91,4.08]:
        half=2.14*math.sqrt(max(.01,1-((max(z,2.92)-2.92)/1.31)**2));H.bar('inspection_shutter_interlocking_slats',[(-half,-5.51,z),(half,-5.51,z)],.026,.038,'iron',r)
    floor=H.offset(poly,.32);n=len(floor);vertices=[(x,y,z)for z in [-.025,.035]for x,y in floor]
    mesh('actual_inspection_bay_concrete_floor',vertices,[tuple(reversed(range(n))),tuple(range(n,n*2)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'stone',r,0)
    for x in [-.94,.94]:H.bar('recessed_inspection_lane_guide_rail',[(x,-5.64,.04),(x,1.65,.04)],.025,.07,'iron',r)
    outline=roofLine+[(x,z-.15)for x,z in reversed(roofLine)];roof=prism('single_closed_raised_bay_inspection_roof',outline,(0,0),(1,0),(0,1),(-5.95,5.95),'zinc',r,.005);surface_uv(roof)
    for y in [-5.95,5.95]:H.bar('inspection_fitted_roof_edge',[(x,y,z-.07)for x,z in roofLine],.07,.09,'copper',r)
    r['architectureRevision']=6;r['purpose']='Inspection transfer hall with taller central work bay, continuous fitted stepped roof, genuine wide arched vehicle opening, partly raised shutter and physical inspection lane guides';r['wallThicknessMetres']=.32;r['apertureCount']=6
    return r

BUILDERS['inspection_hall_normal']=inspection_hall_normal

def maintenance_workshop():
    palette('clockwork_repair',{'stone':(.89,.78,.60,1),'frost':(.52,.67,.61,1),'copper':(.66,.46,.23,1),'iron':(.20,.30,.28,1)});brick_material();zinc_material((.38,.55,.48,1));r=K.root('designed_northlight_maintenance_workshop_v6')
    poly=[(-6.61,-5.63),(6.61,-5.63),(6.61,5.63),(-6.61,5.63)]
    wall=shell('workshop_continuous_thick_repair_bay_wall',poly,.025,5.42,.31,'brick',r)
    # Cut both wall surfaces with the real stepped northlight section. The
    # sharp step is represented exactly, not approximated by stacked walls.
    shape=[(-5.94,-.35),(5.94,-.35),(5.94,4.30),(-.92,3.89),(-.92,5.19),(-5.94,3.78)]
    clip=H.prism('construction_workshop_roof_section',shape,(0,0),(0,1),(1,0),(-6.85,6.85),None,r)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=wall;m=wall.modifiers.new('actual_workshop_roof_section_intersection','BOOLEAN');m.operation='INTERSECT';m.solver='EXACT';m.object=clip;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(clip,do_unlink=True)
    specs=[('workshop_front_bench_daylight',(3.1,-5.63),(1,0),(0,1),3.25,.86,3.18,True,False),('workshop_rear_staff_entry',(3.85,5.63),(1,0),(0,-1),1.28,.035,2.72,False,True)]
    specs +=[('repair_side_daylight',(x,y),(0,1),(1 if x<0 else-1,0),2.41,1.28,3.24,True,False)for x in [-6.61,6.61]for y in [-2.72,2.60]]
    cut_windows(wall,specs,r)
    at=(-3.0,-5.63);H.difference(wall,[H.prism('full_workshop_repair_bay_void',H.rectangle(4.60,-.10,3.48),at,(1,0),(0,1),(-.13,.51),None,r)],'actual_open_repair_bay');H.finish(wall,.004)
    H.ring('deep_repair_bay_steel_structural_frame',H.rectangle(4.84,-.025,3.60),H.rectangle(4.58,.025,3.47),at,(1,0),(0,1),(-.055,.25),'iron',r)
    prism('partly_raised_sectional_repair_door',H.rectangle(4.52,2.64,3.44),at,(1,0),(0,1),(.13,.20),'zinc',r,.008)
    for z in [2.68,2.86,3.04,3.22,3.40]:H.bar('formed_sectional_door_interlock',[(-5.25,-5.505,z),(-.75,-5.505,z)],.026,.037,'iron',r)
    floor=H.offset(poly,.31);n=len(floor);verts=[(x,y,z)for z in [-.025,.035]for x,y in floor]
    mesh('actual_repair_bay_concrete_floor',verts,[tuple(reversed(range(n))),tuple(range(n,n*2)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'stone',r,0)
    for x in [-3.86,-2.14]:
        prism('actual_low_vehicle_service_ramp',[(-4.86,.035),(-4.17,.36),(-1.25,.36),(-1.25,.035)],(x,0),(0,1),(1,0),(-.20,.20),'iron',r,.01)
    for name,section in [('northlight_high_panel',[(-5.94,3.78),(-.92,5.19),(-.92,5.33),(-5.94,3.92)]),('northlight_low_panel',[(-.92,3.89),(5.94,4.30),(5.94,4.44),(-.92,4.03)])]:
        roof=prism('closed_workshop_'+name,section,(0,0),(0,1),(1,0),(-6.84,6.84),'zinc',r,.004);surface_uv(roof)
    H.ring('workshop_actual_full_span_northlight_frame',H.rectangle(13.28,4.012,5.22),H.rectangle(13.08,4.10,5.13),(0,-.92),(1,0),(0,1),(-.052,.057),'iron',r)
    prism('actual_workshop_vertical_northlight_glazing',H.rectangle(13.08,4.10,5.13),(0,-.92),(1,0),(0,1),(-.018,.024),'frost',r,0)
    for x in [-4.9,-3.27,-1.63,0,1.63,3.27,4.9]:H.bar('northlight_structural_glazing_mullion',[(x,-.94,4.075),(x,-.94,5.16)],.045,.055,'iron',r)
    r['architectureRevision']=6;r['purpose']='Maintenance shed with a real open repair bay and service ramps, continuous brick section, lifted sectional door and full-span vertical northlight glazing between fitted pitched roof panels';r['wallThicknessMetres']=.31;r['apertureCount']=7
    return r

BUILDERS['maintenance_workshop']=maintenance_workshop

def reading_room():
    palette('clockwork_reading',{'ivory':(.91,.78,.57,1),'stone':(.94,.84,.64,1),'roof':(.41,.53,.49,1),'wood':(.62,.47,.28,1),'copper':(.65,.47,.23,1)});brick_material();zinc_material((.41,.55,.46,1));r=K.root('designed_arcaded_public_reading_pavilion_v6')
    poly=[(-5.66,-2.82),(5.66,-2.82),(5.66,4.65),(-5.66,4.65)]
    wall=shell('reading_pavilion_continuous_inner_enclosure',poly,.025,3.60,.30,'ivory',r)
    specs=[('reading_main_public_entry',(0,-2.82),(1,0),(0,1),1.94,.035,2.94,False,True)]
    specs +=[('reading_large_glazed_bay',(x,-2.82),(1,0),(0,1),2.60,.61,3.02,False,False)for x in [-3.42,3.42]]
    specs +=[('reading_side_diffuse_window',(x,y),(0,1),(1 if x<0 else-1,0),2.08,1.02,2.96,False,False)for x in [-5.66,5.66]for y in [-.72,2.41]]
    cut_windows(wall,specs,r)
    glass=K.M['v6_glass'].copy();glass.name='architecture6_reading_clear_glass';bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.70,.85,.92,.12);bs.inputs['Alpha'].default_value=.12;bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.10
    for o in r.children_recursive:
        if o.type=='MESH'and o.name.startswith('reading_large_glazed_bay_actual_glass_depth'):o.data.materials.clear();o.data.materials.append(glass)
    # Three actual open arches are cut from a single deep masonry arcade.
    front=prism('reading_loggia_continuous_arcade_wall',H.rectangle(11.32,.025,3.17),(0,-5.70),(1,0),(0,1),(0,.27),'brick',r,0)
    H.difference(front,[H.prism('reading_arcade_true_open_arch_void',elliptical_arch(2.65,-.10,2.03,2.79,20),(x,-5.70),(1,0),(0,1),(-.10,.42),None,r)for x in [-3.42,0,3.42]],'actual_walkable_reading_arcade_openings');H.finish(front,.006)
    for x in [-3.42,0,3.42]:H.ring('reading_arcade_structural_stone_arch',elliptical_arch(2.92,-.01,2.03,2.97,20),elliptical_arch(2.63,.035,2.03,2.78,20),(x,-5.70),(1,0),(0,1),(-.055,.16),'stone',r)
    for x in [-5.66,5.66]:prism('reading_loggia_load_bearing_side_return',[(-5.70,.025),(-2.80,.025),(-2.80,3.58),(-5.70,3.17)],(x,0),(0,1),(1,0),(-.13,.13),'brick',r,.006)
    prism('closed_reading_loggia_pitch_roof',[(-5.93,3.136),(-2.70,3.59),(-2.70,3.72),(-5.93,3.266)],(0,0),(0,1),(1,0),(-5.85,5.85),'zinc',r,.006)
    hip_roof('reading_main_fitted_hipped_roof',[(-5.86,-3.0),(5.86,-3.0),(5.86,4.85),(-5.86,4.85)],3.69,.85,1,r)
    prism('continuous_reading_loggia_and_indoor_floor',H.rectangle(11.24,-.025,.035),(0,0),(1,0),(0,1),(-5.73,4.45),'stone',r,0)
    dyed_cloth('library_leaf',(.84,.72,.55,1));dyed_cloth('library_binding',(.40,.20,.13,1))
    for centre in [-3.42,3.42]:
        at=(centre,-1.75);shelf=prism('actual_indoor_reading_shelf_joinery',H.rectangle(2.12,.085,2.74),at,(1,0),(0,1),(0,.42),'wood',r,.012)
        levels=[.27,1.07,1.86]
        H.difference(shelf,[H.prism('reading_shelf_actual_open_recess',H.rectangle(1.87,b,b+.68),at,(1,0),(0,1),(-.09,.31),None,r)for b in levels],'open_bookcase_joinery');H.finish(shelf,.003)
        for row,b in enumerate(levels):
            for k in range(7):
                x=centre+(k-3)*.24;h=.41+.06*((k+row*2)%4);prism('reading_shelf_indoor_bound_volume',H.rectangle(.193,b+.013,b+h),(x,-1.75),(1,0),(0,1),(.035,.245),'library_leaf'if(k+row)%3==0 else'library_binding',r,.004)
    r['architectureRevision']=6;r['purpose']='Public reading pavilion with a continuous three-void masonry loggia, genuinely recessed arrival, broad supervised reading windows, actual interior bookshelves and fitted roof/return walls';r['wallThicknessMetres']=.30;r['apertureCount']=10
    return r

BUILDERS['reading_room']=reading_room

def central_control():
    palette('starlight_control',{'ivory':(.65,.77,.85,1),'mint':(.29,.60,.68,1),'stone':(.80,.89,.92,1),'glass':(.24,.51,.65,1),'copper':(.55,.75,.79,1),'iron':(.17,.31,.38,1)});zinc_material((.60,.76,.81,1));r=K.root('designed_starlight_control_observation_core_v6')
    poly=[(-5.48,-2.88),(-4.40,-4.12),(4.40,-4.12),(5.48,-2.88),(5.48,2.88),(4.40,4.12),(-4.40,4.12),(-5.48,2.88)]
    base=shell('control_continuous_chamfered_service_base',poly,.025,3.06,.27,'mint',r)
    cut_windows(base,[('control_access_recessed_door',(0,-4.12),(1,0),(0,1),1.62,.035,2.69,False,True),*[( 'control_service_daylight_lite',(x,-4.12),(1,0),(0,1),1.56,1.30,2.67,True,False)for x in [-2.75,2.75]]],r)
    # One lofted outward observation band, with structural canted lower
    # transition and genuinely cut broad control-room apertures.
    band=H.shell('control_lofted_observation_band',poly,[(3.03,.05),(3.47,-.29),(5.30,-.29),(5.49,-.075)],.24,None,r);band.data.materials.append(K.M['v6_ivory'])
    fronts=[((x,-4.41),(1,0),(0,1))for x in [-2.85,0,2.85]]+[((x,4.41),(1,0),(0,-1))for x in [-2.85,0,2.85]]
    fronts +=[((x,y),(0,1),(1 if x<0 else-1,0))for x in [-5.77,5.77]for y in [-1.42,1.42]]
    cut_windows(band,[('actual_high_control_observation_aperture',at,t,n,2.35,3.70,5.11,False,False)for at,t,n in fronts],r,cutDepth=.72)
    rim=H.offset(poly,-.15);n=len(rim);v=[(x,y,z)for z,scale in [(5.48,1),(5.67,1.016),(5.98,.90)]for x,y in [(a*scale,b*scale)for a,b in rim]]
    f=[tuple(reversed(range(n))),tuple(range(2*n,3*n)),*[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i)for k in range(2)for i in range(n)]]
    roof=mesh('single_closed_faceted_control_roof_cap',v,f,'zinc',r,.009);surface_uv(roof)
    edge=H.offset(poly,-.25);H.bar('control_continuous_load_transition_edge',[(x,y,3.43)for x,y in edge+[edge[0]]],.085,.105,'copper',r)
    # Compact real mast and two crossbars communicate operations equipment.
    for x in [-.83,.83]:H.bar('control_roof_mast_bracing',[(x,1.42,6.00),(0,1.42,6.53)],.048,.053,'iron',r)
    H.bar('control_roof_actual_antenna_mast',[(0,1.42,5.97),(0,1.42,7.14)],.06,.065,'iron',r)
    for z,w in [(6.72,.68),(7.01,.48)]:H.bar('control_roof_signal_antenna_crossbar',[(-w,1.42,z),(w,1.42,z)],.032,.04,'copper',r)
    r['architectureRevision']=6;r['purpose']='Starlight control operations volume: chamfered service base, structurally lofted observation glazing, fitted faceted cap and actual supported signal mast; no added gameplay room or control interaction';r['wallThicknessMetres']=.27;r['apertureCount']=13
    return r

BUILDERS['central_control']=central_control

def service_lodge():
    palette('perimeter_lodge',{'ivory':(.86,.79,.63,1),'mint':(.36,.57,.53,1),'stone':(.90,.83,.68,1),'copper':(.62,.49,.29,1)});zinc_material((.35,.57,.53,1));r=K.root('designed_roadside_service_observation_lodge_v6')
    poly=[(-2.35,-2.05),(1.42,-2.05),(2.22,-1.42),(2.42,-.66),(2.42,.72),(2.22,1.46),(1.42,2.05),(-2.35,2.05)]
    def underside(x):return 2.94+.052*(x+2.35)
    wall=shell('lodge_single_continuous_faceted_roadside_wall',poly,.025,2.94,.20,'ivory',r)
    for v in wall.data.vertices:
        if v.co.z>2.939:v.co.z=underside(v.co.x)
    wall.data.update()
    specs=[('service_lodge_staff_entry',(0,-2.05),(1,0),(0,1),1.10,.035,2.30,False,True)]
    for i in [2,3,4]:
        a,b=Vector(poly[i]),Vector(poly[i+1]);t=(b-a).normalized();at=tuple((a+b)*.5);specs.append(('road_facing_deep_observation_lite',at,tuple(t),(-t.y,t.x),(b-a).length-.24,.88,2.47,False,False))
    cut_windows(wall,specs,r)
    ring=H.offset(poly,-.20);n=len(ring);v=[(x,y,underside(x)+dz)for dz in [0,.14]for x,y in ring]
    roof=mesh('single_closed_faceted_fall_lodge_roof',v,[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'zinc',r,.008);surface_uv(roof)
    line=[(x,y,underside(x)+.065)for x,y in ring+[ring[0]]];H.bar('lodge_resolved_continuous_drip_edge',line,.052,.066,'copper',r)
    plinth=H.shell('lodge_continuous_grounded_stone_skirt',poly,[(-.12,-.025),(.025,-.045),(.21,-.025)],.15,None,r);plinth.data.materials.append(K.M['v6_stone']);H.difference(plinth,[H.prism('lodge_staff_entry_kept_flush',H.rectangle(1.20,-.23,.30),(0,-2.05),(1,0),(0,1),(-.13,.34),None,r)],'no_lodge_threshold_obstruction');H.finish(plinth,.006)
    r['architectureRevision']=6;r['purpose']='Roadside guard/service lodge with a genuinely faceted wraparound road-facing observation bay, fitted one-fall closed roof and separate recessed staff door; no new destination';r['wallThicknessMetres']=.20;r['apertureCount']=4
    return r

BUILDERS['service_lodge']=service_lodge

def clockwork_return_threshold():
    """Open signal bridge with grounded side shoes and a perforated steel span."""
    palette('signal_bridge',{'copper':(.77,.53,.25,1),'ivory':(.94,.87,.67,1),'stone':(.83,.76,.62,1),'mint':(.96,.26,.17,1)})
    zinc_material((.38,.58,.54,1))
    r=K.root('clockwork_signal_bridge')
    for side in (-1,1):
        x=side*6.15
        footing=[(-.33,.005),(.33,.005),(.33,.20),(.29,.30),(-.29,.30),(-.33,.20)]
        prism('stepped_stone_column_shoe',footing,(x,0),(1,0),(0,1),(-.29,.29),'stone',r,.014)
        # The inward knee and vertical column share the same extruded section.
        outer=[(side*u,z)for u,z in [(5.93,.27),(6.37,.27),(6.37,5.58),(4.02,5.58),(4.02,5.26),(4.58,5.17),(5.22,4.84),(5.65,4.37),(5.93,3.83)]]
        column=prism('integral_steel_knee_column',outer,(0,0),(1,0),(0,1),(-.23,.23),'zinc',r,0)
        void=[(side*u,z)for u,z in [(5.68,4.89),(5.98,4.37),(6.03,5.24),(4.89,5.24)]]
        H.difference(column,[H.prism('knee_structural_opening',void,(0,0),(1,0),(0,1),(-.37,.37),None,r)],'pierced_knee')
        H.finish(column,.012)
        # Signal arms are sculptural wayfinding cues at the public opening.
        prism('tapered_semaphore_mast',[(-.10,5.95),(.10,5.95),(.075,7.08),(0,7.22),(-.075,7.08)],(x,0),(1,0),(0,1),(-.10,.10),'ivory',r,.008)
        arm=[(side*u,z)for u,z in [(0,6.87),(.82,6.60),(.94,6.68),(.89,6.84),(0,7.04)]]
        prism('profiled_semaphore_arm',arm,(x,0),(1,0),(0,1),(-.175,-.075),'mint',r,.010)
        lever=[(side*u,z)for u,z in [(0,6.41),(.58,6.41),(.68,6.50),(.57,6.59),(0,6.59)]]
        prism('profiled_lower_signal_arm',lever,(x,0),(1,0),(0,1),(.075,.177),'copper',r,.010)
    for y in (-.27,.27):
        # Triangular daylight holes pass through the steel web itself.
        web=prism('single_perforated_lattice_web',[(-6.38,5.30),(6.38,5.30),(6.38,6.10),(4.5,6.20),(-4.5,6.20),(-6.38,6.10)],(0,y),(1,0),(0,1),(-.055,.055),'zinc',r,0)
        holes=[]
        for i in range(12):
            left=-6.04+i*1.01
            a,b=(5.48,6.00) if i%2==0 else (6.00,5.48)
            section=[(left+.08,a),(left+.93,a),(left+.50,b)]
            holes.append(H.prism('steel_web_open_triangle',section,(0,y),(1,0),(0,1),(-.14,.14),None,r))
        H.difference(web,holes,'through_lattice_web')
        H.finish(web,.008)
        H.bar('formed_lower_flange',[(-6.38,y,5.31),(6.38,y,5.31)],.17,.095,'copper',r)
    H.bar('continuous_crown_connecting_both_webs',[(-6.36,0,6.095),(-4.5,0,6.195),(4.5,0,6.195),(6.36,0,6.095)],.64,.10,'zinc',r)
    r['architectureRevision']=6
    r['purpose']='Clockwork pedestrian connection as a steel signal bridge with a clear central route and integrated pierced knee columns'
    return r

BUILDERS['clockwork_return_threshold']=clockwork_return_threshold

def mirror_waiting():
    """Glazed queue pavilion on the existing waiting-room footprint."""
    palette('mirror_waiting',{'ivory':(.77,.68,.79,1),'stone':(.90,.83,.82,1),'iron':(.50,.38,.56,1),'copper':(.83,.56,.34,1),'wood':(.63,.44,.34,1),'frost':(.62,.78,.85,1)})
    zinc_material((.51,.39,.58,1))
    r=K.root('mirror_waiting_octagonal_lantern_pavilion')
    poly=[(-2.48,-4.43),(2.48,-4.43),(4.43,-2.48),(4.43,2.48),(2.48,4.43),(-2.48,4.43),(-4.43,2.48),(-4.43,-2.48)]
    wall=shell('continuous_cut_stone_pavilion_enclosure',poly,.025,3.17,.25,'ivory',r)
    specs=[('pavilion_public_door',(0,-4.43),(1,0),(0,1),1.88,.035,2.68,False,True)]
    for i in range(len(poly)):
        a,b=Vector(poly[i]),Vector(poly[(i+1)%len(poly)])
        tangent=(b-a).normalized();normal=(-tangent.y,tangent.x)
        positions=[a.lerp(b,f) for f in ((.145,.855) if i==0 else (.24,.76) if i%2==0 else (.5,))]
        width=1.24 if i==0 else 1.92 if i%2==0 else 1.88
        for at in positions:
            specs.append(('pavilion_seating_bay',tuple(at),tuple(tangent),normal,width,.72,2.79,False,False))
    cut_windows(wall,specs,r)
    glass=K.M['v6_glass'].copy();glass.name='architecture6_waiting_clear_glass'
    bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.70,.85,.92,.12);bs.inputs['Alpha'].default_value=.12;bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.10
    for obj in r.children_recursive:
        if obj.type=='MESH' and obj.name.startswith('pavilion_seating_bay_actual_glass_depth'):
            obj.data.materials.clear();obj.data.materials.append(glass)
    # The lower roof is a closed ring section with a real throat for the raised lantern.
    eave=H.offset(poly,-.18);lantern=[(x*.45,y*.45)for x,y in poly];n=len(poly)
    vertices=[(x,y,z)for shape,z in [(eave,3.22),(lantern,3.89),(eave,3.08),(lantern,3.75)]for x,y in shape]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    lower=mesh('eight_fitted_folded_roof_planes',vertices,faces,'zinc',r,.008);surface_uv(lower)
    H.bar('continuous_formed_eave',[(x,y,3.15) for x,y in eave+[eave[0]]],.08,.085,'copper',r)
    monitor=H.shell('continuous_glazed_lantern_frame',lantern,[(3.79,0),(4.27,0)],.11,None,r);monitor.data.materials.append(K.M['v6_ivory'])
    openings=[]
    for i in range(n):
        a,b=Vector(lantern[i]),Vector(lantern[(i+1)%n]);t=(b-a).normalized()
        at=tuple((a+b)*.5);normal=(-t.y,t.x);width=(b-a).length-.25
        opening=H.rectangle(width,3.91,4.19)
        openings.append(H.prism('lantern_daylight_void',opening,at,tuple(t),normal,(-.10,.26),None,r))
        H.ring('lantern_glazing_frame',H.rectangle(width+.075,3.88,4.22),H.rectangle(width-.035,3.925,4.175),at,tuple(t),normal,(-.014,.045),'copper',r)
        prism('lantern_diffusing_recessed_pane',H.rectangle(width-.04,3.92,4.18),at,tuple(t),normal,(.035,.065),'frost',r,0)
    H.difference(monitor,openings,'pierced_lantern_daylight_band');H.finish(monitor,.007)
    roof_eave=H.offset(lantern,-.13);cap=[(x*.62,y*.62)for x,y in lantern]
    vertices=[(x,y,z)for shape,z in [(roof_eave,4.27),(cap,4.54),(roof_eave,4.17),(cap,4.44)]for x,y in shape]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j)])
    faces.extend([tuple(range(n,2*n)),tuple(reversed(range(3*n,4*n)))])
    top=mesh('continuous_folded_lantern_cap',vertices,faces,'zinc',r,.008);surface_uv(top)
    floor_outline=H.offset(poly,.06)
    vertices=[(x,y,z)for z in [-.02,.035]for x,y in floor_outline]
    mesh('continuous_waiting_room_floor',vertices,[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'stone',r,0)
    # Seats follow the side walls and keep the straight entry aisle clear.
    for side in [-1,1]:
        x=side*2.96
        profile=[(.28,.44),(-.28,.44),(-.28,.50),(.18,.50),(.23,.93),(.33,.93)]
        section=[(x+side*u,z)for u,z in profile]
        prism('shaped_waiting_bench_seat_and_back',section,(0,0),(1,0),(0,1),(-1.42,1.42),'wood',r,.016)
        for y in [-1.12,1.12]:
            support=[(x-.24,.04),(x+.24,.04),(x+.21,.13),(x+.12,.45),(x-.12,.45),(x-.21,.13)]
            prism('cast_waiting_bench_support',support,(0,y),(1,0),(0,1),(-.065,.065),'iron',r,.01)
    r['architectureRevision']=6
    r['purpose']='Enclosed octagonal waiting pavilion with real daylight apertures, a raised lantern roof, and seating visible beside the original door'
    return r

BUILDERS['mirror_waiting']=mirror_waiting

def mirror_maze():
    """Folded auditorium shell behind the existing sculpted mask entrance."""
    palette('mirror_maze',{'ivory':(.70,.62,.76,1),'stone':(.89,.76,.70,1),'iron':(.45,.35,.52,1),'glass':(.37,.59,.70,1),'copper':(.77,.57,.32,1)})
    zinc_material((.52,.40,.64,1))
    r=K.root('mirror_maze_folded_show_shell')
    outline=[(-8.02,-9.10),(8.02,-9.10),(8.02,-6.8),(7.58,-5.6),(7.58,.8),(8.02,2.0),(8.02,7.6),(6.74,9.04),(-6.74,9.04),(-8.02,7.6),(-8.02,2.0),(-7.58,.8),(-7.58,-5.6),(-8.02,-6.8)]
    # One continuous asymmetrical roof. The low shoulders fit behind the two
    # tall existing mask pediments while the rear retains the same room depth.
    profile=[(-8.23,3.83),(-6.02,4.39),(-4.15,5.88),(-2.08,5.57),(.05,5.08),(2.35,5.32),(4.22,5.66),(6.14,4.47),(8.23,3.83)]
    profile_below=[(x,z-.145)for x,z in profile]
    roof=prism('closed_continuous_folded_show_roof',profile_below+list(reversed(profile)),(0,0),(1,0),(0,1),(-9.20,9.23),'zinc',r,.010)
    surface_uv(roof)
    body=shell('continuous_canted_mirror_theatre_wall',outline,.025,6.1,.27,'ivory',r)
    limit=H.prism('fitted_show_wall_trim_volume',[(-8.23,-.16),(8.23,-.16),*reversed([(x,z+.013) for x,z in profile_below])],(0,0),(1,0),(0,1),(-9.41,9.42),None,r)
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active=body
    modifier=body.modifiers.new('wall_fits_under_folded_roof','BOOLEAN')
    modifier.operation='INTERSECT'
    modifier.solver='EXACT'
    modifier.object=limit
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(limit,do_unlink=True)
    cuts=[H.prism('existing_mask_entry_clearance',elliptical_arch(3.02,-.10,2.52,3.88,24),(0,-9.10),(1,0),(0,1),(-.10,.49),None,r)]
    specs=[]
    for side in [-1,1]:
        for y in [-3.9,-.82]:
            at=(side*7.58,y);normal=(-side,0)
            specs.append(('reflective_recessed_side_aperture',at,(0,1),normal,2.17,.90,3.05,False,False))
        specs.append(('rear_light_well', (side*3.55,9.04),(1,0),(0,-1),1.82,1.32,2.82,False,False))
    for name,at,tan,normal,w,b,t,_,_ in specs:
        cuts.append(H.prism(name+'_wall_void',H.rectangle(w,b,t),at,tan,normal,(-.11,.49),None,r))
    H.difference(body,cuts,'actual_show_shell_openings');H.finish(body,.008)
    for spec in specs:window(*spec[:7],r,*spec[7:])
    for x,z in profile[1:-1]:
        H.bar('standing_seam_along_fold_ridge',[(x,-8.99,z+.014),(x,9.19,z+.014)],.032,.029,'copper',r)
    for y in [-9.17,9.20]:
        H.bar('folded_roof_profile_edge',[(x,y,z-.066)for x,z in profile],.072,.085,'zinc',r)
    r['architectureRevision']=6
    r['purpose']='Asymmetric folded mirror theatre behind the preserved sculptural mask entry, with recessed canted side bays and actual window openings'
    return r

BUILDERS['mirror_maze']=mirror_maze

def carnival_return_threshold():
    palette('festival_connection',{'ivory':(.95,.88,.74,1),'stone':(.83,.72,.57,1),'copper':(.86,.54,.27,1),'mint':(.64,.22,.36,1)})
    dyed_cloth('gateway_canvas_coral',(.77,.17,.27,1))
    dyed_cloth('gateway_canvas_cream',(.92,.81,.63,1))
    r=K.root('carnival_twin_mast_canvas_gateway')
    for side in [-1,1]:
        x=side*6.15
        shoe=H.rectangle(.62,.012,.26)
        prism('stepped_festival_mast_foot',shoe,(x,0),(1,0),(0,1),(-.28,.28),'stone',r,.021)
        section=[(-.18,.23),(.18,.23),(.13,5.45),(.15,6.30),(.07,6.78),(0,6.92),(-.07,6.78),(-.15,6.30),(-.13,5.45)]
        prism('continuous_tapered_canopy_mast',section,(x,0),(1,0),(0,1),(-.13,.13),'mint',r,.014)
        for y in [-.60,.60]:
            H.bar('mast_to_membrane_tension_stay',[(x,0,6.75),(x,y,6.28)],.032,.032,'copper',r)
    # Patterned closed membrane. Its plan and height both draw inward at the
    # attachment points, and a crowned cross-section drains to both edges.
    columns=49;rows=9
    def roof_point(i,j,dz=0):
        u=i/(columns-1)*2-1;v=j/(rows-1)*2-1
        return (6.15*u,v*(.60+1.05*(1-u*u)),5.04+1.24*u*u+.31*(1-v*v)*(1-u*u)+dz)
    vertices=[roof_point(i,j,dz)for dz in [0,-.056]for i in range(columns)for j in range(rows)]
    layer=columns*rows;faces=[];slots=[]
    for i in range(columns-1):
        for j in range(rows-1):
            k=i*rows+j;quad=(k,k+rows,k+rows+1,k+1)
            faces.extend([quad,tuple(v+layer for v in reversed(quad))]);slots.extend([i//4%2]*2)
    edges=[*(i*rows for i in range(columns)),*(layer-rows+j for j in range(1,rows)),*(i*rows+rows-1 for i in range(columns-2,-1,-1)),*range(rows-2,0,-1)]
    for u,v in zip(edges,edges[1:]+edges[:1]):
        faces.append((u,u+layer,v+layer,v));slots.append((u//rows)//4%2)
    canopy=mesh('sewn_two_colour_closed_tension_canopy',vertices,faces,'gateway_canvas_coral',r,0)
    canopy.data.materials.append(K.M['v6_gateway_canvas_cream'])
    for face,slot in zip(canopy.data.polygons,slots):
        face.material_index=slot
        face.use_smooth=len({v//layer for v in face.vertices})==1
    for j in [0,rows-1]:
        H.bar('continuous_fabric_edge_tension_cable',[roof_point(i,j,-.024)for i in range(columns)],.040,.042,'copper',r)
    r['architectureRevision']=6
    r['purpose']='Festival connection marked by a wide striped fabric saddle between two tension masts'
    return r

def mirrors_return_threshold():
    palette('mirror_connection',{'ivory':(.86,.74,.86,1),'stone':(.83,.76,.80,1),'copper':(.88,.63,.36,1),'glass':(.43,.68,.76,1)})
    zinc_material((.46,.34,.62,1))
    r=K.root('mirror_midway_deco_reflector_portal')
    # Offset sculpted pylons set the direction of the long swept lintel.
    for side in [-1,1]:
        x=side*6.15;high=7.46 if side<0 else 5.82
        section=[(-.31,.015),(.31,.015),(.29,2.22),(.42,3.26),(.33,high-.50),(.14,high),(-.26,high-.52),(-.33,4.42),(-.28,2.30)]
        pylon=prism('continuous_tapered_deco_pylon',[(side*u,z)for u,z in section],(x,0),(1,0),(0,1),(-.27,.27),'ivory',r,0)
        outline=H.rectangle(.24,3.58,high-.64)
        pane=H.prism('pylon_mirror_recess',outline,(x,0),(1,0),(0,1),(-.35,-.12),None,r)
        H.difference(pylon,[pane],'deep_reflector_inset');H.finish(pylon,.009)
        prism('recessed_reflector_glazing',H.rectangle(.219,3.60,high-.66),(x,0),(1,0),(0,1),(-.145,-.126),'glass',r,0)
    profile=[(x,.64*(1-(x/6.15)**2),5.08+.25*(1-(x/6.15)**2)-.062*x)for x in [-6.15,-5.1,-4,-2.8,-1.4,0,1.4,2.8,4,5.1,6.15]]
    H.bar('closed_swept_deco_marquee',profile,.88,.40,'zinc',r)
    for side in [-1,1]:
        H.bar('folded_marquee_metal_edge',[(x,y+side*.45,z+.055)for x,y,z in profile],.055,.090,'copper',r)
    r['architectureRevision']=6
    r['purpose']='Mirror zone connection with an asymmetric stepped reflector pylon pair and swept Deco marquee'
    return r

def starlight_return_threshold():
    palette('orbit_connection',{'ivory':(.95,.93,.86,1),'stone':(.71,.76,.82,1),'copper':(.35,.68,.82,1),'frost':(.59,.80,.88,1)})
    zinc_material((.39,.56,.69,1))
    r=K.root('starlight_folded_orbit_pylon_gateway')
    for side in [-1,1]:
        # The folded load-bearing fins widen high above the through route.
        section=[(5.85,.014),(6.46,.014),(6.46,1.93),(6.30,4.07),(5.72,6.12),(4.72,7.10),(4.47,7.08),(4.99,5.57),(5.58,3.65),(5.85,1.84)]
        prism('shaped_orbital_load_bearing_fin',[(side*x,z)for x,z in section],(0,0),(1,0),(0,1),(-.285,.285),'ivory',r,.020)
    # A hollow ribbon whose sweep changes both depth and section. The lower
    # edge stays above the visitor route and meets the tapered fin shoulders.
    samples=33;vertices=[]
    for i in range(samples):
        u=i/(samples-1)*2-1;x=5.96*u
        y=.48*math.sin(math.pi*u);z=5.40+1.40*(1-u*u)
        vertices.extend([(x,y-.48,z-.11),(x,y-.51,z+.14),(x,y+.51,z+.14),(x,y+.48,z-.11)])
    faces=[(3,2,1,0),tuple(range(len(vertices)-4,len(vertices)))]
    for i in range(samples-1):
        faces.extend([(i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j)for j in range(4)])
    ribbon=mesh('closed_orbit_ribbon_shell',vertices,faces,'zinc',r,.014)
    surface_uv(ribbon)
    for side in [-1,1]:
        points=[(5.96*u,.48*math.sin(math.pi*u)+side*.494,5.40+1.40*(1-u*u)+.014)for u in [i/16-1 for i in range(33)]]
        H.bar('recessed_frosted_orbit_ribbon_edge',points,.043,.055,'frost',r)
    r['architectureRevision']=6
    r['purpose']='Space zone connection with swept aerodynamic fins and a raised orbit ribbon'
    return r

BUILDERS.update(carnival_return_threshold=carnival_return_threshold,mirrors_return_threshold=mirrors_return_threshold,starlight_return_threshold=starlight_return_threshold)

def mirror_observatory_support():
    palette('observatory_structure',{'ivory':(.79,.69,.82,1),'stone':(.87,.77,.81,1),'copper':(.77,.55,.31,1)})
    zinc_material((.51,.36,.60,1))
    r=K.root('mirror_observatory_actual_load_paths')
    # Closed ring girder under the existing deck. Its upper shelf touches
    # the deck underside at 5.65 m, and the brackets reach the outer columns.
    section=[(6.27,5.66),(6.70,5.66),(6.70,5.52),(6.49,5.52),(6.41,5.31),(6.23,5.31),(6.23,5.45),(6.31,5.45)]
    steps=72;n=len(section)
    verts=[(radius*math.cos(i*math.tau/steps),radius*math.sin(i*math.tau/steps),z)for i in range(steps)for radius,z in section]
    faces=[(i*n+j,i*n+(j+1)%n,((i+1)%steps)*n+(j+1)%n,((i+1)%steps)*n+j)for i in range(steps)for j in range(n)]
    ring=mesh('continuous_cast_ring_girder_under_observation_deck',verts,faces,'zinc',r,.006)
    for face in ring.data.polygons:face.use_smooth=True
    for i in range(1,12):
        angle=i*math.tau/12
        radial=(math.cos(angle),math.sin(angle));lateral=(-radial[1],radial[0])
        section=[(6.22,5.61),(7.10,5.61),(7.10,4.85),(6.91,4.85),(6.79,5.04),(6.59,5.24),(6.22,5.41)]
        prism('one_piece_observatory_deck_bearing_bracket',section,(0,0),radial,lateral,(-.12,.12),'zinc',r,.012)
        cap=[(6.82,9.88),(7.15,9.88),(7.85,9.97),(7.85,10.07),(7.02,10.62),(6.82,10.62)]
        prism('column_head_to_fitted_radial_canopy',cap,(0,0),radial,lateral,(-.095,.095),'zinc',r,.012)
    # The former central pillar crossed the 2.10 m stair width. A shaped
    # crossbeam at the crown carries this canopy bay between adjacent posts.
    x=7*math.cos(math.pi/6)
    profile=[(-3.50,9.89),(-3.50,10.45),(-2.6,10.53),(-1.5,10.66),(0,10.69),(1.5,10.66),(2.6,10.53),(3.50,10.45),(3.50,9.89),(2.62,10.20),(1.5,10.40),(0,10.47),(-1.5,10.40),(-2.62,10.20)]
    prism('shaped_transfer_arch_above_stair_landing',profile,(x,0),(0,1),(1,0),(-.105,.105),'zinc',r,.014)
    prism('outward_canopy_support_above_clear_stair',[(x-.09,10.52),(7.92,9.94),(7.95,10.04),(7.04,10.55),(x-.09,10.66)],(0,0),(1,0),(0,1),(-.09,.09),'zinc',r,.012)
    for y in [-1.05,1.05]:
        for i in [1,5,9,13,17,21,25,29]:
            t=(i+.5)/32
            x=16-9.6*t
            z=5.85*(i+1)/32
            H.bar('stair_handrail_grounded_stanchion',[(x,y,z-.018),(x,y,1+5.85*t)],.055,.058,'zinc',r)
        H.bar('stair_guardrail_secondary_rail',[(15.55,y,.82),(6.47,y,6.36)],.040,.045,'copper',r)
    r['architectureRevision']=6
    r['purpose']='Annular deck girder and curved canopy load paths around an unobstructed stair landing'
    return r

BUILDERS['mirror_observatory_support']=mirror_observatory_support

def perimeter_service_gateway():
    palette('service_road_gateway',{'ivory':(.83,.78,.61,1),'stone':(.76,.73,.61,1),'copper':(.55,.44,.28,1),'wood':(.64,.53,.39,1)})
    zinc_material((.34,.57,.51,1))
    r=K.root('service_road_fitted_ventilated_canopy')
    for x in [-3.9,3.9]:
        # Same road envelope: rounded structural shoes and splayed pier heads.
        profiles=[(.34,.43,.01),(.34,.43,.29),(.27,.35,.46),(.23,.34,3.69),(.29,.42,4.08),(.34,.46,4.35)]
        verts=[]
        for rx,ry,z in profiles:
            verts.extend((x+rx*math.cos(i*math.tau/12),ry*math.sin(i*math.tau/12),z)for i in range(12))
        faces=[tuple(reversed(range(12))),tuple(range(len(verts)-12,len(verts)))]
        for ring in range(len(profiles)-1):
            faces.extend([(ring*12+i,ring*12+(i+1)%12,(ring+1)*12+(i+1)%12,(ring+1)*12+i)for i in range(12)])
        pier=mesh('continuous_cast_stone_service_pier',verts,faces,'stone',r,.008)
        for face in pier.data.polygons:face.use_smooth=True
        for side in [-1,1]:
            support=[(side*u,z)for u,z in [(0,4.61),(.82,4.53),(.82,4.36),(.49,4.20),(.30,4.08),(0,3.83)]]
            prism('shaped_eave_bearing_arm',support,(x,0),(0,1),(1,0),(-.16,.16),'copper',r,.009)
    # Single closed folded section with matching underside and deep drip.
    top=[(-1.64,4.38),(-1.43,4.50),(-.88,4.68),(0,4.88),(.90,4.72),(1.47,4.53),(1.65,4.42)]
    below=[(y,z-.13)for y,z in top]
    roof=prism('single_closed_folded_service_road_roof',below+list(reversed(top)),(0,0),(0,1),(1,0),(-4.66,4.66),'zinc',r,.012)
    surface_uv(roof)
    beam=[(-.34,4.25),(.34,4.25),(.32,4.60),(.22,4.75),(-.22,4.75),(-.32,4.60)]
    prism('continuous_formed_spanning_box_beam',beam,(0,0),(0,1),(1,0),(-4.18,4.18),'wood',r,.012)
    for x in [-3.9,-1.42,1.42,3.9]:
        section=[(y,z-.134)for y,z in top]+list(reversed([(y,z-.21)for y,z in top]))
        prism('shaped_roof_bearing_rib',section,(x,0),(0,1),(1,0),(-.07,.07),'wood',r,.006)
    for y,z in [top[0],top[-1]]:
        H.bar('continuous_metal_drip_at_roof_eave',[(-4.65,y,z-.052),(4.65,y,z-.052)],.064,.075,'copper',r)
    r['architectureRevision']=6
    r['purpose']='Fitted service-road canopy on cast piers and load-bearing ribs, with a full-width open road'
    return r

BUILDERS['perimeter_service_gateway']=perimeter_service_gateway

def fairytale_castle_gateway():
    palette('garden_gatehouse',{'ivory':(.89,.78,.79,1),'stone':(.85,.78,.73,1),'roof':(.56,.73,.90,1),'copper':(.85,.60,.28,1),'glass':(.36,.53,.70,1)})
    zinc_material((.48,.63,.86,1))
    r=K.root('fairytale_castle_gatehouse_real_vault')
    steps=32
    for side,shift in [(-1,.64),(1,0)]:
        x=side*9
        wallplan=[(x+2.55*math.cos((i+.5)*math.tau/steps),2.55*math.sin((i+.5)*math.tau/steps))for i in range(steps)]
        section=[(.02,-.115),(.33,-.115),(.63,-.018),(6.85,0),(7.16,-.15),(7.37,-.17),(8.87+shift,-.07),(9.08+shift,-.12)]
        tower=H.shell('one_piece_masonry_turret_with_belled_cornice',wallplan,section,.32,None,r)
        tower.data.materials.append(K.M['v6_ivory'])
        specs=[]
        for angle in [-math.pi/2,math.pi/2,0 if side==1 else math.pi]:
            direction=Vector((math.cos(angle),math.sin(angle)));t=(-direction.y,direction.x)
            for height in [2.91,6.02]:
                at=(x+2.54*direction.x,2.54*direction.y)
                specs.append((at,t,tuple(-direction),.72,height,1.30,'window'))
        cutters=[]
        for at,tangent,normal,width,bottom,height,_ in specs:
            shape=H.arch(width,bottom,height,9)
            cutters.append(H.prism('tower_true_recessed_lancet_void',shape,at,tangent,normal,(-.16,.56),None,r))
            H.ring('tower_continuous_deep_lancet_jamb',H.arch(width+.19,bottom-.08,height+.16,9),H.arch(width-.022,bottom+.011,height-.020,9),at,tangent,normal,(-.07,.16),'stone',r)
            prism('tower_lancet_recessed_glazing',H.arch(width-.062,bottom+.033,height-.06,9),at,tangent,normal,(.254,.284),'glass',r,0)
        H.difference(tower,cutters,'tower_true_lancet_openings')
        H.finish(tower,.005)
        roof_base=9.04+shift
        section=[(2.82,0),(2.84,.13),(2.64,.32),(2.24,.62),(1.80,1.03),(1.34,1.54),(.94,2.14),(.57,2.79),(.32,3.45),(.145,4.01),(.055,4.32)]
        verts=[(x+radius*math.cos(i*math.tau/steps),radius*math.sin(i*math.tau/steps),roof_base+z)for radius,z in section for i in range(steps)]
        faces=[tuple(reversed(range(steps))),tuple(range(len(verts)-steps,len(verts)))]
        for row in range(len(section)-1):
            faces.extend([(row*steps+i,row*steps+(i+1)%steps,(row+1)*steps+(i+1)%steps,(row+1)*steps+i)for i in range(steps)])
        roof=mesh('closed_flared_storybook_turret_roof',verts,faces,'roof',r,0)
        for f in roof.data.polygons:f.use_smooth=len(f.vertices)==4
        # Preserve the full walk width at ground level. The deeper stone
        # arch projects above the pier collar, well above player head height.
        pier=[(side*u,z)for u,z in [(5.59,.018),(6.40,.018),(6.40,.24),(6.34,.41),(6.31,3.63),(5.66,3.63),(5.68,.41),(5.59,.24)]]
        prism('single_stepped_vault_spring_pier',pier,(0,0),(1,0),(0,1),(-.415,.415),'stone',r,.012)
        shoulder=[(-.40,2.87),(.40,2.87),(.59,3.18),(1.15,3.56),(1.19,3.68),(-1.19,3.68),(-1.15,3.56),(-.59,3.18)]
        prism('splayed_stone_pier_head_under_the_vault',shoulder,(side*5.995,0),(0,1),(1,0),(-.321,.321),'stone',r,.009)
    left=-6.62;right=6.62
    crown=[(right,9.60),(5.60,9.60),(5.60,10.03),(4.86,10.03),(4.86,9.60),(3.64,9.60),(3.64,10.24),(2.87,10.24),(2.87,9.94),(1.64,9.94),(1.64,10.61),(-1.64,10.61),(-1.64,9.94),(-2.87,9.94),(-2.87,10.24),(-3.64,10.24),(-3.64,9.60),(-4.86,9.60),(-4.86,10.03),(-5.60,10.03),(-5.60,9.60),(left,9.60)]
    vault=prism('thick_through_castle_gatehouse',[(left,3.58),(right,3.58),*crown],(0,0),(1,0),(0,1),(-1.20,1.20),'stone',r,0)
    through=elliptical_arch(11.32,3.22,6.68,9.31,36)
    cutters=[H.prism('actual_through_vault_clearance',through,(0,0),(1,0),(0,1),(-1.44,1.44),None,r)]
    for x in [-4.82,4.82]:
        cutters.append(H.prism('deep_gatehouse_watch_opening',H.arch(.62,8.58,.88,16),(x,0),(1,0),(0,1),(-1.44,1.44),None,r))
    H.difference(vault,cutters,'true_gatehouse_vault_and_sight_openings');H.finish(vault,.012)
    band=elliptical_arch(11.82,3.58,6.68,9.54,36)
    inner=elliptical_arch(11.34,3.60,6.68,9.32,36)
    # Skip the floor edge so the trim is open at both spring piers.
    band=[band[1],*band[2:],band[0]]
    inner=[inner[1],*inner[2:],inner[0]]
    for side in [-1,1]:
        prism('deep_vault_archivolt',band+list(reversed(inner)),(0,side*1.20),(1,0),(0,-side),(-.16,.055),'ivory',r,.006)
    r['architectureRevision']=6
    r['purpose']='Asymmetric masonry gatehouse with a deep through-vault, two actual towers and flared tiled roofs'
    return r

BUILDERS['fairytale_castle_gateway']=fairytale_castle_gateway

def ring_toss_kiosk(festival=False):
    palette('festival_ring_lane' if festival else 'garden_ring_lane',{'ivory':(.95,.83,.65,1),'mint':(.75,.31,.34,1) if festival else (.39,.72,.62,1),'stone':(.84,.73,.59,1),'copper':(.89,.58,.24,1),'wood':(.56,.36,.25,1)})
    zinc_material((.68,.33,.35,1) if festival else (.32,.58,.56,1))
    dyed_cloth('ring_target_lane',(.72,.33,.29,1) if festival else (.37,.61,.51,1))
    r=K.root('purpose_built_tiered_ring_toss_lane')
    footprint=[(-2.50,-2.14),(2.50,-2.14),(2.50,1.40),(2.12,2.11),(-2.12,2.11),(-2.50,1.40)]
    body=shell('continuous_wraparound_ring_lane_wall',footprint,.026,3.86,.23,'ivory',r)
    roof_top=[(-2.66,3.08),(-2.05,3.28),(-.85,3.59),(.35,3.74),(1.35,3.65),(2.14,3.46),(2.65,3.14)]
    roof=prism('closed_leaning_ring_lane_roof',[(x,z-.11)for x,z in roof_top]+list(reversed(roof_top)),(0,0),(1,0),(0,1),(-2.51,2.24),'zinc',r,.012)
    surface_uv(roof)
    # Fit the whole wall into the roof underside, including the raked ends.
    cut_section=[(-2.66,-.20),(2.65,-.20),*reversed([(x,z-.10)for x,z in roof_top])]
    clip=H.prism('ring_lane_fitted_wall_extent',cut_section,(0,0),(1,0),(0,1),(-2.48,2.22),None,r)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=body
    modifier=body.modifiers.new('ring_lane_wall_exact_roof_section','BOOLEAN')
    modifier.operation='INTERSECT';modifier.solver='EXACT';modifier.object=clip
    bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(clip,do_unlink=True)
    H.difference(body,[H.prism('wide_open_player_front',H.rectangle(4.38,-.12,2.86),(0,-2.14),(1,0),(0,1),(-.22,.51),None,r)],'full_width_ring_lane_opening')
    H.finish(body,.009)
    H.bar('finished_ring_lane_eave',[(x,-2.51,z-.053)for x,z in roof_top],.067,.074,'copper',r)
    prism('continuous_kiosk_floor',H.rectangle(4.87,-.01,.05),(0,0),(1,0),(0,1),(-2.16,2.02),'stone',r,0)
    tiers=[(-.76,.04),(1.76,.04),(1.76,1.78),(1.15,1.78),(1.15,1.48),(.53,1.48),(.53,1.18),(-.08,1.18),(-.08,.88),(-.76,.88)]
    prism('single_closed_four_step_toss_target_rack',tiers,(0,0),(0,1),(1,0),(-2.00,2.00),'ring_target_lane',r,.012)
    prism('shaped_player_leaning_rail',[(-2.21,.06),(-1.94,.06),(-1.94,.93),(-2.18,1.02),(-2.26,.97)],(0,0),(0,1),(1,0),(-2.17,2.17),'wood',r,.011)
    H.bar('rounded_player_hand_edge',[(-2.18,-2.19,.992),(2.18,-2.19,.992)],.074,.059,'copper',r)
    # The pins are single tapered lathes with real necks. Their visible rings
    # sit on the rack and front tray, well behind the spectator envelope.
    peg_profile=[(.085,0),(.10,.028),(.091,.066),(.057,.126),(.042,.20),(.066,.25),(.046,.30)]
    for row in range(4):
        for col in range(7):
            x=(col-3)*.54
            y=-.43+row*.62
            z=.88+row*.30
            n=10
            verts=[(x+rr*math.cos(i*math.tau/n),y+rr*math.sin(i*math.tau/n),z+h)for rr,h in peg_profile for i in range(n)]
            faces=[tuple(reversed(range(n))),tuple(range(len(verts)-n,len(verts)))]
            for k in range(len(peg_profile)-1):
                faces.extend([(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i)for i in range(n)])
            pin=mesh('tapered_toss_target_with_narrow_neck',verts,faces,'copper' if (col+row)%3 else 'mint',r,0)
            for f in pin.data.polygons:f.use_smooth=len(f.vertices)==4
    for x,y,z in [(-1.57,-.47,.892),(-.45,.24,1.192),(.63,.86,1.492),(1.17,1.51,1.792),(.63,-2.08,.995),(.93,-2.08,.995)]:
        points=[(x+.115*math.cos(i*math.tau/20),y+.115*math.sin(i*math.tau/20),z)for i in range(21)]
        H.bar('physical_ring_toss_loop',points,.026,.024,'stone',r)
    r['architectureRevision']=6
    r['purpose']='An open ring-toss lane with an actual stepped target rack, narrow-neck pins, individual rings, and a separate visitor rail'
    return r

BUILDERS['fairytale_ring_kiosk']=ring_toss_kiosk
BUILDERS['carnival_ring_kiosk']=lambda:ring_toss_kiosk(True)

def prize_kiosk(festival=False):
    palette('festival_prize' if festival else 'garden_prize',{'ivory':(.95,.79,.73,1) if festival else (.86,.84,.67,1),'stone':(.92,.80,.62,1),'copper':(.89,.59,.24,1),'wood':(.61,.43,.29,1),'mint':(.74,.29,.40,1) if festival else (.34,.65,.57,1),'roof':(.72,.42,.48,1) if festival else (.46,.68,.84,1)})
    zinc_material((.63,.35,.48,1) if festival else (.39,.60,.64,1))
    r=K.root('faceted_midway_prize_showcase')
    poly=[(-1.57,-2.20),(1.57,-2.20),(2.48,-1.45),(2.48,1.78),(1.89,2.17),(-1.89,2.17),(-2.48,1.78),(-2.48,-1.45)]
    body=shell('continuous_canted_prize_showcase_wall',poly,.024,3.12,.22,'ivory',r)
    specs=[('prize_showcase_display_window',(0,-2.20),(1,0),(0,1),2.62,.90,2.72,False,False),('prize_staff_door',(0,2.17),(1,0),(0,-1),.93,.035,2.39,False,True)]
    for i in [1,7]:
        a,b=Vector(poly[i]),Vector(poly[(i+1)%len(poly)]);t=(b-a).normalized()
        specs.append(('prize_showcase_display_window',tuple((a+b)*.5),tuple(t),(-t.y,t.x),.79,.95,2.69,False,False))
    cut_windows(body,specs,r)
    glass=K.M['v6_glass'].copy();glass.name='architecture6_prize_clear_glass'
    bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.70,.85,.92,.12);bs.inputs['Alpha'].default_value=.12;bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.10
    for obj in r.children_recursive:
        if obj.type=='MESH' and obj.name.startswith('prize_showcase_display_window_actual_glass_depth'):
            obj.data.materials.clear();obj.data.materials.append(glass)
    eave=H.offset(poly,-.155);crown=[(x*.34,y*.29)for x,y in eave];n=len(poly)
    vertices=[(x,y,z)for shape,z in [(eave,3.19),(crown,3.79),(eave,3.06),(crown,3.66)]for x,y in shape]
    faces=[tuple(range(n,2*n)),tuple(reversed(range(3*n,4*n)))]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j)])
    roof=mesh('fitted_hipped_showcase_roof',vertices,faces,'roof',r,.012);surface_uv(roof)
    H.bar('fitted_showcase_eave_trim',[(x,y,3.13)for x,y in eave+[eave[0]]],.061,.080,'copper',r)
    H.bar('prize_window_sloped_display_ledge',[(-1.42,-2.16,.88),(1.42,-2.16,.88)],.33,.12,'wood',r)
    floor_plan=H.offset(poly,.06)
    vertices=[(x,y,z)for z in [-.02,.035]for x,y in floor_plan]
    mesh('actual_indoor_display_floor',vertices,[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'stone',r,0)
    shelf=prism('single_joined_window_display_cabinet',H.rectangle(3.70,.05,2.72),(0,.12),(1,0),(0,1),(0,.42),'wood',r,0)
    levels=[.62,1.25,1.88]
    H.difference(shelf,[H.prism('display_shelf_recess',H.rectangle(3.42,z,z+.47),(0,.12),(1,0),(0,1),(-.12,.33),None,r)for z in levels],'shelf_actual_openings')
    H.finish(shelf,.006)
    dyed_cloth('prize_berry',(.79,.20,.36,1));dyed_cloth('prize_aqua',(.21,.55,.64,1))
    for row,z in enumerate(levels):
        for col in range(5):
            x=(col-2)*.62
            width=.36+.045*((row+col)%3);height=.28+.05*((row+2*col)%3)
            colour='prize_berry' if (col+row)%2==0 else 'prize_aqua'
            outline=H.rectangle(width,z+.006,z+height)
            prism('wrapped_display_prize',outline,(x,.08),(1,0),(0,1),(0,.245),colour,r,.024)
            prism('creased_gift_ribbon',H.rectangle(.054,z+.020,z+height+.008),(x,.08),(1,0),(0,1),(-.012,.014),'copper',r,.005)
    r['architectureRevision']=6
    r['purpose']='Enclosed faceted prize display with three real glazed openings and wrapped prizes on recessed shelves'
    return r

def carnival_can_kiosk():
    palette('festival_can_lane',{'ivory':(.95,.80,.63,1),'mint':(.73,.29,.32,1),'wood':(.63,.39,.24,1),'stone':(.90,.79,.62,1),'copper':(.79,.59,.30,1)})
    zinc_material((.39,.53,.60,1))
    r=K.root('festival_can_knockdown_target_alley')
    poly=[(-2.49,-2.12),(2.49,-2.12),(2.49,1.93),(-2.49,1.93)]
    body=shell('full_depth_target_lane_walls',poly,.025,3.25,.24,'mint',r)
    opening=elliptical_arch(4.31,-.12,2.26,2.94,23)
    holes=[H.prism('actual_open_carnival_target_lane',opening,(0,-2.12),(1,0),(0,1),(-.20,.55),None,r)]
    for side in [-1,1]:
        at=(side*2.49,.21);normal=(-side,0)
        holes.append(H.prism('side_daylight_slot',H.rectangle(1.32,2.36,2.89),at,(0,1),normal,(-.11,.46),None,r))
        H.ring('finished_side_daylight_reveal',H.rectangle(1.45,2.30,2.95),H.rectangle(1.28,2.38,2.87),at,(0,1),normal,(-.057,.12),'stone',r)
    H.difference(body,holes,'open_carnival_can_arch')
    H.finish(body,.009)
    roof=[(-2.45,3.20),(-2.32,3.34),(-.41,3.51),(2.05,3.84),(2.15,3.80),(2.15,3.69),(-.41,3.39),(-2.32,3.22)]
    prism('formed_sloped_can_lane_roof',roof,(0,0),(0,1),(1,0),(-2.64,2.64),'zinc',r,.009)
    for v in body.data.vertices:
        if v.co.z>3.249:v.co.z=3.25+max(0,v.co.y+1.98)*.108
    body.data.update()
    outer=elliptical_arch(4.57,.02,2.26,3.07,23)
    inner=elliptical_arch(4.28,.03,2.26,2.93,23)
    outer=[outer[1],*outer[2:],outer[0]];inner=[inner[1],*inner[2:],inner[0]]
    prism('contoured_arch_reveal_of_target_lane',outer+list(reversed(inner)),(0,-2.12),(1,0),(0,1),(-.09,.12),'stone',r,.008)
    prism('real_target_alley_floor',H.rectangle(4.82,-.02,.035),(0,0),(1,0),(0,1),(-2.11,1.88),'stone',r,0)
    prism('substantial_shaped_toss_counter',[(.07,-.03),(.82,-.03),(.77,.85),(.92,.99),(.92,1.09),(-.06,1.09),(-.06,.97),(.05,.84)],(0,-2.12),(0,1),(1,0),(-2.11,2.11),'wood',r,.013)
    prism('tiered_target_stands_under_cover',[(.57,.05),(1.76,.05),(1.76,1.54),(1.09,1.54),(1.09,1.26),(.57,1.26)],(0,-.96),(0,1),(1,0),(-1.95,1.95),'wood',r,.009)
    for group,x in enumerate([-1.24,0,1.24]):
        for row,count in enumerate([3,2,1]):
            for col in range(count):
                at=x+(col-(count-1)/2)*.235
                z=1.54+row*.240
                section=[(.111,z),(.117,z+.023),(.108,z+.053),(.108,z+.204),(.116,z+.223),(.110,z+.240)]
                n=12
                v=[(at+rad*math.cos(i*math.tau/n),.49+rad*math.sin(i*math.tau/n),h)for rad,h in section for i in range(n)]
                f=[tuple(reversed(range(n))),tuple(range(len(v)-n,len(v)))]
                for k in range(len(section)-1):
                    f.extend([(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i)for i in range(n)])
                can=mesh('formed_beaded_knockdown_target_can',v,f,'copper' if (group+row)%2 else 'ivory',r,0)
                for face in can.data.polygons:face.use_smooth=len(face.vertices)==4
    r['architectureRevision']=6
    r['purpose']='Open target alley with a curved reveal, high rain canopy, shaped counter and three sets of actual stacked knockdown cans'
    return r

BUILDERS.update(fairytale_prize_kiosk=prize_kiosk,carnival_prize_kiosk=lambda:prize_kiosk(True),carnival_can_kiosk=carnival_can_kiosk)

def display_glass(root,prefix):
    glass=K.M['v6_glass'].copy();glass.name='architecture6_prize_clear_glass'
    bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.70,.85,.92,.12);bs.inputs['Alpha'].default_value=.12;bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.10
    for obj in root.children_recursive:
        if obj.type=='MESH' and obj.name.startswith(prefix) and '_actual_glass_depth' in obj.name:
            obj.data.materials.clear();obj.data.materials.append(glass)

def mirrors_mask_kiosk():
    palette('mirror_mask_studio',{'ivory':(.87,.76,.85,1),'stone':(.94,.81,.72,1),'mint':(.66,.34,.58,1),'copper':(.84,.57,.31,1),'wood':(.52,.40,.47,1)})
    zinc_material((.63,.39,.65,1))
    r=K.root('masked_midway_display_pavilion')
    outline=[(-2.51,-1.08),(-1.67,-1.96),(-.71,-2.10),(.71,-2.10),(1.67,-1.96),(2.51,-1.08),(2.51,1.79),(2.12,2.10),(-2.12,2.10),(-2.51,1.79)]
    wall=shell('one_folding_wall_around_mask_displays',outline,.024,3.00,.19,'mint',r)
    specs=[]
    for i in [0,4]:
        a,b=Vector(outline[i]),Vector(outline[i+1]);t=(b-a).normalized()
        specs.append(('mask_side_recess',tuple((a+b)*.5),tuple(t),(-t.y,t.x),.79,.79,2.67,False,False))
    specs.append(('mask_front_recess',(0,-2.10),(1,0),(0,1),1.22,.82,2.64,False,False))
    specs.append(('mask_staff_door',(0,2.10),(1,0),(0,-1),.94,.035,2.36,False,True))
    cut_windows(wall,specs,r)
    display_glass(r,('mask_side_recess','mask_front_recess'))
    eave=H.offset(outline,-.14);n=len(eave)
    verts=[(x,y,z+.19*(1-(x/2.65)**2))for z in [2.99,3.13]for x,y in eave]
    for v in wall.data.vertices:
        if v.co.z>2.999:v.co.z=3.015+.19*(1-(v.co.x/2.65)**2)
    wall.data.update()
    roof=mesh('joined_cambered_mask_display_canopy',verts,[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'zinc',r,.012);surface_uv(roof)
    H.bar('faceted_brass_canopy_eave',[(x,y,3.049+.19*(1-(x/2.65)**2))for x,y in eave+[eave[0]]],.054,.075,'copper',r)
    floor_plan=H.offset(outline,.06)
    verts=[(x,y,z)for z in [-.02,.035]for x,y in floor_plan]
    mesh('continuous_floor_under_the_display',verts,[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'stone',r,0)
    for x,y,scale in [(-1.68,-.95,.64),(0,-1.39,.79),(1.68,-.95,.64)]:
        stand=[(-.37,.04),(.37,.04),(.32,.21),(.11,.29),(.06,2.07),(-.06,2.07),(-.11,.29),(-.32,.21)]
        prism('freestanding_mask_display_cradle',stand,(x,y+.22),(1,0),(0,1),(-.10,.12),'wood',r,.01)
        for row,cz in enumerate([1.27,2.02]):
            shape=[(.42*scale*math.cos(i*math.tau/24),cz+.47*scale*math.sin(i*math.tau/24))for i in range(24)]
            mask=prism('actual_pierced_collectible_mask',shape,(x,y),(1,0),(0,1),(-.040,.06),'ivory' if row==0 else 'stone',r,0)
            eyes=[H.prism('mask_eye_opening',[(dx+.084*math.cos(i*math.tau/12),cz+.11+.041*math.sin(i*math.tau/12))for i in range(12)],(x,y),(1,0),(0,1),(-.14,.13),None,r)for dx in [-.13,.13]]
            H.difference(mask,eyes,'actual_mask_eye_clearance');H.finish(mask,.006)
            H.bar('raised_sculpted_mask_nose',[(x,y-.044,cz+.11),(x+.012,y-.135,cz-.04),(x,y-.064,cz-.079)],.063,.055,'stone',r)
            H.bar('display_mask_hanging_pin',[(x,y+.05,cz-.045),(x,y+.153,cz-.045)],.047,.055,'copper',r)
    r['architectureRevision']=6
    r['purpose']='Canted mask pavilion with its own curved roof, actual transparent display bays and pierced collectible masks on interior cradles'
    return r

def clockwork_demo_kiosk():
    import theme_park_v2_kit as T
    palette('clockwork_demonstration',{'ivory':(.87,.80,.63,1),'stone':(.88,.77,.60,1),'mint':(.43,.58,.53,1),'copper':(.92,.59,.26,1),'wood':(.55,.38,.25,1)})
    brick_material();zinc_material((.42,.56,.54,1))
    r=K.root('clockwork_open_geared_demo_kiosk')
    footprint=[(-2.44,-2.05),(2.44,-2.05),(2.44,1.93),(-2.44,1.93)]
    wall=shell('continuous_brick_mechanical_demo_shell',footprint,.025,3.80,.23,'brick',r)
    holes=[H.prism('open_demonstration_front',H.rectangle(4.27,-.08,2.73),(0,-2.05),(1,0),(0,1),(-.12,.46),None,r)]
    for side in [-1,1]:
        at=(side*2.44,.27);normal=(-side,0)
        holes.append(H.prism('side_cross_light_opening',H.rectangle(1.55,1.76,2.65),at,(0,1),normal,(-.12,.49),None,r))
        H.ring('stone_sill_to_open_side_light',H.rectangle(1.70,1.68,2.73),H.rectangle(1.51,1.78,2.63),at,(0,1),normal,(-.04,.10),'stone',r)
    section=[(-2.43,3.09),(-1.03,3.24),(-.49,3.73),(.25,3.31),(2.09,3.11),(2.09,2.99),(.25,3.19),(-.49,3.59),(-1.03,3.12),(-2.43,2.97)]
    cutoff=[(-2.43,-.20),(2.09,-.20),*[(y,z+.01)for y,z in section[5:]]]
    clip=H.prism('mechanical_wall_fit_to_roof_section',cutoff,(0,0),(0,1),(1,0),(-2.59,2.59),None,r)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=wall
    modifier=wall.modifiers.new('exact_folded_wall_head','BOOLEAN')
    modifier.operation='INTERSECT';modifier.solver='EXACT';modifier.object=clip
    bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(clip,do_unlink=True)
    H.difference(wall,holes,'open_mechanical_demonstration_apertures');H.finish(wall,.009)
    prism('folded_mechanical_kiosk_steel_roof',section,(0,0),(0,1),(1,0),(-2.63,2.63),'zinc',r,.009)
    H.bar('steel_roof_rake_end_frame',[(-2.46,y,z-.066)for y,z in section[:5]],.080,.069,'copper',r)
    H.bar('steel_roof_rake_end_frame',[(2.46,y,z-.066)for y,z in section[:5]],.080,.069,'copper',r)
    prism('folded_steel_shop_bench_profile',[(0,.035),(.59,.035),(.56,.91),(.67,.99),(.67,1.11),(-.08,1.11),(-.08,1.00),(.02,.93)],(0,-2.05),(0,1),(1,0),(-2.09,2.09),'wood',r,.012)
    prism('grounded_demo_station_floor',H.rectangle(4.73,-.025,.035),(0,0),(1,0),(0,1),(-2.02,1.90),'stone',r,0)
    for x,z,rad in [(-.87,1.62,.58),(.15,1.85,.45),(1.02,1.54,.51)]:
        H.bar('raked_gear_axle_support',[(x,.53,.045),(x,.39,z)],.11,.14,'mint',r)
        H.bar('gear_axle_seated_in_support',[(x,.41,z),(x,-.03,z)],.09,.09,'zinc',r)
        T.gear(r,(x,.10,z),rad,12,'v6_copper',.15)
    r['architectureRevision']=6
    r['purpose']='Open industrial demonstration booth with cross-light openings, formed steel roof and visible gearing on its own axles'
    return r

def starlight_orbit_kiosk():
    import theme_park_v2_kit as T
    palette('starlight_orbit_display',{'ivory':(.86,.92,.92,1),'stone':(.73,.81,.83,1),'mint':(.39,.63,.70,1),'copper':(.70,.55,.28,1),'frost':(.73,.87,.94,1)})
    zinc_material((.36,.56,.75,1))
    r=K.root('starlight_low_orbit_capsule_display')
    poly=[(-1.69,-2.11),(1.69,-2.11),(2.45,-1.49),(2.58,-.40),(2.43,1.26),(1.82,2.02),(-1.82,2.02),(-2.43,1.26),(-2.58,-.40),(-2.45,-1.49)]
    body=shell('continuous_faceted_capsule_pressure_shell',poly,.025,2.79,.20,'ivory',r)
    specs=[('orbit_panorama_pane',(0,-2.11),(1,0),(0,1),2.88,.85,2.35,False,False),('orbit_technical_door',(0,2.02),(1,0),(0,-1),.96,.035,2.28,False,True)]
    for i in [1,9]:
        a,b=Vector(poly[i]),Vector(poly[(i+1)%len(poly)]);t=(b-a).normalized()
        specs.append(('orbit_panorama_pane',tuple((a+b)*.5),tuple(t),(-t.y,t.x),.62,.91,2.33,False,False))
    cut_windows(body,specs,r)
    display_glass(r,'orbit_panorama_pane_actual_glass_depth')
    eave=H.offset(poly,-.10);n=len(poly)
    rings=[(eave,2.74),([(x*.90,y*.88)for x,y in eave],2.99),([(x*.71,y*.68)for x,y in eave],3.23),([(x*.42,y*.39)for x,y in eave],3.36)]
    verts=[(x,y,z)for shape,z in rings for x,y in shape];faces=[tuple(reversed(range(n))),tuple(range(len(verts)-n,len(verts)))]
    for layer in range(len(rings)-1):
        faces.extend([(layer*n+i,layer*n+(i+1)%n,(layer+1)*n+(i+1)%n,(layer+1)*n+i)for i in range(n)])
    roof=mesh('closed_elliptic_capsule_roof',verts,faces,'zinc',r,.008);surface_uv(roof)
    H.bar('capsule_wraparound_eave_seam',[(x,y,2.756)for x,y in eave+[eave[0]]],.063,.065,'frost',r)
    H.bar('formed_panorama_display_sill',[(-1.39,-2.11,.82),(1.39,-2.11,.82)],.22,.092,'mint',r)
    floor_plan=H.offset(poly,.06)
    verts=[(x,y,z)for z in [-.02,.035]for x,y in floor_plan]
    mesh('continuous_capsule_display_floor',verts,[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'stone',r,0)
    for x,h,radius in [(-.91,1.44,.31),(0,1.55,.43),(.92,1.42,.28)]:
        section=[(-.22,.03),(.22,.03),(.22,.12),(.16,.21),(.14,h-.17),(-.14,h-.17),(-.16,.21),(-.22,.12)]
        prism('sculpted_planet_display_plinth',section,(x,-.69),(1,0),(0,1),(-.18,.18),'mint',r,.01)
        centre=h-.20+radius
        T.ball('glazed_planet_scale_model',r,(x,-.69,centre),radius,'v6_copper' if x==0 else 'v6_frost')
        points=[(x+radius*1.46*math.cos(i*math.tau/32),-.69+radius*1.10*math.sin(i*math.tau/32),centre+radius*.59*math.sin(i*math.tau/32))for i in range(33)]
        H.bar('tilted_ring_around_display_planet',points,.033,.025,'copper',r)
    r['architectureRevision']=6
    r['purpose']='Panoramic capsule kiosk with a closed layered roof and scale planets in its actual window display'
    return r

BUILDERS.update(mirrors_mask_kiosk=mirrors_mask_kiosk,clockwork_demo_kiosk=clockwork_demo_kiosk,starlight_orbit_kiosk=starlight_orbit_kiosk)
BOOTH_SLOTS={
    'fairytale_prize_kiosk':('fairytale_prize_kiosk','fairytale',(-17,-28)),
    'fairytale_ring_kiosk':('fairytale_ring_kiosk','fairytale',(17,-29)),
    'carnival_can_kiosk':('carnival_can_kiosk','carnival',(-51,-27)),
    'carnival_prize_kiosk':('carnival_prize_kiosk','carnival',(-51,-18)),
    'carnival_prize_kiosk_east':('carnival_prize_kiosk','carnival',(-42,-40)),
    'carnival_ring_kiosk':('carnival_ring_kiosk','carnival',(-51,-36)),
    'carnival_ring_kiosk_east':('carnival_ring_kiosk','carnival',(-16,-43)),
    'mirrors_mask_kiosk':('mirrors_mask_kiosk','mirrors',(-38,-35)),
    'mirrors_mask_kiosk_east':('mirrors_mask_kiosk','mirrors',(-16,-39)),
    'clockwork_demo_kiosk':('clockwork_demo_kiosk','clockwork',(-41,-37)),
    'clockwork_demo_kiosk_east':('clockwork_demo_kiosk','clockwork',(-17,-40)),
    'starlight_orbit_kiosk':('starlight_orbit_kiosk','starlight',(-36,-39)),
    'starlight_orbit_kiosk_east':('starlight_orbit_kiosk','starlight',(-13,-45)),
}

WALK_SLOTS={
    'fairytale_west_walk':('fairytale',0),
    'fairytale_east_walk':('fairytale',1),
    'carnival_covered_walk':('carnival',0),
    'mirrors_covered_walk':('mirrors',0),
    'clockwork_covered_walk':('clockwork',0),
    'starlight_covered_walk':('starlight',0),
}

def covered_visitor_walk(ident):
    from pathlib import Path
    import json
    district,index=WALK_SLOTS[ident]
    plan=Path(__file__).resolve().parents[1]/'art/space_v4/park_levels_v1/theme_park_v2/site-plan.json'
    spec=json.loads(plan.read_text(encoding='utf8'))[district]['coveredWalks'][index]
    points=[Vector(p) for p in spec['points']]
    width=spec['width']
    pigments={
        'fairytale':((.49,.65,.88,1),(.88,.76,.57,1),(.95,.82,.62,1)),
        'carnival':((.77,.22,.37,1),(.91,.62,.29,1),(.97,.86,.67,1)),
        'mirrors':((.55,.38,.68,1),(.87,.66,.36,1),(.90,.82,.85,1)),
        'clockwork':((.50,.62,.55,1),(.86,.58,.30,1),(.92,.79,.64,1)),
        'starlight':((.37,.61,.80,1),(.65,.82,.89,1),(.83,.89,.90,1)),
    }
    roof_tint,metal_tint,stone_tint=pigments[district]
    palette(ident,{'roof':roof_tint,'copper':metal_tint,'ivory':stone_tint,'stone':stone_tint})
    zinc_material(roof_tint)
    r=K.root('themed_visitor_walk_'+ident)
    sections={
        'fairytale':[(-1,3.46),(-.81,3.52),(-.59,3.79),(-.26,4.13),(0,4.57),(.26,4.13),(.59,3.79),(.81,3.52),(1,3.46)],
        'carnival':[(u,3.45+.77*math.sqrt(max(0,1-u*u)))for u in [i/6-1 for i in range(13)]],
        'mirrors':[(-1,3.45),(-.80,3.52),(-.47,3.90),(-.15,4.39),(.13,4.61),(.43,4.06),(.73,3.63),(1,3.45)],
        'clockwork':[(-1,3.45),(-.70,3.57),(-.38,3.66),(.06,4.32),(.28,4.32),(.36,3.79),(.66,3.62),(1,3.45)],
        'starlight':[(-1,3.45),(-.89,3.47),(-.70,3.73),(-.36,3.99),(0,4.09),(.36,3.99),(.70,3.73),(.89,3.47),(1,3.45)],
    }
    section=sections[district]
    profile=[(u*width/2,z)for u,z in section]
    normals=[]
    for i in range(len(points)):
        tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
        normals.append(Vector((-tangent.y,tangent.x)))
    def xyz(point,normal,x,z):
        return (point.x+normal.x*x,point.y+normal.y*x,z)
    vertices=[xyz(at,n,x,z+dz)for dz in [0,-.095]for at,n in zip(points,normals)for x,z in profile]
    count=len(profile);layer=count*len(points);faces=[];material_indices=[]
    for i in range(len(points)-1):
        for j in range(count-1):
            k=i*count+j;face=(k,k+count,k+count+1,k+1)
            faces.extend([face,tuple(v+layer for v in reversed(face))])
            accent=(district=='carnival' and (j//2)%2==0) or (district=='mirrors' and j in (2,3,4)) or (district=='starlight' and j in (1,6)) or (district=='clockwork' and j==4)
            material_indices.extend([int(accent)]*2)
    rim=[*(i*count for i in range(len(points))),*(layer-count+j for j in range(1,count)),*(i*count+count-1 for i in range(len(points)-2,-1,-1)),*range(count-2,0,-1)]
    for a,b in zip(rim,rim[1:]+rim[:1]):
        faces.append((a,a+layer,b+layer,b));material_indices.append(0)
    if district=='carnival':
        dyed_cloth('festival_covered_walk_canvas',roof_tint)
        dyed_cloth('festival_covered_walk_linen',stone_tint)
    main='roof' if district=='fairytale' else 'festival_covered_walk_canvas' if district=='carnival' else 'zinc'
    accent='festival_covered_walk_linen' if district=='carnival' else 'frost'
    roof=mesh('continuous_closed_swept_covered_walk_roof',vertices,faces,main,r,0)
    roof.data.materials.append(K.M['v6_'+accent])
    for face,material in zip(roof.data.polygons,material_indices):face.material_index=material
    surface_uv(roof)
    # The low footprint follows the actual columns used by the existing
    # collision. Each eave beam receives their load at the same support line.
    for side in [-1,1]:
        edge=[at+n*side*(width/2-.15)for at,n in zip(points,normals)]
        H.bar('continuous_structural_eave_beam',[(p.x,p.y,3.409)for p in edge],.164,.192,'copper',r)
        stations=[]
        for a,b in zip(edge,edge[1:]):
            steps=max(1,math.ceil((b-a).length/6.5))
            stations.extend(a.lerp(b,i/steps)for i in range(steps))
        stations.append(edge[-1])
        for at in stations:
            section=[(.26,0),(.26,.16),(.19,.25),(.15,.44),(.14,3.14),(.23,3.28),(.265,3.39)]
            steps=10
            verts=[(at.x+rr*math.cos(i*math.tau/steps),at.y+rr*math.sin(i*math.tau/steps),z)for rr,z in section for i in range(steps)]
            faces=[tuple(reversed(range(steps))),tuple(range(len(verts)-steps,len(verts)))]
            for row in range(len(section)-1):
                faces.extend([(row*steps+i,row*steps+(i+1)%steps,(row+1)*steps+(i+1)%steps,(row+1)*steps+i)for i in range(steps)])
            column=mesh('tapered_arcade_column_at_original_footprint',verts,faces,'ivory',r,0)
            for face in column.data.polygons:face.use_smooth=len(face.vertices)==4
    for at,n in zip(points,normals):
        H.bar('true_transverse_roof_rib',[xyz(at,n,x,z-.103)for x,z in profile],.077,.095,'copper',r)
    r['architectureRevision']=6
    r['reviewWalkPoints']=json.dumps([list(p)for p in points])
    r['purpose']='The district-specific covered walk follows the existing promenade and column footprint with a new continuous roof section'
    return r

for walk_id in WALK_SLOTS:
    BUILDERS[walk_id]=lambda walk_id=walk_id:covered_visitor_walk(walk_id)

def mirrors_arcade_panels():
    palette('mirror_arcade_panels',{'ivory':(.85,.74,.85,1),'stone':(.89,.78,.75,1),'copper':(.89,.66,.34,1),'wood':(.49,.34,.46,1)})
    r=K.root('supported_mirror_arcade_panel_pair')
    for side in [-1,1]:
        at=(side*3.45,0);tangent=(0,1);normal=(-side,0)
        outer=elliptical_arch(2.79,.61,2.77,3.40,23)
        inner=elliptical_arch(2.50,.75,2.77,3.26,23)
        H.ring('continuous_arch_frame_around_mirror_panel',outer,inner,at,tangent,normal,(-.062,.073),'copper',r)
        pane=prism('deep_silver_mirror_pane',elliptical_arch(2.52,.74,2.77,3.27,23),at,tangent,normal,(-.031,.019),None,r,0)
        pane.data.materials.append(K.M['mirror'])
        for y in [-1.23,1.23]:
            footing=[(-.095,.015),(.095,.015),(.095,.17),(.067,.27),(.058,.78),(-.058,.78),(-.067,.27),(-.095,.17)]
            prism('formed_stone_floor_mounted_mirror_shoe',footing,(at[0],y),tangent,normal,(-.074,.074),'stone',r,.008)
            H.bar('recessed_mirror_frame_attachment',[(at[0],y,.72),(at[0],y,2.78)],.075,.090,'wood',r)
        H.bar('supported_mirror_rail_below_glazing',[(at[0],-1.29,.647),(at[0],1.29,.647)],.095,.11,'wood',r)
    r['architectureRevision']=6
    r['purpose']='Two framed silver panels fixed to real stone shoes within each existing mirror gallery bay'
    return r

BUILDERS['mirrors_arcade_panels']=mirrors_arcade_panels
ARCADE_SLOTS={
    'mirrors_arcade_panels':(-31,-12),
    'mirrors_arcade_panels_2':(-26,-1),
    'mirrors_arcade_panels_3':(-24,10),
    'mirrors_arcade_panels_4':(-28,22),
}

def architecture_model(ident):
    if ident in BOOTH_SLOTS:return BOOTH_SLOTS[ident][0]
    if ident in ARCADE_SLOTS:return 'mirrors_arcade_panels'
    return ident

def obstructing_observatory_column(root):
    matches=[obj for obj in root.children if obj.type=='MESH' and obj.name.startswith('rotunda_structural_column')
             and len(obj.data.vertices) and all(abs(v.co.x-21)<.2 and abs(v.co.y-3.5)<.2 for v in obj.data.vertices)]
    assert len(matches)<=1,'Only one original middle stair column may be retired'
    return matches[0] if matches else None

STRUCTURE_SLOTS={
    'mirror_observatory_support':('observatory_structure_v6','park_level_mirrors',(14,3.5,0),'mirrors'),
    'perimeter_service_gateway':('perimeter_gateway_structure_v6','perimeter_actual_access',(0,7,0),'perimeter'),
    'fairytale_castle_gateway':('fairytale_gatehouse_structure_v6','park_level_fairytale',(0,-40,0),'fairytale'),
}

def structure_slot(ident):
    name,parent_name,at,district=STRUCTURE_SLOTS[ident]
    parent=bpy.data.objects[parent_name]
    if ident=='mirror_observatory_support':
        middle=obstructing_observatory_column(parent)
        retired=[middle] if middle else []
    elif ident=='perimeter_service_gateway':
        names=('fitted_service_gateway_roof','gate_roof_connection','service_gateway_tapered_pier')
        retired=[obj for obj in parent.children if obj.type=='MESH' and obj.name.split('.')[0] in names]
        assert len(retired) in (0,5),('Unexpected legacy service gateway meshes',len(retired))
    else:
        names=('castle_continuous_round_tower','fitted_conical_turret_roof','main_fairy_castle_gateway_continuous_arch','main_fairy_castle_gateway_pier','tower_inset_window')
        retired=[obj for obj in parent.children if obj.type=='MESH' and obj.name.split('.')[0] in names]
        assert len(retired) in (0,11),('Unexpected legacy castle gateway meshes',len(retired))
    owner=bpy.data.objects.get(name)
    if owner is None:
        owner=K.root(name,parent)
        owner.location=at
        owner['_parkSourceCollection']=district
    assert owner.parent==parent and (owner.location-Vector(at)).length<.001
    return owner,retired

def architecture_owner(ident):
    if ident in ARCADE_SLOTS:
        at=Vector(ARCADE_SLOTS[ident]);parent=bpy.data.objects.get('park_level_mirrors')
        matches=[o for o in parent.children if o.name.startswith('illusion_arcade_bay') and (o.location.xy-at).length<.01] if parent else []
        assert len(matches)==1,('Expected the original mirror arcade bay',ident)
        return matches[0]
    if ident in WALK_SLOTS:
        district,index=WALK_SLOTS[ident]
        parent=bpy.data.objects.get('textfree_theme_v2_'+district)
        walks=[o for o in parent.children if o.name.startswith('continuous_covered_visitor_walk')] if parent else []
        if district=='fairytale':
            def minimum_x(owner):
                return min((v.co.x for obj in owner.children_recursive if obj.type=='MESH' for v in obj.data.vertices),default=float('inf'))
            walks.sort(key=lambda obj:(minimum_x(obj),obj.name))
        assert len(walks)==(2 if district=='fairytale' else 1),('Missing the original covered walks',ident)
        return walks[index]
    if ident in BOOTH_SLOTS:
        _,district,at=BOOTH_SLOTS[ident]
        parent=bpy.data.objects.get('textfree_theme_v2_'+district)
        matches=[o for o in parent.children if o.name.startswith('purpose_midway_booth_') and (o.location.xy-Vector(at)).length<.01] if parent else []
        assert len(matches)==1,('Expected one booth at the original position',ident,at)
        return matches[0]
    if ident in STRUCTURE_SLOTS:
        return bpy.data.objects.get(STRUCTURE_SLOTS[ident][0])
    if ident=='service_lodge':
        return bpy.data.objects.get('actual_service_lodge')
    if ident.endswith('_return_threshold'):
        parent=bpy.data.objects.get('textfree_theme_v2_'+ident.removesuffix('_return_threshold'))
        if parent:
            owners=[obj for obj in parent.children if obj.name.startswith('purpose_park_return_threshold')]
            if len(owners)==1:return owners[0]
        return None
    return bpy.data.objects.get('parkcopy_facade_'+ident)

def restore_reviewed(root,district):
    """Restore current reviewed facility bodies during an existing site rebuild."""
    import json,hashlib
    from pathlib import Path
    repo=Path(__file__).resolve().parents[1];file=repo/'art/space_v4/park_levels_v1/architecture_v6/manifest.json'
    if not file.exists():return []
    rows=json.loads(file.read_text(encoding='utf8'))['assets'];changed=[]
    for ident,row in rows.items():
        if row['district']!=district or not row['sourceReviewed']:continue
        if ident in STRUCTURE_SLOTS:
            owner,retired=structure_slot(ident)
            if retired:bpy.data.batch_remove(ids=retired)
        else:owner=architecture_owner(ident)
        if owner is None:raise RuntimeError('Missing reviewed facility owner: '+row['owner'])
        source=repo/row['source'];sourceSHA=hashlib.sha256(source.read_bytes()).hexdigest();assert sourceSHA==row['sourceSHA256']
        if owner.get('architectureSourceSHA256')==sourceSHA:continue
        bpy.data.batch_remove(ids=list(owner.children_recursive))
        with bpy.data.libraries.load(str(source),link=False)as(a,b):b.objects=list(a.objects)
        for o in b.objects:
            if o:owner.users_collection[0].objects.link(o);o['_parkSourceCollection']=district
        asset=next(o for o in b.objects if o and o.parent is None);asset.parent=owner;asset.location=(0,0,0);owner['architectureRevision']=6;owner['architectureSourceSHA256']=sourceSHA;owner['architectureSource']=row['source'];changed.append(ident)
    return changed
