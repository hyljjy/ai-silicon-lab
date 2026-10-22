"""Tests for build_package and build_prompt (materials package and prompts; CASE-01 stage B, Task 9, protocol
section 5). Run per module, never with discover. Packages, prompts and smoke prompts are written only into temporary
directories under tasks/CASE-01/runs/ (temporary git repositories and sealed directories for the mapping); the real
revise/package/, revise/prompts/r1|r2/ and runs/revise-smoke/ are never written. The templates are the real
revise/prompts/ and revise/package_src/ files (read only)."""
import contextlib
import io
import json
import os
import re
import shutil
import tempfile
import unittest
from unittest import mock

import build_package as bp
import build_prompt as bpr
import extract
import feedback
import mapping
import revpaths as rp
from test_stops import git

RUNS = os.path.join(rp.CASE, "runs")
MODELS = ["claude", "kimi", "deepseek"]
STAGE_A_ROUND2 = os.path.join(rp.CASE, "diag", "outputs", "round2")
TEMPLATE_FILES = [os.path.join(rp.REVISE, "package_src", "constraints.md")] + [
    os.path.join(rp.PROMPTS, n) for n in ("system.md", "round1_template.md", "round2_template.md",
                                          "smoke_rehearsal_template.md", "smoke_system.md", "smoke_user.md",
                                          "cap_probe_user.md")]
# words naming a design approach or recommending an order: none may appear in the templates or constraints.md
DIRECTION_WORDS = ("乘积后寄存", "输入寄存", "输出寄存", "建议先", "建议", "推荐", "可以考虑", "不妨", "流水", "插一级",
                   "插入寄存器", "打一拍", "寄存一级", "重定时", "retim", "pipelin", "进位保留", "carry-save",
                   "carry save", "CSA", "Wallace", "Booth", "加法树", "树形", "压缩树", "提前饱和", "拆分")
NEVER_WORDS = ("signoff", "sign-off", "签核")
HEADER = "| " + " | ".join(extract.PREDICTION_COLUMNS) + " |"


def wbytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def quiet(fn, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*a, **kw)


def text_of(path):
    return rp.read_bytes(path).decode("utf-8")


class Tmp(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="build_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        # a slip in a test must not reach the real package, sealed directory or smoke directory
        for obj, attr, sub in ((mapping, "SEALED", "sealed-guard"), (bpr, "SMOKE_PROMPTS", "smoke-guard")):
            p = mock.patch.object(obj, attr, os.path.join(self.tmp.name, sub))
            p.start()
            self.addCleanup(p.stop)
        self.pkg = os.path.join(self.tmp.name, "package")
        self.assertEqual(quiet(bp.main, [], package=self.pkg), 0)


class Repo(Tmp):
    """A temporary git repository with tasks/CASE-01/revise/ and committed round-1 (and round-2) codes."""
    def setUp(self):
        super().setUp()
        self.repo = os.path.join(self.tmp.name, "repo")
        self.sealed = os.path.join(self.tmp.name, "sealed")
        os.makedirs(self.repo)
        git(self.repo, "init", "-q", ".")
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "core.autocrlf", "false")
        self.revise = os.path.join(self.repo, "tasks", "CASE-01", "revise")
        wbytes(os.path.join(self.repo, "README"), b"temp\n")
        self.commit(os.path.join(self.repo, "README"))
        self.kw = {"revise": self.revise, "sealed": self.sealed}

    def commit(self, *paths):
        git(self.repo, "add", "--", *paths)
        git(self.repo, "commit", "-q", "-m", "c")

    def codes(self, rnd, prev=None):
        codes = mapping.commit_codes(rnd, MODELS, prev, **self.kw)
        out = os.path.join(self.revise, "outputs")
        self.commit(os.path.join(out, f"r{rnd}", "codes.txt"), os.path.join(out, f"mapping_r{rnd}.sha256"))
        return dict(zip(MODELS, codes))


class TestPackage(Tmp):
    def test_contract_excerpt_from_pinned_commit(self):
        commit, sha = bp.contract_source()
        self.assertRegex(commit, r"^[0-9a-f]{40}$")
        self.assertTrue(commit.startswith("90777e7"), commit)
        spec = bp.spec_at(commit)
        self.assertEqual(rp.sha256_bytes(spec), sha)
        ex = text_of(os.path.join(self.pkg, "contract_excerpt.md"))
        self.assertTrue(ex.startswith("## 1. 接口\n"))
        self.assertIn("| `out_data` | 出 | 32 | 32 位二进制补码 |", ex)          # section 1 port table
        self.assertIn("## 2. 时序与交易规则", ex)
        self.assertIn("### 2.5 L 的配置", ex)
        self.assertIn("### 3.1 参考函数", ex)                                  # section 3.1 reference function
        self.assertIn("y = clamp(s, −2^31, 2^31−1)", ex)
        for bad in ("## 0. ", "## 3. ", "### 3.2", "## 4. ", "### 4.2"):
            self.assertNotIn(bad, ex)
        # verbatim: exactly the spec lines of sections 1-2 and 3.1
        lines = spec.decode("utf-8").splitlines(keepends=True)
        i1 = next(i for i, ln in enumerate(lines) if ln.startswith("## 1. "))
        i3 = next(i for i, ln in enumerate(lines) if ln.startswith("## 3. "))
        j1 = next(i for i, ln in enumerate(lines) if ln.startswith("### 3.1 "))
        j2 = next(i for i, ln in enumerate(lines) if ln.startswith("### 3.2 "))
        want = "".join(lines[i1:i3]).rstrip("\n") + "\n\n" + "".join(lines[j1:j2]).rstrip("\n") + "\n"
        self.assertEqual(ex, want)

    def test_excerpt_read_from_commit_not_working_tree(self):
        repo = os.path.join(self.tmp.name, "specrepo")
        os.makedirs(repo)
        git(repo, "init", "-q", ".")
        git(repo, "config", "user.name", "test")
        git(repo, "config", "user.email", "test@example.invalid")
        git(repo, "config", "core.autocrlf", "false")
        spec = os.path.join(repo, "spec.md")
        v1 = "# c\n\n## 0. x\n\n## 1. 接口\n\nA\n\n## 2. 时序\n\nB\n\n## 3. 功能\n\n### 3.1 参考函数\n\nC\n\n### 3.2 x\n"
        wbytes(spec, v1.encode("utf-8"))
        git(repo, "add", "spec.md")
        git(repo, "commit", "-q", "-m", "v1")
        commit = git(repo, "rev-parse", "HEAD").decode().strip()
        wbytes(spec, v1.replace("A\n", "CHANGED\n").encode("utf-8"))       # working tree differs from the commit
        src = os.path.join(self.tmp.name, "contract_source.txt")
        wbytes(src, f"commit {commit}\nspec_sha256 {rp.sha256_bytes(v1.encode('utf-8'))}\n".encode())
        files, sources = bp.build(source=src, case=repo)
        self.assertEqual(files["contract_excerpt.md"].decode("utf-8"),
                         "## 1. 接口\n\nA\n\n## 2. 时序\n\nB\n\n### 3.1 参考函数\n\nC\n")
        self.assertIn(commit, dict((n, s) for n, s, _ in sources)["contract_excerpt.md"])

    def test_package_written_and_checked(self):
        names = sorted(os.listdir(self.pkg))
        self.assertEqual(names, sorted(bp.ORDER + bp.LISTINGS))
        for n in bp.STAGE_A:
            self.assertEqual(rp.read_bytes(os.path.join(self.pkg, n)),
                             rp.read_bytes(os.path.join(rp.CASE, "diag", "package", n)))
        self.assertEqual(rp.read_bytes(os.path.join(self.pkg, "constraints.md")),
                         rp.read_bytes(os.path.join(rp.REVISE, "package_src", "constraints.md")))
        sums = text_of(os.path.join(self.pkg, "SHA256SUMS")).splitlines()
        self.assertEqual([ln.split("  ")[1] for ln in sums], list(bp.ORDER))
        for ln in sums:
            h, n = ln.split("  ")
            self.assertEqual(rp.sha256(os.path.join(self.pkg, n)), h)
        src = text_of(os.path.join(self.pkg, "SOURCES.tsv")).splitlines()
        self.assertEqual([ln.split("\t")[0] for ln in src[1:]], list(bp.ORDER))
        self.assertEqual(quiet(bp.main, ["--check"], package=self.pkg), 0)
        self.assertEqual(quiet(bp.main, [], package=self.pkg), 0)         # same bytes: accepted, nothing rewritten

    def test_package_refuses_changed_source(self):
        # a stage A file that differs from diag/package/SHA256SUMS
        diag = os.path.join(self.tmp.name, "diag_package")
        shutil.copytree(os.path.join(rp.CASE, "diag", "package"), diag)
        with open(os.path.join(diag, "values.txt"), "ab") as f:
            f.write(b"x\n")
        with self.assertRaises(bp.PackageError):
            bp.build(diag_package=diag)
        # a missing stage A file in SHA256SUMS
        shutil.rmtree(diag)
        shutil.copytree(os.path.join(rp.CASE, "diag", "package"), diag)
        sums = os.path.join(diag, "SHA256SUMS")
        wbytes(sums, b"".join(ln + b"\n" for ln in rp.read_bytes(sums).splitlines()[:-1]))
        with self.assertRaises(bp.PackageError):
            bp.build(diag_package=diag)
        # spec bytes whose sha256 is not the recorded one
        commit, _ = bp.contract_source()
        src = os.path.join(self.tmp.name, "contract_source.txt")
        wbytes(src, f"commit {commit}\nspec_sha256 {'0' * 64}\n".encode())
        with self.assertRaises(bp.PackageError):
            bp.build(source=src)
        wbytes(src, f"commit {commit}\n".encode())
        with self.assertRaises(bp.PackageError):
            bp.build(source=src)
        # changed constraints source: the existing package file is not rewritten, --check reports the difference
        srcdir = os.path.join(self.tmp.name, "package_src")
        shutil.copytree(os.path.join(rp.REVISE, "package_src"), srcdir)
        with open(os.path.join(srcdir, "constraints.md"), "ab") as f:
            f.write("补一行\n".encode("utf-8"))
        before = rp.read_bytes(os.path.join(self.pkg, "constraints.md"))
        self.assertEqual(quiet(bp.main, [], package=self.pkg, package_src=srcdir), 1)
        self.assertEqual(rp.read_bytes(os.path.join(self.pkg, "constraints.md")), before)
        self.assertEqual(quiet(bp.main, ["--check"], package=self.pkg, package_src=srcdir), 1)
        # an edited package file is reported by --check
        with open(os.path.join(self.pkg, "dot4sat.v"), "ab") as f:
            f.write(b"\n")
        self.assertEqual(quiet(bp.main, ["--check"], package=self.pkg), 1)


class TestRound1(Repo):
    def test_round1_differs_only_in_own_attachment(self):
        codes = self.codes(1)
        texts, atts = {}, {}
        for m, c in codes.items():
            texts[m] = bpr.round1_bytes(c, package=self.pkg, **self.kw).decode("utf-8")
            data = rp.read_bytes(os.path.join(STAGE_A_ROUND2, bpr.ATTACHMENT[m] + ".md"))
            atts[m] = bpr.numbered(bpr.ATTACHMENT_NAME, data)
        stripped = set()
        for m in MODELS:
            self.assertEqual(texts[m].count(atts[m]), 1, m)
            for n in MODELS:
                if n != m:
                    self.assertNotIn(atts[n], texts[m])
            stripped.add(texts[m].replace(atts[m], "<ATTACHMENT>"))
        self.assertEqual(len(stripped), 1)
        common = stripped.pop()
        heads = [ln for ln in common.splitlines() if ln.startswith("=== 文件：")]
        self.assertEqual([h.split("：")[1].split("（")[0] for h in heads], list(bp.ORDER))
        for n in bp.ORDER:                                      # every package file inserted with line numbers
            self.assertIn(bpr.numbered(n, rp.read_bytes(os.path.join(self.pkg, n))), common)
        self.assertEqual(texts["claude"], bpr.round1_for_model("claude", package=self.pkg).decode("utf-8"))

    def test_round1_written_by_code(self):
        codes = self.codes(1)
        for m, c in codes.items():
            self.assertEqual(quiet(bpr.main, ["round1", c], package=self.pkg, **self.kw), 0)
            p = os.path.join(self.revise, "prompts", "r1", f"{c}_prompt.md")
            self.assertEqual(rp.read_bytes(p), bpr.round1_bytes(c, package=self.pkg, **self.kw))
            self.assertEqual(quiet(bpr.main, ["round1", c, "--check"], package=self.pkg, **self.kw), 0)
            self.assertEqual(quiet(bpr.main, ["round1", c], package=self.pkg, **self.kw), 0)   # same bytes again
        self.assertEqual(sorted(os.listdir(os.path.join(self.revise, "prompts", "r1"))),
                         sorted(f"{c}_prompt.md" for c in codes.values()))
        c = codes["kimi"]
        p = os.path.join(self.revise, "prompts", "r1", f"{c}_prompt.md")
        with open(p, "ab") as f:
            f.write(b"\n")
        self.assertEqual(quiet(bpr.main, ["round1", c, "--check"], package=self.pkg, **self.kw), 1)
        self.assertEqual(quiet(bpr.main, ["round1", c], package=self.pkg, **self.kw), 1)       # never rewritten
        self.assertNotEqual(quiet(bpr.main, ["round1", "cand_zzzz"], package=self.pkg, **self.kw), 0)
        self.assertEqual(quiet(bpr.main, ["round1"], package=self.pkg, **self.kw), 2)

    def test_round1_refuses_uncommitted_mapping_and_changed_package(self):
        codes = mapping.commit_codes(1, MODELS, None, **self.kw)
        with self.assertRaises(mapping.MappingError):
            bpr.round1_bytes(codes[0], package=self.pkg, **self.kw)
        out = os.path.join(self.revise, "outputs")
        self.commit(os.path.join(out, "r1", "codes.txt"), os.path.join(out, "mapping_r1.sha256"))
        bpr.round1_bytes(codes[0], package=self.pkg, **self.kw)
        with open(os.path.join(self.pkg, "values.txt"), "ab") as f:
            f.write(b"x\n")
        with self.assertRaises(bpr.PromptError):
            bpr.round1_bytes(codes[0], package=self.pkg, **self.kw)


class TestRound2(Repo):
    def setUp(self):
        super().setUp()
        self.c1 = self.codes(1)
        self.c2 = self.codes(2, prev=self.c1)
        self.endings = feedback.load_endings()
        self.r1 = {}
        for m, c in self.c1.items():
            quiet(bpr.main, ["round1", c], package=self.pkg, **self.kw)
            p = os.path.join(self.revise, "prompts", "r1", f"{c}_prompt.md")
            self.commit(p)
            self.r1[m] = rp.read_bytes(p)

    def answer(self, code, text):
        p = os.path.join(self.revise, "outputs", "r1", f"{code}.md")
        wbytes(p, text.encode("utf-8"))
        self.commit(p)

    def state(self, code, state):
        wbytes(os.path.join(self.revise, "results", "r1", code, "status.json"),
               json.dumps({"code": code, "rnd": 1, "state": state}).encode())

    def fb(self, code, data):
        wbytes(os.path.join(self.revise, "prompts", "r2", f"{code}_feedback.md"), data)

    def test_round2_prompt_composition(self):
        rules = bpr.round2_sections()["rules"]
        # answered: round-1 prompt + public answer + rules + feedback (which already ends with the ending)
        c = self.c1["claude"]
        self.answer(c, "## 修改假设\n\n答复正文。\n")
        self.state(c, "eligible_no_gain")
        fbk = ("GRADE OK\n\n- rtl_sim：pass\n\n" + self.endings["evaluated_valid"] + "\n").encode("utf-8")
        self.fb(c, fbk)
        r2, data = bpr.round2_bytes(c, **self.kw)
        self.assertEqual(r2, self.c2["claude"])
        t = data.decode("utf-8")
        self.assertTrue(data.startswith(self.r1["claude"].rstrip(b"\n") + b"\n"))
        self.assertTrue(data.endswith(fbk))
        self.assertEqual(t.count(self.r1["claude"].decode("utf-8").rstrip("\n")), 1)
        self.assertIn("<<<第 1 轮答复开始>>>\n## 修改假设\n\n答复正文。\n<<<第 1 轮答复结束>>>", t)
        self.assertEqual(t.count(rules), 1)
        self.assertLess(t.index(rules), t.index("GRADE OK"))
        self.assertEqual(t.count(self.endings["evaluated_valid"]), 1)         # the ending only once, at the end
        for other in ("evaluated_no_analysis", "not_evaluated"):
            self.assertNotIn(self.endings[other], t)
        self.assertEqual(quiet(bpr.main, ["round2", c], **self.kw), 0)
        p = os.path.join(self.revise, "prompts", "r2", f"{r2}_prompt.md")
        self.assertEqual(rp.read_bytes(p), data)
        self.assertEqual(quiet(bpr.main, ["round2", c, "--check"], **self.kw), 0)

        # unavailable: the same order without the answer: round-1 prompt -> rules -> feedback -> ending (the
        # feedback no longer carries the round-1 prompt; it appears once, first)
        u = self.c1["kimi"]
        self.state(u, "unavailable")
        fbu = ("第 1 轮没有收到你的有效答复（原因类别：第 1 次调用：记录不完整）。\n\n" + self.endings["not_evaluated"] +
               "\n").encode("utf-8")
        self.fb(u, fbu)
        r2u, du = bpr.round2_bytes(u, **self.kw)
        self.assertEqual(r2u, self.c2["kimi"])
        tu = du.decode("utf-8")
        self.assertEqual(du, self.r1["kimi"].rstrip(b"\n") + b"\n\n" + (rules + "\n\n以下是你第 1 轮的结果。\n\n")
                         .encode("utf-8") + fbu)
        self.assertEqual(tu.count(self.r1["kimi"].decode("utf-8").rstrip("\n")), 1)
        self.assertEqual(tu.count(self.endings["not_evaluated"]), 1)
        self.assertNotIn("<<<第 1 轮答复开始>>>", tu)

    def test_round2_order_every_state(self):
        # Every round-1 state: round-1 prompt (exactly once, first) -> own answer (all but unavailable) -> rules ->
        # feedback -> its fixed ending (last).
        rules = bpr.round2_sections()["rules"]
        ending_of = {"unavailable": "not_evaluated", "delivery_fail": "not_evaluated", "gate_reject": "not_evaluated",
                     "infra_fail": "evaluated_no_analysis", "grade_fail": "evaluated_no_analysis",
                     "ineligible": "evaluated_valid", "eligible_no_gain": "evaluated_valid",
                     "eligible_gain": "evaluated_valid"}
        self.assertEqual(set(ending_of), set(bpr.ROUND1_STATES))
        for m in MODELS:
            c = self.c1[m]
            p = os.path.join(self.revise, "outputs", "r1", f"{c}.md")
            wbytes(p, f"## 修改假设\n\n{m} 的答复。\n".encode("utf-8"))
            self.commit(p)
        for i, (state, ending) in enumerate(sorted(ending_of.items())):
            with self.subTest(state=state):
                m = MODELS[i % 3]
                c = self.c1[m]
                self.state(c, state)
                fbk = (f"反馈正文 {state}\n\n" + self.endings[ending] + "\n").encode("utf-8")
                wbytes(os.path.join(self.revise, "prompts", "r2", f"{c}_feedback.md"), fbk)
                t = bpr.round2_bytes(c, **self.kw)[1].decode("utf-8")
                r1 = self.r1[m].decode("utf-8").rstrip("\n")
                self.assertTrue(t.startswith(r1 + "\n\n"))
                self.assertEqual(t.count(r1), 1)
                self.assertTrue(t.endswith(fbk.decode("utf-8")))
                self.assertTrue(t.rstrip("\n").endswith(self.endings[ending]))
                self.assertEqual(t.count(rules), 1)
                pos = [t.index(r1), t.index(rules), t.index("以下是你第 1 轮的结果。"), t.index(f"反馈正文 {state}")]
                if state != "unavailable":
                    pos.insert(1, t.index(f"{m} 的答复。"))
                else:
                    self.assertNotIn("<<<第 1 轮答复开始>>>", t)
                self.assertEqual(pos, sorted(pos))

    def test_round2_refusals(self):
        c = self.c1["deepseek"]
        self.state(c, "grade_fail")
        with self.assertRaises(bpr.PromptError):                          # no feedback yet
            bpr.round2_bytes(c, **self.kw)
        self.fb(c, ("GRADE FAIL\n\n" + self.endings["evaluated_no_analysis"] + "\n").encode("utf-8"))
        with self.assertRaises(bpr.PromptError):                          # public answer missing
            bpr.round2_bytes(c, **self.kw)
        p = os.path.join(self.revise, "outputs", "r1", f"{c}.md")
        wbytes(p, b"answer\n")
        with self.assertRaises(bpr.PromptError):                          # public answer not committed
            bpr.round2_bytes(c, **self.kw)
        self.commit(p)
        bpr.round2_bytes(c, **self.kw)
        prompt = os.path.join(self.revise, "prompts", "r1", f"{c}_prompt.md")
        with open(prompt, "ab") as f:                                     # round-1 prompt differs from HEAD
            f.write(b"\n")
        with self.assertRaises(bpr.PromptError):
            bpr.round2_bytes(c, **self.kw)
        # a feedback that still carries the round-1 prompt (the old unavailable form) is refused: the round-1
        # prompt must appear exactly once
        u = self.c1["kimi"]
        self.state(u, "unavailable")
        self.fb(u, ("x\n\n" + self.endings["not_evaluated"] + "\n\n").encode("utf-8") + self.r1["kimi"])
        with self.assertRaisesRegex(bpr.PromptError, "round-1 prompt"):
            bpr.round2_bytes(u, **self.kw)
        self.fb(u, ("x\n\n" + self.endings["not_evaluated"] + "\n").encode("utf-8"))
        bpr.round2_bytes(u, **self.kw)
        with self.assertRaises(mapping.MappingError):                     # not a round-1 code
            bpr.round2_bytes(self.c2["kimi"], **self.kw)

    def test_round2_refuses_unknown_state(self):
        c = self.c1["claude"]
        p = os.path.join(self.revise, "outputs", "r1", f"{c}.md")
        wbytes(p, b"answer\n")
        self.commit(p)
        self.fb(c, ("GRADE OK\n\n" + self.endings["evaluated_valid"] + "\n").encode("utf-8"))
        self.state(c, "eligible_gain")
        bpr.round2_bytes(c, **self.kw)
        for bad in ("declined", "await_retry", None, "GRADE OK"):
            self.state(c, bad)
            with self.assertRaises(bpr.PromptError, msg=repr(bad)):
                bpr.round2_bytes(c, **self.kw)
        wbytes(os.path.join(self.revise, "results", "r1", c, "status.json"), json.dumps({"code": c}).encode())
        with self.assertRaises(bpr.PromptError):                          # no state at all
            bpr.round2_bytes(c, **self.kw)
        self.assertEqual(quiet(bpr.main, ["round2", c], **self.kw), 1)


class TestTemplates(Repo):
    def test_no_placeholders_left(self):
        known = set(bpr.PLACEHOLDERS)
        want = {"round1_template.md": {"材料", "附件"}, "smoke_rehearsal_template.md": {"题目前部"},
                "round2_template.md": {"第1轮题目", "第1轮答复", "第2轮规则", "反馈"}}     # per section below
        for path in TEMPLATE_FILES:
            t = text_of(path)
            names = set(re.findall(r"\{\{([^{}]*)\}\}", t))
            self.assertEqual(names, want.get(os.path.basename(path), set()), path)
            self.assertNotIn("{{", re.sub(r"\{\{[^{}]*\}\}", "", t), path)
            self.assertNotIn("}}", re.sub(r"\{\{[^{}]*\}\}", "", t), path)
        sections = bpr.round2_sections()
        self.assertEqual(set(sections), {"answered", "unavailable", "rules"})
        for key, names in (("answered", {"第1轮题目", "第1轮答复", "第2轮规则", "反馈"}),
                           ("unavailable", {"第1轮题目", "第2轮规则", "反馈"}), ("rules", set())):
            self.assertEqual(set(re.findall(r"\{\{([^{}]*)\}\}", sections[key])), names, key)
        self.assertTrue(set().union(*want.values(), {"第1轮题目", "第1轮答复", "第2轮规则", "反馈"}) <= known)

        # every generated prompt: no placeholder of ours is left
        left = re.compile(r"\{\{(?:" + "|".join(map(re.escape, known)) + r")\}\}")
        c1 = self.codes(1)
        c2 = self.codes(2, prev=c1)
        outs = []
        for m, c in c1.items():
            quiet(bpr.main, ["round1", c], package=self.pkg, **self.kw)
            p = os.path.join(self.revise, "prompts", "r1", f"{c}_prompt.md")
            self.commit(p)
            outs.append(rp.read_bytes(p))
            outs.append(bpr.rehearsal_bytes(m, package=self.pkg))
        a, u = c1["claude"], c1["kimi"]
        wbytes(os.path.join(self.revise, "outputs", "r1", f"{a}.md"), b"answer {{x}}\n")
        self.commit(os.path.join(self.revise, "outputs", "r1", f"{a}.md"))
        for code, state, data in ((a, "grade_fail", b"GRADE FAIL\n"), (u, "unavailable", b"x\n")):
            wbytes(os.path.join(self.revise, "results", "r1", code, "status.json"),
                   json.dumps({"state": state}).encode())
            wbytes(os.path.join(self.revise, "prompts", "r2", f"{code}_feedback.md"), data)
            outs.append(bpr.round2_bytes(code, **self.kw)[1])
        outs.append(bpr.canary_bytes()[1])
        outs.append(bpr.cap_probe_bytes())
        for data in outs:
            self.assertIsNone(left.search(data.decode("utf-8")))
        self.assertIn("answer {{x}}", outs[-4].decode("utf-8"))           # inserted text is never substituted
        self.assertEqual(len(c2), 3)

    def test_template_shaped_answer_extracts_only_its_failure_conditions(self):
        r1 = text_of(os.path.join(rp.PROMPTS, "round1_template.md"))
        reh = text_of(os.path.join(rp.PROMPTS, "smoke_rehearsal_template.md"))
        task = r1[r1.index("\n" + bpr.TASK_HEADING + "\n"):]
        heads = ["修改假设", "预测表", "代价", "失败条件", "声明行和 RTL"]
        self.assertEqual(re.findall(r"`([^`]+)`", task.split("\n\n")[1])[:5], heads)   # the five headings, in order
        self.assertIn("`## 声明行和 RTL`", task)
        self.assertIn("`## 预测表`", reh)
        self.assertIn("`## 声明行和 RTL`", reh)
        rtl = text_of(os.path.join(rp.CASE, "rtl", "dot4sat.v")).rstrip("\n")
        row = "| P1 | x | L |  |  |  |  |  |  |  |  | 1 | dot4sat.v:1 |"            # RV-02 layout
        row2 = "| P2 | a \\| b | function |  |  |  |  |  |  |  |  | pass | dot4sat.v:2 |"
        delim = "|" + "---|" * len(extract.PREDICTION_COLUMNS)
        body = ["## 修改假设", "", "文字。", "", "## 预测表", "", HEADER, delim, row, row2, "", "## 代价", "", "文字。", "",
                "## 失败条件", "", "- 条件一", "- 条件二", ""]
        tail = ["DECLARED_L = 1", "", "```verilog", rtl, "```", "", "- 说明：这一条不是失败条件。", ""]
        answer = "\n".join(body + ["## 声明行和 RTL", ""] + tail)
        p = extract.parse_answer(answer, 1)
        self.assertEqual(p.status, "ok")
        self.assertEqual(p.declared_L, 1)
        self.assertEqual(len(p.predictions), 2)
        self.assertEqual([(r["id"], r["metric"], r["point"]) for r in p.predictions], [("P1", "L", "1"),
                                                                                     ("P2", "function", "pass")])
        self.assertEqual(p.predictions[1]["action"], "a | b")                       # `\|` is a literal bar
        self.assertEqual([f["text"] for f in p.failure_conditions], ["条件一", "条件二"])
        # control: without the heading the trailing item would be taken as a third failure condition
        loose = extract.parse_answer("\n".join(body + tail), 1)
        self.assertEqual(len(loose.failure_conditions), 3)

    def test_no_direction_words(self):
        for path in TEMPLATE_FILES:
            t = text_of(path)
            for w in DIRECTION_WORDS:
                self.assertNotIn(w.lower(), t.lower(), f"{os.path.basename(path)}: {w}")
            for w in NEVER_WORDS:
                self.assertNotIn(w.lower(), t.lower(), f"{os.path.basename(path)}: {w}")

    def test_required_text_in_templates(self):
        cons = text_of(os.path.join(rp.REVISE, "package_src", "constraints.md"))
        r1 = text_of(os.path.join(rp.PROMPTS, "round1_template.md"))
        rules = bpr.round2_sections()["rules"]
        for t in (cons, r1):
            self.assertIn(HEADER, t.splitlines())
            self.assertIn("比较基准一律相对 F1 基线", t)
            for v in ("`slack`", "`area`", "`L`", "`function`", "`setup`", "`hold`", "`all`", "`global`",
                      "`in2reg`", "`reg2reg`", "`reg2out`", "`absolute`", "`delta`", "改善", "退化", "不变", "未知"):
                self.assertIn(v, t)
        # the header the prompt asks for is exactly what extract.py accepts
        line = next(ln for ln in r1.splitlines() if ln == HEADER)
        self.assertEqual(extract._split_row(line), extract.PREDICTION_COLUMNS)
        for s in ("`预测表`", "`失败条件`", "DECLARED_L = <n>",
                  "如果给出多个代码块，只有第一个 verilog 代码块会被评估；第一个代码块不完整时，不会改用后面的代码块"):
            self.assertIn(s, r1)
        self.assertIn("可以用评估结果直接检查", r1)
        self.assertIn("NO_SUBMISSION", rules)
        self.assertIn("verilog 代码块", rules)
        self.assertNotIn("NO_SUBMISSION", r1)
        for s in ("56729.408", "45383.5264", "hold 只记录，不作判据", "阶段 B 附加提交格式限制", "合同要求",
                  "`@(posedge clk)`", "`localparam`"):
            self.assertIn(s, cons)
        for g in range(1, 9):
            self.assertRegex(cons, rf"\| G{g} \|")
        system = text_of(os.path.join(rp.PROMPTS, "system.md"))
        for s in ("被测试的 RTL 修改助手", "不确定", "文件名:行号"):
            self.assertIn(s, system)

    def test_author_checkpoint1_wording(self):
        # Author checkpoint 1 (2026-10-21, Codex CASE01_BC2 2.3 adopted in full) and RV-02.
        cons = text_of(os.path.join(rp.REVISE, "package_src", "constraints.md"))
        r1 = text_of(os.path.join(rp.PROMPTS, "round1_template.md"))
        reh = text_of(os.path.join(rp.PROMPTS, "smoke_rehearsal_template.md"))
        # removed: the evaluation of the attachment, the results-field list, the dependence on it
        for gone in ("只供参考", "不一定正确", "阶段 A 只做诊断"):
            self.assertNotIn(gone, r1)
        self.assertIn("下面是你自己在阶段 A 第 2 轮的答复，已按行编号。引用时文件名写 `阶段A答复.md`。\n\n{{附件}}", r1)
        for gone in ("评估给出以下结果", "失败条件可以用它们来写", "全局最小 setup slack", "起点、终点", "下一步查询"):
            self.assertNotIn(gone, cons)
        self.assertNotIn("第 8 节", r1)
        self.assertIn("- 尽量写成可以用评估结果直接检查的条件。\n", r1)
        for gone in ("怎样比较", "阈值", "用括号标明先后"):
            self.assertNotIn(gone, r1)
        self.assertIn("- 评估用冻结的流程：RTL 仿真、门级功能仿真、综合、6 个 std 点的 STA。", cons)
        self.assertIn("- 本阶段不能调用工具或查询，也不提供网表。原样材料中关于查询的说明属于阶段 A。\n", cons)
        self.assertTrue(cons.endswith("原样材料中关于查询的说明属于阶段 A。\n"))
        # RV-02: L / function rows, the same sentence in both files
        rv02 = ("每行保留 `id`、`metric`，并填写适用的 `action`、`basis`。`metric` 为 `L` 时，数值和判定字段只填整数 "
                "`point`；为 `function` 时只填 `point` = `pass` 或 `fail`；这两类的 `check`、`corner`、`category`、"
                "`value_kind`、`direction`、`low`、`high`、`unit` 留空。")
        for t in (cons, r1):
            self.assertIn(rv02, t)
            self.assertNotIn("其余字段留空", t)
        self.assertIn("两者都通过为 `pass`，任一失败为 `fail`，其他情况为无结果。", cons)
        # rehearsal: what is done with the delivery
        self.assertIn("这是一次格式演练：交付结果将用于抽取和提交门槛检查，不运行 `grade.py`。", reh)
        self.assertNotIn("只做格式检查", reh)
        # neutral format notes (before the task section, so the rehearsal prompt carries them too)
        head = r1[:r1.index("\n" + bpr.TASK_HEADING + "\n")]
        for note in ("答复中不要先复述一遍题目中的格式模板或示例标题",
                     "表头使用上面的原始列名，不给列名加反引号、加粗或其他装饰。",
                     "每项预测占一行；单元格中如需写字面的竖线，写成 `\\|`。",
                     "每条失败条件写成一个顶层列表项（以 `- ` 开头），不要把独立的条件缩进成上一条的子项。",
                     "保留 `DECLARED_L = <n>` 的精确写法：等号两边各一个空格，等号用 ASCII 字符 `=`。",
                     "代码围栏的语言名写小写的 `verilog`。"):
            self.assertIn(note, head)
        # the five headings stay; `## 声明行和 RTL` still closes the failure-condition list
        for h in ("`修改假设`", "`预测表`", "`代价`", "`失败条件`", "`声明行和 RTL`", "`## 声明行和 RTL`"):
            self.assertIn(h, r1)


class TestSmoke(Tmp):
    def test_rehearsal_replaces_only_the_task(self):
        for m in MODELS:
            full = bpr.round1_for_model(m, package=self.pkg).decode("utf-8")
            reh = bpr.rehearsal_bytes(m, package=self.pkg).decode("utf-8")
            cut = full.index("\n" + bpr.TASK_HEADING + "\n")
            self.assertTrue(reh.startswith(full[:cut].rstrip("\n") + "\n\n"))
            self.assertNotIn(full[cut:].strip("\n"), reh)
            self.assertIn("DECLARED_L = 1", reh[cut:])
            self.assertEqual(full.count("\n" + bpr.TASK_HEADING + "\n"), 1)
        self.assertNotIn("NO_SUBMISSION", reh)

    def test_missing_attachment_is_prompt_fail(self):
        empty = os.path.join(self.tmp.name, "no_round2")
        os.makedirs(empty)
        with mock.patch.object(bpr, "STAGE_A_ROUND2", empty):
            with self.assertRaises(bpr.PromptError):
                bpr.round1_for_model("kimi", package=self.pkg)
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                rc = bpr.main(["smoke-rehearsal", "kimi"], package=self.pkg,
                              smoke_dir=os.path.join(self.tmp.name, "smoke"))
        self.assertEqual(rc, 1)
        self.assertIn("PROMPT FAIL", out.getvalue())
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "smoke")))

    def test_smoke_prompts_written_outside_git(self):
        smoke = os.path.join(self.tmp.name, "smoke")
        for args in (["smoke-canary"], ["cap-probe"], ["smoke-rehearsal", "deepseek"]):
            self.assertEqual(quiet(bpr.main, args, package=self.pkg, smoke_dir=smoke), 0, args)
            self.assertEqual(quiet(bpr.main, args + ["--check"], package=self.pkg, smoke_dir=smoke), 0, args)
        self.assertEqual(sorted(os.listdir(smoke)),
                         ["canary_user.md", "cap_probe_user.md", "rehearsal_deepseek.md"])
        self.assertEqual(rp.read_bytes(os.path.join(smoke, "rehearsal_deepseek.md")),
                         bpr.rehearsal_bytes("deepseek", package=self.pkg))
        system, user = bpr.canary_bytes()
        self.assertEqual(rp.read_bytes(os.path.join(smoke, "canary_user.md")), user)
        sys_word = re.search(r"暗号是：(\S+?)。", system.decode("utf-8")).group(1)
        user_word = re.search(r"暗号是：(\S+?)。", user.decode("utf-8")).group(1)
        self.assertNotEqual(sys_word, user_word)
        self.assertNotIn(sys_word, user.decode("utf-8"))
        self.assertIn("300", bpr.cap_probe_bytes().decode("utf-8"))
        self.assertNotEqual(quiet(bpr.main, ["smoke-rehearsal", "gpt"], package=self.pkg, smoke_dir=smoke), 0)
        self.assertEqual(bpr.SMOKE_PROMPTS, os.path.join(self.tmp.name, "smoke-guard"))


if __name__ == "__main__":
    unittest.main()
