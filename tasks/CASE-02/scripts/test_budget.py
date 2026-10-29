"""Unit tests of budget.py (protocol v0.3 section 6.4 (b)(c); impl_plan Task 5). Run in WSL from tasks/CASE-02/scripts:
  python3 -B -m unittest -v test_budget"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "scripts")
              if os.path.basename(os.path.dirname(HERE)) == "impl" else HERE)
import c2paths  # noqa: E402
import budget  # noqa: E402
import contract  # noqa: E402


def c(total=1000, ratio=4.0):
    with open(os.path.join(c2paths.RULES, "contract.json"), encoding="utf-8") as f:
        d = json.load(f)
    d["total_budget_tokens"], d["token_bytes_ratio"] = total, ratio
    return contract.from_dict(d)


def inst(qid, ctx, rendered, priority=None, returned=None, truncated=False, raw_lines=10):
    return {"qid": qid, "ctx": ctx, "rendered_bytes": rendered, "returned_bytes": returned if returned is not None else rendered,
            "priority": priority, "truncated": truncated, "raw_lines": raw_lines, "returned_lines": raw_lines}


class TestAllocate(unittest.TestCase):
    def test_all_fit(self):
        a = budget.allocate([inst("A1", "R1", 400), inst("A1", "R2", 400)], c(total=1000, ratio=1.0))
        self.assertEqual([i["qid"] + i["ctx"] for i in a["returned"]], ["A1R1", "A1R2"])
        self.assertEqual(a["dropped"], [])
        self.assertEqual((a["total_tokens"], a["budget_tokens"]), (800, 1000))

    def test_second_context_dropped_last_with_reason(self):
        a = budget.allocate([inst("A1", "R1", 600), inst("A1", "R2", 600)], c(total=1000, ratio=1.0))
        self.assertEqual([i["ctx"] for i in a["returned"]], ["R1"])
        self.assertEqual(a["dropped"][0]["qid"], "A1")
        self.assertEqual(a["dropped"][0]["ctx"], "R2")
        self.assertEqual(a["dropped"][0]["rule"], "R1_before_R2")
        self.assertEqual(a["dropped"][0]["attribution"], "流程限制：总预算")

    def test_declared_priority_first(self):
        ins = [inst("A1", "R1", 600), inst("A2", "R1", 600, priority=1)]
        a = budget.allocate(ins, c(total=1000, ratio=1.0))
        self.assertEqual([i["qid"] for i in a["returned"]], ["A2"])
        self.assertEqual(a["dropped"][0]["qid"], "A1")
        self.assertEqual(a["dropped"][0]["rule"], "declared_priority")

    def test_qid_numeric_order(self):
        ins = [inst("A10", "R1", 600), inst("A2", "R1", 600)]
        a = budget.allocate(ins, c(total=1000, ratio=1.0))
        self.assertEqual([i["qid"] for i in a["returned"]], ["A2"])
        self.assertEqual(a["dropped"][0]["rule"], "qid_numeric")

    def test_exact_budget_boundary(self):
        a = budget.allocate([inst("A1", "R1", 500), inst("A2", "R1", 500)], c(total=1000, ratio=1.0))
        self.assertEqual(len(a["returned"]), 2)

    def test_one_token_over(self):
        a = budget.allocate([inst("A1", "R1", 500), inst("A2", "R1", 501)], c(total=1000, ratio=1.0))
        self.assertEqual(len(a["returned"]), 1)
        self.assertEqual(a["dropped"][0]["qid"], "A2")

    def test_ratio_converts_bytes_to_tokens_by_division(self):
        a = budget.allocate([inst("A1", "R1", 4000)], c(total=1000, ratio=4.0))
        self.assertEqual(a["total_tokens"], 1000)
        self.assertEqual(len(a["returned"]), 1)
        a2 = budget.allocate([inst("A1", "R1", 4001)], c(total=1000, ratio=4.0))
        self.assertEqual(a2["returned"], [])

    def test_everything_after_first_drop_is_dropped(self):
        ins = [inst("A1", "R1", 900), inst("A2", "R1", 200), inst("A3", "R1", 50)]
        a = budget.allocate(ins, c(total=1000, ratio=1.0))
        self.assertEqual([i["qid"] for i in a["returned"]], ["A1"])
        self.assertEqual([d["qid"] for d in a["dropped"]], ["A2", "A3"])

    def test_refuses_without_budget(self):
        with self.assertRaises(contract.ContractError):
            budget.allocate([inst("A1", "R1", 1)], contract.load(os.path.join(c2paths.RULES, "contract.json")))


class TestStatement(unittest.TestCase):
    def test_statement_four_items_fixed_sentence(self):
        ins = [inst("A1", "R1", 600, raw_lines=120), inst("A1", "R2", 600, raw_lines=130, truncated=True)]
        a = budget.allocate(ins, c(total=1000, ratio=1.0))
        s = budget.statement(a, c(total=1000, ratio=1.0))
        self.assertIn("① 总预算", s)
        self.assertIn("1000 token", s)
        self.assertIn("② 已交还", s)
        self.assertIn("A1 R1", s)
        self.assertIn("③ 未交还", s)
        self.assertIn("A1 R2", s)
        self.assertIn("R1 先于 R2", s)
        self.assertIn("130 行", s)
        self.assertTrue(s.rstrip().endswith("以上未交还的结果已完整归档，未交还原因是累计超过公开的总预算，不是查询失败。"))

    def test_statement_no_dropped(self):
        a = budget.allocate([inst("A1", "R1", 100)], c(total=1000, ratio=1.0))
        s = budget.statement(a, c(total=1000, ratio=1.0))
        self.assertIn("③ 未交还的实例：（无）", s)
        self.assertIn("以上未交还的结果已完整归档", s)

    def test_statement_marks_truncated(self):
        a = budget.allocate([inst("A1", "R1", 100, truncated=True)], c(total=1000, ratio=1.0))
        self.assertIn("已截断", budget.statement(a, c(total=1000, ratio=1.0)))


if __name__ == "__main__":
    unittest.main()
