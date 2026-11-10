"""Original editable edge-only VFX/masks and actor contact marks; no image repaint."""
from pathlib import Path
import math,json,hashlib
from PIL import Image
import make_v4_ui_batch as u
R=Path(__file__).resolve().parents[1];O=R/'ui/v4/motion_hd';O.mkdir(parents=True,exist_ok=True);u.OUT=O;u.SCALE=4;records=[]
def save(p,ident,frame):
 f=O/(ident+f'_{frame:02d}');f.with_suffix('.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{p.w*4}" height="{p.h*4}" viewBox="0 0 {p.w} {p.h}">'+''.join(p.svg)+'</svg>\n',encoding='utf8');p.im.save(f.with_suffix('.png'));p.im.save(f.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
 with Image.open(f.with_suffix('.webp')) as q:assert q.convert('RGBA').tobytes()==p.im.tobytes()
 return {'frame':frame,'svg':f.with_suffix('.svg').relative_to(R).as_posix(),'png':f.with_suffix('.png').relative_to(R).as_posix(),'webp':f.with_suffix('.webp').relative_to(R).as_posix(),'size':list(p.im.size),'alpha_extrema':list(p.im.getchannel('A').getextrema())}
for ident in ['concentration_border_native_r2','panic_noise_native_r2','scene_ink_cover','scene_ink_uncover']:
 frames=[];N=16
 for frame in range(N):
  t=frame/(N-1);p=u.Plate(ident,960,540)
  if ident.startswith(('concentration','panic')):
   amp=(.75+.10*math.cos(t*math.tau)) if ident.startswith('concentration') else math.sin(math.pi*t)**2
   for sx,sy in [(1,1),(-1,1),(1,-1),(-1,-1)]:
    ox=0 if sx==1 else 960;oy=0 if sy==1 else 540
    for k in range(10):
     inset=4+k*5;length=(20+k*6)*(amp if ident.startswith('panic') else 1)
     pts=[(inset,0),(inset+7,0),(inset+length*.56,18+k*3),(inset+length*.21,7+k*2)]
     p.poly([(ox+sx*x,oy+sy*y) for x,y in pts],'#9770cf' if k%4==0 else '#14131b')
   # Only alpha is attenuated; no bright full-screen center flash.
   alpha=p.im.getchannel('A').point(lambda x:round(x*(.18 if ident.startswith('concentration') else .38)*amp));p.im.putalpha(alpha)
   opacity=(.18 if ident.startswith('concentration') else .38)*amp;p.svg=['<g opacity="'+str(opacity)+'">']+p.svg+['</g>']
  else:
   progress=t if ident=='scene_ink_cover' else 1-t
   if progress>0:
    if progress==1:p.box(0,0,960,540,'#14131b')
    else:
     x=-75+1110*progress;edge=[(x+23*math.sin(k*1.7)+7*math.sin(k*3.4),k*54) for k in range(11)]
     p.poly([(0,0)]+edge+[(0,540)],'#14131b')
  frames.append(save(p,ident,frame))
 record={'id':ident,'tool':'original editable vector geometry + native4x rasterization','frames':frames,'fps':16,'loop':ident.startswith('concentration'),'anchor':[.5,.5],'blend':'straight-alpha','reduced_motion':'crossfade70ms, no shake; concentration static at max0.12opacity','runtime_integrated':False}
 if ident.startswith(('concentration','panic')):record.update(center_clear_rect_normalized=[.14,.20,.86,.80],replaces='fx_'+('concentration_border_r1' if ident.startswith('concentration') else 'panic_noise_r1'),replacement_reason='generated concentration contained an unsolicited person; panic was center-burst instead of edge-only. Replaced by original code-native effect, old files retained.')
 else:record.update(mask_channel='alpha',monotonic_coverage=True,role='actual full-field opaque scene cover/uncover; generated torn-edge overlay is decoration only')
 records.append(record)
# Independent contact shadow and selection rings, never burned into standing sprites.
for ident,col in [('actor_contact_shadow','#14131b'),('actor_focus_ring','#9770cf'),('actor_target_ring','#f3ead9')]:
 p=u.Plate(ident,512,160)
 for k in range(18):
  rx=230-k*9;ry=58-k*2.1;pts=[(256+rx*math.cos(i*math.tau/64),80+ry*math.sin(i*math.tau/64)) for i in range(64)]
  if ident=='actor_contact_shadow':p.poly(pts,col)
  elif k<2:p.line(pts+[pts[0]],col,3)
 if ident=='actor_contact_shadow':p.im.putalpha(p.im.getchannel('A').point(lambda v:round(v*.18)));p.svg=['<g opacity=".18">']+p.svg+['</g>']
 f=save(p,ident,0);records.append({'id':ident,'frames':[f],'tool':'editable native4x vector','world_role':'separate horizontal ground plane; foot anchor origin center, actual world scale supplied by scene','runtime_integrated':False})
(O/'manifest.json').write_text(json.dumps({'scale':4,'assets':records,'runtime_integrated':False,'not_claimed':'camera impulse/trigger integration or game shader acceptance'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Created4native motion sequences64frames +3ground-contact markers')
