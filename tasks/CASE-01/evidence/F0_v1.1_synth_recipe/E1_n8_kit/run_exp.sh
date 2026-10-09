#!/bin/bash -l
# E1: N=8 frozen recipe; E2: N=16 abc -fast (no fraig) both calls; E3: N=16 synth -noabc + default abc -liberty
cd "$(dirname "$0")"
sed 's/^synth -top \$::env(TOP)$/synth -top $::env(TOP) -noabc/' $SKY130_KIT/synth.tcl > synth_noabc.tcl
sed -e 's/^synth -top \$::env(TOP)$/synth -top $::env(TOP) -noabc/' -e 's/^abc -liberty/abc -fast -liberty/' $SKY130_KIT/synth.tcl > synth_fast.tcl
diff $SKY130_KIT/synth.tcl synth_noabc.tcl; diff $SKY130_KIT/synth.tcl synth_fast.tcl
one() { local name=$1 script=$2 rtl=$3; mkdir -p $name; local s=$(date +%s)
  ( cd $name && env -u SYNTH_LIB TOP=dot4sat RTL=$rtl OUT=net.v timeout 1200 yosys -q -c $script -l yosys.log > /dev/null 2>&1 ); local rc=$?
  echo "$name exit=$rc time=$(( $(date +%s)-s ))s $(grep 'Chip area' $name/yosys.log | tail -1)"; }
one E1_n8_frozen  $SKY130_KIT/synth.tcl  $PWD/dot4sat8.v &
one E2_n16_fast   $PWD/synth_fast.tcl    $PWD/../rtl/dot4sat.v &
one E3_n16_noabc  $PWD/synth_noabc.tcl   $PWD/../rtl/dot4sat.v &
wait
