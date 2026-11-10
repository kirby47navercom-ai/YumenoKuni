"""Contact sheets of actual native captures, without changing game assets."""
import json, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
work = root / 'Game/Saved/native-all-tasks-1793928979909'
out = root / 'Game/Saved/nonstop-all-20261106/contact'
out.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 18)
groups = {}
works = [work, root/'Game/Saved/native-all-tasks-ns23-20261106', root/'Game/Saved/native-all-tasks-ns45-20261106', root/'Game/Saved/native-all-tasks-ns6-host-20261106', root/'Game/Saved/native-all-tasks-ns-first-focus-20261106',root/'Game/Saved/native-all-tasks-ns-ink-20261106']
for session in sorted((session for base in works for session in base.glob('session-*')),key=lambda p:p.name):
    for file in session.glob('*.png'):
        m = re.fullmatch(r'(t\d-[a-z0-9-]+)-line-(\d+)\.png', file.name)
        if m:
            groups.setdefault(m[1], {})[int(m[2])] = file
for task, rows in groups.items():
    target = out / (task + '.jpg')
    if target.exists() and target.stat().st_mtime >= max(p.stat().st_mtime for p in rows.values()):
        continue
    count = len(rows)
    sheet = Image.new('RGB', (1440, ((count + 2)//3)*298), '#17191d')
    draw = ImageDraw.Draw(sheet)
    for slot, (index, file) in enumerate(sorted(rows.items())):
        x, y = slot % 3 * 480, slot // 3 * 298
        draw.text((x+8, y+3), f'{task} / utterance {index}', font=font, fill='white')
        with Image.open(file) as im:
            sheet.paste(im.resize((480, 270), Image.Resampling.LANCZOS), (x, y+28))
    sheet.save(target, quality=88)
print(json.dumps({task: len(rows) for task, rows in groups.items()}))
