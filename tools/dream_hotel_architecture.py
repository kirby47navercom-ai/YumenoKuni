"""Designed park hotel: continuous sectioned wall, cut apertures and fitted roof.

Blender metres, Z up. The 14 x 12 m authored room envelope/entry stay fixed.
All structural solids begin as explicit face/edge meshes, not primitive props.
"""
import bpy,bmesh,math
from mathutils import Vector
import v4_rebuilt_environment_kit as K

PLAN=[(-7,-5.40),(-6.60,-6),(-4.10,-6),(-3.75,-5.40),(-2.10,-5.40),(-2.10,-6.05),(2.10,-6.05),(2.10,-5.40),(3.75,-5.40),(4.10,-6),(6.60,-6),(7,-5.40),(7,5.30),(6.30,6),(-6.30,6),(-7,5.30)]
ROOF_PLAN=[(-7.15,-6.15),(7.15,-6.15),(7.15,6.15),(-7.15,6.15)]
STATS={}

def palette():
    for key,base,tint,rough,metal,normal in [
        ('rose','plaster',(.61,.35,.33,1),.83,0,.13),
        ('stone','stone',(.87,.79,.66,1),.80,0,.16),
        ('slate','roof',(.21,.30,.40,1),.76,.06,.22),
        ('iron','iron',(.10,.15,.17,1),.46,.28,.12),
        ('copper','lacquer',(.22,.36,.33,1),.49,.24,.10),
        ('wood','wood',(.34,.23,.18,1),.56,0,.14)]:
        m=K.M[base].copy();m.name='architecture_hotel_'+key;m['surfaceTint']=tint
        bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=metal
        for link in list(bs.inputs['Roughness'].links):m.node_tree.links.remove(link)
        bs.inputs['Roughness'].default_value=rough
        old=bs.inputs['Base Color'].links[0].from_socket if bs.inputs['Base Color'].links else None
        if old:
            mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=tint
            m.node_tree.links.new(old,mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color'])
        else:bs.inputs['Base Color'].default_value=tint
        for n in m.node_tree.nodes:
            if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=normal
        K.M['hotel_'+key]=m
    m=bpy.data.materials.new('architecture_hotel_glass');m.use_nodes=True;m['surfaceTint']=[.15,.25,.29,1]
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.15,.25,.29,1);bs.inputs['Metallic'].default_value=.25;bs.inputs['Roughness'].default_value=.19
    K.M['hotel_glass']=m

def mesh(name,verts,faces,material,parent):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update()
    bm=bmesh.new();bm.from_mesh(d);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(d);bm.free()
    o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.parent=parent
    if material:d.materials.append(K.M['hotel_'+material])
    return o

def finish(o,bevel=.012):
    if bevel:
        bpy.context.view_layer.objects.active=o
        mod=o.modifiers.new('small_constructed_edge_bevel','BEVEL');mod.width=bevel;mod.segments=2;mod.limit_method='ANGLE';mod.angle_limit=.52
        bpy.ops.object.modifier_apply(modifier=mod.name)
    d=o.data;uv=d.uv_layers.get('UVMap')or d.uv_layers.new(name='UVMap')
    bm=bmesh.new();bm.from_mesh(d)
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(d)
    bm.free()
    for face in d.polygons:
        axis=max(range(3),key=lambda i:abs(face.normal[i]));axes=[i for i in range(3)if i!=axis]
        for li in face.loop_indices:
            co=d.vertices[d.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]*.55,co[axes[1]]*.55)
    return o

def offset(poly,distance):
    result=[]
    for i,b in enumerate(poly):
        a,c=Vector(poly[i-1]),Vector(poly[(i+1)%len(poly)]);b=Vector(b)
        u=(b-a).normalized();v=(c-b).normalized();nu=Vector((-u.y,u.x));nv=Vector((-v.y,v.x))
        delta=(nu+nv)*(distance/max(.05,1+nu.dot(nv)));result.append(tuple(b+delta))
    for i,p in enumerate(result):
        j=(i+1)%len(poly)
        assert (Vector(result[j])-Vector(p)).dot(Vector(poly[j])-Vector(poly[i]))>1e-7,('Collapsed architectural offset edge',i,distance)
    return result

def shell(name,poly,rings,thickness,material,parent):
    # Each course is part of the same continuous outer wall. The inner face
    # has a real offset, so apertures expose jamb depth rather than a flat card.
    n=len(poly);v=[]
    for z,inset in rings:v.extend((x,y,z)for x,y in offset(poly,inset))
    inner=offset(poly,thickness);start=len(v)
    for z in [rings[0][0],rings[-1][0]]:v.extend((x,y,z)for x,y in inner)
    f=[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i)for k in range(len(rings)-1)for i in range(n)]
    last=(len(rings)-1)*n
    f +=[(i,start+i,start+(i+1)%n,(i+1)%n)for i in range(n)]
    f +=[(last+i,last+(i+1)%n,start+n+(i+1)%n,start+n+i)for i in range(n)]
    f +=[(start+i,start+n+i,start+n+(i+1)%n,start+(i+1)%n)for i in range(n)]
    return mesh(name,v,f,material,parent)

def arch(width,bottom,height,n=16):
    a=width/2;spring=bottom+height-a
    return [(-a,bottom),(a,bottom),(a,spring)]+[(a*math.cos(i*math.pi/n),spring+a*math.sin(i*math.pi/n))for i in range(1,n+1)]

def prism(name,outline,center,tangent,normal,depths,mat,parent):
    v=[(center[0]+tangent[0]*x+normal[0]*s,center[1]+tangent[1]*x+normal[1]*s,z)for s in depths for x,z in outline];n=len(outline)
    return mesh(name,v,[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],mat,parent)

def difference(obj,cutters,label):
    # Disjoint aperture cutters are evaluated in one exact Boolean operation.
    bpy.context.view_layer.update();v=[];f=[]
    for c in cutters:
        start=len(v);v.extend(c.matrix_world@p.co for p in c.data.vertices);f.extend(tuple(start+i for i in p.vertices)for p in c.data.polygons)
    tool=mesh('construction_cutters_'+label,v,f,None,None)
    tool.data.materials.append(obj.data.materials[0])
    if label=='roof_opened_for_dormer_rooms':
        import json
        from pathlib import Path
        rows=[]
        for q in [obj,tool]:
            bm=bmesh.new();bm.from_mesh(q.data);rows.append({'name':q.name,'signedVolume':bm.calc_volume(signed=True),'nonManifold':sum(not e.is_manifold for e in bm.edges),'vertices':[list(p.co)for p in q.data.vertices],'faces':[list(p.vertices)for p in q.data.polygons]});bm.free()
        (Path(__file__).resolve().parents[1]/'Game/Saved/park-levels-20261104/hotel-architecture/roof-boolean-input.json').write_text(json.dumps(rows),encoding='utf8')
        print('ROOF_BOOLEAN_INPUT',[(q['name'],q['signedVolume'],q['nonManifold'])for q in rows],flush=True)
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new(label,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool
    bpy.ops.object.modifier_apply(modifier=mod.name)
    STATS[label]=len(cutters)
    bpy.data.batch_remove(ids=[tool,*cutters])

def ring(name,outer,inner,center,tangent,normal,depths,mat,parent):
    assert len(outer)==len(inner);n=len(outer)
    # Model the stone/timber section directly. Beveling every generated Boolean
    # edge inflated tiny upper-floor frames without improving their silhouette.
    sections=[(0,depths[1]),(0,depths[0]+.012),(.055,depths[0]),(.945,depths[0]),(1,depths[0]+.012),(1,depths[1])]
    v=[]
    for t,s in sections:
        for a,b in zip(outer,inner):
            x=a[0]*(1-t)+b[0]*t;z=a[1]*(1-t)+b[1]*t
            v.append((center[0]+tangent[0]*x+normal[0]*s,center[1]+tangent[1]*x+normal[1]*s,z))
    f=[(k*n+i,k*n+(i+1)%n,((k+1)%len(sections))*n+(i+1)%n,((k+1)%len(sections))*n+i)for k in range(len(sections))for i in range(n)]
    return finish(mesh(name,v,f,mat,parent),0)

def rectangle(width,bottom,top):return [(-width/2,bottom),(width/2,bottom),(width/2,top),(-width/2,top)]

def bar(name,points,width,depth,mat,parent):
    # A swept rectangular structural section, retaining shaped beam/flashing edges.
    points=[Vector(p)for p in points];closed=(points[0]-points[-1]).length<1e-7
    if closed:points=points[:-1]
    verts=[]
    for i,p in enumerate(points):
        direction=(points[(i+1)%len(points)]-points[(i-1)%len(points)]).normalized()if closed else(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();side=direction.cross(Vector((0,0,1)))
        if side.length<.01:side=direction.cross(Vector((0,1,0)))
        side.normalize();other=direction.cross(side).normalized()
        a,b=width/2,depth/2;c=min(width,depth)*.12
        verts.extend(tuple(p+side*x+other*y)for x,y in [(-a+c,-b),(a-c,-b),(a,-b+c),(a,b-c),(a-c,b),(-a+c,b),(-a,b-c),(-a,-b+c)])
    f=[]if closed else[tuple(reversed(range(8))),tuple(range(len(verts)-8,len(verts)))]
    f +=[(i*8+k,i*8+(k+1)%8,((i+1)%len(points))*8+(k+1)%8,((i+1)%len(points))*8+k)for i in range(len(points)if closed else len(points)-1)for k in range(8)]
    return finish(mesh(name,verts,f,mat,parent),0)

def window(spec,parent,door=False):
    center,tangent,normal,w,b,h=spec
    ring('recessed_door_stone_reveal'if door else'recessed_window_stone_reveal',arch(w+.22,b-.10,h+.20),arch(w-.012,b+.01,h-.01),center,tangent,normal,(-.055,.13),'stone',parent)
    ring('deep_timber_door_sash'if door else'deep_timber_window_sash',arch(w-.04,b+.025,h-.04),arch(w-.15,b+.08,h-.15),center,tangent,normal,(.235,.30),'wood',parent)
    finish(prism('thick_recessed_glass',arch(w-.14,b+.075,h-.14),center,tangent,normal,(.288,.32),'glass',parent),0)
    # True sloping sill with a projecting drip edge, clipped within the reveal.
    sill=[(-.11,b-.10),(-.11,b-.02),(.31,b+.025),(.36,b-.035),(.36,b-.10)]if not door else[(-.11,b-.01),(-.11,b+.005),(.31,b+.025),(.36,b+.005),(.36,b-.01)]
    verts=[(center[0]+tangent[0]*x+normal[0]*s,center[1]+tangent[1]*x+normal[1]*s,z)for x in [-w/2-.14,w/2+.14]for s,z in sill];n=len(sill)
    finish(mesh('sloping_stone_sill_with_drip',verts,[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'stone',parent),0)
    spring=b+h-w/2;transom=b+(h-w/2)*.72
    def point(x,z,s=.23):return(center[0]+tangent[0]*x+normal[0]*s,center[1]+tangent[1]*x+normal[1]*s,z)
    bar('sash_meeting_stile',[point(0,b+.11),point(0,b+h-.10)],.035,.05,'wood',parent)
    bar('fitted_sash_transom',[point(-w/2+.10,transom),point(w/2-.10,transom)],.037,.05,'wood',parent)
    if door:
        for side in [-1,1]:bar('actual_entrance_pull',[point(side*.17,b+1.02,-.10),point(side*.17,b+1.65,-.10)],.025,.045,'copper',parent)
    else:
        for side in [-1,1]:bar('arched_fanlight_radial_sash',[point(0,spring),point(side*(w/2-.10)*.70,spring+(w/2-.10)*.70)],.025,.04,'wood',parent)

def roof_shell(parent):
    # Constant-thickness folded roof, including the inner soffit and sealed eaves.
    rings=[(12.12,-.22),(12.30,-.22),(14.50,1.02),(15.20,1.80)]
    n=len(ROOF_PLAN);v=[]
    for z,d in rings:v.extend((x,y,z)for x,y in offset(ROOF_PLAN,d))
    # Offset perpendicular to the roof section. A vertical-only thickness
    # overlaps the vertical eave and makes an exact Boolean erase the shell.
    directions=[Vector((b[1]-a[1],b[0]-a[0])).normalized()for a,b in zip(rings,rings[1:])]
    normals=[Vector((d.y,-d.x))for d in directions]
    for i,(z,d)in enumerate(rings):
        a=normals[max(0,i-1)];b=normals[i]if i<len(normals)else Vector((0,-1))
        m=(a+b)*(.14/(1+a.dot(b)))
        v.extend((x,y,z+m.y)for x,y in offset(ROOF_PLAN,d+m.x))
    count=n*len(rings);faces=[]
    for k in range(len(rings)-1):
        for i in range(n):
            a=k*n+i;b=k*n+(i+1)%n;c=(k+1)*n+(i+1)%n;d=(k+1)*n+i
            faces.extend([(a,b,c,d),(d+count,c+count,b+count,a+count)])
    for k in [0]:
        for i in range(n):a=k*n+i;b=k*n+(i+1)%n;faces.append((a,b,b+count,a+count))
    # The upper small hipped deck is closed, not an unrendered hole.
    faces.extend([tuple(range((len(rings)-1)*n,len(rings)*n)),tuple(reversed(range(count+(len(rings)-1)*n,2*count)))])
    roof=mesh('continuous_thick_mansard_roof',v,faces,'slate',parent)
    cuts=[]
    for x,y,w,h in [(-5.25,-6.0,1.38,1.65),(0,-6.05,1.90,2.0),(5.25,-6.0,1.38,1.65)]:
        cuts.append(prism('roof_dormer_real_opening',rectangle(w+.22,12.45,12.85+h+.15),(x,y),(1,0),(0,1),(-.30,1.80),None,parent))
    difference(roof,cuts,'roof_opened_for_dormer_rooms');finish(roof,.014)
    roof.data.materials.append(K.M['hotel_iron'])
    deckMaterial=len(roof.data.materials)-1
    for face in roof.data.polygons:
        if all(roof.data.vertices[i].co.z>15.19 for i in face.vertices):face.material_index=deckMaterial
    finish(shell('sealed_overhanging_roof_soffit',ROOF_PLAN,[(12.00,-.19),(12.13,-.19)],1.10,'stone',parent),.012)
    return roof

def dormer(parent,x,y,w,h):
    bottom=12.75;top=bottom+h+.12;back=y+2.0
    # Thick jamb/cheek walls return into the cut mansard. No solid roof remains
    # behind the window; the dormer has an actual usable opening into its volume.
    xl,xr=x-w/2-.18,x+w/2+.18;front=y-.025;t=.16
    poly=[(xl,front+t),(xl,back),(xr,back),(xr,front+t),(xr-t,front+t),(xr-t,back-t),(xl+t,back-t),(xl+t,front+t)]
    n=len(poly);v=[(a,b,z)for z in [12.35,top]for a,b in poly]
    body=mesh('dormer_continuous_u_shaped_cheeks',v,[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'rose',parent)
    spec=((x,y-.025),(1,0),(0,1),w,bottom,h)
    from v4_facility_forms import curve_wall
    outline=[(xl,12.35),(xr,12.35),(xr,top),(xl,top)]
    hole=[(x+a,z)for a,z in reversed(arch(w,bottom,h))]
    facade=curve_wall('dormer_apertured_front',outline,[hole],front+t/2,'hotel_rose',parent,t)
    bm=bmesh.new();bm.from_mesh(facade.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(facade.data);bm.free();finish(facade,.009)
    finish(body,.012);window(spec,parent)
    outer=[(-w/2-.30,top-.03),(0,top+.62),(w/2+.30,top-.03)]
    band=outer+[(a,z-.13)for a,z in reversed(outer)]
    cap=prism('fitted_dormer_gable_roof',band,(x,y),(1,0),(0,1),(-.23,2.05),'slate',parent);finish(cap,.012)
    for face in cap.data.polygons:
        for li in face.loop_indices:
            co=cap.data.vertices[cap.data.loops[li].vertex_index].co;cap.data.uv_layers[0].data[li].uv=(co.y*.55,co.z*.55)
    finish(prism('solid_dormer_pediment',[(w/2+.1,top-.02),(0,top+.47),(-w/2-.1,top-.02)],(x,y),(1,0),(0,1),(-.025,.135),'rose',parent),.009)
    bar('dormer_gable_stone_coping',[(x+a,y-.245,z)for a,z in outer],.075,.09,'stone',parent)

def porch(parent):
    # Existing two column centres are part of the collision/save contract.
    for x in [-3.6,3.6]:
        profile=[(.21,.02),(.21,.20),(.13,.31),(.10,.46),(.09,2.88),(.15,3.03),(.21,3.08),(.21,3.31)]
        n=12;v=[(x+rr*math.cos(i*math.tau/n),-7.10+rr*math.sin(i*math.tau/n),z)for rr,z in profile for i in range(n)]
        faces=[tuple(reversed(range(n))),tuple(range((len(profile)-1)*n,len(profile)*n))]+[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i)for k in range(len(profile)-1)for i in range(n)]
        finish(mesh('structural_cast_column_with_capital',v,faces,'iron',parent),.008)
    def zz(x):return 3.16+.82*(1-(x/4.05)**2)
    for yy in [-7.12,-5.34]:
        bar('load_bearing_segmental_arch_beam',[(x,yy,zz(x))for x in [-4.05+i*8.1/32 for i in range(33)]],.11,.14,'iron',parent)
    v=[(x,yy,zz(x)+.06+k*.045)for k in range(2)for yy in [-7.58,-5.22]for x in [-4.05+i*8.1/32 for i in range(33)]];n=33
    faces=[]
    for i in range(32):faces.extend([(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),(i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)])
    faces.extend([(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)])
    finish(mesh('single_curved_thick_copper_entry_roof',v,faces,'copper',parent),.008)
    for x in [-3.6,-2.4,-1.2,0,1.2,2.4,3.6]:bar('canopy_fitted_standing_seam',[(x,-7.60,zz(x)+.11),(x,-5.20,zz(x)+.11)],.025,.035,'iron',parent)
    # Braces resolve thrust into the existing columns instead of floating eaves.
    for x in [-3.6,3.6]:
        for side in [-1,1]:
            target=zz(x+side*.40)-.06
            bar('curved_column_arch_bracket',[(x+side*.40*t,-7.10,2.65+(target-2.65)*t+.10*t*(1-t))for t in [i/8 for i in range(9)]],.045,.07,'iron',parent)

def balcony(parent):
    poly=[(-1.82,-6.02),(-1.82,-6.78),(-1.54,-6.96),(1.54,-6.96),(1.82,-6.78),(1.82,-6.02)]
    n=len(poly);v=[(x,y,z)for z in [3.31,3.48]for x,y in poly]
    finish(mesh('shaped_balcony_load_slab',v,[tuple(reversed(range(n))),tuple(range(n,2*n)),*[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]],'stone',parent),.02)
    for z in [3.62,4.39]:bar('balcony_continuous_metal_rail',[(x,y,z)for x,y in poly[:]],.035,.045,'iron',parent)
    for a,b in zip(poly,poly[1:]):
        a,b=Vector(a),Vector(b);steps=max(1,math.ceil((b-a).length/.22))
        for i in range(steps+1):p=a+(b-a)*i/steps;bar('balcony_fixed_baluster',[(p.x,p.y,3.48),(p.x,p.y,4.39)],.022,.025,'iron',parent)

def build(parent=None,at=(0,0),name='designed_dream_hotel_architecture'):
    STATS.clear();palette();root=K.root(name,parent);root.location=(*at,0);root['architectureRevision']=4;root['originalEntryLocal']=[0,-6,0]
    levels=[(0,-.10),(.25,-.10),(.36,0),(.78,0),(.86,.035),(3.16,.035),(3.28,-.075),(3.46,-.075),(3.56,.035),(6.02,.035),(6.14,-.055),(6.28,-.055),(6.36,.035),(8.86,.035),(9.00,-.055),(9.14,-.055),(9.22,.035),(11.70,.035),(11.80,-.12),(11.97,-.12),(12.12,0)]
    body=shell('continuous_coursed_load_bearing_wall',PLAN,levels,.32,'rose',root)
    body.data.materials.append(K.M['hotel_stone'])
    for p in body.data.polygons:
        if p.center.z<.86 or any(a-.001<=p.center.z<=b+.001 for a,b in [(3.16,3.56),(6.02,6.36),(8.86,9.22),(11.7,12.12)]):p.material_index=1
    openings=[]
    for floor,b in enumerate([.97,4.02,6.86,9.70]):
        for x in [-5.25,-3.0,0,3.0,5.25]:
            y=-6.05 if x==0 else -6.0 if abs(x)>4 else -5.40
            if floor==0 and x==0:continue
            wb,wh=(3.50,2.42)if floor==1 and x==0 else(b,2.03 if x==0 else 1.92)
            openings.append(((x,y),(1,0),(0,1),2.10 if x==0 else 1.16,wb,wh))
        for side in [-1,1]:
            for y in [-2.85,.25,3.35]:openings.append(((side*7,y),(0,side),(-side,0),1.20,b,1.92))
        for x in [-4.8,-2.4,0,2.4,4.8]:openings.append(((x,6),(-1,0),(0,-1),1.18,b,1.92))
    door=((0,-6.05),(1,0),(0,1),2.35,.015,3.13)
    cutters=[prism('wall_aperture_boolean',arch(w,b,h),c,t,n,(-.35,.85),None,root)for c,t,n,w,b,h in [*openings,door]]
    difference(body,cutters,'architectural_cut_apertures');finish(body,.012)
    for spec in openings:window(spec,root,door=spec[4]==3.50)
    window(door,root,True)
    roof_shell(root)
    for x,y,w,h in [(-5.25,-6.0,1.38,1.65),(0,-6.05,1.90,2.0),(5.25,-6.0,1.38,1.65)]:dormer(root,x,y,w,h)
    porch(root);balcony(root)
    # Ridge/eave flashings follow the same closed architectural footprint.
    edge=offset(ROOF_PLAN,-.20)
    bar('continuous_mansard_eave_flashing',[(x,y,12.22)for x,y in edge+[edge[0]]],.065,.07,'iron',root)
    root['wallThicknessMetres']=.32;root['openingCount']=len(openings)+1;root['roofShellThicknessMetres']=.14;root['design']='Victorian park lodge with recessed bays and inhabited mansard, not turret props'
    return root
