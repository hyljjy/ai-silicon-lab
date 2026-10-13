# 对照：把 _11509_（o21ai_0）换成 o21ai_4 后，ss_n40C 下全设计最差 in2reg 路径的完整报告（6 位小数，带 slew、电容、
# 输入引脚、扇出），以及最差的 5 个终点（用于 A-2-034、A-2-035、A-2-036、A-2-037）
replace_cell _11509_ sky130_fd_sc_hd__o21ai_4
report_instance _11509_
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 6
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -group_path_count 5 -endpoint_path_count 1 -format end -digits 6
