"""Unit tests of build_package.py, build_prompt.py and scoring.core_window (protocol v0.3 sections 4.1, 6.2, 6.3;
impl_plan Task 7). In memory / temporary directories; nothing under package/ is written. Run in WSL from
tasks/CASE-02/scripts: python3 -B -m unittest -v test_build"""
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
import build_package as bp  # noqa: E402
import build_prompt as bpr  # noqa: E402
import scoring  # noqa: E402

SELFTEST = os.path.join(c2paths.QUERIES, "selftest")
HAVE_SELFTEST = all(os.path.isfile(os.path.join(SELFTEST, v, "sta_results.tsv")) for v in ("correct", "missing"))
ASSIGN = {"R1": "correct", "R2": "missing"}


class TestPackageParts(unittest.TestCase):
    def test_summary_keeps_only_ws_cat_topo(self):
        tsv = "BIND\tx\ny\nWS\ttt\tmax\t1.0\nCAT\ttt\tin2reg\tmax\t1.0\ta\tb\nTOPO\tin2reg\t130\nLIB\tl\t/p\nDONE\n"
        out = bp.summary(tsv)
        self.assertEqual(out.splitlines(), ["WS\ttt\tmax\t1.0", "CAT\ttt\tin2reg\tmax\t1.0\ta\tb", "TOPO\tin2reg\t130"])

    def test_values_from_f1_cfg(self):
        self.assertEqual(bp.values("T_ns = 27.91 # period\nC_load_pF = 0.0024\nX=1\n"), "T_ns = 27.91\nC_load_pF = 0.0024\n")

    def test_intent_has_required_sentence(self):
        text = bp.intent_text()
        self.assertIn("这份意图说明表达的是要求", text)
        self.assertIn("0.2", text)
        self.assertIn("sky130_fd_sc_hd__buf_2", text)

    @unittest.skipUnless(HAVE_SELFTEST, "self-test contexts not built")
    def test_build_from_selftest_contexts(self):
        files, sources = bp.build(ASSIGN, formal_root=SELFTEST, frozen_context=b"## context\n")
        self.assertEqual(list(files), list(bp.ORDER))
        kinds = {l.split("\t", 1)[0] for l in files["summary_R1.tsv"].decode().splitlines()}
        self.assertEqual(kinds, {"WS", "CAT", "TOPO"})      # file order is kept, as in stage A
        self.assertNotEqual(files["summary_R1.tsv"], files["summary_R2.tsv"])
        self.assertIn(b"Startpoint:", files["path_R1.rpt"])
        self.assertEqual(files["context.md"], b"## context\n")
        for name, src, digest in sources:
            self.assertNotIn("correct", src)
            self.assertNotIn("missing", src)
            self.assertEqual(len(digest), 64)
        full = bp.sources_full(ASSIGN, formal_root=SELFTEST)
        self.assertIn("missing", full)

    def test_build_refuses_wrong_frozen_context(self):
        with self.assertRaises(SystemExit):
            bp.check_frozen_context(b"a\n", b"b\n")


class TestPrompt(unittest.TestCase):
    def test_numbered_lines(self):
        out = bpr.numbered("x.txt", b"a\nb\n")
        self.assertIn("=== 文件：x.txt（共 2 行）===", out)
        self.assertIn("   1| a", out)

    def test_round1_template_has_four_sections_and_limits(self):
        with open(os.path.join(c2paths.PROMPTS, "round1_template.md"), encoding="utf-8") as f:
            t = f.read()
        for s in ("一、观察", "二、结论和确定程度", "三、证据", "四、检查请求", "120 行", "12 条", "R1", "R2", "{{材料}}"):
            self.assertIn(s, t)

    def test_round2_template_sentence(self):
        with open(os.path.join(c2paths.PROMPTS, "round2_template.md"), encoding="utf-8") as f:
            t = f.read()
        self.assertIn("根据这些结果，确认或修正你第 1 轮的判断，栏位不变", t)
        for p in ("{{第1轮题目}}", "{{第1轮答复}}", "{{执行结果}}"):
            self.assertIn(p, t)

    def test_round2_prompt_contains_results_and_statement(self):
        tmp = tempfile.mkdtemp(prefix="pr_", dir=c2paths.RUNS)
        try:
            r1 = b"ROUND1 PROMPT\n"
            answer = b"answer text\n"
            results = "### 查询 A1（R1）\n...\n## 预算账单\n① 总预算：1 token\n".encode("utf-8")
            out = bpr.round2_from_parts(r1, answer, results).decode("utf-8")
            self.assertIn("ROUND1 PROMPT", out)
            self.assertIn("<<<第 1 轮回答开始>>>\nanswer text\n<<<第 1 轮回答结束>>>", out)
            self.assertIn("预算账单", out)
            self.assertTrue(out.rstrip().endswith("栏位不变。"))
        finally:
            shutil.rmtree(tmp)

    def test_check_budget_of_whole_prompt(self):
        chk = bpr.prompt_budget(b"x" * 400, ratio=4.0, budget_tokens=100)
        self.assertEqual((chk["rendered_bytes"], chk["tokens"], chk["ok"]), (400, 100, True))
        self.assertFalse(bpr.prompt_budget(b"x" * 401, ratio=4.0, budget_tokens=100)["ok"])


class TestCoreWindow(unittest.TestCase):
    def test_core_window_120_lines(self):
        body = ["一、观察"] + [f"obs {i}" for i in range(50)] + ["二、结论和确定程度"] + [f"c {i}" for i in range(50)] + \
               ["三、证据"] + [f"e {i}" for i in range(30)] + ["四、检查请求"] + [f"q {i}" for i in range(10)]
        text = "preamble line\n" + "\n".join(body) + "\n"
        core = scoring.core_window(text)
        self.assertEqual(len(core.splitlines()), 120)
        self.assertTrue(core.startswith("一、观察"))
        self.assertNotIn("preamble", core)

    def test_core_window_short_answer_unchanged(self):
        text = "一、观察\na\n二、结论和确定程度\nb\n三、证据\nc\n四、检查请求\nd\n"
        self.assertEqual(scoring.core_window(text), text)

    def test_core_window_without_headings_is_first_120(self):
        text = "\n".join(f"l{i}" for i in range(200)) + "\n"
        self.assertEqual(len(scoring.core_window(text).splitlines()), 120)


if __name__ == "__main__":
    unittest.main()
