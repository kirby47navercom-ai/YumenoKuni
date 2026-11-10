"""Register current generated candidates for resumable HD export, never approve art."""
from pathlib import Path
import json
import hashlib
ROOT = Path(__file__).resolve().parents[1]

def main():
    path = ROOT / 'art/v4_production/upscale_jobs.json'
    record = json.loads(path.read_text(encoding='utf8'))
    jobs = record['jobs']
    ids = {j['id'] for j in jobs}
    sources = {j['source'] for j in jobs}
    requests = json.loads((ROOT / 'art/v4_production/derived_jobs.json').read_text(encoding='utf8'))['jobs']
    added = 0
    for job in requests:
        source = job['output']
        if not (ROOT / source).exists() or job['id'] in ids or source in sources:
            continue
        family = 'clean_masters' if job['family'] == 'master_cleanup' else 'derived'
        output = f"art/hd_v4/{family}/{job['character']}/{job['id']}.png"
        meta_path = (ROOT / source).with_suffix('.json')
        if meta_path.exists():
            output = json.loads(meta_path.read_text(encoding='utf8')).get('hd_file', output)
        jobs.append({'id': job['id'], 'source': source, 'output': output,
                     'family': job['family'], 'review': 'candidate; individual HD visual acceptance separate'})
        ids.add(job['id']); sources.add(source); added += 1
    # Include retained drawings too. Upscaling an older candidate never selects it
    # for the game, and excluded independently generated NAI pose batches stay out.
    for folder in ('art/sprites_v4', 'art/fx_v4', 'art/cg_v4', 'art/standing_v4','art/materials_v4','art/bg_v4'):
        for src in sorted((ROOT / folder).rglob('*.png')):
            if any(x in src.relative_to(ROOT / folder).parts for x in ('guides','delivery')) or src.stem.endswith('_mask'):
                continue  # Blender input guides are not delivered 2D art.
            source = src.relative_to(ROOT).as_posix()
            if source in sources:
                continue
            relative = src.relative_to(ROOT / folder)
            family = Path(folder).name
            identifier = family + '_' + '_'.join(relative.with_suffix('').parts)
            if identifier in ids:
                raise ValueError('duplicate HD candidate id: ' + identifier)
            output = f'art/hd_v4/archive_candidates/{family}/{relative.as_posix()}'
            meta_path = src.with_suffix('.json')
            if meta_path.exists():
                output = json.loads(meta_path.read_text(encoding='utf8')).get('hd_file', output)
            jobs.append({'id': identifier, 'source': source,
                         'output': output,
                         'family': 'retained_candidate',
                         'review': 'retained original candidate; upscale is not artistic acceptance'})
            ids.add(identifier); sources.add(source); added += 1
    # Early exports predate synchronous HD creation. Reconcile their stale
    # "upscale: pending" only against an existing, matching export stamp.
    reconciled = 0
    for job in jobs:
        src = ROOT / job['source']
        meta_path = src.with_suffix('.json')
        # A source PNG can appear before its synchronous exporter writes metadata.
        # Repair the early archive default only against a matching completed HD stamp.
        if meta_path.exists():
            source_meta = json.loads(meta_path.read_text(encoding='utf8'))
            desired = source_meta.get('hd_file')
            if desired and desired != job['output'] and (ROOT / desired).with_suffix('.json').exists():
                actual = json.loads((ROOT / desired).with_suffix('.json').read_text(encoding='utf8'))
                if actual.get('source_sha256') == hashlib.sha256(src.read_bytes()).hexdigest():
                    job['output'] = desired
        hd = ROOT / job['output']
        hd_stamp = hd.with_suffix('.json')
        if not all(p.is_file() for p in (src, meta_path, hd, hd.with_suffix('.webp'), hd_stamp)):
            continue
        stamp = json.loads(hd_stamp.read_text(encoding='utf8'))
        if stamp.get('source_sha256') != hashlib.sha256(src.read_bytes()).hexdigest():
            continue
        meta = json.loads(meta_path.read_text(encoding='utf8'))
        if meta.get('hd_file') == job['output'] and meta.get('upscale') == 'complete':
            continue
        meta.update(hd_file=job['output'], upscale='complete')
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        reconciled += 1
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(f'Registered {added}; {len(jobs)} HD candidates including superseded revisions, not final unique assets')
    print(f'Reconciled {reconciled} source HD links; no artistic approval')

if __name__ == '__main__':
    main()
