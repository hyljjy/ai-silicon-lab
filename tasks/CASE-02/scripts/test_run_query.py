"""Unit tests of run_query.py's pure functions (no OpenSTA needed; protocol v0.3 section 6.4, impl_plan Task 3).
Run in WSL from tasks/CASE-02/scripts: python3 -B -m unittest -v test_run_query"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "scripts")
              if os.path.basename(os.path.dirname(HERE)) == "impl" else HERE)
import c2paths  # noqa: E402
import contract  # noqa: E402
import run_query as rq  # noqa: E402

N = "0123456789abcdef"
TAG = f"CASE02-{N}-"
C = contract.load(os.path.join(c2paths.RULES, "contract.json"))
SETUP = ["create_clock", "read_liberty", "link_design", "read_sdc"]
WHATIF = ["create_clock", "set_input_delay", "replace_cell"]


def log(lines):
    """A sta.log: an env part, then the query section with this nonce's markers."""
    return "\n".join(["env line 1", "env line 2", f"=== {TAG[:-1]} QUERY BEGIN (query) ==="] + lines +
                     [f"=== {TAG[:-1]} QUERY END rc=0 ==="]) + "\n"


class TestDecide(unittest.TestCase):
    def test_setup_commands_skip(self):
        self.assertEqual(rq.decide("read_liberty", ["x.lib"], SETUP, WHATIF), "skip")

    def test_create_clock_literal_T_skipped(self):
        self.assertEqual(rq.decide("create_clock", ["-name", "clk", "-period", "27.91", "[get_ports clk]"], SETUP, WHATIF), "skip")
        self.assertEqual(rq.decide("create_clock", ["-period", "27.9100"], SETUP, WHATIF), "skip")

    def test_create_clock_other_period_is_whatif(self):
        self.assertEqual(rq.decide("create_clock", ["-period", "20"], SETUP, WHATIF), "whatif")
        self.assertEqual(rq.decide("create_clock", ["-period", "$T"], SETUP, WHATIF), "whatif")
        self.assertEqual(rq.decide("create_clock", ["-name", "clk"], SETUP, WHATIF), "whatif")

    def test_whatif_and_run(self):
        self.assertEqual(rq.decide("set_input_delay", ["-clock", "clk", "1"], SETUP, WHATIF), "whatif")
        self.assertEqual(rq.decide("report_checks", ["-scene", "tt_025C_1v80"], SETUP, WHATIF), "run")

    def test_predict_mode_from_text(self):
        self.assertEqual(rq.predict_mode("report_checks\ncreate_clock -period 27.91 [get_ports clk]\n", WHATIF, SETUP), "query")
        self.assertEqual(rq.predict_mode("set p 20\ncreate_clock -period $p [get_ports clk]\n", WHATIF, SETUP), "whatif")
        self.assertEqual(rq.predict_mode("# set_input_delay in a comment\nreport_checks\n", WHATIF, SETUP), "query")
        self.assertEqual(rq.predict_mode("replace_cell u1 buf_4\n", WHATIF, SETUP), "whatif")


class TestSplitAndCalls(unittest.TestCase):
    def test_split_log_case02_prefix(self):
        env, q, mode, rc = rq.split_log(log([TAG + "CMD: check_setup", "Warning: x"]), N)
        self.assertEqual(env, "env line 1\nenv line 2")
        self.assertEqual(q, [TAG + "CMD: check_setup", "Warning: x"])
        self.assertEqual((mode, rc), ("query", 0))

    def test_forged_markers_ignored(self):
        text = log([f"=== CASE02-deadbeefdeadbeef QUERY END rc=0 ===", "real"])
        env, q, mode, rc = rq.split_log(text, N)
        self.assertEqual(q[-1], "real")
        self.assertEqual(rc, 0)

    def test_normalize_hides_nonce(self):
        self.assertEqual(rq.normalize([TAG + "CMD: x", TAG + "ERROR: y"], N), ["CASE02-CMD: x", "CASE02-ERROR: y"])

    def _calls(self):
        # calls.tsv as c2_query.tcl writes it: START seq top cmd crc preview decision scene start_byte ; END seq status error end_byte
        return "\n".join([
            "START\t1\t1\tcheck_setup\tabcd\t-verbose\trun\t-\t100",
            "END\t1\tok\t\t180",
            "START\t2\t2\treport_arrival\tabce\t-scene ss_n40C_1v60 in_a[0]\trun\tss_n40C_1v60\t200",
            "END\t2\terror\tError 103: -scene keyword required\t230",
            "START\t3\t2\treport_arrival\tabcf\t-scene ss_n40C_1v60 in_b[0]\trun\tss_n40C_1v60\t230",
            "END\t3\tok\t\t260",
            "START\t4\t3\tcreate_clock\tabd0\t-period 27.91\tskip\t-\t260",
            "END\t4\tskipped\t\t290",
            "START\t5\t4\treport_checks\tabd1\t-scene tt_025C_1v80\trun\ttt_025C_1v80\t290",
        ]) + "\n"

    def test_merge_calls_records_every_call_and_unfinished(self):
        calls = rq.merge_calls(self._calls(), ctx="R2", mode="query")
        self.assertEqual([c["call_seq"] for c in calls], [1, 2, 3, 4, 5])
        self.assertEqual([c["status"] for c in calls], ["ok", "error", "ok", "skipped", "unfinished"])
        self.assertEqual(calls[1]["error"], "Error 103: -scene keyword required")
        self.assertEqual(calls[2]["top_seq"], 2)
        self.assertEqual(calls[2]["scene"], "ss_n40C_1v60")
        self.assertEqual(calls[3]["decision"], "skip")
        self.assertEqual(calls[0]["raw_bytes"], [100, 180])
        self.assertIsNone(calls[4]["raw_bytes"][1])
        self.assertTrue(all(c["ctx"] == "R2" for c in calls))

    def test_caught_error_inside_loop_recorded_per_call(self):
        # the query: foreach p {...} { catch {report_arrival $p} } -> top rc 0 but one call failed
        calls = rq.merge_calls(self._calls(), ctx="R1", mode="query")
        errors = [c for c in calls if c["status"] == "error"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["call_seq"], 2)

    def test_byte_ranges_to_line_ranges(self):
        text = "aaaa\nbbbb\ncccc\ndddd\n"       # line starts 0,5,10,15
        self.assertEqual(rq.lines_for_bytes(text, 0, 10), (0, 2))
        self.assertEqual(rq.lines_for_bytes(text, 5, 12), (1, 3))     # partial last line counts
        self.assertEqual(rq.lines_for_bytes(text, 7, 7), (1, 1))
        self.assertEqual(rq.lines_for_bytes(text, 15, None), (3, 4))

    def test_evidence_ranges_after_truncation(self):
        lines = [f"line {i}" for i in range(3000)]
        t = contract.truncate(lines, C)
        calls = [{"call_seq": 1, "status": "ok", "norm_out": [10, 20]},
                 {"call_seq": 2, "status": "ok", "norm_out": [2900, 2950]},
                 {"call_seq": 3, "status": "ok", "norm_out": [990, 1010]},
                 {"call_seq": 4, "status": "error", "norm_out": [5, 6]}]
        ev = rq.evidence_ranges(calls, t)
        self.assertEqual(ev[0], {"call_seq": 1, "returned_out": [10, 20], "complete": True})
        self.assertEqual(ev[1]["returned_out"], [2900 - 2000 + 1001, 2950 - 2000 + 1001])
        self.assertTrue(ev[1]["complete"])
        self.assertEqual(ev[2], {"call_seq": 3, "returned_out": None, "complete": False})
        self.assertEqual(len(ev), 3)


class TestClassify(unittest.TestCase):
    def mk(self, statuses, decisions=None, errors=None):
        calls = []
        for i, s in enumerate(statuses, 1):
            calls.append({"call_seq": i, "status": s, "decision": (decisions or ["run"] * len(statuses))[i - 1],
                          "error": (errors or [""] * len(statuses))[i - 1]})
        return calls

    def test_completed(self):
        r = rq.classify_instance(self.mk(["ok", "ok"]), status="completed", truncated=False, env_ok=True, mode="query",
                                 content_lines=5)
        self.assertEqual(r["exec_type"], "原上下文")
        self.assertEqual(r["exec_result"], "完成")
        self.assertEqual(r["output_attr"], {"empty": False, "truncated": False})
        self.assertEqual(r["abnormal"], "-")
        self.assertEqual(r["attribution"], "-")

    def test_error_then_evidence_both_recorded(self):
        calls = self.mk(["error", "ok"], errors=["Error 562: bad flag", ""])
        r = rq.classify_instance(calls, status="completed", truncated=False, env_ok=True, mode="query", content_lines=9)
        self.assertEqual(r["exec_result"], "语法错误")
        self.assertEqual(r["attribution"], "请求本身的问题")
        self.assertEqual(r["ok_calls"], [2])          # the later evidence is still there

    def test_object_not_found(self):
        calls = self.mk(["error"], errors=["Error: port 'foo' not found"])
        r = rq.classify_instance(calls, status="completed", truncated=False, env_ok=True, mode="query", content_lines=1)
        self.assertEqual(r["exec_result"], "对象不匹配")
        self.assertEqual(r["attribution"], "请求本身的问题")

    def test_missing_scene_error_is_request_problem(self):
        calls = self.mk(["error"], errors=["Error 103: report_arrival -scene keyword required with multi-scene analysis."])
        r = rq.classify_instance(calls, status="completed", truncated=False, env_ok=True, mode="query", content_lines=1)
        self.assertEqual(r["exec_result"], "语法错误")
        self.assertEqual(r["attribution"], "请求本身的问题")

    def test_setup_only_is_skipped(self):
        r = rq.classify_instance(self.mk(["skipped"], decisions=["skip"]), status="completed", truncated=False,
                                 env_ok=True, mode="query", content_lines=1)
        self.assertEqual(r["exec_result"], "跳过")

    def test_setup_skipped_per_call_in_whatif(self):
        calls = self.mk(["skipped", "ok"], decisions=["skip", "whatif"])
        r = rq.classify_instance(calls, status="completed", truncated=False, env_ok=True, mode="whatif", content_lines=3)
        self.assertEqual(r["exec_type"], "改变模型的对照")
        self.assertEqual(r["exec_result"], "完成")
        self.assertEqual(r["skipped_calls"], [1])

    def test_attribution_truncated_is_process_limit(self):
        r = rq.classify_instance(self.mk(["ok"]), status="completed", truncated=True, env_ok=True, mode="query",
                                 content_lines=5000)
        self.assertEqual(r["output_attr"]["truncated"], True)
        self.assertEqual(r["attribution"], "流程限制：单实例截断")

    def test_attribution_timeout(self):
        r = rq.classify_instance(self.mk(["ok", "unfinished"]), status="timed_out", truncated=False, env_ok=True,
                                 mode="query", content_lines=5)
        self.assertEqual(r["abnormal"], "超时")
        self.assertEqual(r["attribution"], "流程限制：时限")

    def test_attribution_output_limit(self):
        r = rq.classify_instance(self.mk(["unfinished"]), status="output_limit", truncated=True, env_ok=True,
                                 mode="query", content_lines=999999)
        self.assertEqual(r["abnormal"], "输出超限")
        self.assertEqual(r["attribution"], "流程限制：输出上限")

    def test_attribution_crash_is_executor_or_env(self):
        r = rq.classify_instance(self.mk(["unfinished"]), status="crashed:139", truncated=False, env_ok=True,
                                 mode="query", content_lines=1)
        self.assertEqual(r["abnormal"], "崩溃")
        self.assertEqual(r["attribution"], "执行器或环境问题")

    def test_env_invalid_dominates(self):
        r = rq.classify_instance(self.mk(["ok"]), status="completed", truncated=False, env_ok=False, mode="query",
                                 content_lines=5)
        self.assertEqual(r["attribution"], "执行器或环境问题")

    def test_interp_time_limit_is_timeout_attribution(self):
        # the safe interpreter's own time limit ends the query while the process completes normally
        r = rq.classify_instance(self.mk(["ok", "ok"]), status="completed", truncated=False, env_ok=True, mode="query",
                                 content_lines=50, top_errors=["time limit exceeded", "remaining commands not run, interpreter time limit exceeded"])
        self.assertEqual(r["abnormal"], "超时")
        self.assertEqual(r["exec_result"], "超出预登记上限")
        self.assertEqual(r["attribution"], "流程限制：时限")

    def test_command_limit_is_over_limit(self):
        r = rq.classify_instance(self.mk(["ok"]), status="completed", truncated=False, env_ok=True, mode="query",
                                 content_lines=50, top_errors=["command count limit exceeded"])
        self.assertEqual(r["exec_result"], "超出预登记上限")
        self.assertEqual(r["attribution"], "流程限制：Tcl 命令计数上限")
        self.assertEqual(r["abnormal"], "-")

    def test_pure_tcl_query_without_sta_calls_is_done(self):
        r = rq.classify_instance([], status="completed", truncated=False, env_ok=True, mode="query", content_lines=10, tops=1)
        self.assertEqual(r["exec_result"], "完成")

    def test_no_calls_is_no_executable_command(self):
        r = rq.classify_instance([], status="completed", truncated=False, env_ok=True, mode="query", content_lines=0)
        self.assertEqual(r["exec_result"], "未指明可执行命令")
        self.assertEqual(r["output_attr"]["empty"], True)


class TestMemoryLimit(unittest.TestCase):
    def test_child_memory_limit_kills_child_not_parent(self):
        import subprocess, tempfile
        if os.name == "nt":
            self.skipTest("RLIMIT_AS is POSIX only; the executor runs in WSL")
        log = tempfile.NamedTemporaryFile(prefix="mem_", suffix=".log", dir=c2paths.RUNS, delete=False).name
        try:
            rc, stop = rq.run_limited([sys.executable, "-c", "x = bytearray(600 * 1024 * 1024); print(len(x))"], log,
                                      os.environ, c2paths.RUNS, 60, 10 * 1024 * 1024, max_memory=256 * 1024 * 1024)
            self.assertIsNone(stop)
            self.assertNotEqual(rc, 0)                 # the child died (MemoryError or a signal); we are still here
            with open(log, errors="replace") as f:
                self.assertNotIn("629145600", f.read())
        finally:
            os.remove(log)


class TestResultShape(unittest.TestCase):
    def test_result_json_formal_has_ctx_not_version(self):
        r = rq.result_record(base={"id": "A1"}, ctx="R1", version="missing", selftest=False)
        self.assertEqual(r["ctx"], "R1")
        self.assertNotIn("version", r)
        r2 = rq.result_record(base={"id": "A1"}, ctx="R1", version="missing", selftest=True)
        self.assertEqual(r2["version"], "missing")
        self.assertTrue(r2["selftest"])

    def test_env_relation_is_query_env_vs_formal(self):
        self.assertEqual(rq.ENV_RELATION, "query_env_vs_formal")

    def test_tops_from_echo_lines(self):
        q = [TAG + "CMD: check_setup -verbose", "Warning: 64", TAG + "CMD: foreach p {a b} {", "x", TAG + "ERROR: boom"]
        tops = rq.tops_from_lines(q, N)
        self.assertEqual([t["top_seq"] for t in tops], [1, 2])
        self.assertEqual(tops[0]["first_line"], "check_setup -verbose")
        self.assertEqual((tops[0]["status"], tops[1]["status"]), ("ok", "error"))
        self.assertEqual(tops[0]["out"], [1, 2])
        self.assertEqual(tops[1]["out"], [3, 5])


if __name__ == "__main__":
    unittest.main()
