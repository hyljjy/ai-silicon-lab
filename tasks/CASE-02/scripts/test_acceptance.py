"""Unit tests of acceptance.py's pure checks (CASE02_R6 M6). Run in WSL from tasks/CASE-02/scripts:
  python3 -B -m unittest -v test_acceptance"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import acceptance as acc  # noqa: E402

PORTS = [f"in_a[{i}]" for i in range(64)] + [f"in_b[{i}]" for i in range(64)] + ["in_valid", "rst"]


def arrival(p):
    return f"{p} (clk ^) r 0.00:5.58 f 0.00:5.58" if not p.startswith("in_b") else f"{p}  r 0.00:0.00 f 0.00:0.00"


class TestOrderedPairs(unittest.TestCase):
    def test_all_130_ports_once(self):
        n, missing, extra = acc.ordered_pairs("CASE02-CMD: foreach ...\n" + "\n".join(arrival(p) for p in PORTS) + "\n")
        self.assertEqual((n, missing, extra), (130, [], []))

    def test_missing_port_and_duplicate(self):
        text = "\n".join(arrival(p) for p in PORTS if p != "in_b[7]") + "\n" + arrival("in_a[0]") + "\n"
        n, missing, extra = acc.ordered_pairs(text)
        self.assertEqual(missing, ["in_b[7]"])
        self.assertEqual(extra, ["in_a[0]"])


class TestVersions(unittest.TestCase):
    def test_versions_consistent(self):
        a = {"sample": "a", "ran": True, "result": {"executor": {"scripts/run_query.py": "x"}, "contract_version": "v"}}
        b = {"sample": "b", "ran": True, "result": {"executor": {"scripts/run_query.py": "x"}, "contract_version": "v"}}
        c = {"sample": "c", "ran": True, "result": {"executor": {"scripts/run_query.py": "y"}, "contract_version": "v"}}
        self.assertEqual(acc.version_problems({"a": a, "b": b}, {"scripts/run_query.py": "x"}), [])
        probs = acc.version_problems({"a": a, "c": c}, {"scripts/run_query.py": "x"})
        self.assertTrue(any("c" in p for p in probs))
        probs2 = acc.version_problems({"a": a}, {"scripts/run_query.py": "z"})
        self.assertTrue(probs2)


if __name__ == "__main__":
    unittest.main()
