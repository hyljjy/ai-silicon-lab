#!/bin/bash -l
cd "$(dirname "$0")"
mkdir -p out/syn
s=$(date +%s)
( cd out/syn && env -u SYNTH_LIB TOP=dot4sat RTL="$OLDPWD/rtl/dot4sat.v" OUT=net.v yosys -q -c $SKY130_KIT/synth.tcl -l yosys.log > /dev/null 2>&1 ); echo "yosys exit=$? ($(( $(date +%s)-s ))s)"
grep -E "Chip area|Number of cells|cells$" out/syn/yosys.log | tail -3
echo "yosys warnings: $(grep -ci 'warning' out/syn/yosys.log)"; grep -i -m5 'warning' out/syn/yosys.log
s=$(date +%s)
E1=$(python3 -c "import json;print(json.load(open('out/v1/manifest.json'))['expected_checked'])")
iverilog -g2012 -DFUNCTIONAL -DUNIT_DELAY=#1 -o out/gl.vvp tb/tb_dot4sat.v out/syn/net.v $SKY130_HD/verilog/primitives.v $SKY130_HD/verilog/sky130_fd_sc_hd.v > out/gl.compile 2>&1; echo "gl compile exit=$? ($(( $(date +%s)-s ))s) lines=$(wc -l < out/gl.compile)"
s=$(date +%s)
vvp -n out/gl.vvp +VEC=out/v1/vectors.txt +L=1 +LMAX=3 +EXP=$E1 > out/gl.log 2>&1; echo "gl sim exit=$? ($(( $(date +%s)-s ))s) $(grep -m1 '^SIM' out/gl.log)"
grep -c "sky130_fd_sc_hd__df" out/syn/net.v; grep -o "sky130_fd_sc_hd__df[a-z0-9_]*" out/syn/net.v | sort | uniq -c
