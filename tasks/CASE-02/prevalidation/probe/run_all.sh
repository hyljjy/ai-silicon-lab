#!/usr/bin/env bash
# Adapted and extended from scratch/probe/run_all.sh (the original covered q1–q8 only). Reruns all 13 probes exactly as
# the recorded probe_out/ directories were produced: q1–q11 and q13 with run_probe.sh (600 s), q12 with run_probe300.sh
# (300 s); q8 and q13 in whatif mode; q10–q13 on the missing version only.
S=$(cd "$(dirname "$0")" && pwd)
for q in q1_checksetup q2_reportchecks q3_worst_tns q4_perport q5_enumerate q6_fanin q7_safety; do
  for k in missing correct; do "$S/run_probe.sh" ${q}_$k $k $q.tcl; done
done
"$S/run_probe.sh" q8_whatif_missing missing q8_whatif.tcl whatif
"$S/run_probe.sh" q8_whatif_correct correct q8_whatif.tcl whatif
for q in q9_arrival; do for k in missing correct; do "$S/run_probe.sh" ${q}_$k $k $q.tcl; done; done
"$S/run_probe.sh" q10_flush_missing missing q10_flush.tcl
"$S/run_probe.sh" q11_noscene_missing missing q11_noscene.tcl
"$S/run_probe300.sh" q12_sixscene_missing missing q12_sixscene.tcl
"$S/run_probe.sh" q13_calib_missing missing q13_calib.tcl whatif
