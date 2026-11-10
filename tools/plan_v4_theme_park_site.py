"""Author-directed visitor circuits + room connectors and planted islands.

All input/output XY here is the runtime horizontal X/Z plane. The site brief's
Blender XY is converted once at the boundary, so the map cannot silently mirror.
"""
import json,sys,math,heapq,random
from pathlib import Path
from functools import lru_cache
from collections import deque
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'Game/Saved/facility-form-20261104/python-geometry'))
from shapely import LineString,Point,union_all,constrained_delaunay_triangles,get_parts,Polygon,box
from shapely.affinity import scale
from shapely.ops import nearest_points
path=Path(sys.argv[1]);data=json.loads(path.read_text(encoding='utf8'));site=data['sitePlan'];bounds=data['bounds'];boxes=data['obstacles']+[h+[0,2]for h in data.get('groundHoles',[])];step=1.0

def router(clearance):
    forbidden=union_all([box(c[0]-clearance,c[1]-clearance,c[2]+clearance,c[3]+clearance)for c in boxes])
    @lru_cache(maxsize=None)
    def solid(k):
        x,z=k
        return x<bounds[0]+2 or x>bounds[2]-2 or z<bounds[1]+2 or z>bounds[3]-2 or any(c[0]-clearance<x<c[2]+clearance and c[1]-clearance<z<c[3]+clearance for c in boxes)
    def near(p,allowed=None):
        k=round(p[0]),round(p[1])
        for rr in range(42):
            options=[(k[0]+i,k[1]+j)for i in range(-rr,rr+1)for j in range(-rr,rr+1)if abs(i)==rr or abs(j)==rr]
            for c in sorted(options,key=lambda c:(c[0]-p[0])**2+(c[1]-p[1])**2):
                if not solid(c)and(allowed is None or c in allowed):return c
        raise AssertionError(('No public approach',p,clearance))
    origin=near(data['spawn']);reachable={origin};q=deque([origin])
    while q:
        at=q.popleft()
        for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
            nxt=(at[0]+dx,at[1]+dz)
            if nxt not in reachable and not solid(nxt):reachable.add(nxt);q.append(nxt)
    def route(a,b):
        start,end=near(a,reachable),near(b,reachable);g={start:0};prev={start:None};q=[(0,start)]
        while q:
            _,at=heapq.heappop(q)
            if at==end:break
            for dx,dz in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                nxt=(at[0]+dx,at[1]+dz)
                if solid(nxt)or(dx and dz and(solid((at[0]+dx,at[1]))or solid((at[0],at[1]+dz)))):continue
                v=g[at]+math.hypot(dx,dz)
                if v>=g.get(nxt,1e20):continue
                g[nxt]=v;prev[nxt]=at;heapq.heappush(q,(v+math.dist(nxt,end),nxt))
        assert end in prev,(a,b,clearance)
        points=[];at=end
        while at is not None:points.append(at);at=prev[at]
        points.reverse();pulled=[points[0]];at=0
        while at<len(points)-1:
            nxt=len(points)-1
            while nxt>at+1 and LineString([points[at],points[nxt]]).intersects(forbidden):nxt-=1
            pulled.append(points[nxt]);at=nxt
        return pulled
    return route

parts=[];primary=[];routeProof=[];routes={};streetLines=[]
for spec in site['primaryRoutes']:
    width=spec['width'];key=round(width/2+.45,3)
    if key not in routes:routes[key]=router(key)
    points=[(x,-y)for x,y in spec['points']];allPoints=[]
    for a,b in zip(points,points[1:]):
        line=routes[key](a,b);allPoints.extend(line if not allPoints else line[1:])
    surface=LineString(allPoints).buffer(width/2,quad_segs=10,join_style='round');parts.append(surface);primary.append(surface)
    streetLines.append(LineString(allPoints))
    routeProof.append({'kind':'primary','width':width,'centerline':allPoints})
connect=router(2.65)
coveredEnds=[]
for spec in site.get('coveredWalks',[]):
    points=[(x,-y)for x,y in spec['points']];width=spec.get('width',4.4)-.9
    parts.append(LineString(points).buffer(width/2,quad_segs=8,join_style='round'));coveredEnds.extend([points[0],points[-1]])
    routeProof.append({'kind':'covered-promenade','width':width,'centerline':points})
streets=union_all(streetLines)
for dest in [*data['destinations'],*coveredEnds]:
    # Door aprons join the nearest authored street. A spoke from the spawn to
    # every door cut straight across all courts and flattened their composition.
    anchor=nearest_points(Point(dest),streets)[1]
    points=connect((anchor.x,anchor.y),dest)
    # Only the final door apron is permitted closer to its facade than a street.
    if math.dist(points[-1],dest)>1e-6:points.append(dest)
    if len(points)<2:continue
    parts.append(LineString(points).buffer(2.15,quad_segs=8,join_style='round'));routeProof.append({'kind':'room-connector','width':4.3,'centerline':points})
for x,y,r in site['courts']:parts.append(Point(x,-y).buffer(r,quad_segs=24))
surface=union_all(parts).buffer(.60,quad_segs=10).buffer(-.60,quad_segs=10)
assert surface.geom_type=='Polygon'and surface.is_valid,('Disconnected visitor circuit',surface.geom_type)
surface=Polygon(surface.exterior,[r.coords for r in surface.interiors if Polygon(r).area>14])
groundHoles=union_all([box(*h)for h in data.get('groundHoles',[])])
if not groundHoles.is_empty:surface=surface.difference(groundHoles)
triangles=[list(q.exterior.coords)[:-1]for q in get_parts(constrained_delaunay_triangles(surface))if q.geom_type=='Polygon'and q.area>1e-9]
for t in triangles:
    a,b,c=t
    if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>0:t.reverse()
def polys(geom):return [{'outer':list(q.exterior.coords),'holes':[list(r.coords)for r in q.interiors]}for q in get_parts(geom)if q.geom_type=='Polygon']
# Landscape occupies designed plots, not every point that happens to be grass.
# Reserve full local case movement volumes even if a visible prop covers less.
e=site['landscapeEnvelope'];envelope=box(e[0],-e[3],e[2],-e[1]);keep=[box(*b).buffer(1.5)for b in data.get('keepClearRects',[])]
continuations=[(LineString([(x,-y)for x,y in route['points']]),route['width'])for route in site.get('continuingRoutes',[])]
# These scenic roads are emitted as separate ribbons. Reserve their shoulders
# here too so neither the island hedge mesh nor its collision crosses the road.
road_reserve=union_all([line.buffer(width/2+1.2,quad_segs=8)for line,width in continuations])
occupied=union_all([box(c[0],c[1],c[2],c[3]).buffer(1)for c in boxes]+keep+[road_reserve])
garden=envelope.difference(surface.buffer(1.1)).difference(occupied)
central=union_all([surface.buffer(2.4,quad_segs=10),*[box(*b)for b in data.get('caseCourtyardRects',[])]])
# Central residual space is a designed paved precinct with inset planted beds,
# not another lawn around a ribbon of paths. Dense planting screens its outside.
inside=[]
for q in get_parts(garden.intersection(central)):
    if q.geom_type=='Polygon'and q.area>30:
        c=q.representative_point();inside.append(scale(q,.92,.92,origin=c).intersection(q))
garden=union_all([garden.difference(central),*inside])
# Smaller soft islands organize foregrounds; avoid building an enormous hedge
# around the whole map. Larger residual plots get a few interior tree groups.
islands=[]
for q in get_parts(garden):
    if q.geom_type!='Polygon'or q.area<20:continue
    simplified=q.buffer(-.25).buffer(.25).simplify(.24,preserve_topology=True)
    for v in get_parts(simplified):
        if v.geom_type=='Polygon'and v.area>20:islands.append({'outer':list(v.exterior.coords),'holes':[list(r.coords)for r in v.interiors],'area':v.area,'center':list(v.representative_point().coords)[0]})
planted=union_all([Polygon(p['outer'],p['holes'])for p in islands]).difference(groundHoles);guest=central.union(surface).difference(planted).difference(surface).difference(groundHoles)
for line,width in continuations:
    assert not planted.intersects(line.buffer(width/2)),('Planting crosses continuing road',path.stem)
# Foreground groves and seating are spatial edges of the visitor streets, not
# a distant single row of trees. Their full footprints stay out of case volumes,
# door approaches and public circulation before collisions are emitted.
rng=random.Random(21511+sum(map(ord,path.stem)));treePositions=[]
safeGarden=planted.buffer(-2.65).difference(occupied)
grid=[]
for x in range(math.floor(e[0])+4,math.ceil(e[2])-3,8):
    for z in range(math.floor(-e[3])+4,math.ceil(-e[1])-3,8):
        p=Point(x+rng.uniform(-1.2,1.2),z+rng.uniform(-1.2,1.2))
        if safeGarden.contains(p):grid.append(p)
grid.sort(key=lambda p:p.distance(surface)+.07*p.distance(Point(data['spawn'])))
for p in grid:
    if all(p.distance(Point(q))>7.2 for q in treePositions):treePositions.append([p.x,p.y])
    if len(treePositions)>=38:break
def triangulate(geom):
    triangles=[]
    for polygon in get_parts(geom):
        if polygon.geom_type!='Polygon':continue
        for q in get_parts(constrained_delaunay_triangles(polygon)):
            if q.geom_type!='Polygon'or q.area<1e-9:continue
            t=list(q.exterior.coords)[:-1];a,b,c=t
            if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>0:t.reverse()
            triangles.append(t)
    return triangles
out={'routes':len(routeProof),'connected':True,'layout':'authored visitor circuits with nearest-street door aprons, planted court edges and foreground groves','polygons':polys(surface),'primaryPolygons':polys(union_all(primary)),'triangles':triangles,'guestTriangles':triangulate(guest),'plantingTriangles':triangulate(planted),'landscapeIslands':islands,'foregroundTrees':treePositions,'routeProof':routeProof,'pavedArea':surface.area+guest.area,'guestPrecinctArea':central.area,'insetPlantingArea':planted.intersection(central).area}
path.with_suffix('.mesh.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf8')
print('SITE_CIRCUIT',path.stem,'paved',round(surface.area),'islands',len(islands),flush=True)
