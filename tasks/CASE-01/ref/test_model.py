import unittest

from model import OUT_MAX, OUT_MIN, decode16, full_sum, ref


def enc(v):
    return v & 0xFFFF


def enc4(vals):
    return [enc(v) for v in vals]


class TestModel(unittest.TestCase):
    def test_decode(self):
        self.assertEqual(decode16(0x8000), -32768)
        self.assertEqual(decode16(0x7FFF), 32767)
        self.assertEqual(decode16(0xFFFF), -1)
        self.assertEqual(decode16(0), 0)

    def test_decode_rejects_non_16_bit(self):
        for bad in (-1, 0x10000, 1.0):
            with self.assertRaises(ValueError):
                decode16(bad)

    def test_needs_four_lanes(self):
        with self.assertRaises(ValueError):
            full_sum([0, 0, 0], [0, 0, 0])

    def test_full_range(self):  # spec 3.1: [-4294836224, 4294967296]
        m, x = enc(-32768), enc(32767)
        self.assertEqual(full_sum([m] * 4, [m] * 4), 4294967296)
        self.assertEqual(full_sum([m] * 4, [x] * 4), -4294836224)

    def test_spec_boundary_table(self):  # spec 3.3 item 2
        cases = [((-32768, -32768, -1, 0), (-32768, -32768, 1, 0), OUT_MAX),
                 ((-32768, -32768, 0, 0), (-32768, -32768, 0, 0), OUT_MAX + 1),
                 ((-32768, -32768, -32768, 0), (32767, 32767, 2, 0), OUT_MIN),
                 ((-32768, -32768, -32768, -1), (32767, 32767, 2, 1), OUT_MIN - 1)]
        for a, b, s in cases:
            self.assertEqual(full_sum(enc4(a), enc4(b)), s)

    def test_saturation_and_encoding(self):
        self.assertEqual(ref(enc4((-32768, -32768, -1, 0)), enc4((-32768, -32768, 1, 0))), 0x7FFFFFFF)
        self.assertEqual(ref(enc4((-32768, -32768, 0, 0)), enc4((-32768, -32768, 0, 0))), 0x7FFFFFFF)
        self.assertEqual(ref(enc4((-32768, -32768, -32768, 0)), enc4((32767, 32767, 2, 0))), 0x80000000)
        self.assertEqual(ref(enc4((-32768, -32768, -32768, -1)), enc4((32767, 32767, 2, 1))), 0x80000000)
        self.assertEqual(ref(enc4((3, 0, 0, 0)), enc4((-4, 0, 0, 0))), (-12) & 0xFFFFFFFF)
        self.assertEqual(ref(enc4((0, 0, 0, 0)), enc4((5, 6, 7, 8))), 0)


if __name__ == "__main__":
    unittest.main()
