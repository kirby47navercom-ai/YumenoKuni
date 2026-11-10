"""Validate late room geometry, materials, and the authored state object contract."""
from pathlib import Path
import sys,json,re,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from v4_lowpoly_glb import read,array,digest
from compile_v4_rebuilt_environment import matrices
O=R/'art/space_v4/rebuilt_dedicated_v2';raw=(O/'manifest.json').read_bytes();m=json.loads(raw)
old=json.loads((R/'art/space_v4/dedicated_v1/manifest.json').read_text(encoding='utf8'));oldrows={r['id']:r for r in old['spaces']};rows=[]
prefixes=['can_0_','can_1_','can_2_','can_metal_rim','soft_throw_ball','toy_goldfish_','toy_eye','toy_display_mount','toy_car_','plain_closed_game_box','blank_drawing_mount','folded_shared_towel','current_side_door_hinge','garden_glass_door_hinge']
for a in m['assets']:
    file=R/a['file'];j,b=read(file);assert digest(file.read_bytes())==a['sha256']and file.stat().st_size<64*1024*1024
    assert a['nodeGraphPreserved']and a['imageProof']['sceneGeometryMaterialsSamplersUnchanged']and all(p['exactPixels']for p in a['imageProof']['textures'])
    tris=0;textured=set();normals=set()
    for mesh in j['meshes']:
        for p in mesh['primitives']:
            xyz=array(j,b,p['attributes']['POSITION']);n=array(j,b,p['attributes']['NORMAL']);uv=array(j,b,p['attributes']['TEXCOORD_0']);ix=array(j,b,p['indices']).reshape(-1,3)
            assert np.isfinite(xyz).all()and np.isfinite(n).all()and np.isfinite(uv).all();assert np.allclose(np.linalg.norm(n,axis=1),1,atol=.001)
            area=np.linalg.norm(np.cross(xyz[ix[:,1]]-xyz[ix[:,0]],xyz[ix[:,2]]-xyz[ix[:,0]]),axis=1);assert (area>1e-12).all(),(file,mesh['name']);tris+=len(ix)
            mat=j['materials'][p['material']]
            if 'baseColorTexture'in mat.get('pbrMetallicRoughness',{}):textured.add(p['material'])
            if 'normalTexture'in mat:normals.add(p['material'])
    renderedTriangles=sum(len(array(j,b,p['indices']))//3 for n in j['nodes']if'mesh'in n for p in j['meshes'][n['mesh']]['primitives'])
    assert renderedTriangles==a['triangles']and len(textured)>=4 and len(normals)>=4
    orig,_=read(R/oldrows[file.stem]['file']);oldworld=matrices(orig);world=matrices(j);byname={n.get('name'):i for i,n in enumerate(j['nodes'])};protected=[]
    for i,node in enumerate(orig['nodes']):
        name=node.get('name','')
        if not any(name.startswith(p)for p in prefixes):continue
        assert name in byname and np.allclose(oldworld[i],world[byname[name]],atol=1e-5),(file,name,'state placement changed');protected.append(name)
    assert all(s.get('minFilter')==9987 for s in j.get('samplers',[]))
    rows.append({'runtime':a['runtime'],'sha256':a['sha256'],'triangles':tris,'texturedMaterials':len(textured),'normalMappedMaterials':len(normals),'protectedNamedStateObjects':protected})
assert len(rows)==6
result={'ok':True,'manifestSHA256':digest(raw),'rows':rows,'worldMetadataChanged':False,'originalSourcePreserved':True,'scope':'Actual decoded geometry/PBR and original named state world-transform comparison; native visual checks remain separate.'}
(O/'static-verification.json').write_text(json.dumps(result,indent=2)+'\n');print('DEDICATED_STATIC_PASS',len(rows),sum(r['triangles']for r in rows))
