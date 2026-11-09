"""Bake the revised case art into native book and replay surfaces."""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

from build_v4_comic_book import warp
from revised_comic import ROOT, comic_stage
from v4_comic_geometry import MAIN, PREVIOUS, REPLAY, SIZE, panels, thumb


def build(output, stage):
    presentation = stage['comicPresentation']
    book_path = presentation['bookFile']
    chapter = Path(book_path).stem
    prefix = f'Assets/Art/revision_comic/{chapter}/'
    art = output / prefix
    art.mkdir(parents=True, exist_ok=True)
    assets = {}

    def picture(texture, size, *, cover=False):
        name = Path(texture).name
        if texture.startswith(prefix):
            source = ROOT / 'art/revision_comic' / chapter / name
            if not source.is_file():
                source = ROOT / 'art/inspection_v4/delivery' / name
            assets[texture] = source.as_posix()
        else:
            source = ROOT / texture
        with Image.open(source) as image:
            if cover:
                return ImageOps.fit(image.convert('RGB'), size, method=Image.Resampling.LANCZOS)
            return ImageOps.pad(image.convert('RGB'), size, method=Image.Resampling.LANCZOS, color=(5, 4, 8))

    def save(name, image):
        texture = prefix + f'{stage["id"]}-{name}.webp'
        box = image.getbbox()
        if not box:
            raise ValueError(f'Empty comic surface {name}')
        file = output / texture
        image.crop(box).save(file, lossless=True, method=4)
        assets[texture] = file.as_posix()
        left, top, right, bottom = box
        return {'texture': texture, 'rect': [left, top, right-left, bottom-top]}

    def darken(image):
        return ImageEnhance.Brightness(warp(image, PREVIOUS)).enhance(.32)

    bank = json.loads((ROOT / 'ui/v4/climax_original_20261106/runtime.json').read_text(encoding='utf-8'))
    question = bank['sharedPageUI']['questionPink']['texture']
    pages, layers, replay = [], {}, []
    for index, page in enumerate(presentation['pages']):
        slots, contexts = page['slots'], page['contexts']
        assert 3 <= len(slots) + len(contexts) <= 4 and len(contexts) >= 1
        geometry = page.get('panelRects', panels(len(slots) + len(contexts)))
        assert len(geometry) == len(slots) + len(contexts)
        slot_positions = list(zip(slots, geometry[:len(slots)]))
        base = Image.new('RGBA', SIZE, (3, 2, 5, 255))
        for (cx, cy, cw, ch), texture in zip(geometry[len(slots):], contexts):
            base.paste(picture(texture, (cw, ch)), (cx, cy))
        record = {'slots': slots}
        if index == 0:
            record['cover'] = save('cover', darken(base))
        for _, (x, y, w, h) in slot_positions:
            base.paste(picture(question, (w, h), cover='panelRects' in page), (x, y))
        record.update(base=save(f'{index}-base', warp(base, MAIN)),
                      previous=save(f'{index}-previous', darken(base)),
                      thumb=save(f'{index}-thumb', warp(base, thumb(0))))
        for slot, (x, y, w, h) in slot_positions:
            answer = picture(stage['slots'][slot]['options'][0]['image'], (w, h))
            layer = Image.new('RGBA', SIZE)
            layer.paste(answer, (x, y))
            layers[str(slot)] = {'filled': save(f'{slot}-filled', warp(layer, MAIN)),
                                 'previous': save(f'{slot}-filled-previous', darken(layer)),
                                 'thumb': save(f'{slot}-filled-thumb', warp(layer, thumb(0)))}
            base.paste(answer, (x, y))
        record['complete'] = save(f'{index}-complete', warp(base, REPLAY))
        replay.extend({'slot': slot, 'page': index, 'image': record['complete']} for slot in slots)
        pages.append(record)
    assert [row['slot'] for row in replay] == list(range(len(stage['slots'])))
    for choice in presentation['storyStock']:
        if choice['originSlot'] < 0:
            picture(choice['image'], (32, 18))
    recap = picture(presentation['recapImage'], SIZE).convert('RGBA')
    replay.append({'page': len(pages), 'image': save('recap', warp(recap, REPLAY))})
    book = output / book_path
    book.parent.mkdir(parents=True, exist_ok=True)
    book.write_text(json.dumps({'pages': pages, 'slots': layers, 'replay': replay}, separators=(',', ':')), encoding='utf-8')
    assets[book_path] = book.as_posix()
    return assets


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--stdin', action='store_true')
    arguments = parser.parse_args()
    stages = json.load(sys.stdin) if arguments.stdin else [comic_stage()]
    if not stages or any(stage is None for stage in stages):
        raise ValueError('No reviewed comic art')
    assets = {}
    for stage in stages:
        assets.update(build(arguments.output, stage))
    print(json.dumps(assets))
