import json
import os
import tempfile
import unittest

import coverage
import gen_vectors
from model import OUT_MAX, OUT_MIN, full_sum, ref


class TestGenVectors(unittest.TestCase):
    def run_gen(self, L, lmax=3, seed=1):
        out = tempfile.mkdtemp()
        rc = gen_vectors.main(["--L", str(L), "--lmax", str(lmax), "--seed", str(seed), "--out", out])
        with open(os.path.join(out, "manifest.json")) as f:
            manifest = json.load(f)
        with open(os.path.join(out, "vectors.txt")) as f:
            lines = f.read().splitlines()
        return rc, manifest, lines

    def test_coverage_ok_for_each_L(self):
        for L in (1, 2, 3):
            rc, m, lines = self.run_gen(L)
            self.assertEqual(rc, 0, m["coverage"]["failures"])
            self.assertEqual(m["drain"], 4)
            self.assertEqual(m["n_vectors"], len(lines))
            self.assertEqual(m["expected_checked"], m["coverage"]["counts"]["checked"])
            self.assertEqual(m["coverage"]["counts"]["undelivered"], 0)
            self.assertIn("rand_uniform", m["generated_by_tag"])
            self.assertIn("rand_extreme", m["scenario_params"])

    def test_cancel_positions_counted_separately(self):
        _, m1, _ = self.run_gen(1)
        self.assertIn("rst_cancel", m1["coverage"]["not_applicable"])
        self.assertEqual(m1["coverage"]["counts"]["cancelled"], 0)
        self.assertFalse(any(k.startswith("rst_cancel_m") for k in m1["coverage"]["counts"]))
        _, m3, _ = self.run_gen(3)
        self.assertGreater(m3["coverage"]["counts"]["rst_cancel_m1"], 0)
        self.assertGreater(m3["coverage"]["counts"]["rst_cancel_m2"], 0)

    def test_line_format_and_reference_values(self):
        _, _, lines = self.run_gen(1)
        for line in lines[:4]:
            self.assertTrue(line.startswith("1 0 "), "first 4 vectors hold reset (spec 2.4)")
        for line in lines:
            f = line.split()
            self.assertEqual(len(f), 12)
            a = [int(x, 16) for x in f[2:6]]
            b = [int(x, 16) for x in f[6:10]]
            self.assertEqual(int(f[10], 16), ref(a, b))

    def test_exact_and_far_boundaries_present(self):
        _, m, _ = self.run_gen(1)
        c = m["coverage"]["counts"]
        for k in ("sat_hi_exact", "sat_hi_over1", "sat_lo_exact", "sat_lo_over1", "sat_pos_far", "sat_neg_far",
                  "rst_single_in_traffic", "rst_multi_in_traffic", "rand_uniform_checked", "rand_extreme_checked"):
            self.assertGreater(c[k], 0, k)
        self.assertEqual(c["sign_bins"], 100)

    def test_deterministic_by_seed(self):
        _, m1, l1 = self.run_gen(2, seed=7)
        _, m2, l2 = self.run_gen(2, seed=7)
        _, m3, _ = self.run_gen(2, seed=8)
        self.assertEqual(l1, l2)
        self.assertEqual(m1["vectors_sha256"], m2["vectors_sha256"])
        self.assertNotEqual(m1["vectors_sha256"], m3["vectors_sha256"])

    def test_bad_L_rejected(self):
        out = tempfile.mkdtemp()
        self.assertEqual(gen_vectors.main(["--L", "3", "--lmax", "2", "--seed", "1", "--out", out]), 1)

    # --- negative probes from the P1 review: coverage must fail when a required scenario is removed ---
    def assert_fails(self, cyc, L, key):
        cov = coverage.compute(cyc, L, 4)
        self.assertFalse(cov["ok"], key)
        self.assertTrue(any(f.startswith(key) for f in cov["failures"]), (key, cov["failures"]))

    def test_missing_exact_saturation_fails(self):
        cyc = [c for c in gen_vectors.build(1, 1) if not c[4].startswith("sat_")]
        self.assert_fails(cyc, 1, "sat_hi_exact")

    def test_missing_rand_uniform_fails(self):
        self.assert_fails([c for c in gen_vectors.build(1, 1) if c[4] != "rand_uniform"], 1, "rand_uniform_checked")

    def test_missing_rand_extreme_fails(self):
        self.assert_fails([c for c in gen_vectors.build(1, 1) if c[4] != "rand_extreme"], 1, "rand_extreme_checked")

    def test_missing_cancel_position_m1_fails(self):
        cyc = [list(c) for c in gen_vectors.build(3, 1)]
        for j in range(4, len(cyc)):             # clear valid on the edge before every reset after POR
            if cyc[j][0]:
                cyc[j - 1][1] = 0
        self.assert_fails([tuple(c) for c in cyc], 3, "rst_cancel_m1")

    def test_missing_far_saturation_fails(self):
        cyc = [c for c in gen_vectors.build(1, 1)
               if not (c[1] and not OUT_MIN - 1 <= full_sum(c[2], c[3]) <= OUT_MAX + 1)]
        self.assert_fails(cyc, 1, "sat_pos_far")

    def test_long_power_on_reset_is_not_a_pulse(self):
        cyc = gen_vectors.build(1, 1)
        longer = [(1, 0, (0,) * 4, (0,) * 4, "por")] * 6 + cyc
        base = coverage.compute(cyc, 1, 4)["counts"]["rst_multi_in_traffic"]
        self.assertEqual(coverage.compute(longer, 1, 4)["counts"]["rst_multi_in_traffic"], base)


if __name__ == "__main__":
    unittest.main()
