"""Wrap owned rule prose using the actual UI font, inside the source viewport."""
import json
import re
import sys
from pathlib import Path
from PIL import ImageFont

root=Path(__file__).resolve().parents[1]
font=ImageFont.truetype(str(root/'fonts/pretendard/Pretendard-Medium.otf'),300)
payload=json.load(sys.stdin)
out={}
for key,text in payload.items():
    lines=[]
    for paragraph in text.split('\n'):
        line=''
        for token in re.findall(r'\S+|\s+',paragraph):
            if line and not token.isspace() and font.getlength(line+token)/10>878:
                lines.append(line.rstrip());line=''
            if not line and token.isspace():continue
            if font.getlength(token)/10>878:
                for char in token:
                    if line and font.getlength(line+char)/10>878:
                        lines.append(line);line=''
                    line+=char
            else:line+=token
        lines.append(line)
    out[key]={'text':text,'wrapped':'\n'.join(lines),'height':max(73.33333,len(lines)*39),'lines':len(lines)}
print(json.dumps(out,ensure_ascii=False))
