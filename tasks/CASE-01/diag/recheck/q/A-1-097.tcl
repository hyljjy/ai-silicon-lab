# 对照：把 in_b[2] -> _12026_/D 这条路径上的每个组合单元换成同功能的 _4 尺寸（没有 _4 就用 _2），终点寄存器不换；
# 看这条路径在 ss_n40C 下的 slack（用于 A-1-097、B-1-075）
# 2026-10-12 修正（介入日志）：第一版从路径对象的 points 属性取单元，get_property 不接受这种对象而报错；
# 改为直接列出路径上的 37 个组合单元，清单取自材料 path_report.rpt 第 13–86 行。判定条件不变。
set insts {_10621_ _10905_ _10907_ _11029_ _11087_ _11113_ _11186_ _11255_ _11257_ _11302_ _11306_ _11338_ _11340_
  _11416_ _11418_ _11420_ _11421_ _11422_ _11423_ _11424_ _11426_ _11427_ _11428_ _11429_ _11430_ _11431_ _11433_
  _11434_ _11438_ _11440_ _11443_ _11446_ _11451_ _11453_ _11507_ _11509_ _11512_}
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
