# 基线面积（按 Liberty 单元面积求和）、单元数、寄存器个数和面积，以及几种寄存器、缓冲单元的库面积
# （用于 A-1-108、B-1-085、C-1-038、C-1-039）
set n 0
set area 0.0
set ffn 0
set ffa 0.0
foreach c [get_cells *] {
  set a [get_property [get_property $c liberty_cell] area]
  incr n
  set area [expr {$area + $a}]
  if {[string match *dfxtp* [get_property $c ref_name]]} { incr ffn; set ffa [expr {$ffa + $a}] }
}
puts "cells $n total_area [format %.3f $area] registers $ffn register_area [format %.3f $ffa]"
foreach lc {dfxtp_1 dfxtp_2 dfxtp_4 buf_1 buf_2 buf_4 buf_8 buf_16 o21ai_0 o21ai_4} {
  puts "lib cell sky130_fd_sc_hd__$lc area [get_property [lindex [get_lib_cells sky130_fd_sc_hd__$lc] 0] area]"
}
