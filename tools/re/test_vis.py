"""Independent fixtures for VIS bit order, scaling and range admission."""
import struct
import unittest

from vis import parse_vis, unpack_record


class VisTests(unittest.TestCase):
    def test_all_bit_positions_and_values(self):
        for channel in range(8):
            for value in range(64):
                expected = [0] * 8
                expected[channel] = value
                words = [sum(expected[k + i] << shift for i, shift in enumerate((18, 12, 6, 0)))
                         for k in (0, 4)]
                packed = b''.join(w.to_bytes(3, 'little') for w in words)
                self.assertEqual(unpack_record(packed), tuple(expected))
                result = parse_vis(struct.pack('<4I', 1, 1, 20, 30) + packed)
                self.assertEqual(result['normalized_channel_ranges'][channel], [value / 63] * 2)

    def test_float_variant_scaling(self):
        values = [-256, 0, 64, 128, 256, 512, 1024, -64]
        result = parse_vis(struct.pack('<4I8f', 0, 1, 0, 0, *values))
        self.assertEqual(result['normalized_channel_ranges'], [[v / 256] * 2 for v in values])

    def test_malformed_and_empty(self):
        for data in (b'', bytes(15), struct.pack('<4I', 1, 1, 0, 0),
                     struct.pack('<4I', 1, 0, 0, 0) + b'0',
                     struct.pack('<4I8f', 0, 1, 0, 0, float('nan'), *([0] * 7))):
            with self.assertRaises(ValueError):
                parse_vis(data)
        self.assertEqual(parse_vis(struct.pack('<4I', 1, 0, 0, 0))['normalized_channel_ranges'], [])


if __name__ == '__main__':
    unittest.main()
