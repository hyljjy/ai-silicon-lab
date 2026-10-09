"""TB self-test (spec 3.6). Run inside WSL from tasks/CASE-01:  python3 scripts/selftest.py [--lmax 3]

Every case must behave as expected: correct designs PASS with the manifest count; broken designs, corrupted
vectors and bad plusargs FAIL for the expected reason. Exit 0 only then. Writes
runs/<ts>-selftest-lmax<N>/selftest.json; before F1 the results are labelled "dev-selftest".
"""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

import check_sim

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CASE, "ref"))
from model import decode16          # noqa: E402
from timeline import classify       # noqa: E402

BASE = "rtl/dot4sat.v"
PIPE = "tb/selftest/dot4sat_pipe.v"


def cases(lmax):
    """(name, rtl, defines, L for TB, vector set, EXP delta, plusarg overrides, expected 'PASS' or failure text).
    Vector sets: 'L<k>' = generated for L=k; other names are corrupted copies of L1 (see corrupt())."""
    out = [("base_L1", BASE, [], 1, "L1", 0, {}, "PASS"),
           ("mut_num", "tb/selftest/dot4sat_mut_num.v", [], 1, "L1", 0, {}, "DATA MISMATCH"),
           ("mut_valid", "tb/selftest/dot4sat_mut_valid.v", [], 1, "L1", 0, {}, "VALID MISMATCH"),
           ("mut_xdata", "tb/selftest/dot4sat_mut_xdata.v", [], 1, "L1", 0, {}, "DATA MISMATCH"),
           ("exp_off_by_one", BASE, [], 1, "L1", 1, {}, "!= expected"),
           ("missing_L", BASE, [], 1, "L1", 0, {"L": None}, "missing or malformed +L"),
           ("malformed_L", BASE, [], 1, "L1", 0, {"L": "1x"}, "missing or malformed +L"),
           ("L_above_lmax", BASE, [], lmax + 1, "L1", 0, {}, "outside 1..LMAX"),
           ("no_vector_file", BASE, [], 1, "missing", 0, {}, "cannot open vector file"),
           ("unknown_values", BASE, [], 1, "x_in_valid_row", 0, {}, "not lowercase hex"),
           ("split_line", BASE, [], 1, "split_line", 0, {}, "need exactly 12"),
           ("extra_field", BASE, [], 1, "extra_field", 0, {}, "need exactly 12"),
           ("wide_field", BASE, [], 1, "wide_field", 0, {}, "not lowercase hex"),
           ("truncated_tail", BASE, [], 1, "truncated_tail", 0, {}, "manifest says"),
           ("watchdog", BASE, [], 1, "L1", 0, {"WATCHDOG": "10"}, "watchdog timeout")]
    if lmax >= 2:
        out += [("pipe_L2", PIPE, [], 2, "L2", 0, {}, "PASS"),
                ("cfg_L2_on_L1_dut", BASE, [], 2, "L2", 0, {}, "VALID MISMATCH")]
    if lmax >= 3:
        out += [("pipe_L3", PIPE, ["-DEXTRA2"], 3, "L3", 0, {}, "PASS")]
    return out


def corrupt(lines, kind):
    """Corrupted copies of the L=1 vectors; the line count given to the TB stays the manifest's n_vectors."""
    out = list(lines)
    first_valid = next(i for i, l in enumerate(out) if l.split()[:2] == ["0", "1"])
    f = out[first_valid].split()
    if kind == "x_in_valid_row":
        out[first_valid] = " ".join(f[:2] + ["xxxx"] * 8 + ["xxxxxxxx", f[11]])
    elif kind == "split_line":
        out[first_valid] = " ".join(f[:6]) + "\n" + " ".join(f[6:])
    elif kind == "extra_field":
        out[first_valid] = out[first_valid] + " extra"
    elif kind == "wide_field":
        out[first_valid] = " ".join(f[:2] + ["1" + f[2]] + f[3:])
    elif kind == "truncated_tail":
        out = out[:-10]
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def provenance(lmax, generated):
    """Tool identity and the sha256 of every file this self-test used (final review I5): the TB, every RTL/mutant/
    fixture of cases(lmax), this script and the code it runs (check_sim, ref/), and the generated vectors, manifests
    and corrupted vector files. Paths are relative to tasks/CASE-01."""
    try:
        out = subprocess.run(["iverilog", "-V"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             errors="replace").stdout
        iverilog = out.splitlines()[0] if out.strip() else "(no output from iverilog -V)"
    except OSError as e:
        iverilog = f"unavailable: {e}"
    used = (["tb/tb_dot4sat.v"] + sorted({c[1] for c in cases(lmax)}) +
            [os.path.relpath(os.path.abspath(__file__), CASE), "scripts/check_sim.py", "ref/gen_vectors.py",
             "ref/model.py", "ref/timeline.py", "ref/coverage.py"])
    files = {rel: sha256(os.path.join(CASE, rel)) for rel in used}
    files.update({os.path.relpath(p, CASE): sha256(p) for p in generated})
    return {"iverilog": iverilog, "python": sys.version, "sha256": files}


def lane3_negative_checked(vec_path, L, drain):
    """Activation proof for mut_num: checked transactions whose lane-3 operand is negative."""
    rows = [l.split() for l in open(vec_path)]
    rst = [int(r[0]) for r in rows] + [0] * drain
    valid = [int(r[1]) for r in rows] + [0] * drain
    kinds = classify(rst, valid, L)
    return sum(1 for n, r in enumerate(rows) if kinds[n] == "delivered"
               and (decode16(int(r[5], 16)) < 0 or decode16(int(r[9], 16)) < 0))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lmax", type=int, default=3)
    args = ap.parse_args(argv)
    root = os.path.join(CASE, "runs", f"{datetime.datetime.now():%Y%m%d-%H%M%S}-selftest-lmax{args.lmax}")
    os.makedirs(root)
    vec, manifests, generated = {}, {}, []
    for L in range(1, args.lmax + 1):
        out = os.path.join(root, f"vec_L{L}")
        rc = subprocess.run([sys.executable, os.path.join(CASE, "ref", "gen_vectors.py"), "--L", str(L),
                             "--lmax", str(args.lmax), "--seed", "1", "--out", out]).returncode
        if rc:
            print(f"SELFTEST FAIL: gen_vectors L={L}")
            return 1
        with open(os.path.join(out, "manifest.json")) as f:
            manifests[f"L{L}"] = json.load(f)
        vec[f"L{L}"] = os.path.join(out, "vectors.txt")
        generated += [vec[f"L{L}"], os.path.join(out, "manifest.json")]
    base_lines = open(vec["L1"]).read().splitlines()
    for kind in ("x_in_valid_row", "split_line", "extra_field", "wide_field", "truncated_tail"):
        path = os.path.join(root, f"vec_{kind}.txt")
        with open(path, "w", newline="\n") as f:
            f.write("\n".join(corrupt(base_lines, kind)) + "\n")
        vec[kind], manifests[kind] = path, manifests["L1"]
        generated.append(path)
    vec["missing"], manifests["missing"] = os.path.join(root, "missing.txt"), manifests["L1"]

    tb = os.path.join(CASE, "tb", "tb_dot4sat.v")
    results, all_ok = [], True
    for name, rtl, defs, L_tb, vset, delta, over, want in cases(args.lmax):
        vvp, log = os.path.join(root, f"{name}.vvp"), os.path.join(root, f"{name}.log")
        with open(log + ".compile", "w") as f:
            rc = subprocess.run(["iverilog", "-g2012"] + defs + ["-o", vvp, tb, os.path.join(CASE, rtl)],
                                stdout=f, stderr=subprocess.STDOUT).returncode
        if rc:
            results.append({"case": name, "ok": False, "why": "compile failed"})
            all_ok = False
            print(f"FAIL {name:18s} compile failed")
            continue
        m = manifests[vset]
        plus = {"VEC": vec[vset], "NVEC": str(m["n_vectors"]), "L": str(L_tb), "LMAX": str(args.lmax),
                "EXP": str(m["expected_checked"] + delta)}
        plus.update(over)
        argv_plus = [f"+{k}={v}" for k, v in plus.items() if v is not None]
        with open(log, "w") as f:
            rc = subprocess.run(["vvp", "-n", vvp] + argv_plus, stdout=f, stderr=subprocess.STDOUT).returncode
        text = open(log, errors="replace").read()
        if want == "PASS":
            ok, why = check_sim.check(text, rc, m["expected_checked"])
        else:
            ok = rc != 0 and want in text and "SIM PASS" not in text
            why = f"exit {rc}, expected failure text {want!r} {'found' if want in text else 'NOT found'}"
        entry = {"case": name, "rtl": rtl, "L_tb": L_tb, "vectors": vset, "expect": want, "ok": ok, "why": why}
        if name == "mut_num":
            n = lane3_negative_checked(vec["L1"], 1, args.lmax + 1)
            entry["activation_lane3_negative_checked"] = n
            if n == 0:
                entry["ok"], entry["why"] = False, "mutation never activated by a checked transaction"
        results.append(entry)
        all_ok = all_ok and entry["ok"]
        print(f"{'ok  ' if entry['ok'] else 'FAIL'} {name:18s} {entry['why']}")
    label = "dev-selftest" if not os.path.exists(os.path.join(CASE, "config", "f1.cfg")) else "selftest"
    with open(os.path.join(root, "selftest.json"), "w") as f:
        json.dump({"label": label, "lmax": args.lmax, "all_ok": all_ok, "results": results,
                   **provenance(args.lmax, generated)}, f, indent=1)
    print(f"SELFTEST {'OK' if all_ok else 'FAIL'} ({label}, lmax={args.lmax}, {len(results)} cases) "
          f"-> {os.path.relpath(root, CASE)}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
