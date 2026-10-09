import os
import tempfile
import unittest

import logcheck

ABC = 'ABC: Warning: Detected 9 multi-output cells (for example, "sky130_fd_sc_hd__fa_1").'
RULE = "yosys\t" + r'^ABC: Warning: Detected 9 multi-output cells \(for example, "sky130_fd_sc_hd__fa_1"\)\.$' \
       + "\treviewed\n"


def tmp(text):
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, "w") as f:
        f.write(text)
    return path


class TestLogcheck(unittest.TestCase):
    def test_whitelisted_warning_passes_and_is_counted(self):
        rules = logcheck.load_rules(tmp(RULE))
        problems, hits = logcheck.scan("yosys", tmp("ok\n" + ABC + "\n" + ABC + "\n"), rules)
        self.assertEqual(problems, [])
        self.assertEqual(hits, {1: 2})

    def test_rule_is_tool_specific(self):
        rules = logcheck.load_rules(tmp(RULE))
        problems, _ = logcheck.scan("sta", tmp(ABC + "\n"), rules)
        self.assertEqual(len(problems), 1)

    def test_runtime_warning_in_sim_log_fails(self):
        problems, _ = logcheck.scan("iverilog", tmp("WARNING: tb.v:3: codex runtime warning probe\n"), [])
        self.assertTrue(problems and "unreviewed warning" in problems[0])

    def test_sta_warning_fails(self):
        problems, _ = logcheck.scan("sta", tmp("Warning 366: x.tcl line 3, port '__probe__' not found.\n"), [])
        self.assertEqual(len(problems), 1)

    def test_errors_never_pass(self):
        rules = logcheck.load_rules(tmp("sta\t.*\twide rule must not excuse errors\n"))
        for line in ("Error: sta_run.tcl, 12 invalid command name", "Error 1520: bad", "ERROR: yosys failed",
                     "tb.v:5: error: syntax", "FATAL: tb.v:9: boom"):
            problems, _ = logcheck.scan("sta", tmp(line + "\n"), rules)
            self.assertTrue(problems and "error" in problems[0], line)

    def test_python_traceback_fails(self):
        problems, _ = logcheck.scan("python", tmp("Traceback (most recent call last):\n  File \"x.py\"\n"
                                                  "ValueError: bad\n"), [])
        self.assertEqual(len(problems), 1)
        self.assertIn("Traceback", problems[0])

    def test_plain_lines_pass(self):
        problems, _ = logcheck.scan("yosys", tmp("Chip area for module '\\dot4sat': 1.0\nWarnings: none\n"), [])
        self.assertEqual(problems, [])

    def test_malformed_rule_rejected(self):
        with self.assertRaises(logcheck.RuleError):
            logcheck.load_rules(tmp("yosys\tonly-two-fields\n"))
        with self.assertRaises(logcheck.RuleError):
            logcheck.load_rules(tmp("vcs\tx\treason\n"))


if __name__ == "__main__":
    unittest.main()
