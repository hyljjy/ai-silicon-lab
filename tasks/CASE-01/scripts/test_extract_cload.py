import os
import subprocess
import sys
import unittest

from extract_cload import extract

LIB_HDR = 'library ("x") {\n  capacitive_load_unit(1.0000000000, "pf");\n'
CELL_OK = ('  cell ("sky130_fd_sc_hd__buf_4") {\n    pin ("A") {\n      capacitance : 0.0024000000;\n'
           '      rise_capacitance : 0.0025;\n    }\n    pin ("X") {\n      direction : "output";\n    }\n  }\n')


class TestExtract(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(extract(LIB_HDR + CELL_OK + "}\n"), 0.0024)

    def test_missing_pin(self):
        with self.assertRaises(ValueError):
            extract(LIB_HDR + CELL_OK.replace('pin ("A")', 'pin ("B")') + "}\n")

    def test_capacitance_from_other_cell_not_used(self):
        other = '  cell ("sky130_fd_sc_hd__buf_4") {\n    pin ("A") {\n      direction : "input";\n    }\n  }\n' \
                '  cell ("sky130_fd_sc_hd__buf_8") {\n    pin ("A") {\n      capacitance : 0.9;\n    }\n  }\n'
        with self.assertRaises(ValueError):
            extract(LIB_HDR + other + "}\n")

    def test_wrong_unit(self):
        with self.assertRaises(ValueError):
            extract(LIB_HDR.replace('"pf"', '"ff"') + CELL_OK + "}\n")

    def test_real_lib(self):
        hd, kit = os.environ.get("SKY130_HD"), os.environ.get("SKY130_KIT")
        if not hd or not kit:
            self.skipTest("needs login shell env")
        lib = os.path.join(hd, "lib", "sky130_fd_sc_hd__tt_025C_1v80.lib")
        r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "extract_cload.py"),
                            lib, os.path.join(kit, "MANIFEST.txt")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('"value_pf": 0.0024', r.stdout)


if __name__ == "__main__":
    unittest.main()
