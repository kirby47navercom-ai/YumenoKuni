"""Seek-only ISO-BMFF/MP4 track metadata from CPK member ranges.

Reference: https://developer.apple.com/documentation/quicktime-file-format
Uses atom framing, mvhd/mdhd duration, tkhd size, hdlr type, stsd codec and
stts sample timing. Does not decode frames, inspect content, or export movies.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct


def movie(source, base, length):
    def read(at, count):
        if at < 0 or count < 0 or at + count > length:
            raise ValueError('Movie read outside parent CPK member')
        source.seek(base + at)
        result = source.read(count)
        if len(result) != count:
            raise ValueError('Truncated movie metadata')
        return result

    def atoms(start, end):
        result, cursor = [], start
        while cursor < end:
            if end - cursor < 8:
                raise ValueError('Truncated atom header')
            size, kind = struct.unpack('>I4s', read(cursor, 8))
            head = 8
            if size == 1:
                size = struct.unpack('>Q', read(cursor + 8, 8))[0]
                head = 16
            elif size == 0:
                size = end - cursor
            if size < head or cursor + size > end:
                raise ValueError('Invalid atom size')
            result.append({'type': kind.decode('latin1'), 'offset': cursor, 'size': size, 'payload': cursor + head})
            cursor += size
        return result

    def children(atom):
        return atoms(atom['payload'], atom['offset'] + atom['size'])

    def pick(items, kind):
        matches = [a for a in items if a['type'] == kind]
        if len(matches) != 1:
            raise ValueError(f'Expected one {kind} atom')
        return matches[0]

    def timing(atom):
        pos = atom['payload']
        version = read(pos, 1)[0]
        if version == 0:
            scale, duration = struct.unpack('>II', read(pos + 12, 8))
        elif version == 1:
            scale, duration = struct.unpack('>IQ', read(pos + 20, 12))
        else:
            raise ValueError('Unknown movie timing version')
        return {'timescale': scale, 'duration_ticks': duration, 'duration_seconds': duration / scale if scale else None}

    top = atoms(0, length)
    moov = children(pick(top, 'moov'))
    result = {'size': length, 'top_atoms': top, 'movie_timing': timing(pick(moov, 'mvhd')), 'tracks': []}
    for track in (a for a in moov if a['type'] == 'trak'):
        track_children = children(track)
        tkhd = pick(track_children, 'tkhd')
        width, height = struct.unpack('>II', read(tkhd['offset'] + tkhd['size'] - 8, 8))
        media = children(pick(track_children, 'mdia'))
        handler = read(pick(media, 'hdlr')['payload'] + 8, 4).decode('latin1')
        table = children(pick(children(pick(media, 'minf')), 'stbl'))
        stsd = pick(table, 'stsd')
        sample_count = struct.unpack('>I', read(stsd['payload'] + 4, 4))[0]
        descriptions = atoms(stsd['payload'] + 8, stsd['offset'] + stsd['size'])
        if len(descriptions) != sample_count:
            raise ValueError('Movie sample description count mismatch')
        item = {'handler': handler, 'width': width / 65536, 'height': height / 65536,
                'codecs': [a['type'] for a in descriptions], 'timing': timing(pick(media, 'mdhd'))}
        stts = pick(table, 'stts')
        n = struct.unpack('>I', read(stts['payload'] + 4, 4))[0]
        if stts['payload'] + 8 + n * 8 > stts['offset'] + stts['size']:
            raise ValueError('Truncated movie time-to-sample table')
        pairs = [struct.unpack('>II', read(stts['payload'] + 8 + i * 8, 8)) for i in range(n)]
        samples = sum(count for count, delta in pairs)
        ticks = sum(count * delta for count, delta in pairs)
        item.update(sample_count=samples, sample_duration_ticks=ticks, time_to_sample_runs=[list(p) for p in pairs],
                    average_samples_per_second=samples * item['timing']['timescale'] / ticks if ticks else None)
        result['tracks'].append(item)
    return result


def scan(inventory, output):
    results, errors = [], []
    for file in sorted(inventory.glob('partition*.json')):
        doc = json.loads(file.read_text(encoding='utf-8-sig'))
        with Path(doc['archive']).open('rb') as source:
            for member in doc['members']:
                if Path(member['path']).suffix.lower() != '.mp4':
                    continue
                record = {'archive': doc['archive'], 'member': member['path'], 'offset': member['offset']}
                try:
                    record['metadata'] = movie(source, member['offset'], member['stored_size'])
                except (ValueError, OSError, struct.error) as error:
                    record['error'] = str(error)
                    errors.append(record)
                results.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'count': len(results), 'errors': errors, 'movies': results}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'count': len(results), 'errors': len(errors), 'video_dimensions': dict(Counter(str((t['width'],t['height'])) for r in results for t in r.get('metadata',{}).get('tracks',[]) if t['handler']=='vide'))}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    scan(args.inventory, args.output)
