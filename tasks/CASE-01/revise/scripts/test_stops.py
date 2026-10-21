"""Tests for stops (stop records, clearances, round locks; CASE-01 stage B, Task 1, protocol section 16).
Run per module, never with discover. Every test works in a temporary git repository under tasks/CASE-01/runs/."""
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import limits
import revpaths as rp
import stops

RUNS = os.path.join(rp.CASE, "runs")
# a helper process that exits by itself after at most 10 s and prints nothing (Global Constraints)
HOLDER = [sys.executable, "-B", "-c",
          "import os, sys, threading; threading.Timer(10, lambda: os._exit(0)).start(); sys.stdin.read(); os._exit(0)"]
GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_CEILING_DIRECTORIES")


def git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
    r = subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args], cwd=cwd, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if r.returncode != 0:
        raise AssertionError(f"git {args} failed: {r.stderr.decode('utf-8', 'replace')}")
    return r.stdout


class Base(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="stops_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.repo = self.tmp.name
        git(self.repo, "init", "-q", ".")
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "core.autocrlf", "false")
        self.revise = os.path.join(self.repo, "tasks", "CASE-01", "revise")
        os.makedirs(self.revise)
        with open(os.path.join(self.repo, "README"), "wb") as f:
            f.write(b"temp\n")
        git(self.repo, "add", "README")
        git(self.repo, "commit", "-q", "-m", "init")

    def rdir(self, rnd=1):
        return os.path.join(self.revise, "stops", f"r{rnd}")

    def commit(self, *paths):
        git(self.repo, "add", "--", *paths)
        git(self.repo, "commit", "-q", "-m", "c")

    def clear(self, rnd, stop_id, sha=None, name=None, commit=True, extra=b"decision: continue\n"):
        rec = os.path.join(self.rdir(rnd), f"{stop_id}.json")
        sha = sha or rp.sha256(rec)
        path = os.path.join(self.rdir(rnd), name or f"{stop_id}.cleared.md")
        with open(path, "wb") as f:
            f.write(f"stop_id: {stop_id}\nstop_sha256: {sha}\n".encode() + extra)
        if commit:
            self.commit(rec, path)
        return path


class TestStops(Base):
    def test_raise_and_open(self):
        sid = stops.raise_stop(1, "call", "KILL FAIL pid 123", code="KILL_FAIL", details={"pids": [123]},
                               revise=self.revise)
        self.assertRegex(sid, r"^\d{8}T\d{6}(\.\d+)?-[a-z0-9]{4}$")
        path = os.path.join(self.rdir(1), f"{sid}.json")
        with open(path, "rb") as f:
            raw = f.read()
        self.assertNotIn(b"\r\n", raw)
        rec = json.loads(raw)
        self.assertEqual(set(rec), {"stop_id", "rnd", "side", "reason", "code", "details", "time"})
        self.assertEqual((rec["stop_id"], rec["rnd"], rec["side"], rec["code"]), (sid, 1, "call", "KILL_FAIL"))
        opened = stops.open_stops(1, revise=self.revise)
        self.assertEqual([s["stop_id"] for s in opened], [sid])
        self.assertEqual(stops.open_stops(2, revise=self.revise), [])
        with self.assertRaises(ValueError):
            stops.raise_stop(1, "other", "x", revise=self.revise)
        sid2 = stops.raise_stop(1, "eval", "second", revise=self.revise)
        self.assertNotEqual(sid, sid2)
        self.assertEqual(len(stops.open_stops(1, revise=self.revise)), 2)

    def test_unreadable_stop_record_counts_as_open(self):
        os.makedirs(self.rdir(1))
        with open(os.path.join(self.rdir(1), "20261020T000000-zzzz.json"), "wb") as f:
            f.write(b"{not json")
        opened = stops.open_stops(1, revise=self.revise)
        self.assertEqual([s["stop_id"] for s in opened], ["20261020T000000-zzzz"])

    def test_cleared_with_matching_id_and_sha(self):
        sid = stops.raise_stop(1, "eval", "infra_fail twice", revise=self.revise)
        self.clear(1, sid)
        self.assertEqual(stops.open_stops(1, revise=self.revise), [])

    def test_old_clearance_does_not_clear_new_stop(self):
        old = stops.raise_stop(1, "call", "first", revise=self.revise)
        self.clear(1, old)
        new = stops.raise_stop(1, "call", "second", revise=self.revise)
        self.assertEqual([s["stop_id"] for s in stops.open_stops(1, revise=self.revise)], [new])
        # the old clearance copied under the new name still names the old stop: rejected
        with open(os.path.join(self.rdir(1), f"{old}.cleared.md"), "rb") as f:
            body = f.read()
        copy = os.path.join(self.rdir(1), f"{new}.cleared.md")
        with open(copy, "wb") as f:
            f.write(body)
        self.commit(copy, os.path.join(self.rdir(1), f"{new}.json"))
        self.assertEqual([s["stop_id"] for s in stops.open_stops(1, revise=self.revise)], [new])

    def test_clearance_with_wrong_sha_rejected(self):
        sid = stops.raise_stop(1, "call", "prompt hash mismatch", revise=self.revise)
        self.clear(1, sid, sha="0" * 64)
        self.assertEqual([s["stop_id"] for s in stops.open_stops(1, revise=self.revise)], [sid])
        # a stop record changed after the clearance was written no longer matches it
        sid2 = stops.raise_stop(1, "call", "another", revise=self.revise)
        cl = self.clear(1, sid2)
        rec = os.path.join(self.rdir(1), f"{sid2}.json")
        with open(rec, "ab") as f:
            f.write(b" ")
        self.commit(rec, cl)
        self.assertIn(sid2, [s["stop_id"] for s in stops.open_stops(1, revise=self.revise)])

    def test_uncommitted_clearance_ignored(self):
        sid = stops.raise_stop(1, "eval", "x", revise=self.revise)
        cl = self.clear(1, sid, commit=False)
        self.assertEqual([s["stop_id"] for s in stops.open_stops(1, revise=self.revise)], [sid])
        self.commit(os.path.join(self.rdir(1), f"{sid}.json"), cl)
        self.assertEqual(stops.open_stops(1, revise=self.revise), [])
        with open(cl, "ab") as f:                       # committed, then changed in the working tree
            f.write(b"edited\n")
        self.assertEqual([s["stop_id"] for s in stops.open_stops(1, revise=self.revise)], [sid])

    def test_committed_record_deleted_or_changed_stays_open(self):
        sid = stops.raise_stop(1, "call", "x", revise=self.revise)
        rec = os.path.join(self.rdir(1), f"{sid}.json")
        self.commit(rec)
        os.remove(rec)                                   # deleting the record does not clear the stop
        opened = stops.open_stops(1, revise=self.revise)
        self.assertEqual([s["stop_id"] for s in opened], [sid])
        self.assertIn("HEAD", opened[0]["why_open"])
        # a record changed in the working tree, with a clearance made for the changed bytes: still open
        with open(rec, "wb") as f:
            f.write(json.dumps({"stop_id": sid, "rnd": 1, "side": "call", "reason": "edited", "code": None,
                                "details": None, "time": "t"}).encode())
        self.clear(1, sid, commit=False)
        git(self.repo, "add", "--", os.path.join(self.rdir(1), f"{sid}.cleared.md"))
        git(self.repo, "commit", "-q", "-m", "clearance only")
        opened = stops.open_stops(1, revise=self.revise)
        self.assertEqual([s["stop_id"] for s in opened], [sid])
        self.assertIn("HEAD", opened[0]["why_open"])

    def test_both_sides_checked(self):
        sid = stops.raise_stop(2, "eval", "KILL FAIL in run_grade", revise=self.revise)
        # the call-side entry point (run_revise) checks the same round and sees the evaluation-side stop
        with stops.round_lock(2, "call", revise=self.revise):
            opened = stops.open_stops(2, revise=self.revise)
        self.assertEqual([(s["stop_id"], s["side"]) for s in opened], [(sid, "eval")])


class TestLocks(Base):
    def lock_path(self, rnd, side):
        return os.path.join(self.revise, "outputs" if side == "call" else "results", f"r{rnd}", ".lock")

    def test_lock_exclusive(self):
        with stops.round_lock(1, "call", revise=self.revise):
            path = self.lock_path(1, "call")
            with open(path, encoding="utf-8") as f:
                rec = json.load(f)
            self.assertEqual(rec["pid"], os.getpid())
            self.assertEqual(rec["start"], limits._start_time(os.getpid()))
            with self.assertRaises(stops.LockError) as cm:
                with stops.round_lock(1, "call", revise=self.revise):
                    pass
            self.assertIn("LOCKED", str(cm.exception))
            with stops.round_lock(1, "eval", revise=self.revise):    # the other side has its own lock
                self.assertTrue(os.path.exists(self.lock_path(1, "eval")))
            with stops.round_lock(2, "call", revise=self.revise):    # another round too
                pass
        self.assertFalse(os.path.exists(self.lock_path(1, "call")))
        self.assertFalse(os.path.exists(self.lock_path(1, "eval")))
        with stops.round_lock(1, "call", revise=self.revise):         # free again
            pass
        with self.assertRaises(ValueError):
            with stops.round_lock(1, "x", revise=self.revise):
                pass

    def test_lock_from_other_os_refused(self):
        path = self.lock_path(1, "eval")
        os.makedirs(os.path.dirname(path))
        other = "linux" if sys.platform == "win32" else "win32"
        raw = json.dumps({"pid": 999999, "start": "1", "side": "eval", "acquired_at": "t0", "platform": other})
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(raw)
        with self.assertRaises(stops.LockError) as cm:   # pid 999999 does not run here, still never taken over
            with stops.round_lock(1, "eval", revise=self.revise):
                pass
        self.assertIn("LOCKED", str(cm.exception))
        self.assertIn("another OS", str(cm.exception))
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), raw)
        self.assertFalse(os.path.exists(os.path.join(self.rdir(1), "lock_history.txt")))
        with stops.round_lock(1, "call", revise=self.revise):
            with open(self.lock_path(1, "call"), encoding="utf-8") as f:
                self.assertEqual(json.load(f)["platform"], sys.platform)

    def write_json(self, path, rec):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        raw = (json.dumps(rec) + "\n").encode("utf-8")
        with open(path, "wb") as f:
            f.write(raw)
        return raw

    def stale(self, **kw):
        # same pid as this process, other start time: provably not this holder, same platform
        return dict({"pid": os.getpid(), "start": "1", "side": "eval", "acquired_at": "t0",
                     "platform": sys.platform}, **kw)

    def hook_once(self, point, action, where=None):
        """Patch stops._hook so that action() runs once, the first time the given point is reached for the lock
        path; returns a list that records whether it fired."""
        fired = []
        where = where or self.lock_path(1, "eval")

        def hook(name, path):
            if name == point and path == where and not fired:
                fired.append(True)
                action()
        p = mock.patch.object(stops, "_hook", hook)
        p.start()
        self.addCleanup(p.stop)
        return fired

    def others(self, path):
        return sorted(n for n in os.listdir(os.path.dirname(path)) if n != ".lock")

    def test_takeover_race_lock_changed_before_guard(self):
        path = self.lock_path(1, "eval")
        self.write_json(path, self.stale())
        fresh = b'{"pid": 1, "start": "2", "side": "eval", "acquired_at": "t1", "platform": "x"}\n'

        def other_takes_over():          # another process took the stale lock over between our check and our guard
            with open(path, "wb") as f:
                f.write(fresh)
        fired = self.hook_once("judged", other_takes_over)
        with self.assertRaises(stops.LockError) as cm:
            with stops.round_lock(1, "eval", revise=self.revise):
                pass
        self.assertTrue(fired)
        self.assertIn("another process took the lock over first", str(cm.exception))
        with open(path, "rb") as f:
            self.assertEqual(f.read(), fresh)
        self.assertEqual(self.others(path), [])
        self.assertFalse(os.path.exists(os.path.join(self.rdir(1), "lock_history.txt")))

    def test_takeover_three_way_interleaving(self):
        # A and B both judge the same stale lock; A takes over and works; B's delayed attempt must not displace A
        # (never moves, removes or replaces .lock), and C must not get in while A works.
        path = self.lock_path(1, "eval")
        self.write_json(path, self.stale())
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        held = {}
        touched = []

        def a_takes_over():              # B has judged the lock stale; A now takes it over completely
            held["a"] = stack.enter_context(stops.round_lock(1, "eval", revise=self.revise))
            with open(path, "rb") as f:
                held["raw"] = f.read()
        fired = self.hook_once("judged", a_takes_over)
        real = {n: getattr(stops.os, n) for n in ("replace", "rename", "remove", "unlink")}

        def spy(name):
            def f(*args, **kw):
                if "raw" in held and os.path.abspath(args[0]) == os.path.abspath(path):
                    touched.append((name, args))
                return real[name](*args, **kw)
            return f
        with mock.patch.multiple(stops.os, **{n: spy(n) for n in real}):
            with self.assertRaises(stops.LockError) as cm:      # B
                with stops.round_lock(1, "eval", revise=self.revise):
                    self.fail("B entered while A holds the lock")
        self.assertTrue(fired)
        self.assertIn("LOCKED", str(cm.exception))
        self.assertEqual(touched, [])                           # B never moved or removed A's lock
        with open(path, "rb") as f:
            self.assertEqual(f.read(), held["raw"])
        self.assertEqual(json.loads(held["raw"])["acquired_at"], held["a"]["acquired_at"])
        with self.assertRaises(stops.LockError) as cm:          # C, while A works
            with stops.round_lock(1, "eval", revise=self.revise):
                self.fail("C entered while A holds the lock")
        self.assertIn("held by a running process", str(cm.exception))
        with open(path, "rb") as f:
            self.assertEqual(f.read(), held["raw"])
        self.assertEqual(self.others(path), [])
        stack.close()                                           # A finishes
        self.assertFalse(os.path.exists(path))
        with open(os.path.join(self.rdir(1), "lock_history.txt"), encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 1)     # only A took over

    def test_takeover_guard_held_by_live_taker_refused(self):
        # B holds the takeover guard and is about to replace the stale lock: A and C are refused, the stale lock
        # stays in place until B replaces it, and B then completes the takeover.
        path = self.lock_path(1, "eval")
        stale_raw = self.write_json(path, self.stale())
        errors = []

        def others_try():
            errors.append(os.path.exists(path + ".takeover"))
            for _ in ("A", "C"):
                try:
                    with stops.round_lock(1, "eval", revise=self.revise):
                        errors.append("entered")
                except stops.LockError as e:
                    errors.append(str(e))
            with open(path, "rb") as f:
                errors.append(f.read() == stale_raw)
        fired = self.hook_once("guarded", others_try)
        with stops.round_lock(1, "eval", revise=self.revise) as mine:    # B
            with open(path, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["acquired_at"], mine["acquired_at"])
            self.assertEqual(self.others(path), [])
        self.assertTrue(fired)
        self.assertEqual(len(errors), 4)
        self.assertIs(errors[0], True)
        for e in errors[1:3]:
            self.assertIn("LOCKED", e)
            self.assertIn("takeover", e)
        self.assertIs(errors[3], True)
        with open(os.path.join(self.rdir(1), "lock_history.txt"), encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 1)

    def test_stale_takeover_guard_broken(self):
        path = self.lock_path(1, "eval")
        self.write_json(path, self.stale())
        self.write_json(path + ".takeover", self.stale(acquired_at="t5"))
        with stops.round_lock(1, "eval", revise=self.revise) as mine:
            with open(path, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["acquired_at"], mine["acquired_at"])
            self.assertEqual(self.others(path), [])
        self.assertFalse(os.path.exists(path))
        with open(os.path.join(self.rdir(1), "lock_history.txt"), encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("takeover guard", lines[0])
        self.assertIn("t5", lines[0])
        self.assertIn("taken over", lines[1])

    def test_takeover_guard_not_broken_unless_provably_stale(self):
        path = self.lock_path(1, "eval")
        guard = path + ".takeover"
        other = "linux" if sys.platform == "win32" else "win32"
        p = subprocess.Popen(HOLDER, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            live_start = limits._start_time(p.pid)
            self.assertIsNotNone(live_start)
            cases = {
                "other OS": (json.dumps(self.stale(platform=other, pid=999999)) + "\n").encode(),
                "running": (json.dumps(self.stale(pid=p.pid, start=live_start)) + "\n").encode(),
                "unreadable": b"",
                "no platform": (json.dumps({"pid": os.getpid(), "start": "1"}) + "\n").encode(),
            }
            for name, graw in cases.items():
                with self.subTest(name):
                    lraw = self.write_json(path, self.stale())
                    with open(guard, "wb") as f:
                        f.write(graw)
                    with self.assertRaises(stops.LockError) as cm:
                        with stops.round_lock(1, "eval", revise=self.revise):
                            pass
                    self.assertIn("LOCKED", str(cm.exception))
                    with open(path, "rb") as f:
                        self.assertEqual(f.read(), lraw)
                    with open(guard, "rb") as f:
                        self.assertEqual(f.read(), graw)
                    self.assertEqual(self.others(path), [".lock.takeover"])
        finally:
            p.stdin.close()
            p.wait(timeout=20)
        self.assertFalse(os.path.exists(os.path.join(self.rdir(1), "lock_history.txt")))

    def test_stale_guard_of_guard_refused(self):
        path = self.lock_path(1, "eval")
        lraw = self.write_json(path, self.stale())
        g1 = self.write_json(path + ".takeover", self.stale(acquired_at="t5"))
        g2 = self.write_json(path + ".takeover.takeover", self.stale(acquired_at="t6"))
        with self.assertRaises(stops.LockError) as cm:
            with stops.round_lock(1, "eval", revise=self.revise):
                pass
        self.assertIn("LOCKED", str(cm.exception))
        self.assertIn("by hand", str(cm.exception))
        for f_, raw in ((path, lraw), (path + ".takeover", g1), (path + ".takeover.takeover", g2)):
            with open(f_, "rb") as f:
                self.assertEqual(f.read(), raw)
        self.assertEqual(self.others(path), [".lock.takeover", ".lock.takeover.takeover"])
        self.assertFalse(os.path.exists(os.path.join(self.rdir(1), "lock_history.txt")))

    def test_two_breakers_of_stale_guard_exclusive(self):
        # X and Y both judge the same stale takeover guard; X breaks it and is about to replace the lock; Y's
        # delayed attempt must not displace X's guard nor enter.
        path = self.lock_path(1, "eval")
        guard = path + ".takeover"
        self.write_json(path, self.stale())
        self.write_json(guard, self.stale(acquired_at="t5"))
        state = {}

        def y_tries():                   # X now holds the broken guard; Y runs a whole attempt
            with open(guard, "rb") as f:
                state["x_guard"] = f.read()
            try:
                with stops.round_lock(1, "eval", revise=self.revise):
                    state["y"] = "entered"
            except stops.LockError as e:
                state["y"] = str(e)
            with open(guard, "rb") as f:
                state["after"] = f.read()
        fired = self.hook_once("guarded", y_tries)
        with stops.round_lock(1, "eval", revise=self.revise):
            pass
        self.assertTrue(fired)
        self.assertIn("LOCKED", state["y"])
        self.assertEqual(state["after"], state["x_guard"])
        self.assertNotIn(b"t5", state["x_guard"])
        self.assertEqual(self.others(path), [])

    def test_guard_judged_then_replaced_before_break(self):
        # Y judges a stale guard; before Y breaks it, X breaks it and holds it: Y must not displace X's guard.
        path = self.lock_path(1, "eval")
        guard = path + ".takeover"
        self.write_json(path, self.stale())
        self.write_json(guard, self.stale(acquired_at="t5"))
        x_guard = (json.dumps({"pid": os.getpid(), "start": limits._start_time(os.getpid()), "acquired_at": "tx",
                               "platform": sys.platform}) + "\n").encode()

        def x_breaks():
            with open(guard, "wb") as f:
                f.write(x_guard)
        fired = self.hook_once("judged", x_breaks, where=guard)
        with self.assertRaises(stops.LockError) as cm:
            with stops.round_lock(1, "eval", revise=self.revise):
                pass
        self.assertTrue(fired)
        self.assertIn("LOCKED", str(cm.exception))
        with open(guard, "rb") as f:
            self.assertEqual(f.read(), x_guard)
        self.assertEqual(self.others(path), [".lock.takeover"])

    def test_unreadable_lock_refused(self):
        path = self.lock_path(1, "eval")
        os.makedirs(os.path.dirname(path))
        with open(path, "wb") as f:
            f.write(b"garbage")
        with self.assertRaises(stops.LockError):
            with stops.round_lock(1, "eval", revise=self.revise):
                pass
        with open(path, "rb") as f:
            self.assertEqual(f.read(), b"garbage")

    def test_stale_lock_taken_over_after_owner_exit(self):
        p = subprocess.Popen(HOLDER, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            start = limits._start_time(p.pid)
            self.assertIsNotNone(start)
            path = self.lock_path(1, "eval")
            os.makedirs(os.path.dirname(path))
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                json.dump({"pid": p.pid, "start": start, "side": "eval", "acquired_at": "t0",
                           "platform": sys.platform}, f)
            with self.assertRaises(stops.LockError):                  # holder still alive
                with stops.round_lock(1, "eval", revise=self.revise):
                    pass
        finally:
            p.stdin.close()
            p.wait(timeout=20)
        with stops.round_lock(1, "eval", revise=self.revise):         # holder exited: taken over
            with open(path, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["pid"], os.getpid())
        hist = os.path.join(self.rdir(1), "lock_history.txt")
        with open(hist, encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn(f"{p.pid}", lines[0])
        self.assertIn(f"{os.getpid()}", lines[0])
        self.assertIn("eval", lines[0])
        self.assertEqual(stops.open_stops(1, revise=self.revise), [])   # lock_history is not a stop record
        # same pid, different start time (pid reuse): not the holder, taken over as well
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"pid": os.getpid(), "start": "1", "side": "eval", "acquired_at": "t1",
                       "platform": sys.platform}, f)
        with stops.round_lock(1, "eval", revise=self.revise):
            pass
        with open(hist, encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
