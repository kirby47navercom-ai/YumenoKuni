"""Continuous landscape and paths outside the playable park, Blender Z-up.

The playable bounds are not the world's visible edge. Distant ground, graded
landforms and tree belts occlude the finite mesh edge; service roads bend into
that scenery. No new destination, escape route, story clue or unlock is added.
"""
import bpy,math,random,json,subprocess
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import v4_rebuilt_environment_kit as K
R=Path(__file__).resolve().parents[1]

def ribbon(parent,name,points,width,mat='paving',z=.008):
    pts=[Vector((x,y))for x,y in points];edges=[]
    for i,p in enumerate(pts):
        a=(p-pts[max(0,i-1)]);b=(pts[min(len(pts)-1,i+1)]-p)
        if a.length<1e-5:a=b.copy()
        if b.length<1e-5:b=a.copy()
        a.normalize();b.normalize();n=Vector((-a.y,a.x))+Vector((-b.y,b.x));n.normalize();scale=min(width*.65,width/2/max(.4,n.dot(Vector((-b.y,b.x)))))
        edges.append((p-n*scale,p+n*scale))
    verts=[(p.x,p.y,z)for a,b in edges for p in [a,b]]
    road=K.mesh(name,verts,[(i*2,i*2+1,i*2+3,i*2+2)for i in range(len(pts)-1)],mat,parent)
    for side in [0,1]:
        line=[(a[side].x,a[side].y,z+.025)for a in edges];K.tube('continuous_path_coping',line,[.045]*len(line),'stone',parent,6)
    return road

def distant_tree(parent,x,y,seed):
    rng=random.Random(seed);h=rng.uniform(4.5,8);r=K.root('landscape_tree',parent);r.location=(x,y,0)
    K.tube('connected_background_tree_trunk',[(0,0,0),(.12,.04,h*.7)],[.18,.09],'bark',r,6)
    for side in [-1,1]:K.tube('background_tree_branch',[(.05,.01,h*.42),(side*.75,side*.3,h*.74)],[.08,.035],'bark',r,5)
    for i in range(3):
        a=i*math.tau/3;cx,cy,cz=math.cos(a)*h*.18,math.sin(a)*h*.17,h*.73+rng.uniform(-.35,.5);radius=h*rng.uniform(.22,.29);n=12;bands=6
        vertices=[(cx,cy,cz+radius)]
        for band in range(1,bands):
            theta=math.pi*band/bands
            for j in range(n):
                angle=j*math.tau/n;rr=radius*(1+.13*math.sin(angle*3+i)+rng.uniform(-.10,.10));vertices.append((cx+rr*math.sin(theta)*math.cos(angle),cy+rr*math.sin(theta)*math.sin(angle),cz+rr*math.cos(theta)*1.08))
        bottom=len(vertices);vertices.append((cx,cy,cz-radius*1.08));faces=[(0,1+j,1+(j+1)%n)for j in range(n)]
        faces +=[(1+band*n+j,1+band*n+(j+1)%n,1+(band+1)*n+(j+1)%n,1+(band+1)*n+j)for band in range(bands-2)for j in range(n)]
        faces +=[(bottom,1+(bands-2)*n+(j+1)%n,1+(bands-2)*n+j)for j in range(n)]
        K.mesh('irregular_branch_connected_tree_crown',vertices,faces,'leaf',r,True)
    return r

def build(world,A):
    previous=[o for o in world.children_recursive if o.name.startswith('walkway')]
    for root in [o for o in world.children_recursive if o.name.startswith('park_continuity_v3')]:previous+=A.descendants(root)
    A.erase(previous);r=K.root('park_continuity_v3',world);paths=[]
    # Preserve the pool opening in actual global coordinates while extending
    # ground well beyond the camera's useful range. No exposed slab end.
    terrain=next(o for o in world.children_recursive if A.base(o)=='terrain');inverse=terrain.matrix_world.inverted()
    layout=json.loads((R/'art/space_v4/full_v2/world_layout.json').read_text(encoding='utf8'));pool=next(i for i in layout['instances']if i['id']=='pool_edge')['position_blender'];px,py,_=pool
    outer=[(-1800,-1800),(1800,-1800),(1800,1800),(-1800,1800)];inner=[(px-6.01,py-3.01),(px+6.01,py-3.01),(px+6.01,py+3.01),(px-6.01,py+3.01)]
    verts=[tuple(inverse@Vector((x,y,z)))for z in [-.16,-.04]for ring in [outer,inner]for x,y in ring];faces=[]
    for i in range(4):
        j=(i+1)%4;faces.extend([(i+8,j+8,j+12,i+12),(i,i+4,j+4,j),(i,j,j+8,i+8),(i+4,i+12,j+12,j+4)])
    o=K.mesh('continuous_extended_ground',verts,faces,'grass');terrain.data=o.data;bpy.data.objects.remove(o,do_unlink=True);terrain['poolOpeningWorldBlender']=[px,py,12.02,6.02];terrain['visualExtentBeyondWalkBounds']=True
    routes=[
      ('main_approach',[(0,-95),(0,-65),(0,-42),(0,-14),(0,18)],6),
      ('west_facility_loop',[(0,12),(-50,12),(-50,56),(-16,56),(-16,18),(0,18)],4),
      ('east_park_loop',[(14,0),(42,0),(42,-13),(130,-13),(130,53),(42,53),(42,0)],5),
      ('north_guest_promenade',[(42,56),(70,56),(98,56),(112,56),(112,69)],4),
      ('west_attraction_service', [(-14,0),(-50,0),(-50,84),(-70,84),(-70,96)],4.4),
      ('continuing_outer_service_road',[(-70,96),(-70,112),(-70,137),(-66,155),(-53,173),(-42,191),(-40,225),(-47,264),(-62,300),(-78,365),(-71,445),(-42,535),(-18,650),(-33,790)],5.5),
      # Turn before the first rising terrain belt. The former straight run
      # entered that belt before its bend and looked like a road ending in grass.
      ('bending_main_road',[(0,-95),(2,-112),(9,-130),(22,-146),(35,-162),(41,-187),(39,-225),(31,-270),(11,-320),(-18,-380),(-33,-450),(-24,-530),(4,-640),(28,-780)],6),
    ]
    # Public doors join a promenade rather than ending a painted strip on grass.
    specs={s['id']:s for s in json.loads((R/'art/space_v4/full_v2/manifest.json').read_text(encoding='utf8'))['spaces']}
    byid={i['id']:i for i in layout['instances']}
    for ident in ['dining_room','kitchen','clinic','laundry_room','supply_store','hotel_multiuse']:
        x,y,z=byid[ident]['position_blender'];y-=specs[ident]['size_m'][1]/2;routes.append(('connected_front_'+ident,[(-50,y-2.1),(x,y-2.1),(x,y+.15)],2.6))
    for ident in ['management_office','electrical_room']:
        x,y,z=byid[ident]['position_blender'];y-=specs[ident]['size_m'][1]/2;routes.append(('connected_front_'+ident,[(42,y-2),(x,y-2),(x,y+.15)],2.5))
    for ident in ['performance_stage','mirror_maze']:
        x,y,z=byid[ident]['position_blender'];y-=specs[ident]['size_m'][1]/2;routes.append(('connected_front_'+ident,[(x,-13),(x,y+.12)],3.5))
    for ident in ['dream_lobby','reading_room','archive_room']:
        x,y,z=byid[ident]['position_blender'];y-=specs[ident]['size_m'][1]/2;routes.append(('connected_front_'+ident,[(x,56),(x,y+.12)],2.7))
    for ident in ['maintenance_workshop','exhibition_room','record_room','inspection_hall_normal']:
        x,y,z=byid[ident]['position_blender'];y-=specs[ident]['size_m'][1]/2;routes.append(('connected_front_'+ident,[(-50,y-1.7),(x,y-1.7),(x,y+.12)],2.6))
    routes +=[('control_front',[(130,35.8),(118,35.8),(118,37.6)],2.6),('waiting_front',[(130,21.3),(118,21.3),(118,23.1)],2.6),('glazing_service_access',[(130,34),(96.4,34),(96.4,27.5)],2.6),('stock_service_access',[(42,33.3),(58,33.3),(58,35.1)],2.6)]
    for name,points,width in routes:paths.append({'id':name,'centerlineBlenderXY':points,'width':width,'endCondition':'continues_into_next_path_building_apron_or_curved_occluded_landscape'})
    O=R/'art/space_v4/facility_forms_v3';pathspec=O/'path-union-input.json';pathspec.write_text(json.dumps(paths)+'\n');subprocess.run(['C:/python/python.exe',str(R/'tools/union_v4_park_paths.py'),str(pathspec)],check=True)
    union=json.loads((O/'unified-paths.json').read_text())
    vertices=[];faces=[];lookup={}
    for triangle in union['triangles']:
        face=[]
        for x,y in triangle:
            key=(round(x,8),round(y,8))
            if key not in lookup:lookup[key]=len(vertices);vertices.append((x,y,.008))
            face.append(lookup[key])
        if len(set(face))==3:faces.append(face)
    road_surfaces=[K.mesh('continuous_union_park_paving',vertices,faces,'paving',r)];road_copings=[]
    for part in union['polygons']:
        for outline in [part['outer'],*part['holes']]:
            points=[]
            for a,b in zip(outline,[*outline[1:],outline[0]]):
                count=max(1,math.ceil(math.dist(a,b)/2))
                points.extend([(a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count,.035)for i in range(count)])
            points.append(points[0]);road_copings.append(K.tube('outer_perimeter_path_coping',points,[.04]*len(points),'stone',r,6))
    # Several depth layers, not a flat fence or an opaque wall at the map limit.
    verts=[];rings=[(145,0),(190,1.0),(245,10),(320,23),(440,28),(650,19),(950,35),(1300,21)]
    for ri,(radius,amplitude)in enumerate(rings):
        for i in range(128):
            a=i*math.tau/128;z=-.06+amplitude*(.55+.20*math.sin(a*3+ri*.11)+.17*math.cos(a*7-.5));verts.append((math.cos(a)*radius,35+math.sin(a)*radius,z))
    land=K.mesh('continuous_layered_background_landforms',verts,[(ri*128+i,ri*128+(i+1)%128,(ri+1)*128+(i+1)%128,(ri+1)*128+i)for ri in range(len(rings)-1)for i in range(128)],'grass',r,True,uv_scale=.1)
    bpy.context.view_layer.update()
    terrain_tree=BVHTree.FromPolygons([land.matrix_world@v.co for v in land.data.vertices],[tuple(p.vertices)for p in land.data.polygons])
    for road in [*road_surfaces,*road_copings]:
        inv=road.matrix_world.inverted()
        for vertex in road.data.vertices:
            point=road.matrix_world@vertex.co;hit=terrain_tree.ray_cast(Vector((point.x,point.y,1000)),Vector((0,0,-1)),2000)[0]
            if hit is not None and hit.z>0:point.z+=hit.z+.08;vertex.co=inv@point
        road.data.update();road['terrainConformingRoad']=True
    def plant(x,y,seed):
        node=distant_tree(r,x,y,seed);hit=terrain_tree.ray_cast(Vector((x,y,1000)),Vector((0,0,-1)),2000)[0]
        if hit is not None:node.location.z=max(0,hit.z)
        return node
    # Inner belts screen long flat sightlines. Each tree has a real trunk and a
    # crown with volume; no identical black billboard cylinder around the park.
    rng=random.Random(241104)
    for cluster in range(24):
        a=rng.uniform(0,math.tau);rad=rng.uniform(145,230);cx=math.cos(a)*rad;cy=35+math.sin(a)*rad
        for j in range(rng.randint(4,8)):
            x=cx+rng.uniform(-15,15);y=cy+rng.uniform(-14,14)
            if abs(x)<9 and y<0 or abs(x+70)<10 and 95<y<150:continue
            plant(x,y,8031+cluster*31+j)
    for x,y in [(-87,142),(-84,156),(-78,169),(-71,180),(-58,196),(-32,210),(25,-137),(29,-148),(46,-159),(49,-176),(55,-189),(9,-224),(12,-241),(20,-264),(44,-276)]:plant(x,y,round(x*17+y*3))
    # Ground-cover foliage on the outside of the bend hides the far paving
    # entering the landform. A tree's high crown alone leaves that sightline open.
    for i,(x,y) in enumerate([(20,-137),(24,-142),(29,-148),(34,-153)]):
        shrub=plant(x,y,91404+i);shrub.name='main_road_bend_understorey';shrub.scale=(1.25,1.25,.42)
        low=min(v.co.z for o in shrub.children if o.type=='MESH'and'crown'in o.name for v in o.data.vertices)
        shrub.location.z+=.04-low*.42
    # Real entrance structure over the preserved existing locked gate leaves.
    for x in [-4.25,4.25]:K.tube('park_entry_load_bearing_pier',[(x,-40,0),(x,-40,5.15)],[.33,.24],'stone',r,12)
    arch=[(-4.3+i*8.6/32,-40,5.05+1.10*math.sin(i*math.pi/32))for i in range(33)];K.tube('continuous_park_entrance_arch',arch,[.25]*len(arch),'cream_trim',r,10)
    r['visualWorldEndsBeyondCamera']=True;r['newGameplayDestinations']=0;r['existingWorldRoutesUnchanged']=True
    return {'paths':paths,'groundWorldBounds':[-1800,-1800,1800,1800],'distantLandscapeRings':rings,'newGameplayDestinations':0,'storyGeographyClaim':'Generic continuous park surroundings only; no new named city, country, escape route, people or story fact.'}
