"""Structural decoder for V3 binary debate DAT variants (not typed-table DAT).

Reference baseline: Spiral NonstopDebateV3.kt, commit
f43cfdc845deabaecfc1183a16f77370faf8ec60. Its 12-byte header and
404-byte records are corroborated by installed files. Installed PC trailers,
388/108-byte variants, hanron suffix and style slots came from actual bytes.
Numeric lane views deliberately do not claim camera/time/layout semantics.
"""
import argparse
import json
import math
from pathlib import Path
import re
import struct


NATIVE_DECODE_EVIDENCE = 'ev_9370204cc93bd20b81c65f25cae4c096c3ea5cc8847584b3394f35d68782a58a'
NATIVE_FRAME_OFFSETS = (28, 32, 36, 40, 44, 48, 52, 56, 60, 76, 360, 384)


def _native_record(data, kind, offset):
    """Observed conversion only; names of the runtime animation channels unknown."""
    conversions = []
    for relative in NATIVE_FRAME_OFFSETS:
        value = struct.unpack_from('<f', data, relative)[0]
        if not math.isfinite(value):
            raise ValueError('nonfinite value in native time-conversion lane')
        product = struct.unpack('<f', struct.pack('<f', value * 60.0))[0]
        frames = math.trunc(product)
        if relative != 360:
            frames = (frames + 32768) % 65536 - 32768
        if relative == 384 and frames == 0:
            frames = 1
        if relative == 76 and kind == 'hanron':
            frames = 0
        conversions.append(dict(offset=offset + relative, relative_offset=relative,
                                source_float32=value, runtime_count=frames))
    channels = []
    for index in range(6):
        relative = 120 + index * 36
        channels.append(dict(index=index, offset=offset + relative,
                             vec3_groups=[list(struct.unpack_from('<3f', data, relative + j * 12)) for j in range(3)]))
    return dict(procedure='0x140484ed0', evidence_id=NATIVE_DECODE_EVIDENCE,
                frame_conversions=conversions, six_parameter_groups=channels,
                limitation='Runtime counts and vector copy destinations are proven statically; channel meanings require rendering consumers.')


def _slot(data, offset, width):
    raw = data[offset:offset + width]
    end = raw.find(b'\0')
    if len(raw) != width or end < 0 or any(raw[end:]):
        raise ValueError(f'invalid fixed ASCII slot at {offset:#x}')
    return dict(offset=offset, width=width, text=raw[:end].decode('ascii'))


def _numeric(data, offset):
    """Lossless uint16/signed16 lanes plus explicitly hypothetical float views."""
    values = list(struct.unpack('<' + 'H' * (len(data) // 2), data))
    floats = []
    for relative in range(0, len(data) - 3, 4):
        value = struct.unpack_from('<f', data, relative)[0]
        if value != 0 and math.isfinite(value):
            floats.append(dict(offset=offset + relative, relative_offset=relative,
                               bits=data[relative:relative + 4].hex(), value=value))
    return dict(u16=values, s16=[x if x < 32768 else x - 65536 for x in values],
                nonzero_float32_reinterpretations=floats)


def _scrum_extra(data, offset):
    first, second = [], []
    for index in range(5):
        pos = offset + index * 16
        raw = data[index * 16:index * 16 + 16]
        value = struct.unpack_from('<f', raw, 4)[0]
        first.append(dict(index=index, offset=pos, bytes_0_3=list(raw[:4]),
                          float_4=value, runtime_count_4=value * 60.0,
                          u16_8_14=list(struct.unpack_from('<4H', raw, 8))))
    for index in range(10):
        pos = offset + 80 + index * 8
        raw = data[80 + index * 8:88 + index * 8]
        second.append(dict(index=index, offset=pos,
                           u16_0_4=list(struct.unpack_from('<3H', raw)),
                           u8_6_7=list(raw[6:8]), runtime_counts_6_7=[x * 60 for x in raw[6:8]]))
    return dict(procedure='0x140484630', evidence_id='ev_d0bcc55309779743e70d4487ae1c5c79c27d16cf97b995962bab6abc54d62240',
                five_blocks=first, ten_blocks=second,
                limitation='Field meanings and difficulty selector return values remain unnamed.')


def parse(data, filename):
    name = Path(filename).name.lower()
    if name == 'nonstop_type.dat':
        if len(data) != 3172:
            raise ValueError('unrecognized nonstop_type layout')
        slots = [_slot(data, i * 32, 32) for i in range(96)]
        return dict(format='V3_DEBATE_STYLE_SLOTS', strings=slots,
                    unknown_tail_offset=3072, unknown_tail_hex=data[3072:].hex(),
                    limitation='96 fixed ASCII slots observed; tail semantics unverified')
    match = re.fullmatch(r'(nonstop|panic|hanron|kokoronpa|scrum|nico)_\d+_\d+(?:_\d+)?\.dat', name)
    if match is None or len(data) < 12:
        raise ValueError('not a supported V3 binary debate DAT name/header')
    kind = match[1]
    limit, count, flags, unknown, p0, p1, p2 = struct.unpack_from('<HBB4H', data)
    if not count:
        raise ValueError('empty or unknown binary debate record layout')
    strides = (108,) if kind == 'scrum' else (404,) if kind == 'hanron' else (404, 388)
    extra = 160 if kind == 'scrum' else 0
    suffix = count * 12 if kind == 'hanron' else 0
    matches = [stride for stride in strides if len(data) == 12 + count * stride + extra + 768 + suffix]
    if len(matches) != 1:
        raise ValueError('binary debate length/count do not match a validated layout')
    stride = matches[0]
    records, warnings = [], []
    for index in range(count):
        offset = 12 + index * stride
        record = dict(index=index, offset=offset, size=stride,
                      **_numeric(data[offset:offset + stride], offset))
        if stride == 404:
            record['native_conversion'] = _native_record(data[offset:offset + stride], kind, offset)
        elif kind == 'scrum':
            value = struct.unpack_from('<f', data, offset + 8)[0]
            frames = math.trunc(struct.unpack('<f', struct.pack('<f', value * 60.0))[0]) & 65535
            record['native_conversion'] = dict(procedure='0x140484630',
                evidence_id='ev_d0bcc55309779743e70d4487ae1c5c79c27d16cf97b995962bab6abc54d62240',
                offset=offset + 8, source_float32=value, runtime_count_base=frames,
                even_index_selector_0_count=math.trunc(frames * 1.5),
                even_index_selector_1_count=math.trunc(frames * 1.2))
        if record['u16'][0] != index:
            warnings.append(dict(kind='nonsequential_record_ordinal', offset=offset,
                                 ordinal=index, stored=record['u16'][0]))
        records.append(record)
    extra_offset = 12 + count * stride
    footer = extra_offset + extra
    supplementary = dict(offset=extra_offset, size=extra, hex=data[extra_offset:footer].hex())
    if kind == 'scrum':
        supplementary['native_conversion'] = _scrum_extra(data[extra_offset:footer], extra_offset)
    suffix_data = dict(offset=footer + 768, size=suffix,
                       **_numeric(data[footer + 768:], footer + 768))
    if kind == 'hanron':
        groups, covered = [], 0
        while covered < count:
            pos = footer + 768 + covered * 12
            raw = data[pos:pos + 12]
            span = raw[0]
            if span == 0:
                raise ValueError('invalid native hanron group span')
            if covered + span > count:
                warnings.append(dict(kind='hanron_group_span_exceeds_record_count',
                                     offset=pos, covered=covered, span=span, count=count))
            value = struct.unpack_from('<f', raw, 8)[0]
            groups.append(dict(offset=pos, covered_row_start=covered, covered_row_count=span,
                               bytes_0_7=list(raw[:8]), float32_8=value,
                               runtime_count_8=math.trunc(struct.unpack('<f', struct.pack('<f', value * 60.0))[0])))
            covered += span
        suffix_data['native_groups'] = groups
        suffix_data['native_evidence_id'] = NATIVE_DECODE_EVIDENCE
    return dict(format='V3_BINARY_DEBATE', kind=kind,
                header=dict(offset=0, size=12, time_limit_raw=limit,
                            base_time_count_before_skill=(limit * 60) & 65535,
                            record_count=count, flags_u8_3=flags,
                            unknown_u16_4=unknown, unknown_u16_6=p0,
                            unknown_u16_8=p1, unknown_u16_10=p2),
                stride=stride, records=records,
                supplementary=supplementary,
                asset_slots=[_slot(data, footer + i * 64, 64) for i in range(12)],
                suffix=suffix_data,
                warnings=warnings,
                limitations=['All integer lanes are raw storage, not proven runtime field semantics.',
                             'float32 values are bit reinterpretations; packed integer lanes can look like floats.',
                             'Native-conversion lanes are separately corroborated by 0x140484ed0.',
                             'Stored 388-byte variant is not supported by the observed native 404-byte loader.',
                             'No DR1/DR2 semantic field names are applied to V3.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(parse(args.source.read_bytes(), args.source.name), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
