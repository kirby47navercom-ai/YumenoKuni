"""Read STXT/JPLL string tables, retaining IDs and physical offsets.

Format reference: DRV3-Sharp commit 3155b11f225e2223dcdd4cc8555f0e051808e931.
No newline normalization: returned strings preserve original data.
"""
import argparse
import json
from pathlib import Path
import struct


def parse(data):
    if len(data) < 16 or data[:8] != b'STXTJPLL':
        raise ValueError('not an STXT/JPLL string table (STX can also hold SRD resources)')
    count, position = struct.unpack_from('<II', data, 8)
    if 16 + count * 16 > len(data):
        raise ValueError('truncated STX table descriptors')
    tables = []
    for index in range(count):
        unknown, strings = struct.unpack_from('<II', data, 16 + index * 16)
        if position + strings * 8 > len(data):
            raise ValueError('truncated STX index')
        items = []
        for _ in range(strings):
            sid, offset = struct.unpack_from('<II', data, position)
            entry_offset = position
            position += 8
            end = offset
            if offset >= len(data):
                raise ValueError('STX string offset outside file')
            while end + 2 <= len(data) and data[end:end + 2] != b'\0\0':
                end += 2
            if end + 2 > len(data):
                raise ValueError('unterminated STX UTF16 string')
            items.append(dict(id=sid, index_offset=entry_offset, offset=offset,
                              text=data[offset:end].decode('utf-16le')))
        tables.append(dict(index=index, unknown=unknown, strings=items))
    return dict(format='STXT', tables=tables)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(parse(args.source.read_bytes()), ensure_ascii=False, indent=2), encoding='utf-8')
