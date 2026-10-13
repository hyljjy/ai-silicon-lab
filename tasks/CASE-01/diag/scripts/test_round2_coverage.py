"""Unit tests of round2_coverage.py. Run: python3 -B -m unittest test_round2_coverage"""
import unittest

import claims_stats as cs
import round2_coverage as rc


def row(rid, typ="事实", label="证实", r1_ref="", action=""):
    r = dict.fromkeys(cs.COLUMNS, "")
    code, rnd = rid[0], rid.split("-")[1]
    r.update(id=rid, code=code, round=rnd, type=typ, type_initial=typ, label=label, r1_ref=r1_ref, r2_action=action)
    return r


class TestCoverage(unittest.TestCase):
    def setUp(self):
        self.rows = [
            row("A-1-001"), row("A-1-002", "证据引用", "引用正确"),
            row("A-1-003", label="推翻"), row("A-1-004", "假设", "支持"),
            row("A-2-001", r1_ref="A-1-001", action="保持"), row("A-2-002", "证据引用", "引用正确"),
            row("A-2-003", "假设", "支持", r1_ref="A-1-004", action="修改"),
            row("A-2-004", "假设", "支持", r1_ref="A-1-004", action="保持"),
            row("A-2-005", "假设", "支持", action="新增"),
        ]

    def test_counts_round1_judgments_mentioned_in_round2(self):
        cov = rc.coverage(self.rows)
        # citation rows are not judgments; A-1-004 is mentioned twice but counted once
        self.assertEqual(cov["A"]["事实"], (1, 2))
        self.assertEqual(cov["A"]["假设"], (1, 1))

    def test_refuted_round1_facts_not_mentioned_are_listed(self):
        self.assertEqual(rc.unmentioned_refuted(self.rows), ["A-1-003"])

    def test_modifications_of_facts_and_hypotheses(self):
        self.assertEqual(rc.modified_judgments(self.rows), [("A-2-003", "A-1-004", "支持", "支持")])

    def test_report_names_models_when_given(self):
        text = rc.report(self.rows, {"A": "claude"})
        self.assertIn("| claude | 事实 | 1 | 2 |", text)
        self.assertIn("A-1-003", text)


if __name__ == "__main__":
    unittest.main()
