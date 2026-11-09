"""Original trial input motion and digital clocks, with own cast in source card geometry."""
from pathlib import Path
import json,sys,hashlib,math,re
import numpy as np
from PIL import Image,ImageFilter
import import_v3_climax_ui as resolver
import build_trial_input_source_art as raster
ROOT=Path(__file__).resolve().parents[1];BANK=ROOT/'ui/v3_authorized/trial_inputs';OUT=ROOT/'ui/v4/trial_inputs_motion';OUT.mkdir(parents=True,exist_ok=True)
M=json.loads((BANK/'manifest.json').read_text(encoding='utf-8'));resolver.OUT=OUT;L=resolver.layout(M);raster.OUT=OUT;raster.records={};raster.L=L;raster.M=M
ASSET='Assets/Art/ui/v3/trial_inputs_motion/';textures={};copies={}
def source(container,resource):return next(r for r in M['textures']if r['container']==container and r['resource']==resource)
def image(file,resource):
 im=Image.open(ROOT/file).convert('RGBA')
 if resource.endswith('_DXT1.png'):
  a=np.array(im,dtype=np.float32);alpha=a[:,:,:3].max(axis=2);a[:,:,:3]*=255/np.maximum(alpha[:,:,None],1);a[:,:,3]=alpha;im=Image.fromarray(np.clip(a,0,255).astype('uint8'))
 return im
def asset(im,key):
 digest=hashlib.sha256(key.encode()).hexdigest()[:18];n='r_'+digest+'.png';dest=OUT/n
 if n not in copies:im.save(dest);copies[n]=str(dest.relative_to(ROOT)).replace('\\','/')
 return ASSET+n

def leaf(row,shift=(640,360)):
 if row['resource'].startswith('__solid_'):return None
 key=json.dumps([row['texture'],row['colorMultiply'],row['colorAdd'],row['sourceAffine'][0]*row['sourceAffine'][3]-row['sourceAffine'][1]*row['sourceAffine'][2]<0])
 if key not in textures:
  im=image(row['texture'],row['resource']);a=np.array(im,dtype=np.float32);a[:,:,:3]=np.clip(a[:,:,:3]*row['colorMultiply']+np.array(row['colorAdd'])*255,0,255);im=Image.fromarray(a.astype('uint8'))
  if row['sourceAffine'][0]*row['sourceAffine'][3]-row['sourceAffine'][1]*row['sourceAffine'][2]<0:im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  textures[key]=asset(im,key)
 r=row['rect'];return [textures[key],r[0]+shift[0],r[1]+shift[1],r[2],r[3],row['rotation'],row['opacity']]

def frame(rows):
 assert not any(r.get('clips')for r in rows),'Use original mask renderer for clipped family'
 return [v for r in rows if (v:=leaf(r)) and v[-1]>.00001]

tracks={}
for key,name,start,stop in [('intro','t_tohyo_start_US','fl_in','fl_wait'),('press','t_tohyo_bt_US','fl_press','fl_out'),('timeout','t_tohyo_timeup_US','fl_in','fl_wait')]:
 v=L[name];tracks[key]=[frame(f)for f in v['frames'][v['labels'][start]:v['labels'][stop]+1]]
assert max(len(f)for frames in tracks.values()for f in frames)<=25

clocks={}
for kind,name,shift in [('choice','t_choice_frame_US',(0,0)),('bullet','t_ktdm_time',(0,0)),('vote','t_tohyo_time',(640,360))]:
 # The second group is the authored flickering afterimage, not nine extra clock slots.
 rows=[r for r in L[name]['states']['fl_wait']if re.search(r'time_num_\d+',r['resource']) and r['opacity']==1];rows.sort(key=lambda r:r['rect'][0]);assert len(rows)==9,(kind,len(rows))
 digits={}
 for num in range(11):
  rec=next(t for t in M['textures']if t['container']==name and re.search(r'time_num_'+str(num).zfill(3)+r'\.png$',t['resource']));digits[str(num)]=asset(image(rec['file'],rec['resource']),kind+'clock'+str(num))
 clocks[kind]={'digits':digits,'rects':[[r['rect'][0]+shift[0],r['rect'][1]+shift[1],*r['rect'][2:]]for r in rows]}
 raster.save(kind+'_clock_base',raster.comp([r for r in L[name]['states']['fl_wait']if not re.search(r'time_num_\d+',r['resource']) and not r['resource'].startswith('__solid_')],shift),True)

# The source flat frame and actual localized Answer art replace handmade title ink.
raster.save('choice_decor',raster.comp([r for r in L['t_choice_frame_US']['states']['fl_wait_lang']if r['resource'].startswith('t_choice_frame_')or r['resource'].startswith('t_choice_tx_lang')]),True)
# Keep the original masked sand movement, mapped over the authored duration.
v=L['t_choice_time'];start=v['labels']['fl_start'];glass=[]
for i in range(61):
 at=start+round(i*(len(v['frames'])-1-start)/60);rows=[r for r in v['frames'][at]if not r['resource'].startswith('__solid_')];name='choice_glass_'+str(i);raster.save(name,raster.comp(rows));glass.append(name)

# The normal gun carrier is a 3D mask/stripe material, not a flat blue wheel.
# Use the original evidence-selector wheel's authored affine/color as the own UI adapter.
raster.save('bullet_cylinder',raster.comp(L['t_ktdm_sele']['states']['fl_wait']),True)
raster.save('bullet_scroll',raster.comp(L['t_ktdm_sele_scr']['states']['fl_wait']),True)
# The standalone selector uses the cyan focus, unlike the yellow loaded bullet.
for on in [False,True]:
 out=Image.new('RGBA',(670,128))
 colors=[[1,1,1],[1,1,1]if on else [.2,.2,.2],[0,.7,1]if on else [.15,.15,.15]]
 for stem,color in zip(['t_bullet_base','t_bullet','t_bullet_glow'],colors):
  for i,(x,w)in enumerate([(0,64),(64,542),(606,64)]):
   r=source('trial_bullet',stem+f'_{i:03d}.png');im=Image.open(ROOT/r['file']).convert('RGBA');a=np.array(im,dtype=np.float32);a[:,:,:3]*=color;im=Image.fromarray(np.clip(a,0,255).astype('uint8')).resize((w,128),Image.Resampling.LANCZOS);out.alpha_composite(im,(x,0))
 box=out.getbbox();out=out.crop((0,box[1],670,box[3]));n='bullet_row_'+('on'if on else'off');file=OUT/(n+'.png');out.save(file);raster.records[n]={'file':file.relative_to(ROOT).as_posix(),'rect':[0,0,670,out.height],'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
raster.save('spot_cursor',raster.comp([r for r in L['t_sub_spot_cursor']['states']['fl_wait']if '_base_' in r['resource']or '_dot_' in r['resource']],(640,360)))
spotLock=[];v=L['t_sub_spot_cursor']
for i in range(v['labels']['fl_lock'],v['labels']['fl_lock_wait']+1):
 name='spot_lock_'+str(i-v['labels']['fl_lock']);raster.save(name,raster.comp([r for r in v['frames'][i]if 'cursor_line'not in r['resource']and not r['resource'].startswith('__solid_')],(640,360)));spotLock.append(name)

# Localized voting title and exact source card positions; no original cast is displayed.
t=next(t for t in M['textures']if t['container']=='t_tohyo_title_US'and 'title_tx_' in t['resource']);voteTitle=asset(image(t['file'],t['resource']),'vote-title-korean')
cardRows=[r for r in L['t_tohyo_chara_US']['states']['fl_wait']if re.fullmatch(r't_tohyo_chara_frame_\d+_blank\.png',r['resource'])];assert len(cardRows)==16
raster.save('vote_title_complete',raster.comp(L['t_tohyo_title_US']['states']['fl_wait'],(640,360)),True)
raster.save('vote_name_complete',raster.comp([r for r in L['t_tohyo_name_US']['states']['fl_wait']if '_pl_'in r['resource']],(640,360)),True)
deadRec=next(t for t in M['textures']if t['container']=='t_tohyo_chara_US'and t['resource']=='t_tohyo_chara_dead_000.png');deadAsset=asset(image(deadRec['file'],deadRec['resource']),'vote-dead')
cards=[]
for i,r in enumerate(cardRows):
 q=r['rect'];cards.append([q[0]+640,q[1]+360,q[2],q[3]])

result={'schema':'v3-trial-input-motion-v1','sourceManifestSHA256':hashlib.sha256((BANK/'manifest.json').read_bytes()).hexdigest(),'copies':copies,'rasters':raster.records,'clocks':clocks,'glass':glass,'tracks':tracks,'voteCards':cards,'voteTitle':voteTitle,'voteTitleRect':[469.333333,32,341.333333,85.333333],'votePortraitRect':[319.6,-1.8,1365.333333,1365.333333],'scope':'Original SFL labels/affine/alpha and supplied Korean PNGs. Additive DXT1 is explicitly converted for normal-alpha own UI. Not original GPU blend/3D projection or human usability acceptance.'}
result['voteDead']=deadAsset
result['spotLock']=spotLock
raster.save('vote_result_back',raster.comp(L['t_tosen_bg_US']['states']['fl_wait'],(640,360)),True)
raster.save('vote_result_board',raster.comp([r for r in L['t_tosen_memori_US']['states']['fl_wait']if '_pl_'in r['resource']],(640,360)),True)
raster.save('vote_result_name',raster.comp([r for r in L['t_tosen_name_US']['states']['fl_wait']if '_pl_'in r['resource']],(640,360)),True)
marker=next(t for t in M['textures']if t['container']=='t_tosen_memori_US'and t['resource']=='t_tosen_memori_000.png');result['voteMark']=asset(image(marker['file'],marker['resource']),'original-vote-mark')
result['voteResultFaces']=[[r['rect'][0]+640,r['rect'][1]+360,*r['rect'][2:]]for r in L['t_tosen_memori_US']['states']['fl_wait']if re.fullmatch(r't_tosen_memori_chara_\d+.png',r['resource'])and r['rect'][0]<640 and r['rect'][1]<360]
result['voteResultNames']=[[r['rect'][0]+640,r['rect'][1]+360,*r['rect'][2:]]for r in L['t_tosen_memori_US']['states']['fl_wait']if re.fullmatch(r't_tohyo_name_tx_\d+_2_US.png',r['resource'])and r['rect'][0]<640 and r['rect'][1]<360]
assert len(result['voteResultFaces'])==len(result['voteResultNames'])==16
(OUT/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8');print(json.dumps({'tracks':{k:len(v)for k,v in tracks.items()},'copies':len(copies),'glass':len(glass),'sourceRasters':len(raster.records)}))
