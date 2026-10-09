# CASE-01 STA (spec 4.3-4.5). Run: sta -no_init -no_splash -exit scripts/sta_run.tcl
# Env: TOP NETLIST T_NS CLOAD_PF SCENESET(std|all) OUTDIR CASE_DIR SKY130_KIT
# Order: libs -> link -> scenes -> SDC (TOOL-012). Results go to $OUTDIR/sta_results.tsv; scripts/check_sta.py
# decides whether the analysis is valid.
source $::env(SKY130_KIT)/corners.tcl
set out $::env(OUTDIR)
set corners [sky130_read_libs $::env(SCENESET)]
read_verilog $::env(NETLIST)
link_design $::env(TOP)
sky130_define_scenes
set T $::env(T_NS)
set C_load $::env(CLOAD_PF)
source [file join $::env(CASE_DIR) sdc case01_sdc.tcl]

set f [open [file join $out sta_results.tsv] w]
proc emit {args} { global f; puts $f [join $args "\t"] }

emit MODE [sta::cmd_mode_name]
emit SCENES {*}[lmap s [get_scenes *] {get_name $s}]
emit CHECK_SETUP [check_setup -verbose]
foreach p [all_outputs] {
  emit LOAD [get_full_name $p] [sta::port_ext_pin_cap $p max] [sta::port_ext_pin_cap $p min]
}
write_sdc -no_timestamp [file join $out expanded.sdc]

set ins     [all_inputs -no_clocks]
set regs_d  [all_registers -data_pins]
set regs_ck [all_registers -clock_pins]
set reg0    [get_full_name [lindex [all_registers -cells] 0]]
emit OBJECTS [llength $ins] [llength [all_outputs]] [llength $regs_d] [llength $regs_ck]

foreach c $corners {
  # scene binding (spec 4.5): PVT actually used by this scene's delay calculation
  report_dcalc -from [get_pins $reg0/CLK] -to [get_pins $reg0/Q] -scene $c > [file join $out dcalc_$c.txt]
  emit WS $c max [worst_slack -scene $c -max]
  emit WS $c min [worst_slack -scene $c -min]
  foreach {cat from to} [list in2reg $ins $regs_d reg2reg $regs_ck $regs_d reg2out $regs_ck [all_outputs]] {
    foreach mm {max min} {
      set pes [find_timing_paths -from $from -to $to -path_delay $mm -scenes $c -group_path_count 1]
      if {[llength $pes]} {
        set pe [lindex $pes 0]
        emit CAT $c $cat $mm [get_property $pe slack] \
          [get_full_name [get_property $pe startpoint]] [get_full_name [get_property $pe endpoint]]
      } elseif {[llength [find_timing_paths -from $from -to $to -path_delay $mm -scenes $c \
                            -group_path_count 1 -unconstrained]]} {
        emit CAT $c $cat $mm UNCONSTRAINED
      } else {
        emit CAT $c $cat $mm NONE
      }
    }
  }
  report_checks -path_delay max -scene $c -fields {slew cap input_pins fanout} -digits 4 \
    > [file join $out path_max_$c.rpt]
  report_checks -path_delay min -scene $c -fields {slew cap input_pins fanout} -digits 4 \
    > [file join $out path_min_$c.rpt]
}
emit DONE
close $f
