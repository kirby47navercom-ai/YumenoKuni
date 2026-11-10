"""Original Nonstop gun display lists, three source bullet slices and cylinder mask affine."""
from pathlib import Path
import json,math,copy
import numpy as np
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1]
BANK=ROOT/'ui/v3_authorized/nonstop_ammo'
OUT=ROOT/'ui/v4/nonstop_hud_source'
S=2;SIZE=(880,540);BOUNDS=(0,450,440,720)

def raster(row):
 if not row['opacity']:return Image.new('RGBA',SIZE)
 if row['resource'].startswith('__solid_'):
  im=Image.new('RGBA',(1,1),'white' if row['resource']=='__solid_white' else 'black')
 else: im=Image.open(OUT/'ammoKotodama.png' if row['resource']=='t_gun_tx_000_US.png' else ROOT/row['texture']).convert('RGBA')
 cm,ca=row['colorMultiply'],row['colorAdd'];a=np.array(im,dtype=np.float32);a[:,:,:3]=np.clip(a[:,:,:3]*cm+np.array(ca)*255,0,255);im=Image.fromarray(a.astype('uint8'))
 a,b,c,d,x,y=row['sourceAffine'];rw=row['rect'][2]*1.5/math.hypot(a,b);rh=row['rect'][3]*1.5/math.hypot(c,d)
 a,b,c,d=[a*rw/im.width,b*rw/im.width,c*rh/im.height,d*rh/im.height];a,b,c,d,x,y=[v*2/3*S for v in (a,b,c,d,x,y)];y-=450*S;det=a*d-b*c
 out=im.transform(SIZE,Image.Transform.AFFINE,(d/det,-c/det,(c*y-d*x)/det,-b/det,a/det,(b*x-a*y)/det),Image.Resampling.BICUBIC)
 alpha=out.getchannel('A').point(lambda v:round(v*row['opacity']))
 for clip in row.get('clips',[]):
  mask=Image.new('RGBA',SIZE)
  for child in clip:mask.alpha_composite(raster(child))
  alpha=ImageChops.multiply(alpha,mask.getchannel('A'))
 out.putalpha(alpha);return out

def composite(rows):
 out=Image.new('RGBA',SIZE)
 for row in rows:out.alpha_composite(raster(row))
 return out

def cropped(im):return im
def save(name,im):cropped(im).save(OUT/(name+'.png'))
def gun(rows):return [r for r in rows if not r['path'].startswith(('p_gun_stock','p_t_gun_stock_ico'))]
def tint(im,rgb):
 a=np.array(im,dtype=np.float32);a[:,:,:3]*=rgb;return Image.fromarray(np.clip(a,0,255).astype('uint8'))

def build(records):
 # Retain the actual Korean-reference Kotodama lettering instead of the US Truth Bullets text.
 ref=ROOT/'ui/v3_authorized/nonstop_ammo/korean-reference.png'
 im=Image.open(ref).convert('RGB').crop((207,588,346,632));a=np.array(im,dtype=np.float32)
 lum=a.mean(axis=2);sat=a.max(axis=2)-a.min(axis=2)
 mask=Image.new('L',im.size);from PIL import ImageDraw
 ImageDraw.Draw(mask).polygon([(0,24),(139,0),(139,21),(0,44)],fill=255)
 alpha=np.clip((lum-83)*255/100,0,255)*(sat<45)*np.array(mask)/255
 own=Image.new('RGBA',im.size,(225,237,242,0));own.putalpha(Image.fromarray(alpha.astype('uint8')))
 own=own.resize((217,48),Image.Resampling.LANCZOS);label=Image.new('RGBA',(256,64));label.alpha_composite(own,(15,8));label.save(OUT/'ammoKotodama.png')
 layout=json.loads((BANK/'layout.json').read_text(encoding='utf-8'));main=layout['t_gun_US'];wheel=layout['t_gun_cylinder']
 for lie in [False,True]:
  suffix='Lie' if lie else '';wait='fl_uso_wait' if lie else 'fl_wait';shot='fl_uso_shot' if lie else 'fl_shot'
  save('ammoFrame'+suffix,composite(gun(main['states'][wait])))
  at=main['labels'][shot]-main['labels']['fl_in']
  for i in range(23):save('ammoFrame'+suffix+'Shot'+str(i),composite(gun(main['frames'][at+i])))
  # The native gun uses this mask's affine, not t_cylinder (another UI's wheel).
  source=next(r for r in wheel['states']['fl_wait_uso' if lie else 'fl_wait'] if r['resource'].startswith('t_cylinder_stripe'))['clips'][0][0]
  for step in range(36):
   out=Image.new('RGBA',SIZE)
   for index in [0,1]:
    row=copy.deepcopy(source);row.pop('clips',None);row['resource']=f't_cylinder_{index:03d}.png';row['texture']=f'ui/v3_authorized/nonstop_hud/t_cylinder/t_cylinder_{index:03d}.png.png'
    # Rotate the source face before the recovered perspective affine.
    im=Image.open(ROOT/row['texture']).convert('RGBA').rotate(step*10,Image.Resampling.BICUBIC)
    rgb=([.55,.13,.75] if lie else [.15,.78,1.0]) if index==0 else ([.86,.58,1.0] if lie else [.40,.88,1.0])
    im=tint(im,rgb)
    temp=OUT/('_wheel_face'+str(index)+'.png');im.save(temp);row['texture']=temp.relative_to(ROOT).as_posix();row['colorMultiply']=[1,1,1];row['colorAdd']=[0,0,0];row['opacity']=.78 if index==0 else .92
    out.alpha_composite(raster(row))
   save('ammoCylinder'+suffix+str(step),out)
  # Runtime owns source frame recoil; wheel face stays on its source mask pivot.
  for i in [0,1]:(OUT/('_wheel_face'+str(i)+'.png')).unlink(missing_ok=True)
  parts=[]
  colors=[[1,1,1],[1,.3137255,.627451] if lie else [.8627451,1,1],[.4705882,.0784314,.627451] if lie else [0,.8235294,1]]
  for stem,color in zip(['t_bullet_base','t_bullet','t_bullet_glow'],colors):
   strip=Image.new('RGBA',(192,128))
   for i in range(3):
    im=Image.open(BANK/(stem+f'_{i:03d}')/(stem+f'_{i:03d}.png.png')).convert('RGBA');strip.alpha_composite(tint(im,color),(i*64,0))
   parts.append(strip)
  plate=Image.new('RGBA',(192,128))
  for im in parts:plate.alpha_composite(im)
  plate.save(OUT/('ammoPlate'+suffix+'.png'))
  for i,name in enumerate(['Left','Middle','Tip']):plate.crop((i*64,0,(i+1)*64,128)).save(OUT/('ammoPlate'+suffix+name+'.png'))
 rows=main['states']['fl_wait'];markers=[]
 for i in range(9):
  marker=next(r for r in rows if r['path']==f'p_t_gun_stock_ico_bullet_{i:03d}/1');arr=[r for r in rows if r['path'] in [f'p_t_gun_stock_ico_ar_dn_{i:03d}/1',f'p_t_gun_stock_ico_ar_up_{i:03d}/1']]
  save('ammoStock'+str(i),composite([marker]));save('ammoSelected'+str(i),composite([marker]+arr));markers.append(marker['rect'])
 records['ammo']={'rect':[0,450,440,270],'source':'t_gun_US fl_wait/fl_shot/fl_uso_wait/fl_uso_shot; t_gun_cylinder mask affine; original native 3x64 bullet slices', 'plate':{'left':114.70667,'pivotY':613.1289,'rotation':-5,'cap':42.666667,'height':85.333333},'stockRects':markers,'nativeEvidence':['ev_98811394d658dcc6fea5f856b18ffe06d5cab6d683149a30eb694409480f69a7','ev_32baac9841f7af1b0ba8ff6536d317dcf4e358b064f5d44a814616d55183e160','ev_4dce2962e95de63efdcc55754baae8e66bc66617a35f2309fe57e983befec46b']}
 if __name__=='__main__':
  path=OUT/'layout.json';d=json.loads(path.read_text(encoding='utf-8'));d['tiles']=records;path.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':build(json.loads((OUT/'layout.json').read_text(encoding='utf-8'))['tiles'])
