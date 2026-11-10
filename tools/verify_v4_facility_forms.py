"""Inspect actual authored Blender roof meshes, entry apertures and continuous ground."""
import bpy,bmesh,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/facility_forms_v3';m=json.loads((O/'manifest.json').read_text(encoding='utf8'))
bpy.ops.wm.open_mainfile(filepath=str(O/'park-form-source.blend'));bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();rows=[]
for row in m['rows']:
    root=bpy.data.objects[row['sourceObject']];meshes=[o for o in root.children_recursive if o.type=='MESH'];roofs=[o for o in meshes if o.name.startswith(('continuous_purpose_roof','continuous_radial_pavilion_roof','formed_octagonal_ticket_roof'))]
    if row['id']not in ['loading_gate','outside_threshold']:
        assert roofs,row['id'];roofrows=[]
        for roof in roofs:
            bm=bmesh.new();bm.from_mesh(roof.data);bad=sum(len(e.link_faces)!=2 for e in bm.edges);bm.free();assert bad==0,(row['id'],roof.name,bad,'open roof edges');roofrows.append({'mesh':roof.name,'watertightEdgeCount':len(roof.data.edges)})
        walls=[o for o in meshes if any(k in o.name for k in ['profiled_front','continuous_wing_front','pierced_load_bearing','octagonal_kiosk_wall'])]
        p=root.matrix_world.translation;d=row['size'][1];blocked=[]
        for x in [-.60,0,.60]:
            origin=Vector((p.x+x,p.y-d/2-.40,p.z+1.40));direction=Vector((0,1,0))
            for wall in walls:
                inv=wall.matrix_world.inverted();hit=wall.ray_cast(inv@origin,inv.to_3x3()@direction,distance=.75)
                if hit[0]:blocked.append((x,wall.name))
        assert not blocked,(row['id'],'door centre blocked',blocked)
        rows.append({'id':row['id'],'roofs':roofrows,'actualEntryRayChecks':3})
    else:rows.append({'id':row['id'],'scope':'open boundary/service structure, not enclosed house'})
terrain=bpy.data.objects['terrain'];tree=BVHTree.FromObject(terrain,deps);ground=[]
for x,y in [(-700,-500),(700,-500),(700,700),(-700,700),(-70,145),(0,-200)]:
    inv=terrain.matrix_world.inverted();hit=tree.ray_cast(inv@Vector((x,y,10)),inv.to_3x3()@Vector((0,0,-1)),20)[0];assert hit is not None;co=terrain.matrix_world@hit;assert abs(co.z+.04)<1e-4;ground.append([x,y,co.z])
pool=next(s for s in json.loads((R/'art/space_v4/full_v2/world_layout.json').read_text(encoding='utf8'))['instances']if s['id']=='pool_edge')['position_blender'];inv=terrain.matrix_world.inverted();assert tree.ray_cast(inv@Vector((pool[0],pool[1],2)),inv.to_3x3()@Vector((0,0,-1)),4)[0]is None,'Extended ground filled the pool'
paths=[]
union_objects=[o for o in bpy.data.objects if o.type=='MESH'and o.name.startswith('continuous_union_park_paving')]
union_trees=[BVHTree.FromObject(o,deps)for o in union_objects];assert union_trees
landform=next(o for o in bpy.data.objects if o.type=='MESH'and o.name.startswith('continuous_layered_background_landforms'));land_tree=BVHTree.FromObject(landform,deps)
for row in m['continuity']['paths']:
    checks=0
    for a,b in zip(row['centerlineBlenderXY'],row['centerlineBlenderXY'][1:]):
        origin=Vector(((a[0]+b[0])/2,(a[1]+b[1])/2,1000));hits=[hit for bt in union_trees if(hit:=bt.ray_cast(origin,Vector((0,0,-1)),2000)[0])is not None];assert hits,(row['id'],'gap in visible path')
        land_hit=land_tree.ray_cast(origin,Vector((0,0,-1)),2000)[0]
        if land_hit is not None:assert max(hit.z for hit in hits)>=land_hit.z-.015,(row['id'],'road buried in landscape')
        checks+=1
    paths.append({'id':row['id'],'actualSegmentRays':checks,'pavingAboveActualTerrain':True})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();proof={'ok':True,'sourceBlendSHA256':sha(O/'park-form-source.blend'),'compiledSHA256':m['asset']['sha256'],'rows':rows,'extendedGroundActualRays':ground,'poolOpeningPreserved':True,'pathMeshRays':paths,'scope':'Actual source meshes and physical apertures/ground/path continuity. This is not semantic user acceptance, native visual QA, whole gameplay or navigation-unlock evidence.'}
(O/'geometry-verification.json').write_text(json.dumps(proof,indent=2)+'\n');print('ACTUAL_FORMS_GEOMETRY_VERIFIED',len(rows),len(paths),flush=True)
