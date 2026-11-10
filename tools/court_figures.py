"""Technical runtime export of existing 4x full-body art; never calls a generator/API."""
import json
import re
from pathlib import Path
from PIL import Image
import numpy as np
from game_sprites import heights
from v4_character_sources import catalogue

ROOT = Path(__file__).resolve().parents[1]
SLUGS = 'mio rin ken nana taiga ai rei sora haruka sho koto akari riku satsuki yuu kaede'.split()

def main():
    dest = ROOT / 'Game/Assets/Art/court_figures'
    dest.mkdir(parents=True, exist_ok=True)
    catalog = {}
    metadata = ROOT/"Game/Saved/court-figures-export.json"
    metadata.parent.mkdir(parents=True,exist_ok=True)
    prior = metadata if metadata.exists() else dest/"manifest.json"
    previous = json.loads(prior.read_text(encoding="utf-8")) if prior.exists() else {}
    tall = heights()
    _, curated = catalogue(hd=True)
    for slug in SLUGS:
        selected = {key: source for key, source in curated.items() if key == slug or key.startswith(slug+"_")}
        for key, source in selected.items():
            front = dest / (key + '.webp')
            back = dest / (key + '_back.webp')
            if key in previous and previous[key].get("source") == source.relative_to(ROOT).as_posix() and front.exists() and back.exists() and min(front.stat().st_mtime,back.stat().st_mtime) >= source.stat().st_mtime:
                catalog[key] = previous[key]
                continue
            im = Image.open(source).convert('RGBA')
            alpha = im.getchannel('A')
            box = alpha.point(lambda a: 255 if a > 32 else 0).getbbox()
            if not box:
                raise ValueError(source)
            # Center the feet, not the hands or the bounding-box center.
            feet = np.asarray(alpha.crop((0, box[3]-int((box[3]-box[1])*.08), im.width, box[3]))) > 128
            cols = np.flatnonzero(feet.any(0))
            anchor = (int(cols[0])+int(cols[-1]))/2
            half = int(max(anchor-box[0], box[2]-anchor))+8
            box = (round(anchor-half), box[1]-4, round(anchor+half), box[3]+4)
            w, h = box[2]-box[0], box[3]-box[1]
            height = 2.5 * tall.get(slug, 170)/188
            catalog[key] = {'texture': f'Assets/Art/court_figures/{key}.webp',
                            'back': f'Assets/Art/court_figures/{key}_back.webp',
                            'width': height*w/h, 'height': height, 'center': .1+height/2,
                            'source': str(source.relative_to(ROOT)).replace('\\','/'), 'crop': box}
            im = im.crop(box)
            im.thumbnail((2048,3072),Image.Resampling.LANCZOS)
            im.save(front,'WEBP',quality=94,method=4)
            silhouette = Image.new('RGBA',im.size,(0,0,0,0))
            silhouette.putalpha(im.getchannel('A'))
            silhouette.save(back,'WEBP',lossless=True,method=4)
    for slug in SLUGS:
        catalog[slug+"_C01"] = dict(catalog[slug])  # C01 must never fall through to old art.
    metadata.write_text(json.dumps(catalog,ensure_ascii=False,indent=1),encoding='utf-8')
    runtime = {key: {k:v for k,v in row.items() if k not in ('source','crop')} for key,row in catalog.items()}
    (dest/'manifest.json').write_text(json.dumps(runtime,ensure_ascii=False,indent=1),encoding='utf-8')
    print(f'Court full-body export: {len(catalog)} front/back pairs')

if __name__ == '__main__':
    main()
