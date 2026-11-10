"""Check true OTF advances against the game cartridge width for every authored name."""
from pathlib import Path
import json
from PIL import ImageFont
ROOT=Path(__file__).resolve().parents[1]
def main():
 tasks=json.loads((ROOT/'data/v4_story/native_tasks.json').read_text(encoding='utf-8'))['tasks'];labels=set()
 for task in tasks.values():
  if task.get('stage',{}).get('kind')!='nonstop':continue
  labels.update(o['name'] for o in task['stage'].get('options',[]) if o.get('name'))
  if task.get('transformation',{}).get('intentionalHold'):labels.add(task['transformation']['lieLabel'])
 source=(ROOT/'Game/Source/GlyphMetricsV4.hpp').read_text(encoding='utf-8');line=next(l for l in source.splitlines() if l.startswith(' {"pretendard/Pretendard-Medium.otf"'))
 ascii=[float(x.rstrip('f')) for x in line.split('{{',1)[1].split('},',1)[0].split(',')];hangul=float(line.split('},',1)[1].split('f,')[0]);rows=[]
 for label in sorted(labels):
  em=sum(ascii[ord(c)-32] if 32<=ord(c)<127 else hangul for c in label);size=min(20,320/max(.1,em));width=max(139.3333,size*em+62)
  actual=ImageFont.truetype(str(ROOT/'fonts/pretendard/Pretendard-Medium.otf'),round(size*64)).getlength(label)/64
  assert actual<=width-54,(label,actual,width-54)
  rows.append({'characters':len(label),'font':size,'plateWidth':width,'actualTextWidth':actual,'availableTextWidth':width-54})
 result={'ok':True,'uniqueNames':len(rows),'maximumWidth':max(r['plateWidth'] for r in rows),'rows':rows,'scope':'Actual OTF FreeType advances against em-based game sizing; native representative images are separate.'}
 (ROOT/'Game/Saved/nonstop-ammo-20261107/label-fit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('OTF fit PASS',len(rows),'max plate',result['maximumWidth'])
if __name__=='__main__':main()
