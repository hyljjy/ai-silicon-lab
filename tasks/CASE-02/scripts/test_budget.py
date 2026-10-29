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


def fits(returned, dropped, ratio=1.0):
    """The exact token cost of returning `returned` with `dropped` listed in the statement (the allocation rule
    charges the statement and the dropped markers too, R6 M5)."""
    total = 10 ** 9
    for _ in range(4):      # the statement prints the budget figure too, so the cost depends on the budget's own width
        cc = c(total=total, ratio=ratio)
        new_total, _ = budget._cost([dict(i, tokens=0, returned=True) for i in returned], [dict(d, rule="-") for d in dropped], cc)
        if new_total == total:
            break
        total = new_total
    return total


class TestAllocate(unittest.TestCase):
    def test_all_fit(self):
        ins = [inst("A1", "R1", 400), inst("A1", "R2", 400)]
        a = budget.allocate(ins, c(total=fits(ins, []), ratio=1.0))
        self.assertEqual([i["qid"] + i["ctx"] for i in a["returned"]], ["A1R1", "A1R2"])
        self.assertEqual(a["dropped"], [])
        self.assertEqual(a["total_tokens"], fits(ins, []))

    def test_second_context_dropped_last_with_reason(self):
        ins = [inst("A1", "R1", 600), inst("A1", "R2", 600)]
        a = budget.allocate(ins, c(total=fits(ins[:1], ins[1:]), ratio=1.0))
        self.assertEqual([i["ctx"] for i in a["returned"]], ["R1"])
        self.assertEqual((a["dropped"][0]["qid"], a["dropped"][0]["ctx"], a["dropped"][0]["rule"]), ("A1", "R2", "R1_before_R2"))
        self.assertEqual(a["dropped"][0]["attribution"], "流程限制：总预算")

    def test_declared_priority_first(self):
        ins = [inst("A1", "R1", 600), inst("A2", "R1", 600, priority=1)]
        a = budget.allocate(ins, c(total=fits(ins[1:], ins[:1]), ratio=1.0))
        self.assertEqual([i["qid"] for i in a["returned"]], ["A2"])
        self.assertEqual((a["dropped"][0]["qid"], a["dropped"][0]["rule"]), ("A1", "declared_priority"))

    def test_qid_numeric_order(self):
        ins = [inst("A10", "R1", 600), inst("A2", "R1", 600)]
        a = budget.allocate(ins, c(total=fits(ins[1:], ins[:1]), ratio=1.0))
        self.assertEqual([i["qid"] for i in a["returned"]], ["A2"])
        self.assertEqual(a["dropped"][0]["rule"], "qid_numeric")

    def test_exact_budget_boundary(self):
        ins = [inst("A1", "R1", 500), inst("A2", "R1", 500)]
        exact = fits(ins, [])
        self.assertEqual(len(budget.allocate(ins, c(total=exact, ratio=1.0))["returned"]), 2)

    def test_one_token_over(self):
        ins = [inst("A1", "R1", 500), inst("A2", "R1", 500)]
        a = budget.allocate(ins, c(total=fits(ins, []) - 1, ratio=1.0))
        self.assertEqual(len(a["returned"]), 1)
        self.assertEqual(a["dropped"][0]["qid"], "A2")

    def test_ratio_converts_bytes_to_tokens_by_division(self):
        ins = [inst("A1", "R1", 4000)]
        a = budget.allocate(ins, c(total=fits(ins, [], ratio=4.0), ratio=4.0))
        self.assertEqual(len(a["returned"]), 1)
        a2 = budget.allocate([inst("A1", "R1", 4004)], c(total=fits(ins, [], ratio=4.0), ratio=4.0))
        self.assertEqual(a2["returned"], [])

    def test_everything_after_first_drop_is_dropped(self):
        ins = [inst("A1", "R1", 900), inst("A2", "R1", 200), inst("A3", "R1", 50)]
        a = budget.allocate(ins, c(total=fits(ins[:1], ins[1:]), ratio=1.0))
        self.assertEqual([i["qid"] for i in a["returned"]], ["A1"])
        self.assertEqual([d["qid"] for d in a["dropped"]], ["A2", "A3"])

    def test_refuses_without_budget(self):
        with self.assertRaises(contract.ContractError):
            budget.allocate([inst("A1", "R1", 1)], c(total=None, ratio=None))


class TestStatement(unittest.TestCase):
    def test_statement_four_items_fixed_sentence(self):
        ins = [inst("A1", "R1", 600, raw_lines=120), inst("A1", "R2", 600, raw_lines=130, truncated=True)]
        total = fits(ins[:1], ins[1:])
        a = budget.allocate(ins, c(total=total, ratio=1.0))
        s = budget.statement(a, c(total=total, ratio=1.0))
        self.assertIn("① 总预算", s)
        self.assertIn(f"{total} token", s)
        self.assertIn("② 已交还", s)
        self.assertIn("A1 R1", s)
        self.assertIn("③ 未交还", s)
        self.assertIn("A1 R2", s)
        self.assertIn("R1 先于 R2", s)
        self.assertIn("130 行", s)
        self.assertTrue(s.rstrip().endswith("以上未交还的结果已完整归档，未交还原因是累计超过公开的总预算，不是查询失败。"))

    def test_statement_no_dropped(self):
        a = budget.allocate([inst("A1", "R1", 100)], c(total=2000, ratio=1.0))
        s = budget.statement(a, c(total=2000, ratio=1.0))
        self.assertIn("③ 未交还的实例：（无）", s)
        self.assertIn("以上未交还的结果已完整归档", s)

    def test_statement_marks_truncated(self):
        a = budget.allocate([inst("A1", "R1", 100, truncated=True)], c(total=2000, ratio=1.0))
        self.assertIn("已截断", budget.statement(a, c(total=2000, ratio=1.0)))


if __name__ == "__main__":
    unittest.main()


class TestR6Budget(unittest.TestCase):
    """CASE02_R6 M5: the allocation charges everything that reaches the prompt (markers, statement), and the whole
    round-2 prompt is checked against the input capacity, not against the results budget again."""

    def test_allocation_charges_statement_and_markers(self):
        cc = c(total=2000, ratio=1.0)
        ins = [inst("A1", "R1", 400), inst("A1", "R2", 400)]
        a = budget.allocate(ins, cc)
        self.assertEqual(len(a["returned"]), 2)
        self.assertGreater(a["total_tokens"], 800)          # + the statement that lists them
        self.assertGreater(a["overhead_tokens"], 0)
        a2 = budget.allocate([inst("A1", "R1", 1500), inst("A1", "R2", 200)], cc)
        self.assertEqual(len(a2["returned"]), 1)             # 1500 + statement fits; + 200 + its marker does not

    def test_capacity_check_separate_from_results_budget(self):
        cc = c(total=1000, ratio=1.0)
        chk = budget.prompt_capacity(rendered_bytes=5000, results_bytes=900, c=cc, capacity_tokens=20000)
        self.assertTrue(chk["results_ok"])
        self.assertTrue(chk["capacity_ok"])
        chk2 = budget.prompt_capacity(rendered_bytes=25000, results_bytes=900, c=cc, capacity_tokens=20000)
        self.assertFalse(chk2["capacity_ok"])
        self.assertTrue(chk2["results_ok"])
