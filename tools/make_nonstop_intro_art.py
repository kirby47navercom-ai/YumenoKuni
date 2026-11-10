"""Original editable vector title/streaks, outlined from the project's OFL brush font."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'ui/v4/nonstop_intro'
FONT = ROOT / 'fonts/dokdo/Dokdo-Regular.ttf'


def lettering(text, width, height, fill, stroke, glow=False):
    font = TTFont(FONT)
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    advance, boxes = 0, []
    for c in text:
        glyph = glyphs[cmap[ord(c)]]
        bounds = BoundsPen(glyphs); glyph.draw(bounds)
        if bounds.bounds:
            left, bottom, right, top = bounds.bounds
            boxes.append((advance+left,bottom,advance+right,top))
        advance += glyph.width
    left,bottom,right,top=min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)
    scale = min((width - 48) / (right-left), (height - 40) / (top-bottom))
    x = (width-(right-left)*scale)/2-left*scale
    baseline = (height+(top-bottom)*scale)/2+bottom*scale
    paths = []
    for c in text:
        glyph = glyphs[cmap[ord(c)]]
        pen = SVGPathPen(glyphs)
        glyph.draw(pen)
        paths.append(f'<path d="{pen.getCommands()}" transform="translate({x:.3f} {baseline:.3f}) scale({scale:.6f} {-scale:.6f})" vector-effect="non-scaling-stroke"/>')
        x += glyph.width * scale
    font.close()
    ink = ''.join(paths)
    halo = ''.join(f'<g fill="{fill}" stroke="{stroke}" stroke-width="{w}" opacity="{a}" stroke-linejoin="round">{ink}</g>' for w, a in [(22,.08),(14,.14),(8,.3)]) if glow else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><title>{escape(text)}</title><desc>Original lettering; Dokdo OFL project font. No reference-game pixels.</desc>{halo}<g fill="{fill}" stroke="{stroke}" stroke-width="1.5" stroke-linejoin="round" paint-order="stroke" vector-effect="non-scaling-stroke">{ink}</g></svg>'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'nonstop_title.svg').write_text(lettering('논스톱 논의', 1280, 260, '#080716', '#17cbe8'), encoding='utf-8')
    (OUT / 'nonstop_start.svg').write_text(lettering('시작!', 700, 300, '#00d9ff', '#08baff', True), encoding='utf-8')
    (OUT / 'nonstop_start_echo.svg').write_text(lettering('시작!', 700, 300, '#049bff', '#006aff', True), encoding='utf-8')
    for i, char in enumerate('논스톱논의'):
        (OUT / f'nonstop_glyph{i}.svg').write_text(lettering(char, 256, 300, '#080812', '#061429'), encoding='utf-8')
        (OUT / f'nonstop_glow{i}.svg').write_text(lettering(char, 256, 300, '#00cfff', '#006bff', True), encoding='utf-8')
    (OUT / 'nonstop_hoop.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800"><title>Concentric cyan impact ring</title><g fill="none" stroke="#087eff"><circle cx="400" cy="400" r="370" stroke-width="19" opacity=".1"/><circle cx="400" cy="400" r="370" stroke-width="9" opacity=".2"/><circle cx="400" cy="400" r="370" stroke="#27baff" stroke-width="2.5" stroke-dasharray="112 9 37 6 89 12" opacity=".95"/></g></svg>', encoding='utf-8')
    colors = ['#17d5ff', '#0075ff', '#bc35ed', '#ff49cc', '#60ffaf', '#b4f7ff']
    lines = []
    for i in range(26):
        y = 25 + i * 5
        bend = (i % 5 - 2) * 10
        curve=f'M-80 {y} C400 {y+bend} 1050 {y-bend} 1740 {y+4}'
        lines.append(f'<path d="{curve}" fill="none" stroke="{colors[i%6]}" stroke-width="{7+i%3}" opacity=".12"/><path d="{curve}" fill="none" stroke="{colors[i%6]}" stroke-width="{2+i%3}" opacity="{.65+(i%4)*.1}"/>')
    (OUT / 'nonstop_streaks.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1660" height="180" viewBox="0 0 1660 180"><title>Chromatic moving light trails</title>' + ''.join(lines) + '</svg>', encoding='utf-8')
    print('Original outlined title, START and light trails written.')


if __name__ == '__main__':
    main()
