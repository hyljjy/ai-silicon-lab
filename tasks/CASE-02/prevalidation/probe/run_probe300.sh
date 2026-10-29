#!/usr/bin/env bash
# Adapted from scratch/probe/run_probe300.sh (original kept in the external archive; see MANIFEST.tsv). Paths are repo-relative.
# usage: run_probe300.sh <name> <correct|missing> <query.tcl> [query|whatif]
# Rebuilds the context through the stage-A safe interpreter (safe_query.tcl = tasks/CASE-01/diag/scripts/diag_query.tcl
# with line 8 changed per probe/safe_query.diff; generated into rerun/ on first use), runs the query, and compares the rebuilt
# records with a reference run byte for byte. Safe-interpreter time limit: 300 s. Outputs: ${PREVAL_OUT:-<prevalidation>/rerun}/probe_out/<name>/.
# Reference for the record comparison: ${PREVAL_REF:-rerun/runs/<kind>_1 if present, else the committed subset runs/<kind>_1
# (sta_results.tsv, expanded.sdc only)}. For a full-file comparison run ./run.sh <kind>_1 <kind> first.
set -u
S=$(cd "$(dirname "$0")/.." && pwd)
ROOT=$(cd "$S/../../.." && pwd)
F1=$ROOT/tasks/CASE-01/runs/20261009-092827-base-T27.91
OUTROOT=${PREVAL_OUT:-$S/rerun}
name=$1; kind=$2; q=$3; mode=${4:-query}
mkdir -p "$OUTROOT"
SAFE=$OUTROOT/safe_query.tcl
[ -f "$SAFE" ] || patch -s -o "$SAFE" "$ROOT/tasks/CASE-01/diag/scripts/diag_query.tcl" "$S/probe/safe_query.diff"
ref=${PREVAL_REF:-}
if [ -z "$ref" ]; then if [ -d "$OUTROOT/runs/${kind}_1" ]; then ref=$OUTROOT/runs/${kind}_1; else ref=$S/runs/${kind}_1; fi; fi
out=$OUTROOT/probe_out/$name; rm -rf "$out"; mkdir -p "$out/env"
case $kind in
  correct) sdc=$ROOT/tasks/CASE-01/sdc/case01_sdc.tcl ;;
  missing) sdc=$S/case02_missing_inb.tcl ;;
esac
export TOP=dot4sat NETLIST=$F1/synth/netlist.v T_NS=27.91 CLOAD_PF=0.0024 SCENESET=std OUTDIR=$out/env CASE_DIR=$F1/inputs
export SDC_FILE=$sdc DRIVER=$S/sta_run_case02.tcl QUERY_FILE=$S/probe/$q QUERY_MODE=$mode
export RULES_DIR=$ROOT/tasks/CASE-01/diag/rules CASE01_NONCE=probe CASE01_QUERY_SECONDS=300
cp "$S/probe/$q" "$out/query.tcl"
cd "$out"
start=$(date +%s.%N)
sta -no_init -no_splash -exit "$SAFE" > full.log 2>&1; rc=$?
end=$(date +%s.%N)
{ echo "name=$name kind=$kind query=$q mode=$mode rc=$rc seconds=$(echo "$end - $start" | bc)"
  echo "argv: sta -no_init -no_splash -exit $SAFE"; echo "SDC_FILE=$sdc"; echo "ref=$ref"
  bad=0; for f in "$ref"/*; do b=$(basename "$f"); [ "$b" = cmd.txt ] && continue; [ "$b" = sta.log ] && continue; cmp -s "$f" "env/$b" || { echo "ENV DIFF: $b"; bad=1; }; done
  echo "env_records_identical_to_ref=$((1-bad))"; } > cmd.txt
# the query part of the log (after the env build)
awk '/=== CASE01-probe QUERY BEGIN/{p=1} p' full.log > query.txt
cat cmd.txt; echo "query lines: $(wc -l < query.txt)"
