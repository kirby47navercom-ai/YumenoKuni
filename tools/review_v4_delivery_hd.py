"""Source context + two actual 1:1 HD regions per selected CG, never final-image painting."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Game/Saved/v4-delivery-hd-review';OUT.mkdir(parents=True,exist_ok=True)
catalog=json.loads((ROOT/'art/v4_production/full/production_catalog.json').read_text(encoding='utf8'));rows=catalog['cg']
special={
'p01_notebook_boundary':[(.29,.32),(.4,.58)],'p08_pen_at_closed_door':[(.30,.34),(.27,.59)],
'c1_room_exchange':[(.35,.22),(.25,.48)],'incident_c1':[(.66,.32),(.85,.77)],
'incident_c2':[(.33,.34),(.45,.56)],'incident_c3a':[(.58,.25),(.66,.75)],
'incident_c3b':[(.09,.4),(.11,.73)],'incident_c4':[(.25,.45),(.24,.75)],
'incident_c5':[(.24,.5),(.42,.53)],
'c3_blindfold_test':[(.15,.22),(.86,.25)],'c4_workshop_alignment':[(.63,.26),(.56,.69)],'c6_current_and_old':[(.19,.30),(.36,.30)],'c6_support_stop':[(.44,.32),(.55,.65)],'c6_support_keep':[(.535,.22),(.53,.38)]}
for start in range(0,len(rows),15):
 page=Image.new('RGB',(1440,2240),'#e6e0d6');draw=ImageDraw.Draw(page)
 for i,j in enumerate(rows[start:start+15]):
  x=i%3*480;y=i//3*448
  with Image.open(ROOT/j['source']) as im:
   source=im.convert('RGB');source.thumbnail((474,267));page.paste(source,(x,y+16))
  draw.text((x+2,y+2),j['selected_id'],fill='black')
  points=special.get(j['logical_id'],[(.30,.30),(.70,.56)])
  with Image.open(ROOT/j['raw_4x']) as im:
   for n,(u,v) in enumerate(points):
    cx=max(118,min(im.width-118,round(im.width*u)));cy=max(80,min(im.height-80,round(im.height*v)))
    patch=im.crop((cx-118,cy-80,cx+118,cy+80)).convert('RGB');page.paste(patch,(x+n*240,y+284))
 page.save(OUT/f'cg_{start//15+1:02d}.jpg',quality=96)
(OUT/'index.json').write_text(json.dumps({'assets':len(rows),'method':'whole source context; two actual1:1 HD crop samples each, approximate nonsemantic centers except explicit critical ROIs','no_claim':'sampling does not inspect every final pixel or validate game import','files':[j['selected_id'] for j in rows]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('HD inspection pages:',len(rows),'selected CGs,',len(rows)*2,'actual1:1 regions')
