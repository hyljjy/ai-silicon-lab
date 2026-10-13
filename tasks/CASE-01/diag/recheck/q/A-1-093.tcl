# _11509_/Y 的负载，以及每个负载的输出最终到达的寄存器和输出端口；ss_n40C 下最差 50 个 in2reg 终点中，
# 最差路径经过 _11509_/Y 的有几个（用于 A-1-093、B-1-069、A-1-104、B-1-083、C-1-039、B-1-081）
# 2026-10-12 修正（介入日志）：report_net 要线网名，第一版传了对象；第二次 find_timing_paths 会让第一次返回的路径对象
# 失效，第一版之后再读它们导致段错误。改为传线网名，并在第二次查询之前先把最差 50 个终点的名字和 slack 存下来。判定条件不变。
report_instance _11509_
set net [get_nets -of_objects [get_pins _11509_/Y]]
report_net -digits 4 [get_full_name $net]
set loads {}
foreach p [get_pins -of_objects $net] {
  if {[get_property $p direction] eq "input"} { lappend loads $p }
}
puts "load pins: [llength $loads]"
foreach p $loads {
  set c [get_cells -of_objects $p]
  set outs {}
  foreach q [get_pins -of_objects $c] {
    if {[get_property $q direction] eq "output"} { lappend outs $q }
  }
  set regs {}
  foreach q $outs {
    foreach e [get_fanout -from $q -endpoints_only -flat] { lappend regs [get_full_name $e] }
  }
  set ports {}
  foreach r [lsort -unique $regs] {
    set rc [get_cells -quiet -of_objects [get_pins -quiet $r]]
    if {$rc eq ""} { continue }
    foreach o [get_fanout -from [get_pins [get_full_name $rc]/Q] -endpoints_only -flat] { lappend ports [get_full_name $o] }
  }
  puts "load [get_full_name $p] ([get_property $c ref_name]) -> endpoints [llength [lsort -unique $regs]]: [lsort -unique $regs] -> ports [lsort -unique $ports]"
}
set worst {}
foreach pe [find_timing_paths -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
             -scenes ss_n40C_1v60 -group_path_count 50 -endpoint_path_count 1] {
  lappend worst [list [get_full_name [get_property $pe endpoint]] [get_property $pe slack]]
}
foreach pe [find_timing_paths -from [all_inputs -no_clocks] -through [get_pins _11509_/Y] -to [all_registers -data_pins] \
            -path_delay max -scenes ss_n40C_1v60 -group_path_count 1000 -endpoint_path_count 1] {
  set t([get_full_name [get_property $pe endpoint]]) [get_property $pe slack]
}
set n 0
foreach es $worst {
  lassign $es e s
  set ts [expr {[info exists t($e)] ? $t($e) : "none"}]
  set via [expr {$ts ne "none" && abs($ts - $s) < 1e-6}]
  incr n $via
  puts "top50 endpoint $e worst [format %.6f $s] through_11509 [expr {$ts eq "none" ? "none" : [format %.6f $ts]}] worst_path_through_11509 $via"
}
puts "top50 endpoints whose worst path goes through _11509_/Y: $n of [llength $worst]"
