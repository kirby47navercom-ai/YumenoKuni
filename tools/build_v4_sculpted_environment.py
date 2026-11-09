"""Rebuild prop bodies and pierced architectural shells, preserving game metadata.

Run Blender --background --python tools/build_v4_sculpted_environment.py.
Original sources are never overwritten. Exported replacements retain their runtime
path and root transform; the copy manifest is published by the integration tool.
"""
import bpy,json,math,sys,hashlib,os,subprocess,struct
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_sculpted_kit as K
O=R/'art/space_v4/sculpted_v1';O.mkdir(parents=True,exist_ok=True)
P=R/'Game/Saved/sculpted-environment-20261103';P.mkdir(parents=True,exist_ok=True)
S=R/'art/space_v4/full_v2'

def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True);K.materials(O/'maps')

def family(o):return [o,*o.children_recursive]

def export(objects,filename,runtime,join=False):
    objects=[o for o in objects if o.name in bpy.data.objects]
    K.bake_modifiers(objects);bpy.ops.object.select_all(action='DESELECT')
    meshes=[o for o in objects if o.type=='MESH']
    assert meshes,filename
    if join:
        for o in meshes:o.hide_set(False);o.hide_render=False;o.select_set(True)
        bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join();joined=bpy.context.object;matrix=joined.matrix_world.copy();joined.parent=None;joined.matrix_world=matrix
        if joined.data.users>1:joined.data=joined.data.copy()
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);objects=[joined]
    else:
        for o in objects:o.hide_set(False);o.hide_render=False;o.select_set(True)
        bpy.context.view_layer.objects.active=meshes[0]
    for o in objects:
        if o.type=='MESH' and any(len(p.vertices)>4 for p in o.data.polygons):o.modifiers.new('export_ngon_triangulation','TRIANGULATE')
    K.bake_modifiers(objects)
    path=O/filename;bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_extras=False,export_tangents=True)
    if path.stat().st_size>=64*1024*1024:subprocess.run(['python',str(R/'tools/pack_sculpted_glb.py'),str(path)],check=True)
    return {'file':path.relative_to(R).as_posix(),'runtime':runtime,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def upper_windows(w,h):return [(x,4.05,5.25,.36,min(1.8,w*.18)) for x in [-w*.3,0,w*.3]] if h>5.5 else []

def architectural_body(parent,w,d,h):
    for child in list(parent.children):
        if child.name.startswith('sculpted_architecture'):
            for part in reversed(family(child)):bpy.data.objects.remove(part,do_unlink=True)
    r=K.root('sculpted_architecture',parent);front=-d/2-.10
    # Profiled stonework is extruded as a continuous section, including returns.
    for z in [.15,h-.13]:
        profile=[(front+.08,z-.10),(front-.12,z-.10),(front-.20,z-.045),(front-.20,z+.015),(front-.13,z+.055),(front-.10,z+.13),(front+.08,z+.13)]
        K.extrusion('coved_stone_course',profile,w+.14,'stone',r)
    for x in [-w/2+.16,-.96,.96,w/2-.16]:
        p=K.lathe('engaged_fluted_column',[(0,.05),(.14,.05),(.15,.12),(.15,.23),(.115,.30),(.09,.4),(.085,h-.43),(.12,h-.32),(.15,h-.29),(.15,h-.16),(0,h-.16)],'stone',r,n=24,flute=.035);p.location=(x,front-.10,0)
    K.sweep('entrance_arch',[(.80*math.cos(i*math.pi/32),front-.13,2.48+.42*math.sin(i*math.pi/32)) for i in range(33)],.07,'brass',r)
    for x,bottom,spring,rise,ww in upper_windows(w,h):
        pts=[(x-ww/2,front-.035,bottom),(x-ww/2,front-.035,spring)]
        pts.extend((x+ww/2*math.cos(math.pi-i*math.pi/32),front-.035,spring+rise*math.sin(math.pi-i*math.pi/32)) for i in range(33));pts.append((x+ww/2,front-.035,bottom));K.sweep('upper_architrave',pts,.055,'stone',r)
        K.mesh('upper_recessed_glazing',[(p[0],front+.16,p[2]) for p in pts],[tuple(range(len(pts)))],'glass',r)
        K.sweep('upper_mullion',[(x,front+.13,bottom),(x,front+.13,spring+rise)],.022,'iron',r,n=8)
        K.sweep('upper_transom',[(x-ww/2,front+.13,spring-.15),(x+ww/2,front+.13,spring-.15)],.02,'iron',r,n=8)
        K.board('upper_profiled_sill',(x,front-.06,bottom-.06),ww+.2,.4,.12,'stone',r)
    return r

def pierced_wall(parent,w,d,h):
    # One filled 2D contour with holes, then one closed extrusion. Segmenting
    # the flat front into disconnected quads creates false internal shadow rims.
    curve=bpy.data.curves.new('pierced_wall_contour','CURVE');curve.dimensions='2D';curve.fill_mode='BOTH';curve.extrude=.12;curve.bevel_depth=.012;curve.bevel_resolution=2;curve.resolution_u=1
    def loop(points):
        s=curve.splines.new('POLY');s.points.add(len(points)-1)
        for p,(x,z) in zip(s.points,points):p.co=(x,z,0,1)
        s.use_cyclic_u=True
    loop([(-w/2,0),(-.7,0),(-.7,2.5),(.7,2.5),(.7,0),(w/2,0),(w/2,h),(-w/2,h)])
    for x,bottom,spring,rise,ww in [(x,1,2.10,.38,min(2,w*.22)) for x in [-w*.3,w*.3]]+upper_windows(w,h):
        pts=[(x-ww/2,bottom),(x+ww/2,bottom),(x+ww/2,spring)]
        pts.extend((x+ww/2*math.cos(i*math.pi/32),spring+rise*math.sin(i*math.pi/32)) for i in range(1,33));loop(list(reversed(pts)))
    o=bpy.data.objects.new('pierced_arch_wall',curve);bpy.context.scene.collection.objects.link(o)
    graph=bpy.context.evaluated_depsgraph_get();data=bpy.data.meshes.new_from_object(o.evaluated_get(graph));bpy.data.objects.remove(o,do_unlink=True)
    o=bpy.data.objects.new('pierced_arch_wall',data);bpy.context.scene.collection.objects.link(o);o.parent=parent
    for vertex in data.vertices:
        x,z,depth=vertex.co;vertex.co=(x,-d/2-.10+depth,z)
    import bmesh
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free();data.update()
    # Curve conversion already supplies a perimeter-following UVMap. Replace it
    # rather than adding UVMap.001: glTF consumes the first/render layer and the
    # old contour UV bends stone veins into rings around doors and windows.
    uv=data.uv_layers[0] if data.uv_layers else data.uv_layers.new(name='UVMap')
    data.uv_layers.active_index=0;uv.active_render=True
    for extra in list(data.uv_layers)[1:]:data.uv_layers.remove(extra)
    for polygon in data.polygons:
        for li in polygon.loop_indices:
            p=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=(p.x,p.z)
    data.materials.append(K.M['stone']);return o

def facade(parent,w,d,h):
    # Delete the old blind front walls and stuck-on window strips, retaining
    # original side/back walls, portal and source-local transform.
    remove=('facade_front','facade_lintel','pitched_cel_roof','roof','window','front_','entry_arch','corner_column','pilaster','blank_signboard')
    for o in list(parent.children_recursive):
        if o.name.startswith(remove):bpy.data.objects.remove(o,do_unlink=True)
    front=-d/2-.10
    windows=[(-w*.3,min(2,w*.22)),(w*.3,min(2,w*.22))]
    pierced_wall(parent,w,d,h)
    for x,ww in windows:
        pts=[(x-ww/2,front-.035,1),(x-ww/2,front-.035,2.10)]
        pts.extend((x+ww/2*math.cos(math.pi-i*math.pi/32),front-.035,2.10+.38*math.sin(math.pi-i*math.pi/32)) for i in range(33))
        pts.append((x+ww/2,front-.035,1));K.sweep('carved_architrave',pts,.055,'stone',parent)
        # The recessed glazing lies behind the actual wall aperture, no decal.
        points=[(p[0],front+.16,p[2]) for p in pts];K.mesh('recessed_arch_glazing',points,[tuple(range(len(points)))],'glass',parent)
        for dx in [-ww/4,0,ww/4]:K.sweep('slender_window_mullion',[(x+dx,front+.13,1.03),(x+dx,front+.13,2.10+.38*math.sqrt(max(0,1-(dx/(ww/2))**2)))],.018,'iron',parent,n=8)
        K.sweep('window_transom',[(x-ww/2,front+.13,1.65),(x+ww/2,front+.13,1.65)],.023,'iron',parent,n=8)
        K.board('profiled_stone_sill',(x,front-.05,.94),ww+.22,.42,.12,'stone',parent)
    # Roof body: continuous pitched extrusion with an actual soffit and thickness.
    xx=w/2+.36;yy=d/2+.38;eave=h+.13;ridge=h+1.48
    contour=[(-xx,eave),(-xx,eave+.13),(0,ridge),(xx,eave+.13),(xx,eave),(0,ridge-.15)]
    # extrusion() extrudes along X, so rotate the authored YZ profile into XZ.
    roof=K.extrusion('solid_pitched_roof',contour,yy*2,'iron',parent);roof.rotation_euler.z=math.pi/2
    for side in [-1,1]:K.sweep('roof_eave_moulding',[(side*xx,-yy,eave),(side*xx,yy,eave)],.065,'brass',parent)
    K.sweep('rolled_ridge_cap',[(0,-yy-.02,ridge+.025),(0,yy+.02,ridge+.025)],.075,'brass',parent)
    for y in [-yy,yy]:K.sweep('gable_stone_fascia',[(-xx,y,eave),(0,y,ridge),(xx,y,eave)],.065,'stone',parent)
    architectural_body(parent,w,d,h)
    return {'parent':parent.name,'windows':2+len(upper_windows(w,h)),'wallThickness':.24,'windowDepth':.16}

def render_kit():
    clear();scene=bpy.context.scene
    objects=[]
    for builder,x in [(K.fountain,0),(K.bench,-3.6),(K.lamp,3.1),(K.planter,4.3),(K.chair,-3.0),(K.table,-3.5)]:
        o=builder();o.location=(x,0,0);objects+=family(o)
        if builder==K.chair:o.location.y=1.6
        if builder==K.table:o.location.y=3
    K.bake_modifiers(objects)
    health=K.mesh_health(objects)
    (O/'kit-health.json').write_text(json.dumps(health,indent=2))
    # Editable complete source, not a screenshot substitute for game geometry.
    scene.world=bpy.data.worlds.new('neutral_preview_world');scene.world.use_nodes=True
    bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.16,.20,.26,1);bg.inputs['Strength'].default_value=.65
    bpy.ops.mesh.primitive_plane_add(size=200);ground=bpy.context.object;ground.data.materials.append(K.M['stone']);ground.location.z=-.025
    bpy.ops.object.light_add(type='AREA',location=(-4,-5,8));key=bpy.context.object;key.data.energy=1600;key.data.shape='DISK';key.data.size=5;key.rotation_euler=(Vector((0,0,1))-key.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='AREA',location=(4,3,6));key=bpy.context.object;key.data.energy=950;key.data.size=4;key.rotation_euler=(Vector((0,0,1))-key.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(8,-12,7));cam=bpy.context.object;scene.camera=cam;cam.rotation_euler=(Vector((.2,0,1.3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=48
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
    scene.render.filepath=str(P/'kit-materials.png');bpy.ops.wm.save_as_mainfile(filepath=str(O/'sculpted-kit.blend'));bpy.ops.render.render(write_still=True)
    # Wire geometry evidence of the same editable mesh.
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.show_cavity=True;scene.display.shading.show_shadows=True
    for o in objects:
        if o.type=='MESH':o.show_wire=True;o.show_all_edges=True
    scene.render.filepath=str(P/'kit-topology.png');bpy.ops.render.render(write_still=True)

mode=os.environ.get('V4_SCULPT_MODE','all')
if mode=='preview':render_kit();sys.exit(0)
if mode=='walls':
    bpy.ops.wm.open_mainfile(filepath=str(O/'park-sculpted-source.blend'));K.materials(O/'maps');world=bpy.data.objects['park_exterior_level']
    layout=json.loads((S/'world_layout.json').read_text(encoding='utf8'));specs={s['id']:s for s in json.loads((S/'manifest.json').read_text(encoding='utf8'))['spaces']}
    for inst in layout['instances']:
        p=bpy.data.objects.get('facade_'+inst['id'])
        if not p or p.type!='EMPTY':continue
        for child in list(p.children):
            if child.name.startswith('pierced_arch_wall'):bpy.data.objects.remove(child,do_unlink=True)
        pierced_wall(p,*specs[inst['asset_id']]['size_m'])
        architectural_body(p,*specs[inst['asset_id']]['size_m'])
    groups=[bpy.data.objects['exterior_'+n] for n in ['plaza','park_garden','pool_edge','ferris_platform','coaster_platform','park_main_gate']];exclude=set(o for p in groups for o in family(p))
    bpy.ops.wm.save_as_mainfile(filepath=str(O/'park-sculpted-source.blend'))
    asset=export([o for o in world.children_recursive if o.type=='MESH' and o not in exclude],'finish_context.glb','Assets/Art/explore3d/finish_context.glb',True)
    for filename in ['manifest.json','exterior-manifest.json']:
        result=json.loads((O/filename).read_text(encoding='utf8'));result['assets']=[asset if a['runtime']==asset['runtime'] else a for a in result['assets']];(O/filename).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('PIERCED_WALLS_REBUILT',flush=True);sys.exit(0)
result={'policy':'Original continuous surface prop bodies + real pierced facade wall/roof shells. No original-game extraction, engine edits, gameplay metadata or placement changes.','assets':[],'replacements':[]}
catalog=json.loads((R/'art/space_v4/runtime_v1/copy_manifest.json').read_text(encoding='utf8'))
baseline=O/'source-catalog.json'
if baseline.exists():catalog=json.loads(baseline.read_text(encoding='utf8'))
else:baseline.write_text(json.dumps(catalog,indent=2),encoding='utf8')
if mode in ('all','exterior'):
    reuse=os.environ.get('V4_SCULPT_REUSE_SOURCE')=='1'
    bpy.ops.wm.open_mainfile(filepath=str(O/'park-sculpted-source.blend' if reuse else S/'park_exterior_r2_source.blend'));K.materials(O/'maps');world=bpy.data.objects['park_exterior_level']
    layout=json.loads((S/'world_layout.json').read_text(encoding='utf8'));specs={s['id']:s for s in json.loads((S/'manifest.json').read_text(encoding='utf8'))['spaces']}
    result['facades']=[]
    for inst in layout['instances']:
        p=bpy.data.objects.get('facade_'+inst['id'])
        if p and p.type=='EMPTY':result['facades'].append({'parent':p.name,'reusedEditableSource':True} if reuse else facade(p,*specs[inst['asset_id']]['size_m']))
    if not reuse:result['replacements']+=K.replace_props(list(world.children_recursive))
    result['seatCorrections']=K.orient_path_benches(list(world.children_recursive))
    groups={n:bpy.data.objects['exterior_'+n] for n in ['plaza','park_garden','pool_edge','ferris_platform','coaster_platform','park_main_gate']}
    landmarks=set(o for p in groups.values() for o in family(p));common=[o for o in world.children_recursive if o.type=='MESH' and o not in landmarks]
    # Save the editable environment once before joining optimized runtime chunks.
    K.bake_modifiers(list(world.children_recursive))
    bpy.ops.wm.save_as_mainfile(filepath=str(O/'park-sculpted-source.blend'))
    result['assets'].append(export(common,'finish_context.glb','Assets/Art/explore3d/finish_context.glb',True))
    for n,p in groups.items():result['assets'].append(export(family(p),'finish_'+n+'.glb','Assets/Art/explore3d/finish_'+n+'.glb',True))
    (O/'exterior-manifest.json').write_text(json.dumps(result,indent=2))
if mode in ('all','rooms'):
    if mode=='rooms':result=json.loads((O/'exterior-manifest.json').read_text())
    for row in catalog:
        if not row['from'].endswith('.glb') or '/finish_' in row['to']:continue
        raw=(R/row['from']).read_bytes();spec=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
        if not any(any(n.get('name','').split('.')[0].endswith('_'+key) for key in K.BUILDERS) or n.get('name','').split('.')[0]=='lamp_post' for n in spec['nodes']):continue
        clear();bpy.ops.import_scene.gltf(filepath=str(R/row['from']));objects=list(bpy.data.objects);changes=K.replace_props(objects)
        if not changes:continue
        new_objects=list(bpy.data.objects);name=Path(row['to']).name
        asset=export(new_objects,name,row['to']);asset['source']=row['from'];asset['replacements']=changes;result['assets'].append(asset)
        print('SCULPTED_ROOM',name,len(changes),flush=True)
if mode=='exterior' and (O/'manifest.json').exists():
    previous=json.loads((O/'manifest.json').read_text(encoding='utf8'))
    result['assets'] += [a for a in previous['assets'] if '/finish_' not in a['runtime']]
(O/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('SCULPTED_ENVIRONMENT_READY',len(result['assets']),flush=True)
