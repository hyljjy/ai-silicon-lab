"""Unit tests of records.py (protocol v0.3 sections 5.2, 5.3 layer 2, 5.6). Run in WSL from tasks/CASE-02/scripts:
  python3 -B -m unittest -v test_records
Fixtures: fixtures/records/correct = the F1 archived sta/ records (the correct version equals F1 byte for byte);
fixtures/records/missing = the pre-validation missing_1 run (archived outside git, copied here)."""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2paths  # noqa: E402
import records  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "records")
CORRECT = os.path.join(FIX, "correct")
MISSING = os.path.join(FIX, "missing")
RULES = os.path.join(os.path.dirname(HERE), "rules")
SCENES = ["tt_025C_1v80", "tt_100C_1v80", "ss_100C_1v60", "ss_n40C_1v60", "ff_n40C_1v95", "ff_100C_1v95"]


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TmpCopy:
    """A temporary editable copy of a fixture run directory."""

    def __init__(self, src):
        self.src = src

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="rec_", dir=c2paths.RUNS)
        self.dir = os.path.join(self.tmp, "run")
        shutil.copytree(self.src, self.dir)
        return self.dir

    def __exit__(self, *a):
        shutil.rmtree(self.tmp)


def edit(path, old, new):
    text = read(path)
    assert old in text, (path, old)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace(old, new, 1))


class TestFileSet(unittest.TestCase):
    def test_record_file_set_is_50(self):
        self.assertEqual(len(records.RECORD_FILES), 50)
        self.assertIn("expanded.sdc", records.RECORD_FILES)
        self.assertIn("path_min_ff_100C_1v95.rpt", records.RECORD_FILES)
        self.assertIn("dcalc_tt_025C_1v80_min.txt", records.RECORD_FILES)
        self.assertIn("cat_ss_n40C_1v60_reg2out_min.rpt", records.RECORD_FILES)

    def test_metadata_files_not_counted_as_extra(self):
        with TmpCopy(MISSING) as run:
            for name in ("cmd.txt", "valid.json", "SHA256SUMS", "lib_lines_raw.txt", "snapshot.log"):
                with open(os.path.join(run, name), "w") as f:
                    f.write("x\n")
            os.makedirs(os.path.join(run, "musts"))
            r = records.compare("missing_vs_correct", run, CORRECT, RULES)
            self.assertEqual(r["extra_files"], [])
            self.assertTrue(r["ok"], r["problems"])

    def test_unknown_record_file_fails(self):
        with TmpCopy(MISSING) as run:
            with open(os.path.join(run, "cat_ss_n40C_1v60_reg2reg_max.rpt"), "w") as f:
                f.write("x\n")
            r = records.compare("missing_vs_correct", run, CORRECT, RULES)
            self.assertFalse(r["ok"])
            self.assertEqual(r["extra_files"], ["cat_ss_n40C_1v60_reg2reg_max.rpt"])

    def test_missing_file_in_set_fails(self):
        with TmpCopy(MISSING) as run:
            os.remove(os.path.join(run, "dcalc_ff_100C_1v95_min.txt"))
            r = records.compare("missing_vs_correct", run, CORRECT, RULES)
            self.assertFalse(r["ok"])
            self.assertEqual(r["missing_files"], ["dcalc_ff_100C_1v95_min.txt"])


class TestRelations(unittest.TestCase):
    def test_correct_vs_f1_identical(self):
        r = records.compare("correct_vs_f1", CORRECT, CORRECT, RULES)
        self.assertTrue(r["ok"], r["problems"])
        self.assertEqual(r["allowed_changes_seen"], [])
        self.assertTrue(r["lib"]["normalized_ok"])
        self.assertTrue(r["lib"]["raw_identical"])

    def test_missing_vs_correct_only_allowed_changes(self):
        r = records.compare("missing_vs_correct", MISSING, CORRECT, RULES)
        self.assertTrue(r["ok"], r["problems"])
        seen = sorted(r["allowed_changes_seen"])
        expected = sorted([f"WS\t{c}\tmax" for c in SCENES] + [f"CAT\t{c}\tin2reg\tmax" for c in SCENES]
                          + [f"cat_{c}_in2reg_max.rpt" for c in SCENES] + [f"path_max_{c}.rpt" for c in SCENES])
        self.assertEqual(seen, expected)
        self.assertEqual(len(r["numeric"]), 12)
        self.assertTrue(all(n["ok"] for n in r["numeric"]), r["numeric"])
        self.assertIs(r["mutation_verified"], True)

    def test_missing_with_correct_expanded_sdc_is_not_verified(self):
        with TmpCopy(MISSING) as run:
            shutil.copyfile(os.path.join(CORRECT, "expanded.sdc"), os.path.join(run, "expanded.sdc"))
            r = records.compare("missing_vs_correct", run, CORRECT, RULES)
            self.assertFalse(r["ok"])
            self.assertIs(r["mutation_verified"], False)

    def test_missing_extra_change_fails(self):
        with TmpCopy(MISSING) as run:
            edit(os.path.join(run, "sta_results.tsv"), "WS\ttt_025C_1v80\tmin\t0.09305387279663745",
                 "WS\ttt_025C_1v80\tmin\t0.09305387279663746")
            r = records.compare("missing_vs_correct", run, CORRECT, RULES)
            self.assertFalse(r["ok"])
            self.assertTrue(any("WS\ttt_025C_1v80\tmin" in p for p in r["problems"]), r["problems"])

    def test_query_env_vs_formal_missing_requires_identity(self):
        self.assertTrue(records.compare("query_env_vs_formal", MISSING, MISSING, RULES)["ok"])
        with TmpCopy(MISSING) as run:
            edit(os.path.join(run, "sta_results.tsv"), "WS\tss_n40C_1v60\tmax\t-4.172594832200332",
                 "WS\tss_n40C_1v60\tmax\t-4.172594832200333")
            r = records.compare("query_env_vs_formal", run, MISSING, RULES)
            self.assertFalse(r["ok"], "a drift in an otherwise allowed-to-differ record must fail in strict mode")

    def test_restored_any_byte_difference_fails(self):
        self.assertTrue(records.compare("restored_vs_correct", CORRECT, CORRECT, RULES)["ok"])
        with TmpCopy(CORRECT) as run:
            path = os.path.join(run, "cat_tt_100C_1v80_reg2out_min.rpt")
            with open(path, "ab") as f:
                f.write(b" ")
            r = records.compare("restored_vs_correct", run, CORRECT, RULES)
            self.assertFalse(r["ok"])
            self.assertTrue(any("cat_tt_100C_1v80_reg2out_min.rpt" in p for p in r["problems"]))

    def test_unknown_relation_rejected(self):
        with self.assertRaises(ValueError):
            records.compare("missing_vs_f1", MISSING, CORRECT, RULES)


class TestLib(unittest.TestCase):
    def test_parse_lib_line(self):
        line = "LIB\tsky130_fd_sc_hd__tt_025C_1v80\t/home/eda/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
        self.assertEqual(records.parse_lib_line(line, RULES),
                         ("sky130_fd_sc_hd__tt_025C_1v80", "sky130_fd_sc_hd__tt_025C_1v80.lib"))

    def test_lib_prefix_not_registered_rejected(self):
        line = "LIB\tsky130_fd_sc_hd__tt_025C_1v80\t/opt/pdk/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
        with self.assertRaises(records.LibPrefixError):
            records.parse_lib_line(line, RULES)

    def test_lib_filename_matches_libname(self):
        line = "LIB\tsky130_fd_sc_hd__tt_025C_1v80\t/home/eda/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_100C_1v80.lib"
        with self.assertRaises(records.LibPrefixError):
            records.parse_lib_line(line, RULES)

    def test_lib_raw_lines_saved(self):
        r = records.compare("missing_vs_correct", MISSING, CORRECT, RULES)
        self.assertEqual(len(r["lib"]["raw_lines"]), 6)
        self.assertTrue(r["lib"]["raw_lines"][0].startswith("LIB\t"))


class TestNumeric(unittest.TestCase):
    def test_check_setup_must_be_0_or_1(self):
        with TmpCopy(MISSING) as run:
            edit(os.path.join(run, "sta_results.tsv"), "CHECK_SETUP\t0", "CHECK_SETUP\t2")
            r = records.compare("missing_vs_correct", run, CORRECT, RULES)
            self.assertFalse(r["ok"])
            self.assertTrue(any("CHECK_SETUP" in p for p in r["problems"]))

    def test_check_setup_expected_per_relation(self):
        with TmpCopy(MISSING) as run:
            edit(os.path.join(run, "sta_results.tsv"), "CHECK_SETUP\t0", "CHECK_SETUP\t1")
            r = records.compare("missing_vs_correct", run, CORRECT, RULES)
            self.assertFalse(r["ok"])

    def test_numeric_nan_fails(self):
        with TmpCopy(MISSING) as run:
            edit(os.path.join(run, "sta_results.tsv"), "WS\tss_n40C_1v60\tmax\t-4.172594832200332", "WS\tss_n40C_1v60\tmax\tnan")
            r = records.compare("missing_vs_correct", run, CORRECT, RULES)
            self.assertFalse(r["ok"])

    def test_numeric_startpoint_mismatch_fails(self):
        with TmpCopy(MISSING) as run:
            edit(os.path.join(run, "sta_results.tsv"), "CAT\tss_n40C_1v60\tin2reg\tmax\t-4.172595\tin_a[34]\t_12026_/D",
                 "CAT\tss_n40C_1v60\tin2reg\tmax\t-4.172595\tin_a[3]\t_12026_/D")
            r = records.compare("missing_vs_correct", run, CORRECT, RULES)
            self.assertFalse(r["ok"])
            bad = [n for n in r["numeric"] if not n["ok"]]
            self.assertEqual(len(bad), 1)
            self.assertFalse(bad[0]["startpoint_ok"])

    def test_numeric_ws_4dp_matches_report(self):
        with TmpCopy(MISSING) as run:
            edit(os.path.join(run, "sta_results.tsv"), "WS\tss_n40C_1v60\tmax\t-4.172594832200332", "WS\tss_n40C_1v60\tmax\t-4.17270")
            r = records.compare("missing_vs_correct", run, CORRECT, RULES)
            self.assertFalse(r["ok"])
            bad = [n for n in r["numeric"] if not n["ok"] and n["record"].startswith("WS")]
            self.assertEqual(bad[0]["report_value"], "-4.1726")

    def test_numeric_wrong_scene_fails(self):
        with TmpCopy(MISSING) as run:
            edit(os.path.join(run, "sta_results.tsv"), "WS\tss_n40C_1v60\tmax\t", "WS\tss_n40C_1v65\tmax\t")
            r = records.compare("missing_vs_correct", run, CORRECT, RULES)
            self.assertFalse(r["ok"])


class TestWarningBlock(unittest.TestCase):
    MUT = os.path.join(RULES, "mutation_lines.txt")

    def test_warning_block_exact_64_unique_names(self):
        w = records.warning_block(read(os.path.join(MISSING, "sta.log")), self.MUT)
        self.assertEqual((w["present"], w["count"], w["names_ok"]), (True, 64, True))
        self.assertEqual(w["problems"], [])

    def test_warning_block_absent_in_correct_ok(self):
        w = records.warning_block(read(os.path.join(CORRECT, "sta.log")), self.MUT)
        self.assertEqual((w["present"], w["count"], w["names_ok"]), (False, None, False))

    def test_warning_block_63_fails(self):
        text = read(os.path.join(MISSING, "sta.log")).replace("  in_b[9]\n", "")
        w = records.warning_block(text, self.MUT)
        self.assertTrue(w["present"])
        self.assertFalse(w["names_ok"])
        self.assertTrue(w["problems"])

    def test_warning_block_duplicate_fails(self):
        text = read(os.path.join(MISSING, "sta.log"))
        w = records.warning_block(text + text, self.MUT)
        self.assertFalse(w["names_ok"])
        self.assertTrue(any("2" in p for p in w["problems"]))

    def test_warning_block_foreign_name_fails(self):
        text = read(os.path.join(MISSING, "sta.log")).replace("  in_b[9]\n", "  in_a[9]\n")
        w = records.warning_block(text, self.MUT)
        self.assertFalse(w["names_ok"])


class TestExpanded(unittest.TestCase):
    MUT = os.path.join(RULES, "mutation_lines.txt")

    def test_expanded_diff_exactly_128(self):
        ok, problems = records.expanded_diff_is_exactly(read(os.path.join(CORRECT, "expanded.sdc")),
                                                        read(os.path.join(MISSING, "expanded.sdc")), read(self.MUT).splitlines())
        self.assertTrue(ok, problems)

    def test_expanded_diff_extra_deletion_fails(self):
        missing = read(os.path.join(MISSING, "expanded.sdc")).replace(
            "set_input_delay 0.0000 -clock [get_clocks {clk}] -min -add_delay [get_ports {in_a[5]}]\n", "", 1)
        ok, problems = records.expanded_diff_is_exactly(read(os.path.join(CORRECT, "expanded.sdc")), missing,
                                                        read(self.MUT).splitlines())
        self.assertFalse(ok)

    def test_expanded_constraints_parse(self):
        c = records.expanded_constraints(read(os.path.join(CORRECT, "expanded.sdc")))
        self.assertEqual(len(c), 130)
        self.assertEqual(c["in_a[5]"], {"min": "0.0000", "max": "5.5820", "clock": "clk", "edge": "rise",
                                        "rise": True, "fall": True, "driver": "sky130_fd_sc_hd__buf_2"})

    def test_layer2_correct_all_complete(self):
        c = records.expanded_constraints(read(os.path.join(CORRECT, "expanded.sdc")))
        ok, problems = records.layer2_check(c, "correct")
        self.assertTrue(ok, problems)

    def test_layer2_missing_exactly_64_without_min_max(self):
        c = records.expanded_constraints(read(os.path.join(MISSING, "expanded.sdc")))
        self.assertIsNone(c["in_b[5]"]["min"])
        self.assertIsNone(c["in_b[5]"]["max"])
        self.assertEqual(c["in_b[5]"]["driver"], "sky130_fd_sc_hd__buf_2")
        ok, problems = records.layer2_check(c, "missing")
        self.assertTrue(ok, problems)
        ok2, _ = records.layer2_check(c, "correct")
        self.assertFalse(ok2)


if __name__ == "__main__":
    unittest.main()
