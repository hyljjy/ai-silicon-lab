"""Unit tests of claims_stats.py. Run: python3 -B -m unittest test_claims_stats"""
import json
import os
import tempfile
import unittest

import claims_stats as cs
import run_query as rq

N = "0123456789abcdef"


def row(**kw):
    r = dict.fromkeys(cs.COLUMNS, "")
    r.update({"id": "A-1-001", "code": "A", "round": "1", "type_initial": "事实", "type": "事实",
              "label": "证实", "query_ids": "base_B02"})
    r.update(kw)
    return r


def cite(parent, rid, label="引用正确"):
    return row(id=rid, type_initial="证据引用", type="证据引用", label=label, query_ids="", parent_id=parent)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="claims_test_")
        self.addCleanup(self.tmp.cleanup)
        self.diag = self.tmp.name
        # result codes exactly as run_query.classify produces them (never hand-written)
        done = rq.classify("query", ["out"], 0, "completed", N)
        self.result("base", "base_B02", {"env_ok": True, "query_status": "completed", "codes": done,
                                          "strict_log": True, "query_log_ok": True, "mode": "query"})
        self.result("recheck", "rc_whatif", {"env_ok": True, "query_status": "completed", "mode": "whatif",
                                              "codes": rq.classify("whatif", ["out"], 0, "completed", N),
                                              "strict_log": True, "query_log_ok": True})
        self.result("recheck", "rc_crash", {"env_ok": True, "query_status": "crashed:-11", "mode": "query",
                                             "codes": rq.classify("query", ["out"], None, "crashed:-11", N)})
        os.makedirs(os.path.join(self.diag, "package"))
        with open(os.path.join(self.diag, "package", "case01_sdc.tcl"), "w", encoding="utf-8") as f:
            f.write("".join(f"line {i}\n" for i in range(1, 11)))

    def result(self, group, qid, data):
        p = os.path.join(self.diag, "queries", group, qid)
        os.makedirs(p)
        with open(os.path.join(p, "result.json"), "w", encoding="utf-8") as f:
            json.dump(data, f)

    def problems(self, rows):
        return " | ".join(cs.problems(rows, self.diag))


class TestClaims(Base):
    def test_valid_rows(self):
        rows = [row(), cite("A-1-001", "A-1-002"),
                row(id="A-1-003", type_initial="假设", type="假设", label="支持", falsifier_given="是",
                    query_ids="rc_whatif"),
                row(id="B-1-001", code="B", label="推翻", author_label="无法核对", query_ids=""),
                cite("B-1-001", "B-1-002", "无引用")]
        self.assertEqual(cs.problems(rows, self.diag), [])
        text = cs.stats(rows)
        self.assertIn("| A | 1 | 事实 | 1 | 证实 1 |", text)
        self.assertIn("作者改动的标签：1 / 5", text)
        self.assertIn("给出证伪条件的假设：1 / 1", text)

    def test_rule_violations(self):
        msgs = self.problems([
            row(), row(),                                                 # duplicate id; facts without citation rows
            row(id="x2", type="假设", falsifier_given="", label="支持"),    # retyped without reason; falsifier
            row(id="x3", label="支持"),                                     # wrong label for a fact
            row(id="x4", label="证实", query_ids=""),                       # confirmed without a query or citation
            row(id="x5", label="证实", query_ids="nope"),                   # not a collected run
            row(id="x6", label="证实", query_ids="rc_crash"),               # run does not meet 7.3 d
            row(id="x7", label="证实", query_ids="rc_whatif"),              # fact on a whatif run
            row(id="x8", type_initial="假设", type="假设", falsifier_given="否", label="未判定", query_ids=""),
            cite("nobody", "x9"),
            row(id="x10", code="D")])
        for needle in ("duplicate id", "retyped without a reason", "falsifier_given", "not allowed for type",
                       "needs query_ids or a package", "not a collected run", "minimum conditions", "whatif run",
                       "未判定 needs", "parent_id must name", "exactly one 证据引用", "bad code"):
            self.assertIn(needle, msgs)

    def test_whatif_run_supports_a_hypothesis_but_never_confirms_a_fact(self):
        hyp = row(id="A-1-001", type_initial="假设", type="假设", falsifier_given="是", label="支持",
                  query_ids="rc_whatif")
        self.assertEqual(cs.problems([hyp], self.diag), [])
        self.assertIn("whatif run", self.problems([row(query_ids="rc_whatif"), cite("A-1-001", "A-1-002")]))
        self.assertIn("支持 without query_ids", self.problems([dict(hyp, query_ids="")]))

    def test_material_citation_confirms_or_refutes_a_fact(self):
        for lab in ("证实", "推翻"):
            fact = row(label=lab, query_ids="-", evidence="package/case01_sdc.tcl:7")
            self.assertEqual(cs.problems([fact, cite("A-1-001", "A-1-002")], self.diag), [], lab)
        ranged = row(query_ids="-", evidence="package/case01_sdc.tcl:3-10; 手算 27.91-0.5559")
        self.assertEqual(cs.problems([ranged, cite("A-1-001", "A-1-002")], self.diag), [])
        for bad in ("package/case01_sdc.tcl:11", "package/case01_sdc.tcl:5-3", "package/nope.tcl:1"):
            msgs = self.problems([row(query_ids="-", evidence=bad), cite("A-1-001", "A-1-002")])
            self.assertIn("is not a line range", msgs, bad)

    def test_round2_rows_and_transitions(self):
        rows = [row(), cite("A-1-001", "A-1-002"),
                row(id="A-2-001", round="2", r2_action="保持", r1_ref="A-1-001"), cite("A-2-001", "A-2-002"),
                row(id="A-2-003", round="2", type_initial="查询", type="查询", label="语法错误", query_ids="",
                    r2_action="新增")]
        rows[3]["round"] = "2"
        rows[3]["r2_action"] = "新增"
        self.assertEqual(cs.problems(rows, self.diag), [])
        self.assertIn("| A | 证实 → 保持 | 1 |", cs.stats(rows))
        bad = [row(), cite("A-1-001", "A-1-002"), row(id="A-2-001", round="2", r2_action="改了", r1_ref="")]
        self.assertIn("r2_action must be", self.problems(bad))

    def test_mapping_names(self):
        self.assertIn("| kimi | 1 | 事实 |", cs.stats([row()], {"A": "kimi"}))

    def test_load_checks_columns(self):
        p = os.path.join(self.tmp.name, "c.tsv")
        with open(p, "w", encoding="utf-8") as f:
            f.write("# c\nid\tcode\n1\tA\n")
        with self.assertRaises(SystemExit):
            cs.load(p)


if __name__ == "__main__":
    unittest.main()
