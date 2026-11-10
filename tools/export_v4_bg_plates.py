"""Local-only 4x delivery of full-HD still plates rendered from own 3D scenes."""
from pathlib import Path
import json,hashlib,os
from PIL import Image
from upscale_v4_assets import run
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/os.environ.get('V4_BG_FOLDER','art/bg_v4/plates')
manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
for j in manifest['assets']:
    src=ROOT/j['source']
    with Image.open(src) as im:
        assert im.size==(1920,1080),j['id']
        im.save(src.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
    # An edited Blender plate must never overwrite its previous super-resolution.
    # Rendering a new source is not permission to replace a different HD hash.
    desired=ROOT/j['hd_file'];digest=hashlib.sha256(src.read_bytes()).hexdigest();index=1
    while desired.with_suffix('.json').exists():
        stamp=json.loads(desired.with_suffix('.json').read_text(encoding='utf8'))
        if stamp.get('source_sha256')==digest:break
        index+=1;desired=(ROOT/j['hd_file']).with_stem(Path(j['hd_file']).stem+f'_r{index}')
    if desired!=ROOT/j['hd_file']:
        j['previous_hd_file']=j['hd_file'];j['hd_file']=desired.relative_to(ROOT).as_posix()
    run({'id':'bg_plate_'+j['id'],'family':'authored_3d_still','source':j['source'],'output':j['hd_file']})
    j.update(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),upscale='complete',delivery_file=j['hd_file'],delivery_size=[7680,4320])
    src.with_suffix('.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS',len(manifest['assets']),'3D-derived full-screen background plates; native originals + local4x',flush=True)
