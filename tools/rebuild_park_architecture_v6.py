"""Sequential architecture authoring, real geometric inspection and render views."""
import bpy,bmesh,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector
R=Path.cwd();sys.path.insert(0,str(R/'tools'));import v4_rebuilt_environment_kit as K;import park_architecture_v6 as A
O=R/'art/space_v4/park_levels_v1/architecture_v6';W=R/'Game/Saved/park-architecture-v6';O.mkdir(exist_ok=True);W.mkdir(exist_ok=True)
ident=next((a.split('=',1)[1]for a in sys.argv if a.startswith('--asset=')),'clinic');D=O/ident;D.mkdir(exist_ok=True)

def weld_collinear_boolean_junctions(root):
    repaired=0
    for o in root.children_recursive:
        if o.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(o.data);boundary=[e for e in bm.edges if e.is_boundary];points={v for e in boundary for v in e.verts}
        for edge in boundary:
            if not edge.is_valid:continue
            a,b=edge.verts;direction=b.co-a.co
            if direction.length_squared<1e-14:continue
            candidates=[]
            for v in points:
                if v in edge.verts:continue
                t=(v.co-a.co).dot(direction)/direction.length_squared
                if 1e-6<t<1-1e-6 and (a.co+direction*t-v.co).length<1e-6:candidates.append((t,v.co.copy()))
            # A Boolean n-gon's collinear ear can dissolve into a T junction.
            # Split the corresponding long edge at its existing real vertices;
            # never cap an opening or conceal a non-manifold shell.
            part=edge;limit=1.0
            for t,co in sorted(candidates,reverse=True):
                _,v=bmesh.utils.edge_split(part,a,t/limit);v.co=co
                part=next(e for e in v.link_edges if a in e.verts);limit=t;repaired+=1
        if boundary:
            bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.triangulate(bm,faces=list(bm.faces),ngon_method='EAR_CLIP');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);o.data.update()
        bm.free()
    return repaired

def inspect(root):
    rows=[];tri=0
    for o in root.children_recursive:
        if o.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-12 for f in bm.faces);volume=bm.calc_volume(signed=True);bm.free();n=sum(len(p.vertices)-2 for p in o.data.polygons);tri+=n
        if bad or deg or volume<=0:
            q=bmesh.new();q.from_mesh(o.data)
            (W/(ident+'-topology-failure.json')).write_text(json.dumps({'mesh':o.name,'badEdges':[[list(v.co)for v in e.verts]for e in q.edges if not e.is_manifold],'zeroFaces':[[list(v.co)for v in f.verts]for f in q.faces if f.calc_area()<1e-12]},indent=2));q.free()
        assert not bad and not deg and volume>0,(o.name,bad,deg,volume)
        assert o.data.uv_layers and all(o.data.materials[p.material_index]for p in o.data.polygons),o.name
        rows.append({'name':o.name,'triangles':n,'nonManifoldEdges':bad,'degenerateFaces':deg,'volume':volume})
    assert tri<16000,('Small facility triangle budget',ident,tri)
    return {'ok':True,'id':ident,'triangles':tri,'meshObjects':len(rows),'rows':rows,'scope':'Actual closed mesh/UV/material/volume checks, not aesthetic or runtime acceptance.'}

def author():
    bpy.ops.wm.read_factory_settings(use_empty=True);K.setup_materials();root=A.BUILDERS[ident]();bpy.context.view_layer.update()
    # Validate the exact triangulated runtime topology, including removal of
    # collinear polygon ears, before any source is accepted or rendered.
    import build_v4_rebuilt_environment as E
    E.freeze([root,*root.children_recursive]);repaired=weld_collinear_boolean_junctions(root);proof=inspect(root);proof['weldedCollinearBooleanJunctions']=repaired;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(D/'source.blend'),compress=True);proof['sourceSHA256']=hashlib.sha256((D/'source.blend').read_bytes()).hexdigest();(D/'geometry.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('ARCHITECTURE_AUTHORED',ident,proof['triangles'],flush=True)

def render():
    context_source=None
    if ident in ('mirror_maze','mirror_observatory_support'):
        # Review replacements in their exact retained context. Only the new
        # review scene is rendered. The master authoring file is never saved.
        master=O.parent/'parks-authoring.blend'
        bpy.ops.wm.open_mainfile(filepath=str(master))
        scene=bpy.data.scenes.new(ident+'_exact_context_review')
        bpy.context.window.scene=scene
        if ident=='mirror_maze':
            facade=bpy.data.objects['actual_mask_funhouse_front']
            facade.parent=None;facade.location=(0,0,0)
            for o in [facade,*facade.children_recursive]:scene.collection.objects.link(o)
            context_owner='actual_mask_funhouse_front'
        else:
            original=bpy.data.objects['park_level_mirrors']
            retired=A.obstructing_observatory_column(original)
            baseline=next(row for row in json.loads((W/'existing.json').read_text(encoding='utf8'))['rows'] if row['id']=='42')
            waiting=bpy.data.objects['parkcopy_facade_mirror_waiting']
            for o in [waiting,*waiting.children_recursive]:scene.collection.objects.link(o)
            waiting.parent=None;waiting.location=(0,0,0)
            parts=[bpy.data.objects[entry['name']] for entry in baseline['groups']]
            parts.extend(o for o in original.children if o.name.startswith('fitted_stair_handrail'))
            for obj in parts:
                if obj==retired:continue
                scene.collection.objects.link(obj)
                obj.parent=None;obj.location-=Vector((14,3.5,0))
            context_owner='park_level_mirrors/observatory'
        with bpy.data.libraries.load(str(D/'source.blend'),link=False) as (a,b):b.objects=list(a.objects)
        for o in b.objects:scene.collection.objects.link(o)
        root=next(o for o in b.objects if o.parent is None)
        context_source={'owner':context_owner,'masterSHA256':hashlib.sha256(master.read_bytes()).hexdigest()}
    else:
        bpy.ops.wm.open_mainfile(filepath=str(D/'source.blend'))
        scene=bpy.context.scene
        root=next(o for o in scene.objects if o.parent is None and o.type=='EMPTY')
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='OPTIX'
        if any(d.use for d in prefs.devices):scene.cycles.device='GPU'
    except Exception:pass
    scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
    world=bpy.data.worlds.new('review_world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.36,.43,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
    floor=A.mesh('review_only_ground',[(-100,-100,-.035),(100,-100,-.035),(100,100,-.035),(-100,100,-.035)],[(0,1,2,3)],None,None,0);mat=bpy.data.materials.new('review_only_ground');mat.diffuse_color=(.16,.18,.2,1);floor.data.materials.append(mat)
    walk=json.loads(root['reviewWalkPoints']) if root.get('reviewWalkPoints') else None
    focus=Vector((0,0,0))
    if walk:
        focus=Vector(((min(p[0] for p in walk)+max(p[0] for p in walk))*.5,(min(p[1] for p in walk)+max(p[1] for p in walk))*.5,0))
    for name,at,energy,size,color in [('key',(-10,-12,18),2400,10,(1,.88,.75)),('fill',(12,0,12),1400,9,(.70,.82,1)),('rim',(-4,12,16),2200,8,(1,.88,.76))]:
        d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=Vector(at)+focus;o.rotation_euler=(focus+Vector((0,0,2))-o.location).to_track_quat('-Z','Y').to_euler();d.energy=energy;d.shape='DISK';d.size=size;d.color=color
    d=bpy.data.cameras.new('review_camera');cam=bpy.data.objects.new('review_camera',d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO'
    if root.get('presentationLights'):
        for rig in json.loads(root['presentationLights']):
            light=bpy.data.lights.new('authored_review_'+rig['id'],'SPOT');o=bpy.data.objects.new(light.name,light);scene.collection.objects.link(o);o.location=rig['position'];o.rotation_euler=(Vector(rig['target'])-o.location).to_track_quat('-Z','Y').to_euler();light.energy=700;light.color=rig['color'][:3];light.spot_size=math.radians(rig['angle']);light.spot_blend=rig['penumbra'];light.shadow_soft_size=.18
    shots=[('front',(0,-26,4.8),(0,0,2),13.8),('side',(26,0,5),(0,0,2),14),('rear',(0,26,5),(0,0,2),13.8),('quarter',(18,-24,17),(0,0,1.8),16),('entry-close',(4,-11,4.7),(0,-4.4,1.8),6.8),('roof-close',(9,-8,12),(0,0,3.3),10)]
    if ident=='performance_stage':shots=[('front',(0,-32,7),(0,0,3.6),19),('side',(32,0,7),(0,0,3.6),21),('rear',(0,32,7),(0,0,3.6),19),('quarter',(23,-29,22),(0,0,3.4),25),('entry-close',(7,-17,7.5),(0,-8.1,3.1),9),('roof-close',(16,-14,19),(0,0,5.4),18)]
    if ident=='dream_lobby':shots=[('front',(0,-29,5.1),(0,0,2),16.2),('side',(28,0,5),(0,0,2),14),('rear',(0,29,5.1),(0,0,2),16.2),('quarter',(21,-27,19),(0,0,1.9),20.5),('entry-close',(4,-11,4.7),(0,-4.4,1.8),6.8),('roof-close',(9,-8,12),(0,0,3.3),10)]
    if ident=='record_room':shots=[('front',(0,-30,5.4),(0,0,2.3),16.2),('side',(30,0,6),(0,0,2.3),16),('rear',(0,30,5.4),(0,0,2.3),16.2),('quarter',(23,-28,20),(0,0,2.2),22),('entry-close',(4,-13,4.7),(0,-5.2,1.8),8),('roof-close',(10,-10,14),(0,0,3.6),12)]
    if ident=='screening_room':shots=[('front',(0,-35,7),(0,0,3.1),17),('side',(35,0,7),(0,0,3.1),23),('rear',(0,35,7),(0,0,3.1),17),('quarter',(26,-32,22),(0,0,3),27),('entry-close',(5,-18,5.7),(0,-10.0,1.9),9),('roof-close',(13,-12,18),(0,0,4.6),18)]
    if ident=='exhibition_room':shots=[('front',(0,-29,5.5),(0,0,2.3),16.4),('side',(28,0,5.7),(0,0,2.3),15.2),('rear',(0,29,5.5),(0,0,2.3),16.4),('quarter',(21,-27,19),(0,0,2.1),22),('entry-close',(4,-13,4.4),(0,-5.9,1.8),8.5),('roof-close',(10,-10,14),(0,0,3.7),12)]
    if ident=='service_lodge':shots=[('front',(0,-18,4.2),(0,0,1.6),6.5),('side',(18,0,4.2),(0,0,1.6),6.2),('rear',(0,18,4.2),(0,0,1.6),6.5),('quarter',(12,-14,11),(0,0,1.6),8.2),('entry-close',(4,-7,3.6),(0,-2.0,1.45),4.6),('roof-close',(5,-6,9),(0,0,2.7),6.5)]
    if ident.endswith('_return_threshold'):shots=[('front',(0,-29,6.4),(0,0,3.6),16),('side',(29,0,6.4),(0,0,3.6),12),('rear',(0,29,6.4),(0,0,3.6),16),('quarter',(19,-27,15),(0,0,3.3),18),('entry-close',(10,-9,4.2),(5.6,0,3.4),8),('roof-close',(10,-9,11),(4.9,0,6.1),8)]
    if ident=='mirror_maze':shots=[('front',(0,-40,6.5),(0,0,3.6),20.5),('side',(42,0,7),(0,0,3.2),23),('rear',(0,41,7),(0,0,3.1),20),('quarter',(29,-36,22),(0,0,3.3),28),('entry-close',(6,-19,5.8),(0,-9.2,2.5),10),('roof-close',(14,-12,18),(0,-1,4.4),20)]
    if ident=='mirror_observatory_support':shots=[('front',(2.5,-42,9),(2.5,0,6.1),27),('side',(43,0,9),(0,0,6.7),23),('rear',(2.5,43,9),(2.5,0,6.7),27),('quarter',(34,-42,25),(3,0,6.2),29),('entry-close',(18,-8,8),(6.2,0,6.5),11),('roof-close',(13,-13,7.7),(4,-3,5.7),10)]
    if ident=='fairytale_castle_gateway':shots=[('front',(0,-47,9),(0,0,6.9),29),('side',(47,0,9),(0,0,6.9),24),('rear',(0,47,9),(0,0,6.9),29),('quarter',(29,-45,24),(0,0,6.5),34),('entry-close',(6,-18,6.9),(0,0,5.3),15),('roof-close',(17,-15,23),(6,0,10.6),15)]
    if ident=='perimeter_service_gateway':shots=[('front',(0,-25,5.3),(0,0,2.45),12),('side',(25,0,5.3),(0,0,2.45),8),('rear',(0,25,5.3),(0,0,2.45),12),('quarter',(16,-21,14),(0,0,2.3),14),('entry-close',(7,-10,3.9),(3.9,0,3.9),6.4),('roof-close',(8,-7,11),(2.7,0,4.4),8.5)]
    if ident=='mirrors_arcade_panels':shots=[('front',(2,-18,4.1),(0,0,1.8),10),('side',(19,-2,4.1),(0,0,1.8),7),('rear',(-2,18,4.1),(0,0,1.8),10),('quarter',(10,-15,11),(0,0,1.6),12),('entry-close',(5,-5,3.1),(3.45,-.9,1.32),5.3),('roof-close',(7,-6,8),(3.45,0,2.8),5.9)]
    if ident.endswith('_kiosk'):shots=[('front',(0,-21,4),(0,0,1.9),7.2),('side',(21,0,4),(0,0,1.9),7.2),('rear',(0,21,4),(0,0,1.9),7.2),('quarter',(12,-17,11),(0,0,1.85),8.8),('entry-close',(3,-9,3.0),(0,-1.1,1.5),5.7),('roof-close',(8,-8,11),(0,0,2.9),7.1)]
    if walk:
        long=max(max(p[i]for p in walk)-min(p[i]for p in walk)for i in range(2))
        shots=[(name,tuple(Vector(at)+focus),tuple(Vector(aim)+focus),long+14)for name,at,aim in [('front',(0,-48,10),(0,0,2)),('side',(48,0,10),(0,0,2)),('rear',(0,48,10),(0,0,2)),('quarter',(32,-42,25),(0,0,2))]]
        a,b=Vector(walk[0]),Vector(walk[1]);end=(a-b).normalized()
        eye=a+end*10;aim=a-end*1.5
        shots += [('entry-close',(eye.x,eye.y,4.0),(aim.x,aim.y,2.3),11),('roof-close',(focus.x+8,focus.y-8,13),(focus.x,focus.y,3.7),13)]
    rows=[]
    only=next((set(a.split('=',1)[1].split(','))for a in sys.argv if a.startswith('--shots=')),None)
    for name,at,target,size in shots:
        if only and name not in only:continue
        cam.location=at;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=size;scene.render.filepath=str(D/(name+'.png'));bpy.ops.render.render(write_still=True);rows.append({'view':name,'image':str(D/(name+'.png'))});print('ARCHITECTURE_RENDERED',ident,name,flush=True)
    proof={'id':ident,'actualRenders':rows,'sourceSHA256':hashlib.sha256((D/'source.blend').read_bytes()).hexdigest(),'visualReviewPending':True}
    if context_source:proof['contextSource']=context_source
    (D/'renders.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')

if '--render'in sys.argv:render()
else:author()
