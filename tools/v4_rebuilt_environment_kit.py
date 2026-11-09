"""Whole environment rebuild: coherent low-mesh bodies, surface detail in maps.

Blender metres / Z-up. No stacked solid blocks used as decorative detail.
Structural casework uses real walls and cavities; trees have connected junctions.
"""
import bpy,bmesh,math,random
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];M={}

def setup_materials():
    old=R/'art/space_v4/materials_v2';new=R/'art/space_v4/rebuild_v1'
    roles={'wood':('walnut',(.8,.8,.8,1),0),'stone':('limestone',(1,1,1,1),0),'plaster':('plaster',(1,1,1,1),0),'cloth':('velvet',(1,1,1,1),0),'iron':('metal',(.05,.06,.08,1),.65),'brass':('metal',(.55,.35,.12,1),.72),'lacquer':('lacquer',(1,1,1,1),0),'linen':('linen',(1,1,1,1),0),'paving':('paving',(1,1,1,1),0),'leaf':('leaf',(1,1,1,1),0),'bark':('bark',(1,1,1,1),0),'roof':('roof',(1,1,1,1),.05),'foliage':('foliage',(1,1,1,1),0)}
    for name,(key,color,metal) in roles.items():
        mat=bpy.data.materials.new('rebuilt_'+name);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color;bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=.75 if name in ['cloth','bark','foliage','roof'] else .5
        if name in ['roof','bark','foliage','cloth']:bs.inputs['Specular IOR Level'].default_value=.2
        folder=new if key in ['bark','roof','foliage'] else old
        path=folder/'masters'/(key+'.png');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True);tex.extension='REPEAT';tex.image.pack();mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        if color!=(1,1,1,1):
            tint=mat.node_tree.nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=color;mat.node_tree.links.new(tex.outputs['Color'],tint.inputs[1]);mat.node_tree.links.new(tint.outputs[0],bs.inputs['Base Color'])
        normal=folder/'maps'/(key+'_normal.png');rough=folder/'maps'/(key+'_roughness.png')
        if normal.exists():
            t=mat.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(normal),check_existing=True);t.image.colorspace_settings.name='Non-Color';t.image.pack();n=mat.node_tree.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.45;mat.node_tree.links.new(t.outputs[0],n.inputs['Color']);mat.node_tree.links.new(n.outputs[0],bs.inputs['Normal'])
        if rough.exists():
            t=mat.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(rough),check_existing=True);t.image.colorspace_settings.name='Non-Color';t.image.pack();mat.node_tree.links.new(t.outputs[0],bs.inputs['Roughness'])
        if name=='foliage':mat.use_backface_culling=False;mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
        M[name]=mat
    if (new/'masters/grass.png').exists():
        mat=bpy.data.materials.new('rebuilt_grass');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.94;bs.inputs['Specular IOR Level'].default_value=.12
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(new/'masters/grass.png'),check_existing=True);tex.image.pack();mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);M['grass']=mat
        for kind in ['normal','roughness']:
            file=new/'maps'/('grass_'+kind+'.png')
            if not file.exists():continue
            t=mat.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(file),check_existing=True);t.image.colorspace_settings.name='Non-Color';t.image.pack()
            if kind=='normal':
                n=mat.node_tree.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.25;mat.node_tree.links.new(t.outputs[0],n.inputs['Color']);mat.node_tree.links.new(n.outputs[0],bs.inputs['Normal'])
            else:mat.node_tree.links.new(t.outputs[0],bs.inputs['Roughness'])
    mat=bpy.data.materials.new('rebuilt_glass');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.08,.17,.23,1);bs.inputs['Metallic'].default_value=.35;bs.inputs['Roughness'].default_value=.18;M['glass']=mat
    mat=bpy.data.materials.new('rebuilt_mirror');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.80,.86,.91,1);bs.inputs['Metallic'].default_value=.65;bs.inputs['Roughness'].default_value=.06;M['mirror']=mat
    mat=bpy.data.materials.new('rebuilt_light');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(1,.8,.48,1);bs.inputs['Emission Color'].default_value=(1,.72,.36,1);bs.inputs['Emission Strength'].default_value=1.35;M['light']=mat
    panel=new/'maps/panel_geometry_normal.png'
    if panel.exists():
        mat=M['wood'].copy();mat.name='rebuilt_baked_wood_panel'
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE' and 'normal' in node.image.name:
                node.image=bpy.data.images.load(str(panel),check_existing=True);node.image.colorspace_settings.name='Non-Color';node.image.pack()
            if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.65
        M['wood_panel']=mat

def root(name,parent=None):
    obj=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(obj);obj.parent=parent;return obj

def mesh(name,verts,faces,material,parent=None,smooth=False,uv_scale=1):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.dissolve_degenerate(bm,dist=.0000001,edges=list(bm.edges));bm.to_mesh(data);bm.free()
    uv=data.uv_layers.new(name='UVMap')
    for face in data.polygons:
        face.use_smooth=smooth;axis=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3) if k!=axis]
        for li in face.loop_indices:
            co=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]*uv_scale,co[axes[1]]*uv_scale)
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);obj.parent=parent;data.materials.append(M[material]);return obj

def section(name,profile,length,material,parent=None):
    # One closed structural extrusion, not intersecting decorative cuboids.
    profile=[p for i,p in enumerate(profile) if i==0 or math.dist(p,profile[i-1])>.0000001]
    if math.dist(profile[0],profile[-1])<.0000001:profile=profile[:-1]
    n=len(profile);v=[(x,y,z) for x in [-length/2,length/2] for y,z in profile]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,v,faces,material,parent)

def rounded_solid(name,width,depth,height,material,parent=None,radius=.025,loc=(0,0,0)):
    # Eight perimeter corners form a single watertight housing with actual volume.
    x,y=width/2,depth/2;r=min(radius,x*.25,y*.25,height*.2)
    outline=[(-x+r,-y),(x-r,-y),(x,-y+r),(x,y-r),(x-r,y),(-x+r,y),(-x,y-r),(-x,-y+r)]
    v=[(a,b,z) for z in [-height/2,height/2] for a,b in outline]
    f=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    obj=mesh(name,v,f,material,parent);obj.location=loc;return obj

def tube(name,points,radii,material,parent=None,n=8):
    v=[];closed=(Vector(points[0])-Vector(points[-1])).length<.000001
    if closed:points=points[:-1];radii=radii[:-1]
    for i,(point,radius) in enumerate(zip(points,radii)):
        tangent=Vector(points[(i+1)%len(points) if closed else min(i+1,len(points)-1)])-Vector(points[(i-1)%len(points) if closed else max(0,i-1)]);tangent.normalize();axis=tangent.cross(Vector((0,0,1)))
        if axis.length<.001:axis=tangent.cross(Vector((0,1,0)))
        axis.normalize();other=tangent.cross(axis)
        v.extend(tuple(Vector(point)+radius*(axis*math.cos(j*math.tau/n)+other*math.sin(j*math.tau/n)))for j in range(n))
    count=len(points);f=[] if closed else [tuple(reversed(range(n))),tuple(range((count-1)*n,count*n))]
    f.extend((i*n+j,i*n+(j+1)%n,((i+1)%count)*n+(j+1)%n,((i+1)%count)*n+j)for i in range(count if closed else count-1)for j in range(n))
    return mesh(name,v,f,material,parent,True)

def frame_ring(name,w,h,border,depth,material,parent=None,loc=(0,0,0),inner_size=None,inner_offset=(0,0)):
    outer=[(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]
    inner=[(-w/2+border,-h/2+border),(w/2-border,-h/2+border),(w/2-border,h/2-border),(-w/2+border,h/2-border)]
    if inner_size:
        iw,ih=inner_size;inner=[(-iw/2,-ih/2),(iw/2,-ih/2),(iw/2,ih/2),(-iw/2,ih/2)]
    inner=[(x+inner_offset[0],z+inner_offset[1])for x,z in inner]
    vertices=[(x,y,z)for y in [-depth/2,depth/2]for ring in [outer,inner]for x,z in ring];faces=[]
    for i in range(4):
        k=(i+1)%4;faces.extend([(i,k,k+4,i+4),(i+8,i+12,k+12,k+8),(i,i+8,k+8,k),(i+4,k+4,k+12,i+12)])
    obj=mesh(name,vertices,faces,material,parent);obj.location=loc;return obj

def casework(name,w,d,h,parent=None,material='wood'):
    # A continuous U-shaped case with a rear, open front and genuine cavity.
    r=root(name,parent);t=.045
    profile=[(-d/2,0),(d/2,0),(d/2,h),(-d/2,h),(-d/2,h-t),(d/2-t,h-t),(d/2-t,t),(-d/2,t)]
    section('continuous_case_shell',profile,w,material,r)
    for side in [-1,1]:
        panel=rounded_solid('case_end',t,d,h,material,r,.006,(side*(w/2-t/2),0,h/2))
    return r

def drawer(parent,width,depth,height,loc,name='drawer_slide'):
    r=root(name,parent);r.location=loc;t=.022
    # Bottom plus a continuous U tray wall; the opening is real geometry.
    profile=[(-depth/2,0),(depth/2,0),(depth/2,height),(depth/2-t,height),(depth/2-t,t),(-depth/2+t,t),(-depth/2+t,height),(-depth/2,height)]
    section('drawer_tray',profile,width,'wood',r)
    for side in [-1,1]:rounded_solid('drawer_side',t,depth,height,'wood',r,.004,(side*(width/2-t/2),0,height/2))
    rounded_solid('drawer_front',width+.04,.035,height+.025,'wood',r,.01,(0,-depth/2-.012,height/2))
    tube('curved_pull',[(-.14,-depth/2-.04,height*.6),(-.12,-depth/2-.08,height*.6),(.12,-depth/2-.08,height*.6),(.14,-depth/2-.04,height*.6)],[.012]*4,'brass',r,n=6)
    r['open_translation_local']=[0,-.35,0];return r

def storage_cabinet():
    r=casework('storage_cabinet',1.3,.55,1.9)
    for side in [-1,1]:
        door=rounded_solid('recessed_panel_door',.597,.035,1.25,'wood',r,.012,(side*.31,-.285,1.18))
        tube('door_pull',[(side*.31-side*.19,-.321,1.04),(side*.31-side*.19,-.35,1.07),(side*.31-side*.19,-.35,1.31),(side*.31-side*.19,-.321,1.34)],[.012]*4,'brass',r,n=6)
    rounded_solid('structural_drawer_divider',1.2,.46,.035,'wood',r,.005,(0,0,.525))
    drawer(r,1.15,.44,.38,(0,-.05,.10),'cabinet_lower_drawer')
    return r

def office_desk():
    r=root('detail_office_desk')
    rounded_solid('continuous_bullnose_desktop',2.6,1.1,.09,'wood',r,.04,(0,0,.79))
    for side in [-1,1]:tube('bent_desk_frame',[(side*1.02,-.43,.03),(side*1.02,-.43,.74),(side*1.02,.43,.74),(side*1.02,.43,.03)],[.045]*4,'iron',r)
    shell=casework('drawer_case',1.1,.85,.27,r);shell.location=(.5,0,.43)
    drawer(r,1.02,.75,.18,(.5,-.15,.48))
    return r

def tree(seed=0):
    random.seed(seed);r=root('landscape_tree')
    points=[(0,0,0),(.05,0,.3),(.04,.015,1.5),(.12,.03,2.8),(.18,0,4.1),(.14,.05,5.4)]
    edges=[(i,i+1)for i in range(5)];radii=[.28,.22,.16,.12,.075,.025];tips=[]
    for i in range(8):
        a=i*2.399963;z=2.5+(i%4)*.58;base=3 if z<3.6 else 4;length=1.25+random.random()*.45
        mid=(math.cos(a)*length*.6,math.sin(a)*length*.6,z+.55);tip=(math.cos(a)*length,math.sin(a)*length,z+1.3)
        k=len(points);points.extend([mid,tip]);edges.extend([(base,k),(k,k+1)]);radii.extend([.058,.018]);tips.append(tip)
    data=bpy.data.meshes.new('continuous_branch_graph');data.from_pydata(points,edges,[]);obj=bpy.data.objects.new('connected_trunk_and_branches',data);bpy.context.scene.collection.objects.link(obj);obj.parent=r
    skin=obj.modifiers.new('Connected branch junctions','SKIN');bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.context.view_layer.update()
    for vert,rad in zip(data.skin_vertices[0].data,radii):vert.radius=(rad,rad)
    data.skin_vertices[0].data[0].use_root=True
    sub=obj.modifiers.new('Simple rounded branch form','SUBSURF');sub.levels=1;sub.render_levels=1
    graph=bpy.context.evaluated_depsgraph_get();obj.data=bpy.data.meshes.new_from_object(obj.evaluated_get(graph));obj.modifiers.clear();obj.data.materials.append(M['bark'])
    uv=obj.data.uv_layers.new(name='UVMap')
    for poly in obj.data.polygons:
        poly.use_smooth=True
        for li in poly.loop_indices:
            c=obj.data.vertices[obj.data.loops[li].vertex_index].co;uv.data[li].uv=(math.atan2(c.y,c.x)/math.tau,c.z/1.6)
    for j,tip in enumerate(tips+[Vector((0,0,5.1))]):
        for k in range(5):
            a=k*math.tau/5+j*.73;center=Vector(tip)+Vector((math.cos(a)*.42,math.sin(a)*.42,.08*(k%2)));u=Vector((math.cos(a),math.sin(a),0));v=Vector((-.18*math.sin(a),.18*math.cos(a),1));v.normalize();w=1.05;h=.78
            normal=u.cross(v);verts=[tuple(center+u*x*w+v*z*h+normal*((1-x*x)*.12*math.cos(z)))for z in [-1,0,1]for x in [-1,0,1]]
            faces=[(zz*3+xx,zz*3+xx+1,(zz+1)*3+xx+1,(zz+1)*3+xx)for zz in range(2)for xx in range(2)]
            leaf=mesh('volumetric_leaf_cluster',verts,faces,'foliage',r)
            for poly in leaf.data.polygons:
                for li in poly.loop_indices:
                    idx=leaf.data.loops[li].vertex_index;leaf.data.uv_layers[0].data[li].uv=((idx%3)/2,(idx//3)/2)
    return r

def house(w=8,d=8,h=3.5,kind='gable'):
    r=root('rebuilt_building_'+kind);t=.20
    # Continuous open-U wall shell with mitred corners; south is the doorway.
    outer=[(-w/2,-d/2+t),(-w/2,d/2),(w/2,d/2),(w/2,-d/2+t)]
    inner=[(-w/2+t,-d/2+t),(-w/2+t,d/2-t),(w/2-t,d/2-t),(w/2-t,-d/2+t)]
    v=[(x,y,z)for z in [0,h]for ring in [outer,inner]for x,y in ring]
    faces=[]
    for i in range(3):faces.extend([(i,i+1,i+9,i+8),(i+4,i+12,i+13,i+5),(i+8,i+9,i+13,i+12),(i,i+4,i+5,i+1)])
    mesh('continuous_mitred_wall_shell',v,faces,'plaster',r)
    curve=bpy.data.curves.new('front_with_actual_openings','CURVE');curve.dimensions='2D';curve.fill_mode='BOTH';curve.extrude=t/2;curve.resolution_u=1
    def loop(points):
        s=curve.splines.new('POLY');s.points.add(len(points)-1)
        for p,(x,z)in zip(s.points,points):p.co=(x,z,0,1)
        s.use_cyclic_u=True
    loop([(-w/2,0),(-.7,0),(-.7,2.5),(.7,2.5),(.7,0),(w/2,0),(w/2,h),(-w/2,h)])
    apertures=[(x,1.,min(h-.4,2.35))for x in [-w*.30,w*.30]]
    if h>5.8:apertures.extend((x,4.05,min(h-.5,5.4))for x in [-w*.30,0,w*.30])
    for x,bottom,top in apertures:
        ww=min(1.65,w*.20)
        loop([(x-ww/2,bottom),(x-ww/2,top),(x+ww/2,top),(x+ww/2,bottom)])
        # A closed reveal ring adds physical window depth; fine muntins stay in a map.
        frame_ring('recessed_window_reveal',ww+.10,top-bottom+.10,.05,.22,'stone',r,(x,-d/2+.04,(top+bottom)/2))
        pane=mesh('inset_glazing',[(x-ww/2,-d/2+.14,bottom),(x+ww/2,-d/2+.14,bottom),(x+ww/2,-d/2+.14,top),(x-ww/2,-d/2+.14,top)],[(0,1,2,3)],'glass',r)
    frame_ring('continuous_entrance_reveal',1.6,2.7,.1,.24,'stone',r,(0,-d/2+.02,1.25),inner_size=(1.4,2.5))
    obj=bpy.data.objects.new('pierced_facade',curve);bpy.context.scene.collection.objects.link(obj);graph=bpy.context.evaluated_depsgraph_get();data=bpy.data.meshes.new_from_object(obj.evaluated_get(graph));bpy.data.objects.remove(obj,do_unlink=True)
    for vertex in data.vertices:x,z,depth=vertex.co;vertex.co=(x,-d/2+t/2+depth,z)
    obj=bpy.data.objects.new('pierced_facade',data);bpy.context.scene.collection.objects.link(obj);obj.parent=r;data.materials.append(M['plaster'])
    if not data.uv_layers:data.uv_layers.new(name='UVMap')
    for poly in data.polygons:
        for li in poly.loop_indices:co=data.vertices[data.loops[li].vertex_index].co;data.uv_layers[0].data[li].uv=(co.x,co.z)
    xx=w/2+.28;eave=h+.08
    if kind=='mansard':profile=[(-xx,eave),(-xx+.55,eave+1.05),(-xx+1,eave+1.32),(xx-1,eave+1.32),(xx-.55,eave+1.05),(xx,eave),(xx,eave-.10),(-xx,eave-.10)]
    elif kind=='barrel':
        profile=[(-xx*math.cos(i*math.pi/12),eave+1.2*math.sin(i*math.pi/12))for i in range(13)]+[(xx,eave-.12),(-xx,eave-.12)]
    elif kind=='hip':profile=[(-xx,eave),(-xx*.55,eave+1.2),(xx*.55,eave+1.2),(xx,eave),(xx,eave-.10),(-xx,eave-.10)]
    else:profile=[(-xx,eave),(0,eave+1.25),(xx,eave),(xx,eave-.10),(0,eave+1.13),(-xx,eave-.10)]
    roof=section('coherent_'+kind+'_roof',profile,d+.56,'roof',r);roof.rotation_euler.z=math.pi/2
    r['roof_family']=kind;r['door_clear_width']=1.4;r['door_clear_height']=2.5
    return r

def soft_body(name,w,d,h,material,parent,loc):
    vertices=[];outline=[(-.78,-1),(.78,-1),(1,-.78),(1,.78),(.78,1),(-.78,1),(-1,.78),(-1,-.78)]
    for z,s in [(-.5,.78),(-.28,.98),(.22,1),(.5,.76)]:vertices.extend((x*w*s/2,y*d*s/2,z*h)for x,y in outline)
    faces=[tuple(reversed(range(8))),tuple(range(24,32))]+[(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i)for j in range(3)for i in range(8)]
    obj=mesh(name,vertices,faces,material,parent,True);obj.location=loc;return obj

def bed():
    r=root('single_bed')
    tube('continuous_open_bed_frame',[(-.50,-1.0,.39),(.50,-1.0,.39),(.50,1.0,.39),(-.50,1.0,.39),(-.50,-1.0,.39)],[.035]*5,'iron',r,6)
    for x in [-.46,.46]:
        for y in [-.94,.94]:tube('tapered_bed_leg',[(x,y,.025),(x,y,.40)],[.026,.032],'iron',r,6)
    for y in [-.65,0,.65]:tube('mattress_cross_support',[(-.48,y,.40),(.48,y,.40)],[.02,.02],'iron',r,4)
    soft_body('rounded_mattress',1.02,2.04,.24,'linen',r,(0,0,.54));soft_body('filled_pillow',.76,.42,.15,'linen',r,(0,.71,.73))
    verts=[];cross=[-.60,-.56,-.52,-.50,-.45,0,.45,.50,.52,.56,.60]
    for j in range(9):
        y=-.97+j*1.35/8
        for i,x in enumerate(cross):
            z=.686-max(0,abs(x)-.51)*2.1+.004*math.sin(j*1.4+i*.65);verts.append((x,y,z))
    n=len(cross);faces=[(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i)for j in range(8)for i in range(n-1)];mesh('draped_fabric_cover',verts,faces,'cloth',r,True)
    rounded_solid('shaped_headboard',1.15,.10,1.2,'wood',r,.04,(0,1.07,.65));return r

def shelf():
    r=casework('book_shelf',1.6,.55,2.4)
    for z in [.55,1.02,1.49,1.96]:rounded_solid('structural_shelf',1.5,.49,.045,'wood',r,.005,(0,-.015,z))
    for row in range(4):
        # A continuous varied book-block silhouette; spine detail is textured.
        vertices=[];x=-.68
        for j in range(10):
            width=.11;top=.58+row*.47+.29+.035*((j+row)%3)
            vertices.extend([(x,-.23,.58+row*.47),(x+width,-.23,.58+row*.47),(x+width,-.23,top),(x,-.23,top),(x,.12,.58+row*.47),(x+width,.12,.58+row*.47),(x+width,.12,top),(x,.12,top)]);x+=.14
        faces=[]
        for j in range(10):
            k=j*8;faces.extend(tuple(k+i for i in f)for f in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)])
        obj=mesh('book_row_with_varied_heights',vertices,faces,'lacquer',r)
    return r

def kitchen_counter():
    r=casework('kitchen_counter',1.8,.65,.86,material='linen')
    rounded_solid('continuous_worktop',1.86,.7,.07,'iron',r,.025,(0,0,.90))
    for side in [-1,1]:
        rounded_solid('flush_cabinet_door',.84,.032,.7,'wood',r,.009,(side*.44,-.339,.46));tube('recessed_pull',[(side*.44-.12,-.37,.65),(side*.44-.10,-.39,.65),(side*.44+.10,-.39,.65),(side*.44+.12,-.37,.65)],[.011]*4,'iron',r,6)
    return r

def reception_counter():
    r=casework('reception_counter',3.4,.9,1.1,material='lacquer');rounded_solid('rounded_countertop',3.6,1.06,.12,'wood',r,.05,(0,0,1.14));return r

def hinged_door():
    r=root('door_hinged_1m');hinge=root('door_hinge',r);hinge.location=(-.49,0,0)
    rounded_solid('solid_door_leaf',.98,.065,2.38,'wood',hinge,.012,(.49,0,1.19))
    tube('lever_handle',[(.82,-.055,1.1),(.82,-.095,1.1),(.71,-.095,1.1)],[.016]*3,'brass',hinge,8);return r

def door_frame():
    r=root('door_frame_1m');frame_ring('one_piece_door_frame',1.18,2.52,.09,.19,'wood',r,(0,0,1.2));return r

def window():
    r=root('fixed_window_2m');frame_ring('joined_window_frame',2,1.55,.085,.16,'wood',r,(0,0,0))
    mesh('recessed_glass',[(-.915,.03,-.69),(.915,.03,-.69),(.915,.03,.69),(-.915,.03,.69)],[(0,1,2,3)],'glass',r)
    tube('window_centre_mullion',[(0,-.035,-.70),(0,-.035,.70)],[.025,.025],'wood',r,4);return r

def stairs():
    r=root('stairs_18');rise=3.2/18;run=.26
    profile=[(-.13,0),(17.5*run,0),(17.5*run,3.2)]
    for i in range(17,-1,-1):profile.extend([(i*run-run/2,(i+1)*rise),(i*run-run/2,i*rise)])
    section('single_closed_stair_body',profile,1.65,'stone',r)
    for side in [-1,1]:
        tube('continuous_handrail',[(side*.85,-.1,.9+rise),(side*.85,17*run,4.10)],[.03,.03],'brass',r)
        for i in [0,4,8,12,17]:tube('structural_baluster',[(side*.85,i*run,(i+1)*rise),(side*.85,i*run,(i+1)*rise+.88)],[.018,.018],'iron',r,6)
    return r

def upholstered_screen():
    r=root('privacy_screen')
    for side in [-1,1]:tube('bent_screen_frame',[(side*.85,-.28,.07),(side*.85,0,.07),(side*.85,0,1.83),(0,0,1.83)],[.022]*4,'iron',r)
    vertices=[(-.80+i*.10,.035*math.cos(i*math.pi),z)for z in [.30,1.77]for i in range(17)];mesh('one_pleated_fabric_sheet',vertices,[(i,i+1,i+18,i+17)for i in range(16)],'linen',r,True);return r

def chest():
    r=root('blue_props_chest');t=.04;w=1.85;d=.83;h=.8
    # Open-topped connected tray and four real wheels; hinge remains a pivot.
    profile=[(-d/2,0),(d/2,0),(d/2,h),(d/2-t,h),(d/2-t,t),(-d/2+t,t),(-d/2+t,h),(-d/2,h)]
    obj=section('continuous_chest_tray',profile,w,'lacquer',r);obj.location.z=.24
    for side in [-1,1]:rounded_solid('chest_end',t,d,h,'lacquer',r,.006,(side*(w/2-t/2),0,.24+h/2))
    lid=root('lid_hinge',r);lid.location=(0,d/2,1.05);rounded_solid('formed_lid',1.95,.94,.09,'lacquer',lid,.025,(0,-d/2,.035))
    for x in [-.88,.88]:
        for y in [-.4,.4]:tube('caster',[(x,y-.03,.14),(x,y+.03,.14)],[.12,.12],'iron',r,12)
    for x in [-.6,.6]:rounded_solid('outside_latch',.10,.04,.18,'brass',r,.008,(x,-.46,.96))
    return r

def printer():
    r=root('printer');rounded_solid('formed_printer_housing',.55,.43,.29,'linen',r,.045,(0,0,.17));rounded_solid('scanner_lid',.52,.36,.04,'iron',r,.025,(0,.04,.33));rounded_solid('output_tray',.4,.27,.02,'iron',r,.01,(0,-.28,.11));rounded_solid('paper_stack',.27,.24,.008,'linen',r,.004,(0,-.28,.127));return r

def cold_storage():
    r=casework('detail_cold_storage',1.3,.85,2.1,material='iron')
    pivot=root('fridge_hinge',r);pivot.location=(-.62,-.44,0)
    for z,h in [(.7,1.28),(1.72,.62)]:
        rounded_solid('recessed_insulated_door',1.22,.065,h,'linen',pivot,.025,(.62,0,z));tube('raised_fridge_pull',[(.98,-.045,z-.20),(.98,-.09,z-.16),(.98,-.09,z+.16),(.98,-.045,z+.20)],[.018]*4,'iron',pivot)
    return r

def trolley():
    r=root('detail_medical_trolley')
    for x in [-.38,.38]:tube('one_piece_trolley_frame',[(x,-.24,.12),(x,-.24,.95),(x,.24,.95),(x,.24,.12)],[.018]*4,'iron',r)
    for z in [.25,.66,.94]:rounded_solid('drawn_metal_tray',.83,.58,.035,'iron',r,.03,(0,0,z))
    for x in [-.38,.38]:
        for y in [-.24,.24]:tube('castor_wheel',[(x,y-.025,.09),(x,y+.025,.09)],[.075,.075],'iron',r,10)
    for i in range(3):soft_body('generic_sealed_pack',.16,.24,.045,'linen',r,(-.22+i*.20,0,.97))
    return r

def coat_rack():
    r=root('detail_costume_rack');tube('continuous_clothes_frame',[(-.8,-.25,.08),(-.8,0,.08),(-.8,0,1.75),(.8,0,1.75),(.8,0,.08),(.8,.25,.08)],[.026]*6,'iron',r)
    for i in range(6):
        x=-.62+i*.25;tube('hanger',[(x,0,1.74),(x-.10,0,1.57),(x+.10,0,1.57),(x,0,1.74)],[.007]*4,'brass',r,5)
        soft_body('hanging_costume',.23,.10,.82,'cloth',r,(x,0,1.14))
    return r

def iv_stand():
    r=root('detail_iv_stand');tube('telescopic_stand',[(0,0,.13),(0,0,1.92),(0,0,2.05),(.15,0,2.05),(.15,0,1.99)],[.018,.013,.013,.013,.013],'iron',r)
    for i in range(5):
        a=i*math.tau/5;tube('splayed_base',[(0,0,.15),(.28*math.cos(a),.28*math.sin(a),.06)],[.015,.015],'iron',r,6)
    r['bag_attached']=False;return r

def mirror():
    r=root('mirror_panel');frame_ring('coherent_mirror_frame',1.52,2.68,.085,.12,'brass',r,(0,0,1.35));mesh('mirror_surface',[(-.67,-.065,.10),(.67,-.065,.10),(.67,-.065,2.60),(-.67,-.065,2.60)],[(0,1,2,3)],'mirror',r);return r

def sink_unit():
    r=kitchen_counter();r.name='detail_sink_unit'
    for o in list(r.children):
        if o.name.startswith('continuous_worktop'):bpy.data.objects.remove(o,do_unlink=True)
    top=frame_ring('perforated_worktop',1.86,.70,.05,.07,'iron',r,(0,0,.90),inner_size=(.66,.40));top.rotation_euler.x=math.pi/2
    # Open vessel profile, not a dark disc painted over a solid counter.
    rim=frame_ring('deep_sink_rim',.70,.44,.045,.20,'iron',r,(0,-.02,.94));rim.rotation_euler.x=math.pi/2
    rounded_solid('sink_bottom',.60,.34,.035,'iron',r,.03,(0,-.02,.80));tube('swan_neck_tap',[(.28,.18,.94),(.28,.18,1.22),(.28,.10,1.29),(.28,-.06,1.27)],[.018]*4,'iron',r)
    return r

def wash_machine():
    r=root('washing_machine');rounded_solid('formed_washer_body',.68,.66,.94,'linen',r,.045,(0,0,.47))
    points=[(.235*math.cos(i*math.tau/24),-.36,.48+.235*math.sin(i*math.tau/24))for i in range(25)];tube('round_door_gasket',points,[.028]*25,'iron',r,6)
    vertices=[(0,-.385,.48)]+[(.20*math.cos(i*math.tau/24),-.385,.48+.20*math.sin(i*math.tau/24))for i in range(24)];mesh('washer_glazing',vertices,[(0,i+1,(i+1)%24+1)for i in range(24)],'glass',r)
    rounded_solid('control_fascia',.58,.025,.09,'iron',r,.01,(0,-.343,.84));return r

def phone():
    r=root('detail_office_phone');rounded_solid('sloped_phone_housing',.28,.23,.13,'linen',r,.025,(0,0,.065));receiver=root('receiver',r);receiver.location=(0,.075,.19)
    tube('continuous_shaped_receiver',[(-.17,-.025,-.02),(-.14,.015,.018),(-.09,.02,.03),(.09,.02,.03),(.14,.015,.018),(.17,-.025,-.02)],[.045,.04,.025,.025,.04,.045],'iron',receiver,8)
    rounded_solid('single_keypad_fascia',.17,.13,.012,'iron',r,.015,(0,-.03,.137))
    # A cable follows one smooth sweep instead of 35 independent cylinder actors.
    points=[(-.19-.04*i/35,-.02+.013*math.cos(i*math.tau/4),.09+.013*math.sin(i*math.tau/4))for i in range(36)];tube('continuous_phone_cord',points,[.004]*36,'iron',r,4)
    receiver['off_hook_local_translation']=[.34,-.15,.03];return r

def console():
    r=root('control_console');section('sloped_control_body',[(-.35,0),(.35,0),(.35,1.04),(-.35,.87)],1.8,'iron',r)
    for x in [-.5,0,.5]:
        frame_ring('monitor_housing',.43,.36,.035,.10,'iron',r,(x,.10,1.24));mesh('recessed_monitor',[(x-.18,.035,1.10),(x+.18,.035,1.10),(x+.18,.035,1.38),(x-.18,.035,1.38)],[(0,1,2,3)],'glass',r)
    rounded_solid('continuous_control_surface',1.6,.33,.02,'lacquer',r,.012,(0,-.13,.98));return r

def clock():
    r=root('wall_clock');points=[(.23*math.sin(i*math.tau/24),0,.23*math.cos(i*math.tau/24))for i in range(25)];tube('clock_bezel',points,[.024]*25,'brass',r,6)
    verts=[(0,.01,0)]+[(.215*math.sin(i*math.tau/24),.01,.215*math.cos(i*math.tau/24))for i in range(24)];mesh('clock_dial',verts,[(0,i+1,(i+1)%24+1)for i in range(24)],'linen',r)
    for i in range(12):
        a=i*math.tau/12;tube('dial_index',[(.176*math.sin(a),-.019,.176*math.cos(a)),(.198*math.sin(a),-.019,.198*math.cos(a))],[.004,.004],'iron',r,4)
    tube('minute_hand',[(0,-.025,0),(.06,-.025,.145)],[.005,.004],'iron',r,4);tube('hour_hand',[(0,-.027,0),(-.105,-.027,.03)],[.007,.005],'iron',r,4);r['hands_are_static_art_not_time_evidence']=True;return r

def microphone():
    r=root('microphone_stand');soft_body('weighted_microphone_foot',.44,.44,.10,'iron',r,(0,0,.055));tube('microphone_stand_tube',[(0,0,.08),(0,0,1.54),(.35,0,1.67)],[.022,.022,.017],'iron',r,8);tube('microphone_capsule',[(.34,0,1.67),(.52,0,1.72)],[.033,.032],'iron',r,12);return r

def ceiling_lamp():
    r=root('ceiling_lamp');tube('hanging_stem',[(0,0,0),(0,0,-.31)],[.022,.022],'brass',r,8)
    section('shaped_lamp_shade',[(-.26,-.43),(-.26,-.35),(-.13,-.30),(.13,-.30),(.26,-.35),(.26,-.43)],.50,'iron',r);rounded_solid('lamp_diffuser',.44,.44,.018,'light',r,.025,(0,0,-.44));return r

def sconce():
    r=root('wall_sconce');rounded_solid('sconce_wall_mount',.15,.045,.32,'iron',r,.018,(0,0,0));tube('curved_sconce_arm',[(0,-.03,-.05),(0,-.15,-.05),(0,-.18,.06)],[.015]*3,'brass',r,8);soft_body('frosted_sconce_globe',.18,.15,.26,'light',r,(0,-.18,.17));return r

def cooking_range():
    r=casework('detail_cooking_range',1.65,.75,.88,material='iron');rounded_solid('stove_top',1.72,.80,.06,'iron',r,.025,(0,0,.92));frame_ring('oven_door_frame',1.40,.53,.07,.045,'iron',r,(0,-.39,.43))
    for x in [-.4,.4]:
        for y in [-.16,.16]:
            points=[(x+.13*math.cos(i*math.tau/16),y+.13*math.sin(i*math.tau/16),.95)for i in range(17)];tube('formed_burner_ring',points,[.018]*17,'iron',r,4)
    rounded_solid('oven_glass',.75,.015,.38,'glass',r,.018,(0,-.37,.47));tube('oven_pull',[(-.32,-.39,.72),(-.28,-.43,.72),(.28,-.43,.72),(.32,-.39,.72)],[.014]*4,'iron',r,6);return r

def hood():
    r=root('detail_extraction_hood');verts=[(-1.05,-.475,-.09),(1.05,-.475,-.09),(1.05,.475,-.09),(-1.05,.475,-.09),(-.48,-.22,.30),(.48,-.22,.30),(.48,.22,.30),(-.48,.22,.30)]
    mesh('single_drawn_hood_shell',verts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'iron',r);rounded_solid('extraction_stack',.74,.42,.6,'iron',r,.02,(0,0,.58));return r

def vanity():
    r=root('detail_vanity_station');rounded_solid('vanity_worktop',1.8,.65,.12,'wood',r,.025,(0,0,.79))
    for side in [-1,1]:
        p=casework('vanity_pedestal',.32,.57,.72,r);p.location.x=side*.72;rounded_solid('flush_pedestal_front',.27,.025,.64,'wood',p,.008,(0,-.30,.36))
    frame_ring('mirror_surround',1.45,1.20,.07,.09,'wood',r,(0,.29,1.52));mesh('vanity_mirror_surface',[(-.645,.235,1),(.645,.235,1),(.645,.235,2.04),(-.645,.235,2.04)],[(0,1,2,3)],'mirror',r)
    for side in [-1,1]:
        for z in [1.08,1.38,1.68,1.98]:soft_body('vanity_bulb',.11,.09,.11,'light',r,(side*.70,.17,z))
    return r

def kiosk():
    r=casework('detail_refreshment_kiosk',3.6,1.8,1.1,material='lacquer');rounded_solid('curved_kiosk_counter',3.8,2,.12,'wood',r,.06,(0,-.05,1.13))
    for side in [-1,1]:tube('canopy_frame',[(side*1.75,.65,1.1),(side*1.75,.65,2.90)],[.048,.048],'iron',r,8)
    section('continuous_curved_canopy',[(-1.25,2.70),(-1.21,2.90),(-.7,3.14),(.6,3.14),(1.10,2.98),(1.10,2.89),(-.7,3.05),(-1.1,2.83),(-1.14,2.70)],4.1,'roof',r)
    return r

def key_rack():
    r=casework('hotel_key_rack',1.4,.18,1.0)
    for x in [-.47,0,.47]:
        for z in [.22,.54,.86]:tube('key_hook',[(x,-.12,z),(x,-.18,z),(x,-.18,z+.025)],[.008]*3,'brass',r,5)
    return r

def notice():
    r=root('wall_notice_plate');frame_ring('one_piece_notice_frame',.44,.30,.025,.035,'iron',r);rounded_solid('blank_notice_insert',.39,.008,.25,'linen',r,.002,(0,-.021,0));r['text_baked']=False;return r

def sensor():
    r=root('door_sensor');rounded_solid('rounded_sensor_housing',.07,.04,.12,'iron',r,.01);rounded_solid('sensor_indicator',.025,.006,.02,'light',r,.003,(0,-.024,.025));return r

def reinforcement():
    r=root('reinforcement_bar');section('rolled_metal_bar',[(-.06,-.09),(.06,-.09),(.06,.09),(-.06,.09),(-.06,.06),(.03,.06),(.03,-.06),(-.06,-.06)],1.42,'iron',r)
    for side in [-1,1]:
        bracket=section('formed_end_bracket',[(-.10,-.16),(.10,-.16),(.10,.16),(.06,.16),(.06,-.12),(-.10,-.12)],.14,'iron',r);bracket.location.x=side*.60
    return r

def archive_box():
    r=root('archive_box');rounded_solid('folded_archive_box',.48,.36,.36,'linen',r,.008,(0,0,.18));rounded_solid('folded_box_lid',.50,.38,.035,'wood',r,.008,(0,0,.38));rounded_solid('blank_label',.23,.006,.09,'linen',r,.002,(0,-.185,.20));r['text_baked']=False;return r

def floor_tile():
    r=root('floor_tile_4m');rounded_solid('single_floor_surface',4,4,.08,'paving',r,.001,(0,0,-.04));return r

def wall_panel():
    r=root('wall_panel_4m');rounded_solid('coherent_wall_volume',4,.18,3.2,'plaster',r,.005,(0,0,1.6));return r

def podium():
    r=root('trial_podium')
    # A single curved closed shell and overhanging desk, with a real recess.
    for name,z,h,rad in [('podium_foot',.08,.16,.68),('podium_body',.59,.94,.60),('podium_worktop',1.10,.10,.72)]:
        verts=[(rad*math.cos(i*math.tau/24),rad*math.sin(i*math.tau/24),zz)for zz in [z-h/2,z+h/2]for i in range(24)]
        mesh(name,verts,[tuple(reversed(range(24))),tuple(range(24,48))]+[(i,(i+1)%24,(i+1)%24+24,i+24)for i in range(24)],'wood' if name=='podium_worktop' else 'lacquer',r,True)
    return r

def nozzle():
    r=root('fountain_nozzle');tube('machined_nozzle',[(0,0,0),(0,0,.24)],[.045,.025],'brass',r,12);r['water_not_baked']=True;return r

def curved_family(key):
    import v4_sculpted_kit as S
    S.LOW_DETAIL=True;S.M.update({k:M[v]for k,v in {'wood':'wood','stone':'stone','iron':'iron','brass':'brass','cloth':'cloth','leaf':'leaf','glass':'light'}.items()})
    obj=({'street_lamp':S.lamp}|S.BUILDERS)[key]()
    S.bake_modifiers(obj.children_recursive)
    for part in obj.children_recursive:
        if part.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(part.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.dissolve_degenerate(bm,dist=.0000001,edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(part.data);bm.free()
    return obj

BUILDERS={'storage_cabinet':storage_cabinet,'detail_office_desk':office_desk,'single_bed':bed,'book_shelf':shelf,'kitchen_counter':kitchen_counter,'reception_counter':reception_counter,'door_hinged_1m':hinged_door,'door_frame_1m':door_frame,'fixed_window_2m':window,'stairs_18':stairs,'privacy_screen':upholstered_screen,'blue_props_chest':chest,'printer':printer,'detail_cold_storage':cold_storage,'detail_medical_trolley':trolley,'detail_costume_rack':coat_rack,'detail_iv_stand':iv_stand,'mirror_panel':mirror,'detail_sink_unit':sink_unit,'washing_machine':wash_machine,'detail_office_phone':phone,'control_console':console,'wall_clock':clock,'microphone_stand':microphone,'ceiling_lamp':ceiling_lamp,'wall_sconce':sconce,'detail_cooking_range':cooking_range,'detail_extraction_hood':hood,'detail_vanity_station':vanity,'detail_refreshment_kiosk':kiosk,'hotel_key_rack':key_rack,'wall_notice_plate':notice,'door_sensor':sensor,'reinforcement_bar':reinforcement,'archive_box':archive_box,'floor_tile_4m':floor_tile,'wall_panel_4m':wall_panel}
BUILDERS.update({key:(lambda k=key:curved_family(k))for key in ['park_bench','detail_fountain_dry','detail_planter','chair','meeting_table','street_lamp']})
BUILDERS.update({'trial_podium':podium,'fountain_nozzle':nozzle})

