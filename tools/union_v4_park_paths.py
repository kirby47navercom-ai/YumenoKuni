"""Authoring-only 2D union; no runtime or engine dependency."""
import sys,json,math
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Game/Saved/facility-form-20261104/python-geometry'))
from shapely import LineString,union_all,box,intersects,intersection,constrained_delaunay_triangles,get_parts
p=Path(sys.argv[1]);data=json.loads(p.read_text());surface=union_all([LineString(r['centerlineBlenderXY']).buffer(r['width']/2,cap_style='flat',join_style='round',quad_segs=4)for r in data])
assert surface.is_valid
parts=list(surface.geoms)if surface.geom_type=='MultiPolygon'else[surface]
out=[{'outer':[list(v)for v in q.exterior.coords[:-1]],'holes':[[list(v)for v in ring.coords[:-1]]for ring in q.interiors]}for q in parts]
x0,y0,x1,y1=surface.bounds;xs=np.arange(math.floor(x0/2)*2,x1,2);ys=np.arange(math.floor(y0/2)*2,y1,2);xx,yy=np.meshgrid(xs,ys);cells=box(xx.ravel(),yy.ravel(),xx.ravel()+2,yy.ravel()+2);cells=cells[intersects(surface,cells)]
triangles=[]
for q in get_parts(constrained_delaunay_triangles(intersection(surface,cells))):
    if q.geom_type!='Polygon'or q.area<1e-9:continue
    points=[list(v)for v in q.exterior.coords[:-1]];assert len(points)==3
    a,b,c=points
    if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:points.reverse()
    triangles.append(points)
p.with_name('unified-paths.json').write_text(json.dumps({'polygons':out,'triangles':triangles,'maxTileMeters':2,'sourcePaths':len(data),'area':surface.area,'valid':True},separators=(',',':'))+'\n');print('CONNECTED_PATH_SURFACE_UNION',len(data),len(parts),'TERRAIN_TILES',len(triangles))
