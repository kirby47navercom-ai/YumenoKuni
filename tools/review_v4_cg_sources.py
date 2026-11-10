"""Inspection-only contact pages from saved originals, including still-running export batches."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Game/Saved/v4-cg-source-contact';OUT.mkdir(parents=True,exist_ok=True)
rows={}
for p in (ROOT/'art/cg_v4/builtin').glob('*.json'):
 j=json.loads(p.read_text(encoding='utf8'));rows[j['id']]=(ROOT/j['source_file'],j)
registry=ROOT/'art/v4_production/full/builtin_generation_results.json'
for r in json.loads(registry.read_text(encoding='utf-8-sig'))['results']:
 jp=ROOT/'art/v4_production/full/builtin_jobs'/(r['id']+'.json');j=json.loads(jp.read_text(encoding='utf8'));rows.setdefault(r['id'],(Path(r['path']),j))
for family in ['event','incident','execution','climax','revision']:
 selected=[]
 for ident,(p,j) in sorted(rows.items()):
  k=j.get('kind','event');group='revision' if k=='targeted_revision' else 'climax' if k=='climax_page' else k if k in ['incident','execution'] else 'event'
  if group==family:selected.append((ident,p))
 for start in range(0,len(selected),6):
  page=Image.new('RGB',(1180,1080),'#e6e0d6');d=ImageDraw.Draw(page)
  for i,(ident,p) in enumerate(selected[start:start+6]):
   with Image.open(p) as im:
    im=im.convert('RGB');im.thumbnail((580,326));x=i%2*590;y=i//2*360;page.paste(im,(x,y));d.text((x+5,y+331),ident,fill='black')
  page.save(OUT/f'{family}_{start//6+1:02d}.jpg',quality=96)
 print(family,len(selected))
