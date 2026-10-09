#!/bin/bash -l
# Re-verify synth_case01.tcl after the header/SYNTH_LIB edit: netlist must be byte-identical to E4/V.
cd "$(dirname "$0")"
O=out/v12_$(date +%Y%m%d%H%M%S); mkdir -p $O
S=/mnt/d/study/ai_native_design/tasks/CASE-01/scripts/synth_case01.tcl
( cd $O && env -u SYNTH_LIB TOP=dot4sat RTL=$OLDPWD/rtl/dot4sat.v OUT=net.v yosys -q -c $S -l yosys.log > /dev/null 2>&1 ); echo "yosys exit=$? $(grep 'Chip area' $O/yosys.log | tail -1)"
sha256sum $O/net.v exp/E4_n16_dc2/net.v out/v11/net.v rtl/dot4sat.v $S | sed "s#$PWD/##"
( cd $O && SYNTH_LIB=/tmp/x TOP=dot4sat RTL=$OLDPWD/rtl/dot4sat.v OUT=net2.v yosys -q -c $S -l yosys2.log > /dev/null 2>&1 ); echo "with SYNTH_LIB set: exit=$? $(grep -m1 'SYNTH_LIB' $O/yosys2.log)"
