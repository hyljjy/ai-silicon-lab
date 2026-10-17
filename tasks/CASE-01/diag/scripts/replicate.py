"""Replicate the tool side of CASE-01 stage A from a fresh clone (not a pre-registered file; added 2026-10-17).

Run inside WSL (login shell) from tasks/CASE-01, after regenerating the F1 baseline with the frozen grader:
  python3 scripts/grade.py --impl config/impl.base.cfg                 # first line: RUN_ID=<id>
  python3 -B diag/scripts/replicate.py --f1-run runs/<id> [--groups base,recheck]

What it checks (see REPRODUCE.md at the repository root):
 1. the regenerated F1 run against the archived F1 evidence: the synthesized netlist has the sha256 that the diag
    executor pins (NETLIST_SHA), and sta/sta_results.tsv and the given ss_n40C in2reg report equal
    evidence/F1/sta_results.tsv and evidence/F1/f1_run_cat_ss_n40C_1v60_in2reg_max.rpt byte for byte;
 2. every committed base check and operator recheck is re-run through run_query.main with the query text that was
    run (queries/<group>/<dir>/query.tcl), the recorded mode and --strict-log, against the regenerated F1 run;
 3. each new query_full.txt is compared with the committed one: "identical", "identical-masked" (equal once object
    addresses such as _0000561c2a3b4c50_p_Port are masked; OpenSTA prints a different address in every process),
    or "different".
The executor's pre-registration self-check (rules/executor.sha256 against git and the tag diag-prereg) is skipped:
run_query.py was changed after the study (process-tree kill on Windows), and a replication is not part of the
pre-registered study. Every other environment check of run_query.py still runs (env/snapshot.sh check, the netlist
hash, the frozen inputs, the STA records byte for byte against the F1 run, the log check). Each replicated
result.json gets "replication": {...}. Nothing under diag/queries/ is written.
Exit 0 only if step 1 holds and every query is env_ok, completed and identical or identical-masked.

--allow-tool-drift: OpenSTA and CUDD are built from source, so on another machine their binaries differ from
env/tools.sha256 even at the same commit, and env/snapshot.sh check reports "DRIFT: tool binaries differ". With this
flag a query whose only environment problem is that one drift line is accepted and reported as "tool drift"; every
other drift (kit scripts, liberty files, snapshot files) still fails. The netlist hash and the query outputs remain
the test of whether the replication holds.
"""
import argparse
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from diagpaths import CASE, DIAG  # noqa: E402

ADDRESS = re.compile(r"_[0-9a-f]{8,}_p_[A-Za-z_]+")
GROUPS = {"base": "queries/base", "recheck": "queries/recheck"}
F1_EVIDENCE = (("sta/sta_results.tsv", "evidence/F1/sta_results.tsv"),
               ("sta/cat_ss_n40C_1v60_in2reg_max.rpt", "evidence/F1/f1_run_cat_ss_n40C_1v60_in2reg_max.rpt"))


TOOL_DRIFT = "DRIFT: tool binaries differ from tools.sha256"


def only_tool_drift(snapshot_log):
    """True when env/snapshot.sh check failed only because the tool binaries differ from tools.sha256."""
    drift = [l.strip() for l in snapshot_log.splitlines() if l.startswith(("DRIFT:", "FAIL: snapshot files"))]
    return drift == [TOOL_DRIFT]


def mask(text):
    return ADDRESS.sub("<addr>", text)


def compare_text(new, old):
    """Return (verdict, first differing line pair or None)."""
    if new == old:
        return "identical", None
    if mask(new) == mask(old):
        return "identical-masked", None
    a, b = mask(new).splitlines(), mask(old).splitlines()
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else "<missing>"
        y = b[i] if i < len(b) else "<missing>"
        if x != y:
            return "different", (i + 1, x, y)
    return "different", None


def committed_queries(groups, diag=DIAG):
    """[(group, dir name, query.tcl path, recorded result)] for every committed query of the given groups."""
    out = []
    for g in groups:
        base = os.path.join(diag, GROUPS[g])
        for name in sorted(os.listdir(base)):
            d = os.path.join(base, name)
            if not os.path.isdir(d):
                continue
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                rec = json.load(f)
            out.append((g, name, os.path.join(d, "query.tcl"), rec))
    return out


def check_f1(f1_run, case=CASE):
    import run_query
    problems = []
    netlist = os.path.join(f1_run, "synth", "netlist.v")
    if not os.path.isfile(netlist):
        return [f"no netlist at {netlist}"]
    if run_query.sha256(netlist) != run_query.NETLIST_SHA:
        problems.append("regenerated netlist sha256 differs from the F1 netlist")
    for new_rel, old_rel in F1_EVIDENCE:
        with open(os.path.join(f1_run, new_rel), "rb") as f:
            new = f.read()
        with open(os.path.join(case, old_rel), "rb") as f:
            old = f.read()
        if new != old:
            problems.append(f"{new_rel} differs from {old_rel}")
    return problems


def run_one(qid, query, mode, f1_run):
    """Run one query through run_query.main against f1_run, skipping only the pre-registration self-check."""
    import run_query
    run_query.F1_RUN = os.path.abspath(f1_run)
    run_query.executor_problems = lambda *a, **k: []
    run_query.manifest_committed = lambda *a, **k: True
    before = set(os.listdir(os.path.join(CASE, "runs")))
    rc = run_query.main(["--id", f"rep-{qid}", "--query", query, "--mode", mode, "--strict-log"])
    new = sorted(set(os.listdir(os.path.join(CASE, "runs"))) - before)
    new = [d for d in new if d.endswith(f"-diag-rep-{qid}")]
    if len(new) != 1:
        return rc, None
    run_dir = os.path.join(CASE, "runs", new[0])
    path = os.path.join(run_dir, "result.json")
    with open(path, encoding="utf-8") as f:
        res = json.load(f)
    res["replication"] = {"by": "diag/scripts/replicate.py", "f1_run": os.path.relpath(f1_run, CASE),
                          "prereg_self_check": "skipped", "executor_committed": "not checked"}
    res["executor_committed"] = None
    with open(path, "w", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    return rc, run_dir


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--f1-run", required=True, help="the regenerated F1 run directory, e.g. runs/<RUN_ID>")
    ap.add_argument("--groups", default="base,recheck")
    ap.add_argument("--out", help="summary file (default runs/<ts>-replicate.md)")
    ap.add_argument("--allow-tool-drift", action="store_true",
                    help="accept env/snapshot.sh failing only on the tool binary fingerprints (built from source)")
    args = ap.parse_args(argv)
    f1_run = os.path.abspath(args.f1_run if os.path.isabs(args.f1_run) else os.path.join(CASE, args.f1_run))
    groups = [g for g in args.groups.split(",") if g]
    lines = [f"# CASE-01 stage A replication ({datetime.datetime.now():%Y-%m-%d %H:%M})", "",
             f"F1 run: `{os.path.relpath(f1_run, CASE)}`", ""]
    f1_problems = check_f1(f1_run)
    lines += ["## F1 baseline", ""] + ([f"- FAIL: {p}" for p in f1_problems] or
                                        ["- OK: netlist sha256, sta_results.tsv and the given report equal F1"]) + [""]
    print("F1 " + ("OK" if not f1_problems else "FAIL: " + "; ".join(f1_problems)), flush=True)
    rows, bad = [], len(f1_problems)
    for group, name, query, rec in committed_queries(groups):
        rc, run_dir = run_one(name, query, rec["mode"], f1_run)
        if run_dir is None:
            verdict, where, status = "no run", None, "-"
        else:
            with open(os.path.join(run_dir, "result.json"), encoding="utf-8") as f:
                res = json.load(f)
            env_ok = res["env_ok"]
            if not env_ok and args.allow_tool_drift and res["env_problems"] == ["env/snapshot.sh check failed"]:
                with open(os.path.join(run_dir, "snapshot.log"), encoding="utf-8", errors="replace") as f:
                    env_ok = only_tool_drift(f.read())
            drift_note = " (tool drift accepted)" if env_ok and not res["env_ok"] else ""
            status = f"env_ok={res['env_ok']}{drift_note} {res['query_status']}"
            with open(os.path.join(run_dir, "query_full.txt"), encoding="utf-8", errors="replace") as f:
                new = f.read()
            with open(os.path.join(DIAG, GROUPS[group], name, "query_full.txt"), encoding="utf-8", errors="replace") as f:
                old = f.read()
            verdict, where = compare_text(new, old)
            log_ok = res["query_log_ok"]
            if not env_ok or not log_ok or res["query_status"] != "completed":
                verdict = "env/log problem: " + verdict
        if verdict not in ("identical", "identical-masked"):
            bad += 1
        detail = f"line {where[0]}: new `{where[1][:80]}` / committed `{where[2][:80]}`" if where else ""
        rows.append(f"| {group} | {name} | {status} | {verdict} | {detail} |")
        print(f"{name}: {verdict} ({status})", flush=True)
    lines += ["## Queries", "", "| group | query | run | compared with committed output | first difference |",
              "|---|---|---|---|---|"] + rows + ["", f"Result: {'REPLICATION OK' if not bad else f'REPLICATION FAIL ({bad})'}", ""]
    out = args.out or os.path.join(CASE, "runs", f"{datetime.datetime.now():%Y%m%d-%H%M%S}-replicate.md")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(("REPLICATION OK" if not bad else f"REPLICATION FAIL ({bad})") + f" -> {os.path.relpath(out, CASE)}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
