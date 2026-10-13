"""Unit tests of run_round.py with a fake claude (no model is called). Windows Python, from this directory:
  python -B -m unittest test_run_round"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import run_round as rr

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = os.path.join(HERE, "fake_claude.py")
EMAIL = "someone.test@example.org"
NAMES = ("claude", "kimi", "deepseek")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def git_in(repo):
    run = lambda *a: subprocess.run(["git", "-C", repo] + list(a), capture_output=True, check=True)
    run("init", "-q")
    run("config", "user.email", "t@example.org")
    run("config", "user.name", "t")
    return run


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="run_round_test_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.diag = os.path.join(self.tmp, "diag")
        for name in ("run_order.json", "expected.json"):
            shutil.copyfile(os.path.join(HERE, "..", "rules", name), os.path.join(self.mkdir("rules"), name))
        write(os.path.join(self.diag, "rules", "cli.sha256"), f"{sha(FAKE)}  claude-2.1.296.exe\n")
        write(os.path.join(self.diag, "prompts", "system.md"), "系统提示\n")
        write(os.path.join(self.diag, "prompts", "round1_user.md"), "第 1 轮题目\n")
        write(os.path.join(self.diag, "prompts", "smoke_system.md"), "系统暗号是：青松-0427。\n")
        write(os.path.join(self.diag, "prompts", "smoke_user.md"), "本题的暗号是：白鹭-1010。\n")
        shutil.copyfile(os.path.join(HERE, "..", "prompts", "cap_probe_user.md"),      # the real probe prompt
                        os.path.join(self.diag, "prompts", "cap_probe_user.md"))
        self.mkdir("outputs")
        self.profile = os.path.join(self.tmp, "profile")
        sums = []
        for n in NAMES:
            write(os.path.join(self.profile, ".diag-models", f"{n}.json"), '{"env": {}}\n')
            sums.append(f"{sha(os.path.join(self.profile, '.diag-models', f'{n}.json'))}  "
                        f"%USERPROFILE%/.diag-models/{n}.json\n")
        write(os.path.join(self.diag, "models", "originals.sha256"), "".join(sums))
        self.sandbox = os.path.join(self.tmp, "sandbox")
        env = {"CASE01_PRIVACY_EMAIL": EMAIL, "FAKE_EMAIL": EMAIL, "USERPROFILE": self.profile}
        self.patch = mock.patch.dict(os.environ, dict(env, ANTHROPIC_BASE_URL="http://leak", CLAUDECODE="1"))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.scenarios({})

    def mkdir(self, rel):
        p = os.path.join(self.diag, rel)
        os.makedirs(p, exist_ok=True)
        return p

    def scenarios(self, mapping):
        os.environ["FAKE_CLAUDE_SCENARIOS"] = json.dumps(mapping)

    def runner(self):
        r = rr.RoundRunner(self.tmp, self.diag, self.sandbox, [sys.executable, FAKE])
        r.round1_bytes = lambda: "第 1 轮题目\n".encode("utf-8")
        return r

    def started(self):
        """A runner whose mapping is initialised, as after --init-mapping."""
        r = self.runner()
        r.init_mapping()
        return r

    def read(self, *rel):
        with open(os.path.join(self.diag, *rel), encoding="utf-8") as f:
            return f.read()

    def mapping(self):
        with open(os.path.join(self.sandbox, "sealed", "mapping.json"), encoding="utf-8") as f:
            return json.load(f)["codes"]

    def code_of(self, name):
        return next(c for c, n in self.mapping().items() if n == name)


class TestHelpers(unittest.TestCase):
    def test_clean_env(self):
        env = rr.clean_env({"PATH": "p", "ANTHROPIC_BASE_URL": "x", "CLAUDE_CODE_SIMPLE": "1", "ClaudeCode": "1",
                            "anthropic_api_key": "k"})
        self.assertEqual(env, {"PATH": "p", "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "32000", "DISABLE_AUTOUPDATER": "1"})

    def test_redact(self):
        text, n = rr.redact("mail " + EMAIL.upper() + " path C:" + "\\" + "Users" + "\\" + "bob\\x"
                            + r" cwd D:\study\diag_sandbox\run-0a1b2c3d", EMAIL)
        self.assertEqual(n, 3)
        self.assertNotIn(EMAIL.upper(), text)
        self.assertNotIn("run-0a1b2c3d", text)
        self.assertEqual(text.count(rr.HIDDEN), 3)


class TestPrereg(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="prereg_test_")
        self.addCleanup(shutil.rmtree, self.repo, True)
        self.git = git_in(self.repo)
        write(os.path.join(self.repo, "a.txt"), "a\n")
        write(os.path.join(self.repo, "d", "b.txt"), "b\n")
        write(os.path.join(self.repo, "list.txt"), "# pre-registered\na.txt\nround d\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "x")
        self.list = os.path.join(self.repo, "list.txt")

    def test_tiers(self):
        self.assertEqual(rr.prereg_paths(self.list, "smoke"), {"smoke": ["a.txt"], "round": []})
        self.assertEqual(rr.prereg_paths(self.list, "round"), {"smoke": ["a.txt"], "round": ["d"]})

    def test_tracked_and_unchanged(self):
        self.assertEqual(rr.prereg_problems(self.repo, self.list, "round", use_tags=False), [])
        write(os.path.join(self.repo, "a.txt"), "changed\n")
        self.assertEqual(rr.prereg_problems(self.repo, self.list, "smoke", use_tags=False),
                         ["differs from HEAD: a.txt"])
        self.git("checkout", "--", "a.txt")
        write(os.path.join(self.repo, "d", "new.txt"), "n\n")
        self.assertEqual(rr.prereg_problems(self.repo, self.list, "round", use_tags=False),
                         ["untracked files under: d"])
        write(self.list, "a.txt\nnew.txt\n")
        self.assertIn("not tracked: new.txt", rr.tracked_problems(self.repo, ["new.txt"]))

    def test_tags(self):
        self.assertEqual(rr.prereg_problems(self.repo, self.list, "smoke"), ["tag diag-prereg does not exist"])
        self.git("tag", "diag-prereg")
        self.git("tag", "diag-prereg-round")
        self.assertEqual(rr.prereg_problems(self.repo, self.list, "round"), [])
        write(os.path.join(self.repo, "a.txt"), "changed and committed\n")
        self.git("commit", "-q", "-am", "edit after pre-registration")
        self.assertEqual(rr.prereg_problems(self.repo, self.list, "smoke"),
                         ["changed since tag diag-prereg: a.txt"])


class TestMapping(Base):
    def test_round1_needs_mapping(self):
        with self.assertRaises(SystemExit):
            self.runner().run_round(1)

    def test_init_mapping_and_commitment(self):
        r = self.runner()
        commitment = r.init_mapping()
        with open(r.mapping_path(), "rb") as f:
            raw = f.read()
        mapping = json.loads(raw)
        self.assertEqual(len(mapping["salt"]), 64)
        self.assertEqual(sorted(mapping["codes"]), list(rr.CODES))
        self.assertEqual(sorted(mapping["codes"].values()), sorted(NAMES))
        self.assertEqual(commitment, rr.sha256(raw))
        self.assertEqual(self.read("outputs", "mapping.sha256"), f"{commitment}  sealed/mapping.json\n")
        with self.assertRaises(SystemExit):
            r.init_mapping()

    def test_tampered_mapping_refused(self):
        r = self.started()
        with open(r.mapping_path(), "a", encoding="utf-8") as f:
            f.write(" ")
        with self.assertRaises(SystemExit):
            r.run_round(1)


class TestRound(Base):
    def test_round1_all_valid(self):
        self.scenarios({"k3[1M]": "email", "deepseek-v4-pro[1M]": "workdir"})
        lines = self.started().run_round(1)
        self.assertEqual(len(lines), 3)
        self.assertTrue(all("通过" in l for l in lines))
        answers = {c: self.read("outputs", "round1", f"{c}.md") for c in rr.CODES}
        self.assertTrue(all("leaked=[]" in a for a in answers.values()), "inherited variables reached claude")
        self.assertFalse(any(EMAIL in a or "run-" in a for a in answers.values()))
        self.assertIn(rr.HIDDEN, answers[self.code_of("kimi")])
        self.assertIn(rr.HIDDEN, answers[self.code_of("deepseek")])
        with open(os.path.join(self.sandbox, "sealed", "round1", "kimi-1.meta.json"), encoding="utf-8") as f:
            meta = json.load(f)
        self.assertEqual(meta["hidden_in_answer"], 1)
        self.assertEqual(os.listdir(meta["workdir"]), [])

    def test_repository_side_never_names_a_model(self):
        self.scenarios({"deepseek-v4-pro[1M]": "truncated"})
        self.started().run_round(1)
        text = "".join(self.read("outputs", "round1", n) for n in os.listdir(os.path.join(self.diag, "outputs",
                                                                                         "round1")))
        text += self.read("outputs", "mapping.sha256")
        for word in NAMES + ("k3", "opus", "deepseek"):
            self.assertNotIn(word, text.lower())

    def test_void_then_one_rerun(self):
        self.scenarios({"deepseek-v4-pro[1M]": "truncated"})
        lines = self.started().run_round(1)
        void = [l for l in lines if "作废" in l]
        self.assertEqual(len(void), 1)
        self.assertIn("运行未正常结束", void[0])
        self.assertIn("可补跑 1 次", void[0])
        code = void[0][2]
        self.assertFalse(os.path.exists(os.path.join(self.diag, "outputs", "round1", f"{code}.md")))
        self.scenarios({})
        lines = self.runner().rerun(1, code)       # a rerun is a new invocation: fresh environment snapshot
        self.assertIn(f"- {code}：通过（第 2 次尝试）", lines)
        self.assertTrue(os.path.exists(os.path.join(self.diag, "outputs", "round1", f"{code}.md")))
        with self.assertRaises(SystemExit):
            self.runner().rerun(1, code)

    def test_rerun_of_valid_code_refused(self):
        r = self.started()
        r.run_round(1)
        with self.assertRaises(SystemExit):
            r.rerun(1, "A")

    def test_round1_twice_refused(self):
        r = self.started()
        r.run_round(1)
        with self.assertRaises(SystemExit):
            r.run_round(1)

    def test_missing_memory_path_voids(self):
        self.scenarios({"claude-opus-5-5": "nomemory"})
        lines = self.started().run_round(1)
        self.assertEqual([l for l in lines if "作废" in l],
                         [f"- {self.code_of('claude')}：作废（原因类别：记录不完整），可补跑 1 次"])

    def test_prompt_mismatch_voids(self):
        write(os.path.join(self.diag, "prompts", "round1_user.md"), "被改过的题目\n")
        lines = self.started().run_round(1)
        self.assertTrue(all("题目字节不符" in l for l in lines))

    def test_workdirs_created_together(self):
        dirs = self.runner().make_workdirs(3)
        self.assertEqual(len(set(dirs)), 3)
        self.assertTrue(all(os.path.isdir(d) and not os.listdir(d) for d in dirs))


class TestResume(Base):
    def interrupted_round(self):
        """Round 1 that dies while the second model in run order is running."""
        r = self.started()
        real, calls = r.attempt, []

        def attempt(*a, **k):
            calls.append(1)
            if len(calls) == 2:
                raise KeyboardInterrupt("operator tool timed out")
            return real(*a, **k)
        r.attempt = attempt
        with self.assertRaises(KeyboardInterrupt):
            r.run_round(1)
        return r

    def test_interrupt_then_resume_then_rerun(self):
        r = self.interrupted_round()
        attempts = r.load_attempts(1)
        self.assertEqual([(a["model"], a["state"]) for a in attempts], [("claude", "done"), ("kimi", "started")])
        self.assertFalse(os.path.exists(os.path.join(self.diag, "outputs", "round1")))     # nothing written yet
        with self.assertRaises(SystemExit):
            self.runner().rerun(1, self.code_of("kimi"))                                   # resume first
        lines = self.runner().resume(1)
        kimi = self.code_of("kimi")
        self.assertIn(f"- {kimi}：作废（原因类别：运行中断），可补跑 1 次", lines)
        self.assertEqual(sum("通过（第 1 次尝试）" in l for l in lines), 2)
        attempts = self.runner().load_attempts(1)
        self.assertEqual([(a["model"], a["attempt"]) for a in attempts], [("claude", 1), ("kimi", 1), ("deepseek", 1)])
        lines = self.runner().rerun(1, kimi)
        self.assertIn(f"- {kimi}：通过（第 2 次尝试）", lines)
        self.assertEqual(sorted(os.listdir(os.path.join(self.diag, "outputs", "round1"))),
                         ["A.md", "B.md", "C.md", "status.md"])

    def test_resume_is_idempotent_after_a_finished_round(self):
        r = self.started()
        r.run_round(1)
        before = self.read("outputs", "round1", "A.md")
        self.runner().resume(1)
        self.assertEqual(self.read("outputs", "round1", "A.md"), before)
        self.assertEqual(len(self.runner().load_attempts(1)), 3)

    def test_resume_before_start_refused(self):
        with self.assertRaises(SystemExit):
            self.started().resume(1)


class TestRound2(Base):
    def test_round2_needs_committed_inputs_and_skips_unfinished_codes(self):
        self.scenarios({"deepseek-v4-pro[1M]": "truncated"})
        self.started().run_round(1)
        done = sorted(n[0] for n in os.listdir(os.path.join(self.diag, "outputs", "round1")) if n[1:] == ".md")
        self.assertEqual(len(done), 2)                       # the void code has no answer
        write(os.path.join(self.diag, "round2", "translation.tsv"), "code\n")
        for c in done:
            write(os.path.join(self.diag, "prompts", "round2", f"{c}.md"), f"round2 {c}\n")
            write(os.path.join(self.diag, "round2", f"{c}_results.md"), "r\n")
        git = git_in(self.tmp)
        r = self.runner()
        r.round2_bytes = lambda c: f"round2 {c}\n".encode()
        with self.assertRaises(SystemExit):                  # not committed yet
            r.run_round(2)
        git("add", "-A")
        git("commit", "-q", "-m", "round2 inputs")
        write(os.path.join(self.diag, "round2", "q", "A9.tcl"), "report_units\n")
        with self.assertRaises(SystemExit):                  # an uncommitted query file
            r.run_round(2)
        os.remove(os.path.join(self.diag, "round2", "q", "A9.tcl"))
        self.scenarios({})
        r = self.runner()
        r.round2_bytes = lambda c: f"round2 {c}\n".encode()
        lines = r.run_round(2)
        self.assertEqual(len(lines), 2)
        self.assertTrue(all("通过" in l for l in lines))


class TestPreflight(Base):
    def test_ok(self):
        self.assertEqual(self.runner().preflight(), [])

    def test_each_problem(self):
        os.environ.update(FAKE_CLAUDE_VERSION="2.1.300", FAKE_LOGGED_IN="0")
        write(os.path.join(self.profile, ".diag-models", "kimi.json"), '{"env": {"X": "changed"}}\n')
        write(os.path.join(self.diag, "rules", "cli.sha256"), "0" * 64 + "  claude-2.1.296.exe\n")
        problems = self.runner().preflight()
        self.assertEqual(problems, ["CLI file sha256 differs from rules/cli.sha256", "CLI version is not 2.1.296",
                                    "settings file of kimi differs from models/originals.sha256",
                                    "auth status is not logged in"])
        self.assertFalse(any(EMAIL in p for p in problems))


class TestSmoke(Base):
    def smoke(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = self.runner().smoke()
        return rc, out.getvalue()

    def test_smoke_ok(self):
        rc, out = self.smoke()
        self.assertEqual(rc, 0, out)
        # the reported field is Claude Code's per-model value, not the cap (diagnosed 2026-10-12)
        self.assertIn("claude: valid=True canaries=True per_turn_effort_active=True maxOutputTokens=128000", out)
        self.assertIn("kimi: valid=True canaries=True per_turn_effort_active=False maxOutputTokens=32000", out)
        for name in NAMES:                       # the 64-token cap probe must cut every model off
            self.assertIn(f"{name}: cap_probe capped=True", out)

    def test_smoke_detects_a_model_that_ignores_the_cap(self):
        self.scenarios({"deepseek-v4-pro[1M]": "nocap"})
        rc, out = self.smoke()
        self.assertEqual(rc, 1)
        self.assertIn("deepseek: cap_probe capped=False", out)
        self.assertIn("SMOKE FAIL", out)

    def test_smoke_detects_prompt_not_read_from_stdin(self):
        self.scenarios({"k3[1M]": "nostdin"})
        rc, out = self.smoke()
        self.assertEqual(rc, 1)
        self.assertIn("kimi: valid=True canaries=False", out)


class TestMainProcess(Base):
    """main() in a child process whose stdout is a pipe and without PYTHONIOENCODING: Chinese must print as UTF-8."""

    def run_main(self, *args, tag=None):
        write(os.path.join(self.diag, "rules", "preregistered.txt"), "diag/rules/run_order.json\n")
        git = git_in(self.tmp)
        git("add", "-A")
        git("commit", "-q", "-m", "prereg")
        if tag:
            git("tag", tag)
        env ={k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
        proc = subprocess.run([sys.executable, "-B", os.path.join(HERE, "run_round.py"), "--repo-root", self.tmp,
                               "--diag-dir", self.diag, "--sandbox-root", self.sandbox, "--no-tags",
                               "--claude-cmd", json.dumps([sys.executable, FAKE])] + list(args),
                              env=env, capture_output=True)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8", "replace")

    def test_no_tags_refused_once_a_tag_exists(self):
        rc, out, err = self.run_main("--smoke", tag="diag-prereg")
        self.assertEqual(rc, 1, err)
        self.assertIn("--no-tags is for tests only", out)
        self.assertFalse(os.path.exists(self.sandbox))

    def test_smoke_failure_prints_chinese_category(self):
        self.scenarios({"deepseek-v4-pro[1M]": "truncated"})
        rc, out, err = self.run_main("--smoke")
        self.assertEqual(rc, 1, err)
        self.assertIn("运行未正常结束", out)
        self.assertIn("SMOKE FAIL", out)

    def test_preflight_failure_uses_no_attempt(self):
        os.environ["FAKE_LOGGED_IN"] = "0"
        rc, out, err = self.run_main("--smoke")
        self.assertEqual(rc, 1, err)
        self.assertIn("PREFLIGHT auth status is not logged in", out)
        self.assertFalse(os.path.exists(self.sandbox) and any(n.startswith("smoke-") for n in os.listdir(self.sandbox)))


if __name__ == "__main__":
    unittest.main()
