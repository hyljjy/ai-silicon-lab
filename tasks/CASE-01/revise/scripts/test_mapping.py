"""Tests for mapping (code commitment and the salted mapping; CASE-01 stage B, Task 1, protocol section 7.1).
Run per module, never with discover. Every test works in a temporary git repository under tasks/CASE-01/runs/ and a
temporary sealed directory; the real sealed directory is never touched."""
import json
import os
import re
import tempfile
import unittest
from unittest import mock

import mapping
import revpaths as rp
from test_stops import git

RUNS = os.path.join(rp.CASE, "runs")
MODELS = ["claude-opus-5-5", "k3[1M]", "deepseek-v4-pro[1M]"]


class Base(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="mapping_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.repo = os.path.join(self.tmp.name, "repo")
        self.sealed = os.path.join(self.tmp.name, "sealed")
        os.makedirs(self.repo)
        git(self.repo, "init", "-q", ".")
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "core.autocrlf", "false")
        self.revise = os.path.join(self.repo, "tasks", "CASE-01", "revise")
        os.makedirs(self.revise)
        with open(os.path.join(self.repo, "README"), "wb") as f:
            f.write(b"temp\n")
        git(self.repo, "add", "README")
        git(self.repo, "commit", "-q", "-m", "init")
        # a slip in a test must not reach the real sealed directory
        p = mock.patch.object(mapping, "SEALED", os.path.join(self.tmp.name, "sealed-default-guard"))
        p.start()
        self.addCleanup(p.stop)
        self.kw = {"revise": self.revise, "sealed": self.sealed}

    def commit_round(self, rnd):
        out = os.path.join(self.revise, "outputs")
        git(self.repo, "add", "--", os.path.join(out, f"r{rnd}", "codes.txt"), os.path.join(out, f"mapping_r{rnd}.sha256"))
        git(self.repo, "commit", "-q", "-m", f"codes r{rnd}")


class TestMapping(Base):
    def test_commit_then_load(self):
        codes = mapping.commit_codes(1, MODELS, None, **self.kw)
        self.assertEqual(len(codes), 3)
        for c in codes:
            self.assertRegex(c, r"^cand_[a-z0-9]{4}$")
        self.assertEqual(len(set(codes)), 3)
        with open(os.path.join(self.revise, "outputs", "r1", "codes.txt"), "rb") as f:
            text = f.read().decode()
        self.assertEqual(text, "".join(c + "\n" for c in sorted(codes)))
        for m in MODELS:
            self.assertNotIn(m, text)
        sealed_file = os.path.join(self.sealed, "mapping_r1.json")
        with open(os.path.join(self.revise, "outputs", "mapping_r1.sha256"), encoding="utf-8") as f:
            self.assertEqual(f.read().split()[0], rp.sha256(sealed_file))
        self.assertFalse(os.path.exists(mapping.SEALED))
        self.commit_round(1)
        m = mapping.load(1, **self.kw)
        self.assertEqual(m["round"], 1)
        self.assertRegex(m["salt"], r"^[0-9a-f]{32,}$")
        for model, code in zip(MODELS, codes):
            self.assertEqual(mapping.code_of(m, model), code)
            self.assertEqual(mapping.model_of(m, code), model)
            self.assertIsNone(mapping.prev_code(m, code))
        with self.assertRaises(mapping.MappingError):
            mapping.code_of(m, "unknown-model")
        with self.assertRaises(mapping.MappingError):           # a round is committed once
            mapping.commit_codes(1, MODELS, None, **self.kw)
        # round 2 records each model's round-1 code
        prev = {model: mapping.code_of(m, model) for model in MODELS}
        codes2 = mapping.commit_codes(2, MODELS, prev, **self.kw)
        self.commit_round(2)
        m2 = mapping.load(2, **self.kw)
        for model, code in zip(MODELS, codes2):
            self.assertEqual(mapping.prev_code(m2, code), prev[model])
        with self.assertRaises(mapping.MappingError):           # prev must match the committed round-1 mapping
            mapping.commit_codes(3, MODELS, {MODELS[0]: codes[1], MODELS[1]: codes[0], MODELS[2]: codes[2]},
                                 **self.kw)

    def test_load_refuses_uncommitted_commitment(self):
        mapping.commit_codes(1, MODELS, None, **self.kw)
        with self.assertRaises(mapping.MappingError):
            mapping.load(1, **self.kw)
        self.commit_round(1)
        mapping.load(1, **self.kw)
        sha_file = os.path.join(self.revise, "outputs", "mapping_r1.sha256")
        with open(sha_file, "ab") as f:                       # committed, then changed in the working tree
            f.write(b"\n")
        with self.assertRaises(mapping.MappingError):
            mapping.load(1, **self.kw)

    def test_load_refuses_changed_sealed_file(self):
        mapping.commit_codes(1, MODELS, None, **self.kw)
        self.commit_round(1)
        sealed_file = os.path.join(self.sealed, "mapping_r1.json")
        with open(sealed_file, "rb") as f:
            data = json.loads(f.read())
        a, b = data["entries"][0]["code"], data["entries"][1]["code"]
        data["entries"][0]["code"], data["entries"][1]["code"] = b, a
        with open(sealed_file, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f)
        with self.assertRaises(mapping.MappingError) as cm:
            mapping.load(1, **self.kw)
        self.assertIn("sha256", str(cm.exception))
        os.remove(sealed_file)
        with self.assertRaises(mapping.MappingError):
            mapping.load(1, **self.kw)

    def test_codes_unique_across_rounds(self):
        with mock.patch.object(mapping, "_new_code", side_effect=["cand_aaaa", "cand_aaaa", "cand_bbbb", "cand_cccc"]):
            codes1 = mapping.commit_codes(1, MODELS, None, **self.kw)
        self.assertEqual(codes1, ["cand_aaaa", "cand_bbbb", "cand_cccc"])
        self.commit_round(1)
        prev = dict(zip(MODELS, codes1))
        seq = ["cand_bbbb", "cand_dddd", "cand_cccc", "cand_aaaa", "cand_eeee", "cand_dddd", "cand_ffff"]
        with mock.patch.object(mapping, "_new_code", side_effect=seq):
            codes2 = mapping.commit_codes(2, MODELS, prev, **self.kw)
        self.assertEqual(codes2, ["cand_dddd", "cand_eeee", "cand_ffff"])
        # the real generator: cand_ + 4 characters from [a-z0-9]
        for _ in range(50):
            self.assertTrue(re.fullmatch(r"cand_[a-z0-9]{4}", mapping._new_code()))


if __name__ == "__main__":
    unittest.main()
