"""Read-only source asset inventory and audit contact sheets; never edits source art."""
from pathlib import Path
from collections import Counter
import json
import re
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/analysis/v3_rebuild'
SHEETS = ROOT / 'Game/Saved/v3-rebuild-audit'
OUT.mkdir(parents=True, exist_ok=True)
SHEETS.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 13)
rows = []
for folder in ('bg', 'art/sprites', 'art/cutin', 'art/cg', 'art/trial3d', 'ui'):
    for p in sorted((ROOT / folder).rglob('*')):
        if not p.is_file() or p.suffix.lower() not in ('.png', '.webp', '.svg'):
            continue
        if any(part.startswith('_') for part in p.relative_to(ROOT).parts):
            continue
        if p.suffix == '.png' and p.with_suffix('.webp').exists():
            continue
        if any(x in p.stem.lower() for x in ('sheet', 'preview')):
            continue
        rel = p.relative_to(ROOT).as_posix()
        category = folder
        if folder == 'art/cg':
            category += '/' + next((x for x in ('death', 'exec', 'climax', 'event', 'interlude') if p.stem.startswith(x)), 'other')
        if folder == 'ui':
            category += '/' + p.relative_to(ROOT / folder).parts[0]
        row = {'path': rel, 'category': category, 'bytes': p.stat().st_size}
        if p.suffix != '.svg':
            try:
                with Image.open(p) as im:
                    row.update(width=im.width, height=im.height, mode=im.mode)
            except Exception as exc:
                row['read_error'] = str(exc)
        rows.append(row)

groups = {}
for r in rows:
    group = r['category']
    if group == 'art/sprites':
        # Every student included, with representative emotion/action slots.
        if not re.search(r'_(C01|C05|C06|C12|T01|T04|L01|L02|L05)\.', r['path']):
            continue
        group = 'sprites_representative'
    if group.startswith('ui/') and group not in ('ui/dialog', 'ui/trial', 'ui/common', 'ui/pad', 'ui/minigame'):
        continue
    if group == 'art/cg/climax':
        # Detailed scene-dependent replacement decisions require the new case scripts.
        continue
    if group in ('art/cg/event', 'art/cg/interlude', 'art/cg/exec', 'art/cg/other'):
        # Cover each family; full inventory still includes all files.
        if sum(1 for x in groups.get(group, [])) >= 32:
            continue
    if r.get('width'):
        groups.setdefault(group, []).append(r)

sheets = []
for group, items in groups.items():
    for start in range(0, len(items), 24):
        page = items[start:start+24]
        canvas = Image.new('RGB', (1280, 6*204), '#282330')
        draw = ImageDraw.Draw(canvas)
        for i, r in enumerate(page):
            x, y = i % 4 * 320, i // 4 * 204
            with Image.open(ROOT / r['path']) as im:
                tile = im.convert('RGBA')
                tile.thumbnail((312, 176))
                canvas.paste(tile, (x+(320-tile.width)//2, y), tile)
            draw.text((x+3, y+177), Path(r['path']).name[:42], fill='white', font=font)
        name = group.replace('/', '_') + f'_{start//24+1:02}.jpg'
        target = SHEETS / name
        canvas.save(target, quality=88)
        sheets.append({'path': target.relative_to(ROOT).as_posix(), 'sources': [r['path'] for r in page]})

result = {'scope': 'source logical images; WebP preferred over paired PNG; previews excluded',
          'counts': dict(Counter(r['category'] for r in rows)), 'assets': rows,
          'contact_sheets': sheets, 'limits': ['contact sheets are representative, not full pixel QA',
          'existence or size does not prove narrative correctness or production readiness']}
(OUT / 'asset_inventory.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({'counts': result['counts'], 'contact_sheets': len(sheets), 'read_errors': [r for r in rows if 'read_error' in r]}, ensure_ascii=False))
