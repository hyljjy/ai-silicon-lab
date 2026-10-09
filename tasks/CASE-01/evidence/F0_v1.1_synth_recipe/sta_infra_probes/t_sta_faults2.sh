#!/bin/bash -l
cd "$(dirname "$0")"
NET=$PWD/exp/E4_n16_dc2/net.v
mk() { local d=$PWD/out/fi_$1; rm -rf $d; mkdir -p $d/sdc $d/out; cp sdc/case01_sdc.tcl $d/sdc/; echo $d; }
run() { local name=$1 cd=$2 script=$3 tchk=$4
  TOP=dot4sat NETLIST=$NET T_NS=20.0 CLOAD_PF=0.0024 SCENESET=std OUTDIR=$cd/out CASE_DIR=$cd \
    sta -no_init -no_splash -exit $script > $cd/out/sta.log 2>&1; local src=$?
  python3 scripts/check_sta.py $cd/out $tchk 0.0024 std > $cd/out/check.log 2>&1; local crc=$?
  echo "== $name: sta=$src check=$crc"; grep -m3 -E "INVALID|VALID" $cd/out/check.log | cut -c1-110; }
c=$(mk normal); run normal $c scripts/sta_run.tcl 20.0
c=$(mk load_before)
python3 - scripts/sta_run.tcl $c/sta_before.tcl <<'PY'
import sys
s = open(sys.argv[1]).read()
src = "source [file join $::env(CASE_DIR) sdc case01_sdc.tcl]\n"
s = s.replace("sky130_define_scenes\n", "", 1).replace(src, src + "sky130_define_scenes\n", 1)
s = s.replace("set T $::env(T_NS)\nset C_load $::env(CLOAD_PF)\n" + src + "sky130_define_scenes\n",
              "set T $::env(T_NS)\nset C_load $::env(CLOAD_PF)\n" + src + "sky130_define_scenes\n")
# move SDC before scenes: put scenes after the SDC source line (TOOL-012 situation)
open(sys.argv[2], "w").write(s)
PY
grep -n "define_scenes\|case01_sdc.tcl\]" $c/sta_before.tcl
run load_before $c $c/sta_before.tcl 20.0
c=$(mk drop_in_delay); echo 'set_input_delay -clock clk -max 0 [get_ports {in_b[3]}]' > /dev/null
python3 - $c/sdc/case01_sdc.tcl <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
s = s.replace("set ins  [get_ports {in_a[*] in_b[*] in_valid rst}]", "set ins  [get_ports {in_a[*] in_b[0] in_b[1] in_b[2] in_b[4] in_b[5] in_b[6] in_b[7] in_b[8] in_b[9] in_b[1?] in_b[2?] in_b[3?] in_b[4?] in_b[5?] in_b[6?] in_valid rst}]")
open(p, "w").write(s)
PY
run drop_in_delay_in_b3 $c scripts/sta_run.tcl 20.0
