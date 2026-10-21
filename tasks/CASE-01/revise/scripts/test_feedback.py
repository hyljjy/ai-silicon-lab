"""Tests for feedback (round-2 feedback of CASE-01 stage B, Task 8, protocol section 11).
Run per module, never with discover. Every test works in a temporary git repository under tasks/CASE-01/runs/ and a
temporary sealed directory; the real revise/prompts and the real sealed directory are never written. The templates
are the real revise/prompts/feedback/ files (read only)."""
import json
import os
import re
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

import feedback
import mapping
import revpaths as rp
from test_stops import git

RUNS = os.path.join(rp.CASE, "runs")
MODELS = ["claude-opus-5-5", "k3[1M]", "deepseek-v4-pro[1M]"]
CORNERS = ("ff_100C_1v95", "ff_n40C_1v95", "ss_100C_1v60", "ss_n40C_1v60", "tt_025C_1v80", "tt_100C_1v80")
GATE_RULES_MD = """# 合同门槛规则（测试夹具，原文取自规程 §7.2）

| 编号 | 规则原文 | 性质 |
|---|---|---|
| G1 | 模块名 `dot4sat`，端口集合与合同第 1 节完全一致：名称、方向、位宽，不多不少 | 合同要求 |
| G2 | 不使用 plusarg、文件读写、shell、波形转储类系统任务，不用 `` `include `` | 合同要求 |
| G3 | 文件中只有一个模块 | 附加提交格式限制 |
| G4 | 不用 `parameter`（可以用 `localparam`） | 附加提交格式限制 |
| G5 | 不用任何反引号编译指令 | 附加提交格式限制 |
| G6 | 时序 always 块的事件控制恰好是 `@(posedge clk)`；不用 `initial`、`#` 延时、`negedge` | 附加提交格式限制 |
| G7 | 标识符 `clk` 只出现在端口列表、端口声明和 `posedge clk` 事件控制中 | 附加提交格式限制 |
| G8 | `DECLARED_L` 在 1..3 之间 | `config/f1.cfg` 的 L_max |
| unrecognized | 门槛无法识别 | 门槛无法识别 |
"""


def wbytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def wtext(path, text):
    wbytes(path, text.encode("utf-8"))


def wjson(path, obj):
    wtext(path, json.dumps(obj, indent=1, ensure_ascii=False) + "\n")


def cells(numeric_shift="0"):
    """compare cells list: 6 corners x {setup, hold} x {global, in2reg, reg2reg, reg2out}; reg2reg not_applicable."""
    out = []
    for i, c in enumerate(CORNERS):
        for chk in ("setup", "hold"):
            base = (-4 if chk == "setup" else 0) + i
            for scope in ("global", "in2reg", "reg2reg", "reg2out"):
                if scope == "reg2reg":
                    cand = {"slack": "not_applicable", "start": "not_applicable", "end": "not_applicable"}
                else:
                    off = {"global": "0.1234565", "in2reg": "0.1234565", "reg2out": "1.5"}[scope]
                    cand = {"slack": format(Decimal(base) + Decimal(off), "f"),
                            "start": f"in_b[{i}]" if scope != "reg2out" else f"_{i}_/Q",
                            "end": f"_{i}_/D" if scope != "reg2out" else "out_data[0]"}
                out.append({"corner": c, "check": chk, "scope": scope, "base": cand, "cand": cand,
                            "delta": "0", "change": "same", "same_path": True})
    return out


class Base(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="feedback_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.repo = os.path.join(self.tmp.name, "repo")
        self.sealed = os.path.join(self.tmp.name, "sealed")
        os.makedirs(self.repo)
        git(self.repo, "init", "-q", ".")
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "core.autocrlf", "false")
        self.case = os.path.join(self.repo, "tasks", "CASE-01")
        self.revise = os.path.join(self.case, "revise")
        os.makedirs(self.revise)
        wtext(os.path.join(self.repo, "README"), "temp\n")
        git(self.repo, "add", "README")
        git(self.repo, "commit", "-q", "-m", "init")
        p = mock.patch.object(mapping, "SEALED", os.path.join(self.tmp.name, "sealed-default-guard"))
        p.start()
        self.addCleanup(p.stop)
        self.kw = {"case": self.case, "sealed": self.sealed}
        wtext(os.path.join(self.revise, "rules", "gate_rules.md"), GATE_RULES_MD)

    def commit(self, *paths, msg="c"):
        git(self.repo, "add", "--", *paths)
        git(self.repo, "commit", "-q", "-m", msg)

    def commit_codes(self, rounds=(1, 2)):
        out = os.path.join(self.revise, "outputs")
        self.c1 = mapping.commit_codes(1, MODELS, None, revise=self.revise, sealed=self.sealed)
        if 1 in rounds:
            self.commit(os.path.join(out, "r1", "codes.txt"), os.path.join(out, "mapping_r1.sha256"))
        if 2 in rounds and 1 in rounds:
            mapping.commit_codes(2, MODELS, dict(zip(MODELS, self.c1)), revise=self.revise, sealed=self.sealed)
            self.commit(os.path.join(out, "r2", "codes.txt"), os.path.join(out, "mapping_r2.sha256"))
        for c in self.c1:
            self.prompt(c)

    def prompt(self, code, text=None):
        p = os.path.join(self.revise, "prompts", "r1", f"{code}_prompt.md")
        wtext(p, text or f"# 第 1 轮题目 {code}\n\n题目正文。\n")
        self.commit(p)

    # ---- fixtures
    def status(self, code, state, **fields):
        st = {"code": code, "rnd": 1, "state": state, "flags": [], "selected_attempt": None,
              "grade_status": "not_run", "final_line_missing": False, "rtl_sim": "not_run", "gl_sim": "not_run",
              "sta_analysis": "not_run", "checked_rtl": "not_available", "checked_gl": "not_available",
              "area_um2": "not_available", "within_cap": "not_available", "author_veto": False, "declared_L": 1,
              "cfg_L": 1, "prediction_L_mismatch": False, "numeric_target_met": "not_available",
              "eligible_target_met": False, "improvement": "not_applicable", "worst_setup_delta": "not_available",
              "failure_location": "not_run", "attribution": "not_run", "attribution_evidence": [], "inputs": []}
        st.update(fields)
        wjson(os.path.join(self.revise, "results", "r1", code, "status.json"), st)

    def ok_status(self, code, state="eligible_no_gain", **fields):
        base = dict(selected_attempt=1, grade_status="GRADE OK", rtl_sim="pass", gl_sim="pass", sta_analysis="pass",
                    checked_rtl="checked=2856", checked_gl="checked=2856", area_um2="45383.5264", within_cap=True,
                    numeric_target_met=False, failure_location="none", attribution="no_external_evidence")
        base.update(fields)
        self.status(code, state, **base)

    def compare(self, code, worst_setup="-4.189726018044011", worst_hold="0.059112952317363035"):
        doc = {"code": code, "rnd": 1, "hold_note": "x",
               "candidate": {"label": code, "files": {},
                             "summary": {"worst_setup": {"slack": worst_setup, "corner": "ss_n40C_1v60",
                                                         "category": "in2reg"},
                                         "worst_hold": {"slack": worst_hold, "corner": "ff_100C_1v95"}},
                             "extra": {}},
               "cells": cells(), "degradations": []}
        wjson(os.path.join(self.revise, "compare", f"r1_{code}.json"), doc)

    def attempt(self, code, k=1, location="none", steps=None, files=None, run_id="20261101-000000-x",
                exit_code=0, timed_out=False, verdict=None):
        d = os.path.join(self.revise, "results", "r1", code, f"attempt{k}")
        wjson(os.path.join(d, "attempt.json"),
              {"code": code, "rnd": 1, "k": k, "run_id": run_id, "failure_location": location,
               "exit_code": exit_code, "timed_out": timed_out, "final_line": None, "files": []})
        if steps is not None:
            wjson(os.path.join(d, "steps.json"), steps)
        if verdict is not None:
            wjson(os.path.join(d, "verdict.json"), verdict)
        for rel, text in (files or {}).items():
            wtext(os.path.join(d, *rel.split("/")), text)
        return d

    def call(self, code, final, calls=()):
        wjson(os.path.join(self.revise, "outputs", "r1", f"{code}.call.json"),
              {"final": final, "calls": [{"categories": list(c), "delivery": "retry", "retry_allowed": True,
                                          "global_stop": False} for c in calls]})

    def parsed(self, code, status="delivery_fail", reason="no_declared_L", trigger_lines=(), trigger_texts=None):
        texts = [f"answer line {n}" for n in trigger_lines] if trigger_texts is None else list(trigger_texts)
        wjson(os.path.join(self.revise, "outputs", "r1", f"{code}.parsed.json"),
              {"status": status, "reason": reason, "lines": [3, 9], "trigger_lines": list(trigger_lines),
               "trigger_texts": texts, "declared_L": None, "prediction_L_mismatch": False})

    def gate(self, code, hits, passed=False):
        """hits: (rule, line, kind) or (rule, line, kind, text); default text 'rtl line <n>'."""
        wjson(os.path.join(self.revise, "results", "r1", code, "gate.json"),
              {"passed": passed, "hits": [{"rule": h[0], "line": h[1], "kind": h[2],
                                           "text": h[3] if len(h) > 3 else f"rtl line {h[1]}"} for h in hits],
               "yosys_problem": None})

    def render(self, code):
        return feedback.render(code, **self.kw).decode("utf-8")

    def endings(self):
        return feedback.load_endings()


def _steps(fail_step="gl_compile", logs=("gl_sim/compile.log",), problems=()):
    return [{"step": "rtl_compile", "returncode": 0, "timed_out": False, "logs": ["rtl_sim/compile.log"],
             "log_problems": []},
            {"step": fail_step, "returncode": 1, "timed_out": False, "logs": list(logs),
             "log_problems": list(problems)}]


class TestLogSummary(Base):
    def test_log_problems_prefix_survives_truncation(self):
        body = "".join(f"line {i}\n" for i in range(1, 101))
        probs = [f"problem {i}: see /mnt/x/tasks/CASE-01/runs/R1/gl_sim/compile.log" for i in range(1, 51)]
        d = self.attempt("cand_aaaa", location="gl_compile", run_id="R1",
                         steps=_steps(problems=probs), files={"gl_sim/compile.log": body})
        s = feedback.log_summary(d, repo="/mnt/x")
        head, _, tail = s.partition("\n" + feedback.TAIL_HEADER + "\n")
        self.assertTrue(head.startswith(feedback.PROBLEMS_HEADER + "\n"))
        for i in range(1, 51):                                 # the prefix is never cut
            self.assertIn(f"problem {i}: see <RUN>/gl_sim/compile.log", head)
        lines = tail.split("\n")
        self.assertEqual(len(lines), 40)                       # the prefix does not count against the 40 lines
        self.assertEqual(lines[0], "line 61")
        self.assertEqual(lines[-1], "line 100")

    def test_missing_log_placeholder(self):
        d = self.attempt("cand_aaaa", location="gl_compile", steps=_steps(logs=("gl_sim/compile.log", "gl_sim/b.log",
                                                                                  "gl_sim/c.log")),
                         files={"gl_sim/compile.log": "first\n", "gl_sim/c.log": "third\n"})
        s = feedback.log_summary(d, repo="/mnt/x")
        self.assertEqual(s.split("\n"), [feedback.TAIL_HEADER, "first", "<日志未生成：gl_sim/b.log>", "third"])

    def test_outside_steps_uses_stdout_stderr(self):
        for loc in ("outside_steps", "no_final_line"):
            with self.subTest(loc=loc):
                d = self.attempt(f"cand_{loc[:4]}", location=loc, steps=_steps(),
                                 files={"stdout.txt": "RUN_ID=x\nGRADE FAIL: lint\n", "stderr.txt": "err line\n",
                                        "gl_sim/compile.log": "not used\n"})
                s = feedback.log_summary(d, repo="/mnt/x")
                self.assertEqual(s.split("\n"), [feedback.TAIL_HEADER, "RUN_ID=x", "GRADE FAIL: lint", "err line"])
                self.assertNotIn(feedback.PROBLEMS_HEADER, s)
        d = self.attempt("cand_none", location="no_final_line", steps=None, files={})
        self.assertEqual(feedback.log_summary(d, repo="/mnt/x").split("\n"),
                         [feedback.TAIL_HEADER, "<日志未生成：stdout.txt>", "<日志未生成：stderr.txt>"])

    def test_bare_cr_becomes_line_break(self):
        text = "a\r\nprogress 10%\rprogress 100%\nend\n"
        d = self.attempt("cand_aaaa", location="outside_steps", files={"stdout.txt": text, "stderr.txt": "e\r"})
        s = feedback.log_summary(d, repo="/mnt/x")
        self.assertNotIn("\r", s)
        self.assertEqual(s.split("\n"), [feedback.TAIL_HEADER, "a", "progress 10%", "progress 100%", "end", "e"])

    def test_path_normalization_order(self):
        repo = "/mnt/d/study/ai_native_design"
        run = f"{repo}/tasks/CASE-01/runs/20261101-000000-x"
        text = (f"open {run}/gl_sim/net.v\n"
                f"lib {repo}/scripts/grade.py and {run}\n"
                f"tool /home/eda/tools/bin/yosys\n")
        d = self.attempt("cand_aaaa", location="outside_steps", files={"stdout.txt": text, "stderr.txt": ""})
        s = feedback.log_summary(d, repo=repo)
        self.assertIn("open <RUN>/gl_sim/net.v", s)
        self.assertIn("lib <REPO>/scripts/grade.py and <RUN>", s)
        self.assertIn("tool /home/eda/tools/bin/yosys", s)
        self.assertNotIn("<REPO>/tasks/CASE-01/runs", s)


class TestRender(Base):
    def setUp(self):
        super().setUp()
        self.commit_codes()
        self.c = self.c1[0]

    def write_state(self, code, state):
        """Fixture files of one round-1 state (the minimum the field-source table needs)."""
        if state == "unavailable":
            self.call(code, "unavailable", calls=[("模型不符",), ("记录不完整", "退出码非 0")])
            self.status(code, state)
        elif state == "delivery_fail":
            self.call(code, "parse")
            self.parsed(code, reason="conflicting_declared_L", trigger_lines=[7, 4],
                        trigger_texts=["DECLARED_L = 2", "DECLARED_L = 1"])
            self.status(code, state)
        elif state == "gate_reject":
            self.call(code, "parse")
            self.parsed(code, status="ok", reason=None)
            self.gate(code, [("G6", 12, "extra", "  always @(negedge clk) begin")])
            self.status(code, state)
        elif state == "infra_fail":
            self.attempt(code, location="env_snapshot", steps=_steps("env_snapshot", ("env_snapshot.log",)))
            self.status(code, state, selected_attempt=2, grade_status="GRADE FAIL", failure_location="env_snapshot")
        elif state == "grade_fail":
            self.attempt(code, location="gl_compile", steps=_steps(), files={"gl_sim/compile.log": "error x\n"})
            self.status(code, state, selected_attempt=1, grade_status="GRADE FAIL", rtl_sim="pass",
                        gl_sim="fail", checked_rtl="checked=2856", failure_location="gl_compile")
        else:
            self.attempt(code)
            self.compare(code)
            self.ok_status(code, state)

    def test_state_template_mapping(self):
        e = self.endings()
        expect = {"unavailable": ("unavailable", "not_evaluated"), "delivery_fail": ("delivery_fail", "not_evaluated"),
                  "gate_reject": ("gate_reject", "not_evaluated"),
                  "infra_fail": ("infra_fail", "evaluated_no_analysis"),
                  "grade_fail": ("grade_fail", "evaluated_no_analysis"),
                  "ineligible": ("grade_ok", "evaluated_valid"), "eligible_no_gain": ("grade_ok", "evaluated_valid"),
                  "eligible_gain": ("grade_ok", "evaluated_valid")}
        self.assertEqual(set(expect), set(feedback.TEMPLATE_OF))
        for i, (state, (template, ending)) in enumerate(expect.items()):
            with self.subTest(state=state):
                self.assertEqual(feedback.TEMPLATE_OF[state], template)
                code = f"cand_s{i}zz"
                self.prompt(code)
                self.write_state(code, state)
                with open(os.path.join(feedback.TEMPLATES, f"{template}.md"), encoding="utf-8") as f:
                    first = f.read().split("\n", 1)[0]
                with mock.patch.object(mapping, "model_of", return_value="m"), \
                        mock.patch.object(feedback, "_r2_code", return_value="cand_r2zz"):
                    text = self.render(code)
                self.assertTrue(text.startswith(re.split(r"\{", first)[0]))
                # every state, unavailable included: the feedback ends with its ending; the round-1 prompt is
                # never appended (build_prompt places it first in every round-2 prompt)
                self.assertTrue(text.endswith(e[ending] + "\n"), (state, text[-200:]))
                for other in set(e) - {ending}:
                    self.assertNotIn(e[other], text)
                self.assertNotIn(f"# 第 1 轮题目 {code}", text)
        # grade_fail with a valid analysis gets the "valid analysis" ending
        code = "cand_gfok"
        self.attempt(code, location="outside_steps", files={"stdout.txt": "GRADE FAIL: area\n", "stderr.txt": ""})
        self.compare(code)
        self.ok_status(code, "grade_fail", grade_status="GRADE FAIL", failure_location="outside_steps")
        with mock.patch.object(mapping, "model_of", return_value="m"), \
                mock.patch.object(feedback, "_r2_code", return_value="cand_r2zz"):
            text = self.render(code)
        self.assertTrue(text.rstrip("\n").endswith(e["evaluated_valid"]))
        # declined and unknown states are refused
        self.status(self.c, "declined")
        with self.assertRaises(feedback.FeedbackError):
            self.render(self.c)

    def test_fields_per_state(self):
        c0, c1, c2 = self.c1
        # unavailable: categories of every call, then the ending; the round-1 prompt is not appended
        self.write_state(c0, "unavailable")
        t = self.render(c0)
        self.assertEqual(t, "第 1 轮没有收到你的有效答复（原因类别：第 1 次调用：模型不符；第 2 次调用：记录不完整、退出码非 0）。"
                            "\n\n" + self.endings()["not_evaluated"] + "\n")
        self.assertNotIn("第 1 轮题目", t)
        self.assertEqual(set(feedback.ENDING_KEYS), {"evaluated_valid", "evaluated_no_analysis", "not_evaluated"})
        for word in ("rtl_sim", "GRADE", "失败位置"):
            self.assertNotIn(word, t)
        written = os.path.join(self.revise, "prompts", "r2", f"{c0}_feedback.md")
        with open(written, "rb") as f:
            self.assertEqual(f.read().decode("utf-8"), t)
        # delivery_fail (content): the check and the trigger lines; no result fields
        self.write_state(c1, "delivery_fail")
        t = self.render(c1)
        self.assertIn("conflicting_declared_L", t)
        self.assertIn("```text\n第 4 行：DECLARED_L = 1\n第 7 行：DECLARED_L = 2\n```", t)
        for word in ("rtl_sim", "GRADE", "G6"):
            self.assertNotIn(word, t)
        # gate_reject: rule id, rule text from gate_rules.md, RTL line
        self.write_state(c2, "gate_reject")
        t = self.render(c2)
        self.assertIn("G6：时序 always 块的事件控制恰好是 `@(posedge clk)`", t)
        self.assertIn("```text\n第 12 行（G6）：  always @(negedge clk) begin\n```", t)
        self.assertNotIn("rtl_sim", t)
        self.assertNotIn("附加提交格式限制", t)

    def test_fields_per_state_evaluated(self):
        e = self.endings()
        c0, c1, c2 = self.c1
        self.write_state(c0, "infra_fail")
        t = self.render(c0)
        self.assertIn("这不是候选本身的问题", t)
        for word in ("rtl_sim", "失败位置", "GRADE"):
            self.assertNotIn(word, t)
        self.write_state(c1, "grade_fail")
        t = self.render(c1)
        self.assertTrue(t.startswith("GRADE FAIL\n\ngrade_status：GRADE FAIL\n"))
        self.assertNotIn("未取得最终判定行", t)
        self.assertIn("失败位置：步骤 gl_compile", t)
        self.assertIn("```text\n日志末尾摘要（最多 40 个物理行）：\nerror x\n```", t)
        self.assertIn("error x", t)
        self.assertIn("rtl_sim：pass（checked=2856）", t)
        self.assertIn("gl_sim：fail", t)
        self.assertIn("sta_analysis：not_run", t)
        self.assertIn("面积（µm²）：not_available", t)
        self.assertTrue(t.rstrip("\n").endswith(e["evaluated_no_analysis"]))
        self.write_state(c2, "eligible_gain")
        t = self.render(c2)
        self.assertTrue(t.startswith("GRADE OK\n"))
        for want in ("rtl_sim：pass（checked=2856）", "gl_sim：pass（checked=2856）", "sta_analysis：pass",
                     "cfg_L：1", "面积（µm²）：45383.526400", "是否超过面积上限：否",
                     "全局最差 setup slack（ns）：-4.189726（ss_n40C_1v60）",
                     "全局最差 hold slack（ns）：0.059113（ff_100C_1v95）",
                     "| ss_n40C_1v60 | -0.876544 | 3.123457 |",
                     "| ff_100C_1v95 | setup | reg2reg | not_applicable | not_applicable | not_applicable |",
                     "| tt_100C_1v80 | hold | reg2out | 6.500000 | _5_/Q | out_data[0] |"):
            self.assertIn(want, t)
        self.assertNotIn("失败位置", t)
        for banned in ("signoff", "签核", "author_veto", "eligible", "improvement", "合格"):
            self.assertNotIn(banned, t)

    def test_grade_fail_heading_without_final_line(self):
        # RV-03: no final verdict line -> heading '未取得最终判定行' and grade_status indeterminate, same template.
        code = self.c
        self.attempt(code, location="no_final_line", exit_code=137, timed_out=True,
                     files={"stdout.txt": "RUN_ID=x\nstep gl_sim\n", "stderr.txt": "killed\n"})
        self.status(code, "grade_fail", selected_attempt=1, grade_status="indeterminate", final_line_missing=True,
                    rtl_sim="pass", gl_sim="indeterminate", checked_rtl="checked=2856",
                    failure_location="no_final_line")
        t = self.render(code)
        self.assertTrue(t.startswith("未取得最终判定行\n\ngrade_status：indeterminate\n"), t[:80])
        self.assertNotIn("GRADE FAIL", t)
        self.assertIn("失败位置：步骤之外（没有最终判定行；退出码 137，超时 true）", t)
        self.assertIn("日志末尾摘要（最多 40 个物理行）：\nRUN_ID=x\nstep gl_sim\nkilled\n", t)
        self.assertIn("rtl_sim：pass（checked=2856）", t)
        self.assertTrue(t.endswith(self.endings()["evaluated_no_analysis"] + "\n"))
        # the heading follows final_line_missing; a status whose grade_status contradicts it is refused
        for code2, fields in ((self.c1[1], dict(grade_status="GRADE FAIL", final_line_missing=True)),
                              (self.c1[2], dict(grade_status="indeterminate", final_line_missing=False))):
            self.attempt(code2, location="no_final_line", files={"stdout.txt": "x\n", "stderr.txt": ""})
            self.status(code2, "grade_fail", selected_attempt=1, failure_location="no_final_line", **fields)
            with self.assertRaisesRegex(feedback.FeedbackError, "grade_status"):
                self.render(code2)

    def test_log_heading_text(self):
        self.assertEqual(feedback.TAIL_HEADER, "日志末尾摘要（最多 40 个物理行）：")
        self.assertEqual(feedback.TAIL_LINES, 40)

    def test_templates_use_only_known_placeholders(self):
        self.write_state(self.c, "eligible_gain")
        known = set(feedback._values(feedback.mechanical_view(self.c, 1, case=self.case)))
        for name in sorted(set(feedback.TEMPLATE_OF.values())):
            with open(os.path.join(feedback.TEMPLATES, f"{name}.md"), encoding="utf-8") as f:
                text = f.read()
            for ph in re.findall(r"\{([^{}\n]*)\}", text):
                self.assertIn(ph, known, (name, ph))
        for text in feedback.load_endings().values():
            self.assertNotRegex(text, r"\{[^{}\n]*\}")

    def test_veto_does_not_change_bytes(self):
        a, b = self.c1[0], self.c1[1]
        for code in (a, b):
            self.attempt(code)
            self.compare(code)
        self.ok_status(a, "ineligible", author_veto=True, flags=["author_veto"], improvement="not_applicable",
                       eligible_target_met=False)
        self.ok_status(b, "eligible_gain", author_veto=False, flags=[], improvement=True, eligible_target_met=True,
                       worst_setup_delta="0.5")
        wtext(os.path.join(self.revise, "review", "r1.tsv"), f"code\t否决条目\n{a}\tV1\n{b}\t-\n")
        self.assertEqual(feedback.render(a, **self.kw), feedback.render(b, **self.kw))

    def test_numeric_target_met_true_and_false_with_matrix(self):
        for code, met, word in ((self.c1[0], True, "是"), (self.c1[1], False, "否")):
            self.attempt(code)
            self.compare(code)
            self.ok_status(code, numeric_target_met=met)
            t = self.render(code)
            self.assertIn(f"是否数值上满足 setup_ge_0_std：{word}", t)
            self.assertIn("| tt_025C_1v80 | 0.123457 | 4.123457 |", t)

    def test_compile_fail_with_area_reports_area(self):
        code = self.c
        self.attempt(code, location="gl_compile", steps=_steps(), files={"gl_sim/compile.log": "syntax error\n"},
                     verdict={"worst_setup": None, "worst_hold": None})
        self.status(code, "grade_fail", selected_attempt=1, grade_status="GRADE FAIL", rtl_sim="pass",
                    gl_sim="fail", checked_rtl="checked=2856", area_um2="41234.56789", within_cap=True,
                    failure_location="gl_compile")
        t = self.render(code)
        self.assertIn("面积（µm²）：41234.567890", t)
        self.assertIn("是否超过面积上限：否", t)
        self.assertIn("全局最差 setup slack（ns）：not_run", t)
        self.assertIn("6 个 std 点的全局最小 slack（ns）：not_run", t.replace("：\n\nnot_run", "：not_run"))
        self.assertIn("syntax error", t)

    def test_state_without_evidence_refused(self):
        c0, c1 = self.c1[0], self.c1[1]
        self.call(c0, "parse")
        self.parsed(c0, status="ok", reason=None)               # parsed ok, no truncation: no delivery failure
        self.status(c0, "delivery_fail")
        with self.assertRaisesRegex(feedback.FeedbackError, "delivery_fail"):
            self.render(c0)
        self.call(c1, "parse")
        self.parsed(c1, status="ok", reason=None)
        self.status(c1, "gate_reject")
        with self.assertRaisesRegex(feedback.FeedbackError, "gate_reject"):  # no gate.json
            self.render(c1)
        self.gate(c1, [], passed=True)
        with self.assertRaisesRegex(feedback.FeedbackError, "gate_reject"):  # gate passed
            self.render(c1)
        self.assertFalse(os.path.exists(os.path.join(self.revise, "prompts", "r2")))

    def test_parsed_trigger_texts_must_parallel_lines(self):
        code = self.c
        self.call(code, "parse")
        self.parsed(code, reason="conflicting_declared_L", trigger_lines=[3, 5], trigger_texts=["only one"])
        with self.assertRaises(feedback.FeedbackError):
            feedback.mechanical_view(code, 1, case=self.case)

    def test_log_summary_saved_with_sha256(self):
        c0, c1 = self.c1[0], self.c1[1]
        self.write_state(c0, "grade_fail")
        t = self.render(c0)
        out = os.path.join(self.revise, "prompts", "r2")
        with open(os.path.join(out, f"{c0}_log_summary.txt"), "rb") as f:
            summary = f.read()
        self.assertEqual(summary.decode("utf-8"), feedback.TAIL_HEADER + "\nerror x\n")
        self.assertIn(summary.decode("utf-8").rstrip("\n"), t)
        with open(os.path.join(out, f"{c0}_log_summary.sha256"), "rb") as f:
            self.assertEqual(f.read().decode("ascii"), f"{rp.sha256_bytes(summary)}  {c0}_log_summary.txt\n")
        self.write_state(c1, "eligible_gain")                 # no log summary in the feedback: no files
        self.render(c1)
        self.assertFalse(os.path.exists(os.path.join(out, f"{c1}_log_summary.txt")))
        self.assertFalse(os.path.exists(os.path.join(out, f"{c1}_log_summary.sha256")))

    def test_truncated_delivery_fail_without_parsed(self):
        code = self.c
        self.call(code, "delivery_fail", calls=[("输出上限", "退出码非 0")])
        self.status(code, "delivery_fail")
        t = self.render(code)
        self.assertIn("失败的检查项：输出上限", t)
        self.assertIn("无可定位的原文行", t)
        self.call(code, "delivery_fail", calls=[("退出码非 0",)])         # no cap category: refused, not guessed
        with self.assertRaises(feedback.FeedbackError):
            feedback.mechanical_view(code, 1, case=self.case)

    def test_delivery_fail_lines_first_10_ascending(self):
        code = self.c
        self.call(code, "parse")
        self.parsed(code, reason="no_submission_with_code", trigger_lines=[40, 3, 25, 12, 7, 99, 1, 18, 33, 5, 60, 2])
        self.status(code, "delivery_fail")
        t = self.render(code)
        want = "\n".join(f"第 {n} 行：answer line {n}" for n in (1, 2, 3, 5, 7, 12, 18, 25, 33, 40))
        self.assertIn(f"```text\n{want}\n```", t)
        self.assertNotIn("第 60 行", t)
        self.assertNotIn("第 99 行", t)
        code2 = self.c1[1]
        self.call(code2, "parse")
        self.parsed(code2, reason="no_verilog_block", trigger_lines=[])
        self.status(code2, "delivery_fail")
        self.assertIn("无可定位的原文行", self.render(code2))

    def test_gate_reject_lines_first_10_ascending(self):
        code = self.c
        self.call(code, "parse")
        self.parsed(code, status="ok", reason=None)
        hits = [("G7", n, "extra") for n in (50, 8, 31, 14, 2, 77, 19, 26, 5, 44, 61, 11)]
        hits += [("G6", 8, "extra"), ("G6", 8, "extra"), ("G2", 3, "contract")]
        self.gate(code, hits)
        self.status(code, "gate_reject")
        t = self.render(code)
        lines = re.findall(r"^第 (\d+) 行（([^）]*)）：rtl line (\d+)$", t, re.M)
        self.assertEqual([int(n) for n, _, _ in lines], [2, 3, 5, 8, 11, 14, 19, 26, 31, 44])
        self.assertEqual([n for n, _, _ in lines], [m for _, _, m in lines])
        self.assertEqual({n: r for n, r, _ in lines}["8"], "G6、G7")
        rules = re.findall(r"^- (G\d|unrecognized)：", t, re.M)
        self.assertEqual(rules, ["G2", "G6", "G7"])
        # a hit without text, or two texts for one line, is refused
        for bad in ([("G6", 4, "extra", None)], [("G6", 4, "extra", "a"), ("G7", 4, "extra", "b")]):
            self.gate(code, bad)
            with self.assertRaises(feedback.FeedbackError):
                feedback.mechanical_view(code, 1, case=self.case)
        self.gate(code, hits)
        # gate_rules.md missing: a clear error
        os.remove(os.path.join(self.revise, "rules", "gate_rules.md"))
        with self.assertRaisesRegex(feedback.FeedbackError, "gate_rules.md"):
            self.render(code)


class TestMappingGuard(Base):
    def test_refuses_uncommitted_mapping(self):
        self.commit_codes(rounds=())                            # nothing committed
        code = self.c1[0]
        self.call(code, "unavailable", calls=[("模型不符",)])
        self.status(code, "unavailable")
        with self.assertRaises(mapping.MappingError):
            feedback.render(code, **self.kw)
        self.assertFalse(os.path.exists(os.path.join(self.revise, "prompts", "r2")))

    def test_refuses_uncommitted_round2_mapping(self):
        self.commit_codes(rounds=(1,))
        code = self.c1[0]
        self.call(code, "unavailable", calls=[("模型不符",)])
        self.status(code, "unavailable")
        with self.assertRaises(mapping.MappingError):
            feedback.render(code, **self.kw)
        self.assertFalse(os.path.exists(os.path.join(self.revise, "prompts", "r2")))


if __name__ == "__main__":
    unittest.main()
