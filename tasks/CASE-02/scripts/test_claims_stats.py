"""Unit tests of claims_stats.py for CASE-02 (protocol v0.3 sections 5.5, 7, 12; impl_plan Task 8). Run in WSL from
tasks/CASE-02/scripts: python3 -B -m unittest -v test_claims_stats"""
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
import claims_stats as cs  # noqa: E402


def row(**kw):
    r = dict.fromkeys(cs.COLUMNS, "")
    r.update({"id": "A-1-001", "code": "A", "round": "1", "field": "F1", "proposition": "-", "value": "尚不能确认",
              "review_status": "已复核", "scope_claimed": "-", "evidence_level": "-", "judgments": "-", "attribution": "-"})
    r.update(kw)
    return r


def full_round(code="A", rnd="1", **over):
    """A complete set of field rows for one model-round."""
    n = [0]

    def rid():
        n[0] += 1
        return f"{code}-{rnd}-{n[0]:03d}"
    rows = [row(id=rid(), code=code, round=rnd, field="F1", value="尚不能确认"),
            row(id=rid(), code=code, round=rnd, field="F2", value="假设"),
            row(id=rid(), code=code, round=rnd, field="F3", proposition="报告差异", value="充分", scope_claimed="R1/R2 summary"),
            row(id=rid(), code=code, round=rnd, field="F3", proposition="原因", value="不足", scope_claimed="in_b 全部"),
            row(id=rid(), code=code, round=rnd, field="F3", proposition="范围", value="不足", scope_claimed="in_b 全部"),
            row(id=rid(), code=code, round=rnd, field="F4", value="未定位"),
            row(id=rid(), code=code, round=rnd, field="F5", value="是"),
            row(id=rid(), code=code, round=rnd, field="F6", value="待执行核实"),
            row(id=rid(), code=code, round=rnd, field="F7", value="原理上能" if rnd == "1" else "线索"),
            row(id=rid(), code=code, round=rnd, field="F8", value="不适用" if rnd == "1" else "单独标记")]
    if rnd == "2":
        for r in rows:
            r["r2_action"] = "保持"
            r["r1_ref"] = r["id"].replace("-2-", "-1-")
    for r in rows:
        r.update(over)
    return rows


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="claims_", dir=c2paths.RUNS)
        self.addCleanup(shutil.rmtree, self.tmp)
        self.case = self.tmp
        os.makedirs(os.path.join(self.case, "queries", "round2", "A1_R2"))
        with open(os.path.join(self.case, "queries", "round2", "A1_R2", "calls.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"call_seq": 1, "status": "ok", "returned_out": [1, 66], "complete": True}) + "\n")
            f.write(json.dumps({"call_seq": 2, "status": "ok", "returned_out": None, "complete": False}) + "\n")
            f.write(json.dumps({"call_seq": 3, "status": "error", "returned_out": [70, 71], "complete": True}) + "\n")

    def problems(self, rows, evidence_rows=None):
        return cs.problems(rows, evidence_rows or [], self.case)


class TestFields(Base):
    def test_eight_fields_complete_round_ok(self):
        self.assertEqual(self.problems(full_round()), [])

    def test_eight_fields_or_whole_round_unobtained(self):
        rows = full_round()[:-1]                               # F8 missing
        self.assertTrue(any("F8" in p for p in self.problems(rows)))
        unobtained = [row(id="B-2-001", code="B", round="2", field="ROUND", value="未取得 / 不可评价",
                          note="第 1 轮两次作废，未启动第 2 轮", attribution="原因未定")]
        self.assertEqual(self.problems(unobtained), [])
        no_note = [row(id="B-2-001", code="B", round="2", field="ROUND", value="未取得 / 不可评价")]
        self.assertTrue(self.problems(no_note))

    def test_f3_three_rows_each_with_scope(self):
        rows = [r for r in full_round() if not (r["field"] == "F3" and r["proposition"] == "范围")]
        self.assertTrue(any("F3" in p and "范围" in p for p in self.problems(rows)))
        rows = full_round()
        [r for r in rows if r["proposition"] == "原因"][0]["scope_claimed"] = "-"
        self.assertTrue(any("scope_claimed" in p for p in self.problems(rows)))

    def test_f2_values_only_four(self):
        rows = full_round()
        [r for r in rows if r["field"] == "F2"][0]["value"] = "表述矛盾"
        self.assertTrue(any("F2" in p for p in self.problems(rows)))

    def test_contradiction_in_judgments_not_f2(self):
        rows = full_round()
        f1 = [r for r in rows if r["field"] == "F1"][0]
        f1["value"], f1["judgments"] = "表述矛盾", "表述矛盾"
        self.assertEqual(self.problems(rows), [])

    def test_f7_six_levels_unordered(self):
        self.assertEqual(set(cs.FIELD_VALUES["F7"]["2"]), {"线索", "名单级", "现象级", "局部确认", "目标集合完整", "未取得"})
        self.assertEqual(set(cs.FIELD_VALUES["F7"]["1"]), {"原理上能", "否"})
        rows = full_round(rnd="2")
        [r for r in rows if r["field"] == "F7"][0]["value"] = "实际完成"
        self.assertTrue(any("F7" in p for p in self.problems(rows + full_round())))
        self.assertFalse(hasattr(cs, "F7_ORDER"))

    def test_f8_round2_not_applicable_allowed_with_reason(self):
        rows = full_round(rnd="2") + full_round()
        f8 = [r for r in rows if r["field"] == "F8" and r["round"] == "2"][0]
        f8["value"] = "不适用"
        self.assertTrue(any("F8" in p for p in self.problems(rows)))
        f8["note"] = "第 2 轮没有空结果、报错、截断可供对待"
        self.assertEqual(self.problems(rows), [])

    def test_f8_round1_must_be_not_applicable(self):
        rows = full_round()
        [r for r in rows if r["field"] == "F8"][0]["value"] = "单独标记"
        self.assertTrue(any("F8" in p for p in self.problems(rows)))

    def test_unfinished_requires_attribution(self):
        rows = full_round(rnd="2") + full_round()
        f7 = [r for r in rows if r["field"] == "F7" and r["round"] == "2"][0]
        f7["value"], f7["judgments"], f7["attribution"] = "未取得", "判断合理;查询任务未完成", "-"
        self.assertTrue(any("attribution" in p for p in self.problems(rows)))
        f7["attribution"] = "流程限制：单实例截断"
        self.assertEqual(self.problems(rows), [])

    def test_judgment_labels_from_table(self):
        rows = full_round()
        rows[0]["judgments"] = "合理观察;不是表里的标签"
        self.assertTrue(any("judgments" in p for p in self.problems(rows)))

    def test_review_status_and_dissent(self):
        rows = full_round()
        rows[0]["review_status"] = "有分歧"
        self.assertTrue(any("dissent" in p for p in self.problems(rows)))
        rows[0]["dissent"] = "作者认为是假设"
        self.assertEqual(self.problems(rows), [])
        rows[0]["review_status"] = "随便"
        self.assertTrue(self.problems(rows))


class TestFactsAndEvidence(Base):
    def fact(self, rid, label="证实", **kw):
        return row(id=rid, field="fact", value=label, quote="x", evidence="package/intent.md:1", **kw)

    def cite(self, parent, rid, label="引用正确"):
        return row(id=rid, field="cite", value=label, parent_id=parent)

    def test_fact_needs_one_cite_and_max_ten(self):
        rows = full_round() + [self.fact("A-1-101"), self.cite("A-1-101", "A-1-102")]
        self.assertEqual(self.problems(rows), [])
        rows2 = full_round() + [self.fact("A-1-101")]
        self.assertTrue(any("证据引用" in p for p in self.problems(rows2)))
        many = full_round()
        for i in range(11):
            many += [self.fact(f"A-1-{200 + 2 * i:03d}"), self.cite(f"A-1-{200 + 2 * i:03d}", f"A-1-{201 + 2 * i:03d}")]
        self.assertTrue(any("10" in p for p in self.problems(many)))

    def test_evidence_map_complete_from_calls(self):
        ev = [{"code": "A", "round": "2", "port": "in_b[0]", "item": "max", "ctx": "R2", "scene": "ss_n40C_1v60",
               "run_id": "A1_R2", "call_seq": "1", "returned_range": "1-66", "element_row": "E3", "complete": "1",
               "mapping_rule": "E3", "review_status": "已复核", "dissent": ""}]
        self.assertEqual(self.problems(full_round(), ev), [])
        bad = [dict(ev[0], call_seq="2", complete="1")]
        self.assertTrue(any("complete" in p for p in self.problems(full_round(), bad)))
        err = [dict(ev[0], call_seq="3")]
        self.assertTrue(any("error" in p or "status" in p for p in self.problems(full_round(), err)))

    def test_partial_instance_evidence_counts(self):
        # call 1 is complete although call 3 of the same instance errored: no whole-instance gate
        ev = [{"code": "A", "round": "2", "port": "in_b[0]", "item": "min", "ctx": "R2", "scene": "ss_n40C_1v60",
               "run_id": "A1_R2", "call_seq": "1", "returned_range": "1-66", "element_row": "E3", "complete": "1",
               "mapping_rule": "E3", "review_status": "已复核", "dissent": ""}]
        self.assertEqual(self.problems(full_round(), ev), [])


class TestRound2(Base):
    def test_six_actions(self):
        self.assertEqual(set(cs.ACTIONS), {"没有再提", "保持", "提高确定程度", "降低确定程度", "修改结论", "明确撤回"})
        rows = full_round(rnd="2") + full_round()
        rows[0]["r2_action"] = "撤回"
        self.assertTrue(any("r2_action" in p for p in self.problems(rows)))

    def test_two_kinds_of_unrecognized(self):
        self.assertIn("未利用充分证据：未识别现象", cs.JUDGMENTS)
        self.assertIn("未利用充分证据：已识别现象未下结论", cs.JUDGMENTS)
        self.assertIn("完成名单级诊断", cs.JUDGMENTS)
        self.assertIn("完成现象级诊断", cs.JUDGMENTS)


class TestStats(Base):
    def test_parallel_judgments_not_summed_and_no_total_score(self):
        rows = full_round(rnd="2") + full_round()
        f1 = [r for r in rows if r["field"] == "F1" and r["round"] == "2"][0]
        f1["judgments"] = "合理观察;合理假设"
        text = cs.stats(rows, [], {"A": "模型甲"})
        self.assertIn("模型甲", text)
        self.assertIn("合理观察;合理假设", text)
        self.assertNotIn("总分", text)
        self.assertNotIn("排名", text)
        self.assertIn("分母", text)
        self.assertIn("复核状态", text)
        self.assertIn("F7", text)


def ev_row(**kw):
    e = {"code": "A", "round": "2", "port": "in_b[0]", "item": "min,max,clock", "ctx": "R2", "scene": "ss_n40C_1v60",
         "run_id": "A1_R2", "call_seq": "1", "returned_range": "1-66", "element_row": "E3", "complete": "1",
         "mapping_rule": "E3", "review_status": "已复核", "dissent": ""}
    e.update(kw)
    if "mapping_rule" not in kw:
        e["mapping_rule"] = e["element_row"]
    return e


class TestR6Evidence(Base):
    """CASE02_R6 M2: evidence rows are checked against the call they cite (range, context, element/item), and the F7
    level claimed for a model-round needs the element set of that level; S4: action and limit counts in stats."""

    def r2(self, level):
        rows = full_round() + full_round(rnd="2")
        for r in rows:
            if r["field"] == "F7" and r["round"] == "2":
                r["value"] = level
                r["evidence_level"] = level
        return rows

    def test_returned_range_must_lie_inside_the_call(self):
        probs = self.problems(self.r2("名单级"), [ev_row(element_row="E1", item="list", returned_range="60-70")])
        self.assertTrue(any("returned_range" in p for p in probs), probs)

    def test_ctx_must_match_run_id(self):
        probs = self.problems(self.r2("名单级"), [ev_row(element_row="E1", item="list", ctx="R1")])
        self.assertTrue(any("ctx" in p for p in probs), probs)

    def test_element_and_item_must_agree(self):
        probs = self.problems(self.r2("名单级"), [ev_row(element_row="E1", item="max")])
        self.assertTrue(any("item" in p for p in probs), probs)
        probs = self.problems(self.r2("现象级"), [ev_row(element_row="E8")])
        self.assertTrue(any("E8" in p for p in probs), probs)
        probs = self.problems(self.r2("现象级"), [ev_row(element_row="E3", scene="")])
        self.assertTrue(any("scene" in p for p in probs), probs)

    def test_puts_output_is_not_tool_evidence(self):
        with open(os.path.join(self.case, "queries", "round2", "A1_R2", "calls.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"call_seq": 4, "status": "ok", "returned_out": [80, 81], "complete": True, "cmd": "puts"}) + "\n")
        probs = self.problems(self.r2("名单级"), [ev_row(element_row="E2", item="list", call_seq="4", returned_range="80-81")])
        self.assertTrue(any("puts" in p for p in probs), probs)

    def test_level_needs_its_elements(self):
        lst = ev_row(element_row="E1", item="list")
        arr = ev_row(element_row="E3")
        self.assertTrue(any("名单级" in p for p in self.problems(self.r2("名单级"), [arr])))
        self.assertEqual([p for p in self.problems(self.r2("名单级"), [lst]) if "名单级" in p], [])
        self.assertTrue(any("现象级" in p for p in self.problems(self.r2("现象级"), [lst])))
        self.assertTrue(any("局部确认" in p for p in self.problems(self.r2("局部确认"), [arr])))
        self.assertEqual([p for p in self.problems(self.r2("局部确认"), [lst, arr]) if "局部确认" in p], [])
        probs = self.problems(self.r2("目标集合完整"), [lst, arr])
        self.assertTrue(any("目标集合完整" in p and "63" in p for p in probs), probs)
        full = [lst] + [ev_row(port=f"in_b[{i}]") for i in range(64)]
        self.assertEqual([p for p in self.problems(self.r2("目标集合完整"), full) if "目标集合完整" in p], [])

    def test_expected_rounds_fixed_denominator(self):
        rows = full_round()
        probs = cs.problems(rows, [], self.case, expected_rounds=[("A", "1"), ("A", "2"), ("B", "1")])
        self.assertTrue(any("A round 2" in p for p in probs), probs)
        self.assertTrue(any("B round 1" in p for p in probs), probs)
        self.assertEqual([p for p in cs.problems(rows, [], self.case, expected_rounds=[("A", "1")]) if "missing" in p], [])

    def test_stats_count_actions_and_limits(self):
        rows = full_round() + full_round(rnd="2")
        inst = [{"code": "A", "qid": "A1", "ctx": "R2", "truncated": True, "attribution": "流程限制：单实例截断", "raw_lines": 39000, "returned_lines": 2001},
                {"code": "A", "qid": "A2", "ctx": "R2", "truncated": False, "attribution": "流程限制：总预算", "raw_lines": 50, "returned_lines": 0}]
        text = cs.stats(rows, [], {"A": "模型甲"}, instances=inst)
        self.assertIn("保持", text)
        self.assertIn("流程限制：单实例截断", text)
        self.assertIn("39000", text)


if __name__ == "__main__":
    unittest.main()
