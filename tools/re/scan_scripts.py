"""Reproduce V3 WRD/STX/debate-DAT coverage from saved CPK/SPC inventories.

First run catalog.py against the installed data/win folder. This command then
reads only selected members from the original archives, validates decompression,
and writes lossless decoded JSON outside the repository. Hash-identical payloads
are decoded once; every carrier retains its own ancestry and physical offsets.
"""
import argparse
from collections import Counter
import fnmatch
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct

from catalog import read_child
import stx
import font
import trial_data
import wrd


def scan(inventory, output, match='*', include_trials=False):
    inventory, output = Path(inventory).resolve(), Path(output).resolve()
    repository = Path(__file__).resolve().parents[2]
    if output.is_relative_to(repository):
        raise ValueError('Original script/string dumps must stay outside the repository')
    if output.exists():
        raise FileExistsError('Use a new output directory to preserve earlier evidence')
    listings = sorted(inventory.glob('*.spc.jsonl'))
    if not listings:
        raise ValueError('No SPC inventory JSONL files found; run catalog.py first')
    if (inventory / 'nested-deeper.jsonl').exists():
        listings.append(inventory / 'nested-deeper.jsonl')
    output.mkdir(parents=True)
    (output / 'decoded').mkdir()
    summary = dict(carriers=0, unique_decodes=0, formats=Counter(), warnings=Counter(),
                   command_counts=Counter(), main_command_counts=Counter(), errors=[],
                   scope=match, includes_trials=include_trials,
                   limitations=['Static byte decoding is not runtime observation.',
                                'RSC command names decode via shipped labels; extension argument schemas remain unverified.',
                                'Non-STXT STX decodes as font metrics; glyph rendering is not runtime observation.'])
    cache = {}
    with (output / 'carriers.jsonl').open('w', encoding='utf-8') as log:
        for listing in listings:
            for line in listing.open(encoding='utf-8-sig'):
                parent = json.loads(line)
                if 'error' in parent:
                    summary['errors'].append(dict(listing=str(listing), error=parent['error']))
                    continue
                ancestry = [parent['parent']['path']] if 'parent' in parent else parent['ancestry']
                for entry in parent['members']:
                    ext = Path(entry['name']).suffix.lower()
                    binary_trial = include_trials and (entry['name'].lower() == 'nonstop_type.dat' or
                        re.fullmatch(r'(nonstop|panic|hanron|kokoronpa|scrum|nico)_\d+_\d+(?:_\d+)?\.dat', entry['name'].lower()))
                    if ext not in ('.wrd', '.stx') and not binary_trial:
                        continue
                    identity = Path(parent['archive']).stem + '/' + '/'.join(ancestry + [entry['name']])
                    if not fnmatch.fnmatchcase(identity, match):
                        continue
                    record = dict(archive=parent['archive'], ancestry=ancestry,
                                  entry=entry, identity=identity)
                    try:
                        data = read_child(parent, entry['index'], inventory)
                        digest = hashlib.sha256(data).hexdigest()
                        dialect = 'rsc' if '/minigame/rsc/' in identity else 'main'
                        key = (ext, digest, dialect if ext == '.wrd' else None)
                        if key not in cache:
                            if ext == '.wrd':
                                decoded = wrd.parse(data, dialect=dialect)
                                meta = dict(format='WRD', commands=len(decoded['commands']),
                                            counts=decoded['counts'], warnings=decoded['warnings'], dialect=dialect)
                            elif ext == '.stx' and data[:4] == b'STXT':
                                decoded = stx.parse(data)
                                meta = dict(format='STXT', strings=sum(len(t['strings']) for t in decoded['tables']))
                            elif ext == '.stx':
                                decoded = font.parse(data)
                                meta = dict(format='RESOURCE_STX', resource_format=decoded['format'])
                            else:
                                decoded = trial_data.parse(data, entry['name'])
                                meta = dict(format=decoded['format'], records=len(decoded.get('records', [])),
                                            warnings=decoded.get('warnings', []))
                            destination = output / 'decoded' / (digest + ('.rsc' if ext == '.wrd' and dialect == 'rsc' else '') + ext + '.json.gz')
                            with gzip.open(destination, 'wt', encoding='utf-8', compresslevel=1) as stream:
                                json.dump(decoded, stream, ensure_ascii=False, allow_nan=False)
                            meta['decoded'] = str(destination)
                            cache[key] = meta
                            summary['unique_decodes'] += 1
                        record.update(cache[key], sha256=digest, size=len(data))
                        if ext == '.wrd':
                            summary['command_counts'].update(record['counts'])
                            if record['dialect'] == 'main':
                                summary['main_command_counts'].update(record['counts'])
                        summary['formats'].update([record['format']])
                        summary['warnings'].update(w['kind'] for w in record.get('warnings', []))
                    except (ValueError, OSError, UnicodeError, IndexError, KeyError, struct.error) as error:
                        record['error'] = str(error)
                        summary['errors'].append(dict(identity=identity, error=str(error)))
                    log.write(json.dumps(record, ensure_ascii=False) + '\n')
                    summary['carriers'] += 1
            print(json.dumps(dict(listing=listing.name, carriers=summary['carriers'],
                                  errors=len(summary['errors']))), flush=True)
    for field in ('formats', 'warnings', 'command_counts', 'main_command_counts'):
        summary[field] = dict(summary[field])
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('output', type=Path, help='new directory outside the repository')
    parser.add_argument('--match', default='*', help='carrier path glob, including archive stem')
    parser.add_argument('--trial-data', action='store_true')
    args = parser.parse_args()
    report = scan(args.inventory, args.output, args.match, args.trial_data)
    print(json.dumps(dict(carriers=report['carriers'], unique_decodes=report['unique_decodes'],
                         formats=report['formats'], errors=len(report['errors']))))
