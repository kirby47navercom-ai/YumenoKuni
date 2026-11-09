"""Re-export only the two oversized imported lights; keep the own maze intact."""
import copy,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE='art/space_v4/full_v2/mirror_maze.glb'
SOURCE_SHA='5af39324cab7a2e13ac6e7eb5eb109aabfa9dfa3f6dd06f6ef854c32a30788e9'
FOLDER='art/space_v4/mirror_lighting_v1'

def build():
    raw=(ROOT/SOURCE).read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    size,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
    before=json.loads(raw[20:20+size]);after=copy.deepcopy(before)
    lights=after['extensions']['KHR_lights_punctual']['lights']
    assert len(lights)==2 and all(v['type']=='point'and 8696<v['intensity']<8697 for v in lights)
    old=[v['intensity']for v in lights]
    for light in lights:light['intensity']=20.0
    expected=copy.deepcopy(after)
    for light,intensity in zip(expected['extensions']['KHR_lights_punctual']['lights'],old):light['intensity']=intensity
    assert before==expected
    payload=json.dumps(after,ensure_ascii=False,separators=(',',':')).encode();payload+=b' '*(-len(payload)%4)
    tail=raw[20+size:]
    out=struct.pack('<III',0x46546c67,2,20+len(payload)+len(tail))+struct.pack('<II',len(payload),kind)+payload+tail
    folder=ROOT/FOLDER;folder.mkdir(exist_ok=True);target=folder/'mirror_maze.glb';target.write_bytes(out)
    report={'source':SOURCE,'sourceSHA256':SOURCE_SHA,'file':target.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(out).hexdigest(),
            'builder':'tools/v4_mirror_lighting.py','builderSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'beforeIntensities':old,'afterIntensities':[20,20],'allGeometryMaterialsImagesAndTransformsExact':True,'binaryChunksSHA256':hashlib.sha256(tail).hexdigest(),
            'nativeVerified':False,'scope':'Only two embedded glTF point light intensities. Original own asset untouched; no mesh, material, collision, portal or story change.'}
    (folder/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'derivedMirrorLightAsset':True,'geometryChanged':False,'originalUnchanged':hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest()==SOURCE_SHA}))

def copies(world):
    report=json.loads((ROOT/FOLDER/'manifest.json').read_text(encoding='utf-8'))
    for path,hash_key in [('source','sourceSHA256'),('file','sha256'),('builder','builderSha256')]:
        assert hashlib.sha256((ROOT/report[path]).read_bytes()).hexdigest()==report[hash_key]
    return [{'from':report['file'],'to':world['spaces']['mirror_maze']['mesh']}]

if __name__=='__main__':build()
