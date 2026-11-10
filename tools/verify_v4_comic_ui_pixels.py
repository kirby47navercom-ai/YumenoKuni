"""Offline font-fit proof for source HUD rectangles; never a native visual pass."""
import json
from pathlib import Path
from PIL import ImageFont
ROOT=Path(__file__).resolve().parents[1]
tasks=json.loads((ROOT/'data/v4_story/native_tasks.json').read_text(encoding='utf-8'))['tasks']
font=ImageFont.truetype(str(ROOT/'fonts/pretendard/Pretendard-Medium.otf'),26)
def lines(text,width):
 out=['']
 for char in text:
  if char=='\n':out.append('');continue
  if font.getlength(out[-1]+char)>width:out.append('')
  out[-1]+=char
 return out
labels=responses=0;max_caption=max_replay=0
for task in tasks.values():
 if task.get('stage',{}).get('kind')!='climax':continue
 for slot in task['stage']['slots']:
  card=next(c for c in slot['options'] if c['id']==slot['answer'])
  rows=len(lines(card['label'],520));assert rows*26*1.3<=112;labels+=1;max_caption=max(max_caption,rows)
  for row in card.get('response',[]):
   if row.get('text'):
    count=len(lines(row['text'],950));assert count*26*1.3<=112;responses+=1;max_replay=max(max_replay,count)
print(json.dumps({'ok':True,'acceptedCaptions':labels,'narrationRows':responses,'maximumCaptionLines':max_caption,'maximumReplayLines':max_replay,'scope':'Offline Korean font metrics only; original source pixels and actual runtime checked separately'},ensure_ascii=False))
