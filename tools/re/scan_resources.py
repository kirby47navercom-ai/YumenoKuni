"""Validate every DAT/SRD/SFL carrier from catalog.py inventories, read-only.

Usage: python tools/re/scan_resources.py INVENTORY_DIRECTORY OUTPUT_DIRECTORY
Raw assets are not materialized. Per-SHA decoded metadata and a carrier linkage
ledger are written to OUTPUT_DIRECTORY (choose a directory outside the repo).
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import catalog
import dat
import map_data
import sfl
import srd
import trial_data


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False,
                               separators=(',', ':')), encoding='utf-8')


def _decode(kind, raw, name):
    if kind == 'dat':
        try:
            result = dat.parse_dat(raw)
            return result, dict(status='decoded_typed', rows=result['row_count'],
                                columns=len(result['columns']))
        except (ValueError, UnicodeError) as typed_error:
            try:
                result = trial_data.parse(raw, name)
                return result, dict(status='decoded_binary_debate',
                                    format=result['format'],
                                    records=len(result.get('records',result.get('strings',[]))),
                                    semantic_limitations=result.get('limitations',[]))
            except (ValueError, UnicodeError) as binary_error:
                try:
                    result=map_data.parse(raw,name)
                    return result,dict(status='partial_binary_animation' if result['format'].endswith('_PARTIAL') else 'decoded_binary_map_structure',format=result['format'],
                                       semantic_limitations=result['limitations'])
                except (ValueError,UnicodeError) as map_error:
                    raise ValueError(f'typed: {typed_error}; binary: {binary_error}; map: {map_error}') from map_error
    if kind == 'sfl':
        result = sfl.parse_sfl(raw)
        operations = [op for table in result['tables'] for entry in table['entries']
                      for seq in entry.get('sequences', []) for op in seq['operations']]
        sequence_errors = sum('sequence_decode_error' in entry for table in result['tables']
                              for entry in table['entries'])
        text_errors = sum('text_decode_error' in entry for table in result['tables']
                          for entry in table['entries'])
        operation_errors = sum('decode_error' in op for op in operations)
        residuals = sum(bool(any(bytes.fromhex(op.get('decoded', {}).get('trailing_hex', ''))))
                        for op in operations)
        return result, dict(status='partial' if sequence_errors or operation_errors or residuals or text_errors else 'decoded',
                            tables=len(result['tables']), operations=len(operations),
                            sequence_errors=sequence_errors, operation_errors=operation_errors,
                            text_header_errors=text_errors,
                            nonzero_residual_operations=residuals)
    result = srd.parse_srd(raw)
    blocks = list(srd.walk(result['blocks']))
    errors = sum('decode_error' in block for block in blocks)
    # The catalog keeps offsets/digests for unknown payloads, rather than
    # duplicating shader bytecode as a huge hex string.
    for block in blocks:
        decoded = block.get('decoded', {})
        if 'raw_hex' in decoded:
            decoded['raw_sha256'] = hashlib.sha256(bytes.fromhex(decoded.pop('raw_hex'))).hexdigest()
        for local in decoded.get('local', []):
            if local['length'] > 256:
                local['raw_sha256'] = hashlib.sha256(bytes.fromhex(local.pop('raw_hex'))).hexdigest()
                local.pop('float32_interpretation', None)
                local.pop('uint32_interpretation', None)
    return result, dict(status='partial' if errors else 'structurally_decoded',
                        block_counts=result['block_counts'], block_decode_errors=errors)


def scan(inventory, output, kinds=('dat', 'srd', 'sfl'), max_carriers=None):
    records = []
    files = sorted(inventory.glob('*.spc.jsonl'))
    if (inventory/'nested-deeper.jsonl').exists(): files.append(inventory/'nested-deeper.jsonl')
    for path in files:
        records.extend(json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines())
    seen, counts, pointer_counts = {}, Counter(), Counter()
    started, processed, total = time.monotonic(), 0, 0
    total = sum(Path(member['name']).suffix.lower().lstrip('.') in kinds
                for record in records for member in record['members'])
    output.mkdir(parents=True, exist_ok=True)
    with (output/'carriers.jsonl').open('w', encoding='utf-8') as stream:
        for record in records:
            for member in record['members']:
                kind = Path(member['name']).suffix.lower().lstrip('.')
                if kind not in kinds: continue
                if max_carriers is not None and processed >= max_carriers: break
                carrier = dict(archive=record['archive'], ancestry=record.get('ancestry',
                               [record.get('parent', {}).get('path')]), member=member['name'], kind=kind)
                try:
                    raw = catalog.read_child(record, member['index'], inventory)
                    digest = hashlib.sha256(raw).hexdigest()
                    carrier['sha256'] = digest
                    key = (kind, digest)
                    if key not in seen:
                        try:
                            decoded, metadata = _decode(kind, raw, member['name'])
                            target = output/kind/(digest+'.json')
                            _write(target, decoded)
                            metadata['output'] = str(target.resolve())
                            refs = [dict(block_offset=b['offset'], **ref)
                                    for b in srd.walk(decoded['blocks'])
                                    for ref in b.get('decoded', {}).get('external', [])] if kind == 'srd' else []
                        except (ValueError, UnicodeError) as error:
                            metadata, refs = dict(status='unsupported', error=str(error)), []
                        seen[key] = (metadata, refs)
                    metadata, refs = seen[key]
                    carrier.update(metadata)
                    if refs:
                        sizes = {m['name'].lower(): m['size'] for m in record['members']}
                        base = str(Path(member['name']).with_suffix('')).lower()
                        local_counts = Counter()
                        for ref in refs:
                            if ref['location'] == 'inline_payload':
                                status = 'inline_valid' if ref['range_valid'] else 'inline_invalid'
                            else:
                                size = sizes.get(base+'.'+ref['location'])
                                status = 'missing' if size is None else ('valid' if ref['offset']+ref['length'] <= size else 'invalid')
                            local_counts[status] += 1
                        carrier['pointer_ranges'] = dict(local_counts)
                        pointer_counts.update(local_counts)
                except (ValueError, OSError, KeyError) as error:
                    carrier.update(status='read_error', error=str(error))
                counts[(kind, carrier['status'])] += 1
                stream.write(json.dumps(carrier, ensure_ascii=False)+'\n')
                processed += 1
                if processed % 500 == 0:
                    print(json.dumps(dict(processed=processed, total=total)), flush=True)
            if max_carriers is not None and processed >= max_carriers: break
    summary = dict(processed=processed, total=total, exhausted=processed == total,
                   unique_bodies=len(seen), elapsed_seconds=time.monotonic()-started,
                   counts=[dict(kind=k[0],status=k[1],count=v) for k,v in counts.items()],
                   pointer_ranges=dict(pointer_counts),
                   limitations=['Structural decoding does not prove all runtime semantics.',
                                'SFL framerate/root viewport and SRD world transforms remain separate observations.'])
    _write(output/'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--kinds', nargs='+', choices=['dat','srd','sfl'], default=['dat','srd','sfl'])
    parser.add_argument('--max-carriers', type=int, help='Bounded smoke scan; summary marks coverage incomplete')
    args = parser.parse_args()
    print(json.dumps(scan(args.inventory, args.output, args.kinds, args.max_carriers)))


if __name__ == '__main__': main()
