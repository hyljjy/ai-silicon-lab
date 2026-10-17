"""Tests for replicate.py's pure parts (compare and query listing); the OpenSTA runs themselves are checked by the
end-to-end replication described in REPRODUCE.md."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate  # noqa: E402


class TestCompare(unittest.TestCase):
    def test_identical(self):
        self.assertEqual(replicate.compare_text("a\nb\n", "a\nb\n"), ("identical", None))

    def test_addresses_masked(self):
        new = "pin _0000561c2a3b4c50_p_Port x\n"
        old = "pin _00007f00aa11bb22_p_Port x\n"
        self.assertEqual(replicate.compare_text(new, old), ("identical-masked", None))

    def test_number_change_is_different(self):
        verdict, where = replicate.compare_text("slack -4.189726\n", "slack -4.189727\n")
        self.assertEqual(verdict, "different")
        self.assertEqual(where, (1, "slack -4.189726", "slack -4.189727"))

    def test_missing_line_is_different(self):
        verdict, where = replicate.compare_text("a\n", "a\nb\n")
        self.assertEqual(verdict, "different")
        self.assertEqual(where, (2, "<missing>", "b"))

    def test_mask_does_not_touch_plain_hex(self):
        self.assertEqual(replicate.mask("sha 1fa89c975162f4f1"), "sha 1fa89c975162f4f1")


class TestCommittedQueries(unittest.TestCase):
    def test_lists_dirs_with_recorded_mode(self):
        with tempfile.TemporaryDirectory() as d:
            for name, mode in (("base_B01_units", "query"), ("base_B02_x", "query")):
                q = os.path.join(d, "queries", "base", name)
                os.makedirs(q)
                with open(os.path.join(q, "result.json"), "w", encoding="utf-8") as f:
                    json.dump({"mode": mode}, f)
            with open(os.path.join(d, "queries", "base", "SHA256SUMS"), "w") as f:
                f.write("")
            got = replicate.committed_queries(["base"], diag=d)
        self.assertEqual([(g, n, r["mode"]) for g, n, _, r in got],
                         [("base", "base_B01_units", "query"), ("base", "base_B02_x", "query")])

    def test_real_repository_has_24_queries(self):
        got = replicate.committed_queries(["base", "recheck"])
        self.assertEqual(len(got), 24)
        self.assertTrue(all(os.path.isfile(q) for _, _, q, _ in got))


class TestToolDrift(unittest.TestCase):
    def test_only_tool_drift(self):
        log = "DRIFT: tool binaries differ from tools.sha256\nFAIL: live environment differs from the snapshot\n"
        self.assertTrue(replicate.only_tool_drift(log))

    def test_other_drift_not_accepted(self):
        log = ("DRIFT: liberty files differ from sky130hd_kit/MANIFEST.txt\n"
               "DRIFT: tool binaries differ from tools.sha256\nFAIL: live environment differs from the snapshot\n")
        self.assertFalse(replicate.only_tool_drift(log))

    def test_broken_snapshot_not_accepted(self):
        self.assertFalse(replicate.only_tool_drift("FAIL: snapshot files do not match SHA256SUMS\n"))


if __name__ == "__main__":
    unittest.main()
