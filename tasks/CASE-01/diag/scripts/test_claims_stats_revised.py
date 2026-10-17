"""Tests for claims_stats_revised.py (post-unblinding review overlay; not a pre-registered file)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claims_stats_revised as rev  # noqa: E402

HEAD = "\t".join(["id", "codex_flag", "author_decision", "new_label", "new_r2_action", "reason", "date"])


def write(text):
    fd, path = tempfile.mkstemp(suffix=".tsv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def row(**kw):
    r = {c: "" for c in rev.COLUMNS}
    r.update(kw)
    return r


class TestDecisions(unittest.TestCase):
    def test_last_row_wins_and_comments_skipped(self):
        p = write("# c\n" + HEAD + "\n"
                  "X-1-001\t-\t维持\t-\t-\tfirst\t2026-10-16\n"
                  "X-1-001\t-\t修订\t反对\t-\tsecond\t2026-10-17\n")
        try:
            d = rev.load_decisions(p)
        finally:
            os.remove(p)
        self.assertEqual(d["X-1-001"]["new_label"], "反对")
        self.assertEqual(d["X-1-001"]["reason"], "second")

    def test_bad_column_count_fails(self):
        p = write(HEAD + "\nX-1-001\t-\t维持\t-\n")
        try:
            with self.assertRaises(SystemExit):
                rev.load_decisions(p)
        finally:
            os.remove(p)


class TestOverlay(unittest.TestCase):
    def setUp(self):
        self.rows = [row(id="A-1-001", round="1", type="假设", label="支持", note=""),
                     row(id="A-2-001", round="2", type="假设", label="支持", r1_ref="A-1-001", r2_action="保持", note="n")]

    def test_label_and_action_overridden_on_a_copy(self):
        dec = {"A-1-001": {"new_label": "反对", "new_r2_action": "-", "author_decision": "修订", "reason": "r1"},
               "A-2-001": {"new_label": "-", "new_r2_action": "修改", "author_decision": "修订", "reason": "r2"}}
        out, changed_labels, changed_actions = rev.overlay(self.rows, dec)
        self.assertEqual(out[0]["label"], "反对")
        self.assertEqual(out[1]["r2_action"], "修改")
        self.assertEqual(self.rows[0]["label"], "支持")  # original untouched
        self.assertEqual(changed_labels, ["A-1-001"])
        self.assertEqual(changed_actions, ["A-2-001"])
        self.assertIn("揭盲后修订", out[0]["note"])

    def test_unknown_id_fails(self):
        with self.assertRaises(SystemExit):
            rev.overlay(self.rows, {"Z-9-999": {"new_label": "反对", "new_r2_action": "-",
                                                "author_decision": "修订", "reason": "x"}})

    def test_label_not_allowed_for_type_fails(self):
        with self.assertRaises(SystemExit):
            rev.overlay(self.rows, {"A-1-001": {"new_label": "引用错误", "new_r2_action": "-",
                                                "author_decision": "修订", "reason": "x"}})


if __name__ == "__main__":
    unittest.main()
