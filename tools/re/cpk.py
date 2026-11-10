"""Read-only CPK inventory and selective extraction, authored for V3 analysis.

Format references read as source (no external executable used):
https://github.com/esperknight/CriPakTools/blob/master/CriPakTools/CPK.cs
https://github.com/kamikat/cpktools/blob/master/cpk/utf.py
https://github.com/vgmstream/vgmstream/blob/master/src/util/cri_utf.c
CPK packets are little-endian; UTF fields are big-endian, offsets relative
to UTF+8. TOC file offsets use min(ContentOffset, TocOffset). ITOC-only
archives are deliberately rejected rather than silently partially inventoried.
"""
import argparse
from collections import Counter
import fnmatch
import hashlib
import json
import os.path
from pathlib import Path, PurePosixPath, PureWindowsPath
import struct


class FormatError(ValueError):
    pass


def span(data, offset, size):
    if offset < 0 or size < 0 or offset + size > len(data):
        raise FormatError(f"Out-of-bounds range {offset}+{size}/{len(data)}")
    return data[offset:offset + size]


def utf_table(data):
    """Decode UTF constants, zero/default columns, per-row scalars and blobs."""
    if not data.startswith(b'@UTF'):
        key = 0x5f
        decrypted = bytearray()
        for byte in data:
            decrypted.append(byte ^ key)
            key = key * 0x15 & 255
        data = bytes(decrypted)
    if span(data, 0, 4) != b'@UTF':
        raise FormatError('Invalid UTF signature')
    size, version, ro, so, do, name, nc, width, nr = struct.unpack('>IHHIIIHHI', span(data, 4, 28))
    if version not in (0, 1):
        raise FormatError(f'Unknown UTF header version {version}')
    if size + 8 > len(data):
        raise FormatError('Truncated UTF table')
    data = data[:size + 8]
    ro, so, do = ro + 8, so + 8, do + 8
    if not 32 <= ro <= so <= do <= len(data) or ro + width * nr > so:
        raise FormatError('Invalid UTF sections')

    def string(offset):
        start = so + offset
        if not so <= start < do:
            raise FormatError('Invalid UTF string offset')
        end = data.find(b'\0', start, do)
        if end < 0:
            raise FormatError('Unterminated UTF string')
        raw = data[start:end]
        try:
            return raw.decode('utf-8')
        except UnicodeDecodeError:
            return raw.decode('shift_jis')

    def value(kind, pos):
        patterns = {0:'B', 1:'b', 2:'H', 3:'h', 4:'I', 5:'i',
                    6:'Q', 7:'q', 8:'f', 9:'d', 10:'I', 11:'II'}
        if kind not in patterns:
            raise FormatError(f'Unknown UTF type {kind}')
        fmt = '>' + patterns[kind]
        count = struct.calcsize(fmt)
        values = struct.unpack(fmt, span(data, pos, count))
        result = values[0]
        if kind == 10:
            result = string(result)
        elif kind == 11:
            result = span(data, do + values[0], values[1])
        return result, pos + count

    columns, pos = [], 32
    for _ in range(nc):
        flags = span(data, pos, 1)[0]
        pos += 1
        if flags == 0:  # Older schema stores flags in a four-byte slot.
            pos += 3
            flags = span(data, pos, 1)[0]
            pos += 1
        no = struct.unpack('>I', span(data, pos, 4))[0]
        pos += 4
        storage, kind = flags & 0xf0, flags & 15
        const = None
        if storage == 0x30:
            const, pos = value(kind, pos)
        elif storage == 0x10:
            const = '' if kind == 10 else b'' if kind == 11 else 0
        elif storage not in (0, 0x50):
            raise FormatError(f'Unknown UTF storage {storage:#x}')
        columns.append((string(no), storage, kind, const))
    if pos > ro:
        raise FormatError('UTF schema overlaps rows')
    rows = []
    for index in range(nr):
        pos = ro + width * index
        row = {}
        for column, storage, kind, const in columns:
            row[column] = const
            if storage == 0x50:
                row[column], pos = value(kind, pos)
        if pos > ro + width * (index + 1):
            raise FormatError('UTF row exceeds declared width')
        rows.append(row)
    return {'name': string(name), 'version': version, 'rows': rows, 'columns': [c[0] for c in columns]}


def crilayla(data, expected=None):
    if span(data, 0, 8) != b'CRILAYLA':
        raise FormatError('Invalid CRILAYLA signature')
    size, prefix_offset = struct.unpack('<II', span(data, 8, 8))
    if expected is not None and size + 256 != expected:
        raise FormatError('CRILAYLA size differs from TOC')
    prefix_start = 16 + prefix_offset
    prefix = span(data, prefix_start, 256)
    result = bytearray(size + 256)
    result[:256] = prefix
    source, pool, left = prefix_start - 1, 0, 0

    def bits(count):
        nonlocal source, pool, left
        value = 0
        while count:
            if not left:
                if source < 16:
                    raise FormatError('Truncated CRILAYLA bitstream')
                pool, source, left = data[source], source - 1, 8
            take = min(left, count)
            value = value << take | (pool >> (left - take) & ((1 << take) - 1))
            left -= take
            count -= take
        return value

    dest = len(result) - 1
    while dest >= 256:
        if not bits(1):
            result[dest] = bits(8)
            dest -= 1
            continue
        back = dest + bits(13) + 3
        length = 3
        for width in (2, 3, 5, 8):
            extra = bits(width)
            length += extra
            if extra != (1 << width) - 1:
                break
        else:
            while True:
                extra = bits(8)
                length += extra
                if extra != 255:
                    break
        if back >= len(result) or length > dest - 255:
            raise FormatError('Invalid CRILAYLA backreference')
        for _ in range(length):
            result[dest] = result[back]
            dest -= 1
            back -= 1
    return bytes(result)


def safe_path(root, name):
    """Reject traversal, drive paths, streams and Windows special filenames."""
    name = name.replace('\\', '/')
    path = PurePosixPath(name)
    if not name or path.is_absolute() or PureWindowsPath(name).drive:
        raise FormatError(f'Unsafe member path: {name!r}')
    for part in name.split('/'):
        if (part in ('', '.', '..') or ':' in part or part.endswith((' ', '.'))
                or os.path.isreserved(part) or any(ord(c) < 32 for c in part)
                or any(c in part for c in '<>"|?*')):
            raise FormatError(f'Unsafe member path: {name!r}')
    root = Path(root).resolve()
    target = root.joinpath(*path.parts).resolve()
    if not target.is_relative_to(root):
        raise FormatError('Member path escapes output directory')
    return target


class CPK:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.size = self.path.stat().st_size
        with self.path.open('rb') as source:
            self.header = self._packet(source, 0, b'CPK ')['rows'][0]
            toc_offset = self.header.get('TocOffset')
            content = self.header.get('ContentOffset')
            if toc_offset is None or content is None:
                raise FormatError('Only named TOC CPKs are supported; no TOC/ContentOffset')
            toc = self._packet(source, toc_offset, b'TOC ')
            base = min(toc_offset, content)
            self.members = []
            seen = set()
            for index, row in enumerate(toc['rows']):
                name = '/'.join(p for p in (row.get('DirName'), row.get('FileName')) if p and p != '<NULL>')
                safe_path(Path.cwd(), name)
                if name.casefold() in seen:
                    raise FormatError('Duplicate member path')
                seen.add(name.casefold())
                offset, packed = base + row['FileOffset'], row['FileSize']
                unpacked = row.get('ExtractSize')
                unpacked = packed if unpacked is None else unpacked
                if offset < content or packed < 0 or offset + packed > self.size:
                    raise FormatError(f'Member {index} outside archive')
                source.seek(offset)
                magic = source.read(min(16, packed))
                compressed = magic.startswith(b'CRILAYLA')
                if compressed and (len(magic) < 16 or struct.unpack('<I', magic[8:12])[0] + 256 != unpacked):
                    raise FormatError(f'Member {index} CRILAYLA size mismatch')
                if not compressed and packed != unpacked:
                    raise FormatError(f'Member {index} has unknown compression')
                self.members.append({'index': index, 'path': name, 'offset': offset,
                    'stored_size': packed, 'size': unpacked, 'compression': 'CRILAYLA' if compressed else 'none',
                    'magic_hex': magic[:8].hex(), 'id': row.get('ID')})
            declared = self.header.get('Files')
            if declared is not None and declared != len(self.members):
                raise FormatError('CPK header file count differs from TOC')
            ranges = sorted((m['offset'], m['offset'] + m['stored_size']) for m in self.members if m['stored_size'])
            if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
                raise FormatError('Overlapping member payloads')

    def _packet(self, source, offset, magic):
        if offset < 0 or offset + 16 > self.size:
            raise FormatError('Packet offset outside CPK')
        source.seek(offset)
        signature, flags, length = struct.unpack('<4sIQ', source.read(16))
        if signature != magic or length > self.size - offset - 16 or length > 256 * 1024 * 1024:
            raise FormatError('Invalid CPK packet header/size')
        return utf_table(source.read(length))

    def inventory(self):
        return {'archive': str(self.path), 'archive_size': self.size,
                'header': {k: {'bytes_hex':v.hex()} if isinstance(v, bytes) else v for k,v in self.header.items()}, 'member_count': len(self.members),
                'stored_bytes': sum(m['stored_size'] for m in self.members),
                'extracted_bytes': sum(m['size'] for m in self.members),
                'compression_counts': dict(Counter(m['compression'] for m in self.members)),
                'extension_counts': dict(Counter(PurePosixPath(m['path']).suffix.lower() for m in self.members)),
                'members': self.members}

    def extract(self, root, exact=(), patterns=()):
        selected = [m for m in self.members if m['path'] in exact or any(fnmatch.fnmatchcase(m['path'], p) for p in patterns)]
        missing = set(exact) - {m['path'] for m in selected}
        if missing:
            raise KeyError(f'Exact members not found: {sorted(missing)}')
        results = []
        with self.path.open('rb') as source:
            for member in selected:
                target = safe_path(root, member['path'])
                if target.exists():
                    raise FileExistsError(target)
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                source.seek(member['offset'])
                if member['compression'] == 'CRILAYLA':
                    payload = crilayla(source.read(member['stored_size']), member['size'])
                    with target.open('xb') as out:
                        out.write(payload)
                    digest.update(payload)
                else:
                    remaining = member['stored_size']
                    with target.open('xb') as out:
                        while remaining:
                            block = source.read(min(1024 * 1024, remaining))
                            if not block:
                                raise FormatError('Unexpected end of member payload')
                            out.write(block)
                            digest.update(block)
                            remaining -= len(block)
                results.append({'path': member['path'], 'output': str(target), 'size': member['size'], 'sha256': digest.hexdigest()})
        return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--exact', action='append', default=[])
    parser.add_argument('--filter', action='append', default=[])
    args = parser.parse_args()
    cpk = CPK(args.archive)
    inventory = cpk.inventory()
    if args.inventory:
        args.inventory.parent.mkdir(parents=True, exist_ok=True)
        args.inventory.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.out:
        if not args.exact and not args.filter:
            parser.error('Extraction requires --exact or --filter (use --filter "*" explicitly for all)')
        extracted = cpk.extract(args.out, args.exact, args.filter)
        print(json.dumps({'extracted_count': len(extracted), 'extracted_bytes': sum(m['size'] for m in extracted)}, ensure_ascii=False))
        log = args.out / (args.archive.stem + '.extraction.json')
        previous = json.loads(log.read_text(encoding='utf-8')) if log.exists() else []
        log.write_text(json.dumps(previous + extracted, ensure_ascii=False, indent=2), encoding='utf-8')
    else:
        print(json.dumps({k:v for k,v in inventory.items() if k not in ('members', 'header')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
