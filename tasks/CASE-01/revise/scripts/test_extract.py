"""Tests for extract (CASE-01 stage B, Task 3, protocol sections 7.1 and 10.1). Run per module, never with discover.
Pure Python: runs on Windows and in WSL. Candidate files are only ever written below a temporary dest_root."""
import hashlib
import os
import tempfile
import unittest

import extract as x
import revpaths

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "answers")
RUNS = os.path.join(revpaths.CASE, "runs")


def load(name):
    with open(os.path.join(FIX, name + ".md"), "rb") as f:
        return f.read().decode("utf-8")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def tmpdir():
    os.makedirs(RUNS, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=RUNS)


def tree_state(path):
    out = {}
    for base, _dirs, files in os.walk(path):
        for fn in files:
            p = os.path.join(base, fn)
            out[p] = (os.path.getsize(p), os.path.getmtime(p))
    return out


class ParseFixtures(unittest.TestCase):
    def check(self, name, rnd, status, reason, lines, declared):
        p = x.parse_answer(load(name), rnd)
        self.assertEqual((p.status, p.reason, p.lines, p.declared_L), (status, reason, lines, declared), name)
        return p

    def test_normal(self):
        p = self.check("normal", 1, "ok", None, [5, 9], 2)
        self.assertEqual(p.rtl, b"module dot4sat(input clk);\n  // normal\nendmodule\n")
        self.assertEqual(p.rtl_sha_raw, sha(p.rtl))
        self.assertEqual(p.rtl_sha_lf, sha(p.rtl))
        self.assertEqual(p.unrun_blocks, [])

    def test_two_blocks_first_used(self):
        p = self.check("two_blocks", 1, "ok", None, [1, 4], 1)
        self.assertEqual(p.rtl, b"module first;\nendmodule\n")
        self.assertEqual(p.unrun_blocks, ["module second;\nendmodule\n"])

    def test_first_block_unclosed_does_not_fall_back(self):
        p = self.check("first_unclosed_later_complete", 1, "delivery_fail", "unclosed_block", [1], None)
        self.assertEqual(p.rtl, b"")
        self.assertIsNone(p.rtl_sha_raw)

    def test_no_block(self):
        self.check("no_block", 1, "delivery_fail", "no_verilog_block", [], 1)

    def test_no_declared(self):
        self.check("no_declared", 1, "delivery_fail", "no_declared_L", [1, 4], None)

    def test_conflicting_declared(self):
        self.check("conflicting_declared", 1, "delivery_fail", "conflicting_declared_L", [1, 4], None)

    def test_repeated_same_declared_is_fine(self):
        self.check("repeated_same_declared", 1, "ok", None, [1, 4], 1)

    def test_declared_only_in_block_quote_inline_or_malformed(self):
        # in the block, in a quote, inline, two digits, no spaces around "=": none counts
        self.check("declared_only_in_block_or_quote", 1, "delivery_fail", "no_declared_L", [1, 5], None)

    def test_no_submission_with_code(self):
        self.check("no_submission_with_code", 2, "delivery_fail", "no_submission_with_code", [1, 4], 1)

    def test_no_submission_in_fence_quote_inline_not_counted(self):
        p = self.check("no_submission_not_counted", 2, "ok", None, [6, 9], 1)
        self.assertEqual(p.unrun_blocks, ["NO_SUBMISSION\n"])

    def test_round1_no_submission_ignored(self):
        self.check("only_no_submission", 1, "delivery_fail", "no_verilog_block", [], None)
        self.check("no_submission_with_code", 1, "ok", None, [1, 4], 1)

    def test_round2_only_no_submission_is_declined(self):
        p = self.check("only_no_submission", 2, "declined", None, [], None)
        self.assertEqual(p.rtl, b"")

    def test_uppercase_verilog_skipped(self):
        p = self.check("uppercase_verilog", 1, "delivery_fail", "no_verilog_block", [], 1)
        self.assertEqual(p.unrun_blocks, ["module upper;\nendmodule\n"])

    def test_no_info_fence_before_verilog_block(self):
        p = self.check("no_info_fence_before", 1, "ok", None, [6, 9], 1)    # the 3 inside the plain fence is ignored
        self.assertEqual(p.unrun_blocks, ["not verilog, plain notes\nDECLARED_L = 3\n"])
        self.assertEqual(p.rtl, b"module real_one;\nendmodule\n")

    def test_close_fence_trailing_whitespace(self):
        p = self.check("close_fence_trailing_ws", 1, "ok", None, [1, 4], 1)
        self.assertEqual(p.rtl, b"module m;\nendmodule\n")

    def test_four_backtick_fence_with_inner_triple(self):
        p = self.check("four_backtick_inner", 1, "ok", None, [1, 5], 1)
        self.assertEqual(p.rtl, b"module m;\n```\nendmodule\n")

    def test_tilde_fence_with_declared_and_verilog_is_skipped(self):
        p = self.check("tilde_fence_before", 1, "ok", None, [7, 10], 1)
        self.assertEqual(p.rtl, b"module real_one;\nendmodule\n")
        self.assertEqual(p.unrun_blocks, ["module decoy;\nendmodule\nDECLARED_L = 3\n"])

    def test_declared_zero_is_recognized(self):
        p = self.check("declared_zero", 1, "ok", None, [1, 4], 0)
        self.assertIsNotNone(p.declared_L)

    def test_fence_edge_cases(self):
        # indented 4 spaces is not a fence; backtick in the info string is not a fence; closing needs same char
        t = "    ```verilog\nmodule a;\n```verilog x`\n```verilog\nmodule b;\n~~~\nendmodule\n```\nDECLARED_L = 1\n"
        p = x.parse_answer(t, 1)
        self.assertEqual((p.status, p.lines, p.rtl), ("ok", [4, 8], b"module b;\n~~~\nendmodule\n"))
        # a short closing fence does not close a longer opener
        t2 = "````verilog\nmodule a;\n```\nDECLARED_L = 1\n"
        self.assertEqual(x.parse_answer(t2, 1).reason, "unclosed_block")

    def test_crlf_normalized_and_both_hashes(self):
        crlf = load("normal").replace("\n", "\r\n")
        p = x.parse_answer(crlf, 1)
        raw_block = "module dot4sat(input clk);\r\n  // normal\r\nendmodule\r\n".encode("utf-8")
        self.assertEqual((p.status, p.declared_L, p.lines), ("ok", 2, [5, 9]))
        self.assertEqual(p.rtl_sha_raw, sha(raw_block))
        self.assertEqual(p.rtl, b"module dot4sat(input clk);\n  // normal\nendmodule\n")
        self.assertEqual(p.rtl_sha_lf, sha(p.rtl))
        self.assertNotEqual(p.rtl_sha_raw, p.rtl_sha_lf)
        self.assertEqual(p.predictions[0]["id"], "P1")             # tables parse with CRLF too

    def test_unicode_hash_is_utf8(self):
        p = x.parse_answer("```verilog\n// 中文\nmodule m;\nendmodule\n```\nDECLARED_L = 1\n", 1)
        self.assertEqual(p.rtl_sha_raw, sha("// 中文\nmodule m;\nendmodule\n".encode("utf-8")))


class Predictions(unittest.TestCase):
    def test_prediction_fields_and_failure_conditions_verbatim(self):
        p = x.parse_answer(load("normal"), 1)
        self.assertIsNone(p.prediction_table_problem)
        self.assertEqual(p.predictions[0], {
            "id": "P1", "action": "add pipeline register after multiplier", "metric": "slack", "check": "setup",
            "corner": "all", "category": "reg2reg", "value_kind": "delta", "direction": "改善", "low": "0.5",
            "high": "2.0", "unit": "ns", "point": "1.2", "basis": "dot4sat.v:40"})
        self.assertEqual(p.predictions[1]["metric"], "L")
        self.assertEqual(p.predictions[1]["check"], "")
        self.assertEqual(p.predictions[1]["point"], "2")
        self.assertEqual(len(p.predictions), 2)
        self.assertEqual(p.failure_conditions, [
            {"fc_id": "F1", "source": "line 22",
             "text": "F-a: setup slack at corner ss does not improve versus baseline"},
            {"fc_id": "F2", "source": "line 23", "text": "the area exceeds the cap\ncontinued second line"},
            {"fc_id": "F3", "source": "line 25", "text": "numbered item"}])
        self.assertFalse(p.prediction_L_mismatch)

    def test_columns_in_any_order(self):
        cols = "basis point unit high low direction value_kind category corner check metric action id".split()
        vals = [f"v_{c}" for c in cols]
        t = ("```verilog\nmodule m;\nendmodule\n```\nDECLARED_L = 1\n\n### 预测表\n\n| " + " | ".join(cols)
             + " |\n| " + " | ".join("---" for _ in cols) + " |\n| " + " | ".join(vals) + " |\n")
        p = x.parse_answer(t, 1)
        self.assertIsNone(p.prediction_table_problem)
        self.assertEqual(p.predictions, [{c: f"v_{c}" for c in cols}])

    def test_prediction_L_mismatch_flag(self):
        p = x.parse_answer(load("prediction_L_mismatch"), 1)
        self.assertEqual((p.status, p.declared_L), ("ok", 1))
        self.assertTrue(p.prediction_L_mismatch)
        self.assertEqual(len(p.predictions), 1)

    def test_no_prediction_table(self):
        p = x.parse_answer(load("no_prediction_table"), 1)
        self.assertEqual((p.status, p.predictions, p.prediction_table_problem, p.failure_conditions),
                         ("ok", [], "no_prediction_heading", []))
        self.assertFalse(p.prediction_L_mismatch)

    def test_heading_without_table(self):
        p = x.parse_answer("```verilog\nm\n```\nDECLARED_L = 1\n## 预测表\nnothing\n", 1)
        self.assertEqual((p.predictions, p.prediction_table_problem), ([], "no_prediction_table"))

    def test_bad_columns(self):
        p = x.parse_answer(load("bad_prediction_columns"), 1)
        self.assertEqual(p.predictions, [])
        self.assertTrue(p.prediction_table_problem.startswith("bad_columns"), p.prediction_table_problem)
        self.assertIn("missing=", p.prediction_table_problem)

    def test_row_with_wrong_cell_count(self):
        t = load("prediction_L_mismatch").replace("| 2 | x.v:1 |", "| 2 |")
        p = x.parse_answer(t, 1)
        self.assertEqual(p.predictions, [])
        self.assertEqual(p.prediction_table_problem, "row_cell_count: row 1")

    def test_table_inside_fence_not_used(self):
        t = "```verilog\nm\n```\nDECLARED_L = 1\n## 预测表\n```\n| a |\n|---|\n| b |\n```\n"
        self.assertEqual(x.parse_answer(t, 1).prediction_table_problem, "no_prediction_table")

    def test_failure_conditions_stop_at_same_or_higher_heading(self):
        base = "```verilog\nm\n```\nDECLARED_L = 1\n"
        t = base + "## 失败条件\n- a\n### 子节\n- b\n## 下一节\n- c\n"
        self.assertEqual([f["text"] for f in x.parse_answer(t, 1).failure_conditions], ["a", "b"])

    def test_non_ok_has_no_predictions(self):
        t = load("normal").replace("DECLARED_L = 2\n", "")
        p = x.parse_answer(t, 1)
        self.assertEqual((p.status, p.reason, p.predictions, p.failure_conditions, p.prediction_table_problem),
                         ("delivery_fail", "no_declared_L", [], [], None))

    def test_extracted_rows(self):
        p = x.parse_answer(load("normal"), 1)
        rows = x.extracted_rows("cand_ab12", p)
        self.assertEqual([r["row_type"] for r in rows], ["prediction", "prediction",
                                                          "failure_condition", "failure_condition",
                                                          "failure_condition"])
        self.assertEqual(rows[0]["code"], "cand_ab12")
        self.assertEqual(rows[0]["index"], 1)
        self.assertEqual(rows[0]["id"], "P1")
        self.assertEqual(rows[2], {"code": "cand_ab12", "row_type": "failure_condition", "fc_id": "F1",
                                   "source": "line 22", "text": p.failure_conditions[0]["text"]})
        bad = x.extracted_rows("cand_ab12", x.parse_answer(load("no_prediction_table"), 1))
        self.assertEqual(bad, [{"code": "cand_ab12", "row_type": "prediction_table_problem",
                                "problem": "no_prediction_heading"}])


class WriteCandidate(unittest.TestCase):
    def parsed(self):
        return x.parse_answer(load("normal"), 1)

    def test_write_candidate_cfg_content(self):
        with tmpdir() as d:
            cf = x.write_candidate("cand_ab12", self.parsed(), dest_root=d)
            rtl = os.path.join(d, "rtl", "dot4sat_cand_ab12.v")
            cfg = os.path.join(d, "config", "impl.cand_ab12.cfg")
            self.assertEqual((cf.rtl_path, cf.cfg_path), (rtl, cfg))
            with open(cfg, "rb") as f:
                cfg_bytes = f.read()
            self.assertEqual(cfg_bytes, b"name = cand_ab12\ntop = dot4sat\nrtl = rtl/dot4sat_cand_ab12.v\nL = 2\n")
            with open(rtl, "rb") as f:
                self.assertEqual(f.read(), self.parsed().rtl)
            self.assertEqual(cf.cfg_sha, sha(cfg_bytes))
            self.assertEqual((cf.rtl_sha_raw, cf.rtl_sha_lf), (self.parsed().rtl_sha_raw, self.parsed().rtl_sha_lf))
            x.write_candidate("cand_ab12", self.parsed(), dest_root=d)         # same bytes again: fine

    def test_write_candidate_refuses_different_bytes(self):
        with tmpdir() as d:
            x.write_candidate("cand_ab12", self.parsed(), dest_root=d)
            other = x.parse_answer(load("two_blocks"), 1)
            with self.assertRaises(revpaths.RevpathsError):
                x.write_candidate("cand_ab12", other, dest_root=d)
            with open(os.path.join(d, "rtl", "dot4sat_cand_ab12.v"), "rb") as f:
                self.assertEqual(f.read(), self.parsed().rtl)

    def test_write_candidate_crlf_input_writes_lf(self):
        p = x.parse_answer(load("normal").replace("\n", "\r\n"), 1)
        with tmpdir() as d:
            x.write_candidate("cand_cr01", p, dest_root=d)
            with open(os.path.join(d, "rtl", "dot4sat_cand_cr01.v"), "rb") as f:
                self.assertNotIn(b"\r", f.read())

    def test_write_candidate_refuses_non_ok_and_bad_code(self):
        with tmpdir() as d:
            bad = x.parse_answer(load("no_declared"), 1)
            with self.assertRaises(x.ExtractError):
                x.write_candidate("cand_ab12", bad, dest_root=d)
            for code in ("../x", "a/b", "", "cand 1"):
                with self.assertRaises(x.ExtractError):
                    x.write_candidate(code, self.parsed(), dest_root=d)
            self.assertEqual(os.listdir(d), [])

    def test_smoke_dest_root_does_not_touch_rtl(self):
        before = {n: tree_state(os.path.join(revpaths.CASE, n)) for n in ("rtl", "config")}
        with tmpdir() as d:
            x.write_candidate("cand_sm01", self.parsed(), dest_root=os.path.join(d, "revise-smoke", "cand_sm01"))
            self.assertTrue(os.path.exists(os.path.join(d, "revise-smoke", "cand_sm01", "rtl",
                                                        "dot4sat_cand_sm01.v")))
        after = {n: tree_state(os.path.join(revpaths.CASE, n)) for n in ("rtl", "config")}
        self.assertEqual(before, after)
        self.assertFalse(os.path.exists(os.path.join(revpaths.CASE, "rtl", "dot4sat_cand_sm01.v")))


if __name__ == "__main__":
    unittest.main()
