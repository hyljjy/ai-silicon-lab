"""Netlist compatibility diagnosis of CASE-01 stage B (revise/notes/netlist_diagnosis_plan.md, author-confirmed
2026-10-25; decision D-01 option B). Not part of the preregistration; its results never enter the formal judgments.

Run inside WSL (login shell) from tasks/CASE-01, only after revise/outputs/r2/round_complete.json is committed:
  python3 -B revise/diag_netlist/diag_netlist.py plan     list the fixed objects and the transformation, run nothing
  python3 -B revise/diag_netlist/diag_netlist.py run      baseline first, then every candidate, each exactly once
  python3 -B revise/diag_netlist/diag_netlist.py report   write runs/revise-diag-netlist/results.md from result.json

Objects (plan section 3, fixed, never chosen by result): the F1 archive baseline netlist; every formal attempt of
rounds 1 and 2 (revise/results/r<r>/<code>/attempt*/attempt.json -> runs/<run_id>/) whose steps.json has synth
returncode 0 and whose synth/netlist.v exists. Attempts without a netlist are listed as not included.

The only transformation (plan section 4): on a line that is exactly a declaration
  <ws>(wire|reg)<ws>signed<ws>[<range><ws>]<identifier><ws>;<ws>
the word signed and the whitespace after it are removed; nothing else changes. The object is not diagnosed
("cannot be diagnosed: uncovered syntax") when signed occurs anywhere else, when the netlist has always/initial
blocks, a string, or an operator outside the single "=" of an assign statement, or when the line-by-line check
finds any other difference.

Replay (plan section 5): gl_compile, gl_sim, sta and check_sta exactly as recorded in the object's steps.json, in its
own new directory runs/revise-diag-netlist/<object>/. The only argv/env substitutions are: the recorded run root ->
where the run dir is read now (the baseline was recorded under runs/ and is read from evidence/F1/archive/), the
netlist path -> the transformed copy, the sta output directory -> the diagnosis sta/. A formal attempt that failed
at sta has no recorded check_sta step; its check_sta command is then built the way the frozen grade.py builds it
([python, -B, inputs/scripts/check_sta.py, <sta dir>, repr(T_ns), repr(C_load_pF), sceneset], values from the
attempt's verdict.json) and marked "derived" in result.json. The sta environment is grade.py's (TOP, NETLIST, T_NS,
CLOAD_PF, SCENESET, OUTDIR, CASE_DIR on top of the login environment), its values from verdict.json and the impl
config. Every frozen input (TB, vectors, scripts, SDC, whitelist, gate-level models) is read from the original run
dir, read only, after checking inputs.sha256, verdict.json netlist_sha256 and config/gl_models.sha256. Timing values
are reported only when gl_sim passes and sta and check_sta pass.

Order and stops: the baseline is run first; every later `run` re-checks the baseline result against the F1 archive
before any candidate. STOP is written (and every remaining object skipped) when the baseline's gl_sim message,
sta_check.json or sta_results.tsv differ from the F1 archive, when any object ends in an infrastructure error, and
when the run is interrupted. An object directory that already exists is never run again. WSL/POSIX only; Python
standard library only.
"""
import argparse
import datetime
import difflib
import hashlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True        # loading the objects' logcheck/check_sim must not write into their run dirs

HERE =os.path.dirname(os.path.abspath(__file__))
REVISE = os.path.dirname(HERE)
CASE = os.path.dirname(REVISE)
OUT = os.path.join(CASE, "runs", "revise-diag-netlist")
BASELINE_RUN = "20261009-092827-base-T27.91"
BASELINE_DIR = os.path.join(CASE, "evidence", "F1", "archive", BASELINE_RUN)
ROUNDS = (1, 2)
STD = ["tt_025C_1v80", "tt_100C_1v80", "ss_100C_1v60", "ss_n40C_1v60", "ff_n40C_1v95", "ff_100C_1v95"]
STEPS = ("gl_compile", "gl_sim", "sta", "check_sta")
# Same tool classes and wall-clock limits as the frozen grade.py (STEP_TOOL, STEP_TIMEOUT_S).
STEP_TOOL = {"gl_compile": "iverilog", "gl_sim": "iverilog", "sta": "sta", "check_sta": "python"}
STEP_TIMEOUT_S = {"gl_compile": 600, "gl_sim": 3600, "sta": 3600, "check_sta": 600}
GL_MODELS = ("primitives.v", "sky130_fd_sc_hd.v")

IDENT = r"(?:[A-Za-z_][A-Za-z0-9_$]*|\\\S+)"
DECL_RE = re.compile(r"^(\s*(?:wire|reg)\s+)signed\s+((?:\[[^\]]+\]\s+)?" + IDENT + r"\s*;\s*)$")
SIGNED_RE = re.compile(r"(?<![A-Za-z0-9_\\])signed(?![A-Za-z0-9_$])")    # $signed counts as signed
ESCAPED_RE = re.compile(r"\\\S+(?:\s|$)")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
PROC_RE = re.compile(r"(?<![A-Za-z0-9_$])(?:always\w*|initial)(?![A-Za-z0-9_$])")
OPERATOR_RE = re.compile(r"[~!&|^+\-*/%?<>=\"#@]")
ASSIGN_RE = re.compile(r"^\s*assign\s+([^=;]+?)\s*=\s*([^=;]+?)\s*;\s*$")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def _scrub(line):
    """The line without escaped identifiers (their characters are names, not operators)."""
    return ESCAPED_RE.sub(" ", line)


def transform(text):
    """{"ok", "text", "changed": [line numbers, 1-based], "reason"}: the plan's single rule and its stop rules.
    text is the whole netlist (str, newlines kept as given). On ok=False, text is None."""
    def stop(reason):
        return {"ok": False, "text": None, "changed": [], "reason": reason}

    body = LINE_COMMENT_RE.sub("", BLOCK_COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text))
    out, changed = [], []
    orig_lines = text.splitlines(keepends=True)
    body_lines = body.splitlines(keepends=True)
    if len(orig_lines) != len(body_lines):
        return stop("comment removal changed the line count")
    for n, (line, code) in enumerate(zip(orig_lines, body_lines), 1):
        eol = line[len(line.rstrip("\r\n")):]
        bare_code = code.rstrip("\r\n")
        scrubbed = _scrub(bare_code)
        m = DECL_RE.match(bare_code)
        if m:
            if bare_code != line.rstrip("\r\n"):
                return stop(f"line {n}: comment on a signed declaration")
            out.append(m.group(1) + m.group(2) + eol)
            changed.append(n)
            continue
        if SIGNED_RE.search(scrubbed):
            return stop(f"line {n}: signed outside a plain wire/reg declaration: {bare_code.strip()[:120]}")
        if PROC_RE.search(scrubbed):
            return stop(f"line {n}: procedural block: {bare_code.strip()[:120]}")
        a = ASSIGN_RE.match(scrubbed)
        if a:
            if OPERATOR_RE.search(a.group(1)) or OPERATOR_RE.search(a.group(2)):
                return stop(f"line {n}: operator in an assign statement: {bare_code.strip()[:120]}")
        elif OPERATOR_RE.search(scrubbed):
            return stop(f"line {n}: operator or unsupported character: {bare_code.strip()[:120]}")
        out.append(line)
    new = "".join(out)
    probs = verify_transform(text, new, changed)
    if probs:
        return stop("; ".join(probs))
    return {"ok": True, "text": new, "changed": changed, "reason": None}


def verify_transform(old, new, changed):
    """Independent line-by-line check (plan 4.5): same line count; every unchanged line byte-identical; every changed
    line equals the original with exactly one 'signed ' word removed from a declaration. Instances, their cell types,
    names and connections therefore cannot differ."""
    a, b = old.splitlines(keepends=True), new.splitlines(keepends=True)
    if len(a) != len(b):
        return [f"line count {len(a)} -> {len(b)}"]
    probs = []
    want = set(changed)
    for n, (x, y) in enumerate(zip(a, b), 1):
        if x == y:
            if n in want:
                probs.append(f"line {n} reported changed but identical")
            continue
        if n not in want:
            probs.append(f"line {n} differs but is not a reported change")
            continue
        m = DECL_RE.match(x.rstrip("\r\n"))
        if not m or y != m.group(1) + m.group(2) + x[len(x.rstrip("\r\n")):]:
            probs.append(f"line {n}: change is not the removal of signed from a declaration")
    return probs


def instance_count(text):
    """Number of cell instances (lines '<cell> <name> (' at statement start); recorded only, for the report."""
    return len(re.findall(r"^\s*(?!module\b)[A-Za-z_]\w*\s+" + IDENT + r"\s*\($", text, re.M))


def objects():
    """Fixed object list [(name, kind, src_root, recorded_root)] plus [(name, reason)] of attempts not included."""
    objs = [("baseline", "baseline", BASELINE_DIR, None)]
    skipped = []
    for r in ROUNDS:
        res = os.path.join(REVISE, "results", f"r{r}")
        for code in sorted(os.listdir(res)):
            cdir = os.path.join(res, code)
            if not os.path.isdir(cdir):
                continue
            for att in sorted(d for d in os.listdir(cdir) if d.startswith("attempt")):
                with open(os.path.join(cdir, att, "attempt.json"), encoding="utf-8") as f:
                    run_id = json.load(f).get("run_id")
                name = f"r{r}_{code}_{att}"
                if not run_id:
                    skipped.append((name, "no run_id (no run directory)"))
                    continue
                root = os.path.join(CASE, "runs", run_id)
                steps = load_steps(root)
                synth = next((s for s in steps if s["step"] == "synth"), None) if steps else None
                if not synth or synth.get("returncode") != 0 or not os.path.isfile(os.path.join(root, "synth",
                                                                                                "netlist.v")):
                    skipped.append((name, "synth did not return 0 or synth/netlist.v is missing"))
                    continue
                objs.append((name, "candidate", root, None))
    return objs, skipped


def load_steps(root):
    try:
        with open(os.path.join(root, "steps.json"), encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return None


def recorded_root(steps):
    """The run root the steps were recorded under: the directory of the recorded sta_run.tcl, two levels up."""
    sta = next(s for s in steps if s["step"] == "sta")
    return os.path.dirname(os.path.dirname(os.path.dirname(sta["argv"][-1])))


def rewrite(argv, rec_root, src_root, netlist, sta_dir):
    """argv with the three allowed substitutions (netlist, sta out dir, then run root); returns (argv, [changes])."""
    subs = [(rec_root + "/synth/netlist.v", netlist), (rec_root + "/sta", sta_dir)]
    out, changes = [], []
    for a in argv:
        b = a
        for old, new in subs:
            if b == old:
                b = new
                break
        else:
            if b.startswith(rec_root + "/"):
                b = src_root + b[len(rec_root):]
            elif b.startswith("+") and "=" in b and b.split("=", 1)[1].startswith(rec_root + "/"):
                k, v = b.split("=", 1)
                b = k + "=" + src_root + v[len(rec_root):]
        if b != a:
            changes.append([a, b])
        out.append(b)
    return out, changes


def _load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_kv(path):
    d = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if "=" in line:
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip()
    return d


class Interrupted(BaseException):
    """SIGTERM, raised in the main thread like Ctrl-C so the running step's process group is killed (grade.py does
    the same with on_sigterm)."""


def on_sigterm(signum, frame):
    raise Interrupted("SIGTERM")


def check_inputs(src_root):
    """Problems of the source run dir's frozen inputs against its inputs.sha256 (paths relative to inputs/)."""
    probs = []
    inp = os.path.join(src_root, "inputs")
    with open(os.path.join(src_root, "inputs.sha256"), encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            digest, rel = line.split(None, 1)
            rel = rel.strip().lstrip("*")
            p = os.path.join(inp, rel)
            if not os.path.isfile(p) or sha256(p) != digest.lower():
                probs.append(f"inputs/{rel} does not match inputs.sha256")
    return probs


def check_argv(st, argv, rec_root, src_root, orig_netlist, netlist, sta_dir):
    """The replayed argv may not reach the original netlist or (for the baseline) the recorded root; the netlist and
    sta substitutions must each happen exactly where grade.py put them."""
    probs = []
    origs = {orig_netlist, rec_root + "/synth/netlist.v", src_root + "/synth/netlist.v"}
    if any(a in origs or a.endswith("=" + orig_netlist) for a in argv):
        probs.append(f"{st}: argv still names the original netlist")
    if rec_root != src_root and any(rec_root + "/" in a or a == rec_root for a in argv):
        probs.append(f"{st}: argv still names the recorded root {rec_root}")
    if st == "gl_compile" and argv.count(netlist) != 1:
        probs.append("gl_compile: the transformed netlist is not on the command line exactly once")
    if st == "check_sta" and argv.count(sta_dir) != 1:
        probs.append("check_sta: the diagnosis sta directory is not on the command line exactly once")
    return probs


def run_step(odir, name, argv, log, env, logcheck, rules):
    path = os.path.join(odir, log)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    t0 = time.monotonic()
    timed_out = False
    with open(path, "w") as f:
        proc = subprocess.Popen(argv, cwd=odir, env=env, stdin=subprocess.DEVNULL, stdout=f,
                                stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = proc.wait(timeout=STEP_TIMEOUT_S[name])
        except BaseException as e:                            # timeout, Ctrl-C, SIGTERM: kill the whole group
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except OSError:
                pass
            rc = proc.wait(timeout=60)
            if not isinstance(e, subprocess.TimeoutExpired):
                raise
            timed_out = True
    problems, hits = logcheck.scan(STEP_TOOL[name], path, rules)
    with open(path, errors="replace") as f:
        text = f.read()
    return {"step": name, "argv": argv, "returncode": rc, "timed_out": timed_out,
            "seconds": round(time.monotonic() - t0, 3), "log": log, "log_problems": problems,
            "whitelist_hits": {str(k): v for k, v in hits.items()}}, text


def diagnose(name, kind, src_root):
    """One object, once. Returns its result dict (also written to <object>/result.json)."""
    odir = os.path.join(OUT, name)
    os.makedirs(odir)                                         # raises if it exists: never run twice
    res = {"object": name, "kind": kind, "source": os.path.relpath(src_root, CASE).replace(os.sep, "/"),
           "started": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "script_sha256": sha256(os.path.abspath(__file__)), "status": None}
    try:
        steps = load_steps(src_root)
        rec_root = recorded_root(steps)
        with open(os.path.join(src_root, "verdict.json"), encoding="utf-8") as f:
            formal = json.load(f)
        orig_path = os.path.join(src_root, "synth", "netlist.v")
        with open(orig_path, "rb") as f:
            orig = f.read()
        bad = check_inputs(src_root)
        if sha256_bytes(orig) != formal.get("netlist_sha256"):
            bad.append("synth/netlist.v does not match verdict.json netlist_sha256")
        res["source_checks"] = {"inputs_sha256": "pass" if not bad else "fail", "problems": bad}
        if bad:
            raise RuntimeError("; ".join(bad[:5]))
        text = orig.decode("utf-8")
        t = transform(text)
        res["transform"] = {"original_sha256": sha256_bytes(orig), "changed_lines": t["changed"],
                            "changed_count": len(t["changed"]), "reason": t["reason"],
                            "instances": instance_count(text)}
        if not t["ok"]:
            res["status"] = "cannot_diagnose"
            return res
        new = t["text"].encode("utf-8")
        netlist = os.path.join(odir, "netlist.v")
        with open(netlist, "wb") as f:
            f.write(new)
        diff = "".join(difflib.unified_diff(text.splitlines(keepends=True), t["text"].splitlines(keepends=True),
                                            "original/synth/netlist.v", "diag/netlist.v"))
        with open(os.path.join(odir, "netlist.diff"), "w", encoding="utf-8") as f:
            f.write(diff)
        inst_after = instance_count(t["text"])
        res["transform"].update({"transformed_sha256": sha256_bytes(new), "diff_sha256": sha256_bytes(
            diff.encode("utf-8")), "instances_after": inst_after,
            "semantic_check": {"method": "line-by-line: unchanged lines byte-identical, changed lines differ only "
                                         "by the removed word signed (plan 4.5)",
                               "result": "pass" if inst_after == res["transform"]["instances"] else "fail"}})
        if inst_after != res["transform"]["instances"]:
            raise RuntimeError("instance count changed by the transformation")

        inp = os.path.join(src_root, "inputs")
        logcheck = _load(os.path.join(inp, "scripts", "logcheck.py"), f"diag_logcheck_{name}")
        check_sim = _load(os.path.join(inp, "scripts", "check_sim.py"), f"diag_check_sim_{name}")
        rules = logcheck.load_rules(os.path.join(inp, "config", "warn_whitelist.txt"))
        impl = next(f for f in os.listdir(os.path.join(inp, "config")) if f.startswith("impl."))
        top = read_kv(os.path.join(inp, "config", impl))["top"]
        sta_dir = os.path.join(odir, "sta")
        rec = {s["step"]: s for s in steps}
        missing = [st for st in STEPS[:3] if st not in rec]
        if missing:
            raise RuntimeError(f"steps.json has no {', '.join(missing)} step")
        T, cload, sceneset = repr(formal["T_ns"]), repr(formal["C_load_pF"]), formal["sceneset"]
        python = rec["gen_vectors"]["argv"][0]
        if "check_sta" in rec:
            if rec["check_sta"]["argv"][-3:] != [T, cload, sceneset]:
                raise RuntimeError("recorded check_sta arguments differ from verdict.json T_ns/C_load_pF/sceneset")
        else:                                                  # attempt failed at sta: build it as grade.py does
            rec["check_sta"] = {"step": "check_sta", "logs": ["sta/check.log"], "derived": True,
                                "argv": [python, "-B", os.path.join(inp, "scripts", "check_sta.py").replace(
                                    src_root, rec_root, 1), rec_root + "/sta", T, cload, sceneset]}
        want = {}
        with open(os.path.join(inp, "config", "gl_models.sha256")) as f:
            for line in f:
                if line.strip():
                    digest, model = line.split()
                    want[model] = digest
        models = [a for a in rec["gl_compile"]["argv"] if os.path.basename(a) in GL_MODELS]
        if sorted(os.path.basename(m) for m in models) != sorted(GL_MODELS):
            raise RuntimeError("recorded gl_compile does not name both gate-level models")
        for m in models:
            if sha256(m) != want.get(os.path.basename(m)):
                raise RuntimeError(f"gate-level model {m} does not match config/gl_models.sha256")
        env_sta = dict(os.environ, TOP=top, NETLIST=netlist, T_NS=T, CLOAD_PF=cload, SCENESET=sceneset,
                       OUTDIR=sta_dir, CASE_DIR=inp)
        res["sta_env"] = {"TOP": top, "NETLIST": netlist, "T_NS": T, "CLOAD_PF": cload, "SCENESET": sceneset,
                          "OUTDIR": sta_dir, "CASE_DIR": inp}
        res["replay"] = []
        net_sha = res["transform"]["transformed_sha256"]
        for st in STEPS:
            argv, changes = rewrite(rec[st]["argv"], rec_root, src_root, netlist, sta_dir)
            bad = check_argv(st, argv, rec_root, src_root, orig_path, netlist, sta_dir)
            if bad:
                raise RuntimeError("; ".join(bad))
            if st == "sta":
                os.makedirs(sta_dir)
            if sha256(netlist) != net_sha:
                raise RuntimeError(f"transformed netlist changed before {st}")
            rec_log = rec[st]["logs"][0]
            r, text_log = run_step(odir, st, argv, rec_log, env_sta if st == "sta" else None, logcheck, rules)
            r["recorded_argv"] = rec[st]["argv"]
            r["derived"] = bool(rec[st].get("derived"))
            r["substitutions"] = changes
            res["replay"].append(r)
            if st == "gl_sim":
                exp = int(next(a for a in rec[st]["argv"] if a.startswith("+EXP="))[5:])
                ok, msg = check_sim.check(text_log, r["returncode"], exp)
                res["gl_sim"] = msg
                if not ok or r["log_problems"]:
                    res["status"] = "fail"
                    res["failure_location"] = "gl_sim"
                    return res
            elif r["returncode"] != 0 or r["timed_out"] or r["log_problems"]:
                res["status"] = "fail"
                res["failure_location"] = st
                res["failure_tail"] = text_log.splitlines()[-5:]
                return res
        with open(os.path.join(sta_dir, "sta_check.json"), encoding="utf-8") as f:
            sta = json.load(f)
        if not sta.get("valid"):
            res["status"] = "fail"
            res["failure_location"] = "check_sta"
            return res
        if sha256(netlist) != net_sha:
            raise RuntimeError("transformed netlist changed during the replay")
        worst = min(sta["corners"][c]["ws_max"] for c in STD)
        res.update({"status": "ok", "worst_setup": sta["worst_setup"], "worst_hold": sta["worst_hold"],
                    "corners": {c: sta["corners"][c] for c in STD}, "area_um2": formal.get("area_um2"),
                    "timing_target": {"rule": "setup_ge_0_std", "worst_setup_std": worst, "met": worst >= 0}})
        return res
    except Exception as e:                                    # infrastructure, not a diagnosis result
        res["status"] = "error"
        res["error"] = f"{type(e).__name__}: {e}"
        return res
    finally:
        res["ended"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        with open(os.path.join(odir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)


def baseline_matches(res):
    """Problems of the baseline control against the F1 archive (empty = the replay itself is unbiased)."""
    probs = []
    if res.get("status") != "ok":
        return [f"baseline status {res.get('status')} ({res.get('failure_location') or res.get('error')})"]
    if res["transform"]["changed_count"] != 0:
        probs.append("baseline transformation is not a no-op")
    with open(os.path.join(BASELINE_DIR, "verdict.json"), encoding="utf-8") as f:
        v = json.load(f)
    if res.get("gl_sim") != v.get("gl_sim"):
        probs.append(f"gl_sim {res.get('gl_sim')!r} != F1 {v.get('gl_sim')!r}")
    for rel in ("sta/sta_check.json", "sta/sta_results.tsv"):
        a = os.path.join(OUT, "baseline", rel)
        b = os.path.join(BASELINE_DIR, rel)
        if rel.endswith(".json"):
            with open(a, encoding="utf-8") as f1, open(b, encoding="utf-8") as f2:
                if json.load(f1) != json.load(f2):
                    probs.append(f"{rel} differs from the F1 archive")
        elif sha256(a) != sha256(b):
            probs.append(f"{rel} differs from the F1 archive")
    return probs


def write_stop(lines):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "STOP"), "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    for line in lines:
        print(f"STOP: {line}")
    print("STOP: every remaining object skipped; hand over to the author", flush=True)


def git_state():
    """HEAD and whether this script is committed unchanged (plan 6: commit before running); None if git is absent."""
    rel = os.path.relpath(os.path.abspath(__file__), os.path.dirname(os.path.dirname(CASE)))
    try:
        head = subprocess.run(["git", "-C", CASE, "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=60).stdout.strip()
        dirty = subprocess.run(["git", "-C", CASE, "status", "--porcelain", "--", HERE], capture_output=True,
                               text=True, timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return {"head": head, "script": rel.replace(os.sep, "/"), "diag_dir_clean": dirty == ""}


def preflight():
    probs = []
    if os.name != "posix":
        probs.append("run inside WSL: process-group cleanup needs POSIX")
    if not os.path.isfile(os.path.join(REVISE, "outputs", "r2", "round_complete.json")):
        probs.append("revise/outputs/r2/round_complete.json does not exist: round 2 is not closed")
    if "SKY130_HD" not in os.environ:
        probs.append("SKY130_HD is not set (run in the WSL login shell)")
    if os.path.exists(os.path.join(OUT, "STOP")):
        probs.append("runs/revise-diag-netlist/STOP exists: an earlier run stopped; the author decides")
    g = git_state()
    if g is None or not g["head"] or not g["diag_dir_clean"]:
        probs.append("revise/diag_netlist/ is not committed unchanged (plan 6: review, author, commit, then run)")
    return probs


def cmd_plan():
    objs, skipped = objects()
    for name, kind, root, _ in objs:
        steps = load_steps(root)
        with open(os.path.join(root, "synth", "netlist.v"), encoding="utf-8") as f:
            t = transform(f.read())
        state = f"{len(t['changed'])} signed declaration(s) to change" if t["ok"] else f"STOP: {t['reason']}"
        state += "; check_sta " + ("recorded" if any(st["step"] == "check_sta" for st in steps) else
                                   "not recorded (formal attempt failed at sta): derived as grade.py builds it")
        print(f"OBJECT {name}: {os.path.relpath(root, CASE)} recorded_root={recorded_root(steps)} {state}")
    for name, why in skipped:
        print(f"NOT INCLUDED {name}: {why}")
    print(f"script sha256 {sha256(os.path.abspath(__file__))}")
    return 0


def _stored_baseline():
    p = os.path.join(OUT, "baseline", "result.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def cmd_run():
    probs = preflight()
    if probs:
        for p in probs:
            print(f"REFUSED: {p}")
        return 1
    objs, skipped = objects()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"run-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"), "w",
              encoding="utf-8") as f:
        vstep = next(st for st in load_steps(BASELINE_DIR) if st["step"] == "versions")
        try:
            versions = subprocess.run(vstep["argv"], capture_output=True, text=True, timeout=120).stdout
        except (OSError, subprocess.SubprocessError) as e:
            versions = f"unavailable: {type(e).__name__}"
        json.dump({"git": git_state(), "script_sha256": sha256(os.path.abspath(__file__)), "tool_versions": versions,
                   "objects": [o[0] for o in objs], "not_included": skipped}, f, ensure_ascii=False, indent=1)
    previous = signal.signal(signal.SIGTERM, on_sigterm)
    current = None
    try:
        for name, kind, root, _ in objs:
            if kind != "baseline":
                base = _stored_baseline()
                try:
                    bp = baseline_matches(base) if base else ["no baseline result.json"]
                except Exception as e:
                    bp = [f"baseline control could not be checked ({type(e).__name__}: {e})"]
                if bp:
                    write_stop([f"baseline control: {p}" for p in bp])
                    return 1
            if os.path.exists(os.path.join(OUT, name)):
                print(f"SKIP {name}: already diagnosed (one run per object)")
                continue
            current = name
            res = diagnose(name, kind, root)
            current = None
            print(f"OBJECT {name}: {res['status']} " + json.dumps({k: res.get(k) for k in (
                "failure_location", "gl_sim", "worst_setup", "worst_hold", "timing_target", "error")
                if res.get(k) is not None}, ensure_ascii=False), flush=True)
            if res["status"] == "error":
                write_stop([f"infrastructure error on {name}: {res.get('error')}"])
                return 1
            if kind == "baseline":
                try:
                    bp = baseline_matches(res)
                except Exception as e:
                    bp = [f"baseline control could not be checked ({type(e).__name__}: {e})"]
                if bp:
                    write_stop([f"baseline control: {p}" for p in bp])
                    return 1
                print("BASELINE CONTROL OK: replay matches the F1 archive", flush=True)
    except BaseException as e:                                 # Ctrl-C, SIGTERM: the step's group is already killed
        write_stop([f"interrupted ({type(e).__name__}) while diagnosing {current or 'between objects'}"])
        raise
    finally:
        signal.signal(signal.SIGTERM, previous)
    for name, why in skipped:
        print(f"NOT INCLUDED {name}: {why}")
    return 0


def hold_end(r):
    """'，start → end' of the min-slack hold category at the worst hold corner, or ''."""
    cats = [c for k, c in r["corners"][r["worst_hold"]["corner"]]["categories"].items()
            if k.endswith("_min") and isinstance(c, dict)]
    if not cats:
        return ""
    c = min(cats, key=lambda c: c["slack"])
    return f"，{c['start']} → {c['end']}"


def cmd_report():
    rows = []
    for name in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, name, "result.json")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                rows.append(json.load(f))
    lines = ["# 网表兼容性诊断结果（自动汇总，写入 notes 前由操作者核对）", "",
             "| 对象 | 状态 | 改动声明行数 | 门级回归 | 六点最差 setup（ns） | 最差 setup 端点 | 最差 hold（ns） | 达到 F1 目标 "
             "| 面积（µm²） | 说明 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        tr = r.get("transform", {})
        ok = r.get("status") == "ok"
        ws = r.get("worst_setup") or {}
        wh = r.get("worst_hold") or {}
        end = ""
        if ok:
            cat = r["corners"][ws["corner"]]["categories"].get(f"{ws.get('category')}_max")
            end = f"{cat['start']} → {cat['end']}" if isinstance(cat, dict) else ""
        lines.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            r["object"], r["status"], tr.get("changed_count", ""), r.get("gl_sim", ""),
            f"{ws['slack']:.6f}（{ws['corner']}，{ws.get('category', '')}）" if ok else "", end,
            f"{wh['slack']:.6f}（{wh['corner']}{hold_end(r)}）" if ok else "",
            ("是" if r["timing_target"]["met"] else "否") if ok else "",
            r.get("area_um2", "") if ok else "",
            tr.get("reason") or r.get("failure_location") or r.get("error") or ""))
    with open(os.path.join(OUT, "results.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {os.path.join(OUT, 'results.md')}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cmd", choices=("plan", "run", "report"))
    a = ap.parse_args(argv)
    return {"plan": cmd_plan, "run": cmd_run, "report": cmd_report}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
