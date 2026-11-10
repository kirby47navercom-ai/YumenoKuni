"""Bake source-affine Climax generic UI into cropped alpha tiles (no game run)."""
from pathlib import Path
import json,math,re,hashlib
import numpy as np
from PIL import Image,ImageChops,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
BANK=ROOT/'ui/v4/climax_original_20261106'
OUT=BANK/'baked'
SCALE=2/3
def read(p):return json.loads(p.read_text(encoding='utf8'))
def build():
 core=read(BANK/'core.json');OUT.mkdir(exist_ok=True)
 texture_info={v['file']:v for v in core['textures'].values()}
 def bounds(row):
  a,b,c,d,x,y=row['sourceAffine'];p=row['sourceRect'];w=p[1]-p[0];h=p[3]-p[2]
  return[(x,y),(x+a*w,y+b*w),(x+a*w+c*h,y+b*w+d*h),(x+c*h,y+d*h)]
 def tile(name,rows):
  rows=[r for r in rows if r['texture']and r['opacity']>.001]
  if not rows:return None
  q=[p for r in rows for p in bounds(r)];left=math.floor(min(p[0]for p in q))-2;top=math.floor(min(p[1]for p in q))-2
  width=math.ceil(max(p[0]for p in q))-left+2;height=math.ceil(max(p[1]for p in q))-top+2
  assert width<6000 and height<6000,(name,width,height)
  size=(width,height)
  def layer(r):
   im=Image.open(ROOT/r['texture']).convert('RGBA');arr=np.array(im,dtype=np.float32)
   # These source DXT1 glow sprites use additive black. Convert black to alpha
   # for the engine's regular alpha Image; original decoded PNG stays unchanged.
   focus_effect=r['texture']==core['textures']['climax_koma_choise_US/little_koma_ef.png']['file']
   if texture_info[r['texture']]['format']=='DXT1'or focus_effect:arr[:,:,3]*=arr[:,:,:3].max(axis=2)/255
   arr[:,:,:3]=np.clip(arr[:,:,:3]*r['colorMultiply']+np.array(r['colorAdd'])*255,0,255)
   arr[:,:,3]*=r['opacity'];im=Image.fromarray(arr.astype('uint8'))
   a,b,c,d,x,y=r['sourceAffine'];p=r['sourceRect'];w=p[1]-p[0];h=p[3]-p[2]
   a,b,c,d=a*w/im.width,b*w/im.width,c*h/im.height,d*h/im.height;x-=left;y-=top;det=a*d-b*c
   if abs(det)<1e-8:return Image.new('RGBA',size)
   inv=(d/det,-c/det,(c*y-d*x)/det,-b/det,a/det,(b*x-a*y)/det)
   result=im.transform(size,Image.Transform.AFFINE,inv,Image.Resampling.BICUBIC)
   for clip in r.get('clips',[]):
    mask=Image.new('RGBA',size)
    for child in clip:mask.alpha_composite(layer(child))
    result.putalpha(ImageChops.multiply(result.getchannel('A'),mask.getchannel('A')))
   return result
  out=Image.new('RGBA',size)
  for r in rows:out.alpha_composite(layer(r))
  crop=out.getbbox()
  if not crop:return None
  file=OUT/(name+'.png');out.crop(crop).save(file,optimize=True)
  return dict(texture=file.relative_to(ROOT).as_posix(),rect=[(left+crop[0])*SCALE,(top+crop[1])*SCALE,(crop[2]-crop[0])*SCALE,(crop[3]-crop[1])*SCALE],rotation=0,sourceScale=SCALE,sha256=hashlib.sha256(file.read_bytes()).hexdigest())
 core['bakedComponents']={name:tile(name,rows)for name,rows in core['components'].items()}
 core['bakedStockSlots']=[{key:tile('stock'+str(slot['index'])+'_'+key,slot[key])for key in ['idle','used','locked','focus']}for slot in core['stockSlots']]
 core['bakedExpandedStockSlots']=[{key:tile('stockExpanded'+str(slot['index'])+'_'+key,slot[key])for key in ['idle','used','locked','focus']}for slot in core.get('stockExpandedSlots',[])]
 core['bakedHearts']={n:[tile('heart'+n+'_'+str(i),[r])for i,r in enumerate(rows)]for n,rows in core['hearts'].items()}
 # Own HP uses1000/800 damage increments. These are proportional left crops
 # of source full fills, not recovered original half-heart states.
 fractions={}
 for group,hearts in core['bakedHearts'].items():
  fractions[group]=[]
  for index,full in enumerate(hearts):
   source=Image.open(ROOT/full['texture']).convert('RGBA');steps=[None]
   for step in range(1,10):
    width=max(1,round(source.width*step/10));image=source.crop((0,0,width,source.height))
    target=OUT/f'heart{group}_{index}_fraction{step}.png';image.save(target,optimize=True)
    rect=full['rect'];steps.append(dict(texture=target.relative_to(ROOT).as_posix(),rect=[rect[0],rect[1],rect[2]*step/10,rect[3]],rotation=0,sourceScale=SCALE,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
   steps.append(full);fractions[group].append(steps)
 core['bakedHeartFractions']=fractions
 core['heartFractionNotes']=['Project HP fraction presentation only, not recovered original half-heart states.','Groups5/7/10 contain each original heart index and steps0..10. Step0=null;step10 is the unchanged full source tile. Steps1..9 are left pixel-crops of the full baked PNG, with rect.w multiplied bystep/10 and unchanged x/y/h.','Select the proportion using actual remaining HP, without ceil-to-full-heart rounding. Pixel cut width is rounded to the nearest source pixel; no color/alpha pulse or horizontal image compression is added.']
 # Only the actual closed/open-lock branches belong to unlock. Other nested
 # symbols (used tick and US PANEL) are independent runtime-controlled branches.
 # Never bake the original manga thumbnail or those unrelated branches here.
 source_layout=read(BANK/'layout.json')['climax_koma_act_US']
 unlock_samples=[24,28,32,36,40,44,46,48,50,52,55,60,68,76,82,87]
 unlock=[]
 for source_frame in unlock_samples:
  rows=source_layout['frames'][source_frame]
  lock_rows=[r for r in rows if r['path'].startswith(('/p_rock_00/','/i_rock_01/'))]
  own_image=next(r for r in rows if r['path'].startswith('/p_koma_act/'))
  unlock.append(dict(sourceFrame=source_frame,atFrame=source_frame-24,secondsAt60=(source_frame-24)/60,tile=tile('unlock_'+f'{source_frame:03d}',lock_rows),ownImage={k:own_image[k]for k in ['rect','rotation','opacity']}))
 core.setdefault('sequences',{})['unlock']=dict(sourceContainer='climax_koma_act_US',label='fl_rock',sourceStartFrame=24,sourceStopFrame=87,durationFrames=64,fps=60,duration=64/60,runtimeRateVerified=False,playback='step-hold',frames=unlock,replacesStaticComponent='selectedLocked',sourceLayers=['/p_rock_00/','/i_rock_01/'],originalMangaIncluded=False,alphaBaked=True,colorBaked=True,notes=['Exact source affine/color/opacity at16 sampled frames. Hold each tile until the next atFrame; no added tint, opacity pulse or crossfade.','Hide static selectedLocked while this sequence is playing. Keep own manga, frame and localized KOMA badge visible.','ownImage supplies source thumbnail motion only; original image pixels are never included.','Last sample at source87 is empty. Clear animation and unlock input at64/60 seconds. Original runtime FPS remains unverified;60 is this project playback contract.'])
 # Placement verdicts must play their actual source clip, not a held frame23.
 layout=read(BANK/'layout.json');core['placementClips']={}
 for key,container in [('ok','climax_cutin_ok'),('ng','climax_cutin_ng')]:
  source_frames=layout[container]['frames'];start=layout[container]['labels']['fl_in']
  frames=[tile('placement_'+key+'_'+str(i),source_frames[i]) for i in range(start,len(source_frames))]
  core['placementClips'][key]={'fps':60,'runtimeFPSVerified':False,'frames':frames,'durationFrames':len(frames)}
 # Compact/expanded STOCK morphs have independent source timelines.
 core['stockSequenceFiles']={}
 stock_layout=layout['climax_koma_choise_US']
 for key,label in [('open','fl_s_l'),('close','fl_l_s')]:
  timing=core['clipDurations']['stockExpand' if key=='open' else 'stockCollapse'];frames=[]
  for at in range(timing['startFrame'],timing['stopFrame']+1):
   rows=stock_layout['frames'][at];slots=[]
   for i in range(8):
    prefix='/p_'+f'{i:02d}'+'/'
    own=next(r for r in rows if r['path'].startswith(prefix)and'/p_koma_'in r['path'])
    r={'image':[{k:own[k]for k in ['rect','rotation','opacity']}]}
    for variant,token in [('idle','/i_def/'),('used','/p_ok_'),('locked','/p_rock_'),('focus','/p_act_l_')]:
     r[variant]=tile('stock_'+key+'_'+str(at)+'_'+str(i)+'_'+variant,[r for r in rows if r['path'].startswith(prefix)and token in r['path']])
    slots.append(r)
   frames.append({'base':tile('stock_'+key+'_'+str(at)+'_base',[r for r in rows if r['path'].startswith(('/i_base/','/p_stock/'))]),'slots':slots})
  sequence={'fps':60,'runtimeFPSVerified':False,'frames':frames,'durationFrames':len(frames)}
  file=BANK/('stock_'+key+'.json');file.write_text(json.dumps(sequence,separators=(',',':')),encoding='utf8');core['stockSequenceFiles'][key]=file.relative_to(ROOT).as_posix()
 def digits(container,prefix):return[core['textures'][container+'/'+prefix+str(i)+'.png']['file']for i in range(10)]
 core['timerDigits']=digits('climax_time_US','time_no_')
 core['pageDigits']=digits('climax_page_US','no_')
 core['pageActiveDigits']=digits('climax_page_US','act_no_')
 core['lockedRemainingDigits']=digits('climax_koma_choise_US','lock_no_')
 core['bakingNotes']=['Cropped PNGs preserve source affine and source color transforms. Rects use original1920 SFL coordinates scaled2/3; rotation is baked, including shear.','DXT1 additive-black glow sprites have luminance-derived presentation alpha; raw decoded PNGs remain unchanged.','The single BC7 climax_koma_choise_US/little_koma_ef.png also uses luminance-derived presentation alpha in28 compact/expanded focus tiles. This is an ordinary Image glow adaptation, not a claim that the original blend equation was recovered. Raw pixels and source focus-above-image draw order remain unchanged.','No data_3d projection is applied; body source space differs from final source camera projection.','SelectedPanelWordUS is original PANEL, not video KOMA; do not falsely relabel its pixels.']
 # core is build-time provenance; only runtime.json must meet DataGet limits.
 payload=json.dumps(core,ensure_ascii=False,separators=(',',':'))
 (BANK/'core.json').write_text(payload,encoding='utf8')
 # The provenance-rich core exceeds the engine's 10k JSON-node runtime ceiling.
 # Keep it build-time only, and emit the same integration fields without raw
 # per-branch affines or whole texture metadata for runtime DataGet consumers.
 runtime={k:v for k,v in core.items()if k not in ['components','hearts','textures','data3d','stockSlots','stockExpandedSlots']}
 for key in ['stockSlots','stockExpandedSlots']:
  runtime[key]=[dict(index=s['index'],image=[{k:r[k]for k in ['rect','rotation','sourceAffine','sourceRect']}for r in s['image']])for s in core[key]]
 count=lambda v:1+(sum(count(a)for a in v.values())if isinstance(v,dict)else sum(count(a)for a in v)if isinstance(v,list)else 0)
 runtime['schema']='v3-climax-compact-runtime-v1';runtime['provenanceFile']='ui/v4/climax_original_20261106/core.json'
 assert count(runtime)<10000
 runtime_payload=json.dumps(runtime,ensure_ascii=False,separators=(',',':'));assert len(runtime_payload)<262144
 (BANK/'runtime.json').write_text(runtime_payload,encoding='utf8')
 print(json.dumps(dict(coreBytes=len(payload.encode()),bakedComponents=len(core['bakedComponents']),tiles=len(list(OUT.glob('*.png'))))))
 # Generic source UI visual audit, no original narrative artwork.
 preview=Image.new('RGBA',(1280,720),(45,36,60,255))
 for name in ['pageBar','pageWord','stockBase','stockWord','selectedPanelFrame','selectedPanelWordUS','captionPlate','heartBase10','timerBase']:
  r=core['bakedComponents'][name]
  if r:
   im=Image.open(ROOT/r['texture']);x,y,w,h=r['rect'];preview.alpha_composite(im.resize((round(w),round(h)),Image.Resampling.LANCZOS),(round(x),round(y)))
 for r in core['bakedHearts']['10']:
  im=Image.open(ROOT/r['texture']);x,y,w,h=r['rect'];preview.alpha_composite(im.resize((round(w),round(h)),Image.Resampling.LANCZOS),(round(x),round(y)))
 preview.convert('RGB').save('C:/Users/kirby/Downloads/v3_re/native/climax-ui-20261106/core-preview.jpg')
 # Contact sheet of the generic lock only, evaluated at original sampled frames.
 contact=Image.new('RGBA',(960,720),(48,32,60,255));draw=ImageDraw.Draw(contact)
 for i,frame in enumerate(unlock):
  x=(i%4)*240;y=(i//4)*180;record=frame['tile']
  if record:
   im=Image.open(ROOT/record['texture']).convert('RGBA');im.thumbnail((170,145),Image.Resampling.LANCZOS);contact.alpha_composite(im,(x+25,y+20))
  draw.text((x+8,y+4),'source '+str(frame['sourceFrame']),fill='white')
 contact.convert('RGB').save('C:/Users/kirby/Downloads/v3_re/native/climax-ui-20261106/unlock-contact.jpg')
 return core
if __name__=='__main__':build()
