"""Own full-name image binding using OFL glyph outlines, no first-glyph overlay."""
import json
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

data = json.load(sys.stdin)
font = TTFont(data['font'])
glyphs = font.getGlyphSet()
cmap = font.getBestCmap()
upem = font['head'].unitsPerEm
result = {}
trial = data.get('trial', False)
for text in data['names']:
    width = sum(font['hmtx'][cmap.get(ord(ch), '.notdef')][0] for ch in text)
    scale = min((42 if trial else 45) / upem, (212 if trial else 443) / max(1, width))
    x = 36 if trial else 4
    paths = []
    for ch in text:
        name = cmap.get(ord(ch), '.notdef')
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        paths.append(f'<path d="{pen.getCommands()}" transform="translate({x} {130 if trial else 51}) scale({scale} {-scale})" fill="#ffffff"/>')
        x += font['hmtx'][name][0] * scale
    result[text] = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {"256 256" if trial else "455 65"}">' + ''.join(paths) + '</svg>'
json.dump(result, sys.stdout, ensure_ascii=False)
