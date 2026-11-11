"""Independent geometry, preserved room semantics and public door connectivity."""
import json,sys,hashlib,collections,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from v4_lowpoly_glb import read,array
from v4_dedicated_spaces import apply_world
from v4_freetime_paths import apply as ft
from v4_park_levels import apply,district_collision
O=R/'art/space_v4/park_levels_v1';W=R/'Game/Saved/park-levels-20261104'
base=json.loads((R/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf8'));apply_world(base);ft(base);w=json.loads(json.dumps(base));apply(w)
m=json.loads((O/'manifest.json').read_text(encoding='utf8'));rows=[];errors=[]

def blocks_player(box,x,z,radius=.28):
    if not ((len(box)<6 or box[4]<1.6 and box[5]>.34) and
            box[0]-radius<x<box[2]+radius and box[1]-radius<z<box[3]+radius):
        return False
    if len(box)!=10:
        return True
    x0,z0,x1,z1=box[6:]
    dx,dz=x1-x0,z1-z0
    t=max(0,min(1,((x-x0)*dx+(z-z0)*dz)/(dx*dx+dz*dz)))
    return math.hypot(x-x0-dx*t,z-z0-dz*t)<.36+radius

for ident,s in base['spaces'].items():
    if s.get('outdoor'):continue
    for k in ['mesh','spawn','collision','bounds','targets','mode','walk_surfaces']:
        assert w['spaces'][ident].get(k)==s.get(k),('Interior semantics changed',ident,k)
for a in m['assets']:
    file=R/a['file'];assert hashlib.sha256(file.read_bytes()).hexdigest()==a['sha256'];j,b=read(file);tri=0;normal_maps=0
    for mesh in j['meshes']:
        for p in mesh['primitives']:
            pos=array(j,b,p['attributes']['POSITION']);norm=array(j,b,p['attributes']['NORMAL']);uv=array(j,b,p['attributes']['TEXCOORD_0']);ids=array(j,b,p['indices']).reshape(-1,3)
            assert np.isfinite(pos).all()and np.isfinite(norm).all()and np.isfinite(uv).all();assert np.all(np.linalg.norm(norm,axis=1)>.98)
            area=np.linalg.norm(np.cross(pos[ids[:,1]]-pos[ids[:,0]],pos[ids[:,2]]-pos[ids[:,0]]),axis=1);assert np.all(area>1e-12),(a['id'],'Degenerate geometry')
            tri+=len(ids);normal_maps+=int('normalTexture'in j['materials'][p['material']])
    assert normal_maps>0;assert tri==a['triangles'];d=w['parkLevels']['districts'][a['id']];hub=d['hub'];s=w['spaces'][w['instances'][hub]['space']];bounds=s['bounds'];boxes=s['collision'];step=.5
    assert [c[:6] for c in boxes]==district_collision(a,w),('Unexpected collision change',a['id'])
    for c in boxes:
        if len(c)==10:
            assert blocks_player(c,(c[6]+c[8])/2,(c[7]+c[9])/2),('Walk-through hedge',a['id'],c)
    if a['id']=='fairytale':
        assert any(blocks_player(c,15,18.95) for c in a['collision'])
        assert not any(blocks_player(c,15,18.95) for c in boxes)
    def blocked(x,z):
        return x<bounds[0]+.28 or x>bounds[2]-.28 or z<bounds[1]+.28 or z>bounds[3]-.28 or any(blocks_player(c,x,z) for c in boxes)
    spawn=s['spawn'];assert not blocked(spawn[0],spawn[2]),(hub,'Blocked spawn');start=(round(spawn[0]/step),round(spawn[2]/step));q=collections.deque([start]);seen={start}
    while q:
        x,z=q.popleft()
        for k in [(x+1,z),(x-1,z),(x,z+1),(x,z-1)]:
            if k not in seen and not blocked(k[0]*step,k[1]*step):seen.add(k);q.append(k)
    doors=[]
    for e in w['connections']:
        if e['a']!=hub and e['b']!=hub:continue
        p=e['a_p']if e['a']==hub else e['b_p'];nearest=min((math.hypot(k[0]*step-p[0],k[1]*step-p[2])for k in seen),default=1e10);doors.append({'id':e['id'],'distance':nearest})
        if nearest>1.3:errors.append({'level':a['id'],'door':e['id'],'distanceToReachableFloor':nearest})
    rows.append({'id':a['id'],'triangles':tri,'materialGroups':len(j['meshes'][0]['primitives']),'normalMappedGroups':normal_maps,'bytes':file.stat().st_size,'reachablePublicCells':len(seen),'doors':doors})
assert not errors,errors
for ch in range(1,7):
    q=collections.deque(['plaza']);seen={'plaza'}
    while q:
        at=q.popleft()
        for e in w['connections']:
            if e['minimumChapter']>ch:continue
            nxt=e['b']if e['a']==at else e['a']if e['b']==at else None
            if nxt and nxt not in seen:seen.add(nxt);q.append(nxt)
    for d in w['parkLevels']['districts'].values():assert(d['hub']in seen)==(d['chapter']<=ch),(ch,d)
result={'ok':True,'geometryManifestSHA256':hashlib.sha256((O/'manifest.json').read_bytes()).hexdigest(),'rows':rows,'indoorGeometryAndTargetsPreserved':True,'chapterGatesTopology':True,'runtimeVerified':False,'scope':'Independent file/geometry/public-floor and chapter topology checks. Human visual review and actual native traversal/save remain separate.'}
(W/'static-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(W/'world-complete.json').write_text(json.dumps(w,ensure_ascii=False),encoding='utf8');print('PARK_STATIC_GATE',len(rows),True,flush=True)
