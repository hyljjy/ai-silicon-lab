#!/bin/bash -l
# Infra test only: does sta_run.tcl + check_sta.py work on a CASE-01-shaped netlist (E4 recipe)? Not a result.
cd "$(dirname "$0")"
rm -rf out/sta_t; mkdir -p out/sta_t
s=$(date +%s)
TOP=dot4sat NETLIST=$PWD/exp/E4_n16_dc2/net.v T_NS=20.0 CLOAD_PF=0.0024 SCENESET=std OUTDIR=$PWD/out/sta_t CASE_DIR=$PWD \
  sta -no_init -no_splash -exit scripts/sta_run.tcl > out/sta_t/sta.log 2>&1; echo "sta exit=$? ($(( $(date +%s)-s ))s)"
grep -iE "^(error|warning)" out/sta_t/sta.log | head -5
python3 scripts/check_sta.py out/sta_t 20.0 0.0024 std > out/sta_t/check.log; echo "check_sta exit=$?"
grep -E "INVALID" out/sta_t/check.log | head -10
grep -E "^(MODE|SCENES|CHECK_SETUP|OBJECTS|DONE)" out/sta_t/sta_results.tsv
grep -c "^LOAD" out/sta_t/sta_results.tsv; grep "^CAT" out/sta_t/sta_results.tsv | cut -f2-4,6 | head -6 | sed 's/\t-\?[0-9.]*\t/\t<slack>\t/'
grep -m1 "P = " out/sta_t/dcalc_ss_n40C_1v60.txt
grep -vE "^(set_input_delay|set_output_delay|set_driving_cell|set_load|#|$)" out/sta_t/expanded.sdc
