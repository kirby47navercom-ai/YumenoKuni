"""Read numeric VIS metadata using the installed native consumer contract.

REA 0x140540a40: 4xu32 header, then 8xf32/256 if format0, otherwise
two little-endian24-bit groups containing four6-bit values each, divided63.
Only format1 was observed in all93 installed files. No audio is decoded and
the result deliberately excludes original frame arrays.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct


def unpack_record(data):
    if len(data) != 6:
        raise ValueError('Packed VIS record must contain6bytes')
    return tuple((int.from_bytes(data[k:k + 3], 'little') >> shift) & 63
                 for k in (0, 3) for shift in (18, 12, 6, 0))


def parse_vis(data):
    if len(data) < 16:
        raise ValueError('Truncated VIS header')
    fmt, count, start, length = struct.unpack_from('<4I', data)
    stride = 32 if fmt == 0 else 6
    if len(data) != 16 + count * stride:
        raise ValueError('VIS count/stride does not match file length')
    low, high = [math.inf] * 8, [-math.inf] * 8
    for pos in range(16, len(data), stride):
        values = (tuple(v / 256 for v in struct.unpack_from('<8f', data, pos))
                  if fmt == 0 else tuple(v / 63 for v in unpack_record(data[pos:pos + 6])))
        for channel, value in enumerate(values):
            if not math.isfinite(value):
                raise ValueError('Nonfinite VIS value')
            low[channel] = min(low[channel], value)
            high[channel] = max(high[channel], value)
    return {'format': 'VIS', 'sha256': hashlib.sha256(data).hexdigest(),
            'native_format': fmt, 'record_count': count, 'record_stride': stride,
            'channels': 8, 'loop_start': start, 'loop_length': length,
            'normalized_channel_ranges': [[lo, hi] for lo, hi in zip(low, high)] if count else [],
            'limitations': ['Static numeric metadata; not live visualization.',
                            'Only native_format1 was observed in the installed corpus.',
                            'Channel frequency/amplitude meanings are unresolved.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    print(json.dumps(parse_vis(args.source.read_bytes()), ensure_ascii=False, indent=2))
