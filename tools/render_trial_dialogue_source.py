"""Compose the requested original dialogue rasters at their decoded SFL transforms."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from PIL import Image,ImageChops,ImageDraw,ImageFont,ImageFilter
ROOT=Path(__file__).resolve().parents[1];BANK=ROOT/'ui/v3_authorized/trial_dialogue';OUT=ROOT/'ui/v4/trial_dialogue_source';OUT.mkdir(parents=True,exist_ok=True)
LAYOUT=json.loads((BANK/'layout.json').read_text(encoding='utf-8'));SCALE=2;SIZE=(1280*SCALE,720*SCALE);records={}
def layer(row):
 im=Image.new('RGBA',(2,2),(0,0,0,255)if row['resource']=='__solid_black'else(255,255,255,255))if row['resource'].startswith('__solid_')else Image.open(ROOT/row['texture']).convert('RGBA')
 if 'DXT1' in row['resource']:
  a=np.array(im);a[:,:,3]=np.minimum(a[:,:,3],a[:,:,:3].max(axis=2));im=Image.fromarray(a)
 # The user supplied the blue dialogue-frame variant. Preserve source glow
 # alpha/shape, choosing that palette rather than inventing new line geometry.
 if row['resource']=='t_kaiwa_line_DXT1.png' or row['resource'].startswith('t_kaiwa_gl_') or row['resource']=='t_kaiwa_title_tx_US.png':
  a=np.array(im);light=a[:,:,:3].max(axis=2).astype(np.float32)/255;a[:,:,0]=(light*24).astype('uint8');a[:,:,1]=(light*195).astype('uint8');a[:,:,2]=(light*255).astype('uint8');im=Image.fromarray(a)
 cm,ca=row['colorMultiply'],row['colorAdd']
 if cm!=[1,1,1] or ca!=[0,0,0]:
  a=np.array(im,dtype=np.float32);a[:,:,:3]=np.clip(a[:,:,:3]*cm+np.array(ca)*255,0,255);im=Image.fromarray(a.astype('uint8'))
 a,b,c,d,x,y=row['sourceAffine'];rw=row['rect'][2]*1.5/math.hypot(a,b);rh=row['rect'][3]*1.5/math.hypot(c,d);a,b,c,d=[a*rw/im.width,b*rw/im.width,c*rh/im.height,d*rh/im.height];a,b,c,d,x,y=[v*2/3*SCALE for v in [a,b,c,d,x,y]];det=a*d-b*c
 out=im.transform(SIZE,Image.Transform.AFFINE,(d/det,-c/det,(c*y-d*x)/det,-b/det,a/det,(b*x-a*y)/det),Image.Resampling.BICUBIC);alpha=out.getchannel('A').point(lambda v:round(v*row['opacity']))
 for clip in row.get('clips',[]):
  mask=Image.new('RGBA',SIZE)
  for child in clip:mask.alpha_composite(layer(child))
  alpha=ImageChops.multiply(alpha,mask.getchannel('A'))
 out.putalpha(alpha);return out
def composite(rows):
 out=Image.new('RGBA',SIZE)
 for row in rows:out.alpha_composite(layer(row))
 return out
def write(name,im):
 box=im.getbbox() if name in ['next','auto'] else(0,0,*SIZE)
 im.crop(box).save(OUT/(name+'.png'));records[name]={'file':name+'.png','rect':[box[0]/SCALE,box[1]/SCALE,(box[2]-box[0])/SCALE,(box[3]-box[1])/SCALE]}
frame=LAYOUT['t_kaiwa_fl_US']['states']['fl_wait_d'];background=frame[:4];foreground=frame[4:]
for chapter in range(1,7):
 rows=[]
 for original in foreground:
  row=dict(original)
  if 'kaisu_tx_' in row['resource']:
   row['texture']=str(Path(row['texture']).with_name(f't_kaiwa_title_kaisu_tx_{chapter-1:03d}_DXT1_US.png.png')).replace('\\','/')
  rows.append(row)
 write('frame'+str(chapter),composite(rows))
write('frame_plain',composite([r for r in foreground if not any(s in r['resource']for s in ['title_tx','title_kaisu','title_pl'])]))
body=LAYOUT['t_kaiwa_pl']['states']['fl_d_c_in_wait']
write('body',composite(background+body));write('body_plain',composite(background[:2]+body))
for key,state in [('next','fl_wait'),('auto','fl_auto_wait')]:write(key,composite(LAYOUT['t_next_US']['states'][state]))

# Project our existing high-resolution character portraits into the face-card plane in the
# user's screenshot. This replaces identities only; original UI raster is above.
quad=np.array([[160,138],[267,66],[393,453],[193,453]],dtype=float)
for slug in 'mio rin ken nana taiga ai rei sora haruka sho koto akari riku satsuki yuu kaede lappy'.split():
 source=ROOT/('art/character_delivery_v4/portraits/lappy.webp' if slug=='lappy' else f'art/trial3d/id_portraits_color_v1/runtime/{slug}.webp')
 im=Image.open(source).convert('RGBA');w,h=im.size
 crop=(w*.105,h*.015,w*.90,h*.810) if slug!='lappy' else (w*.12,h*.02,w*.88,h*.64)
 im=im.crop(tuple(round(n)for n in crop)).resize((512,512),Image.Resampling.LANCZOS)
 # Crop a naturally proportioned face through the narrow card opening. Fitting
 # the whole head into that opening would unnaturally squeeze the character.
 im=im.rotate(-14,Image.Resampling.BICUBIC,center=(256,256))
 mask=Image.new('L',(512,512));ImageDraw.Draw(mask).polygon([tuple(p)for p in quad],fill=255);im.putalpha(ImageChops.multiply(im.getchannel('A'),mask));im.save(OUT/f'portrait_{slug}.png')
records['portrait']={'rect':[-30.664062,147.335938,341.328125,341.328125],'referenceQuad512':quad.tolist(),'scope':'Own character image projected to supplied screenshot face-card; source dummy portrait texture is empty. Original character RGB is not used.'}

# One full-name image, including the larger cyan first syllable. No separate
# first-letter widget, no stock Japanese names, no duplicate name text.
characters=json.loads((ROOT/'data/characters.json').read_text(encoding='utf-8'));full_names={c['heading'].split('(')[0].strip().split()[-1]:c['heading'].split('(')[0].strip() for c in characters}
# Alias and anonymous labels need the same card typography, never the wide ADV
# banner squeezed into a square. Collect exactly the generation-time speakers.
def scan(value):
 if isinstance(value,list):
  for item in value:scan(item)
 elif isinstance(value,dict):
  for key in ['speaker','who']:
   text=value.get(key)
   if isinstance(text,str) and text and len(text)<40 and text not in full_names:full_names[text]=text
  for item in value.values():scan(item)
for folder in ['data/v4_story/chapters','data/v4_story/freetime','data/flow','data/trials']:
 for file in (ROOT/folder).glob('*.json'):scan(json.loads(file.read_text(encoding='utf8')))
font=ROOT/'fonts/gothica1/GothicA1-Light.ttf';names={} 
for given,full in full_names.items():
 parts=full.split();family=parts[0];personal=' '.join(parts[1:]);canvas=Image.new('RGBA',(512,512));ink=Image.new('RGBA',canvas.size);draw=ImageDraw.Draw(ink)
 regular=ImageFont.truetype(str(font),84);large=ImageFont.truetype(str(font),112)
 extent=max(sum(draw.textlength(ch,font=large if i==0 else regular)for i,ch in enumerate(family)),draw.textlength(personal,font=regular))
 if extent>440:
  factor=440/extent;regular=ImageFont.truetype(str(font),max(14,round(84*factor)));large=ImageFont.truetype(str(font),max(18,round(112*factor)))
 widths=[draw.textlength(ch,font=large if i==0 else regular)for i,ch in enumerate(family)];x=(512-sum(widths))/2
 for i,ch in enumerate(family):
  draw.text((x,256),ch,font=large if i==0 else regular,anchor='ls',fill=(70,230,255,255)if i==0 else(226,169,255,255));x+=widths[i]
 if personal:draw.text((256,350),personal,font=regular,anchor='ms',fill=(226,169,255,255))
 canvas.alpha_composite(ink.filter(ImageFilter.GaussianBlur(5)));canvas.alpha_composite(ink);canvas=canvas.rotate(5,Image.Resampling.BICUBIC,center=(256,256));file='name_'+hashlib.sha256(given.encode()).hexdigest()[:16]+'.png';canvas.save(OUT/file);names[given]={'file':file,'fullName':full}
records['names']=names
# Fixed-size left face card and right corner; stretch only the empty middle.
for name in [key for key in records if key.startswith(('frame','body'))]:
 im=Image.open(OUT/(name+'.png'))
 for suffix,x0,x1 in [('left',0,340),('middle',340,1000),('right',1000,1280)]:
  im.crop((x0*SCALE,0,x1*SCALE,SIZE[1])).save(OUT/(name+'_'+suffix+'.png'))
(OUT/'layout.json').write_text(json.dumps({'source':'Selective original trial UI conversion requested by user20261106; source SFL transforms and source raster ink; DXT1 black emission keyed for the UI compositor. No original character faces/names.','tiles':records},ensure_ascii=False,indent=2),encoding='utf-8')
print('TRIAL_DIALOGUE_SOURCE',len(records))
