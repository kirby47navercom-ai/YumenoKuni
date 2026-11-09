"""Apply selected original inspection illustrations without changing story facts."""
import hashlib,json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'art/inspection_v4/illustrations_20261104/selection.json'

def apply(entries):
    if not REGISTRY.exists():return entries
    for key,row in json.loads(REGISTRY.read_text(encoding='utf-8'))['entries'].items():
        prior=entries[key]
        assert prior['inspectionScope']==row['inspectionScope']
        assert prior['source']==row['source'],'Re-read changed observation sources before replacing art'
        file=ROOT/row['image'];raw=file.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['sha256']
        with Image.open(file) as im:size=list(im.size)
        assert size==row['rasterSize']
        assert {r['id']:r['correct'] for r in prior['regions']}=={r['id']:r['correct'] for r in row['regions']}
        prior.update({k:row[k] for k in ('image','sha256','rasterSize','regions','visualReview')})
        prior['svg']=None
        prior['authoredIllustration']=True
        prior['nativeResolutionPreserved']=True
    return entries

def bind_runtime(payload):
    if not REGISTRY.exists():return payload
    rows=json.loads(REGISTRY.read_text(encoding='utf-8'))['entries']
    manifest=json.loads((ROOT/'ui/v4/investigation_diagrams_v4/manifest.json').read_text(encoding='utf-8'))
    apply(manifest['entries'])
    def bind(value):
        if isinstance(value,str):
            return next((r['image'] for r in rows.values() if value==r['replaces']),value)
        if isinstance(value,list):return [bind(v) for v in value]
        if not isinstance(value,dict):return value
        out={k:bind(v) for k,v in value.items()}
        for key,row in rows.items():
            if out.get('pictureProvenance',{}).get('entry')!=key:continue
            assert {r['id']:r['correct'] for r in out['regions']}=={r['id']:r['correct'] for r in row['regions']}
            geometry={r['id']:r['polygon'] for r in row['regions']}
            for region in out['regions']:region['polygon']=geometry[region['id']]
            out['pictureProvenance']['imageSha256']=row['sha256']
        return out
    return bind(payload)

if __name__=='__main__':
    import sys
    json.dump(bind_runtime(json.load(sys.stdin)),sys.stdout,ensure_ascii=False)
