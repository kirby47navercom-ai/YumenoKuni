"""Reauthor the five public parks in the owned background Blender process.

Keeps room IDs, case-local geometry, evidence transforms and save poses intact.
Each district is saved/exported as a checkpoint; --only reuses that checkpoint.
"""
import bpy,bmesh,math,json,sys,shutil,subprocess,hashlib,random
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_rebuilt_environment_kit as K
import build_v4_rebuilt_environment as A
import theme_park_v2_kit as T
import theme_park_surface_finish as D
O=R/'art/space_v4/park_levels_v1';V=O/'theme_park_v2';V.mkdir(exist_ok=True)
only=next((set(s.split('=',1)[1].split(','))for s in sys.argv if s.startswith('--only=')),None)
# Preserve one recoverable source checkpoint in the location requested by user.
backup=R/'삭제 대기/테마공원_구외관_v1_20261104'
backup.mkdir(exist_ok=True)
for name in ['parks-authoring.blend','raw-manifest.json','manifest.json']:
    if not(backup/name).exists():shutil.copy2(O/name,backup/name)
detailBackup=R/'삭제 대기/테마공원_디테일_이전_d2_20261104'
detailBackup.mkdir(exist_ok=True)
for name in ['parks-authoring.blend','raw-manifest.json','manifest.json']:
    if not(detailBackup/name).exists():shutil.copy2(O/name,detailBackup/name)
baseline=json.loads((backup/'raw-manifest.json').read_text(encoding='utf8'))
baseRows={r['id']:r for r in baseline['levels']}
manifest=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'))
bpy.ops.wm.open_mainfile(filepath=str(O/'parks-authoring.blend'))
# Keep the complete recoverable source, but do not evaluate every other park
# and the old facility authoring library during each curved-wall operation.
# Object parents and source mesh data remain intact; only collections change.
def organize_sources():
    groups={};owned=set()
    for ident in baseRows:
        obj=bpy.data.objects.get('park_level_'+ident)
        if obj:groups[ident]=[obj,*obj.children_recursive];owned.update(groups[ident])
    if not bpy.data.collections.get('THEME_SOURCE_source_reference'):groups['source_reference']=[o for o in list(bpy.data.objects)if o not in owned]
    for ident,objects in groups.items():
        name='THEME_SOURCE_'+ident;collection=bpy.data.collections.get(name)
        if not collection:collection=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(collection)
        for o in objects:
            if o.get('_parkSourceCollection')==ident:continue
            if collection not in o.users_collection:
                for old in list(o.users_collection):old.objects.unlink(o)
                collection.objects.link(o)
            o['_parkSourceCollection']=ident
    return groups
def focus(ident):
    for c in bpy.context.view_layer.layer_collection.children:
        if c.name.startswith('THEME_SOURCE_'):c.exclude=c.name!='THEME_SOURCE_'+ident
organize_sources();T.palette();D.setup();print('PARK_SOURCE_COLLECTIONS_READY',len(bpy.data.objects),flush=True)
# Old objects retain their authored palette when an unchanged surface is retained.
for key in ['cream','red','blue','enamel','brick','ink','teal']:
    m=next((m for m in bpy.data.materials if m.name=='park_'+key),None)
    if m:K.M[key]=m
proofFile=V/'authoring.json';proof=json.loads(proofFile.read_text(encoding='utf8'))if proofFile.exists()else{'districts':{},'runtimeVerified':False}
sitePlan=json.loads((V/'site-plan.json').read_text(encoding='utf8'))
localWorld=json.loads((R/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf8'))

def erase(objects):
    live={o for o in objects if o and o.name in bpy.data.objects}
    if live:bpy.data.batch_remove(ids=list(live))
def tree_erase(o):erase([o,*o.children_recursive])
def matching(root,prefixes):
    selected=[o for o in root.children_recursive if o.name.startswith(tuple(prefixes))]
    erase([v for o in selected for v in [o,*o.children_recursive]])
def strip_names(root):
    selected=[o for o in root.children_recursive if o.type=='FONT' or 'facilityLabel' in o or o.name.startswith(('physical_wayfinding','backed_architectural_sign','sign_continuous_border','attached_sign_hanger'))]
    count=len(selected);erase([v for o in selected for v in [o,*o.children_recursive]])
    faces=0
    for o in list(root.children_recursive):
        if o.type!='MESH':continue
        ids={i for i,m in enumerate(o.data.materials)if m and 'identity_facility_sign' in m.name}
        if not ids:continue
        label=[p for p in o.data.polygons if p.material_index in ids]
        if not label:continue
        coords=[o.data.vertices[i].co for p in label for i in p.vertices]
        lo=[min(v[k]for v in coords)-.08 for k in range(3)];hi=[max(v[k]for v in coords)+.08 for k in range(3)]
        delete={p.index for p in label}
        for p in o.data.polygons:
            m=o.data.materials[p.material_index]
            if m and 'iron' in m.name and all(all(lo[k]<=o.data.vertices[i].co[k]<=hi[k]for k in range(3))for i in p.vertices):delete.add(p.index)
        bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i]for i in delete],context='FACES_ONLY');bm.to_mesh(o.data);bm.free();o.data.update();faces+=len(delete)
    return {'removedLabelObjects':count,'removedBakedNameFaces':faces}

def remove_redundant_local_ground(root):
    # Case props/platforms remain. Remove only the legacy ground-level paving
    # and turf faces under the new single partitioned guest surface, preventing
    # the two nearly coplanar surfaces that produced striped/z-fighting views.
    removed=0;bpy.context.view_layer.update()
    for group in [o for o in root.children if o.name.startswith('preserved_outdoor_')]:
        for o in group.children_recursive:
            if o.type!='MESH'or o.get('partitionedGroundOwner')==3:continue
            ids={i for i,m in enumerate(o.data.materials)if m and any(k in m.name for k in ['paving','grass'])}
            delete=[]
            for p in o.data.polygons:
                points=[o.matrix_world@o.data.vertices[i].co for i in p.vertices];z=[v.z for v in points]
                base=p.material_index in ids and max(z)-min(z)<.0002 and min(z)>-.15 and max(z)<.065
                mat=o.data.materials[p.material_index];strip=group.name=='preserved_outdoor_plaza'and mat and 'ivory_generated_limestone'in mat.name and all(abs(v.x)<2.5 and 4.2<abs(v.y)<18 and -.2<v.z<.18 for v in points)
                oldGate=group.name=='preserved_outdoor_plaza'and all(abs(v.x)<14.2 and -14.2<v.y<-13.0 and -.2<v.z<5.4 for v in points)
                if base or strip or oldGate:delete.append(p.index)
            if delete:
                bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i]for i in delete],context='FACES_ONLY');bm.to_mesh(o.data);bm.free();o.data.update();removed+=len(delete)
            o['partitionedGroundOwner']=3
    return removed

def box(row,x0,y0,x1,y1,h=2):
    row['collision'].append([min(x0,x1),-max(y0,y1),max(x0,x1),-min(y0,y1),0,h])
def walls(row,pts,height=1.1,r=.065):
    for a,b in zip(pts,pts[1:]):box(row,min(a[0],b[0])-r,min(a[1],b[1])-r,max(a[0],b[0])+r,max(a[1],b[1])+r,height)
def rect(row,at,rx,ry,h):box(row,at[0]-rx,at[1]-ry,at[0]+rx,at[1]+ry,h)
def circular_walk(row,at,radius,height):
    for i in range(48):
        y0=-radius+2*radius*i/48;y1=-radius+2*radius*(i+1)/48;half=math.sqrt(max(0,radius*radius-max(abs(y0),abs(y1))**2))
        if half>.01:row['walkSurfaces'].append([at[0]-half,-at[1]-y1,at[0]+half,-at[1]-y0,height])
def asset_collision(row,obj,at,radius=None,solid=False):
    if solid:
        row.setdefault('landscapeKeepClear',[]).append([at[0]-radius-.5,-at[1]-radius-.5,at[0]+radius+.5,-at[1]+radius+.5])
        # Background ride has a closed boarding gate; no invisible playable ride.
        n=24;pts=[(at[0]+radius*math.cos(i*math.tau/n),at[1]+radius*math.sin(i*math.tau/n))for i in range(n+1)]
        walls(row,pts,1.1)
    # Physical queue rail / column / planter collisions, expressed by their
    # finite world extents, never a box around the whole public forecourt.
    bpy.context.view_layer.update()
    prefixes=('continuous_safety_top_rail','continuous_safety_low_rail','fixed_safety_upright','load_bearing_station_column','arcade_turned_column','theatre_grounded_canopy_column','tied_back_canvas_entry_drape','bank_metal_support','curved_show_audience_bank','planter_fitted_stone_bowl')
    for o in obj.children_recursive:
        if o.type!='MESH'or not o.name.startswith(prefixes):continue
        bb=[o.matrix_world@Vector(c)for c in o.bound_box]
        # A ring/curved bank needs short segments; using its bounding box would
        # close the entire inside. The closed ride ring was handled above.
        if o.name.startswith(('continuous_safety_','curved_show_audience_bank')):continue
        lo=[min(v[k]for v in bb)for k in range(3)];hi=[max(v[k]for v in bb)for k in range(3)]
        if hi[2]>.34 and lo[2]<1.6:row['collision'].append([lo[0],-hi[1],hi[0],-lo[1],lo[2],hi[2]])
def forecourt(p,at,radius,mat='paving'):
    q=T.root('connected_attraction_forecourt',p,(*at,0));n=64
    K.mesh('fitted_forecourt_paving',[(0,0,.031)]+[(radius*math.cos(i*math.tau/n),radius*math.sin(i*math.tau/n),.031)for i in range(n)],[(0,i+1,(i+1)%n+1)for i in range(n)],mat,q,uv_scale=.30)
    T.ring('forecourt_flush_inset',q,radius-.1,.035,'stone',.025);return q

def architectural_export_flags(root,flags):
    # Every caller has just applied D.finish; do not lose its proof on resume.
    flags['surfaceDetailRevision']=3
    flags['surfaceMaterialRevision']=5
    if any(o.name.startswith('designed_dream_hotel_architecture')and o.get('architectureRevision')==4 for o in root.children_recursive):
        flags['hotelArchitectureRevision']=4
    if any(o.get('architectureRevision')==6 for o in root.children_recursive):
        flags['facilityArchitectureRevision']=6
    return flags

def promenade(row,root,owner,extra):
    matching(root,['composed_site_landscape_','composed_guest_ground_','fitted_forecourt_paving'])
    matching(root,['themed_park_entrance'])
    if owner.get('architectureRevision',0)<3:
        matching(owner,['continuous_covered_visitor_walk','purpose_park_return_threshold'])
        if row['id']=='fairytale':
            matching(owner,['fantasy_resort_facade','designed_dream_hotel_architecture']);T.hotel(owner,(0,24))
        else:T.return_threshold(owner,sitePlan[row['id']]['returnThreshold'],row['id'])
        for spec in sitePlan[row['id']].get('coveredWalks',[]):T.covered_walk(owner,spec['points'],spec.get('width',4.4),spec['material'])
        owner['architectureRevision']=3
    if row['id']=='mirrors':
        matching(root,['illusion_arcade_fitted_roof','continuous_arcade_roof_spine','glass_arcade_continuous_arch','glass_arcade_pier'])
        front=next(o for o in owner.children if o.name.startswith('actual_mask_funhouse_front'))
        if front.get('recessedEntryRevision',0)<1:T.funhouse_entry(front)
        rect(row,(-6,-19.05),1.42,.11,3.85)
    for obj in owner.children:
        if obj.name.startswith('continuous_covered_visitor_walk'):asset_collision(row,obj,(0,0))
        if obj.name.startswith('purpose_park_return_threshold'):
            for side in [-1,1]:rect(row,(obj.location.x+side*6.15,obj.location.y),.35,.3,4)
    for obj in root.children_recursive:
        if obj.type=='MESH':
            for i,mat in enumerate(obj.data.materials):
                key=mat.name.split('.')[0].removeprefix('theme_v2_')if mat else''
                if mat and mat.name.startswith('theme_v2_')and key in K.M:obj.data.materials[i]=K.M[key]
    remove_redundant_local_ground(root)
    if row['id']=='fairytale':row['collision']=[c for c in row['collision']if not(-14.2<c[0]<14.2 and -14.2<c[2]<14.2 and 13.0<c[1]<14.2 and 13.0<c[3]<14.2)]
    row.setdefault('landscapeKeepClear',[])
    for obj in owner.children:
        radius=next((rr for name,rr in [('complete_royal_carousel',8.1),('complete_teacup_attraction',8.1),('complete_suspended_chair_ride',8.2),('complete_orbital_vehicle_attraction',9.7),('complete_big_top',13.0)]if obj.name.startswith(name)),None)
        if radius:
            x,y=obj.location.x,obj.location.y;footprint=[x-radius-.5,-y-radius-.5,x+radius+.5,-y+radius+.5]
            if footprint not in row['landscapeKeepClear']:row['landscapeKeepClear'].append(footprint)
            if not obj.name.startswith('complete_big_top'):
                # An inactive ride's closed safety fence excludes its interior
                # too; existing saves inside a newly placed ride use the game's
                # existing invalid-pose recovery rather than becoming trapped.
                rr=radius-.12
                for k in range(48):
                    y0=-rr+2*rr*k/48;y1=-rr+2*rr*(k+1)/48;half=math.sqrt(max(0,rr*rr-max(abs(y0),abs(y1))**2))
                    if half>.01:box(row,x-half,y+y0,x+half,y+y1,1.12)
    route=O/('paths-'+row['id']+'.json');data=json.loads(route.read_text(encoding='utf8'))
    baseKey='baseDestinations'
    if baseKey not in data:data[baseKey]=data['destinations']
    data['destinations']=data[baseKey]+[p for p in extra if p not in data[baseKey]]
    data['obstacles']=[c for c in row['collision']if c[4]<1.6 and c[5]>.34]
    data['sitePlan']=sitePlan[row['id']]
    data['groundHoles']=[[7.99,-11.01,20.01,-4.99]]if row['id']=='carnival'else[]
    # Keep planting completely out of original outdoor case movement volumes.
    data['keepClearRects']=list(row.get('landscapeKeepClear',[]));data['caseCourtyardRects']=[]
    # Stair/deck support surfaces are public circulation too. Reserving only
    # building envelopes allowed a new planting edge to cover the stair toe,
    # making an existing valid saved pose invalid and forcing spawn recovery.
    data['keepClearRects'].extend(c[:4]for c in row['walkSurfaces']if len(c)>4 and c[4]>.05)
    if row['id']=='mirrors':
        data['keepClearRects'].append([19.8,-6.2,33.0,-.8])
        if [30.5,-3.5]not in data['destinations']:data['destinations'].append([30.5,-3.5])
    for ident,at in row['placedFacilities'].items():
        rec=localWorld['instances'].get(ident)
        if not rec:continue
        spec=localWorld['spaces'].get(rec['space'])
        if not spec or not spec.get('outdoor'):continue
        b=spec['bounds'];court=[at[0]+b[0],-at[1]+b[1],at[0]+b[2],-at[1]+b[3]];data['keepClearRects'].append(court);data['caseCourtyardRects'].append(court)
    route.write_text(json.dumps(data,ensure_ascii=False),encoding='utf8')
    subprocess.run(['C:/python/python.exe','-X','utf8',str(R/'tools/plan_v4_theme_park_site.py'),str(route)],check=True)
    matching(root,['one_connected_public_promenade','continuous_fitted_promenade_edging'])
    paving=json.loads(route.with_suffix('.mesh.json').read_text(encoding='utf8'))
    assert paving['connected'],row['id']
    vertices=[(x,-z,.026)for t in paving['triangles']for x,z in t]
    K.mesh('one_connected_public_promenade',vertices,[(i,i+1,i+2)for i in range(0,len(vertices),3)],'main_paving',owner,uv_scale=.3)
    ground=T.root('composed_guest_ground_'+row['id'],owner)
    for name,key,mat,z in [('continuous_guest_courtyard_floor','guestTriangles','guest_paving',.026),('inset_actual_planted_ground','plantingTriangles','planting_soil',.10)]:
        v=[(x,-zz,z)for t in paving[key]for x,zz in t]
        if v:K.mesh(name,v,[(i,i+1,i+2)for i in range(0,len(v),3)],mat,ground,uv_scale=.28)
    from v4_park_continuity import ribbon
    for spec in sitePlan[row['id']].get('continuingRoutes',[]):ribbon(ground,'continuing_occluded_park_route',spec['points'],spec['width'],'main_paving',.04)
    for polygon in paving['polygons']:
        for line in [polygon['outer'],*polygon['holes']]:K.tube('continuous_fitted_promenade_edging',[(x,-z,.065)for x,z in line],[.055]*len(line),'stone',owner,6)
    # Shape the actual level's empty plots, instead of scattering more props
    # across the same undifferentiated flat grass plane.
    landscape=T.root('composed_site_landscape_'+row['id'],owner)
    prototypes=[]
    candidates=sorted(paving['landscapeIslands'],key=lambda v:v['area'],reverse=True)
    for i,island in enumerate(candidates):
        line=island['outer'];xyz=[(x,-z,.60)for x,z in line]
        if island['area']<650:
            # Low clipped planting islands frame courts but preserve long views.
            T.hedge(landscape,[(x,-z)for x,z in line])
            walls(row,[(x,-z)for x,z in line],.96,.36)
        else:
            # Larger plots are layered planting, with deliberately open breaks.
            for k in range(0,len(xyz)-1,12):
                pts=xyz[k:min(k+9,len(xyz))]
                if len(pts)>1:T.hedge(landscape,[(x,y)for x,y,_ in pts],1.0);walls(row,[(x,y)for x,y,_ in pts],1.06,.36)
        if i<18 and island['area']>65:
            x,z=island['center']
            if not prototypes:
                a=K.tree(18461);a.parent=landscape;a.location=(x,-z,0)
                for branch in a.children_recursive:
                    if branch.type=='MESH'and 'connected_trunk'in branch.name:modifier=branch.modifiers.new('bounded_foreground_branch_detail','DECIMATE');modifier.ratio=.18
                prototypes=[a,*a.children_recursive]
            else:
                # Reuse the authored branch/leaf meshes, keeping storage and
                # runtime geometry bounded. Different tree poses break repeats.
                mapping={}
                for old in prototypes:
                    new=old.copy();bpy.context.scene.collection.objects.link(new);mapping[old]=new
                for old,new in mapping.items():new.parent=mapping.get(old.parent,landscape)
                a=mapping[prototypes[0]];a.location=(x,-z,0);a.rotation_euler.z=i*2.39996;a.scale=(1+.08*(i%3),)*3
            rect(row,(x,-z),.28,.28,5.4)
    oldFinish=bpy.data.objects.get('public_space_finish_'+row['id'])
    if oldFinish:matching(oldFinish,['landscape_tree'])
    parts=T.low_tree_parts();protected=list(data['keepClearRects'])
    for i,(x,z) in enumerate(paving.get('foregroundTrees',[])):
        at=(x,-z);tree=T.root('visitor_street_foreground_tree',landscape,(*at,0),i*2.39996)
        s=1.0+.08*(i%4);tree.scale=(s,s,s)
        for mesh in parts:
            obj=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(obj);obj.parent=tree
        if i<14:
            T.tree_seating_bed(landscape,at);rect(row,at,2.10,2.10,.53)
        else:rect(row,at,.3,.3,5.4*s)
    for ident,at in row['placedFacilities'].items():
        rec=localWorld['instances'].get(ident)
        if rec:
            b=localWorld['spaces'][rec['space']]['bounds'];protected.append([at[0]+b[0]-3,-at[1]+b[1]-3,at[0]+b[2]+3,-at[1]+b[3]+3])
    rng=random.Random(40511+sum(map(ord,row['id'])));trees=0
    gates=[(59,1),(64,-42),(-64,-24),(24,64),(70,-26)]if row['id']=='fairytale'else[]
    for belt,radius in enumerate([83,103]):
        for k in range(72):
            a=(k+.5*belt)*math.tau/72;x=(radius+rng.uniform(-3,3))*math.cos(a);z=(radius+rng.uniform(-3,3))*math.sin(a)
            if any(b[0]-2<x<b[2]+2 and b[1]-2<z<b[3]+2 for b in protected)or any(math.hypot(x-gx,z-gz)<12 for gx,gz in gates):continue
            def distance_to_segment(point,a,b):
                a,b=Vector(a),Vector(b);delta=b-a;t=max(0,min(1,(Vector(point)-a).dot(delta)/max(1e-9,delta.length_squared)));return (Vector(point)-(a+delta*t)).length
            if any(distance_to_segment((x,-z),a,b)<spec['width']/2+4 for spec in sitePlan[row['id']].get('continuingRoutes',[])for a,b in zip(spec['points'],spec['points'][1:])):continue
            tree=T.root('layered_park_backdrop_tree',landscape,(x,-z,0),rng.uniform(0,math.tau));s=rng.uniform(1.05,1.65);tree.scale=(s,s,s)
            for mesh in parts:o=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(o);o.parent=tree
            # Grounded low planting obscures the empty band below tree crowns.
            brush=[(x-3.1*math.sin(a),-z-3.1*math.cos(a)),(x+3.1*math.sin(a),-z+3.1*math.cos(a))];T.hedge(landscape,brush,1.3)
            b=row['bounds']
            if b[0]<x<b[2]and b[1]<z<b[3]:rect(row,(x,-z),.30*s,.30*s,5.4*s);walls(row,brush,1.3,.35)
            trees+=1
    return {'connected':paving['connected'],'destinations':len(data['destinations']),'primaryVisitorCircuits':len(data['sitePlan']['primaryRoutes']),'pavedArea':paving['pavedArea'],'plantedIslands':len(candidates),'treeGroups':min(18,len(candidates)),'foregroundStreetTrees':len(paving.get('foregroundTrees',[])),'seatingBeds':min(14,len(paving.get('foregroundTrees',[]))),'layeredBackdropTrees':trees,'guestGround':'matte visitor streets with planted court edges and seating groves','coveredWalks':len(sitePlan[row['id']].get('coveredWalks',[]))}

for row in manifest['levels']:
    ident=row['id']
    if only and ident not in only:continue
    focus(ident);print('SITE_REAUTHOR_BEGIN',ident,flush=True)
    root=bpy.data.objects['park_level_'+ident]
    if '--detail-only' in sys.argv:
        if ident=='perimeter':continue
        owner=bpy.data.objects['textfree_theme_v2_'+ident];details=D.finish(row,root,owner);__import__('park_architecture_v6').restore_reviewed(root,ident);__import__('park_material_finish').apply(root,ident);A.O=O
        row['raw']=A.export([root,*root.children_recursive],ident+'.glb','Assets/Art/park_levels/'+ident+'.glb',architectural_export_flags(root,{'textFreePublicArchitecture':True,'themeParkRevision':2,'surfaceDetailRevision':3}))
        proof['districts'][ident]['surfaceDetail']=details
        (O/'raw-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');proofFile.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        organize_sources();focus(ident);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True);print('SURFACE_DETAIL_CHECKPOINT',ident,flush=True);continue
    if '--site-only' in sys.argv:
        state=json.loads((V/('geometry-'+ident+'.json')).read_text(encoding='utf8'));row.clear();row.update(state['row']);owner=bpy.data.objects['textfree_theme_v2_'+ident]
        paths=promenade(row,root,owner,state['extra']);details=D.finish(row,root,owner);__import__('park_architecture_v6').restore_reviewed(root,ident);__import__('park_material_finish').apply(root,ident);A.O=O
        row['raw']=A.export([root,*root.children_recursive],ident+'.glb','Assets/Art/park_levels/'+ident+'.glb',architectural_export_flags(root,{'textFreePublicArchitecture':True,'themeParkRevision':2}))
        proof['districts'][ident]={'labels':state['removed'],'authoredFeatures':state['features'],'paths':paths,'collisionCount':len(row['collision']),'caseRoomTransformsUnchanged':True}
        proof['districts'][ident]['surfaceDetail']=details
        (O/'raw-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');proofFile.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        organize_sources();focus(ident);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True);print('THEME_PARK_V2_CHECKPOINT',ident,flush=True);continue
    old=bpy.data.objects.get('textfree_theme_v2_'+ident)
    if old:tree_erase(old)
    removed=strip_names(root)
    if ident=='perimeter':
        A.O=O;row['raw']=A.export([root,*root.children_recursive],ident+'.glb','Assets/Art/park_levels/'+ident+'.glb',{'textFreePublicArchitecture':True})
        proof['districts'][ident]={'labels':removed,'existingCurvedAccessRetained':True}
    else:
        owner=T.root('textfree_theme_v2_'+ident,root);row['collision']=json.loads(json.dumps(baseRows[ident]['collision']));row['landscapeKeepClear']=[]
        # The old thin tree ring exposed the same empty test-ground horizon in
        # every district. The new site plan owns foreground/middle planting;
        # retain the farther continuous landscape belt beyond it.
        for tree in list(root.children):
            if tree.name.startswith('landscape_tree'):tree_erase(tree)
        features=[];extra=[]
        if ident=='fairytale':
            matching(root,['carousel_load_bearing_center','carousel_round_boarding_plinth','carved_carousel_pony','continuous_radial_canopy_panel','scalloped_canopy_edge','canopy_finial'])
            matching(root,['parkcopy_facade_hotel_lobby'])
            row['collision']=[c for c in row['collision']if c[:4]!=[-40,17,-26,31]]
            a=T.carousel(owner,(-33,-24));asset_collision(row,a,(-33,-24),8.1,True);features.append(a.name)
            print('SITE_FEATURE_READY',ident,'carousel',flush=True)
            a=T.teacups(owner,(32,-27));asset_collision(row,a,(32,-27),8.1,True);features.append(a.name)
            a=T.hotel(owner,(0,24));features.append(a.name)
            print('SITE_FEATURE_READY',ident,'resort',flush=True)
            for x in [-3.6,3.6]:rect(row,(x,16.9),.28,.28,3.6)
            for at in [(-10,14),(10,14),(-12,-4),(12,-4),(-19,-26),(18,-29)]:a=T.planter(owner,at);asset_collision(row,a,at)
            for x in [-16,16]:T.bunting(owner,[(x,-6,4.7),(x,-16,4.1),(x,-28,4.7)])
            for at in [(-33,-35),(32,-38)]:forecourt(owner,at,4.0)
            extra=[[-33,35],[32,38],[0,-14]]
        elif ident=='carnival':
            matching(root,['continuous_radial_canopy_panel','scalloped_canopy_edge','canopy_finial','circus_canopy_load_pole','festival_proscenium','circus_public_boarded_apron','circus_apron_fitted_edge','circus_central_show_ring','show_ring_inset_border','curved_audience_bench','bench_shaped_metal_leg'])
            # All of these were owned by the replaced open canopy; neither the
            # obsolete full box nor front centre post survives into the big top.
            keep=len(baseRows[ident].get('publicSpaceBaseCollision',[]))
            row['collision']=json.loads(json.dumps(baseRows[ident]['publicSpaceBaseCollision']))
            row['collision']=[c for c in row['collision']if c[:4]!=[-41,1,-17,25]]
            a=T.big_top(owner,(-29,-13));features.append(a.name);asset_collision(row,a,(-29,-13));circular_walk(row,(-29,-13),12.95,.085);circular_walk(row,(-29,-13),4.35,.30)
            row['landscapeKeepClear'].append([-42.5,-.5,-15.5,26.5])
            pts=[]
            for i in range(64):
                a0=i*math.tau/64;a1=(i+1)*math.tau/64
                if math.sin((a0+a1)/2)<-.965:continue
                walls(row,[(-29+13*math.cos(a0),-13+13*math.sin(a0)),(-29+13*math.cos(a1),-13+13*math.sin(a1))],5.5,.10)
            # The show's mast and curved banks are solid. Keep front aisle open.
            rect(row,(-29,-13),.23,.23,12.8)
            for rr in [7.3,9.1,10.8]:
                for a0,a1 in [(.05,1.3),(1.85,3.09)]:
                    walls(row,[(-29+rr*math.cos(a0+(a1-a0)*i/24),-13+rr*math.sin(a0+(a1-a0)*i/24))for i in range(25)],1.03,.34)
            a=T.swing_ride(owner,(33,-35));asset_collision(row,a,(33,-35),8.2,True);features.append(a.name)
            for i,(y,kind)in enumerate([(-36,'rings'),(-27,'cans'),(-18,'prizes')]):
                a=T.booth(owner,(-51,y),yaw=math.pi/2,kind=kind);features.append(a.name);rect(row,(-51,y),2.1,3.6,3.5)
            T.bunting(owner,[(-46,-40,5.3),(-42,-24,4.5),(-46,-9,5.3)])
            for at in [(-29,-30),(33,-47)]:forecourt(owner,at,4.8)
            extra=[[-29,30],[-44,36],[-44,27],[-44,18],[33,47]]
        elif ident=='mirrors':
            # Stable facade sides/rear keep the same room envelope. Replacing
            # its old flat front with a pierced sculptural funhouse front adds
            # identity without moving the doorway or case room.
            facade=bpy.data.objects.get('parkcopy_facade_mirror_maze')
            if facade:
                matching(facade,['parkcopy_front_gable','parkcopy_form_front','parkcopy_facility_roof_sign'])
            a=T.funhouse_facade(owner,(-6,-10));features.append(a.name)
            for at in [(-16,-22),(5,-23),(-37,-18),(-34,8)]:a=T.planter(owner,at);asset_collision(row,a,at)
            for bay in [o for o in root.children_recursive if o.type=='EMPTY'and o.name.startswith('illusion_arcade_bay')]:
                for side in [-1,1]:T.mask(bay,(side*2.9,-1.7,3.7),.55,side<0)
            forecourt(owner,(-6,-24),4.1);extra=[[-6,24]]
        elif ident=='clockwork':
            matching(root,['clockwork_tower_faceted_body','clockwork_tower_roof','tower_recessed_lancet','ornamental_mechanism_dial','mechanism_real_dial_spoke'])
            row['collision']=[c for c in row['collision']if c[:4]!=[-43,2,-35,10]]
            a=T.mechanical_tower(owner,(-39,-6));features.append(a.name);rect(row,(-39,-6),3.8,1.4,16)
            a=T.coaster_station(owner,(6,-16));features.append(a.name);asset_collision(row,a,(6,-16))
            # Physical queue is west of local coaster room bounds, not across
            # its established boarding/evidence movement volume.
            forecourt(owner,(-5,-30),4.0)
            for at in [(-17,-12),(-26,-6)]:a=T.planter(owner,at);asset_collision(row,a,at)
            extra=[[-5,30],[-32,6]]
        elif ident=='starlight':
            matching(root,['planetarium_true_segmented_dome','planetarium_curved_enclosing_wall','dome_meridian_rib','planetarium_entry','planetarium_recessed_glazed_entry','observatory_lower_wall_course'])
            a=T.retro_theatre(owner,(-34,-5));features.append(a.name);asset_collision(row,a,(-34,-5))
            a=T.orbit_ride(owner,(35,-32));asset_collision(row,a,(35,-32),9.7,True);features.append(a.name)
            # Wheel platform and cabin are retained at their exact case poses;
            # add a separate entrance court without fencing off their access.
            forecourt(owner,(2,8),5.2);forecourt(owner,(-34,-23),4.6);forecourt(owner,(35,-45),4.4)
            for at in [(-43,-21),(-24,-21),(10,6),(-7,6)]:a=T.planter(owner,at);asset_collision(row,a,at)
            extra=[[-34,23],[35,45],[2,-8]]
        for i,(x,y,yaw)in enumerate(sitePlan[ident]['entryFrontages']):
            mat={'fairytale':'mint','carnival':'coral','mirrors':'violet','clockwork':'copper','starlight':'cobalt'}[ident]
            kind={'mirrors':'masks','clockwork':'clockwork','starlight':'orbit'}.get(ident,'prizes'if i==0 else'rings')
            a=T.booth(owner,(x,y),yaw=yaw,kind=kind,mat=mat);features.append(a.name)
            bpy.context.view_layer.update();bb=[o.matrix_world@Vector(v)for o in a.children_recursive if o.type=='MESH'for v in o.bound_box]
            box(row,min(v.x for v in bb),min(v.y for v in bb),max(v.x for v in bb),max(v.y for v in bb),3.9)
        # Geometry checkpoint lets route/landscape corrections resume here,
        # without constructing the rides or room facades again.
        (V/('geometry-'+ident+'.json')).write_text(json.dumps({'row':row,'features':features,'removed':removed,'extra':extra},ensure_ascii=False),encoding='utf8')
        organize_sources();focus(ident);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True)
        print('SITE_GEOMETRY_CHECKPOINT',ident,flush=True)
        paths=promenade(row,root,owner,extra)
        details=D.finish(row,root,owner)
        __import__('park_architecture_v6').restore_reviewed(root,ident)
        __import__('park_material_finish').apply(root,ident)
        bpy.context.view_layer.update();A.O=O
        row['raw']=A.export([root,*root.children_recursive],ident+'.glb','Assets/Art/park_levels/'+ident+'.glb',architectural_export_flags(root,{'textFreePublicArchitecture':True,'themeParkRevision':2}))
        proof['districts'][ident]={'labels':removed,'authoredFeatures':features,'paths':paths,'collisionCount':len(row['collision']),'caseRoomTransformsUnchanged':True}
        proof['districts'][ident]['surfaceDetail']=details
    # Source and raw proof are checkpointed together after a completed district.
    (O/'raw-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    proofFile.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    organize_sources();focus(ident);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True)
    print('THEME_PARK_V2_CHECKPOINT',ident,flush=True)
