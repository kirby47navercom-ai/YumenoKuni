"""Small visual index; original screenshots remain unchanged."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'연출 모아보기'
m=json.loads((OUT/'manifest.json').read_text(encoding='utf8'))
rows=[r for r in m['rows'] if r['current']]
hero=[];used=set()
for c in sorted({r['category'] for r in rows},key=lambda c:(not c.startswith('재판 · '),c)):
    r=next(r for r in rows if r['category']==c);hero.append(r);used.add(r['id'])
rows=hero+[r for r in rows if r['id'] not in used]
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19)
small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
title=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',29)
pages=[]
for page in range(math.ceil(len(rows)/24)):
    part=rows[page*24:(page+1)*24];cols=4;cellw=416;cellh=277;top=105
    image=Image.new('RGB',(cols*cellw+40,top+math.ceil(len(part)/cols)*cellh+35),'#111218');draw=ImageDraw.Draw(image)
    draw.text((20,14),'유메노쿠니 · 현재 빌드 실제 캡처',font=title,fill='#fff0a4')
    draw.text((20,58),f"{m['build']}  |  {page+1:02d} / {math.ceil(len(rows)/24):02d}  |  정지 화면·축소 미리보기 / 사건 화면 포함",font=small,fill='#c8c9d2')
    for i,r in enumerate(part):
        x=20+(i%cols)*cellw;y=top+(i//cols)*cellh
        with Image.open(ROOT/r['path']) as source:
            thumb=source.convert('RGB');thumb.thumbnail((400,225),Image.Resampling.LANCZOS)
            image.paste(thumb,(x+(400-thumb.width)//2,y+(225-thumb.height)//2))
        label=r['category']+' · '+r['label']
        while draw.textlength(label,font=font)>400:label=label[:-2]+'…'
        draw.text((x,y+229),label,font=font,fill='white')
        draw.text((x,y+254),f"{r['width']}×{r['height']} 원본"+(' · 조건 저장' if r['fixture'] else ''),font=small,fill='#aeb0bc')
    dest=OUT/f'현재 연출 {page+1:02d}.jpg';image.save(dest,quality=89,optimize=True);pages.append(dest.name)
(OUT/'contact-sheets.json').write_text(json.dumps({'build':m['build'],'screenshots':len(rows),'pages':pages,'originalPixelsUnchanged':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Created',len(pages),'contact sheets for',len(rows),'current screenshots')
