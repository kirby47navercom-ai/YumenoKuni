"""Build inspection contact sheets only. Does not alter 3D models or delivered pictures."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1];folder=root/'Game/Saved/v4-space-detail-v1'
manifest=json.loads((root/'art/space_v4/detail_v1/manifest.json').read_text(encoding='utf8'))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
for kind in ['cutaway','inside']:
    selected=[]
    for row in manifest['spaces']:
        if kind=='inside' and row['mode']=='scripted_court':continue
        suffix='' if kind=='cutaway' else ('_center' if row['mode']=='fixed_pan' else '_entry')
        selected.append((row['id'],folder/(row['id']+suffix+'.png')))
    sheet=Image.new('RGB',(1600,math.ceil(len(selected)/3)*370),'#2d2b35');d=ImageDraw.Draw(sheet)
    for i,(name,path) in enumerate(selected):
        im=Image.open(path);im.thumbnail((525,330));x=i%3*533;y=i//3*370
        sheet.paste(im,(x,y));d.text((x+8,y+336),name,font=font,fill='white')
    sheet.save(folder/(kind+'_contact.jpg'),quality=95)
    print(kind,len(selected),'rendered-space views')
