"""Tests for run_grade (formal-evaluation wrapper, attempt records, recovery; CASE-01 stage B Task 5, protocol 8).
WSL only (run per module, never with discover). The real scripts/grade.py is never run: every attempt runs
fixtures/fake_grade.py, which limits itself to 10 s and 64 KB. Everything is written in a temporary git repository
under tasks/CASE-01/runs/ (never /tmp, never the real revise/results, revise/outputs or revise/stops)."""
import contextlib
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

import limits
import revpaths as rp
import stops

if os.name != "nt":
    import run_grade

RUNS = os.path.join(rp.CASE, "runs")
HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = os.path.join(HERE, "fixtures", "fake_grade.py")
CODE = "cand_ab12"
CODE2 = "cand_cd34"
GB = rp.GB
STD = ["tt_025C_1v80", "tt_100C_1v80", "ss_100C_1v60", "ss_n40C_1v60", "ff_n40C_1v95", "ff_100C_1v95"]
GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_CEILING_DIRECTORIES")
TEST_LIMIT = limits.Limit(20, 1 * limits.MB, 1 * limits.MB, 5, 5)


def git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
    r = subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=cwd, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=60)
    if r.returncode != 0:
        raise AssertionError(f"git {args} failed: {r.stderr.decode('utf-8', 'replace')}")


def touch(path, data=b"x\n", mode=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    if mode is not None:
        os.chmod(path, mode)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def alive(pid):
    return limits._start_time(pid) is not None


def wait_for(cond, timeout=8.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        v = cond()
        if v:
            return v
        time.sleep(0.05)
    raise AssertionError("condition not reached in time")


@unittest.skipIf(os.name == "nt", "test_run_grade runs only in WSL")
class Base(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="rungrade_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        t = self.tmp.name
        self.case = os.path.join(t, "case")
        self.revise = os.path.join(self.case, "revise")
        os.makedirs(os.path.join(self.case, "runs"))
        os.makedirs(self.revise)
        git(self.case, "init", "-q", ".")
        git(self.case, "config", "user.name", "test")
        git(self.case, "config", "user.email", "test@example.invalid")
        touch(os.path.join(self.case, "README"))
        git(self.case, "add", "README")
        git(self.case, "commit", "-q", "-m", "init")
        for code in (CODE, CODE2):
            touch(os.path.join(self.case, "config", f"impl.{code}.cfg"),
                  f"name = {code}\ntop = dot4sat\nrtl = rtl/dot4sat_{code}.v\nL = 1\n".encode())
        # fake environment: tools on PATH, kit, gate-level models, liberty files, env/ hash files
        self.bin = os.path.join(t, "bin")
        for tool in ("iverilog", "vvp", "yosys", "sta", "python3"):
            touch(os.path.join(self.bin, tool), b"#!/bin/sh\nexit 0\n", 0o755)
        self.kit = os.path.join(t, "kit")
        touch(os.path.join(self.kit, "MANIFEST.txt"))
        self.hd = os.path.join(t, "hd")
        for m in ("primitives.v", "sky130_fd_sc_hd.v"):
            touch(os.path.join(self.hd, "verilog", m))
        for c in STD:
            touch(os.path.join(self.hd, "lib", f"sky130_fd_sc_hd__{c}.lib"))
        self.repo = os.path.join(t, "repo")
        touch(os.path.join(self.repo, "env", "SHA256SUMS"))
        touch(os.path.join(self.repo, "env", "tools.sha256"))
        self.env = {"PATH": self.bin, "SKY130_KIT": self.kit, "SKY130_HD": self.hd, "LANG": "C.UTF-8"}
        self.preflights = []
        self.kw = dict(case=self.case, repo=self.repo, env=self.env, free_bytes=lambda vol: 100 * GB,
                       preflight=lambda rnd, step: self.preflights.append((rnd, step)))
        p = mock.patch.dict(limits.LIMITS, {"grade": TEST_LIMIT})
        p.start()
        self.addCleanup(p.stop)
        self.out = io.StringIO()

    def cdir(self, code=CODE):
        return os.path.join(self.revise, "results", "r1", code)

    def adir(self, k, code=CODE):
        return os.path.join(self.cdir(code), f"attempt{k}")

    def cmd(self, mode, code=CODE):
        return [sys.executable, "-B", FAKE, "--mode", mode, "--impl", f"config/impl.{code}.cfg"]

    def run_attempt(self, mode, code=CODE, retry=False, **kw):
        args = dict(self.kw, **kw)
        with contextlib.redirect_stdout(self.out):
            return run_grade.attempt(code, 1, retry=retry, grade_cmd=self.cmd(mode, code), **args)

    def recover(self, code=CODE, **kw):
        with contextlib.redirect_stdout(self.out):
            return run_grade.recover(code, 1, **dict(self.kw, **kw))

    def stop_records(self):
        d = os.path.join(self.revise, "stops", "r1")
        if not os.path.isdir(d):
            return []
        return [load(os.path.join(d, n)) for n in sorted(os.listdir(d)) if n.endswith(".json")]

    def file_entry(self, rec, path):
        hits = [f for f in rec["files"] if f["path"] == path]
        self.assertEqual(len(hits), 1, f"{path} in {rec['files']}")
        return hits[0]

    def threaded(self, mode, **kw):
        """Run an attempt in a thread; returns (thread, box) where box['rec'] or box['err'] is set at the end."""
        box = {}

        def target():
            try:
                box["rec"] = run_grade.attempt(CODE, 1, grade_cmd=self.cmd(mode), **dict(self.kw, **kw))
            except BaseException as e:            # reported by the test
                box["err"] = e

        th = threading.Thread(target=target, daemon=True)
        with contextlib.redirect_stdout(self.out):
            th.start()
        self.addCleanup(th.join, 30)
        return th, box

    def proc_record(self, k=1):
        path = os.path.join(self.adir(k), "proc.json")
        try:
            return load(path)
        except (OSError, ValueError):
            return None

    def registry_ready(self):
        """The proc record once its registry holds the root and at least one descendant (read once per poll)."""
        rec = self.proc_record()
        return rec if rec and len(rec.get("registry") or []) >= 2 else None

    def craft_crash(self, stdout_text, run_files=None, run_id="20261101-120000-cand_ab12-T27.91-1",
                    proc_fields=None):
        """State of a wrapper that died after starting grade: started.json, proc.json of a process that is gone
        (plus proc_fields; without them the record has the older format that lacks signals_sent / timed_out),
        partial stdout.txt; optional run directory files copied from a fixture sample."""
        adir = self.adir(1)
        os.makedirs(adir)
        dep = run_grade.dependency_check(self.env, self.repo)
        started = {"code": CODE, "rnd": 1, "k": 1, "cmd": self.cmd("hang"), "start": "2026-11-01T12:00:00+08:00",
                   "disk_before": {"free_bytes": {}}, "dependency_check": dep}
        touch(os.path.join(adir, "started.json"), json.dumps(started).encode())
        gone = subprocess.Popen([sys.executable, "-B", "-c", "pass"])
        gone.wait()
        proc = {"root_pid": gone.pid, "root_start": "1", "registry": [[gone.pid, "1"]], "isolation": "subreaper",
                "started_at": "2026-11-01T12:00:00+08:00", "run_id": run_id}
        proc.update(limits._launch_marks())         # a run token no process carries: nothing of the run is left
        proc.update(proc_fields or {})
        for key in [k for k, v in proc.items() if v is None]:
            del proc[key]
        touch(os.path.join(adir, "proc.json"), json.dumps(proc).encode())
        touch(os.path.join(adir, "stdout.txt"), stdout_text.encode())
        touch(os.path.join(adir, "stderr.txt"), b"")
        if run_files:
            src = os.path.join(HERE, "fixtures", "runs", run_files, "run")
            dst = os.path.join(self.case, "runs", run_id)
            shutil.copytree(src, dst)
        return adir


class TestRecords(Base):
    def test_success_archives_files(self):
        rec = self.run_attempt("success")
        adir = self.adir(1)
        self.assertEqual(self.preflights, [(1, "evaluate")])
        on_disk = load(os.path.join(adir, "attempt.json"))
        for key in ("code rnd k cmd start end exit_code timed_out over_limit signals_sent launch_error run_id "
                    "final_line final_line_missing failure_location attribution attribution_evidence disk_before "
                    "disk_after dependency_after files").split():
            self.assertIn(key, on_disk)
        started = load(os.path.join(adir, "started.json"))
        self.assertEqual(sorted(started), sorted("code rnd k cmd start disk_before dependency_check".split()))
        self.assertTrue(started["dependency_check"]["ok"])
        self.assertEqual(on_disk["exit_code"], 0)
        self.assertTrue(on_disk["final_line"].startswith("GRADE OK: " + on_disk["run_id"]))
        self.assertFalse(on_disk["final_line_missing"])
        self.assertEqual(on_disk["failure_location"], "none")
        self.assertEqual(on_disk["attribution"], "no_external_evidence")
        self.assertEqual(rec["attribution"], "no_external_evidence")
        for rel in ("stdout.txt", "stderr.txt", "verdict.json", "steps.json", "inputs.sha256", "sta/sta_results.tsv",
                    "sta/sta_check.json", "sta/cat_ss_n40C_1v60_in2reg_max.rpt", "sta/path_max_tt_025C_1v80.rpt",
                    "sta/path_min_ff_100C_1v95.rpt"):
            e = self.file_entry(on_disk, rel)
            self.assertEqual(e["state"], "produced", rel)
            self.assertEqual(e["sha256"], rp.sha256(os.path.join(adir, *rel.split("/"))), rel)
        self.assertEqual(rp.read_bytes(os.path.join(adir, "steps.json")),
                         rp.read_bytes(os.path.join(HERE, "fixtures", "runs", "success", "run", "steps.json")))

    def test_outside_steps_failure(self):
        rec = self.run_attempt("check_impl_fail")
        self.assertIsNone(rec["run_id"])
        self.assertEqual(rec["failure_location"], "outside_steps")
        self.assertEqual(rec["attribution"], "no_external_evidence")
        e = self.file_entry(rec, "verdict.json")
        self.assertEqual(e["state"], "not_run")
        self.assertTrue(e["reason"])
        rec2 = self.run_attempt("lint_fail", code=CODE2)
        self.assertIsNotNone(rec2["run_id"])
        self.assertEqual(rec2["failure_location"], "outside_steps")
        self.assertEqual(self.file_entry(rec2, "steps.json")["state"], "produced")

    def test_timeout_is_not_external(self):
        rec = self.run_attempt("synth_timeout")
        self.assertEqual(rec["failure_location"], "synth")
        self.assertEqual(rec["attribution"], "no_external_evidence")
        self.assertEqual(self.file_entry(rec, "synth/yosys.stdout")["state"], "produced")
        # the wrapper's own time limit: the SIGTERM it sends is not evidence of an external fault
        with mock.patch.dict(limits.LIMITS, {"grade": limits.Limit(2, limits.MB, limits.MB, 5, 5)}):
            rec2 = self.run_attempt("hang", code=CODE2)
        self.assertTrue(rec2["timed_out"])
        self.assertTrue(rec2["signals_sent"])
        self.assertEqual(rec2["exit_code"], 143)
        self.assertEqual(rec2["attribution"], "no_external_evidence")

    def test_log_problems_location(self):
        rec = self.run_attempt("log_problems")
        self.assertEqual(rec["failure_location"], "rtl_sim")
        self.assertEqual(self.file_entry(rec, "rtl_sim/sim.log")["state"], "produced")

    def test_interrupted_key_is_location(self):
        rec = self.run_attempt("interrupted_no_final")
        self.assertEqual(rec["failure_location"], "rtl_sim")
        self.assertEqual(run_grade.failure_location([{"step": "a", "returncode": 0, "timed_out": False,
                                                      "log_problems": [], "interrupted": ""},
                                                     {"step": "b", "returncode": 0, "timed_out": False,
                                                      "log_problems": [], "interrupted": "SystemExit"}],
                                                    "GRADE FAIL: x"), "b")

    def test_final_line_missing(self):
        rec = self.run_attempt("interrupted_no_final")
        self.assertIsNone(rec["final_line"])
        self.assertTrue(rec["final_line_missing"])
        self.assertEqual(rec["exit_code"], 130)
        self.assertEqual(run_grade.failure_location(None, None), "no_final_line")
        self.assertEqual(run_grade.failure_location([], "GRADE OK: x"), "none")
        self.assertEqual(run_grade.failure_location(None, "GRADE FAIL: x"), "outside_steps")


class TestAttribution(Base):
    def test_snapshot_failure_is_external(self):
        rec = self.run_attempt("env_snapshot_fail")
        self.assertEqual(rec["failure_location"], "env_snapshot")
        self.assertEqual(rec["attribution"], "external")
        self.assertTrue(any("env_snapshot" in e for e in rec["attribution_evidence"]))

    def test_sigterm_143_is_external(self):
        th, box = self.threaded("hang")
        rec = wait_for(lambda: (self.proc_record() or {}).get("run_id") and self.proc_record())
        cpath = os.path.join(self.case, "runs", rec["run_id"], "children.txt")
        wait_for(lambda: os.path.exists(cpath) and rp.read_bytes(cpath).strip())
        child = int(rp.read_bytes(cpath).split()[0])
        os.kill(rec["root_pid"], signal.SIGTERM)
        th.join(30)
        self.assertNotIn("err", box)
        r = box["rec"]
        self.assertEqual(r["exit_code"], 143)
        self.assertEqual(r["signals_sent"], [])
        self.assertEqual(r["attribution"], "external")
        self.assertTrue(any("143" in e for e in r["attribution_evidence"]))
        self.assertEqual(r["failure_location"], "rtl_sim")
        self.assertFalse(alive(child))

    def test_launch_error_is_external(self):
        with contextlib.redirect_stdout(self.out):
            rec = run_grade.attempt(CODE, 1, grade_cmd=[os.path.join(self.tmp.name, "no_such_grader")], **self.kw)
        self.assertEqual(rec["launch_error"]["type"], "FileNotFoundError")
        self.assertEqual(rec["launch_error"]["errno"], 2)
        self.assertEqual(rec["attribution"], "external")
        self.assertTrue(rec["final_line_missing"])

    def failing_record_write(self):
        real = limits._write_json

        def failing(p, obj):                       # the first registry update after grade.py's child started
            if len(obj.get("registry") or []) > 1 and "ended_at" not in obj:
                raise OSError(28, "No space left on device")
            real(p, obj)
        return mock.patch.object(limits, "_write_json", failing)

    def test_supervision_failure_is_not_launch_error(self):
        with self.failing_record_write():
            rec = self.run_attempt("hang")
        self.assertIsNone(rec["launch_error"])
        self.assertEqual(rec["supervision_error"], {"type": "OSError", "errno": 28})
        self.assertEqual(self.file_entry(rec, "stdout.txt")["state"], "produced")
        self.assertTrue(rec["run_id"])
        self.assertIn("supervision_error: OSError errno=28", rec["attribution_evidence"])
        self.assertNotIn("wrapper_interrupted", rec["attribution_evidence"])
        self.assertEqual(self.stop_records(), [])
        self.assertIs(self.proc_record()["aborted"], True)

    def test_supervision_failure_with_failed_cleanup_stops(self):
        with self.failing_record_write(), mock.patch.object(limits, "_force_kill", lambda ctx, pids: None):
            rec = self.run_attempt("hang")
        proc = self.proc_record()
        self.addCleanup(lambda: limits.cleanup(proc, "grade"))
        self.assertIsNone(rec["launch_error"])
        self.assertIn(proc["root_pid"], proc["alive_after"])
        self.assertIn("KILL FAIL", [s["reason"] for s in self.stop_records()])
        res = limits.cleanup(proc, "grade")
        self.assertEqual(res.killed_pids_alive, [])

    def test_missing_dependency_is_external(self):
        os.remove(os.path.join(self.bin, "yosys"))
        rec = self.run_attempt("success")
        started = load(os.path.join(self.adir(1), "started.json"))
        self.assertFalse(started["dependency_check"]["ok"])
        self.assertIsNone(rec["exit_code"])
        self.assertIsNone(rec["run_id"])
        self.assertFalse(os.path.exists(os.path.join(self.adir(1), "stdout.txt")))
        self.assertEqual(rec["attribution"], "external")
        self.assertTrue(any(e.startswith("dependency_missing_before_start: ") and "yosys" in e
                            for e in rec["attribution_evidence"]))
        self.assertEqual(self.file_entry(rec, "stdout.txt")["state"], "not_run")

    def test_only_gl_model_missing_is_external(self):
        rec = self.run_attempt("remove_gl")
        model = os.path.join(self.hd, "verilog", "sky130_fd_sc_hd.v")
        self.assertTrue(load(os.path.join(self.adir(1), "started.json"))["dependency_check"]["ok"])
        missing = [i for i in rec["dependency_after"]["items"] if not i["exists"]]
        self.assertEqual([i["path"] for i in missing], [model])
        self.assertEqual(rec["failure_location"], "outside_steps")
        self.assertEqual(rec["attribution"], "external")
        self.assertIn(f"dependency_missing_after_run: {model}", rec["attribution_evidence"])

    def test_log_text_is_not_external_evidence(self):
        rec = self.run_attempt("nospace_compile_fail")
        self.assertIn("No space left on device", rec["final_line"])
        self.assertEqual(rec["failure_location"], "rtl_compile")
        self.assertEqual(rec["attribution"], "no_external_evidence")
        self.assertEqual(rec["attribution_evidence"], [])
        with self.assertRaises(run_grade.RunGradeError):
            self.run_attempt("success", retry=True)

    def test_disk_drop_after_run_stops_not_external(self):
        calls = []

        def free(vol):                             # the two volumes are measured once before and once after
            calls.append(vol)
            return 100 * GB if len(calls) <= 2 else 5 * GB

        rec = self.run_attempt("check_sta_fail", free_bytes=free)
        self.assertEqual(rec["attribution"], "no_external_evidence")
        self.assertTrue(rec["disk_after"]["problems"])
        reasons = [s["reason"] for s in self.stop_records()]
        self.assertIn("运行后磁盘不足", reasons)
        self.assertIn("commit revise/stops/r1/", self.out.getvalue())


class TestAttempts(Base):
    def test_retry_refused_without_external(self):
        self.run_attempt("check_sta_fail")
        with self.assertRaises(run_grade.RunGradeError):
            self.run_attempt("success", retry=True)
        with self.assertRaises(run_grade.RunGradeError):
            self.run_attempt("success")
        self.assertFalse(os.path.exists(self.adir(2)))

    def test_third_attempt_refused(self):
        self.run_attempt("env_snapshot_fail")
        self.run_attempt("check_sta_fail", retry=True)
        with self.assertRaises(run_grade.RunGradeError) as cm:
            self.run_attempt("success", retry=True)
        self.assertIn("two attempts", str(cm.exception))
        self.assertFalse(os.path.exists(self.adir(3)))

    def test_retry_keeps_first_attempt(self):
        self.run_attempt("env_snapshot_fail")
        before = {n: rp.sha256(os.path.join(self.adir(1), n)) for n in os.listdir(self.adir(1))
                  if os.path.isfile(os.path.join(self.adir(1), n))}
        rec = self.run_attempt("success", retry=True)
        self.assertEqual(rec["k"], 2)
        after = {n: rp.sha256(os.path.join(self.adir(1), n)) for n in before}
        self.assertEqual(before, after)
        self.assertEqual(sorted(before), sorted(n for n in os.listdir(self.adir(1))
                                                if os.path.isfile(os.path.join(self.adir(1), n))))
        self.assertNotEqual(load(os.path.join(self.adir(1), "attempt.json"))["run_id"], rec["run_id"])

    def test_direct_retry_infra_fail_raises_stop(self):
        self.run_attempt("env_snapshot_fail")
        self.assertEqual(self.stop_records(), [])
        rec = self.run_attempt("env_snapshot_fail", retry=True)
        self.assertEqual(rec["attribution"], "external")
        recs = self.stop_records()
        self.assertEqual(len(recs), 1)
        self.assertIn("infra_fail", recs[0]["reason"])
        self.assertEqual(recs[0]["side"], "eval")
        self.assertEqual(recs[0]["code"], CODE)
        self.assertIn(f"STOP {recs[0]['stop_id']}", self.out.getvalue())

    def test_attempt_json_is_write_once(self):
        self.run_attempt("success")
        path = os.path.join(self.adir(1), "attempt.json")
        data = rp.read_bytes(path)
        with self.assertRaises(rp.RevpathsError):
            run_grade._write_once(path, {"changed": True})
        self.assertEqual(self.recover(), [])
        self.assertEqual(rp.read_bytes(path), data)

    def test_low_disk_refuses(self):
        with self.assertRaises(run_grade.RunGradeError) as cm:
            self.run_attempt("success", free_bytes=lambda vol: 5 * GB)
        self.assertIn("DISK FAIL", str(cm.exception))
        self.assertFalse(os.path.exists(self.adir(1)))

    def test_open_stop_refuses(self):
        stops.raise_stop(1, "eval", "test stop", revise=self.revise)
        with self.assertRaises(run_grade.RunGradeError):
            self.run_attempt("success")
        self.assertFalse(os.path.exists(self.adir(1)))

    def test_preflight_problems_refuse_attempt(self):
        with self.assertRaises(run_grade.RunGradeError) as cm:
            self.run_attempt("success", preflight=lambda rnd, step: ["NOT COMMITTED: review/r1.tsv is missing"])
        self.assertTrue(str(cm.exception).startswith("REFUSED: NOT COMMITTED: review/r1.tsv"))
        self.assertFalse(os.path.exists(os.path.join(self.adir(1), "started.json")))
        self.assertFalse(os.path.exists(self.adir(1)))
        self.assertEqual(self.run_attempt("success", preflight=lambda rnd, step: [])["k"], 1)

    def test_stdout_streamed_and_run_id_recorded_early(self):
        th, box = self.threaded("hang")
        stdout = os.path.join(self.adir(1), "stdout.txt")
        wait_for(lambda: os.path.exists(stdout) and b"child " in rp.read_bytes(stdout))
        first = rp.read_bytes(stdout).decode().splitlines()[0]
        self.assertTrue(first.startswith("RUN_ID="))
        # wait for a registry update written after the child started: run_id must survive that rewrite
        rec = wait_for(self.registry_ready)
        self.assertEqual(rec.get("run_id"), first[len("RUN_ID="):])
        self.assertEqual(rec.get("signals_sent"), [])
        self.assertIs(rec.get("timed_out"), False)
        self.assertTrue(alive(rec["root_pid"]))
        self.assertTrue(th.is_alive())
        os.kill(rec["root_pid"], signal.SIGTERM)
        th.join(30)
        self.assertNotIn("err", box)
        final = self.proc_record()
        self.assertEqual(final.get("run_id"), first[len("RUN_ID="):])
        self.assertIn("ended_at", final)

    def test_grade_new_session_children_killed_on_timeout(self):
        with mock.patch.dict(limits.LIMITS, {"grade": limits.Limit(2, limits.MB, limits.MB, 2, 2)}):
            rec = self.run_attempt("hang_leak")
        children = [int(x) for x in rp.read_bytes(os.path.join(self.case, "runs", rec["run_id"], "children.txt")).split()]
        self.assertTrue(children)
        self.assertTrue(rec["timed_out"])
        self.assertTrue(any(s.startswith("SIGTERM") for s in rec["signals_sent"]))
        self.assertTrue(any(s.startswith("SIGKILL") and str(children[0]) in s for s in rec["signals_sent"]))
        for pid in children:
            self.assertFalse(alive(pid))
        self.assertEqual(rec["attribution"], "no_external_evidence")
        self.assertEqual(self.stop_records(), [])
        proc = self.proc_record()
        self.assertIs(proc["timed_out"], True)
        self.assertEqual(proc["signals_sent"], rec["signals_sent"])


class TestRecovery(Base):
    def test_wrapper_crash_recovered_counts_attempt(self):
        self.craft_crash("RUN_ID=20261101-120000-cand_ab12-T27.91-1\nrunning rtl_sim\n")
        out = self.recover()
        self.assertEqual(len(out), 1)
        rec = load(os.path.join(self.adir(1), "attempt.json"))
        self.assertTrue(rec["final_line_missing"])
        self.assertEqual(rec["attribution"], "external")
        self.assertIn("wrapper_interrupted", rec["attribution_evidence"])
        # the interrupted attempt counts: the next one is attempt 2 and needs --retry
        with self.assertRaises(run_grade.RunGradeError):
            self.run_attempt("success")
        rec2 = self.run_attempt("success", retry=True)
        self.assertEqual(rec2["k"], 2)

    def test_recovery_kills_surviving_grader_first(self):
        driver = ("import json, os, sys, threading\n"
                  "threading.Timer(25, lambda: os._exit(9)).start()\n"
                  f"sys.path.insert(0, {HERE!r})\n"
                  "import run_grade\n"
                  "kw = json.loads(sys.argv[1])\n"
                  "run_grade.attempt(kw.pop('code'), 1, grade_cmd=kw.pop('cmd'), preflight=lambda r, s: None,\n"
                  "                  free_bytes=lambda v: 100 * 2 ** 30, **kw)\n")
        kw = {"code": CODE, "cmd": self.cmd("hang"), "case": self.case, "repo": self.repo, "env": self.env}
        wrapper = subprocess.Popen([sys.executable, "-B", "-c", driver, json.dumps(kw)], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        def stop_wrapper():
            if wrapper.poll() is None:
                wrapper.kill()
            wrapper.wait(10)
        self.addCleanup(stop_wrapper)
        rec = wait_for(self.registry_ready, timeout=15)
        children = [p for p, _ in rec["registry"] if p != rec["root_pid"]]
        os.kill(wrapper.pid, signal.SIGKILL)       # only the wrapper dies
        wrapper.wait(10)
        self.assertTrue(alive(rec["root_pid"]))
        self.assertTrue(all(alive(p) for p in children))
        self.assertFalse(os.path.exists(os.path.join(self.adir(1), "attempt.json")))
        out = self.recover()
        self.assertEqual(len(out), 1)
        self.assertFalse(alive(rec["root_pid"]))
        for p in children:
            self.assertFalse(alive(p))
        att = load(os.path.join(self.adir(1), "attempt.json"))
        self.assertEqual(att["attribution"], "external")
        self.assertIn("wrapper_interrupted", att["attribution_evidence"])
        self.assertEqual(att["run_id"], rec["run_id"])
        self.assertEqual(self.stop_records(), [])

    def test_recovery_uses_completed_result(self):
        rid = "20261101-120000-cand_ab12-T27.91-1"
        self.craft_crash(f"RUN_ID={rid}\nfrozen inputs copied\nGRADE OK: {rid} functional_pass analysis_valid\n",
                         run_files="success", run_id=rid)
        self.recover()
        rec = load(os.path.join(self.adir(1), "attempt.json"))
        self.assertFalse(rec["final_line_missing"])
        self.assertTrue(rec["final_line"].startswith("GRADE OK: "))
        self.assertEqual(rec["run_id"], rid)
        self.assertNotIn("wrapper_interrupted", rec["attribution_evidence"])
        self.assertIn("由包装器恢复", rec["attribution_evidence"])
        self.assertEqual(self.file_entry(rec, "steps.json")["state"], "produced")
        self.assertEqual(rec["exit_code"], "unknown")
        self.assertEqual(rec["timed_out"], "unknown")
        self.assertEqual(rec["over_limit"], "unknown")

    def crash_after_sigterm(self, proc_fields):
        """grade.py was stopped by SIGTERM (interrupted step, final 'GRADE FAIL: interrupted' line, steps.json), then
        the wrapper died before writing attempt.json."""
        rid = "20261101-120000-cand_ab12-T27.91-1"
        self.craft_crash(f"RUN_ID={rid}\nrunning rtl_sim\nGRADE FAIL: interrupted: SystemExit\n",
                         run_files="interrupted_no_final", run_id=rid, proc_fields=proc_fields)
        self.recover()
        rec = load(os.path.join(self.adir(1), "attempt.json"))
        self.assertEqual(rec["final_line"], "GRADE FAIL: interrupted: SystemExit")
        self.assertEqual(rec["failure_location"], "rtl_sim")
        self.assertNotIn("wrapper_interrupted", rec["attribution_evidence"])
        return rec

    def test_recovery_after_wrapper_timeout_not_external(self):
        rec = self.crash_after_sigterm({"signals_sent": ["SIGTERM 4242"], "timed_out": True})
        self.assertEqual(rec["attribution"], "no_external_evidence")
        self.assertIs(rec["timed_out"], True)
        self.assertEqual(rec["signals_sent"], ["SIGTERM 4242"])
        with self.assertRaises(run_grade.RunGradeError):
            self.run_attempt("success", retry=True)

    def test_recovery_unknown_wrapper_signals_not_external(self):
        rec = self.crash_after_sigterm(None)
        self.assertEqual(rec["attribution"], "no_external_evidence")
        self.assertIn("wrapper signals unknown (recovered)", rec["attribution_evidence"])
        self.assertEqual(rec["timed_out"], "unknown")

    def test_recovery_known_no_signal_interrupt_is_external(self):
        rec = self.crash_after_sigterm({"signals_sent": [], "timed_out": False})
        self.assertEqual(rec["attribution"], "external")
        self.assertIs(rec["timed_out"], False)

    def test_recovery_without_proc_json_stops(self):
        adir = self.craft_crash("")
        os.remove(os.path.join(adir, "proc.json"))
        with self.assertRaises(run_grade.RunGradeError):
            self.recover()
        self.assertFalse(os.path.exists(os.path.join(adir, "attempt.json")))
        self.assertIn("恢复时无法确认旧进程已退出", [s["reason"] for s in self.stop_records()])

    def test_recovery_old_record_without_token_stops(self):
        # a Linux record without the run token, of a run that did not end normally: unregistered orphans cannot be
        # ruled out (Codex BC1-02)
        adir = self.craft_crash("RUN_ID=20261101-120000-cand_ab12-T27.91-1\n", proc_fields={"token": None})
        with self.assertRaises(run_grade.RunGradeError):
            self.recover()
        self.assertFalse(os.path.exists(os.path.join(adir, "attempt.json")))

    def test_recovery_launching_record_is_wrapper_interrupted(self):
        # the wrapper died after the record written before Popen: the token proves that no process of it is left
        self.craft_crash("", proc_fields={"root_pid": None, "root_start": None, "registry": None,
                                          "phase": "launching"})
        self.recover()
        rec = load(os.path.join(self.adir(1), "attempt.json"))
        self.assertIn("wrapper_interrupted", rec["attribution_evidence"])
        self.assertEqual(rec["attribution"], "external")
        self.assertEqual(self.stop_records(), [])

    def test_recovery_not_started_record_is_launch_error(self):
        self.craft_crash("", proc_fields={"root_pid": None, "root_start": None, "registry": None,
                                          "phase": "not_started",
                                          "launch_error": {"type": "FileNotFoundError", "errno": 2}})
        self.recover()
        rec = load(os.path.join(self.adir(1), "attempt.json"))
        self.assertEqual(rec["launch_error"], {"type": "FileNotFoundError", "errno": 2})
        self.assertNotIn("wrapper_interrupted", rec["attribution_evidence"])
        self.assertEqual(self.file_entry(rec, "stdout.txt")["state"], "not_run")

    def test_recovery_record_says_kill_fail_stops(self):
        # the old wrapper's cleanup failed and it died before raising the stop: recovery raises it
        self.craft_crash("RUN_ID=20261101-120000-cand_ab12-T27.91-1\n",
                         proc_fields={"ended_at": "x", "alive_after": [4242], "cleanup_unconfirmed": False,
                                      "signals_sent": ["SIGKILL 4242"], "timed_out": True})
        self.recover()
        self.assertTrue(os.path.exists(os.path.join(self.adir(1), "attempt.json")))
        self.assertIn("KILL FAIL", [s["reason"] for s in self.stop_records()])
        rec = load(os.path.join(self.adir(1), "attempt.json"))
        self.assertNotIn("wrapper_interrupted", rec["attribution_evidence"])
        self.assertEqual(rec["attribution"], "no_external_evidence")

    def test_recovery_ended_record_without_final_line_not_external(self):
        # the wrapper finished the run itself (ended normally) and died before attempt.json: a missing final line is
        # grade.py's own result, not a wrapper interruption (R17 narrowed)
        self.craft_crash("RUN_ID=20261101-120000-cand_ab12-T27.91-1\nrunning rtl_sim\n",
                         proc_fields={"ended_at": "x", "alive_after": [], "cleanup_unconfirmed": False,
                                      "signals_sent": [], "timed_out": False})
        self.recover()
        rec = load(os.path.join(self.adir(1), "attempt.json"))
        self.assertTrue(rec["final_line_missing"])
        self.assertNotIn("wrapper_interrupted", rec["attribution_evidence"])
        self.assertEqual(rec["attribution"], "no_external_evidence")
        with self.assertRaises(run_grade.RunGradeError):
            self.run_attempt("success", retry=True)

    def test_recovery_aborted_record_is_supervision_error(self):
        self.craft_crash("RUN_ID=20261101-120000-cand_ab12-T27.91-1\nrunning rtl_sim\n",
                         proc_fields={"ended_at": "x", "alive_after": [], "cleanup_unconfirmed": False,
                                      "aborted": True, "abort_error": "OSError", "signals_sent": ["SIGKILL 4242"],
                                      "timed_out": False})
        self.recover()
        rec = load(os.path.join(self.adir(1), "attempt.json"))
        self.assertNotIn("wrapper_interrupted", rec["attribution_evidence"])
        self.assertEqual(rec["supervision_error"]["type"], "OSError")
        self.assertIsNone(rec["launch_error"])
        self.assertEqual(self.stop_records(), [])

    def test_recovery_interrupt_abort_is_wrapper_interrupted(self):
        self.craft_crash("RUN_ID=20261101-120000-cand_ab12-T27.91-1\nrunning rtl_sim\n",
                         proc_fields={"ended_at": "x", "alive_after": [], "cleanup_unconfirmed": False,
                                      "aborted": True, "abort_error": "interrupted", "signals_sent": [],
                                      "timed_out": False})
        self.recover()
        rec = load(os.path.join(self.adir(1), "attempt.json"))
        self.assertIn("wrapper_interrupted", rec["attribution_evidence"])
        self.assertIsNone(rec["supervision_error"])

    def test_recovery_unconfirmed_raises_stop(self):
        self.craft_crash("RUN_ID=20261101-120000-cand_ab12-T27.91-1\n")
        with mock.patch.object(limits, "still_alive", return_value=([], True)):
            with self.assertRaises(run_grade.RunGradeError):
                self.recover()
        self.assertFalse(os.path.exists(os.path.join(self.adir(1), "attempt.json")))
        reasons = [s["reason"] for s in self.stop_records()]
        self.assertIn("恢复时无法确认旧进程已退出", reasons)
        self.assertIn("commit revise/stops/r1/", self.out.getvalue())


if __name__ == "__main__":
    unittest.main()
