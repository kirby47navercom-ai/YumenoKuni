"""Validate GLB buffers/geometry and authored camera-mode contracts, without running the game."""
from pathlib import Path
import struct,json,hashlib,math,os
import numpy as np

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/os.environ.get('V4_SPACE_OUT','art/space_v4')
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf8'))
reports=[]
types={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
assemblies=[{'id':p.stem,'file':p.relative_to(ROOT).as_posix()} for name in ('park_exterior.glb','park_exterior_r2.glb') if (p:=OUT/name).exists()]
art_manifest=OUT/'interior_art_r3/manifest.json'
art_variants=json.loads(art_manifest.read_text(encoding='utf8'))['spaces'] if art_manifest.exists() else []
finish_manifest=OUT/'interior_art_r4/manifest.json'
if finish_manifest.exists():art_variants+=json.loads(finish_manifest.read_text(encoding='utf8'))['spaces']
for record in manifest['models']+manifest['spaces']+assemblies+art_variants:
    p=ROOT/record['file'];data=p.read_bytes();magic,version,length=struct.unpack_from('<4sII',data)
    assert magic==b'glTF' and version==2 and length==len(data),record['id']
    offset=12;doc=None;binary=b''
    while offset<len(data):
        size,kind=struct.unpack_from('<II',data,offset);chunk=data[offset+8:offset+8+size];assert len(chunk)==size
        if kind==0x4E4F534A:doc=json.loads(chunk)
        elif kind==0x004E4942:binary=chunk
        offset+=8+size
    assert doc and doc.get('meshes'),record['id']
    for view in doc.get('bufferViews',[]):assert view.get('byteOffset',0)+view['byteLength']<=len(binary)
    def accessor(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];dtype=np.dtype(types[a['componentType']]);n=widths[a['type']];start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',dtype.itemsize*n)
        assert start+(a['count']-1)*stride+n*dtype.itemsize<=v.get('byteOffset',0)+v['byteLength']
        arr=np.ndarray((a['count'],n),dtype=dtype,buffer=binary,offset=start,strides=(stride,dtype.itemsize))
        assert np.isfinite(arr).all();return arr
    triangles=0;textured=0
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            pos=accessor(prim['attributes']['POSITION']);assert pos.shape[1]==3
            material=doc.get('materials',[])[prim['material']] if 'material' in prim else {}
            texture=material.get('pbrMetallicRoughness',{}).get('baseColorTexture')
            if texture is not None:
                uv=accessor(prim['attributes']['TEXCOORD_'+str(texture.get('texCoord',0))]);assert len(uv)==len(pos)
                image=doc['images'][doc['textures'][texture['index']]['source']]
                assert 'bufferView' in image and doc['bufferViews'][image['bufferView']]['byteLength']>0
                textured+=1
            if 'indices' in prim:
                idx=accessor(prim['indices']);assert int(idx.max())<len(pos)
                if prim.get('mode',4)==4:assert idx.size%3==0;triangles+=idx.size//3
    parents={}
    for i,node in enumerate(doc.get('nodes',[])):
        for child in node.get('children',[]):assert child<len(doc['nodes']) and child not in parents;parents[child]=i
    for i in range(len(doc.get('nodes',[]))):
        seen=set();j=i
        while j in parents:assert j not in seen;seen.add(j);j=parents[j]
    reports.append({'id':record['id'],'file':record['file'],'sha256':hashlib.sha256(data).hexdigest(),'nodes':len(doc.get('nodes',[])),'meshes':len(doc['meshes']),'triangles':triangles,'textured_primitives_with_valid_uv_and_embedded_image':textured,'bytes':len(data),'buffer_bounds':'PASS','finite_geometry':'PASS','index_bounds':'PASS','node_tree':'PASS'})

contracts=[]
for s in manifest['spaces']:
    c=s['camera'];mode=s['mode']
    if mode=='free_walk':assert c['manual_translation'] is True
    if mode in ('fixed_orbit','fixed_pan'):
        assert c['manual_translation'] is False and c['radius']>0
        assert c['pitch_limits_degrees'][0]<c['pitch_limits_degrees'][1]
        if mode=='fixed_pan':assert len(c['eye_blender'])==3 and c['rotation']=='yaw_pitch_about_fixed_eye'
    contracts.append({'space':s['id'],'control_mode':mode,'model':s['file'],'camera':c,'coordinate_contract':'Blender source (x,y,z) -> standard glTF (x,z,-y)','evidence':'own authored geometry, adapted from V3 mode 1/0 consumption in docs/spec/18_V3_분석/01_탐색.md','not_claimed':'original V3 map mode assignment or completed game integration'})
(OUT/'space_contracts.json').write_text(json.dumps({'source':'authored game-space candidates','spaces':contracts},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(OUT/'qa.json').write_text(json.dumps({'status':'PASS: GLB structural/geometry checks and camera contract checks','model_count':len(manifest['models']),'space_count':len(manifest['spaces']),'assembly_versions_checked':len(assemblies),'interior_visual_variants_checked':len(art_variants),'runtime_integration':'NOT RUN','visual_review':'selected cutaway and inside-camera Blender renders inspected; not a game runtime capture','files':reports},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS',len(reports),'GLB files including',len(assemblies),'assembly versions and',len(art_variants),'interior visual variants;',len(contracts),'explicit space camera contracts')
