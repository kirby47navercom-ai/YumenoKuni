"""Technical 64px delivery of approved image_gen head outputs, originals kept."""
from pathlib import Path
import json,shutil,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/facility_identity_v1';m=json.loads((O/'generation-manifest.json').read_text(encoding='utf8'))
for folder in ['masters','faces']:(O/folder).mkdir(exist_ok=True)
preview=Image.new('RGB',(4*288,4*320),'#272d38');d=ImageDraw.Draw(preview);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',20)
for i,row in enumerate(m['rows']):
    source=Path(row['source']);master=O/'masters'/(row['slug']+'.png');shutil.copyfile(source,master);im=Image.open(master).convert('RGBA');box=im.getchannel('A').getbbox();assert box
    head=im.crop(box);head.thumbnail((60,60),Image.Resampling.NEAREST);out=Image.new('RGBA',(64,64));out.alpha_composite(head,((64-head.width)//2,(64-head.height)//2));file=O/'faces'/(row['slug']+'.png');out.save(file)
    row.update(master=master.relative_to(R).as_posix(),masterSHA256=hashlib.sha256(master.read_bytes()).hexdigest(),face=file.relative_to(R).as_posix(),faceSHA256=hashlib.sha256(file.read_bytes()).hexdigest(),size=[64,64],technicalConversion='Trim transparent padding, fit60px within64 square with nearest-neighbor; preserve alpha. No repaint.')
    x=i%4*288+16;y=i//4*320+8;preview.paste(out.resize((256,256),Image.Resampling.NEAREST),(x,y),out.resize((256,256),Image.Resampling.NEAREST));d.text((x,y+269),row['slug'],font=font,fill='#f2eee3')
(O/'generation-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8');preview.save(O/'pixel-heads-review.png');print('PIXEL_HEADS_DELIVERED',len(m['rows']))
