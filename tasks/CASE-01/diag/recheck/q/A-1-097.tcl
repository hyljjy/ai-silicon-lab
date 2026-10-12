# 对照：把 in_b[2] -> _12026_/D 这条路径上的每个组合单元换成同功能的 _4 尺寸（没有 _4 就用 _2），终点寄存器不换；
# 看这条路径在 ss_n40C 下的 slack（用于 A-1-097、B-1-075）
set pe [lindex [find_timing_paths -from [get_ports {in_b[2]}] -to [get_pins _12026_/D] -path_delay max -scenes ss_n40C_1v60] 0]
set insts {}
foreach pt [get_property $pe points] {
  set c [get_cells -quiet -of_objects [get_property $pt pin]]
  if {$c ne "" && ![string match *dfxtp* [get_property $c ref_name]]} { lappend insts [get_full_name $c] }
}
set insts [lsort -unique $insts]
set done 0
foreach i $insts {
  set ref [get_property [get_cells $i] ref_name]
  if {![regexp {^(.*)_([0-9]+)$} $ref -> base size]} { puts "skip $i $ref"; continue }
  set to ""
  foreach z {4 2} {
    if {$z > $size && [llength [get_lib_cells -quiet ${base}_$z]] > 0} { set to ${base}_$z; break }
  }
  if {$to eq ""} { puts "keep $i $ref"; continue }
  replace_cell $i $to
  incr done
  puts "upsize $i $ref -> $to"
}
puts "upsized $done of [llength $insts] cells"
report_checks -from [get_ports {in_b[2]}] -to [get_pins _12026_/D] -path_delay max -scenes ss_n40C_1v60 -format end -digits 4
