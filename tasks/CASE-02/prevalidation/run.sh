#!/usr/bin/env bash
# Adapted from scratch/run.sh (original kept in the external archive; see MANIFEST.tsv). Paths are repo-relative.
# usage: run.sh <name> <correct|missing>   -> ${PREVAL_OUT:-<this dir>/rerun}/runs/<name>/
# Run inside WSL Ubuntu-24.04 (user eda) with OpenSTA 3.1.0 on PATH. Needs the F1 baseline run directory
# tasks/CASE-01/runs/20261009-092827-base-T27.91 (not in git; rebuild it per tasks/CASE-01/revise/REPRODUCE.md).
set -u
S=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$S/../../.." && pwd)
F1=$ROOT/tasks/CASE-01/runs/20261009-092827-base-T27.91
OUTROOT=${PREVAL_OUT:-$S/rerun}
name=$1; kind=$2
out=$OUTROOT/runs/$name; rm -rf "$out"; mkdir -p "$out"
case $kind in
  correct) sdc=$ROOT/tasks/CASE-01/sdc/case01_sdc.tcl ;;
  missing) sdc=$S/case02_missing_inb.tcl ;;
  *) echo "bad kind"; exit 2 ;;
esac
export TOP=dot4sat NETLIST=$F1/synth/netlist.v T_NS=27.91 CLOAD_PF=0.0024 SCENESET=std OUTDIR=$out CASE_DIR=$F1/inputs SDC_FILE=$sdc
cd "$out"
{ echo "argv: sta -no_init -no_splash -exit $S/sta_run_case02.tcl"; echo "SDC_FILE=$sdc"; echo "NETLIST=$NETLIST"; } > cmd.txt
sta -no_init -no_splash -exit "$S/sta_run_case02.tcl" > sta.log 2>&1
echo "rc=$?" >> cmd.txt
cat cmd.txt
