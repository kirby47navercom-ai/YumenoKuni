"""Repair hash-map keys after the reversible PNG/WebP migration; verify move receipt."""
from pathlib import Path
import collections, hashlib, json

R = Path(__file__).resolve().parents[1]
Q = R / '_삭제대기_2026-10-29'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
plan = read(Q / 'move-plan.json')
receipt = read(Q / 'move-receipt.json')
moves = {a['source']: a['destination'] for a in plan['files']}
pngs = {a['source']: str(Path(a['source']).with_suffix('.webp')).replace('\\', '/')
        for a in plan['files'] if a['category'] == 'A_pixel_identical_png'}
mapping = {k: moves.get(v, v) for k, v in pngs.items()}
cache = {}

def sha(rel):
    if rel not in cache:
        cache[rel] = hashlib.sha256((R / rel).read_bytes()).hexdigest()
    return cache[rel]

changed, hash_updates = [], []

def repair(value, file):
    if isinstance(value, list):
        return [repair(v, file) for v in value]
    if not isinstance(value, dict):
        return value
    out = {}
    for k, v in value.items():
        new_key = mapping.get(k, moves.get(k, k))
        out[new_key] = repair(v, file)
        if k in mapping and isinstance(v, str) and len(v) == 64:
            original = moves[k]
            if v == sha(original):
                out[new_key] = sha(mapping[k])
                hash_updates.append([file, k, new_key])
    return out

for base in ['art', 'ui', 'bg', 'tools']:
    for p in (R / base).rglob('*.json'):
        if p.stat().st_size > 10_000_000:
            continue
        try:
            before = read(p)
        except (OSError, ValueError):
            continue
        rel = p.relative_to(R).as_posix()
        after = repair(before, rel)
        if before != after:
            p.write_text(json.dumps(after, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
            changed.append(rel)

missing, wrong_size, still_at_source = [], [], []
for a in plan['files']:
    dest = R / a['destination']
    if not dest.is_file():
        missing.append(a['destination'])
    elif dest.stat().st_size != a['bytes']:
        wrong_size.append(a['destination'])
    if (R / a['source']).is_file():
        still_at_source.append(a['source'])
counts = collections.Counter(a['category'] for a in plan['files'])
sizes = collections.Counter()
for a in plan['files']:
    sizes[a['category']] += a['bytes']
report = {'status': 'PASS' if not (missing or wrong_size or still_at_source) else 'FAIL',
          'file_count': len(plan['files']), 'moved_bytes': receipt['movedBytes'], 'deleted_bytes': 0,
          'categories': {k: {'files': counts[k], 'bytes': sizes[k]} for k in counts},
          'missing_destinations': missing, 'wrong_size': wrong_size, 'still_at_source': still_at_source,
          'hash_map_files_repaired': changed, 'hash_map_keys_repaired': hash_updates,
          'current_build_exists': (R / plan['current_build_preserved']).is_dir()}
(Q / 'integrity.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({k: v for k, v in report.items() if k not in ['hash_map_keys_repaired', 'categories']}, ensure_ascii=False))
assert report['status'] == 'PASS' and report['current_build_exists']
