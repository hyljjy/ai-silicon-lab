"""Tests for stops (stop records, clearances, round locks; CASE-01 stage B, Task 1, protocol section 16).
Run per module, never with discover. Every test works in a temporary git repository under tasks/CASE-01/runs/."""
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

    def test_takeover_race_puts_other_lock_back(self):
        path = self.lock_path(1, "eval")
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8", newline="\n") as f:      # stale: same pid, other start time
            json.dump({"pid": os.getpid(), "start": "1", "side": "eval", "acquired_at": "t0",
                       "platform": sys.platform}, f)
        fresh = b'{"pid": 1, "start": "2", "side": "eval", "acquired_at": "t1", "platform": "x"}\n'
        real_replace = os.replace

        def racing_replace(src, dst):
            # another process took the stale lock over between our check and our move
            with open(src, "wb") as f:
                f.write(fresh)
            real_replace(src, dst)
        with mock.patch.object(stops.os, "replace", racing_replace):
            with self.assertRaises(stops.LockError) as cm:
                with stops.round_lock(1, "eval", revise=self.revise):
                    pass
        self.assertIn("another process took the lock over first", str(cm.exception))
        with open(path, "rb") as f:
            self.assertEqual(f.read(), fresh)
        self.assertEqual([n for n in os.listdir(os.path.dirname(path)) if n != ".lock"], [])
        self.assertFalse(os.path.exists(os.path.join(self.rdir(1), "lock_history.txt")))

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
