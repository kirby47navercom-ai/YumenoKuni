"""Technical reference contact sheets, preserving every supplied character reference."""
from pathlib import Path
import json, math
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[1]
J=R/'art/v4_production/completion/jobs'
O=R/'Game/Saved/v4-completion-references';O.mkdir(parents=True,exist_ok=True)
for p in J.glob('*.json'):
 j=json.loads(p.read_text(encoding='utf8'))
 if len(j['references'])<=5:continue
 refs=j['references'];w,h=520,800;cols=3;rows=math.ceil(len(refs)/cols)
 sheet=Image.new('RGB',(cols*w,rows*h),'#e8e2d9');d=ImageDraw.Draw(sheet)
 for i,ref in enumerate(refs):
  with Image.open(R/ref) as raw:
   im=raw.convert('RGBA');im.thumbnail((w-24,h-55));x=(i%cols)*w+(w-im.width)//2;y=(i//cols)*h+40
   sheet.paste(im,(x,y),im)
  d.text(((i%cols)*w+12,(i//cols)*h+10),f'Original attachment {i+1}: {Path(ref).stem}',fill='#17141e')
 dest=O/(j['id']+'.png');sheet.save(dest)
 j['generation_references']=[dest.relative_to(R).as_posix()]
 j['generation_reference_policy']='Technical contact sheet preserves all original references; original attachment numbering is printed above each image.'
 j['generation_prompt_prefix']='The single attached image is a reference CONTACT SHEET. Read original attachment numbers above each reference; every AttachmentN mentioned below means that numbered reference INSIDE this contact sheet. Do not draw the sheet or labels. '
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Packed all oversized reference lists without discarding references')
