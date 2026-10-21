"""Tests for limits.run_limited / still_alive / cleanup (CASE-01 stage B, Task 1). Run per module, never with discover.
Both fixtures limit themselves (10 s, 64 KB) so a broken wrapper cannot leave a runaway process (incident 2026-10-12)."""
import json
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

import limits

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "limits")
TREE = [sys.executable, "-B", os.path.join(FIX, "tree.py")]
CHATTY = [sys.executable, "-B", os.path.join(FIX, "chatty.py")]
RUNS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "runs")
POSIX = os.name != "nt"

# fast limits for the tests: 2 s run time, 1 KB output, 1 s after the gentle stop, 3 s after the forced stop
FAST = limits.Limit(timeout=2, stdout_max=1024, stderr_max=1024, term_wait=1, kill_wait=3)


def alive(pid):
    return limits._start_time(pid) is not None


class Base(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="limits_", dir=RUNS)
        self.d = self.tmp.name
        self.pidfile = os.path.join(self.d, "pids.txt")
        open(self.pidfile, "w").close()
        p = mock.patch.dict(limits.LIMITS, {"fast": FAST})
        p.start()
        self.addCleanup(p.stop)

    def tearDown(self):
        # safety net: whatever the wrapper did, no fixture process outlives the test
        for role, pid in self.pids().items():
            if alive(pid):
                limits._kill_pid(pid)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and any(alive(p) for p in self.pids().values()):
            time.sleep(0.05)
        self.tmp.cleanup()

    def pids(self):
        out = {}
        with open(self.pidfile, encoding="ascii") as f:
            for line in f:
                role, pid = line.split()
                out[role] = int(pid)
        return out

    def tree(self, *args, **kw):
        t0 = time.monotonic()
        res = limits.run_limited(TREE + ["--pidfile", self.pidfile] + list(args), "fast", cwd=self.d, **kw)
        self.elapsed = time.monotonic() - t0
        return res

    def assert_all_gone(self, res, roles):
        # fixtures live up to 10 s on their own: a run must end well before that, or "gone" proves nothing
        self.assertLess(self.elapsed, 8)
        pids = self.pids()
        self.assertEqual(sorted(pids), sorted(roles))
        for role, pid in pids.items():
            self.assertFalse(alive(pid), f"{role} {pid} still alive")
        self.assertEqual(res.killed_pids_alive, [])
        self.assertFalse(res.cleanup_unconfirmed)


class TestTrees(Base):
    def test_timeout_kills_child_and_grandchild(self):
        res = self.tree()
        self.assertTrue(res.timed_out)
        self.assert_all_gone(res, ["root", "child", "grandchild"])
        self.assertTrue(res.signals_sent)

    def test_new_session_grandchild_killed(self):
        res = self.tree("--new-session")
        self.assertTrue(res.timed_out)
        self.assert_all_gone(res, ["root", "child", "grandchild"])
        reg = {pid for pid, _ in res.registry}
        self.assertIn(self.pids()["root"], reg)

    def test_root_without_children_killed(self):
        res = self.tree("--no-children")
        self.assertTrue(res.timed_out)
        self.assert_all_gone(res, ["root"])
        self.assertEqual(res.registry[0][0], self.pids()["root"])

    @unittest.skipUnless(POSIX, "Windows has no gentle termination signal: run_limited goes straight to "
                                "TerminateJobObject, so there is no SIGTERM to ignore")
    def test_root_ignores_term(self):
        res = self.tree("--ignore-term")
        self.assertTrue(res.timed_out)
        self.assert_all_gone(res, ["root"])
        kinds = [s.split()[0] for s in res.signals_sent]
        self.assertIn("SIGTERM", kinds)
        self.assertIn("SIGKILL", kinds)
        self.assertLess(kinds.index("SIGTERM"), kinds.index("SIGKILL"))

    def test_short_lived_parent_orphan_found(self):
        # no periodic scan before the timeout: the orphan (whose parent is gone) must be found by the ownership
        # mechanism itself (subreaper adoption / job membership), not by an earlier registry snapshot
        with mock.patch.object(limits, "SCAN_INTERVAL", 60):
            res = self.tree("--orphan")
        self.assertTrue(res.timed_out)
        self.assert_all_gone(res, ["root", "child", "grandchild"])

    def test_root_exits_first_descendants_killed(self):
        t0 = time.monotonic()
        res = self.tree("--root-exits")
        self.assertFalse(res.timed_out)
        self.assertEqual(res.rc, 0)
        self.assert_all_gone(res, ["root", "grandchild"])
        self.assertTrue(res.signals_sent, "killing the leftover grandchild must be recorded")
        if POSIX:
            self.assertIn(self.pids()["grandchild"], {pid for pid, _ in res.registry})
        self.assertLess(time.monotonic() - t0, 8)

    def test_isolation_mechanism_reported(self):
        res = self.tree("--no-children")
        self.assertEqual(res.isolation, "job" if os.name == "nt" else "subreaper")
        marker = os.path.join(self.d, "marker")

        def broken():
            raise OSError("mechanism unavailable")
        with mock.patch.object(limits, "_setup_isolation", broken):
            with self.assertRaises(limits.IsolationFail) as cm:
                limits.run_limited(CHATTY + ["--marker", marker], "fast", cwd=self.d)
        self.assertIn("ISOLATION FAIL", str(cm.exception))
        time.sleep(0.5)
        self.assertFalse(os.path.exists(marker))


class TestOutput(Base):
    def test_stdout_over_limit_kills(self):
        t0 = time.monotonic()
        res = limits.run_limited(CHATTY + ["--flood"], "fast", cwd=self.d)
        self.assertTrue(res.stdout_over)
        self.assertFalse(res.timed_out)
        self.assertEqual(res.stdout_bytes, 1024)
        self.assertEqual(len(res.stdout), 1024)
        self.assertNotEqual(res.rc, 0)
        self.assertEqual(res.killed_pids_alive, [])
        self.assertTrue(res.incomplete)
        self.assertLess(time.monotonic() - t0, 5)

    def test_stdout_and_stderr_streamed_to_file(self):
        out, err = os.path.join(self.d, "o.txt"), os.path.join(self.d, "e.txt")
        res = limits.run_limited(CHATTY + ["--stdout", "700", "--stderr", "300"], "fast", cwd=self.d,
                                 stdout_path=out, stderr_path=err)
        self.assertEqual(res.rc, 0)
        with open(out, "rb") as f:
            self.assertEqual(f.read(), res.stdout)
        with open(err, "rb") as f:
            self.assertEqual(f.read(), res.stderr)
        self.assertEqual((res.stdout_bytes, res.stderr_bytes), (700, 300))
        # interrupted run: what was captured before the kill is on disk
        out2, err2 = os.path.join(self.d, "o2.txt"), os.path.join(self.d, "e2.txt")
        res = limits.run_limited(CHATTY + ["--stdout", "100", "--stderr", "50", "--sleep"], "fast", cwd=self.d,
                                 stdout_path=out2, stderr_path=err2)
        self.assertTrue(res.timed_out)
        self.assertTrue(res.incomplete)
        self.assertEqual(os.path.getsize(out2), 100)
        self.assertEqual(os.path.getsize(err2), 50)

    def test_on_line_called_on_first_line(self):
        flag = os.path.join(self.d, "seen")
        lines = []

        def on_line(line):
            lines.append(line)
            open(flag, "w").close()
        t0 = time.monotonic()
        res = limits.run_limited(CHATTY + ["--first-line", "RUN_ID 20261020-abc", "--wait-file", flag], "fast",
                                 cwd=self.d, on_line=on_line)
        self.assertEqual(res.rc, 0)
        self.assertFalse(res.timed_out)
        self.assertEqual(lines, ["RUN_ID 20261020-abc"])
        self.assertLess(time.monotonic() - t0, 2)

    def test_stdin_bytes_passed(self):
        res = limits.run_limited([sys.executable, "-B", "-c",
                                  "import sys; d=sys.stdin.buffer.read(4096); sys.stdout.buffer.write(d[::-1])"],
                                 "fast", cwd=self.d, stdin_bytes=b"abc\n")
        self.assertEqual(res.rc, 0)
        self.assertEqual(res.stdout, b"\ncba")

    def test_normal_exit(self):
        res = limits.run_limited(CHATTY + ["--first-line", "hello"], "fast", cwd=self.d)
        self.assertEqual(res.rc, 0)
        self.assertEqual(res.stdout, b"hello\n")
        self.assertEqual((res.stdout_bytes, res.stderr_bytes), (6, 0))
        self.assertFalse(res.timed_out or res.stdout_over or res.stderr_over or res.cleanup_unconfirmed)
        self.assertEqual(res.signals_sent, [])
        self.assertEqual(res.killed_pids_alive, [])
        self.assertFalse(res.incomplete)


class TestRecords(Base):
    def test_limits_table(self):
        mb = 1024 * 1024
        self.assertEqual(list(limits.LIMITS)[:5], ["model", "preflight", "yosys", "grade", "test"])
        self.assertEqual(limits.LIMITS["model"], limits.Limit(1800, 50 * mb, 1 * mb, 30, 30))
        self.assertEqual(limits.LIMITS["preflight"], limits.Limit(60, 1 * mb, 1 * mb, 10, 10))
        self.assertEqual(limits.LIMITS["yosys"], limits.Limit(60, 10 * mb, 10 * mb, 10, 10))
        self.assertEqual(limits.LIMITS["grade"], limits.Limit(7200, 50 * mb, 50 * mb, 90, 30))
        self.assertEqual(limits.LIMITS["test"], limits.Limit(30, 1 * mb, 1 * mb, 5, 5))
        with self.assertRaises(KeyError):
            limits.run_limited(CHATTY, "no_such_kind")

    def test_proc_record_written_and_updated(self):
        path = os.path.join(self.d, "proc.json")
        seen = []

        def on_line(line):
            with open(path, encoding="utf-8") as f:
                seen.append(json.load(f))
        res = self.tree(proc_path=path, on_line=on_line)
        self.assertEqual(len(seen), 1)
        first = seen[0]
        self.assertEqual(first["root_pid"], self.pids()["root"])
        self.assertIn("started_at", first)
        self.assertNotIn("ended_at", first)
        self.assertEqual(first["isolation"], res.isolation)
        with open(path, encoding="utf-8") as f:
            last = json.load(f)
        self.assertEqual(last["root_pid"], first["root_pid"])
        self.assertEqual(last["root_start"], first["root_start"])
        self.assertIn("ended_at", last)
        self.assertEqual(last["alive_after"], [])
        reg = {pid for pid, _ in last["registry"]}
        self.assertTrue({self.pids()["root"], self.pids()["child"], self.pids()["grandchild"]} <= reg)
        self.assertEqual([tuple(e) for e in last["registry"]], [tuple(e) for e in res.registry])

    def test_proc_record_shows_signals_and_timeout(self):
        path = os.path.join(self.d, "proc.json")
        seen = []
        real_kill = os.kill

        def spy(pid, sig):                          # what the record says at the moment a signal is sent
            with open(path, encoding="utf-8") as f:
                seen.append((sig, json.load(f)))
            return real_kill(pid, sig)

        if POSIX:
            with mock.patch.object(limits.os, "kill", spy):
                res = self.tree("--ignore-term", proc_path=path)
        else:
            res = self.tree(proc_path=path)
        self.assertTrue(res.timed_out)
        with open(path, encoding="utf-8") as f:
            last = json.load(f)
        self.assertIs(last["timed_out"], True)
        self.assertEqual(last["signals_sent"], res.signals_sent)
        self.assertTrue(last["signals_sent"])
        if POSIX:
            import signal as sg
            term = [rec for sig, rec in seen if sig == sg.SIGTERM]
            kill = [rec for sig, rec in seen if sig == sg.SIGKILL]
            self.assertTrue(term and kill)
            self.assertIs(term[0]["timed_out"], True)
            self.assertTrue(term[0]["signals_sent"][0].startswith("SIGTERM"))
            self.assertTrue(any(s.startswith("SIGKILL") for s in kill[0]["signals_sent"]))

    def test_proc_extra_saved_on_request(self):
        path = os.path.join(self.d, "proc.json")
        extra = {}
        saves = []
        real = limits._write_json

        def spy(p, obj):
            saves.append(dict(obj))
            real(p, obj)

        def on_line(line):
            extra["run_id"] = "r1"
            extra["root_pid"] = -1                   # the record's own keys win
            return True                              # save now

        with mock.patch.object(limits, "_write_json", spy):
            self.tree("--no-children", proc_path=path, on_line=on_line, proc_extra=extra)
        first = next(r for r in saves if "run_id" in r)
        self.assertIs(first["timed_out"], False)     # saved on request, before the time limit
        self.assertNotIn("ended_at", first)
        with open(path, encoding="utf-8") as f:
            last = json.load(f)
        self.assertEqual(last["run_id"], "r1")
        self.assertEqual(last["root_pid"], self.pids()["root"])

    def test_still_alive_detects_survivor_and_pid_reuse(self):
        import subprocess
        proc = subprocess.Popen(TREE + ["--pidfile", self.pidfile, "--no-children"], stdout=subprocess.DEVNULL,
                                stdin=subprocess.DEVNULL)
        try:
            start = None
            deadline = time.monotonic() + 5
            while start is None and time.monotonic() < deadline:
                start = limits._start_time(proc.pid)
            rec = {"root_pid": proc.pid, "root_start": start, "registry": [[proc.pid, start]]}
            self.assertEqual(limits.still_alive(rec), ([proc.pid], False))
            reused = {"root_pid": proc.pid, "root_start": "1" + start, "registry": [[proc.pid, "1" + start]]}
            self.assertEqual(limits.still_alive(reused), ([], False))
            res = limits.cleanup(rec, "fast")
            self.assertEqual(res.killed_pids_alive, [])
            self.assertFalse(res.cleanup_unconfirmed)
            self.assertEqual(limits.still_alive(rec), ([], False))
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=10)

    def test_kill_fail_reported(self):
        path = os.path.join(self.d, "proc.json")
        with mock.patch.object(limits, "_force_kill", lambda ctx, pids: None):
            res = self.tree("--ignore-term", proc_path=path)
        root = self.pids()["root"]
        self.assertIn(root, res.killed_pids_alive)
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        self.assertIn(root, rec["alive_after"])
        # clean up with the real functions before the test ends
        res2 = limits.cleanup(rec, "fast")
        self.assertEqual(res2.killed_pids_alive, [])
        self.assertFalse(alive(root))

    def test_unconfirmed_cleanup_reported(self):
        def broken(pid, start):
            raise OSError("process table unreadable")
        with mock.patch.object(limits, "_is_alive", broken):
            res = self.tree("--no-children")
        self.assertTrue(res.timed_out)
        self.assertTrue(res.cleanup_unconfirmed)


class TestFailurePaths(Base):
    def assert_tree_gone_later(self):
        # give a process that escaped the cleanup time to show up, then check every recorded pid
        time.sleep(1.5)
        for role, pid in self.pids().items():
            self.assertFalse(alive(pid), f"{role} {pid} still alive")

    def test_bad_output_path_cleans_tree(self):
        bad = os.path.join(self.d, "no_such_dir", "out.txt")
        t0 = time.monotonic()
        with self.assertRaises(OSError):
            self.tree("--new-session", stdout_path=bad)
        self.assertLess(time.monotonic() - t0, 8)
        self.assert_tree_gone_later()

    def test_proc_record_failure_cleans_tree(self):
        path = os.path.join(self.d, "proc.json")
        real = limits._write_json
        calls = []

        def failing(p, obj):
            calls.append(obj)
            if len(calls) > 1 and "ended_at" not in obj:  # the first registry update after launch fails
                raise OSError(28, "No space left on device")
            real(p, obj)
        t0 = time.monotonic()
        with mock.patch.object(limits, "_write_json", failing):
            with self.assertRaises(OSError):
                self.tree("--new-session", proc_path=path)
        self.assertLess(time.monotonic() - t0, 8)
        self.assertGreaterEqual(len(self.pids()), 2)
        self.assert_tree_gone_later()
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        self.assertEqual(rec["alive_after"], [])
        self.assertIn("ended_at", rec)

    def test_output_write_error_reported(self):
        class Full:
            def write(self, data):
                raise OSError(28, "No space left on device")

            def flush(self):
                pass

            def close(self):
                pass
        hooked = []
        out = os.path.join(self.d, "o.txt")
        t0 = time.monotonic()
        with mock.patch.object(limits, "_open_output", lambda path: Full()), \
                mock.patch("threading.excepthook", lambda args: hooked.append(args)):
            res = limits.run_limited(CHATTY + ["--stdout", "100", "--sleep"], "fast", cwd=self.d, stdout_path=out)
        self.assertLess(time.monotonic() - t0, 2)      # stopped on the write error, not by the 2 s timeout
        self.assertFalse(res.timed_out)
        self.assertIn("No space left on device", res.output_error)
        self.assertTrue(res.incomplete)
        self.assertEqual(res.killed_pids_alive, [])
        self.assertFalse(res.cleanup_unconfirmed)
        self.assertEqual(res.stdout_bytes, 100)            # still captured in memory
        self.assertEqual(hooked, [])


if __name__ == "__main__":
    unittest.main()
