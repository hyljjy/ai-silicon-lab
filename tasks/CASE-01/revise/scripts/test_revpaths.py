"""Tests for revpaths (CASE-01 stage B, Task 1). Run per module, never with discover."""
import json
import os
import sys
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

import limits
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
            binary = os.path.join(d, "binary.sha256")      # Git Bash sha256sum writes "<hash> *<path>"
            with open(binary, "w", encoding="utf-8", newline="\n") as f:
                f.write(f"{rp.sha256(os.path.join(rp.REPO, rels[0]))} *{rels[0]}\n")
                f.write(f"{rp.sha256(os.path.join(rp.REPO, rels[1]))}  {rels[1]}\n")
            self.assertEqual(rp.reused_problems(binary), [])
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

    def test_disk_measurement_kill_fail_is_distinguishable(self):
        def killfail(v):
            raise rp.MeasureKillFail("df left processes", [4242], False)
        probs = rp.disk_problems(free_bytes=killfail)
        self.assertEqual(len(probs), 2)
        self.assertTrue(all(p.startswith(rp.KILL_FAIL + ": ") for p in probs), probs)
        self.assertEqual(rp.kill_fail_problems(probs), probs)
        self.assertIn("4242", probs[0])

        def broken(v):
            raise OSError("cannot measure")
        self.assertEqual(rp.kill_fail_problems(rp.disk_problems(free_bytes=broken)), [])
        self.assertTrue(issubclass(rp.MeasureKillFail, OSError))   # callers catching OSError still see a failure

    def test_measure_free_wsl_cleanup_failure_raises_kill_fail(self):
        def res(**kw):
            base = dict(rc=0, timed_out=False, stdout_over=False, stderr_over=False, stdout=b"Avail\n99\n",
                        stderr=b"", stdout_bytes=9, stderr_bytes=0)
            base.update(kw)
            return limits.Limited(**base)
        with mock.patch.object(limits, "run_limited", return_value=res()):
            self.assertEqual(rp._measure_free("WSL /"), 99)
        for kw in ({"killed_pids_alive": [77]}, {"cleanup_unconfirmed": True}):
            with mock.patch.object(limits, "run_limited", return_value=res(**kw)):
                with self.assertRaises(rp.MeasureKillFail):
                    rp._measure_free("WSL /")
        for fields, kill in (({"killed_pids_alive": [5]}, True), ({"cleanup_unconfirmed": True}, True), ({}, False)):
            err = limits.SupervisionError("supervision failed", cause_type="OSError", **fields)
            with mock.patch.object(limits, "run_limited", side_effect=err):
                with self.assertRaises(OSError) as cm:
                    rp._measure_free("WSL /")
            self.assertEqual(isinstance(cm.exception, rp.MeasureKillFail), kill, fields)
        with mock.patch.object(limits, "run_limited", return_value=res(rc=1)):
            with self.assertRaises(OSError) as cm:
                rp._measure_free("WSL /")
        self.assertNotIsInstance(cm.exception, rp.MeasureKillFail)

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


class LoadDiagTests(unittest.TestCase):
    def diag_dir_entries(self):
        want = os.path.normcase(rp.DIAG_SCRIPTS)
        return [e for e in sys.path if os.path.normcase(os.path.abspath(e or ".")) == want]

    def test_alias_only_and_cached(self):
        vc = rp.load_diag("void_check")
        self.assertIs(vc, sys.modules["diag_void_check"])
        self.assertIs(rp.load_diag("void_check"), vc)
        self.assertTrue(callable(vc.parse_stream))
        self.assertNotIn("void_check", sys.modules)
        self.assertEqual(self.diag_dir_entries(), [])

    def test_missing_module(self):
        with self.assertRaises(rp.RevpathsError):
            rp.load_diag("no_such_module_xyz")

    def test_no_shadowing_after_importing_stage_b_users(self):
        import classify
        if os.name == "nt":
            import run_revise  # noqa: F401
        self.assertEqual(self.diag_dir_entries(), [])
        here = os.path.normcase(rp.HERE)
        for name in ("build_prompt", "build_package"):
            mod = __import__(name)
            self.assertEqual(os.path.normcase(os.path.dirname(os.path.abspath(mod.__file__))), here, name)
        self.assertIs(classify.void_check, sys.modules["diag_void_check"])
        for bare in ("void_check", "privacy_check", "diagpaths"):
            self.assertNotIn(bare, sys.modules)


if __name__ == "__main__":
    unittest.main()
