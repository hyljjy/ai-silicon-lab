# 5.3 layers 1 and 3: object match and structural connectivity (operator evidence).
foreach p [get_ports {in_b[*]}] { puts "OBJ [get_full_name $p] [get_property $p direction]" }
puts "N in_b=[llength [get_ports {in_b[*]}]]"
set regs_d [all_registers -data_pins]
set starts [get_fanin -to $regs_d -startpoints_only -flat -trace_arcs all]
puts "N fanin startpoints=[llength $starts]"
set names {}
foreach s $starts { lappend names [get_full_name $s] }
foreach p [get_ports {in_b[*]}] { set n [get_full_name $p]; puts "FANIN $n in_startpoints=[expr {[lsearch -exact $names $n] >= 0}] fanout_endpoints=[llength [get_fanout -from $p -endpoints_only -flat -trace_arcs all]]" }
foreach e [get_fanout -from [get_ports {in_b[0]}] -endpoints_only -flat -trace_arcs all] { puts "FANOUT in_b\[0\] -> [get_full_name $e]" }
