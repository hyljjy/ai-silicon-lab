"""Unit tests of the CASE-02 run_round.py with a fake claude (no model is called). Windows Python, from
tasks/CASE-02/scripts:  python -B -m unittest -v test_run_round
Adapted from tasks/CASE-01/diag/scripts/test_run_round.py; the new tests cover the output monitoring, the probe mode,
the label check and the CASE-02 tags."""
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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "scripts")
              if os.path.basename(os.path.dirname(HERE)) == "impl" else HERE)
import c2paths  # noqa: E402
import run_round as rr  # noqa: E402

FAKE = os.path.join(HERE, "fake_claude_c2.py")
EMAIL = "someone.test@example.org"
NAMES = ("claude", "kimi", "deepseek")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="c2_run_round_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.case = os.path.join(self.tmp, "CASE-02")
        for name in ("run_order.json", "expected.json"):
            shutil.copyfile(os.path.join(c2paths.RULES, name), os.path.join(self.mkdir("rules"), name))
        write(os.path.join(self.case, "rules", "cli.sha256"), f"{sha(FAKE)}  claude-2.1.296.exe\n")
        write(os.path.join(self.case, "rules", "label_words.txt"), "correct\nmissing\nrestored\nmutation\n")
        write(os.path.join(self.case, "prompts", "system.md"), "系统提示\n")
        write(os.path.join(self.case, "prompts", "round1_user.md"), "第 1 轮题目\n")
        write(os.path.join(self.case, "prompts", "smoke_system.md"), "系统暗号是：青松-0427。\n")
        write(os.path.join(self.case, "prompts", "smoke_user.md"), "本题的暗号是：白鹭-1010。\n")
        shutil.copyfile(os.path.join(c2paths.PROMPTS, "cap_probe_user.md"), os.path.join(self.case, "prompts", "cap_probe_user.md"))
        for n in ("blank", "prose", "report"):
            write(os.path.join(self.case, "prompts", f"budget_probe_{n}.md"), "x" * {"blank": 100, "prose": 8000, "report": 8000}[n] + "\n")
        self.mkdir("outputs")
        self.profile = os.path.join(self.tmp, "profile")
        sums = []
        for n in NAMES:
            write(os.path.join(self.profile, ".diag-models", f"{n}.json"), '{"env": {}}\n')
            sums.append(f"{sha(os.path.join(self.profile, '.diag-models', f'{n}.json'))}  %USERPROFILE%/.diag-models/{n}.json\n")
        write(os.path.join(self.case, "models", "originals.sha256"), "".join(sums))
        self.sandbox = os.path.join(self.tmp, "sandbox")
        env = {"CASE01_PRIVACY_EMAIL": EMAIL, "FAKE_EMAIL": EMAIL, "USERPROFILE": self.profile}
        self.patch = mock.patch.dict(os.environ, dict(env, ANTHROPIC_BASE_URL="http://leak", CLAUDECODE="1"))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.scenarios({})

    def mkdir(self, rel):
        p = os.path.join(self.case, rel)
        os.makedirs(p, exist_ok=True)
        return p

    def scenarios(self, mapping):
        os.environ["FAKE_CLAUDE_SCENARIOS"] = json.dumps(mapping)

    def runner(self, **limits):
        r = rr.RoundRunner(self.tmp, self.case, self.sandbox, [sys.executable, FAKE], limits=limits or None)
        r.round1_bytes = lambda: "第 1 轮题目\n".encode("utf-8")
        return r

    def started(self):
        r = self.runner()
        r.init_mapping()
        return r

    def read(self, *rel):
        with open(os.path.join(self.case, *rel), encoding="utf-8") as f:
            return f.read()


class TestConstants(unittest.TestCase):
    def test_tags_case02(self):
        self.assertEqual(rr.TAGS, {"smoke": "case02-prereg", "round": "case02-prereg-round"})

    def test_sealed_dir_name(self):
        r = rr.RoundRunner("/r", "/c", "/sb", ["x"])
        self.assertTrue(r.sealed.replace("\\", "/").endswith("/sb/sealed-case02"))

    def test_default_limits_from_contract(self):
        r = rr.RoundRunner("/r", "/c", "/sb", ["x"])
        self.assertEqual((r.limits["process_seconds"], r.limits["stdout_bytes"], r.limits["stderr_bytes"]),
                         (1800, 52428800, 1048576))


class TestLimits(Base):
    def test_stdout_limit_terminates_and_records(self):
        self.scenarios({"k3[1M]": "bigout"})
        r = self.started()
        r.limits["stdout_bytes"] = 200000
        r.limits["poll_seconds"] = 0.2
        lines = r.run_round(1)
        with open(os.path.join(self.sandbox, "sealed-case02", "round1", "kimi-1.proc.json"), encoding="utf-8") as f:
            proc = json.load(f)
        self.assertEqual(proc["limit_hit"], "stdout_bytes")
        self.assertTrue(proc["terminated"])
        self.assertTrue(any("作废" in l for l in lines))

    def test_stderr_limit(self):
        self.scenarios({"deepseek-v4-pro[1M]": "bigerr"})
        r = self.started()
        r.limits["stderr_bytes"] = 50000
        r.limits["poll_seconds"] = 0.2
        r.run_round(1)
        with open(os.path.join(self.sandbox, "sealed-case02", "round1", "deepseek-1.proc.json"), encoding="utf-8") as f:
            proc = json.load(f)
        self.assertEqual(proc["limit_hit"], "stderr_bytes")

    def test_timeout_two_stage_kill(self):
        self.scenarios({"claude-opus-5-5": "hang"})
        r = self.started()
        r.limits["process_seconds"] = 2
        r.limits["poll_seconds"] = 0.2
        r.limits["soft_kill_wait_seconds"] = 1
        r.limits["hard_kill_wait_seconds"] = 1
        r.run_round(1)
        with open(os.path.join(self.sandbox, "sealed-case02", "round1", "claude-1.proc.json"), encoding="utf-8") as f:
            proc = json.load(f)
        self.assertEqual(proc["limit_hit"], "process_seconds")
        self.assertIn(proc["kill_stage"], ("soft", "hard"))
        with open(os.path.join(self.sandbox, "sealed-case02", "round1", "claude-1.meta.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["exit"], "timeout")

    def test_normal_run_records_sizes(self):
        r = self.started()
        r.run_round(1)
        with open(os.path.join(self.sandbox, "sealed-case02", "round1", "claude-1.proc.json"), encoding="utf-8") as f:
            proc = json.load(f)
        self.assertIsNone(proc["limit_hit"])
        self.assertGreater(proc["stdout_bytes"], 0)


class TestRound(Base):
    def test_round1_all_valid_and_repository_side_neutral(self):
        self.scenarios({"k3[1M]": "email"})
        lines = self.started().run_round(1)
        self.assertEqual(len(lines), 3)
        self.assertTrue(all("通过" in l for l in lines))
        for c in rr.CODES:
            a = self.read("outputs", "round1", f"{c}.md")
            self.assertIn("leaked=[]", a)
            self.assertNotIn(EMAIL, a)
        status = self.read("outputs", "round1", "status.md")
        for n in NAMES:
            self.assertNotIn(n, status)

    def test_refuses_operator_label_in_prompt(self):
        r = self.started()
        write(os.path.join(self.case, "prompts", "round1_user.md"), "第 1 轮题目\n### 文件 summary_missing.tsv\n")
        r.round1_bytes = lambda: "第 1 轮题目\n### 文件 summary_missing.tsv\n".encode("utf-8")
        with self.assertRaises(SystemExit):
            r.run_round(1)
        self.assertFalse(os.path.exists(os.path.join(self.sandbox, "sealed-case02", "round1", "attempts.json")))

    def test_model_prose_in_prompt_allowed(self):
        r = self.started()
        text = "第 1 轮题目\n<<<第 1 轮回答开始>>>\nI think constraints are missing\n<<<第 1 轮回答结束>>>\n"
        write(os.path.join(self.case, "prompts", "round1_user.md"), text)
        r.round1_bytes = lambda: text.encode("utf-8")
        lines = r.run_round(1)
        self.assertEqual(len(lines), 3)


class TestProbe(Base):
    def test_probe_mode_saves_usage_only(self):
        r = self.runner()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = r.probe()
        self.assertEqual(rc, 0, out.getvalue())
        probe_dir = next(d for d in os.listdir(self.sandbox) if d.startswith("smoke-case02-budget"))
        files = os.listdir(os.path.join(self.sandbox, probe_dir))
        self.assertIn("usage.json", files)
        self.assertFalse(any(f.endswith(".answer.md") for f in files))
        with open(os.path.join(self.sandbox, probe_dir, "usage.json"), encoding="utf-8") as f:
            usage = json.load(f)
        self.assertEqual(set(usage), set(NAMES))
        self.assertEqual(set(usage["claude"]), {"blank", "prose", "report"})
        self.assertIn("input_tokens", usage["claude"]["prose"])
        self.assertIn("prompt_bytes", usage["claude"]["prose"])
        self.assertIn("PROBE OK", out.getvalue())


class TestSmoke(Base):
    def smoke(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = self.runner().smoke()
        return rc, out.getvalue()

    def test_smoke_ok(self):
        rc, out = self.smoke()
        self.assertEqual(rc, 0, out)
        for name in NAMES:
            self.assertIn(f"{name}: cap_probe capped=True", out)


class TestR6Prereg(unittest.TestCase):
    """CASE02_R6 M10: read-only dependencies outside the tier-1 paths ("dep <path>" lines of preregistered.txt) are
    verified before a run against the hash registered in rules/copied_from.tsv."""

    def test_dep_lines_verified_by_hash(self):
        tmp = tempfile.mkdtemp(prefix="c2_dep_")
        self.addCleanup(shutil.rmtree, tmp, True)
        dep = os.path.join(tmp, "tasks", "CASE-01", "scripts", "logcheck.py")
        write(dep, "print(1)\n")
        copied = os.path.join(tmp, "copied_from.tsv")
        write(copied, "case02_path\tcase01_path\tcase01_sha256\tdiff_file\tnote\n"
              f"scripts/(import) logcheck\ttasks/CASE-01/scripts/logcheck.py\t{sha(dep)}\t-\tread-only import\n")
        lst = os.path.join(tmp, "preregistered.txt")
        write(lst, "tasks/CASE-02/rules\ndep tasks/CASE-01/scripts/logcheck.py\n")
        self.assertEqual(rr.prereg_paths(lst, "round")["smoke"], ["tasks/CASE-02/rules"])
        self.assertEqual(rr.dep_problems(tmp, lst, copied), [])
        write(dep, "print(2)\n")
        probs = rr.dep_problems(tmp, lst, copied)
        self.assertTrue(any("logcheck.py" in p for p in probs), probs)
        write(lst, "dep tasks/CASE-01/scripts/other.py\n")
        self.assertTrue(any("not registered" in p for p in rr.dep_problems(tmp, lst, copied)))


if __name__ == "__main__":
    unittest.main()


class TestR6Shell(Base):
    """CASE02_R6 M12: size limits are checked after a normal exit too; the hard stage kills the whole tree; waits recorded."""

    def test_burst_then_exit_is_still_output_limit(self):
        self.scenarios({"k3[1M]": "burstexit"})
        r = self.started()
        r.limits["stdout_bytes"] = 100000
        r.limits["poll_seconds"] = 5          # longer than the burst, so only the post-exit check can see it
        r.run_round(1)
        with open(os.path.join(self.sandbox, "sealed-case02", "round1", "kimi-1.proc.json"), encoding="utf-8") as f:
            proc = json.load(f)
        self.assertEqual(proc["limit_hit"], "stdout_bytes")
        self.assertIn("waits", proc)

    def test_child_of_child_killed_on_timeout(self):
        self.scenarios({"claude-opus-5-5": "hangtree"})
        r = self.started()
        r.limits["process_seconds"] = 2
        r.limits["poll_seconds"] = 0.2
        r.limits["soft_kill_wait_seconds"] = 1
        r.limits["hard_kill_wait_seconds"] = 2
        r.run_round(1)
        with open(os.path.join(self.sandbox, "sealed-case02", "round1", "claude-1.proc.json"), encoding="utf-8") as f:
            proc = json.load(f)
        self.assertEqual(proc["limit_hit"], "process_seconds")
        self.assertTrue(proc["tree_clean"], proc)
