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
                for f in ("answer_r1.md", "answer_r2.md", "returns.md", "returns_bytes.json", "claims_rehearsal.tsv", "expected.tsv"):
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
        rehearse._fake_case(spec)                      # the fake calls.jsonl files the evidence rows point to
        for g in spec["groups"]:
            rows, ev = rehearse.claims_rows(g)
            self.assertEqual(cs.problems(rows, ev, case=rehearse.FAKE_CASE), [], g["name"])


if __name__ == "__main__":
    unittest.main()
