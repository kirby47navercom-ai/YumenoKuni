"""Exact GLB graph copying and content keys for shared high-to-low bake results."""
from pathlib import Path
import copy, hashlib, json, struct, re
import numpy as np

def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):
    b=Path(p).read_bytes();n=struct.unpack_from('<I',b,12)[0]
    return json.loads(b[20:20+n]),b[28+n:]
def write(p,j,b,limit=True):
    j['buffers']=[{'byteLength':len(b)}];s=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();s+=b' '*(-len(s)%4);b+=b'\0'*(-len(b)%4)
    data=struct.pack('<III',0x46546c67,2,28+len(s)+len(b))+struct.pack('<II',len(s),0x4e4f534a)+s+struct.pack('<II',len(b),0x004e4942)+b
    assert not limit or len(data)<64*1024*1024,(p,len(data));Path(p).write_bytes(data);return data
def array(j,b,i):
    a=j['accessors'][i];v=j['bufferViews'][a['bufferView']]
    dt=np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    return np.ndarray((a['count'],w),dt,b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',w*dt.itemsize),dt.itemsize))
def triangles(j,mi):return sum(j['accessors'][p['indices']]['count']//3 for p in j['meshes'][mi]['primitives'])
def material_key(j,b,mi):
    m=copy.deepcopy(j['materials'][mi]);m.pop('extras',None);m.pop('name',None)
    def walk(o):
        if isinstance(o,dict):
            for k,v in list(o.items()):
                if k.endswith('Texture') and isinstance(v,dict) and 'index' in v:
                    t=j['textures'][v['index']];ii=t.get('source',t.get('extensions',{}).get('EXT_texture_webp',{}).get('source'));im=j['images'][ii];bv=j['bufferViews'][im['bufferView']];off=bv.get('byteOffset',0)
                    v['index']=digest(b[off:off+bv['byteLength']]);v['sampler']=j.get('samplers',[])[t['sampler']] if 'sampler'in t else None
                else:walk(v)
        elif isinstance(o,list):
            for v in o:walk(v)
    walk(m);return m
def keys(j,b):
    mats={i:material_key(j,b,i) for i in range(len(j.get('materials',[])))};out={}
    for i,m in enumerate(j['meshes']):
        h=hashlib.sha256()
        for p in m['primitives']:
            h.update(json.dumps(mats.get(p.get('material')),sort_keys=True).encode())
            for k,a in sorted(p['attributes'].items()):h.update(k.encode());h.update(array(j,b,a).tobytes())
            h.update(array(j,b,p['indices']).tobytes())
        out[i]=h.hexdigest()
    return out

class Copier:
    def __init__(self,j):
        self.j=copy.deepcopy(j);self.b=bytearray();self.cache={};self.images={}
        for key in ['meshes','accessors','bufferViews','materials','textures','images','samplers']:self.j[key]=[]
    def append(self,key,obj):
        index=len(self.j[key]);self.j[key].append(obj);return index
    def copy(self,j,b,key,i,token):
        ck=(token,key,i)
        if ck in self.cache:return self.cache[ck]
        obj=copy.deepcopy(j[key][i])
        if key=='bufferViews':
            off=obj.get('byteOffset',0);raw=b[off:off+obj['byteLength']]
            self.b.extend(b'\0'*(-len(self.b)%4));obj['byteOffset']=len(self.b);obj['buffer']=0;self.b.extend(raw)
        elif key=='accessors':obj['bufferView']=self.copy(j,b,'bufferViews',obj['bufferView'],token)
        elif key=='images':
            bv=j['bufferViews'][obj['bufferView']];off=bv.get('byteOffset',0);ik=digest(b[off:off+bv['byteLength']])
            if ik in self.images:self.cache[ck]=self.images[ik];return self.images[ik]
            obj['bufferView']=self.copy(j,b,'bufferViews',obj['bufferView'],token)
        elif key=='textures':
            if 'source'in obj:obj['source']=self.copy(j,b,'images',obj['source'],token)
            for ex in obj.get('extensions',{}).values():
                if 'source'in ex:ex['source']=self.copy(j,b,'images',ex['source'],token)
            if 'sampler'in obj:obj['sampler']=self.copy(j,b,'samplers',obj['sampler'],token)
        elif key=='materials':
            def walk(o):
                if isinstance(o,dict):
                    for k,v in o.items():
                        if k.endswith('Texture') and isinstance(v,dict) and 'index'in v:v['index']=self.copy(j,b,'textures',v['index'],token)
                        else:walk(v)
                elif isinstance(o,list):
                    for v in o:walk(v)
            walk(obj)
        elif key=='meshes':
            for p in obj['primitives']:
                p['attributes']={k:self.copy(j,b,'accessors',v,token) for k,v in p['attributes'].items()}
                p['indices']=self.copy(j,b,'accessors',p['indices'],token)
                if 'material'in p:p['material']=self.copy(j,b,'materials',p['material'],token)
        result=self.append(key,obj);self.cache[ck]=result
        if key=='images':self.images[ik]=result
        for k in ['extensionsUsed','extensionsRequired']:
            for ext in j.get(k,[]):
                if ext not in self.j.setdefault(k,[]):self.j[k].append(ext)
        return result

def node_keys(j,b):
    import numpy as np
    meshkeys=keys(j,b);parents={c:i for i,n in enumerate(j['nodes']) for c in n.get('children',[])};world={}
    def matrix(i):
        if i in world:return world[i]
        n=j['nodes'][i]
        if 'matrix'in n:m=np.array(n['matrix']).reshape(4,4,order='F')
        else:
            x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4);m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
        world[i]=matrix(parents[i])@m if i in parents else m;return world[i]
    out={}
    for i,n in enumerate(j['nodes']):
        if 'mesh'not in n:continue
        basis=matrix(i)[:3,:3];metric=np.round(basis.T@basis,6).tolist()
        out[n['name']]=hashlib.sha256((meshkeys[n['mesh']]+json.dumps(metric)+str(float(np.linalg.det(basis))<0)).encode()).hexdigest()
    return out

