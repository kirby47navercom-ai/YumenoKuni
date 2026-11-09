"""Compose original ADV/choice UI at decoded affine geometry; no engine or game execution."""
from pathlib import Path
import json,math,copy,hashlib
import numpy as np
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1];BANK=ROOT/'ui/v3_authorized/adv_source';OUT=ROOT/'ui/v4/adv_source';OUT.mkdir(parents=True,exist_ok=True)
SCALE=2;SIZE=(1280*SCALE,720*SCALE)

def layer(row):
 if not row['opacity']:return Image.new('RGBA',SIZE)
 im=Image.new('RGBA',(2,2),'black' if row['resource']=='__solid_black' else 'white') if row['resource'].startswith('__solid_') else Image.open(ROOT/row['texture']).convert('RGBA')
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

def phase(rows,name):
 out=copy.deepcopy(rows)
 def skin(row):
  resource=row['resource'];target=resource.replace('_day','_'+name)
  file=Path(row['texture']).with_name(target+'.png')
  if name!='day' and resource!=target and (ROOT/file).exists():row['resource']=target;row['texture']=file.as_posix()
  for group in row.get('clips',[]):
   for child in group:skin(child)
 for row in out:skin(row)
 return out

def main():
 layout=json.loads((BANK/'layout.json').read_text(encoding='utf-8'));tiles={}
 def save(name,im,crop=False):
  box=im.getbbox() if crop else (0,0,*SIZE);assert box
  file=name+'.png';im.crop(box).save(OUT/file);tiles[name]={'file':file,'rect':[box[0]/SCALE,box[1]/SCALE,(box[2]-box[0])/SCALE,(box[3]-box[1])/SCALE]}
 for palette in ['day','night','close']:
  for key,label in [('normal','fl_nomal_wait'),('hero','fl_hero_wait'),('nameless','fl_wait')]:save('adv_'+palette+'_'+key,composite(phase(layout['adv_kaiwa_window']['states'][label],palette)))
  for key,label in [('next','fl_wait'),('auto','fl_auto_wait')]:save(key+'_'+palette,composite(phase(layout['adv_common_page_US']['states'][label],palette)),True)
 save('event',composite(layout['adv_event_window']['states']['fl_wait']))
 # All three source textures retain their actual alpha/ink. Geometry/focus/commit
 # remains owned by the current source tracks, not a second input controller.
 for key,resource in [('choice_off','choice_off.png'),('choice_on','choice_on.png'),('choice_check','t_choice_check_000.png')]:
  im=Image.open(BANK/'adv_choices'/(resource+'.png')).convert('RGBA');im.save(OUT/(key+'.png'));tiles[key]={'file':key+'.png','size':list(im.size)}
 # Preserve the source confirm color-transform progression, rather than a plain
 # white rectangle. The existing controller still owns focus coordinates/time.
 choice=layout['adv_choices'];confirm={}
 raw=Image.open(OUT/'choice_on.png').convert('RGBA')
 for count in [2,3,4]:
  for index in range(count):
   first=choice['labels'][f'fl_ok_{count}_{index+1}']-choice['labels']['fl_in_4'];slot=4-count+index;names=[]
   for frame in range(12):
    rows=[r for r in choice['frames'][first+frame] if r['path'].startswith(f'i_act_{slot:03d}/')]
    result=Image.new('RGBA',raw.size)
    for r in rows:
     a=np.array(raw,dtype=np.float32);a[:,:,:3]=np.clip(a[:,:,:3]*r['colorMultiply']+np.array(r['colorAdd'])*255,0,255);a[:,:,3]*=r['opacity'];result.alpha_composite(Image.fromarray(a.astype('uint8')))
    name=f'choice_confirm_{count}_{index}_{frame}';result.save(OUT/(name+'.png'));names.append(name+'.png')
   confirm[f'{count}:{index}']=names
 im=Image.open(OUT/'choice_confirm_2_0_7.png');im.save(OUT/'choice_flash.png');tiles['choice_flash']={'file':'choice_flash.png','size':list(im.size),'scope':'Actual original confirm frame7 colorMultiply/colorAdd/alpha, not a white rectangle.'}
 manifest={'source':'User20261107 all-UI original-equivalent request. Original bitmap alpha/RGB and decoded source affine; own dialogue text/names/portraits remain separate. Static settled phases, no claim of all original runtime animation or additive shaders.','tiles':tiles,'confirmationFrames':confirm}
 (OUT/'layout.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print('ADV_SOURCE',len(tiles))
if __name__=='__main__':main()
