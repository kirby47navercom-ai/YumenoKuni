"""Restore encrypted code bytes in a static-analysis copy of SteamStub3.1 x64.

Format research: atom0s/Steamless commit
cd770bf9749d3e4f438d23ac643917ad1a804257, Variant31.x64 header/Main and
API/Crypto/AesHelper.cs. This implementation is independently authored.
https://github.com/atom0s/Steamless/tree/cd770bf9749d3e4f438d23ac643917ad1a804257

Only the code-section byte range changes. Entry point, TLS, .bind and Steamworks
integration remain byte-identical. This intentionally is NOT a runnable unpacked
game: the retained packing stub would try to decrypt the restored code again.
Do not execute the result; open it only in a static analysis tool.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def xor_header(data):
    if len(data) != 240:
        raise ValueError('SteamStub3.1 header must be 240 bytes')
    words = struct.unpack('<60I', data)
    result = [words[0]] + [a ^ b for a,b in zip(words, words[1:])]
    decoded = struct.pack('<60I', *result)
    if result[1] != 0xC0DEC0DF:
        raise ValueError('Not a SteamStub3.1 header')
    return decoded


def restore(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output or output.exists():
        raise ValueError('Choose a new derived output path')
    raw = source.read_bytes()
    if raw[:2] != b'MZ':
        raise ValueError('Not a PE file')
    nt = struct.unpack_from('<I', raw, 60)[0]
    if raw[nt:nt+4] != b'PE\0\0' or struct.unpack_from('<H', raw, nt+4)[0] != 0x8664:
        raise ValueError('Only x64 PE is supported')
    optional, count = nt + 24, struct.unpack_from('<H', raw, nt+6)[0]
    size = struct.unpack_from('<H', raw, nt+20)[0]
    if struct.unpack_from('<H', raw, optional)[0] != 0x20b:
        raise ValueError('Expected PE32+ optional header')
    base = struct.unpack_from('<Q', raw, optional+24)[0]
    ep = struct.unpack_from('<I', raw, optional+16)[0]
    sections = []
    for index in range(count):
        at = optional + size + 40 * index
        name = raw[at:at+8].split(b'\0')[0].decode('ascii')
        virtual_size, rva, raw_size, file_offset = struct.unpack_from('<4I', raw, at+8)
        if file_offset + raw_size > len(raw):
            raise ValueError('PE section exceeds file')
        sections.append({'name': name, 'rva': rva, 'virtual_size': virtual_size,
                         'raw_size': raw_size, 'file_offset': file_offset})

    def owner(rva):
        matches = [s for s in sections if s['rva'] <= rva < s['rva'] + max(s['virtual_size'], s['raw_size'])]
        if len(matches) != 1:
            raise ValueError('RVA does not have exactly one owner section')
        return matches[0]

    stub = owner(ep)
    if stub['name'] != '.bind':
        raise ValueError('Entry point is not in .bind; TLS variants unsupported')
    ep_offset = stub['file_offset'] + ep - stub['rva']
    if raw[ep_offset:ep_offset+14] != bytes.fromhex('e800000000505351525657554150'):
        raise ValueError('Known SteamStub x64 signature not found at entry point')
    header = xor_header(raw[ep_offset-240:ep_offset])
    image, packed_ep = struct.unpack_from('<QQ', header, 8)
    original_ep = struct.unpack_from('<Q', header, 32)[0]
    app, flags = struct.unpack_from('<II', header, 56)
    code_rva, code_size = struct.unpack_from('<QQ', header, 72)
    if image != base or packed_ep != ep or flags & 4:
        raise ValueError('SteamStub header identity or encryption flags mismatch')
    section = owner(code_rva)
    if section['rva'] != code_rva or section['raw_size'] != code_size or code_size % 16:
        raise ValueError('Encrypted code region differs from complete aligned PE section')
    key, stored_iv, stolen = header[88:120], header[120:136], header[136:152]
    transform = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
    iv = transform.update(stored_iv) + transform.finalize()
    offset = section['file_offset']
    encrypted = stolen + raw[offset:offset+code_size]
    transform = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    decoded = transform.update(encrypted) + transform.finalize()
    # Verify the transform in reverse without saving any encryption material.
    transform = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    if transform.update(decoded) + transform.finalize() != encrypted:
        raise ValueError('AES restoration roundtrip failed')
    result = bytearray(raw)
    result[offset:offset+code_size] = decoded[:code_size]
    if len(result) != len(raw) or result[:offset] != raw[:offset] or result[offset+code_size:] != raw[offset+code_size:]:
        raise ValueError('Derived PE changed outside code-section bytes')
    record = {'source': str(source), 'source_sha256': hashlib.sha256(raw).hexdigest(),
              'output': str(output), 'output_sha256': hashlib.sha256(result).hexdigest(),
              'variant': 'SteamStub3.1 x64', 'image_base': hex(base),
              'entrypoint_rva_retained': hex(ep), 'header_original_entrypoint_rva': hex(original_ep),
              'steam_app_id': app, 'stub_flags_unchanged': flags, 'header_file_offset': ep_offset-240,
              'restored_section': section, 'restored_prefix_hex': decoded[:32].hex(),
              'all_other_bytes_identical': True, 'aes_roundtrip_verified': True,
              'sections': sections,
              'reference_commit': 'cd770bf9749d3e4f438d23ac643917ad1a804257',
              'limitations': ['Static analysis copy only. Never execute this copy.',
                              'Packing stub and original entry point intentionally unchanged.',
                              'Runtime behavior has not been observed or changed.']}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as target:
        target.write(result)
    output.with_suffix(output.suffix+'.provenance.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(args.source, args.output), indent=2))
