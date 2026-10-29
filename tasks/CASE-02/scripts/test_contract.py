"""Unit tests of contract.py (protocol v0.3 section 6.4; impl_plan Task 2). Run in WSL from tasks/CASE-02/scripts:
  python3 -B -m unittest -v test_contract"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2paths  # noqa: E402
import contract  # noqa: E402

RULES = c2paths.RULES
CONTRACT = os.path.join(RULES, "contract.json")
ALLOW = os.path.join(RULES, "allow_query.txt")
WHATIF = os.path.join(RULES, "allow_whatif.txt")
SETUP = os.path.join(RULES, "setup_commands.txt")


def lines(n, width=60, prefix="L"):
    return [f"{prefix}{i:06d} " + "x" * (width - 8) for i in range(n)]


class TestLoad(unittest.TestCase):
    def test_values_from_plan(self):
        c = contract.load(CONTRACT)
        self.assertEqual(c.per_instance_max_lines, 2000)
        self.assertEqual(c.per_instance_max_bytes, 262144)
        self.assertEqual((c.query_seconds, c.process_seconds, c.process_max_bytes), (600, 1200, 52428800))
        self.assertEqual(c.tcl_command_limit, 1000000)
        self.assertEqual((c.max_requests, c.max_logical_instances, c.max_executions), (12, 72, 144))
        self.assertEqual(c.keep_order, ["declared_priority", "qid_numeric", "R1_before_R2"])
        self.assertTrue(c.budget_ready)            # filled by Task 6 (budget.md section 3)

    def test_budget_ready_when_filled(self):
        with open(CONTRACT, encoding="utf-8") as f:
            d = json.load(f)
        d["total_budget_tokens"], d["token_bytes_ratio"] = 100000, 3.2
        c = contract.from_dict(d)
        self.assertTrue(c.budget_ready)


class TestCount(unittest.TestCase):
    def test_count_excludes_begin_end(self):
        norm = ["=== QUERY BEGIN (query) ===", "CMD: check_setup", "Warning: x", "=== QUERY END rc=0 ==="]
        self.assertEqual(contract.count(norm), 2)


class TestTruncate(unittest.TestCase):
    def setUp(self):
        self.c = contract.load(CONTRACT)

    def test_truncate_under_limit_unchanged(self):
        t = contract.truncate(lines(2000), self.c)
        self.assertFalse(t["truncated"])
        self.assertEqual(t["returned_lines"], lines(2000))
        self.assertEqual((t["omitted_lines"], t["raw_lines"], t["cut_by"], t["marker_index"]), (0, 2000, None, None))
        self.assertEqual(t["raw_bytes"], sum(len(l.encode()) + 1 for l in lines(2000)))
        self.assertEqual(t["returned_bytes"], t["raw_bytes"])

    def test_truncate_6500_lines_keeps_1000_1000_and_marker(self):
        src = lines(6500, width=40)
        t = contract.truncate(src, self.c)
        self.assertTrue(t["truncated"])
        self.assertEqual(t["cut_by"], "lines")
        self.assertEqual(len(t["returned_lines"]), 2001)
        self.assertEqual(t["returned_lines"][:1000], src[:1000])
        self.assertEqual(t["returned_lines"][1001:], src[-1000:])
        self.assertEqual(t["marker_index"], 1000)
        self.assertEqual(t["omitted_lines"], 4500)
        marker = t["returned_lines"][1000]
        self.assertIn("省略 4500 行", marker)
        self.assertIn("原始 6500 行", marker)
        self.assertIn(f"{t['raw_bytes']} 字节", marker)

    def test_truncate_bytes_first_1500_lines_300B(self):
        src = lines(1500, width=300)
        t = contract.truncate(src, self.c)
        self.assertTrue(t["truncated"])
        self.assertEqual(t["cut_by"], "bytes")
        self.assertLessEqual(t["returned_bytes"], 262144)
        kept = len(t["returned_lines"]) - 1
        self.assertEqual(kept, 2 * (kept // 2))      # head and tail halves of equal size
        self.assertEqual(t["returned_lines"][:kept // 2], src[:kept // 2])
        self.assertEqual(t["returned_lines"][kept // 2 + 1:], src[-(kept // 2):])
        self.assertEqual(t["omitted_lines"], 1500 - kept)

    def test_truncate_single_huge_line(self):
        src = ["a" * 300000, "short"]
        t = contract.truncate(src, self.c)
        self.assertTrue(t["truncated"])
        self.assertTrue(t["returned_lines"][0].startswith("a" * 131072))
        self.assertTrue(t["returned_lines"][0].endswith("[本行截断]"))
        self.assertLessEqual(t["returned_bytes"], 262144)

    def test_truncate_utf8_multibyte_boundary(self):
        src = ["时序" * 40] * 1500          # 240 bytes per line
        t = contract.truncate(src, self.c)
        self.assertEqual(t["cut_by"], "bytes")
        for l in t["returned_lines"]:
            l.encode("utf-8")              # every returned line is valid text (no split code point)
        self.assertLessEqual(t["returned_bytes"], 262144)

    def test_marker_not_counted_in_returned_bytes(self):
        src = lines(3000, width=40)
        t = contract.truncate(src, self.c)
        content = [l for i, l in enumerate(t["returned_lines"]) if i != t["marker_index"]]
        self.assertEqual(t["returned_bytes"], sum(len(l.encode()) + 1 for l in content))


class TestMapRange(unittest.TestCase):
    def test_map_range_head_tail_and_crossing(self):
        c = contract.load(CONTRACT)
        src = lines(6500, width=40)
        t = contract.truncate(src, c)
        self.assertEqual(contract.map_range(t, (10, 20)), (10, 20))
        self.assertEqual(contract.map_range(t, (6400, 6500)), (1901, 2001))
        self.assertIsNone(contract.map_range(t, (990, 1010)))
        self.assertIsNone(contract.map_range(t, (3000, 3005)))
        t0 = contract.truncate(src[:100], c)
        self.assertEqual(contract.map_range(t0, (5, 7)), (5, 7))


class TestRender(unittest.TestCase):
    def setUp(self):
        with open(CONTRACT, encoding="utf-8") as f:
            d = json.load(f)
        d["total_budget_tokens"], d["token_bytes_ratio"] = 120000, 3.0
        self.c = contract.from_dict(d)
        self.text = contract.render_context_section(self.c, ALLOW, WHATIF, SETUP)

    def words(self, path):
        with open(path, encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip() and not l.startswith("#")]

    def test_render_lists_every_allowed_command_once_in_file_order(self):
        for path in (ALLOW, WHATIF, SETUP):
            ws = self.words(path)
            pos = [self.text.index("`" + w + "`") for w in ws]
            self.assertEqual(pos, sorted(pos), path)
            for w in ws:
                self.assertGreaterEqual(self.text.count("`" + w + "`"), 1, w)   # create_clock is in two lists

    def test_render_no_answer_words(self):
        import re
        for bad in (r"in_b", r"(?<![\d_])64(?![\d_])", r"(?<![\d_])132(?![\d_])", r"(?<![\d_])198(?![\d_])",
                    "建议", "推荐", "组合", r"missing", r"correct", r"restored"):
            self.assertIsNone(re.search(bad, self.text), bad)

    def test_render_mentions_limits(self):
        for s in ("2000", "256 KiB", "600", "1200", "50 MiB", "1000000", "120000", "12 条"):
            self.assertIn(s, self.text, s)
        self.assertIn("Error 103", self.text)
        self.assertIn("flush", self.text)

    def test_render_refuses_without_budget(self):
        with open(CONTRACT, encoding="utf-8") as f:
            d = json.load(f)
        d["total_budget_tokens"], d["token_bytes_ratio"] = None, None
        c = contract.from_dict(d)
        with self.assertRaises(contract.ContractError):
            contract.render_context_section(c, ALLOW, WHATIF, SETUP)


class TestWorkloads(unittest.TestCase):
    def test_workload_files_exist_and_expect_no_truncation(self):
        c = contract.load(CONTRACT)
        ws = contract.workloads(c)
        self.assertEqual([w["name"] for w in ws], [f"W0{i}" for i in range(1, 9)])
        for w in ws:
            self.assertTrue(os.path.isfile(os.path.join(c2paths.CASE, w["file"])), w["file"])
            self.assertFalse(w["expect_truncated"])
            self.assertLessEqual(w["raw_lines"], c.per_instance_max_lines)


if __name__ == "__main__":
    unittest.main()
