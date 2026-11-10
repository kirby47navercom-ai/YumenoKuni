"""Validate selected exports and make inspection sheets; never edit generated art."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Game/Saved/v4-asset-batch01'
OUT.mkdir(parents=True,exist_ok=True)
manifest=json.loads((ROOT/'art/v4_asset_batch_01.json').read_text(encoding='utf8'))
ui=json.loads((ROOT/'ui/v4/batch01/manifest.json').read_text(encoding='utf8'))
assert len(manifest['assets'])==19
assert len({a['id'] for a in manifest['assets']})==19
assert len(ui['assets'])==20
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
records=[]
sprites=[a for a in manifest['assets'] if a['path'].startswith('art/sprites_v4/')]
assert len(sprites)==18 and len({Path(a['path']).parent.name for a in sprites})==17
sheet=Image.new('RGB',(1500,5*430),'#68656e')
for i,a in enumerate(sprites):
    x,y=(i%4)*375,(i//4)*430
    for xx in range(x,x+375,25):
        for yy in range(y,y+400,25):
            ImageDraw.Draw(sheet).rectangle((xx,yy,xx+24,yy+24),fill='#eeeeee' if ((xx-x)//25+(yy-y)//25)%2 else '#89858d')
    im=Image.open(ROOT/a['runtime_file']);im.thumbnail((340,390))
    sheet.paste(im,(x+(375-im.width)//2,y+5),im)
    ImageDraw.Draw(sheet).text((x+10,y+404),a['id'],font=font,fill='white')
sheet.save(OUT/'cast_contact_sheet.jpg',quality=94)
for a in manifest['assets']:
    src=Image.open(ROOT/a['path']);packed=Image.open(ROOT/a['runtime_file'])
    assert src.size==packed.size and src.mode==packed.mode=='RGBA'
    assert src.getchannel('A').tobytes()==packed.getchannel('A').tobytes()
    alpha=packed.getchannel('A');assert alpha.getextrema()[0]==0 and alpha.getextrema()[1]>240
    corners=[alpha.getpixel(xy) for xy in [(0,0),(packed.width-1,0),(0,packed.height-1),(packed.width-1,packed.height-1)]]
    # Generated sprite antialiasing can retain alpha 1/255; effect ink can reach an edge.
    if a in sprites: assert max(corners)<=1, (a['id'],corners)
    bounds=alpha.point(lambda p:255 if p>128 else 0).getbbox()
    row={'id':a['id'],'file':a['runtime_file'],'size':list(src.size),'alpha_equal':True,'corner_alpha':corners,'sprite_corner_alpha_limit':1 if a in sprites else None,'visible_bbox_alpha128':bounds,'sha256':hashlib.sha256((ROOT/a['runtime_file']).read_bytes()).hexdigest()}
    if a['id']=='nana_insisting':
        row['framing']='upper-body only; never use as a walkable-space full-body actor'
    elif a in sprites:
        row['framing']='full-body; source-level visual check; foot normalization pending'
        row['anchor_candidate']=[(bounds[0]+bounds[2])/(2*src.width),bounds[3]/src.height]
    else:
        row['framing']='effect overlay; center and duration must be checked in actual scene'
    records.append(row)
for a in ui['assets']:
    assert (ROOT/a['source']).is_file()
    with Image.open(ROOT/a['file']) as im:
        assert list(im.size)==a['texture_size'] and im.mode=='RGBA'
    if a['text_rect']:
        x,y,w,h=a['text_rect'];sw,sh=a['logical_size'];assert x>=0 and y>=0 and x+w<=sw and y+h<=sh
qa={'checks':'PASS: selected paths, unique IDs, cast coverage, dimensions, lossless alpha, corner alpha, UI text bounds',
    'selected_raster_count':len(records),'acting_sprites':18,'identities':17,'effects':1,'ui_state_plates':20,
    'runtime_integrated':False,'runtime_test':'NOT RUN: no Game source or consuming references changed',
    'visual_review':'individual generated outputs and inspection compositions; not full-game visual acceptance',
    'remaining':['all character expression sets','Nana full-body reference/figure','story-specific scene/incident/execution/comic art','new map geometry/layout and coherent background production','complete UI screens and runtime composition/motion','audio audition and cue editing'],
    'assets':records}
(ROOT/'art/v4_asset_batch_01_qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS: 19 selected raster exports, 18 sprites / 17 identities, 20 UI states; source and WebP alpha equal')
