"""WSL-side per-round entry point and unified preflight of CASE-01 stage B (implementation plan Task 11; protocol
v0.4 section 3 steps 8-12, sections 8 and 16; data contract "提交阶段" A-E).

Command line (WSL, from tasks/CASE-01):
  python3 -B revise/scripts/round.py ingest <r>
  python3 -B revise/scripts/round.py evaluate <r>
  python3 -B revise/scripts/round.py finalize <r>
  python3 -B revise/scripts/round.py close <r> --author-review "<what the author actually looked at>"
<r> is 1 or 2. Exit codes: 0 done; 1 refused or stopped (nothing done after a failed preflight); 2 usage.
Every subcommand holds the eval lock (stops.round_lock(r, "eval")) for its whole run, runs preflight(r, <stage>)
first and prints one status line per code at the end (codes only, never a model name).

preflight(r, stage) -> list of problems (empty: go). Stages are cumulative: ingest < evaluate < finalize < close.
  all     the eval lock (taken for the checks, or already held by this process); no open stop on either side
          (stops.open_stops); prereg.problems("formal"); revpaths.reused_problems(); revpaths.disk_problems();
          mapping.load(r); outputs/r<r>/codes.txt committed.
  ingest  stage-B products committed (data contract B): attempts.json, status.md, every code's call.json (final one
          of parse / delivery_fail / unavailable), the public answer <code>.md (final parse or delivery_fail),
          <code>.parsed.json (final parse), for parsed status "ok" the candidate rtl/dot4sat_<code>.v and
          config/impl.<code>.cfg, and predictions/r<r>_extracted.jsonl (when any code was parsed; each parsed code
          has rows). The candidate's sha256 must equal the hashes recorded in parsed.json (rtl_sha_lf, candidate.cfg_sha;
          paths rtl/dot4sat_<code>.v, config/impl.<code>.cfg). No answer is re-extracted: parsed.json and the
          extracted rows are redacted, the candidate came from the raw answer.
  evaluate  + results/r<r>/<code>/gate.json committed for every "ok" code and byte-equal to a re-run of the gate;
          review/r<r>.tsv committed, header exactly REVIEW_COLUMNS, exactly one row per gate-passed code, legal
          fields (符合合同 是/否/不确定; 理由 not empty; 否决条目 empty or V1 / V2 / both, separated by "," "、" or
          blanks, and then 合同条款 and RTL行号 not empty; 耗时分钟 a non-negative number; every code in codes.txt, at
          most one row each); r<r>_criteria.jsonl and .tsv committed and judge.views(r, check=True) passes (round 2:
          also r2_coverage.jsonl / .tsv committed; judge.views(2) validates the coverage table with
          coverage.validate after the same_as resolution of the criteria); every code with an extracted prediction or
          failure-condition row has criteria rows; baseline.verify().
  finalize  + every gate-passed code has attempts, all with attempt.json, and a final status.build state (never
          await_retry, never undeterminable).
  close   + revise/outputs/r<r>/round_complete.json does not exist yet; stage-D products committed: every file under
          results/r<r>/ (locks aside), revise/compare/r<r>_<code>.json/.md of the codes whose status.json has
          sta_analysis "pass", r<r>_judgments.jsonl/.md, (round 2) r2_coverage_result.json, r<r>_notes.jsonl;
          recomputation in check mode is byte-identical: status.finalize_round, compare matrix, judge.run and
          (round 2) coverage.compute, in that order (judge before coverage: coverage does not redo same_as).
          Notes (operator-written, author-reviewed; only existence, committed state and links are checked):
          r<r>_notes.jsonl lines {"candidate", "ref", "note"}; every judgment row judged 未判定 or 不适用 needs a
          note, every note must name an existing judgment row (ref = prediction_id or fc_id); the file is required
          only when such rows exist. The coverage link_basis is checked by coverage.validate (non-empty where
          required).

Subcommands
  ingest    runs the gate on every "ok" code and writes results/r<r>/<code>/gate.json (never rewritten; an existing
            file must hold the same bytes). The gate is injectable (Ctx(gate=...)); default: gate.gate(rtl_path,
            declared_L) -> GateResult(passed, hits, yosys_problem), hits with rule, line, kind, text (Task 4).
  evaluate  first recovers attempts that have started.json only (run_grade.recover), then, code by code (sorted),
            runs run_grade.attempt for every gate-passed code (vetoed ones included) until the code is terminal:
            attempt 1 when there is none, the one retry when attempt 1 is attributed "external" and did not end with
            GRADE OK (protocol 8). Before each attempt: open stops, disk and baseline are re-checked (a disk or
            baseline failure raises an eval stop). Stops at once, exit 1, on a refusal of run_grade, a stop raised by
            run_grade (KILL FAIL, cleanup, low disk after the run, infra_fail), DISK, BASELINE FAIL, or open_stops(r)
            becoming non-empty. Attempts run one after another in this process (limits.run_limited: one at a time).
            run_grade.attempt is called with locked=True and a no-op preflight: this process holds the eval lock for
            the whole evaluate and ran the full evaluate preflight once at the start (re-running it per attempt
            would re-run the gate each time); stops, disk and baseline are re-checked before every attempt.
  finalize  status.finalize_round -> compare matrix for the codes with sta_analysis "pass" -> judge.run ->
            (round 2) coverage.compute; stops at the first error (exit 1).
  close     writes revise/outputs/r<r>/round_complete.json: {round, time, states: {code: state}, author_review:
            {text, recorded_at}}.
After writing, the operator commits (diag_commit.sh); every stop raised prints the instruction to commit its record
now (ruling R12).

Roots are injectable for tests (Ctx): case (tasks/CASE-01), sealed (mapping), repo (run_grade env files), env,
free_bytes, base_root (baseline), gate, grade_cmd (code -> command list), prereg_problems, reused_problems.
Python standard library only; WSL (evaluate runs grade.py)."""
import contextlib
import datetime
import io
import json
import os
import re
import sys

import baseline
import limits
import mapping
import prereg
import revpaths as rp
import stops

STAGES = ("ingest", "evaluate", "finalize", "close")
FINALS = ("parse", "delivery_fail", "unavailable")
PARSED_STATES = ("ok", "declined", "delivery_fail")
REVIEW_COLUMNS = ("code", "符合合同", "理由", "否决条目", "合同条款", "RTL行号", "耗时分钟")
CONFORMS = ("是", "否", "不确定")
VETO_ITEMS = ("V1", "V2")
NOTE_WORDS = ("未判定", "不适用")
ROUNDS = (1, 2)


class RoundError(Exception):
    pass


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _default_gate(rtl_path, declared_L):
    import gate as gate_mod                           # Task 4 (revise/scripts/gate.py); lazy, injectable
    return gate_mod.gate(rtl_path, declared_L)


class Ctx:
    def __init__(self, case=None, sealed=None, repo=None, env=None, free_bytes=None, base_root=None, gate=None,
                 grade_cmd=None, prereg_problems=None, reused_problems=None):
        self.case = case or rp.CASE
        self.revise = os.path.join(self.case, "revise")
        self.sealed = sealed
        self.repo = repo
        self.env = env
        self.free_bytes = free_bytes
        self.base_root = base_root
        self.gate = gate or _default_gate
        self.grade_cmd = grade_cmd
        self.prereg_problems = prereg_problems or (lambda: prereg.problems("formal"))
        self.reused_problems = reused_problems or rp.reused_problems

    def rg_roots(self):
        return {"case": self.case, "repo": self.repo, "env": self.env, "free_bytes": self.free_bytes}

    # paths
    def out_dir(self, r):
        return os.path.join(self.revise, "outputs", f"r{r}")

    def cand_dir(self, r, code):
        return os.path.join(self.revise, "results", f"r{r}", code)

    def pred(self, name):
        return os.path.join(self.revise, "predictions", name)

    def rel(self, path):
        return os.path.relpath(path, self.case).replace(os.sep, "/")


# ------------------------------------------------------------------------------------------------ helpers
def _load(path):
    try:
        with open(path, "rb") as f:
            return json.loads(f.read().decode("utf-8"))
    except (OSError, ValueError):
        return None


def _quiet(fn, *args, **kw):
    """(return value, printed lines) of fn; its stdout is captured."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*args, **kw)
    return rc, [ln for ln in buf.getvalue().splitlines() if ln.strip()]


def _committed(ctx, path, probs, what=None):
    if not prereg.committed_unchanged(path):
        probs.append(f"NOT COMMITTED: {what or ctx.rel(path)} is missing, untracked or differs from HEAD")
        return False
    return True


def _held_by_me(ctx, r):
    """True when the eval lock of round r is held by this very process (pid, start time and platform)."""
    rec = _load(stops.lock_path(r, "eval", ctx.revise))
    return (isinstance(rec, dict) and rec.get("pid") == os.getpid() and rec.get("platform") == sys.platform
            and rec.get("start") == limits._start_time(os.getpid()))


def _codes(ctx, r):
    path = os.path.join(ctx.out_dir(r), "codes.txt")
    return [c.strip() for c in rp.read_bytes(path).decode("utf-8").splitlines() if c.strip()]


def _prev(ctx, r):
    """{round-r code: previous code} from the committed mapping (round >= 2), else None."""
    if r < 2:
        return None
    m = mapping.load(r, revise=ctx.revise, sealed=ctx.sealed)
    return {e["code"]: e["prev_code"] for e in m["entries"]}


def gate_doc(res):
    """gate.json content of a GateResult (object or dict): {passed, hits: [{rule, line, kind, text}], yosys_problem}."""
    def get(o, k):
        return o[k] if isinstance(o, dict) else getattr(o, k)
    passed = get(res, "passed")
    if not isinstance(passed, bool):
        raise RoundError(f"gate result: passed is {passed!r}, not a bool")
    hits = [{k: get(h, k) for k in ("rule", "line", "kind", "text")} for h in (get(res, "hits") or [])]
    return {"passed": passed, "hits": hits, "yosys_problem": get(res, "yosys_problem")}


def gate_bytes(res):
    return (json.dumps(gate_doc(res), indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def _stop(ctx, r, reason, code=None, details=None):
    sid = stops.raise_stop(r, "eval", reason, code, details, revise=ctx.revise)
    print(f"STOP {sid}: {reason} — commit revise/stops/r{r}/{sid}.json now", flush=True)
    return sid


# ------------------------------------------------------------------------------------------------ stage B
def _phase_b(ctx, r, codes, probs):
    """Checks of the stage-B products; returns {code: {"final", "parsed", "declared_L"}}."""
    info = {}
    od = ctx.out_dir(r)
    _committed(ctx, os.path.join(od, "attempts.json"), probs)
    _committed(ctx, os.path.join(od, "status.md"), probs)
    any_parsed = []
    for code in codes:
        e = info[code] = {"final": None, "parsed": None, "declared_L": None}
        p_call = os.path.join(od, f"{code}.call.json")
        if not _committed(ctx, p_call, probs):
            continue
        call = _load(p_call)
        final = call.get("final") if isinstance(call, dict) else None
        if final not in FINALS:
            probs.append(f"INGEST FAIL {code}: call.json final is {final!r}, not one of {'/'.join(FINALS)}")
            continue
        e["final"] = final
        if final in ("parse", "delivery_fail"):
            _committed(ctx, os.path.join(od, f"{code}.md"), probs)
        if final != "parse":
            continue
        p_parsed = os.path.join(od, f"{code}.parsed.json")
        if not _committed(ctx, p_parsed, probs):
            continue
        parsed = _load(p_parsed)
        status = parsed.get("status") if isinstance(parsed, dict) else None
        if status not in PARSED_STATES:
            probs.append(f"INGEST FAIL {code}: parsed.json status is {status!r}")
            continue
        e["parsed"] = status
        any_parsed.append(code)
        if status != "ok":
            continue
        cand = parsed.get("candidate")
        dl = parsed.get("declared_L")
        if not isinstance(cand, dict) or not isinstance(dl, int) or isinstance(dl, bool):
            probs.append(f"INGEST FAIL {code}: parsed.json of an ok answer lacks candidate / declared_L")
            continue
        e["declared_L"] = dl
        rtl_rel, cfg_rel = f"rtl/dot4sat_{code}.v", f"config/impl.{code}.cfg"
        if cand.get("rtl_path") != rtl_rel or cand.get("cfg_path") != cfg_rel:
            probs.append(f"INGEST FAIL {code}: parsed.json candidate paths are {cand.get('rtl_path')!r} / "
                         f"{cand.get('cfg_path')!r}, not {rtl_rel} / {cfg_rel}")
            continue
        rtl, cfg = os.path.join(ctx.case, *rtl_rel.split("/")), os.path.join(ctx.case, *cfg_rel.split("/"))
        ok_rtl = _committed(ctx, rtl, probs)
        ok_cfg = _committed(ctx, cfg, probs)
        if cand.get("rtl_sha_lf") != parsed.get("rtl_sha_lf") or cand.get("rtl_sha_raw") != parsed.get("rtl_sha_raw"):
            probs.append(f"INGEST FAIL {code}: parsed.json candidate hashes disagree with its rtl_sha_lf / rtl_sha_raw")
        if ok_rtl and rp.sha256(rtl) != parsed.get("rtl_sha_lf"):
            probs.append(f"INGEST FAIL {code}: {rtl_rel}: sha256 {rp.sha256(rtl)} != parsed.json rtl_sha_lf "
                         f"{parsed.get('rtl_sha_lf')} (the candidate changed)")
        if ok_cfg and rp.sha256(cfg) != cand.get("cfg_sha"):
            probs.append(f"INGEST FAIL {code}: {cfg_rel}: sha256 {rp.sha256(cfg)} != parsed.json cfg_sha "
                         f"{cand.get('cfg_sha')} (the candidate changed)")
    if any_parsed:
        p_ext = ctx.pred(f"r{r}_extracted.jsonl")
        if _committed(ctx, p_ext, probs):
            have = set()
            for ln in rp.read_bytes(p_ext).decode("utf-8", "replace").splitlines():
                try:
                    obj = json.loads(ln)
                except ValueError:
                    probs.append(f"INGEST FAIL: {ctx.rel(p_ext)} has a line that is not JSON")
                    continue
                if isinstance(obj, dict):
                    have.add(obj.get("code"))
            for code in any_parsed:
                if code not in have:
                    probs.append(f"INGEST FAIL {code}: {ctx.rel(p_ext)} has no row of this parsed code")
    return info


# ------------------------------------------------------------------------------------------------ stage C
def review_problems(text, codes, passed):
    """Problems of the author's review table (see module doc)."""
    probs = []
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    if not lines or tuple(lines[0].rstrip("\r").split("\t")) != REVIEW_COLUMNS:
        return [f"REVIEW FAIL: the header must be exactly: {' '.join(REVIEW_COLUMNS)} (tab separated)"]
    seen = {}
    for n, ln in enumerate(lines[1:], 2):
        cells = ln.rstrip("\r").split("\t")
        w = f"REVIEW FAIL: line {n}"
        if len(cells) != len(REVIEW_COLUMNS):
            probs.append(f"{w}: {len(cells)} cells, expected {len(REVIEW_COLUMNS)}")
            continue
        row = dict(zip(REVIEW_COLUMNS, (c.strip() for c in cells)))
        code = row["code"]
        if code not in codes:
            probs.append(f"{w}: code {code!r} is not a code of this round")
            continue
        seen[code] = seen.get(code, 0) + 1
        if row["符合合同"] not in CONFORMS:
            probs.append(f"{w}: 符合合同 is {row['符合合同']!r}, not one of {'/'.join(CONFORMS)}")
        if not row["理由"]:
            probs.append(f"{w}: 理由 is empty")
        veto = row["否决条目"]
        if veto:
            items = [t for t in re.split(r"[,、，\s]+", veto) if t]
            if not items or any(t not in VETO_ITEMS for t in items) or len(set(items)) != len(items):
                probs.append(f"{w}: 否决条目 is {veto!r}; only V1, V2 (one or both) or empty")
            if not row["合同条款"] or not row["RTL行号"]:
                probs.append(f"{w}: a veto needs 合同条款 and RTL行号")
        if not re.fullmatch(r"[0-9]+(\.[0-9]+)?", row["耗时分钟"]):
            probs.append(f"{w}: 耗时分钟 is {row['耗时分钟']!r}, not a non-negative number")
    for code in codes:
        k = seen.get(code, 0)
        if k > 1:
            probs.append(f"REVIEW FAIL: code {code} has {k} rows")
        elif k == 0 and code in passed:
            probs.append(f"REVIEW FAIL: gate-passed code {code} has no review row")
    return probs


def _phase_c(ctx, r, codes, info, probs):
    """Checks of the stage-C products; returns the gate-passed codes."""
    import judge                                      # local imports: pure modules, loaded only when needed
    passed = []
    for code in codes:
        if info[code]["parsed"] != "ok":
            continue
        p_gate = os.path.join(ctx.cand_dir(r, code), "gate.json")
        if not _committed(ctx, p_gate, probs):
            continue
        rtl = os.path.join(ctx.case, "rtl", f"dot4sat_{code}.v")
        try:
            again = gate_bytes(ctx.gate(rtl, info[code]["declared_L"]))
        except Exception as e:                        # ImportError (gate.py missing), gate failures
            probs.append(f"GATE FAIL {code}: the gate could not be re-run ({e.__class__.__name__}: {e})")
            continue
        if rp.read_bytes(p_gate) != again:
            probs.append(f"GATE FAIL {code}: gate.json differs from a re-run of the gate")
            continue
        if json.loads(again.decode("utf-8"))["passed"]:
            passed.append(code)
    p_rev = os.path.join(ctx.revise, "review", f"r{r}.tsv")
    if _committed(ctx, p_rev, probs):
        try:
            probs += review_problems(rp.read_bytes(p_rev).decode("utf-8"), codes, passed)
        except UnicodeDecodeError:
            probs.append(f"REVIEW FAIL: {ctx.rel(p_rev)} is not UTF-8")
    p_crit, p_tsv = ctx.pred(f"r{r}_criteria.jsonl"), ctx.pred(f"r{r}_criteria.tsv")
    ok = _committed(ctx, p_crit, probs) & _committed(ctx, p_tsv, probs)
    if r == 2:
        ok &= _committed(ctx, ctx.pred("r2_coverage.jsonl"), probs) & _committed(ctx, ctx.pred("r2_coverage.tsv"),
                                                                                  probs)
    if ok:
        rc, lines = _quiet(judge.views, r, check=True, case=ctx.case, prev=_prev(ctx, r))
        if rc:
            probs += [f"VIEWS FAIL: {ln}" for ln in lines] or ["VIEWS FAIL: judge views check failed"]
        else:
            crit = judge.read_jsonl(p_crit)
            have = {row.get("candidate") for row in crit}
            ext = ctx.pred(f"r{r}_extracted.jsonl")
            rows = judge.read_jsonl(ext) if os.path.isfile(ext) else []
            need = sorted({e.get("code") for e in rows if e.get("row_type") in ("prediction", "failure_condition")})
            for code in need:
                if code not in have:
                    probs.append(f"CRITERIA FAIL {code}: it has predictions or failure conditions but no criteria row")
    probs += baseline.verify(ctx.base_root)
    return passed


# ------------------------------------------------------------------------------------------------ stage D/E
def _passed_codes(ctx, r, codes):
    out = []
    for code in codes:
        g = _load(os.path.join(ctx.cand_dir(r, code), "gate.json"))
        if isinstance(g, dict) and g.get("passed") is True:
            out.append(code)
    return out


def _terminal_problems(ctx, r, passed):
    import run_grade
    import status
    probs = []
    for code in passed:
        dirs = run_grade.attempt_dirs(ctx.cand_dir(r, code))
        if not dirs:
            probs.append(f"FINALIZE FAIL {code}: no attempt (run evaluate first)")
            continue
        if any(not os.path.isfile(os.path.join(d, "attempt.json")) for _, d in dirs):
            probs.append(f"FINALIZE FAIL {code}: an attempt has started.json only (run evaluate: it recovers it)")
            continue
        state = status.build(code, r, case=ctx.case)["state"]
        if state == "await_retry":
            probs.append(f"AWAIT RETRY {code}: attempt 1 is attributed to an external fault and has no retry yet")
        elif state is None:
            probs.append(f"FINALIZE FAIL {code}: the state cannot be determined")
    return probs


def _sta_pass_codes(ctx, r, codes):
    out = []
    for code in codes:
        st = _load(os.path.join(ctx.cand_dir(r, code), "status.json"))
        if isinstance(st, dict) and st.get("sta_analysis") == "pass":
            out.append(code)
    return out


def _is_lock_file(name):
    return name == ".lock" or name.startswith(".lock.")


def notes_problems(judgments, notes_rows):
    probs = []
    rows = {}
    for j in judgments:
        ref = j.get("prediction_id") if j.get("row_type") == "prediction" else j.get("fc_id")
        rows[(j.get("candidate"), ref)] = j.get("judgment")
    have = set()
    for n, x in enumerate(notes_rows, 1):
        if not isinstance(x, dict) or not all(isinstance(x.get(k), str) for k in ("candidate", "ref", "note")) \
                or not x["note"].strip():
            probs.append(f"NOTES FAIL: line {n} needs string fields candidate, ref and a non-empty note")
            continue
        key = (x["candidate"], x["ref"])
        if key not in rows:
            probs.append(f"NOTES FAIL: line {n} names {x['ref']!r} of {x['candidate']}, which has no judgment row")
        have.add(key)
    for key, word in rows.items():
        if word in NOTE_WORDS and key not in have:
            probs.append(f"NOTES FAIL: judgment {key[1]!r} of {key[0]} is {word} and has no note")
    return probs


def _phase_d(ctx, r, codes, probs):
    import compare
    import coverage
    import judge
    import status
    if os.path.exists(os.path.join(ctx.out_dir(r), "round_complete.json")):
        probs.append(f"CLOSE FAIL: revise/outputs/r{r}/round_complete.json already exists (round already closed)")
        return
    res = os.path.join(ctx.revise, "results", f"r{r}")
    for base, dirs, files in os.walk(res):
        dirs.sort()
        for fn in sorted(files):
            if not _is_lock_file(fn):
                _committed(ctx, os.path.join(base, fn), probs)
    sta = _sta_pass_codes(ctx, r, codes)
    for code in sta:
        for ext in ("json", "md"):
            _committed(ctx, os.path.join(ctx.revise, "compare", f"r{r}_{code}.{ext}"), probs)
    p_j = ctx.pred(f"r{r}_judgments.jsonl")
    ok_j = _committed(ctx, p_j, probs) & _committed(ctx, ctx.pred(f"r{r}_judgments.md"), probs)
    if r == 2:
        _committed(ctx, ctx.pred("r2_coverage_result.json"), probs)
    if ok_j:
        p_n = ctx.pred(f"r{r}_notes.jsonl")
        try:
            judgments = judge.read_jsonl(p_j)
            need = any(j.get("judgment") in NOTE_WORDS for j in judgments)
            if os.path.exists(p_n) or need:
                if _committed(ctx, p_n, probs):
                    probs += notes_problems(judgments, judge.read_jsonl(p_n))
        except judge.JudgeError as e:
            probs.append(f"NOTES FAIL: {e}")
    if probs:
        return
    # recomputation in check mode: status -> compare -> judge -> coverage (judge before coverage)
    prev = _prev(ctx, r)
    steps = [("status", lambda: status.finalize_round(r, check=True, locked=True, case=ctx.case))]
    for code in sta:
        steps.append((f"compare {code}", lambda c=code: compare.write_matrix(c, r, check=True, case=ctx.case,
                                                                             base_root=ctx.base_root)))
    steps.append(("judge", lambda: judge.run(r, check=True, case=ctx.case, base_root=ctx.base_root, prev=prev)))
    if r == 2:
        steps.append(("coverage", lambda: coverage.compute(case=ctx.case, check=True, prev=prev)))
    for name, fn in steps:
        rc, lines = _quiet(fn)
        if rc:
            probs += [f"RECHECK FAIL ({name}): {ln}" for ln in lines] or [f"RECHECK FAIL ({name})"]


# ------------------------------------------------------------------------------------------------ preflight
def preflight(r, stage, ctx=None):
    """List of problems of round r before subcommand `stage` (see the module doc); empty means go."""
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}, not {stage!r}")
    ctx = ctx or Ctx()
    try:
        if _held_by_me(ctx, r):
            return _checks(ctx, r, stage)
        with stops.round_lock(r, "eval", revise=ctx.revise):
            return _checks(ctx, r, stage)
    except stops.LockError as e:
        return [str(e)]
    except (stops.StopsError, prereg.PreregError, rp.RevpathsError, OSError, UnicodeDecodeError) as e:
        return [f"PREFLIGHT FAIL: {e.__class__.__name__}: {e}"]


def _checks(ctx, r, stage):
    level = STAGES.index(stage)
    probs = []
    for s in stops.open_stops(r, revise=ctx.revise):
        probs.append(f"STOPPED: open stop {s.get('stop_id')} (side {s.get('side')}, {s.get('reason')}): "
                     f"{s.get('why_open')}")
    probs += ctx.prereg_problems()
    probs += ctx.reused_problems()
    probs += rp.disk_problems(free_bytes=ctx.free_bytes)
    try:
        mapping.load(r, revise=ctx.revise, sealed=ctx.sealed)
    except mapping.MappingError as e:
        probs.append(str(e))
        return probs
    codes_path = os.path.join(ctx.out_dir(r), "codes.txt")
    if not _committed(ctx, codes_path, probs):
        return probs
    codes = _codes(ctx, r)
    if probs:
        return probs
    info = _phase_b(ctx, r, codes, probs)
    if probs or level < 1:
        return probs
    passed = _phase_c(ctx, r, codes, info, probs)
    if probs or level < 2:
        return probs
    probs += _terminal_problems(ctx, r, passed)
    if probs or level < 3:
        return probs
    _phase_d(ctx, r, codes, probs)
    return probs


# ------------------------------------------------------------------------------------------------ status lines
def status_lines(ctx, r):
    """One line per code: codes, call/parse/gate/review/attempt facts and the status.json state; no model names."""
    try:
        codes = _codes(ctx, r)
    except (OSError, UnicodeDecodeError):
        return [f"r{r}: codes.txt cannot be read"]
    review = {}
    p_rev = os.path.join(ctx.revise, "review", f"r{r}.tsv")
    try:
        for ln in rp.read_bytes(p_rev).decode("utf-8").splitlines()[1:]:
            cells = ln.split("\t")
            if len(cells) >= 4:
                review[cells[0].strip()] = cells[3].strip() or "no_veto"
    except (OSError, UnicodeDecodeError):
        pass
    out = []
    for code in codes:
        call = _load(os.path.join(ctx.out_dir(r), f"{code}.call.json"))
        parsed = _load(os.path.join(ctx.out_dir(r), f"{code}.parsed.json"))
        gate = _load(os.path.join(ctx.cand_dir(r, code), "gate.json"))
        st = _load(os.path.join(ctx.cand_dir(r, code), "status.json"))
        attempts, last = 0, "-"
        cdir = ctx.cand_dir(r, code)
        if os.path.isdir(cdir):
            ks = sorted(int(n[7:]) for n in os.listdir(cdir) if re.fullmatch(r"attempt[1-9][0-9]*", n))
            attempts = len(ks)
            if ks:
                a = _load(os.path.join(cdir, f"attempt{ks[-1]}", "attempt.json"))
                if not isinstance(a, dict):
                    last = "unfinished"
                else:
                    fl = a.get("final_line") or ""
                    last = ("GRADE OK" if fl.startswith("GRADE OK:") else "GRADE FAIL" if fl.startswith("GRADE FAIL:")
                            else "no_final_line") + f"/{a.get('attribution')}"
        g = "-" if not isinstance(gate, dict) else ("passed" if gate.get("passed") is True else "rejected")
        out.append(f"CODE {code}: call={call.get('final') if isinstance(call, dict) else '-'} "
                   f"parsed={parsed.get('status') if isinstance(parsed, dict) else '-'} gate={g} "
                   f"review={review.get(code, '-')} attempts={attempts} last={last} "
                   f"state={st.get('state') if isinstance(st, dict) else '-'}")
    return out


# ------------------------------------------------------------------------------------------------ subcommands
def _refuse(probs):
    for p in probs:
        print(p, flush=True)
    print(f"REFUSED: {len(probs)} preflight problem(s); nothing was done", flush=True)
    return 1


def cmd_ingest(ctx, r):
    probs = preflight(r, "ingest", ctx)
    if probs:
        return _refuse(probs)
    written = []
    for code in _codes(ctx, r):
        parsed = _load(os.path.join(ctx.out_dir(r), f"{code}.parsed.json"))
        call = _load(os.path.join(ctx.out_dir(r), f"{code}.call.json"))
        if call.get("final") != "parse" or not isinstance(parsed, dict) or parsed.get("status") != "ok":
            continue
        rtl = os.path.join(ctx.case, "rtl", f"dot4sat_{code}.v")
        try:
            data = gate_bytes(ctx.gate(rtl, parsed["declared_L"]))
        except Exception as e:                        # ImportError (gate.py missing), gate failures
            print(f"GATE FAIL {code}: {e.__class__.__name__}: {e}", flush=True)
            return 1
        path = os.path.join(ctx.cand_dir(r, code), "gate.json")
        try:
            if rp.write_new_or_same(path, data):
                written.append(ctx.rel(path))
        except rp.RevpathsError:
            print(f"GATE FAIL {code}: {ctx.rel(path)} exists with different content; it is not rewritten", flush=True)
            return 1
    if written:
        print("commit now (stage C, gate records): " + " ".join(written), flush=True)
    return 0


def _noop_preflight(rnd, stage):
    """evaluate already ran the full preflight under the lock it holds (see the module doc)."""
    return []


def _next_attempt(ctx, r, code):
    """None (terminal), False (attempt 1) or True (the retry) for a gate-passed code."""
    import run_grade
    dirs = run_grade.attempt_dirs(ctx.cand_dir(r, code))
    if not dirs:
        return False
    att = _load(os.path.join(dirs[-1][1], "attempt.json"))
    if not isinstance(att, dict):
        raise RoundError(f"{code}: attempt{dirs[-1][0]} has no attempt.json after recovery")
    if len(dirs) == 1 and att.get("attribution") == "external" and \
            not str(att.get("final_line") or "").startswith("GRADE OK:"):
        return True
    return None


def _open_stop_lines(ctx, r):
    return [f"STOPPED: open stop {s.get('stop_id')} (side {s.get('side')}, {s.get('reason')})"
            for s in stops.open_stops(r, revise=ctx.revise)]


def cmd_evaluate(ctx, r):
    import run_grade
    probs = preflight(r, "evaluate", ctx)
    if probs:
        return _refuse(probs)
    codes = _codes(ctx, r)
    passed = _passed_codes(ctx, r, codes)
    roots = ctx.rg_roots()
    # 1. recover attempts that have started.json only
    for code in passed:
        dirs = run_grade.attempt_dirs(ctx.cand_dir(r, code))
        if any(not os.path.isfile(os.path.join(d, "attempt.json")) for _, d in dirs):
            try:
                for rec in run_grade.recover(code, r, locked=True, **roots):
                    print(f"RECOVERED {code} attempt{rec['k']}: attribution={rec['attribution']}", flush=True)
            except run_grade.RunGradeError as e:
                print(str(e), flush=True)
                return 1
            lines = _open_stop_lines(ctx, r)
            if lines:
                return _refuse(lines)
    # 2. attempts, one after another
    for code in passed:
        while True:
            try:
                retry = _next_attempt(ctx, r, code)
            except RoundError as e:
                print(f"EVALUATE FAIL: {e}", flush=True)
                return 1
            if retry is None:
                break
            lines = _open_stop_lines(ctx, r)
            if lines:
                return _refuse(lines)
            disk = rp.disk_problems(free_bytes=ctx.free_bytes)
            if disk:
                _stop(ctx, r, "DISK: 可用空间不足，不开始新的正式运行", code, {"problems": disk})
                return 1
            base = baseline.verify(ctx.base_root)
            if base:
                _stop(ctx, r, "BASELINE FAIL", code, {"problems": base})
                return 1
            cmd = ctx.grade_cmd(code) if ctx.grade_cmd else None
            try:
                rec = run_grade.attempt(code, r, retry=retry, grade_cmd=cmd, locked=True,
                                        preflight=_noop_preflight, **roots)
            except run_grade.RunGradeError as e:
                print(str(e), flush=True)
                return 1
            print(f"ATTEMPT {code} attempt{rec['k']}: {rec['final_line'] or 'no final line'} | "
                  f"location={rec['failure_location']} | attribution={rec['attribution']}", flush=True)
            if rec["stops"]:
                return 1
            lines = _open_stop_lines(ctx, r)
            if lines:
                return _refuse(lines)
    print("evaluate done; next: round.py finalize, then commit the stage-D products", flush=True)
    return 0


def cmd_finalize(ctx, r):
    import compare
    import coverage
    import judge
    import status
    probs = preflight(r, "finalize", ctx)
    if probs:
        return _refuse(probs)
    codes = _codes(ctx, r)
    if status.finalize_round(r, locked=True, case=ctx.case):
        print("FINALIZE FAIL: status (stopped at the first error)", flush=True)
        return 1
    for code in _sta_pass_codes(ctx, r, codes):
        if compare.write_matrix(code, r, case=ctx.case, base_root=ctx.base_root):
            print(f"FINALIZE FAIL: compare matrix {code} (stopped at the first error)", flush=True)
            return 1
    prev = _prev(ctx, r)
    if judge.run(r, case=ctx.case, base_root=ctx.base_root, prev=prev):
        print("FINALIZE FAIL: judge (stopped at the first error)", flush=True)
        return 1
    if r == 2 and coverage.compute(case=ctx.case, prev=prev):
        print("FINALIZE FAIL: coverage (stopped at the first error)", flush=True)
        return 1
    print(f"finalize done; write revise/predictions/r{r}_notes.jsonl where needed, then commit the stage-D "
          f"products (results/r{r}/, compare/r{r}_*, predictions/r{r}_judgments.*"
          f"{', r2_coverage_result.json' if r == 2 else ''}) before close", flush=True)
    return 0


def cmd_close(ctx, r, author_review):
    if not author_review or not author_review.strip():
        print("REFUSED: --author-review must say what the author actually looked at", flush=True)
        return 1
    probs = preflight(r, "close", ctx)
    if probs:
        return _refuse(probs)
    states = {}
    for code in _codes(ctx, r):
        st = _load(os.path.join(ctx.cand_dir(r, code), "status.json"))
        states[code] = st.get("state") if isinstance(st, dict) else None
    now = _now()
    doc = {"round": r, "time": now, "states": states,
           "author_review": {"text": author_review.strip(), "recorded_at": now}}
    path = os.path.join(ctx.out_dir(r), "round_complete.json")
    with open(path, "xb") as f:
        f.write((json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"round {r} closed; commit {ctx.rel(path)} now", flush=True)
    return 0


def run(sub, r, ctx, author_review=None):
    """Run subcommand `sub` of round r under the eval lock; prints the status lines at the end. Returns the exit
    code."""
    try:
        with stops.round_lock(r, "eval", revise=ctx.revise):
            try:
                if sub == "ingest":
                    return cmd_ingest(ctx, r)
                if sub == "evaluate":
                    return cmd_evaluate(ctx, r)
                if sub == "finalize":
                    return cmd_finalize(ctx, r)
                return cmd_close(ctx, r, author_review)
            finally:
                for ln in status_lines(ctx, r):
                    print(ln, flush=True)
    except stops.LockError as e:
        print(str(e), flush=True)
        return 1
    except (stops.StopsError, prereg.PreregError, mapping.MappingError, rp.RevpathsError, RoundError, OSError) as e:
        print(f"{sub.upper()} FAIL: {e.__class__.__name__}: {e}", flush=True)
        return 1


def main(argv=None, **roots):
    args = list(sys.argv[1:] if argv is None else argv)
    review = None
    if "--author-review" in args:
        i = args.index("--author-review")
        if i + 1 >= len(args):
            print("usage: --author-review needs a text", file=sys.stderr)
            return 2
        review = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2 or args[0] not in STAGES or args[1] not in ("1", "2") or \
            (review is not None and args[0] != "close"):
        print('usage: round.py ingest|evaluate|finalize <r> | round.py close <r> --author-review "<text>"   '
              '(<r> is 1 or 2)', file=sys.stderr)
        return 2
    return run(args[0], int(args[1]), Ctx(**roots), author_review=review)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
