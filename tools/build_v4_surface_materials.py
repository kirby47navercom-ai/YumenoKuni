"""Apply generated PBR surfaces to every active environment GLB.

GLB structure patching retains all geometry/index bytes and node identities.
Only declared seat yaw corrections and material/image bindings change. Unused
embedded images are compacted, so a material pass does not append dead textures.
"""
from pathlib import Path
import json,struct,hashlib,io,math,re,copy
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/materials_v2';OUT=O/'models';OUT.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
def write(p,j,b):
 j['buffers']=[{'byteLength':len(b)}];s=json.dumps(j,separators=(',',':')).encode();s+=b' '*(-len(s)%4);b+=b'\0'*(-len(b)%4)
 data=struct.pack('<III',0x46546c67,2,28+len(s)+len(b))+struct.pack('<II',len(s),0x4e4f534a)+s+struct.pack('<II',len(b),0x004e4942)+b
 assert len(data)<64*1024*1024,(p,len(data));p.write_bytes(data);return data
def arr(j,b,index):
 a=j['accessors'][index];v=j['bufferViews'][a['bufferView']];typ={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype=np.dtype(typ)
 return np.ndarray((a['count'],width),dtype=dtype,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*dtype.itemsize),dtype.itemsize))
def rotation(q):
 x,y,z,w=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def seat_corrections(j,room):
 changes=[];nodes=j.get('nodes',[])
 seats=[n for n in nodes if re.search(r'_(chair|park_bench)(\.\d+)?$',n.get('name',''))]
 tables=[n for n in nodes if re.search(r'_meeting_table(\.\d+)?$',n.get('name',''))]
 for n in seats:
  pos=np.array(n.get('translation',[0,0,0]));target=None;why=None
  if '_chair' in n['name']:
   if room in ['performance_stage','screening_room','theatre_preparation','dream_lobby','hotel_multiuse']:
    direction=np.array([0.,-1.]);why='face stage/screen/counter at north of room'
   elif tables:
    t=min(tables,key=lambda t:np.linalg.norm((np.array(t.get('translation',[0,0,0]))-pos)[[0,2]]));target=np.array(t.get('translation',[0,0,0]));delta=(target-pos)[[0,2]]
    # Seat rows remain perpendicular to their table edge, never diagonally aim
    # at the table centre. Project in the table's local X/Z axes.
    axes=rotation(t.get('rotation',[0,0,0,1]))[np.ix_([0,2],[0,2])];local=axes.T@delta;axis=int(np.argmax(np.abs(local)/np.array([1.3,.56])));direction=axes[:,axis]*np.sign(local[axis]);why='face associated table edge'
   else:continue # Ticket clerk already faces counter, not an invented table.
  else:
   direction=-pos[[0,2]];direction=direction/(np.linalg.norm(direction) or 1);why='face room/path centre'
   # Benches lining a straight path keep perpendicular cardinal alignment.
   direction=np.eye(2)[np.argmax(np.abs(direction))]*np.sign(direction[np.argmax(np.abs(direction))])
  direction/=np.linalg.norm(direction);yaw=math.atan2(direction[0],direction[1]);new=[0,math.sin(yaw/2),0,math.cos(yaw/2)];old=n.get('rotation',[0,0,0,1]);forward=rotation(old)@np.array([0.,0.,1.]);before=float(forward[[0,2]]@direction)
  if before<.999:
   n['rotation']=new;changes.append({'node':n['name'],'oldRotation':old,'newRotation':new,'reason':why,'forwardBefore':before,'desiredDirectionXZ':direction.tolist(),'position':pos.tolist()})
 return changes
def family(name,mesh):
 n=re.sub(r'\.\d+$','',name);s=mesh.lower()
 if n in ['material_palette','scrum_dots','scrum_stripes']:return None
 if any(v in n for v in ['glass','mirror','light']):return None
 if 'screen_surface' in s:return 'linen' # Projection cloth, never wall plaster.
 if any(v in s for v in ['blanket','duvet','bed_cover']) and any(v in n for v in ['purple','rose']):return 'velvet'
 if 'leaf' in n or n=='sage':return 'leaf'
 if 'wood' in n:return 'walnut'
 if n in ['sculpt_cloth']:return 'velvet'
 if 'rose' in n:return 'carpet' if any(v in s for v in ['carpet','runner','rug']) else 'velvet'
 if 'paving' in n:return 'paving'
 if 'stone' in n:return 'limestone'
 if 'paper' in n:return 'limestone' if any(v in s for v in ['coping','tile','pavement','sill']) else 'plaster'
 if 'ivory' in n or 'white' in n:
  if any(v in s for v in ['cabinet','counter','washer','locker','sink','trolley','utility']):return 'metal'
  if any(v in s for v in ['sheet','pillow','mattress','curtain','privacy','medical_screen']):return 'linen'
  return 'limestone' if any(v in s for v in ['floor','tile','stone','plinth','pillar','column','fountain','vessel','model_base']) else 'plaster'
 if any(v in n for v in ['steel','iron','brass','gold','ink','purple','blue']):
  if 'purple' in n and any(v in s for v in ['panel','door','wainscot','cabinet']):return 'lacquer'
  if any(v in s for v in ['carpet','runner','rug']):return 'carpet'
  if any(v in s for v in ['floor','path','deck','pavement','platform']) and not any(v in s for v in ['metal','cabin','gate','wheel','car']):return 'paving'
  return 'metal'
 raise AssertionError(('Unclassified material',name,mesh))
def image_bytes(key,kind):
 p=O/('masters' if kind=='color' else 'maps')/(key+'.png' if kind=='color' else key+'_'+kind+'.png');im=Image.open(p).convert('RGB')
 if kind=='roughness':
  # Native glTF reads G for roughness and B for metallic; retain per-material
  # metallicFactor rather than accidentally squaring roughness in all channels.
  r=im.getchannel('R');im=Image.merge('RGB',(Image.new('L',im.size,255),r,Image.new('L',im.size,255)))
 out=io.BytesIO();im.save(out,format='WEBP',lossless=True,exact=True,method=4);return out.getvalue()
IMAGES={(key,kind):image_bytes(key,kind) for key in ['walnut','limestone','plaster','velvet','paving','metal','carpet','leaf','lacquer','linen'] for kind in ['color','normal','roughness']}
def patch(source,runtime):
 j,b=read(R/source);original=copy.deepcopy(j);room=Path(runtime).stem;changes=seat_corrections(j,room);b=bytearray(b);textures={};mapped=[]
 sampler=len(j.setdefault('samplers',[]));j['samplers'].append({'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497})
 def texture(key,kind):
  if (key,kind) in textures:return textures[key,kind]
  data=IMAGES[key,kind];b.extend(b'\0'*(-len(b)%4));vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(data)});b.extend(data)
  ii=len(j.setdefault('images',[]));j['images'].append({'name':'generated_'+key+'_'+kind,'mimeType':'image/webp','bufferView':vi})
  ti=len(j.setdefault('textures',[]));j['textures'].append({'sampler':sampler,'extensions':{'EXT_texture_webp':{'source':ii}}});textures[key,kind]=ti;return ti
 cache={}
 for mesh in j.get('meshes',[]):
  for p in mesh['primitives']:
   mi=p.get('material');
   if mi is None:continue
   m=original['materials'][mi];key=family(m.get('name',''),mesh.get('name',''));attrs=p['attributes']
   if key is None:continue
   assert 'TEXCOORD_0' in attrs and 'NORMAL' in attrs,(runtime,mesh.get('name'),attrs)
   ck=(mi,key)
   if ck not in cache:
    new=copy.deepcopy(m);new['name']=m.get('name','surface')+'_generated_'+key;new.setdefault('extras',{})['generatedSurfaceFamily']=key
    pbr=new.setdefault('pbrMetallicRoughness',{});oldcolor=pbr.get('baseColorFactor',[1,1,1,1]);pbr['baseColorTexture']={'index':texture(key,'color')}
    # Texture images carry the surface colour. Preserve deliberate painted-metal
    # palette tints, without multiplying dark wood/fabric by the former flat fill.
    pbr['baseColorFactor']=oldcolor if key=='metal' else [1,1,1,1]
    if key=='leaf':pbr['baseColorFactor']=[.62,.80,.66,1]
    pbr['metallicFactor']=min(.85,max(.05,pbr.get('metallicFactor',0))) if key=='metal' else 0
    if key=='metal' and any(v in m.get('name','') for v in ['brass','gold','steel','iron']):pbr['metallicFactor']=.78
    pbr['roughnessFactor']=1;pbr['metallicRoughnessTexture']={'index':texture(key,'roughness')};new['normalTexture']={'index':texture(key,'normal'),'scale':.65}
    cache[ck]=len(j['materials']);j['materials'].append(new);mapped.append({'sourceMaterial':m.get('name'),'family':key})
   p['material']=cache[ck]
 if not cache:return None
 for k in ['extensionsUsed','extensionsRequired']:
  if 'EXT_texture_webp' not in j.setdefault(k,[]):j[k].append('EXT_texture_webp')
 # Remap only resources actually referenced by material slots. Geometry bytes,
 # including UV and index accessors, remain byte-exact in environment models.
 usedmat=sorted({p['material'] for mesh in j['meshes'] for p in mesh['primitives'] if 'material'in p});mt={v:i for i,v in enumerate(usedmat)}
 j['materials']=[j['materials'][i] for i in usedmat]
 for mesh in j['meshes']:
  for p in mesh['primitives']:
   if 'material'in p:p['material']=mt[p['material']]
 usedtex=set()
 def texwalk(v):
  if isinstance(v,dict):
   for k,q in v.items():
    if k.endswith('Texture') and isinstance(q,dict) and 'index'in q:usedtex.add(q['index'])
    else:texwalk(q)
  elif isinstance(v,list):
   for q in v:texwalk(q)
 texwalk(j['materials']);tm={v:i for i,v in enumerate(sorted(usedtex))}
 def remaptex(v):
  if isinstance(v,dict):
   for k,q in v.items():
    if k.endswith('Texture') and isinstance(q,dict) and 'index'in q:q['index']=tm[q['index']]
    else:remaptex(q)
  elif isinstance(v,list):
   for q in v:remaptex(q)
 remaptex(j['materials']);j['textures']=[j['textures'][i] for i in sorted(usedtex)]
 usedimg=set()
 for t in j['textures']:
  if 'source'in t:usedimg.add(t['source'])
  for ext in t.get('extensions',{}).values():
   if 'source'in ext:usedimg.add(ext['source'])
 it={v:i for i,v in enumerate(sorted(usedimg))};j['images']=[j['images'][i] for i in sorted(usedimg)]
 for t in j['textures']:
  if 'source'in t:t['source']=it[t['source']]
  for ext in t.get('extensions',{}).values():
   if 'source'in ext:ext['source']=it[ext['source']]
 usedviews={a['bufferView'] for a in j.get('accessors',[]) if 'bufferView'in a}|{i['bufferView'] for i in j.get('images',[]) if 'bufferView'in i};vt={v:i for i,v in enumerate(sorted(usedviews))};newb=bytearray();views=[]
 for vi in sorted(usedviews):
  v=copy.deepcopy(j['bufferViews'][vi]);newb.extend(b'\0'*(-len(newb)%4));start=v.get('byteOffset',0);chunk=b[start:start+v['byteLength']];v['byteOffset']=len(newb);newb.extend(chunk);views.append(v)
 for a in j.get('accessors',[]):
  if 'bufferView'in a:a['bufferView']=vt[a['bufferView']]
 for i in j.get('images',[]):
  if 'bufferView'in i:i['bufferView']=vt[i['bufferView']]
 j['bufferViews']=views
 # Regression proof: attributes and indices retain exact decoded values.
 _,beforeb=read(R/source)
 for i in range(len(original.get('accessors',[]))):assert np.array_equal(arr(original,beforeb,i),arr(j,newb,i)),(runtime,i)
 for a,c in zip(original.get('nodes',[]),j.get('nodes',[])):
  assert a.get('translation')==c.get('translation') and a.get('scale')==c.get('scale')
  assert a.get('children')==c.get('children') and a.get('name')==c.get('name')
 path=OUT/(runtime.replace('Assets/Art/','').replace('/','__'));data=write(path,j,bytes(newb))
 return {'file':path.relative_to(R).as_posix(),'runtime':runtime,'source':source,'bytes':len(data),'sha256':sha(data),'materialMappings':mapped,'seatCorrections':changes,'geometryAccessorsUnchanged':len(original.get('accessors',[]))}
def main():
 import sys
 only=next((set(v[7:].split(',')) for v in sys.argv if v.startswith('--only=')),None)
 catalog=O/'source-catalog.json'
 if not catalog.exists():
  inventory=json.loads((R/'Game/Saved/sculpted-environment-20261103/material-inventory.json').read_text(encoding='utf8'))['files'];catalog.write_text(json.dumps(inventory,indent=2),encoding='utf8')
 rows=json.loads(catalog.read_text(encoding='utf8'));result=[];preserved=[]
 if only:
  previous=json.loads((O/'manifest.json').read_text(encoding='utf8'));result=[a for a in previous['assets'] if Path(a['runtime']).stem not in only];preserved=previous.get('preservedOpticalOrGraphicOnlyModels',[]);rows=[a for a in rows if Path(a['runtime']).stem in only];assert rows,only
 for row in rows:
  a=patch(row['source'],row['runtime'])
  if a:result.append(a);print('SURFACE_APPLIED',Path(row['runtime']).stem,len(a['materialMappings']),len(a['seatCorrections']),a['bytes'],flush=True)
  else:preserved.append(row['runtime'])
 (O/'manifest.json').write_text(json.dumps({'assets':result,'preservedOpticalOrGraphicOnlyModels':preserved,'policy':'Generated albedo + Blender-baked shallow normal and roughness, geometry/IDs preserved; declared seating yaw corrections only'},ensure_ascii=False,indent=2),encoding='utf8')
 print('SURFACE_COMPLETE',len(result),sum(len(a['seatCorrections']) for a in result),flush=True)
if __name__=='__main__':main()
