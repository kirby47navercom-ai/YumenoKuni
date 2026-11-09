"""Compose redrawn grayscale ID photos with the existing purple-marked frame."""
from pathlib import Path
import hashlib
import json
import subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art/trial3d/memorial_v3'
SLUGS = 'mio rin ken nana taiga ai rei sora haruka sho koto akari riku satsuki yuu kaede'.split()
FRAME = ROOT / 'art/hd_v4/memorial/frame_blood_x.webp'
SIZE = 2048

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = {}
    for slug in SLUGS:
        portrait = ROOT / f'art/hd_v4/id_portraits_color_v1/{slug}.webp'
        with Image.open(portrait) as im:
            box = (0, 0, *im.size)
            width, height = im.size
        assert box, slug
        # Export the same editable composition without large inline-raster SVG surfaces.
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{SIZE}" height="{SIZE}" viewBox="0 0 1254 1254">
<defs><filter id="neutral"><feColorMatrix type="saturate" values="0"/></filter><linearGradient id="paper" x2="0" y2="1"><stop stop-color="#a0a0a0"/><stop offset="1" stop-color="#373737"/></linearGradient><clipPath id="photo"><rect x="420" y="302" width="485" height="660"/></clipPath></defs>
<g clip-path="url(#photo)" filter="url(#neutral)"><rect x="420" y="302" width="485" height="660" fill="url(#paper)"/>
<svg x="420" y="302" width="485" height="660" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMin slice"><image xlink:href="../../hd_v4/id_portraits_color_v1/{slug}.webp" width="{width}" height="{height}"/></svg></g>
<image xlink:href="../../hd_v4/memorial/frame_blood_x.webp" width="1254" height="1254"/>
</svg>'''
        source = OUT / f'{slug}.svg'
        source.write_text(svg, encoding='utf8')
        output = OUT / f'{slug}.webp'
        identity = {'portrait_sha256': sha(portrait), 'frame_sha256': sha(FRAME), 'svg_sha256': sha(source), 'renderer': 'sharp-buffer-layer-composite-v1-neutral-photo'}
        stamp = OUT / f'{slug}.json'
        if not (stamp.exists() and output.exists() and all(json.loads(stamp.read_text()).get(k) == v for k, v in identity.items())):
            # SVG composition/render and format conversion; no generated face or painted pixels.
            subprocess.run(['node', str(ROOT/'tools/render_memorial_layers.mjs'), str(portrait), str(FRAME), str(output)], check=True)
        with Image.open(output) as im:
            assert im.size == (SIZE, SIZE) and im.mode == 'RGBA'
            assert im.getpixel((0, 0))[3] == 0
            assert im.getpixel((1070, 620))[3] > 250, 'photo backing fills the opening'
            back = Image.new('RGBA', im.size, (0,0,0,0))
            back.putalpha(im.getchannel('A'))
            back.save(OUT/f'{slug}_back.webp', 'WEBP', lossless=True, method=4)
        row = {**identity, 'character': slug, 'portrait_source': portrait.relative_to(ROOT).as_posix(),
               'frame_source': FRAME.relative_to(ROOT).as_posix(), 'editable_source': source.relative_to(ROOT).as_posix(),
               'texture': f'Assets/Art/memorials/{slug}.webp', 'back': f'Assets/Art/memorials/{slug}_back.webp', 'file': output.relative_to(ROOT).as_posix(),
               'size': [SIZE, SIZE], 'mark': 'purple_blood_x', 'width': 1.2, 'height': 1.2, 'center': 1.85,
               'photo_alpha_bbox': list(box), 'output_sha256': sha(output)}
        stamp.write_text(json.dumps(row, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        rows[slug] = row
    assert len({x['output_sha256'] for x in rows.values()}) == 16, 'Every frame must contain its own different photo'
    manifest = {'purpose': 'Per-character courtroom memorials, regardless of current survival status; runtime selects only actual dead seats',
                'frame_art': 'built-in image_gen edit, locally Real-ESRGAN4x; original ribbons removed, purple blood X, transparent opening',
                'portrait_policy': '16 full COLOR formal ID masters, built-in image_gen reference edits and local Real-ESRGAN4x. Student IDs use these same color files unchanged; memorial export derives grayscale ONLY at composition time. Colored frame and purple blood mark retained.',
                'special_marks': 'No ability-based exception invented without a story-specific reason. Each character has an independent editable source.',
                'characters': rows}
    (OUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(f'Court memorials: {len(rows)} individual photos / purple blood X / {SIZE}px')

if __name__ == '__main__':
    main()
