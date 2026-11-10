"""Technical crop correction only; preserve rejected ears-only delivery."""
from pathlib import Path
import json,shutil
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'art/character_delivery_v4';p=O/'manifest.json';m=json.loads(p.read_text('utf8'));a=next(x for x in m['assets'] if x['id']=='lappy_profile')
for key in ['file','webp']:
 src=R/a[key];old=O/'rejected_technical_crops'/src.name;old.parent.mkdir(exist_ok=True)
 if not old.exists():shutil.copy2(src,old)
with Image.open(R/a['source']) as raw:
 raw=raw.convert('RGBA');x0,y0,x1,y1=raw.getchannel('A').getbbox();box=(max(0,x0-(x1-x0)//12),max(0,y0-50),min(raw.width,x1+(x1-x0)//12),min(raw.height,y0+int((y1-y0)*.72)))
 face=raw.crop(box);face.thumbnail((1490,1490));canvas=Image.new('RGBA',(1600,1600));canvas.alpha_composite(face,((1600-face.width)//2,(1600-face.height)//2))
 canvas.save(R/a['file']);canvas.save(R/a['webp'],'WEBP',lossless=True,exact=True,method=4);a.update(crop=list(box),alpha_bbox=list(canvas.getbbox()),review='mascot-specific head/ears/face/bow crop; rejected human0.34crop preserved, no image generation')
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Corrected Lappy profile: ears+whole face+bow, preserved earlier technical crop')
