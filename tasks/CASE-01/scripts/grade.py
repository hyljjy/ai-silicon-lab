"""CASE-01 grader (spec 6): one evaluation of one implementation.

Run inside WSL (login shell) from tasks/CASE-01:
  before F1: python3 scripts/grade.py --impl config/impl.base.cfg --T 20 --cload 0.0024 [--lmax 3] [--seed 1]
             [--sceneset std]
  after F1:  python3 scripts/grade.py --impl config/impl.<name>.cfg [--sceneset std|all]
After F1, config/f1.cfg is the only source of T, C_load, L_max and the seed (passing --T/--cload/--lmax/--seed is
then an error), and config/f1.sha256 must match the live evaluation files (a changed one is an evaluation revision).
The first output line is RUN_ID=<id>; the last line is always one 'GRADE OK: ...' or 'GRADE FAIL: ...' line.
Exit 0 only if both simulations pass and the STA analysis is valid; negative slack, a missed timing target and an
exceeded area cap are recorded, not failures. Never overwrites: every evaluation gets a new runs/<run_id>/.
All inputs are first copied to runs/<run_id>/inputs/ (same relative paths, made read-only) and every step runs from
that frozen copy (P1 M6); the candidate RTL is linted before it runs, and the frozen inputs are re-verified after
each simulation and at the end (final review I1); every step's log is checked against the frozen warning whitelist
(P1 M5).
"""
import argparse
import datetime
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback

import check_sim
import logcheck

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(CASE))
GL_MODELS = ("primitives.v", "sky130_fd_sc_hd.v")
FROZEN_INPUTS = ["tb/tb_dot4sat.v", "sdc/case01_sdc.tcl", "config/warn_whitelist.txt", "config/gl_models.sha256",
                 "ref/model.py", "ref/timeline.py", "ref/coverage.py", "ref/gen_vectors.py",
                 "scripts/grade.py", "scripts/check_sim.py", "scripts/logcheck.py", "scripts/check_sta.py",
                 "scripts/sta_run.tcl", "scripts/synth_case01.tcl"]
IN_PROCESS = ["scripts/grade.py", "scripts/check_sim.py", "scripts/logcheck.py"]   # imported by this process
STEP_TOOL = {"env_snapshot": "shell", "versions": "shell", "gen_vectors": "python", "rtl_compile": "iverilog",
             "rtl_sim": "iverilog", "synth": "yosys", "gl_compile": "iverilog", "gl_sim": "iverilog",
             "sta": "sta", "check_sta": "python"}
# Wall-clock limit per step, in seconds. The TB watchdog only counts simulation time, so a zero-time hang
# (e.g. a combinational loop in a candidate design) or a hung tool is stopped here (task review of Task 9).
STEP_TIMEOUT_S = {"env_snapshot": 600, "versions": 120, "gen_vectors": 600, "rtl_compile": 600, "rtl_sim": 1800,
                  "synth": 3600, "gl_compile": 600, "gl_sim": 3600, "sta": 3600, "check_sta": 600}
RECIPE_SHA = "b517940e44b8d0a87a7b649f7f3355fa8960759ba436a8acf5684bf9bc674049"   # spec 4.2: the recipe is its hash
STD = ["tt_025C_1v80", "tt_100C_1v80", "ss_100C_1v60", "ss_n40C_1v60", "ff_n40C_1v95", "ff_100C_1v95"]
# Frozen timing-target rules (spec 6: third verdict state). Decided by the author at checkpoint C (2026-10-09).
TIMING_RULES = {"setup_ge_0_std": "worst setup slack over the six std corners >= 0 at the frozen T; hold observed only"}
F1_KEYS = ("T_ns", "C_load_pF", "L_max", "area_cap", "timing_target", "seed", "calib_session")
F1_FILES = ["config/f1.cfg", "config/f1.sha256"]             # frozen into every post-F1 run as well
# RTL lint (final review I1; spec 1 and frozen-input integrity): candidate code runs inside the run dir during
# rtl_sim, so it must not open, read or write files, read plusargs, dump waveforms, call the shell or include other
# files. The b/h/o variants of the file-output tasks and the remaining file-descriptor and dump tasks are included.
LINT_SYSTF = ("fopen", "fclose", "fwrite", "fwriteb", "fwriteh", "fwriteo", "fdisplay", "fdisplayb", "fdisplayh",
              "fdisplayo", "fstrobe", "fstrobeb", "fstrobeh", "fstrobeo", "fmonitor", "fmonitorb", "fmonitorh",
              "fmonitoro", "fputc", "fflush", "fscanf", "fgets", "fgetc", "ungetc", "fread", "feof", "ferror",
              "fseek", "ftell", "rewind", "readmemh", "readmemb", "writememh", "writememb", "value$plusargs",
              "test$plusargs", "system", "dumpfile", "dumpvars", "dumpall", "dumpflush", "dumplimit", "dumpoff",
              "dumpon", "dumpports")
LINT_RE = re.compile(r"(?<![\w$])\$(?:" + "|".join(re.escape(n) for n in LINT_SYSTF) + r")(?![\w$])"
                     r"|`[ \t]*include\b|``")


class GradeError(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_kv(path):
    out = {}
    with open(path) as f:
        lines = f.readlines()
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "=" not in line:
            raise GradeError(f"{path}: bad line {raw.strip()!r}")
        key, value = (s.strip() for s in line.split("=", 1))
        if key in out:
            raise GradeError(f"{path}: duplicate key {key}")
        out[key] = value
    return out


def versions_argv():
    """The versions step (spec 3.5, 4.1; final review M3): every command must succeed (set -e; a missing tool exits
    127), the first line of `iverilog -V` is taken without a pipe (no SIGPIPE under pipefail), and the Python that
    runs this grader (sys.executable, passed as $1) is reported instead of python3 from PATH."""
    script = ('set -e -o pipefail; v=$(iverilog -V 2>&1); printf "%s\\n" "${v%%$\'\\n\'*}"; yosys -V; '
              's=$(sta -version); echo "OpenSTA $s"; "$1" --version')
    return ["bash", "-c", script, "versions", sys.executable]


def env_ids():
    """Library and tool identity for verdict.json (spec 6; final review M3); a missing file raises OSError."""
    return {"env/SHA256SUMS": sha256(os.path.join(REPO, "env", "SHA256SUMS")),
            "env/tools.sha256": sha256(os.path.join(REPO, "env", "tools.sha256")),
            "$SKY130_KIT/MANIFEST.txt": sha256(os.path.join(os.environ["SKY130_KIT"], "MANIFEST.txt"))}


def code_only(text):
    """Verilog text with comments removed and string literals emptied; newlines are kept, so line numbers stay right.
    Strings are skipped first, so a '//' or '/*' inside a string cannot hide the code after it."""
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("\n" * text.count("\n", i, j))
            i = j
        elif text[i] == '"':
            j = i + 1
            while j < n and text[j] not in '"\n':
                j += 2 if text[j] == "\\" else 1
            j = min(j, n)
            out.append('""' + "\n" * text.count("\n", i, j))
            i = j + 1 if j < n and text[j] == '"' else j
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def lint_rtl(text):
    """Forbidden constructs in candidate RTL, as ['line <n>: <construct>', ...]; empty when clean (final review I1)."""
    code = code_only(text)
    hits = []
    for m in LINT_RE.finditer(code):
        what = m.group(0)
        if what == "``":
            what = "`` (macro token pasting)"
        elif what.startswith("`"):
            what = "`include"
        hits.append(f"line {code.count(chr(10), 0, m.start()) + 1}: {what}")
    return hits


def read_only(path):
    """Best effort (DrvFs may ignore it): the integrity guarantee is verify_frozen, not the file mode."""
    try:
        os.chmod(path, 0o444)
    except OSError:
        pass


def verify_frozen(root, frozen, others, stage):
    """Re-check the run's frozen inputs after candidate code has run (final review I1). frozen: path under inputs/ ->
    sha256 recorded when it was frozen (kept in memory, so rewriting inputs.sha256 does not help); others: path under
    the run dir -> expected sha256 (inputs.sha256 itself and, once generated, vectors/vectors.txt and
    vectors/manifest.json). Any changed, missing or extra file or directory under inputs/ is an error."""
    inp = os.path.join(root, "inputs")
    problems = []
    for rel, digest in frozen.items():
        p = os.path.join(inp, rel)
        if os.path.islink(p) or not os.path.isfile(p):
            problems.append(f"missing inputs/{rel}")
        elif sha256(p) != digest:
            problems.append(f"changed inputs/{rel}")
    dirs = {"/".join(rel.split("/")[:k]) for rel in frozen for k in range(1, rel.count("/") + 1)}
    for dirpath, dirnames, filenames in os.walk(inp):
        here = os.path.relpath(dirpath, inp)
        prefix = "" if here == "." else here + "/"
        for d in list(dirnames):
            if prefix + d not in dirs or os.path.islink(os.path.join(dirpath, d)):
                problems.append(f"extra inputs/{prefix}{d}/")
                dirnames.remove(d)
        problems += [f"extra inputs/{prefix}{fn}" for fn in filenames if prefix + fn not in frozen]
    for rel, digest in others.items():
        p = os.path.join(root, rel)
        if os.path.islink(p) or not os.path.isfile(p):
            problems.append(f"missing {rel}")
        elif sha256(p) != digest:
            problems.append(f"changed {rel}")
    if problems:
        raise GradeError(f"frozen inputs changed after {stage}: " + "; ".join(problems[:10]))


def check_rel(rel, what):
    """rel must be a normalized relative path that stays inside tasks/CASE-01, also after resolving symlinks
    (final review M1). Every frozen input goes through this check."""
    if (not rel or os.path.isabs(rel) or os.path.normpath(rel) != rel or ".." in rel.split("/")):
        raise GradeError(f"{what} {rel!r} must be a normalized relative path inside tasks/CASE-01")
    case = os.path.realpath(CASE)
    if os.path.commonpath([case, os.path.realpath(os.path.join(CASE, rel))]) != case:
        raise GradeError(f"{what} {rel!r} resolves outside tasks/CASE-01")


def check_impl(args, lmax, phase):
    """Read and check the implementation config; every rejection happens before a run dir exists.
    Returns (impl, path of the cfg relative to tasks/CASE-01)."""
    impl = read_kv(os.path.join(CASE, args.impl))
    for key in ("name", "top", "rtl", "L"):
        if key not in impl:
            raise GradeError(f"{args.impl}: missing key {key}")
    # The TB always instantiates dot4sat and the recipe does not flatten: any other top would simulate one module
    # and time another (final review C1).
    if impl["top"] != "dot4sat":
        raise GradeError(f"{args.impl}: top = {impl['top']!r}; the interface module is dot4sat (spec 1) and the TB, "
                         f"synthesis and STA must all use it")
    if not re.fullmatch(r"[1-9]", impl["L"]) or not 1 <= int(impl["L"]) <= lmax:
        raise GradeError(f"{args.impl}: L={impl['L']!r} is not an integer in 1..{lmax}")
    if not re.fullmatch(r"[A-Za-z0-9_]+", impl["name"]):
        raise GradeError(f"{args.impl}: bad name {impl['name']!r}")
    # Candidate RTL lives under rtl/. Before F1 the grader's own self-test fixtures (tb/selftest/, e.g.
    # config/impl.pipe2.cfg) are also accepted; after F1 only rtl/ (final review M1).
    rtl = impl["rtl"]
    dirs = ("rtl/",) if phase == "post-F1" else ("rtl/", "tb/selftest/")
    if (os.path.isabs(rtl) or os.path.normpath(rtl) != rtl or ".." in rtl.split("/") or not rtl.startswith(dirs)
            or not rtl.endswith(".v")):
        raise GradeError(f"{args.impl}: rtl = {rtl!r} must be a normalized relative path "
                         f"{' or '.join(d + '<file>.v' for d in dirs)} inside tasks/CASE-01")
    check_rel(rtl, "RTL")
    if not os.path.isfile(os.path.join(CASE, rtl)):
        raise GradeError(f"RTL {rtl} not found")
    impl_rel = os.path.relpath(os.path.join(CASE, args.impl), CASE)
    if impl_rel.split("/")[0] == "..":
        raise GradeError(f"implementation config {args.impl} is outside tasks/CASE-01")
    check_rel(impl_rel, "implementation config")
    return impl, impl_rel


def kill_tree(proc):
    """Kill proc and every process it started, on Windows as well as POSIX (PRJ-004: os.killpg does not exist on
    Windows; the AttributeError skipped the kill and an orphaned test child filled the system disk)."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        else:
            os.killpg(proc.pid, signal.SIGKILL)      # start_new_session=True: the group id is the child's pid
    except (OSError, subprocess.SubprocessError):
        pass
    if proc.poll() is None:
        try:
            proc.kill()
        except OSError:
            pass


class Run:
    def __init__(self, root, rules):
        self.root = root
        self.rules = rules
        self.steps = []
        self.hits = {}

    def cmd(self, name, argv, log, env=None, extra_logs=()):
        """Run argv in the run dir, stdout+stderr to <root>/<log>, then check this step's logs immediately.
        A step that outlives STEP_TIMEOUT_S[name] is killed together with its whole process tree and fails. If this
        process is interrupted (Ctrl-C, SIGTERM) the step's process tree is killed too, the step is recorded as
        interrupted and the interrupt propagates (same pattern as calibrate.run_limited; final review M2).
        Every step records its wall-clock duration in seconds (final review M5)."""
        path = os.path.join(self.root, log)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        limit = STEP_TIMEOUT_S[name]
        timed_out = False
        t0 = time.monotonic()
        with open(path, "w") as f:
            proc = subprocess.Popen(argv, cwd=self.root, env=env, stdin=subprocess.DEVNULL, stdout=f,
                                    stderr=subprocess.STDOUT, start_new_session=True)
            try:
                rc = proc.wait(timeout=limit)
            except BaseException as e:
                kill_tree(proc)
                try:
                    rc = proc.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    raise RuntimeError(f"pid {proc.pid} survived the kill; stop it by hand") from e
                if not isinstance(e, subprocess.TimeoutExpired):
                    self.steps.append({"step": name, "argv": argv, "returncode": rc, "timed_out": False,
                                       "timeout_s": limit, "seconds": round(time.monotonic() - t0, 3),
                                       "logs": [log, *extra_logs], "log_problems": [],
                                       "interrupted": type(e).__name__})
                    raise
                timed_out = True
        seconds = round(time.monotonic() - t0, 3)
        problems = []
        for lg in (log,) + tuple(extra_logs):
            if timed_out and not os.path.exists(os.path.join(self.root, lg)):
                continue                                  # a step killed early may not have written its extra logs
            p, hits = logcheck.scan(STEP_TOOL[name], os.path.join(self.root, lg), self.rules)
            problems += p
            for k, v in hits.items():
                self.hits[k] = self.hits.get(k, 0) + v
        self.steps.append({"step": name, "argv": argv, "returncode": rc, "timed_out": timed_out,
                           "timeout_s": limit, "seconds": seconds, "logs": [log, *extra_logs],
                           "log_problems": problems})
        if timed_out:
            raise GradeError(f"{name} timed out after {limit} s and was killed (see {log})")
        with open(path, errors="replace") as f:
            return rc, f.read(), problems

    def require(self, name, argv, log, env=None, extra_logs=()):
        rc, text, problems = self.cmd(name, argv, log, env, extra_logs)
        if rc != 0:
            tail = "\n".join(text.splitlines()[-5:])
            raise GradeError(f"{name} failed (exit {rc}, see {log}):\n{tail}")
        if problems:
            raise GradeError(f"{name}: log check failed:\n" + "\n".join(problems[:10]))
        return text


def parse_f1(path):
    """Validate config/f1.cfg (final review I2): every key present, no unknown key, every value well formed."""
    kv = read_kv(path)
    unknown = sorted(set(kv) - set(F1_KEYS))
    missing = [k for k in F1_KEYS if k not in kv]
    if unknown or missing:
        raise GradeError(f"config/f1.cfg: unknown keys {unknown}, missing keys {missing}; keys are {list(F1_KEYS)}")

    def number(key):
        try:
            value = float(kv[key])
        except ValueError:
            raise GradeError(f"config/f1.cfg: {key} = {kv[key]!r} is not a number") from None
        if not math.isfinite(value):
            raise GradeError(f"config/f1.cfg: {key} = {kv[key]!r} is not finite")
        return value

    T = number("T_ns")
    if T <= 0:
        raise GradeError(f"config/f1.cfg: T_ns = {kv['T_ns']!r} must be > 0")
    cload = number("C_load_pF")
    try:
        with open(os.path.join(CASE, "evidence", "cload_extract.json")) as f:
            extracted = float(json.load(f)["value_pf"])
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise GradeError(f"cannot read value_pf from evidence/cload_extract.json ({type(e).__name__}: {e})") from None
    if cload != extracted:
        raise GradeError(f"config/f1.cfg: C_load_pF = {kv['C_load_pF']} != value_pf {extracted!r} in "
                         f"evidence/cload_extract.json (spec 9)")
    if not re.fullmatch(r"[0-9]+", kv["L_max"]) or not 1 <= int(kv["L_max"]) <= 3:
        raise GradeError(f"config/f1.cfg: L_max = {kv['L_max']!r} is not an integer in 1..3 (spec 9)")
    if kv["area_cap"] == "unset":
        cap = "unset"
    else:
        cap = number("area_cap")
        if cap <= 0:
            raise GradeError(f"config/f1.cfg: area_cap = {kv['area_cap']!r} must be > 0 (um2) or 'unset'")
    if kv["timing_target"] not in TIMING_RULES:
        raise GradeError(f"config/f1.cfg: timing_target = {kv['timing_target']!r}; known rules: {list(TIMING_RULES)}")
    if not re.fullmatch(r"-?[0-9]+", kv["seed"]):
        raise GradeError(f"config/f1.cfg: seed = {kv['seed']!r} is not an integer")
    if not kv["calib_session"]:
        raise GradeError("config/f1.cfg: calib_session is empty")
    return {"phase": "post-F1", "T": T, "cload": cload, "lmax": int(kv["L_max"]), "seed": int(kv["seed"]),
            "area_cap": cap, "timing_rule": kv["timing_target"], "calib_session": kv["calib_session"]}


def check_f1_list():
    """config/f1.sha256 (sha256sum format, written at F1) must list exactly FROZEN_INPUTS, and every live file must
    still match it: after F1 a changed evaluation file is an evaluation revision (spec 8; final review I2)."""
    path = os.path.join(CASE, "config", "f1.sha256")
    if not os.path.isfile(path):
        raise GradeError("config/f1.cfg exists but config/f1.sha256 does not (written at F1, Task 12)")
    listed = {}
    with open(path) as f:
        lines = f.read().splitlines()
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        m = re.fullmatch(r"([0-9a-f]{64}) [ *](.+)", line)
        if not m:
            raise GradeError(f"config/f1.sha256:{n}: not a sha256sum line: {line!r}")
        if m.group(2) in listed:
            raise GradeError(f"config/f1.sha256:{n}: {m.group(2)} listed twice")
        listed[m.group(2)] = m.group(1)
    if set(listed) != set(FROZEN_INPUTS):
        extra, missing = sorted(set(listed) - set(FROZEN_INPUTS)), sorted(set(FROZEN_INPUTS) - set(listed))
        raise GradeError(f"config/f1.sha256 must list exactly the frozen evaluation files; extra {extra}, "
                         f"missing {missing}")
    changed = [rel for rel in FROZEN_INPUTS if sha256(os.path.join(CASE, rel)) != listed[rel]]
    if changed:
        raise GradeError(f"evaluation file changed after F1: {', '.join(changed)} — that is an evaluation revision "
                         f"(spec 8)")
    return listed


def settings(args):
    """Evaluation settings. After F1, config/f1.cfg is the only source of T, C_load, L_max and the seed (passing
    --T/--cload/--lmax/--seed is an error) and config/f1.sha256 must match the live evaluation files. Before F1,
    --T and --cload are required, --lmax defaults to 3 (range 1..3, spec 2.5) and --seed to 1. In both phases the
    synthesis recipe must be the frozen one (spec 4.2). Everything here runs before a run dir is created."""
    f1 = os.path.join(CASE, "config", "f1.cfg")
    if os.path.exists(f1):
        given = [opt for opt, value in (("--T", args.T), ("--cload", args.cload), ("--lmax", args.lmax),
                                        ("--seed", args.seed)) if value is not None]
        if given:
            raise GradeError(f"config/f1.cfg exists: T, C_load, L_max and the seed are frozen; do not pass "
                             f"{'/'.join(given)}")
        s = parse_f1(f1)
        s["f1_list"] = check_f1_list()
    else:
        if args.T is None or args.cload is None:
            raise GradeError("before F1, --T and --cload are required")
        lmax = 3 if args.lmax is None else args.lmax
        if not 1 <= lmax <= 3:
            raise GradeError(f"before F1, --lmax must be in 1..3 (spec 2.5), got {lmax}")
        s = {"phase": "pre-F1", "T": args.T, "cload": args.cload, "lmax": lmax,
             "seed": 1 if args.seed is None else args.seed, "area_cap": None, "timing_rule": None,
             "calib_session": None}
    recipe = os.path.join(CASE, "scripts", "synth_case01.tcl")
    if sha256(recipe) != RECIPE_SHA:
        raise GradeError(f"scripts/synth_case01.tcl is not the frozen recipe (sha256 must be {RECIPE_SHA}, spec 4.2)")
    return s


def timing_target(s, sta):
    """Third verdict state (spec 6; final review I3). sta is the valid sta_check.json, or None when the analysis is
    not valid. setup_ge_0_std: met iff the worst setup slack over the six std corners is >= 0 at the frozen T (hold
    is observed only); sweep corners of --sceneset all do not count. Not meeting it is recorded, not a failure."""
    if s["timing_rule"] is None:
        return {"rule": None, "met": None, "note": "pre-F1: no frozen target"}
    if sta is None:
        return {"rule": s["timing_rule"], "met": None, "worst_setup_std": None,
                "note": "not evaluated: no valid analysis"}
    worst = min(sta["corners"][c]["ws_max"] for c in STD)
    return {"rule": s["timing_rule"], "met": worst >= 0, "worst_setup_std": worst}


def area_record(s, area):
    """Area against the frozen cap (spec 9; final review I3): within_cap is null before F1, when the cap is 'unset'
    or when there is no area yet. Exceeding the cap is recorded, not a failure."""
    if s["phase"] == "pre-F1":
        return {"area_um2": area, "cap_um2": None, "within_cap": None, "note": "pre-F1: no frozen cap"}
    cap = s["area_cap"]
    return {"area_um2": area, "cap_um2": cap, "within_cap": None if cap == "unset" or area is None else area <= cap}


def ok_line(v):
    t, a = v["timing_target"], v["area"]
    target = "n/a(pre-F1)" if t["rule"] is None else f"{t['rule']}:{'met' if t['met'] else 'not_met'}"
    if a["cap_um2"] is None:
        cap = "n/a(pre-F1)"
    elif a["cap_um2"] == "unset":
        cap = "unset"
    else:
        cap = f"{a['cap_um2']!r}:{'within' if a['within_cap'] else 'exceeded'}"
    return (f"GRADE OK: {v['run_id']} functional_pass analysis_valid worst_setup={v['worst_setup']} "
            f"worst_hold={v['worst_hold']} area={v['area_um2']} timing_target={target} area_cap={cap}")


def grade(args, verdict):
    s = settings(args)
    T, cload, lmax, phase = s["T"], s["cload"], s["lmax"], s["phase"]
    if "SYNTH_LIB" in os.environ:
        raise GradeError("SYNTH_LIB is set; the synthesis recipe must not be overridden (spec 4.2)")
    impl, impl_rel = check_impl(args, lmax, phase)
    L = int(impl["L"])
    rels = list(dict.fromkeys([impl_rel, impl["rtl"]] + FROZEN_INPUTS + (F1_FILES if phase == "post-F1" else [])))
    for rel in rels:
        check_rel(rel, "input")

    run_id = f"{datetime.datetime.now():%Y%m%d-%H%M%S}-{impl['name']}-T{T:g}"
    root = os.path.join(CASE, "runs", run_id)
    os.makedirs(root)                                   # FileExistsError if it exists: never overwrite
    print(f"RUN_ID={run_id}", flush=True)
    verdict.update({"run_id": run_id, "phase": phase, "impl": impl, "T_ns": T, "C_load_pF": cload,
                    "L_max": lmax, "seed": s["seed"], "sceneset": args.sceneset})
    if phase == "post-F1":
        verdict["calib_session"] = s["calib_session"]
    verdict.update({"timing_target": timing_target(s, None), "area": area_record(s, None)})

    run = Run(root, [])
    try:                                                # from here on, steps.json is written whatever happens (M2)
        # freeze every input at its relative path; all steps below read only the frozen copy
        inp = os.path.join(root, "inputs")
        frozen = {}
        with open(os.path.join(root, "inputs.sha256"), "w") as f:
            for rel in rels:
                dst = os.path.join(inp, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(os.path.join(CASE, rel), dst)
                frozen[rel] = sha256(dst)
                f.write(f"{frozen[rel]}  {rel}\n")
        for rel in rels:
            read_only(os.path.join(inp, rel))
        read_only(os.path.join(root, "inputs.sha256"))
        others = {"inputs.sha256": sha256(os.path.join(root, "inputs.sha256"))}

        def frozen_ok(stage):                          # final review I1: candidate code has run since the last check
            verify_frozen(root, frozen, others, stage)
            verdict.setdefault("frozen_checks", []).append(stage)

        if frozen["scripts/synth_case01.tcl"] != RECIPE_SHA:
            raise GradeError(f"frozen scripts/synth_case01.tcl is not the frozen recipe {RECIPE_SHA} (spec 4.2)")
        if phase == "post-F1":
            changed = [rel for rel in FROZEN_INPUTS if frozen[rel] != s["f1_list"][rel]]
            if changed:
                raise GradeError(f"evaluation file changed after F1: {', '.join(changed)} — that is an evaluation "
                                 f"revision (spec 8)")
        run.rules = logcheck.load_rules(os.path.join(inp, "config", "warn_whitelist.txt"))

        with open(os.path.join(inp, impl["rtl"]), errors="replace") as f:
            verdict["rtl_lint"] = lint_rtl(f.read())
        if verdict["rtl_lint"]:
            raise GradeError(f"RTL lint: {impl['rtl']} uses constructs a candidate must not use (file access, "
                             f"plusargs, shell, waveform dumps, `include, macro token pasting; spec 1): "
                             + "; ".join(verdict["rtl_lint"][:10]))
        run.require("env_snapshot", ["bash", os.path.join(REPO, "env", "snapshot.sh"), "check"], "env_snapshot.log")
        verdict["env_ids"] = env_ids()
        text = run.require("versions", versions_argv(), "versions.log")
        verdict["tool_versions"] = text.strip().splitlines()           # spec 3.5, 4.1

        run.require("gen_vectors", [sys.executable, "-B", os.path.join(inp, "ref", "gen_vectors.py"), "--L", str(L),
                                    "--lmax", str(lmax), "--seed", str(s["seed"]), "--out", "vectors"],
                    "vectors/gen.log")
        others["vectors/manifest.json"] = sha256(os.path.join(root, "vectors", "manifest.json"))
        with open(os.path.join(root, "vectors", "manifest.json")) as f:
            manifest = json.load(f)
        vec = os.path.join(root, "vectors", "vectors.txt")
        if sha256(vec) != manifest["vectors_sha256"]:
            raise GradeError("vectors.txt does not match the manifest hash")
        others["vectors/vectors.txt"] = manifest["vectors_sha256"]
        read_only(vec)
        read_only(os.path.join(root, "vectors", "manifest.json"))
        if not manifest["coverage"]["ok"]:
            raise GradeError("coverage requirements not met: " + "; ".join(manifest["coverage"]["failures"]))
        expected = manifest["expected_checked"]
        plus = [f"+VEC={vec}", f"+NVEC={manifest['n_vectors']}", f"+L={L}", f"+LMAX={lmax}", f"+EXP={expected}"]
        tb = os.path.join(inp, "tb", "tb_dot4sat.v")
        rtl = os.path.join(inp, impl["rtl"])

        run.require("rtl_compile", ["iverilog", "-g2012", "-o", "rtl_sim/sim.vvp", tb, rtl], "rtl_sim/compile.log")
        rc, text, problems = run.cmd("rtl_sim", ["vvp", "-n", "rtl_sim/sim.vvp"] + plus, "rtl_sim/sim.log")
        frozen_ok("rtl_sim")
        ok, msg = check_sim.check(text, rc, expected)
        verdict["rtl_sim"] = msg
        if not ok or problems:
            raise GradeError(f"RTL simulation: {msg}; " + "; ".join(problems[:5]))

        netlist = os.path.join(root, "synth", "netlist.v")
        env = {k: v for k, v in os.environ.items() if k != "SYNTH_LIB"}
        env.update({"TOP": impl["top"], "RTL": rtl, "OUT": netlist})
        os.makedirs(os.path.join(root, "synth"))
        run.require("synth", ["yosys", "-q", "-c", os.path.join(inp, "scripts", "synth_case01.tcl"),
                              "-l", os.path.join(root, "synth", "yosys.log")], "synth/yosys.stdout", env,
                    extra_logs=("synth/yosys.log",))
        with open(os.path.join(root, "synth", "yosys.log")) as f:
            areas = re.findall(r"Chip area for module '\\?%s': ([0-9.]+)" % re.escape(impl["top"]), f.read())
        if not areas:
            raise GradeError("no chip area in yosys.log")
        verdict["area_um2"] = float(areas[-1])
        verdict["area"] = area_record(s, verdict["area_um2"])
        net_sha = sha256(netlist)
        verdict["netlist_sha256"] = net_sha

        def same_netlist(stage):
            if sha256(netlist) != net_sha:
                raise GradeError(f"netlist changed before {stage}")
            verdict.setdefault("netlist_checks", []).append(stage)

        want = {}
        with open(os.path.join(inp, "config", "gl_models.sha256")) as f:
            gl_lines = f.readlines()
        for line in gl_lines:
            if line.strip():
                digest, name = line.split()
                want[name] = digest
        models = []
        for name in GL_MODELS:
            path = os.path.join(os.environ["SKY130_HD"], "verilog", name)
            if sha256(path) != want.get(name):
                raise GradeError(f"gate-level model {name} does not match config/gl_models.sha256")
            models.append(path)
        same_netlist("gate-level simulation")
        run.require("gl_compile", ["iverilog", "-g2012", "-DFUNCTIONAL", "-DUNIT_DELAY=#1", "-o", "gl_sim/sim.vvp",
                                   tb, netlist] + models, "gl_sim/compile.log")    # tb first: timescale (spec 3.5)
        rc, text, problems = run.cmd("gl_sim", ["vvp", "-n", "gl_sim/sim.vvp"] + plus, "gl_sim/sim.log")
        frozen_ok("gl_sim")
        ok, msg = check_sim.check(text, rc, expected)
        verdict["gl_sim"] = msg
        if not ok or problems:
            raise GradeError(f"gate-level simulation: {msg}; " + "; ".join(problems[:5]))
        verdict["functional_pass"] = True

        sta_dir = os.path.join(root, "sta")
        os.makedirs(sta_dir)
        env = dict(os.environ, TOP=impl["top"], NETLIST=netlist, T_NS=repr(T), CLOAD_PF=repr(cload),
                   SCENESET=args.sceneset, OUTDIR=sta_dir, CASE_DIR=inp)
        same_netlist("STA")
        run.require("sta", ["sta", "-no_init", "-no_splash", "-exit", os.path.join(inp, "scripts", "sta_run.tcl")],
                    "sta/sta.log", env)
        same_netlist("after STA")
        run.require("check_sta", [sys.executable, "-B", os.path.join(inp, "scripts", "check_sta.py"), sta_dir, repr(T),
                                  repr(cload), args.sceneset], "sta/check.log")
        with open(os.path.join(sta_dir, "sta_check.json")) as f:
            sta = json.load(f)
        for rel in IN_PROCESS:                         # the grader's own code must not change during the run
            if sha256(os.path.join(CASE, rel)) != frozen[rel]:
                raise GradeError(f"{rel} changed during the run")
        frozen_ok("end of run")
        target = timing_target(s, sta)
        verdict["analysis_valid"] = True
        verdict.update({"latency_L": L, "throughput": "1 transaction per cycle",
                        "worst_setup": sta["worst_setup"], "worst_hold": sta["worst_hold"],
                        "hold_note": sta["hold_note"], "topology": sta["topology"], "corners": sta["corners"],
                        "timing_target": target})
    finally:
        verdict["whitelist_hits"] = {str(k): v for k, v in run.hits.items()}
        with open(os.path.join(root, "steps.json"), "w") as f:
            json.dump(run.steps, f, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", required=True)
    ap.add_argument("--T", type=float)
    ap.add_argument("--cload", type=float)
    ap.add_argument("--lmax", type=int)
    ap.add_argument("--seed", type=int, help="pre-F1 only (default 1); after F1 the seed comes from config/f1.cfg")
    ap.add_argument("--sceneset", choices=("std", "all"), default="std")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        if e.code:                                     # usage error (argparse has printed the reason to stderr)
            print(f"GRADE FAIL: invalid command line (argparse exit {e.code}; see the usage message)", flush=True)
        raise
    verdict = {"functional_pass": False, "analysis_valid": False}
    previous = signal.signal(signal.SIGTERM, on_sigterm)
    try:
        try:
            grade(args, verdict)
            code = 0
        except (GradeError, logcheck.RuleError, OSError, KeyError, ValueError) as e:
            verdict["error"] = f"{type(e).__name__}: {e}"
            code = 1
        except Exception as e:                         # an unexpected internal error is still a failed evaluation
            verdict["error"] = f"{type(e).__name__}: {e}"
            verdict["traceback"] = traceback.format_exc()
            code = 1
        except BaseException as e:                     # Ctrl-C, SIGTERM (see on_sigterm): record, then stop
            verdict["error"] = f"interrupted: {type(e).__name__}"
            finish(verdict, 1)
            raise
        return finish(verdict, code)
    finally:
        signal.signal(signal.SIGTERM, previous)


def on_sigterm(signum, frame):
    raise SystemExit(143)                              # SIGTERM takes the same path as Ctrl-C (final review M2)


def finish(verdict, code):
    """Write verdict.json (when a run dir exists) and print the final stdout line: always exactly one
    'GRADE OK: ...' or 'GRADE FAIL: ...' line (a multi-line error is joined with ' | ')."""
    if "run_id" in verdict:
        try:
            with open(os.path.join(CASE, "runs", verdict["run_id"], "verdict.json"), "w") as f:
                json.dump(verdict, f, indent=1)
        except OSError as e:
            verdict["error"] = "; ".join(filter(None, [verdict.get("error"), f"cannot write verdict.json: {e}"]))
            code = 1
    if code:
        print("GRADE FAIL: " + " | ".join(ln.strip() for ln in str(verdict["error"]).splitlines() if ln.strip()),
              flush=True)
    else:
        print(ok_line(verdict), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
