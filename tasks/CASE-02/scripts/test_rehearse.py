"""Unit tests of rehearse.py (protocol v0.3 step 4; impl_plan Task 10). Run in WSL from tasks/CASE-02/scripts:
  python3 -B -m unittest -v test_rehearse"""
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
import rehearse  # noqa: E402

REH = os.path.join(c2paths.RULES, "rehearsal")


class TestSpecAndCoverage(unittest.TestCase):
    def test_spec_generates_every_group(self):
        spec = rehearse.load_spec()
        self.assertGreaterEqual(len(spec["groups"]), 12)
        tmp = tempfile.mkdtemp(prefix="reh_", dir=c2paths.RUNS)
        try:
            rehearse.generate(spec, tmp)
            for g in spec["groups"]:
                for f in ("answer_r1.md", "answer_r2.md", "returns.md", "returns_bytes.json", "expected.tsv"):
                    self.assertTrue(os.path.isfile(os.path.join(tmp, g["name"], f)), (g["name"], f))
            self.assertTrue(os.path.isfile(os.path.join(tmp, "coverage.tsv")))
        finally:
            shutil.rmtree(tmp)

    def test_coverage_every_row_hit(self):
        spec = rehearse.load_spec()
        cov = rehearse.coverage_targets()
        hit = rehearse.coverage_hits(spec)
        missing = [t for t in cov if t not in hit]
        self.assertEqual(missing, [], f"targets without a rehearsal group: {missing}")

    def test_required_targets_include_every_decision_row_and_field_value(self):
        cov = set(rehearse.coverage_targets())
        for j in cs.JUDGMENTS:
            if j != "-":
                self.assertIn(("judgment_row", j), cov)
        for f, per_round in cs.FIELD_VALUES.items():
            for rnd, vals in per_round.items():
                for v in vals:
                    self.assertIn(("field_value", f"{f}/{rnd}/{v}"), cov)
        for shape in rehearse.QUERY_SHAPES:
            self.assertIn(("query_shape", shape), cov)


class TestRun(unittest.TestCase):
    def test_result_lists_groups_and_passes(self):
        tmp = tempfile.mkdtemp(prefix="rehrun_", dir=c2paths.RUNS)
        try:
            spec = rehearse.load_spec()
            rehearse.generate(spec, tmp)
            rehearse.operator_fill().write_all(spec, tmp)
            ok, report = rehearse.run(spec, tmp)
            self.assertTrue(ok, report)
            for g in spec["groups"]:
                self.assertIn(g["name"], report)
            self.assertTrue(os.path.isfile(os.path.join(tmp, "result.md")))
        finally:
            shutil.rmtree(tmp)

    def test_budget_uses_bytes_not_lines(self):
        spec = rehearse.load_spec()
        g = next(g for g in spec["groups"] if g["name"].endswith("over_budget"))
        alloc = rehearse.allocate_group(g)
        self.assertTrue(alloc["dropped"], "the over-budget group must drop an instance")
        self.assertTrue(all("rendered_bytes" in i for i in g["instances"]))

    def test_extraction_matches_expected_requests(self):
        spec = rehearse.load_spec()
        for g in spec["groups"]:
            units = rehearse.extract_group(g)
            self.assertEqual([u["ctx_requested"] for u in units], [i["ctx_requested"] for i in g["requests"]], g["name"])
            self.assertEqual([u["priority"] for u in units], [i.get("priority") for i in g["requests"]], g["name"])

    def test_claims_of_every_group_pass_validation(self):
        spec = rehearse.load_spec()
        cases = rehearse._fake_case(spec)              # the fake calls.jsonl files the evidence rows point to
        fill = rehearse.operator_fill().FILL
        for g in spec["groups"]:
            r1, r2, ev = fill[g["name"]]
            rows = rehearse.rows_from_labels({"1": r1, "2": r2})
            self.assertEqual(cs.problems(rows, ev, case=cases[g["name"]], expected_rounds=[("A", "1"), ("A", "2")]), [], g["name"])


class TestR6Rehearsal(unittest.TestCase):
    """CASE02_R6 M1/M2: corrected expectations, a genuine local-confirmation group, operator claims filled apart from
    the expected labels, the comparison covers scope_claimed and facts, returns carry a fixed body."""

    def group(self, suffix):
        return next(g for g in rehearse.load_spec()["groups"] if g["name"].endswith(suffix))

    def test_phenomenon_only_groups_are_not_local_confirmation(self):
        for suffix in ("few_unconstrained_no_overreach", "fail_then_hold", "overclaims_from_partial"):
            self.assertEqual(self.group(suffix)["expected"]["2"]["F7"], "现象级", suffix)
        self.assertEqual(self.group("few_unconstrained_no_overreach")["expected"]["2"]["F3"]["原因"][0], "不足")
        self.assertEqual(self.group("overclaims_from_partial")["expected"]["2"]["F3"]["原因"][1], "in_b 全部（R2）")

    def test_local_confirmation_group_exists_with_both_elements(self):
        g = self.group("local_confirm")
        self.assertEqual(g["expected"]["2"]["F7"], "局部确认")
        self.assertIn("完成局部诊断", g["expected"]["2"]["judgments"])

    def test_extra_propositions_recorded_as_facts(self):
        self.assertTrue(any("R1" in f["quote"] for f in self.group("split_across_instances")["expected"]["2"]["facts"]))
        self.assertTrue(any("R1" in f["quote"] for f in self.group("one_context_only")["expected"]["2"]["facts"]))

    def test_f8_not_applicable_when_nothing_failed(self):
        for suffix in ("only_checksetup_honest", "loop_without_flush", "split_across_instances"):
            e = self.group(suffix)["expected"]["2"]
            self.assertEqual(e["F8"], "不适用", suffix)
            self.assertTrue(e["f8_note"], suffix)

    def test_over_budget_text_names_the_dropped_instances(self):
        self.assertIn("A3 R2", self.group("over_budget")["r2_text"])
        self.assertNotIn("A5", self.group("over_budget")["r2_text"])

    def test_operator_claims_are_not_generated_from_expected(self):
        tmp = tempfile.mkdtemp(prefix="rehop_", dir=c2paths.RUNS)
        try:
            spec = rehearse.load_spec()
            rehearse.generate(spec, tmp)
            self.assertFalse(os.path.exists(os.path.join(tmp, spec["groups"][0]["name"], "claims_rehearsal.tsv")))
            ok, report = rehearse.run(spec, tmp)
            self.assertFalse(ok)
            self.assertIn("operator claims missing", report)
        finally:
            shutil.rmtree(tmp)

    def test_run_with_operator_fill_passes_and_compares_scope(self):
        tmp = tempfile.mkdtemp(prefix="rehfill_", dir=c2paths.RUNS)
        try:
            spec = rehearse.load_spec()
            rehearse.generate(spec, tmp)
            rehearse.operator_fill().write_all(spec, tmp)
            ok, report = rehearse.run(spec, tmp)
            self.assertTrue(ok, report)
            g = spec["groups"][0]
            p = os.path.join(tmp, g["name"], "claims_rehearsal.tsv")
            rows = rehearse.read_tsv(p)
            for r in rows:
                if r["field"] == "F3" and r["round"] == "2" and r["proposition"] == "原因":
                    r["scope_claimed"] = "改过的范围"
            rehearse.write_tsv(p, rehearse.CLAIM_COLS, rows)
            ok, report = rehearse.run(spec, tmp)
            self.assertFalse(ok)
            self.assertIn("scope_claimed", report)
        finally:
            shutil.rmtree(tmp)

    def test_returns_have_a_body_to_review(self):
        g = self.group("split_across_instances")
        self.assertTrue(all(i.get("body") for i in g["instances"]), "every instance needs a fixed output body")


if __name__ == "__main__":
    unittest.main()
