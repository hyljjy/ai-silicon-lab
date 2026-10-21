"""Tests for baseline (the F1 baseline read from the archive originals; CASE-01 stage B, Task 1).
Run per module, never with discover. The real F1 evidence is only read; tamper tests work on temporary copies."""
import os
import shutil
import tempfile
import unittest

import baseline
import revpaths as rp

RUNS = os.path.join(rp.CASE, "runs")
EVIDENCE_F1 = os.path.join(rp.CASE, "evidence", "F1")
ARCH = "20261009-092827-base-T27.91"


class TestBaseline(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="baseline_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)

    def copy_tree(self, name):
        """Temporary copy of exactly the files baseline reads, in the layout of evidence/F1."""
        root = os.path.join(self.tmp.name, name)
        src = baseline.source()
        files = [src["sums"], src["verdict"], src["sta_results"], src["copy_verdict"], src["copy_sta_results"]]
        files += [p for kind in ("max", "min") for p in src["path_reports"][kind].values()]
        for f in files:
            dst = os.path.join(root, os.path.relpath(f, EVIDENCE_F1))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(f, dst)
        return root

    @staticmethod
    def flip(path):
        with open(path, "rb") as f:
            data = bytearray(f.read())
        data[len(data) // 2] ^= 0x01
        with open(path, "wb") as f:
            f.write(bytes(data))

    def test_source(self):
        src = baseline.source()
        arch = os.path.join(EVIDENCE_F1, "archive", ARCH)
        self.assertEqual(src["archive"], arch)
        self.assertEqual(src["verdict"], os.path.join(arch, "verdict.json"))
        self.assertEqual(src["sta_results"], os.path.join(arch, "sta", "sta_results.tsv"))
        self.assertEqual(src["sums"], os.path.join(EVIDENCE_F1, "archive", "SHA256SUMS"))
        self.assertEqual(src["copy_verdict"], os.path.join(EVIDENCE_F1, "f1_run_verdict.json"))
        self.assertEqual(src["copy_sta_results"], os.path.join(EVIDENCE_F1, "sta_results.tsv"))
        self.assertEqual(sorted(src["path_reports"]), ["max", "min"])
        for kind in ("max", "min"):
            self.assertEqual(len(src["path_reports"][kind]), 6)
            for corner, p in src["path_reports"][kind].items():
                self.assertEqual(p, os.path.join(arch, "sta", f"path_{kind}_{corner}.rpt"))
                self.assertTrue(os.path.isfile(p))

    def test_verify_ok(self):
        self.assertEqual(baseline.verify(), [])
        self.assertEqual(baseline.verify(root=self.copy_tree("ok")), [])

    def test_tampered_copy_rejected(self):
        for name in ("f1_run_verdict.json", "sta_results.tsv"):
            root = self.copy_tree(name)
            self.flip(os.path.join(root, name))
            probs = baseline.verify(root=root)
            self.assertEqual(len(probs), 1, probs)
            self.assertIn(name, probs[0])

    def test_tampered_archive_report_rejected(self):
        root = self.copy_tree("rpt")
        rpt = os.path.join(root, "archive", ARCH, "sta", "path_min_tt_025C_1v80.rpt")
        self.flip(rpt)
        probs = baseline.verify(root=root)
        self.assertTrue(probs)
        self.assertTrue(all("path_min_tt_025C_1v80.rpt" in p for p in probs), probs)
        os.remove(rpt)
        self.assertTrue(any("path_min_tt_025C_1v80.rpt" in p for p in baseline.verify(root=root)))
        # the archive verdict changed together with its copy: the copies agree, the SHA256SUMS entry does not
        root = self.copy_tree("both")
        self.flip(os.path.join(root, "archive", ARCH, "verdict.json"))
        self.flip(os.path.join(root, "f1_run_verdict.json"))
        probs = baseline.verify(root=root)
        self.assertEqual(len(probs), 1, probs)
        self.assertIn("verdict.json", probs[0])
        # an original without its SHA256SUMS entry is rejected
        root = self.copy_tree("sums")
        sums = os.path.join(root, "archive", "SHA256SUMS")
        with open(sums, "rb") as f:
            lines = f.read().split(b"\n")
        with open(sums, "wb") as f:
            f.write(b"\n".join(ln for ln in lines if not ln.endswith(f"./{ARCH}/verdict.json".encode())))
        probs = baseline.verify(root=root)
        self.assertEqual(len(probs), 1, probs)
        self.assertIn("verdict.json", probs[0])


if __name__ == "__main__":
    unittest.main()
