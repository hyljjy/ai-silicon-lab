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

    def test_requested_saves_stay_on_supervising_thread(self):
        # regression (review of 4214c49): a save requested from on_line must not read the registry on the reader
        # thread while the supervisor's scan() inserts into it (OrderedDict mutated during iteration)
        import threading
        path = os.path.join(self.d, "proc.json")
        extra = {}
        threads = []
        lines = []
        real = limits._Run.record

        def record(run_self):
            threads.append(threading.current_thread())
            return real(run_self)

        def on_line(line):
            lines.append(line)
            extra["n"] = len(lines)
            return True                              # request a save for every line

        with mock.patch.object(limits._Run, "record", record):
            res = limits.run_limited(CHATTY + ["--stdout", "960"], "fast", cwd=self.d, proc_path=path, on_line=on_line,
                                     proc_extra=extra)
        self.assertGreater(len(lines), 10)
        self.assertTrue(threads)
        self.assertEqual({t for t in threads}, {threading.current_thread()})
        self.assertFalse(res.stdout_over)            # a healthy run is not stopped by the requested saves
        with open(path, encoding="utf-8") as f:
            last = json.load(f)
        self.assertEqual(last["n"], len(lines))

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
        # the target was already running when the output file failed: a supervision failure, not a launch failure
        bad = os.path.join(self.d, "no_such_dir", "out.txt")
        t0 = time.monotonic()
        with self.assertRaises(limits.SupervisionError) as cm:
            self.tree("--new-session", stdout_path=bad)
        self.assertLess(time.monotonic() - t0, 8)
        e = cm.exception
        self.assertNotIsInstance(e, OSError)
        self.assertIsInstance(e.__cause__, OSError)
        self.assertIsInstance(e.pid, int)
        if "root" in self.pids():                   # the root may be stopped before it wrote its pid
            self.assertEqual(e.pid, self.pids()["root"])
        self.assertTrue(e.root_start)
        self.assertEqual(e.isolation, "job" if os.name == "nt" else "subreaper")
        self.assertEqual(e.killed_pids_alive, [])
        self.assertFalse(e.cleanup_unconfirmed)
        self.assertEqual(e.cause_type, "FileNotFoundError")
        self.assert_tree_gone_later()

    def test_proc_record_failure_cleans_tree(self):
        path = os.path.join(self.d, "proc.json")
        real = limits._write_json

        def failing(p, obj):
            # the first registry update after the children were found fails
            if len(obj.get("registry") or []) > 1 and "ended_at" not in obj:
                raise OSError(28, "No space left on device")
            real(p, obj)
        t0 = time.monotonic()
        with mock.patch.object(limits, "_write_json", failing):
            with self.assertRaises(limits.SupervisionError) as cm:
                self.tree("--new-session", proc_path=path)
        self.assertLess(time.monotonic() - t0, 8)
        self.assertGreaterEqual(len(self.pids()), 2)
        self.assert_tree_gone_later()
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        self.assertEqual(rec["alive_after"], [])
        self.assertIn("ended_at", rec)
        self.assertIs(rec["aborted"], True)
        self.assertIs(rec["cleanup_unconfirmed"], False)
        self.assertEqual(rec["abort_error"], "OSError")
        self.assertEqual(cm.exception.killed_pids_alive, [])
        self.assertFalse(limits.record_cleanup_failed(rec))

    def test_emergency_cleanup_failure_propagated(self):
        # the forced stop does nothing: the error raised after the supervision failure must carry the survivors
        path = os.path.join(self.d, "proc.json")
        real = limits._write_json

        def failing(p, obj):
            if len(obj.get("registry") or []) > 1 and "ended_at" not in obj:
                raise OSError(28, "No space left on device")
            real(p, obj)
        with mock.patch.object(limits, "_write_json", failing), \
                mock.patch.object(limits, "_force_kill", lambda ctx, pids: None):
            with self.assertRaises(limits.SupervisionError) as cm:
                self.tree(proc_path=path)
        root = self.pids()["root"]
        self.assertIn(root, cm.exception.killed_pids_alive)
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        self.assertIs(rec["aborted"], True)
        self.assertIn(root, rec["alive_after"])
        self.assertTrue(limits.record_cleanup_failed(rec))

    def test_launch_failure_is_oserror_and_recorded(self):
        path = os.path.join(self.d, "proc.json")
        with self.assertRaises(OSError) as cm:
            limits.run_limited([os.path.join(self.d, "no_such_program")], "fast", cwd=self.d, proc_path=path)
        self.assertNotIsInstance(cm.exception, limits.SupervisionError)
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        self.assertEqual(rec["phase"], "not_started")
        self.assertEqual(rec["launch_error"]["type"], type(cm.exception).__name__)
        self.assertEqual(limits.still_alive(rec), ([], False))

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


DRIVER = r"""
import json, os, subprocess, sys, threading
threading.Timer(25, lambda: os._exit(9)).start()            # self-limit of the driver itself
sys.path.insert(0, {here!r})
import limits
cfg = json.loads(sys.argv[1])
limits.LIMITS["drv"] = limits.Limit(*cfg["limit"])
limits.SCAN_INTERVAL = cfg.get("scan", 1.0)
if cfg.get("crash") == "after_popen":                       # the wrapper dies right after Popen returned
    real = subprocess.Popen
    class P(real):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            with open(cfg["pidout"], "w") as f:
                f.write(str(self.pid))
            os._exit(9)
    limits.subprocess.Popen = P
elif cfg.get("crash") == "before_release":                 # Windows: dies after the record, before ResumeThread
    limits._resume_process = lambda pid: os._exit(9)
limits.run_limited(cfg["argv"], "drv", cwd=cfg["cwd"], proc_path=cfg["proc"])
"""


class TestLifecycle(Base):
    """Wrapper death at the real launch boundary and after the last registry scan (Codex BC1-01, BC1-02)."""

    def driver(self, argv, crash=None, scan=1.0, limit=(8, 1024, 1024, 1, 3)):
        import subprocess
        self.proc_path = os.path.join(self.d, "proc.json")
        self.pidout = os.path.join(self.d, "pidout.txt")
        cfg = {"argv": argv, "cwd": self.d, "proc": self.proc_path, "crash": crash, "scan": scan,
               "limit": list(limit), "pidout": self.pidout}
        p = subprocess.Popen([sys.executable, "-B", "-c", DRIVER.format(here=HERE), json.dumps(cfg)],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        def stop():
            if p.poll() is None:
                p.kill()
            p.wait(10)
        self.addCleanup(stop)
        return p

    def record(self):
        with open(self.proc_path, encoding="utf-8") as f:
            return json.load(f)

    def wait(self, cond, timeout=8.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if cond():
                return True
            time.sleep(0.05)
        self.fail("condition not reached in time")

    def kill_later(self, pid):
        self.addCleanup(lambda: alive(pid) and limits._kill_pid(pid))

    def test_crash_right_after_popen(self):
        marker = os.path.join(self.d, "marker")
        p = self.driver(CHATTY + ["--sleep", "--marker", marker], crash="after_popen")
        p.wait(15)
        with open(self.pidout, encoding="ascii") as f:
            pid = int(f.read())
        self.kill_later(pid)
        rec = self.record()
        self.assertEqual(rec["phase"], "launching")
        self.assertNotIn("root_pid", rec)
        if POSIX:
            # the target runs; the record written before Popen holds the run token that every process of the run
            # carries in its environment: a fresh process finds it although no pid was recorded
            self.wait(lambda: os.path.exists(marker))
            self.assertRegex(rec["token"], r"^[0-9a-f]{32}$")
            self.assertEqual(limits.still_alive(rec), ([pid], False))
            res = limits.cleanup(rec, "fast")
            self.assertEqual(res.killed_pids_alive, [])
            self.assertFalse(res.cleanup_unconfirmed)
            self.assertFalse(alive(pid))
            self.assertEqual(limits.still_alive(rec), ([], False))
        else:
            # created suspended, outside any job: it never ran, but nothing in the record identifies it
            time.sleep(0.5)
            self.assertFalse(os.path.exists(marker))
            self.assertEqual(limits.still_alive(rec), ([], True))
            self.assertTrue(limits.cleanup(rec, "fast").cleanup_unconfirmed)
            self.assertTrue(alive(pid))
            limits._kill_pid(pid)

    @unittest.skipIf(POSIX, "CREATE_SUSPENDED and the job object exist only on Windows")
    def test_crash_before_release_is_confirmed(self):
        marker = os.path.join(self.d, "marker")
        p = self.driver(CHATTY + ["--sleep", "--marker", marker], crash="before_release")
        p.wait(15)
        rec = self.record()
        self.assertEqual(rec["phase"], "pending_release")
        self.kill_later(rec["root_pid"])
        # the wrapper's death closed the only job handle: KILL_ON_JOB_CLOSE ended the still suspended target
        self.wait(lambda: not alive(rec["root_pid"]))
        self.assertFalse(os.path.exists(marker))
        self.assertEqual(limits.still_alive(rec), ([], False))

    def test_orphan_after_last_scan_found_after_wrapper_killed(self):
        p = self.driver(TREE + ["--pidfile", self.pidfile, "--orphan"], scan=60)
        self.wait(lambda: "grandchild" in self.pids())
        self.wait(lambda: os.path.exists(self.proc_path) and "root_pid" in self.record())
        p.kill()                                   # only the wrapper dies
        p.wait(10)
        pids = self.pids()
        rec = self.record()
        self.assertNotIn(pids["grandchild"], {pid for pid, _ in rec["registry"]})
        if POSIX:
            # the registered root goes too: only the unregistered orphan is left, its subreaper is gone
            limits._kill_pid(pids["root"])
            self.wait(lambda: not alive(pids["root"]))
            self.assertTrue(alive(pids["grandchild"]))
            got, unconfirmed = limits.still_alive(rec)
            self.assertFalse(unconfirmed)
            self.assertIn(pids["grandchild"], got)
            res = limits.cleanup(rec, "fast")
            self.assertEqual(res.killed_pids_alive, [])
            self.assertFalse(res.cleanup_unconfirmed)
            self.assertFalse(alive(pids["grandchild"]))
        else:
            # KILL_ON_JOB_CLOSE: closing the wrapper's job handle ended every member, registered or not
            self.wait(lambda: not any(alive(x) for x in pids.values()))
        self.assertEqual(limits.still_alive(rec), ([], False))


class TestRecordChecks(unittest.TestCase):
    def gone(self):
        import subprocess
        p = subprocess.Popen([sys.executable, "-B", "-c", "pass"])
        p.wait()
        return p.pid

    def test_missing_root_start_is_unconfirmed(self):
        pid = self.gone()
        for iso in ("job", "subreaper", None):
            rec = {"root_pid": pid, "root_start": None, "registry": [[pid, None]], "ended_at": "x",
                   "alive_after": [], "cleanup_unconfirmed": False}
            if iso:
                rec["isolation"] = iso
            self.assertEqual(limits.still_alive(rec), ([], True), iso)

    def test_launching_record_without_token_unconfirmed(self):
        self.assertEqual(limits.still_alive({"phase": "launching", "isolation": "job"}), ([], True))
        self.assertEqual(limits.still_alive({"phase": "not_started", "isolation": "job"}), ([], False))

    def test_subreaper_record_without_token(self):
        # an older record (no run token) of a run that did not end normally cannot prove that no unregistered
        # descendant survives; one that ended normally was verified by its own (live) wrapper
        pid = self.gone()
        rec = {"root_pid": pid, "root_start": "1", "registry": [[pid, "1"]], "isolation": "subreaper"}
        self.assertEqual(limits.still_alive(rec), ([], True))
        ended = dict(rec, ended_at="x", alive_after=[], cleanup_unconfirmed=False)
        self.assertEqual(limits.still_alive(ended), ([], False))
        self.assertEqual(limits.still_alive(dict(ended, aborted=True)), ([], True))

    def test_record_cleanup_failed(self):
        self.assertFalse(limits.record_cleanup_failed({"alive_after": [], "cleanup_unconfirmed": False}))
        self.assertFalse(limits.record_cleanup_failed({}))
        self.assertTrue(limits.record_cleanup_failed({"alive_after": [12]}))
        self.assertTrue(limits.record_cleanup_failed({"alive_after": [], "cleanup_unconfirmed": True}))

    @unittest.skipUnless(POSIX, "the run token is the Linux ownership marker")
    def test_token_scan(self):
        import subprocess
        marks = limits._launch_marks()
        self.assertNotIn(limits.TOKEN_VAR, os.environ)
        env = dict(os.environ, **{limits.TOKEN_VAR: marks["token"]})
        p = subprocess.Popen([sys.executable, "-B", "-c", "import time; time.sleep(8)"], env=env,
                             stdin=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 5
            while limits._start_time(p.pid) is None and time.monotonic() < deadline:
                time.sleep(0.02)
            rec = dict(marks, phase="launching", isolation="subreaper")
            self.assertEqual(limits.still_alive(rec), ([p.pid], False))
            # another boot: nothing of that run can still exist
            self.assertEqual(limits.still_alive(dict(rec, boot_id="not-this-boot")), ([], False))
            # an environment of this user that cannot be read: unconfirmed
            real = limits._read_environ

            def denied(pid):
                if pid == p.pid:
                    raise PermissionError(13, "Permission denied")
                return real(pid)
            with mock.patch.object(limits, "_read_environ", denied):
                self.assertEqual(limits.still_alive(rec), ([], True))
                # ... unless it lies outside the wrapper's cgroup v2 subtree (e.g. "systemd --user")
                real_cg = limits._cgroup
                user_mgr = "/user.slice/user-1000.slice/user@1000.service/init.scope"
                with mock.patch.object(limits, "_cgroup", lambda pid: user_mgr if pid == p.pid else real_cg(pid)):
                    want = ([], True) if rec.get("cgroup") in (None, "/") else ([], False)
                    self.assertEqual(limits.still_alive(rec), want)
        finally:
            p.kill()
            p.wait(10)

    @unittest.skipUnless(POSIX, "prctl is Linux only")
    def test_prctl_prototype(self):
        import ctypes
        fn = limits._prctl()
        self.assertIs(fn.restype, ctypes.c_int)
        self.assertEqual(fn.argtypes, [ctypes.c_int] + [ctypes.c_ulong] * 4)


if __name__ == "__main__":
    unittest.main()
