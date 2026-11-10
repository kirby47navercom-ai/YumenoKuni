"""Static presentation audit. Writes audit evidence only, never game data/art/audio."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/analysis/v3_rebuild'
SH = ROOT/'Game/Saved/presentation-audit'
SH.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 13)
cues = json.loads((ROOT/'audio/cues.json').read_text(encoding='utf8'))
catalog = {k: v for group in ('bgm','jingle','sfx') for k,v in cues.get(group,{}).items()}
chapters = {}
rows = []
for p in sorted((ROOT/'Game/Assets/Data/flow').glob('*.json')):
    data = json.loads(p.read_text(encoding='utf8'))
    counts = Counter()
    for bi,b in enumerate(data['beats']):
        scene = {'file': p.relative_to(ROOT).as_posix(), 'file_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                 'beat': bi, 'id': b.get('id'), 'kind': b['t'], 'bgm': b.get('bgm'), 'contexts': []}
        contexts = [('events', b.get('events',[]))]
        for kind in ('pool','spots'):
            contexts += [(kind+'/'+str(i)+'/events',x.get('events',[])) for i,x in enumerate(b.get(kind,[]))]
        contexts += [('options/'+str(i)+'/beat/events',x.get('beat',{}).get('events',[])) for i,x in enumerate(b.get('options',[])) if isinstance(x,dict) and isinstance(x.get('beat'),dict)]
        for context, evs in contexts:
            music = []
            effects = []
            for ei,e in enumerate(evs):
                if 'music' in e:
                    music.append({'event':ei,'cue':e['music']});counts['event_music']+=1
                if 'sfx' in e:
                    sfx = e['sfx'] if isinstance(e['sfx'],list) else [e['sfx']]
                    effects.extend({'event':ei,'cue':c} for c in sfx);counts['sfx_events']+=1
                counts['events']+=1
                counts['say_events']+=e.get('type')=='say'
                for key in ('camera','shake','flash','pan','zoom','pause','stopMusic','fade','silence','timeline'):
                    counts['authored_'+key]+=key in e
            scene['contexts'].append({'context':context,'event_count':len(evs),'music':music,'sfx':effects})
        if b.get('bgm'): counts['scene_bgm']+=1
        rows.append(scene)
    chapters[p.stem]=dict(counts)
inventory=json.loads((OUT/'asset_inventory.json').read_text(encoding='utf8'))
groups={}
for r in inventory['assets']:
    if not r['category'].startswith('art/cg/') or re.search(r'_(bg|fg)\.',r['path']):continue
    groups.setdefault(r['category'].split('/')[-1],[]).append(r['path'])
sheets=[]
for group, paths in groups.items():
    for start in range(0,len(paths),24):
        page=paths[start:start+24];sheet=Image.new('RGB',(1280,6*204),'#282330');draw=ImageDraw.Draw(sheet)
        for i,rel in enumerate(page):
            x,y=i%4*320,i//4*204
            with Image.open(ROOT/rel) as im:
                tile=im.convert('RGBA');tile.thumbnail((312,176));sheet.paste(tile,(x+(320-tile.width)//2,y),tile)
            draw.text((x+3,y+177),Path(rel).name[:42],fill='white',font=font)
        target=SH/f'{group}_{start//24+1:02}.jpg';sheet.save(target,quality=90)
        sheets.append({'path':target.relative_to(ROOT).as_posix(),'sources':page})
result={'source':'current generated flow and source audio catalog; static inspection, not listening',
        'catalog_counts':{g:len(cues.get(g,{})) for g in ('bgm','jingle','sfx')},
        'audio_files':{g:len(list((ROOT/'audio'/g).glob('*'))) for g in ('bgm','sfx')},
        'catalog':catalog,'chapters':chapters,'scenes':rows,
        'composite_cg_counts':{k:len(v) for k,v in groups.items()},'cg_contact_sheets':sheets,
        'limits':['authored event keys only; hardcoded runtime motion is separate',
                  'no all-path audio listening, no original V3 execution',
                  'contact sheet creation is not visual review']}
(OUT/'presentation_evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:result[k] for k in ('catalog_counts','audio_files','chapters','composite_cg_counts')},ensure_ascii=False))
