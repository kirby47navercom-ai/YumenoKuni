"""Small synthetic boundary and format checks; no original-game fixtures."""
import struct
import io
import tempfile
import unittest
from pathlib import Path

from cpk import FormatError, crilayla, safe_path, utf_table
from catalog import nested_entries
from spc import entries
from extra_formats import rsct, san, ppp
from movie import movie
from steamstub import xor_header


def literal_stream(payload):
    bits = ''.join('0' + format(byte, '08b') for byte in reversed(payload))
    bits += '0' * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))[::-1]


class CpkTest(unittest.TestCase):
    def test_crilayla_literals_and_empty(self):
        prefix = bytes(range(256))
        for tail in (b'', b'abc', b'example format payload'):
            stream = literal_stream(tail)
            packed = b'CRILAYLA' + struct.pack('<II', len(tail), len(stream)) + stream + prefix
            self.assertEqual(crilayla(packed, len(tail) + 256), prefix + tail)
            with self.assertRaises(FormatError):
                crilayla(packed, len(tail) + 257)

    def test_crilayla_backreference_and_truncation(self):
        # Literal abc (read backwards), then distance 3, length 3.
        bits = ''.join('0' + format(byte, '08b') for byte in b'cba') + '1' + '0' * 13 + '00'
        bits += '0' * (-len(bits) % 8)
        stream = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))[::-1]
        packed = b'CRILAYLA' + struct.pack('<II', 6, len(stream)) + stream + bytes(256)
        self.assertEqual(crilayla(packed)[256:], b'abcabc')
        with self.assertRaises(FormatError):
            crilayla(packed[:20])

    def test_utf_zero_constant_row_and_cipher(self):
        strings = b'table\0zero\0constant\0row\0value\0'
        schema = bytes([0x14]) + struct.pack('>I', 6)
        schema += bytes([0x3a]) + struct.pack('>II', 11, 24)
        schema += bytes([0x52]) + struct.pack('>I', 20)
        rows = struct.pack('>HH', 123, 456)
        ro = 32 + len(schema)
        so = ro + len(rows)
        end = so + len(strings)
        data = b'@UTF' + struct.pack('>IIIIIHHI', end - 8, ro - 8, so - 8, end - 8, 0, 3, 2, 2)
        data += schema + rows + strings
        expected = [{'zero': 0, 'constant': 'value', 'row': 123}, {'zero': 0, 'constant': 'value', 'row': 456}]
        self.assertEqual(utf_table(data)['rows'], expected)
        version_one = bytearray(data)
        struct.pack_into('>H', version_one, 8, 1)
        self.assertEqual(utf_table(bytes(version_one))['rows'], expected)
        self.assertEqual(utf_table(bytes(version_one))['version'], 1)
        key, encrypted = 0x5f, bytearray()
        for byte in data:
            encrypted.append(byte ^ key)
            key = key * 0x15 & 255
        self.assertEqual(utf_table(bytes(encrypted))['rows'], expected)
        with self.assertRaises(FormatError):
            utf_table(data[:-1])

    def test_extraction_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(safe_path(root, 'sub/file.spc'), root / 'sub/file.spc')
            for name in ('../bad', '/bad', 'C:/bad', 'x:stream', 'CON', 'x/../../bad', 'x./bad', 'x//bad'):
                with self.subTest(name=name), self.assertRaises(FormatError):
                    safe_path(root, name)

    def test_streaming_census_matches_spc_reader(self):
        header = bytearray(80)
        header[:4] = b'CPS.'
        header[64:68] = b'Root'
        struct.pack_into('<I', header, 40, 1)
        entry = struct.pack('<HHIII', 1, 4, 3, 3, 8) + bytes(16)
        data = bytes(header) + entry + b'file.dat\0' + bytes(7) + b'abc' + bytes(13)
        expected = entries(data)
        result, trailing = nested_entries(io.BytesIO(b'padding' + data),
            {'offset': 7, 'stored_size': len(data), 'compression': 'none'})
        self.assertEqual(trailing, 0)
        for key, value in expected[0].items():
            self.assertEqual(result[0][key], value)
        self.assertEqual(result[0]['absolute_offset'], 7 + expected[0]['offset'])

    def test_rsct_and_san(self):
        text = 'example'.encode('utf-16-le') + b'\0\0'
        data = b'RSCT' + struct.pack('<4I', 0, 1, 20, 28)
        data += struct.pack('<III', 123, 28, len(text)) + text
        decoded = rsct(data)
        self.assertEqual(decoded['strings'][0]['text'], 'example')
        self.assertTrue(decoded['strings'][0]['pointer_matches_record'])
        with self.assertRaises(ValueError):
            rsct(data[:-1])
        data = struct.pack('>4sIII', b'$CFH', 0, 0, 1)
        self.assertEqual(san(data)['block_counts'], {'$CFH': 1})
        with self.assertRaises(ValueError):
            san(data[:-1])
        decoded = ppp(b'\x01\x00\x0a\x00\x05\x04abcd\x00')
        self.assertEqual([x['opcode'] for x in decoded['commands']], [10, 5])
        self.assertEqual(decoded['commands'][1]['payload_size'], 4)
        self.assertEqual(decoded['terminator_offset'], 10)
        self.assertEqual(decoded['trailing_bytes'], 0)
        with self.assertRaises(ValueError):
            ppp(b'\x01\x00\x05\x04abc')

    def test_movie_metadata(self):
        def atom(kind, data):
            return struct.pack('>I4s', len(data) + 8, kind) + data
        timing = bytes(12) + struct.pack('>II', 30000, 60000)
        tkhd = atom(b'tkhd', bytes(76) + struct.pack('>II', 1920 * 65536, 1080 * 65536))
        stsd = atom(b'stsd', bytes(4) + struct.pack('>I', 1) + atom(b'avc1', b''))
        stts = atom(b'stts', bytes(4) + struct.pack('>III', 1, 60, 1000))
        mdia = atom(b'mdia', atom(b'mdhd', timing)
                    + atom(b'hdlr', bytes(8) + b'vide')
                    + atom(b'minf', atom(b'stbl', stsd + stts)))
        data = atom(b'ftyp', b'isom') + atom(b'moov', atom(b'mvhd', timing) + atom(b'trak', tkhd + mdia))
        result = movie(io.BytesIO(b'pad' + data), 3, len(data))
        self.assertEqual(result['movie_timing']['duration_seconds'], 2)
        self.assertEqual(result['tracks'][0]['average_samples_per_second'], 30)
        self.assertEqual(result['tracks'][0]['width'], 1920)
        self.assertEqual(result['tracks'][0]['codecs'], ['avc1'])

    def test_steamstub_header_chain(self):
        values = [0x12345678, 0xc0dec0df] + list(range(58))
        encoded = [values[0]]
        for word in values[1:]:
            encoded.append(word ^ encoded[-1])
        self.assertEqual(xor_header(struct.pack('<60I', *encoded)), struct.pack('<60I', *values))
        with self.assertRaises(ValueError):
            xor_header(bytes(240))


if __name__ == '__main__':
    unittest.main()
