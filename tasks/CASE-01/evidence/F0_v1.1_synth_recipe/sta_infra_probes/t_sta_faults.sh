#!/bin/bash -l
# Fault injection for sta_run.tcl + check_sta.py (infra test, E4 netlist). Only exit codes and problems are shown.
cd "$(dirname "$0")"
NET=$PWD/exp/E4_n16_dc2/net.v
case_dir() { local d=out/fi_$1; rm -rf $d; mkdir -p $d/sdc $d/out; cp sdc/case01_sdc.tcl $d/sdc/; echo $PWD/$d; }
run() {  # name, case_dir, sta script, checker T
  local name=$1 cd=$2 script=$3 tchk=$4
  TOP=dot4sat NETLIST=$NET T_NS=20.0 CLOAD_PF=0.0024 SCENESET=std OUTDIR=$cd/out CASE_DIR=$cd \
    sta -no_init -no_splash -exit $script > $cd/out/sta.log 2>&1; local src=$?
  python3 scripts/check_sta.py $cd/out $tchk 0.0024 std > $cd/out/check.log; local crc=$?
  printf '%-22s sta=%d check=%d  %s\n' $name $src $crc "$(grep -m2 INVALID $cd/out/check.log | cut -c1-90 | tr '\n' ' ')"
}
c=$(case_dir normal);        run normal $c scripts/sta_run.tcl 20.0
c=$(case_dir load_before);   sed 's/^sky130_define_scenes$/# moved/; s#^source \[file join $::env(CASE_DIR) sdc case01_sdc.tcl\]#&\nsky130_define_scenes#' scripts/sta_run.tcl > $c/sta_before.tcl
                             sed -i 's#^set T $::env(T_NS)#&#' $c/sta_before.tcl
                             python3 - "$c/sta_before.tcl" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
# TOOL-012 situation: SDC (incl. set_load) sourced BEFORE define_scene
s = s.replace("# moved\n", "").replace("set T $::env(T_NS)\nset C_load $::env(CLOAD_PF)\nsource [file join $::env(CASE_DIR) sdc case01_sdc.tcl]\nsky130_define_scenes",
              "set T $::env(T_NS)\nset C_load $::env(CLOAD_PF)\nsource [file join $::env(CASE_DIR) sdc case01_sdc.tcl]\nsky130_define_scenes")
open(p, "w").write(s)
PY
                             grep -n "define_scenes\|case01_sdc" $c/sta_before.tcl | head -3
                             run load_before $c $c/sta_before.tcl 20.0
c=$(case_dir drop_in_delay); sed -i 's/^set ins  \[get_ports {in_a\[\*\] in_b\[\*\] in_valid rst}\]/set ins [get_ports {in_a[*] in_b[*] in_valid rst}]\nset ins_all $ins/' $c/sdc/case01_sdc.tcl
                             echo 'remove_input_delay [get_ports {in_a[5]}]' >> $c/sdc/case01_sdc.tcl; run drop_in_delay $c scripts/sta_run.tcl 20.0
c=$(case_dir false_path);    echo 'set_false_path -from [get_ports rst]' >> $c/sdc/case01_sdc.tcl; run false_path $c scripts/sta_run.tcl 20.0
c=$(case_dir wrong_T);       run checker_T_mismatch $c scripts/sta_run.tcl 21.0
