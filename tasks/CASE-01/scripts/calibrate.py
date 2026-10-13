"""Clock-period calibration (spec 5). Run inside WSL from tasks/CASE-01, after a valid pre-F1 baseline run:
  python3 scripts/calibrate.py --run runs/<baseline run_id>
Re-runs STA (std corners) on the baseline run's FROZEN netlist, SDC, scripts and whitelist at trial periods until
the worst setup slack S satisfies -0.20 <= S/T <= -0.10. Everything goes to a new session directory
runs/<ts>-calib-<baseline run_id>/ (calib_record.json/.md written after every trial, also on failure).
Refuses to start after F1 (config/f1.cfg exists) and refuses sources that are not the frozen baseline (P1 M6).
Freezes nothing: the author reviews the session (checkpoint B) and F1 records which session was used.
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys

import logcheck

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(CASE))
LO, HI, R = -0.20, -0.10, 0.15
MAX_TRIALS = 20
STD = ["tt_025C_1v80", "tt_100C_1v80", "ss_100C_1v60", "ss_n40C_1v60", "ff_n40C_1v95", "ff_100C_1v95"]
BASELINE_RTL_SHA = "422ba000b48903558d797510cd4d0189b3fac9f83ba4ce4a1b22eb497194c802"   # evidence/F0_v1.1_*
RECIPE_SHA = "b517940e44b8d0a87a7b649f7f3355fa8960759ba436a8acf5684bf9bc674049"         # spec 4.2, v1.2
MODEL_FILES = ("scripts/sta_run.tcl", "scripts/check_sta.py", "sdc/case01_sdc.tcl", "config/warn_whitelist.txt")


class CalibError(Exception):
    pass


# Wall-clock limits per subprocess, in seconds: the same values as STEP_TIMEOUT_S in grade.py for these steps
# (task review of Task 11). A hung tool or an interrupted calibration must not leave orphans or a silent stall.
TIMEOUT_S = {"env_snapshot": 600, "versions": 120, "sta": 3600, "check_sta": 600}


def kill_tree(proc):
    """Kill proc and every process it started, on Windows as well as POSIX. Incident 2026-10-12: os.killpg does not
    exist on Windows; the AttributeError skipped the kill and an orphaned `yes` filled the system disk."""
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


def run_limited(name, argv, log_path, env=None):
    """Run argv with stdout+stderr to log_path and return its exit code. After TIMEOUT_S[name] seconds, or if this
    process is interrupted, the whole process tree is killed; a timeout raises CalibError."""
    with open(log_path, "w") as f:
        proc = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            return proc.wait(timeout=TIMEOUT_S[name])
        except BaseException as e:
            kill_tree(proc)
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"pid {proc.pid} survived the kill; stop it by hand") from e
            if isinstance(e, subprocess.TimeoutExpired):
                raise CalibError(f"{name} timed out after {TIMEOUT_S[name]} s and was killed (see {log_path})") \
                    from None
            raise


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def validate_source(run_root):
    """The source must be a valid pre-F1 std-corner evaluation of the frozen baseline; returns its verdict."""
    with open(os.path.join(run_root, "verdict.json")) as f:
        v = json.load(f)
    if not (v.get("functional_pass") and v.get("analysis_valid")):
        raise CalibError("source run is not functionally passing with a valid analysis")
    if v.get("phase") != "pre-F1" or v.get("sceneset") != "std":
        raise CalibError("source run must be a pre-F1 run on the std corners")
    impl = v.get("impl", {})
    if (impl.get("name"), impl.get("rtl"), impl.get("L"), impl.get("top")) != ("base", "rtl/dot4sat.v", "1", "dot4sat"):
        raise CalibError(f"source run is not the baseline implementation: {impl}")
    recorded = {}
    with open(os.path.join(run_root, "inputs.sha256")) as f:
        for line in f:
            digest, rel = line.split(None, 1)
            recorded[rel.strip()] = digest
    if recorded.get("rtl/dot4sat.v") != BASELINE_RTL_SHA or recorded.get("scripts/synth_case01.tcl") != RECIPE_SHA:
        raise CalibError("source run's RTL or synthesis recipe is not the frozen baseline/recipe")
    for rel, digest in recorded.items():
        if sha256(os.path.join(run_root, "inputs", rel)) != digest:
            raise CalibError(f"frozen input {rel} of the source run was modified")
    if sha256(os.path.join(run_root, "synth", "netlist.v")) != v.get("netlist_sha256"):
        raise CalibError("source run netlist does not match its recorded hash")
    with open(os.path.join(run_root, "sta", "sta_check.json")) as f:
        if not json.load(f).get("valid"):
            raise CalibError("source run STA check is not valid")
    return v


def model_fingerprint(run_root):
    inp = os.path.join(run_root, "inputs")
    fp = {rel: sha256(os.path.join(inp, rel)) for rel in MODEL_FILES}
    fp["netlist"] = sha256(os.path.join(run_root, "synth", "netlist.v"))
    return fp


def trial(T, sta, where, fingerprint):
    S = sta["worst_setup"]["slack"]
    return {"T_ns": round(T, 2), "S_ns": S, "S_over_T": S / T, "worst_corner": sta["worst_setup"]["corner"],
            "worst_category": sta["worst_setup"]["category"], "worst_hold": sta["worst_hold"],
            "ws_max": {c: v["ws_max"] for c, v in sta["corners"].items()},
            "ws_min": {c: v["ws_min"] for c, v in sta["corners"].items()}, "sta_dir": where, "model": fingerprint}


def sta_at(run_root, verdict, session, T, idx):
    """One trial on the source run's frozen model; only T (and what derives from it) changes."""
    inp = os.path.join(run_root, "inputs")
    out = os.path.join(session, "trials", f"{idx:02d}_T{T:.2f}")
    os.makedirs(out)
    rules = logcheck.load_rules(os.path.join(inp, "config", "warn_whitelist.txt"))
    env = dict(os.environ, TOP="dot4sat", NETLIST=os.path.join(run_root, "synth", "netlist.v"), T_NS=f"{T:.2f}",
               CLOAD_PF=repr(verdict["C_load_pF"]), SCENESET="std", OUTDIR=out, CASE_DIR=inp)
    fp_before = model_fingerprint(run_root)
    rc = run_limited("sta", ["sta", "-no_init", "-no_splash", "-exit", os.path.join(inp, "scripts", "sta_run.tcl")],
                     os.path.join(out, "sta.log"), env=env)
    problems, _ = logcheck.scan("sta", os.path.join(out, "sta.log"), rules)
    if rc or problems:
        raise CalibError(f"STA at T={T:.2f}: exit {rc}; " + "; ".join(problems[:5]))
    rc = run_limited("check_sta", [sys.executable, "-B", os.path.join(inp, "scripts", "check_sta.py"), out,
                                   f"{T:.2f}", repr(verdict["C_load_pF"]), "std"], os.path.join(out, "check.log"))
    if rc:
        raise CalibError(f"STA analysis invalid at T={T:.2f} (see {out}/check.log)")
    if model_fingerprint(run_root) != fp_before:
        raise CalibError("frozen model changed during a trial")
    with open(os.path.join(out, "sta_check.json")) as f:
        return trial(T, json.load(f), os.path.relpath(out, CASE), fp_before)


def search(run_root, verdict, session, record, save, sta=None):
    """Formula guess, then measured bracketing and bisection at 0.01 ns resolution (spec 5)."""
    sta = sta or sta_at
    with open(os.path.join(run_root, "sta", "sta_check.json")) as f:
        t0 = trial(verdict["T_ns"], json.load(f), os.path.relpath(os.path.join(run_root, "sta"), CASE),
                   model_fingerprint(run_root))
    trials = record["trials"] = [t0]
    record.update({"T0_ns": t0["T_ns"], "S0_ns": t0["S_ns"]})
    formula = t0["worst_category"] in ("in2reg", "reg2out")
    record["formula_applicable"] = formula
    if formula:
        record["D_eff_ns"] = 0.8 * t0["T_ns"] - t0["S_ns"]
        T = round(record["D_eff_ns"] / (0.8 + R), 2)
    else:
        T = t0["T_ns"]
    save(record)
    for idx in range(1, MAX_TRIALS + 2):
        lo = hi = None                 # lo: largest T too tight (S/T < LO); hi: smallest T too loose (S/T > HI)
        for t in trials:
            if t["S_over_T"] < LO:
                lo = t["T_ns"] if lo is None else max(lo, t["T_ns"])
            elif t["S_over_T"] > HI:
                hi = t["T_ns"] if hi is None else min(hi, t["T_ns"])
            else:
                record.update({"status": "candidate_found", "chosen": t})
                return record
        if idx > MAX_TRIALS:
            break
        if idx > 1 or T in {t["T_ns"] for t in trials}:   # after the formula guess: bracket and bisect
            if lo is not None and hi is not None:
                T = round((lo + hi) / 2, 2)
            elif lo is not None:
                T = round(lo * 1.1, 2)
            else:
                T = round(hi * 0.9, 2)
        if T <= 0 or T in {t["T_ns"] for t in trials}:
            raise CalibError(f"search stalled at T={T:.2f} (0.01 ns resolution)")
        trials.append(sta(run_root, verdict, session, T, idx))
        save(record)
    record["status"] = f"failed: no period within target after {MAX_TRIALS} trials"
    return record


def write_md(record, path):
    lines = ["# CASE-01 校准记录（自动生成，供作者在检查点 B 审阅）", "",
             f"- 来源运行：`{record['source_run']}`，网表 sha256 `{record.get('netlist_sha256')}`",
             f"- C_load：{record.get('C_load_pF')} pF；规则：S 取 std 六点真实最差 setup slack，目标 "
             f"{LO} ≤ S/T ≤ {HI}，公式试探 r = {R}",
             f"- 公式前提成立：{record.get('formula_applicable')}" +
             (f"，D_eff = {record['D_eff_ns']:.4f} ns" if "D_eff_ns" in record else ""),
             f"- 状态：{record.get('status', 'running')}" + (f"；原因：{record['error']}" if "error" in record else ""),
             "", "## 试探汇总", "",
             "| # | T (ns) | S (ns) | S/T | 最差 corner | 类别 | 最小 hold（corner） | STA 目录 |",
             "|---|---|---|---|---|---|---|---|"]
    for i, t in enumerate(record.get("trials", [])):
        lines.append(f"| {i} | {t['T_ns']:.2f} | {t['S_ns']:.4f} | {t['S_over_T']:.4f} | {t['worst_corner']} | "
                     f"{t['worst_category']} | {t['worst_hold']['slack']:.4f}（{t['worst_hold']['corner']}） | "
                     f"`{t['sta_dir']}` |")
    lines += ["", "## 六点逐项（setup / hold 的真实最差 slack，ns）", "",
              "| # | T (ns) | " + " | ".join(STD) + " |", "|---|---|" + "---|" * len(STD)]
    for i, t in enumerate(record.get("trials", [])):
        lines.append(f"| {i} | {t['T_ns']:.2f} | " +
                     " | ".join(f"{t['ws_max'][c]:.4f} / {t['ws_min'][c]:.4f}" for c in STD) + " |")
    with open(path, "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    args = ap.parse_args(argv)
    if os.path.exists(os.path.join(CASE, "config", "f1.cfg")):
        print("CALIBRATION FAIL: config/f1.cfg exists; a new calibration after F1 is an evaluation revision")
        return 1
    run_root = os.path.join(CASE, args.run)
    session = os.path.join(CASE, "runs", f"{datetime.datetime.now():%Y%m%d-%H%M%S}-calib-{os.path.basename(run_root)}")
    os.makedirs(session)
    shutil.copyfile(os.path.abspath(__file__), os.path.join(session, "calibrate.py"))
    record = {"source_run": os.path.relpath(run_root, CASE), "session": os.path.relpath(session, CASE),
              "command": " ".join([os.path.basename(sys.executable)] + sys.argv),
              "calibrate_sha256": sha256(os.path.abspath(__file__)), "steps": []}

    def save(rec):
        with open(os.path.join(session, "calib_record.json"), "w", newline="\n") as f:
            json.dump(rec, f, indent=1)
        write_md(rec, os.path.join(session, "calib_record.md"))

    code = 1
    try:
        for name, cmd in (("env_snapshot", ["bash", os.path.join(REPO, "env", "snapshot.sh"), "check"]),
                          ("versions", ["bash", "-c", "set -o pipefail; yosys -V; echo \"OpenSTA $(sta -version)\"; "
                                                      "python3 --version"])):
            rc = run_limited(name, cmd, os.path.join(session, f"{name}.log"))
            record["steps"].append({"step": name, "returncode": rc})
            if rc:
                raise CalibError(f"{name} failed (see {name}.log)")
        verdict = validate_source(run_root)
        record.update({"netlist_sha256": verdict["netlist_sha256"], "C_load_pF": verdict["C_load_pF"]})
        search(run_root, verdict, session, record, save)
        code = 0 if record["status"] == "candidate_found" else 1
    except (CalibError, logcheck.RuleError, OSError, KeyError, ValueError) as e:
        record.update({"status": "failed", "error": f"{type(e).__name__}: {e}"})
    except BaseException as e:       # interrupted (e.g. Ctrl-C): leave a failed record behind, then stop
        record.update({"status": "failed", "error": f"interrupted: {type(e).__name__}"})
        save(record)
        raise
    save(record)
    msg = (f"T={record['chosen']['T_ns']:.2f} ns, S/T={record['chosen']['S_over_T']:.4f}"
           if "chosen" in record else record.get("error", ""))
    print(f"CALIBRATION {record['status']}: {msg} -> {record['session']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
