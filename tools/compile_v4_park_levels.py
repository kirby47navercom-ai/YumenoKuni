"""Compile the authored park meshes with the existing lossless static packer."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import compile_v4_rebuilt_environment as C
O=R/'art/space_v4/park_levels_v1';C.O=O;(O/'models').mkdir(exist_ok=True)
raw=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'));p=json.loads((O/'plan.json').read_text(encoding='utf8'))
old=json.loads((O/'manifest.json').read_text(encoding='utf8'))if(O/'manifest.json').exists()else{}
cache={a['id']:a for a in old.get('assets',[])if a.get('paletteVersion')==3};assets=[]
palette={name:[*color,1]for name,color in {'park_cream':[1,.87,.67],'park_red':[.68,.045,.09],'park_blue':[.08,.22,.47],'park_violet':[.27,.09,.40],'park_enamel':[.65,.79,.86],'park_brick':[.48,.16,.09],'park_ink':[.08,.07,.11],'park_gold':[.85,.57,.21],'park_teal':[.06,.38,.36]}.items()}

def texture_references(value):
    if isinstance(value,dict):
        for key,child in value.items():
            if key=='extras':continue
            if key.endswith('Texture') and isinstance(child,dict) and 'index' in child:
                yield key,child
            else:
                yield from texture_references(child)
    elif isinstance(value,list):
        for child in value:
            yield from texture_references(child)

def compact_runtime_textures(asset):
    file=R/asset['file']
    document,binary=C.read(file)
    textures=document['textures']
    references=list(texture_references(document['materials']))
    usages=[set() for _ in textures]
    for channel,reference in references:usages[reference['index']].add(channel)
    # glTF color and data textures can have different decoding even with the
    # same sampler and image. Preserve distinct channel usage when sharing.
    signatures=[(json.dumps(texture,sort_keys=True,separators=(',',':')),frozenset(usage))
                for texture,usage in zip(textures,usages)]
    compact=[];indices={};remap=[]
    for texture,signature,usage in zip(textures,signatures,usages):
        if not usage:
            remap.append(None)
            continue
        if signature not in indices:
            indices[signature]=len(compact)
            compact.append(texture)
        remap.append(indices[signature])
    for _,reference in references:
        original=reference['index']
        reference['index']=remap[original]
        assert compact[reference['index']]==textures[original]
    document['textures']=compact
    previous=asset['sha256']
    if len(compact)!=len(textures):
        temporary=file.with_name(file.name+'.compact.tmp')
        data=C.write(temporary,document,binary)
        after,after_binary=C.read(temporary)
        assert after==document and after_binary==binary
        temporary.replace(file)
        asset.update(sha256=C.digest(data),bytes=len(data))
    asset['runtimeTextureDedup']={'before':len(textures),'after':len(compact),'sourcePackedSHA256':previous,
                                  'binarySHA256':C.digest(binary),'exactReferences':True}
    print('PARK_TEXTURE_REFERENCES',file.name,len(textures),len(compact),flush=True)

for row in raw['levels']:
    a=cache.get(row['id']);source=R/row['raw']['file']
    if not(a and a['sourceSHA256']==C.digest(source.read_bytes())and(R/a['file']).exists()and a['sha256']==C.digest((R/a['file']).read_bytes())):a=C.compile(row['raw'],material_tints=palette,material_albedo_source='park_cream',material_pbr_overrides={'park_gold':{'metallicFactor':.35,'roughnessFactor':.42}})
    a['paletteVersion']=3
    if not a.get('runtimeTextureDedup'):compact_runtime_textures(a)
    a.update({k:row[k]for k in ['id','collision','walkSurfaces','placedFacilities','bounds','landmarks']});assert a['bytes']<64*1024*1024;assets.append(a)
result={'geometryComplete':{a['id']for a in assets}=={d['id']for d in p['districts']},'runtimeVerified':False,'source':'art/space_v4/park_levels_v1/parks-authoring.blend','assets':assets}
temporary=O/'manifest.texture-compile.tmp'
temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
temporary.replace(O/'manifest.json')
print('PARK_LEVEL_BANK',len(assets),result['geometryComplete'],flush=True)
