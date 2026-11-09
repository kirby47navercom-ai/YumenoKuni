"""Pack unchanged generated panoramas into an inward, unlit game skydome."""
from pathlib import Path
import hashlib,json,math,struct,shutil,sys
R=Path(__file__).resolve().parents[1];O=R/'art/environment_v4';O.mkdir(exist_ok=True)
SOURCE=Path('C:/Users/kirby/.codex/generated_images/01a173a2-a942-7360-924c-2c61eb0d9924')
FILES={'day':'exec-7ed6bf72-70c0-43c0-947a-a11de5d883e6.png','night':'exec-a74a4149-fd31-4404-af2f-209c1cfef994.png','evening':'exec-7313d87c-89a6-4e39-9044-11277aec1ece.png'}
PROMPTS={
 'day':'Seamless360 equirectangular2:1 natural blue daytime sky; visible sun22degrees above front-centre horizon, substantial white cumulus/cloud undersides and cirrus; horizon halfway; lower atmospheric fill; no ground/buildings/people/text/UI/lens flare.',
 'night':'Seamless360 equirectangular2:1 navy night sky; hundreds of fine varied stars, delicate blue-grey clouds and detailed waxing gibbous moon22degrees above front-centre horizon, restrained halo; horizon halfway; no ground/buildings/people/text/UI.',
 'evening':'Seamless360 equirectangular2:1 sunset sky; visible golden sun12degrees above front-centre horizon, layered peach/gold clouds with blue-grey undersides and blue-violet upper sky; horizon halfway; no ground/scenery/people/text/UI/lens flare.'}
config=R/'art/environment_v5/source.json'
if config.exists():
 cfg=json.loads(config.read_text(encoding='utf8'));O=R/cfg['output'];SOURCE=R/cfg['source'];FILES=cfg['files'];PROMPTS=cfg['prompts'];O.mkdir(exist_ok=True)
positions=[];uv=[];indices=[];W=96;H=48
for y in range(H+1):
 v=y/H;e=(.5-v)*math.pi
 for x in range(W+1):
  u=x/W;a=(u-.5)*math.tau;positions.extend([-math.cos(e)*math.sin(a),math.sin(e),-math.cos(e)*math.cos(a)]);uv.extend([u,min(1,max(0,.5+(v-.5)*1.35))])
for y in range(H):
 for x in range(W):
  a=y*(W+1)+x;b=a+W+1;indices.extend([a,b,a+1,a+1,b,b+1])
def packed(values,code):return struct.pack('<'+code*len(values),*values)
def align(b):return b+b'\0'*((-len(b))%4)
manifest={'generator':'built-in image_gen','projection':'Own360 equirectangular environment; unchanged PNG embedded in an inward unlit sphere; front is native camera -Z; vertical UV fit1.35 for ground-level celestial visibility. Not original V3 art.','phases':{}}
for phase,name in FILES.items():
 src=SOURCE/name;target=O/(phase+'.png')
 if src.resolve()!=target.resolve():shutil.copyfile(src,target)
 image=target.read_bytes();assert image[:8]==b'\x89PNG\r\n\x1a\n';width,height=struct.unpack_from('>II',image,16);assert width==height*2
 chunks=[packed(positions,'f'),packed(uv,'f'),packed(indices,'I'),image];blob=b'';views=[]
 for i,chunk in enumerate(chunks):views.append({'buffer':0,'byteOffset':len(blob),'byteLength':len(chunk),**({'target':34963 if i==2 else 34962} if i<3 else {})});blob+=align(chunk)
 gltf={'asset':{'version':'2.0','generator':'YumenoKuni sky packer'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':'SkyPanorama'}],'meshes':[{'primitives':[{'attributes':{'POSITION':0,'TEXCOORD_0':1},'indices':2,'material':0}]}],'materials':[{'name':'sky_'+phase,'doubleSided':True,'extensions':{'KHR_materials_unlit':{}},'pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':1}}],'extensionsUsed':['KHR_materials_unlit'],'textures':[{'source':0,'sampler':0}],'samplers':[{'wrapS':10497,'wrapT':33071,'magFilter':9729,'minFilter':9987}],'images':[{'bufferView':3,'mimeType':'image/png'}],'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':[{'bufferView':0,'componentType':5126,'count':len(positions)//3,'type':'VEC3','min':[-1,-1,-1],'max':[1,1,1]},{'bufferView':1,'componentType':5126,'count':len(uv)//2,'type':'VEC2'},{'bufferView':2,'componentType':5125,'count':len(indices),'type':'SCALAR'}]}
 exposure=cfg.get('displayExposure',{}).get(phase,1)if config.exists()else 1;gltf['materials'][0]['pbrMetallicRoughness']['baseColorFactor']=[exposure,exposure,exposure,1]
 j=json.dumps(gltf,separators=(',',':')).encode();j+=b' '*((-len(j))%4);data=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob
 file=O/('sky_'+phase+'.glb');file.write_bytes(data);manifest['phases'][phase]={'png':target.relative_to(R).as_posix(),'size':[width,height],'png_sha256':hashlib.sha256(image).hexdigest(),'mesh':file.relative_to(R).as_posix(),'mesh_sha256':hashlib.sha256(data).hexdigest(),'prompt':PROMPTS[phase],'source_output':str(src)}
if '--publish' in sys.argv:
 runtime=R/'Game/Assets/Art/environment';runtime.mkdir(parents=True,exist_ok=True)
 for phase in FILES:shutil.copyfile(O/('sky_'+phase+'.glb'),runtime/('sky_'+phase+'.glb'))
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if config.exists()and cfg.get('discBoxes'):
 import numpy as np
 from PIL import Image
 alignment={}
 for phase,(l,t,r,b)in cfg['discBoxes'].items():
  file=O/(phase+'.png');pixels=np.asarray(Image.open(file).convert('RGB'));a=pixels[t:b,l:r].astype(float);luma=a.mean(axis=2);yy,xx=np.where(luma>=luma.max()-5);assert len(xx)>0
  x=float(xx.mean()+l);y=float(yy.mean()+t);h,w=pixels.shape[:2];az=(x/w-.5)*math.tau;el=(.5-(.5+(y/h-.5)/1.35))*math.pi;direction=[-math.cos(el)*math.sin(az),math.sin(el),-math.cos(el)*math.cos(az)];dx,dy,dz=direction
  alignment[phase]={'image':file.relative_to(R).as_posix(),'sourceSHA256':hashlib.sha256(file.read_bytes()).hexdigest(),'discPixel':[x,y],'direction':direction,'rotationDegrees':[math.degrees(math.atan2(-dy,dz)),math.degrees(math.asin(dx)),0],'elevationDegrees':math.degrees(el),'projectionVerticalFit':1.35,'meanLuma':float(pixels.mean()),'horizontalEdgeMeanDifference':float(np.abs(pixels[:,0].astype(float)-pixels[:,-1].astype(float)).mean())}
 (O/'celestial-alignment.json').write_text(json.dumps(alignment,indent=2)+'\n',encoding='utf8')
print(json.dumps({'phases':list(FILES),'mesh_vertices':len(positions)//3,'triangles':len(indices)//3,'original_PNGs_unchanged':True}))
