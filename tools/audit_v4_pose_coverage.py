"""Reconcile standing coverage without treating generated files as approved art."""
from pathlib import Path
from collections import Counter
import json, re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art/v4_production/pose_coverage.json'


def hd_present(job):
    source = ROOT / job['output']
    stamp = source.with_suffix('.json')
    if not stamp.is_file():
        return False
    metadata = json.loads(stamp.read_text(encoding='utf8'))
    hd = metadata.get('hd_file')
    if not hd:
        return False
    output = ROOT / hd
    return all(p.is_file() for p in (output, output.with_suffix('.webp'), output.with_suffix('.json')))


def main():
    jobs = json.loads((OUT.parent / 'derived_jobs.json').read_text(encoding='utf8'))['jobs']
    participants = sorted({j['character'] for j in jobs if j['family'] == 'derived_acting'})
    common = [f'C{i:02}' for i in range(2, 15)] + [f'T{i:02}' for i in range(1, 5)]
    rows = []
    for slug in participants:
        for pose in common:
            candidates = [j for j in jobs if j['character'] == slug and j['pose'] == pose
                          and (ROOT / j['output']).is_file()]
            rows.append({'character': slug, 'pose': pose,
                         'candidates': [j['id'] for j in candidates],
                         'generated': bool(candidates),
                         'hd_present': any(hd_present(j) for j in candidates),
                         'acceptance': 'individual source/HD/continuity review is separate'})
    legacy = []
    for file in sorted((ROOT / 'art/sprites').glob('*/*.webp')):
        if file.name.startswith('sheet'):
            continue
        slug = file.parent.name
        pose = file.stem.removeprefix(slug + '_')
        if pose in common or pose == 'C01' or (slug == 'lappy' and re.fullmatch(r'L\d{2}', pose)):
            continue
        legacy.append({'character': slug, 'pose': pose,
                       'legacy_file': file.relative_to(ROOT).as_posix(),
                       'status': 'reconcile with rewritten story; not covered by common pose production'})
    groups = Counter(re.match(r'[A-Za-z]+', x['pose'])[0] for x in legacy)
    unique = [j for j in jobs if j['family'].startswith('derived_unique')]
    unique_rows = [{'id': j['id'], 'character': j['character'], 'pose': j['pose'],
                    'generated': (ROOT / j['output']).is_file(),
                    'hd_present': hd_present(j),
                    'acceptance': 'individual source/HD/continuity review is separate'}
                   for j in unique]
    report = {'scope': 'coverage ledger, never artistic acceptance or whole-game completion',
              'unique_requested': len(unique_rows),
              'unique_generated': sum(x['generated'] for x in unique_rows),
              'unique_hd_present': sum(x['hd_present'] for x in unique_rows),
              'unique': unique_rows,
              'common_derived_requested': len(rows),
              'common_derived_generated': sum(x['generated'] for x in rows),
              'common_hd_present': sum(x['hd_present'] for x in rows),
              'base_C01': 'separate selected NAI masters; not included in common derived count',
              'common': rows, 'legacy_extras': legacy,
              'legacy_extra_groups': dict(sorted(groups.items())),
              'definitions': {'U': 'character-specific acting', 'M': 'ability acting',
                              'K': 'childhood flashback', 'R': 'specific flashback identity',
                              'P': 'special acting / identity sequence', 'X': 'breakdown / reveal'},
              'definition_sources': ['docs/spec/12_스프라이트_포즈_CG_목록.md',
                                     'docs/spec/14_코덱스_에셋_작업지시서.md'],
              'all_assets_complete': False, 'runtime_integrated': False}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(f"Common derived generated {report['common_derived_generated']}/{len(rows)}; "
          f"legacy extras requiring story reconciliation {len(legacy)}; no automatic art approval")


if __name__ == '__main__':
    main()
