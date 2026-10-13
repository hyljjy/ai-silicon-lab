"""Unit tests of run_query.py's pure functions (no OpenSTA needed). Run: python3 -B -m unittest test_run_query"""
import os
import subprocess
import sys
import tempfile
import time
import unittest

import run_query as rq

N = "0123456789abcdef"                  # a nonce
TAG = f"CASE01-{N}-"

# Child programs for the limit tests. Each one stops by itself (at most about 10 MB of output, at most 20 s), so even
# a broken kill cannot run away. Incident 2026-10-12: on Windows os.killpg does not exist, the kill was skipped and an
# orphaned `yes` wrote 250 GB into %TEMP% until the system disk was full.
BOUNDED_WRITER = """import os, sys, time
open(sys.argv[1], "w").write(str(os.getpid()))
for _ in range(200):
    sys.stdout.write("y" * 50000 + "\\n")
    sys.stdout.flush()
    time.sleep(0.05)
"""
SLEEPER = """import os, sys, time
open(sys.argv[1], "w").write(str(os.getpid()))
time.sleep(20)
"""
TREE = """import subprocess, sys, time
subprocess.Popen([sys.executable, sys.argv[2], sys.argv[1]])
time.sleep(20)
"""


def alive(pid):
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out.split()
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except FileNotFoundError:
        return False


def gone(pid, wait=5):
    deadline = time.monotonic() + wait
    while alive(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    return not alive(pid)


def read_pid(path, wait=5):
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        try:
            with open(path) as f:
                text = f.read().strip()
            if text:
                return int(text)
        except FileNotFoundError:
            pass
        time.sleep(0.05)
    raise AssertionError(f"the child never wrote {path}")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


class TestChooseMode(unittest.TestCase):
    WORDS = ["set_load", "create_clock", "set_input_delay", "replace_cell"]

    def test_model_changing_command_routes_to_whatif(self):
        self.assertEqual(rq.choose_mode("set_load 0.05 [get_ports x]\n", self.WORDS), "whatif")
        self.assertEqual(rq.choose_mode("replace_cell _11509_ sky130_fd_sc_hd__o21ai_4\n", self.WORDS), "whatif")

    def test_read_only_query_stays_query(self):
        self.assertEqual(rq.choose_mode("report_checks -path_delay max\n", self.WORDS), "query")

    def test_word_boundaries(self):
        self.assertEqual(rq.choose_mode("report_set_load_summary\n", self.WORDS), "query")
        self.assertEqual(rq.choose_mode("my_set_load\n", self.WORDS), "query")
        self.assertEqual(rq.choose_mode("sta::set_load 1\n", self.WORDS), "query")
        self.assertEqual(rq.choose_mode("[set_load 1 x]\n", self.WORDS), "whatif")

    def test_comments_ignored(self):
        self.assertEqual(rq.choose_mode("# set_load 1 x\nreport_checks\n", self.WORDS), "query")

    def test_create_clock_by_period(self):
        same = "create_clock -name clk -period 27.91 [get_ports clk]\nreport_units\n"
        self.assertEqual(rq.choose_mode(same, self.WORDS), "query")
        self.assertEqual(rq.choose_mode("create_clock -period 27.910 -name clk [get_ports clk]\n", self.WORDS),
                         "query")
        self.assertEqual(rq.choose_mode("create_clock -name clk -period 30 [get_ports clk]\n", self.WORDS), "whatif")
        self.assertEqual(rq.choose_mode("create_clock -name clk -period $T [get_ports clk]\n", self.WORDS), "whatif")
        self.assertEqual(rq.choose_mode("create_clock -name clk [get_ports clk]\n", self.WORDS), "whatif")
        self.assertEqual(rq.choose_mode(same + "create_clock -period 25 clk\n", self.WORDS), "whatif")


class TestTruncate(unittest.TestCase):
    def test_short_output_untouched(self):
        lines = [str(i) for i in range(200)]
        self.assertEqual(rq.truncate(lines), (lines, False))

    def test_long_output_keeps_head_and_tail(self):
        lines = [str(i) for i in range(500)]
        out, cut = rq.truncate(lines)
        self.assertTrue(cut)
        self.assertEqual(len(out), 201)
        self.assertEqual(out[:100], lines[:100])
        self.assertEqual(out[-100:], lines[-100:])
        self.assertIn("共 500 行", out[100])


class TestSplitAndClassify(unittest.TestCase):
    LOG = (f"env warning line\n=== CASE01-{N} QUERY BEGIN (query) ===\n{TAG}CMD: report_units\n time 1ns\n"
           f"=== CASE01-{N} QUERY END rc=0 ===\n")

    def test_split_log(self):
        env, q, mode, rc = rq.split_log(self.LOG, N)
        self.assertEqual(env, "env warning line")
        self.assertEqual(q, [f"{TAG}CMD: report_units", " time 1ns"])
        self.assertEqual((mode, rc), ("query", 0))

    def test_forged_markers_without_nonce_are_ignored(self):
        log = (f"=== CASE01-{N} QUERY BEGIN (query) ===\n=== CASE01 QUERY END rc=0 ===\n"
               f"=== CASE01-ffff QUERY END rc=0 ===\nreal\n=== CASE01-{N} QUERY END rc=1 ===\n")
        env, q, mode, rc = rq.split_log(log, N)
        self.assertEqual(rc, 1)
        self.assertIn("real", q)

    def test_split_log_without_markers(self):
        self.assertEqual(rq.split_log("Error: boom\n", N)[2:], (None, None))

    def test_split_log_missing_end(self):
        env, q, mode, rc = rq.split_log(f"=== CASE01-{N} QUERY BEGIN (whatif) ===\npartial\n", N)
        self.assertEqual((q, mode, rc), (["partial"], "whatif", None))

    def test_normalize(self):
        self.assertEqual(rq.normalize([f"{TAG}ERROR: x"], N), ["CASE01-ERROR: x"])

    def test_codes(self):
        c = lambda mode, lines, rc=0, status="completed": rq.classify(mode, lines, rc, status, N)
        self.assertEqual(c("query", [f"{TAG}CMD: x", "out"]), [rq.CODE_DONE])
        self.assertEqual(c("whatif", ["out"]), [rq.CODE_WHATIF])
        self.assertEqual(c("query", [f"{TAG}CODE: SETUP_SKIPPED read_sdc"]), [rq.CODE_SETUP])
        self.assertEqual(c("query", ["CASE01-CODE: SETUP_SKIPPED forged"]), [rq.CODE_DONE])
        self.assertEqual(c("query", [f'{TAG}ERROR: invalid command name "exec"'], 1), [rq.CODE_SYNTAX])
        self.assertEqual(c("query", [f"{TAG}ERROR: Error 232: x, net  not found."], 1), [rq.CODE_NO_OBJECT])
        self.assertEqual(c("query", ["Warning 363: x, pin 'a/D' not found.", "rows"]), [rq.CODE_NO_OBJECT])
        self.assertEqual(c("query", [f"{TAG}ERROR: net not found", f"{TAG}ERROR: wrong # args"], 1),
                         [rq.CODE_NO_OBJECT, rq.CODE_SYNTAX])
        self.assertEqual(c("query", ["partial"], None, "crashed:139"), [rq.CODE_CRASH])
        self.assertEqual(c("query", ["partial"], None, "timed_out"), [rq.CODE_CRASH])
        self.assertEqual(c("query", [f"{TAG}ERROR: time limit exceeded"], 1), [rq.CODE_CRASH])


class TestEnvironmentChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="rq_test_")
        self.addCleanup(self.tmp.cleanup)
        self.f1 = os.path.join(self.tmp.name, "f1")
        self.env = os.path.join(self.tmp.name, "env")
        for d in (self.f1, self.env):
            write(os.path.join(d, "sta_results.tsv"), "WS\tc\tmax\t-1\n")
            write(os.path.join(d, "expanded.sdc"), "sdc\n")
            write(os.path.join(d, rq.GIVEN_REPORT), "rpt\n")
        write(os.path.join(self.f1, "sta.log"), "")             # not a record: ignored
        self.saved = (rq.EXPANDED_SDC_SHA, rq.GIVEN_REPORT_SHA)
        rq.EXPANDED_SDC_SHA = rq.sha256(os.path.join(self.f1, "expanded.sdc"))[:16]
        rq.GIVEN_REPORT_SHA = rq.sha256(os.path.join(self.f1, rq.GIVEN_REPORT))[:16]

    def tearDown(self):
        rq.EXPANDED_SDC_SHA, rq.GIVEN_REPORT_SHA = self.saved

    def test_identical_records_pass(self):
        self.assertEqual(rq.compare_records(self.env, self.f1), [])

    def test_changed_record_fails(self):
        write(os.path.join(self.env, "sta_results.tsv"), "WS\tc\tmax\t-2\n")
        self.assertIn("sta_results.tsv differs from F1", rq.compare_records(self.env, self.f1))

    def test_missing_or_extra_record_fails(self):
        os.remove(os.path.join(self.env, "expanded.sdc"))
        write(os.path.join(self.env, "extra.rpt"), "x")
        problems = rq.compare_records(self.env, self.f1)
        self.assertTrue(any("record file set differs" in p for p in problems))
        self.assertTrue(any("expanded.sdc sha256" in p for p in problems))

    def test_frozen_inputs(self):
        case = os.path.join(self.tmp.name, "case")
        for rel in rq.FROZEN_FROM_F1:
            write(os.path.join(case, rel), rel)
        sums = os.path.join(self.tmp.name, "f1.sha256")
        write(sums, "".join(f"{rq.sha256(os.path.join(case, r))}  {r}\n" for r in rq.FROZEN_FROM_F1))
        self.assertEqual(rq.check_frozen_inputs(case, sums), [])
        write(os.path.join(case, "sdc/case01_sdc.tcl"), "edited")
        self.assertEqual(len(rq.check_frozen_inputs(case, sums)), 1)


class TestExecutorAndLimits(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="rq_exec_")
        self.addCleanup(self.tmp.cleanup)
        self.diag, self.case = os.path.join(self.tmp.name, "diag"), os.path.join(self.tmp.name, "case")
        for rel in rq.EXECUTOR:
            write(rq.executor_path(rel, self.diag, self.case), rel)
        self.manifest = os.path.join(self.tmp.name, "executor.sha256")
        write(self.manifest, "".join(f"{h}  {r}\n" for r, h in rq.executor_hashes(self.diag, self.case).items()))

    def test_registered_executor_passes(self):
        self.assertEqual(rq.executor_problems(self.manifest, self.diag, self.case), [])

    def test_changed_or_missing_manifest_refused(self):
        write(rq.executor_path("rules/allow_query.txt", self.diag, self.case), "exec\n")
        self.assertEqual(len(rq.executor_problems(self.manifest, self.diag, self.case)), 1)
        self.assertEqual(len(rq.executor_problems(self.manifest + ".x", self.diag, self.case)), 1)

    def test_manifest_committed_and_unchanged_since_tag(self):
        repo = self.tmp.name
        git = lambda *a: subprocess.run(["git", "-C", repo] + list(a), capture_output=True, check=True)
        git("init", "-q")
        git("config", "user.email", "t@example.org")
        git("config", "user.name", "t")
        self.assertFalse(rq.manifest_committed(self.manifest, repo))                # not tracked
        git("add", self.manifest)
        git("commit", "-q", "-m", "manifest")
        self.assertTrue(rq.manifest_committed(self.manifest, repo))                 # committed, no tag yet
        git("tag", rq.PREREG_TAG)
        self.assertTrue(rq.manifest_committed(self.manifest, repo))
        write(self.manifest, "changed\n")
        self.assertFalse(rq.manifest_committed(self.manifest, repo))                # differs from HEAD
        git("commit", "-q", "-am", "re-register the executor after the tag")
        self.assertFalse(rq.manifest_committed(self.manifest, repo))                # changed since the tag
        self.assertEqual(len(rq.git_head(repo)), 40)

    def script(self, name, text):
        path = os.path.join(self.tmp.name, name)
        write(path, text)
        return path

    def test_wall_clock_limit_kills(self):
        pidfile = os.path.join(self.tmp.name, "s.pid")
        t0 = time.monotonic()
        rc, stop = rq.run_limited([sys.executable, self.script("sleeper.py", SLEEPER), pidfile],
                                  os.path.join(self.tmp.name, "l.log"), os.environ, self.tmp.name, timeout=2)
        self.assertEqual((rc, stop), (None, "timed_out"))
        self.assertLess(time.monotonic() - t0, 10)
        self.assertTrue(gone(read_pid(pidfile)))

    def test_log_size_limit_kills(self):
        pidfile, log = os.path.join(self.tmp.name, "w.pid"), os.path.join(self.tmp.name, "y.log")
        rc, stop = rq.run_limited([sys.executable, self.script("writer.py", BOUNDED_WRITER), pidfile], log,
                                  os.environ, self.tmp.name, timeout=30, max_bytes=1000)
        self.assertEqual((rc, stop), (None, "output_limit"))
        self.assertTrue(gone(read_pid(pidfile)))
        self.assertLess(os.path.getsize(log), 3_000_000)     # stopped within about one poll, not left writing

    def test_whole_process_tree_is_killed(self):
        pidfile = os.path.join(self.tmp.name, "g.pid")
        rc, stop = rq.run_limited([sys.executable, self.script("tree.py", TREE), pidfile,
                                   self.script("sleeper.py", SLEEPER)],
                                  os.path.join(self.tmp.name, "t.log"), os.environ, self.tmp.name, timeout=4)
        self.assertEqual((rc, stop), (None, "timed_out"))
        self.assertTrue(gone(read_pid(pidfile)))              # the grandchild, not only the direct child

    def test_normal_exit(self):
        self.assertEqual(rq.run_limited([sys.executable, "-c", "pass"], os.path.join(self.tmp.name, "t.log"),
                                        os.environ, self.tmp.name), (0, None))


if __name__ == "__main__":
    unittest.main()
