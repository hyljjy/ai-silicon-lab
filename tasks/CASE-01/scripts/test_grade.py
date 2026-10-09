"""Unit tests for grade.py's step runner: wall-clock timeout (task review fix for Task 9)."""
import os
import tempfile
import time
import unittest

import grade


def alive(pid):
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except FileNotFoundError:
        return False


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


if __name__ == "__main__":
    unittest.main()
