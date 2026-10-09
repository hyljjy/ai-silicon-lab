# CASE-01 STA (spec 4.3-4.5). Run: sta -no_init -no_splash -exit scripts/sta_run.tcl
# Env: TOP NETLIST T_NS CLOAD_PF SCENESET(std|all) OUTDIR CASE_DIR SKY130_KIT
# Order: libs -> link -> scenes -> SDC (TOOL-012). Everything scripts/check_sta.py needs goes to $OUTDIR:
#   sta_results.tsv (one record per line, tab separated), expanded.sdc, dcalc_<corner>_<min|max>.txt,
#   cat_<corner>_<category>_<min|max>.rpt, path_<max|min>_<corner>.rpt
set out $::env(OUTDIR)
set f [open [file join $out sta_results.tsv] w]
proc emit {args} { global f; puts $f [join $args "\t"]; flush $f }

source $::env(SKY130_KIT)/corners.tcl
# record every define_scene call actually made (spec 4.5: scene binding)
rename define_scene _case01_define_scene
proc define_scene {args} {
  emit BIND {*}$args
  uplevel 1 [list _case01_define_scene {*}$args]
}

set corners [sky130_read_libs $::env(SCENESET)]
read_verilog $::env(NETLIST)
link_design $::env(TOP)
sky130_define_scenes
set T $::env(T_NS)
set C_load $::env(CLOAD_PF)
source [file join $::env(CASE_DIR) sdc case01_sdc.tcl]

emit MODE [sta::cmd_mode_name]
emit SCENES {*}[lmap s [get_scenes *] {get_name $s}]
foreach l [get_libs *] { emit LIB [get_name $l] [get_property $l filename] }
foreach p [get_ports *] { emit PORT [get_full_name $p] [get_property $p direction] }
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

# structural evidence, independent of timing queries (spec 4.5): startpoints of the fanin cones.
# Do not use the pin property is_clock: it crashes this OpenSTA version (TOOL-014); match port names instead.
set in_names [lmap p $ins {get_full_name $p}]
proc count_starts {sinks kind} {
  global in_names
  set n 0
  foreach p [get_fanin -to $sinks -startpoints_only -flat -trace_arcs all] {
    if {$kind eq "port" && [get_property $p is_port] && [lsearch -exact $in_names [get_full_name $p]] >= 0} {
      incr n
    }
    if {$kind eq "regck" && [get_property $p is_register_clock]} { incr n }
  }
  return $n
}
emit TOPO in2reg  [count_starts $regs_d port]
emit TOPO reg2reg [count_starts $regs_d regck]
emit TOPO reg2out [count_starts [all_outputs] regck]

foreach c $corners {
  foreach mm {min max} {
    report_dcalc -from [get_pins $reg0/CLK] -to [get_pins $reg0/Q] -scene $c -$mm > [file join $out dcalc_${c}_$mm.txt]
  }
  emit WS $c max [worst_slack -scene $c -max]
  emit WS $c min [worst_slack -scene $c -min]
  foreach {cat from to} [list in2reg $ins $regs_d reg2reg $regs_ck $regs_d reg2out $regs_ck [all_outputs]] {
    foreach mm {max min} {
      set pes [find_timing_paths -from $from -to $to -path_delay $mm -scenes $c -group_path_count 1]
      if {[llength $pes]} {
        set pe [lindex $pes 0]
        emit CAT $c $cat $mm [get_property $pe slack] \
          [get_full_name [get_property $pe startpoint]] [get_full_name [get_property $pe endpoint]]
        report_checks -from $from -to $to -path_delay $mm -scene $c -fields {slew cap input_pins fanout} \
          -digits 4 > [file join $out cat_${c}_${cat}_$mm.rpt]
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
