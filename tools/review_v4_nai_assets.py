"""Generate contact sheets and structural checks; never treat these as visual acceptance."""
from pathlib import Path
import json, hashlib
from datetime import datetime, timezone
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Game/Saved/v4-asset-batch01/nai_review'
OUT.mkdir(parents=True,exist_ok=True)
records=[]
groups={}
for folder in ('art/standing_v4','art/sprites_nai_v4','art/cg_v4/incidents'):
    for meta in sorted((ROOT/folder).rglob('*.json')):
        info=json.loads(meta.read_text(encoding='utf8'))
        png=meta.with_suffix('.png');webp=meta.with_suffix('.webp')
        if not png.exists():continue
        with Image.open(png) as source:
            im=source.convert('RGBA')
        alpha=im.getchannel('A');bbox=alpha.getbbox()
        same=False
        if webp.exists():
            with Image.open(webp) as other:same=other.convert('RGBA').tobytes()==im.tobytes()
        edge_touch=bool(bbox and (bbox[0]==0 or bbox[1]==0 or bbox[2]==im.width or bbox[3]==im.height))
        record={'file':png.relative_to(ROOT).as_posix(),'model':info.get('model'),'size':list(im.size),'alpha_bbox':bbox,'edge_touch':edge_touch,'lossless_pair_equal':same,'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'visual_acceptance':'pending'}
        records.append(record)
        group='incidents_PRIVATE' if 'incidents' in folder else ('standing' if 'standing' in folder else png.parent.name)
        groups.setdefault(group,[]).append((png,im))
for group,items in groups.items():
    for start in range(0,len(items),20):
        page=items[start:start+20];cols=5;rows=(len(page)+cols-1)//cols
        sheet=Image.new('RGB',(cols*220,rows*340),(222,224,228));draw=ImageDraw.Draw(sheet)
        for i,(path,im) in enumerate(page):
            thumb=im.copy();thumb.thumbnail((210,310))
            x=(i%cols)*220+(220-thumb.width)//2;y=(i//cols)*340
            sheet.paste(thumb,(x,y),thumb)
            draw.text(((i%cols)*220+5,y+315),path.stem[:30],fill=(20,20,20))
        sheet.save(OUT/f'{group}_{start//20+1:02}.jpg',quality=92)
coverage=[]
for jobfile in sorted((ROOT/'art/v4_production').glob('*jobs.json')):
    jobs=json.loads(jobfile.read_text(encoding='utf8')).get('jobs',[])
    for family in sorted({j['family'] for j in jobs}):
        subset=[j for j in jobs if j['family']==family]
        done=[j for j in subset if (ROOT/j['output']).with_suffix('.json').exists()]
        coverage.append({'jobfile':jobfile.relative_to(ROOT).as_posix(),'family':family,'requested':len(subset),'generated_candidates':len(done),'visually_accepted':'not inferred from generation'})
report={'snapshot_utc':datetime.now(timezone.utc).isoformat(),'scope':'generated files present at review snapshot; structural checks are not visual approval','coverage':coverage,'records':records,'counts':{'files':len(records),'edge_touch_flags':sum(r['edge_touch'] for r in records),'pair_mismatch':sum(not r['lossless_pair_equal'] for r in records)}}
(ROOT/'art/v4_production/structural_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report['counts']))
