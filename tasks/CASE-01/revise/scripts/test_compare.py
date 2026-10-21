"""Tests for compare (comparison matrix, diffs, degradations, C2 consistency; protocol v0.4 sections 12.2, 14;
CASE-01 stage B Task 6). Both sides (Windows and WSL); run per module, never with discover. Pure file work: the F1
baseline is read (read only) from the archive originals via baseline.source(); pipe2 comes from fixtures/sta/pipe2/;
everything written goes to a temporary directory under tasks/CASE-01/runs/ (never /tmp, never revise/compare/)."""
import contextlib
import copy
import io
import json
import os
import re
import shutil
import tempfile
import unittest
from decimal import Decimal

import baseline
import compare
import revpaths as rp

RUNS = os.path.join(rp.CASE, "runs")
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE2 = os.path.join(HERE, "fixtures", "sta", "pipe2")
BASE = baseline.source()


def rd(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def wbytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def dump_verdict(path, verdict):
    """Write a verdict object back as JSON, every Decimal as a raw JSON number with all its digits."""
    def default(o):
        if isinstance(o, Decimal):
            return f"@@DEC:{format(o, 'f')}@@"
        raise TypeError(type(o))
    text = re.sub(r'"@@DEC:([-0-9.]+)@@"', lambda m: m.group(1), json.dumps(verdict, indent=1, default=default))
    wbytes(path, (text + "\n").encode("utf-8"))


class Base(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="compare_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.case = os.path.join(self.tmp.name, "case")

    def candidate(self, code="CAND", rnd=1, mutate=None, status=None, k=1):
        """A candidate below the temporary case: status.json and attempt<k>/ holding pipe2's verdict.json and sta/."""
        cdir = os.path.join(self.case, "revise", "results", f"r{rnd}", code)
        adir = os.path.join(cdir, f"attempt{k}")
        shutil.copytree(PIPE2, adir)
        if mutate:
            v = rp.load_json_decimal(os.path.join(adir, "verdict.json"))
            mutate(v)
            dump_verdict(os.path.join(adir, "verdict.json"), v)
        st = {"code": code, "rnd": rnd, "state": "eligible_no_gain", "flags": [], "selected_attempt": k,
              "grade_status": "GRADE OK", "rtl_sim": "pass", "gl_sim": "pass", "sta_analysis": "pass",
              "checked_rtl": "checked=2835", "checked_gl": "checked=2835", "area_um2": "46444.544",
              "within_cap": True, "author_veto": False, "declared_L": 2, "cfg_L": 2,
              "numeric_target_met": False}
        st.update(status or {})
        wbytes(os.path.join(cdir, "status.json"), (json.dumps(st, indent=1) + "\n").encode("utf-8"))
        return cdir, adir


# --------------------------------------------------------------------------------------------- endpoints
REG2OUT = """Startpoint: _11958_ (rising edge-triggered flip-flop clocked by clk)
Endpoint: out_data[0] (output port clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

Fanout       Cap      Slew     Delay      Time   Description
-------------------------------------------------------------------------------------
                    0.0000    0.0000    0.0000   clock clk (rise edge)
                              0.0000    0.0000   clock network delay (ideal)
                    0.0000    0.0000    0.0000 ^ _11958_/CLK (sky130_fd_sc_hd__dfxtp_1)
     1    0.0024    0.0761    0.6356    0.6356 ^ _11958_/Q (sky130_fd_sc_hd__dfxtp_1)
                    0.0761    0.0000    0.6356 ^ out_data[0] (out)
                                        0.6356   data arrival time

                    0.0000   20.0000   20.0000   clock clk (rise edge)
                             -4.0000   16.0000   output external delay
                                       16.0000   data required time
"""


class Endpoints(Base):
    def pipe2(self, name):
        return rd(os.path.join(PIPE2, "sta", name))

    def test_endpoints_base(self):
        p = BASE["path_reports"]
        self.assertEqual(compare.path_endpoints(rd(p["max"]["tt_025C_1v80"])), ("in_b[35]", "_12026_/D"))
        self.assertEqual(compare.path_endpoints(rd(p["max"]["ss_n40C_1v60"])), ("in_b[2]", "_12026_/D"))
        self.assertEqual(compare.path_endpoints(rd(p["min"]["ss_n40C_1v60"])), ("rst", "_12058_/D"))

    def test_endpoints_pipe2(self):
        self.assertEqual(compare.path_endpoints(self.pipe2("path_max_ss_n40C_1v60.rpt")), ("in_a[1]", "_11924_/D"))
        self.assertEqual(compare.path_endpoints(self.pipe2("path_max_tt_025C_1v80.rpt")), ("in_a[17]", "_11924_/D"))
        self.assertEqual(compare.path_endpoints(self.pipe2("path_min_ss_n40C_1v60.rpt")), ("rst", "_11956_/D"))

    def test_register_startpoint_pin(self):
        self.assertEqual(compare.path_endpoints(self.pipe2("cat_ss_n40C_1v60_reg2reg_max.rpt")),
                         ("_11956_/Q", "_11957_/D"))

    def test_output_port_endpoint(self):
        self.assertEqual(compare.path_endpoints(REG2OUT), ("_11958_/Q", "out_data[0]"))

    def test_missing_arrival_section_stops(self):
        text = self.pipe2("cat_ss_n40C_1v60_reg2reg_max.rpt").replace("data arrival time", "arrival")
        with self.assertRaises(compare.EndpointError):
            compare.path_endpoints(text)

    def test_two_candidate_pins_stops(self):
        text = self.pipe2("cat_ss_n40C_1v60_reg2reg_max.rpt")
        line = "     1    0.0013    0.0327    0.5395    0.5395 v _11956_/Q (sky130_fd_sc_hd__dfxtp_1)\n"
        self.assertIn(line, text)
        text = text.replace(line, line + line.replace("_11956_/Q", "_11956_/Q_N"))
        with self.assertRaises(compare.EndpointError):
            compare.path_endpoints(text)

    def test_capture_clock_section_ignored(self):
        # a pin of the start register after the first "data arrival time" (capture side) is not a candidate
        text = self.pipe2("cat_ss_n40C_1v60_reg2reg_max.rpt")
        text = text.replace("_11957_/CLK (sky130", "_11956_/QX (sky130")
        self.assertEqual(compare.path_endpoints(text), ("_11956_/Q", "_11957_/D"))

    def test_similar_cell_names_not_confused(self):
        text = self.pipe2("cat_ss_n40C_1v60_reg2reg_max.rpt")
        # the start register renamed _1195_: its own pins are _1195_/CLK and _1195_/Q; a pin of _11956_ remains
        text = text.replace("Startpoint: _11956_", "Startpoint: _1195_")
        text = text.replace("_11956_/CLK", "_1195_/CLK").replace("_11956_/Q", "_1195_/Q")
        extra = "                    0.0327    0.0000    0.5395 v _11956_/B (sky130_fd_sc_hd__nor2b_1)\n"
        anchor = "                    0.0327    0.0000    0.5395 v _11397_/B_N"
        text = text.replace(anchor, extra + anchor)
        self.assertEqual(compare.path_endpoints(text), ("_1195_/Q", "_11957_/D"))
        # and the other way round: Startpoint _11956_ with only pins of _1195_ in the arrival part
        text2 = text.replace("Startpoint: _1195_", "Startpoint: _11956_").replace("_11956_/B (", "_1195_/B (")
        with self.assertRaises(compare.EndpointError):
            compare.path_endpoints(text2)

    def test_endpoint_cell_mismatch_stops(self):
        text = self.pipe2("path_min_ss_n40C_1v60.rpt").replace("Endpoint: _11956_", "Endpoint: _1195_")
        with self.assertRaises(compare.EndpointError):
            compare.path_endpoints(text)

    def test_multiple_paths_uses_first_only(self):
        first = self.pipe2("path_min_ss_n40C_1v60.rpt")
        second = self.pipe2("cat_ss_n40C_1v60_reg2reg_max.rpt")
        self.assertEqual(compare.path_endpoints(first + "\n" + second), ("rst", "_11956_/D"))
        self.assertEqual(compare.path_endpoints(second + "\n" + first), ("_11956_/Q", "_11957_/D"))


# ------------------------------------------------------------------------------------------------- matrix
class Matrix(Base):
    def test_matrix_has_48_cells_summary_and_extras(self):
        self.candidate()
        m = compare.matrix(compare.source_candidate("CAND", 1, case=self.case))
        self.assertEqual(len(m.cells), 48)
        self.assertEqual(set(m.cells), {(c, k, s) for c in baseline.CORNERS for k in ("setup", "hold")
                                        for s in ("global", "in2reg", "reg2reg", "reg2out")})
        self.assertEqual(m.cells[("ss_n40C_1v60", "setup", "global")],
                         {"slack": Decimal("-10.919105928491199"), "start": "in_a[1]", "end": "_11924_/D"})
        self.assertEqual(m.cells[("ss_n40C_1v60", "hold", "global")],
                         {"slack": Decimal("0.2157636630433057"), "start": "rst", "end": "_11956_/D"})
        self.assertEqual(m.cells[("tt_025C_1v80", "setup", "reg2reg")],
                         {"slack": Decimal("19.510481"), "start": "_11956_/Q", "end": "_11957_/D"})
        self.assertEqual(m.summary["worst_setup"], {"slack": Decimal("-10.919105928491199"),
                                                    "corner": "ss_n40C_1v60", "category": "in2reg"})
        self.assertEqual(m.summary["worst_hold"], {"slack": Decimal("0.06857570261298768"), "corner": "ff_100C_1v95"})
        self.assertEqual(set(m.extra), set("area cfg_L rtl_sim gl_sim sta_analysis numeric_target_met state "
                                           "topology checked_rtl checked_gl".split()))
        self.assertEqual(m.extra["area"], Decimal("46444.544"))
        self.assertEqual(m.extra["cfg_L"], 2)
        self.assertEqual(m.extra["sta_analysis"], "pass")
        self.assertEqual(m.extra["state"], "eligible_no_gain")
        self.assertEqual(m.extra["topology"], {"in2reg": 130, "reg2reg": 33, "reg2out": 33})

    def test_candidate_without_sta_pass_rejected(self):
        self.candidate(status={"sta_analysis": "fail"})
        with self.assertRaises(compare.MatrixError):
            compare.source_candidate("CAND", 1, case=self.case)

    def test_baseline_source_has_no_status(self):
        src = compare.source_baseline()
        self.assertIsNone(src.status)
        m = compare.matrix(src)
        self.assertEqual(len(m.cells), 48)
        for key in ("rtl_sim", "gl_sim", "sta_analysis", "state"):
            self.assertEqual(m.extra[key], "not_applicable")
        self.assertEqual(m.extra["area"], Decimal("45383.5264"))
        self.assertEqual(m.extra["cfg_L"], 1)
        self.assertIs(m.extra["numeric_target_met"], False)
        self.assertEqual(m.extra["checked_rtl"], "checked=2856")
        self.assertEqual(m.cells[("tt_025C_1v80", "setup", "reg2reg")],
                         {"slack": "not_applicable", "start": "not_applicable", "end": "not_applicable"})
        self.assertEqual(m.summary["worst_setup"]["slack"], Decimal("-4.189726018044011"))

    def test_missing_corner_rejected(self):
        self.candidate(code="NOC", mutate=lambda v: v["corners"].pop("tt_100C_1v80"))
        with self.assertRaises(compare.MatrixError):
            compare.matrix(compare.source_candidate("NOC", 1, case=self.case))
        self.candidate(code="NOK", mutate=lambda v: v["corners"]["ff_100C_1v95"]["categories"].pop("reg2out_min"))
        with self.assertRaises(compare.MatrixError):
            compare.matrix(compare.source_candidate("NOK", 1, case=self.case))

    def test_global_cell_uses_parsed_pins(self):
        def mutate(v):
            v["corners"]["ss_n40C_1v60"]["categories"]["in2reg_max"]["start"] = "in_a[9]"
            v["corners"]["ss_n40C_1v60"]["categories"]["in2reg_max"]["end"] = "_11999_/D"
        self.candidate(mutate=mutate)
        m = compare.matrix(compare.source_candidate("CAND", 1, case=self.case))
        self.assertEqual(m.cells[("ss_n40C_1v60", "setup", "global")]["start"], "in_a[1]")
        self.assertEqual(m.cells[("ss_n40C_1v60", "setup", "global")]["end"], "_11924_/D")
        self.assertEqual(m.cells[("ss_n40C_1v60", "setup", "in2reg")]["start"], "in_a[9]")

    def test_known_last_digit_differences_pass(self):
        mb = compare.matrix(compare.source_baseline())
        for c in ("tt_100C_1v80", "ff_n40C_1v95"):
            g, cat = mb.cells[(c, "setup", "global")]["slack"], mb.cells[(c, "setup", "in2reg")]["slack"]
            self.assertNotEqual(rp.fmt6(g), rp.fmt6(cat))
        self.candidate()
        mc = compare.matrix(compare.source_candidate("CAND", 1, case=self.case))
        for c in ("ff_n40C_1v95", "ff_100C_1v95"):
            g, cat = mc.cells[(c, "setup", "global")]["slack"], mc.cells[(c, "setup", "in2reg")]["slack"]
            self.assertNotEqual(rp.fmt6(g), rp.fmt6(cat))

    def test_consistency_error_beyond_1e5(self):
        def far(v):
            v["corners"]["tt_025C_1v80"]["ws_max"] = Decimal("4.646131") + Decimal("0.0000101")
        self.candidate(code="FAR", mutate=far)
        with self.assertRaises(compare.ConsistencyError):
            compare.matrix(compare.source_candidate("FAR", 1, case=self.case))

        def near(v):
            v["corners"]["tt_025C_1v80"]["ws_max"] = Decimal("4.646131") + Decimal("0.00001")
        self.candidate(code="NEAR", mutate=near)
        compare.matrix(compare.source_candidate("NEAR", 1, case=self.case))

        def hold_far(v):
            v["corners"]["ff_100C_1v95"]["ws_min"] = Decimal("0.06859")
        self.candidate(code="HFAR", mutate=hold_far)
        with self.assertRaises(compare.ConsistencyError):
            compare.matrix(compare.source_candidate("HFAR", 1, case=self.case))

    def test_report_corner_mismatch_rejected(self):
        _, adir = self.candidate()
        p = os.path.join(adir, "sta", "path_max_tt_025C_1v80.rpt")
        wbytes(p, rd(p).replace("Corner: tt_025C_1v80", "Corner: tt_100C_1v80").encode("utf-8"))
        with self.assertRaises(compare.MatrixError):
            compare.matrix(compare.source_candidate("CAND", 1, case=self.case))


# -------------------------------------------------------------------------------------------------- diffs
def adjusted(m, check, by):
    """A copy of matrix m with every numeric slack of the check moved by `by`."""
    cells = copy.deepcopy(m.cells)
    for (c, k, s), cell in cells.items():
        if k == check and cell["slack"] != "not_applicable":
            cell["slack"] = cell["slack"] + by
    return compare.Matrix(cells=cells, summary=copy.deepcopy(m.summary), extra=copy.deepcopy(m.extra))


class Diffs(Base):
    def setUp(self):
        super().setUp()
        self.candidate()
        self.mb = compare.matrix(compare.source_baseline())
        self.mc = compare.matrix(compare.source_candidate("CAND", 1, case=self.case))

    def test_introduced_removed(self):
        d = compare.diff(self.mb, self.mc)
        cell = d[("tt_025C_1v80", "setup", "reg2reg")]
        self.assertEqual(cell["change"], "introduced")
        self.assertEqual(cell["delta"], "not_applicable")
        self.assertEqual(d[("ff_100C_1v95", "hold", "reg2reg")]["change"], "introduced")
        r = compare.diff(self.mc, self.mb)
        self.assertEqual(r[("tt_025C_1v80", "setup", "reg2reg")]["change"], "removed")
        for dd in (d, r):
            listed = {tuple(x["cell"]) for x in compare.degradations(dd, Decimal("1"), Decimal("1"))}
            self.assertNotIn(("tt_025C_1v80", "setup", "reg2reg"), listed)

    def test_same_cell_changed_path_flagged(self):
        d = compare.diff(self.mb, self.mc)
        cell = d[("ss_n40C_1v60", "setup", "global")]
        self.assertFalse(cell["same_path"])
        self.assertEqual(cell["change"], "worse")
        self.assertEqual(cell["delta"], Decimal("-10.919105928491199") - Decimal("-4.189726018044011"))
        same = compare.diff(self.mb, self.mb)[("ss_n40C_1v60", "setup", "global")]
        self.assertTrue(same["same_path"])
        self.assertEqual(same["change"], "same")

    def test_all_hold_degradations_listed(self):
        cand = adjusted(self.mb, "hold", Decimal("-0.000002"))
        d = compare.diff(self.mb, cand)
        deg = compare.degradations(d, Decimal("45383.5264"), Decimal("45383.5264"))
        hold_cells = {k for k, v in self.mb.cells.items() if k[1] == "hold" and v["slack"] != "not_applicable"}
        self.assertEqual(len(hold_cells), 18)
        self.assertEqual({tuple(x["cell"]) for x in deg}, hold_cells)
        for x in deg:
            self.assertEqual(x["kind"], "slack")
            self.assertEqual(x["note"], compare.HOLD_NOTE)
            self.assertEqual(x["delta"], Decimal("-0.000002"))
        # exactly one epsilon is not beyond it
        d1 = compare.diff(self.mb, adjusted(self.mb, "hold", Decimal("-0.000001")))
        self.assertEqual(compare.degradations(d1, Decimal("1"), Decimal("1")), [])
        self.assertEqual(d1[("ff_100C_1v95", "hold", "global")]["change"], "same")
        up = compare.diff(self.mb, adjusted(self.mb, "setup", Decimal("0.0000011")))
        self.assertEqual(up[("ss_n40C_1v60", "setup", "global")]["change"], "better")

    def test_area_degradation_epsilon(self):
        d = compare.diff(self.mb, self.mb)
        self.assertEqual(compare.degradations(d, Decimal("100"), Decimal("100.0001")), [])
        self.assertEqual(compare.degradations(d, Decimal("100"), Decimal("99")), [])
        deg = compare.degradations(d, Decimal("100"), Decimal("100.00011"))
        self.assertEqual(len(deg), 1)
        self.assertEqual(deg[0]["kind"], "area")
        self.assertEqual(deg[0]["delta"], Decimal("0.00011"))


# ------------------------------------------------------------------------------------------- command line
class Command(Base):
    def run_main(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            rc = compare.main(list(args), case=self.case)
        return rc, out.getvalue()

    def test_matrix_write_and_check(self):
        self.candidate()
        rc, out = self.run_main("matrix", "CAND", "1", "--check")
        self.assertEqual(rc, 1, out)
        self.assertIn("CHECK FAIL", out)
        rc, out = self.run_main("matrix", "CAND", "1")
        self.assertEqual(rc, 0, out)
        pj = os.path.join(self.case, "revise", "compare", "r1_CAND.json")
        pm = os.path.join(self.case, "revise", "compare", "r1_CAND.md")
        doc = rp.load_json_decimal(pj)
        self.assertEqual(len(doc["cells"]), 48)
        self.assertIn("degradations", doc)
        self.assertNotIn(b"\r", rp.read_bytes(pm))
        self.assertIn(compare.HOLD_NOTE, rd(pm))
        self.assertIn("| cfg_L | 1 | 2 |", rd(pm))
        self.assertIn("| worst_setup.slack | -4.189726 | -10.919106 |", rd(pm))
        self.assertEqual(doc["candidate"]["summary"]["worst_setup"]["slack"], "-10.919105928491199")
        rc, out = self.run_main("matrix", "CAND", "1", "--check")
        self.assertEqual(rc, 0, out)
        wbytes(pm, rp.read_bytes(pm) + b"x")
        rc, out = self.run_main("matrix", "CAND", "1", "--check")
        self.assertEqual(rc, 1)
        self.assertIn("CHECK FAIL", out)

    def test_matrix_stop_writes_nothing(self):
        _, adir = self.candidate()
        p = os.path.join(adir, "sta", "path_max_tt_025C_1v80.rpt")
        wbytes(p, rd(p).replace("data arrival time", "arrival").encode("utf-8"))
        rc, out = self.run_main("matrix", "CAND", "1")
        self.assertEqual(rc, 1)
        self.assertIn("MATRIX FAIL", out)
        self.assertFalse(os.path.exists(os.path.join(self.case, "revise", "compare", "r1_CAND.json")))


# --------------------------------------------------------------------------------------------- consistency
def tune(v):
    """pipe2 made F1-like for layer 6: target known, area under a cap."""
    v["timing_target"] = {"rule": "setup_ge_0_std", "met": False}
    v["area"] = {"area_um2": v["area_um2"], "cap_um2": Decimal("56729.408"), "within_cap": True}


class C2(Base):
    def pair(self, c2_mutate=None, local_mutate=None, status=None):
        def lm(v):
            tune(v)
            if local_mutate:
                local_mutate(v)
        _, local = self.candidate(mutate=lm, status=status)
        c2 = os.path.join(self.tmp.name, "c2")
        shutil.copytree(local, c2)
        if c2_mutate:
            v = rp.load_json_decimal(os.path.join(c2, "verdict.json"))
            c2_mutate(v)
            dump_verdict(os.path.join(c2, "verdict.json"), v)
        return compare.consistency(local, c2)

    def layer(self, layers, n):
        return [x for x in layers if x["layer"] == n][0]

    def assert_only_layer(self, layers, n):
        for x in layers:
            self.assertEqual(x["same"], x["layer"] != n, (n, x))

    def test_identical_is_consistent(self):
        verdict, layers = self.pair()
        self.assertEqual(verdict, "consistent")
        self.assertEqual([x["layer"] for x in layers], [1, 2, 3, 4, 5, 6, 7])
        l3 = self.layer(layers, 3)
        hold_cat = [f for f in l3["fields"] if f["field"] == "worst_hold.category"][0]
        self.assertTrue(hold_cat["derived"])
        self.assertEqual(hold_cat["local"], "in2reg")
        l7 = self.layer(layers, 7)
        self.assertEqual(l7["fields"][0]["local"], {})

    def test_layer1_netlist(self):
        verdict, layers = self.pair(lambda v: v.update(netlist_sha256="0" * 64))
        self.assertEqual(verdict, "inconsistent")
        self.assert_only_layer(layers, 1)

    def test_layer2_flags_and_cfg_L(self):
        verdict, layers = self.pair(lambda v: v.update(analysis_valid=False))
        self.assertEqual(verdict, "inconsistent")
        self.assertFalse(self.layer(layers, 2)["same"])

        def bad_L(v):
            v["impl"]["L"] = "3"
        shutil.rmtree(self.case)
        shutil.rmtree(os.path.join(self.tmp.name, "c2"))
        verdict, layers = self.pair(bad_L)
        self.assertEqual(verdict, "inconsistent")
        l2 = self.layer(layers, 2)
        f = [x for x in l2["fields"] if x["field"] == "cfg_L"][0]
        self.assertEqual(f["local"], 2)
        self.assertEqual(f["status"], "missing")       # impl.L 3 vs latency_L 2: invalid on the C2 side

    def test_layer3_worst_setup_category(self):
        def m(v):
            v["worst_setup"]["category"] = "reg2reg"
        verdict, layers = self.pair(m)
        self.assertEqual(verdict, "inconsistent")
        self.assert_only_layer(layers, 3)

    def test_layer4_category_endpoint(self):
        def m(v):
            v["corners"]["tt_025C_1v80"]["categories"]["reg2out_min"]["end"] = "out_data[1]"
        verdict, layers = self.pair(m)
        self.assertEqual(verdict, "inconsistent")
        self.assert_only_layer(layers, 4)

    def test_layer5_area_and_topology(self):
        verdict, layers = self.pair(lambda v: v["topology"].update(reg2reg=34))
        self.assertEqual(verdict, "inconsistent")
        self.assert_only_layer(layers, 5)

    def test_layer6_recomputed_research(self):
        def m(v):
            v["area"]["within_cap"] = False
        verdict, layers = self.pair(m)
        self.assertEqual(verdict, "inconsistent")
        self.assert_only_layer(layers, 6)
        l6 = self.layer(layers, 6)
        f = [x for x in l6["fields"] if x["field"] == "eligible"][0]
        self.assertEqual((f["local"], f["c2"]), (True, False))

    def test_layer6_uses_local_author_veto(self):
        verdict, layers = self.pair(status={"author_veto": True})
        self.assertEqual(verdict, "consistent")
        f = [x for x in self.layer(layers, 6)["fields"] if x["field"] == "eligible"][0]
        self.assertEqual((f["local"], f["c2"]), (False, False))

    def test_layer7_other_drift(self):
        def m(v):
            v["env_snapshot"] = {"allow_tool_drift": True, "tool_drift": {"opensta/bin/sta": "a" * 64,
                                                                          "yosys/bin/yosys": "b" * 64}}
        verdict, layers = self.pair(m)
        self.assertEqual(verdict, "inconsistent")
        self.assert_only_layer(layers, 7)

    def test_allowed_sta_drift_only(self):
        def m(v):
            v["env_snapshot"] = {"allow_tool_drift": True, "tool_drift": {"opensta/bin/sta": "a" * 64}}
        verdict, layers = self.pair(m)
        self.assertEqual(verdict, "consistent")
        l7 = self.layer(layers, 7)
        self.assertEqual(l7["fields"][0]["local"], {})
        self.assertEqual(l7["fields"][0]["c2"], {"opensta/bin/sta": "a" * 64})

    def test_display_consistent_numeric_only(self):
        def m(v):
            v["worst_setup"]["slack"] = Decimal("-10.9191059")
            v["corners"]["ss_n40C_1v60"]["ws_max"] = Decimal("-10.9191059")
            v["corners"]["ff_100C_1v95"]["ws_min"] = Decimal("0.0685757")
        verdict, layers = self.pair(m)
        self.assertEqual(verdict, "display_consistent")
        self.assertTrue(self.layer(layers, 3)["display_only"])
        self.assertTrue(self.layer(layers, 4)["display_only"])
        # beyond the display: inconsistent
        shutil.rmtree(self.case)
        shutil.rmtree(os.path.join(self.tmp.name, "c2"))
        verdict, _ = self.pair(lambda v: v["corners"]["ss_n40C_1v60"].update(ws_max=Decimal("-10.919107")))
        self.assertEqual(verdict, "inconsistent")

    def test_display_consistent_requires_same_corner(self):
        def m(v):
            v["worst_setup"]["slack"] = Decimal("-10.9191059")
            v["worst_hold"]["corner"] = "ff_n40C_1v95"
        verdict, _ = self.pair(m)
        self.assertEqual(verdict, "inconsistent")

    def test_display_level_not_for_area(self):
        verdict, layers = self.pair(lambda v: v.update(area_um2=Decimal("46444.5440001")))
        self.assertEqual(verdict, "inconsistent")
        self.assert_only_layer(layers, 5)

    def test_both_missing_is_inconsistent(self):
        # c2 is copied from the local attempt, so removing the field locally removes it on both sides
        verdict, layers = self.pair(local_mutate=lambda v: v.pop("netlist_sha256"))
        self.assertNotIn("netlist_sha256", rp.load_json_decimal(os.path.join(self.tmp.name, "c2", "verdict.json")))
        self.assertEqual(verdict, "inconsistent")
        l1 = self.layer(layers, 1)
        self.assertFalse(l1["same"])
        self.assertEqual(l1["fields"][0]["status"], "missing")
        self.assertIn("netlist_sha256", l1["missing"])

    def test_consistency_command_prints_json(self):
        _, local = self.candidate(mutate=tune)
        c2 = os.path.join(self.tmp.name, "c2")
        shutil.copytree(local, c2)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = compare.main(["consistency", local, c2], case=self.case)
        self.assertEqual(rc, 0)
        doc = json.loads(out.getvalue())
        self.assertEqual(doc["verdict"], "consistent")
        self.assertEqual(len(doc["layers"]), 7)


if __name__ == "__main__":
    unittest.main()
