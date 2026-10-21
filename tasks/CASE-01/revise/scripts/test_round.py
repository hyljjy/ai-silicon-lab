"""Tests for round (WSL-side per-round entry point and unified preflight; CASE-01 stage B Task 11; protocol v0.4
section 3 steps 8-12, sections 8 and 16). WSL only (run per module, never with discover). Everything is written in a
temporary git repository under tasks/CASE-01/runs/ (never /tmp, never the real revise/outputs, results, stops or
predictions; no tags). The gate is a stub (the real gate, Task 4, is pending); grade.py is never run: every attempt
runs fixtures/fake_grade.py, which limits itself to 10 s and 64 KB."""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import extract
import limits
import mapping
import revpaths as rp
import stops

if os.name != "nt":
    import coverage
    import judge
    import round as rnd_mod

RUNS = os.path.join(rp.CASE, "runs")
HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = os.path.join(HERE, "fixtures", "fake_grade.py")
GB = rp.GB
STD = ["tt_025C_1v80", "tt_100C_1v80", "ss_100C_1v60", "ss_n40C_1v60", "ff_n40C_1v95", "ff_100C_1v95"]
GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_CEILING_DIRECTORIES")
TEST_LIMIT = limits.Limit(20, 1 * limits.MB, 1 * limits.MB, 5, 5)
MODELS = ("zz-model-alpha", "zz-model-beta")
ORIENT = {"slack": ("increase", "0.000001", "decimal")}

ANSWER = """说明。

```verilog
module dot4sat(input clk); // {code}
endmodule
```

DECLARED_L = 2

## 预测表

| id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 流水线 | slack | setup | ss_100C_1v60 | global | delta | 改善 | 未知 | 未知 | ns | - | rtl:10 |
"""


def git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
    r = subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=cwd, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=60)
    if r.returncode != 0:
        raise AssertionError(f"git {args} failed: {r.stderr.decode('utf-8', 'replace')}")


def touch(path, data=b"x\n", mode=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    if mode is not None:
        os.chmod(path, mode)


def dump(obj):
    return (json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def jsonl(rows):
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@unittest.skipIf(os.name == "nt", "test_round runs only in WSL")
class Base(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="round_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        t = self.tmp.name
        self.case = os.path.join(t, "case")
        self.revise = os.path.join(self.case, "revise")
        self.sealed = os.path.join(t, "sealed")
        os.makedirs(os.path.join(self.case, "runs"))
        os.makedirs(self.revise)
        git(self.case, "init", "-q", ".")
        git(self.case, "config", "user.name", "test")
        git(self.case, "config", "user.email", "test@example.invalid")
        touch(os.path.join(self.case, ".gitignore"), b"runs/\n.lock\n")
        git(self.case, "add", ".gitignore")
        git(self.case, "commit", "-q", "-m", "init")
        # fake environment of run_grade's dependency check
        self.bin = os.path.join(t, "bin")
        for tool in ("iverilog", "vvp", "yosys", "sta", "python3"):
            touch(os.path.join(self.bin, tool), b"#!/bin/sh\nexit 0\n", 0o755)
        kit = os.path.join(t, "kit")
        touch(os.path.join(kit, "MANIFEST.txt"))
        hd = os.path.join(t, "hd")
        for m in ("primitives.v", "sky130_fd_sc_hd.v"):
            touch(os.path.join(hd, "verilog", m))
        for c in STD:
            touch(os.path.join(hd, "lib", f"sky130_fd_sc_hd__{c}.lib"))
        repo = os.path.join(t, "repo")
        touch(os.path.join(repo, "env", "SHA256SUMS"))
        touch(os.path.join(repo, "env", "tools.sha256"))
        env = {"PATH": self.bin, "SKY130_KIT": kit, "SKY130_HD": hd, "LANG": "C.UTF-8"}
        self.gate_calls = []
        self.gate_reject = set()                        # codes the stub gate rejects
        self.modes = {}
        self.kw = dict(case=self.case, sealed=self.sealed, repo=repo, env=env, free_bytes=lambda vol: 100 * GB,
                       gate=self.fake_gate, grade_cmd=self.cmd, prereg_problems=lambda: [],
                       reused_problems=lambda: [])
        p = mock.patch.dict(limits.LIMITS, {"grade": TEST_LIMIT})
        p.start()
        self.addCleanup(p.stop)
        self.output = []
        self.codes = {}                                 # round -> codes in model order

    # ---------------------------------------------------------------- stubs
    def fake_gate(self, rtl_path, declared_L):
        self.gate_calls.append((os.path.basename(rtl_path), declared_L))
        if any(f"dot4sat_{c}.v" == os.path.basename(rtl_path) for c in self.gate_reject):
            return {"passed": False, "hits": [{"rule": "G1", "line": 1, "kind": "latch", "text": "x"}],
                    "yosys_problem": None}
        return {"passed": True, "hits": [], "yosys_problem": None}

    def cmd(self, code):
        return [sys.executable, "-B", FAKE, "--mode", self.modes.get(code, "rtl_compile_fail"), "--impl",
                f"config/impl.{code}.cfg"]

    def ctx(self):
        return rnd_mod.Ctx(**self.kw)

    def run_sub(self, sub, r, review=None):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = rnd_mod.run(sub, r, self.ctx(), author_review=review)
        self.output.append(buf.getvalue())
        return rc, buf.getvalue()

    def commit(self, msg="step"):
        git(self.case, "add", "-A")
        git(self.case, "commit", "-q", "--allow-empty", "-m", msg)

    # ---------------------------------------------------------------- paths
    def out(self, r, name):
        return os.path.join(self.revise, "outputs", f"r{r}", name)

    def pred(self, name):
        return os.path.join(self.revise, "predictions", name)

    def cdir(self, r, code):
        return os.path.join(self.revise, "results", f"r{r}", code)

    def attempts_of(self, r):
        res = os.path.join(self.revise, "results", f"r{r}")
        found = []
        for base, dirs, files in os.walk(res):
            found += [os.path.join(base, d) for d in dirs if d.startswith("attempt")]
        return found

    # ---------------------------------------------------------------- stage A / B
    def setup_round(self, r, commit_b=True):
        prev = None
        if r == 2:
            prev = dict(zip(MODELS, self.codes[1]))
        codes = mapping.commit_codes(r, list(MODELS), prev, revise=self.revise, sealed=self.sealed)
        self.codes[r] = codes
        self.commit(f"stage A r{r}")
        touch(self.out(r, "attempts.json"), dump({"rnd": r, "codes": {}}))
        touch(self.out(r, "status.md"), b"# status\n")
        for code in sorted(codes):
            text = ANSWER.replace("{code}", code)
            parsed = extract.parse_answer(text, r)
            self.assertEqual(parsed.status, "ok")
            cf = extract.write_candidate(code, parsed, dest_root=self.case)
            touch(self.out(r, f"{code}.call.json"), dump({"code": code, "rnd": r, "final": "parse", "calls": []}))
            touch(self.out(r, f"{code}.md"), text.encode("utf-8"))
            doc = {"status": parsed.status, "declared_L": parsed.declared_L, "rtl_sha_raw": parsed.rtl_sha_raw,
                   "rtl_sha_lf": parsed.rtl_sha_lf, "prediction_L_mismatch": parsed.prediction_L_mismatch,
                   "code": code, "rnd": r,
                   "candidate": {"rtl_path": f"rtl/dot4sat_{code}.v", "cfg_path": f"config/impl.{code}.cfg",
                                 "rtl_sha_raw": cf.rtl_sha_raw, "rtl_sha_lf": cf.rtl_sha_lf, "cfg_sha": cf.cfg_sha}}
            touch(self.out(r, f"{code}.parsed.json"), dump(doc))
            path = self.pred(f"r{r}_extracted.jsonl")
            old = rp.read_bytes(path) if os.path.isfile(path) else b""
            touch(path, old + jsonl(extract.extracted_rows(code, parsed)))
        if commit_b:
            self.commit(f"stage B r{r}")
        return codes

    # ---------------------------------------------------------------- stage C
    def criteria(self, r):
        rows = []
        prev = {c2: c1 for c1, c2 in zip(self.codes[1], self.codes[2])} if r == 2 else {}
        for e in judge.read_jsonl(self.pred(f"r{r}_extracted.jsonl")):
            if e["row_type"] != "prediction":
                continue
            row = {"candidate": e["code"], "row_type": "prediction", "source": "line 12", "criteria_version": "v1",
                   "prediction_id": f"{e['code']}-p1", "extract_index": str(e["index"]),
                   "r1_ref": f"{prev[e['code']]}-p1" if r == 2 else ""}
            for k in judge.EXTRACTED_PREDICTION_COLUMNS:
                row[k] = e[k]
            row["orientation"], row["epsilon"] = ORIENT["slack"][0], ORIENT["slack"][1]
            row["source_field"], row["comparator"] = "", ORIENT["slack"][2]
            rows.append({k: row[k] for k in tuple(judge.COMMON_FIELDS) + tuple(judge.PREDICTION_FIELDS)})
        return rows

    def coverage_rows(self):
        return [{"row_type": "prediction", "r1_ref": f"{c1}-p1", "r2_ref": f"{c2}-p1", "candidate_r1": c1,
                 "candidate_r2": c2, "action": "keep", "same_object": True, "same_criterion": True, "link_basis": ""}
                for c1, c2 in zip(self.codes[1], self.codes[2])]

    def prev2(self):
        return {c2: c1 for c1, c2 in zip(self.codes[1], self.codes[2])}

    def write_views(self, r):
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            rc = judge.views(r, case=self.case, prev=self.prev2() if r == 2 else None)
        self.assertEqual(rc, 0, buf.getvalue())

    def review(self, r, rows=None):
        lines = ["\t".join(rnd_mod.REVIEW_COLUMNS)]
        if rows is None:
            rows = [f"{c}\t是\t看了 diff 和预测表\t\t\t\t5" for c in sorted(self.codes[r])]
        touch(os.path.join(self.revise, "review", f"r{r}.tsv"), ("\n".join(lines + rows) + "\n").encode("utf-8"))

    def phase_c(self, r, review_rows=None):
        rc, out = self.run_sub("ingest", r)
        self.assertEqual(rc, 0, out)
        self.review(r, review_rows)
        touch(self.pred(f"r{r}_criteria.jsonl"), jsonl(self.criteria(r)))
        if r == 2:
            touch(self.pred("r2_coverage.jsonl"), jsonl(self.coverage_rows()))
        self.write_views(r)
        self.commit(f"stage C r{r}")

    def round1_for_round2(self):
        """Round 1 as round 2 needs it: stage A and B, criteria, extracted rows and judgments (committed)."""
        self.setup_round(1)
        crit = self.criteria(1)
        touch(self.pred("r1_criteria.jsonl"), jsonl(crit))
        touch(self.pred("r1_judgments.jsonl"), jsonl([dict(c, judgment="无结果") for c in crit]))
        self.commit("round 1")

    # ---------------------------------------------------------------- stage D
    def notes(self, r):
        rows = [{"candidate": j["candidate"], "ref": j["prediction_id"], "note": "候选未通过回归，没有可用结果"}
                for j in judge.read_jsonl(self.pred(f"r{r}_judgments.jsonl")) if j["judgment"] in ("未判定", "不适用")]
        touch(self.pred(f"r{r}_notes.jsonl"), jsonl(rows))

    def full_round(self, r):
        if r == 2:
            self.round1_for_round2()
        self.setup_round(r)
        self.phase_c(r)
        rc, out = self.run_sub("evaluate", r)
        self.assertEqual(rc, 0, out)
        rc, out = self.run_sub("finalize", r)
        self.assertEqual(rc, 0, out)
        self.notes(r)
        self.commit(f"stage D r{r}")


class Ingest(Base):
    def test_ingest_requires_committed_outputs(self):
        codes = self.setup_round(1, commit_b=False)
        rc, out = self.run_sub("ingest", 1)
        self.assertEqual(rc, 1, out)
        self.assertIn("NOT COMMITTED", out)
        self.assertEqual(self.gate_calls, [])
        for c in codes:
            self.assertFalse(os.path.exists(os.path.join(self.cdir(1, c), "gate.json")))
        self.commit("stage B")
        rc, out = self.run_sub("ingest", 1)
        self.assertEqual(rc, 0, out)
        self.assertEqual(sorted(self.gate_calls), sorted((f"dot4sat_{c}.v", 2) for c in codes))
        for c in codes:
            self.assertEqual(load(os.path.join(self.cdir(1, c), "gate.json")),
                             {"passed": True, "hits": [], "yosys_problem": None})
            self.assertIn(f"CODE {c}: call=parse parsed=ok gate=passed", out)

    def test_ingest_rejects_changed_candidate(self):
        codes = self.setup_round(1)
        rtl = os.path.join(self.case, "rtl", f"dot4sat_{codes[0]}.v")
        touch(rtl, rp.read_bytes(rtl) + b"// edited\n")
        self.commit("edit candidate")
        rc, out = self.run_sub("ingest", 1)
        self.assertEqual(rc, 1, out)
        self.assertIn("the candidate changed", out)
        self.assertEqual(self.gate_calls, [])


class Evaluate(Base):
    def test_evaluate_rejects_missing_review_row(self):
        self.setup_round(1)
        first = sorted(self.codes[1])[0]
        self.phase_c(1, review_rows=[f"{first}\t是\t看了\t\t\t\t5"])
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        self.assertIn("has no review row", out)
        self.assertEqual(self.attempts_of(1), [])

    def test_evaluate_rejects_bad_veto_value(self):
        self.setup_round(1)
        a, b = sorted(self.codes[1])
        self.phase_c(1, review_rows=[f"{a}\t否\t锁存器\tV3\t2.3\t5\t5", f"{b}\t是\t看了\t\t\t\t5"])
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        self.assertIn("否决条目", out)
        self.assertEqual(self.attempts_of(1), [])

    def test_evaluate_rejects_edited_tsv_view(self):
        self.setup_round(1)
        self.phase_c(1)
        p = self.pred("r1_criteria.tsv")
        touch(p, rp.read_bytes(p).replace("流水线".encode("utf-8"), "流水线X".encode("utf-8")))
        self.commit("edit the view")
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        self.assertIn("VIEWS FAIL", out)
        self.assertEqual(self.attempts_of(1), [])

    def test_evaluate_round2_requires_valid_coverage(self):
        self.round1_for_round2()
        self.setup_round(2)
        self.phase_c(2)
        self.assertEqual(rnd_mod.preflight(2, "evaluate", self.ctx()), [])
        rows = self.coverage_rows()
        rows[0]["action"] = "modify"                  # same criterion: modify is illegal (coverage.validate)
        touch(self.pred("r2_coverage.jsonl"), jsonl(rows))
        touch(self.pred("r2_coverage.tsv"), judge.tsv_bytes(rows, coverage.COVERAGE_COLUMNS))
        self.commit("edit coverage")
        rc, out = self.run_sub("evaluate", 2)
        self.assertEqual(rc, 1, out)
        self.assertIn("modify", out)
        self.assertEqual(self.attempts_of(2), [])

    def test_evaluate_runs_vetoed_candidates(self):
        self.setup_round(1)
        a, b = sorted(self.codes[1])
        self.phase_c(1, review_rows=[f"{a}\t否\t锁存器\tV1\t2\t12\t7", f"{b}\t是\t看了\t\t\t\t5"])
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 0, out)
        for c in (a, b):
            self.assertTrue(os.path.isfile(os.path.join(self.cdir(1, c), "attempt1", "attempt.json")))
        self.assertIn(f"CODE {a}: call=parse parsed=ok gate=passed review=V1 attempts=1", out)

    def test_evaluate_recovers_started_only_attempt_first(self):
        self.setup_round(1)
        self.phase_c(1)
        a = sorted(self.codes[1])[0]
        adir = os.path.join(self.cdir(1, a), "attempt1")
        dep = {"time": "2026-11-01T12:00:00+08:00", "ok": False,
               "items": [{"name": "yosys", "path": "yosys (not on PATH)", "exists": False}]}
        touch(os.path.join(adir, "started.json"),
              dump({"code": a, "rnd": 1, "k": 1, "cmd": self.cmd(a), "start": "2026-11-01T12:00:00+08:00",
                    "disk_before": {"free_bytes": {}}, "dependency_check": dep}))
        a_b = sorted(self.codes[1])
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)                  # attempt 1 recovered as external: it awaits its retry
        rec1 = load(os.path.join(adir, "attempt.json"))
        self.assertIn("由包装器恢复", rec1["attribution_evidence"])
        self.assertEqual(rec1["attribution"], "external")
        self.assertFalse(os.path.exists(os.path.join(self.cdir(1, a), "attempt2")))
        self.assertIn(f"AWAIT RETRY {a}: author consent required, then run_grade.py {a} 1 --retry", out)
        self.assertTrue(os.path.isfile(os.path.join(self.cdir(1, a_b[1]), "attempt1", "attempt.json")))
        self.assertLess(out.index(f"RECOVERED {a} attempt1"), out.index("ATTEMPT "))

    def author_retry(self, code):
        """The retry the author consented to: run_grade directly, with the real round.preflight."""
        import run_grade
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rec = run_grade.attempt(code, 1, retry=True, grade_cmd=self.cmd(code), case=self.case,
                                    repo=self.kw["repo"], env=self.kw["env"], free_bytes=self.kw["free_bytes"],
                                    preflight=lambda r, s: rnd_mod.preflight(r, s, self.ctx()))
        self.output.append(buf.getvalue())
        return rec, buf.getvalue()

    def test_evaluate_never_starts_a_retry(self):
        self.setup_round(1)
        self.phase_c(1)
        a, b = sorted(self.codes[1])
        self.modes[a] = "env_snapshot_fail"
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        self.assertIn(f"AWAIT RETRY {a}: author consent required, then run_grade.py {a} 1 --retry", out)
        self.assertFalse(os.path.exists(os.path.join(self.cdir(1, a), "attempt2")))
        self.assertTrue(os.path.isfile(os.path.join(self.cdir(1, b), "attempt1", "attempt.json")))
        rc, out = self.run_sub("evaluate", 1)         # a second evaluate still does not retry
        self.assertEqual(rc, 1, out)
        self.assertFalse(os.path.exists(os.path.join(self.cdir(1, a), "attempt2")))
        self.assertEqual(stops.open_stops(1, revise=self.revise), [])

    def test_evaluate_stops_on_infra_fail(self):
        self.setup_round(1)
        self.phase_c(1)
        a, b = sorted(self.codes[1])
        self.modes[a] = "env_snapshot_fail"
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        rec, out = self.author_retry(a)               # the retry is still an external fault: infra_fail stop
        self.assertEqual(rec["k"], 2)
        recs = stops.open_stops(1, revise=self.revise)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["side"], "eval")
        self.assertTrue(recs[0]["reason"].startswith("infra_fail"))
        self.assertIn(f"commit revise/stops/r1/{recs[0]['stop_id']}.json now", out)
        before = sorted(self.attempts_of(1))
        for sub in ("evaluate", "finalize"):
            rc, out = self.run_sub(sub, 1)
            self.assertEqual(rc, 1, out)
            self.assertIn("STOPPED", out)
        self.assertEqual(sorted(self.attempts_of(1)), before)

    def test_evaluate_stops_at_once_on_a_stop_raised_by_an_attempt(self):
        self.setup_round(1)
        self.phase_c(1)
        a, b = sorted(self.codes[1])
        a1 = os.path.join(self.cdir(1, a), "attempt1")

        def free(vol):                                # low only after attempt 1 of a ran (the disk-after check)
            ran = os.path.exists(os.path.join(a1, "stdout.txt")) and not os.path.exists(os.path.join(a1, "attempt.json"))
            return 5 * GB if ran else 100 * GB
        self.kw["free_bytes"] = free
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        self.assertTrue(os.path.isfile(os.path.join(a1, "attempt.json")))
        self.assertFalse(os.path.exists(os.path.join(self.cdir(1, b), "attempt1")))
        recs = stops.open_stops(1, revise=self.revise)
        self.assertEqual(len(recs), 1)
        self.assertIn(f"commit revise/stops/r1/{recs[0]['stop_id']}.json now", out)

    def test_evaluate_refuses_malformed_jsonl(self):
        self.setup_round(1)
        self.phase_c(1)
        p = self.pred("r1_criteria.jsonl")
        touch(p, rp.read_bytes(p)[:-1])           # last line without LF: judge.read_jsonl raises JudgeError
        self.commit("malformed criteria")
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        self.assertNotIn("Traceback", out)
        with mock.patch.object(judge, "views", return_value=0):     # past the views check: preflight reads it
            probs = rnd_mod.preflight(1, "evaluate", self.ctx())
        self.assertTrue(any("PREFLIGHT FAIL: JudgeError" in x for x in probs), probs)
        self.assertEqual(self.attempts_of(1), [])

    def test_call_side_stop_blocks_evaluate(self):
        self.setup_round(1)
        self.phase_c(1)
        stops.raise_stop(1, "call", "test stop", revise=self.revise)
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        self.assertIn("STOPPED", out)
        self.assertEqual(self.attempts_of(1), [])


class TargetEligibility(Base):
    """Codex BC1-06: the direct run_grade entry and round.py evaluate share round.target_problems, run before any
    attempt directory exists."""

    def direct(self, code, real_preflight=True):
        import run_grade
        pf = (lambda r, s: rnd_mod.preflight(r, s, self.ctx())) if real_preflight else rnd_mod._noop_preflight
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(run_grade.RunGradeError) as cm:
                run_grade.attempt(code, 1, grade_cmd=self.cmd(code), case=self.case, repo=self.kw["repo"],
                                  env=self.kw["env"], free_bytes=self.kw["free_bytes"], preflight=pf)
        self.output.append(buf.getvalue())
        self.assertFalse(os.path.exists(self.cdir(1, code)) and
                         any(n.startswith("attempt") for n in os.listdir(self.cdir(1, code))))
        return str(cm.exception)

    def test_direct_run_grade_refuses_gate_rejected_code(self):
        self.setup_round(1)
        a, b = sorted(self.codes[1])
        self.gate_reject = {a}
        self.phase_c(1)
        self.assertEqual(load(os.path.join(self.cdir(1, a), "gate.json"))["passed"], False)
        self.assertEqual(rnd_mod.preflight(1, "evaluate", self.ctx()), [])   # a correct rejection: round is fine
        for real in (True, False):
            msg = self.direct(a, real_preflight=real)
            self.assertIn(f"NOT ELIGIBLE {a}", msg)
            self.assertIn("gate", msg)
        self.assertEqual(self.attempts_of(1), [])
        self.assertEqual(rnd_mod.target_problems(1, b, self.ctx()), [])

    def test_direct_run_grade_refuses_code_not_in_round(self):
        self.setup_round(1)
        self.phase_c(1)
        for real in (True, False):
            msg = self.direct("cand_zzzz", real_preflight=real)
            self.assertIn("NOT ELIGIBLE cand_zzzz", msg)
            self.assertIn("codes.txt", msg)
        self.assertFalse(os.path.exists(self.cdir(1, "cand_zzzz")))

    def test_direct_run_grade_refuses_code_without_review_row(self):
        self.setup_round(1)
        a, b = sorted(self.codes[1])
        self.phase_c(1, review_rows=[f"{a}\t是\t看了\t\t\t\t5"])
        self.assertIn("has no review row", self.direct(b, real_preflight=True))
        msg = self.direct(b, real_preflight=False)                    # as evaluate calls it (no-op preflight)
        self.assertIn(f"NOT ELIGIBLE {b}", msg)
        self.assertIn("review row", msg)
        self.assertEqual(self.attempts_of(1), [])

    def test_target_problems_call_parse_and_criteria(self):
        self.setup_round(1)
        a, b = sorted(self.codes[1])
        self.phase_c(1)
        crit = [row for row in judge.read_jsonl(self.pred("r1_criteria.jsonl")) if row["candidate"] != a]
        touch(self.pred("r1_criteria.jsonl"), jsonl(crit))
        touch(self.out(1, f"{b}.call.json"), dump({"code": b, "rnd": 1, "final": "unavailable", "calls": []}))
        self.commit("drop criteria of a, b unavailable")
        pa = rnd_mod.target_problems(1, a, self.ctx())
        self.assertTrue(any("criteria" in p for p in pa), pa)
        pb = rnd_mod.target_problems(1, b, self.ctx())
        self.assertTrue(any(f"NOT ELIGIBLE {b}" in p and "parse" in p for p in pb), pb)

    def test_evaluate_refuses_omitted_prediction(self):
        # Codex BC1-05: a code with criteria rows that omit an extracted prediction is not ready for evaluate
        self.setup_round(1)
        self.phase_c(1)
        a, b = sorted(self.codes[1])
        p = self.pred("r1_extracted.jsonl")
        ext = judge.read_jsonl(p)
        p1 = [e for e in ext if e["code"] == a and e["row_type"] == "prediction"][0]
        ext.insert(ext.index(p1) + 1, dict(p1, index=2, id="P2"))
        touch(p, jsonl(ext))
        self.commit("extracted P2 of a without a criteria row")
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        self.assertIn("CRITERIA FAIL", out)
        self.assertIn("index 2", out)
        self.assertEqual(self.attempts_of(1), [])
        pa = rnd_mod.target_problems(1, a, self.ctx())
        self.assertTrue(any(f"NOT ELIGIBLE {a}" in x and "CRITERIA FAIL" in x and "index 2" in x for x in pa), pa)
        self.assertEqual(rnd_mod.target_problems(1, b, self.ctx()), [])


class StatusAndDiskKill(Base):
    def test_status_line_counts_only_started_attempts(self):
        # Codex BC1-S2: an empty attempt1/ is not an attempt (run_grade.attempt_dirs: started.json)
        self.setup_round(1)
        self.phase_c(1)
        a = sorted(self.codes[1])[0]
        os.makedirs(os.path.join(self.cdir(1, a), "attempt1"))
        line = [ln for ln in rnd_mod.status_lines(self.ctx(), 1) if ln.startswith(f"CODE {a}:")][0]
        self.assertIn("attempts=0 last=-", line)

    def test_preflight_disk_kill_fail_raises_eval_stop(self):
        self.setup_round(1)
        self.phase_c(1)

        def free(vol):
            raise rp.MeasureKillFail("df left processes", [4242], False)
        self.kw["free_bytes"] = free
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        recs = stops.open_stops(1, revise=self.revise)
        self.assertEqual([(s["reason"], s["side"]) for s in recs], [("KILL FAIL", "eval")])
        self.assertIn(f"commit revise/stops/r1/{recs[0]['stop_id']}.json now", out)
        self.assertEqual(self.attempts_of(1), [])

    def test_evaluate_disk_kill_fail_before_next_attempt_raises_eval_stop(self):
        self.setup_round(1)
        self.phase_c(1)
        a, b = sorted(self.codes[1])
        done_a = os.path.join(self.cdir(1, a), "attempt1", "attempt.json")

        def free(vol):                                # fails only once attempt 1 of a is written
            if os.path.exists(done_a):
                raise rp.MeasureKillFail("df left processes", [], True)
            return 100 * GB
        self.kw["free_bytes"] = free
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        recs = stops.open_stops(1, revise=self.revise)
        self.assertEqual([(s["reason"], s["side"], s["code"]) for s in recs], [("KILL FAIL", "eval", b)])
        self.assertIn(f"commit revise/stops/r1/{recs[0]['stop_id']}.json now", out)
        self.assertFalse(os.path.exists(os.path.join(self.cdir(1, b), "attempt1")))


class FinalizeClose(Base):
    def test_finalize_stops_on_first_error(self):
        self.setup_round(1)
        self.phase_c(1)
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 0, out)
        a = sorted(self.codes[1])[0]
        os.remove(os.path.join(self.cdir(1, a), "attempt1", "stdout.txt"))
        rc, out = self.run_sub("finalize", 1)
        self.assertEqual(rc, 1, out)
        self.assertIn("ARCHIVE FAIL", out)
        self.assertIn("FINALIZE FAIL: status", out)
        self.assertFalse(os.path.exists(self.pred("r1_judgments.jsonl")))

    def test_finalize_refuses_await_retry(self):
        self.setup_round(1)
        self.phase_c(1)
        a, b = sorted(self.codes[1])
        self.modes[a] = "env_snapshot_fail"
        rc, out = self.run_sub("evaluate", 1)
        self.assertEqual(rc, 1, out)
        rc, out = self.run_sub("finalize", 1)
        self.assertEqual(rc, 1, out)
        self.assertIn(f"AWAIT RETRY {a}", out)
        self.assertIn("REFUSED", out)
        for c in (a, b):
            self.assertFalse(os.path.exists(os.path.join(self.cdir(1, c), "status.json")))
        self.assertFalse(os.path.exists(self.pred("r1_judgments.jsonl")))

    def test_closed_round_refuses_every_subcommand(self):
        self.full_round(1)
        rc, out = self.run_sub("close", 1, review="看了判定表")
        self.assertEqual(rc, 0, out)
        self.commit("close")
        watched = [self.pred("r1_judgments.jsonl"), self.pred("r1_judgments.md")]
        watched += [os.path.join(self.cdir(1, c), "status.json") for c in self.codes[1]]
        before = {p: (rp.read_bytes(p), os.stat(p).st_mtime_ns) for p in watched}
        attempts = sorted(self.attempts_of(1))
        for sub in ("ingest", "evaluate", "finalize", "close"):
            rc, out = self.run_sub(sub, 1, review="again" if sub == "close" else None)
            self.assertEqual(rc, 1, (sub, out))
            self.assertIn("CLOSED", out)
        self.assertEqual({p: (rp.read_bytes(p), os.stat(p).st_mtime_ns) for p in watched}, before)
        self.assertEqual(sorted(self.attempts_of(1)), attempts)

    def test_close_rejects_uncommitted_or_recomputed_difference(self):
        self.full_round(1)
        rc, out = self.run_sub("close", 1, review="")
        self.assertEqual(rc, 1, out)
        a = sorted(self.codes[1])[0]
        st = os.path.join(self.cdir(1, a), "status.json")
        orig = rp.read_bytes(st)
        touch(st, orig + b" ")
        rc, out = self.run_sub("close", 1, review="看了判定表和对照")
        self.assertEqual(rc, 1, out)
        self.assertIn("NOT COMMITTED", out)
        touch(st, orig)
        md = self.pred("r1_judgments.md")
        md_orig = rp.read_bytes(md)
        touch(md, md_orig + b"edited\n")
        self.commit("edit judgments md")
        rc, out = self.run_sub("close", 1, review="看了判定表和对照")
        self.assertEqual(rc, 1, out)
        self.assertIn("RECHECK FAIL (judge)", out)
        self.assertFalse(os.path.exists(self.out(1, "round_complete.json")))
        touch(md, md_orig)
        self.commit("restore")
        rc, out = self.run_sub("close", 1, review="看了判定表和对照")
        self.assertEqual(rc, 0, out)
        doc = load(self.out(1, "round_complete.json"))
        self.assertEqual(doc["author_review"]["text"], "看了判定表和对照")
        self.assertEqual(sorted(doc["states"]), sorted(self.codes[1]))
        self.assertEqual(set(doc["states"].values()), {"grade_fail"})

    def test_close_round2_rechecks_coverage_result(self):
        self.full_round(2)
        p = self.pred("r2_coverage_result.json")
        orig = rp.read_bytes(p)
        touch(p, orig.replace(b'"keep": 2', b'"keep": 3'))
        self.assertNotEqual(rp.read_bytes(p), orig)
        self.commit("edit coverage result")
        rc, out = self.run_sub("close", 2, review="看了覆盖表结果")
        self.assertEqual(rc, 1, out)
        self.assertIn("RECHECK FAIL (coverage)", out)
        touch(p, orig)
        self.commit("restore")
        rc, out = self.run_sub("close", 2, review="看了覆盖表结果")
        self.assertEqual(rc, 0, out)

    def test_output_has_no_model_names(self):
        self.full_round(1)
        self.run_sub("close", 1, review="看了")
        self.run_sub("evaluate", 1)                   # a refusal: the round is closed (CLOSED line)
        text = "".join(self.output)
        self.assertIn("CODE ", text)
        sealed = load(os.path.join(self.sealed, "mapping_r1.json"))
        names = [e["model"] for e in sealed["entries"]]
        self.assertEqual(sorted(names), sorted(MODELS))
        for name in names + ["claude", "opus", "deepseek", "zz-model"]:
            self.assertNotIn(name.lower(), text.lower())


if __name__ == "__main__":
    unittest.main()
