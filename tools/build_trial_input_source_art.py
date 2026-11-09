"""Rasterize admitted original trial-input UI display lists, no game execution."""
from pathlib import Path
import json,math,copy,hashlib
from functools import lru_cache
import numpy as np
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1];BANK=ROOT/'ui/v3_authorized/trial_inputs';OUT=ROOT/'ui/v4/trial_inputs_source';OUT.mkdir(parents=True,exist_ok=True)
L=json.loads((BANK/'layout.json').read_text(encoding='utf-8'));M=json.loads((BANK/'manifest.json').read_text(encoding='utf-8'));S=2;SIZE=(2560,1440);records={}
@lru_cache(maxsize=64)
def texture(file,resource):
 im=Image.open(ROOT/file).convert('RGBA')
 if resource.endswith('_DXT1.png'):
  a=np.array(im,dtype=np.float32);alpha=a[:,:,:3].max(axis=2);ratio=255/np.maximum(1,alpha);a[:,:,:3]*=ratio[:,:,None];a[:,:,3]=alpha;im=Image.fromarray(np.clip(a,0,255).astype('uint8'))
 return im

def layer(row,shift=(0,0)):
 if row['opacity']<=0:return Image.new('RGBA',SIZE)
 im=Image.new('RGBA',(1,1),'black' if row['resource']=='__solid_black' else 'white') if row['resource'].startswith('__solid_') else texture(row['texture'],row['resource']).copy()
 a=np.array(im,dtype=np.float32);a[:,:,:3]=np.clip(a[:,:,:3]*row['colorMultiply']+np.array(row['colorAdd'])*255,0,255);im=Image.fromarray(a.astype('uint8'))
 a,b,c,d,x,y=row['sourceAffine'];rw=row['rect'][2]*1.5/math.hypot(a,b);rh=row['rect'][3]*1.5/math.hypot(c,d);a,b,c,d=[a*rw/im.width,b*rw/im.width,c*rh/im.height,d*rh/im.height];a,b,c,d,x,y=[v*2/3*S for v in [a,b,c,d,x,y]];x+=shift[0]*S;y+=shift[1]*S;det=a*d-b*c
 if abs(det)<1e-10:return Image.new('RGBA',SIZE)
 out=im.transform(SIZE,Image.Transform.AFFINE,(d/det,-c/det,(c*y-d*x)/det,-b/det,a/det,(b*x-a*y)/det),Image.Resampling.BICUBIC);alpha=out.getchannel('A').point(lambda v:round(v*min(1,row['opacity'])))
 for clip in row.get('clips',[]):
  mask=Image.new('RGBA',SIZE)
  for child in clip:mask.alpha_composite(layer(child,shift))
  alpha=ImageChops.multiply(alpha,mask.getchannel('A'))
 out.putalpha(alpha);return out

def comp(rows,shift=(0,0)):
 out=Image.new('RGBA',SIZE)
 for r in rows:out.alpha_composite(layer(r,shift))
 return out

def save(name,im,full=False):
 box=(0,0,*SIZE) if full else im.getbbox();assert box,(name,'empty source');im=im.crop(box);file=OUT/(name+'.png');im.save(file);records[name]={'file':file.relative_to(ROOT).as_posix(),'rect':[box[0]/S,box[1]/S,(box[2]-box[0])/S,(box[3]-box[1])/S],'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}

def rows(name,label='fl_wait'):return L[name]['states'][label]
def res(name,resource):return next(r for r in M['textures'] if r['container']==name and r['resource']==resource)
def direct(name,container,resource,opacity=1):
 r=res(container,resource);im=texture(r['file'],resource).copy();im.putalpha(im.getchannel('A').point(lambda v:round(v*opacity)));f=OUT/(name+'.png');im.save(f);records[name]={'file':f.relative_to(ROOT).as_posix(),'rect':[0,0,im.width,im.height],'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}

def main():
 save('picker_seat',comp([r for r in rows('t_sub_jinbutu_zaseki_US') if not r['path'].lstrip('/').startswith(('_a_dead_','p_line_')) and '_name_' not in r['resource']]),True)
 for i in range(16):
  n=f'{i:03d}';save('picker_seat_'+str(i),comp([r for r in rows('t_sub_jinbutu_zaseki_US') if r['path'].lstrip('/').startswith('p_line_'+n+'/')]),True);save('picker_dead_'+str(i),comp([r for r in rows('t_sub_jinbutu_zaseki_US') if r['path'].lstrip('/').startswith('_a_dead_'+n+'/')]),True)
 save('picker_person_back',comp(rows('t_sub_jinbutu_pl')),True)
 for side,r in zip(['left','right'],rows('t_sub_jinbutu_arrow')):save('picker_arrow_'+side,layer(r))
 save('picker_title',comp([r for r in rows('t_sub_title_US') if not any(t in r['resource'] for t in ['monokumark','chpt_num','_JP.png'])]),True)
 save('picker_evidence_back',comp([r for r in rows('t_ktdm_detail') if not r['path'].startswith('p_t_ktdm_detail_img')]),True)
 save('picker_guide',comp(rows('t_sub_mondai')))
 for on in [False,True]:
  out=Image.new('RGBA',(670,128));colors=[[1,1,1],[1,1,1] if on else [.7,.7,.7],[1,.84,0] if on else [.55,.55,.55]]
  for stem,color in zip(['t_bullet_base','t_bullet','t_bullet_glow'],colors):
   for i,(x,w) in enumerate([(0,64),(64,542),(606,64)]):
    r=next(r for r in M['textures'] if r['container']=='trial_bullet' and r['resource']==stem+f'_{i:03d}.png');im=Image.open(ROOT/r['file']).convert('RGBA');a=np.array(im,dtype=np.float32);a[:,:,:3]*=color;im=Image.fromarray(np.clip(a,0,255).astype('uint8')).resize((w,128),Image.Resampling.LANCZOS);out.alpha_composite(im,(x,0))
  # Source strips contain transparent vertical padding. Crop only that padding.
  box=out.getbbox();out=out.crop((0,box[1],670,box[3]));f=OUT/('picker_bullet_'+('on' if on else 'off')+'.png');out.save(f);records[f.stem]={'file':f.relative_to(ROOT).as_posix(),'rect':[0,0,670,out.height],'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 save('choice_frame',comp([r for r in rows('t_choice_frame_US') if 'frame' in r['resource']]),True)
 direct('choice_check','t_choice','t_choice_check_000.png')
 for i in range(4):direct('choice_number_'+str(i),'t_choice',f't_choice_num_{i:03d}.png')
 for key,resource in [('middle','t_choice_cursor_001.png'),('edge','t_choice_cursor_000.png'),('gray','t_choice_cursor_002.png')]:direct('choice_'+key,'t_choice',resource)
 # Voting SFL is centered on (0,0); translate its original plane to the 1280x720 UI canvas.
 save('vote_stage',Image.new('RGBA',SIZE,(0,0,0,255)),True) # Cleared-backdrop adapter; do not use the GUILTY introduction cutin as the live input backdrop.
 save('vote_frame',comp(rows('t_tohyo_frame'),(640,360)),True)
 direct('vote_portrait_on','t_tohyo_cursor','t_tohyo_chara_frame_cursor_000.png');direct('vote_portrait_off','t_tohyo_cursor','t_tohyo_chara_frame_cursor_000.png',0)
 save('vote_title',comp([r for r in rows('t_tohyo_title_US') if 'title_tx' not in r['resource']],(640,360)))
 save('vote_name',comp([r for r in rows('t_tohyo_name_US') if '_pl_' in r['resource']],(640,360)))
 save('vote_commit',comp(rows('t_tohyo_bt_US')))
 save('vote_time',comp([r for r in rows('t_tohyo_time') if '_num_' not in r['resource']],(640,360)))
 (OUT/'manifest.json').write_text(json.dumps({'sourceManifest':'ui/v3_authorized/trial_inputs/manifest.json','records':records,'scope':'Source SFL affine/crop/mask; black-matte adapter for additive DXT1, own evidence/name/face excluded. Static textures, runtime state contracts unchanged.'},ensure_ascii=False,indent=2),encoding='utf-8');print('TRIAL_INPUT_SOURCE_ART',len(records))
if __name__=='__main__':main()
