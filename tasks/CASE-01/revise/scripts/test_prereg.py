"""Tests for prereg (pre-registration checks against the tags; CASE-01 stage B, Task 1, protocol section 15).
Run per module, never with discover. Every test works in a temporary git repository under tasks/CASE-01/runs/; tags
are created only there."""
import json
import os
import tempfile
import unittest

import prereg
import revpaths as rp
from test_stops import git

RUNS = os.path.join(rp.CASE, "runs")
R = "tasks/CASE-01/revise"
TIER1 = [f"{R}/protocol.md", f"{R}/prompts/template.md", f"{R}/scripts/tool.py", f"{R}/rules/preregistered.json",
         f"{R}/rules/scripts.sha256"]
TIER2 = [f"{R}/smoke/record.md", f"{R}/rules/expected.json", f"{R}/rules/prereg_tier1.sha256"]
LOCAL = f"{R}/impl_plan.md"


class Base(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="prereg_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.repo = self.tmp.name
        git(self.repo, "init", "-q", ".")
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "core.autocrlf", "false")
        for rel in [f"{R}/protocol.md", f"{R}/prompts/template.md", f"{R}/scripts/tool.py"]:
            self.write(rel, f"content of {rel}\n")
        self.write(LOCAL, "local plan\n")
        self.manifest = {"tier1": {"tracked": list(TIER1), "local_hash": {LOCAL: rp.sha256(self.p(LOCAL))}},
                         "tier2": {"tracked": list(TIER2)},
                         "generated": [f"{R}/outputs/", f"{R}/results/"]}
        self.write(f"{R}/rules/preregistered.json", json.dumps(self.manifest, indent=1) + "\n")
        self.commit(*[r for r in TIER1 if not r.endswith(".sha256")])

    def p(self, rel):
        return os.path.join(self.repo, *rel.split("/"))

    def write(self, rel, text):
        os.makedirs(os.path.dirname(self.p(rel)), exist_ok=True)
        with open(self.p(rel), "wb") as f:
            f.write(text.encode("utf-8"))

    def commit(self, *rels):
        git(self.repo, "add", "--", *rels)
        git(self.repo, "commit", "-q", "-m", "c")

    def write_lists(self, names):
        lists = prereg.expected_hash_lists(names, repo=self.repo)
        for name in names:
            self.write(f"{R}/rules/{name}", lists[name])

    def smoke_tag(self):
        self.write_lists(["scripts.sha256", "prereg_tier1.sha256"])
        self.commit(f"{R}/rules/scripts.sha256", f"{R}/rules/prereg_tier1.sha256")
        git(self.repo, "tag", prereg.TAGS["smoke"])

    def formal_tag(self, commit_record=True):
        self.write(f"{R}/smoke/record.md", "smoke part 3: all as expected\n")
        self.write(f"{R}/rules/expected.json", "{}\n")
        self.write_lists(["prereg_tier2.sha256"])
        rels = [f"{R}/rules/expected.json", f"{R}/rules/prereg_tier2.sha256"]
        if commit_record:
            rels.append(f"{R}/smoke/record.md")
        self.commit(*rels)
        git(self.repo, "tag", "-a", "-m", "formal", prereg.TAGS["formal"])


class TestPrereg(Base):
    def test_ok_and_committed_unchanged(self):
        self.smoke_tag()
        self.assertEqual(prereg.problems("smoke", repo=self.repo), [])
        self.formal_tag()
        self.assertEqual(prereg.problems("formal", repo=self.repo), [])
        self.assertEqual(prereg.problems("smoke", repo=self.repo), [])
        self.assertTrue(prereg.committed_unchanged(self.p(f"{R}/protocol.md")))
        self.assertFalse(prereg.committed_unchanged(self.p(LOCAL)))
        self.assertFalse(prereg.committed_unchanged(self.p(f"{R}/no_such_file")))
        with self.assertRaises(ValueError):
            prereg.problems("other", repo=self.repo)

    def test_local_hash_file_not_tracked_is_ok(self):
        self.smoke_tag()
        self.assertEqual(prereg.problems("smoke", repo=self.repo), [])
        self.write(LOCAL, "local plan, edited\n")
        probs = prereg.problems("smoke", repo=self.repo)
        self.assertTrue(probs)
        self.assertTrue(any("impl_plan.md" in p for p in probs))

    def test_frozen_template_change_rejected(self):
        self.smoke_tag()
        tmpl = f"{R}/prompts/template.md"
        self.write(tmpl, "changed\n")                       # uncommitted change
        self.assertTrue(any("template.md" in p for p in prereg.problems("smoke", repo=self.repo)))
        self.commit(tmpl)                                    # committed after the tag
        self.assertTrue(any("template.md" in p for p in prereg.problems("smoke", repo=self.repo)))

    def test_new_generated_file_not_rejected(self):
        self.smoke_tag()
        self.write(f"{R}/outputs/r1/codes.txt", "cand_aaaa\n")
        self.commit(f"{R}/outputs/r1/codes.txt")
        self.write(f"{R}/results/r1/note.txt", "x\n")       # untracked generated file
        self.assertEqual(prereg.problems("smoke", repo=self.repo), [])

    def test_tracked_entry_under_generated_prefix_rejected(self):
        self.manifest["tier1"]["tracked"].append(f"{R}/outputs/r1/codes.txt")
        self.write(f"{R}/rules/preregistered.json", json.dumps(self.manifest, indent=1) + "\n")
        self.write(f"{R}/outputs/r1/codes.txt", "cand_aaaa\n")
        self.commit(f"{R}/rules/preregistered.json", f"{R}/outputs/r1/codes.txt")
        self.smoke_tag()
        self.assertTrue(any("generated" in p for p in prereg.problems("smoke", repo=self.repo)))

    def test_untracked_file_in_scripts_rejected(self):
        self.smoke_tag()
        # untracked, would shadow an import of the frozen scripts
        self.write(f"{R}/scripts/extra.py", "x = 1\n")
        probs = prereg.problems("smoke", repo=self.repo)
        self.assertTrue(any("extra.py" in p for p in probs), probs)
        os.remove(self.p(f"{R}/scripts/extra.py"))
        self.write(f"{R}/scripts/__pycache__/tool.cpython-312.pyc", "x")   # byte-code cache is not reported
        self.assertEqual(prereg.problems("smoke", repo=self.repo), [])
        self.write(f"{R}/.gitignore", "scripts/ignored.py\n")
        self.write(f"{R}/scripts/ignored.py", "x = 1\n")    # ignored files count as well
        self.assertTrue(any("ignored.py" in p for p in prereg.problems("smoke", repo=self.repo)))

    def test_hash_lists_are_inside_the_tag(self):
        git(self.repo, "tag", prereg.TAGS["smoke"])          # tag first, lists committed afterwards
        self.write_lists(["scripts.sha256", "prereg_tier1.sha256"])
        self.commit(f"{R}/rules/scripts.sha256", f"{R}/rules/prereg_tier1.sha256")
        probs = prereg.problems("smoke", repo=self.repo)
        self.assertTrue(any("prereg_tier1.sha256" in p for p in probs))
        self.assertTrue(any("scripts.sha256" in p for p in probs))

    def test_tampered_hash_list_rejected(self):
        self.smoke_tag()
        lst = f"{R}/rules/prereg_tier1.sha256"
        with open(self.p(lst), encoding="utf-8") as f:
            lines = f.read().splitlines()
        lines = [("0" * 64 + ln[64:]) if ln.endswith("protocol.md") else ln for ln in lines]
        self.write(lst, "\n".join(lines) + "\n")
        self.assertTrue(any("prereg_tier1.sha256" in p for p in prereg.problems("smoke", repo=self.repo)))
        self.commit(lst)
        probs = prereg.problems("smoke", repo=self.repo)
        self.assertTrue(any("prereg_tier1.sha256" in p for p in probs))
        self.assertTrue(any("protocol.md" in p for p in probs))
        # a scripts file missing from scripts.sha256 is rejected as well
        self.write(f"{R}/scripts/added.py", "x = 1\n")
        self.commit(f"{R}/scripts/added.py")
        self.assertTrue(any("added.py" in p for p in prereg.problems("smoke", repo=self.repo)))

    def test_missing_test_record_in_tier2_rejected(self):
        self.smoke_tag()
        self.formal_tag(commit_record=False)                 # the smoke record listed in tier 2 is not committed
        probs = prereg.problems("formal", repo=self.repo)
        self.assertTrue(any("record.md" in p for p in probs))
        self.assertEqual(prereg.problems("smoke", repo=self.repo), [])

    def test_formal_mode_without_tier2_tag_rejected(self):
        self.smoke_tag()
        probs = prereg.problems("formal", repo=self.repo)
        self.assertTrue(probs)
        self.assertTrue(any(prereg.TAGS["formal"] in p for p in probs))
        empty = prereg.problems("smoke", repo=os.path.join(self.repo, R))   # not the repository root
        self.assertTrue(empty)


if __name__ == "__main__":
    unittest.main()
