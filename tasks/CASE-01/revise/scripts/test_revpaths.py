"""Tests for revpaths (CASE-01 stage B, Task 1). Run per module, never with discover."""
import json
import os
import tempfile
import unittest
from decimal import Decimal

import revpaths as rp

RUNS = os.path.join(rp.CASE, "runs")
GB = 1024 ** 3


def tmpdir():
    os.makedirs(RUNS, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="revpaths_", dir=RUNS)


class TestRevpaths(unittest.TestCase):
    def test_constants(self):
        self.assertTrue(os.path.isfile(os.path.join(rp.CASE, "config", "f1.cfg")))
        self.assertEqual(rp.REVISE, os.path.join(rp.CASE, "revise"))
        self.assertEqual(rp.RULES, os.path.join(rp.REVISE, "rules"))
        self.assertTrue(os.path.isdir(os.path.join(rp.REPO, ".git")))
        self.assertTrue(os.path.isfile(os.path.join(rp.DIAG_SCRIPTS, "wsl.sh")))
        want = r"D:\study\revise_sandbox" if os.name == "nt" else "/mnt/d/study/revise_sandbox"
        self.assertEqual(rp.SANDBOX, want)
        for name in ("PROMPTS", "PACKAGE", "OUTPUTS", "RESULTS", "PREDICTIONS"):
            self.assertEqual(os.path.dirname(getattr(rp, name)), rp.REVISE)

    def test_sha256(self):
        self.assertEqual(rp.sha256_bytes(b""), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        with tmpdir() as d:
            p = os.path.join(d, "a")
            with open(p, "wb") as f:
                f.write(b"abc")
            self.assertEqual(rp.sha256(p), rp.sha256_bytes(b"abc"))

    def test_fmt6_rounds_half_up(self):
        self.assertEqual(rp.fmt6(Decimal("11.3172215")), "11.317222")
        self.assertEqual(rp.fmt6(Decimal("-4.189726018044011")), "-4.189726")
        self.assertEqual(rp.fmt6(Decimal("-0.0000005")), "-0.000001")
        self.assertEqual(rp.fmt6(Decimal("2")), "2.000000")

    def test_load_json_decimal_keeps_digits(self):
        with tmpdir() as d:
            p = os.path.join(d, "v.json")
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write('{"slack": -4.189726018044011, "area": 1234.56789012345678, "n": 3}')
            v = rp.load_json_decimal(p)
        self.assertEqual(v["slack"], Decimal("-4.189726018044011"))
        self.assertEqual(str(v["area"]), "1234.56789012345678")
        self.assertIsInstance(v["slack"], Decimal)
        self.assertEqual(v["n"], 3)

    def test_write_new_or_same(self):
        with tmpdir() as d:
            p = os.path.join(d, "sub", "f.txt")
            self.assertTrue(rp.write_new_or_same(p, b"x\n"))
            self.assertFalse(rp.write_new_or_same(p, b"x\n"))
            with self.assertRaises(rp.RevpathsError):
                rp.write_new_or_same(p, b"y\n")
            with open(p, "rb") as f:
                self.assertEqual(f.read(), b"x\n")

    def test_reused_ok(self):
        rels = ["tasks/CASE-01/diag/scripts/wsl.sh", "tasks/CASE-01/diag/scripts/void_check.py"]
        with tmpdir() as d:
            good = os.path.join(d, "reused.sha256")
            with open(good, "w", encoding="utf-8", newline="\n") as f:
                for rel in rels:
                    f.write(f"{rp.sha256(os.path.join(rp.REPO, rel))}  {rel}\n")
            self.assertEqual(rp.reused_problems(good), [])
            bad = os.path.join(d, "bad.sha256")
            with open(bad, "w", encoding="utf-8", newline="\n") as f:
                f.write("0" * 64 + "  " + rels[0] + "\n")
                f.write(f"{'1' * 64}  tasks/CASE-01/diag/scripts/no_such_file.py\n")
            probs = rp.reused_problems(bad)
            self.assertEqual(len(probs), 2)
            self.assertIn(rels[0], probs[0])
            self.assertIn("no_such_file.py", probs[1])
            self.assertTrue(rp.reused_problems(os.path.join(d, "missing.sha256")))
            empty = os.path.join(d, "empty.sha256")
            open(empty, "w").close()
            self.assertTrue(rp.reused_problems(empty))
        self.assertEqual(rp.REUSED_SHA256, os.path.join(rp.RULES, "reused.sha256"))

    def test_disk_problems_threshold(self):
        vols = rp.DISK_VOLUMES
        self.assertEqual(len(vols), 2)
        low = {vols[0]: 19 * GB, vols[1]: 21 * GB}
        probs = rp.disk_problems(free_bytes=low)
        self.assertEqual(len(probs), 1)
        self.assertIn(vols[0], probs[0])
        self.assertIn(str(19 * GB), probs[0])
        self.assertRegex(probs[0], r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d")
        self.assertEqual(rp.disk_problems(free_bytes={vols[0]: 21 * GB, vols[1]: 21 * GB}), [])
        self.assertEqual(rp.disk_problems(free_bytes=lambda v: 21 * GB), [])

        def broken(v):
            raise OSError("cannot measure")
        probs = rp.disk_problems(free_bytes=broken)
        self.assertEqual(len(probs), 2)

    def test_directions(self):
        with tmpdir() as d:
            p = os.path.join(d, "metric_directions.json")
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                json.dump({"slack": {"better": "increase", "epsilon": "0.000001"},
                           "area": {"better": "decrease", "epsilon": "0.0001"},
                           "L": {"compare": "equal"}, "function": {"compare": "equal"}}, f)
            dirs = rp.directions(p)
            self.assertEqual(dirs["slack"]["epsilon"], Decimal("0.000001"))
            self.assertEqual(dirs["area"]["better"], "decrease")
            self.assertEqual(dirs["L"], {"compare": "equal"})
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                json.dump({"slack": {"better": "up", "epsilon": "0.1"}}, f)
            with self.assertRaises(rp.RevpathsError):
                rp.directions(p)
        self.assertEqual(rp.METRIC_DIRECTIONS, os.path.join(rp.RULES, "metric_directions.json"))

    def test_real_rules_files(self):
        # the committed rules files: reused.sha256 lists the six reused stage-A files and all match;
        # metric_directions.json holds the values of the implementation plan
        self.assertEqual(rp.reused_problems(), [])
        with open(rp.REUSED_SHA256, "rb") as f:
            raw = f.read()
        self.assertNotIn(b"\r", raw)
        rels = sorted(ln.split(None, 1)[1] for ln in raw.decode("utf-8").splitlines())
        want = sorted([f"tasks/CASE-01/diag/scripts/{n}" for n in
                       ("wsl.sh", "privacy_check.py", "diag_commit.sh", "void_check.py", "redact_settings.py")]
                      + ["tasks/CASE-01/diag/models/originals.sha256"])
        self.assertEqual(rels, want)
        self.assertEqual(rp.directions(), {"slack": {"better": "increase", "epsilon": Decimal("0.000001")},
                                           "area": {"better": "decrease", "epsilon": Decimal("0.0001")},
                                           "L": {"compare": "equal"}, "function": {"compare": "equal"}})


if __name__ == "__main__":
    unittest.main()
