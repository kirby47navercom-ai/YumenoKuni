"""Audit the actual full model inventory, rather than equating the old 61 with all 3D."""
from pathlib import Path
import sys,json,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from v4_lowpoly_glb import read,array,digest
W=R/'Game/Saved/sculpted-environment-20261103';known={}
for folder,proof in [('rebuild_v1',W/'rebuilt-static-verification.json'),('rebuilt_dedicated_v2',R/'art/space_v4/rebuilt_dedicated_v2/static-verification.json')]:
    p=R/'art/space_v4'/folder/'manifest.json';raw=p.read_bytes();gate=json.loads(proof.read_text());assert gate['ok']and gate['manifestSHA256']==digest(raw)
    for row in json.loads(raw)['assets']:known[row['runtime']]={'source':row['file'],'sha256':row['sha256'],'owner':folder}
special={
 'Assets/Art/environment/sky_day.glb':('tools/build_v4_sky.py','sky backdrop; textured dome, no opaque surface normal required'),
 'Assets/Art/environment/sky_evening.glb':('tools/build_v4_sky.py','sky backdrop; textured dome, no opaque surface normal required'),
 'Assets/Art/environment/sky_night.glb':('tools/build_v4_sky.py','sky backdrop; textured dome, no opaque surface normal required'),
 'Assets/Art/court3d/scrum_backdrop.glb':('Game/tools/v4-gpu-trial.mjs','authored patterned courtroom backdrop; existing dots/stripes textures retained'),
 'Assets/Art/armament_v4/hall.glb':('tools/build_v4_armament_hall.py','newly authored separate vaulted rhythm hall; existing geometry/intentional stage palette retained')}
rows=[];files=sorted((R/'Game/Assets/Art').rglob('*.glb'));unowned=[]
for file in files:
    runtime=file.relative_to(R/'Game').as_posix();j,b=read(file);raw=file.read_bytes();sha=digest(raw)
    if runtime in known:assert sha==known[runtime]['sha256'],(runtime,'generated copy differs from checked source');owner=known[runtime]
    elif runtime in special:owner={'source':special[runtime][0],'owner':'existing special renderer asset','retentionReason':special[runtime][1]}
    else:unowned.append(runtime);continue
    triangles=0;textureMaterials=0;normalMaterials=0
    for mesh in j.get('meshes',[]):
        for p in mesh['primitives']:
            for attribute,index in p['attributes'].items():assert np.isfinite(array(j,b,index)).all(),(runtime,attribute)
            pos=array(j,b,p['attributes']['POSITION']);ix=array(j,b,p['indices']).reshape(-1);assert ix.max()<len(pos);triangles+=len(ix)//3
    for m in j.get('materials',[]):
        textureMaterials+=int('baseColorTexture'in m.get('pbrMetallicRoughness',{}));normalMaterials+=int('normalTexture'in m)
    assert triangles>0 and len(raw)<64*1024*1024
    rows.append({'runtime':runtime,'sha256':sha,'bytes':len(raw),'triangles':triangles,'texturedMaterials':textureMaterials,'normalMappedMaterials':normalMaterials,**owner})
assert not unowned,unowned;assert len(rows)==len(known)+len(special)==72
refs=[]
for file in (R/'Game/Assets/Scenes').glob('*.json'):
    for obj in json.loads(file.read_text(encoding='utf8')).get('objects',[]):
        for c in obj.get('components',[]):
            if c['type']!='MeshRenderer':continue
            mesh=c.get('properties',{}).get('mesh','')
            if mesh:assert mesh in known or mesh in special,(file.name,obj['id'],mesh)
            refs.append({'scene':file.name,'object':obj['id'],'mesh':mesh or'dynamic room mesh selected from world data'})
out={'ok':True,'models':len(rows),'rebuiltCommon':61,'rebuiltLateSets':6,'retainedSpecialAssets':5,'sceneMeshRenderers':len(refs),'rows':rows,'sceneReferences':refs,'scope':'Complete currently generated GLB inventory and scene reference ownership/finite geometry checks. Counts are coverage, not visual or behavior completion. Native room review is separate.'}
(W/'whole-3d-inventory.json').write_text(json.dumps(out,indent=2)+'\n');print('WHOLE_3D_INVENTORY',len(rows),'REBUILT',len(known),'SPECIAL',len(special))
