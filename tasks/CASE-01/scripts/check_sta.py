"""Validate one CASE-01 STA run (spec 4.3-4.5) and summarize it.

Usage: python3 scripts/check_sta.py <outdir> <T_ns> <C_load_pF> <std|all>
Needs env SKY130_KIT (MANIFEST.txt with the Liberty sha256). Reads the files written by scripts/sta_run.tcl and
writes <outdir>/sta_check.json. Exit 0 = analysis valid (negative slack is NOT a failure); exit 1 = invalid.
Every record must be present exactly once, every number must be finite, and every claim of "no path of this
category" must be backed by the structural (fanin) evidence.
"""
import hashlib
import json
import math
import os
import re
import sys

STD = ["tt_025C_1v80", "tt_100C_1v80", "ss_100C_1v60", "ss_n40C_1v60", "ff_n40C_1v95", "ff_100C_1v95"]
SWEEP = ["ff_100C_1v65", "ff_n40C_1v56", "ff_n40C_1v65", "ff_n40C_1v76", "ss_100C_1v40",
         "ss_n40C_1v28", "ss_n40C_1v35", "ss_n40C_1v40", "ss_n40C_1v44", "ss_n40C_1v76"]
EXPECT_IN = [f"in_a[{i}]" for i in range(64)] + [f"in_b[{i}]" for i in range(64)] + ["in_valid", "rst"]
EXPECT_OUT = [f"out_data[{i}]" for i in range(32)] + ["out_valid"]
CATS = ("in2reg", "reg2reg", "reg2out")
FORBIDDEN = ("set_false_path", "set_multicycle_path", "set_disable_timing", "set_case_analysis",
             "set_max_delay", "set_min_delay")
TOL = 1e-4      # write_sdc prints 4 decimals
CAP_TOL = 1e-18  # farads
NFIELDS = {"MODE": 1, "CHECK_SETUP": 1, "LOAD": 3, "LIB": 2, "PORT": 2, "OBJECTS": 4, "TOPO": 2, "WS": 3, "DONE": 0}

RE_CLOCK = re.compile(r"^create_clock -name clk -period ([0-9.]+) \[get_ports \{clk\}\]$")
CLOCK_ZERO = {  # spec 4.3: written explicitly as 0 by sdc/case01_sdc.tcl; each must be present
    "set_clock_transition 0.0000 [get_clocks {clk}]",
    "set_clock_uncertainty 0.0000 clk",
    "set_clock_latency 0.0000 [get_clocks {clk}]",
    "set_clock_latency -source 0.0000 [get_clocks {clk}]",
}
RE_IODELAY = re.compile(r"^set_(input|output)_delay ([0-9.eE+-]+) -clock \[get_clocks \{clk\}\] "
                        r"-(min|max) -add_delay \[get_ports \{(.+)\}\]$")
RE_DRIVE = re.compile(r"^set_driving_cell -lib_cell sky130_fd_sc_hd__buf_2 -from_pin \{A\} -pin \{X\} "
                      r"-input_transition_rise 0\.0000 -input_transition_fall 0\.0000 \[get_ports \{(.+)\}\]$")
RE_LOAD = re.compile(r"^set_load -pin_load ([0-9.eE+-]+) \[get_ports \{(.+)\}\]$")
RE_PVT = re.compile(r"P = ([0-9.eE+-]+) V = ([0-9.eE+-]+) T = ([0-9.eE+-]+)")
RE_CORNER = re.compile(r"^(tt|ss|ff)_(n?)(\d+)C_(\d)v(\d+)$")


def corner_pvt(name):
    m = RE_CORNER.match(name)
    temp = -int(m.group(3)) if m.group(2) else int(m.group(3))
    return float(f"{m.group(4)}.{m.group(5)}"), float(temp)


def finite(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and abs(v) < 1e29 else None


def close(x, want, tol):
    v = finite(x)
    return v is not None and abs(v - want) <= tol


def manifest_sha():
    out = {}
    for line in open(os.path.join(os.environ["SKY130_KIT"], "MANIFEST.txt")):
        parts = line.split()
        if len(parts) == 2 and re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            out[parts[1]] = parts[0]
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def join_continuations(lines):
    """write_sdc folds long commands with a trailing backslash; rejoin them."""
    out, buf = [], ""
    for raw in lines:
        line = raw.rstrip()
        if line.endswith("\\"):
            buf += line[:-1].rstrip() + " "
            continue
        out.append(buf + line.strip())
        buf = ""
    if buf:
        out.append(buf.strip())
    return out


def check_sdc(lines, T, cload, problems):
    clock, in_d, out_d, drv, load, zeros = [], {}, {}, set(), {}, set()
    for line in join_continuations(lines):
        if not line or line.startswith("#") or line.startswith("current_design"):
            continue
        if line in CLOCK_ZERO:
            zeros.add(line)
            continue
        if line.startswith(FORBIDDEN):
            problems.append(f"forbidden constraint: {line}")
            continue
        m = RE_CLOCK.match(line)
        if m:
            clock.append(float(m.group(1)))
            continue
        m = RE_IODELAY.match(line)
        if m:
            table = in_d if m.group(1) == "input" else out_d
            if m.group(3) in table.setdefault(m.group(4), {}):
                problems.append(f"duplicate {m.group(1)} delay {m.group(3)} for {m.group(4)}")
            table[m.group(4)][m.group(3)] = m.group(2)
            continue
        m = RE_DRIVE.match(line)
        if m:
            drv.add(m.group(1))
            continue
        m = RE_LOAD.match(line)
        if m:
            load[m.group(2)] = m.group(1)
            continue
        problems.append(f"unrecognized constraint line: {line}")
    if len(clock) != 1 or not close(clock[0], T, TOL):
        problems.append(f"clock period {clock} != {T}")
    if zeros != CLOCK_ZERO:
        problems.append(f"missing explicit zero clock settings: {sorted(CLOCK_ZERO - zeros)}")
    for name, table, ports in (("input", in_d, EXPECT_IN), ("output", out_d, EXPECT_OUT)):
        if set(table) != set(ports):
            problems.append(f"{name} delay ports mismatch: missing {sorted(set(ports) - set(table))[:5]} "
                            f"extra {sorted(set(table) - set(ports))[:5]}")
        for p, mm in table.items():
            if not (close(mm.get("max"), 0.2 * T, TOL) and close(mm.get("min"), 0.0, TOL)):
                problems.append(f"{name} delay of {p} is {mm}, want max={0.2 * T} min=0")
    if drv != set(EXPECT_IN):
        problems.append(f"driving cell ports mismatch ({len(drv)} of {len(EXPECT_IN)})")
    if set(load) != set(EXPECT_OUT) or not all(close(v, cload, TOL) for v in load.values()):
        problems.append(f"set_load mismatch in expanded.sdc ({len(load)} ports)")


def check_report(path, corner, mm, cat_row, problems):
    """A category report must exist and agree with the machine record (corner, start, end, slack)."""
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        problems.append(f"missing report {os.path.basename(path)}")
        return
    text = open(path, errors="replace").read()
    start = re.search(r"^Startpoint: (\S+)", text, re.M)
    end = re.search(r"^Endpoint: (\S+)", text, re.M)
    slack = re.search(r"^\s*(-?[0-9.]+)\s+slack \((MET|VIOLATED)\)", text, re.M)
    ok = (re.search(rf"^Corner: {re.escape(corner)}$", text, re.M) and re.search(rf"^Path Type: {mm}$", text, re.M)
          and start and end and slack)
    if not ok:
        problems.append(f"report {os.path.basename(path)} lacks corner/path type/start/end/slack")
        return
    if cat_row is not None:
        _, _, _, s, sp, ep = cat_row
        if start.group(1) != sp.split("/")[0] or end.group(1) != ep.split("/")[0]:
            problems.append(f"report {os.path.basename(path)} path {start.group(1)}->{end.group(1)} "
                            f"!= record {sp}->{ep}")
        if not close(slack.group(1), float(s), 1e-3):
            problems.append(f"report {os.path.basename(path)} slack {slack.group(1)} != record {s}")


def main(argv):
    if len(argv) != 5:
        print(__doc__)
        return 1
    outdir, sceneset = argv[1], argv[4]
    T, cload = finite(argv[2]), finite(argv[3])
    problems = []
    if T is None or T <= 0 or cload is None or cload <= 0:
        print("STA INVALID: T and C_load must be finite and positive")
        return 1
    corners = STD if sceneset == "std" else STD + SWEEP

    rows, seen = [], {}
    for raw in open(os.path.join(outdir, "sta_results.tsv")):
        r = raw.rstrip("\n").split("\t")
        key = r[0]
        if key in NFIELDS and len(r) - 1 != NFIELDS[key]:
            problems.append(f"record {key} has {len(r) - 1} fields")
        elif key not in NFIELDS and key not in ("SCENES", "BIND", "CAT"):
            problems.append(f"unknown record {key}")
        rows.append(r)
    get = lambda key: [r[1:] for r in rows if r[0] == key]
    for key in ("MODE", "CHECK_SETUP", "OBJECTS", "DONE", "SCENES"):
        if len(get(key)) != 1:
            problems.append(f"record {key} appears {len(get(key))} times, need exactly 1")
    if get("MODE") != [["default"]]:
        problems.append(f"mode {get('MODE')} != default")
    if get("SCENES") != [corners]:
        problems.append(f"scenes {get('SCENES')} != {corners}")
    if get("CHECK_SETUP") != [["1"]]:
        problems.append(f"check_setup returned {get('CHECK_SETUP')} (1 = no warnings)")

    # libraries and scene binding (spec 4.5, P1 M2)
    want_libs = {f"sky130_fd_sc_hd__{c}" for c in corners + ["tt_025C_1v80"]}
    libs = {r[0]: r[1] for r in get("LIB") if len(r) == 2}
    if set(libs) != want_libs or len(get("LIB")) != len(want_libs):
        problems.append(f"loaded libraries {sorted(libs)} != {sorted(want_libs)}")
    shas = manifest_sha()
    for name, path in libs.items():
        base = os.path.basename(path)
        if base != name + ".lib" or not os.path.isfile(path) or shas.get(base) != sha256(path):
            problems.append(f"library {name}: file {path} does not match MANIFEST")
    binds = get("BIND")
    if sorted(binds) != sorted([[c, "-liberty", f"sky130_fd_sc_hd__{c}"] for c in corners]):
        problems.append(f"define_scene calls {binds} != one '-liberty sky130_fd_sc_hd__<corner>' per corner")
    for c in corners:
        v, t = corner_pvt(c)
        for mm in ("min", "max"):
            path = os.path.join(outdir, f"dcalc_{c}_{mm}.txt")
            m = RE_PVT.search(open(path).read()) if os.path.isfile(path) else None
            if not m or not (close(m.group(2), v, 1e-3) and close(m.group(3), t, 1e-3)):
                problems.append(f"scene {c} {mm} delay calc PVT {m.groups() if m else None} != V={v} T={t}")

    # ports, objects, loads
    ports = {r[0]: r[1] for r in get("PORT") if len(r) == 2}
    want_ports = {p: "input" for p in EXPECT_IN + ["clk"]}
    want_ports.update({p: "output" for p in EXPECT_OUT})
    if ports != want_ports or len(get("PORT")) != len(want_ports):
        problems.append("port names/directions do not match the interface (spec 1)")
    objs = get("OBJECTS")[0] if len(get("OBJECTS")) == 1 else []
    nums = [finite(x) for x in objs]
    if (len(nums) != 4 or nums[0] != len(EXPECT_IN) or nums[1] != len(EXPECT_OUT) or not nums[2]
            or nums[2] != nums[3]):
        problems.append(f"object counts {objs}: want {len(EXPECT_IN)} inputs, {len(EXPECT_OUT)} outputs, "
                        f"equal non-zero register data/clock pins")
    loads = get("LOAD")
    if sorted(r[0] for r in loads) != sorted(EXPECT_OUT):
        problems.append(f"LOAD ports mismatch ({len(loads)} of {len(EXPECT_OUT)})")
    for p, cmax, cmin in (r for r in loads if len(r) == 3):
        if not (close(cmax, cload * 1e-12, CAP_TOL) and close(cmin, cload * 1e-12, CAP_TOL)):
            problems.append(f"port {p} ext pin cap {cmax}/{cmin} F != {cload} pF")
    check_sdc(open(os.path.join(outdir, "expanded.sdc")).read().splitlines(), T, cload, problems)

    # structural evidence per category
    topo = {}
    for r in get("TOPO"):
        if r[0] not in CATS or r[0] in topo or finite(r[1]) is None:
            problems.append(f"bad TOPO record {r}")
        else:
            topo[r[0]] = int(float(r[1]))
    if set(topo) != set(CATS):
        problems.append(f"TOPO records {sorted(topo)} != {list(CATS)}")

    # per-scene completeness, consistency with structure, reports
    ws, cats = {}, {}
    for r in get("WS"):
        key = (r[0], r[1])
        if key in ws or r[0] not in corners or r[1] not in ("max", "min"):
            problems.append(f"duplicate or unexpected WS record {r}")
        ws[key] = finite(r[2])
    for r in get("CAT"):
        if len(r) not in (4, 6) or r[0] not in corners or r[1] not in CATS or r[2] not in ("max", "min"):
            problems.append(f"bad CAT record {r}")
            continue
        key = (r[0], r[1], r[2])
        if key in cats:
            problems.append(f"duplicate CAT record {key}")
        cats[key] = r
    summary = {}
    for c in corners:
        for mm in ("max", "min"):
            if ws.get((c, mm)) is None:
                problems.append(f"{c} worst_slack {mm} missing or not finite")
            for path in (os.path.join(outdir, f"path_{mm}_{c}.rpt"),):
                check_report(path, c, mm, None, problems)
        cs = {}
        for cat in CATS:
            for mm in ("max", "min"):
                r = cats.get((c, cat, mm))
                if r is None:
                    problems.append(f"{c} {cat} {mm}: CAT record missing")
                    continue
                exists = topo.get(cat, 0) > 0
                if r[3] == "UNCONSTRAINED":
                    problems.append(f"{c} {cat} {mm}: paths exist but are unconstrained")
                elif r[3] == "NONE":
                    if exists:
                        problems.append(f"{c} {cat} {mm}: structural path exists but the timing query is empty")
                    cs[f"{cat}_{mm}"] = "not_applicable"
                elif len(r) != 6 or finite(r[3]) is None:
                    problems.append(f"{c} {cat} {mm}: slack {r[3]} not finite")
                elif not exists:
                    problems.append(f"{c} {cat} {mm}: timing path reported but no structural path")
                else:
                    check_report(os.path.join(outdir, f"cat_{c}_{cat}_{mm}.rpt"), c, mm, r, problems)
                    cs[f"{cat}_{mm}"] = {"slack": finite(r[3]), "start": r[4], "end": r[5]}
        # the worst slack must come from one of the three categories (P2 review): otherwise the worst path is
        # outside them (e.g. input -> output through logic only) and the category summary would be misleading
        for mm in ("max", "min"):
            vals = [v["slack"] for k, v in cs.items() if k.endswith("_" + mm) and isinstance(v, dict)]
            w = ws.get((c, mm))
            if w is not None and vals and abs(w - min(vals)) > 1e-5:   # get_property prints 6 decimals
                problems.append(f"{c} worst_slack {mm} {w} != worst category slack {min(vals)}: "
                                f"the worst path is outside the three categories")
        summary[c] = {"ws_max": ws.get((c, "max")), "ws_min": ws.get((c, "min")), "categories": cs}

    result = {"valid": not problems, "problems": problems, "T_ns": T, "C_load_pF": cload, "sceneset": sceneset,
              "topology": topo, "corners": summary,
              "hold_note": "min hold slack under the ideal-clock, post-synthesis model only (spec 4.4)"}
    if not problems:
        wc = min(STD, key=lambda c: summary[c]["ws_max"])
        hc = min(STD, key=lambda c: summary[c]["ws_min"])
        cs = {k: v for k, v in summary[wc]["categories"].items() if k.endswith("_max") and isinstance(v, dict)}
        result["worst_setup"] = {"slack": summary[wc]["ws_max"], "corner": wc,
                                 "category": min(cs, key=lambda k: cs[k]["slack"])[:-4]}
        result["worst_hold"] = {"slack": summary[hc]["ws_min"], "corner": hc}
    with open(os.path.join(outdir, "sta_check.json"), "w", newline="\n") as f:
        json.dump(result, f, indent=1)
    for p in problems:
        print(f"STA INVALID: {p}")
    if problems:
        return 1
    print(f"STA VALID: worst setup {result['worst_setup']} worst hold {result['worst_hold']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except (OSError, IndexError, ValueError, AttributeError, KeyError, TypeError) as e:
        print(f"STA INVALID: incomplete or unreadable STA output ({type(e).__name__}: {e})")
        sys.exit(1)
