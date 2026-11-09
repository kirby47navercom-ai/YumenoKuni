"""Resolve supplied SFL display lists to source texture quads, without UI redesign."""
from pathlib import Path
import json,math,copy
ROOT=Path(__file__).resolve().parents[1];BANK=ROOT/'ui/v3_authorized/armament'
I=[1,0,0,1,0,0]
ANIMATED_NAMES={'t_phase_start_riron_JP','t_kai_cutin_boushi_JP','t_riron_todome_cutin_JP','t_ronpa_cutin_JP'}
SOLID_NAMES=set()
def matrix(m):return [m.get('scale_x',1),m.get('rotate_skew0',0),m.get('rotate_skew1',0),m.get('scale_y',1),m.get('translate_x',0),m.get('translate_y',0)]
def mul(a,b):return [a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]]
def state(sequences,frame):
 d={}
 for at,q in enumerate(sequences[:frame+1]):
  for op in q['operations']:
   o=op.get('decoded',{});name=o.get('name')
   if name=='RemoveObject2':d.pop(o['depth'],None)
   if name=='PlaceObject2':
    depth=o['depth']
    if not o.get('move'):d[depth]={'born':at}
    d.setdefault(depth,{'born':at}).update(o)
 return d
def build():
 inv=json.loads((BANK/'manifest.json').read_text(encoding='utf-8'));out={}
 for name,file in inv['timelines'].items():
  x=json.loads((ROOT/file).read_text(encoding='utf-8'));tables={t['id']:{e['id']:e for e in t['entries']} for t in x['tables']};textures=[r for r in inv['textures'] if r['container']==name];seq=tables[6][0]['sequences'];labels={q['name']:i for i,q in enumerate(seq) if q['name']}
  def leaves(ref,age,affine=I,alpha=1,path='',depth=0,rgbmul=(1,1,1),rgbadd=(0,0,0)):
   if depth>12:raise ValueError('SFL cycle')
   table,idx=ref['table'],ref['entry'];entry=tables[table][idx]
   if table==3:
    result=[]
    for r in entry.get('rect_records',[]):
     image=r['image_id']
     if image==4294967295:
      if name not in ANIMATED_NAMES and name not in SOLID_NAMES:continue
      if r.get('unknown_hex') not in ['80000000','80ffffff']:continue
      matching=[{'file':'','resource':'__solid_black' if r['unknown_hex']=='80000000' else '__solid_white'}]
     else:matching=[r for r in textures if r.get('imageIndex')==image]
     if not matching:continue
     p=r['four_ints'];a=mul(affine,[1,0,0,1,p[0],p[2]]);w=p[1]-p[0];h=p[3]-p[2]
     sx=math.hypot(a[0],a[1]);sy=math.hypot(a[2],a[3]);rotation=math.degrees(math.atan2(a[1],a[0]));cx=a[4]+a[0]*w/2+a[2]*h/2;cy=a[5]+a[1]*w/2+a[3]*h/2
     result.append({'path':path,'texture':matching[0]['file'],'resource':matching[0]['resource'],'rect':[(cx-w*sx/2)*2/3,(cy-h*sy/2)*2/3,w*sx*2/3,h*sy*2/3],'rotation':rotation,'opacity':alpha,'sourceAffine':a,'colorMultiply':rgbmul,'colorAdd':rgbadd})
    return result
   if table not in [5,6]:return []
   s=entry.get('sequences',[])
   if not s:return []
   stops=[i for i,q in enumerate(s) if any(a.get('name')=='Stop' for op in q['operations'] for a in op.get('decoded',{}).get('actions',[]))]
   frame=min(age,stops[0]) if stops else age%len(s);frame=min(frame,len(s)-1);result=[]
   masks=[]
   for k,o in sorted(state(s,frame).items()):
    masks=[m for m in masks if k<=m[0]]
    if 'character_reference' not in o:continue
    a=mul(affine,matrix(o.get('matrix',{})));al=alpha*o.get('color_transform',{}).get('multiply_rgba',[1,1,1,1])[3]
    ct=o.get('color_transform',{});cm=ct.get('multiply_rgba',[1]*4);ca=ct.get('add_rgba',[0]*4);rm=[rgbmul[i]*cm[i] for i in range(3)];ra=[rgbadd[i]+rgbmul[i]*ca[i] for i in range(3)]
    child=leaves(o['character_reference'],max(0,frame-o['born']),a,al,path+'/'+o.get('instance_name',str(k)),depth+1,rm,ra)
    if o.get('clip_depth'):masks.append((o['clip_depth'],child));continue
    for row in child:
     if masks:row['clips']=row.get('clips',[])+[m[1] for m in masks]
    result+=child
   return result
  def mainframe(at):
   result=[]
   masks=[]
   for k,o in sorted(state(seq,at).items()):
    masks=[m for m in masks if k<=m[0]]
    if 'character_reference' not in o:continue
    child=leaves(o['character_reference'],max(0,at-o['born']),matrix(o.get('matrix',{})),o.get('color_transform',{}).get('multiply_rgba',[1,1,1,1])[3],o.get('instance_name',str(k)),0,o.get('color_transform',{}).get('multiply_rgba',[1]*4)[:3],o.get('color_transform',{}).get('add_rgba',[0]*4)[:3])
    if o.get('clip_depth'):masks.append((o['clip_depth'],child));continue
    for row in child:
     if masks:row['clips']=row.get('clips',[])+[m[1] for m in masks]
    result+=child
   return result
  out[name]={'sha256':x['sha256'],'labels':labels,'states':{k:mainframe(i) for k,i in labels.items()}}
  if name in ANIMATED_NAMES:out[name]['frames']=[mainframe(i) for i in range(labels.get('fl_in',0),len(seq))]
 (BANK/'layout.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf-8');print(json.dumps(json.loads((BANK/'runtime-layout.json').read_text(encoding='utf-8')),ensure_ascii=True))
if __name__=='__main__':build()
