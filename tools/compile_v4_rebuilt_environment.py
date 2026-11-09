"""Compact static runtime chunks with exact image pixels and shared PBR surfaces.

Transforms bake once into vertices; each chunk has one primitive per material.
Individual moving podiums remain separate engine scene instances, never fused.
"""
import sys,json,copy,hashlib,io,struct,re
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from v4_lowpoly_glb import read,write,array,Copier,digest,material_key
from optimize_native_glb import encode_png
O=R/'art/space_v4/rebuild_v1';(O/'models').mkdir(exist_ok=True)

def matrices(j):
    parents={c:i for i,n in enumerate(j['nodes'])for c in n.get('children',[])};world={}
    def get(i):
        if i in world:return world[i]
        n=j['nodes'][i]
        if 'matrix'in n:m=np.array(n['matrix'],dtype=np.float64).reshape(4,4,order='F')
        else:
            x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4);m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
        world[i]=get(parents[i])@m if i in parents else m;return world[i]
    return[get(i)for i in range(len(j['nodes']))]

def compile(row,omit_mesh_nodes=(),material_tints=None,material_albedo_source=None,material_pbr_overrides=None):
    source=R/row['file'];j,b=read(source);assert not j.get('animations')and not j.get('skins')
    for i in omit_mesh_nodes:j['nodes'][i].pop('mesh',None)
    albedo_source=next((m.get('pbrMetallicRoughness',{}).get('baseColorTexture')for m in j.get('materials',[])if re.sub(r'\.\d+$','',m.get('name',''))==material_albedo_source),None)if material_albedo_source else None
    for m in j.get('materials',[]):
        tint=m.get('extras',{}).get('surfaceTint')
        if tint:m.setdefault('pbrMetallicRoughness',{})['baseColorFactor']=tint
        if 'rebuilt_foliage' in m.get('name',''):m['alphaMode']='MASK';m['alphaCutoff']=.5;m['doubleSided']=True
        # Blender's glTF exporter does not retain the constant MixRGB tint.
        # Keep the authored painted-metal palette explicitly in the owning compiler.
        name=re.sub(r'\.\d+$','',m.get('name',''))
        if material_tints and name in material_tints:m.setdefault('pbrMetallicRoughness',{})['baseColorFactor']=material_tints[name]
        if albedo_source and material_tints and name in material_tints and name not in ['park_gold','park_ink']:m.setdefault('pbrMetallicRoughness',{})['baseColorTexture']=copy.deepcopy(albedo_source)
        if material_pbr_overrides and name in material_pbr_overrides:
            m.setdefault('pbrMetallicRoughness',{}).update(copy.deepcopy(material_pbr_overrides[name]))
            if albedo_source and name=='park_gold':m['pbrMetallicRoughness']['baseColorTexture']=copy.deepcopy(albedo_source)
        if name=='form_display_glass':m.update(alphaMode='BLEND',doubleSided=True);m.setdefault('pbrMetallicRoughness',{}).update(baseColorFactor=[.45,.67,.71,.20],metallicFactor=0,roughnessFactor=.18)
        # Fully metallic panes appeared black under the native indoor lighting.
        # Retain a diffuse silver contribution for readable stylized mirrors.
        if name=='rebuilt_mirror':m.setdefault('pbrMetallicRoughness',{}).update(baseColorFactor=[.80,.86,.91,1],metallicFactor=.65,roughnessFactor=.06)
        if name in ['rebuilt_cabin_clear_glass','rebuilt_ticket_clear_glass']:m.update(alphaMode='BLEND',doubleSided=True);m.setdefault('pbrMetallicRoughness',{}).update(baseColorFactor=[.70,.85,.92,.12],metallicFactor=0,roughnessFactor=.10)
        if name in ['architecture6_laundry_clear_glass','architecture6_archive_clear_glass','architecture6_exhibit_clear_glass','architecture6_reading_clear_glass','architecture6_waiting_clear_glass','architecture6_prize_clear_glass']:m.update(alphaMode='BLEND',doubleSided=True);m.setdefault('pbrMetallicRoughness',{}).update(baseColorFactor=[.70,.85,.92,.12],metallicFactor=0,roughnessFactor=.10)
        for key,color in [('rebuilt_iron',[.05,.06,.08,1]),('rebuilt_brass',[.55,.35,.12,1]),('rebuilt_wood',[.8,.8,.8,1])]:
            if name==key:m.setdefault('pbrMetallicRoughness',{})['baseColorFactor']=color
    c=Copier(j);c.j['nodes']=[];c.j['meshes']=[];c.j['scenes']=[{'nodes':[0]}];c.j['scene']=0
    groups={};source_triangles=0;world=matrices(j);metadata=[]
    for ni,n in enumerate(j['nodes']):
        if n.get('extras'):metadata.append({'name':n.get('name'),**n['extras']})
        if 'mesh'not in n:continue
        mat=world[ni];basis=mat[:3,:3];normal_basis=np.linalg.inv(basis).T;negative=np.linalg.det(basis)<0
        for p in j['meshes'][n['mesh']]['primitives']:
            assert p.get('mode',4)==4
            pos=array(j,b,p['attributes']['POSITION']).astype(np.float64);indices=array(j,b,p['indices']).reshape(-1).astype(np.uint32);source_triangles+=len(indices)//3
            attrs={'POSITION':(pos@basis.T+mat[:3,3]).astype('<f4')}
            norm=array(j,b,p['attributes']['NORMAL']).astype(np.float64)@normal_basis.T;norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-20);attrs['NORMAL']=norm.astype('<f4')
            attrs['TEXCOORD_0']=array(j,b,p['attributes']['TEXCOORD_0']).astype('<f4')
            if 'TANGENT'in p['attributes']:
                tan=array(j,b,p['attributes']['TANGENT']).astype(np.float64).copy();tan[:,:3]=tan[:,:3]@basis.T;tan[:,:3]-=norm*np.sum(norm*tan[:,:3],axis=1,keepdims=True);tan[:,:3]/=np.maximum(np.linalg.norm(tan[:,:3],axis=1,keepdims=True),1e-20);tan[:,3]*=-1 if negative else 1;attrs['TANGENT']=tan.astype('<f4')
            if negative:indices=indices.reshape(-1,3)[:,[0,2,1]].copy().reshape(-1)
            assert all(np.isfinite(v).all()for v in attrs.values())
            mi=c.copy(j,b,'materials',p['material'],'source');key=(mi,tuple(sorted(attrs)))
            g=groups.setdefault(key,{'attributes':{k:[]for k in attrs},'indices':[],'count':0});g['indices'].append(indices+g['count']);g['count']+=len(pos)
            for k,v in attrs.items():g['attributes'][k].append(v)
    # Every referenced image is compressed losslessly and checked pixel for pixel.
    image_proofs=[]
    for ii,im in enumerate(c.j['images']):
        view=c.j['bufferViews'][im['bufferView']];off=view.get('byteOffset',0);raw=bytes(c.b[off:off+view['byteLength']])
        if im.get('mimeType')!='image/png':continue
        encoded,proof=encode_png(raw)
        if len(encoded)>=len(raw):continue
        c.b.extend(b'\0'*(-len(c.b)%4));im['bufferView']=len(c.j['bufferViews']);c.j['bufferViews'].append({'buffer':0,'byteOffset':len(c.b),'byteLength':len(encoded)});c.b.extend(encoded);im['mimeType']='image/webp';image_proofs.append(proof)
        for t in c.j['textures']:
            if t.get('source')==ii:t.setdefault('extensions',{})['EXT_texture_webp']={'source':t.pop('source')}
    if image_proofs:
        for k in ['extensionsUsed','extensionsRequired']:
            if 'EXT_texture_webp'not in c.j.setdefault(k,[]):c.j[k].append('EXT_texture_webp')
    # Imported materials and newly authored meshes can refer to the same master
    # through differently encoded PNG/WebP wrappers. Deduplicate decoded pixels,
    # not filenames or compressed-byte hashes; retain every original pixel.
    unique=[];seen={};remap={};duplicate_images=0
    for ii,im in enumerate(c.j['images']):
        v=c.j['bufferViews'][im['bufferView']];off=v.get('byteOffset',0);raw=bytes(c.b[off:off+v['byteLength']]);image=Image.open(io.BytesIO(raw)).convert('RGBA');key=(image.size,digest(image.tobytes()))
        if key not in seen:seen[key]=len(unique);unique.append(im)
        else:duplicate_images+=1
        remap[ii]=seen[key]
    c.j['images']=unique
    for t in c.j['textures']:
        if 'source'in t:t['source']=remap[t['source']]
        for ex in t.get('extensions',{}).values():
            if 'source'in ex:ex['source']=remap[ex['source']]
    for s in c.j['samplers']:s.update({'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497})
    for m in c.j['materials']:
        if not m.get('name','').startswith('identity_'):continue
        tex=m.get('pbrMetallicRoughness',{}).get('baseColorTexture')
        if not tex or m['name'].startswith('identity_wall_'):continue
        sampler={'magFilter':9728,'minFilter':9728,'wrapS':33071,'wrapT':33071}if re.sub(r'\.\d+$','',m['name'])=='identity_room_face'else{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}
        si=len(c.j['samplers']);c.j['samplers'].append(sampler)
        for channel in [tex,m.get('emissiveTexture')]:
            if channel:c.j['textures'][channel['index']]['sampler']=si
    # Reopened Blender sources contain separately named copies of identical
    # materials. Merge only exact optical/texture/sampler equivalents, so later
    # architectural passes do not add a draw call merely for a .001 suffix.
    before_material_groups=len(groups);unique_materials=[];material_seen={};material_remap={}
    for mi,m in enumerate(c.j['materials']):
        signature=json.dumps(material_key(c.j,bytes(c.b),mi),sort_keys=True)
        if signature not in material_seen:material_seen[signature]=len(unique_materials);unique_materials.append(m)
        material_remap[mi]=material_seen[signature]
    merged={}
    for (mi,attributes),g in groups.items():
        key=(material_remap[mi],attributes);dest=merged.setdefault(key,{'attributes':{k:[]for k in g['attributes']},'indices':[],'count':0})
        for k,values in g['attributes'].items():dest['attributes'][k].extend(values)
        dest['indices'].extend(v+dest['count']for v in g['indices']);dest['count']+=g['count']
    groups=merged;c.j['materials']=unique_materials
    # Repack just the live image views to remove the replaced PNG bytes.
    oldb=bytes(c.b);oldviews=c.j['bufferViews'];c.b=bytearray();c.j['bufferViews']=[]
    for im in c.j['images']:
        v=oldviews[im['bufferView']];off=v.get('byteOffset',0);data=oldb[off:off+v['byteLength']];c.b.extend(b'\0'*(-len(c.b)%4));im['bufferView']=len(c.j['bufferViews']);c.j['bufferViews'].append({'buffer':0,'byteOffset':len(c.b),'byteLength':len(data)});c.b.extend(data)
    def accessor(values,kind):
        values=np.ascontiguousarray(values);data=values.tobytes();c.b.extend(b'\0'*(-len(c.b)%4));vi=len(c.j['bufferViews']);c.j['bufferViews'].append({'buffer':0,'byteOffset':len(c.b),'byteLength':len(data)});c.b.extend(data)
        a={'bufferView':vi,'componentType':5125 if values.dtype==np.dtype('uint32')else 5126,'count':len(values),'type':kind}
        if kind=='VEC3':a['min']=values.min(axis=0).tolist();a['max']=values.max(axis=0).tolist()
        ai=len(c.j['accessors']);c.j['accessors'].append(a);return ai
    primitives=[];triangles=0
    for (mi,_),g in groups.items():
        attrs={k:np.concatenate(v)for k,v in g['attributes'].items()};indices=np.concatenate(g['indices']).astype('<u4');triangles+=len(indices)//3
        p={'attributes':{k:accessor(v,{2:'VEC2',3:'VEC3',4:'VEC4'}[v.shape[1]])for k,v in attrs.items()},'indices':accessor(indices,'SCALAR'),'material':mi};primitives.append(p)
    assert triangles==source_triangles
    c.j['meshes']=[{'name':'Rebuilt_'+Path(row['runtime']).stem,'primitives':primitives}];c.j['nodes']=[{'name':'Rebuilt_'+Path(row['runtime']).stem,'mesh':0,'extras':{'sourcePivots':metadata,'staticChunkOnly':True}}]
    file=O/'models'/Path(row['file']).name;data=write(file,c.j,bytes(c.b));out={'file':file.relative_to(R).as_posix(),'runtime':row['runtime'],'sha256':digest(data),'bytes':len(data),'triangles':triangles,'materialPrimitives':len(primitives),'source':row['file'],'sourceSHA256':digest(source.read_bytes()),'losslessImageProofs':image_proofs,'duplicateDecodedImagesRemoved':duplicate_images,'staticGeometryTransformBake':True,'sourceNodes':len(j['nodes']),**{k:v for k,v in row.items()if k not in ['file','runtime','triangles','source']}}
    out['materialGroupsBeforeOpticalDedup']=before_material_groups;out['exactOpticalMaterialDedup']=True
    print('REBUILT_PACKED',Path(file).name,triangles,len(primitives),len(data),flush=True);return out

def main():
    rows=json.loads((O/'exterior-assembly.json').read_text())['assets']+json.loads((O/'room-assembly.json').read_text())['assets'];cached={a['runtime']:a for a in json.loads((O/'manifest.json').read_text())['assets']}if '--changed-only'in sys.argv and (O/'manifest.json').exists()else{}
    assets=[]
    forced=next((set(s.split('=',1)[1].split(','))for s in sys.argv if s.startswith('--recompile=')),set())
    for row in rows:
        old=cached.get(row['runtime'])if Path(row['runtime']).stem not in forced else None
        if old and old['sourceSHA256']==digest((R/row['file']).read_bytes())and (R/old['file']).exists()and old['sha256']==digest((R/old['file']).read_bytes()):assets.append(old)
        else:assets.append(compile(row))
    expected={a['runtime']for a in json.loads((R/'art/space_v4/materials_v2/manifest.json').read_text(encoding='utf8'))['assets']};assert{a['runtime']for a in assets}==expected;assert len(assets)==61
    result={'completeEnvironmentAssembly':True,'runtimeVerified':False,'scope':'All 61 current runtime 3D chunks, rebuilt prefab bodies, all 31 facades, 22 trees, ride/gate/pool/court recipes, baked wall trim. Runtime acceptance separate.','sourceMaterialManifestSHA256':digest((R/'art/space_v4/materials_v2/manifest.json').read_bytes()),'assets':assets}
    exterior=json.loads((O/'exterior-assembly.json').read_text())
    if exterior.get('facilityArchitectureVersion',0)>=2:
        result['facilityArchitectureVersion']=exterior['facilityArchitectureVersion'];result['facilityArchitectureSource']=exterior.get('facilityArchitectureSource','art/space_v4/facility_architecture_v2/manifest.json')
    (O/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('REBUILT_BANK_READY',len(assets),flush=True)
if __name__=='__main__':main()
