set starts [get_fanin -to [all_registers -data_pins] -startpoints_only -flat -trace_arcs all]
set names {}
foreach s $starts { lappend names [get_full_name $s] }
foreach p [all_inputs -no_clocks] { set n [get_full_name $p]; if {[lsearch -exact $names $n] >= 0} { puts "FANIN $n" } }
foreach p [all_inputs -no_clocks] { puts "FANOUT [get_full_name $p] [llength [get_fanout -from $p -endpoints_only -flat -trace_arcs all]]" }
