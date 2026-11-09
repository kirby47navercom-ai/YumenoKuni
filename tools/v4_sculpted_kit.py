"""Authored continuous surface meshes; Blender-only, metres and Z-up.

Lathed vessels have an inner wall and rolled lip, sweeps have shared quad rings,
and UVs follow the surface rather than projecting across bevels. Geometry stays
inside the established furniture envelopes; gameplay collision is a separate owner.
"""
import bpy,bmesh,math
import numpy as np
from mathutils import Vector
from pathlib import Path

TAU=math.tau
M={}
LOW_DETAIL=False # Opt-in new environment bank; published source remains reproducible.
def materials(out):
    out.mkdir(parents=True,exist_ok=True)
    # Numerical surface maps: broad grain/tooling only, no salt-and-pepper noise.
    n=512;y,x=np.mgrid[0:n,0:n]/n
    for key,color,rough,metal in [('stone',(.61,.57,.48),.76,0),('wood',(.16,.073,.043),.48,0),('iron',(.032,.038,.051),.38,.72),('brass',(.39,.23,.075),.32,.76),('cloth',(.23,.065,.15),.86,0),('leaf',(.075,.18,.11),.71,0),('glass',(.12,.26,.29),.18,.15)]:
        mat=bpy.data.materials.get('sculpt_'+key) or bpy.data.materials.new('sculpt_'+key);mat.use_nodes=True
        bs=next(v for v in mat.node_tree.nodes if v.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
        if key=='glass':bs.inputs['Emission Color'].default_value=(.62,.43,.19,1);bs.inputs['Emission Strength'].default_value=.16
        generated=Path(__file__).resolve().parents[1]/'art/space_v4/materials_v2'
        surface={'stone':'limestone','wood':'walnut','iron':'metal','brass':'metal','cloth':'velvet','leaf':'leaf'}.get(key)
        if surface and (generated/'masters'/(surface+'.png')).exists():
            bs.inputs['Base Color'].default_value=(*color,1) if key in ('iron','brass') else (1,1,1,1)
            for channel,folder,suffix in [('color','masters',''),('normal','maps','_normal'),('roughness','maps','_roughness')]:
                file=generated/folder/(surface+suffix+'.png')
                image=bpy.data.images.load(str(file),check_existing=True)
                if channel!='color':image.colorspace_settings.name='Non-Color'
                image.pack();tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='REPEAT'
                if channel=='normal':
                    normalnode=mat.node_tree.nodes.new('ShaderNodeNormalMap');normalnode.inputs['Strength'].default_value=.65
                    mat.node_tree.links.new(tex.outputs['Color'],normalnode.inputs['Color']);mat.node_tree.links.new(normalnode.outputs['Normal'],bs.inputs['Normal'])
                else:mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color' if channel=='color' else 'Roughness'])
        elif key in ('stone','wood','cloth'):
            h=(.45*np.sin(TAU*(12*y+.14*np.sin(TAU*x*2)))+.17*np.sin(TAU*(25*y+2*x))) if key=='wood' else (.20*np.sin(TAU*x*14)*np.sin(TAU*y*14) if key=='cloth' else .13*np.sin(TAU*(4*x+3*y))+.07*np.cos(TAU*(9*x-7*y)))
            dx=(np.roll(h,-1,1)-np.roll(h,1,1))*.8;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*.8
            normal=np.stack((-dx,-dy,np.ones_like(h)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
            a=np.ones((n,n,4),dtype=np.float32);a[:,:,:3]=normal*.5+.5
            image=bpy.data.images.new('sculpt_'+key+'_normal',n,n);image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(a.ravel());image.filepath_raw=str(out/(key+'_normal.png'));image.file_format='PNG';image.save();image.pack()
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Linear';normalnode=mat.node_tree.nodes.new('ShaderNodeNormalMap');normalnode.inputs['Strength'].default_value=.65
            mat.node_tree.links.new(tex.outputs['Color'],normalnode.inputs['Color']);mat.node_tree.links.new(normalnode.outputs['Normal'],bs.inputs['Normal'])
            # Roughness uses the same physical surface, packed G (glTF exporter).
            a[:,:,:3]=np.clip(rough+h[:,:,None]*.07,0,1)
            image=bpy.data.images.new('sculpt_'+key+'_roughness',n,n);image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(a.ravel());image.filepath_raw=str(out/(key+'_roughness.png'));image.file_format='PNG';image.save();image.pack()
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Roughness'])
            # Bake the same broad physical grain into albedo; no unrelated noise
            # texture, and no high-frequency painted black contour on every pore.
            if key=='wood':
                albedo=np.ones((n,n,4),dtype=np.float32)
                albedo[:,:,:3]=np.clip(np.array([.37,.23,.15])[None,None,:]*(1+h[:,:,None]*.19),0,1)
                image=bpy.data.images.new('sculpt_wood_albedo',n,n);image.pixels.foreach_set(albedo.ravel());image.filepath_raw=str(out/'wood_albedo.png');image.file_format='PNG';image.save();image.pack()
                tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        M[key]=mat
    return M

def root(name,parent=None):
    o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);o.parent=parent;return o

def mesh(name,v,f,mat,parent=None,uv=None,smooth=False):
    d=bpy.data.meshes.new(name);d.from_pydata(v,[],f);d.update()
    bm=bmesh.new();bm.from_mesh(d);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(d);bm.free()
    layer=d.uv_layers.new(name='UVMap')
    for p in d.polygons:
        p.use_smooth=smooth
        for li in p.loop_indices:
            co=d.vertices[d.loops[li].vertex_index].co
            layer.data[li].uv=uv[d.loops[li].vertex_index] if uv else (co.x,co.y+co.z)
    o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.parent=parent;d.materials.append(M[mat]);return o

def lathe(name,profile,mat,parent=None,n=64,flute=0):
    assert len(profile)>2
    if LOW_DETAIL:n=min(n,24);flute=0
    dist=[0]
    for a,b in zip(profile,profile[1:]):dist.append(dist[-1]+math.dist(a,b))
    vertices=[];uv=[]
    for j,(r,z) in enumerate(profile):
        for i in range(n+1):
            a=TAU*i/n;rr=r*(1+flute*math.cos(a*16));vertices.append((rr*math.cos(a),rr*math.sin(a),z));uv.append((i/n,dist[j]))
    s=n+1;faces=[(j*s+i,j*s+i+1,(j+1)*s+i+1,(j+1)*s+i) for j in range(len(profile)-1) for i in range(n)]
    obj=mesh(name,vertices,faces,mat,parent,uv,True)
    # Weld the UV seam spatially; UV coordinates remain split per loop.
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(obj.data);bm.free();return obj

def sweep(name,points,radius,mat,parent=None,n=12):
    if LOW_DETAIL:n=min(n,6)
    points=[Vector(p) for p in points];v=[];uv=[];distance=0
    for j,p in enumerate(points):
        t=(points[min(j+1,len(points)-1)]-points[max(j-1,0)]).normalized();side=t.cross(Vector((1,0,0)))
        if side.length<.01:side=t.cross(Vector((0,0,1)))
        side.normalize();up=t.cross(side).normalized()
        if j:distance+=(p-points[j-1]).length
        r=radius[j] if isinstance(radius,list) else radius
        for i in range(n+1):
            a=TAU*i/n;q=p+r*(math.cos(a)*side+math.sin(a)*up);v.append(tuple(q));uv.append((i/n,distance))
    s=n+1;faces=[(j*s+i,j*s+i+1,(j+1)*s+i+1,(j+1)*s+i) for j in range(len(points)-1) for i in range(n)]
    faces.extend([tuple(reversed(range(n))),tuple((len(points)-1)*s+i for i in range(n))]);o=mesh(name,v,faces,mat,parent,uv,True)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(o.data);bm.free();return o

def extrusion(name,contour,width,mat,parent=None):
    # Closed cast side plate; the YZ contour is the structural body, not tubes
    # intersecting a pile of boxes. Bevels define the actual cast-metal edge.
    n=len(contour);v=[(x,y,z) for x in [-width/2,width/2] for y,z in contour];f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,v,f,mat,parent);b=o.modifiers.new('cast_edge_radius','BEVEL');b.width=.012;b.segments=1 if LOW_DETAIL else 3
    return o

def board(name,loc,length,width,thick,mat,parent,tilt=0):
    # Rounded rectangular cross-section swept along the grain, ten quad rings.
    profile=[];r=min(.018,width/5,thick/3)
    for cy,cz,a0 in [(width/2-r,thick/2-r,0),(-width/2+r,thick/2-r,90),(-width/2+r,-thick/2+r,180),(width/2-r,-thick/2+r,270)]:
        for j in range(2 if LOW_DETAIL else 4):
            a=math.radians(a0+j*(90 if LOW_DETAIL else 30));profile.append((cy+r*math.cos(a),cz+r*math.sin(a)))
    v=[];uv=[];n=len(profile)
    steps=1 if LOW_DETAIL else 8
    for k in range(steps+1):
        xx=(k/steps-.5)*length
        for j,(y,z) in enumerate(profile):
            v.append((xx,y*math.cos(tilt)-z*math.sin(tilt),y*math.sin(tilt)+z*math.cos(tilt)));uv.append((k/steps*length,j/n*.3))
    f=[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i) for k in range(steps) for i in range(n)];f.extend([tuple(reversed(range(n))),tuple(steps*n+i for i in range(n))]);o=mesh(name,v,f,mat,parent,uv,True);o.location=loc;return o

def bench(name='SculptBench',parent=None):
    r=root(name,parent)
    for j in range(5):
        y=-.235+j*.111;board('curved_seat_slat',(0,y,.485+.065*(y/.5)**2),1.85,.097,.055,'wood',r,tilt=.10*y)
    for j in range(4):board('reclined_back_slat',(0,.25+(j*.104)*.20,.66+j*.104),1.85,.09,.055,'wood',r,tilt=math.radians(78))
    for x in [-.70,.70]:
        contour=[(-.29,.035),(-.19,.035),(-.12,.36),(.16,.36),(.24,.035),(.34,.035),(.29,.18),(.23,.52),(.34,1.04),(.26,1.06),(.14,.56),(-.22,.55),(-.28,.36)]
        o=extrusion('cast_iron_side_frame',contour,.065,'iron',r);o.location.x=x
        pts=[(x,-.21+.46*t/16,.67+.10*math.sin(math.pi*t/16)) for t in range(17)];sweep('curved_armrest',pts,.027,'brass',r)
        for yy,zz in [(-.22,.5),(.22,.5),(.30,.84)]:
            o=lathe('countersunk_fastener',[(0,0),(.012,0),(.015,.004),(.011,.01),(0,.01)],'brass',r,n=12);o.location=(x,yy,zz)
    sweep('lower_cross_brace',[(-.7,.10,.25),(.7,.10,.25)],.024,'iron',r)
    return r

def fountain(name='SculptFountain',parent=None):
    r=root(name,parent)
    # The basin is one continuous closed cross-section, including the dry floor.
    lathe('carved_basin',[(0,.06),(1.86,.06),(1.98,.09),(2.08,.17),(2.13,.26),(2.13,.42),(2.10,.48),(2.04,.51),(1.97,.51),(1.93,.47),(1.93,.39),(1.88,.22),(.36,.19),(0,.19)],'stone',r,n=96)
    lathe('basin_brass_inlay',[(2.13,.28),(2.135,.28),(2.135,.307),(2.13,.307),(2.13,.28)],'brass',r,n=96)
    lathe('turned_fluted_pedestal',[(0,.17),(.47,.17),(.49,.23),(.46,.29),(.34,.34),(.28,.51),(.22,.66),(.20,1.05),(.27,1.15),(.35,1.19),(.35,1.26),(.25,1.30),(.16,1.37),(.12,1.9),(.20,2.0),(.21,2.09),(.13,2.16),(.08,2.72),(0,2.76)],'stone',r,n=64,flute=.025)
    for z,rad in [(.95,1.30),(1.80,.83),(2.48,.43)]:
        profile=[(0,z-.11),(rad*.22,z-.11),(rad*.62,z-.06),(rad*.91,z+.09),(rad,z+.18),(rad,z+.23),(rad*.98,z+.25),(rad*.94,z+.25),(rad*.92,z+.20),(rad*.84,z+.12),(rad*.50,z+.01),(0,z-.02)]
        lathe('scalloped_bowl',profile,'stone',r,n=96,flute=.008)
    lathe('finial',[(0,2.62),(.085,2.62),(.11,2.70),(.13,2.78),(.12,2.84),(.07,2.90),(0,3.02)],'brass',r,n=48)
    return r

def lamp(name='SculptLamp',parent=None):
    r=root(name,parent)
    lathe('cast_lamp_column',[(0,0),(.19,0),(.20,.05),(.20,.13),(.15,.18),(.13,.45),(.10,.52),(.065,.60),(.055,2.65),(.09,2.72),(.09,2.78),(.06,2.84),(0,2.84)],'iron',r,n=32,flute=.045)
    lathe('collar',[(.06,.56),(.09,.56),(.09,.61),(.06,.61),(.06,.56)],'brass',r,n=32)
    lathe('lantern_foot',[(0,2.78),(.16,2.78),(.21,2.84),(.20,2.9),(.16,2.94),(0,2.94)],'iron',r,n=8)
    lathe('lantern_glazing',[(0,2.93),(.14,2.93),(.20,3.3),(.18,3.34),(0,3.34)],'glass',r,n=8)
    for i in range(8):
        a=i*TAU/8;sweep('lantern_rib',[(.165*math.cos(a),.165*math.sin(a),2.9),(.215*math.cos(a),.215*math.sin(a),3.31)],.012,'iron',r,n=8)
    lathe('curved_lantern_roof',[(0,3.31),(.25,3.31),(.27,3.34),(.24,3.39),(.17,3.43),(.08,3.52),(.05,3.57),(0,3.62)],'iron',r,n=32)
    lathe('roof_finial',[(0,3.57),(.04,3.57),(.055,3.63),(.035,3.69),(0,3.77)],'brass',r,n=16)
    return r

def planter(name='SculptPlanter',parent=None):
    r=root(name,parent)
    lathe('moulded_planter_vessel',[(0,0),(.39,0),(.43,.05),(.43,.12),(.37,.16),(.39,.21),(.49,.62),(.53,.65),(.55,.69),(.54,.75),(.48,.77),(.45,.74),(.44,.67),(.34,.22),(0,.22)],'stone',r,n=48,flute=.018)
    lathe('inset_soil',[(0,.62),(.43,.62),(.43,.64),(0,.64)],'wood',r,n=32)
    for i in range(13):
        a=i*2.39996;length=.30+.08*(i%3);base=(.15*math.cos(a),.15*math.sin(a),.64)
        # Curved, double-sided leaf blade with central fold and closed thickness.
        pts=[]
        steps=4 if LOW_DETAIL else 8
        for j in range(steps+1):
            t=j/steps;rad=.15+length*t;z=.64+.48*math.sin(t*1.7);w=.065*math.sin(math.pi*t)+.003
            for side in [-1,0,1]:pts.append((rad*math.cos(a)-side*w*math.sin(a),rad*math.sin(a)+side*w*math.cos(a),z+(.018 if side==0 else 0)))
        faces=[(j*3+k,j*3+k+1,(j+1)*3+k+1,(j+1)*3+k) for j in range(steps) for k in range(2)]
        o=mesh('folded_leaf',pts,faces,'leaf',r,smooth=True);s=o.modifiers.new('leaf_thickness','SOLIDIFY');s.thickness=.003
    return r

def chair(name='SculptChair',parent=None):
    r=root(name,parent)
    # Upholstered capsule with shared rings, rounded corners and convex cushion.
    for part,z,w,d,h in [('seat',.46,.48,.50,.095),('back',.81,.48,.105,.62)]:
        v=[];f=[];nx=12 if LOW_DETAIL else 20;nz=8 if LOW_DETAIL else 12
        for j in range(nz+1):
            phi=math.pi*j/nz
            for i in range(nx):
                a=TAU*i/nx;v.append((w/2*math.sin(phi)*math.copysign(abs(math.cos(a))**.35,math.cos(a)),d/2*math.sin(phi)*math.copysign(abs(math.sin(a))**.35,math.sin(a)),h/2*math.cos(phi)))
        for j in range(nz):
            for i in range(nx):f.append((j*nx+i,j*nx+(i+1)%nx,(j+1)*nx+(i+1)%nx,(j+1)*nx+i))
        o=mesh('tailored_'+part,v,f,'cloth',r,smooth=True);o.location=(0,.23 if part=='back' else 0,z)
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.dissolve_degenerate(bm,dist=.000001,edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    for x in [-.19,.19]:
        for y in [-.19,.19]:sweep('tapered_leg',[(x*1.15,y*1.15,.025),(x,y,.42),(x,y,.49)],[.018,.025,.027],'wood',r)
        sweep('bent_back_stile',[(x,.2,.34),(x,.23,.65),(x,.27,1.09)],.022,'wood',r)
    sweep('crest_rail',[(-.23,.27,1.06),(0,.28,1.12),(.23,.27,1.06)],.022,'brass',r)
    return r

def table(name='SculptTable',parent=None):
    r=root(name,parent)
    # A rounded-rectangle tabletop formed as nested contour loops (real bullnose).
    v=[];uv=[];n=24 if LOW_DETAIL else 64
    for sx,sy,z in [(1.25,.51,.70),(1.29,.55,.72),(1.30,.56,.76),(1.28,.54,.81),(1.24,.50,.82)]:
        for i in range(n):
            a=i*TAU/n;x=sx*math.copysign(abs(math.cos(a))**.22,math.cos(a));y=sy*math.copysign(abs(math.sin(a))**.22,math.sin(a));v.append((x,y,z));uv.append((x,y))
    f=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(4) for i in range(n)];f.extend([tuple(reversed(range(n))),tuple(4*n+i for i in range(n))]);mesh('bullnose_tabletop',v,f,'wood',r,uv,True)
    for x in [-1.05,1.05]:
        for y in [-.38,.38]:
            p=lathe('turned_table_leg',[(0,.02),(.04,.02),(.045,.08),(.031,.16),(.035,.45),(.055,.59),(.052,.69),(0,.70)],'wood',r,n=24);p.location=(x,y,0)
    return r

BUILDERS={'park_bench':bench,'detail_fountain_dry':fountain,'detail_planter':planter,'chair':chair,'meeting_table':table}

def orient_path_benches(objects):
    """The backrest is +Y: face the usable centre of the owning path/room."""
    changes=[]
    for o in objects:
        if o.type!='EMPTY' or not o.name.split('.')[0].endswith('_park_bench'):continue
        x,y=o.location.x,o.location.y
        dx,dy=(-math.copysign(1,x),0) if abs(x)>abs(y) else (0,-math.copysign(1,y))
        yaw=math.atan2(dx,-dy)
        if abs(math.atan2(math.sin(o.rotation_euler.z-yaw),math.cos(o.rotation_euler.z-yaw)))>.001:
            changes.append({'root':o.name,'oldYaw':o.rotation_euler.z,'newYaw':yaw,'reason':'backrest outside, seat opening toward owning path centre'})
            o.rotation_euler.z=yaw
    return changes

def bake_modifiers(objects):
    graph=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        if o.type=='MESH' and o.modifiers:
            original=o.data;o.data=bpy.data.meshes.new_from_object(o.evaluated_get(graph));o.modifiers.clear()
            if original.users==0:bpy.data.meshes.remove(original)

def replace_props(objects):
    changed=[]
    for old in list(objects):
        try:old.name
        except ReferenceError:continue
        if old.type!='EMPTY':continue
        key=next((k for k in BUILDERS if old.name.split('.')[0].endswith('_'+k)),None)
        if not key:continue
        # Preserve root transform/pivot and source identity for reaction/targets.
        children=list(old.children_recursive)
        for child in reversed(children):bpy.data.objects.remove(child,do_unlink=True)
        new=BUILDERS[key](old.name+'_surface',old)
        changed.append({'root':old.name,'kind':key})
    # Direct ground-anchored lamp pairs have no prop parent in the old kit.
    live=[]
    for o in objects:
        try:o.name;live.append(o)
        except ReferenceError:pass
    heads=[o for o in live if o.name.split('.')[0]=='lamp_head']
    posts=[o for o in live if o.name.split('.')[0]=='lamp_post']
    for post in posts:
        head=min(heads,key=lambda h:(h.location-post.location).length,default=None)
        matrix=post.matrix_world.copy();base=matrix.translation.copy();base.z=0
        parent=post.parent;o=lamp('sculpt_street_lamp',parent)
        o.matrix_world.translation=base
        bpy.data.objects.remove(post,do_unlink=True)
        if head and head.name in bpy.data.objects:heads.remove(head);bpy.data.objects.remove(head,do_unlink=True)
        changed.append({'kind':'street_lamp'})
    return changed

def mesh_health(objects):
    out={'vertices':0,'triangles':0,'nonManifoldEdges':0,'degenerateFaces':0,'missingUV':[]}
    for o in objects:
        if o.type!='MESH':continue
        d=o.data;out['vertices']+=len(d.vertices);out['triangles']+=sum(len(p.vertices)-2 for p in d.polygons)
        if not d.uv_layers:out['missingUV'].append(o.name)
        bm=bmesh.new();bm.from_mesh(d);out['nonManifoldEdges']+=sum(not e.is_manifold for e in bm.edges);out['degenerateFaces']+=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free()
    return out
