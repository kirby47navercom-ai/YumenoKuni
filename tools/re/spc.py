"""Read PC V3 CPS. archives. Independently implemented from format research.

Reference: CaptainSwag101/DRV3-Sharp, commit
3155b11f225e2223dcdd4cc8555f0e051808e931, SPC serializer/compressor.
Only extracts to caller-selected directories; never changes the source.
"""
import argparse
import json
from pathlib import Path
import struct


def decompress(data, expected):
    out = bytearray()
    cursor = 0
    while cursor < len(data):
        flags = data[cursor]
        cursor += 1
        for bit in range(7, -1, -1):
            if cursor == len(data):
                break
            if flags & (1 << bit):
                out.append(data[cursor])
                cursor += 1
            else:
                if cursor + 2 > len(data):
                    raise ValueError('truncated SPC backreference')
                value = struct.unpack_from('<H', data, cursor)[0]
                cursor += 2
                length, offset = (value >> 10) + 2, value & 1023
                for _ in range(length):
                    source = len(out) - 1024 + offset
                    if source < 0 or source >= len(out):
                        raise ValueError('invalid SPC backreference')
                    out.append(out[source])
            if len(out) > expected:
                raise ValueError('SPC output exceeds declared size')
    if len(out) != expected:
        raise ValueError(f'SPC size mismatch {len(out)} != {expected}')
    return bytes(out)


def entries(data):
    if len(data) < 80 or data[:4] != b'CPS.' or data[64:68] != b'Root':
        raise ValueError('not a PC CPS. archive')
    count = struct.unpack_from('<I', data, 40)[0]
    cursor = 80
    result = []
    for index in range(count):
        start = cursor
        if cursor + 32 > len(data):
            raise ValueError('truncated SPC entry header')
        flag, unknown, size, original, name_length = struct.unpack_from('<HHIII', data, cursor)
        cursor += 32
        end_name = cursor + name_length
        if end_name >= len(data) or data[end_name] != 0:
            raise ValueError('invalid SPC filename terminator')
        name = data[cursor:end_name].decode('cp932')
        cursor += (name_length + 1 + 15) & ~15
        if cursor + size > len(data) or flag not in (1, 2):
            raise ValueError('invalid SPC payload bounds or compression')
        result.append(dict(index=index, name=name, header_offset=start,
                           offset=cursor, stored_size=size, size=original,
                           compression=flag, unknown=unknown))
        cursor += (size + 15) & ~15
    return result


def payload(data, entry):
    raw = data[entry['offset']:entry['offset'] + entry['stored_size']]
    if entry['compression'] == 2:
        return decompress(raw, entry['size'])
    if len(raw) != entry['size']:
        raise ValueError('uncompressed SPC size mismatch')
    return raw


def extract(data, output):
    root = Path(output).resolve()
    listing = entries(data)
    for entry in listing:
        target = (root / entry['name']).resolve()
        if not target.is_relative_to(root):
            raise ValueError('SPC path escapes output directory')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload(data, entry))
    return listing


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--extract', type=Path)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    print(json.dumps(extract(raw, args.extract) if args.extract else entries(raw), ensure_ascii=False, indent=2))
