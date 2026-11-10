import json,sys,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from v4_lowpoly_glb import read,array
O=R/'art/space_v4/park_levels_v1';W=R/'Game/Saved/park-materials-20261104'
def fingerprint(file):
 j,b=read(file);parts=[];uvbad=0;tri=0
 for m in j['meshes']:
  for p in m['primitives']:
   ids=array(j,b,p['indices']).reshape(-1,3);pos=array(j,b,p['attributes']['POSITION']);n=array(j,b,p['attributes']['NORMAL']);uv=array(j,b,p['attributes']['TEXCOORD_0']);q=np.rint(np.concatenate([pos,n],axis=1)[ids]*100000).astype('<i4');q=q.view('V24').reshape(-1,3);q.sort(axis=1);parts.append(q.reshape(-1).view('V72'));t=uv[ids];uvbad+=int((np.abs(((t[:,1,0]-t[:,0,0])*(t[:,2,1]-t[:,0,1])-(t[:,1,1]-t[:,0,1])*(t[:,2,0]-t[:,0,0])))<1e-10).sum());tri+=len(ids)
 a=np.concatenate(parts);a.sort();return {'triangles':tri,'triangleCornerPositionNormalHash1e5':hashlib.sha256(a.tobytes()).hexdigest(),'degenerateUVTriangles':uvbad}