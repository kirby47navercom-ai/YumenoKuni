"""Compile cached SFL quads/masks into small HUD tiles; no V3 execution."""
from pathlib import Path
import json, math
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / 'ui/v3_authorized/nonstop_hud'
OUT = ROOT / 'ui/v4/nonstop_hud_source'
OUT.mkdir(parents=True, exist_ok=True)
LAYOUT = json.loads((BANK / 'layout.json').read_text(encoding='utf8'))
SCALE = 2
SIZE = (1280*SCALE, 720*SCALE)
records = {}
cylinder_negative = False

def layer(row, rotate=0):
    im = Image.open(ROOT/row['texture']).convert('RGBA')
    if row['resource']=='t_cylinder_000.png':
        a=np.array(im,dtype=np.float32)
        stripe=np.array(Image.open(BANK/'t_hr_cylinder/t_hr_cylinder_stripe_DXT1.png.png').convert('RGB').resize(im.size),dtype=np.float32)
        a[:,:,:3]=np.clip(a[:,:,:3]*([.75,.20,.95] if cylinder_negative else [.18,.7,.95])+stripe*1.4,0,255)
        a[:,:,3]*=.68
        im=Image.fromarray(a.astype('uint8'))

    if rotate:
        im = im.rotate(rotate, Image.Resampling.BICUBIC)
    cm, ca = row['colorMultiply'], row['colorAdd']
    if cm != [1,1,1] or ca != [0,0,0]:
        a=np.array(im,dtype=np.float32)
        a[:,:,:3]=np.clip(a[:,:,:3]*cm+np.array(ca)*255,0,255)
        im=Image.fromarray(a.astype('uint8'))
    a,b,c,d,x,y=row['sourceAffine']
    rw=row['rect'][2]*1.5/math.hypot(a,b)
    rh=row['rect'][3]*1.5/math.hypot(c,d)
    a,b,c,d=[a*rw/im.width,b*rw/im.width,c*rh/im.height,d*rh/im.height]
    a,b,c,d,x,y=[v*2/3*SCALE for v in [a,b,c,d,x,y]]
    det=a*d-b*c
    inv=(d/det,-c/det,(c*y-d*x)/det,-b/det,a/det,(b*x-a*y)/det)
    out=im.transform(SIZE,Image.Transform.AFFINE,inv,Image.Resampling.BICUBIC)
    alpha=out.getchannel('A').point(lambda v:round(v*row['opacity']))
    for clip in row.get('clips',[]):
        mask=Image.new('RGBA',SIZE)
        for child in clip:mask.alpha_composite(layer(child))
        alpha=ImageChops.multiply(alpha,mask.getchannel('A'))
    out.putalpha(alpha)
    return out

def composite(rows):
    out=Image.new('RGBA',SIZE)
    for row in rows:out.alpha_composite(layer(row))
    return out

def write(name, im, bounds=None):
    box=tuple(round(v*SCALE) for v in bounds) if bounds else im.getbbox()
    assert box
    target=OUT/(name+'.png')
    im.crop(box).save(target)
    records[name]={'file':target.relative_to(ROOT).as_posix(),'rect':[box[0]/SCALE,box[1]/SCALE,(box[2]-box[0])/SCALE,(box[3]-box[1])/SCALE]}

write('status',composite(LAYOUT['t_status_base_US']['states']['fl_wait']))
write('statusLie',composite(LAYOUT['t_status_base_US']['states']['fl_uso_wait']))
for n in [5,7,10]:
    for kind in ['heart','star']:
        rows=LAYOUT[f't_status_{kind}{n}']['states']['fl_wait']
        frame=next(r for r in rows if 'all_frame' in r['resource'])
        fills=[r for r in rows if r.get('clips') and '_color_' in r['resource']]
        assert len(fills)==n
        slots=sorted([layer(r) for r in fills],key=lambda im:im.getbbox()[0])
        bounds=composite([frame]).getbbox()
        for parts in range(n*2+1):
            out=layer(frame)
            for i,slot in enumerate(slots):
                if parts<=i*2:continue
                if parts==i*2+1:
                    slot=slot.copy();box=slot.getbbox();mask=Image.new('L',SIZE);ImageDraw.Draw(mask).rectangle((0,0,(box[0]+box[2])//2,SIZE[1]),fill=255);slot.putalpha(ImageChops.multiply(slot.getchannel('A'),mask))
                out.alpha_composite(slot)
            write(f'{kind}{n}_{parts}',out,tuple(v/SCALE for v in bounds))
        negative_rows=LAYOUT[f't_status_{kind}{n}']['states']['fl_uso_wait']
        negative_frame=next(r for r in negative_rows if 'all_frame' in r['resource'] and r['opacity']>0)
        negative_fills=sorted([layer(r) for r in negative_rows if r.get('clips') and '_color_' in r['resource'] and r['opacity']>0],key=lambda im:im.getbbox()[0])
        assert len(negative_fills)==n
        for parts in range(n*2+1):
            out=layer(negative_frame)
            for i,slot in enumerate(negative_fills):
                if parts<=i*2:continue
                if parts==i*2+1:
                    slot=slot.copy();box=slot.getbbox();mask=Image.new('L',SIZE);ImageDraw.Draw(mask).rectangle((0,0,(box[0]+box[2])//2,SIZE[1]),fill=255);slot.putalpha(ImageChops.multiply(slot.getchannel('A'),mask))
                out.alpha_composite(slot)
            write(f'{kind}{n}Lie_{parts}',out,tuple(v/SCALE for v in bounds))

rows=LAYOUT['t_time']['states']['fl_wait']
write('clock',composite(rows[:3]))
clock_rect=records['clock']['rect']
negative_clock=[r for r in LAYOUT['t_time']['states']['fl_uso_wait'] if r['resource'].startswith(('t_time_base_','t_time_ico_play'))]
write('clockLie',composite(negative_clock),[clock_rect[0],clock_rect[1],clock_rect[0]+clock_rect[2],clock_rect[1]+clock_rect[3]])
clock_digits=[r for r in rows if r['path'].startswith('_a_t_time_num_') and 'anime' not in r['path']]
assert len(clock_digits)==9
for i in range(11):
    source=BANK/'t_time'/f't_time_num_{i:03d}.png.png'
    im=Image.open(source).convert('RGBA')
    # This decoded texture already carries the source glow in its alpha.
    # Transparent texels have non-black RGB; deriving alpha from RGB fills boxes.
    im.save(OUT/f'digit{i}.png')
    Image.open(BANK/'t_time'/f't_time_num_{i:03d}_uso.png.png').convert('RGBA').save(OUT/f'digitLie{i}.png')
records['clockDigits']={'rects':[r['rect'] for r in clock_digits],'files':[f'ui/v4/nonstop_hud_source/digit{i}.png' for i in range(11)]}

cylinder=LAYOUT['t_cylinder']['states']['fl_wait']
start=LAYOUT["t_cylinder"]["labels"]["fl_shot"]-LAYOUT["t_cylinder"]["labels"]["fl_in"]
for cylinder_negative in [False,True]:
    prefix='cylinderLie' if cylinder_negative else 'cylinder'
    for step in range(36):
        out=Image.new('RGBA',SIZE)
        for r in cylinder:out.alpha_composite(layer(r,step*10))
        write(prefix+str(step),out,(0,450,310,720))
    # Source fl_shot retains its recoil/flash in both cartridge palettes.
    for i in range(23):
        write(prefix+'Shot'+str(i),composite(LAYOUT['t_cylinder']['frames'][start+i]),(0,450,310,720))
cylinder_negative=False

# Keep source speaker base/markers and affine placement; use own Korean name text.
speaker=LAYOUT['t_speaker_US']['states']['fl_wait']
write('name',composite([r for r in speaker if r['resource']=='t_speaker_base_000.png']))
for key,resource in [('dot','t_speaker_memori_base.png'),('dotActive','t_speaker_memori_now.png')]:
    rows=[r for r in speaker if r['resource']==resource]
    write(key,layer(rows[0]))
    first=records[key]['rect']
    records[key]['positions']=[[first[0]+r['rect'][0]-rows[0]['rect'][0],first[1]+r['rect'][1]-rows[0]['rect'][1]] for r in rows]
records['speakerText']={'rect':next(r['rect'] for r in speaker if r['resource']=='t_speaker_tx_000_US.png')}
negative=LAYOUT['t_speaker_US']['states']['fl_uso_wait']
write('nameLie',composite([r for r in negative if r['resource']=='t_speaker_base_000.png']),records['name']['rect'][:2]+[records['name']['rect'][0]+records['name']['rect'][2],records['name']['rect'][1]+records['name']['rect'][3]])
for key,resource in [('dotLie','t_speaker_memori_base.png'),('dotActiveLie','t_speaker_memori_now.png')]:
    write(key,layer(next(r for r in negative if r['resource']==resource)))

from render_nonstop_ammo_source import build as build_ammo
build_ammo(records)

manifest={'source':'Existing decoded authorized SFL/PNG cache; no original game run/new archive extraction. Source affine/masks for speaker/status/clock/cylinder; fl_uso_wait speaker, heart/star, status and clock imagery retained. Own Korean speaker/evidence text; cylinder blue/purple tint is an adaptation, not a recovered shader.','tiles':records}
(OUT/'layout.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print('HUD_SOURCE_TILES',len(records))
