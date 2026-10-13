# 对照：输入端口改为理想驱动（驱动电阻 0），看这条路径和 ss_n40C 下全设计最差 in2reg 的 slack（用于 A-1-099）
set_drive 0 [all_inputs -no_clocks]
report_checks -from [get_ports {in_b[2]}] -to [get_pins _12026_/D] -path_delay max -scenes ss_n40C_1v60 -digits 4
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -format end -digits 4
