# ss_n40C 和 ss_100C 下 in2reg setup 违例终点的个数、TNS（违例终点最差 slack 之和）和逐个终点的 slack
# （用于 A-1-105、B-1-081、C-1-035）
foreach s {ss_n40C_1v60 ss_100C_1v60} {
  set pes [find_timing_paths -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scenes $s -group_path_count 1000 -endpoint_path_count 1 -slack_max 0]
  set tns 0.0
  foreach pe $pes { set tns [expr {$tns + [get_property $pe slack]}] }
  puts "scene $s: violating endpoints [llength $pes], TNS [format %.4f $tns]"
  foreach pe $pes { puts "  [get_full_name [get_property $pe startpoint]] -> [get_full_name [get_property $pe endpoint]] [format %.6f [get_property $pe slack]]" }
}
