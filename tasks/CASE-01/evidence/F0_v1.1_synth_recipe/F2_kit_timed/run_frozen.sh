#!/bin/bash -l
# Frozen recipe (env/sky130hd_kit/synth.tcl, unchanged), N=16 baseline: measure the full synthesis time.
cd "$(dirname "$0")"
rm -rf F_n16_frozen; mkdir F_n16_frozen; cd F_n16_frozen
echo "start $(date '+%F %T')" > timing.txt
env -u SYNTH_LIB TOP=dot4sat RTL=$PWD/../../rtl/dot4sat.v OUT=net.v timeout 7000 yosys -q -c $SKY130_KIT/synth.tcl -l yosys.log > /dev/null 2>&1
rc=$?
echo "end   $(date '+%F %T') exit=$rc" >> timing.txt
cat timing.txt; grep 'Chip area' yosys.log | tail -1; grep -E "^Time spent|CPU: user" yosys.log | tail -2
