"""Run one CASE-02 context (correct / missing / restored) formally or as a self-test (protocol v0.3 sections 4.2,
5.1-5.4; impl_plan Task 4). Run inside WSL from tasks/CASE-02:
  python3 -B scripts/run_context.py <correct|missing|restored> [--selftest]
Writes queries/<formal|selftest>/<version>/ (refuses an existing directory):
  sta_results.tsv, expanded.sdc, dcalc_*, cat_*, path_*   the records of a fresh `sta` process running the driver
  sta.log, cmd.txt, lib_lines_raw.txt                      process output, invocation record, raw LIB lines
  musts/M01..M13.txt, musts/constraints.tsv, musts/layers.json, musts/SHA256SUMS
                                                           the must-check items (second fresh process) and the four
                                                           evidence layers of protocol 5.3
  valid.json, SHA256SUMS
run_valid is true only when: env/snapshot.sh check passes; the netlist, SDC and driver hash as registered; the log
passes logcheck (missing version: plus the one whitelisted warning); records.compare passes for the version's
relation (correct_vs_f1 / missing_vs_correct / restored_vs_correct); the check_setup warning block is exactly as
expected (present with the 64 names on missing, absent otherwise); all four evidence layers pass; the must-check
process rebuilt the same records. mutation_verified is the expanded.sdc rule (missing) or the empty difference
(correct, restored)."""
import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2paths  # noqa: E402
import records  # noqa: E402
import run_query as rq  # noqa: E402

sys.path.insert(0, c2paths.CASE01_SCRIPTS)
import logcheck  # noqa: E402

VERSIONS = ("correct", "missing", "restored")
RELATION = {"correct": "correct_vs_f1", "missing": "missing_vs_correct", "restored": "restored_vs_correct"}
STATE_CONSTRAINED = "受约束路径存在"
STATE_UNCONSTRAINED = "查到目标 unconstrained 路径"
STATE_BOTH_EMPTY = "两类时序查询都为空，但结构路径存在"


# ---------------------------------------------------------------- pure parts
def target_dir(version, selftest, queries_root=None):
    root = queries_root or c2paths.QUERIES
    d = os.path.join(root, "selftest" if selftest else "formal", version)
    if os.path.exists(d):
        raise SystemExit(f"CASE02 FAIL: {d} exists; a context run is never overwritten")
    return d


def layer1(m11_text):
    ports, bad_dir = [], []
    for line in m11_text.splitlines():
        f = line.split()
        if len(f) >= 3 and f[0] == "PORT":
            ports.append(f[1])
            if f[2] != "input":
                bad_dir.append(f[1])
    info = {"count": len(ports), "bad_direction": bad_dir,
            "missing": sorted(set(records.TARGET_PORTS) - set(ports)), "foreign": sorted(set(ports) - set(records.TARGET_PORTS))}
    ok = len(ports) == 64 and len(set(ports)) == 64 and not info["missing"] and not info["foreign"] and not bad_dir
    return ok, info


def layer3(m12_text):
    fanin, fanout = set(), {}
    for line in m12_text.splitlines():
        f = line.split()
        if len(f) >= 2 and f[0] == "FANIN":
            fanin.add(f[1])
        elif len(f) >= 3 and f[0] == "FANOUT":
            fanout[f[1]] = int(f[2])
    no_fanout = [p for p in records.ALL_INPUTS if fanout.get(p, 0) <= 0]
    not_start = sorted(set(records.TARGET_PORTS) - fanin)
    info = {"fanin_startpoints": len(fanin), "targets_not_startpoints": not_start, "inputs_without_fanout": no_fanout}
    return (not not_start and not no_fanout), info


def layer4(m13_text, version):
    ports = {}
    for line in m13_text.splitlines():
        f = line.split()
        if len(f) < 2 or f[0] != "PAIR":
            continue
        kv = dict(x.split("=", 1) for x in f[2:] if "=" in x)
        try:
            mc, mu, nc, nu = (int(kv.get(k, "0")) for k in ("max_c", "max_u", "min_c", "min_u"))
        except ValueError:
            mc = mu = nc = nu = -1
        if mc > 0 or nc > 0:
            state = STATE_CONSTRAINED
        elif mu > 0 or nu > 0:
            state = STATE_UNCONSTRAINED
        else:
            state = STATE_BOTH_EMPTY
        ports[f[1]] = {"max_c": mc, "max_u": mu, "min_c": nc, "min_u": nu, "max_u_end": kv.get("max_u_end", "-"),
                       "min_u_end": kv.get("min_u_end", "-"), "scene": kv.get("scene", "-"), "state": state}
    problems = []
    for p in records.TARGET_PORTS:
        e = ports.get(p)
        if e is None:
            problems.append(f"{p}: no PAIR line")
            continue
        if version == "missing":
            if not (e["max_c"] == 0 and e["max_u"] == 1 and e["min_c"] == 0 and e["min_u"] == 1):
                problems.append(f"{p}: {e['max_c']}/{e['max_u']}/{e['min_c']}/{e['min_u']}")
        elif not (e["max_c"] >= 1 and e["max_u"] >= 1 and e["min_c"] >= 1 and e["min_u"] >= 1):
            problems.append(f"{p}: {e['max_c']}/{e['max_u']}/{e['min_c']}/{e['min_u']}")
    return (not problems), {"ports": ports, "problems": problems}


def validity(version, snapshot_ok, hashes_ok, log_ok, compare, warning, layers, musts_ok, selftest=False):
    problems = []
    if not snapshot_ok:
        problems.append("env/snapshot.sh check failed")
    if not hashes_ok:
        problems.append("frozen input hashes differ")
    if not log_ok:
        problems.append("log check failed")
    if not compare.get("ok"):
        problems += ["records: " + p for p in compare.get("problems", [])] or ["records differ"]
    if version == "missing":
        if not (warning.get("present") and warning.get("names_ok")):
            problems.append("check_setup warning block missing or malformed: " + "; ".join(warning.get("problems", [])))
    elif warning.get("present"):
        problems.append("check_setup warning block present on a version that must not have one")
    for k, v in layers.items():
        if not v:
            problems.append(f"evidence layer {k} failed")
    if not musts_ok:
        problems.append("must-check process did not rebuild the same records")
    if version == "missing":
        mutation_verified = compare.get("mutation_verified") is True
    else:
        mutation_verified = bool(compare.get("ok")) and not compare.get("allowed_changes_seen")
    if not mutation_verified:
        problems.append("mutation_verified false")
    return {"selftest": bool(selftest), "version": version, "run_valid": not problems, "mutation_verified": mutation_verified,
            "relation": RELATION[version], "problems": problems, "allowed_changes_seen": compare.get("allowed_changes_seen", []),
            "lib": {k: compare.get("lib", {}).get(k) for k in ("normalized_ok", "raw_identical")},
            "warning_block": {k: warning.get(k) for k in ("present", "count", "names_ok")}, "layers": layers}


MUST_IDS = [f"M{i:02d}" for i in range(1, 14)]


def musts_complete(parts):
    """All thirteen must-check items present and each sourced without error (R6 M8)."""
    return all(m in parts and parts[m][1] == 0 for m in MUST_IDS)


def split_musts(text, nonce):
    begin = re.compile(r"^=== CASE02-" + re.escape(nonce) + r" MUST (M\d+) BEGIN ===$")
    end = re.compile(r"^=== CASE02-" + re.escape(nonce) + r" MUST (M\d+) END rc=(\d+) ===$")
    out, cur, buf = {}, None, []
    for line in text.splitlines():
        m = begin.match(line)
        if m:
            cur, buf = m.group(1), []
            continue
        m = end.match(line)
        if m and cur == m.group(1):
            out[cur] = ("".join(l + "\n" for l in buf), int(m.group(2)))
            cur = None
            continue
        if cur is not None:
            buf.append(line)
    return out


def write_sha256sums(directory):
    rows = []
    for dp, dn, fn in os.walk(directory):
        for name in sorted(fn):
            if name == "SHA256SUMS" and dp == directory:
                continue
            p = os.path.join(dp, name)
            rel = "./" + os.path.relpath(p, directory).replace(os.sep, "/")
            with open(p, "rb") as f:
                rows.append(f"{hashlib.sha256(f.read()).hexdigest()}  {rel}")
    rows.sort(key=lambda r: r.split("  ", 1)[1])
    with open(os.path.join(directory, "SHA256SUMS"), "w", newline="\n") as f:
        f.write("\n".join(rows) + "\n")


# ---------------------------------------------------------------- the run
def sta_env(version, outdir):
    sdc = os.path.join(c2paths.CASE, "sdc", "case02_missing_inb.tcl") if version == "missing" else \
        os.path.join(c2paths.CASE01, "sdc", "case01_sdc.tcl")
    return dict(os.environ, TOP="dot4sat", NETLIST=os.path.join(c2paths.F1_ARCHIVE, "synth", "netlist.v"), T_NS=rq.T_NS,
                CLOAD_PF=rq.CLOAD_PF, SCENESET="std", OUTDIR=outdir, CASE_DIR=os.path.join(c2paths.F1_ARCHIVE, "inputs"),
                SDC_FILE=sdc, DRIVER=os.path.join(c2paths.CASE, "scripts", "sta_run_case02.tcl")), sdc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("version", choices=VERSIONS)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    version, selftest = args.version, args.selftest
    target = target_dir(version, selftest)
    base = os.path.join(c2paths.F1_ARCHIVE, "sta") if version == "correct" else \
        os.path.join(c2paths.QUERIES, "selftest" if selftest else "formal", "correct")
    if not os.path.isdir(base):
        raise SystemExit(f"CASE02 FAIL: baseline {base} missing (run the correct version first)")
    os.makedirs(target)
    env, sdc = sta_env(version, target)
    driver = env["DRIVER"]
    hashes = {"netlist": c2paths.sha256(env["NETLIST"]), "sdc": c2paths.sha256(sdc), "driver": c2paths.sha256(driver)}
    hashes_ok = hashes["netlist"] == rq.NETLIST_SHA and hashes["sdc"] == rq.SDC_SHA[version] and hashes["driver"] == rq.DRIVER_SHA
    snap_rc, _ = rq.run_limited(["bash", os.path.join(c2paths.REPO, "env", "snapshot.sh"), "check"],
                                os.path.join(target, "snapshot.log"), os.environ, c2paths.CASE, 120, 10 * 1024 * 1024)
    argv1 = ["sta", "-no_init", "-no_splash", "-exit", driver]
    rc1, stop1 = rq.run_limited(argv1, os.path.join(target, "sta.log"), env, target, 1200, 50 * 1024 * 1024)
    with open(os.path.join(target, "cmd.txt"), "w", newline="\n") as f:
        f.write(f"version={version} selftest={selftest}\nargv: {' '.join(argv1)}\nSDC_FILE={sdc}\nNETLIST={env['NETLIST']}\n"
                f"rc={rc1} stop={stop1}\nhead={rq.git_head()}\n" + "".join(f"{k}_sha256={v}\n" for k, v in hashes.items()))
    rules = logcheck.load_rules(os.path.join(c2paths.CASE01, "config", "warn_whitelist.txt"))
    if version == "missing":
        rules = rules + logcheck.load_rules(os.path.join(c2paths.RULES, "warn_whitelist_missing.txt"))
    log_problems = logcheck.scan("sta", os.path.join(target, "sta.log"), rules)[0]
    cmp = records.compare(RELATION[version], target, base, c2paths.RULES)
    if cmp["lib"].get("raw_lines"):
        rq.write_text(os.path.join(target, "lib_lines_raw.txt"), cmp["lib"]["raw_lines"])
    with open(os.path.join(target, "sta.log"), encoding="utf-8", errors="replace") as f:
        warning = records.warning_block(f.read(), os.path.join(c2paths.RULES, "mutation_lines.txt"))

    # second fresh process: the must-check items on a scratch rebuild of the same context
    musts_dir = os.path.join(target, "musts")
    os.makedirs(musts_dir)
    scratch = c2paths.new_run_dir("ctx", f"musts-{version}")
    env2, _ = sta_env(version, os.path.join(scratch, "env"))
    os.makedirs(env2["OUTDIR"])
    nonce = secrets.token_hex(8)
    env2.update(MUSTS_DIR=os.path.join(c2paths.RULES, "musts"), CASE02_NONCE=nonce)
    rc2, stop2 = rq.run_limited(["sta", "-no_init", "-no_splash", "-exit", os.path.join(HERE, "c2_musts.tcl")],
                                os.path.join(musts_dir, "musts.log"), env2, scratch, 1200, 50 * 1024 * 1024)
    with open(os.path.join(musts_dir, "musts.log"), encoding="utf-8", errors="replace") as f:
        parts = split_musts(f.read(), nonce)
    for mid, (text, mrc) in sorted(parts.items()):
        rq.write_text(os.path.join(musts_dir, f"{mid}.txt"), text + f"[rc={mrc}]\n")
    musts_cmp = records.compare("query_env_vs_formal", env2["OUTDIR"], target, c2paths.RULES)
    musts_ok = musts_cmp["ok"] and rc2 == 0 and stop2 is None and musts_complete(parts)
    with open(os.path.join(target, "expanded.sdc"), encoding="utf-8") as f:
        constraints = records.expanded_constraints(f.read())
    with open(os.path.join(musts_dir, "constraints.tsv"), "w", newline="\n") as f:
        f.write("port\tmin\tmax\tclock\tedge\trise\tfall\tdriver\n")
        for p in records.ALL_INPUTS:
            e = constraints[p]
            f.write("\t".join(str(e[k]) for k in ("min", "max", "clock", "edge", "rise", "fall", "driver")).join([p + "\t", "\n"]))
    l1_ok, l1 = layer1(parts.get("M11", ("", 1))[0])
    l2_ok, l2 = records.layer2_check(constraints, version)
    l3_ok, l3 = layer3(parts.get("M12", ("", 1))[0])
    l4_ok, l4 = layer4(parts.get("M13", ("", 1))[0], version)
    layers = {"L1_ports": l1_ok, "L2_constraints": l2_ok, "L3_structure": l3_ok, "L4_pairs": l4_ok}
    with open(os.path.join(musts_dir, "layers.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"L1": {"ok": l1_ok, **l1}, "L2": {"ok": l2_ok, "problems": l2}, "L3": {"ok": l3_ok, **l3},
                   "L4": {"ok": l4_ok, **l4}, "musts_rc": {k: v[1] for k, v in parts.items()}, "musts_process_rc": rc2,
                   "musts_records_identical": musts_cmp["ok"]}, f, ensure_ascii=False, indent=1)
    write_sha256sums(musts_dir)
    v = validity(version, snap_rc == 0, hashes_ok, not log_problems and rc1 == 0 and stop1 is None, cmp, warning, layers,
                 musts_ok, selftest=selftest)
    v["log_problems"] = log_problems[:20]
    v["hashes"] = hashes
    v["head"] = rq.git_head()
    with open(os.path.join(target, "valid.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(v, f, ensure_ascii=False, indent=1)
    write_sha256sums(target)
    shutil.rmtree(scratch, ignore_errors=True)
    print(f"CASE02 CONTEXT {'OK' if v['run_valid'] else 'FAIL'}: {version}{' (selftest)' if selftest else ''} "
          f"run_valid={v['run_valid']} mutation_verified={v['mutation_verified']} relation={v['relation']} "
          f"allowed_changes={len(v['allowed_changes_seen'])} layers={layers} -> {os.path.relpath(target, c2paths.CASE)}")
    for p in v["problems"][:10]:
        print(f"  {p}")
    return 0 if v["run_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
