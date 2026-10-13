"""Unit tests of collect_runs.py and build_results.py (temporary directories only).
Run: python3 -B -m unittest test_collect_results"""
import json
import os
import tempfile
import unittest

import build_results as br
import collect_runs as cr


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def fake_run(case, name, qid, env_ok=True, codes=("已执行",), out="out\n", strict=False, log_ok=True,
             committed=True, selftest=False):
    rd = os.path.join(case, "runs", name)
    for f in cr.FILES:
        write(os.path.join(rd, f), f + "\n")
    write(os.path.join(rd, "query_return.txt"), out)
    write(os.path.join(rd, "result.json"), json.dumps({"id": qid, "env_ok": env_ok, "codes": list(codes),
                                                       "strict_log": strict, "query_log_ok": log_ok,
                                                       "executor_committed": committed, "selftest": selftest}))
    return rd


class TestCollect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="collect_test_")
        self.addCleanup(self.tmp.cleanup)
        self.case, self.diag = self.tmp.name, os.path.join(self.tmp.name, "diag")

    def test_uncommitted_executor_or_selftest_refused(self):
        for kw in ({"committed": False}, {"selftest": True}):
            rd = fake_run(self.case, "r-" + next(iter(kw)), "q9", **kw)
            with self.assertRaises(SystemExit):
                cr.collect("base", [rd], self.case, self.diag)

    def test_collect_and_sums(self):
        rd = fake_run(self.case, "r1", "base_B01")
        n = cr.collect("base", [rd], self.case, self.diag)
        self.assertEqual(n, len(cr.FILES))
        with open(os.path.join(self.diag, "queries", "base", "SHA256SUMS")) as f:
            self.assertEqual(len(f.read().splitlines()), len(cr.FILES))

    def test_env_fail_refused(self):
        rd = fake_run(self.case, "r2", "base_B02", env_ok=False)
        with self.assertRaises(SystemExit):
            cr.collect("base", [rd], self.case, self.diag)

    def test_strict_run_with_dirty_log_refused(self):
        with self.assertRaises(SystemExit):
            cr.collect("base", [fake_run(self.case, "r5", "b", strict=True, log_ok=False)], self.case, self.diag)
        cr.collect("round2", [fake_run(self.case, "r6", "q", strict=False, log_ok=False)], self.case, self.diag)

    def test_same_id_different_content_refused(self):
        cr.collect("base", [fake_run(self.case, "r3", "x")], self.case, self.diag)
        with self.assertRaises(SystemExit):
            cr.collect("base", [fake_run(self.case, "r4", "x", out="other\n")], self.case, self.diag)


class TestResults(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="results_test_")
        self.addCleanup(self.tmp.cleanup)
        self.diag = self.tmp.name
        write(os.path.join(self.diag, "round2", "q", "A1.tcl"), "report_checks -corner ss\n")
        write(os.path.join(self.diag, "round2", "q", "A1x.tcl"), "report_checks -scene ss\n")
        write(os.path.join(self.diag, "round2", "q", "A2.tcl"), "查一下扇出\n")
        write(os.path.join(self.diag, "round2", "q", "A3.tcl"), "set_load 1 x\n")
        for qid, codes in (("r2_A1", ["已执行"]), ("r2_A3", [br.WHATIF])):
            write(os.path.join(self.diag, "queries", "round2", qid, "result.json"), json.dumps({"codes": codes}))
            write(os.path.join(self.diag, "queries", "round2", qid, "query_return.txt"), f"output of {qid}\n")
        write(os.path.join(self.diag, "round2", "translation.tsv"),
              "# reviewed\n" + "\t".join(br.COLUMNS) + "\n"
              "A\tQ1\tround2/q/A1.tcl\tround2/q/A1x.tcl\t-corner→-scene\tr2_A1\t-\n"
              "A\tQ2\tround2/q/A2.tcl\t-\t-\t-\t未执行：未指明可执行的对象或命令\n"
              "A\tQ3\tround2/q/A3.tcl\tround2/q/A3.tcl\t-\tr2_A3\t-\n")

    def test_render(self):
        text = br.render("A", self.diag)
        self.assertEqual(text.count("### 查询 "), 3)
        self.assertIn("机械改写：-corner→-scene", text)
        self.assertIn("output of r2_A1", text)
        self.assertIn("结果代码：未执行：未指明可执行的对象或命令", text)
        self.assertIn("结果只作对照", text)

    def test_no_query(self):
        self.assertEqual(br.render("B", self.diag), br.NO_QUERY)


if __name__ == "__main__":
    unittest.main()
