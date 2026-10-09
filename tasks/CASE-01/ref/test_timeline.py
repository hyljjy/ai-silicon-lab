import itertools
import unittest

from timeline import classify, expected_valid


def shift_model(rst, valid, L):
    """Independent pipeline model: L valid stages, sync reset clears all; O_(n+1) = last stage after R_n."""
    pipe = [False] * L
    outs = []
    for n in range(len(rst)):
        pipe = [False] * L if rst[n] else [bool(valid[n])] + pipe[:-1]
        outs.append(pipe[-1])
    return outs


class TestTimeline(unittest.TestCase):
    def test_exhaustive_against_shift_model(self):
        for L in (1, 2, 3):
            for bits in itertools.product((0, 1), repeat=12):
                rst, valid = list(bits[:6]), list(bits[6:])
                want = shift_model(rst, valid, L)
                got = [expected_valid(rst, valid, L, k) for k in range(1, 7)]
                self.assertEqual(got, want, (L, rst, valid))

    def test_classify_matches_observations(self):
        for L in (1, 2, 3):
            for bits in itertools.product((0, 1), repeat=12):
                rst, valid = list(bits[:6]), list(bits[6:])
                kinds = classify(rst, valid, L)
                delivered = {n for n, k in enumerate(kinds) if k == "delivered"}
                observed = {k - L for k in range(1, 7) if expected_valid(rst, valid, L, k)}
                self.assertEqual(delivered, observed, (L, rst, valid))

    def test_edge_cases(self):
        # L=1: O_(n+1).valid = valid[n] and not rst[n]
        self.assertTrue(expected_valid([0, 0], [1, 0], 1, 1))
        self.assertFalse(expected_valid([1, 0], [1, 0], 1, 1))
        # L=3: reset at R_(n+L-1) cancels; reset at R_(n+L) does not
        self.assertEqual(classify([0, 0, 1, 0], [1, 0, 0, 0], 3)[0], "cancelled")
        self.assertEqual(classify([0, 0, 0, 1], [1, 0, 0, 0], 3)[0], "delivered")
        self.assertEqual(classify([0, 0], [0, 1], 3)[1], "undelivered")


if __name__ == "__main__":
    unittest.main()
