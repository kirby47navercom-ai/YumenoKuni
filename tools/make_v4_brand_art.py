"""Original editable outlined wordmark using the project's OFL font, never generated pseudo-text."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];O=R/'ui/v4/brand_hd';O.mkdir(parents=True,exist_ok=True);W,H,S=1200,360,4
path=R/'fonts/blackhansans/BlackHanSans-Regular.ttf';tt=TTFont(path);glyphs=tt.getGlyphSet();cmap=tt.getBestCmap();upem=tt['head'].unitsPerEm;font=ImageFont.truetype(str(path),172*S);im=Image.new('RGBA',(W*S,H*S));d=ImageDraw.Draw(im);svg=[]
def poly(pts,c):
 d.polygon([(round(x*S),round(y*S)) for x,y in pts],fill=c);svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="{c}"/>')
poly([(48,76),(1056,48),(1110,237),(1012,289),(28,281)],'#14131b');poly([(58,294),(1108,255),(1088,273),(47,314)],'#9770cf');poly([(60,321),(899,290),(883,300),(54,332)],'#d34c66')
x=80;baseline=254;scale=172/upem
for ch in '유메노쿠니':
 name=cmap[ord(ch)];pen=SVGPathPen(glyphs);glyphs[name].draw(pen);p=pen.getCommands()
 svg.append(f'<path d="{p}" transform="translate({x+6} {baseline+7}) scale({scale} {-scale})" fill="#9770cf"/>');svg.append(f'<path d="{p}" transform="translate({x} {baseline}) scale({scale} {-scale})" fill="#f3ead9"/>')
 d.text((round((x+6)*S),round((baseline+7)*S)),ch,font=font,fill='#9770cf',anchor='ls');d.text((round(x*S),round(baseline*S)),ch,font=font,fill='#f3ead9',anchor='ls');x+=tt['hmtx'][name][0]*scale+9
for i in range(5):
 x0=1041+i*17;poly([(x0,78),(x0+7,75),(x0+21,121),(x0+14,124)],'#f3ead9')
p=O/'yumeno_wordmark';p.with_suffix('.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S}" height="{H*S}" viewBox="0 0 {W} {H}">'+''.join(svg)+'</svg>\n',encoding='utf8');im.save(p.with_suffix('.png'));im.save(p.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=6)
(O/'manifest.json').write_text(json.dumps({'assets':[{'id':'yumeno_wordmark','source':p.with_suffix('.svg').relative_to(R).as_posix(),'file':p.with_suffix('.webp').relative_to(R).as_posix(),'logical_size':[W,H],'texture_size':list(im.size),'text_baked':'exact Korean brand name as editable glyph paths, not AI glyphs','font_source':path.relative_to(R).as_posix(),'font_license':'fonts/blackhansans/OFL.txt','art_source':'original project lettering/layout/stitch motif','runtime_integrated':False}],'scale':4},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Created original outlined logo, native4800x1440, no generated letters')
