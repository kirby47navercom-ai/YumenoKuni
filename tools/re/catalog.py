"""Streaming CPK/SPC metadata census; original payloads stay in installation.

SPC layout follows our spc.entries implementation, whose source reference is
DRV3-Sharp commit 3155b11f225e2223dcdd4cc8555f0e051808e931.
This inventories declared members and probes only their stored header bytes;
it does not assert that compressed payloads have been fully decoded.
"""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import struct

from cpk import CPK, FormatError, safe_path
from spc import decompress


def read_child(record, child, inventory_directory=None):
    """Read a census child on demand. `child` may be member index or name.

    For deep records, offsets refer to the decoded immediate SPC parent;
    ancestry carries the path through compressed carriers. No output is written.
    """
    from spc import entries, payload
    children = record['members']
    matches = [entry for entry in children if entry['index'] == child] if isinstance(child, int) else [entry for entry in children if entry['name'] == child]
    if len(matches) != 1:
        raise KeyError(f'Expected exactly one census child matching {child!r}')
    selected = matches[0]
    archive = Path(record['archive'])
    with archive.open('rb') as source:
        if 'parent' in record:
            parent = record['parent']
            if selected['offset'] < 0 or selected['offset'] + selected['stored_size'] > parent['stored_size']:
                raise FormatError('Census child exceeds immediate parent')
            offset = record['parent']['offset'] + selected['offset']
            if offset != selected['absolute_offset']:
                raise FormatError('Census absolute/relative offsets disagree')
            if source.seek(0, 2) < offset + selected['stored_size']:
                raise FormatError('Census range outside source archive')
            source.seek(offset)
            raw = source.read(selected['stored_size'])
            prefix = selected.get('stored_prefix_hex')
            if prefix is not None and raw[:len(bytes.fromhex(prefix))].hex() != prefix:
                raise FormatError('Stored child prefix differs from census identity')
            result = decompress(raw, selected['size']) if selected['compression'] == 2 else raw
        else:
            ancestry = record['ancestry']
            # Locate the outer carrier from the saved sibling CPK inventory.
            inventory_path = Path(inventory_directory or record.get('inventory_directory', Path(__file__).parent)) / (archive.stem + '.json')
            if not inventory_path.exists():
                raise ValueError('Deep read_child record requires inventory_directory pointing to CPK inventory JSONs')
            inventory = json.loads(inventory_path.read_text(encoding='utf-8-sig'))
            if archive.stat().st_size != inventory['archive_size']:
                raise FormatError('Source archive size differs from census identity')
            parents = [m for m in inventory['members'] if m['path'] == ancestry[0]]
            if len(parents) != 1:
                raise FormatError('Deep census outer carrier missing or ambiguous')
            parent = parents[0]
            source.seek(parent['offset'])
            data = source.read(parent['stored_size'])
            for name in ancestry[1:]:
                matches = [m for m in entries(data) if m['name'] == name]
                if len(matches) != 1:
                    raise FormatError('Deep census carrier missing or ambiguous')
                data = payload(data, matches[0])
            matches = [m for m in entries(data) if m['name'] == selected['name']]
            if len(matches) != 1 or any(matches[0][key] != selected[key] for key in ('offset', 'stored_size', 'size', 'compression')):
                raise FormatError('Deep census child disagrees with source')
            result = payload(data, matches[0])
    if len(result) != selected['size']:
        raise FormatError('Census child decoded size mismatch')
    return result


def nested_entries(source, member):
    base, size = member['offset'], member['stored_size']
    if member['compression'] != 'none':
        raise FormatError('Streaming SPC census requires an uncompressed CPK member')

    def read(offset, length):
        if offset < 0 or length < 0 or offset + length > size:
            raise FormatError('SPC range outside parent member')
        source.seek(base + offset)
        data = source.read(length)
        if len(data) != length:
            raise FormatError('Truncated SPC member')
        return data

    header = read(0, 80)
    if header[:4] != b'CPS.' or header[64:68] != b'Root':
        raise FormatError('Unknown SPC signature')
    count = struct.unpack_from('<I', header, 40)[0]
    if count > (size - 80) // 48:
        raise FormatError('Impossible SPC member count')
    cursor, seen, result = 80, set(), []
    for index in range(count):
        start = cursor
        flag, unknown, packed, original, name_length = struct.unpack_from('<HHIII', read(cursor, 32))
        cursor += 32
        name_data = read(cursor, name_length + 1)
        if name_data[-1] != 0:
            raise FormatError('Missing SPC filename terminator')
        name = name_data[:-1].decode('cp932')
        safe_path(Path.cwd(), name)
        if name.casefold() in seen:
            raise FormatError('Duplicate SPC member name')
        seen.add(name.casefold())
        cursor += (name_length + 16) & ~15
        if flag not in (1, 2) or cursor + packed > size:
            raise FormatError('Invalid SPC compression or payload bounds')
        if flag == 1 and packed != original:
            raise FormatError('SPC raw payload size mismatch')
        probe = read(cursor, min(16, packed))
        result.append({'index': index, 'name': name, 'header_offset': start,
                       'offset': cursor, 'absolute_offset': base + cursor,
                       'stored_size': packed, 'size': original,
                       'compression': flag, 'unknown': unknown,
                       'stored_prefix_hex': probe.hex()})
        cursor += (packed + 15) & ~15
    return result, size - cursor


def census(directory, output):
    output.mkdir(parents=True, exist_ok=True)
    summary = {'archives': [], 'cpk_members': 0, 'spc_archives': 0,
               'spc_members': 0, 'extensions': Counter(), 'compression': Counter(),
               'top_level_spc_directories': Counter(), 'errors': []}
    for path in sorted(directory.glob('*.cpk')):
        archive = CPK(path)
        inventory = archive.inventory()
        # One streamed digest pass per complete archive; metadata pass uses seeks.
        with path.open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        inventory['sha256'] = digest
        (output / (path.stem + '.json')).write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
        record = {k:v for k,v in inventory.items() if k not in ('members', 'header')}
        summary['archives'].append(record)
        summary['cpk_members'] += len(archive.members)
        log_path = output / (path.stem + '.spc.jsonl')
        with path.open('rb') as source, log_path.open('w', encoding='utf-8') as log:
            for member in archive.members:
                if Path(member['path']).suffix.lower() != '.spc':
                    continue
                summary['spc_archives'] += 1
                entry = {'archive': str(path), 'archive_sha256': digest, 'parent': member}
                try:
                    children, trailing = nested_entries(source, member)
                    entry.update(members=children, trailing_bytes=trailing)
                    summary['spc_members'] += len(children)
                    summary['extensions'].update(Path(c['name']).suffix.lower() for c in children)
                    summary['compression'].update(str(c['compression']) for c in children)
                    summary['top_level_spc_directories'].update({member['path'].split('/')[0]: len(children)})
                except (ValueError, OSError, UnicodeError, struct.error) as error:
                    entry['error'] = str(error)
                    summary['errors'].append({'archive': path.name, 'parent': member['path'], 'error': str(error)})
                log.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(json.dumps({'archive': path.name, 'sha256': digest, 'cpk_members': len(archive.members)}, ensure_ascii=False), flush=True)
    (output / 'nested-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k != 'archives'}, ensure_ascii=False, indent=2))


def deeper_census(output):
    """Decode only nested SPC carriers, never image/audio/model payloads."""
    summary = {'archives': 0, 'members': 0, 'extensions': Counter(), 'errors': []}
    with (output / 'nested-deeper.jsonl').open('w', encoding='utf-8') as log:
        for listing in sorted(output.glob('*.spc.jsonl')):
            inventory = json.loads(listing.with_name(listing.name.replace('.spc.jsonl', '.json')).read_text(encoding='utf-8'))
            with Path(inventory['archive']).open('rb') as source, listing.open(encoding='utf-8') as lines:
                def descend(data, ancestry):
                    summary['archives'] += 1
                    record = {'archive': inventory['archive'], 'ancestry': ancestry, 'inventory_directory': str(output.resolve()),
                              'offset_coordinate_system': 'decoded immediate parent SPC bytes'}
                    try:
                        children, trailing = nested_entries(io.BytesIO(data), {'offset': 0, 'stored_size': len(data), 'compression': 'none'})
                        for child in children:
                            child.pop('absolute_offset')
                        record.update(members=children, trailing_bytes=trailing)
                        summary['members'] += len(children)
                        summary['extensions'].update(Path(c['name']).suffix.lower() for c in children)
                        log.write(json.dumps(record, ensure_ascii=False) + '\n')
                        for child in children:
                            if Path(child['name']).suffix.lower() == '.spc':
                                raw = data[child['offset']:child['offset'] + child['stored_size']]
                                decoded = decompress(raw, child['size']) if child['compression'] == 2 else raw
                                descend(decoded, ancestry + [child['name']])
                    except (ValueError, OSError, UnicodeError, struct.error) as error:
                        record['error'] = str(error)
                        summary['errors'].append({'ancestry': ancestry, 'error': str(error)})
                        log.write(json.dumps(record, ensure_ascii=False) + '\n')
                for line in lines:
                    entry = json.loads(line)
                    for child in entry.get('members', []):
                        if Path(child['name']).suffix.lower() != '.spc':
                            continue
                        source.seek(child['absolute_offset'])
                        raw = source.read(child['stored_size'])
                        decoded = decompress(raw, child['size']) if child['compression'] == 2 else raw
                        descend(decoded, [entry['parent']['path'], child['name']])
    (output / 'nested-deeper-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--nested-only', action='store_true', help='Reuse saved inventories and census nested SPC carriers only')
    args = parser.parse_args()
    if args.nested_only:
        deeper_census(args.output)
    else:
        census(args.directory, args.output)
        deeper_census(args.output)
