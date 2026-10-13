# _11509_/Y、_11510_/Y、_11302_/X 的扇出终点；_11510_ 的连接和输出线网的负载；ss_n40C 下全部 in2reg 违例终点中，
# 最差路径经过 _11509_/Y、_11302_/X 的各有几个（用于 A-2-028、A-2-037、A-2-065、A-2-069、A-2-070、B-2-069）
foreach drv {_11509_/Y _11510_/Y _11302_/X} {
  set eps {}
  foreach e [get_fanout -from [get_pins $drv] -endpoints_only -flat] { lappend eps [get_full_name $e] }
  set eps [lsort -dictionary -unique $eps]
  puts "fanout endpoints of $drv: [llength $eps]: $eps"
}
report_instance _11510_
foreach pin {_11510_/Y} {
  set net [get_full_name [get_nets -of_objects [get_pins $pin]]]
  report_net -digits 4 $net
  set loads {}
  foreach p [get_pins -of_objects [get_nets $net]] {
    if {[get_property $p direction] eq "input"} { lappend loads [get_full_name $p] }
  }
  puts "load pins of $pin (net $net): [llength $loads]: [lsort -dictionary $loads]"
}
set viol {}
foreach pe [find_timing_paths -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
             -scenes ss_n40C_1v60 -group_path_count 1000 -endpoint_path_count 1 -slack_max 0] {
  lappend viol [list [get_full_name [get_property $pe endpoint]] [get_property $pe slack]]
}
foreach drv {_11509_/Y _11302_/X} {
  array unset t
  foreach pe [find_timing_paths -from [all_inputs -no_clocks] -through [get_pins $drv] -to [all_registers -data_pins] \
               -path_delay max -scenes ss_n40C_1v60 -group_path_count 1000 -endpoint_path_count 1] {
    set t([get_full_name [get_property $pe endpoint]]) [get_property $pe slack]
  }
  set n 0
  set off {}
  foreach es $viol {
    lassign $es e s
    if {[info exists t($e)] && abs($t($e) - $s) < 1e-6} { incr n } else { lappend off $e }
  }
  puts "ss_n40C violating endpoints: [llength $viol]; worst path through $drv: $n; not through: [lsort -dictionary $off]"
}
