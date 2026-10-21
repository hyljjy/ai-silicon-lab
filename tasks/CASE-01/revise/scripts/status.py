"""Candidate status and round finalisation of CASE-01 stage B (implementation plan Task 5; protocol v0.4 sections
9.1, 12.3). Pure file work; Windows and WSL.

build(code, rnd) reads (paths relative to tasks/CASE-01):
  revise/outputs/r<rnd>/<code>.call.json   written by run_revise (Task 10). Only one field is used here:
        "final": "unavailable" | "delivery_fail" | "parse"   -- the final call decision: attempts used up; delivery
        failure decided at call level (output-cap / truncation evidence, no parse); or the answer was parsed.
  revise/outputs/r<rnd>/<code>.parsed.json  (extract.Parsed fields) -- used: "status" ("ok" | "declined" |
        "delivery_fail"), "declared_L", "prediction_L_mismatch".
  rtl/dot4sat_<code>.v, config/impl.<code>.cfg   the candidate (cfg_L is read from the cfg's "L = <n>" line).
  revise/results/r<rnd>/<code>/gate.json    GateResult (Task 4) -- used: "passed" (bool).
  revise/review/r<rnd>.tsv                  the author's review row of the code (header line with the columns
        code 符合合同 理由 否决条目 合同条款 RTL行号 耗时分钟, tab separated). author_veto is true when the
        否决条目 cell is not empty and not one of "-", "无", "none" (case-insensitive).
  revise/results/r<rnd>/<code>/attempt<k>/  attempt.json and the archived verdict.json / steps.json (run_grade).
The state follows protocol 9.1 top-down; await_retry (attempt 1 attributed "external", no attempt 2) is not final.
A state that cannot be determined (an input missing) is null; finalize_round then fails on the missing input.
Decimal values (area, slack delta) are written as decimal strings with all digits.

finalize_round(rnd, check=False): status.json for every code of revise/outputs/r<rnd>/codes.txt, and SHA256SUMS in
each candidate directory (its top-level files) and in each attempt directory (all its files). Prints
'ARCHIVE FAIL ...' (a required input missing without a reason, a state that cannot be determined, an attempt file
entry missing/invalid without a reason, a produced file absent or changed) and 'AWAIT RETRY ...'; returns 1 then.
check=True recomputes and compares with the files on disk ('CHECK FAIL ...'), never writes.

Command line:  python3 -B revise/scripts/status.py finalize <rnd> [--check]"""
import json
import os
import re
import sys
from decimal import Decimal

import revpaths as rp
import stops

BASE_WORST_SETUP = Decimal("-4.189726018044011")   # F1 baseline worst_setup.slack (evidence/F1/f1_run_verdict.json)
EPS_SLACK = Decimal("0.000001")
STATUS_FIELDS = ("code rnd state flags selected_attempt grade_status final_line_missing rtl_sim gl_sim sta_analysis "
                 "checked_rtl checked_gl area_um2 within_cap author_veto declared_L cfg_L prediction_L_mismatch "
                 "numeric_target_met eligible_target_met improvement worst_setup_delta failure_location attribution "
                 "attribution_evidence inputs").split()
NA = "not_available"
NOT_VETO = ("", "-", "无", "none")
ATTEMPT_DIR_RE = re.compile(r"^attempt([1-9][0-9]*)$")
# stage -> (its steps in steps.json, the step that only runs after grade.py accepted the stage)
STAGES = {"rtl_sim": (("rtl_compile", "rtl_sim"), "synth"),
          "gl_sim": (("gl_compile", "gl_sim"), "sta"),
          "sta_analysis": (("sta", "check_sta"), None)}


def _load(path):
    """(object, problem): object None when the file is missing (problem None) or unreadable (problem text)."""
    if not os.path.isfile(path):
        return None, None
    try:
        return rp.load_json_decimal(path), None
    except (OSError, ValueError) as e:
        return None, f"{e.__class__.__name__}: {e}"


def _dec_out(v):
    return format(v, "f") if isinstance(v, Decimal) else v


def _rel(case, path):
    return os.path.relpath(path, case).replace(os.sep, "/")


def _cfg_L(path):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                key, sep, value = line.partition("=")
                if sep and key.strip() == "L":
                    v = value.split("#", 1)[0].strip()
                    return int(v) if re.fullmatch(r"[0-9]+", v) else NA
    except OSError:
        pass
    return NA


def _review_row(path, code):
    """(row dict or None, problem)."""
    if not os.path.isfile(path):
        return None, None
    try:
        lines = rp.read_bytes(path).decode("utf-8").split("\n")
    except (OSError, UnicodeDecodeError) as e:
        return None, f"{e.__class__.__name__}: {e}"
    header = lines[0].rstrip("\r").split("\t")
    if "code" not in header or "否决条目" not in header:
        return None, "header lacks code / 否决条目"
    for ln in lines[1:]:
        cells = ln.rstrip("\r").split("\t")
        if cells and cells[0].strip() == code:
            cells += [""] * (len(header) - len(cells))
            return dict(zip(header, cells)), None
    return None, None


def _attempts(cdir):
    """[(k, dir, attempt dict | None, steps | None, verdict | None)] for attempt dirs holding started.json or
    attempt.json, by k."""
    out = []
    if not os.path.isdir(cdir):
        return out
    for name in os.listdir(cdir):
        m = ATTEMPT_DIR_RE.match(name)
        d = os.path.join(cdir, name)
        if not m or not (os.path.isfile(os.path.join(d, "started.json")) or
                         os.path.isfile(os.path.join(d, "attempt.json"))):
            continue
        att, _ = _load(os.path.join(d, "attempt.json"))
        steps, _ = _load(os.path.join(d, "steps.json"))
        verdict, _ = _load(os.path.join(d, "verdict.json"))
        out.append((int(m.group(1)), d, att if isinstance(att, dict) else None,
                    steps if isinstance(steps, list) else None, verdict if isinstance(verdict, dict) else None))
    return sorted(out, key=lambda t: t[0])


def _grade_called(att):
    stdout = [f for f in att.get("files") or [] if f.get("path") == "stdout.txt"]
    return not (stdout and stdout[0].get("state") == "not_run")


def stage_state(steps, verdict, final_line, stage, called=True):
    """not_run | pass | fail | indeterminate for rtl_sim / gl_sim / sta_analysis, from steps.json and grade.py's
    decisions; the initial false of functional_pass / analysis_valid is never read as an executed failure."""
    names, after = STAGES[stage]
    if steps is None:
        return "not_run" if (final_line or not called) else "indeterminate"
    recs = {s.get("step"): s for s in steps if isinstance(s, dict)}
    present = [recs[n] for n in names if n in recs]
    if not present:
        return "not_run"
    if any(s.get("interrupted") for s in present):
        return "indeterminate"
    if any(s.get("returncode") != 0 or s.get("timed_out") or s.get("log_problems") for s in present):
        return "fail"
    v = verdict or {}
    if stage == "sta_analysis":
        accepted = v.get("analysis_valid") is True
    else:
        accepted = v.get("functional_pass") is True or (after is not None and after in recs)
    if accepted and len(present) == len(names):
        return "pass"
    if final_line and final_line.startswith("GRADE FAIL:"):
        return "fail"
    return "indeterminate"


def _veto(row):
    if row is None:
        return NA
    return row.get("否决条目", "").strip().lower() not in NOT_VETO


def build(code, rnd, case=None):
    """Candidate-level status.json content (fields STATUS_FIELDS)."""
    case = case or rp.CASE
    revise = os.path.join(case, "revise")
    out_dir = os.path.join(revise, "outputs", f"r{rnd}")
    cdir = os.path.join(revise, "results", f"r{rnd}", code)
    p_call = os.path.join(out_dir, f"{code}.call.json")
    p_parsed = os.path.join(out_dir, f"{code}.parsed.json")
    p_rtl = os.path.join(case, "rtl", f"dot4sat_{code}.v")
    p_cfg = os.path.join(case, "config", f"impl.{code}.cfg")
    p_gate = os.path.join(cdir, "gate.json")
    p_review = os.path.join(revise, "review", f"r{rnd}.tsv")
    flags = []

    call, call_problem = _load(p_call)
    parsed, parsed_problem = _load(p_parsed)
    gate, gate_problem = _load(p_gate)
    row, review_problem = _review_row(p_review, code)
    attempts = _attempts(cdir)
    final = call.get("final") if isinstance(call, dict) else None
    pstatus = parsed.get("status") if isinstance(parsed, dict) else None
    for path, problem in ((p_call, call_problem), (p_parsed, parsed_problem), (p_gate, gate_problem),
                          (p_review, review_problem)):
        if problem:
            flags.append(f"invalid_input: {_rel(case, path)}: {problem}")

    # ---- state, by protocol 9.1 (top-down)
    state, category = None, "all"
    if final == "unavailable":
        state, category = "unavailable", "unavailable"
    elif final == "delivery_fail":
        state, category = "delivery_fail", "truncated"
    elif final == "parse" and pstatus == "declined":
        state, category = "declined", "content"
    elif final == "parse" and pstatus == "delivery_fail":
        state, category = "delivery_fail", "content"
    elif final == "parse" and pstatus == "ok" and isinstance(gate, dict) and gate.get("passed") is False:
        state, category = "gate_reject", "gate"

    sel = attempts[-1] if attempts and category == "all" else None
    att = sel[2] if sel else None
    steps = sel[3] if sel else None
    verdict = sel[4] if sel else None
    final_line = att.get("final_line") if att else None
    called = _grade_called(att) if att else False
    if att is None:
        grade_status = "not_run"
    elif not called:
        grade_status = "not_run"
    elif final_line and final_line.startswith("GRADE OK:"):
        grade_status = "GRADE OK"
    elif final_line and final_line.startswith("GRADE FAIL:"):
        grade_status = "GRADE FAIL"
    else:
        grade_status = "indeterminate"

    # ---- facts that are reported whatever the state
    declared_L = parsed.get("declared_L") if isinstance(parsed, dict) and isinstance(parsed.get("declared_L"), int) \
        and not isinstance(parsed.get("declared_L"), bool) else NA
    pred_mismatch = parsed.get("prediction_L_mismatch") if isinstance(parsed, dict) and \
        isinstance(parsed.get("prediction_L_mismatch"), bool) else NA
    cfg_L = _cfg_L(p_cfg)
    author_veto = _veto(row)
    v = verdict or {}
    area = v.get("area_um2")
    area_um2 = area if isinstance(area, (int, Decimal)) and not isinstance(area, bool) else NA
    wc = (v.get("area") or {}).get("within_cap") if isinstance(v.get("area"), dict) else None
    within_cap = wc if isinstance(wc, bool) else NA
    met = (v.get("timing_target") or {}).get("met") if isinstance(v.get("timing_target"), dict) else None
    numeric_target_met = met if isinstance(met, bool) else NA
    slack = (v.get("worst_setup") or {}).get("slack") if isinstance(v.get("worst_setup"), dict) else None
    delta = slack - BASE_WORST_SETUP if isinstance(slack, (int, Decimal)) and not isinstance(slack, bool) else None
    impl_L = (v.get("impl") or {}).get("L") if isinstance(v.get("impl"), dict) else None
    impl_L = int(impl_L) if isinstance(impl_L, (int, str)) and re.fullmatch(r"[0-9]+", str(impl_L)) else None

    if author_veto is True:
        flags.append("author_veto")
    if within_cap is False:
        flags.append("area_over_cap")
    L_bad = (declared_L != NA and not 1 <= declared_L <= 3) or \
        (declared_L != NA and cfg_L != NA and declared_L != cfg_L) or \
        (impl_L is not None and cfg_L != NA and impl_L != cfg_L)
    if L_bad:
        flags.append("L_mismatch")
    if grade_status == "GRADE OK" and within_cap == NA:
        flags.append("area_not_available")

    reasons = [f for f in flags if not f.startswith("invalid_input")]
    eligible = (grade_status == "GRADE OK" and not reasons and author_veto is False and within_cap is True
                and declared_L != NA and cfg_L != NA)

    if category == "all" and state is None and final == "parse" and pstatus == "ok" and \
            isinstance(gate, dict) and gate.get("passed") is True and att is not None and \
            all(a[2] is not None for a in attempts):
        k = sel[0]
        if grade_status == "GRADE OK":
            if eligible:
                state = "eligible_gain" if delta is not None and delta > EPS_SLACK else "eligible_no_gain"
            else:
                state = "ineligible"
        elif att.get("attribution") == "external" or (k >= 2 and att.get("final_line_missing")):
            state = "await_retry" if k == 1 else "infra_fail"
        else:
            state = "grade_fail"

    # ---- inputs
    inputs = []

    def item(path, required, present, rel=None):
        rel = rel or _rel(case, path)
        if not required:
            inputs.append({"path": rel, "required": False, "state": "not_applicable", "reason": None})
        else:
            inputs.append({"path": rel, "required": True, "state": "present" if present else "missing",
                           "reason": None})

    need_parsed = category not in ("unavailable", "truncated")
    need_cand = category in ("gate", "all")
    need_run = category == "all"
    item(p_call, True, isinstance(call, dict) and final in ("unavailable", "delivery_fail", "parse"))
    item(p_parsed, need_parsed, isinstance(parsed, dict) and pstatus in ("ok", "declined", "delivery_fail"))
    item(p_rtl, need_cand, os.path.isfile(p_rtl))
    item(p_cfg, need_cand, os.path.isfile(p_cfg))
    item(p_gate, need_cand, isinstance(gate, dict) and isinstance(gate.get("passed"), bool))
    item(None, need_run, row is not None, rel=f"{_rel(case, p_review)}#{code}")
    if attempts and need_run:
        for k, d, a, _, _ in attempts:
            item(os.path.join(d, "attempt.json"), True, a is not None)
    else:
        item(os.path.join(cdir, "attempt1", "attempt.json"), need_run, False)

    run_fields = att is not None
    st = {"code": code, "rnd": rnd, "state": state, "flags": flags,
          "selected_attempt": sel[0] if sel else None,
          "grade_status": grade_status,
          "final_line_missing": bool(att.get("final_line_missing")) if run_fields else False,
          "rtl_sim": stage_state(steps, verdict, final_line, "rtl_sim", called) if run_fields else "not_run",
          "gl_sim": stage_state(steps, verdict, final_line, "gl_sim", called) if run_fields else "not_run",
          "sta_analysis": stage_state(steps, verdict, final_line, "sta_analysis", called) if run_fields
          else "not_run",
          "checked_rtl": v["rtl_sim"] if isinstance(v.get("rtl_sim"), str) else NA,
          "checked_gl": v["gl_sim"] if isinstance(v.get("gl_sim"), str) else NA,
          "area_um2": _dec_out(area_um2), "within_cap": within_cap, "author_veto": author_veto,
          "declared_L": declared_L, "cfg_L": cfg_L, "prediction_L_mismatch": pred_mismatch,
          "numeric_target_met": numeric_target_met,
          "eligible_target_met": bool(eligible and numeric_target_met is True),
          "improvement": (delta is not None and delta > EPS_SLACK) if eligible else "not_applicable",
          "worst_setup_delta": _dec_out(delta) if delta is not None else NA,
          "failure_location": att.get("failure_location") if run_fields else "not_run",
          "attribution": att.get("attribution") if run_fields else "not_run",
          "attribution_evidence": list(att.get("attribution_evidence") or []) if run_fields else [],
          "inputs": inputs}
    return st


# ------------------------------------------------------------------------------------- finalisation
def _dump(obj):
    return (json.dumps(obj, indent=1, ensure_ascii=False, default=_dec_out) + "\n").encode("utf-8")


def _sums(d, recursive):
    lines = []
    if recursive:
        for base, dirs, files in os.walk(d):
            dirs.sort()
            for fn in files:
                p = os.path.join(base, fn)
                rel = _rel(d, p)
                if rel != "SHA256SUMS" and not rel.endswith(".tmp"):
                    lines.append((rel, rp.sha256(p)))
    else:
        for fn in os.listdir(d):
            p = os.path.join(d, fn)
            if os.path.isfile(p) and fn != "SHA256SUMS" and not fn.endswith(".tmp"):
                lines.append((fn, rp.sha256(p)))
    return "".join(f"{sha}  {rel}\n" for rel, sha in sorted(lines)).encode("utf-8")


def _attempt_problems(code, d, att):
    probs = []
    for f in att.get("files") or []:
        path, state = f.get("path"), f.get("state")
        if state in ("missing", "invalid", "not_run") and not f.get("reason"):
            probs.append(f"ARCHIVE FAIL {code}: {os.path.basename(d)}/{path} is {state} without a reason")
        if state == "produced":
            p = os.path.join(d, *str(path).split("/"))
            if not os.path.isfile(p):
                probs.append(f"ARCHIVE FAIL {code}: {os.path.basename(d)}/{path} is recorded as produced but absent")
            elif f.get("sha256") and rp.sha256(p) != f["sha256"]:
                probs.append(f"ARCHIVE FAIL {code}: {os.path.basename(d)}/{path} differs from its recorded sha256")
    return probs


def finalize_round(rnd, check=False, locked=False, case=None):
    """See the module doc; returns the exit code (0 or 1) and prints every problem."""
    case = case or rp.CASE
    if locked:
        return _finalize(rnd, check, case)
    with stops.round_lock(rnd, "eval", revise=os.path.join(case, "revise")):
        return _finalize(rnd, check, case)


def _finalize(rnd, check, case):
    revise = os.path.join(case, "revise")
    codes_path = os.path.join(revise, "outputs", f"r{rnd}", "codes.txt")
    try:
        codes = [c.strip() for c in rp.read_bytes(codes_path).decode("utf-8").splitlines() if c.strip()]
    except (OSError, UnicodeDecodeError) as e:
        print(f"ARCHIVE FAIL: {_rel(case, codes_path)} cannot be read ({e.__class__.__name__})", flush=True)
        return 1
    problems = []
    for code in codes:
        st = build(code, rnd, case=case)
        cdir = os.path.join(revise, "results", f"r{rnd}", code)
        for i in st["inputs"]:
            if i["required"] and i["state"] == "missing" and not i["reason"]:
                problems.append(f"ARCHIVE FAIL {code}: required input {i['path']} is missing")
        if st["state"] is None:
            problems.append(f"ARCHIVE FAIL {code}: the state cannot be determined from the inputs")
        if st["state"] == "await_retry":
            problems.append(f"AWAIT RETRY {code}: attempt 1 is attributed to an external fault; run the retry "
                            f"(run_grade.py {code} {rnd} --retry) before finalising")
        for k, d, att, _, _ in _attempts(cdir):
            if att is not None:
                problems += _attempt_problems(code, d, att)
        targets = [(os.path.join(cdir, "status.json"), _dump(st))]
        if check:
            _compare(targets[0][0], targets[0][1], case, problems, code)
        else:
            os.makedirs(cdir, exist_ok=True)
            with open(targets[0][0], "wb") as f:
                f.write(targets[0][1])
        sums = [(os.path.join(cdir, "SHA256SUMS"), cdir, False)]
        sums += [(os.path.join(d, "SHA256SUMS"), d, True) for _, d, _, _, _ in _attempts(cdir)]
        for path, d, recursive in sums:
            if not os.path.isdir(d):
                problems.append(f"CHECK FAIL {code}: {_rel(case, d)} does not exist")
                continue
            data = _sums(d, recursive)
            if check:
                _compare(path, data, case, problems, code)
            else:
                with open(path, "wb") as f:
                    f.write(data)
    for p in problems:
        print(p, flush=True)
    return 1 if problems else 0


def _compare(path, data, case, problems, code):
    try:
        same = rp.read_bytes(path) == data
    except OSError:
        same = False
    if not same:
        problems.append(f"CHECK FAIL {code}: {_rel(case, path)} differs from the recomputed content")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    if len(args) != 2 or args[0] != "finalize" or not args[1].isdigit():
        print("usage: status.py finalize <rnd> [--check]", file=sys.stderr)
        return 2
    try:
        return finalize_round(int(args[1]), check=check)
    except stops.StopsError as e:
        print(str(e), flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
