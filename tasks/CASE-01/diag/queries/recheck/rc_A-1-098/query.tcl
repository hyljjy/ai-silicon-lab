# 同一条路径（-from in_b[2] -through _11509_/Y -to _12026_/D）在 6 个场景下的 arrival、required、slack，
# 以及各场景 in2reg setup 违例终点的个数（用于 A-1-098、B-1-072）
foreach s {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  puts "=== scene $s"
  report_checks -from [get_ports {in_b[2]}] -through [get_pins _11509_/Y] -to [get_pins _12026_/D] -path_delay max -scenes $s -format end -digits 6
  set v [find_timing_paths -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scenes $s -group_path_count 1000 -endpoint_path_count 1 -slack_max 0]
  puts "scene $s violating in2reg endpoints: [llength $v]"
}
