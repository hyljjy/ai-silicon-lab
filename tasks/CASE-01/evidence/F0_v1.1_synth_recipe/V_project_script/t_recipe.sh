#!/bin/bash -l
cd "$(dirname "$0")"
rm -rf out/v11; mkdir -p out/v11; s=$(date +%s)
( cd out/v11 && env -u SYNTH_LIB TOP=dot4sat RTL=$OLDPWD/rtl/dot4sat.v OUT=net.v yosys -q -c /mnt/d/study/ai_native_design/tasks/CASE-01/scripts/synth_case01.tcl -l yosys.log > /dev/null 2>&1 ); echo "yosys exit=$? ($(( $(date +%s)-s ))s) $(grep 'Chip area' out/v11/yosys.log | tail -1)"
echo "netlist identical to E4 (ignoring header line): $(cmp -s <(tail -n +2 out/v11/net.v) <(tail -n +2 exp/E4_n16_dc2/net.v) && echo yes || echo NO)"
echo "warnings: $(grep -ci 'warning' out/v11/yosys.log)"; grep -i 'warning' out/v11/yosys.log | head -3
grep -o "sky130_fd_sc_hd__df[a-z0-9_]*" out/v11/net.v | sort | uniq -c
E1=$(python3 -c "import json;print(json.load(open('out/v1/manifest.json'))['expected_checked'])")
iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 -o out/v11/gl.vvp tb/tb_dot4sat.v out/v11/net.v $SKY130_HD/verilog/primitives.v $SKY130_HD/verilog/sky130_fd_sc_hd.v > out/v11/gl.compile 2>&1; echo "gl compile exit=$? lines=$(wc -l < out/v11/gl.compile)"
vvp -n out/v11/gl.vvp +VEC=out/v1/vectors.txt +L=1 +LMAX=3 +EXP=$E1 > out/v11/gl.log 2>&1; echo "gl sim exit=$? $(grep -m1 '^SIM' out/v11/gl.log)"
sha256sum /mnt/d/study/ai_native_design/tasks/CASE-01/scripts/synth_case01.tcl
