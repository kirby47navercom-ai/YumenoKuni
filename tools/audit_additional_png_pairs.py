"""Read-only extension beyond the prior three-folder pixel audit. Two decoders maximum."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import json,struct,hashlib,os
R=Path(__file__).resolve().parents[1]
known={x['png'] for x in json.loads((R/'Game/Saved/storage-duplicate-audit-2026-10-29.json').read_text(encoding='utf-8'))['pairs']}
def lossless(p):
    with p.open('rb') as f:
        if f.read(4)!=b'RIFF':return False
        f.seek(12)
        while True:
            h=f.read(8)
            if len(h)<8:return False
            tag,n=struct.unpack('<4sI',h)
            if tag==b'VP8L':return True
            if tag==b'VP8 ':return False
            f.seek(n+(n%2),1)
jobs=[];lossy=[]
for base in ['art','bg','ui','inspect']:
    for p in (R/base).rglob('*.png'):
        rel=p.relative_to(R).as_posix();w=p.with_suffix('.webp')
        if rel in known or not w.exists():continue
        if lossless(w):jobs.append(p)
        else:lossy.append({'png':rel,'webp':w.relative_to(R).as_posix(),'bytes':p.stat().st_size,'reason':'lossy WebP is not pixel-identical archival replacement'})
print(f'Additional lossless candidates: {len(jobs)}; lossy pairs preserved: {len(lossy)}',flush=True)
def check(p):
    with Image.open(p) as a,Image.open(p.with_suffix('.webp')) as b:
        same=a.size==b.size and hashlib.sha256(a.convert('RGBA').tobytes()).digest()==hashlib.sha256(b.convert('RGBA').tobytes()).digest()
        return {'png':p.relative_to(R).as_posix(),'webp':p.with_suffix('.webp').relative_to(R).as_posix(),'bytes':p.stat().st_size,'size':list(a.size),'rgba_identical':same}
rows=[]
with ThreadPoolExecutor(max_workers=2) as pool:
    for i,x in enumerate(pool.map(check,jobs)):
        rows.append(x)
        if (i+1)%100==0:print(f'Checked {i+1}/{len(jobs)}',flush=True)
out={'scope':'read-only source trees beyond prior audit; only VP8L exact matches eligible','pairs':rows,'lossy_pairs_protected':lossy,'eligible_bytes':sum(x['bytes'] for x in rows if x['rgba_identical']),'deleted_bytes':0}
(R/'Game/Saved/storage-additional-pairs-2026-10-29.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checked':len(rows),'identical':sum(x['rgba_identical'] for x in rows),'eligible_bytes':out['eligible_bytes'],'lossy_protected':len(lossy)}))
