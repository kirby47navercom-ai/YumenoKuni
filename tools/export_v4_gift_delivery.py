"""Technical component isolation, no repaint: avoid cutting atlas icons at guessed grid lines."""
from pathlib import Path
import json,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'art/gifts_v4/delivery';O.mkdir(parents=True,exist_ok=True);Q=R/'Game/Saved/v4-gift-delivery';Q.mkdir(parents=True,exist_ok=True);records=[]
metadata=sorted((R/'art/completion_v4/gift_icons').glob('gift_icons_*.json'))
correction=R/'art/completion_v4/gift_icons/gift_object_corrections_r2.json'
if correction.exists():metadata.append(correction)
latest={}
for p in metadata:
 j=json.loads(p.read_text(encoding='utf8'));im=Image.open(R/j['source_file']).convert('RGBA');a=np.array(im)[:,:,3];H,W=a.shape;n,labels,stats,centroids=cv2.connectedComponentsWithStats((a>24).astype('uint8'),8)
 # The atlas defines ordering. Whole connected pieces choose a cell by center,
 # rather than clipping long object edges at an inaccurate equal-grid boundary.
 positions=[]
 for opt in j['options']:
  uv=j['option_uv'][opt['key']];positions.append((((uv[0]+uv[2])/2*W,(uv[1]+uv[3])/2*H),opt))
 target=np.zeros(n,dtype='int16')-1
 for k in range(1,n):
  if stats[k,cv2.CC_STAT_AREA]<3:continue
  x,y=centroids[k];dist=[(x-c[0])**2+(y-c[1])**2 for c,_ in positions];target[k]=int(np.argmin(dist))
 with Image.open(R/j['hd_file']) as raw:hd=raw.convert('RGBA');hw,hh=hd.size
 for i,(center,opt) in enumerate(positions):
  assigned=(target[labels]==i).astype('uint8')*255
  assert assigned.max()==255,(p,opt['key'])
  # Binary extraction mask only; never square the real alpha or recolor pixels.
  mask=Image.fromarray(cv2.dilate(assigned,np.ones((3,3),np.uint8))).resize((hw,hh),Image.Resampling.NEAREST)
  arr=np.asarray(hd).copy();arr[:,:,3]=np.where(np.asarray(mask)>0,arr[:,:,3],0);isolated=Image.fromarray(arr,'RGBA');bbox=isolated.getbbox();tile=isolated.crop(bbox);original_size=tile.size;tile.thumbnail((1536,1536),Image.Resampling.LANCZOS)
  canvas=Image.new('RGBA',(2048,2048));canvas.alpha_composite(tile,((2048-tile.width)//2,(2048-tile.height)//2));dest=O/(opt['key']+'.png');canvas.save(dest);canvas.save(dest.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
  with Image.open(dest.with_suffix('.webp')) as q:assert q.convert('RGBA').tobytes()==canvas.tobytes()
  rec={'id':opt['key'],'name':opt['inventory_name'],'file':dest.relative_to(R).as_posix(),'webp':dest.with_suffix('.webp').relative_to(R).as_posix(),'size':[2048,2048],'logical_size':[512,512],'atlas':j['id'],'source':j['source_file'],'source_sha256':j['source_image_sha256'],'source_hd':j['hd_file'],'extracted_hd_bbox':list(bbox),'extracted_size':list(original_size),'alpha_bbox':list(canvas.getbbox()),'method':'whole alpha-component technical atlas isolation and uniform contain/padding from complete locally4x source; no new painting/semantic alteration','runtime_integrated':False}
  latest[opt['key']]=rec
records=sorted(latest.values(),key=lambda x:x['id']);items=json.loads((R/'data/gifts.json').read_text(encoding='utf8'))['items'];assert {x['id'] for x in items}=={x['id'] for x in records};assert len(records)==110
for start in range(0,110,20):
 sheet=Image.new('RGB',(1600,1400),'#655e6b');d=ImageDraw.Draw(sheet)
 for i,a in enumerate(records[start:start+20]):
  im=Image.open(R/a['file']).convert('RGBA');im.thumbnail((290,285));x=i%5*320+12;y=i//5*350+8;sheet.paste(im,(x,y),im);d.text((x+8,y+294),a['id']+' / '+a['atlas'],fill='white')
 sheet.save(Q/f'icons_{start//20+1:02d}.jpg',quality=96)
(O/'manifest.json').write_text(json.dumps({'status':'110original inventory icon deliveries; visual review separate','count':110,'assets':records,'legacy_imported_wiki_icons':'preserved, NOT new final assets and NOT used as generation reference','runtime_integrated':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('GIFT_DELIVERY_COMPLETE110, individual padded2048RGBA PNG/WebP, inventory-ID equality PASS')
