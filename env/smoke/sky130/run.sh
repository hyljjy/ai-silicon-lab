#!/bin/bash -l
# Sky130 smoke flow: RTL sim -> Yosys (tt, LibreLane excluded cells) -> gate-level sim -> 16-corner STA.
# Run from this directory: ./run.sh   (exits non-zero with a "FAIL: ..." line if any step fails; see docs/env/BUGLOG.md PRJ-001)
set -eo pipefail
cd "$(dirname "$0")"

fail() { echo "FAIL: $1"; exit 1; }
check_sim() {  # $1 = label, $2 = log; tb.v only prints PASS/FAIL and always $finish-es with 0, so judge by its output
  head -1 "$2"
  grep -q '^SIM PASS' "$2" || fail "$1 simulation did not print SIM PASS (see $2)"
}

iverilog -o rtl_sim tb.v mac.v > rtl_compile.log 2>&1 || { tail -5 rtl_compile.log; fail "RTL compile (see rtl_compile.log)"; }
vvp rtl_sim > rtl_sim.log 2>&1 || { tail -3 rtl_sim.log; fail "RTL simulation exited non-zero (see rtl_sim.log)"; }
check_sim RTL rtl_sim.log

TOP=mac RTL=mac.v OUT=mac_netlist.v yosys -q -c $SKY130_KIT/synth.tcl -l yosys.log > /dev/null 2>&1 \
  || { tail -5 yosys.log; fail "synthesis (see yosys.log)"; }
grep "Chip area" yosys.log

iverilog -DFUNCTIONAL -DUNIT_DELAY=#1 -o gl_sim tb.v mac_netlist.v \
  $SKY130_HD/verilog/primitives.v $SKY130_HD/verilog/sky130_fd_sc_hd.v > gl_compile.log 2>&1 \
  || { grep -iv warning gl_compile.log | tail -5; fail "gate-level compile (see gl_compile.log)"; }
vvp gl_sim > gl_sim.log 2>&1 || { tail -3 gl_sim.log; fail "gate-level simulation exited non-zero (see gl_sim.log)"; }
check_sim gate-level gl_sim.log

sta -no_init -no_splash -exit sta.tcl > sta.log 2>&1 \
  || { tail -3 sta.log; fail "OpenSTA exited non-zero (see sta.log)"; }
if grep -qiE '^(error|warning)' sta.log; then
  grep -iE '^(error|warning)' sta.log | head -5; fail "OpenSTA reported errors/warnings (see sta.log)"
fi
sed -n '1,17p' sta.log
echo "SMOKE OK"
