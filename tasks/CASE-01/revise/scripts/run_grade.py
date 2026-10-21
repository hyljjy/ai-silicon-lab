"""Formal evaluation wrapper of CASE-01 stage B (implementation plan Task 5; protocol v0.4 sections 8, 12.3, 16).

One call of attempt() is one attempt k of one candidate: revise/results/r<rnd>/<code>/attempt<k>/ gets
  started.json  before grade.py starts (code rnd k cmd start disk_before dependency_check); never rewritten;
  stdout.txt, stderr.txt  grade.py's output, appended chunk by chunk while it runs (limits.run_limited);
  proc.json     lifecycle record (limits), plus "run_id" as soon as the first stdout line RUN_ID=<id> is read;
  copies of the files grade.py produced (protocol 12.3) at their run-directory relative paths;
  attempt.json  the result (fields: ATTEMPT_FIELDS); never rewritten.
At most two attempts per candidate; the second only with --retry and only when attempt 1 is attributed "external"
(protocol 8). Only WSL runs it (the frozen grade.py, no --allow-tool-drift).

Attribution uses structured evidence only (never log text): env_snapshot/versions step failed; launch error (grade.py
never ran: Popen failed / ISOLATION FAIL); a supervision failure after grade.py had started (limits.SupervisionError:
lifecycle record or output file write failed, ...; recorded as supervision_error, never as launch_error; the files
already produced are archived); a dependency missing before the start or after the run; an interrupt the wrapper did
not send (exit 143/130/negative or a step's "interrupted" key, with signals_sent empty); the wrapper itself interrupted
(recovery: a lifecycle record exists, the wrapper is gone, and the record is neither ended nor aborted; ruling R17
narrowed by Codex BC1-03). A timeout and the wrapper's own SIGTERM are no evidence.

Stops (stops.raise_stop, side "eval"; the operator commits the record at once, ruling R12): second attempt still an
external fault (infra_fail) or still without a final line; KILL FAIL; cleanup_unconfirmed (also when a supervision
failure's emergency cleanup failed, and on recovery when proc.json itself records alive_after / cleanup_unconfirmed);
recovery cannot confirm that the old processes exited (no usable proc.json included); low disk after the run.

Target eligibility (Codex BC1-06): before anything of an attempt is created (and before recovery), the shared check
round.target_problems(rnd, code) must pass: the code is in this round's codes.txt, its call ended in "parse" with
parsed status "ok" and an unchanged committed candidate, gate.json is committed with passed true, the review row and
(where predictions / failure conditions exist) criteria rows exist. round.py evaluate runs the same check (it passes
it explicitly); otherwise the default builds round.Ctx(case=<case>).

Stops after recovery (Codex BC1-07): every stop raised while recovering an earlier attempt refuses the run; open stops
and both disks are then checked again before the next started.json. A disk measurement whose process cleanup failed
(revpaths.kill_fail_problems) raises a KILL FAIL stop, before the attempt (no attempt directory) or after the run.

Roots are injectable for tests: case (tasks/CASE-01; revise = case/revise), repo (env/ hash files), env (environment of
the dependency check and of grade.py), free_bytes (revpaths.disk_problems), preflight (round.preflight, Task 11),
eligibility (callable(rnd, code) -> problems; default round.target_problems).
The proc.json run_id goes through limits.run_limited(proc_extra=...); proc.json also records the wrapper's own
signals_sent and timed_out (limits), which recovery uses: an interrupt is external evidence only when the record
shows that the wrapper sent no signal; a record without that information (older format) gives no such evidence.
Recovery cannot know the exit code, nor (old records) timed_out / over_limit: they are written as "unknown".

Command line (WSL, from tasks/CASE-01):  python3 -B revise/scripts/run_grade.py <code> <rnd> [--retry]"""
import datetime
import glob
import json
import os
import re
import shutil
import sys

import limits
import revpaths as rp
import stops

ATTEMPT_FIELDS = ("code rnd k cmd start end exit_code timed_out over_limit signals_sent launch_error supervision_error "
                  "run_id final_line final_line_missing failure_location attribution attribution_evidence disk_before "
                  "disk_after dependency_after files").split()
TOOLS = ("iverilog", "vvp", "yosys", "sta", "python3")
GL_MODELS = ("primitives.v", "sky130_fd_sc_hd.v")                     # grade.py:38, 624-629
STD = ("tt_025C_1v80", "tt_100C_1v80", "ss_100C_1v60", "ss_n40C_1v60", "ff_n40C_1v95", "ff_100C_1v95")
RUN_FILES = ("verdict.json", "steps.json", "inputs.sha256")
CODE_RE = re.compile(r"^cand_[a-z0-9]{4}$")
RUN_ID_RE = re.compile(r"^RUN_ID=([A-Za-z0-9][A-Za-z0-9._+-]*)$")
FINAL_RE = re.compile(r"^GRADE (OK|FAIL): ")
ATTEMPT_DIR_RE = re.compile(r"^attempt([1-9][0-9]*)$")
RECOVERED = "由包装器恢复"
WRAPPER_INTERRUPTED = "wrapper_interrupted"
SIGNALS_UNKNOWN = "wrapper signals unknown (recovered)"
UNKNOWN = "unknown"


class RunGradeError(Exception):
    pass


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


class _Ctx:
    def __init__(self, case=None, repo=None, env=None, free_bytes=None, preflight=None, eligibility=None):
        self.case = case or rp.CASE
        self.revise = os.path.join(self.case, "revise")
        self.repo = repo or rp.REPO
        self.env = dict(os.environ) if env is None else env
        self.free_bytes = free_bytes
        self.preflight = preflight or _default_preflight
        self.eligibility = eligibility or (lambda rnd, code: _default_eligibility(self.case, rnd, code))


def _default_preflight(rnd, step):
    import round as round_py                          # Task 11 writes revise/scripts/round.py
    return round_py.preflight(rnd, step)


def _default_eligibility(case, rnd, code):
    import round as round_py                          # the check shared with round.py evaluate (Codex BC1-06)
    return round_py.target_problems(rnd, code, round_py.Ctx(case=case))


def cand_dir(ctx, rnd, code):
    return os.path.join(ctx.revise, "results", f"r{rnd}", code)


def attempt_dirs(cdir):
    """[(k, path)] of attempt<k>/ directories holding a started.json (only those count as attempts), by k."""
    out = []
    if os.path.isdir(cdir):
        for name in os.listdir(cdir):
            m = ATTEMPT_DIR_RE.match(name)
            if m and os.path.isfile(os.path.join(cdir, name, "started.json")):
                out.append((int(m.group(1)), os.path.join(cdir, name)))
    return sorted(out)


def _dump(obj):
    return (json.dumps(obj, indent=1, ensure_ascii=False, default=str) + "\n").encode("utf-8")


def _write_once(path, obj):
    """Write-once JSON (started.json, attempt.json): an existing file is never rewritten (RevpathsError)."""
    return rp.write_new_or_same(path, _dump(obj))


def _load_json(path):
    try:
        with open(path, "rb") as f:
            return json.loads(f.read().decode("utf-8"))
    except (OSError, ValueError):
        return None


# ------------------------------------------------------------------------------------- dependencies and disk
def dependency_check(env, repo=None):
    """Every item {name, path, exists}: the tools on PATH, $SKY130_KIT and its MANIFEST.txt, the two gate-level models
    under $SKY130_HD/verilog, the six std-corner Liberty files of F1 under $SKY130_HD/lib, env/SHA256SUMS and
    env/tools.sha256 (grade.py env_ids)."""
    repo = repo or rp.REPO
    items = []
    for tool in TOOLS:
        p = shutil.which(tool, path=env.get("PATH", ""))
        items.append({"name": tool, "path": p or f"{tool} (not on PATH)", "exists": p is not None})

    def add(name, var, rel, isdir=False):
        base = env.get(var)
        if not base:
            items.append({"name": name, "path": f"${var} (unset)", "exists": False})
            return
        path = os.path.join(base, *rel) if rel else base
        items.append({"name": name, "path": path, "exists": os.path.isdir(path) if isdir else os.path.isfile(path)})

    add("$SKY130_KIT", "SKY130_KIT", (), isdir=True)
    add("$SKY130_KIT/MANIFEST.txt", "SKY130_KIT", ("MANIFEST.txt",))
    for m in GL_MODELS:
        add(f"$SKY130_HD/verilog/{m}", "SKY130_HD", ("verilog", m))
    for c in STD:
        add(f"liberty {c}", "SKY130_HD", ("lib", f"sky130_fd_sc_hd__{c}.lib"))
    for rel in ("env/SHA256SUMS", "env/tools.sha256"):
        path = os.path.join(repo, *rel.split("/"))
        items.append({"name": rel, "path": path, "exists": os.path.isfile(path)})
    return {"time": _now(), "ok": all(i["exists"] for i in items), "items": items}


def _disk(ctx):
    """One measurement of both volumes: {time, min_gib, free_bytes: {volume: bytes|None}, problems}."""
    seen = {}

    def measure(vol):
        if ctx.free_bytes is None:
            v = rp._measure_free(vol)
        elif callable(ctx.free_bytes):
            v = ctx.free_bytes(vol)
        else:
            v = ctx.free_bytes[vol]
        seen[vol] = v
        return v

    when = _now()
    problems = rp.disk_problems(free_bytes=measure)
    return {"time": when, "min_gib": 20, "free_bytes": {v: seen.get(v) for v in rp.DISK_VOLUMES},
            "problems": problems}


def _disk_or_refuse(ctx, rnd, code):
    """A disk measurement before an attempt: KILL FAIL (the measurement's cleanup failed) raises a stop and refuses;
    any other problem refuses. Returns the measurement."""
    disk = _disk(ctx)
    kill = rp.kill_fail_problems(disk["problems"])
    if kill:
        sid = _stop(ctx, rnd, "KILL FAIL", code, {"source": "disk measurement before an attempt", "problems": kill})
        raise RunGradeError(f"STOP {sid}: KILL FAIL in the disk measurement before an attempt of {code}: "
                            + "; ".join(kill))
    if disk["problems"]:
        raise RunGradeError("REFUSED: " + "; ".join(disk["problems"]))
    return disk


# ------------------------------------------------------------------------------------- location and attribution
def _bad_step(s):
    return s.get("returncode") != 0 or bool(s.get("timed_out")) or bool(s.get("interrupted")) \
        or bool(s.get("log_problems"))


def failure_location(steps, final_line):
    """First step with returncode != 0, timed_out, a non-empty "interrupted" or non-empty log_problems; otherwise
    "outside_steps" (GRADE FAIL line), "no_final_line" (no final line) or "none" (success)."""
    for s in steps or []:
        if isinstance(s, dict) and _bad_step(s):
            return str(s.get("step"))
    if final_line and final_line.startswith("GRADE FAIL:"):
        return "outside_steps"
    if not final_line:
        return "no_final_line"
    return "none"


def attribution(attempt, steps):
    """("external" | "no_external_evidence", evidence). attempt: the attempt record, plus "dependency_check" (the
    check before the start, from started.json) and, for recovery, "wrapper_interrupted": True and
    "wrapper_signals_unknown": True (the lifecycle record does not say which signals the wrapper sent: then neither
    the exit code nor a step's "interrupted" key counts as an external interrupt)."""
    ev = []
    for s in steps or []:
        if isinstance(s, dict) and s.get("step") in ("env_snapshot", "versions") and s.get("returncode") != 0:
            ev.append(f"{s['step']}_failed: returncode={s.get('returncode')}")
    le = attempt.get("launch_error")
    if le:
        ev.append(f"launch_error: {le.get('type')} errno={le.get('errno')}")
    se = attempt.get("supervision_error")
    if se:
        ev.append(f"supervision_error: {se.get('type')} errno={se.get('errno')}")
    before = attempt.get("dependency_check")
    after = attempt.get("dependency_after")
    if before is not None and not before.get("ok"):
        ev += [f"dependency_missing_before_start: {i['path']}" for i in before["items"] if not i["exists"]]
    elif after is not None and not after.get("ok"):
        ev += [f"dependency_missing_after_run: {i['path']}" for i in after["items"] if not i["exists"]]
    if not attempt.get("signals_sent") and not attempt.get("wrapper_signals_unknown"):
        ec = attempt.get("exit_code")
        if isinstance(ec, int) and not isinstance(ec, bool) and (ec in (143, 130) or ec < 0):
            ev.append(f"external_interrupt: exit_code={ec} and the wrapper sent no signal")
        for s in steps or []:
            if isinstance(s, dict) and s.get("interrupted"):
                ev.append(f"external_interrupt: step {s.get('step')} interrupted ({s['interrupted']}) and the "
                          f"wrapper sent no signal")
    if attempt.get("wrapper_interrupted"):
        ev.append(WRAPPER_INTERRUPTED)
    return ("external" if ev else "no_external_evidence"), ev


# ------------------------------------------------------------------------------------- stdout, files, stops
def _stdout_text(adir):
    try:
        return rp.read_bytes(os.path.join(adir, "stdout.txt")).decode("utf-8", "replace")
    except OSError:
        return None


def _first_run_id(text):
    if not text:
        return None
    m = RUN_ID_RE.match(text.split("\n", 1)[0].rstrip("\r"))
    return m.group(1) if m else None


def _final_line(text):
    """The last stdout line when it is complete (ends with a newline) and starts with 'GRADE OK: '/'GRADE FAIL: '."""
    if not text or not text.endswith("\n"):
        return None
    last = text[:-1].split("\n")[-1].rstrip("\r")
    return last if FINAL_RE.match(last) else None


def _safe_rel(rel):
    parts = rel.replace("\\", "/").split("/")
    return bool(rel) and not os.path.isabs(rel) and ".." not in parts and "" not in parts


def _archive(adir, run_dir, run_id, started_ok, final_line):
    """Copy what grade.py produced (protocol 12.3) into adir; returns (files, steps)."""
    files = []

    def entry(path, state, reason=None):
        sha = rp.sha256(os.path.join(adir, *path.split("/"))) if state in ("produced", "invalid") and \
            os.path.isfile(os.path.join(adir, *path.split("/"))) else None
        files.append({"path": path, "state": state, "reason": reason, "sha256": sha})

    def copy(rel, kind=None):
        if not _safe_rel(rel):
            entry(rel, "invalid", "unsafe path in steps.json; not copied")
            return
        src = os.path.join(run_dir, *rel.split("/"))
        if not os.path.isfile(src):
            entry(rel, "missing", f"not in runs/{run_id}/ (grade.py did not write it)")
            return
        dst = os.path.join(adir, *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        if kind is not None and not isinstance(_load_json(dst), kind):
            entry(rel, "invalid", f"not valid JSON ({kind.__name__} expected)")
            return
        entry(rel, "produced")

    for n in ("stdout.txt", "stderr.txt"):
        if not started_ok:
            entry(n, "not_run", "grade.py was not started")
        elif os.path.isfile(os.path.join(adir, n)):
            entry(n, "produced")
        else:
            entry(n, "missing", "the wrapper did not write it")
    if not started_ok or not run_id:
        why = "grade.py was not started" if not started_ok else \
            "no RUN_ID line: grade.py did not create a run directory"
        for n in RUN_FILES:
            entry(n, "not_run", why)
        entry("sta/", "not_run", why)
        return files, None
    if not os.path.isdir(run_dir):
        for n in RUN_FILES:
            entry(n, "missing", f"run directory runs/{run_id}/ not found")
        entry("sta/", "missing", f"run directory runs/{run_id}/ not found")
        return files, None
    copy("verdict.json", dict)
    copy("steps.json", list)
    copy("inputs.sha256")
    steps = _load_json(os.path.join(adir, "steps.json"))
    steps = steps if isinstance(steps, list) else None
    verdict = _load_json(os.path.join(adir, "verdict.json"))
    loc = failure_location(steps, final_line)
    for s in steps or []:
        if isinstance(s, dict) and s.get("step") == loc:
            for rel in s.get("logs") or []:
                if isinstance(rel, str):
                    copy(rel)
            break
    if isinstance(verdict, dict) and verdict.get("analysis_valid") is True:
        copy("sta/sta_results.tsv")
        copy("sta/sta_check.json", dict)
        cats = sorted(glob.glob(os.path.join(glob.escape(run_dir), "sta", "cat_*.rpt")))
        if not cats:
            entry("sta/cat_*.rpt", "missing", f"no sta/cat_*.rpt in runs/{run_id}/")
        for p in cats:
            copy("sta/" + os.path.basename(p))
        for kind in ("max", "min"):
            for c in STD:
                copy(f"sta/path_{kind}_{c}.rpt")
    else:
        entry("sta/", "not_run", "sta_analysis is not pass (verdict.json analysis_valid is not true)")
    return files, steps


def _stop(ctx, rnd, reason, code, details):
    stop_id = stops.raise_stop(rnd, "eval", reason, code, details, revise=ctx.revise)
    print(f"STOP {stop_id}: {reason} — commit revise/stops/r{rnd}/{stop_id}.json now", flush=True)
    return stop_id


def _finish(ctx, code, rnd, k, adir, started, info, recovered=False, wrapper_interrupted=False):
    """Write attempt.json from the files on disk and the run information; raise the stops it calls for."""
    started_ok = not info.get("not_started") and not info.get("launch_error")
    text = _stdout_text(adir) if started_ok else None
    proc = _load_json(os.path.join(adir, "proc.json")) or {}
    run_id = proc.get("run_id") or _first_run_id(text)
    if run_id is not None and not RUN_ID_RE.match(f"RUN_ID={run_id}"):
        run_id = None
    final_line = None if wrapper_interrupted else _final_line(text)
    dep_after = dependency_check(ctx.env, ctx.repo) if not info.get("not_started") else None
    disk_after = _disk(ctx)
    run_dir = os.path.join(ctx.case, "runs", run_id) if run_id else None
    files, steps = _archive(adir, run_dir, run_id, started_ok, final_line)
    def flag(v):
        return v if v == UNKNOWN else bool(v)

    rec = {"code": code, "rnd": rnd, "k": k, "cmd": started["cmd"], "start": started["start"], "end": _now(),
           "exit_code": info.get("exit_code"), "timed_out": flag(info.get("timed_out")),
           "over_limit": flag(info.get("over_limit")), "signals_sent": list(info.get("signals_sent") or []),
           "launch_error": info.get("launch_error"), "supervision_error": info.get("supervision_error"),
           "run_id": run_id, "final_line": final_line,
           "final_line_missing": final_line is None,
           "failure_location": failure_location(steps, final_line), "attribution": None,
           "attribution_evidence": None, "disk_before": started.get("disk_before"), "disk_after": disk_after,
           "dependency_after": dep_after, "files": files}
    attr, ev = attribution(dict(rec, dependency_check=started.get("dependency_check"),
                                wrapper_interrupted=wrapper_interrupted,
                                wrapper_signals_unknown=bool(info.get("signals_unknown"))), steps)
    # the notes below are not evidence (attr is already decided)
    if wrapper_interrupted and _final_line(text):
        ev.append("stdout has a final line but runs/<RUN_ID>/steps.json is missing")
    if info.get("signals_unknown"):
        ev.append(SIGNALS_UNKNOWN)
    if recovered:
        ev.append(RECOVERED)
    rec["attribution"], rec["attribution_evidence"] = attr, ev
    # attempt.json first: a failure while raising the stops can never make recovery rewrite this attempt
    _write_once(os.path.join(adir, "attempt.json"), rec)

    raised = []
    kill = info.get("kill") or {}
    if kill.get("alive"):
        raised.append(_stop(ctx, rnd, "KILL FAIL", code, {"attempt": k, "alive": kill["alive"]}))
    if kill.get("unconfirmed"):
        raised.append(_stop(ctx, rnd, "cleanup_unconfirmed", code, {"attempt": k}))
    disk_kill = rp.kill_fail_problems(disk_after["problems"])
    if disk_kill:
        raised.append(_stop(ctx, rnd, "KILL FAIL", code, {"attempt": k, "source": "disk measurement after the run",
                                                          "problems": disk_kill}))
    disk_rest = [p for p in disk_after["problems"] if p not in disk_kill]
    if disk_rest:
        raised.append(_stop(ctx, rnd, "运行后磁盘不足", code,
                            {"attempt": k, "time": disk_after["time"], "free_bytes": disk_after["free_bytes"],
                             "problems": disk_rest}))
    ok = bool(final_line and final_line.startswith("GRADE OK:"))
    if k >= 2 and not ok and (attr == "external" or final_line is None):
        raised.append(_stop(ctx, rnd, "infra_fail: the second attempt is still an external fault or still has no "
                                      "final line", code, {"attempt": k, "attribution_evidence": ev}))
    return dict(rec, stops=raised)


# ------------------------------------------------------------------------------------- one attempt
def _launch(ctx, cmd, adir):
    proc_path = os.path.join(adir, "proc.json")
    extra = {}                                        # limits proc_extra: added to every save of proc.json
    state = {"first": False}

    def on_line(line):
        if state["first"]:
            return False
        state["first"] = True
        m = RUN_ID_RE.match(line)
        if m:
            extra["run_id"] = m.group(1)
            return True                               # save proc.json now
        return False

    try:
        res = limits.run_limited(cmd, "grade", cwd=ctx.case, env=ctx.env,
                                 stdout_path=os.path.join(adir, "stdout.txt"),
                                 stderr_path=os.path.join(adir, "stderr.txt"), proc_path=proc_path, on_line=on_line,
                                 proc_extra=extra)
    except limits.SupervisionError as e:
        # grade.py had started: not a launch error; what it produced is archived, the cleanup result decides the stop
        cause = e.__cause__
        return {"supervision_error": {"type": e.cause_type, "errno": getattr(cause, "errno", None)},
                "exit_code": e.rc, "timed_out": e.timed_out, "over_limit": bool(e.stdout_over or e.stderr_over),
                "signals_sent": list(e.signals_sent),
                "kill": {"alive": list(e.killed_pids_alive), "unconfirmed": bool(e.cleanup_unconfirmed)}}
    except limits.IsolationFail as e:
        return {"launch_error": {"errno": None, "type": "IsolationFail", "message": str(e)}}
    except OSError as e:
        return {"launch_error": {"errno": e.errno, "type": type(e).__name__}}
    return {"exit_code": res.rc, "timed_out": res.timed_out,
            "over_limit": bool(res.stdout_over or res.stderr_over or res.output_error),
            "signals_sent": list(res.signals_sent),
            "kill": {"alive": list(res.killed_pids_alive), "unconfirmed": bool(res.cleanup_unconfirmed)}}


def attempt(code, rnd, retry=False, grade_cmd=None, locked=False, **roots):
    """Run attempt k of candidate `code` in round `rnd` (see the module doc); returns the attempt record (plus
    "stops": the stop ids raised). Refusals raise RunGradeError and leave no attempt directory behind."""
    if not CODE_RE.match(code or ""):
        raise RunGradeError(f"REFUSED: {code!r} is not a candidate code (cand_<4 lowercase letters or digits>)")
    ctx = _Ctx(**roots)
    if locked:
        return _attempt(ctx, code, rnd, retry, grade_cmd)
    with stops.round_lock(rnd, "eval", revise=ctx.revise):
        return _attempt(ctx, code, rnd, retry, grade_cmd)


def _refuse_open_stops(ctx, rnd):
    open_ = stops.open_stops(rnd, revise=ctx.revise)
    if open_:
        raise RunGradeError("REFUSED: open stop records in round %d: %s" % (
            rnd, ", ".join(f"{s['stop_id']} ({s.get('reason')})" for s in open_)))


def _attempt(ctx, code, rnd, retry, grade_cmd):
    _refuse_open_stops(ctx, rnd)
    probs = ctx.preflight(rnd, "evaluate")
    if probs:
        raise RunGradeError("REFUSED: " + "; ".join(probs))
    probs = ctx.eligibility(rnd, code)               # shared target check (Codex BC1-06), before anything is created
    if probs:
        raise RunGradeError("REFUSED: " + "; ".join(probs))
    disk = _disk_or_refuse(ctx, rnd, code)
    cdir = cand_dir(ctx, rnd, code)
    if any(not os.path.isfile(os.path.join(a, "attempt.json")) for _, a in attempt_dirs(cdir)):
        # Codex BC1-07: a stop raised while recovering refuses the run; stops and disks are checked again
        raised = [sid for rec in _recover(ctx, code, rnd) for sid in rec.get("stops") or []]
        if raised:
            raise RunGradeError(f"REFUSED: recovering {code} raised stop(s) {', '.join(raised)}; no further attempt "
                                f"is started")
        _refuse_open_stops(ctx, rnd)
        disk = _disk_or_refuse(ctx, rnd, code)
    done = attempt_dirs(cdir)
    if len(done) >= 2:
        raise RunGradeError(f"REFUSED: {code} already has two attempts (protocol 8: at most two)")
    if len(done) == 1:
        first = _load_json(os.path.join(done[0][1], "attempt.json")) or {}
        if not retry:
            raise RunGradeError(f"REFUSED: {code} already has attempt 1; a second attempt needs --retry and an "
                                f"external-fault attribution of attempt 1")
        if first.get("attribution") != "external":
            raise RunGradeError(f"REFUSED: attempt 1 of {code} is attributed {first.get('attribution')!r}; a retry "
                                f"needs external-fault evidence (protocol 8)")
        if str(first.get("final_line") or "").startswith("GRADE OK:"):
            raise RunGradeError(f"REFUSED: attempt 1 of {code} ended with GRADE OK; nothing to retry")
    elif retry:
        raise RunGradeError(f"REFUSED: --retry, but {code} has no first attempt")
    k = len(done) + 1
    adir = os.path.join(cdir, f"attempt{k}")
    os.makedirs(adir, exist_ok=True)
    cmd = list(grade_cmd) if grade_cmd else ["python3", "-B", "scripts/grade.py", "--impl",
                                             f"config/impl.{code}.cfg"]
    dep = dependency_check(ctx.env, ctx.repo)
    started = {"code": code, "rnd": rnd, "k": k, "cmd": cmd, "start": _now(), "disk_before": disk,
               "dependency_check": dep}
    _write_once(os.path.join(adir, "started.json"), started)
    info = {"not_started": True} if not dep["ok"] else _launch(ctx, cmd, adir)
    return _finish(ctx, code, rnd, k, adir, started, info)


# ------------------------------------------------------------------------------------- recovery
def recover(code, rnd, locked=False, **roots):
    """Complete every attempt of `code` that has started.json but no attempt.json (the wrapper died). Returns the
    records written. Raises RunGradeError after writing a stop when the old processes cannot be confirmed gone."""
    ctx = _Ctx(**roots)
    if locked:
        return _recover(ctx, code, rnd)
    with stops.round_lock(rnd, "eval", revise=ctx.revise):
        return _recover(ctx, code, rnd)


def _recover(ctx, code, rnd):
    out = []
    for k, adir in attempt_dirs(cand_dir(ctx, rnd, code)):
        if os.path.isfile(os.path.join(adir, "attempt.json")):
            continue
        started = _load_json(os.path.join(adir, "started.json"))
        if not isinstance(started, dict):
            sid = _stop(ctx, rnd, "恢复时无法确认旧进程已退出", code, {"attempt": k, "why": "started.json unreadable"})
            raise RunGradeError(f"STOP {sid}: attempt {k} of {code}: started.json is unreadable")
        if not (started.get("dependency_check") or {}).get("ok", False):
            # by design grade.py was never started (dependency check failed before the start)
            out.append(_finish(ctx, code, rnd, k, adir, started, {"not_started": True}, recovered=True))
            continue
        proc = _load_json(os.path.join(adir, "proc.json"))
        if not isinstance(proc, dict) or ("root_pid" not in proc and proc.get("phase") not in
                                          ("launching", "not_started")):
            sid = _stop(ctx, rnd, "恢复时无法确认旧进程已退出", code,
                        {"attempt": k, "why": "proc.json missing or unreadable"})
            raise RunGradeError(f"STOP {sid}: attempt {k} of {code}: no usable proc.json")
        seen = {}                                     # "unreadable": pids whose environment could not be read
        try:
            alive, unconfirmed = limits.still_alive(proc, details=seen)
        except Exception:                                             # noqa: BLE001 - any failure = unconfirmed
            alive, unconfirmed = [], True
        signals = []
        if unconfirmed:
            sid = _stop(ctx, rnd, "恢复时无法确认旧进程已退出", code,
                        {"attempt": k, "alive": alive, "unreadable": seen.get("unreadable", [])})
            raise RunGradeError(f"STOP {sid}: attempt {k} of {code}: process state cannot be confirmed")
        if alive:
            res = limits.cleanup(proc, "grade")
            signals = list(res.signals_sent)
            if res.killed_pids_alive or res.cleanup_unconfirmed:
                sid = _stop(ctx, rnd, "恢复时无法确认旧进程已退出", code,
                            {"attempt": k, "alive": res.killed_pids_alive, "unconfirmed": res.cleanup_unconfirmed,
                             "unreadable": list(res.unreadable)})
                raise RunGradeError(f"STOP {sid}: attempt {k} of {code}: old processes still alive or unconfirmed")
        if proc.get("phase") == "not_started":
            # Popen failed (or the suspended target was killed before release): grade.py never ran
            le = proc.get("launch_error") if isinstance(proc.get("launch_error"), dict) else {}
            out.append(_finish(ctx, code, rnd, k, adir, started,
                               {"launch_error": {"errno": le.get("errno"), "type": le.get("type") or UNKNOWN}},
                               recovered=True))
            continue
        text = _stdout_text(adir)
        run_id = proc.get("run_id") or _first_run_id(text)
        complete = bool(_final_line(text) and run_id and RUN_ID_RE.match(f"RUN_ID={run_id}")
                        and os.path.isfile(os.path.join(ctx.case, "runs", run_id, "steps.json")))
        known = isinstance(proc.get("signals_sent"), list)
        info = {"exit_code": UNKNOWN, "over_limit": UNKNOWN,
                "timed_out": proc["timed_out"] if known and isinstance(proc.get("timed_out"), bool) else UNKNOWN,
                "signals_sent": (list(proc["signals_sent"]) if known else []) + signals,
                "signals_unknown": not known}
        if limits.record_cleanup_failed(proc):
            # the old wrapper's own cleanup failed (KILL FAIL) and it died before it could raise the stop
            info["kill"] = {"alive": list(proc.get("alive_after") or []),
                            "unconfirmed": proc.get("cleanup_unconfirmed") is True}
        # a supervision failure (not a wrapper interruption): the wrapper force-stopped grade.py itself; an abort by
        # KeyboardInterrupt/SystemExit (abort_error "interrupted") is a wrapper interruption
        interrupt_abort = proc.get("abort_error") == "interrupted"
        if proc.get("aborted") and not interrupt_abort:
            info["supervision_error"] = {"type": proc.get("abort_error") or UNKNOWN, "errno": None}
        # R17 narrowed: only a genuine wrapper interruption counts; a record that ended (normally, or aborted by a
        # supervision failure) was finished by the wrapper itself, so a missing final line is grade.py's own result
        interrupted = not complete and ("ended_at" not in proc or interrupt_abort)
        out.append(_finish(ctx, code, rnd, k, adir, started, info, recovered=True,
                           wrapper_interrupted=interrupted))
    return out


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    retry = "--retry" in args
    args = [a for a in args if a != "--retry"]
    if len(args) != 2 or not args[1].isdigit():
        print("usage: run_grade.py <code> <rnd> [--retry]", file=sys.stderr)
        return 2
    try:
        rec = attempt(args[0], int(args[1]), retry=retry)
    except (RunGradeError, stops.StopsError) as e:
        print(str(e), flush=True)
        return 1
    print(f"ATTEMPT {rec['code']} r{rec['rnd']} attempt{rec['k']}: "
          f"{rec['final_line'] or 'no final line'} | location={rec['failure_location']} | "
          f"attribution={rec['attribution']}", flush=True)
    return 1 if rec["stops"] else 0


if __name__ == "__main__":
    sys.exit(main())
