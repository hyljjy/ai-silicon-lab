"""Unit tests of calibrate.py (spec 5, P1 M6): search logic with a fake STA, source validation with a fake run,
the wall-clock limit on subprocesses and the record left by an interrupt. No EDA tools are needed."""
import contextlib
import hashlib
import io
import json
import os
import tempfile
import time
import unittest

import calibrate

STD = calibrate.STD


def fake_sta(S, category):
    return {"valid": True, "worst_setup": {"slack": S, "corner": "ss_n40C_1v60", "category": category},
            "worst_hold": {"slack": 0.1, "corner": "ff_100C_1v95"},
            "corners": {c: {"ws_max": S, "ws_min": 0.1} for c in STD}}


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write(path, text, mode="w"):
    with open(path, mode) as f:
        f.write(text)


def dump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f)


def load(path):
    with open(path) as f:
        return json.load(f)


def tmpdir(test):
    """A temporary directory that is removed when the test finishes."""
    d = tempfile.TemporaryDirectory(prefix="calib_test_")
    test.addCleanup(d.cleanup)
    return d.name


def alive(pid):
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except FileNotFoundError:
        return False


def make_run(test, T0, S0, category, impl=None):
    """A fake source run with frozen inputs; returns (run_root, verdict)."""
    root = tmpdir(test)
    files = {"rtl/dot4sat.v": "module dot4sat; endmodule\n", "scripts/synth_case01.tcl": "# recipe\n",
             "scripts/sta_run.tcl": "# sta\n", "scripts/check_sta.py": "# check\n", "sdc/case01_sdc.tcl": "# sdc\n",
             "config/warn_whitelist.txt": "# rules\n"}
    lines = []
    for rel, text in files.items():
        p = os.path.join(root, "inputs", rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        write(p, text)
        lines.append(f"{sha(p)}  {rel}\n")
    write(os.path.join(root, "inputs.sha256"), "".join(lines))
    os.makedirs(os.path.join(root, "synth"))
    write(os.path.join(root, "synth", "netlist.v"), "// netlist\n")
    os.makedirs(os.path.join(root, "sta"))
    dump(fake_sta(S0, category), os.path.join(root, "sta", "sta_check.json"))
    verdict = {"functional_pass": True, "analysis_valid": True, "phase": "pre-F1", "sceneset": "std", "T_ns": T0,
               "C_load_pF": 0.0024, "netlist_sha256": sha(os.path.join(root, "synth", "netlist.v")),
               "impl": impl or {"name": "base", "top": "dot4sat", "rtl": "rtl/dot4sat.v", "L": "1"}}
    dump(verdict, os.path.join(root, "verdict.json"))
    return root, verdict


class TestSearch(unittest.TestCase):
    def run_search(self, slack_of_T, T0, category):
        root, verdict = make_run(self, T0, slack_of_T(T0), category)
        calls = []

        def sta(run_root, v, session, T, idx):
            calls.append(T)
            return calibrate.trial(T, fake_sta(slack_of_T(T), category), f"fake/{idx}", {})
        record = {"trials": []}
        calibrate.search(root, verdict, tmpdir(self), record, lambda r: None, sta=sta)
        return record, calls

    def test_formula_hits_in_one_trial(self):
        record, calls = self.run_search(lambda T: 0.8 * T - 19.0, 30.0, "in2reg")
        self.assertEqual(record["status"], "candidate_found")
        self.assertEqual(calls, [20.0])
        self.assertAlmostEqual(record["chosen"]["S_over_T"], -0.15, places=3)

    def test_bisection_midpoint_reached_and_succeeds(self):
        # S/T = (T - 25) / 2: the target window is only T in [24.6, 24.8], so the search must bracket and bisect
        record, calls = self.run_search(lambda T: T * (T - 25.0) / 2.0, 40.0, "reg2reg")
        self.assertFalse(record["formula_applicable"])
        self.assertEqual(record["status"], "candidate_found")
        self.assertTrue(-0.20 <= record["chosen"]["S_over_T"] <= -0.10)
        self.assertEqual(calls[:5], [36.0, 32.4, 29.16, 26.24, 23.62])        # x0.9 until too tight
        self.assertIn(round((23.62 + 26.24) / 2, 2), calls)                   # then a real midpoint
        self.assertLessEqual(len(calls), calibrate.MAX_TRIALS)

    def test_stall_raises(self):
        # ratio jumps from -0.25 to -0.05 at T = 20: no period satisfies the target
        with self.assertRaises(calibrate.CalibError):
            self.run_search(lambda T: (-0.25 if T < 20.0 else -0.05) * T, 30.0, "reg2reg")


class TestValidateSource(unittest.TestCase):
    def setUp(self):
        self._rtl, self._recipe = calibrate.BASELINE_RTL_SHA, calibrate.RECIPE_SHA

    def tearDown(self):
        calibrate.BASELINE_RTL_SHA, calibrate.RECIPE_SHA = self._rtl, self._recipe

    def accept_hashes(self, root):
        calibrate.BASELINE_RTL_SHA = sha(os.path.join(root, "inputs", "rtl", "dot4sat.v"))
        calibrate.RECIPE_SHA = sha(os.path.join(root, "inputs", "scripts", "synth_case01.tcl"))

    def test_good_source(self):
        root, _ = make_run(self, 20.0, -3.0, "in2reg")
        self.accept_hashes(root)
        self.assertEqual(calibrate.validate_source(root)["impl"]["name"], "base")

    def test_rejections(self):
        def wrong_impl(root):
            v = load(os.path.join(root, "verdict.json"))
            v["impl"]["name"] = "not_base"
            dump(v, os.path.join(root, "verdict.json"))

        def wrong_rtl_hash(root):
            calibrate.BASELINE_RTL_SHA = "0" * 64

        def modified_input(root):
            write(os.path.join(root, "inputs", "sdc", "case01_sdc.tcl"), "# edited\n", "a")

        def netlist_changed(root):
            write(os.path.join(root, "synth", "netlist.v"), "// edited\n", "a")

        def invalid_sta(root):
            s = fake_sta(-3.0, "in2reg")
            s["valid"] = False
            dump(s, os.path.join(root, "sta", "sta_check.json"))

        for fn in (wrong_impl, wrong_rtl_hash, modified_input, netlist_changed, invalid_sta):
            root, _ = make_run(self, 20.0, -3.0, "in2reg")
            self.accept_hashes(root)
            fn(root)
            with self.assertRaises(calibrate.CalibError, msg=fn.__name__):
                calibrate.validate_source(root)


class TestRunLimited(unittest.TestCase):
    def setUp(self):
        self.saved = dict(getattr(calibrate, "TIMEOUT_S", {}))
        calibrate.TIMEOUT_S = dict(self.saved, sta=2)

    def tearDown(self):
        calibrate.TIMEOUT_S = self.saved

    def test_hung_step_and_its_children_are_killed(self):
        d = tmpdir(self)
        pidfile = os.path.join(d, "child.pid")
        t0 = time.monotonic()
        with self.assertRaises(calibrate.CalibError) as cm:
            calibrate.run_limited("sta", ["bash", "-c", f"sleep 20 & echo $! > {pidfile}; wait"],
                                  os.path.join(d, "sta.log"))
        self.assertLess(time.monotonic() - t0, 10)
        self.assertIn("timed out", str(cm.exception))
        with open(pidfile) as f:
            pid = int(f.read())
        deadline = time.monotonic() + 5
        while alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertFalse(alive(pid))

    def test_normal_step_returns_its_exit_code(self):
        d = tmpdir(self)
        log = os.path.join(d, "x.log")
        self.assertEqual(calibrate.run_limited("sta", ["bash", "-c", "echo hi; exit 3"], log), 3)
        with open(log) as f:
            self.assertEqual(f.read(), "hi\n")


class TestMain(unittest.TestCase):
    def setUp(self):
        self.case = tmpdir(self)
        self.orig = (calibrate.CASE, getattr(calibrate, "run_limited", None))
        calibrate.CASE = self.case

    def tearDown(self):
        calibrate.CASE, calibrate.run_limited = self.orig

    def test_refuses_after_f1(self):
        os.makedirs(os.path.join(self.case, "config"))
        write(os.path.join(self.case, "config", "f1.cfg"), "T_ns = 20\n")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(calibrate.main(["--run", "runs/x"]), 1)
        self.assertIn("CALIBRATION FAIL: config/f1.cfg exists", out.getvalue())
        self.assertFalse(os.path.exists(os.path.join(self.case, "runs")))

    def test_interrupt_leaves_failed_record(self):
        def interrupted(*args, **kwargs):
            raise KeyboardInterrupt
        calibrate.run_limited = interrupted
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                calibrate.main(["--run", "runs/x"])
        sessions = os.listdir(os.path.join(self.case, "runs"))
        self.assertEqual(len(sessions), 1)
        record = load(os.path.join(self.case, "runs", sessions[0], "calib_record.json"))
        self.assertEqual(record["status"], "failed")
        self.assertIn("KeyboardInterrupt", record["error"])


if __name__ == "__main__":
    unittest.main()
