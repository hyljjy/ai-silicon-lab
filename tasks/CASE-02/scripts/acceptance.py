"""Execution-contract acceptance (protocol v0.3 section 6.4 last paragraph; impl_plan Task 9). Run inside WSL from
tasks/CASE-02 after the self-test contexts exist and the contract's budget is filled:
  python3 -B scripts/acceptance.py run [--only acc_i_core,...]      # runs the samples, writes prevalidation/acceptance/
  python3 -B scripts/acceptance.py budget                            # sample (vii) from the recorded (i)(iii)(iv) results
  python3 -B scripts/acceptance.py report                            # RESULT.md from what is recorded
Each sample's expectation is in rules/acceptance/expected.json (written before the runs). Every run uses the installed
executor in self-test mode with --uncommitted-ok (registration state only); the contract and executor snapshots are
saved so that tier 1 can check they equal what gets registered."""
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2paths  # noqa: E402
import budget  # noqa: E402
import contract as contract_mod  # noqa: E402
import run_query as rq  # noqa: E402

ACC = os.path.join(c2paths.PREVALIDATION, "acceptance")
RULES_ACC = os.path.join(c2paths.RULES, "acceptance")
SAMPLES = ("acc_i_core", "acc_ii_noflush", "acc_iii_six", "acc_iv_fullreports", "acc_v_timeout", "acc_vi_outlimit", "acc_ctrl_correct")
KEEP = ("query.tcl", "sta.log", "env_part.log", "query_full.txt", "query_return.txt", "calls.jsonl", "tops.jsonl", "result.json",
        "snapshot.log")
ARRIVAL_LINE = re.compile(r"^\S+ (\(clk [\^v]\) )?r [\d.\-]+:[\d.\-]+ f [\d.\-]+:[\d.\-]+$")


def expected():
    with open(os.path.join(RULES_ACC, "expected.json"), encoding="utf-8") as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith("_")}


def snapshots():
    os.makedirs(ACC, exist_ok=True)
    shutil.copyfile(os.path.join(c2paths.RULES, "contract.json"), os.path.join(ACC, "contract_snapshot.json"))
    with open(os.path.join(ACC, "executor_snapshot.sha256"), "w", newline="\n") as f:
        for rel, h in rq.executor_hashes().items():
            f.write(f"{h}  {rel}\n")


def run_sample(name, exp):
    query = os.path.join(RULES_ACC, f"{name}.tcl")
    t0 = time.monotonic()
    proc = subprocess.run([sys.executable, "-B", os.path.join(HERE, "run_query.py"), "--id", name, "--ctx", exp["ctx"],
                           "--query", query, "--mode", exp.get("mode", "auto"), "--selftest", "--uncommitted-ok"],
                          cwd=c2paths.CASE, capture_output=True, text=True)
    elapsed = time.monotonic() - t0
    m = re.search(r"-> (runs/\S+)", proc.stdout)
    if not m:
        return {"sample": name, "ran": False, "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
    run_dir = os.path.join(c2paths.CASE, m.group(1))
    dest = os.path.join(ACC, name)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    for f in KEEP:
        p = os.path.join(run_dir, f)
        if os.path.exists(p):
            shutil.copyfile(p, os.path.join(dest, f))
    with open(os.path.join(dest, "run.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"run_dir={m.group(1)}\nelapsed_seconds={elapsed:.1f}\nstdout:\n{proc.stdout}\n")
    with open(os.path.join(run_dir, "result.json"), encoding="utf-8") as f:
        res = json.load(f)
    return {"sample": name, "ran": True, "run_dir": m.group(1), "elapsed": elapsed, "result": res, "dest": dest}


def check_sample(name, exp, got):
    diffs = []
    if not got.get("ran"):
        return ["did not run: " + got.get("stdout", "")[-300:]]
    res = got["result"]
    simple = {"truncated": ("output_attr", "truncated"), "raw_lines": ("raw_lines",), "exec_result": ("exec_result",),
              "attribution": ("attribution",), "query_status": ("query_status",), "cut_by": ("cut_by",), "abnormal": ("abnormal",),
              "mode": ("mode",), "ctx": ("ctx",), "calls": ("calls",)}
    for key, path in simple.items():
        if key in exp:
            v = res
            for p in path:
                v = v.get(p) if isinstance(v, dict) else None
            if v != exp[key]:
                diffs.append(f"{key}: expected {exp[key]!r}, got {v!r}")
    calls = []
    cpath = os.path.join(got["dest"], "calls.jsonl")
    if os.path.exists(cpath):
        with open(cpath, encoding="utf-8") as f:
            calls = [json.loads(l) for l in f if l.strip()]
    if exp.get("calls_all_ok") and not (calls and all(c["status"] == "ok" for c in calls)):
        diffs.append("calls_all_ok: some call is not ok")
    if exp.get("last_call_unfinished") and not (calls and calls[-1]["status"] == "unfinished"):
        diffs.append("last_call_unfinished: last call is " + (calls[-1]["status"] if calls else "none"))
    if "returned_bytes_max" in exp and res.get("returned_bytes", 0) > exp["returned_bytes_max"]:
        diffs.append(f"returned_bytes {res.get('returned_bytes')} > {exp['returned_bytes_max']}")
    if "max_seconds" in exp and got["elapsed"] > exp["max_seconds"]:
        diffs.append(f"elapsed {got['elapsed']:.0f}s > {exp['max_seconds']}s")
    with open(os.path.join(got["dest"], "query_return.txt"), encoding="utf-8") as f:
        ret = f.read()
    if "ordered_pairs" in exp:
        n = sum(1 for l in ret.splitlines() if ARRIVAL_LINE.match(l))
        if n != exp["ordered_pairs"]:
            diffs.append(f"ordered_pairs: expected {exp['ordered_pairs']}, got {n}")
    if exp.get("return_ends_with_note") and not ret.rstrip().endswith("以上为结束前的输出]"):
        diffs.append("return does not end with the termination note")
    if "output_contains" in exp and exp["output_contains"] not in ret:
        diffs.append(f"output lacks {exp['output_contains']!r}")
    if "output_lacks" in exp and exp["output_lacks"] in ret:
        diffs.append(f"output contains {exp['output_lacks']!r}")
    return diffs


def budget_sample(exp):
    """Sample (vii): the recorded (i)(iii)(iv) instances for R1 and R2 plus synthetic copies of (iii) until the final
    total budget is exceeded; the full chain allocate -> statement -> prompt budget check."""
    c = contract_mod.load(os.path.join(c2paths.RULES, "contract.json"))
    if not c.budget_ready:
        return {"ran": False, "why": "contract has no total budget yet"}
    instances = []
    for name, qid in (("acc_i_core", "A1"), ("acc_iii_six", "A2"), ("acc_iv_fullreports", "A3")):
        p = os.path.join(ACC, name, "result.json")
        if not os.path.exists(p):
            return {"ran": False, "why": f"{name} not recorded"}
        with open(p, encoding="utf-8") as f:
            res = json.load(f)
        with open(os.path.join(ACC, name, "query_return.txt"), "rb") as f:
            rendered = len(f.read()) + 400          # returned output plus the per-instance template text
        for ctx in ("R1", "R2"):
            instances.append({"qid": qid, "ctx": ctx, "rendered_bytes": rendered, "returned_bytes": res["returned_bytes"],
                              "priority": None, "truncated": res["output_attr"]["truncated"], "raw_lines": res["raw_lines"],
                              "returned_lines": res["returned_lines"]})
    base = list(instances)
    n = 4
    while sum(i["rendered_bytes"] for i in instances) / c.token_bytes_ratio <= c.total_budget_tokens and n < 100:
        for ctx in ("R1", "R2"):
            instances.append(dict(base[2], qid=f"A{n}", ctx=ctx))
        n += 1
    alloc = budget.allocate(instances, c)
    stmt = budget.statement(alloc, c)
    text = "\n".join(f"### 查询 {i['qid']}（{i['ctx']}）\n" + "x" * (i["rendered_bytes"] - 20) for i in alloc["returned"]) + "\n" + stmt
    import math
    tokens = math.ceil(len(text.encode("utf-8")) / c.token_bytes_ratio)
    out = {"ran": True, "instances": len(instances), "returned": len(alloc["returned"]), "dropped": len(alloc["dropped"]),
           "statement_lists_all_dropped": all(f"{d['qid']} {d['ctx']}" in stmt for d in alloc["dropped"]),
           "rendered_check_ok": tokens <= c.total_budget_tokens, "tokens": tokens, "budget_tokens": c.total_budget_tokens}
    d = os.path.join(ACC, "acc_vii_budget")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "budget_statement.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(stmt)
    with open(os.path.join(d, "allocation.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"alloc": alloc, "check": out, "instances": instances}, f, ensure_ascii=False, indent=1)
    diffs = []
    if out["dropped"] < exp["dropped_at_least"]:
        diffs.append("nothing was dropped")
    if exp["statement_lists_all_dropped"] and not out["statement_lists_all_dropped"]:
        diffs.append("statement does not list every dropped instance")
    if exp["rendered_check_ok"] and not out["rendered_check_ok"]:
        diffs.append("rendered prompt exceeds the budget")
    out["diffs"] = diffs
    return out


def report(results):
    exp = expected()
    lines = []
    all_ok = True
    for name in SAMPLES + ("acc_vii_budget",):
        r = results.get(name)
        if r is None:
            lines.append(f"- {name}: NOT RUN")
            all_ok = False
            continue
        diffs = r.get("diffs", [])
        ok = r.get("ran") and not diffs
        all_ok &= bool(ok)
        extra = ""
        if r.get("result"):
            res = r["result"]
            extra = (f" raw_lines={res.get('raw_lines')} returned={res.get('returned_lines')} truncated={res.get('output_attr', {}).get('truncated')} "
                     f"status={res.get('query_status')} result={res.get('exec_result')} attribution={res.get('attribution')} calls={res.get('calls')} "
                     f"elapsed={r.get('elapsed', 0):.0f}s")
        lines.append(f"- {name}: {'OK' if ok else 'FAIL'}{extra}" + ("" if not diffs else "\n  - " + "\n  - ".join(diffs)))
    head = "ACCEPTANCE OK" if all_ok else "ACCEPTANCE FAIL"
    text = f"{head}\n\n执行契约验收（规程 v0.3 第 6.4 节末条；预期值 rules/acceptance/expected.json，运行前写定）。\n\n" + "\n".join(lines) + "\n"
    with open(os.path.join(ACC, "RESULT.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)
    return 0 if all_ok else 1


def load_recorded():
    results = {}
    exp = expected()
    for name in SAMPLES:
        d = os.path.join(ACC, name)
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "result.json")):
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                res = json.load(f)
            elapsed = 0.0
            rp = os.path.join(d, "run.txt")
            if os.path.exists(rp):
                with open(rp, encoding="utf-8") as f:
                    m = re.search(r"elapsed_seconds=([\d.]+)", f.read())
                    elapsed = float(m.group(1)) if m else 0.0
            got = {"sample": name, "ran": True, "result": res, "dest": d, "elapsed": elapsed}
            got["diffs"] = check_sample(name, exp[name], got)
            results[name] = got
    vp = os.path.join(ACC, "acc_vii_budget", "allocation.json")
    if os.path.exists(vp):
        with open(vp, encoding="utf-8") as f:
            results["acc_vii_budget"] = json.load(f)["check"]
    return results


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in ("run", "budget", "report"):
        print("usage: acceptance.py run [--only a,b] | budget | report")
        return 2
    if argv[0] == "run":
        only = SAMPLES
        if len(argv) > 2 and argv[1] == "--only":
            only = tuple(argv[2].split(","))
        snapshots()
        exp = expected()
        for name in only:
            got = run_sample(name, exp[name])
            got["diffs"] = check_sample(name, exp[name], got) if got.get("ran") else ["did not run"]
            print(f"{name}: {'OK' if not got['diffs'] else 'FAIL ' + '; '.join(got['diffs'])}")
        return report(load_recorded())
    if argv[0] == "budget":
        out = budget_sample(expected()["acc_vii_budget"])
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return report(load_recorded())
    return report(load_recorded())


if __name__ == "__main__":
    sys.exit(main())
