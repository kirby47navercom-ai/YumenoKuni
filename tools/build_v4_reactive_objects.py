"""Separate existing own decorative planters for real per-object reactions.
No new model, texture, V3 extraction, Blender scene or original source mutation.
"""
from pathlib import Path
import copy,hashlib,json,struct
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/reactions_v1';O.mkdir(exist_ok=True)

def load(path):
 b=path.read_bytes();n,t=struct.unpack_from('<II',b,12);g=json.loads(b[20:20+n]);offset=20+n;size,kind=struct.unpack_from('<II',b,offset);assert kind==0x004e4942
 return g,b[offset+8:offset+8+size]

def pack(g,blob,roots,path):
 g=copy.deepcopy(g);assert not g.get('animations') and not g.get('skins')
 def mapping(values):return {v:i for i,v in enumerate(sorted(set(values)))}
 selected=set()
 def visit(i):
  if i in selected:return
  selected.add(i)
  for child in g['nodes'][i].get('children',[]):visit(child)
 for i in roots:visit(i)
 nodes=mapping(selected);meshes=mapping(n['mesh'] for i,n in enumerate(g['nodes']) if i in nodes and 'mesh'in n)
 primitives=[p for i,m in enumerate(g.get('meshes',[])) if i in meshes for p in m['primitives']]
 materials=mapping(p['material'] for p in primitives if 'material'in p)
 texture_ids=[]
 def textures(v,replace=None):
  if isinstance(v,list):
   for x in v:textures(x,replace)
  elif isinstance(v,dict):
   for k,x in v.items():
    if k.endswith('Texture') and isinstance(x,dict) and 'index'in x:
     if replace is None:texture_ids.append(x['index'])
     else:x['index']=replace[x['index']]
    else:textures(x,replace)
 for i in materials:textures(g['materials'][i])
 tex=mapping(texture_ids);images=mapping(g['textures'][i]['source'] for i in tex)
 accessors=mapping([a for p in primitives for a in [*p['attributes'].values(),*([p['indices']] if 'indices'in p else [])]])
 assert all('sparse'not in g['accessors'][i] for i in accessors)
 views=mapping([g['accessors'][i]['bufferView'] for i in accessors]+[g['images'][i]['bufferView'] for i in images])
 def subset(key,ids):return [g[key][i] for i in sorted(ids)]
 g['nodes']=subset('nodes',nodes)
 for n in g['nodes']:
  if 'children'in n:n['children']=[nodes[i] for i in n['children']]
  if 'mesh'in n:n['mesh']=meshes[n['mesh']]
 g['meshes']=subset('meshes',meshes)
 for p in primitives:
  p['attributes']={k:accessors[v] for k,v in p['attributes'].items()}
  if 'indices'in p:p['indices']=accessors[p['indices']]
  if 'material'in p:p['material']=materials[p['material']]
 g['materials']=subset('materials',materials)
 for m in g['materials']:textures(m,tex)
 g['textures']=subset('textures',tex)
 for t in g['textures']:t['source']=images[t['source']]
 g['images']=subset('images',images)
 for i in g['images']:i['bufferView']=views[i['bufferView']]
 g['accessors']=subset('accessors',accessors)
 for a in g['accessors']:a['bufferView']=views[a['bufferView']]
 g['bufferViews']=subset('bufferViews',views);data=b''
 for v in g['bufferViews']:
  old=v.get('byteOffset',0);chunk=blob[old:old+v['byteLength']];v['byteOffset']=len(data);v['buffer']=0;data+=chunk+b'\0'*((-len(chunk))%4)
 g['scene']=0;g['scenes']=[{'nodes':[nodes[i] for i in roots]}];g['buffers']=[{'byteLength':len(data)}]
 g['asset']['generator']='YumenoKuni own reactive-prop subset compiler'
 j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
 out=struct.pack('<III',0x46546c67,2,28+len(j)+len(data))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(data),0x004e4942)+data;path.write_bytes(out)
 row={'file':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(out).hexdigest(),'bytes':len(out)};return row

manifest=json.loads((R/'art/space_v4/full_v2/manifest.json').read_text(encoding='utf-8'))
out={'policy':'Two explicitly selected existing decorative planters in each of three public spaces. No evidence furniture, doorway or new geometry. Physical bounce returns to its authored pose, so collision remains valid. Own durability3/stock2 and input timing; source reward gates retained.','spaces':{}}
for sid in ['plaza','hotel_lobby','park_garden']:
 spec=next(s for s in manifest['spaces'] if s['id']==sid);g,blob=load(R/spec['file']);props=[];remove=set()
 for suffix in ['', '.001']:
  name=sid+'_detail_planter'+suffix;index=next(i for i,n in enumerate(g['nodes']) if n.get('name')==name);node=g['nodes'][index];p=node.get('translation',[0,0,0]);assert 'matrix'not in node
  prop=copy.deepcopy(g);prop['nodes'][index].pop('translation',None);row=pack(prop,blob,[index],O/(sid+('_1' if suffix else '_0')+'.glb'))
  row.update({'id':name,'runtime':'Assets/Art/explore3d/reaction_'+Path(row['file']).name,'p':p,'label':'장식 화분','durability':3,'stock':2});props.append(row);remove.add(index)
 for node in g['nodes']:
  if 'children'in node:node['children']=[i for i in node['children'] if i not in remove]
 # Broad original black ground is recolored; no other surface or source file changes.
 mat=len(g['materials']);g['materials'].append({'name':'runtime_paving','pbrMetallicRoughness':{'baseColorFactor':[.25,.34,.23,1] if sid=='park_garden' else [.48,.46,.41,1],'roughnessFactor':1,'metallicFactor':0}})
 for node in g['nodes']:
  if 'mesh'in node and node.get('name','').split('.')[0] in ['floor',sid+'_floor']:
   g['meshes'][node['mesh']]=copy.deepcopy(g['meshes'][node['mesh']])
   for p in g['meshes'][node['mesh']]['primitives']:p['material']=mat
 base=pack(g,blob,g['scenes'][g.get('scene',0)]['nodes'],O/(sid+'_base.glb'));base['props']=props;out['spaces'][sid]=base
(O/'manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'spaces':len(out['spaces']),'props':sum(len(v['props']) for v in out['spaces'].values()),'newModel':False,'originalsUnchanged':True}))
