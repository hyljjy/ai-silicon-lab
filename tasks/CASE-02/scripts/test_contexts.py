"""Unit tests of contexts.py (R1/R2 assignment commitment and resolution; protocol v0.3 sections 6.2, 8, 9).
Run in WSL from tasks/CASE-02/scripts: python3 -B -m unittest -v test_contexts"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "scripts")
              if os.path.basename(os.path.dirname(HERE)) == "impl" else HERE)
import c2paths  # noqa: E402
import contexts  # noqa: E402


class Dirs:
    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="ctx_", dir=c2paths.RUNS)
        self.sealed = os.path.join(self.tmp, "sealed")
        self.out = os.path.join(self.tmp, "outputs")
        os.makedirs(self.sealed)
        os.makedirs(self.out)
        return self

    def __exit__(self, *a):
        import shutil
        shutil.rmtree(self.tmp)


def ok_checker(path):
    return []


def bad_checker(path):
    return ["not tracked"]


class TestCommitResolve(unittest.TestCase):
    def test_commit_resolve_roundtrip(self):
        with Dirs() as d:
            assign = contexts.commit(selftest=False, sealed_dir=d.sealed, out_dir=d.out)
            self.assertEqual(sorted(assign.values()), ["correct", "missing"])
            self.assertEqual(set(assign), {"R1", "R2"})
            with open(os.path.join(d.sealed, "assign.json"), encoding="utf-8") as f:
                sealed = json.load(f)
            self.assertEqual(len(sealed["salt"]), 32)
            with open(os.path.join(d.out, "assign.sha256")) as f:
                line = f.read()
            self.assertEqual(len(line.split()[0]), 64)
            self.assertEqual(contexts.resolve("R1", selftest=False, sealed_dir=d.sealed, out_dir=d.out, checker=ok_checker),
                             assign["R1"])
            self.assertEqual(contexts.resolve("R2", selftest=False, sealed_dir=d.sealed, out_dir=d.out, checker=ok_checker),
                             assign["R2"])
            self.assertEqual(contexts.label_of(assign["R2"], assign), "R2")

    def test_commit_refuses_second_time(self):
        with Dirs() as d:
            contexts.commit(selftest=False, sealed_dir=d.sealed, out_dir=d.out)
            with self.assertRaises(contexts.AssignError):
                contexts.commit(selftest=False, sealed_dir=d.sealed, out_dir=d.out)

    def test_resolve_refuses_uncommitted(self):
        with Dirs() as d:
            contexts.commit(selftest=False, sealed_dir=d.sealed, out_dir=d.out)
            with self.assertRaises(contexts.AssignError):
                contexts.resolve("R1", selftest=False, sealed_dir=d.sealed, out_dir=d.out, checker=bad_checker)

    def test_resolve_refuses_hash_mismatch(self):
        with Dirs() as d:
            contexts.commit(selftest=False, sealed_dir=d.sealed, out_dir=d.out)
            with open(os.path.join(d.sealed, "assign.json"), "a") as f:
                f.write("\n")
            with self.assertRaises(contexts.AssignError):
                contexts.resolve("R1", selftest=False, sealed_dir=d.sealed, out_dir=d.out, checker=ok_checker)

    def test_resolve_refuses_bad_ctx(self):
        with Dirs() as d:
            contexts.commit(selftest=False, sealed_dir=d.sealed, out_dir=d.out)
            with self.assertRaises(contexts.AssignError):
                contexts.resolve("R3", selftest=False, sealed_dir=d.sealed, out_dir=d.out, checker=ok_checker)

    def test_selftest_assignment_fixed(self):
        with Dirs() as d:
            path = os.path.join(d.tmp, "selftest_assign.json")
            assign = contexts.commit(selftest=True, selftest_path=path)
            self.assertEqual(assign, {"R1": "correct", "R2": "missing"})
            self.assertEqual(contexts.resolve("R2", selftest=True, selftest_path=path), "missing")
            self.assertFalse(os.path.exists(os.path.join(d.sealed, "assign.json")))


if __name__ == "__main__":
    unittest.main()
