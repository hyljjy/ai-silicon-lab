#!/bin/bash -l
cd "$(dirname "$0")"
sed -e 's/^synth -top \$::env(TOP)$/synth -top $::env(TOP) -noabc/' -e 's/^abc -liberty/abc -script {+strash;dc2;\&get -n;\&dch -f;\&nf;\&put} -liberty/' $SKY130_KIT/synth.tcl > synth_dc2.tcl
grep -n "^synth\|^abc" synth_dc2.tcl
rm -rf E4_n16_dc2; mkdir E4_n16_dc2; s=$(date +%s)
( cd E4_n16_dc2 && env -u SYNTH_LIB TOP=dot4sat RTL=$PWD/../../rtl/dot4sat.v OUT=net.v timeout 1200 yosys -q -c ../synth_dc2.tcl -l yosys.log > /dev/null 2>&1 ); rc=$?
echo "E4_n16_dc2 exit=$rc time=$(( $(date +%s)-s ))s $(grep 'Chip area' E4_n16_dc2/yosys.log | tail -1)"
