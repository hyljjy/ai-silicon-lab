"""Unit tests of calibrate.py (spec 5, P1 M6): search logic with a fake STA, source validation with a fake run.
No EDA tools are needed."""
import hashlib
import json
import os
import tempfile
import unittest

import calibrate

STD = calibrate.STD


def fake_sta(S, category):
    return {"valid": True, "worst_setup": {"slack": S, "corner": "ss_n40C_1v60", "category": category},
            "worst_hold": {"slack": 0.1, "corner": "ff_100C_1v95"},
            "corners": {c: {"ws_max": S, "ws_min": 0.1} for c in STD}}


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def make_run(T0, S0, category, impl=None):
    """A fake source run with frozen inputs; returns (run_root, verdict)."""
    root = tempfile.mkdtemp()
    files = {"rtl/dot4sat.v": "module dot4sat; endmodule\n", "scripts/synth_case01.tcl": "# recipe\n",
             "scripts/sta_run.tcl": "# sta\n", "scripts/check_sta.py": "# check\n", "sdc/case01_sdc.tcl": "# sdc\n",
             "config/warn_whitelist.txt": "# rules\n"}
    lines = []
    for rel, text in files.items():
        p = os.path.join(root, "inputs", rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(text)
        lines.append(f"{sha(p)}  {rel}\n")
    open(os.path.join(root, "inputs.sha256"), "w").writelines(lines)
    os.makedirs(os.path.join(root, "synth"))
    open(os.path.join(root, "synth", "netlist.v"), "w").write("// netlist\n")
    os.makedirs(os.path.join(root, "sta"))
    json.dump(fake_sta(S0, category), open(os.path.join(root, "sta", "sta_check.json"), "w"))
    verdict = {"functional_pass": True, "analysis_valid": True, "phase": "pre-F1", "sceneset": "std", "T_ns": T0,
               "C_load_pF": 0.0024, "netlist_sha256": sha(os.path.join(root, "synth", "netlist.v")),
               "impl": impl or {"name": "base", "top": "dot4sat", "rtl": "rtl/dot4sat.v", "L": "1"}}
    json.dump(verdict, open(os.path.join(root, "verdict.json"), "w"))
    return root, verdict


class TestSearch(unittest.TestCase):
    def run_search(self, slack_of_T, T0, category):
        root, verdict = make_run(T0, slack_of_T(T0), category)
        calls = []

        def sta(run_root, v, session, T, idx):
            calls.append(T)
            return calibrate.trial(T, fake_sta(slack_of_T(T), category), f"fake/{idx}", {})
        record = {"trials": []}
        calibrate.search(root, verdict, tempfile.mkdtemp(), record, lambda r: None, sta=sta)
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
        root, _ = make_run(20.0, -3.0, "in2reg")
        self.accept_hashes(root)
        self.assertEqual(calibrate.validate_source(root)["impl"]["name"], "base")

    def test_rejections(self):
        def wrong_impl(root):
            v = json.load(open(os.path.join(root, "verdict.json")))
            v["impl"]["name"] = "not_base"
            json.dump(v, open(os.path.join(root, "verdict.json"), "w"))

        def wrong_rtl_hash(root):
            calibrate.BASELINE_RTL_SHA = "0" * 64

        def modified_input(root):
            open(os.path.join(root, "inputs", "sdc", "case01_sdc.tcl"), "a").write("# edited\n")

        def netlist_changed(root):
            open(os.path.join(root, "synth", "netlist.v"), "a").write("// edited\n")

        def invalid_sta(root):
            s = fake_sta(-3.0, "in2reg")
            s["valid"] = False
            json.dump(s, open(os.path.join(root, "sta", "sta_check.json"), "w"))

        for fn in (wrong_impl, wrong_rtl_hash, modified_input, netlist_changed, invalid_sta):
            root, _ = make_run(20.0, -3.0, "in2reg")
            self.accept_hashes(root)
            fn(root)
            with self.assertRaises(calibrate.CalibError, msg=fn.__name__):
                calibrate.validate_source(root)


class TestMainGuard(unittest.TestCase):
    def test_refuses_after_f1(self):
        case = tempfile.mkdtemp()
        os.makedirs(os.path.join(case, "config"))
        open(os.path.join(case, "config", "f1.cfg"), "w").write("T_ns = 20\n")
        orig = calibrate.CASE
        calibrate.CASE = case
        try:
            self.assertEqual(calibrate.main(["--run", "runs/x"]), 1)
            self.assertFalse(os.path.exists(os.path.join(case, "runs")))
        finally:
            calibrate.CASE = orig


if __name__ == "__main__":
    unittest.main()
