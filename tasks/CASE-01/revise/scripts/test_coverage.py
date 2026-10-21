"""Tests for coverage (round-2 coverage table, corrected / wrong predictions and disappearing failure conditions;
protocol v0.4 section 10.4; CASE-01 stage B Task 7). Both sides (Windows and WSL); run per module, never with
discover. Pure Python: no subprocess; file work only in a temporary directory under tasks/CASE-01/runs/."""
import contextlib
import io
import json
import os
import tempfile
import unittest

import coverage
import revpaths as rp
import test_judge as tj

RUNS = os.path.join(rp.CASE, "runs")
C1, C2 = "cand_r1aa", "cand_r2bb"
PREV = {C2: C1}


def p1(pid, **kw):
    return tj.pred(pid, candidate=C1, **kw)


def p2(pid, **kw):
    return tj.pred(pid, candidate=C2, **kw)


def f1(fid, expr, **kw):
    return tj.fc(fid, expr=expr, candidate=C1, **kw)


def f2(fid, expr, **kw):
    return tj.fc(fid, expr=expr, candidate=C2, **kw)


def cov(action, r1_ref="", r2_ref="", row_type="prediction", same_object=None, same_criterion=None,
        link_basis="", c1=C1, c2=C2):
    return {"row_type": row_type, "r1_ref": r1_ref, "r2_ref": r2_ref, "candidate_r1": c1, "candidate_r2": c2,
            "action": action, "same_object": same_object, "same_criterion": same_criterion,
            "link_basis": link_basis}


EXPR_A = tj.atom("status.gl_sim", "is", "fail")
EXPR_B = tj.atom("status.within_cap", "is", "false")


class Validate(unittest.TestCase):
    def v(self, r1, r2, rows):
        return coverage.validate(r1, r2, rows, prev=PREV)

    def base(self):
        r1 = [p1("a1", direction="改善"), p1("a2", direction="退化"), f1("F1", EXPR_A)]
        r2 = [p2("b1", direction="改善"), f2("F1", EXPR_A)]
        rows = [cov("keep", "a1", "b1", same_object=True, same_criterion=True),
                cov("not_mentioned", "a2"),
                cov("keep", "F1", "F1", row_type="failure_condition", same_object=True, same_criterion=True,
                    link_basis="作者复核：同一失败条件原文")]
        return r1, r2, rows

    def test_valid_table_passes(self):
        self.assertEqual(self.v(*self.base()), [])

    def test_validate_missing_r1_row(self):
        r1, r2, rows = self.base()
        probs = self.v(r1, r2, [r for r in rows if r["r1_ref"] != "a2"])
        self.assertTrue(any("a2" in p for p in probs), probs)

    def test_validate_duplicate(self):
        r1, r2, rows = self.base()
        probs = self.v(r1, r2, rows + [cov("withdraw", "a2")])
        self.assertTrue(any("a2" in p for p in probs), probs)
        probs = self.v(r1, r2, rows + [cov("new", "", "b1")])
        self.assertTrue(any("b1" in p for p in probs), probs)

    def test_validate_dangling_ref(self):
        r1, r2, rows = self.base()
        probs = self.v(r1, r2, rows + [cov("new", "", "b9")])
        self.assertTrue(any("b9" in p for p in probs), probs)
        probs = self.v(r1, r2, rows + [cov("withdraw", "a9")])
        self.assertTrue(any("a9" in p for p in probs), probs)

    def test_validate_cross_candidate_mismatch(self):
        r1, r2, rows = self.base()
        bad = [dict(r, candidate_r1="cand_zzzz") if r["r1_ref"] == "a2" else r for r in rows]
        self.assertTrue(self.v(r1, r2, bad))
        swapped = [dict(r, candidate_r1=C2, candidate_r2=C1) for r in rows]   # prev_code direction reversed
        self.assertTrue(self.v(r1, r2, swapped))
        self.assertTrue(coverage.validate(r1, r2, rows, prev={C1: C2}))     # mapping the other way round

    def test_validate_empty_ref_combinations(self):
        r1, r2, rows = self.base()
        r2x = r2 + [p2("b2", direction="改善", category="reg2out")]
        self.assertEqual(self.v(r1, r2x, rows + [cov("new", "", "b2")]), [])
        others = [r for r in rows if r["r1_ref"] != "a2"]
        cases = ((cov("new", "a2", "b2"), "new"),
                 (cov("not_mentioned", "a2", "b2"), "not_mentioned"),
                 (cov("withdraw", "a2", "b2"), "withdraw"),
                 (cov("modify", "a2", "", same_object=True, same_criterion=False), "modify"),
                 (cov("keep", "", "b2", same_object=True, same_criterion=True), "keep"))
        for bad, word in cases:
            probs = self.v(r1, r2x, others + [bad] + ([cov("not_mentioned", "a2")] if not bad["r1_ref"] else [])
                           + ([cov("new", "", "b2")] if not bad["r2_ref"] else []))
            self.assertTrue(any(word in p and "ref" in p for p in probs), (word, probs))
        self.assertTrue(self.v(r1, r2x, others + [cov("bogus", "a2"), cov("new", "", "b2")]))

    def test_validate_wrong_keep(self):
        r1 = [p1("a1", direction="改善")]
        r2 = [p2("b1", direction="退化")]
        probs = self.v(r1, r2, [cov("keep", "a1", "b1", same_object=True, same_criterion=False)])
        self.assertTrue(any("keep" in p for p in probs), probs)
        self.assertEqual(self.v(r1, r2, [cov("modify", "a1", "b1", same_object=True, same_criterion=False)]), [])

    def test_validate_object_change_needs_two_rows(self):
        r1 = [p1("a1", direction="改善")]
        r2 = [p2("b1", direction="改善", category="reg2out")]
        self.assertTrue(self.v(r1, r2, [cov("modify", "a1", "b1", same_object=False, same_criterion=True)]))
        self.assertTrue(self.v(r1, r2, [cov("keep", "a1", "b1", same_object=False, same_criterion=True)]))
        self.assertEqual(self.v(r1, r2, [cov("not_mentioned", "a1"), cov("new", "", "b1")]), [])
        self.assertEqual(self.v(r1, r2, [cov("withdraw", "a1"), cov("new", "", "b1")]), [])

    def test_fc_same_id_changed_expr_is_not_keep(self):
        r1, r2 = [f1("F1", EXPR_A)], [f2("F1", EXPR_B)]
        probs = self.v(r1, r2, [cov("keep", "F1", "F1", row_type="failure_condition", same_object=True,
                                    same_criterion=False, link_basis="同一条")])
        self.assertTrue(probs)
        self.assertEqual(self.v(r1, r2, [cov("modify", "F1", "F1", row_type="failure_condition", same_object=True,
                                             same_criterion=False, link_basis="作者复核：同一条")]), [])
        # author did not confirm the link: only new + not_mentioned
        self.assertTrue(self.v(r1, r2, [cov("modify", "F1", "F1", row_type="failure_condition", same_object=False,
                                            same_criterion=False, link_basis="x")]))
        self.assertEqual(self.v(r1, r2, [cov("not_mentioned", "F1", row_type="failure_condition"),
                                         cov("new", "", "F1", row_type="failure_condition")]), [])
        # key order of the expression does not matter for same_criterion
        r2s = [f2("F1", {"atom": {"value": "fail", "op": "is", "field": "status.gl_sim"}})]
        self.assertEqual(self.v(r1, r2s, [cov("keep", "F1", "F1", row_type="failure_condition", same_object=True,
                                              same_criterion=True, link_basis="同一条")]), [])

    def test_prediction_same_fields_changed_threshold_is_modify(self):
        r1 = [p1("a1", direction="改善", low="0.1")]
        r2 = [p2("b1", direction="改善", low="0.2")]
        self.assertTrue(self.v(r1, r2, [cov("keep", "a1", "b1", same_object=True, same_criterion=True)]))
        self.assertEqual(self.v(r1, r2, [cov("modify", "a1", "b1", same_object=True, same_criterion=False)]), [])
        # the same number written differently is the same criterion
        r2b = [p2("b1", direction="改善", low="0.10")]
        self.assertEqual(self.v(r1, r2b, [cov("keep", "a1", "b1", same_object=True, same_criterion=True)]), [])

    def test_row_type_mismatch_rejected(self):
        r1 = [p1("a1", direction="改善")]
        r2 = [f2("F1", EXPR_A)]
        probs = self.v(r1, r2, [cov("modify", "a1", "F1", same_object=True, same_criterion=False)])
        self.assertTrue(any("row_type" in p for p in probs), probs)
        probs = self.v(r1, r2, [cov("not_mentioned", "a1", row_type="failure_condition"),
                                cov("new", "", "F1", row_type="failure_condition")])
        self.assertTrue(any("row_type" in p for p in probs), probs)

    def test_wrong_same_criterion_rejected(self):
        r1 = [p1("a1", direction="改善", high="1")]
        r2 = [p2("b1", direction="改善", high="2")]
        probs = self.v(r1, r2, [cov("modify", "a1", "b1", same_object=True, same_criterion=True)])
        self.assertTrue(any("same_criterion" in p for p in probs), probs)
        probs = self.v(r1, r2, [cov("modify", "a1", "b1", same_object=None, same_criterion=False)])
        self.assertTrue(any("same_object" in p for p in probs), probs)

    def test_fc_link_requires_basis(self):
        r1, r2 = [f1("F1", EXPR_A)], [f2("F2", EXPR_A)]
        probs = self.v(r1, r2, [cov("keep", "F1", "F2", row_type="failure_condition", same_object=True,
                                    same_criterion=True, link_basis="")])
        self.assertTrue(any("link_basis" in p for p in probs), probs)


# ------------------------------------------------------------------------------------------------- compute
class ComputeBase(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="coverage_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.case = os.path.join(self.tmp.name, "case")
        self.pred_dir = os.path.join(self.case, "revise", "predictions")

    def setup(self, r1, r2, rows, j1, j2, st2=None, mx2=None):
        """j1 / j2: {ref: judgment word}; st2: round-2 status of C2."""
        for rnd, crit, js in ((1, r1, j1), (2, r2, j2)):
            tj.wjsonl(os.path.join(self.pred_dir, f"r{rnd}_criteria.jsonl"), crit)
            jrows = []
            for r in crit:
                ref = r["prediction_id"] if r["row_type"] == "prediction" else r["fc_id"]
                jrows.append(dict(r, judgment=js[ref]))
            tj.wjsonl(os.path.join(self.pred_dir, f"r{rnd}_judgments.jsonl"), jrows)
        tj.wjsonl(os.path.join(self.pred_dir, "r2_coverage.jsonl"), rows)
        tj.wjson(os.path.join(self.case, "revise", "results", "r2", C2, "status.json"),
                 tj.status(code=C2, rnd=2) if st2 is None else st2)
        if mx2 is not None:
            tj.wjson(os.path.join(self.case, "revise", "compare", f"r2_{C2}.json"), mx2)

    def compute(self, check=False):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = coverage.compute(case=self.case, check=check, prev=PREV)
        return rc, buf.getvalue()

    def result(self):
        rc, out = self.compute()
        self.assertEqual(rc, 0, out)
        return json.loads(rp.read_bytes(os.path.join(self.pred_dir, "r2_coverage_result.json")).decode("utf-8"))


class Compute(ComputeBase):
    def pair(self, j1, j2, action="modify"):
        r1 = [p1("a1", direction="改善", low="0.1")]
        r2 = [p2("b1", direction="改善", low="0.2" if action == "modify" else "0.1")]
        rows = [cov(action, "a1", "b1", same_object=True, same_criterion=(action == "keep"))]
        self.setup(r1, r2, rows, {"a1": j1}, {"b1": j2})
        return self.result()

    def test_modify_same_object_corrected(self):
        res = self.pair("反对", "支持")
        self.assertEqual(res["predictions"]["counts"]["预测改对"], 1)
        self.assertEqual(res["predictions"]["records"][0]["outcome"], "预测改对")

    def test_modify_corrected_wrong(self):
        res = self.pair("支持", "反对")
        self.assertEqual(res["predictions"]["counts"]["预测改错"], 1)
        res = self.pair("支持", "支持", action="keep")
        self.assertEqual(res["predictions"]["counts"]["无变化或不可比"], 1)
        res = self.pair("未判定", "支持")
        self.assertEqual(res["predictions"]["counts"]["无变化或不可比"], 1)

    def test_new_object_not_compared(self):
        r1 = [p1("a1", direction="改善")]
        r2 = [p2("b1", direction="改善", category="reg2out")]
        self.setup(r1, r2, [cov("not_mentioned", "a1"), cov("new", "", "b1")], {"a1": "反对"}, {"b1": "支持"})
        res = self.result()
        self.assertEqual(res["predictions"]["records"], [])
        self.assertEqual(sum(res["predictions"]["counts"].values()), 0)
        self.assertEqual(res["actions"]["prediction"]["new"], 1)

    def test_not_mentioned_counted(self):
        r1 = [p1("a1", direction="改善"), p1("a2", direction="退化")]
        r2 = [p2("b1", direction="改善")]
        self.setup(r1, r2, [cov("keep", "a1", "b1", same_object=True, same_criterion=True), cov("not_mentioned", "a2")],
                   {"a1": "支持", "a2": "反对"}, {"b1": "支持"})
        res = self.result()
        self.assertEqual(res["actions"]["prediction"]["not_mentioned"], 1)
        self.assertEqual(res["actions"]["prediction"]["keep"], 1)

    def test_withdraw_not_counted_as_corrected(self):
        r1 = [p1("a1", direction="改善")]
        self.setup(r1, [], [cov("withdraw", "a1")], {"a1": "反对"}, {})
        res = self.result()
        self.assertEqual(res["actions"]["prediction"]["withdraw"], 1)
        self.assertEqual(res["predictions"]["counts"]["预测改对"], 0)

    def fc_case(self, st2, coverage_action="keep", mx2=None):
        r1 = [f1("F1", EXPR_A), f1("F2", EXPR_B)]
        if coverage_action == "keep":
            r2 = [f2("F1", EXPR_A)]
            rows = [cov("keep", "F1", "F1", row_type="failure_condition", same_object=True, same_criterion=True,
                        link_basis="同一条"), cov("not_mentioned", "F2", row_type="failure_condition")]
        else:
            r2 = []
            rows = [cov("not_mentioned", "F1", row_type="failure_condition"),
                    cov("not_mentioned", "F2", row_type="failure_condition")]
        self.setup(r1, r2, rows, {"F1": "触发", "F2": "未触发"}, {"F1": "未触发"}, st2=st2,
                   mx2=tj.mdoc() if mx2 is None and st2.get("sta_analysis") == "pass" else mx2)
        return self.result()

    def test_failure_condition_disappears_on_round2_candidate(self):
        res = self.fc_case(tj.status(code=C2, rnd=2, gl_sim="pass"))
        recs = res["failure_conditions"]["records"]
        self.assertEqual([r["r1_ref"] for r in recs], ["F1"])          # only the round-1 triggered ones
        self.assertEqual(recs[0]["outcome"], "消失")
        res = self.fc_case(tj.status(code=C2, rnd=2, gl_sim="fail"))
        self.assertEqual(res["failure_conditions"]["records"][0]["outcome"], "仍在")
        self.assertEqual(res["failure_conditions"]["counts"]["仍在"], 1)

    def test_failure_condition_evaluated_even_if_not_mentioned(self):
        res = self.fc_case(tj.status(code=C2, rnd=2, gl_sim="pass"), coverage_action="not_mentioned")
        self.assertEqual(res["failure_conditions"]["records"][0]["outcome"], "消失")
        res = self.fc_case(tj.status(code=C2, rnd=2, gl_sim="indeterminate"), coverage_action="not_mentioned")
        self.assertEqual(res["failure_conditions"]["records"][0]["outcome"], "indeterminate")

    def test_declined_round2_is_indeterminate(self):
        st = tj.status(code=C2, rnd=2, state="declined", grade_status="not_run", rtl_sim="not_run",
                       gl_sim="not_run", sta_analysis="not_run")
        res = self.fc_case(st, coverage_action="not_mentioned")
        self.assertEqual(res["failure_conditions"]["records"][0]["outcome"], "indeterminate")
        st = tj.status(code=C2, rnd=2, state="unavailable", gl_sim="fail")   # would evaluate true: still no candidate
        res = self.fc_case(st, coverage_action="not_mentioned")
        self.assertEqual(res["failure_conditions"]["records"][0]["outcome"], "indeterminate")

    def test_compute_check_mode_detects_difference(self):
        self.pair("反对", "支持")
        self.assertEqual(self.compute(check=True)[0], 0)
        path = os.path.join(self.pred_dir, "r2_coverage_result.json")
        before = rp.read_bytes(path)
        tj.wbytes(path, before.replace("预测改对".encode("utf-8"), "预测改错".encode("utf-8"), 1))
        rc, out = self.compute(check=True)
        self.assertEqual(rc, 1)
        self.assertIn("CHECK FAIL", out)
        self.assertNotEqual(rp.read_bytes(path), before)                 # check mode never writes

    def test_invalid_coverage_writes_nothing(self):
        r1 = [p1("a1", direction="改善")]
        self.setup(r1, [], [], {"a1": "反对"}, {})
        rc, out = self.compute()
        self.assertEqual(rc, 1)
        self.assertIn("COVERAGE FAIL", out)
        self.assertFalse(os.path.exists(os.path.join(self.pred_dir, "r2_coverage_result.json")))

    # ---- round-2 same_as rows (controller ruling R16)
    def setup_same_as(self, x="P1", alter=None, model_fields=None):
        r1 = [p1("a1", id="P1", direction="改善", low="0.1")]
        r2row = p2("b1", id=f"same_as={x}", direction="改善", low="0.1",
                   source=f"line 12; same_as={x} resolved from round-1 row {x} of {C1}")
        r2row.update(alter or {})
        rows = [cov("keep", "a1", "b1", same_object=True, same_criterion=True)]
        self.setup(r1, [r2row], rows, {"a1": "反对"}, {"b1": "支持"})
        tj.wjsonl(os.path.join(self.pred_dir, "r1_extracted.jsonl"), tj.extracted_of(r1))
        own = {c: "" for c in tj.judge.EXTRACTED_PREDICTION_COLUMNS}
        own.update({"id": f"same_as={x}", "action": r2row["action"], "basis": r2row["basis"]}, **(model_fields or {}))
        tj.wjsonl(os.path.join(self.pred_dir, "r2_extracted.jsonl"),
                  [{"code": C2, "row_type": "prediction", "index": 1, **own}])

    def views2(self, prev=PREV):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = tj.judge.views(2, case=self.case, prev=prev)
        return rc, buf.getvalue()

    def test_same_as_row_is_keep_and_counted(self):
        self.setup_same_as()
        rc, out = self.views2()
        self.assertEqual(rc, 0, out)
        res = self.result()
        self.assertEqual(res["actions"]["prediction"]["keep"], 1)
        self.assertEqual(res["predictions"]["counts"]["预测改对"], 1)
        self.assertEqual(res["predictions"]["records"][0]["action"], "keep")
        # the model's own row may repeat X's values; it is still a same_as row
        self.setup_same_as(model_fields={"metric": "slack", "low": "0.1"})
        self.assertEqual(self.views2()[0], 0)

    def test_same_as_nonexistent_target_is_criteria_fail(self):
        self.setup_same_as(x="P9")
        rc, out = self.views2()
        self.assertEqual(rc, 1)
        self.assertIn("CRITERIA FAIL", out)
        self.assertIn("P9", out)
        self.setup_same_as()
        rc, out = self.views2(prev={C2: "cand_zzzz"})          # predecessor mismatch
        self.assertEqual(rc, 1)
        self.assertIn("CRITERIA FAIL", out)
        rc, out = self.views2(prev={})                         # no predecessor
        self.assertEqual(rc, 1)

    def test_same_as_altered_fields_is_criteria_fail(self):
        for alter in ({"low": "0.2"}, {"category": "reg2out"}, {"direction": "退化"}):
            self.setup_same_as(alter=alter)
            rc, out = self.views2()
            self.assertEqual(rc, 1, alter)
            self.assertIn("CRITERIA FAIL", out)
        self.setup_same_as(alter={"source": "line 12"})       # source must record the same_as resolution
        self.assertEqual(self.views2()[0], 1)
        self.setup_same_as(model_fields={"low": "0.3"})        # the model's own row contradicts X
        self.assertEqual(self.views2()[0], 1)

    def test_coverage_tsv_view(self):
        r1 = [p1("a1", direction="改善")]
        r2 = [p2("b1", direction="改善")]
        rows = [cov("keep", "a1", "b1", same_object=True, same_criterion=True, link_basis="行\t内")]
        self.setup(r1, r2, rows, {"a1": "支持"}, {"b1": "支持"})
        tj.wjsonl(os.path.join(self.pred_dir, "r2_extracted.jsonl"), tj.extracted_of(r2))
        tj.wjsonl(os.path.join(self.pred_dir, "r1_extracted.jsonl"), tj.extracted_of(r1))
        buf = io.StringIO()
        import judge
        with contextlib.redirect_stdout(buf):
            rc = judge.views(2, case=self.case, prev=PREV)
        self.assertEqual(rc, 0, buf.getvalue())
        data = rp.read_bytes(os.path.join(self.pred_dir, "r2_coverage.tsv")).decode("utf-8")
        lines = data.split("\n")
        self.assertEqual(lines[0].split("\t"), list(coverage.COVERAGE_COLUMNS))
        cells = dict(zip(coverage.COVERAGE_COLUMNS, lines[1].split("\t")))
        self.assertEqual((cells["same_object"], cells["link_basis"]), ("true", json.dumps("行\t内", ensure_ascii=False)))


if __name__ == "__main__":
    unittest.main()
