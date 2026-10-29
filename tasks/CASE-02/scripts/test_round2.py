"""Unit tests of extract_queries.py, build_results.py and collect_runs.py for CASE-02 (protocol v0.3 sections 6.3,
6.4; impl_plan Task 5). Run in WSL from tasks/CASE-02/scripts: python3 -B -m unittest -v test_round2"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "scripts")
              if os.path.basename(os.path.dirname(HERE)) == "impl" else HERE)
import c2paths  # noqa: E402
import budget  # noqa: E402
import build_results  # noqa: E402
import collect_runs  # noqa: E402
import contract  # noqa: E402
import extract_queries as eq  # noqa: E402

CMDS = eq.commands()

ANSWER = """一、观察
- R1 和 R2 的 summary 不同
四、检查请求
1. 对 R2 执行（优先级 1）：
```tcl
check_setup -verbose
```
2. `report_checks -from [get_ports {in_b[0]}] -scene ss_n40C_1v60 -unconstrained`
3. 只对 R1：`report_arrival -scene ss_n40C_1v60 [get_ports {in_a[0]}]`
4. 两组都执行，第 3 优先：
```tcl
# 这段注释提到 R1 但不算
foreach p [all_inputs -no_clocks] { puts [get_full_name $p] }
```
5. 请把网表给我看一下
五、其他
"""


def many_requests(n):
    body = "\n".join(f"{i}. `report_units`" for i in range(1, n + 1))
    return "一、观察\n四、检查请求\n" + body + "\n五、其他\n"


class TestExtract(unittest.TestCase):
    def test_extract_ctx_scope_item_level(self):
        units = eq.extract(ANSWER, CMDS)
        by = {u["qid_n"]: u for u in units}
        self.assertEqual(by[1]["ctx_requested"], "R2")      # item prose names R2, code block has none
        self.assertEqual(by[2]["ctx_requested"], "both")
        self.assertEqual(by[3]["ctx_requested"], "R1")
        self.assertEqual(by[4]["ctx_requested"], "both")    # comment inside the block does not count; prose says both

    def test_extract_comment_not_counted(self):
        text = "四、检查请求\n1. 查询：\n```tcl\n# R2 only in a comment\nreport_units\n```\n五、\n"
        u = eq.extract(text, CMDS)[0]
        self.assertEqual(u["ctx_requested"], "both")

    def test_extract_priority_declared(self):
        units = eq.extract(ANSWER, CMDS)
        by = {u["qid_n"]: u for u in units}
        self.assertEqual(by[1]["priority"], 1)
        self.assertIsNone(by[2]["priority"])
        self.assertEqual(by[4]["priority"], 3)

    def test_extract_kinds_and_text_units(self):
        units = eq.extract(ANSWER, CMDS)
        self.assertEqual([u["kind"] for u in units], ["codeblock", "inline", "inline", "codeblock", "text"])
        self.assertEqual(units[4]["fixed_code"], eq.NOT_RUN)

    def test_extract_13th_over_limit(self):
        units = eq.extract(many_requests(14), CMDS)
        self.assertEqual(len(units), 14)
        self.assertFalse(units[11]["over_limit"])
        self.assertTrue(units[12]["over_limit"])
        self.assertEqual(units[12]["fixed_code"], eq.OVER_LIMIT)
        self.assertEqual(units[13]["fixed_code"], eq.OVER_LIMIT)

    def test_qid_numeric_order(self):
        self.assertEqual(sorted(["A10", "A2", "A1"], key=eq.qid_key), ["A1", "A2", "A10"])


class TmpRound2:
    """A temporary round2/ + queries/round2/ tree for build_results / collect tests."""

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="r2_", dir=c2paths.RUNS)
        self.round2 = os.path.join(self.tmp, "round2")
        self.queries = os.path.join(self.tmp, "queries", "round2")
        os.makedirs(os.path.join(self.round2, "q"))
        os.makedirs(self.queries)
        return self

    def __exit__(self, *a):
        shutil.rmtree(self.tmp)

    def unit(self, qid, text="check_setup -verbose\n"):
        with open(os.path.join(self.round2, "q", f"{qid}.tcl"), "w", encoding="utf-8") as f:
            f.write(text)
        return f"round2/q/{qid}.tcl"

    def run(self, ident, returned="Warning: x\n", result=None, calls=None):
        d = os.path.join(self.queries, ident)
        os.makedirs(d)
        with open(os.path.join(d, "query_return.txt"), "w", encoding="utf-8") as f:
            f.write(returned)
        r = {"exec_type": "原上下文", "exec_result": "完成", "attribution": "-", "env_relation_ok": True,
             "output_attr": {"empty": False, "truncated": False}, "abnormal": "-", "raw_lines": 1, "returned_lines": 1,
             "returned_bytes": len(returned.encode())}
        r.update(result or {})
        with open(os.path.join(d, "result.json"), "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False)
        with open(os.path.join(d, "calls.jsonl"), "w", encoding="utf-8") as f:
            for c in calls or []:
                f.write(json.dumps(c) + "\n")
        return ident

    def translation(self, rows):
        with open(os.path.join(self.round2, "translation.tsv"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\t".join(build_results.COLUMNS) + "\n")
            for r in rows:
                f.write("\t".join(r.get(k, "-") for k in build_results.COLUMNS) + "\n")


def c(total=100000, ratio=1.0):
    with open(os.path.join(c2paths.RULES, "contract.json"), encoding="utf-8") as f:
        d = json.load(f)
    d["total_budget_tokens"], d["token_bytes_ratio"] = total, ratio
    return contract.from_dict(d)


class TestResults(unittest.TestCase):
    def test_results_end_with_statement(self):
        with TmpRound2() as t:
            q = t.unit("A1")
            r1 = t.run("A1_R1")
            r2 = t.run("A1_R2")
            t.translation([{"code": "A", "qid": "A1", "ctx": "R1", "original": q, "executed": q, "collected": r1},
                           {"code": "A", "qid": "A1", "ctx": "R2", "original": q, "executed": q, "collected": r2}])
            text, alloc = build_results.render("A", c(), case=t.tmp)
            self.assertIn("### 查询 A1（R1）", text)
            self.assertIn("### 查询 A1（R2）", text)
            self.assertIn("归因：-", text)
            self.assertTrue(text.rstrip().endswith("不是查询失败。"))
            self.assertEqual(alloc["dropped"], [])

    def test_results_dropped_instance_one_line_marker(self):
        with TmpRound2() as t:
            q = t.unit("A1")
            r1 = t.run("A1_R1", returned="x" * 300 + "\n")
            r2 = t.run("A1_R2", returned="y" * 300 + "\n")
            t.translation([{"code": "A", "qid": "A1", "ctx": "R1", "original": q, "executed": q, "collected": r1},
                           {"code": "A", "qid": "A1", "ctx": "R2", "original": q, "executed": q, "collected": r2}])
            text, alloc = build_results.render("A", c(total=1200, ratio=1.0), case=t.tmp)
            self.assertIn("[未交还：超出总预算，见文末预算账单]", text)
            self.assertNotIn("y" * 300, text)
            self.assertIn("x" * 300, text)
            self.assertEqual(alloc["dropped"][0]["ctx"], "R2")

    def test_results_no_query_still_statement(self):
        with TmpRound2() as t:
            t.translation([])
            text, alloc = build_results.render("B", c(), case=t.tmp)
            self.assertTrue(text.startswith(build_results.NO_QUERY.rstrip()))
            self.assertIn("预算账单", text)
            self.assertIn("③ 未交还的实例：（无）", text)

    def test_results_invalid_env_fixed_text(self):
        with TmpRound2() as t:
            q = t.unit("A1")
            r1 = t.run("A1_R1", result={"env_relation_ok": False, "attribution": "执行器或环境问题"})
            t.translation([{"code": "A", "qid": "A1", "ctx": "R1", "original": q, "executed": q, "collected": r1,
                            "attribution": "执行器或环境问题"}])
            text, _ = build_results.render("A", c(), case=t.tmp)
            self.assertIn("该次执行的环境核对未通过，结果不交还", text)
            self.assertNotIn("Warning: x", text)

    def test_results_fixed_code_unit(self):
        with TmpRound2() as t:
            with open(os.path.join(t.round2, "q", "A5.txt"), "w", encoding="utf-8") as f:
                f.write("请把网表给我看一下\n")
            t.translation([{"code": "A", "qid": "A5", "ctx": "both", "original": "round2/q/A5.txt", "executed": "-",
                            "fixed_code": eq.NOT_RUN}])
            text, _ = build_results.render("A", c(), case=t.tmp)
            self.assertIn(eq.NOT_RUN, text)

    def test_rendered_prompt_within_budget(self):
        with TmpRound2() as t:
            q = t.unit("A1")
            r1 = t.run("A1_R1", returned="x" * 100 + "\n")
            t.translation([{"code": "A", "qid": "A1", "ctx": "R1", "original": q, "executed": q, "collected": r1}])
            text, alloc = build_results.render("A", c(total=100000, ratio=1.0), case=t.tmp)
            chk = build_results.check_budget(text, alloc, c(total=100000, ratio=1.0))
            self.assertTrue(chk["ok"])
            self.assertEqual(chk["rendered_bytes"], len(text.encode("utf-8")))
            chk2 = build_results.check_budget(text, alloc, c(total=10, ratio=1.0))
            self.assertFalse(chk2["ok"])


class TestCollect(unittest.TestCase):
    def make_run(self, root, ident, env_ok=True, selftest=False):
        d = os.path.join(root, ident)
        os.makedirs(d)
        for name in collect_runs.FILES:
            with open(os.path.join(d, name), "w") as f:
                f.write(name + "\n")
        r = {"id": "A1", "ctx": "R1", "version": "missing", "selftest": selftest, "env_relation_ok": env_ok,
             "executor_committed": True, "uncommitted_ok": False, "attribution": "-"}
        with open(os.path.join(d, "result.json"), "w") as f:
            json.dump(r, f)
        return d

    def test_collect_strips_version_and_keeps_failed_run_flagged(self):
        tmp = tempfile.mkdtemp(prefix="col_", dir=c2paths.RUNS)
        try:
            ok = self.make_run(tmp, "run_ok")
            bad = self.make_run(tmp, "run_bad", env_ok=False)
            dest = os.path.join(tmp, "queries")
            collect_runs.collect("round2", [ok, bad], dest_root=dest)
            with open(os.path.join(dest, "round2", "A1_R1", "result.json")) as f:
                r = json.load(f)
            self.assertNotIn("version", r)
            self.assertTrue(r["env_relation_ok"])
            bad_dir = [d for d in os.listdir(os.path.join(dest, "round2")) if d.startswith("A1_R1")]
            self.assertEqual(len(bad_dir), 2)
            self.assertTrue(os.path.exists(os.path.join(dest, "round2", "SHA256SUMS")))
        finally:
            shutil.rmtree(tmp)

    def test_collect_refuses_selftest(self):
        tmp = tempfile.mkdtemp(prefix="col_", dir=c2paths.RUNS)
        try:
            st = self.make_run(tmp, "run_st", selftest=True)
            with self.assertRaises(SystemExit):
                collect_runs.collect("round2", [st], dest_root=os.path.join(tmp, "queries"))
        finally:
            shutil.rmtree(tmp)


class TestR6Window(unittest.TestCase):
    """CASE02_R6 Q3 ruling: check requests are taken only from the 120-line core window of the answer (the same
    window the core scoring reads); requests after it are recorded as dropped, not executed."""

    def text(self):
        filler = "\n".join(f"- 观察 {i}" for i in range(2, 118))               # lines 2..117
        return "一、观察\n" + filler + "\n四、检查请求\n1. `report_units`\n2. `report_units`\n3. `report_units`\n五、其他\n"

    def test_requests_outside_the_window_are_not_extracted(self):
        units = [u for u in eq.extract(self.text(), CMDS) if u["kind"] != "text"]
        self.assertEqual(len(units), 2)
        self.assertEqual(len([u for u in eq.extract(self.text(), CMDS, window=False) if u["kind"] != "text"]), 3)

    def test_dropped_lines_reported(self):
        self.assertEqual(eq.outside_window(self.text()), 2)


if __name__ == "__main__":
    unittest.main()


class TestR6Visibility(unittest.TestCase):
    def test_visibility_table_marks_dropped_instances(self):
        with TmpRound2() as t:
            q = t.unit("A1")
            r1 = t.run("A1_R1", returned="x" * 300 + "\n")
            r2 = t.run("A1_R2", returned="y" * 300 + "\n")
            t.translation([{"code": "A", "qid": "A1", "ctx": "R1", "original": q, "executed": q, "collected": r1},
                           {"code": "A", "qid": "A1", "ctx": "R2", "original": q, "executed": q, "collected": r2}])
            text, alloc = build_results.render("A", c(total=1200, ratio=1.0), case=t.tmp)
            vis = build_results.visibility(alloc)
            self.assertEqual(vis["A1_R1"]["visible"], True)
            self.assertEqual(vis["A1_R2"]["visible"], False)
            self.assertEqual(vis["A1_R2"]["reason"], "流程限制：总预算")
