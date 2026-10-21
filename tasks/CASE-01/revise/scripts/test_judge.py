"""Tests for judge (criteria, judgments and TSV views; protocol v0.4 sections 10.1, 10.2; CASE-01 stage B Task 7).
Both sides (Windows and WSL); run per module, never with discover. Pure Python: no subprocess; file work only in a
temporary directory under tasks/CASE-01/runs/ (never /tmp, never the real revise/predictions)."""
import copy
import json
import os
import tempfile
import unittest
from decimal import Decimal

import judge
import revpaths as rp

RUNS = os.path.join(rp.CASE, "runs")
CORNERS = judge.CORNERS
CODE = "cand_ab12"
BASE_AREA = "1000.0"


# ---------------------------------------------------------------------------------------------- builders
def mdoc(cand=None, base=None, cand_default="-4.000000", base_default="-4.189726", base_area=BASE_AREA,
         cand_area="1001.5"):
    """A compare-document-like matrix (revise/compare/r<rnd>_<code>.json structure): slack values as strings."""
    cand, base = cand or {}, base or {}
    cells = []
    for c in CORNERS:
        for chk in ("setup", "hold"):
            for s in ("global", "in2reg", "reg2reg", "reg2out"):
                cv = cand.get((c, chk, s), cand_default)
                bv = base.get((c, chk, s), base_default)
                cells.append({"corner": c, "check": chk, "scope": s,
                              "base": {"slack": bv, "start": "a", "end": "b"},
                              "cand": {"slack": cv, "start": "a", "end": "b"}})
    return {"code": CODE, "rnd": 1,
            "baseline": {"summary": {"worst_setup": {"slack": "-4.189726018044011", "corner": "ss_100C_1v60",
                                                     "category": "reg2out"}},
                         "extra": {"area": base_area}},
            "candidate": {"summary": {"worst_setup": {"slack": "-4.000000", "corner": "ss_100C_1v60",
                                                      "category": "reg2out"},
                                      "worst_hold": {"slack": "0.100000", "corner": "ff_n40C_1v95"}},
                          "extra": {"area": cand_area, "cfg_L": 2, "rtl_sim": "pass", "gl_sim": "pass",
                                    "sta_analysis": "pass", "state": "eligible_gain"}},
            "cells": cells}


def status(**kw):
    st = {"code": CODE, "rnd": 1, "state": "eligible_gain", "grade_status": "GRADE OK", "rtl_sim": "pass",
          "gl_sim": "pass", "sta_analysis": "pass", "area_um2": "1001.5", "within_cap": True, "author_veto": False,
          "declared_L": 2, "cfg_L": 2, "prediction_L_mismatch": False, "numeric_target_met": False}
    st.update(kw)
    return st


ORIENT = {"slack": ("increase", "0.000001", "decimal"), "area": ("decrease", "0.0001", "decimal"),
          "L": ("equal", "", "integer"), "function": ("equal", "", "text")}


def pred(pid="p1", **kw):
    row = {"candidate": CODE, "row_type": "prediction", "source": "line 10", "criteria_version": "v1",
           "prediction_id": pid, "r1_ref": "", "id": "P1", "action": "pipeline the adder",
           "metric": "slack", "check": "setup", "corner": "ss_100C_1v60", "category": "global",
           "value_kind": "delta", "direction": "未知", "low": "未知", "high": "未知", "unit": "ns", "point": "",
           "basis": "rtl/dot4sat.v:10", "orientation": "", "epsilon": "", "source_field": "", "comparator": ""}
    row.update(kw)
    o = ORIENT.get(row["metric"])
    if o:
        row["orientation"], row["epsilon"], row["comparator"] = (kw.get("orientation", o[0]),
                                                                 kw.get("epsilon", o[1]),
                                                                 kw.get("comparator", o[2]))
    return row


def fc(fid="F1", expr=None, text="功能失败 OR 面积超限", **kw):
    row = {"candidate": CODE, "row_type": "failure_condition", "source": "line 30", "criteria_version": "v1",
           "fc_id": fid, "r1_ref": "", "text": text, "expr": expr}
    row.update(kw)
    return row


def atom(field, op, value):
    return {"atom": {"field": field, "op": op, "value": value}}


def judged(row, st=None, mx=None):
    """(actual, direction_judgment, range_judgment, judgment) as run() computes them for one row."""
    st = status() if st is None else st
    mx = mdoc() if mx is None else mx
    return judge.judge_row(row, st, mx)


# ---------------------------------------------------------------------------------------------- unit tests
class Judgments(unittest.TestCase):
    def test_predict_same_but_improved_is_against(self):
        r = judged(pred(direction="不变"), mx=mdoc(cand={("ss_100C_1v60", "setup", "global"): "-3.689726"}))
        self.assertEqual(r["direction_judgment"], "反对")
        self.assertEqual(r["judgment"], "反对")
        self.assertEqual(r["actual"], Decimal("0.500000"))

    def test_epsilon_boundary_slack(self):
        row = pred(direction="不变")
        for d, want in (("0.000001", "支持"), ("-0.000001", "支持"), ("0.0000011", "反对"),
                        ("-0.0000011", "反对")):
            self.assertEqual(judge.direction_judgment(row, Decimal(d)), want, d)
        self.assertEqual(judge.direction_judgment(pred(direction="改善"), Decimal("0.0000011")), "支持")
        self.assertEqual(judge.direction_judgment(pred(direction="退化"), Decimal("-0.0000011")), "支持")
        self.assertEqual(judge.direction_judgment(pred(direction="改善"), Decimal("0.000001")), "反对")

    def test_epsilon_boundary_area(self):
        row = pred(metric="area", check="", corner="", category="", unit="µm²", direction="不变")
        for d, want in (("0.0001", "支持"), ("-0.0001", "支持"), ("0.00011", "反对"), ("-0.00011", "反对")):
            self.assertEqual(judge.direction_judgment(row, Decimal(d)), want, d)

    def test_area_direction_is_decrease(self):
        row = pred(metric="area", check="", corner="", category="", unit="µm²", direction="改善")
        self.assertEqual(judge.direction_judgment(row, Decimal("-1")), "支持")
        self.assertEqual(judge.direction_judgment(row, Decimal("1")), "反对")
        r = judged(row, st=status(area_um2="990.0"))
        self.assertEqual(r["actual"], Decimal("-10.0"))
        self.assertEqual(r["judgment"], "支持")

    def test_point_only_not_judged(self):
        for point in ("-3.1", "约 -3.1"):
            r = judged(pred(point=point))
            self.assertEqual((r["direction_judgment"], r["range_judgment"], r["judgment"]), ("不判", "不判", "未判定"))
            self.assertEqual(r["format_problems"], [])

    def test_direction_with_point_only_judges_direction(self):
        r = judged(pred(direction="改善", point="0.3"))          # actual delta +0.189726: improvement
        self.assertEqual((r["direction_judgment"], r["range_judgment"], r["judgment"]), ("支持", "不判", "支持"))
        r = judged(pred(direction="退化", point="0.3"))
        self.assertEqual(r["judgment"], "反对")

    def test_unknown_direction_without_range_is_undetermined(self):
        r = judged(pred(direction="未知"))
        self.assertEqual(r["judgment"], "未判定")

    def test_direction_support_range_against_is_against(self):
        r = judged(pred(direction="改善", low="0.5", high="1.0"))
        self.assertEqual((r["direction_judgment"], r["range_judgment"], r["judgment"]), ("支持", "反对", "反对"))
        r = judged(pred(direction="改善", low="0.1", high="0.2"))
        self.assertEqual(r["judgment"], "支持")

    def test_one_sided_range_and_closed_endpoints(self):
        self.assertEqual(judge.range_judgment(pred(low="0.1"), Decimal("1000")), "支持")
        self.assertEqual(judge.range_judgment(pred(low="0.1"), Decimal("0.0999999")), "反对")
        self.assertEqual(judge.range_judgment(pred(high="0.1"), Decimal("-1000")), "支持")
        self.assertEqual(judge.range_judgment(pred(high="0.1"), Decimal("0.1000001")), "反对")
        self.assertEqual(judge.range_judgment(pred(low="0.1", high="0.2"), Decimal("0.1")), "支持")
        self.assertEqual(judge.range_judgment(pred(low="0.1", high="0.2"), Decimal("0.2")), "支持")
        self.assertEqual(judge.range_judgment(pred(), Decimal("0.2")), "不判")
        r = judged(pred(value_kind="absolute", low="-4.1", high="-3.9"))
        self.assertEqual((r["actual"], r["judgment"]), (Decimal("-4.000000"), "支持"))

    def test_low_greater_than_high_is_format_problem(self):
        row = pred(direction="改善", low="0.5", high="0.1")
        self.assertEqual(judge.range_judgment(row, Decimal("0.3")), "格式问题")
        r = judged(row)
        self.assertEqual((r["direction_judgment"], r["range_judgment"], r["judgment"]), ("支持", "格式问题", "支持"))
        self.assertTrue(any("low" in p for p in r["format_problems"]))

    def test_nonnumeric_nan_infinity_bad_unit_bad_enum_are_format_problems(self):
        for kw in ({"low": "abc"}, {"low": "NaN"}, {"high": "Infinity"}, {"high": "-inf"}, {"low": "约 0.1"}):
            row = pred(direction="改善", **kw)
            self.assertTrue(judge.format_problems(row), kw)
            r = judged(row)
            self.assertEqual(r["range_judgment"], "不判", kw)
            self.assertEqual(r["judgment"], "支持", kw)             # only the field is unknown; direction still judged
        row = pred(direction="改善", low="0.5", high="1.0", unit="ps")
        self.assertTrue(any("unit" in p for p in judge.format_problems(row)))
        self.assertEqual(judged(row)["range_judgment"], "不判")    # unit unclear -> range unknown
        row = pred(direction="变好", low="0.1", high="0.2")
        self.assertTrue(any("direction" in p for p in judge.format_problems(row)))
        r = judged(row)
        self.assertEqual((r["direction_judgment"], r["judgment"]), ("不判", "支持"))
        row = pred(metric="speed")
        self.assertTrue(judge.format_problems(row))
        self.assertEqual(judged(row)["judgment"], "未判定")
        row = pred(corner="ss")
        self.assertTrue(any("corner" in p for p in judge.format_problems(row)))
        row = pred(metric="L", check="", corner="", category="", value_kind="", direction="", low="", high="",
                   unit="", point="two")
        self.assertTrue(judge.format_problems(row))
        self.assertEqual(judged(row)["judgment"], "未判定")
        self.assertEqual(judge.format_problems(pred(direction="改善", low="+0.1", high="1e-1")), [])

    def test_no_result_vs_not_applicable_counted_separately(self):
        nr = judged(pred(direction="改善"), st=status(sta_analysis="not_run"), mx=None)
        self.assertEqual((nr["actual"], nr["judgment"]), ("no_result", "无结果"))
        na = judged(pred(direction="改善", category="reg2reg", corner="tt_025C_1v80"),
                    mx=mdoc(cand={("tt_025C_1v80", "setup", "reg2reg"): "not_applicable"}))
        self.assertEqual((na["actual"], na["judgment"]), ("not_applicable", "不适用"))
        self.assertEqual(judged(pred(metric="area", check="", corner="", category="", unit="µm²",
                                     direction="改善"), st=status(area_um2="not_available"))["judgment"], "无结果")
        counts = judge.summary_counts([dict(nr), dict(na), dict(na)])
        self.assertEqual((counts["无结果"], counts["不适用"]), (1, 2))

    def test_corner_all_takes_min_of_scope_and_check(self):
        cand = {(c, "setup", "reg2out"): "-1.000000" for c in CORNERS}
        cand[("ff_100C_1v95", "setup", "reg2out")] = "-2.500000"
        cand[("tt_100C_1v80", "hold", "reg2out")] = "-9.000000"      # other check: ignored
        cand[("tt_100C_1v80", "setup", "reg2reg")] = "-8.000000"     # other scope: ignored
        cand[("ss_n40C_1v60", "setup", "reg2out")] = "not_applicable"
        base = {(c, "setup", "reg2out"): "-3.000000" for c in CORNERS}
        mx = mdoc(cand=cand, base=base)
        row = pred(corner="all", category="reg2out", value_kind="absolute")
        self.assertEqual(judge.actual(row, status(), mx), Decimal("-2.500000"))
        self.assertEqual(judge.actual(pred(corner="all", category="reg2out"), status(), mx), Decimal("0.500000"))

    def test_function_pass_fail_noresult(self):
        row = pred(metric="function", check="", corner="", category="", value_kind="", direction="", low="",
                   high="", unit="", point="pass")
        self.assertEqual(judged(row)["judgment"], "支持")
        self.assertEqual(judged(row, st=status(gl_sim="fail", sta_analysis="not_run"), mx=None)["judgment"], "反对")
        r = judged(row, st=status(rtl_sim="pass", gl_sim="indeterminate"), mx=None)
        self.assertEqual((r["actual"], r["judgment"]), ("no_result", "无结果"))
        self.assertEqual(judged(dict(row, point="fail"), st=status(rtl_sim="fail", gl_sim="not_run"),
                                mx=None)["judgment"], "支持")

    def test_L_mismatch_still_judged_on_cfg_L(self):
        row = pred(metric="L", check="", corner="", category="", value_kind="", direction="", low="", high="",
                   unit="", point="3")
        st = status(declared_L=2, cfg_L=2, prediction_L_mismatch=True)
        r = judged(row, st=st)
        self.assertEqual((r["actual"], r["judgment"]), (2, "反对"))
        self.assertIn("预测不一致", r["reason"])
        self.assertEqual(judged(dict(row, point="2"), st=st)["judgment"], "支持")

    def test_delta_on_introduced_is_not_applicable(self):
        key = ("ss_100C_1v60", "setup", "reg2reg")
        mx = mdoc(cand={key: "-1.000000"}, base={key: "not_applicable"})
        r = judged(pred(category="reg2reg", direction="改善", low="0"), mx=mx)
        self.assertEqual((r["actual"], r["judgment"]), ("not_applicable", "不适用"))
        r = judged(pred(category="reg2reg", value_kind="absolute", direction="改善", low="-2", high="0"), mx=mx)
        self.assertEqual((r["direction_judgment"], r["judgment"]), ("不判", "支持"))

    def test_eval3_truth_tables(self):
        st = status(grade_status="GRADE FAIL", within_cap="not_available", sta_analysis="not_run")
        T = atom("status.grade_status", "is", "GRADE FAIL")
        F = atom("status.cfg_L", "==", "3")
        U = atom("status.within_cap", "is", "false")
        X = {"untestable": "时序明显变差"}
        ev = lambda e: judge.eval3(e, st, None)
        self.assertEqual([ev(T), ev(F), ev(U), ev(X)], [True, False, None, None])
        for a, b, want in ((T, T, True), (T, F, False), (T, U, None), (F, U, False), (U, U, None), (F, F, False)):
            self.assertEqual(ev({"and": [a, b]}), want, ("and", a, b))
        for a, b, want in ((T, T, True), (T, F, True), (T, U, True), (F, U, None), (U, U, None), (F, F, False)):
            self.assertEqual(ev({"or": [a, b]}), want, ("or", a, b))
        self.assertEqual([ev({"not": T}), ev({"not": F}), ev({"not": U})], [False, True, None])
        self.assertIsNone(ev(atom("status.no_such_key", "is", "x")))
        self.assertIsNone(ev(atom("matrix.ss_100C_1v60.setup.global.slack", "<", "0")))   # no matrix
        mx = mdoc()
        self.assertTrue(judge.eval3(atom("matrix.ss_100C_1v60.setup.global.slack", "<", "-3.999999"), st, mx))
        self.assertTrue(judge.eval3(atom("matrix.summary.worst_setup.slack", ">=", "-4"), st, mx))
        self.assertTrue(judge.eval3(atom("matrix.extra.area", ">", "1001"), st, mx))
        with self.assertRaises(judge.JudgeError):
            judge.eval3(atom("status.cfg_L", "<", "abc"), st, mx)

    def test_ordering_op_with_text_value_rejected(self):
        for op in ("<", "<=", "==", ">=", ">"):
            self.assertTrue(judge.expr_problems(atom("status.state", op, "grade_fail")), op)
            self.assertTrue(judge.expr_problems(atom("status.cfg_L", op, "NaN")), op)
        self.assertEqual(judge.expr_problems(atom("status.state", "is", "grade_fail")), [])
        self.assertEqual(judge.expr_problems(atom("status.cfg_L", "==", "2")), [])

    def test_failure_condition_judged_on_grade_fail(self):
        st = status(state="grade_fail", grade_status="GRADE FAIL", gl_sim="fail", sta_analysis="not_run",
                    within_cap="not_available", area_um2="not_available")
        expr = {"or": [atom("status.gl_sim", "is", "fail"), atom("status.within_cap", "is", "false")]}
        r = judged(fc(expr=expr), st=st, mx=None)
        self.assertEqual(r["judgment"], "触发")
        r = judged(fc(expr={"and": [atom("status.gl_sim", "is", "fail"), atom("status.within_cap", "is", "false")]}),
                   st=st, mx=None)
        self.assertEqual(r["judgment"], "未判定")
        r = judged(fc(expr=atom("status.gl_sim", "is", "pass")), st=st, mx=None)
        self.assertEqual(r["judgment"], "未触发")


# ---------------------------------------------------------------------------------------------- file tests
def extracted_of(rows):
    out = []
    k = 0
    for r in rows:
        if r["row_type"] == "prediction":
            k += 1
            out.append({"code": r["candidate"], "row_type": "prediction", "index": k,
                        **{c: r[c] for c in judge.EXTRACTED_PREDICTION_COLUMNS}})
        else:
            out.append({"code": r["candidate"], "row_type": "failure_condition", "fc_id": r["fc_id"],
                        "source": r["source"], "text": r["text"]})
    return out


def wbytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def wjsonl(path, rows):
    wbytes(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8"))


def wjson(path, obj):
    wbytes(path, (json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))


class FileBase(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="judge_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.case = os.path.join(self.tmp.name, "case")
        self.pred_dir = os.path.join(self.case, "revise", "predictions")

    def setup_round(self, rows, rnd=1, st=None, mx="default", code=CODE):
        wjsonl(os.path.join(self.pred_dir, f"r{rnd}_criteria.jsonl"), rows)
        wjsonl(os.path.join(self.pred_dir, f"r{rnd}_extracted.jsonl"), extracted_of(rows))
        wjson(os.path.join(self.case, "revise", "results", f"r{rnd}", code, "status.json"),
              status(rnd=rnd) if st is None else st)
        if mx is not None:
            wjson(os.path.join(self.case, "revise", "compare", f"r{rnd}_{code}.json"),
                  mdoc() if mx == "default" else mx)

    def run_quiet(self, fn, *a, **kw):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = fn(*a, **kw)
        return rc, buf.getvalue()


class Files(FileBase):
    def test_duplicate_id_only_first_judged(self):
        rows = [pred("p1", id="P1", direction="改善"), pred("p2", id="P1", direction="退化"),
                pred("p3", id="P2", direction="改善")]
        self.setup_round(rows)
        rc, out = self.run_quiet(judge.run, 1, case=self.case)
        self.assertEqual(rc, 0, out)
        got = [json.loads(ln) for ln in rp.read_bytes(os.path.join(self.pred_dir, "r1_judgments.jsonl"))
               .decode("utf-8").splitlines()]
        self.assertEqual([g["judgment"] for g in got], ["支持", "格式问题", "支持"])
        self.assertTrue(any("重复" in p for p in got[1]["format_problems"]))

    def test_evidence_recorded(self):
        rows = [pred("p1", direction="改善"),
                pred("p2", id="P2", metric="L", check="", corner="", category="", value_kind="", direction="", low="",
                     high="", unit="", point="2"),
                fc("F1", expr=atom("status.grade_status", "is", "GRADE FAIL"))]
        self.setup_round(rows)
        rc, out = self.run_quiet(judge.run, 1, case=self.case)
        self.assertEqual(rc, 0, out)
        got = [json.loads(ln) for ln in rp.read_bytes(os.path.join(self.pred_dir, "r1_judgments.jsonl"))
               .decode("utf-8").splitlines()]
        self.assertEqual(list(got[0])[-7:], list(judge.JUDGMENT_FIELDS))
        files = {e["file"] for e in got[0]["evidence"]}
        self.assertIn(f"revise/compare/r1_{CODE}.json", files)
        self.assertTrue(any("ss_100C_1v60" in e["field"] for e in got[0]["evidence"]))
        self.assertIn({"file": f"revise/results/r1/{CODE}/status.json", "field": "cfg_L"}, got[1]["evidence"])
        self.assertIn({"file": f"revise/results/r1/{CODE}/status.json", "field": "grade_status"}, got[2]["evidence"])
        self.assertEqual(got[2]["judgment"], "未触发")
        md = rp.read_bytes(os.path.join(self.pred_dir, "r1_judgments.md")).decode("utf-8")
        self.assertIn("r1_notes.jsonl", md)
        # check mode: same bytes -> 0; an edited judgments file -> 1
        self.assertEqual(self.run_quiet(judge.run, 1, check=True, case=self.case)[0], 0)
        wbytes(os.path.join(self.pred_dir, "r1_judgments.md"), b"edited\n")
        rc, out = self.run_quiet(judge.run, 1, check=True, case=self.case)
        self.assertEqual(rc, 1)
        self.assertIn("CHECK FAIL", out)

    def test_criteria_must_preserve_extracted_fields(self):
        rows = [pred("p1", direction="改善")]
        self.setup_round(rows)
        changed = dict(rows[0], low="0.1")                 # operator "fixed" a model field
        wjsonl(os.path.join(self.pred_dir, "r1_criteria.jsonl"), [changed])
        rc, out = self.run_quiet(judge.run, 1, case=self.case)
        self.assertEqual(rc, 1)
        self.assertIn("CRITERIA FAIL", out)
        self.assertFalse(os.path.exists(os.path.join(self.pred_dir, "r1_judgments.jsonl")))

    def test_ordering_op_with_text_value_is_criteria_fail(self):
        self.setup_round([fc("F1", expr={"or": [atom("status.state", "==", "grade_fail"),
                                                 atom("status.gl_sim", "is", "fail")]})])
        rc, out = self.run_quiet(judge.run, 1, case=self.case)
        self.assertEqual(rc, 1)
        self.assertIn("CRITERIA FAIL", out)
        self.assertIn("finite decimal", out)

    def make_baseline(self, area="1000.0", verdict_bytes=None):
        root = os.path.join(self.tmp.name, "F1")
        arch = os.path.join(root, "archive", judge.baseline.RUN)
        files = {"verdict.json": verdict_bytes if verdict_bytes is not None else
                 ('{"area_um2": ' + area + '}\n').encode("utf-8"),
                 "sta/sta_results.tsv": b"corner\tws\n"}
        for kind in ("max", "min"):
            for c in CORNERS:
                files[f"sta/path_{kind}_{c}.rpt"] = f"Corner: {c}\n".encode("ascii")
        sums = []
        for rel, data in files.items():
            wbytes(os.path.join(arch, *rel.split("/")), data)
            sums.append(f"{rp.sha256_bytes(data)}  ./{judge.baseline.RUN}/{rel}\n")
        wbytes(os.path.join(root, "archive", "SHA256SUMS"), "".join(sums).encode("ascii"))
        wbytes(os.path.join(root, "f1_run_verdict.json"), files["verdict.json"])
        wbytes(os.path.join(root, "sta_results.tsv"), files["sta/sta_results.tsv"])
        return root

    def test_area_delta_uses_baseline_without_compare(self):
        row = pred("p1", metric="area", check="", corner="", category="", unit="µm²", direction="改善")
        st = status(state="grade_fail", grade_status="GRADE FAIL", gl_sim="fail", sta_analysis="not_run",
                    area_um2="990.5")
        self.setup_round([row], st=st, mx=None)
        root = self.make_baseline()
        rc, out = self.run_quiet(judge.run, 1, case=self.case, base_root=root)
        self.assertEqual(rc, 0, out)
        got = json.loads(rp.read_bytes(os.path.join(self.pred_dir, "r1_judgments.jsonl")).decode("utf-8"))
        self.assertEqual((got["actual"], got["judgment"]), ("-9.5", "支持"))
        self.assertIn({"file": f"evidence/F1/archive/{judge.baseline.RUN}/verdict.json", "field": "area_um2"},
                      got["evidence"])
        # unreadable / malformed baseline verdict: CRITERIA FAIL, no traceback, nothing written
        os.remove(os.path.join(self.pred_dir, "r1_judgments.jsonl"))
        for bad in (b"{not json", b'{"area_um2": "x"}\n'):
            root = self.make_baseline(verdict_bytes=bad)
            rc, out = self.run_quiet(judge.run, 1, case=self.case, base_root=root)
            self.assertEqual(rc, 1, bad)
            self.assertIn("CRITERIA FAIL", out)
            self.assertIn("baseline verdict.json", out)
            self.assertFalse(os.path.exists(os.path.join(self.pred_dir, "r1_judgments.jsonl")))
        # baseline that fails verification
        root = self.make_baseline()
        wbytes(os.path.join(root, "f1_run_verdict.json"), b"{}\n")
        rc, out = self.run_quiet(judge.run, 1, case=self.case, base_root=root)
        self.assertEqual(rc, 1)
        self.assertIn("BASELINE FAIL", out)

    def test_tsv_view_is_deterministic(self):
        rows = [pred("p1", direction="改善", action="a\tb"),
                fc("F1", text="第一行\n第二行", expr={"or": [atom("status.gl_sim", "is", "fail"),
                                                           {"untestable": "x"}]})]
        self.setup_round(rows)
        tsv = os.path.join(self.pred_dir, "r1_criteria.tsv")
        self.assertEqual(self.run_quiet(judge.views, 1, case=self.case)[0], 0)
        first = rp.read_bytes(tsv)
        os.remove(tsv)
        self.assertEqual(self.run_quiet(judge.views, 1, case=self.case)[0], 0)
        self.assertEqual(rp.read_bytes(tsv), first)
        self.assertNotIn(b"\r", first)
        lines = first.decode("utf-8").split("\n")
        self.assertEqual(lines[-1], "")
        self.assertEqual(lines[0].split("\t"), list(judge.CRITERIA_COLUMNS))
        self.assertEqual(len(lines), 4)                    # header, two rows, final empty
        p, f = (dict(zip(judge.CRITERIA_COLUMNS, ln.split("\t"))) for ln in lines[1:3])
        self.assertEqual(json.loads(p["action"]), "a\tb")
        self.assertEqual(json.loads(f["text"]), "第一行\n第二行")
        self.assertEqual(json.loads(f["expr"]), rows[1]["expr"])
        self.assertEqual(p["fc_id"], "")
        self.assertEqual(f["metric"], "")

    def test_edited_tsv_view_detected(self):
        self.setup_round([pred("p1", direction="改善")])
        tsv = os.path.join(self.pred_dir, "r1_criteria.tsv")
        self.assertEqual(self.run_quiet(judge.views, 1, case=self.case)[0], 0)
        self.assertEqual(self.run_quiet(judge.views, 1, check=True, case=self.case)[0], 0)
        data = rp.read_bytes(tsv).replace("改善".encode("utf-8"), "退化".encode("utf-8"))
        wbytes(tsv, data)
        rc, out = self.run_quiet(judge.views, 1, check=True, case=self.case)
        self.assertEqual(rc, 1)
        self.assertIn("CHECK FAIL", out)
        os.remove(tsv)
        rc, out = self.run_quiet(judge.views, 1, check=True, case=self.case)
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
