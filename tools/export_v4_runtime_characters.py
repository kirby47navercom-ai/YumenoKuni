"""Technical runtime export from one curated V4 family; no legacy art fallback."""
import hashlib
import io
import json
from PIL import Image
from game_sprites import heights
from v4_character_sources import ROOT, catalogue, legacy_codes


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    delivery, sources = catalogue()
    art = (ROOT / 'Game/Assets/Art').resolve()
    receipt_path = ROOT / 'Game/Saved/character-style-export.json'
    prior = json.loads(receipt_path.read_text(encoding='utf8')) if receipt_path.exists() else {}
    old = {r['output']: r for r in prior.get('records', [])}
    expected, records, rendered, hashes = set(), [], {}, {}

    def publish(source, dest, role, size=(1536, 2048), figure_height=None, fallback=False):
        dest = art / dest
        assert dest.resolve().is_relative_to(art)
        expected.add(dest.resolve())
        relative = dest.relative_to(ROOT).as_posix()
        if source not in hashes:
            hashes[source] = digest(source)
        key = (str(source), size, figure_height)
        stamp = {'source': source.relative_to(ROOT).as_posix(), 'source_sha256': hashes[source],
                 'role': role, 'size_limit': list(size), 'figure_height': figure_height,
                 'fallback_to_same_character_master': fallback}
        before = old.get(relative, {})
        fresh = dest.is_file() and all(before.get(k) == v for k, v in stamp.items()) and digest(dest) == before.get('output_sha256')
        if not fresh:
            if key not in rendered:
                with Image.open(source) as image:
                    image = image.convert('RGBA')
                    box = image.getchannel('A').point(lambda a: 255 if a > 32 else 0).getbbox()
                    if not box:
                        raise ValueError(source)
                    image = image.crop(box)
                    if figure_height:
                        image.thumbnail((480, figure_height), Image.Resampling.LANCZOS)
                        canvas = Image.new('RGBA', (480, 1040))
                        canvas.alpha_composite(image, ((480-image.width)//2, 1030-image.height))
                        image = canvas
                    else:
                        image.thumbnail(size, Image.Resampling.LANCZOS)
                    buffer = io.BytesIO()
                    image.save(buffer, 'WEBP', quality=94, method=4)
                    rendered[key] = buffer.getvalue()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(rendered[key])
        records.append({'output': relative, **stamp, 'output_sha256': digest(dest)})

    tall = heights()
    top = max(tall.values())
    for actor in delivery['actors']:
        slug = actor['character']
        codes = legacy_codes() if slug != 'lappy' else [f'L{i:02}' for i in range(1, 13)] + [f'X{i}' for i in range(1, 7)]
        for code in codes:
            key = slug + '_' + code
            publish(sources.get(key, sources[slug]), f'sprites/{slug}/{key}.webp', 'dialogue-pose', fallback=key not in sources)
        publish(sources[slug], f'figure/{slug}.webp', 'exploration-standing', figure_height=round(1000*tall.get(slug,top)/top))
        profile = ROOT / f'art/character_delivery_v4/portraits/{slug}.webp'
        publish(profile, f'pad/face_{slug}.webp', 'pad-profile', size=(512,512))
        for number in range(1, 4):
            source = ROOT / f'art/character_delivery_v4/cutins/{slug}_T{number:02}.webp'
            if not source.exists():
                source = profile
            publish(source, f'cutin/{slug}_{number}.webp', 'trial-cutin', size=(1200,1200))

    removed = []
    for family in ['sprites', 'figure', 'cutin']:
        folder = (art / family).resolve()
        assert folder.is_relative_to(art) and folder.name == family
        for path in folder.rglob('*'):
            if path.is_file() and path.suffix.lower() in ('.webp','.png','.jpg') and path.resolve() not in expected:
                removed.append(path.relative_to(ROOT).as_posix())
                path.unlink()
    for path in (art / 'pad').glob('face_*'):
        assert path.resolve().is_relative_to(art)
        if path.is_file() and path.resolve() not in expected:
            removed.append(path.relative_to(ROOT).as_posix())
            path.unlink()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps({'policy':'curated-V4-only; no legacy image fallback',
        'records':records, 'removed_generated_images':removed, 'unique_curated_sources':len(sources),
        'legacy_aliases_are_not_new_illustrated_poses':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f'Curated V4 characters: {len(records)} runtime routes; removed {len(removed)} obsolete generated images')


if __name__ == '__main__':
    main()
