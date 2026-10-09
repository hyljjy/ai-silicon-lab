"""Validate one CASE-01 STA run (spec 4.3-4.5) and summarize it.

Usage: python3 scripts/check_sta.py <outdir> <T_ns> <C_load_pF> <std|all>
Reads <outdir>/{sta_results.tsv, expanded.sdc, dcalc_<corner>.txt}; writes <outdir>/sta_check.json.
Exit 0 = analysis valid (negative slack is NOT a failure); exit 1 = invalid analysis.
"""
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
FORBIDDEN = ("set_false_path", "set_multicycle_path", "set_disable_timing", "set_case_analysis",
             "set_max_delay", "set_min_delay")
TOL = 1e-4  # write_sdc prints 4 decimals

RE_CLOCK = re.compile(r"^create_clock -name clk -period ([0-9.]+) \[get_ports \{clk\}\]$")
RE_IODELAY = re.compile(r"^set_(input|output)_delay ([0-9.eE+-]+) -clock \[get_clocks \{clk\}\] "
                        r"-(min|max) -add_delay \[get_ports \{(.+)\}\]$")
RE_DRIVE = re.compile(r"^set_driving_cell -lib_cell sky130_fd_sc_hd__buf_2 -from_pin \{A\} -pin \{X\} "
                      r"-input_transition_rise 0\.0000 -input_transition_fall 0\.0000 \[get_ports \{(.+)\}\]$")
RE_LOAD = re.compile(r"^set_load -pin_load ([0-9.eE+-]+) \[get_ports \{(.+)\}\]$")
CLOCK_ZERO = {  # spec 4.3: written explicitly as 0 by sdc/case01_sdc.tcl; each must be present
    "set_clock_transition 0.0000 [get_clocks {clk}]",
    "set_clock_uncertainty 0.0000 clk",
    "set_clock_latency 0.0000 [get_clocks {clk}]",
    "set_clock_latency -source 0.0000 [get_clocks {clk}]",
}
RE_PVT = re.compile(r"P = ([0-9.-]+) V = ([0-9.-]+) T = ([0-9.-]+)")
RE_CORNER = re.compile(r"^(tt|ss|ff)_(n?)(\d+)C_(\d)v(\d+)$")


def corner_pvt(name):
    m = RE_CORNER.match(name)
    temp = -int(m.group(3)) if m.group(2) else int(m.group(3))
    return float(f"{m.group(4)}.{m.group(5)}"), float(temp)


def finite(x):
    try:
        v = float(x)
    except ValueError:
        return None
    return v if math.isfinite(v) and abs(v) < 1e29 else None


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
    for raw in join_continuations(lines):
        line = raw.strip()
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
            table.setdefault(m.group(4), {})[m.group(3)] = float(m.group(2))
            continue
        m = RE_DRIVE.match(line)
        if m:
            drv.add(m.group(1))
            continue
        m = RE_LOAD.match(line)
        if m:
            load[m.group(2)] = float(m.group(1))
            continue
        problems.append(f"unrecognized constraint line: {line}")
    if len(clock) != 1 or abs(clock[0] - T) > TOL:
        problems.append(f"clock period {clock} != {T}")
    if zeros != CLOCK_ZERO:
        problems.append(f"missing explicit zero clock settings: {sorted(CLOCK_ZERO - zeros)}")
    for name, table, ports in (("input", in_d, EXPECT_IN), ("output", out_d, EXPECT_OUT)):
        if set(table) != set(ports):
            problems.append(f"{name} delay ports mismatch: missing {sorted(set(ports) - set(table))[:5]} "
                            f"extra {sorted(set(table) - set(ports))[:5]}")
        for p, mm in table.items():
            if abs(mm.get("max", -1) - 0.2 * T) > TOL or abs(mm.get("min", -1)) > TOL:
                problems.append(f"{name} delay of {p} is {mm}, want max={0.2 * T} min=0")
    if drv != set(EXPECT_IN):
        problems.append(f"driving cell ports mismatch ({len(drv)} of {len(EXPECT_IN)})")
    if set(load) != set(EXPECT_OUT) or any(abs(v - cload) > TOL for v in load.values()):
        problems.append(f"set_load mismatch in expanded.sdc ({len(load)} ports)")


def main(argv):
    if len(argv) != 5:
        print(__doc__)
        return 1
    outdir, T, cload, sceneset = argv[1], float(argv[2]), float(argv[3]), argv[4]
    corners = STD if sceneset == "std" else STD + SWEEP
    problems = []
    rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(outdir, "sta_results.tsv"))]
    get = lambda key: [r[1:] for r in rows if r[0] == key]
    if not get("DONE"):
        problems.append("sta_results.tsv incomplete (no DONE)")
    if get("MODE") != [["default"]]:
        problems.append(f"mode {get('MODE')} != default")
    if get("SCENES") != [corners]:
        problems.append(f"scenes {get('SCENES')} != {corners}")
    if get("CHECK_SETUP") != [["1"]]:
        problems.append(f"check_setup returned {get('CHECK_SETUP')} (1 = no warnings)")
    loads = {r[0]: r[1:] for r in get("LOAD")}
    if set(loads) != set(EXPECT_OUT):
        problems.append(f"LOAD ports mismatch ({len(loads)} of {len(EXPECT_OUT)})")
    for p, (cmax, cmin) in loads.items():
        if abs(float(cmax) - cload * 1e-12) > 1e-18 or abs(float(cmin) - cload * 1e-12) > 1e-18:
            problems.append(f"port {p} ext pin cap {cmax}/{cmin} F != {cload} pF")
    objs = get("OBJECTS")
    if objs != [[str(len(EXPECT_IN)), str(len(EXPECT_OUT))] + objs[0][2:]] or int(objs[0][2]) == 0:
        problems.append(f"object counts {objs}, want {len(EXPECT_IN)} inputs, {len(EXPECT_OUT)} outputs, >0 regs")
    check_sdc(open(os.path.join(outdir, "expanded.sdc")).read().splitlines(), T, cload, problems)

    summary = {}
    for c in corners:
        text = open(os.path.join(outdir, f"dcalc_{c}.txt")).read()
        m = RE_PVT.search(text)
        v, t = corner_pvt(c)
        if not m or abs(float(m.group(2)) - v) > 1e-3 or abs(float(m.group(3)) - t) > 1e-3:
            problems.append(f"scene {c} delay calc PVT {m.groups() if m else None} != V={v} T={t}")
        ws = {r[1]: finite(r[2]) for r in get("WS") if r[0] == c}
        for mm in ("max", "min"):
            if ws.get(mm) is None:
                problems.append(f"{c} worst_slack {mm} not finite")
        cats = {}
        for r in get("CAT"):
            if r[0] != c:
                continue
            cat, mm, val = r[1], r[2], r[3]
            if val == "UNCONSTRAINED":
                problems.append(f"{c} {cat} {mm}: paths exist but are unconstrained")
            elif val == "NONE":
                cats[f"{cat}_{mm}"] = "not_applicable"
            elif finite(val) is None:
                problems.append(f"{c} {cat} {mm}: slack {val} not finite")
            else:
                cats[f"{cat}_{mm}"] = {"slack": finite(val), "start": r[4], "end": r[5]}
        summary[c] = {"ws_max": ws.get("max"), "ws_min": ws.get("min"), "categories": cats}

    result = {"valid": not problems, "problems": problems, "T_ns": T, "C_load_pF": cload,
              "sceneset": sceneset, "corners": summary}
    std_ok = [c for c in STD if summary.get(c, {}).get("ws_max") is not None]
    if not problems and std_ok:
        wc = min(std_ok, key=lambda c: summary[c]["ws_max"])
        hc = min(std_ok, key=lambda c: summary[c]["ws_min"])
        cats = {k: v for k, v in summary[wc]["categories"].items() if k.endswith("_max") and isinstance(v, dict)}
        result["worst_setup"] = {"slack": summary[wc]["ws_max"], "corner": wc,
                                 "category": min(cats, key=lambda k: cats[k]["slack"])[:-4] if cats else None}
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
    except (OSError, IndexError, ValueError, AttributeError) as e:
        print(f"STA INVALID: incomplete or unreadable STA output ({type(e).__name__}: {e})")
        sys.exit(1)
