"""Retain original tab pixels; remove baked original faces for own runtime portraits."""
from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];CACHE=Path('C:/Users/kirby/Downloads/v3_re/ui_scrum_20261106/png');OUT=ROOT/'ui/v4/scrum_source';OUT.mkdir(exist_ok=True)
records=[]
for side,cut in [('l',500),('r',520)]:
 source=CACHE/f't_scm_chara_pl_{side}'/f't_scm_chara_pl_{side}_000.png.png';raw=source.read_bytes();im=Image.open(source).convert('RGBA')
 clear=(0,0,cut,im.height) if side=='l' else (cut,0,im.width,im.height);im.paste((0,0,0,0),clear);file=f'tab_{side}.png';im.save(OUT/file)
 records.append({'source':str(source),'sha256':hashlib.sha256(raw).hexdigest(),'file':file,'clearedOriginalCharacterRect':clear,'ownPortraitSlot':[245,58,255,140] if side=='l' else [520,58,259,140],'policy':'Only original face-containing part made transparent. Original ink elsewhere is unchanged; own runtime portrait fills this slot. No invented vector texture, no original game execution.'})
# Legacy published mash prompt still needs its actual original round-button material.
source=CACHE/'t_scrum_push_US'/'t_scrum_push_button_circle.png.png';raw=source.read_bytes();(OUT/'push_button.png').write_bytes(raw);records.append({'source':str(source),'sha256':hashlib.sha256(raw).hexdigest(),'file':'push_button.png','policy':'Original circle-button material; project keyboard glyph is drawn over its center by the existing controller.'})
(OUT/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('SCRUM_SOURCE_TABS',len(records))
