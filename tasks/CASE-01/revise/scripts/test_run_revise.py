"""Tests for run_revise (Windows run shell, CASE-01 stage B Task 10; protocol 6, 7.1, 16).
Windows only (run per module, never with discover). The real Claude CLI is never run and the real model
configuration directory is never touched: every call runs fake_claude_b.py (it limits itself to 10 s and 1 MB) and
every settings file is a temporary file. Everything is written in a temporary git repository and a temporary sandbox
under tasks/CASE-01/runs/ (never the real revise/outputs, revise/stops, rtl/, config/ or D:\\study\\revise_sandbox)."""
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import limits
import mapping
import prereg
import revpaths as rp
import stops

if os.name == "nt":
    import fake_claude_b
    import run_revise

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = os.path.join(HERE, "fake_claude_b.py")
RUNS = os.path.join(rp.CASE, "runs")
GB = rp.GB
EMAIL = "someone.test@example.invalid"
GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_CEILING_DIRECTORIES")
MODELS = [("claude", "claude-opus-5-5"), ("kimi", "k3[1M]"), ("deepseek", "deepseek-v4-pro[1M]")]
MODEL_ID = dict(MODELS)
TEST_LIMIT = limits.Limit(30, 1 * limits.MB, 1 * limits.MB, 5, 5)
R = "tasks/CASE-01/revise"

DRIVER = """import json, sys
sys.path.insert(0, {scripts!r})
import limits, run_revise
limits.LIMITS["model"] = limits.Limit(30, limits.MB, limits.MB, 5, 5)
limits.LIMITS["preflight"] = limits.Limit(30, limits.MB, limits.MB, 5, 5)
sys.exit(run_revise.main(json.loads(sys.argv[1]), free_bytes=lambda v: 100 * 1024 ** 3))
"""


def git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
    r = subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=cwd, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=60)
    if r.returncode != 0:
        raise AssertionError(f"git {args} failed: {r.stderr.decode('utf-8', 'replace')}")
    return r.stdout.decode("utf-8", "replace")


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode("utf-8"))


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def alive(pid):
    return limits._start_time(pid) is not None


def wait_for(cond, timeout=8.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        v = cond()
        if v:
            return v
        time.sleep(0.05)
    raise AssertionError("condition not reached in time")


@unittest.skipIf(os.name != "nt", "test_run_revise runs only on Windows")
class Base(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="runrevise_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        t = self.tmp.name
        self.repo = os.path.join(t, "repo")
        self.case = os.path.join(self.repo, "tasks", "CASE-01")
        self.revise = os.path.join(self.case, "revise")
        self.sandbox = os.path.join(t, "sandbox")
        self.plan = os.path.join(t, "plan.json")
        self.log = os.path.join(t, "fake.log")
        os.makedirs(self.revise)
        git(self.repo, "init", "-q", ".")
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "core.autocrlf", "false")
        settings_dir = os.path.join(t, "settings")
        order, originals, expect = [], [], {}
        for name, model in MODELS:
            p = os.path.join(settings_dir, f"{name}.json")
            write(p, json.dumps({"env": {"X": name}}) + "\n")
            order.append({"name": name, "model": model, "settings": p})
            originals.append(f"{rp.sha256(p)}  %USERPROFILE%/.diag-models/{name}.json\n")
            expect[name] = {"init_model": model, "assistant_model": model, "cli_version": "2.1.296",
                            "max_output_tokens": 32000,
                            "plugins": ["cc-plugin-agents-md@builtin", "cc-plugin-plugin-authoring@builtin"]}
        rules = os.path.join(self.revise, "rules")
        write(os.path.join(rules, "run_order.json"), json.dumps({"models": order}, indent=1) + "\n")
        write(os.path.join(rules, "cli.sha256"), f"{rp.sha256(FAKE)}  fake_claude_b.py\n")
        write(os.path.join(rules, "expected.json"), json.dumps(expect, indent=1) + "\n")
        write(os.path.join(rules, "expected_tentative.json"), json.dumps(expect, indent=1) + "\n")
        write(os.path.join(self.revise, "models", "originals.sha256"), "".join(originals))
        write(os.path.join(self.revise, "prompts", "system.md"), "你是被测模型。正式系统提示。\n")
        write(os.path.join(self.revise, "prompts", "smoke_system.md"), "系统暗号是：红杉-0815。\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        self.set_plan({})
        self.env = dict(os.environ, FAKE_CLAUDE_PLAN=self.plan, FAKE_CLAUDE_LOG=self.log, CASE01_PRIVACY_EMAIL=EMAIL)
        for k in ("PYTHONIOENCODING", "PYTHONUTF8"):
            self.env.pop(k, None)
        for p in (mock.patch.dict(limits.LIMITS, {"model": TEST_LIMIT, "preflight": TEST_LIMIT}),
                  mock.patch.dict(os.environ, {"CASE01_PRIVACY_EMAIL": EMAIL})):
            p.start()
            self.addCleanup(p.stop)
        self.out = ""
        self.free = 100 * GB

    # ---- helpers
    def flags(self, no_tags=True):
        f = ["--claude-cmd", json.dumps([sys.executable, "-B", FAKE]), "--sandbox-root", self.sandbox,
             "--repo-root", self.repo]
        return f + (["--no-tags"] if no_tags else [])

    def run_main(self, *args, no_tags=True, env=None):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = run_revise.main(list(args) + self.flags(no_tags), free_bytes=lambda v: self.free,
                                 base_env=env or self.env)
        self.out = buf.getvalue()
        return rc

    def set_plan(self, plan):
        """plan: {run_order name: [scenarios]}."""
        write(self.plan, json.dumps({MODEL_ID[n]: s for n, s in plan.items()}))
        d = os.path.dirname(self.plan)
        for f in os.listdir(d):
            if f.startswith("plan.json.count."):
                os.remove(os.path.join(d, f))

    def calls(self, name=None):
        if not os.path.isfile(self.log):
            return []
        with open(self.log, encoding="utf-8") as f:
            rows = [json.loads(ln) for ln in f if ln.strip()]
        return [r for r in rows if name is None or r["model"] == MODEL_ID[name]]

    def commit(self, *paths, msg="c"):
        git(self.repo, "add", "--", *paths)
        git(self.repo, "commit", "-q", "-m", msg)

    def codes(self, rnd=1):
        m = mapping.load(rnd, revise=self.revise, sealed=os.path.join(self.sandbox, "sealed"))
        return {n: mapping.code_of(m, n) for n, _ in MODELS}

    def setup_round(self, commit_prompts=True):
        self.assertEqual(self.run_main("--commit-codes", "1"), 0, self.out)
        self.commit(f"{R}/outputs/r1/codes.txt", f"{R}/outputs/mapping_r1.sha256")
        self.code = self.codes()
        for name, code in self.code.items():
            write(self.prompt_path(code), f"第 1 轮题目，编号 {code}。\n请作答。\n")
        if commit_prompts:
            self.commit(f"{R}/prompts/r1")
        return self.code

    def prompt_path(self, code, rnd=1):
        return os.path.join(self.revise, "prompts", f"r{rnd}", f"{code}_prompt.md")

    def attempts(self):
        return load(os.path.join(self.revise, "outputs", "r1", "attempts.json"))

    def entry(self, name):
        return self.attempts()["codes"][self.code[name]]

    def outp(self, name, suffix):
        return os.path.join(self.revise, "outputs", "r1", f"{self.code[name]}{suffix}")

    def raw(self, name, fname):
        return os.path.join(self.sandbox, "raw", "r1", self.code[name], fname)

    def stop_records(self):
        d = os.path.join(self.revise, "stops", "r1")
        if not os.path.isdir(d):
            return []
        return [load(os.path.join(d, n)) for n in sorted(os.listdir(d)) if n.endswith(".json")]

    def clear_stop(self, rec):
        d = os.path.join(self.revise, "stops", "r1")
        path = os.path.join(d, f"{rec['stop_id']}.json")
        write(os.path.join(d, f"{rec['stop_id']}.cleared.md"),
              f"stop_id: {rec['stop_id']}\nstop_sha256: {rp.sha256(path)}\n作者已排查。\n")
        self.commit(f"{R}/stops/r1")

    def tamper(self, name, calls):
        """Patch read_call_inputs: the given call numbers of model `name` get different stdin bytes."""
        orig = run_revise.read_call_inputs
        seen = {}
        code = self.code[name]

        def fake(ctx, rnd, c):
            system, stdin, ok = orig(ctx, rnd, c)
            if c == code:
                seen[c] = seen.get(c, 0) + 1
                if seen[c] in calls:
                    return system, stdin + b"tampered\n", False
            return system, stdin, ok
        return mock.patch.object(run_revise, "read_call_inputs", fake)

    def driver(self, *args):
        cmd = [sys.executable, "-B", "-c", DRIVER.format(scripts=HERE), json.dumps(list(args) + self.flags())]
        p = subprocess.Popen(cmd, cwd=self.tmp.name, env=self.env, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        self.addCleanup(lambda: p.poll() is None and (p.kill(), p.wait()))
        return p

    def kill_shell_during(self, name, n, cond):
        """Run --round 1 in a shell process, wait until call n of `name` satisfies cond(jsonl bytes), kill the shell
        process only (the job object then ends the fake CLI)."""
        p = self.driver("--round", "1")

        def ready():
            path = self.raw(name, f"call{n}.jsonl")
            return os.path.isfile(self.raw(name, f"call{n}.proc.json")) and os.path.isfile(path) and \
                cond(rp.read_bytes(path))
        wait_for(ready, 9)
        p.kill()
        p.wait(timeout=30)
        pid = [c for c in self.calls(name)][-1]["pid"]
        wait_for(lambda: not alive(pid), 10)


# ------------------------------------------------------------------------------------- modes and preconditions
class TestModes(Base):
    def prereg_repo(self):
        manifest = {"tier1": {"tracked": [f"{R}/rules/run_order.json", f"{R}/prompts/smoke_system.md"],
                              "local_hash": {}},
                    "tier2": {"tracked": [f"{R}/rules/expected.json"]}, "generated": [f"{R}/outputs/"]}
        write(os.path.join(self.repo, *prereg.MANIFEST.split("/")), json.dumps(manifest, indent=1) + "\n")
        self.commit(prereg.MANIFEST)
        for name, text in prereg.expected_hash_lists(repo=self.repo).items():
            write(os.path.join(self.revise, "rules", name), text)
        self.commit(f"{R}/rules")
        git(self.repo, "tag", "revise-prereg-smoke")

    def test_smoke_mode_checks_tier1_only(self):
        self.prereg_repo()
        # tier 2 changes after the smoke tag: smoke mode does not look at it, formal mode refuses
        exp = os.path.join(self.revise, "rules", "expected.json")
        write(exp, rp.read_bytes(exp) + b"\n")
        self.commit(f"{R}/rules/expected.json")
        write(os.path.join(self.case, "runs", "revise-smoke", "prompts", "canary_user.md"), "本题暗号是：灰雁-2026。\n")
        self.set_plan({n: ["prompt_echo"] for n, _ in MODELS})
        self.assertEqual(self.run_main("--smoke", "canary", no_tags=False), 0, self.out)
        self.assertIn("SMOKE canary OK", self.out)
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(self.run_main("--round", "1", no_tags=False), 1)
        self.assertIn("PREREG FAIL", self.out)
        self.assertIn("revise-prereg does not exist", self.out)
        self.assertEqual(len(self.calls()), 3)

    def test_formal_mode_requires_tier2_tag(self):
        self.prereg_repo()
        self.assertEqual(self.run_main("--commit-codes", "1", no_tags=False), 1)
        self.assertIn("tag revise-prereg does not exist", self.out)
        git(self.repo, "tag", "revise-prereg")
        self.assertEqual(self.run_main("--commit-codes", "1", no_tags=False), 0, self.out)
        # once a tag exists, --no-tags is refused
        self.assertEqual(self.run_main("--commit-codes", "2"), 1)
        self.assertIn("--no-tags", self.out)

    def test_round_number_must_be_1_or_2(self):
        for args in (["--round", "3"], ["--resume", "0"], ["--commit-codes", "x"], ["--round", "12"]):
            self.assertEqual(self.run_main(*args), 2, args)
        self.assertEqual(self.calls(), [])

    def test_preflight_failure_consumes_nothing(self):
        self.setup_round()
        self.assertEqual(self.run_main("--round", "1", env=dict(self.env, FAKE_LOGGED_IN="0")), 1)
        self.assertIn("PREFLIGHT FAIL: auth status is not logged in", self.out)
        settings = os.path.join(self.tmp.name, "settings", "kimi.json")
        write(settings, rp.read_bytes(settings) + b" ")
        self.assertEqual(self.run_main("--round", "1"), 1)
        self.assertIn("settings file kimi.json differs", self.out)
        self.assertEqual(self.calls(), [])
        self.assertFalse(os.path.exists(os.path.join(self.revise, "outputs", "r1", "attempts.json")))

    def test_low_disk_refuses(self):
        self.setup_round()
        self.free = 1 * GB
        self.assertEqual(self.run_main("--round", "1"), 1)
        self.assertIn("DISK FAIL", self.out)
        self.assertEqual(self.calls(), [])
        self.assertFalse(os.path.exists(os.path.join(self.revise, "outputs", "r1", "attempts.json")))


# ------------------------------------------------------------------------------------- codes and prompts
class TestCodes(Base):
    def test_codes_committed_before_any_call(self):
        self.assertEqual(self.run_main("--round", "1"), 1)
        self.assertIn("MAPPING FAIL", self.out)
        self.assertEqual(self.run_main("--commit-codes", "1"), 0)
        self.assertIn("请提交这两个文件", self.out)
        self.assertEqual(self.run_main("--round", "1"), 1)            # written but not committed
        self.assertIn("MAPPING FAIL", self.out)
        self.assertEqual(self.calls(), [])
        codes = rp.read_bytes(os.path.join(self.revise, "outputs", "r1", "codes.txt")).decode().split()
        self.assertEqual(codes, sorted(codes))
        self.assertEqual(len(codes), 3)

    def test_mapping_mismatch_refuses(self):
        self.setup_round()
        sealed = os.path.join(self.sandbox, "sealed", "mapping_r1.json")
        write(sealed, rp.read_bytes(sealed) + b" ")
        self.assertEqual(self.run_main("--round", "1"), 1)
        self.assertIn("MAPPING FAIL", self.out)
        self.assertEqual(self.calls(), [])

    def test_commit_codes_twice_refused(self):
        self.assertEqual(self.run_main("--commit-codes", "1"), 0)
        before = rp.read_bytes(os.path.join(self.revise, "outputs", "r1", "codes.txt"))
        self.assertEqual(self.run_main("--commit-codes", "1"), 1)
        self.assertIn("already exist", self.out)
        self.assertEqual(rp.read_bytes(os.path.join(self.revise, "outputs", "r1", "codes.txt")), before)

    def test_round2_codes_require_round1_complete(self):
        self.setup_round()
        write(os.path.join(self.revise, "outputs", "r1", "status.md"), "# 状态\n")
        self.commit(f"{R}/outputs/r1/status.md")
        self.assertEqual(self.run_main("--commit-codes", "2"), 1)
        self.assertIn("round_complete.json", self.out)
        self.assertFalse(os.path.exists(os.path.join(self.revise, "outputs", "r2", "codes.txt")))
        write(os.path.join(self.revise, "outputs", "r1", "round_complete.json"), "{}\n")
        self.commit(f"{R}/outputs/r1/round_complete.json")
        self.assertEqual(self.run_main("--commit-codes", "2"), 0, self.out)
        self.assertTrue(os.path.exists(os.path.join(self.revise, "outputs", "r2", "codes.txt")))

    def test_prompt_must_be_committed(self):
        self.setup_round(commit_prompts=False)
        self.assertEqual(self.run_main("--round", "1"), 1)
        self.assertIn("PROMPT FAIL", self.out)
        self.assertEqual(self.calls(), [])
        self.assertFalse(os.path.exists(os.path.join(self.revise, "outputs", "r1", "attempts.json")))

    def test_stdin_bytes_equal_committed_prompt(self):
        self.setup_round()
        env = dict(self.env, ANTHROPIC_API_KEY="x", CLAUDE_CONFIG_DIR="y", CLAUDECODE="1")
        self.assertEqual(self.run_main("--round", "1", env=env), 0, self.out)
        for name, code in self.code.items():
            (c,) = self.calls(name)
            want = rp.sha256(self.prompt_path(code))
            self.assertEqual(c["stdin_sha256"], want)
            self.assertEqual(load(self.raw(name, "call1.meta.json"))["stdin_sha"], want)
            self.assertEqual(load(self.outp(name, ".parsed.json"))["hashes"]["stdin_sha"], want)
            self.assertEqual(c["leaked_env"], [])
            self.assertEqual(c["max_output_tokens"], 32000)
            for flag in ("-p", "--tools", "--strict-mcp-config", "--no-session-persistence", "--verbose"):
                self.assertIn(flag, c["argv"])
            self.assertEqual(c["argv"][c["argv"].index("--tools") + 1], "")
            self.assertNotIn("--effort", c["argv"])
            self.assertEqual(c["argv"][c["argv"].index("--model") + 1], MODEL_ID[name])


# ------------------------------------------------------------------------------------- state machine
class TestStates(Base):
    def test_round_twice_refused(self):
        self.setup_round()
        self.assertEqual(self.run_main("--round", "1"), 0, self.out)
        self.assertEqual(self.run_main("--round", "1"), 1)
        self.assertIn("--resume", self.out)
        self.assertEqual(len(self.calls()), 3)

    def test_retry_once_then_unavailable(self):
        self.setup_round()
        self.set_plan({"claude": ["wrong_model", "multiturn_no_limit"]})
        self.assertEqual(self.run_main("--round", "1"), 0, self.out)
        e = self.entry("claude")
        self.assertEqual((e["state"], e["consumed"], e["final"]), ("final", 2, "unavailable"))
        call = load(self.outp("claude", ".call.json"))
        self.assertEqual(call["final"], "unavailable")
        self.assertEqual([c["categories"] for c in call["calls"]], [["模型不符"], ["异常多轮"]])
        self.assertFalse(os.path.exists(self.outp("claude", ".md")))
        self.assertFalse(os.path.exists(self.outp("claude", ".parsed.json")))
        self.assertEqual(len(self.calls("claude")), 2)
        self.assertEqual(self.entry("kimi")["final"], "parse")

    def test_retry_then_limit(self):
        self.setup_round()
        self.set_plan({"claude": ["wrong_model", "max_tokens"]})
        self.assertEqual(self.run_main("--round", "1"), 0, self.out)
        e = self.entry("claude")
        self.assertEqual((e["state"], e["consumed"], e["final"]), ("final", 2, "delivery_fail"))
        call = load(self.outp("claude", ".call.json"))
        self.assertIn("输出上限", call["calls"][-1]["categories"])
        self.assertTrue(os.path.exists(self.outp("claude", ".md")))       # partial public answer
        self.assertFalse(os.path.exists(os.path.join(self.case, "rtl", f"dot4sat_{self.code['claude']}.v")))

    def test_limit_never_retries(self):
        self.setup_round()
        self.set_plan({"claude": ["max_tokens_bad_lines", "ok_case01"], "kimi": ["cap_text_only", "ok_case01"]})
        self.assertEqual(self.run_main("--round", "1"), 0, self.out)
        for name in ("claude", "kimi"):
            e = self.entry(name)
            self.assertEqual((e["state"], e["consumed"], e["final"]), ("final", 1, "delivery_fail"), name)
            self.assertEqual(len(self.calls(name)), 1)
        self.assertIn("记录不完整", load(self.outp("claude", ".call.json"))["calls"][0]["categories"])

    def test_resume_interrupted_first_attempt_gets_retry(self):
        self.setup_round()
        self.set_plan({"claude": ["hang", "ok_case01"]})
        self.kill_shell_during("claude", 1, lambda b: b"init" in b)
        self.assertEqual(self.entry("claude")["state"], "running1")
        self.assertEqual(self.run_main("--resume", "1"), 0, self.out)
        e = self.entry("claude")
        self.assertEqual((e["state"], e["consumed"], e["final"]), ("final", 2, "parse"))
        self.assertTrue(e["calls"][0]["interrupted"])
        self.assertIn("记录不完整", e["calls"][0]["categories"])
        self.assertEqual(len(self.calls("claude")), 2)
        self.assertTrue(all(x["state"] == "final" for x in self.attempts()["codes"].values()))

    def test_resume_with_captured_limit_evidence_no_retry(self):
        self.setup_round()
        self.set_plan({"claude": ["partial_limit_then_hang", "ok_case01"]})
        self.kill_shell_during("claude", 1, lambda b: b"max_tokens" in b)
        self.assertEqual(self.run_main("--resume", "1"), 0, self.out)
        e = self.entry("claude")
        self.assertEqual((e["state"], e["consumed"], e["final"]), ("final", 1, "delivery_fail"))
        self.assertIn("输出上限", load(self.outp("claude", ".call.json"))["calls"][-1]["categories"])
        self.assertEqual(len(self.calls("claude")), 1)

    def test_resume_interrupted_second_attempt_is_unavailable(self):
        self.setup_round()
        self.set_plan({"claude": ["wrong_model", "hang", "ok_case01"]})
        self.kill_shell_during("claude", 2, lambda b: b"init" in b)
        self.assertEqual(self.entry("claude")["state"], "running2")
        self.assertEqual(self.run_main("--resume", "1"), 0, self.out)
        e = self.entry("claude")
        self.assertEqual((e["state"], e["consumed"], e["final"]), ("final", 2, "unavailable"))
        self.assertEqual(len(self.calls("claude")), 2)
        self.assertEqual(self.entry("deepseek")["final"], "parse")


# ------------------------------------------------------------------------------------- stops
class TestStops(Base):
    def test_limit_plus_prompt_mismatch_stops_round(self):
        self.setup_round()
        self.set_plan({"claude": ["max_tokens"]})
        with self.tamper("claude", {1}):
            self.assertEqual(self.run_main("--round", "1"), 3, self.out)
        e = self.entry("claude")
        self.assertEqual((e["state"], e["final"]), ("final", "delivery_fail"))
        self.assertEqual(len(self.calls()), 1)
        for name in ("kimi", "deepseek"):
            self.assertEqual((self.entry(name)["state"], self.entry(name)["consumed"]), ("pending", 0))
        (rec,) = self.stop_records()
        self.assertEqual((rec["side"], rec["code"]), ("call", self.code["claude"]))
        self.assertIn(f"STOP {rec['stop_id']}", self.out)

    def test_prompt_mismatch_without_limit_keeps_retry_credit(self):
        self.setup_round()
        with self.tamper("claude", {1}):
            self.assertEqual(self.run_main("--round", "1"), 3, self.out)
        e = self.entry("claude")
        self.assertEqual((e["state"], e["consumed"]), ("await_retry", 1))
        self.assertIn("题目字节不符", e["calls"][0]["categories"])
        self.assertEqual(len(self.stop_records()), 1)

    def test_second_call_prompt_mismatch_is_final(self):
        self.setup_round()
        self.set_plan({"claude": ["wrong_model", "ok_case01"]})
        with self.tamper("claude", {2}):
            self.assertEqual(self.run_main("--round", "1"), 3, self.out)
        e = self.entry("claude")
        self.assertEqual((e["state"], e["consumed"], e["final"]), ("final", 2, "unavailable"))
        (rec,) = self.stop_records()
        self.clear_stop(rec)
        self.assertEqual(self.run_main("--resume", "1"), 0, self.out)
        self.assertEqual(len(self.calls("claude")), 2)
        self.assertEqual(self.entry("claude")["consumed"], 2)
        for name in ("kimi", "deepseek"):
            self.assertEqual(self.entry(name)["final"], "parse")

    def test_resume_refused_while_stopped(self):
        self.setup_round()
        with self.tamper("claude", {1}):
            self.assertEqual(self.run_main("--round", "1"), 3)
        n = len(self.calls())
        self.assertEqual(self.run_main("--resume", "1"), 1)
        self.assertIn("STOPPED", self.out)
        self.assertEqual(len(self.calls()), n)

    def test_resume_after_cleared_continues(self):
        self.setup_round()
        with self.tamper("claude", {1}):
            self.assertEqual(self.run_main("--round", "1"), 3)
        self.clear_stop(self.stop_records()[0])
        self.assertEqual(self.run_main("--resume", "1"), 0, self.out)
        e = self.entry("claude")
        self.assertEqual((e["state"], e["consumed"], e["final"]), ("final", 2, "parse"))
        self.assertTrue(all(x["state"] == "final" for x in self.attempts()["codes"].values()))

    def test_old_clearance_does_not_clear_second_stop(self):
        self.setup_round()
        with self.tamper("claude", {1}):
            self.assertEqual(self.run_main("--round", "1"), 3)
        first = self.stop_records()[0]
        self.clear_stop(first)
        with self.tamper("claude", {1}):                              # first read of this process = call 2
            self.assertEqual(self.run_main("--resume", "1"), 3, self.out)
        self.assertEqual(len(self.stop_records()), 2)
        n = len(self.calls())
        self.assertEqual(self.run_main("--resume", "1"), 1)
        self.assertIn("STOPPED", self.out)
        self.assertNotIn(first["stop_id"], self.out)
        self.assertEqual(len(self.calls()), n)

    def test_eval_side_stop_blocks_resume(self):
        self.setup_round()
        self.set_plan({"claude": ["wrong_model", "wrong_model"]})
        with mock.patch.object(run_revise, "call_code", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.run_main("--round", "1")
        stops.raise_stop(1, "eval", "评估侧停止", None, revise=self.revise)
        self.assertEqual(self.run_main("--resume", "1"), 1)
        self.assertIn("STOPPED", self.out)
        self.assertIn("side eval", self.out)
        self.assertEqual(self.calls(), [])

    def test_private_in_rtl_stops(self):
        self.setup_round()
        self.set_plan({"claude": ["private_in_rtl"]})
        self.assertEqual(self.run_main("--round", "1"), 4, self.out)
        e = self.entry("claude")
        self.assertEqual((e["state"], e["final"]), ("final", "parse"))
        rtl = os.path.join(self.case, "rtl", f"dot4sat_{self.code['claude']}.v")
        self.assertIn(fake_claude_b.PRIVATE_DIR.encode(), rp.read_bytes(rtl))   # candidate bytes not redacted
        (rec,) = self.stop_records()
        self.assertEqual(rec["reason"], run_revise.REASON_PRIVATE)
        self.assertEqual(self.entry("kimi")["state"], "pending")
        self.assertEqual(self.run_main("--resume", "1"), 1)
        self.assertIn("STOPPED", self.out)
        self.assertEqual(len(self.calls()), 1)


# ------------------------------------------------------------------------------------- recovery
class TestRecovery(Base):
    def craft_running(self, name, pid, start, jsonl=b""):
        att = run_revise.new_attempts(1, sorted(self.code.values()))
        att["codes"][self.code[name]].update(state="running1", consumed=1)
        write(os.path.join(self.revise, "outputs", "r1", "attempts.json"), json.dumps(att))
        write(self.raw(name, "call1.proc.json"),
              json.dumps({"root_pid": pid, "root_start": start, "registry": [[pid, start]], "isolation": "job",
                          "started_at": "2026-10-20T10:00:00+08:00"}))
        write(self.raw(name, "call1.jsonl"), jsonl)
        write(self.raw(name, "call1.meta.json"), json.dumps({"n": 1, "prompt_ok": True, "completed": False}))

    def test_resume_kills_surviving_cli_first(self):
        self.setup_round()
        self.set_plan({"claude": ["hang", "ok_case01"]})
        cli = subprocess.Popen([sys.executable, "-B", FAKE, "-p", "--model", MODEL_ID["claude"], "--system-prompt",
                                "x"], env=self.env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL)
        self.addCleanup(cli.stdout.close)
        self.addCleanup(lambda: cli.poll() is None and (cli.kill(), cli.wait()))
        cli.stdin.close()
        first = cli.stdout.readline()
        self.assertIn(b"init", first)
        start = limits._start_time(cli.pid)
        self.craft_running("claude", cli.pid, start, first)
        self.assertEqual(self.run_main("--resume", "1"), 0, self.out)
        self.assertIn("RESUME: old call processes cleaned up", self.out)
        self.assertFalse(alive(cli.pid))
        e = self.entry("claude")
        self.assertEqual((e["state"], e["consumed"], e["final"]), ("final", 2, "parse"))
        self.assertTrue(e["calls"][0]["interrupted"])
        second = [c for c in self.calls("claude") if c["pid"] != cli.pid][-1]
        self.assertNotEqual(second["pid"], cli.pid)

    def test_resume_unconfirmed_raises_stop(self):
        self.setup_round()
        gone = subprocess.Popen([sys.executable, "-B", "-c", "pass"])
        gone.wait()
        self.craft_running("claude", gone.pid, "1")
        with mock.patch.object(limits, "still_alive", return_value=([], True)):
            self.assertEqual(self.run_main("--resume", "1"), 3, self.out)
        (rec,) = self.stop_records()
        self.assertEqual(rec["reason"], run_revise.REASON_RESUME)
        self.assertEqual(self.entry("claude")["state"], "running1")
        self.assertEqual(self.calls(), [])

    def test_consumed_never_exceeds_two(self):
        self.setup_round()
        self.set_plan({n: ["wrong_model"] for n, _ in MODELS})
        self.assertEqual(self.run_main("--round", "1"), 0, self.out)
        self.assertTrue(all(e["consumed"] == 2 for e in self.attempts()["codes"].values()))
        self.assertEqual(len(self.calls()), 6)
        # a record claiming a third call is due is refused, nothing is called
        att = self.attempts()
        att["codes"][self.code["claude"]].update(state="await_retry", final=None)
        write(os.path.join(self.revise, "outputs", "r1", "attempts.json"), json.dumps(att))
        self.assertEqual(self.run_main("--resume", "1"), 1)
        self.assertIn("ATTEMPTS FAIL", self.out)
        self.assertEqual(len(self.calls()), 6)

    def test_concurrent_run_locked(self):
        self.setup_round()
        with stops.round_lock(1, "call", revise=self.revise):
            self.assertEqual(self.run_main("--round", "1"), 1)
            self.assertIn("LOCKED", self.out)
        self.assertEqual(self.calls(), [])


# ------------------------------------------------------------------------------------- bytes and metadata
class TestBytes(Base):
    def test_candidate_bytes_from_raw_answer(self):
        self.setup_round()
        self.set_plan({"claude": ["private_in_rtl"]})
        self.assertEqual(self.run_main("--round", "1"), 4, self.out)
        raw = fake_claude_b.PRIVATE_ANSWER
        block_raw = raw.split("```verilog\r\n", 1)[1].split("```", 1)[0]
        block_lf = block_raw.replace("\r\n", "\n").encode("utf-8")
        rtl = os.path.join(self.case, "rtl", f"dot4sat_{self.code['claude']}.v")
        self.assertEqual(rp.read_bytes(rtl), block_lf)
        parsed = load(self.outp("claude", ".parsed.json"))
        self.assertEqual(parsed["rtl_sha_raw"], sha(block_raw.encode("utf-8")))
        self.assertEqual(parsed["rtl_sha_lf"], sha(block_lf))
        public = rp.read_bytes(self.outp("claude", ".md")).decode("utf-8")
        self.assertIn(run_revise.HIDDEN, public)
        self.assertNotIn(fake_claude_b.PRIVATE_DIR, public)
        self.assertNotIn("\r", public)
        self.assertEqual(rp.read_bytes(self.raw("claude", "answer_raw.md")), raw.encode("utf-8"))
        (rec,) = self.stop_records()
        self.assertEqual(rec["reason"], run_revise.REASON_PRIVATE)

    def test_text_hashes_recorded(self):
        self.setup_round()
        self.assertEqual(self.run_main("--round", "1"), 0, self.out)
        for name in self.code:
            parsed = load(self.outp(name, ".parsed.json"))
            h = parsed["hashes"]
            answer = fake_claude_b.CASE01_ANSWER.encode("utf-8")
            self.assertEqual(h["answer_sha_raw"], sha(answer))
            self.assertEqual(rp.sha256(self.raw(name, "answer_raw.md")), sha(answer))
            self.assertEqual(h["public_sha"], rp.sha256(self.outp(name, ".md")))
            self.assertEqual(h["stdout_sha"], rp.sha256(self.raw(name, "call1.jsonl")))
            self.assertEqual(h["stderr_sha"], rp.sha256(self.raw(name, "call1.err")))
            self.assertEqual(h["system_sha"], rp.sha256(os.path.join(self.revise, "prompts", "system.md")))
            cand = parsed["candidate"]
            self.assertEqual(cand["rtl_sha_lf"], rp.sha256(os.path.join(self.case, cand["rtl_path"])))
            self.assertEqual(cand["cfg_sha"], rp.sha256(os.path.join(self.case, cand["cfg_path"])))
            self.assertEqual(parsed["status"], "ok")
            self.assertNotIn("rtl", parsed)
            for key in ("trigger_lines", "trigger_texts", "predictions", "failure_conditions", "declared_L"):
                self.assertIn(key, parsed)
        with open(os.path.join(self.revise, "predictions", "r1_extracted.jsonl"), encoding="utf-8") as f:
            rows = [json.loads(ln) for ln in f]
        self.assertEqual(sorted({r["code"] for r in rows}), sorted(self.code.values()))

    def test_generated_metadata_has_no_model_names(self):
        self.setup_round()
        self.set_plan({"claude": ["wrong_model", "ok_case01"], "kimi": ["max_tokens"]})
        with self.tamper("deepseek", {1}):
            self.assertEqual(self.run_main("--round", "1"), 3, self.out)
        out = os.path.join(self.revise, "outputs", "r1")
        files = [os.path.join(out, n) for n in os.listdir(out)
                 if n in ("codes.txt", "attempts.json", "status.md") or n.endswith((".call.json", ".parsed.json"))]
        sd = os.path.join(self.revise, "stops", "r1")
        files += [os.path.join(sd, n) for n in os.listdir(sd) if n.endswith(".json")]
        self.assertGreaterEqual(len([f for f in files if f.endswith(".call.json")]), 3)
        self.assertTrue(any(f.endswith(".parsed.json") for f in files))
        for f in files:
            text = rp.read_bytes(f).decode("utf-8").lower()
            for word in ("claude", "kimi", "deepseek", "opus", "k3[", "v4-pro"):
                self.assertNotIn(word, text, f"{word} in {f}")

    def test_utf8_without_pythonioencoding(self):
        env = {k: v for k, v in self.env.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
        r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "run_revise.py"), "--commit-codes", "1",
                            "--dry-run"] + self.flags(), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("请提交这两个文件", r.stdout.decode("utf-8"))
        self.assertFalse(os.path.exists(os.path.join(self.revise, "outputs", "r1", "codes.txt")))


if __name__ == "__main__":
    unittest.main()
