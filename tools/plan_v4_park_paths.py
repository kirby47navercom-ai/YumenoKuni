"""Connected public routes around actual facility footprints; authoring only."""
import json,sys,heapq,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Game/Saved/facility-form-20261104/python-geometry'))
from shapely import LineString,union_all,constrained_delaunay_triangles,get_parts,Polygon,box
p=Path(sys.argv[1]);data=json.loads(p.read_text(encoding='utf8'));step=1.5;boxes=data['obstacles'];bounds=data['bounds'];clearance=2.65
forbidden=union_all([box(c[0]-clearance,c[1]-clearance,c[2]+clearance,c[3]+clearance)for c in boxes])
def solid(k):
 x,z=k[0]*step,k[1]*step
 return x<bounds[0]+2 or x>bounds[2]-2 or z<bounds[1]+2 or z>bounds[3]-2 or any(c[0]-clearance<x<c[2]+clearance and c[1]-clearance<z<c[3]+clearance for c in boxes)
def key(p):return round(p[0]/step),round(p[1]/step)
def safe(p):
 k=key(p)
 for r in range(20):
  candidates=[(k[0]+i,k[1]+j)for i in range(-r,r+1)for j in range(-r,r+1)if abs(i)==r or abs(j)==r]
  for c in sorted(candidates,key=lambda c:(c[0]*step-p[0])**2+(c[1]*step-p[1])**2):
   if not solid(c):return c
 raise AssertionError(('No public space',p))
start=safe(data['spawn']);routes=[]
for dest in data['destinations']:
 end=safe(dest);q=[(0,start)];g={start:0};prev={start:None}
 while q:
  _,at=heapq.heappop(q)
  if at==end:break
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   nxt=(at[0]+dx,at[1]+dz)
   if solid(nxt)or(dx and dz and(solid((at[0]+dx,at[1]))or solid((at[0],at[1]+dz)))):continue
   cost=g[at]+math.hypot(dx,dz)
   if cost>=g.get(nxt,1e20):continue
   g[nxt]=cost;prev[nxt]=at;heapq.heappush(q,(cost+math.hypot(nxt[0]-end[0],nxt[1]-end[1]),nxt))
 assert end in prev,('Unreachable public approach',dest)
 route=[];at=end
 while at is not None:route.append([at[0]*step,at[1]*step]);at=prev[at]
 route.reverse()
 # Remove the grid staircase with visibility-tested straight connections.
 # The full paving width stays outside the expanded facility footprint.
 pulled=[route[0]];at=0
 while at<len(route)-1:
  nxt=len(route)-1
  while nxt>at+1 and LineString([route[at],route[nxt]]).intersects(forbidden):nxt-=1
  pulled.append(route[nxt]);at=nxt
 # An apron may approach a door closer than the public-route clearance.
 pulled.append(dest)
 routes.append(LineString(pulled).buffer(2.15,quad_segs=8,join_style='round'))
surface=union_all(routes).buffer(.55,quad_segs=8).buffer(-.55,quad_segs=8)
assert surface.geom_type=='Polygon'and surface.is_valid
# Tiny slivers between converging routes are paving, not triangular lawns.
surface=Polygon(surface.exterior,[r.coords for r in surface.interiors if Polygon(r).area>9])
triangles=[list(q.exterior.coords)[:-1]for q in get_parts(constrained_delaunay_triangles(surface))if q.geom_type=='Polygon'and q.area>1e-9]
for triangle in triangles:
 a,b,c=triangle
 if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>0:triangle.reverse()
out={'routes':len(routes),'connected':True,'polygons':[{'outer':list(surface.exterior.coords),'holes':[list(r.coords)for r in surface.interiors]}],'triangles':triangles}
p.with_suffix('.mesh.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf8')
