import bpy,sys,json
from pathlib import Path
from mathutils import Vector
R=Path.cwd();O=R/'art/space_v4/park_levels_v1';W=R/'Game/Saved/park-architecture-v6';W.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(O/'parks-authoring.blend'))
catalog=json.loads((R/'Game/Saved/park-materials-20261104/gallery/catalog.json').read_text(encoding='utf8'));rows=[]
for row in catalog['rows']:
    groups=[]
    for name in row['objects']:
        o=bpy.data.objects.get(name)
        if o is None:continue
        inverse=o.matrix_world.inverted();meshes=[q for q in [o,*o.children_recursive]if q.type=='MESH'];points=[inverse@(q.matrix_world@v.co)for q in meshes for v in q.data.vertices]
        groups.append({'name':name,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'localBounds':[[min(v[k]for v in points)for k in range(3)],[max(v[k]for v in points)for k in range(3)]]if points else None,'triangles':sum(len(p.vertices)-2 for q in meshes for p in q.data.polygons),'extras':{k:v for k,v in o.items()if isinstance(v,(str,float,int))}})
    rows.append({'id':row['id'],'district':row['district'],'label':row['label'],'groups':groups})
(W/'existing.json').write_text(json.dumps({'ok':True,'rows':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('ARCHITECTURE_INVENTORY',len(rows),flush=True)
