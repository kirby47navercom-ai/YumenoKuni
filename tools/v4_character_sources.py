"""One source catalogue for every runtime character route; no legacy art fallback."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def catalogue(hd=False):
    delivery = json.loads((ROOT / 'art/character_delivery_v4/manifest.json').read_text(encoding='utf8'))
    out = {}
    for row in delivery['actors']:
        out[row['character']] = ROOT / row['master_hd' if hd else 'master_source']
    for row in delivery['selected_poses']:
        key = row['character'] + '_' + row['pose']
        out[key] = ROOT / row['hd'] if hd else (ROOT / row['source']).with_suffix('.webp')
    assert len(delivery['actors']) == 17 and len(delivery['selected_poses']) == 400
    for key, source in out.items():
        if not source.is_file():
            raise FileNotFoundError(f'Curated character source missing: {key}: {source}')
        if not source.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError(source)
    return delivery, out


def legacy_codes():
    # Unsupported obsolete pose IDs use the same character's curated master.
    return ([f'C{i:02}' for i in range(1, 15)] + [f'T{i:02}' for i in range(1, 5)]
            + [f'U{i}' for i in range(1, 7)] + [f'K{i:02}' for i in range(1, 4)]
            + [f'P{i:02}' for i in range(1, 13)] + ['P03b', 'M']
            + [f'X{i}' for i in range(1, 6)])
