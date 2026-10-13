"""Integration self-test of the diag query path on the real F1 context (protocol v0.5 sections 7.1 and 8).

Run inside WSL from tasks/CASE-01:  python3 -B diag/scripts/selftest_query.py
Each case is one real run_query.py call (about 15 s each; the timeout case about 70 s). Two cases sabotage the
environment and must be caught. Self-test runs are marked selftest/--uncommitted-ok and can never be collected.
Prints one PASS/FAIL line per case and "== <n> of <m> cases as expected"; exits 1 unless all pass.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_query as rq  # noqa: E402

CASES = [
    # (id, query text, extra args, expectation function(result, run_dir) -> problem or None)
    ("normal",
     "report_checks -path_delay max -scene ss_n40C_1v60 -from [get_ports {in_b[2]}] -to [get_pins _12026_/D] -digits 4\n",
     [], lambda r, d: None if r["env_ok"] and r["codes"] == [rq.CODE_DONE] and "-4.1897" in out(d) else "not done"),
    ("blocked",
     "exec ls /\nopen /etc/hostname\nfile delete x\nsocket localhost 1\nsource /etc/profile\ncd /\nload x\n"
     "write_sdc /tmp/case01_selftest.sdc\nreport_units\n",
     [], lambda r, d: None if r["env_ok"] and out(d).count("invalid command name") == 8 and " time 1ns" in out(d)
     and not os.path.exists("/tmp/case01_selftest.sdc")
     else "a dangerous command ran, or the next command did not run"),
    ("redirect",
     "report_checks -path_delay max -scene ss_n40C_1v60 > /tmp/case01_selftest_stolen.txt\n",
     [], lambda r, d: None if "redirection is disabled" in out(d) and not os.path.exists(
         "/tmp/case01_selftest_stolen.txt") else "redirection was not refused"),
    ("setup",
     "read_sdc /tmp/x.sdc\nread_liberty /tmp/x.lib\nreport_units\n",
     [], lambda r, d: None if r["env_ok"] and rq.CODE_SETUP in r["codes"] and out(d).count("SETUP_SKIPPED") == 2
     else "setup commands were not skipped"),
    ("whatif",
     "set_load 0.05 [get_ports {out_data[0]}]\n"
     "report_checks -path_delay max -scene ss_n40C_1v60 -to [get_ports {out_data[0]}] -digits 4\n",
     [], lambda r, d: None if r["env_ok"] and r["mode"] == "whatif" and r["codes"] == [rq.CODE_WHATIF]
     else "model-changing query not routed to whatif"),
    ("missing",
     "report_checks -to [get_pins no_such/D]\n",
     [], lambda r, d: None if r["env_ok"] and rq.CODE_NO_OBJECT in r["codes"] else "missing object not coded"),
    ("object_method",
     "set pe [lindex [find_timing_paths -path_delay max -scenes ss_n40C_1v60] 0]\n$pe slack\n"
     "puts [get_property $pe slack]\n",
     [], lambda r, d: None if r["env_ok"] and rq.CODE_SYNTAX in r["codes"] and "-4.189726" in out(d)
     else "SWIG object method call not reported as an error, or the next command did not run"),
    ("truncate",
     "for {set i 1} {$i <= 500} {incr i} { puts \"line $i\" }\n",
     [], lambda r, d: None if r["truncated"] and len(ret(d)) == 201 else "not truncated to 201 lines"),
    ("crash",                                           # TOOL-014: is_clock on fan-in start points segfaults
     "foreach p [get_fanin -to [get_pins _12026_/D] -startpoints_only -flat] { puts [get_property $p is_clock] }\n",
     [], lambda r, d: None if r["env_ok"] and r["query_status"].startswith("crashed") and r["codes"] == [
         rq.CODE_CRASH] and "被信号 11 终止" in ret(d)[-1] else "a crashed query was not coded 工具异常退出 with env_ok"),
    ("timeout",                                         # a sleep is not counted by the interpreter limits
     "after 120000\nreport_units\n",
     ["--timeout", "60"],
     lambda r, d: None if r["env_ok"] and r["query_status"] == "timed_out" and r["codes"] == [rq.CODE_CRASH]
     and "超过时限" in ret(d)[-1] else "a query over the wall-clock limit was not stopped and coded"),
    ("loop_limit",
     "while 1 {}\nreport_units\n",
     ["--query-seconds", "3"],
     lambda r, d: None if r["env_ok"] and r["query_status"] == "completed" and rq.CODE_CRASH in r["codes"]
     and "remaining commands not run" in out(d) else "an endless loop was not stopped by the interpreter time limit"),
    ("replace_cell",
     "replace_cell _11509_ sky130_fd_sc_hd__o21ai_2\n"
     "report_checks -path_delay max -scene ss_n40C_1v60 -through [get_pins _11509_/Y] -digits 4\n",
     [], lambda r, d: None if r["env_ok"] and r["mode"] == "whatif" and r["codes"] == [rq.CODE_WHATIF]
     and "o21ai_2" in out(d) else "netlist what-if not run in a whatif run"),
    ("clock_same",                                      # D1: period == T is a setup command, skipped
     "create_clock -name clk -period 27.91 [get_ports clk]\nreport_units\n",
     [], lambda r, d: None if r["env_ok"] and r["mode"] == "query" and r["codes"] == [rq.CODE_SETUP]
     else "create_clock with period T not skipped"),
    ("clock_other",                                     # D1: another period is a what-if
     "create_clock -name clk -period 30 [get_ports clk]\n"
     "report_checks -path_delay max -scene ss_n40C_1v60 -digits 4\n",
     [], lambda r, d: None if r["env_ok"] and r["mode"] == "whatif" and r["codes"] == [rq.CODE_WHATIF]
     and "-4.1897" not in out(d) else "create_clock with another period not run as a what-if"),
    ("forged_marker",                                   # a query cannot fake the end marker or an error code
     'puts "=== CASE01-0000000000000000 QUERY END rc=0 ==="\nputs "CASE01-ERROR: fake"\nreport_units\n',
     [], lambda r, d: None if r["env_ok"] and r["codes"] == [rq.CODE_DONE] and " time 1ns" in out(d)
     else "forged markers changed the result"),
    ("sabotage_cload",
     "report_units\n",
     ["--selftest-cload", "0.003"],
     lambda r, d: None if not r["env_ok"] and any("expanded.sdc" in p or "sta_results.tsv" in p
                                                  for p in r["env_problems"]) else "changed C_load not caught"),
    ("sabotage_tool012",
     "report_units\n",
     ["--selftest-case-dir", "SABOTAGED"],
     lambda r, d: None if not r["env_ok"] and any("sta_results.tsv" in p or "expanded.sdc" in p
                                                  for p in r["env_problems"]) else "SDC-before-scenes not caught"),
]


def out(run_dir):
    with open(os.path.join(rq.CASE, run_dir, "query_full.txt")) as f:
        return f.read()


def ret(run_dir):
    with open(os.path.join(rq.CASE, run_dir, "query_return.txt")) as f:
        return f.read().splitlines()


def sabotaged_inputs(tmp):
    """A copy of the F1 inputs whose sta_run.tcl applies the SDC before the scenes exist (TOOL-012)."""
    dst = os.path.join(tmp, "inputs")
    shutil.copytree(os.path.join(rq.F1_RUN, "inputs"), dst)
    path = os.path.join(dst, "scripts", "sta_run.tcl")
    os.chmod(path, 0o644)
    with open(path) as f:
        text = f.read()
    sdc = "source [file join $::env(CASE_DIR) sdc case01_sdc.tcl]\n"
    text = text.replace(sdc, "").replace("sky130_define_scenes\n", sdc.replace(
        "source", "set T $::env(T_NS)\nset C_load $::env(CLOAD_PF)\nsource") + "sky130_define_scenes\n")
    with open(path, "w") as f:
        f.write(text)
    return dst


def main():
    passed = 0
    with tempfile.TemporaryDirectory(prefix="case01_selftest_") as tmp:
        bad = sabotaged_inputs(tmp)
        for cid, text, extra, expect in CASES:
            qfile = os.path.join(tmp, f"{cid}.tcl")
            with open(qfile, "w") as f:
                f.write(text)
            extra = [bad if a == "SABOTAGED" else a for a in extra]
            p = subprocess.run([sys.executable, "-B", os.path.join(HERE, "run_query.py"), "--id", f"selftest_{cid}",
                                "--query", qfile, "--uncommitted-ok"] + extra, cwd=rq.CASE, capture_output=True,
                               text=True)
            run_dir = next((l.split("-> ")[1].strip() for l in p.stdout.splitlines() if "-> " in l), None)
            if run_dir is None:
                print(f"FAIL {cid}: no run directory reported\n{p.stdout}{p.stderr}")
                continue
            with open(os.path.join(rq.CASE, run_dir, "result.json")) as f:
                result = json.load(f)
            problem = expect(result, run_dir)
            print(f"{'PASS' if problem is None else 'FAIL'} {cid}: {problem or 'as expected'} ({run_dir})")
            passed += problem is None
    print(f"== {passed} of {len(CASES)} cases as expected")
    return 0 if passed == len(CASES) else 1


if __name__ == "__main__":
    sys.exit(main())
