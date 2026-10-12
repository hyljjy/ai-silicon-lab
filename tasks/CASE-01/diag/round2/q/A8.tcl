report_lib_cell sky130_fd_sc_hd__dfxtp_1   ;# 是否支持此命令不确定
set a 0
foreach c [get_cells *] { set a [expr {$a + [get_property [get_property $c liberty_cell] area]}] }
puts $a
