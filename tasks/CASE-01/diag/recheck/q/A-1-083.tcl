# 对照：把 _11509_（o21ai_0）换成 o21ai_4，看这条路径和 ss_n40C 下全设计最差 in2reg 的 slack
# （用于 A-1-083、A-1-093、A-1-096、C-1-030）
replace_cell _11509_ sky130_fd_sc_hd__o21ai_4
report_checks -from [get_ports {in_b[2]}] -through [get_pins _11509_/Y] -to [get_pins _12026_/D] -path_delay max -scenes ss_n40C_1v60 -fields {slew cap fanout} -digits 4
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -format end -digits 4
