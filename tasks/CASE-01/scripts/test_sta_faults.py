"""Fault injection for scripts/sta_run.tcl + scripts/check_sta.py (spec 4.3-4.5, P1 M1/M2).

Usage (WSL login shell, from tasks/CASE-01):
  python3 scripts/test_sta_faults.py --with-reg2reg <netlist> --without-reg2reg <netlist>
Use CASE-01-shaped fixture netlists, never the baseline: e.g. the pipe2 fixture (L=2, has reg->reg paths) and the
mut_num mutant (L=1, no reg->reg paths), both synthesized with scripts/synth_case01.tcl.
Every case must be judged as expected; exits 1 otherwise. Work dirs stay under runs/stafaults-<ts>/.
"""
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys

CASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T, C = "20.0", "0.0024"
SRC_LINE = "source [file join $::env(CASE_DIR) sdc case01_sdc.tcl]\n"


def run_sta(work, name, netlist, script=None, sdc_extra="", sdc_edit=None):
    d = os.path.join(work, name)
    os.makedirs(os.path.join(d, "sdc"))
    os.makedirs(os.path.join(d, "out"))
    sdc = open(os.path.join(CASE, "sdc", "case01_sdc.tcl")).read()
    if sdc_edit:
        sdc = sdc_edit(sdc)
    with open(os.path.join(d, "sdc", "case01_sdc.tcl"), "w") as f:
        f.write(sdc + sdc_extra)
    script = script or os.path.join(CASE, "scripts", "sta_run.tcl")
    env = dict(os.environ, TOP="dot4sat", NETLIST=netlist, T_NS=T, CLOAD_PF=C, SCENESET="std",
               OUTDIR=os.path.join(d, "out"), CASE_DIR=d)
    with open(os.path.join(d, "out", "sta.log"), "w") as f:
        subprocess.run(["sta", "-no_init", "-no_splash", "-exit", script], env=env, stdout=f,
                       stderr=subprocess.STDOUT)
    return os.path.join(d, "out")


def check(outdir, t=T, c=C):
    r = subprocess.run([sys.executable, os.path.join(CASE, "scripts", "check_sta.py"), outdir, t, c, "std"],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def variant_script(work, name, transform):
    s = open(os.path.join(CASE, "scripts", "sta_run.tcl")).read()
    path = os.path.join(work, f"sta_run_{name}.tcl")
    with open(path, "w") as f:
        f.write(transform(s))
    return path


def mutate_copy(work, src, name, fn):
    dst = os.path.join(work, name, "out")
    shutil.copytree(src, dst)
    fn(dst)
    return dst


def edit_tsv(path, fn):
    p = os.path.join(path, "sta_results.tsv")
    lines = open(p).read().splitlines()
    with open(p, "w") as f:
        f.write("\n".join(fn(lines)) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-reg2reg", required=True)
    ap.add_argument("--without-reg2reg", required=True)
    args = ap.parse_args(argv)
    net_rr, net_norr = os.path.abspath(args.with_reg2reg), os.path.abspath(args.without_reg2reg)
    work = os.path.join(CASE, "runs", f"stafaults-{datetime.datetime.now():%Y%m%d-%H%M%S}")
    os.makedirs(work)
    results = []

    def expect(name, outdir, want, text="", t=T, c=C):
        rc, out = check(outdir, t, c)
        ok = (rc == 0) if want == "valid" else (rc != 0 and text in out)
        results.append(ok)
        print(f"{'PASS' if ok else 'FAIL'} {name}" + ("" if ok else f" (exit {rc}, want {want} {text!r})\n"
                                                           + "\n".join("     " + l for l in out.splitlines()[:5])))

    normal = run_sta(work, "normal", net_rr)
    expect("normal (with reg2reg)", normal, "valid")
    expect("normal (no reg2reg: category not applicable)", run_sta(work, "normal_norr", net_norr), "valid")

    sdc_first = variant_script(work, "sdc_first", lambda s: s.replace("sky130_define_scenes\n", "", 1)
                               .replace(SRC_LINE, SRC_LINE + "sky130_define_scenes\n", 1))
    expect("SDC before define_scene (TOOL-012)", run_sta(work, "sdc_first", net_rr, script=sdc_first),
           "invalid", "ext pin cap")
    misbind = variant_script(work, "misbind", lambda s: s.replace(
        "sky130_define_scenes\n",
        "foreach c $corners { define_scene $c -liberty_min sky130_fd_sc_hd__tt_025C_1v80 "
        "-liberty_max sky130_fd_sc_hd__$c }\n", 1))
    expect("min library mis-bound to tt", run_sta(work, "misbind", net_rr, script=misbind), "invalid",
           "delay calc PVT")
    expect("in_b loses input delay and driver", run_sta(
        work, "missing_delay", net_rr, sdc_edit=lambda s: s.replace("in_a[*] in_b[*] in_valid rst", "in_a[*] in_valid rst")),
        "invalid", "check_setup returned")
    expect("one bit has another input delay", run_sta(
        work, "wrong_delay", net_rr, sdc_extra="set_input_delay -clock clk -max 0.5 [get_ports {in_b[3]}]\n"),
        "invalid", "input delay of in_b[3]")
    expect("false path added", run_sta(work, "false_path", net_rr, sdc_extra="set_false_path -from [get_ports rst]\n"),
           "invalid", "forbidden constraint")
    expect("checker told another period", normal, "invalid", "clock period", t="21.0")
    expect("checker told another C_load", normal, "invalid", "ext pin cap", c="0.0030")

    def drop_cat(d):
        edit_tsv(d, lambda ls: [l for l in ls if not l.startswith("CAT\t")])
    expect("all CAT records deleted", mutate_copy(work, normal, "no_cat", drop_cat), "invalid", "CAT record missing")

    def drop_reports(d):
        for n in os.listdir(d):
            if re.match(r"path_(max|min)_.*\.rpt$", n):
                os.remove(os.path.join(d, n))
    expect("global path reports deleted", mutate_copy(work, normal, "no_reports", drop_reports), "invalid",
           "missing report")

    def all_none(d):
        edit_tsv(d, lambda ls: ["\t".join(l.split("\t")[:4] + ["NONE"]) if l.startswith("CAT\t") else l
                                for l in ls])
    expect("all categories claimed absent", mutate_copy(work, normal, "all_none", all_none), "invalid",
           "structural path exists")

    def load_nan(d):
        edit_tsv(d, lambda ls: ["\t".join(l.split("\t")[:2] + ["nan", "nan"]) if l.startswith("LOAD\t") else l
                                for l in ls])
    expect("LOAD values are nan", mutate_copy(work, normal, "load_nan", load_nan), "invalid", "ext pin cap")

    def dup_cat(d):
        cat = [l for l in open(os.path.join(d, "sta_results.tsv")).read().splitlines() if l.startswith("CAT\t")]
        assert cat, "normal run has no CAT records"
        edit_tsv(d, lambda ls: ls + cat[:1])
    expect("duplicate CAT record", mutate_copy(work, normal, "dup_cat", dup_cat), "invalid", "duplicate CAT")

    def drop_ws(d):
        edit_tsv(d, lambda ls: [l for l in ls if not l.startswith("WS\tss_n40C_1v60\tmax")])
    expect("one WS record deleted", mutate_copy(work, normal, "drop_ws", drop_ws), "invalid", "worst_slack max")

    def topo_zero(d):
        edit_tsv(d, lambda ls: ["TOPO\treg2reg\t0" if l.startswith("TOPO\treg2reg") else l for l in ls])
    expect("timing path without structural path", mutate_copy(work, normal, "topo_zero", topo_zero), "invalid",
           "no structural path")

    def ws_outside(d):   # worst slack lower than every category: the worst path would be uncategorized
        edit_tsv(d, lambda ls: ["WS\tss_n40C_1v60\tmax\t-999.0" if l.startswith("WS\tss_n40C_1v60\tmax") else l
                                for l in ls])
    expect("worst slack outside the three categories", mutate_copy(work, normal, "ws_outside", ws_outside),
           "invalid", "outside the three categories")

    def tamper_report(d):
        p = os.path.join(d, "cat_ss_n40C_1v60_in2reg_max.rpt")
        s = open(p).read()
        s = re.sub(r"^(\s*)(-?[0-9.]+)(\s+slack)", lambda m: m.group(1) + "99.0000" + m.group(3), s, count=1,
                   flags=re.M)
        open(p, "w").write(s)
    expect("category report slack tampered", mutate_copy(work, normal, "tamper_rpt", tamper_report), "invalid",
           "!= record")

    n_ok = sum(results)
    print(f"== {n_ok} of {len(results)} cases as expected -> {os.path.relpath(work, CASE)}")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
