"""Unit tests of build_package.py and build_prompt.py (in memory; nothing is written).
Run: python3 -B -m unittest test_build"""
import os
import unittest
from unittest import mock

import build_package as bp
import build_prompt as bpr
from diagpaths import CASE, read_bytes


class TestPackage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.sources = bp.build()

    def test_file_set_and_order(self):
        self.assertEqual(sorted(self.files), sorted(bp.ORDER))

    def test_build_is_deterministic(self):
        again, _ = bp.build()
        self.assertEqual(again, self.files)

    def test_copied_files_are_byte_identical(self):
        self.assertEqual(self.files["path_report.rpt"], read_bytes(os.path.join(CASE, bp.REPORT)))
        self.assertEqual(self.files["case01_sdc.tcl"], read_bytes(os.path.join(CASE, bp.SDC)))
        self.assertEqual(self.files["dot4sat.v"], read_bytes(os.path.join(CASE, bp.RTL)))

    def test_context_is_spec_section_1_plus_conditions(self):
        ctx = self.files["context.md"].decode("utf-8")
        self.assertTrue(ctx.startswith("## 1. 接口\n"))
        self.assertNotIn("## 2. ", ctx)
        self.assertIn("## 分析条件", ctx)
        self.assertIn("report_checks -from [all_inputs -no_clocks]", ctx)

    def test_values(self):
        self.assertEqual(self.files["values.txt"], b"T_ns = 27.91\nC_load_pF = 0.0024\n")
        self.assertEqual(bp.values("# c\nT_ns = 1.5  # x\nC_load_pF= 2\n"), "T_ns = 1.5\nC_load_pF = 2\n")

    def test_slack_summary_keeps_only_raw_ws_cat_topo_rows(self):
        lines = self.files["slack_summary.tsv"].decode("utf-8").splitlines()
        rows = [l for l in lines if not l.startswith("#")]
        self.assertEqual([sum(r.startswith(k + "\t") for r in rows) for k in ("WS", "CAT", "TOPO")], [12, 36, 3])
        src = read_bytes(os.path.join(CASE, bp.RESULTS)).decode("utf-8").splitlines()
        self.assertEqual(rows, [l for l in src if l.split("\t", 1)[0] in ("WS", "CAT", "TOPO")])
        self.assertTrue(all(l.startswith("#") for l in lines[:len(lines) - len(rows)]))

    def test_listing(self):
        sums, src = bp.listing(self.files, self.sources)
        self.assertEqual(len(sums.decode().splitlines()), 6)
        self.assertEqual(len(src.decode().splitlines()), 1 + len(self.sources))

    def test_every_source_is_pinned(self):
        self.assertEqual(sorted(bp.PINNED), sorted([bp.REPORT, bp.RTL, bp.SDC, bp.RESULTS, bp.F1_CFG, bp.SPEC]))
        for rel in bp.PINNED:
            with mock.patch.dict(bp.PINNED, {rel: "0" * 64}):
                with self.assertRaises(SystemExit, msg=rel):
                    bp.build()


class TestPrompt(unittest.TestCase):
    def test_numbered(self):
        self.assertEqual(bpr.numbered("a.txt", "x\ny\n".encode()),
                         "=== 文件：a.txt（共 2 行）===\n   1| x\n   2| y\n=== 文件结束：a.txt ===\n")

    def test_fill_is_one_pass(self):
        out = bpr.fill("A{{第1轮答复}}B{{执行结果}}C", {"第1轮答复": "{{执行结果}}", "执行结果": "R"})
        self.assertEqual(out, "A{{执行结果}}BRC")

    def test_fill_missing_value_refused(self):
        with self.assertRaises(SystemExit):
            bpr.fill("{{材料}}", {})

    def test_round1_uses_package_in_order(self):
        files, _ = bp.build()
        with mock.patch.object(bpr, "read_bytes", side_effect=lambda p: files[os.path.basename(p)]
                               if os.path.basename(p) in files else read_bytes(p)):
            text = bpr.round1_bytes().decode("utf-8")
        heads = [l for l in text.splitlines() if l.startswith("=== 文件：")]
        self.assertEqual([h.split("：")[1].split("（")[0] for h in heads], list(bpr.ORDER))
        self.assertNotIn("{{", text)
        self.assertIn("五、可能的修改", text)


if __name__ == "__main__":
    unittest.main()
