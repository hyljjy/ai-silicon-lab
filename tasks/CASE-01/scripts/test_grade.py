"""Unit tests for grade.py (task review of Task 9; final review before F1). Run inside WSL from tasks/CASE-01/scripts:
  python3 -B -m unittest -v test_grade
Step runner (timeout, interrupt, duration), implementation and path checks, F1 settings and freeze, RTL lint,
re-verification of the frozen inputs, verdict records, error paths and self-test provenance. Post-F1 behaviour is
tested only against a temporary CASE directory (grade.CASE is patched); the real tasks/CASE-01 is only read."""
import contextlib
import io
import json
import os
import platform
import shutil
import signal
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

import grade

REAL_CASE = grade.CASE          # read only: frozen inputs are copied from here into temporary CASE directories


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\n") as f:
        f.write(text)


def read(path):
    with open(path) as f:
        return f.read()


def load(path):
    with open(path) as f:
        return json.load(f)


class TempCase:
    """A throw-away repo with tasks/CASE-01 holding copies of the frozen inputs, the baseline RTL as rtl/t.v, the
    C_load evidence and config/impl.t.cfg; grade.CASE, grade.REPO and $SKY130_KIT point into it until the test ends.
    env/snapshot.sh exists (and exits 0) only with snapshot_ok=True, so most runs stop at the env_snapshot step."""

    def __init__(self, test, snapshot_ok=False):
        tmp = tempfile.TemporaryDirectory(prefix="grade_case_")
        test.addCleanup(tmp.cleanup)
        self.repo = tmp.name
        self.case = os.path.join(self.repo, "tasks", "CASE-01")
        for rel in grade.FROZEN_INPUTS + ["evidence/cload_extract.json", "tb/selftest/dot4sat_pipe.v"]:
            os.makedirs(os.path.dirname(os.path.join(self.case, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(REAL_CASE, rel), os.path.join(self.case, rel))
        write(self.path("rtl/t.v"), read(os.path.join(REAL_CASE, "rtl", "dot4sat.v")))
        self.impl()
        write(os.path.join(self.repo, "env", "SHA256SUMS"), "env sums\n")
        write(os.path.join(self.repo, "env", "tools.sha256"), "tool sums\n")
        if snapshot_ok:
            write(os.path.join(self.repo, "env", "snapshot.sh"), "exit 0\n")
        self.kit = os.path.join(self.repo, "kit")
        write(os.path.join(self.kit, "MANIFEST.txt"), "kit manifest\n")
        for p in (mock.patch.object(grade, "CASE", self.case), mock.patch.object(grade, "REPO", self.repo),
                  mock.patch.dict(os.environ, {"SKY130_KIT": self.kit})):
            p.start()
            test.addCleanup(p.stop)

    def path(self, rel):
        return os.path.join(self.case, rel)

    def impl(self, **over):
        kv = dict({"name": "t", "top": "dot4sat", "rtl": "rtl/t.v", "L": "1"}, **over)
        write(self.path("config/impl.t.cfg"), "".join(f"{k} = {v}\n" for k, v in kv.items() if v is not None))

    def runs(self):
        d = self.path("runs")
        return sorted(os.listdir(d)) if os.path.isdir(d) else []

    def run_root(self):
        runs = self.runs()
        assert len(runs) == 1, runs
        return self.path(os.path.join("runs", runs[0]))


def run_main(argv):
    """grade.main with stdout captured; returns (rc, stdout lines)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = grade.main(argv)
    return rc, out.getvalue().splitlines()


PRE_F1 = ["--impl", "config/impl.t.cfg", "--T", "20", "--cload", "0.0024"]


def alive(pid):
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except FileNotFoundError:
        return False


def alive_here(pid):
    """alive() that also works on Windows, for pids reported by the process itself."""
    if os.name == "nt":
        import subprocess
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out.split()
    return alive(pid)


class TestStepTimeout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="grade_timeout_")
        self.root = self.tmp.name
        self.saved = dict(getattr(grade, "STEP_TIMEOUT_S", {}))
        grade.STEP_TIMEOUT_S = dict(self.saved, rtl_sim=2)

    def tearDown(self):
        grade.STEP_TIMEOUT_S = self.saved
        self.tmp.cleanup()

    def test_hung_step_is_killed_and_recorded(self):
        run = grade.Run(self.root, [])
        t0 = time.monotonic()
        with self.assertRaises(grade.GradeError) as cm:
            run.cmd("rtl_sim", ["sleep", "20"], "rtl_sim/sim.log")
        self.assertLess(time.monotonic() - t0, 10)
        self.assertIn("timed out", str(cm.exception))
        self.assertEqual(run.steps[-1]["step"], "rtl_sim")
        self.assertTrue(run.steps[-1]["timed_out"])

    def test_hung_tree_is_killed_on_this_platform(self):
        # Portable twin of the next test (bash's $! is not a Windows pid). The children stop by themselves after
        # 20 s, so a broken kill cannot run away (PRJ-004, an unkillable `yes` on Windows).
        pidfile, sleeper, tree = (os.path.join(self.root, n) for n in ("g.pid", "sleeper.py", "tree.py"))
        with open(sleeper, "w") as f:
            f.write("import os, sys, time\nopen(sys.argv[1], 'w').write(str(os.getpid()))\ntime.sleep(20)\n")
        with open(tree, "w") as f:
            f.write("import subprocess, sys, time\nsubprocess.Popen([sys.executable, sys.argv[2], sys.argv[1]])\n"
                    "time.sleep(20)\n")
        grade.STEP_TIMEOUT_S = dict(grade.STEP_TIMEOUT_S, rtl_sim=4)
        run = grade.Run(self.root, [])
        with self.assertRaises(grade.GradeError):
            run.cmd("rtl_sim", [sys.executable, tree, pidfile, sleeper], "rtl_sim/sim.log")
        with open(pidfile) as f:
            pid = int(f.read())
        deadline = time.monotonic() + 5
        while alive_here(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertFalse(alive_here(pid))

    def test_child_processes_are_killed_too(self):
        pidfile = os.path.join(self.root, "child.pid")
        run = grade.Run(self.root, [])
        with self.assertRaises(grade.GradeError):
            run.cmd("rtl_sim", ["bash", "-c", f"sleep 20 & echo $! > {pidfile}; wait"], "rtl_sim/sim.log")
        with open(pidfile) as f:
            pid = int(f.read())
        deadline = time.monotonic() + 5
        while alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertFalse(alive(pid))

    def test_normal_step_unaffected(self):
        run = grade.Run(self.root, [])
        rc, text, problems = run.cmd("rtl_sim", ["echo", "SIM PASS checked=1"], "rtl_sim/sim.log")
        self.assertEqual((rc, problems), (0, []))
        self.assertIn("SIM PASS checked=1", text)
        self.assertFalse(run.steps[-1]["timed_out"])

    def test_step_records_wall_clock_seconds(self):                       # final review M5
        run = grade.Run(self.root, [])
        run.cmd("rtl_sim", ["sleep", "0.3"], "rtl_sim/sim.log")
        seconds = run.steps[-1]["seconds"]
        self.assertIsInstance(seconds, float)
        self.assertGreaterEqual(seconds, 0.3)
        self.assertLess(seconds, 5)
        self.assertEqual(seconds, round(seconds, 3))

    def test_interrupt_kills_the_step_and_its_children(self):             # final review M2
        pidfile = os.path.join(self.root, "child.pid")
        run = grade.Run(self.root, [])

        def on_alarm(signum, frame):
            raise KeyboardInterrupt

        old = signal.signal(signal.SIGALRM, on_alarm)
        try:
            signal.setitimer(signal.ITIMER_REAL, 1.0)
            with self.assertRaises(KeyboardInterrupt):
                run.cmd("rtl_sim", ["bash", "-c", f"sleep 20 & echo $! > {pidfile}; wait"], "rtl_sim/sim.log")
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)
        with open(pidfile) as f:
            pid = int(f.read())
        deadline = time.monotonic() + 5
        while alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertFalse(alive(pid))
        self.assertEqual(run.steps[-1]["step"], "rtl_sim")
        self.assertEqual(run.steps[-1]["interrupted"], "KeyboardInterrupt")


class TestImplChecks(unittest.TestCase):
    """Final review C1 (top is pinned) and M1 (no path traversal): rejected before any run dir exists."""

    def setUp(self):
        self.tc = TempCase(self)

    def assertRejected(self, text, argv=PRE_F1):
        rc, lines = run_main(argv)
        self.assertEqual(rc, 1)
        self.assertTrue(lines[-1].startswith("GRADE FAIL: "), lines)
        self.assertIn(text, lines[-1])
        self.assertEqual(self.tc.runs(), [])

    def test_top_must_be_dot4sat(self):
        self.tc.impl(top="wrap")
        self.assertRejected("top = 'wrap'")

    def test_rtl_must_be_a_normalized_path_under_rtl(self):
        outside = os.path.join(self.tc.repo, "X.v")
        write(outside, "module dot4sat; endmodule\n")
        for rtl in ("rtl/../../../X.v", "rtl/../rtl/t.v", "./rtl/t.v", "rtl//t.v", self.tc.path("rtl/t.v"),
                    "config/../rtl/t.v", "rtl/t.sv", "tb/tb_dot4sat.v", "ref/model.py", "rtl"):
            with self.subTest(rtl=rtl):
                self.tc.impl(rtl=rtl)
                self.assertRejected("must be a normalized relative path")

    def test_rtl_symlink_leaving_the_case_is_rejected(self):
        outside = os.path.join(self.tc.repo, "X.v")
        write(outside, "module dot4sat; endmodule\n")
        os.symlink(outside, self.tc.path("rtl/link.v"))
        self.tc.impl(rtl="rtl/link.v")
        self.assertRejected("outside tasks/CASE-01")

    def test_impl_cfg_outside_the_case_is_rejected_before_a_run_dir(self):
        cfg = os.path.join(self.tc.repo, "impl.x.cfg")
        shutil.copyfile(self.tc.path("config/impl.t.cfg"), cfg)
        self.assertRejected("outside tasks/CASE-01", ["--impl", cfg, "--T", "20", "--cload", "0.0024"])

    def test_fixture_rtl_still_accepted_before_f1(self):
        self.tc.impl(rtl="tb/selftest/dot4sat_pipe.v", L="2")
        rc, lines = run_main(PRE_F1)
        self.assertEqual(rc, 1)                                   # stops at env_snapshot, after freezing
        root = self.tc.run_root()
        self.assertIn("env_snapshot failed", load(os.path.join(root, "verdict.json"))["error"])
        self.assertIn("tb/selftest/dot4sat_pipe.v", read(os.path.join(root, "inputs.sha256")))


F1_GOOD = {"T_ns": "27.91", "C_load_pF": "0.0024", "L_max": "3", "area_cap": "56729.408",
           "timing_target": "setup_ge_0_std", "seed": "1",
           "calib_session": "runs/20261009-080227-calib-20261009-073842-base-T20"}


def args(**kw):
    return types.SimpleNamespace(**dict({"impl": "config/impl.t.cfg", "T": None, "cload": None, "lmax": None,
                                         "seed": None, "sceneset": "std"}, **kw))


class TestF1Settings(unittest.TestCase):
    """Final review I2: f1.cfg is validated, CLI overrides and changed evaluation files are refused after F1, and the
    synthesis recipe is checked by its hash in both phases. Uses a temporary CASE only."""

    def setUp(self):
        self.tc = TempCase(self)

    def write_f1(self, **over):
        kv = dict(F1_GOOD, **over)
        write(self.tc.path("config/f1.cfg"), "# test\n" + "".join(f"{k} = {v}\n" for k, v in kv.items()
                                                                     if v is not None))

    def write_f1_sha256(self, rels=None):
        rels = sorted(grade.FROZEN_INPUTS) if rels is None else rels
        write(self.tc.path("config/f1.sha256"),
              "".join(f"{grade.sha256(self.tc.path(r))}  {r}\n" for r in rels))

    def post_f1(self, **over):
        self.write_f1(**over)
        self.write_f1_sha256()

    def test_pre_f1_defaults_and_ranges(self):
        s = grade.settings(args(T=20.0, cload=0.0024))
        self.assertEqual((s["phase"], s["T"], s["cload"], s["lmax"], s["seed"]), ("pre-F1", 20.0, 0.0024, 3, 1))
        self.assertEqual((s["area_cap"], s["timing_rule"]), (None, None))
        self.assertEqual(grade.settings(args(T=20.0, cload=0.0024, seed=7, lmax=2))["seed"], 7)
        for lmax in (0, 4):
            with self.subTest(lmax=lmax), self.assertRaises(grade.GradeError):
                grade.settings(args(T=20.0, cload=0.0024, lmax=lmax))

    def test_valid_f1(self):
        self.post_f1(seed="5")
        s = grade.settings(args())
        self.assertEqual((s["phase"], s["T"], s["cload"], s["lmax"], s["seed"]), ("post-F1", 27.91, 0.0024, 3, 5))
        self.assertEqual((s["area_cap"], s["timing_rule"], s["calib_session"]),
                         (56729.408, "setup_ge_0_std", F1_GOOD["calib_session"]))
        self.post_f1(area_cap="unset")
        self.assertEqual(grade.settings(args())["area_cap"], "unset")

    def test_invalid_f1_values(self):
        bad = [("T_ns", "0"), ("T_ns", "-1"), ("T_ns", "nan"), ("T_ns", "inf"), ("T_ns", "abc"),
               ("C_load_pF", "0.003"), ("C_load_pF", "nan"), ("L_max", "0"), ("L_max", "4"), ("L_max", "2.5"),
               ("area_cap", "0"), ("area_cap", "-5"), ("area_cap", "inf"), ("area_cap", "none"),
               ("timing_target", "setup_ge_0"), ("seed", "1.5"), ("seed", "x"), ("calib_session", ""),
               ("T_ns", None), ("seed", None), ("timing_target", None), ("calib_session", None)]
        for key, value in bad:
            with self.subTest(key=key, value=value):
                self.post_f1(**{key: value})
                with self.assertRaises(grade.GradeError):
                    grade.settings(args())

    def test_unknown_key(self):
        self.post_f1(extra="1")
        with self.assertRaises(grade.GradeError) as cm:
            grade.settings(args())
        self.assertIn("extra", str(cm.exception))

    def test_cload_must_equal_the_extracted_value(self):
        self.post_f1()
        write(self.tc.path("evidence/cload_extract.json"), json.dumps({"value_pf": 0.0025}))
        with self.assertRaises(grade.GradeError) as cm:
            grade.settings(args())
        self.assertIn("cload_extract.json", str(cm.exception))

    def test_cli_values_refused_after_f1(self):
        self.post_f1()
        for kw in ({"T": 20.0}, {"cload": 0.0024}, {"lmax": 3}, {"seed": 1}):
            with self.subTest(**kw), self.assertRaises(grade.GradeError):
                grade.settings(args(**kw))

    def test_f1_sha256_must_exist_and_list_exactly_the_frozen_inputs(self):
        self.write_f1()
        with self.assertRaises(grade.GradeError):
            grade.settings(args())                                     # missing
        for rels in (sorted(grade.FROZEN_INPUTS)[1:], sorted(grade.FROZEN_INPUTS) + ["config/impl.t.cfg"],
                     sorted(grade.FROZEN_INPUTS) + sorted(grade.FROZEN_INPUTS)[:1]):
            with self.subTest(n=len(rels)):
                self.write_f1_sha256(rels)
                with self.assertRaises(grade.GradeError):
                    grade.settings(args())
        write(self.tc.path("config/f1.sha256"), "not a sha256sum line\n")
        with self.assertRaises(grade.GradeError):
            grade.settings(args())

    def test_evaluation_file_changed_after_f1(self):
        self.post_f1()
        with open(self.tc.path("scripts/check_sta.py"), "a") as f:
            f.write("# edited\n")
        with self.assertRaises(grade.GradeError) as cm:
            grade.settings(args())
        self.assertIn("evaluation file changed after F1: scripts/check_sta.py", str(cm.exception))
        self.assertIn("evaluation revision (spec 8)", str(cm.exception))

    def test_recipe_hash_checked_in_both_phases(self):
        with open(self.tc.path("scripts/synth_case01.tcl"), "a") as f:
            f.write("# edited\n")
        with self.assertRaises(grade.GradeError) as cm:
            grade.settings(args(T=20.0, cload=0.0024))
        self.assertIn("scripts/synth_case01.tcl", str(cm.exception))
        self.post_f1()                                     # F1 list taken over the edited recipe: still refused
        with self.assertRaises(grade.GradeError) as cm:
            grade.settings(args())
        self.assertIn(grade.RECIPE_SHA, str(cm.exception))

    def test_post_f1_errors_leave_no_run_dir(self):
        self.post_f1(L_max="4")
        rc, lines = run_main(["--impl", "config/impl.t.cfg"])
        self.assertEqual(rc, 1)
        self.assertTrue(lines[-1].startswith("GRADE FAIL: "))
        self.assertEqual(self.tc.runs(), [])
        self.post_f1()
        rc, lines = run_main(["--impl", "config/impl.t.cfg", "--seed", "1"])
        self.assertEqual((rc, self.tc.runs()), (1, []))
        self.assertIn("--seed", lines[-1])

    def test_post_f1_rejects_fixture_rtl(self):
        self.post_f1()
        self.tc.impl(rtl="tb/selftest/dot4sat_pipe.v", L="2")
        rc, lines = run_main(["--impl", "config/impl.t.cfg"])
        self.assertEqual((rc, self.tc.runs()), (1, []))
        self.assertIn("must be a normalized relative path rtl/<file>.v", lines[-1])

    def test_post_f1_run_freezes_both_f1_files_and_uses_the_frozen_seed(self):
        self.post_f1(seed="5")
        rc, lines = run_main(["--impl", "config/impl.t.cfg"])
        self.assertEqual(rc, 1)                                           # stops at env_snapshot
        root = self.tc.run_root()
        listed = dict(reversed(line.split()) for line in read(os.path.join(root, "inputs.sha256")).splitlines())
        self.assertIn("config/f1.cfg", listed)
        self.assertIn("config/f1.sha256", listed)
        self.assertEqual(len(listed), len(grade.FROZEN_INPUTS) + 4)
        v = load(os.path.join(root, "verdict.json"))
        self.assertEqual((v["phase"], v["T_ns"], v["L_max"], v["seed"]), ("post-F1", 27.91, 3, 5))
        self.assertEqual(v["calib_session"], F1_GOOD["calib_session"])
        self.assertEqual((v["timing_target"]["rule"], v["timing_target"]["met"]), ("setup_ge_0_std", None))
        self.assertEqual(v["area"], {"area_um2": None, "cap_um2": 56729.408, "within_cap": None})


PRE = {"phase": "pre-F1", "area_cap": None, "timing_rule": None}
POST = {"phase": "post-F1", "area_cap": 56729.408, "timing_rule": "setup_ge_0_std"}


def sta_result(std_ws, extra=None):
    corners = {c: {"ws_max": w, "ws_min": 0.1, "categories": {}} for c, w in zip(grade.STD, std_ws)}
    corners.update(extra or {})
    return {"corners": corners}


class TestTargets(unittest.TestCase):
    """Final review I3: the third verdict state (timing target) and the area cap are recorded, not failures."""

    def test_pre_f1_has_no_target_and_no_cap(self):
        self.assertEqual(grade.timing_target(PRE, sta_result([1] * 6)),
                         {"rule": None, "met": None, "note": "pre-F1: no frozen target"})
        self.assertEqual(grade.area_record(PRE, 45383.5264),
                         {"area_um2": 45383.5264, "cap_um2": None, "within_cap": None,
                          "note": "pre-F1: no frozen cap"})

    def test_setup_ge_0_std(self):
        self.assertEqual(grade.timing_target(POST, sta_result([1, 2, -0.5, 3, 4, 5])),
                         {"rule": "setup_ge_0_std", "met": False, "worst_setup_std": -0.5})
        self.assertEqual(grade.timing_target(POST, sta_result([0.0, 2, 1, 3, 4, 5])),
                         {"rule": "setup_ge_0_std", "met": True, "worst_setup_std": 0.0})

    def test_only_the_six_std_corners_count(self):            # --sceneset all adds the sweep corners
        sta = sta_result([1] * 6, {"ss_n40C_1v40": {"ws_max": -9.0, "ws_min": 0.0, "categories": {}}})
        self.assertEqual(grade.timing_target(POST, sta)["worst_setup_std"], 1)
        self.assertTrue(grade.timing_target(POST, sta)["met"])

    def test_no_valid_analysis_means_not_evaluated(self):
        t = grade.timing_target(POST, None)
        self.assertEqual((t["rule"], t["met"], t["worst_setup_std"]), ("setup_ge_0_std", None, None))

    def test_area_cap(self):
        self.assertEqual(grade.area_record(POST, 45383.5264),
                         {"area_um2": 45383.5264, "cap_um2": 56729.408, "within_cap": True})
        self.assertTrue(grade.area_record(POST, 56729.408)["within_cap"])
        self.assertFalse(grade.area_record(POST, 56729.409)["within_cap"])
        self.assertEqual(grade.area_record(dict(POST, area_cap="unset"), 1.0),
                         {"area_um2": 1.0, "cap_um2": "unset", "within_cap": None})
        self.assertEqual(grade.area_record(POST, None)["within_cap"], None)

    def test_grade_ok_line(self):
        v = {"run_id": "r1", "worst_setup": {"slack": -4.19}, "worst_hold": {"slack": 0.07}, "area_um2": 45383.5264,
             "timing_target": grade.timing_target(POST, sta_result([-4.19] + [1] * 5)),
             "area": grade.area_record(POST, 45383.5264)}
        line = grade.ok_line(v)
        self.assertNotIn("\n", line)
        self.assertTrue(line.startswith("GRADE OK: r1 functional_pass analysis_valid worst_setup="))
        self.assertTrue(line.endswith(" timing_target=setup_ge_0_std:not_met area_cap=56729.408:within"), line)
        v["area"] = grade.area_record(dict(POST, area_cap="unset"), 45383.5264)
        self.assertTrue(grade.ok_line(v).endswith(" area_cap=unset"))
        v.update(timing_target=grade.timing_target(PRE, None), area=grade.area_record(PRE, 1.0))
        self.assertTrue(grade.ok_line(v).endswith(" timing_target=n/a(pre-F1) area_cap=n/a(pre-F1)"))


def sigterm_guard(signum, frame):
    raise RuntimeError("SIGTERM reached the test's guard handler: grade.main installed no handler")


class TestErrorPaths(unittest.TestCase):
    """Final review M2: verdict.json and steps.json are always written, the last stdout line is always a single
    GRADE line, and interrupts (Ctrl-C, SIGTERM) are recorded and then propagate."""

    def setUp(self):
        self.tc = TempCase(self)
        previous = signal.signal(signal.SIGTERM, sigterm_guard)     # never let a SIGTERM kill the test runner
        self.addCleanup(signal.signal, signal.SIGTERM, previous)

    def verdict(self):
        return load(os.path.join(self.tc.run_root(), "verdict.json"))

    def interrupted_main(self, side_effect, exc):
        out = io.StringIO()
        with mock.patch.object(grade.logcheck, "load_rules", side_effect=side_effect), \
                contextlib.redirect_stdout(out), self.assertRaises(exc) as cm:
            grade.main(PRE_F1)
        return cm.exception, out.getvalue().splitlines()

    def test_bad_whitelist_still_writes_steps_and_verdict(self):
        write(self.tc.path("config/warn_whitelist.txt"), "yosys\tonly two fields\n")
        rc, lines = run_main(PRE_F1)
        self.assertEqual(rc, 1)
        self.assertTrue(lines[-1].startswith("GRADE FAIL: RuleError: "), lines)
        self.assertEqual(load(os.path.join(self.tc.run_root(), "steps.json")), [])
        self.assertTrue(self.verdict()["error"].startswith("RuleError: "))

    def test_unexpected_exception_is_a_grade_fail(self):
        with mock.patch.object(grade.logcheck, "load_rules", side_effect=RuntimeError("boom")):
            rc, lines = run_main(PRE_F1)
        self.assertEqual((rc, lines[-1]), (1, "GRADE FAIL: RuntimeError: boom"))
        self.assertEqual(self.verdict()["error"], "RuntimeError: boom")
        self.assertTrue(os.path.exists(os.path.join(self.tc.run_root(), "steps.json")))

    def test_keyboard_interrupt_is_recorded_and_propagates(self):
        _, lines = self.interrupted_main(KeyboardInterrupt, KeyboardInterrupt)
        self.assertEqual(lines[-1], "GRADE FAIL: interrupted: KeyboardInterrupt")
        self.assertEqual(self.verdict()["error"], "interrupted: KeyboardInterrupt")
        self.assertTrue(os.path.exists(os.path.join(self.tc.run_root(), "steps.json")))

    def test_sigterm_takes_the_same_path(self):
        def term(*args, **kwargs):
            os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(5)

        exc, lines = self.interrupted_main(term, SystemExit)
        self.assertEqual(exc.code, 143)
        self.assertEqual(lines[-1], "GRADE FAIL: interrupted: SystemExit")
        self.assertEqual(self.verdict()["error"], "interrupted: SystemExit")
        self.assertIs(signal.getsignal(signal.SIGTERM), sigterm_guard)          # the previous handler is back

    def test_multi_line_error_is_one_stdout_line(self):
        rc, lines = run_main(PRE_F1)          # no env/snapshot.sh: "env_snapshot failed (...):\n<log tail>"
        self.assertEqual(rc, 1)
        self.assertIn("\n", self.verdict()["error"])
        self.assertEqual(len(lines), 2, lines)
        self.assertTrue(lines[0].startswith("RUN_ID="))
        self.assertTrue(lines[-1].startswith("GRADE FAIL: GradeError: env_snapshot failed (exit 127"), lines)
        self.assertIn(" | bash: ", lines[-1])

    def test_bad_command_line_still_ends_with_a_grade_line(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            grade.main(["--impl", "config/impl.t.cfg", "--T", "abc"])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("invalid float value", err.getvalue())
        self.assertTrue(out.getvalue().splitlines()[-1].startswith("GRADE FAIL: "), out.getvalue())


class TestToolIdentity(unittest.TestCase):
    """Final review M3: the versions step fails when a tool is missing or broken and reports the Python that runs
    the grader (sys.executable), not python3 from PATH; verdict.json records env_ids."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="grade_tools_")
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        self.bin = os.path.join(self.root, "bin")
        os.makedirs(self.bin)
        os.symlink(shutil.which("bash"), os.path.join(self.bin, "bash"))
        self.fake("iverilog", 'echo "Icarus Verilog version fake"; echo "second line"')
        self.fake("yosys", 'echo "Yosys fake"')
        self.fake("sta", "echo 9.9.9")
        self.fake("python3", 'echo "Python 0.0-from-PATH"')

    def fake(self, name, body):
        write(os.path.join(self.bin, name), "#!/bin/bash\n" + body + "\n")
        os.chmod(os.path.join(self.bin, name), 0o755)

    def versions(self):
        with mock.patch.dict(os.environ, {"PATH": self.bin}):
            return grade.Run(self.root, []).require("versions", grade.versions_argv(), "versions.log")

    def test_reports_each_tool_and_this_python(self):
        self.assertEqual(self.versions().splitlines(), ["Icarus Verilog version fake", "Yosys fake", "OpenSTA 9.9.9",
                                                        f"Python {platform.python_version()}"])

    def test_missing_tool_fails_the_step(self):
        for tool in ("iverilog", "yosys", "sta"):
            with self.subTest(tool=tool):
                os.rename(os.path.join(self.bin, tool), os.path.join(self.root, tool))
                try:
                    with self.assertRaises(grade.GradeError) as cm:
                        self.versions()
                    self.assertIn("versions failed", str(cm.exception))
                finally:
                    os.rename(os.path.join(self.root, tool), os.path.join(self.bin, tool))

    def test_failing_tool_fails_the_step(self):
        self.fake("sta", "exit 1")
        with self.assertRaises(grade.GradeError):
            self.versions()

    def test_env_ids(self):
        tc = TempCase(self)
        self.assertEqual(grade.env_ids(), {
            "env/SHA256SUMS": grade.sha256(os.path.join(tc.repo, "env", "SHA256SUMS")),
            "env/tools.sha256": grade.sha256(os.path.join(tc.repo, "env", "tools.sha256")),
            "$SKY130_KIT/MANIFEST.txt": grade.sha256(os.path.join(tc.kit, "MANIFEST.txt"))})
        os.remove(os.path.join(tc.repo, "env", "tools.sha256"))
        with self.assertRaises(OSError):
            grade.env_ids()

    def test_run_records_env_ids_and_tool_versions(self):
        tc = TempCase(self, snapshot_ok=True)
        write(tc.path("ref/gen_vectors.py"), "import sys\nsys.exit(3)\n")      # stop right after versions
        rc, _ = run_main(PRE_F1)
        self.assertEqual(rc, 1)
        v = load(os.path.join(tc.run_root(), "verdict.json"))
        self.assertIn("gen_vectors failed", v["error"])
        self.assertEqual(v["env_ids"], grade.env_ids())
        self.assertEqual(len(v["tool_versions"]), 4)
        self.assertEqual(v["tool_versions"][-1], f"Python {platform.python_version()}")


class TestSelftestProvenance(unittest.TestCase):
    """Final review I5: selftest.json records iverilog, Python and the sha256 of every file the self-test used."""

    def test_records_tools_and_every_used_file(self):
        import selftest
        tmp = tempfile.TemporaryDirectory(prefix="selftest_prov_")
        self.addCleanup(tmp.cleanup)
        generated = [os.path.join(tmp.name, "vec_L1", "vectors.txt"), os.path.join(tmp.name, "vec_L1", "manifest.json"),
                     os.path.join(tmp.name, "vec_split_line.txt")]
        for i, path in enumerate(generated):
            write(path, f"generated {i}\n")
        p = selftest.provenance(3, generated)
        self.assertTrue(p["iverilog"].startswith("Icarus Verilog version "), p["iverilog"])
        self.assertEqual(p["python"], sys.version)
        used = {"tb/tb_dot4sat.v", "rtl/dot4sat.v", "tb/selftest/dot4sat_mut_num.v", "tb/selftest/dot4sat_mut_valid.v",
                "tb/selftest/dot4sat_mut_xdata.v", "tb/selftest/dot4sat_pipe.v", "scripts/selftest.py",
                "scripts/check_sim.py", "ref/gen_vectors.py", "ref/model.py", "ref/timeline.py", "ref/coverage.py"}
        used |= {os.path.relpath(g, selftest.CASE) for g in generated}
        self.assertEqual(set(p["sha256"]), used)
        for rel, digest in p["sha256"].items():
            self.assertEqual(digest, grade.sha256(os.path.join(selftest.CASE, rel)), rel)
        self.assertNotIn("tb/selftest/dot4sat_pipe.v", selftest.provenance(1, [])["sha256"])   # not used at L_max 1


LINT_REQUIRED = ["$fopen", "$fclose", "$fwrite", "$fdisplay", "$fstrobe", "$fmonitor", "$fputc", "$fflush", "$fscanf",
                 "$fgets", "$fgetc", "$fread", "$feof", "$readmemh", "$readmemb", "$writememh", "$writememb",
                 "$value$plusargs", "$test$plusargs", "$system", "$dumpfile", "$dumpvars"]


class TestRtlLint(unittest.TestCase):
    """Final review I1.1: candidate RTL must not touch files, read plusargs or include other files."""

    def test_existing_designs_are_clean(self):
        for rel in ("rtl/dot4sat.v", "tb/selftest/dot4sat_pipe.v", "tb/selftest/dot4sat_mut_num.v",
                    "tb/selftest/dot4sat_mut_valid.v", "tb/selftest/dot4sat_mut_xdata.v"):
            with self.subTest(rel=rel):
                self.assertEqual(grade.lint_rtl(read(os.path.join(REAL_CASE, rel))), [])

    def test_forbidden_system_tasks_and_functions(self):
        for name in LINT_REQUIRED + ["$fwriteh", "$fdisplayb", "$fstrobeo", "$fmonitorh", "$fseek", "$dumpall"]:
            with self.subTest(name=name):
                hits = grade.lint_rtl(f"module m;\ninitial begin\n  x = {name}(a, b);\nend\nendmodule\n")
                self.assertEqual(hits, [f"line 3: {name}"])

    def test_include_and_macro_token_pasting(self):
        self.assertEqual(grade.lint_rtl('`include "x.vh"\nmodule m; endmodule\n'), ["line 1: `include"])
        self.assertEqual(grade.lint_rtl("`define P(a) $f``a\nmodule m; endmodule\n"),
                         ["line 1: `` (macro token pasting)"])

    def test_comments_and_string_contents_are_ignored(self):
        text = ('// $fopen and `include in a line comment\n/* $readmemh\n   $system */\n'
                'module m; initial $display("$fopen // $fclose"); wire [3:0] s = $signed(x); endmodule\n')
        self.assertEqual(grade.lint_rtl(text), [])

    def test_comment_marker_inside_a_string_does_not_hide_code(self):
        self.assertEqual(grade.lint_rtl('initial begin $display("//"); fd = $fopen("a", "w"); end\n'),
                         ["line 1: $fopen"])
        self.assertEqual(grade.lint_rtl('initial $display("/*");\ninitial fd = $fopen("a"); // */\n'),
                         ["line 2: $fopen"])

    def test_similar_names_are_not_flagged(self):
        self.assertEqual(grade.lint_rtl("x = $signed(a); $display(b); $finish; my$fopen; $fopenx; f_fopen;\n"), [])


class TestVerifyFrozen(unittest.TestCase):
    """Final review I1.3: changed, missing or extra files under inputs/, a rewritten inputs.sha256, and changed
    vectors or manifest are all caught."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="grade_verify_")
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        self.frozen = {}
        for rel in ("a/x.txt", "a/b/y.txt", "z.txt"):
            write(self.p("inputs", rel), rel)
            self.frozen[rel] = grade.sha256(self.p("inputs", rel))
        write(self.p("inputs.sha256"), "".join(f"{d}  {r}\n" for r, d in self.frozen.items()))
        write(self.p("vectors/vectors.txt"), "0 1 ...\n")
        write(self.p("vectors/manifest.json"), "{}\n")
        self.others = {r: grade.sha256(self.p(r)) for r in ("inputs.sha256", "vectors/vectors.txt",
                                                           "vectors/manifest.json")}

    def p(self, *rel):
        return os.path.join(self.root, *rel)

    def assertCaught(self, text):
        with self.assertRaises(grade.GradeError) as cm:
            grade.verify_frozen(self.root, self.frozen, self.others, "rtl_sim")
        self.assertIn("after rtl_sim", str(cm.exception))
        self.assertIn(text, str(cm.exception))

    def test_unchanged(self):
        grade.verify_frozen(self.root, self.frozen, self.others, "rtl_sim")

    def test_changed_file(self):
        write(self.p("inputs", "a/b/y.txt"), "edited")
        self.assertCaught("changed inputs/a/b/y.txt")

    def test_missing_file(self):
        os.remove(self.p("inputs", "z.txt"))
        self.assertCaught("missing inputs/z.txt")

    def test_extra_file(self):
        write(self.p("inputs", "a/planted.py"), "x")
        self.assertCaught("extra inputs/a/planted.py")

    def test_extra_directory(self):
        os.makedirs(self.p("inputs", "a", "__pycache__"))
        self.assertCaught("extra inputs/a/__pycache__/")

    def test_rewriting_inputs_sha256_does_not_help(self):
        write(self.p("inputs", "z.txt"), "edited")
        forged = dict(self.frozen, **{"z.txt": grade.sha256(self.p("inputs", "z.txt"))})
        write(self.p("inputs.sha256"), "".join(f"{d}  {r}\n" for r, d in forged.items()))
        self.assertCaught("changed inputs/z.txt")
        self.assertCaught("changed inputs.sha256")

    def test_vectors_and_manifest(self):
        write(self.p("vectors/vectors.txt"), "0 0 ...\n")
        self.assertCaught("changed vectors/vectors.txt")
        write(self.p("vectors/vectors.txt"), "0 1 ...\n")
        write(self.p("vectors/manifest.json"), '{"n_vectors": 1}\n')
        self.assertCaught("changed vectors/manifest.json")


TAMPER = """  integer planted_fd;
  initial begin
    planted_fd = $fopen("inputs/ref/planted.py", "w");
    $fdisplay(planted_fd, "x = 1");
    $fclose(planted_fd);
  end
endmodule
"""


class TestFrozenInputsInARun(unittest.TestCase):
    """Final review I1 end to end in a temporary CASE: the lint stops a candidate before any step, the frozen files
    are read-only, and a candidate that writes into inputs/ during rtl_sim is caught right after that step."""

    def setUp(self):
        self.tc = TempCase(self, snapshot_ok=True)
        base = read(self.tc.path("rtl/t.v"))
        write(self.tc.path("rtl/t.v"), base.rsplit("endmodule", 1)[0] + TAMPER)

    def test_lint_stops_the_candidate_before_any_step(self):
        rc, lines = run_main(PRE_F1)
        self.assertEqual(rc, 1)
        self.assertIn("RTL lint", lines[-1])
        self.assertIn("$fopen", lines[-1])
        root = self.tc.run_root()
        self.assertEqual(load(os.path.join(root, "steps.json")), [])
        v = load(os.path.join(root, "verdict.json"))
        self.assertEqual([h.split(": ")[1] for h in v["rtl_lint"]], ["$fopen", "$fdisplay", "$fclose"])
        for line in read(os.path.join(root, "inputs.sha256")).splitlines():
            rel = line.split(None, 1)[1]
            with self.subTest(rel=rel):
                self.assertEqual(os.stat(os.path.join(root, "inputs", rel)).st_mode & 0o222, 0)

    def test_writing_into_inputs_during_rtl_sim_is_caught(self):
        with mock.patch.object(grade, "lint_rtl", return_value=[]):
            rc, lines = run_main(PRE_F1)
        self.assertEqual(rc, 1)
        root = self.tc.run_root()
        self.assertTrue(os.path.exists(os.path.join(root, "inputs", "ref", "planted.py")))   # the attack happened
        error = load(os.path.join(root, "verdict.json"))["error"]
        self.assertIn("frozen inputs changed after rtl_sim", error)
        self.assertIn("extra inputs/ref/planted.py", error)
        steps = [s["step"] for s in load(os.path.join(root, "steps.json"))]
        self.assertEqual(steps[-1], "rtl_sim")
        self.assertNotIn("synth", steps)


STA_DRIFT_LOG = ("opensta/bin/sta: FAILED\nsha256sum: WARNING: 1 computed checksum did NOT match\n"
                 "DRIFT: tool binaries differ from tools.sha256\nFAIL: live environment differs from the snapshot\n")


class TestToolDrift(unittest.TestCase):
    """spec v1.4: --allow-tool-drift accepts env/snapshot.sh check failing only on the OpenSTA fingerprint; every
    other drift still fails, and without the flag nothing changes."""

    def test_only_the_opensta_fingerprint_is_accepted(self):
        self.assertEqual(grade.tool_drift_only(STA_DRIFT_LOG), ["opensta/bin/sta"])
        rejected = {
            "release tool": STA_DRIFT_LOG.replace("opensta/bin/sta", "oss-cad-suite/libexec/yosys"),
            "extra binary": "oss-cad-suite/libexec/vvp: FAILED\n" + STA_DRIFT_LOG,
            "unreadable": STA_DRIFT_LOG.replace("FAILED\n", "FAILED open or read\n", 1),
            "kit script": "DRIFT: sky130hd_kit/synth.tcl differs from ~/pdk/sky130hd_kit/synth.tcl\n" + STA_DRIFT_LOG,
            "liberty": STA_DRIFT_LOG.replace("FAIL:", "DRIFT: liberty files differ from sky130hd_kit/MANIFEST.txt\nFAIL:"),
            "snapshot files": "FAIL: snapshot files do not match SHA256SUMS\n",
            "no drift line": "opensta/bin/sta: FAILED\nFAIL: live environment differs from the snapshot\n",
            "empty": "",
        }
        for name, log in rejected.items():
            with self.subTest(name=name):
                self.assertIsNone(grade.tool_drift_only(log))

    def drift_case(self, log):
        tc = TempCase(self)
        write(os.path.join(tc.repo, "env", "snapshot.sh"), f"printf '%s' '{log}'\nexit 1\n")
        home = os.path.join(tc.repo, "home")
        write(os.path.join(home, "tools", "opensta", "bin", "sta"), "another build\n")
        p = mock.patch.dict(os.environ, {"HOME": home, "USERPROFILE": home})
        p.start()
        self.addCleanup(p.stop)
        write(tc.path("ref/gen_vectors.py"), "import sys\nsys.exit(3)\n")      # stop right after versions
        return tc, home

    def test_flag_accepts_and_records_the_drift(self):
        tc, home = self.drift_case(STA_DRIFT_LOG)
        rc, _ = run_main(PRE_F1 + ["--allow-tool-drift"])
        self.assertEqual(rc, 1)
        v = load(os.path.join(tc.run_root(), "verdict.json"))
        self.assertIn("gen_vectors failed", v["error"])                    # got past env_snapshot and versions
        self.assertEqual(v["env_snapshot"], {"allow_tool_drift": True, "tool_drift": {
            "opensta/bin/sta": grade.sha256(os.path.join(home, "tools", "opensta", "bin", "sta"))}})

    def test_without_the_flag_the_drift_fails(self):
        tc, _ = self.drift_case(STA_DRIFT_LOG)
        rc, lines = run_main(PRE_F1)
        self.assertEqual(rc, 1)
        self.assertTrue(lines[-1].startswith("GRADE FAIL: GradeError: env_snapshot failed (exit 1"), lines)
        self.assertNotIn("env_snapshot", load(os.path.join(tc.run_root(), "verdict.json")))

    def test_flag_still_fails_on_other_drift(self):
        tc, _ = self.drift_case(STA_DRIFT_LOG.replace("opensta/bin/sta", "oss-cad-suite/libexec/yosys"))
        rc, lines = run_main(PRE_F1 + ["--allow-tool-drift"])
        self.assertEqual(rc, 1)
        self.assertIn("not only an allowed tool drift", lines[-1])

    def test_flag_with_a_clean_snapshot_records_no_drift(self):
        tc = TempCase(self, snapshot_ok=True)
        write(tc.path("ref/gen_vectors.py"), "import sys\nsys.exit(3)\n")
        rc, _ = run_main(PRE_F1 + ["--allow-tool-drift"])
        self.assertEqual(rc, 1)
        v = load(os.path.join(tc.run_root(), "verdict.json"))
        self.assertIn("gen_vectors failed", v["error"])
        self.assertEqual(v["env_snapshot"], {"allow_tool_drift": True, "tool_drift": {}})


if __name__ == "__main__":
    unittest.main()
