"""Audit authored walking space, including outdoor aliases, against runtime rules.

This is a source-data check, not a substitute for native traversal. The raster
uses 12 cm cells and the runtime's 27 cm radius, height filter and hedge capsule.
"""
from pathlib import Path
import argparse
import json
import math
import sys
from collections import deque
import numpy as np
from scipy.ndimage import label, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))


def authored_world():
    from v4_dedicated_spaces import apply_world
    from v4_freetime_paths import apply as freetime
    from v4_park_levels import apply
    w = json.loads((ROOT / 'art/space_v4/runtime_v1/world.json').read_text(encoding='utf8'))
    apply_world(w)
    freetime(w)
    apply(w)
    return w


def solid(s, x, z, y=None, radius=.27):
    b = s['bounds']
    if x < b[0]+radius or x > b[2]-radius or z < b[1]+radius or z > b[3]-radius:
        return True
    floor = (s['spawn'][1] if y is None else y) - s.get('eye_height', 1.6)
    for c in s['collision']:
        if len(c) >= 6 and not (c[4] < floor+1.6 and c[5] > floor+.34):
            continue
        if not (c[0]-radius < x < c[2]+radius and c[1]-radius < z < c[3]+radius):
            continue
        if len(c) == 10:
            ax, az, bx, bz = c[6:]
            dx, dz = bx-ax, bz-az
            t = max(0, min(1, ((x-ax)*dx+(z-az)*dz)/(dx*dx+dz*dz)))
            if math.hypot(x-ax-t*dx, z-az-t*dz) >= .36+radius:
                continue
        return True
    return False


class Grid:
    def __init__(self, s, y=None, step=.12):
        self.s, self.y, self.step = s, y, step
        a,b,c,d = s['bounds']
        self.xx = np.arange(a+.27, c-.27+1e-6, step)
        self.zz = np.arange(b+.27, d-.27+1e-6, step)
        free = np.ones((len(self.zz), len(self.xx)), dtype=bool)
        floor = (s['spawn'][1] if y is None else y)-s.get('eye_height', 1.6)
        for q in s['collision']:
            if len(q) >= 6 and not (q[4] < floor+1.6 and q[5] > floor+.34):
                continue
            ix = np.flatnonzero((self.xx > q[0]-.27)&(self.xx < q[2]+.27))
            iz = np.flatnonzero((self.zz > q[1]-.27)&(self.zz < q[3]+.27))
            if not len(ix) or not len(iz):
                continue
            region = np.s_[iz[0]:iz[-1]+1, ix[0]:ix[-1]+1]
            if len(q) == 10:
                ax,az,bx,bz = q[6:]; dx,dz = bx-ax,bz-az
                xx,zz = np.meshgrid(self.xx[ix], self.zz[iz])
                t = np.clip(((xx-ax)*dx+(zz-az)*dz)/(dx*dx+dz*dz), 0, 1)
                free[region] &= (xx-ax-t*dx)**2+(zz-az-t*dz)**2 >= .63**2
            else:
                free[region] = False
        self.labels, _ = label(free)
        self.sizes = np.bincount(self.labels.ravel())

    def component(self, x, z):
        i,j = round((x-self.xx[0])/self.step), round((z-self.zz[0])/self.step)
        if not (0 <= i < len(self.xx) and 0 <= j < len(self.zz)):
            return 0
        # Snap only within one grid cell, and never accept an actually solid pose.
        if solid(self.s, x, z, self.y):
            return 0
        near = self.labels[max(0,j-1):j+2,max(0,i-1):i+2]
        ids = near[near > 0]
        return int(ids[np.argmax(self.sizes[ids])]) if len(ids) else 0

    def distance(self, comp):
        return distance_transform_edt(self.labels != comp)*self.step

    def at(self, values, x, z):
        i,j = round((x-self.xx[0])/self.step),round((z-self.zz[0])/self.step)
        i,j = max(0,min(len(self.xx)-1,i)),max(0,min(len(self.zz)-1,j))
        return float(values[j,i])+math.hypot(x-self.xx[i],z-self.zz[j])


def landing(s, p):
    x,y,z = p; n = max(.01, math.hypot(x,z))
    x,z,y = x-x/n*.9,z-z/n*.9,y-1.2+s.get('eye_height',1.6)
    for r in range(50):
        for k in range(24 if r else 1):
            a = k*math.pi/12
            px,pz = x+r*.15*math.cos(a),z+r*.15*math.sin(a)
            if not solid(s,px,pz,y):
                return px,y,pz
    return x,y,z


def occluded(s, eye, target):
    x,y,z=eye;tx,ty,tz=target;distance=math.hypot(tx-x,tz-z)
    for c in s['collision']:
        if len(c)>=6 and (c[4]>max(y,ty) or c[5]<min(y,ty)):continue
        start=[x,z];end=[tx,tz];lower=c[:2];upper=c[2:4]
        if len(c)==10:
            ax,az,bx,bz=c[6:];ux,uz=bx-ax,bz-az;length=math.hypot(ux,uz);ux/=length;uz/=length
            def local(px,pz):return [(px-ax)*ux+(pz-az)*uz,(pz-az)*ux-(px-ax)*uz]
            start,end=local(x,z),local(tx,tz);lower,upper=[0,-.36],[length,.36]
        if all(lower[k]-.01<=end[k]<=upper[k]+.01 for k in [0,1]):continue
        lo,hi=0,1;hit=True
        for k in [0,1]:
            delta=end[k]-start[k]
            if abs(delta)<.0001:
                if not lower[k]<=start[k]<=upper[k]:hit=False;break
            else:
                a,b=(lower[k]-start[k])/delta,(upper[k]-start[k])/delta
                lo,hi=max(lo,min(a,b)),min(hi,max(a,b))
                if lo>hi:hit=False;break
        if hit and hi>0 and lo>0 and lo*distance<distance-.38:return True
    return False


def stair_route(s, destination, step=.12):
    """Walk the same <=28 cm floor transitions as floorAt, not a flat raster."""
    eye=s.get('eye_height',1.6);sx,sy,sz=s['spawn'];b=s['bounds']
    start=(round(sx/step),round(sz/step),round((sy-eye)*10000))
    queue=deque([start]);seen={start}
    while queue:
        ix,iz,h=queue.popleft();floor=h/10000
        if math.hypot(ix*step-destination[0],iz*step-destination[2])<.3 and abs(floor+eye-destination[1])<.3:return True
        for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
            x,z=(ix+dx)*step,(iz+dz)*step
            if solid(s,x,z,floor+eye):continue
            surfaces=[p[4] for p in s.get('walk_surfaces',[]) if p[0]-.02<=x<=p[2]+.02 and p[1]-.02<=z<=p[3]+.02 and p[4]<=floor+.28]
            nxt=(ix+dx,iz+dz,round((max(surfaces) if surfaces else s.get('floor',0))*10000))
            if nxt not in seen:seen.add(nxt);queue.append(nxt)
    return False


def door_view(s, g, component, anchor, eye):
    """Find a reachable, unobstructed interaction position, not just proximity."""
    x,y,z=anchor
    ix=np.flatnonzero(abs(g.xx-x)<4.8)[::2];iz=np.flatnonzero(abs(g.zz-z)<4.8)[::2]
    candidates=[]
    for j in iz:
        for i in ix:
            if g.labels[j,i]!=component:continue
            px,pz=float(g.xx[i]),float(g.zz[j]);d=math.hypot(px-x,pz-z)
            pitch=math.degrees(math.atan2(y-eye,max(.1,d)))
            if .45<d<4.75 and s['pitch_limits'][0]<=pitch<=s['pitch_limits'][1]:candidates.append((d,px,pz))
    for _,px,pz in sorted(candidates):
        if not solid(s,px,pz,eye) and not occluded(s,(px,eye,pz),anchor):return [px,eye,pz]
    return None


def audit(w):
    rows,errors = [],[]
    for ident,i in w['instances'].items():
        if i.get('storyGeometryOnly'):
            continue
        s = w['spaces'][i['space']]; x,y,z = s['spawn']
        g = Grid(s); root = g.component(x,z)
        row = dict(id=ident,mode=s['mode'],outdoor=s.get('outdoor',False),spawnBlocked=solid(s,x,z),
                   reachableArea=round(float(g.sizes[root])*.12**2,2) if root else 0,doors=[],targets=[])
        if not root:
            errors.append(dict(id=ident,kind='spawn'))
        distance = g.distance(root) if root else None
        for e in w['connections']:
            side = 'a' if e['a']==ident else 'b' if e['b']==ident else None
            if side is None:
                continue
            px,py,pz = landing(s,e[side+'_p'])
            same = g.component(px,pz)==root and bool(root)
            stair=False
            if abs(py-y)>.3:
                stair=stair_route(s,(px,py,pz));same=stair
            anchor = e[side+'_p']
            near = g.at(distance,anchor[0],anchor[2]) if root else float('inf')
            sight=not occluded(s,(px,py,pz),anchor)
            viewgrid=Grid(s,py) if stair else g;viewroot=viewgrid.component(px,pz) if stair else root
            view=door_view(s,viewgrid,viewroot,anchor,py if stair else y) if viewroot else None
            row['doors'].append(dict(id=e['id'],landing=[round(px,3),round(py,3),round(pz,3)],sameComponent=same,distance=near,stairRoute=stair,arrivalCanSeeDoor=sight,interactionView=view))
            if not same or near > 4.8 or view is None:
                errors.append(dict(id=ident,kind='door',door=e['id'],sameComponent=same,distance=near,interactionView=view))
        if root:
            for t in s['targets']:
                p=t['p'];near=g.at(distance,p[0],p[2]);row['targets'].append(dict(id=t['id'],distance=near))
                if near>4.8:
                    errors.append(dict(id=ident,kind='target',target=t['id'],distance=near))
        rows.append(row)
    return dict(ok=not errors,instances=len(rows),rows=rows,errors=errors,
                scope='12 cm raster connectivity, exact point collision and current radial arrival rules; native traversal is separately required.')


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--world');ap.add_argument('--out',required=True);args=ap.parse_args()
    w=json.loads(Path(args.world).read_text(encoding='utf8')) if args.world else authored_world()
    result=audit(w);Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:result[k] for k in ['ok','instances','errors']},ensure_ascii=False))
    sys.exit(0 if result['ok'] else 1)
