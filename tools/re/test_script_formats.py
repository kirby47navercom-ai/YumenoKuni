"""Focused corruption and evidence-retention checks; no original game content."""
import struct
import unittest

import spc
import stx
import wrd
import trial_data


class ScriptFormatTests(unittest.TestCase):
    def test_rsc_uses_shipped_distinct_opcode_table(self):
        commands = bytes.fromhex('70 0c 00 00 70 53 00 00 70 58 00 02')
        header = struct.pack('<4H6I', 3, 1, 1, 0, 0, 44, 44, 46, 53, 0)
        data = header + commands + struct.pack('<H', 0) + b'\x05start\0\x07Speaker\0'
        parsed = wrd.parse(data, dialect='rsc')
        self.assertEqual([c['name'] for c in parsed['commands']], ['LAB', 'ADV_CHAR_NAME', 'LOC'])
        argument = parsed['commands'][1]['arguments'][0]
        self.assertIsNone(argument['kind'])
        self.assertEqual(argument['parameter_candidate'], 'Speaker')
        self.assertEqual(parsed['commands'][2]['args'], [2])
        self.assertEqual(parsed['warnings'], [])

    def test_compound_ifw_has_four_item_clauses_and_signed_operand(self):
        commands = bytes.fromhex('70 03 00 00 00 01 ff ff 00 02 00 00 00 01 00 07 70 11')
        header = struct.pack('<4H6I', 0, 0, 3, 0, 0, 50, 50, 50, 50, 0)
        parsed = wrd.parse(header + commands + b'\x01x\0\x02==\0\x02||\0')
        args = parsed['commands'][0]['arguments']
        self.assertEqual(args[2]['signed_value'], -1)
        self.assertEqual(args[3]['resolved'], '||')
        self.assertEqual(args[4]['resolved'], 'x')
        self.assertEqual(args[6]['signed_value'], 7)
        self.assertEqual(parsed['warnings'], [])

    def test_debate_layouts_reject_wrong_stride_and_keep_footer(self):
        header = struct.pack('<HBB4H', 300, 2, 1, 0, 706, 710, 712)
        records = bytearray(808)
        struct.pack_into('<H', records, 404, 1)
        struct.pack_into('<f', records, 32, 5.7)
        footer = b'asset\0' + bytes(58) + bytes(704)
        suffix = bytearray(24)
        suffix[0] = 2
        data = header + records + footer + suffix
        parsed = trial_data.parse(data, 'hanron_01_214.dat')
        self.assertEqual(parsed['stride'], 404)
        self.assertEqual(parsed['records'][1]['offset'], 416)
        self.assertEqual(parsed['asset_slots'][0]['text'], 'asset')
        self.assertEqual(parsed['suffix']['size'], 24)
        counts = {x['relative_offset']: x['runtime_count'] for x in parsed['records'][0]['native_conversion']['frame_conversions']}
        self.assertEqual(counts[32], 342)
        self.assertEqual(counts[384], 1)
        with self.assertRaises(ValueError):
            trial_data.parse(data[:-1], 'hanron_01_214.dat')

    def test_lz_overlapping_copy_and_bounds(self):
        # One literal A followed by a five-byte overlapping copy, window offset 1023.
        self.assertEqual(spc.decompress(bytes.fromhex('80 41 ff 0f'), 6), b'AAAAAA')
        with self.assertRaises(ValueError):
            spc.decompress(bytes.fromhex('00 00 00'), 2)
        with self.assertRaises(ValueError):
            spc.decompress(bytes.fromhex('80 41 ff 0f'), 5)

    def test_stx_preserves_ids_shared_offsets_and_carriage_returns(self):
        data = b'STXTJPLL' + struct.pack('<II', 1, 32)
        data += struct.pack('<4I', 123, 2, 0, 0)
        data += struct.pack('<4I', 42, 48, 7, 48) + 'x\r\ny\0'.encode('utf-16le')
        strings = stx.parse(data)['tables'][0]['strings']
        self.assertEqual([s['id'] for s in strings], [42, 7])
        self.assertEqual(strings[0]['text'], 'x\r\ny')
        self.assertEqual(strings[0]['offset'], strings[1]['offset'])
        with self.assertRaises(ValueError):
            stx.parse(data[:-2])

    def test_wrd_big_endian_arguments_and_reference_resolution(self):
        # LAB label 0; LOC dialogue ID 2; unknown opcode FE carrying number 257.
        commands = bytes.fromhex('70 14 00 00 70 46 00 02 70 fe 01 01')
        header = struct.pack('<4H6I', 3, 1, 0, 0, 0, 44, 44, 46, 53, 0)
        data = header + commands + struct.pack('<H', 0) + b'\x05start\0'
        result = wrd.parse(data)
        self.assertEqual(result['commands'][0]['arguments'][0]['resolved'], 'start')
        self.assertEqual(result['commands'][1]['args'], [2])
        self.assertEqual(result['commands'][2]['args'], [257])
        self.assertEqual(result['commands'][2]['offset'], 40)
        self.assertEqual(result['warnings'][0]['kind'], 'unknown_opcode')
        external = [dict(id=2, offset=100, text='matched by ID'), dict(id=2, offset=100, text='matched by ID')]
        linked = wrd.parse(data, external)
        self.assertEqual(linked['commands'][1]['arguments'][0]['resolved'], 'matched by ID')
        broken = bytearray(data)
        broken[32] = 0
        with self.assertRaises(ValueError):
            wrd.parse(broken)


if __name__ == '__main__':
    unittest.main()
