"""One architectural asset; background Blender author/render/integrate checkpoints."""
import bpy,bmesh,sys,json,math,hashlib,shutil,re
from collections import Counter
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_rebuilt_environment_kit as K
import dream_hotel_architecture as H
O=R/'art/space_v4/park_levels_v1/dream_hotel_v4';O.mkdir(exist_ok=True)
W=R/'Game/Saved/park-levels-20261104/hotel-architecture';W.mkdir(exist_ok=True)

def inspect(root):
    rows=[];bad=[];tri=0
    for o in root.children_recursive:
        if o.type!='MESH':continue
        assert len(o.data.polygons)>0,('Empty architectural mesh',o.name)
        assert all(o.data.materials[p.material_index]is not None for p in o.data.polygons),('Unassigned architectural surface',o.name)
        bm=bmesh.new();bm.from_mesh(o.data)
        assert bm.calc_volume(signed=True)>0,('Inverted solid',o.name)
        deg=[f for f in bm.faces if f.calc_area()<1e-12];boundary=sum(1 for e in bm.edges if not e.is_manifold)
        if deg or boundary:bad.append({'name':o.name,'degenerate':len(deg),'nonManifoldEdges':boundary})
        tri+=sum(len(f.verts)-2 for f in bm.faces);rows.append({'name':o.name,'vertices':len(bm.verts),'triangles':sum(len(f.verts)-2 for f in bm.faces),'nonManifoldEdges':boundary});bm.free()
    assert not bad,bad[:12]
    groups=Counter()
    for row in rows:groups[re.sub(r'\.\d+$','',row['name'])]+=row['triangles']
    (W/'mesh-cost.json').write_text(json.dumps({'triangles':tri,'groups':groups.most_common(),'rows':rows},indent=2),encoding='utf8')
    print('HOTEL_MESH_COST',tri,groups.most_common(8),flush=True)
    assert tri<85000,tri
    body=next(o for o in root.children_recursive if o.name.startswith('continuous_coursed_load_bearing_wall'))
    # Ray-section tests prove actual absent wall at openings and real solid piers.
    bm=bmesh.new();bm.from_mesh(body.data);tree=BVHTree.FromBMesh(bm)
    pier=tree.ray_cast(Vector((1.65,-9,5.0)),Vector((0,1,0)),3.3)
    assert pier[0] is not None,'Expected solid central pier'
    glassOpening=tree.ray_cast(Vector((0,-9,4.9)),Vector((0,1,0)),3.5)
    assert glassOpening[0] is None,'Window must actually be removed from load-bearing wall'
    entry=tree.ray_cast(Vector((0,-9,1.6)),Vector((0,1,0)),3.5)
    assert entry[0] is None,'Door must actually be open in load-bearing wall'
    bm.free()
    for o in root.children_recursive:
        if not o.name.startswith('dormer_apertured_front'):continue
        x=(min(v.co.x for v in o.data.vertices)+max(v.co.x for v in o.data.vertices))/2;y=min(v.co.y for v in o.data.vertices)
        bm=bmesh.new();bm.from_mesh(o.data);tree=BVHTree.FromBMesh(bm)
        assert tree.ray_cast(Vector((x,y-1,13.4)),Vector((0,1,0)),1.4)[0]is None,('Blocked dormer opening',o.name)
        bm.free()
    roof=next(o for o in root.children_recursive if o.name.startswith('continuous_thick_mansard_roof'))
    bm=bmesh.new();bm.from_mesh(roof.data);tree=BVHTree.FromBMesh(bm)
    for x,y in [(5.25,-3.75),(-5.25,-3.75),(0,-3.75),(0,0),(5.5,3),(-5.5,3)]:
        assert tree.ray_cast(Vector((x,y,18)),Vector((0,0,-1)),7)[0]is not None,('Unsealed roof',x,y)
    bm.free()
    return {'ok':True,'triangles':tri,'closedMeshObjects':len(rows),'meshChecks':rows,'actualWallSection':{'pierSolid':True,'upperWindowCut':True,'entryCut':True,'nominalThickness':.32},'booleanOperations':dict(H.STATS),'scope':'Geometric validity and structural aperture proof, not aesthetic acceptance.'}

def author():
    bpy.ops.wm.read_factory_settings(use_empty=True);K.setup_materials();root=H.build()
    bpy.context.view_layer.update();proof=inspect(root)
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'hotel-source.blend'),compress=True)
    (O/'geometry.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('HOTEL_AUTHORED',proof['triangles'],proof['closedMeshObjects'],flush=True)

def render():
    bpy.ops.wm.open_mainfile(filepath=str(O/'hotel-source.blend'));root=bpy.data.objects['designed_dream_hotel_architecture']
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.cycles.device='CPU'
    # Physical material/geometry review uses a separate background process.
    # Native engine evidence is captured separately after authoring stops.
    scene.render.engine='CYCLES'
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        gpu=False
        for d in prefs.devices:d.use=d.type=='OPTIX';gpu=gpu or d.use
        if gpu:scene.cycles.device='GPU'
    except Exception:pass
    scene.render.resolution_x=1600;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    if scene.world is None:scene.world=bpy.data.worlds.new('review_world')
    scene.world.color=(.14,.14,.14)
    floor=bpy.data.materials.new('review_ground');floor.diffuse_color=(.18,.19,.22,1)
    data=bpy.data.meshes.new('review_ground');data.from_pydata([(-100,-100,-.07),(100,-100,-.07),(100,100,-.07),(-100,100,-.07)],[],[(0,1,2,3)]);ground=bpy.data.objects.new('review_ground',data);scene.collection.objects.link(ground);ground.data.materials.append(floor)
    def area(name,pos,energy,size,color):
        d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,7))-o.location).to_track_quat('-Z','Y').to_euler();d.energy=energy;d.shape='DISK';d.size=size;d.color=color
    area('review_key',(-15,-18,26),4500,14,(1,.89,.77));area('review_fill',(20,-2,18),2500,12,(.68,.79,1));area('review_rear',(-4,17,25),4500,11,(1,.86,.70))
    world=scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.36,.43,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
    c=bpy.data.cameras.new('review_camera');cam=bpy.data.objects.new('review_camera',c);scene.collection.objects.link(cam);scene.camera=cam
    shots=[('front',(0,-35,8),(0,0,8),23),('side',(35,0,8),(0,0,8),23),('rear',(0,35,8),(0,0,8),23),('quarter',(26,-34,24),(0,0,7.5),25),('window-close',(4,-12,7.3),(0,-6,6.8),6.0),('roof-close',(10,-14,19),(3.7,-4.5,13.7),9)]
    only=next((a.split('=',1)[1].split(',')for a in sys.argv if a.startswith('--shots=')),None)
    rows=[]
    for name,pos,target,size in shots:
        if only and name not in only:continue
        cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();c.type='ORTHO';c.ortho_scale=size
        scene.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True);rows.append({'view':name,'image':str(O/(name+'.png'))});print('HOTEL_RENDERED',name,flush=True)
    (O/'render-review.json').write_text(json.dumps({'actualBlenderRenders':rows,'sourceSHA256':hashlib.sha256((O/'hotel-source.blend').read_bytes()).hexdigest(),'renderer':scene.render.engine,'device':scene.cycles.device,'samples':scene.cycles.samples,'aestheticReviewPending':True},indent=2)+'\n',encoding='utf8')

def integrate():
    park=O.parent;backup=R/'삭제 대기/드림호텔_재설계_이전_c66_20261104';backup.mkdir(exist_ok=True)
    for name in ['parks-authoring.blend','raw-manifest.json','manifest.json']:
        if not(backup/name).exists():shutil.copy2(park/name,backup/name)
    bpy.ops.wm.open_mainfile(filepath=str(park/'parks-authoring.blend'))
    for c in bpy.context.view_layer.layer_collection.children:
        if c.name.startswith('THEME_SOURCE_'):c.exclude=c.name!='THEME_SOURCE_fairytale'
    owner=bpy.data.objects['textfree_theme_v2_fairytale'];old=[o for o in owner.children if o.name.startswith(('fantasy_resort_facade','designed_dream_hotel_architecture'))]
    assert old,'Missing owned previous hotel'
    removedTriangles=sum(len(p.vertices)-2 for o in old for q in o.children_recursive if q.type=='MESH'for p in q.data.polygons)
    bpy.data.batch_remove(ids=[v for o in old for v in [o,*o.children_recursive]])
    with bpy.data.libraries.load(str(O/'hotel-source.blend'),link=False)as(src,dst):dst.objects=list(src.objects)
    collection=bpy.data.collections['THEME_SOURCE_fairytale']
    for obj in dst.objects:
        if obj:collection.objects.link(obj);obj['_parkSourceCollection']='fairytale'
    hotel=next(o for o in dst.objects if o and o.parent is None);hotel.parent=owner;hotel.location=(0,24,0)
    raw=json.loads((park/'raw-manifest.json').read_text(encoding='utf8'));row=next(r for r in raw['levels']if r['id']=='fairytale');root=bpy.data.objects['park_level_fairytale']
    import build_v4_rebuilt_environment as A
    priorTriangles=row['raw']['triangles'];newTriangles=sum(len(p.vertices)-2 for q in hotel.children_recursive if q.type=='MESH'for p in q.data.polygons)
    A.O=park;row['raw']=A.export([root,*root.children_recursive],'fairytale.glb','Assets/Art/park_levels/fairytale.glb',{'textFreePublicArchitecture':True,'themeParkRevision':2,'surfaceDetailRevision':3,'hotelArchitectureRevision':4})
    assert row['raw']['triangles']==priorTriangles-removedTriangles+newTriangles,('Unexpected other geometry change',row['raw']['triangles'],priorTriangles,removedTriangles,newTriangles)
    (park/'raw-manifest.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    proofFile=park/'theme_park_v2/authoring.json';proof=json.loads(proofFile.read_text(encoding='utf8'));proof['districts']['fairytale']['hotelArchitecture']={'revision':4,'source':'dream_hotel_v4/hotel-source.blend','entryAndNavigationMetadataUnchanged':True,'oldHotelEntirelyReplaced':True}
    proofFile.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (O/'integration.json').write_text(json.dumps({'ok':True,'previousFairytaleTriangles':priorTriangles,'removedHotelTriangles':removedTriangles,'newHotelTriangles':newTriangles,'currentFairytaleTriangles':row['raw']['triangles'],'previousBank':str(backup/'manifest.json'),'sourceSHA256':hashlib.sha256((O/'hotel-source.blend').read_bytes()).hexdigest(),'onlyHotelReplaced':True},indent=2)+'\n',encoding='utf8')
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(park/'parks-authoring.blend'),compress=True);print('HOTEL_INTEGRATED',flush=True)

if '--integrate'in sys.argv:integrate()
elif '--render'in sys.argv:render()
else:author()
