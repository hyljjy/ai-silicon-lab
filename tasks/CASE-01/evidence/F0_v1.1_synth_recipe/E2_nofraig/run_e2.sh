#!/bin/bash -l
cd "$(dirname "$0")"
sed -e 's/^synth -top \$::env(TOP)$/synth -top $::env(TOP) -noabc/' -e 's/^abc -liberty/abc -script {+strash;\&get -n;\&dch -f;\&nf;\&put} -liberty/' $SKY130_KIT/synth.tcl > synth_nofraig.tcl
diff $SKY130_KIT/synth.tcl synth_nofraig.tcl
rm -rf E2_n16_nofraig; mkdir E2_n16_nofraig; s=$(date +%s)
( cd E2_n16_nofraig && env -u SYNTH_LIB TOP=dot4sat RTL=$PWD/../../rtl/dot4sat.v OUT=net.v timeout 1200 yosys -q -c ../synth_nofraig.tcl -l yosys.log > /dev/null 2>&1 ); rc=$?
echo "E2_n16_nofraig exit=$rc time=$(( $(date +%s)-s ))s $(grep 'Chip area' E2_n16_nofraig/yosys.log | tail -1)"; tail -2 E2_n16_nofraig/yosys.log
