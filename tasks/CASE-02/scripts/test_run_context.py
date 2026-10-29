"""Unit tests of run_context.py's pure parts (no OpenSTA; protocol v0.3 sections 5.1-5.4; impl_plan Task 4).
Run in WSL from tasks/CASE-02/scripts: python3 -B -m unittest -v test_run_context"""
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
import run_context as rc  # noqa: E402

TARGET = [f"in_b[{i}]" for i in range(64)]
INPUTS = [f"in_a[{i}]" for i in range(64)] + TARGET + ["in_valid", "rst"]


def m11_text(ports=TARGET, direction="input"):
    return "\n".join(f"PORT {p} {direction}" for p in ports) + "\n"


def m12_text(fanin=INPUTS, fanout_counts=None):
    lines = [f"FANIN {p}" for p in fanin]
    for p in INPUTS:
        lines.append(f"FANOUT {p} {(fanout_counts or {}).get(p, 32)}")
    return "\n".join(lines) + "\n"


def m13_text(version="missing"):
    lines = []
    for p in TARGET:
        if version == "missing":
            lines.append(f"PAIR {p} max_c=0 max_u=1 min_c=0 min_u=1 max_u_end=_12026_/D min_u_end=_12026_/D scene=ss_n40C_1v60")
        else:
            lines.append(f"PAIR {p} max_c=1 max_u=1 min_c=1 min_u=1 max_u_end=_12026_/D min_u_end=_12026_/D scene=ss_n40C_1v60")
    return "\n".join(lines) + "\n"


class TestLayers(unittest.TestCase):
    def test_l1_exact_64_names_and_direction(self):
        ok, info = rc.layer1(m11_text())
        self.assertTrue(ok, info)
        self.assertEqual(info["count"], 64)
        ok2, info2 = rc.layer1(m11_text(TARGET[:63]))
        self.assertFalse(ok2)
        ok3, _ = rc.layer1(m11_text(direction="output"))
        self.assertFalse(ok3)
        ok4, _ = rc.layer1(m11_text(TARGET + ["in_a[0]"]))
        self.assertFalse(ok4)

    def test_l3_structure(self):
        ok, info = rc.layer3(m12_text())
        self.assertTrue(ok, info)
        ok2, info2 = rc.layer3(m12_text(fanin=[p for p in INPUTS if p != "in_b[7]"]))
        self.assertFalse(ok2)
        self.assertIn("in_b[7]", str(info2))
        ok3, _ = rc.layer3(m12_text(fanout_counts={"in_b[3]": 0}))
        self.assertFalse(ok3)

    def test_l4_missing_states_table(self):
        ok, info = rc.layer4(m13_text("missing"), "missing")
        self.assertTrue(ok, info)
        self.assertEqual(len(info["ports"]), 64)
        self.assertEqual(info["ports"]["in_b[0]"]["state"], "查到目标 unconstrained 路径")
        ok2, info2 = rc.layer4(m13_text("correct"), "missing")
        self.assertFalse(ok2)
        ok3, _ = rc.layer4(m13_text("correct"), "correct")
        self.assertTrue(ok3)
        ok4, _ = rc.layer4(m13_text("correct"), "restored")
        self.assertTrue(ok4)

    def test_l4_state_names(self):
        text = "PAIR in_b[0] max_c=0 max_u=0 min_c=0 min_u=0 max_u_end=- min_u_end=- scene=ss_n40C_1v60\n"
        ok, info = rc.layer4(text, "missing")
        self.assertFalse(ok)
        self.assertEqual(info["ports"]["in_b[0]"]["state"], "两类时序查询都为空，但结构路径存在")


class TestValidity(unittest.TestCase):
    def base(self, version="missing"):
        return {"version": version, "snapshot_ok": True, "hashes_ok": True, "log_ok": True,
                "compare": {"ok": True, "problems": [], "allowed_changes_seen": ["x"] * 24, "mutation_verified": True,
                            "lib": {"normalized_ok": True, "raw_identical": True, "raw_lines": []}},
                "warning": {"present": True, "count": 64, "names_ok": True, "problems": []},
                "layers": {"L1_ports": True, "L2_constraints": True, "L3_structure": True, "L4_pairs": True},
                "musts_ok": True}

    def test_missing_valid(self):
        v = rc.validity(**self.base())
        self.assertTrue(v["run_valid"], v["problems"])
        self.assertTrue(v["mutation_verified"])
        self.assertEqual(v["relation"], "missing_vs_correct")

    def test_missing_requires_warning_block_and_layers(self):
        b = self.base()
        b["warning"] = {"present": False, "count": None, "names_ok": False, "problems": []}
        self.assertFalse(rc.validity(**b)["run_valid"])
        b = self.base()
        b["layers"]["L4_pairs"] = False
        self.assertFalse(rc.validity(**b)["run_valid"])

    def test_correct_requires_no_warning_block(self):
        b = self.base("correct")
        b["compare"]["allowed_changes_seen"] = []
        b["compare"]["mutation_verified"] = None
        b["warning"] = {"present": False, "count": None, "names_ok": False, "problems": []}
        v = rc.validity(**b)
        self.assertTrue(v["run_valid"], v["problems"])
        self.assertTrue(v["mutation_verified"])          # empty difference
        self.assertEqual(v["relation"], "correct_vs_f1")
        b["warning"]["present"] = True
        self.assertFalse(rc.validity(**b)["run_valid"])

    def test_restored_vs_correct(self):
        b = self.base("restored")
        b["compare"]["allowed_changes_seen"] = []
        b["compare"]["mutation_verified"] = None
        b["warning"] = {"present": False, "count": None, "names_ok": False, "problems": []}
        self.assertEqual(rc.validity(**b)["relation"], "restored_vs_correct")

    def test_selftest_flag(self):
        v = rc.validity(selftest=True, **self.base())
        self.assertTrue(v["selftest"])
        self.assertFalse(rc.validity(**self.base())["selftest"])


class TestOutputDir(unittest.TestCase):
    def test_refuses_existing_dir(self):
        tmp = tempfile.mkdtemp(prefix="ctxrun_", dir=c2paths.RUNS)
        try:
            d = os.path.join(tmp, "queries", "selftest", "missing")
            os.makedirs(d)
            with self.assertRaises(SystemExit):
                rc.target_dir("missing", selftest=True, queries_root=os.path.join(tmp, "queries"))
            d2 = rc.target_dir("correct", selftest=True, queries_root=os.path.join(tmp, "queries"))
            self.assertTrue(d2.endswith(os.path.join("selftest", "correct")))
        finally:
            shutil.rmtree(tmp)

    def test_sha256sums_over_all_files(self):
        tmp = tempfile.mkdtemp(prefix="ctxsum_", dir=c2paths.RUNS)
        try:
            os.makedirs(os.path.join(tmp, "musts"))
            for name in ("a.txt", "musts/M01.txt"):
                with open(os.path.join(tmp, name), "w") as f:
                    f.write(name)
            rc.write_sha256sums(tmp)
            with open(os.path.join(tmp, "SHA256SUMS")) as f:
                lines = f.read().splitlines()
            self.assertEqual(sorted(l.split("  ")[1] for l in lines), ["./a.txt", "./musts/M01.txt"])
        finally:
            shutil.rmtree(tmp)

    def test_split_musts_output(self):
        text = "noise\n=== CASE02-abc MUST M01 BEGIN ===\nline a\n=== CASE02-abc MUST M01 END rc=0 ===\n" \
               "=== CASE02-abc MUST M02 BEGIN ===\nline b\nline c\n=== CASE02-abc MUST M02 END rc=1 ===\n"
        parts = rc.split_musts(text, "abc")
        self.assertEqual(parts, {"M01": ("line a\n", 0), "M02": ("line b\nline c\n", 1)})


if __name__ == "__main__":
    unittest.main()


class TestR6Musts(unittest.TestCase):
    def test_musts_ok_requires_all_thirteen(self):
        parts = {f"M{i:02d}": ("x\n", 0) for i in range(1, 14)}
        self.assertTrue(rc.musts_complete(parts))
        del parts["M05"]
        self.assertFalse(rc.musts_complete(parts))
        parts["M05"] = ("x\n", 1)
        self.assertFalse(rc.musts_complete(parts))
