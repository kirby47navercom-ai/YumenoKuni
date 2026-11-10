"""Remove facility-name geometry from the game's own fixed-view outdoor chunks.

No original game assets are read. Other vertex attributes and clue materials
retain their exact bytes; unused name-atlas resources are omitted from output.
"""
import json,sys,copy
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from v4_lowpoly_glb import read,write,array,digest,Copier
O=R/'art/space_v4/park_levels_v1/theme_park_v2';(O/'local').mkdir(exist_ok=True)
bank=json.loads((R/'art/space_v4/rebuild_v1/manifest.json').read_text(encoding='utf8'));rows=[]
for room in ['ticket_booth','ferris_cabin']:
    row=next(a for a in bank['assets']if a['runtime']=='Assets/Art/explore3d/'+room+'.glb');source=R/row['file'];j,b=read(source);assert digest(source.read_bytes())==row['sha256']
    labelIDs={i for i,m in enumerate(j['materials'])if 'identity_facility_sign' in m.get('name','')}
    if not labelIDs:continue
    removed=0;originalAttributes=[]
    for mesh in j['meshes']:
        labelPoints=[]
        for p in mesh['primitives']:
            if p.get('material') in labelIDs:labelPoints.extend(array(j,b,p['attributes']['POSITION'])[array(j,b,p['indices']).ravel()]);removed+=j['accessors'][p['indices']]['count']//3
        if not labelPoints:continue
        points=np.asarray(labelPoints);lo=points.min(axis=0)-.08;hi=points.max(axis=0)+.08
        kept=[]
        for p in mesh['primitives']:
            if p.get('material') in labelIDs:continue
            originalAttributes.append({k:array(j,b,a).tobytes()for k,a in p['attributes'].items()})
            if 'iron' in j['materials'][p['material']].get('name',''):
                pos=array(j,b,p['attributes']['POSITION']);ids=array(j,b,p['indices']).reshape(-1,3);inside=np.all((pos[ids]>=lo)&(pos[ids]<=hi),axis=(1,2));remaining=ids[~inside].astype('<u4').ravel();removed+=int(inside.sum())
                if inside.any():
                    b+=b'\0'*(-len(b)%4);offset=len(b);b+=remaining.tobytes();bv=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':remaining.nbytes,'target':34963});access=len(j['accessors']);j['accessors'].append({'bufferView':bv,'componentType':5125,'count':len(remaining),'type':'SCALAR'});p['indices']=access
            kept.append(p)
        mesh['primitives']=kept
    c=Copier(j)
    for i in range(len(j['meshes'])):c.copy(j,b,'meshes',i,'owned-'+room)
    file=O/'local'/(room+'.glb');data=write(file,c.j,bytes(c.b));out,blob=read(file)
    assert all('identity_facility_sign'not in m.get('name','')for m in out['materials'])
    after=[{k:array(out,blob,a).tobytes()for k,a in p['attributes'].items()}for m in out['meshes']for p in m['primitives']];assert after==originalAttributes
    rows.append({'file':file.relative_to(R).as_posix(),'runtime':row['runtime'],'sha256':digest(data),'source':row['file'],'sourceSHA256':row['sha256'],'removedNameAndBackingTriangles':removed,'allRemainingVertexAttributesExact':True,'otherMaterialsAndEvidencePreserved':True})
(O/'local-names-manifest.json').write_text(json.dumps({'assets':rows,'scope':'Own fixed-view public exterior name boards only; personal pixel portraits and clue textures preserved.'},indent=2)+'\n',encoding='utf8')
print('TEXT_FREE_FIXED_OUTDOORS',len(rows),sum(r['removedNameAndBackingTriangles']for r in rows))
