"""Inventory the supplied UI actually referenced by emitted widgets.

Read-only with respect to game content. Counts are assets/slots, never visual
acceptance or behaviour progress. Embedded PNGs in the existing SFL-projected
SVG carriers count as supplied pixels, but their transforms remain unaccepted.
"""
from pathlib import Path
import base64
import hashlib
import json
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path('C:/Users/kirby/Downloads/v3_re/ui_authorized_20261029')
OUT = ROOT / 'docs/analysis/v3_rebuild/UI_실사용_자재대조_20261103.json'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    bank = read(CACHE / 'manifest.json')
    known = {}
    for row in bank['textures']:
        p = Path(row['path'])
        if not p.is_file():
            raise FileNotFoundError(p)
        known.setdefault(sha(p.read_bytes()), []).append({
            k: row[k] for k in ('container', 'resource', 'size')})

    memo = {}

    def material(texture):
        if texture in memo:
            return memo[texture]
        p = ROOT / 'Game' / texture
        item = {'runtime': texture, 'exists': p.is_file(), 'suppliedPixels': []}
        if p.is_file():
            b = p.read_bytes()
            hashes = [sha(b)]
            if p.suffix.lower() == '.svg':
                hashes += [sha(base64.b64decode(v)) for v in re.findall(
                    rb'data:image/[^;]+;base64,([A-Za-z0-9+/=\r\n]+)', b)]
            for h in dict.fromkeys(hashes):
                if h in known:
                    item['suppliedPixels'].append({'sha256': h, 'origins': known[h]})
            item['classification'] = ('supplied-pixels-direct-or-embedded'
                                      if item['suppliedPixels'] else
                                      'no-byte-provenance-match-not-necessarily-new-art')
        else:
            item['classification'] = 'unresolved-runtime-reference'
        memo[texture] = item
        return item

    widgets = []
    for p in sorted((ROOT / 'Game/Assets/UI').glob('*.hbwidget.json')):
        w = read(p)
        slots = []
        for n in w['nodes']:
            props = n.get('properties', {})
            if n.get('type') != 'Image':
                continue
            tex = props.get('texture', '')
            if tex:
                material(tex)
            slots.append({'id': n['id'], 'texture': tex,
                          'rect': n.get('slot', {}).get('offset'),
                          'z': n.get('slot', {}).get('zIndex'),
                          'fit': props.get('imageFit'),
                          'rotation': props.get('rotation', 0),
                          'initialVisible': props.get('visible', True),
                          'binding': 'static-template' if tex else 'dynamic-not-counted-as-missing-art'})
        widgets.append({'file': p.relative_to(ROOT).as_posix(),
                        'referenceSize': w.get('referenceSize'),
                        'imageSlots': slots,
                        'directSuppliedTemplateSlots': sum(bool(memo[s['texture']]['suppliedPixels']) for s in slots if s['texture']),
                        'visualAcceptance': False})

    selected = read(ROOT / 'ui/v3_authorized/manifest.json')['components']
    tasks = read(ROOT / 'data/v4_story/native_tasks.json')['tasks']
    scrum = []
    for tid, task in tasks.items():
        stage = task.get('stage', {})
        if stage.get('kind') != 'scrum':
            continue
        for pair in stage.get('pairs', []):
            for field in ('usActor', 'themActor'):
                if pair.get(field):
                    scrum.append(pair[field])
    profiles = []
    for actor in sorted(set(scrum)):
        for direction in ('SL', 'SR'):
            target = ROOT / f'Game/Assets/Art/scrum_faces/{actor}_{direction}.webp'
            profiles.append({'actor': actor, 'direction': direction,
                             'runtimeExists': target.is_file(),
                             'needsNewImage': None,
                             'reason': 'Existing profile banks must be visually checked before commissioning replacements; existence is not quality.'})
    result = {
        'status': 'material-and-template-inventory-not-runtime-acceptance',
        'scope': 'All emitted UI widgets; actual controller overrides, hidden widgets and current shipping package are separate.',
        'rules': [
            'Supplied texture totals include unused languages, story-specific images and other excluded content; never treat them as usable UI totals.',
            'Selected/copied is not used. A template reference is not visible native use.',
            'Unmatched SVG/WebP may be adapted or transcoded supplied art; unmatched never means automatically generate an image.',
            'No global percentage or total new-image promise until every presentation and required pose is visually compared.',
            'UI text, masks, camera motion, modelled environments and generated vectors are not new raster commissions.'
        ],
        'cache': {'manifest': str(CACHE / 'manifest.json'), 'textures': len(bank['textures']), 'containers': len(bank['containers'])},
        'selectionManifestComponents': len(selected),
        'summary': {'widgets': len(widgets), 'uniqueStaticTextures': len(memo),
                    'uniqueSuppliedPixelTextures': sum(bool(m['suppliedPixels']) for m in memo.values()),
                    'staticTemplateImageSlots': sum(bool(s['texture']) for w in widgets for s in w['imageSlots']),
                    'dynamicTemplateImageSlots': sum(not s['texture'] for w in widgets for s in w['imageSlots']),
                    'classifications': dict(Counter(m['classification'] for m in memo.values()))},
        'widgets': widgets, 'materials': list(memo.values()),
        'availableContainers': [
            {'container': c['path'], 'availableTextures': c['textures'],
             'staticTemplatePixelUses': [m['runtime'] for m in memo.values()
                if any(o['container'] == c['path']
                       for match in m['suppliedPixels'] for o in match['origins'])],
             'suitability': 'requires-role-and-phase-comparison-not-automatically-usable'}
            for c in bank['containers']],
        'scrumProfilesRequiredByActualTasks': profiles,
        'newRasterTotal': None,
        'newRasterTotalStatus': 'pending-per-presentation-visual-gap-review'
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['summary'], ensure_ascii=False))


if __name__ == '__main__':
    main()
