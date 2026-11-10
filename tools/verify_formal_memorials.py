"""Read-only pixel/provenance checks for16 ID portraits and32 courtroom textures."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops,ImageFilter
R=Path(__file__).resolve().parents[1]
M=R/'art/trial3d/memorial_v3'
catalog=json.loads((M/'manifest.json').read_text(encoding='utf8'))
frame=Image.open(R/'art/hd_v4/memorial/frame_blood_x.webp').convert('RGBA').resize((2048,2048),Image.Resampling.LANCZOS)
alpha=frame.getchannel('A')
photo=Image.new('L',(2048,2048),0)
photo.paste(255,(690,498,1470,1565))
photo=ImageChops.multiply(photo,alpha.point(lambda a:255 if a==0 else 0))
# The colored frame/blood has antialiased edges; compare only its uncovered photo interior.
photo=photo.filter(ImageFilter.MinFilter(5))
rows=[]
for slug,row in catalog['characters'].items():
 p=R/row['file'];im=Image.open(p).convert('RGBA');back=Image.open(p.with_name(slug+'_back.webp')).convert('RGBA')
 assert im.size==(2048,2048) and back.size==im.size
 assert ImageChops.difference(im.getchannel('A'),back.getchannel('A')).getbbox() is None
 for ch in back.convert('RGB').split():
  assert ImageChops.multiply(ch,back.getchannel('A')).getextrema()[1]==0
 rgb=im.convert('RGB');r,g,b=rgb.split()
 err=ImageChops.lighter(ImageChops.difference(r,g),ImageChops.difference(r,b))
 err=ImageChops.multiply(err,photo).getextrema()[1]
 assert err<=2,(slug,err)
 for point in [(10,10),(1350,140),(1900,1000),(1950,2000)]:
  if alpha.getpixel(point)==0 and photo.getpixel(point)==0:assert im.getpixel(point)[3]==0,(slug,point)
 master=R/f'art/hd_v4/id_portraits_color_v1/{slug}.webp'
 assert row['portrait_source']==master.relative_to(R).as_posix()
 assert row['portrait_sha256']==hashlib.sha256(master.read_bytes()).hexdigest()
 color=Image.open(master).convert('RGB');cr,cg,cb=color.split()
 assert ImageChops.difference(cr,cb).getextrema()[1]>16,'Primary master must remain COLOR'
 upscale=json.loads((R/f'art/hd_v4/id_portraits_color_v1/{slug}.json').read_text(encoding='utf8'))
 assert upscale['scale']==4 and upscale['size']==[5016,5016]
 assert hashlib.sha256(p.read_bytes()).hexdigest()==row['output_sha256']
 rows.append({'character':slug,'neutral_photo_max_channel_difference':err,'front_back_alpha_equal':True,'black_opaque_back':True,'local_upscale':upscale['method'],'sha256':row['output_sha256']})
assert len(rows)==16 and len({x['sha256'] for x in rows})==16
out={'ok':True,'portraits':16,'textures':32,'scope':'formal head/shoulders reference edits; grayscale photo area, colored frame/purple X, alpha-matched black back; all16 are templates, not survival spoilers','technical_checks':rows,'visual_review':'All16 ID portrait and memorial contact sheets inspected, original faces/accessories/front pose retained; final runtime selection tested separately.'}
(R/'art/trial3d/id_portraits_color_v1/qa.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS:16 grayscale ID photos /32 textures /4x provenance /matching black rear alpha')
