"""RSCT strings and structural SAN/PPP observations, with explicit limits.

RSCT reference read: redssu/Harmony-Tools commit
82ff93c1f181f30e403440be5b91303db32d72f2,
dependencies/V3Lib/Rsct/RsctFile.cs. SAN uses observed SRD block framing;
ANM track semantics and PPP bytecode remain unknown, never invented here.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from catalog import read_child


def rsct(data):
    if len(data) < 20 or data[:4] != b'RSCT':
        raise ValueError('Invalid RSCT signature/header')
    padding, count, table_at, strings_at = struct.unpack_from('<4I', data, 4)
    if table_at != 20 or table_at + count * 8 > strings_at or strings_at > len(data):
        raise ValueError('Invalid RSCT table bounds')
    result, cursor = [], strings_at
    for index in range(count):
        unknown, pointer = struct.unpack_from('<II', data, table_at + index * 8)
        if cursor + 4 > len(data):
            raise ValueError('Truncated RSCT length')
        length = struct.unpack_from('<I', data, cursor)[0]
        if length < 2 or length % 2 or cursor + 4 + length > len(data):
            raise ValueError('Invalid RSCT string length')
        raw = data[cursor + 4:cursor + 4 + length]
        if raw[-2:] != b'\0\0':
            raise ValueError('Missing RSCT string terminator')
        result.append({'index': index, 'unknown': unknown, 'table_pointer': pointer,
                       'string_record_offset': cursor, 'pointer_matches_record': pointer == cursor,
                       'text': raw[:-2].decode('utf-16-le')})
        cursor += 4 + length
    return {'format': 'RSCT', 'padding': padding, 'count': count,
            'table_offset': table_at, 'strings_offset': strings_at,
            'strings': result, 'trailing_bytes': len(data) - cursor}


def san(data):
    def blocks(start, end):
        result, cursor = [], start
        while cursor < end:
            if cursor + 16 > end:
                raise ValueError('Truncated SAN block header')
            magic, length, sub_length, unknown = struct.unpack_from('>4sIII', data, cursor)
            if not magic.startswith(b'$'):
                raise ValueError('Unknown SAN block signature')
            payload_at = cursor + 16
            child_at = (payload_at + length + 15) & ~15
            next_at = (child_at + sub_length + 15) & ~15
            if payload_at + length > end or child_at + sub_length > end or next_at > end:
                raise ValueError('SAN block exceeds parent')
            record = {'type': magic.decode('ascii'), 'offset': cursor, 'payload_offset': payload_at,
                      'payload_size': length, 'sub_offset': child_at, 'sub_size': sub_length,
                      'unknown': unknown, 'payload_sha256': hashlib.sha256(data[payload_at:payload_at + length]).hexdigest(),
                      'prefix_hex': data[payload_at:payload_at + min(length, 64)].hex(),
                      'children': blocks(child_at, child_at + sub_length) if sub_length else []}
            result.append(record)
            cursor = next_at
        return result
    result = blocks(0, len(data))
    def walk(items):
        for item in items:
            yield item
            yield from walk(item['children'])
    return {'format': 'SAN (SRD block framing)', 'blocks': result,
            'block_counts': dict(Counter(item['type'] for item in walk(result))),
            'limitations': ['ANM channels, keyframe codecs, frame rate and duration semantics are unresolved.']}


def ppp(data):
    # Authored from original-VA static bytes in the user's analysis copy:
    # 0x140498982 skips two bytes; 0x1404989a1 reads payload byte length;
    # 0x1404989a5..9ac computes next=command+2+length;
    # 0x140499aa1..aab continues until opcode zero. The native switch accepts
    # opcodes 1..96 but does not identify their meanings here. Payload fields
    # use absolute 16-byte alignment in native memory; no relative alignment
    # assumption or float interpretation is needed for this framing parser.
    if len(data) < 3:
        raise ValueError('Truncated PPP prefix or terminator')
    commands = []
    cursor = 2
    while data[cursor]:
        if cursor + 2 > len(data):
            raise ValueError('Truncated PPP command header')
        opcode, length = data[cursor:cursor + 2]
        next_at = cursor + 2 + length
        if next_at >= len(data):
            raise ValueError('Truncated PPP command payload or terminator')
        commands.append({'offset': cursor, 'opcode': opcode,
                         'payload_offset': cursor + 2, 'payload_size': length,
                         'native_switch_range': 1 <= opcode <= 96})
        cursor = next_at
    return {'format': 'PPP (native TLV framing; effect semantics unresolved)', 'size': len(data),
            'raw_hex': data.hex(), 'prefix_hex': data[:16].hex(),
            'prefix_u16_le': int.from_bytes(data[:2], 'little'),
            'commands': commands, 'terminator_offset': cursor,
            'trailing_bytes': len(data) - cursor - 1,
            'limitations': ['Prefix meaning, opcode effects and payload field types are unresolved.',
                            'Native payload alignment depends on the in-memory carrier address.']}


def scan(inventory, output):
    output.mkdir(parents=True, exist_ok=True)
    summary = {'counts': Counter(), 'errors': [], 'san_blocks': Counter(),
               'rsct_strings': 0, 'rsct_pointer_mismatches': 0, 'ppp_sizes': Counter()}
    with (output / 'extra-formats.jsonl').open('w', encoding='utf-8') as target:
        for file in sorted(inventory.glob('*.spc.jsonl')):
            for line in file.open(encoding='utf-8'):
                record = json.loads(line)
                for child in record.get('members', []):
                    ext = Path(child['name']).suffix.lower()
                    if ext not in ('.san', '.ppp', '.rsct'):
                        continue
                    item = {'archive': record['archive'], 'parent': record['parent']['path'], 'name': child['name']}
                    try:
                        data = read_child(record, child['index'])
                        item['sha256'] = hashlib.sha256(data).hexdigest()
                        item['size'] = len(data)
                        item['decoded'] = {'.san': san, '.ppp': ppp, '.rsct': rsct}[ext](data)
                        summary['counts'][ext] += 1
                        if ext == '.san':
                            summary['san_blocks'].update(item['decoded']['block_counts'])
                        elif ext == '.rsct':
                            summary['rsct_strings'] += item['decoded']['count']
                            summary['rsct_pointer_mismatches'] += sum(not s['pointer_matches_record'] for s in item['decoded']['strings'])
                        else:
                            summary['ppp_sizes'][str(len(data))] += 1
                    except (ValueError, OSError, struct.error) as error:
                        item['error'] = str(error)
                        summary['errors'].append({k:v for k,v in item.items() if k != 'decoded'})
                    target.write(json.dumps(item, ensure_ascii=False) + '\n')
    (output / 'extra-formats-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    scan(args.inventory, args.output)
