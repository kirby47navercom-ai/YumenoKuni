"""Read retained artwork from its reversible cleanup location without recreating duplicates."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
plan = ROOT / '_삭제대기_2026-10-29/move-plan.json'
rows = json.loads(plan.read_text(encoding='utf8'))['files'] if plan.exists() else []
moves = {a['source']: a['destination'] for a in rows}
original_png = {}
for a in rows:
    if a['category'] == 'A_pixel_identical_png':
        webp = str(Path(a['source']).with_suffix('.webp')).replace('\\', '/')
        original_png[moves.get(webp, webp)] = a['destination']

def retained(path):
    p = Path(path)
    p = p if p.is_absolute() else ROOT / p
    if p.exists():
        return p
    rel = p.relative_to(ROOT).as_posix()
    # Metadata beside a retired image can remain at the original working path.
    parts = Path(rel).parts
    if len(parts) > 2 and parts[0] == '_삭제대기_2026-10-29':
        original = ROOT.joinpath(*parts[2:])
        if original.exists():
            return original
    return ROOT / moves.get(rel, rel)

def pair_paths(p, q):
    a, b = retained(p), retained(q)
    if a == b:
        rel = b.relative_to(ROOT).as_posix()
        if rel in original_png:
            a = ROOT / original_png[rel]
    assert a != b, 'Cannot prove pixel equivalence by comparing an image to itself'
    return a, b
