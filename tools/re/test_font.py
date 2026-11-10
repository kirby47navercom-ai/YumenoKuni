import struct
import unittest

from font import spft


class FontMetricsTest(unittest.TestCase):
    def example(self):
        data=bytearray(96)
        data[:4]=b'SpFt'
        struct.pack_into('<10I',data,4,6,64,1,92,2,60,44,52,0,76)
        data[48]=0b00000101  # U+0020,U+0022 share one32-character index group
        struct.pack_into('<I',data,56,0)
        struct.pack_into('<5B3b',data,60,0x34,0x52,0x16,12,20,-1,2,-3)
        struct.pack_into('<5B3b',data,68,1,0,0,10,11,0,1,2)
        struct.pack_into('<4I',data,76,92,92,92,92)
        data[92:]=b'T\0\0\0'
        return data

    def test_bit_group_rank_and_packed_xy(self):
        result=spft(self.example())
        self.assertEqual([g['codepoint'] for g in result['glyphs']],[32,34])
        self.assertEqual(result['glyphs'][0]['atlas_x'],0x234)
        self.assertEqual(result['glyphs'][0]['atlas_y'],0x165)
        self.assertEqual(result['glyphs'][0]['kerning_raw'],[-1,2,-3])

    def test_invalid_index_is_rejected(self):
        data=self.example();struct.pack_into('<I',data,56,2)
        with self.assertRaisesRegex(ValueError,'index'):
            spft(data)
