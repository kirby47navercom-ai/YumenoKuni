"""Reuse building-only evidence only when actual triangles, shading and transforms agree."""
from pathlib import Path
import sys,json,hashlib,re,io
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from v4_lowpoly_glb import read,array
from compile_v4_rebuilt_environment import matrices
W=R/'Game/Saved/facility-form-20261104';O=R/'art/space_v4/facility_forms_v3'
def signatures(file):
    j,b=read(file);world=matrices(j);parent={c:i for i,n in enumerate(j['nodes'])for c in n.get('children',[])};roots={i:n['extras']['facilityIdentity']for i,n in enumerate(j['nodes'])if n.get('extras',{}).get('architectureVersion')==3};groups={v:[]for v in roots.values()};material={}
    def pixels(i):
        im=j['images'][i];v=j['bufferViews'][im['bufferView']];at=v.get('byteOffset',0);p=Image.open(io.BytesIO(b[at:at+v['byteLength']])).convert('RGBA');return hashlib.sha256(p.tobytes()).hexdigest()
    def canonical(v):
        if isinstance(v,dict):
            out={}
            for k,x in v.items():
                if k in ['name','extras']:continue
                if k.endswith('Texture')and isinstance(x,dict)and'index'in x:
                    t=j['textures'][x['index']];ii=t.get('source',t.get('extensions',{}).get('EXT_texture_webp',{}).get('source'));out[k]={**x,'index':pixels(ii),'sampler':j.get('samplers',[])[t['sampler']]if'sampler'in t else None}
                else:out[k]=canonical(x)
            return out
        if isinstance(v,list):return[canonical(x)for x in v]
        return v
    for i,m in enumerate(j.get('materials',[])):material[i]=hashlib.sha256(json.dumps(canonical(m),sort_keys=True).encode()).hexdigest()
    for ni,n in enumerate(j['nodes']):
        if'mesh'not in n:continue
        root=ni
        while root not in roots and root in parent:root=parent[root]
        if root not in roots:continue
        mat=world[ni];basis=mat[:3,:3];normalmat=np.linalg.inv(basis).T
        for p in j['meshes'][n['mesh']]['primitives']:
            pos=array(j,b,p['attributes']['POSITION']).astype(float)@basis.T+mat[:3,3];norm=array(j,b,p['attributes']['NORMAL']).astype(float)@normalmat.T;norm/=np.linalg.norm(norm,axis=1,keepdims=True);uv=array(j,b,p['attributes']['TEXCOORD_0']).astype(float);ix=array(j,b,p['indices']).reshape(-1,3)
            for tri in ix:
                points=[tuple(np.round(np.r_[pos[k],norm[k],uv[k]],5))for k in tri];groups[roots[root]].append((material[p['material']],*sorted(points)))
    return{k:hashlib.sha256(repr(sorted(v)).encode()).hexdigest()for k,v in groups.items()}
before=Path(next((a.split('=',1)[1]for a in sys.argv if a.startswith('--before=')),str(W/'architecture-before-landscape-refine.glb')));output=Path(next((a.split('=',1)[1]for a in sys.argv if a.startswith('--output=')),str(W/'unchanged-building-render-proof.json')))
old=signatures(before);m=json.loads((O/'manifest.json').read_text(encoding='utf8'));new=signatures(R/m['rawAsset']['file']);assert old.keys()==new.keys();changed={k for k in old if old[k]!=new[k]};allowed=next((set(a.split('=',1)[1].split(','))for a in sys.argv if a.startswith('--allow-changed=')),set());assert changed<=allowed,sorted(changed-allowed)
output.write_text(json.dumps({'ok':True,'facilities':len(new),'unchangedIDs':sorted(set(new)-changed),'changedIDsRequiringNewNativeViews':sorted(changed),'scope':'Listed unchanged exterior groups have identical actual transformed triangles, normals, UV and decoded material image pixels/PBR. Earlier building-only screenshots may be reused ONLY for these groups; changed facilities and all old tree/path junction views require later native evidence.','before':str(before),'after':m['rawAsset']['file'],'signatures':new},indent=2)+'\n');print('UNCHANGED_ACTUAL_BUILDING_GEOMETRY',len(new)-len(changed),'CHANGED_FOR_RECHECK',len(changed))
