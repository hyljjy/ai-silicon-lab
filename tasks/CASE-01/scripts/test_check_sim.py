import unittest

from check_sim import check

GOOD = "VCD info\nSIM PASS checked=2856\ntb.v:120: $finish called at 1 (1ps)\n"


class TestCheckSim(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check(GOOD, 0, 2856), (True, "checked=2856"))

    def test_nonzero_exit(self):
        self.assertFalse(check(GOOD, 1, 2856)[0])

    def test_count_mismatch(self):
        self.assertFalse(check(GOOD, 0, 2857)[0])

    def test_fail_line_wins(self):
        self.assertFalse(check("SIM FAIL VALID MISMATCH\n" + GOOD, 0, 2856)[0])

    def test_two_pass_lines(self):
        self.assertFalse(check(GOOD + "SIM PASS checked=2856\n", 0, 2856)[0])

    def test_substring_not_enough(self):
        self.assertFalse(check("note: SIM PASS checked=2856 (copied)\n", 0, 2856)[0])

    def test_zero_checked(self):
        self.assertFalse(check("SIM PASS checked=0\n", 0, 0)[0])

    def test_empty_log(self):
        self.assertFalse(check("", 0, 2856)[0])


if __name__ == "__main__":
    unittest.main()
