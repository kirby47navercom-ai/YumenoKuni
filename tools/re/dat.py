"""Read V3 typed DAT tables (not the unrelated wrd_data binary DAT format).

Format cross-check: redssu/Harmony-Tools dependencies/V3Lib/Dat/DatFile.cs.
Offsets in JSON are absolute source byte offsets. No source bytes are modified.
"""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

TYPES = dict(u8='B', u16='H', u32='I', u64='Q', s8='b', s16='h',
             s32='i', s64='q', f32='f', f64='d', ascii='H', label='H',
             refer='H', utf16='H')


def parse_dat(data):
    def unpack(fmt, pos):
        size = struct.calcsize('<' + fmt)
        if pos < 0 or pos + size > len(data):
            raise ValueError(f'DAT read outside file at {pos:#x}')
        return struct.unpack_from('<' + fmt, data, pos)

    def string(pos, encoding='utf-8'):
        start = pos
        step = 2 if encoding == 'utf-16-le' else 1
        while pos + step <= len(data) and data[pos:pos+step] != bytes(step):
            pos += step
        if pos + step > len(data):
            raise ValueError(f'unterminated DAT string at {start:#x}')
        return data[start:pos].decode(encoding), pos + step

    rows, stride, count = unpack('III', 0)
    if count > 65535 or rows > 10000000:
        raise ValueError('not a supported typed DAT header')
    pos, columns, expected_stride = 12, [], 0
    for _ in range(count):
        descriptor_offset = pos
        name, pos = string(pos)
        kind, pos = string(pos, 'ascii')
        length, = unpack('H', pos)
        pos += 2
        kind = kind.lower()
        if kind not in TYPES:
            raise ValueError(f'unsupported DAT column type {kind!r} at {descriptor_offset:#x}')
        columns.append(dict(name=name, type=kind, count=length,
                            descriptor_offset=descriptor_offset, row_offset=expected_stride))
        expected_stride += struct.calcsize('<' + TYPES[kind]) * length
    if expected_stride > stride:
        raise ValueError(f'columns need {expected_stride} bytes but row stride is {stride}')
    row_start = (pos + 15) & ~15
    pool_start = row_start + rows * stride
    utf8_count, utf16_count = unpack('HH', pool_start)
    pos, utf8, utf16 = pool_start + 4, [], []
    for _ in range(utf8_count):
        value, pos = string(pos)
        utf8.append(value)
    pos = (pos + 1) & ~1
    for _ in range(utf16_count):
        value, pos = string(pos, 'utf-16-le')
        utf16.append(value)
    output, references = [], []
    for row in range(rows):
        values, refs = [], {}
        for col_index, col in enumerate(columns):
            at = row_start + row * stride + col['row_offset']
            raw = unpack(TYPES[col['type']] * col['count'], at)
            pool = utf16 if col['type'] == 'utf16' else utf8
            if col['type'] in ('ascii', 'label', 'refer', 'utf16'):
                refs[str(col_index)] = list(raw)
                if any(index >= len(pool) for index in raw):
                    raise ValueError(f'DAT string index outside pool at {at:#x}')
                raw = tuple(pool[index] for index in raw)
            # Preserve nonfinite float bit patterns explicitly in strict JSON.
            cooked = [v if not isinstance(v, float) or math.isfinite(v)
                      else {'nonfinite': repr(v)} for v in raw]
            values.append(cooked[0] if len(cooked) == 1 else cooked)
        output.append(values)
        references.append(refs)
    return dict(format='V3 typed DAT', sha256=hashlib.sha256(data).hexdigest(),
                size=len(data), row_count=rows, bytes_per_row=stride, columns=columns,
                row_data_offset=row_start, string_pool_offset=pool_start,
                utf8_count=utf8_count, utf16_count=utf16_count,
                trailing_bytes=len(data)-pos, unknown_row_bytes=stride-expected_stride,
                rows=output, string_indices=references,
                limitations=['Column names are authored metadata, not proof of runtime use.',
                             'wrd_data binary DAT variant is unsupported.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = parse_dat(args.source.read_bytes())
    result['source'] = str(args.source.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({'rows': result['row_count'], 'columns': len(result['columns']), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
