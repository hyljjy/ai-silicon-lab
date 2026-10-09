"""CASE-01 grader (spec 6): one evaluation of one implementation.

Run inside WSL (login shell) from tasks/CASE-01:
  python3 scripts/grade.py --impl config/impl.base.cfg --T 20 --cload 0.0024 [--lmax 3] [--seed 1] [--sceneset std]
After F1, config/f1.cfg is the only source of T, C_load and L_max; passing --T/--cload/--lmax is then an error.
The first output line is RUN_ID=<id>. Exit 0 only if both simulations pass and the STA analysis is valid;
negative slack is reported, not a failure. Never overwrites: every evaluation gets a new runs/<run_id>/.
All inputs are first copied to runs/<run_id>/inputs/ (same relative paths) and every step runs from that frozen
copy (P1 M6); every step's log is checked against the frozen warning whitelist (P1 M5).
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys

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
    for raw in open(path):
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


class Run:
    def __init__(self, root, rules):
        self.root = root
        self.rules = rules
        self.steps = []
        self.hits = {}

    def cmd(self, name, argv, log, env=None, extra_logs=()):
        """Run argv in the run dir, stdout+stderr to <root>/<log>, then check this step's logs immediately.
        A step that outlives STEP_TIMEOUT_S[name] is killed together with its whole process group and fails."""
        path = os.path.join(self.root, log)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        limit = STEP_TIMEOUT_S[name]
        timed_out = False
        with open(path, "w") as f:
            proc = subprocess.Popen(argv, cwd=self.root, env=env, stdin=subprocess.DEVNULL, stdout=f,
                                    stderr=subprocess.STDOUT, start_new_session=True)
            try:
                rc = proc.wait(timeout=limit)
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                rc = proc.wait()
        problems = []
        for lg in (log,) + tuple(extra_logs):
            if timed_out and not os.path.exists(os.path.join(self.root, lg)):
                continue                                  # a step killed early may not have written its extra logs
            p, hits = logcheck.scan(STEP_TOOL[name], os.path.join(self.root, lg), self.rules)
            problems += p
            for k, v in hits.items():
                self.hits[k] = self.hits.get(k, 0) + v
        self.steps.append({"step": name, "argv": argv, "returncode": rc, "timed_out": timed_out,
                           "timeout_s": limit, "logs": [log, *extra_logs], "log_problems": problems})
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


def settings(args):
    f1 = os.path.join(CASE, "config", "f1.cfg")
    if os.path.exists(f1):
        if args.T is not None or args.cload is not None or args.lmax is not None:
            raise GradeError("config/f1.cfg exists: T, C_load and L_max are frozen; do not pass --T/--cload/--lmax")
        kv = read_kv(f1)
        return float(kv["T_ns"]), float(kv["C_load_pF"]), int(kv["L_max"]), "post-F1"
    if args.T is None or args.cload is None:
        raise GradeError("before F1, --T and --cload are required")
    return args.T, args.cload, 3 if args.lmax is None else args.lmax, "pre-F1"


def grade(args, verdict):
    T, cload, lmax, phase = settings(args)
    if "SYNTH_LIB" in os.environ:
        raise GradeError("SYNTH_LIB is set; the synthesis recipe must not be overridden (spec 4.2)")
    impl = read_kv(os.path.join(CASE, args.impl))
    for key in ("name", "top", "rtl", "L"):
        if key not in impl:
            raise GradeError(f"{args.impl}: missing key {key}")
    if not re.fullmatch(r"[1-9]", impl["L"]) or not 1 <= int(impl["L"]) <= lmax:
        raise GradeError(f"{args.impl}: L={impl['L']!r} is not an integer in 1..{lmax}")
    if not re.fullmatch(r"[A-Za-z0-9_]+", impl["name"]):
        raise GradeError(f"{args.impl}: bad name {impl['name']!r}")
    L = int(impl["L"])
    if not os.path.isfile(os.path.join(CASE, impl["rtl"])):
        raise GradeError(f"RTL {impl['rtl']} not found")

    run_id = f"{datetime.datetime.now():%Y%m%d-%H%M%S}-{impl['name']}-T{T:g}"
    root = os.path.join(CASE, "runs", run_id)
    os.makedirs(root)                                   # FileExistsError if it exists: never overwrite
    print(f"RUN_ID={run_id}", flush=True)
    verdict.update({"run_id": run_id, "phase": phase, "impl": impl, "T_ns": T, "C_load_pF": cload,
                    "L_max": lmax, "seed": args.seed, "sceneset": args.sceneset})

    # freeze every input at its relative path; all steps below read only the frozen copy
    inp = os.path.join(root, "inputs")
    rels = [os.path.relpath(os.path.join(CASE, args.impl), CASE), impl["rtl"]] + FROZEN_INPUTS
    if phase == "post-F1":
        rels.append("config/f1.cfg")
    frozen = {}
    with open(os.path.join(root, "inputs.sha256"), "w") as f:
        for rel in rels:
            if rel.startswith("..") or os.path.isabs(rel):
                raise GradeError(f"input {rel} is outside tasks/CASE-01")
            dst = os.path.join(inp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(CASE, rel), dst)
            frozen[rel] = sha256(dst)
            f.write(f"{frozen[rel]}  {rel}\n")
    run = Run(root, logcheck.load_rules(os.path.join(inp, "config", "warn_whitelist.txt")))
    try:
        run.require("env_snapshot", ["bash", os.path.join(REPO, "env", "snapshot.sh"), "check"], "env_snapshot.log")
        text = run.require("versions", ["bash", "-c", "set -o pipefail; iverilog -V 2>&1 | head -1; yosys -V; "
                                        "echo \"OpenSTA $(sta -version)\"; python3 --version"], "versions.log")
        verdict["tool_versions"] = text.strip().splitlines()           # spec 3.5, 4.1

        run.require("gen_vectors", [sys.executable, "-B", os.path.join(inp, "ref", "gen_vectors.py"), "--L", str(L),
                                    "--lmax", str(lmax), "--seed", str(args.seed), "--out", "vectors"],
                    "vectors/gen.log")
        with open(os.path.join(root, "vectors", "manifest.json")) as f:
            manifest = json.load(f)
        vec = os.path.join(root, "vectors", "vectors.txt")
        if sha256(vec) != manifest["vectors_sha256"]:
            raise GradeError("vectors.txt does not match the manifest hash")
        if not manifest["coverage"]["ok"]:
            raise GradeError("coverage requirements not met: " + "; ".join(manifest["coverage"]["failures"]))
        expected = manifest["expected_checked"]
        plus = [f"+VEC={vec}", f"+NVEC={manifest['n_vectors']}", f"+L={L}", f"+LMAX={lmax}", f"+EXP={expected}"]
        tb = os.path.join(inp, "tb", "tb_dot4sat.v")
        rtl = os.path.join(inp, impl["rtl"])

        run.require("rtl_compile", ["iverilog", "-g2012", "-o", "rtl_sim/sim.vvp", tb, rtl], "rtl_sim/compile.log")
        rc, text, problems = run.cmd("rtl_sim", ["vvp", "-n", "rtl_sim/sim.vvp"] + plus, "rtl_sim/sim.log")
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
        net_sha = sha256(netlist)
        verdict["netlist_sha256"] = net_sha

        def same_netlist(stage):
            if sha256(netlist) != net_sha:
                raise GradeError(f"netlist changed before {stage}")
            verdict.setdefault("netlist_checks", []).append(stage)

        want = {}
        for line in open(os.path.join(inp, "config", "gl_models.sha256")):
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
        verdict["analysis_valid"] = True
        verdict.update({"latency_L": L, "throughput": "1 transaction per cycle",
                        "worst_setup": sta["worst_setup"], "worst_hold": sta["worst_hold"],
                        "hold_note": sta["hold_note"], "topology": sta["topology"], "corners": sta["corners"],
                        "timing_target": "not evaluated here: candidates are compared against the frozen baseline"})
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
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--sceneset", choices=("std", "all"), default="std")
    args = ap.parse_args(argv)
    verdict = {"functional_pass": False, "analysis_valid": False}
    code = 0
    try:
        grade(args, verdict)
    except (GradeError, logcheck.RuleError, OSError, KeyError, ValueError) as e:
        verdict["error"] = f"{type(e).__name__}: {e}"
        code = 1
    if "run_id" in verdict:
        with open(os.path.join(CASE, "runs", verdict["run_id"], "verdict.json"), "w") as f:
            json.dump(verdict, f, indent=1)
    if code:
        print(f"GRADE FAIL: {verdict['error']}")
    else:
        print(f"GRADE OK: {verdict['run_id']} functional_pass analysis_valid "
              f"worst_setup={verdict['worst_setup']} worst_hold={verdict['worst_hold']} area={verdict['area_um2']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
