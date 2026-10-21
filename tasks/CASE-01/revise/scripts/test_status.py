"""Tests for status (candidate status, protocol 9.1, and round finalisation, protocol 12.3; CASE-01 stage B Task 5).
Both sides (Windows and WSL); run per module, never with discover. Pure file work in a temporary directory under
tasks/CASE-01/runs/ (never /tmp, never the real revise/ trees); no subprocess except git for the temporary repo."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from decimal import Decimal

import revpaths as rp
import status

RUNS = os.path.join(rp.CASE, "runs")
HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "fixtures", "runs")
BASE_SLACK = "-4.189726018044011"
GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_CEILING_DIRECTORIES")
REVIEW_HEADER = "code\t符合合同\t理由\t否决条目\t合同条款\tRTL行号\t耗时分钟\n"


def git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
    r = subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=cwd, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=60)
    if r.returncode != 0:
        raise AssertionError(f"git {args} failed: {r.stderr.decode('utf-8', 'replace')}")


def wbytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def wjson(path, obj):
    wbytes(path, (json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))


class Base(unittest.TestCase):
    def setUp(self):
        os.makedirs(RUNS, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="status_", dir=RUNS, ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.case = os.path.join(self.tmp.name, "case")
        self.revise = os.path.join(self.case, "revise")
        os.makedirs(self.revise)
        git(self.case, "init", "-q", ".")
        git(self.case, "config", "user.name", "test")
        git(self.case, "config", "user.email", "test@example.invalid")
        wbytes(os.path.join(self.case, "README"), b"temp\n")
        git(self.case, "add", "README")
        git(self.case, "commit", "-q", "-m", "init")
        self.review_rows = {}

    # ------------------------------------------------------------------------------------------------ builders
    def call(self, code, final):
        wjson(os.path.join(self.revise, "outputs", "r1", f"{code}.call.json"), {"final": final})

    def parsed(self, code, pstatus="ok", declared_L=1, mismatch=False):
        wjson(os.path.join(self.revise, "outputs", "r1", f"{code}.parsed.json"),
              {"status": pstatus, "declared_L": declared_L, "prediction_L_mismatch": mismatch})

    def candidate(self, code, L=1):
        wbytes(os.path.join(self.case, "rtl", f"dot4sat_{code}.v"), b"module dot4sat; endmodule\n")
        wbytes(os.path.join(self.case, "config", f"impl.{code}.cfg"),
               f"name = {code}\ntop = dot4sat\nrtl = rtl/dot4sat_{code}.v\nL = {L}\n".encode())

    def gate(self, code, passed=True):
        wjson(os.path.join(self.revise, "results", "r1", code, "gate.json"), {"passed": passed, "hits": []})

    def review(self, code, veto=""):
        self.review_rows[code] = veto
        text = REVIEW_HEADER + "".join(f"{c}\t是\t理由\t{v}\t\t\t5\n" for c, v in self.review_rows.items())
        wbytes(os.path.join(self.revise, "review", "r1.tsv"), text.encode("utf-8"))

    def attempt(self, code, k, sample, attribution="no_external_evidence", evidence=(), verdict_edit=None,
                final_line="meta", final_line_missing=None):
        adir = os.path.join(self.revise, "results", "r1", code, f"attempt{k}")
        os.makedirs(adir)
        meta = json.loads(rp.read_bytes(os.path.join(SAMPLES, sample, "meta.json")).decode("utf-8"))
        files = []
        src = os.path.join(SAMPLES, sample, "run")
        for name in ("verdict.json", "steps.json"):
            if os.path.exists(os.path.join(src, name)):
                shutil.copyfile(os.path.join(src, name), os.path.join(adir, name))
        if verdict_edit and os.path.exists(os.path.join(adir, "verdict.json")):
            path = os.path.join(adir, "verdict.json")
            text = rp.read_bytes(path).decode("utf-8")
            for old, new in verdict_edit:
                self.assertIn(old, text)
                text = text.replace(old, new)
            wbytes(path, text.encode("utf-8"))
        wbytes(os.path.join(adir, "stdout.txt"), b"RUN_ID=r\n")
        for name in sorted(os.listdir(adir)):
            files.append({"path": name, "state": "produced", "reason": None,
                          "sha256": rp.sha256(os.path.join(adir, name))})
        if final_line == "meta":
            final_line = meta["final"].replace("{run_id}", "r") if meta["final"] else None
        if final_line_missing is None:
            final_line_missing = final_line is None
        steps = json.loads(rp.read_bytes(os.path.join(adir, "steps.json")).decode("utf-8")) if os.path.exists(
            os.path.join(adir, "steps.json")) else None
        rec = {"code": code, "rnd": 1, "k": k, "cmd": ["python3"], "start": "s", "end": "e",
               "exit_code": meta["exit"], "timed_out": False, "over_limit": False, "signals_sent": [],
               "launch_error": None, "run_id": "r", "final_line": final_line,
               "final_line_missing": final_line_missing,
               "failure_location": self.location(steps, final_line), "attribution": attribution,
               "attribution_evidence": list(evidence), "disk_before": {}, "disk_after": {},
               "dependency_after": {"ok": True, "items": []}, "files": files}
        wjson(os.path.join(adir, "attempt.json"), rec)
        return adir

    @staticmethod
    def location(steps, final_line):
        for s in steps or []:
            if s["returncode"] != 0 or s["timed_out"] or s.get("interrupted") or s["log_problems"]:
                return s["step"]
        if final_line and final_line.startswith("GRADE FAIL:"):
            return "outside_steps"
        return "none" if final_line else "no_final_line"

    def evaluated(self, code, sample="success", veto="", L=1, declared_L=1, **kw):
        """A candidate that went through the gate, the author's review and one attempt."""
        self.call(code, "parse")
        self.parsed(code, declared_L=declared_L)
        self.candidate(code, L=L)
        self.gate(code)
        self.review(code, veto)
        return self.attempt(code, 1, sample, **kw)

    def codes(self, *codes):
        wbytes(os.path.join(self.revise, "outputs", "r1", "codes.txt"), "".join(c + "\n" for c in codes).encode())

    def build(self, code):
        return status.build(code, 1, case=self.case)

    def finalize(self, check=False):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = status.finalize_round(1, check=check, case=self.case)
        return rc, out.getvalue()

    def inputs(self, st):
        return {i["path"]: (i["required"], i["state"]) for i in st["inputs"]}

    def assert_inputs(self, st, code, required, not_applicable):
        got = self.inputs(st)
        names = {"call": f"revise/outputs/r1/{code}.call.json", "parsed": f"revise/outputs/r1/{code}.parsed.json",
                 "rtl": f"rtl/dot4sat_{code}.v", "cfg": f"config/impl.{code}.cfg",
                 "gate": f"revise/results/r1/{code}/gate.json", "review": f"revise/review/r1.tsv#{code}",
                 "attempt": f"revise/results/r1/{code}/attempt1/attempt.json"}
        for n in required:
            self.assertEqual(got[names[n]], (True, "present"), n)
        for n in not_applicable:
            self.assertEqual(got[names[n]], (False, "not_applicable"), n)


class TestStates(Base):
    def test_unavailable(self):
        self.call("cand_a001", "unavailable")
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "unavailable")
        self.assertEqual(st["grade_status"], "not_run")
        self.assertIsNone(st["selected_attempt"])
        self.assert_inputs(st, "cand_a001", ["call"], ["parsed", "rtl", "cfg", "gate", "review", "attempt"])

    def test_declined(self):
        self.call("cand_a001", "parse")
        self.parsed("cand_a001", "declined", declared_L=None)
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "declined")
        self.assert_inputs(st, "cand_a001", ["call", "parsed"], ["rtl", "cfg", "gate", "review", "attempt"])

    def test_delivery_fail_truncated_needs_no_parsed(self):
        self.call("cand_a001", "delivery_fail")
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "delivery_fail")
        self.assert_inputs(st, "cand_a001", ["call"], ["parsed", "rtl", "cfg", "gate", "review", "attempt"])
        self.assertEqual(st["rtl_sim"], "not_run")

    def test_delivery_fail_content(self):
        self.call("cand_a001", "parse")
        self.parsed("cand_a001", "delivery_fail", declared_L=None)
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "delivery_fail")
        self.assert_inputs(st, "cand_a001", ["call", "parsed"], ["rtl", "cfg", "gate", "review", "attempt"])

    def test_gate_reject(self):
        self.call("cand_a001", "parse")
        self.parsed("cand_a001")
        self.candidate("cand_a001")
        self.gate("cand_a001", passed=False)
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "gate_reject")
        self.assert_inputs(st, "cand_a001", ["call", "parsed", "rtl", "cfg", "gate"], ["review", "attempt"])

    def test_infra_fail(self):
        self.evaluated("cand_a001", "env_snapshot_fail", attribution="external", evidence=["env_snapshot_failed"])
        self.attempt("cand_a001", 2, "env_snapshot_fail", attribution="external", evidence=["env_snapshot_failed"])
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "infra_fail")
        self.assertEqual(st["selected_attempt"], 2)
        self.assertEqual(st["attribution"], "external")

    def test_grade_fail(self):
        self.evaluated("cand_a001", "check_sta_fail")
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "grade_fail")
        self.assertEqual(st["grade_status"], "GRADE FAIL")
        self.assertEqual(st["failure_location"], "check_sta")
        self.assertEqual(st["attribution"], "no_external_evidence")
        self.assert_inputs(st, "cand_a001", ["call", "parsed", "rtl", "cfg", "gate", "review", "attempt"], [])

    def test_grade_fail_final_line_missing_without_evidence(self):
        self.evaluated("cand_a001", "interrupted_no_final")
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "grade_fail")
        self.assertEqual(st["grade_status"], "indeterminate")
        self.assertTrue(st["final_line_missing"])
        self.assertEqual(st["rtl_sim"], "indeterminate")

    def test_ineligible_L_mismatch(self):
        self.evaluated("cand_a001", "success", L=2, declared_L=1)
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "ineligible")
        self.assertEqual(st["flags"], ["L_mismatch"])

    def test_eligible_no_gain(self):
        self.evaluated("cand_a001", "success")
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "eligible_no_gain")
        self.assertEqual(st["grade_status"], "GRADE OK")
        self.assertEqual(st["flags"], [])
        self.assertIs(st["improvement"], False)
        self.assertEqual(Decimal(st["worst_setup_delta"]), 0)
        self.assertEqual((st["rtl_sim"], st["gl_sim"], st["sta_analysis"]), ("pass", "pass", "pass"))
        self.assertEqual(st["checked_rtl"], "checked=2856")
        self.assertIs(st["numeric_target_met"], False)
        self.assertIs(st["eligible_target_met"], False)
        self.assertEqual(st["cfg_L"], 1)
        self.assertEqual(st["declared_L"], 1)
        self.assertIs(st["author_veto"], False)

    def test_eligible_gain(self):
        self.evaluated("cand_a001", "success", verdict_edit=[(f'"slack": {BASE_SLACK}', '"slack": -4.189724')])
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "eligible_gain")
        self.assertIs(st["improvement"], True)
        self.assertEqual(Decimal(st["worst_setup_delta"]), Decimal("-4.189724") - Decimal(BASE_SLACK))

    def test_await_retry(self):
        self.evaluated("cand_a001", "env_snapshot_fail", attribution="external", evidence=["env_snapshot_failed"])
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "await_retry")


class TestFields(Base):
    def test_priority_veto_and_area_combo(self):
        self.evaluated("cand_a001", "success", veto="V2",
                       verdict_edit=[('"within_cap": true', '"within_cap": false')])
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "ineligible")
        self.assertEqual(sorted(st["flags"]), ["area_over_cap", "author_veto"])
        self.assertIs(st["author_veto"], True)
        self.assertEqual(st["improvement"], "not_applicable")

    def test_initial_false_not_fail(self):
        self.evaluated("cand_a001", "lint_fail")
        st = self.build("cand_a001")
        self.assertEqual((st["rtl_sim"], st["gl_sim"], st["sta_analysis"]), ("not_run", "not_run", "not_run"))
        self.evaluated("cand_b002", "rtl_compile_fail")
        st = self.build("cand_b002")
        self.assertEqual((st["rtl_sim"], st["gl_sim"], st["sta_analysis"]), ("fail", "not_run", "not_run"))

    def test_sta_fail_fields(self):
        self.evaluated("cand_a001", "sta_fail")
        st = self.build("cand_a001")
        self.assertEqual((st["rtl_sim"], st["gl_sim"], st["sta_analysis"]), ("pass", "pass", "fail"))
        self.assertEqual(st["failure_location"], "sta")
        self.assertEqual(Decimal(st["area_um2"]), Decimal("45383.5264"))
        self.assertIs(st["within_cap"], True)
        self.assertEqual(st["numeric_target_met"], "not_available")
        self.assertEqual(st["checked_gl"], "checked=2856")
        self.assertEqual(st["state"], "grade_fail")

    def test_compile_fail_still_reports_available_fields(self):
        self.evaluated("cand_a001", "rtl_compile_fail", veto="V1")
        st = self.build("cand_a001")
        self.assertEqual(st["state"], "grade_fail")
        self.assertEqual(st["failure_location"], "rtl_compile")
        self.assertIs(st["author_veto"], True)
        self.assertEqual(st["declared_L"], 1)
        self.assertEqual(st["cfg_L"], 1)
        self.assertEqual(st["checked_rtl"], "not_available")
        self.assertEqual(st["area_um2"], "not_available")
        self.assertEqual(st["within_cap"], "not_available")
        self.assertEqual(st["worst_setup_delta"], "not_available")
        self.assertIn("author_veto", st["flags"])

    def test_improvement_epsilon_boundary(self):
        at = Decimal(BASE_SLACK) + Decimal("0.000001")
        above = Decimal(BASE_SLACK) + Decimal("0.0000010000001")
        self.evaluated("cand_a001", "success", verdict_edit=[(f'"slack": {BASE_SLACK}', f'"slack": {at}')])
        self.evaluated("cand_b002", "success", verdict_edit=[(f'"slack": {BASE_SLACK}', f'"slack": {above}')])
        self.assertEqual(self.build("cand_a001")["state"], "eligible_no_gain")
        self.assertEqual(self.build("cand_b002")["state"], "eligible_gain")

    def test_baseline_constant_matches_f1_evidence(self):
        v = rp.load_json_decimal(os.path.join(rp.CASE, "evidence", "F1", "f1_run_verdict.json"))
        self.assertEqual(status.BASE_WORST_SETUP, v["worst_setup"]["slack"])

    def test_within_cap_taken_from_verdict(self):
        # the area is below the cap, but the verdict says within_cap false: the verdict is taken as it is
        self.evaluated("cand_a001", "success", verdict_edit=[('"within_cap": true', '"within_cap": false')])
        st = self.build("cand_a001")
        self.assertIs(st["within_cap"], False)
        self.assertEqual(st["flags"], ["area_over_cap"])

    def test_cfg_L_mismatch_flag(self):
        self.evaluated("cand_a001", "success", L=1, declared_L=1, verdict_edit=[('"L": "1"', '"L": "2"')])
        st = self.build("cand_a001")
        self.assertIn("L_mismatch", st["flags"])
        self.assertEqual(st["state"], "ineligible")
        self.evaluated("cand_b002", "success", L=3, declared_L=1)
        st = self.build("cand_b002")
        self.assertEqual(st["cfg_L"], 3)
        self.assertIn("L_mismatch", st["flags"])

    def test_prediction_L_mismatch_is_recorded_not_ineligible(self):
        self.evaluated("cand_a001", "success")
        self.parsed("cand_a001", declared_L=1, mismatch=True)
        st = self.build("cand_a001")
        self.assertIs(st["prediction_L_mismatch"], True)
        self.assertEqual(st["state"], "eligible_no_gain")

    def test_eligible_target_met_needs_eligible(self):
        edit = [('"met": false', '"met": true')]
        self.evaluated("cand_a001", "success", veto="V1", verdict_edit=edit)
        st = self.build("cand_a001")
        self.assertIs(st["numeric_target_met"], True)
        self.assertIs(st["eligible_target_met"], False)
        self.evaluated("cand_b002", "success", verdict_edit=edit)
        self.assertIs(self.build("cand_b002")["eligible_target_met"], True)


class TestFinalize(Base):
    def test_await_retry_blocks_finalize(self):
        self.codes("cand_a001")
        self.evaluated("cand_a001", "env_snapshot_fail", attribution="external", evidence=["env_snapshot_failed"])
        rc, out = self.finalize()
        self.assertEqual(rc, 1)
        self.assertIn("AWAIT RETRY", out)

    def test_finalize_covers_codes_without_attempts(self):
        self.codes("cand_a001", "cand_b002", "cand_c003")
        self.call("cand_a001", "unavailable")
        self.call("cand_b002", "delivery_fail")
        self.evaluated("cand_c003", "success")
        rc, out = self.finalize()
        self.assertEqual(rc, 0, out)
        for code, state in (("cand_a001", "unavailable"), ("cand_b002", "delivery_fail"),
                            ("cand_c003", "eligible_no_gain")):
            st = json.loads(rp.read_bytes(os.path.join(self.revise, "results", "r1", code, "status.json")))
            self.assertEqual(st["state"], state)
            self.assertEqual(st["code"], code)

    def test_finalize_missing_required_input_fails(self):
        self.codes("cand_a001")
        self.call("cand_a001", "parse")
        self.parsed("cand_a001")
        self.candidate("cand_a001")
        self.gate("cand_a001")
        self.attempt("cand_a001", 1, "success")       # no review row
        rc, out = self.finalize()
        self.assertEqual(rc, 1)
        self.assertIn("ARCHIVE FAIL", out)
        self.assertIn("revise/review/r1.tsv#cand_a001", out)

    def test_finalize_produced_file_missing_fails(self):
        self.codes("cand_a001")
        adir = self.evaluated("cand_a001", "success")
        os.remove(os.path.join(adir, "steps.json"))
        rc, out = self.finalize()
        self.assertEqual(rc, 1)
        self.assertIn("ARCHIVE FAIL", out)

    def test_sha256sums_written(self):
        self.codes("cand_a001")
        adir = self.evaluated("cand_a001", "success")
        rc, out = self.finalize()
        self.assertEqual(rc, 0, out)
        cdir = os.path.dirname(adir)
        for d in (cdir, adir):
            lines = rp.read_bytes(os.path.join(d, "SHA256SUMS")).decode().splitlines()
            self.assertTrue(lines)
            for ln in lines:
                digest, rel = ln.split("  ", 1)
                self.assertEqual(rp.sha256(os.path.join(d, *rel.split("/"))), digest, rel)
        top = rp.read_bytes(os.path.join(cdir, "SHA256SUMS")).decode()
        self.assertIn("  status.json\n", top)
        self.assertIn("  gate.json\n", top)
        self.assertNotIn("attempt1/", top)
        self.assertIn("  attempt.json\n", rp.read_bytes(os.path.join(adir, "SHA256SUMS")).decode())

    def test_check_mode_detects_changed_status(self):
        self.codes("cand_a001")
        self.evaluated("cand_a001", "success")
        self.assertEqual(self.finalize()[0], 0)
        path = os.path.join(self.revise, "results", "r1", "cand_a001", "status.json")
        data = rp.read_bytes(path)
        rc, out = self.finalize(check=True)
        self.assertEqual(rc, 0, out)
        self.assertEqual(rp.read_bytes(path), data)
        wbytes(path, data.replace(b'"eligible_no_gain"', b'"eligible_gain"'))
        rc, out = self.finalize(check=True)
        self.assertEqual(rc, 1)
        self.assertIn("CHECK FAIL", out)
        self.assertNotEqual(rp.read_bytes(path), data)          # check mode never writes


if __name__ == "__main__":
    unittest.main()
