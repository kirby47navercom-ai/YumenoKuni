"""Original rhythm display lists, including stopped parents and looping children."""
import json, math
from pathlib import Path
from build_v3_armament_layout import state, matrix, mul, I
ROOT=Path(__file__).resolve().parents[1];BANK=ROOT/'ui/v3_authorized/armament'

def actions(q):
 return [a for op in q['operations'] for a in op.get('decoded',{}).get('actions',[])]

def frame_at(seq,age):
 labels={q['name']:i for i,q in enumerate(seq) if q['name']}
 # These shipped child clips have one forward loop back to their first label.
 for i,q in enumerate(seq):
  aa=actions(q)
  for a in aa:
   if a['name']=='GoToLabel':
    target=labels[a['strings'][0]]
    if target==0 and i>0:return age%i
  if any(a['name']=='Stop' for a in aa):return min(age,i)
 return min(age,len(seq)-1)

def build():
 raw=json.loads((BANK/'t_riron_rythm_US/animation.json').read_text(encoding='utf8'))
 inv=json.loads((BANK/'manifest.json').read_text(encoding='utf8'));textures={r['imageIndex']:r for r in inv['textures'] if r['container']=='t_riron_rythm_US'}
 tables={t['id']:{e['id']:e for e in t['entries']} for t in raw['tables']};root=tables[6][0]['sequences'];labels={q['name']:i for i,q in enumerate(root) if q['name']}
 def leaves(ref,age,affine=I,alpha=1,path='',rgbmul=(1,1,1),rgbadd=(0,0,0)):
  table,idx=ref['table'],ref['entry'];e=tables[table][idx]
  if table==3:
   out=[]
   for r in e.get('rect_records',[]):
    if r['image_id'] not in textures:continue # control/mask vector, not replacement artwork
    tex=textures[r['image_id']];p=r['four_ints'];a=mul(affine,[1,0,0,1,p[0],p[2]]);w=p[1]-p[0];h=p[3]-p[2];sx=math.hypot(a[0],a[1]);sy=math.hypot(a[2],a[3]);cx=a[4]+a[0]*w/2+a[2]*h/2;cy=a[5]+a[1]*w/2+a[3]*h/2
    out.append({'path':path,'resource':tex['resource'],'rect':[(cx-w*sx/2)*2/3,(cy-h*sy/2)*2/3,w*sx*2/3,h*sy*2/3],'rotation':math.degrees(math.atan2(a[1],a[0])),'mirrorY':a[0]*a[3]-a[1]*a[2]<0,'alpha':alpha,'colorMultiply':rgbmul,'colorAdd':rgbadd})
   return out
  if table not in [5,6]:return []
  seq=e.get('sequences',[])
  if not seq:return []
  at=frame_at(seq,age);out=[]
  for _,o in sorted(state(seq,at).items()):
   if 'character_reference' not in o or o.get('clip_depth'):continue
   ct=o.get('color_transform',{});cm=ct.get('multiply_rgba',[1]*4);ca=ct.get('add_rgba',[0]*4);rm=[rgbmul[i]*cm[i] for i in range(3)];ra=[rgbadd[i]+rgbmul[i]*ca[i] for i in range(3)]
   out+=leaves(o['character_reference'],max(0,at-o['born']),mul(affine,matrix(o.get('matrix',{}))),alpha*cm[3],path+'/'+o.get('instance_name',str(o['depth'])),rm,ra)
  return out
 def rootframe(at,extra):
  out=[]
  for _,o in sorted(state(root,at).items()):
   if 'character_reference' not in o or o.get('clip_depth'):continue
   ct=o.get('color_transform',{});cm=ct.get('multiply_rgba',[1]*4);ca=ct.get('add_rgba',[0]*4)
   out+=leaves(o['character_reference'],max(0,at-o['born'])+extra,matrix(o.get('matrix',{})),cm[3],o.get('instance_name',str(o['depth'])),cm[:3],ca[:3])
  return out
 tracks={}
 for name,start,end in [('tap_in',2,10),('tap_out',11,25),('hold_in',25,33),('hold_out',34,48),('mash_in',48,56),('mash_out',57,72)]:tracks[name]=[rootframe(i,0) for i in range(start,end)]
 for name,at,period in [('tap_wait',10,30),('hold_wait',33,28),('mash_wait',56,11)]:tracks[name]=[rootframe(at,i) for i in range(period)]
 out={'sourceSha256':raw['sha256'],'source':'t_riron_rythm_US/animation.json','canvas':'Source local1920->1280 quads, no new icon artwork','labels':labels,'periods':{'hold':28,'mash':11,'tap':30},'tracks':tracks,'limitations':['Native mask controller positions are separate from root display lists; circumference/hold fill uses source bitmap clipping, not a measured per-frame native GPU mask.','PC key image substitutions follow supplied original shape-to-key resource variants; no source key glyphs redrawn.']}
 dest=BANK/'site-frames.json';dest.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf8');print(json.dumps({'frames':sum(map(len,tracks.values())),'sha256':raw['sha256']}))
if __name__=='__main__':build()
