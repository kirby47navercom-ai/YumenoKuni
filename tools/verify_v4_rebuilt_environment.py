"""Independent decoded geometry, masks, texture, count and provenance gate."""
import sys,json,hashlib,io
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from v4_lowpoly_glb import read,array,digest
O=R/'art/space_v4/rebuild_v1';raw=(O/'manifest.json').read_bytes();manifest=json.loads(raw);rows=[]
source=json.loads((R/'art/space_v4/materials_v2/manifest.json').read_text(encoding='utf8'))
assert manifest['sourceMaterialManifestSHA256']==digest((R/'art/space_v4/materials_v2/manifest.json').read_bytes())
assert len(manifest['assets'])==len(source['assets'])==61
assert{a['runtime']for a in manifest['assets']}=={a['runtime']for a in source['assets']}
exterior=json.loads((O/'exterior-assembly.json').read_text());assert len(exterior['facades'])==31;assert len(exterior['trees'])==22
prefabs=json.loads((O/'prefab-manifest.json').read_text());assert len(prefabs['assets'])==45
normal=np.asarray(Image.open(O/'maps/panel_geometry_normal.png'));assert normal[:,:,2].min()>127;assert(np.max(abs(normal[:,:,:2].astype(int)-128),axis=2)>4).sum()>10000
for a in manifest['assets']:
    path=R/a['file'];assert path.stat().st_size<64*1024*1024;assert digest(path.read_bytes())==a['sha256'];j,b=read(path);triangles=0;texture_pixels=0
    assert len(j['nodes'])==1 and len(j['meshes'])==1
    for p in j['meshes'][0]['primitives']:
        attrs=p['attributes'];assert{'POSITION','NORMAL','TEXCOORD_0'}<=set(attrs);pos=array(j,b,attrs['POSITION']);norm=array(j,b,attrs['NORMAL']);uv=array(j,b,attrs['TEXCOORD_0']);indices=array(j,b,p['indices']).reshape(-1);assert len(indices)%3==0;assert indices.max()<len(pos);triangles+=len(indices)//3
        assert all(np.isfinite(v).all()for v in [pos,norm,uv]);assert np.max(abs(np.linalg.norm(norm,axis=1)-1))<.002
        v=pos[indices].reshape(-1,3,3).astype(np.float64);area=np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1);assert area.min()>1e-13,(path,area.min())
        m=j['materials'][p['material']]
        if 'rebuilt_foliage'in m.get('name',''):assert m['alphaMode']=='MASK'and m['alphaCutoff']==.5 and m['doubleSided']
    assert triangles==a['triangles']
    if a['runtime'].endswith('/finish_context.glb'):
        # A global ground plane covering the local basin was found in actual QA.
        # Check decoded final triangles, not just a terrain metadata declaration.
        grass=[]
        for p in j['meshes'][0]['primitives']:
            if not j['materials'][p['material']].get('name','').startswith('rebuilt_grass'):continue
            xyz=array(j,b,p['attributes']['POSITION']);idx=array(j,b,p['indices']).reshape(-1,3);grass.append(xyz[idx].astype(np.float64))
        assert grass;g=np.concatenate(grass);project=g[:,:,[0,2]];a0=project[:,0];u=project[:,1]-a0;v=project[:,2]-a0;den=u[:,0]*v[:,1]-u[:,1]*v[:,0];valid=abs(den)>1e-10
        def hits(x,z):
            d=np.array([x,z])-a0;safe=np.where(valid,den,1);s=(d[:,0]*v[:,1]-d[:,1]*v[:,0])/safe;t=(u[:,0]*d[:,1]-u[:,1]*d[:,0])/safe;return bool(np.any(valid&(s>=-1e-7)&(t>=-1e-7)&(s+t<=1+1e-7)))
        for x,z in [(84,-26),(78.2,-23.2),(89.8,-28.8)]:assert not hits(x,z),('grass occludes pool',x,z)
        assert hits(76,-26)and hits(92,-26),'Ground outside pool must remain present'
    seen_images=set()
    for im in j['images']:
        v=j['bufferViews'][im['bufferView']];off=v.get('byteOffset',0);image=Image.open(io.BytesIO(b[off:off+v['byteLength']]));image.load();texture_pixels+=image.width*image.height
        key=(image.size,digest(image.convert('RGBA').tobytes()));assert key not in seen_images,('duplicate runtime texture',path);seen_images.add(key)
    assert all(p['exactPixels']for p in a['losslessImageProofs'])
    rows.append({'runtime':a['runtime'],'triangles':triangles,'bytes':path.stat().st_size,'primitives':len(j['meshes'][0]['primitives']),'embeddedTexturePixels':texture_pixels})
result={'ok':True,'manifestSHA256':digest(raw),'models':len(rows),'facades':31,'trees':22,'prefabFamilies':45,'decodedTriangles':sum(a['triangles']for a in rows),'totalBytes':sum(a['bytes']for a in rows),'maxModelBytes':max(a['bytes']for a in rows),'actualPanelGeometryBake':True,'runtimeVerified':False,'rows':rows}
out=R/'Game/Saved/sculpted-environment-20261103/rebuilt-static-verification.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
