# 对照：把全部输入的 max 输入延迟设为 0（约束不变，只作对照），看这条路径和 ss_n40C 下全设计最差 in2reg 的 slack
# （用于 A-1-102、B-1-064、B-1-067、C-1-025、C-1-028）
set_input_delay -clock clk -max 0 [all_inputs -no_clocks]
report_checks -from [get_ports {in_b[2]}] -to [get_pins _12026_/D] -path_delay max -scenes ss_n40C_1v60 -digits 6
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -format end -digits 4
