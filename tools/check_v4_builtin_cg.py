"""Check source provenance, lossless exports and widescreen delivery; no visual approval."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];PRE=ROOT/'Game/Saved/v4-builtin-cg-review';PRE.mkdir(parents=True,exist_ok=True)
rows=[];thumbs=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for mp in sorted((ROOT/'art/cg_v4/builtin').glob('*.json')):
    j=json.loads(mp.read_text(encoding='utf8'));src=ROOT/j['source_file'];hd=ROOT/j['hd_file'];final=ROOT/j['delivery_file']
    assert j['tool']=='built-in image_gen' and sha(src)==j['source_sha256'] and sha(final)==j['delivery_sha256'],j['id']
    assert all((ROOT/p).exists() for p in j['references']),j['id']
    s=json.loads(hd.with_suffix('.json').read_text(encoding='utf8'));assert s['source_sha256']==sha(src)
    with Image.open(src) as im:
        size=im.size;thumb=im.convert('RGB');thumb.thumbnail((480,270));thumbs.append((j,thumb.copy()))
    with Image.open(hd) as im:assert im.size==(size[0]*4,size[1]*4)
    with Image.open(final) as im:
        assert im.width*9==im.height*16 and im.width>=3840,j['id']
        with Image.open(final.with_suffix('.webp')) as webp:assert im.convert('RGBA').tobytes()==webp.convert('RGBA').tobytes(),j['id']
    source_current=sha(ROOT/j['source'])==j.get('manuscript_sha256') if j.get('source') else None
    rows.append({'id':j['id'],'tool':j['tool'],'source_size':list(size),'delivery_size':j['delivery_size'],'image_hash':'PASS','raw_4x':'PASS','exact_16_9':'PASS','lossless_webp':'PASS','manuscript_hash_current':source_current,'visual_acceptance':j.get('review',{}),'runtime_integrated':False})
for start in range(0,len(thumbs),6):
    page=Image.new('RGB',(980,890),'#e6e0d6');draw=ImageDraw.Draw(page)
    for i,(j,thumb) in enumerate(thumbs[start:start+6]):
        x=i%2*490;y=i//2*295;page.paste(thumb,(x,y));draw.text((x+4,y+272),str(start+i+1)+' '+j['id'],fill='black')
    page.save(PRE/f'source_sheet_{start//6+1:02d}.jpg',quality=95)
out={'status':'structural checks only; individual source/HD/scene QA recorded separately','candidate_count':len(rows),'art':rows,'runtime_integration':'NOT RUN'}
(ROOT/'art/v4_production/full/builtin_qa.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS',len(rows),'built-in CG exports: provenance, 4x, exact16:9, lossless pixels; visual verdict separate')
