"""Bake original system UI pixels at retained SFL affines; dynamic own text stays native."""
from pathlib import Path
import json,math,copy
import numpy as np
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1];BANK=ROOT/'ui/v3_authorized/pad_system_source';OUT=ROOT/'ui/v4/pad_system_source';S=2

def build():
 OUT.mkdir(parents=True,exist_ok=True)
 import build_v3_armament_layout as resolver
 manifest=json.loads((BANK/'manifest.json').read_text(encoding='utf-8'));resolver.BANK=BANK;resolver.SOLID_NAMES=set(manifest['timelines']);resolver.build()
 data=json.loads((BANK/'layout.json').read_text(encoding='utf-8'));sysc=json.loads((ROOT/'docs/analysis/v3_rebuild/pad_system_ui_contract.json').read_text(encoding='utf-8'));pages=json.loads((ROOT/'docs/analysis/v3_rebuild/pad_system_connection_contract.json').read_text(encoding='utf-8'))['cached_sfl_geometry'];result={'assets':{},'systemStates':[],'missingSourceTextures':manifest['errors'],'source':'Original system UI SFL affine, source RGBA/masks, own Korean dynamic names and text. No original character faces or names used in runtime.'}
 def raster(row,bounds,dy=0):
  size=(max(1,round(bounds[2]*S)),max(1,round(bounds[3]*S)));blank=Image.new('RGBA',size)
  if row['opacity']<=0:return blank
  im=Image.new('RGBA',(1,1),'black' if row['resource']=='__solid_black' else 'white') if row['resource'].startswith('__solid_') else Image.open(ROOT/row['texture']).convert('RGBA')
  if 'DXT1' in row['resource'] and not row['resource'].startswith(('dammy','beta','black')):
   arr=np.array(im);arr[:,:,3]=np.minimum(arr[:,:,3],arr[:,:,:3].max(axis=2));im=Image.fromarray(arr)
  mul,add=row['colorMultiply'],row['colorAdd']
  if mul!=[1,1,1] or add!=[0,0,0]:
   arr=np.array(im,dtype=np.float32);arr[:,:,:3]=np.clip(arr[:,:,:3]*mul+np.array(add)*255,0,255);im=Image.fromarray(arr.astype('uint8'))
  a,b,c,d,x,y=row['sourceAffine'];rw=row['rect'][2]*1.5/math.hypot(a,b);rh=row['rect'][3]*1.5/math.hypot(c,d);a,b,c,d=[a*rw/im.width,b*rw/im.width,c*rh/im.height,d*rh/im.height];a,b,c,d,x,y=[v*2/3*S for v in [a,b,c,d,x,y]];x-=bounds[0]*S;y+=(dy-bounds[1])*S;det=a*d-b*c
  if abs(det)<1e-10:return blank
  out=im.transform(size,Image.Transform.AFFINE,(d/det,-c/det,(c*y-d*x)/det,-b/det,a/det,(b*x-a*y)/det),Image.Resampling.BICUBIC);alpha=out.getchannel('A').point(lambda v:round(v*row['opacity']))
  for clip in row.get('clips',[]):
   mask=Image.new('RGBA',size)
   for child in clip:mask.alpha_composite(raster(child,bounds,dy))
   alpha=ImageChops.multiply(alpha,mask.getchannel('A'))
  out.putalpha(alpha);return out
 def save(id,rows,bounds,dy=0):
  out=Image.new('RGBA',(max(1,round(bounds[2]*S)),max(1,round(bounds[3]*S))))
  for row in rows:out.alpha_composite(raster(row,bounds,dy))
  file=id+'.png';out.save(OUT/file);result['assets'][id]={'file':file,'rect':bounds};return id
 def pick(rows,prefix):return [r for r in rows if r['path'].startswith(prefix)]
 def leaf(leaves,path):return next(r for r in leaves if r['path']==path)
 def group_rect(rows):
  pts=[]
  for r in rows:
   a,b,c,d,x,y=r['sourceAffine'];w=r['rect'][2]*1.5/math.hypot(a,b);h=r['rect'][3]*1.5/math.hypot(c,d);pts.extend([(x*2/3,y*2/3),((x+a*w)*2/3,(y+b*w)*2/3),((x+c*h)*2/3,(y+d*h)*2/3),((x+a*w+c*h)*2/3,(y+b*w+d*h)*2/3)])
  if not pts:return [0,0,1,1]
  xs,ys=zip(*pts);return [min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys)]
 def orig_path(p):return p.replace('/depth1','/1').replace('/d1','/1').replace('/d2','/2').replace('/d3','/3')
 rows=data['techou_system_US']['states']['fl_backlog'];full=[0,0,1280,720]
 save('system_background',[r for r in rows if r['path'].startswith(('i_setumei_base_beta','i_icon_base_beta','p_setumei_base_color','p_line_waku_')) or r['resource']=='notice_base_000.png'],full)
 for i,key in enumerate(sysc['entries']):
  contractBase=leaf(sysc['leaves'],f'p_icon_base_{i:03d}/i_icon_beta/depth1')['rect_1280'];contractIcon=next(r['rect_1280'] for r in sysc['leaves'] if r['path'].startswith('p_icon_'+key+'/') and '_color/' in r['path']);lift=sysc['selection_lift_1280'];offRect=[contractBase[0],contractBase[1]+(lift if i==0 else 0),*contractBase[2:]];offIcon=[contractIcon[0],contractIcon[1]+(lift if i==0 else 0),*contractIcon[2:]]
  entry={}
  for active in [False,True]:
   selected=data['techou_system_US']['states']['fl_'+(key if active else ('save' if i==0 else 'backlog'))];dy=lift if active else 0
   for part,ps,rect in [('base',f'p_icon_base_{i:03d}/',offRect),('icon','p_icon_'+key+'/',offIcon)]:
    id=f'system_{part}_{i}_'+('on' if active else 'off');save(id,pick(selected,ps),rect,dy);entry[part+('On' if active else 'Off')]=id
  result['systemStates'].append(entry)
 for i in range(4):
  rr=pick(rows,f'i_act_waku/i_line_{i:03d}/');
  if i==0:rr+=pick(rows,'p_act_waku_color_')+[r for r in rows if r['path'].startswith('i_act_waku/i_sankaku_')]
  save('SyActive'+str(i),rr,group_rect(rr))
 # Common modal uses actual outer/inner/body pixels, retaining separate own text carriers.
 rows=data['common_window']['states']['fl_wait_2_2'];save('confirm_background',[r for r in rows if not r['path'].startswith(('i_choice_off_','p_choise_'))],full)
 off=next(r for r in rows if r['path']=='i_choice_off_00/1');on=next(r for r in rows if r['path']=='p_choise_00/i_choise/1')
 save('choice_off',[off],off['rect']);save('choice_on',[on],on['rect'])
 # Backlog names and portraits are dynamic and never composed from original character RGB.
 rows=data['common_backlog_US']['states']['fl_wait_1'];save('backlog_background',[r for r in rows if r['path']=='i_sitazi/1' or r['path'].startswith('i_off_') or r['path'] in ['i_black/1','i_white_000/1','p_scroll/1']],full)
 for i in range(4):
  rr=pick(rows,f'p_name_base_off_{i:03d}/');rr=[r for r in rr if '/p_vol_' not in r['path']];rect=pages['backlog_row1']['leaves'];r=leaf(rect,f'p_name_base_off_{i:03d}/i_name_bata/d1')['rect_1280'];save('BlPlate'+str(i),rr,r)
 rows=data['st_save_load']['states']['fl_wait_0'];save('storage_background',[r for r in rows if not r['path'].startswith(('i_tab_','i_ef_on/','p_icon_'))],full)
 for i in range(6):
  for d in range(3):
   rr=[r for r in rows if r['path']==f'i_tab_{i:03d}/{d+1}'];rect=leaf(pages['save_load_wait0']['leaves'],f'i_tab_{i:03d}/d{d+1}')['rect_1280'];save(f'SvTab{i}_{d}',rr,rect)
 active=pick(rows,'i_ef_on/');save('SvActive',active,group_rect(active))
 rows=data['st_load']['states']['fl_wait'];save('load_background',[r for r in rows if not r['path'].startswith(('i_off_','p_icon/'))],full)
 for state,label in [('off','fl_wait'),('on','fl_wait_on_00')]:
  rr=[r for r in data['st_load']['states'][label] if r['path']==('i_off_00/1' if state=='off' else 'i_on/1')];save('load_choice_'+state,rr,group_rect(rr))
 rows=data['techou_system_kisekae_US']['states']['fl_wait_0'];save('theme_background',[r for r in rows if not r['path'].startswith(('p_number_','p_new_set_','p_image/','p_notice_tx','p_image_text/p_image_tx','p_act_ef'))],full)
 rr=pick(rows,'p_act_ef/');save('ThActive',rr,group_rect(rr))
 (OUT/'layout.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('PAD_SYSTEM_RENDER',len(result['assets']))
if __name__=='__main__':build()
