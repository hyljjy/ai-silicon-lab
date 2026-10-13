# 对照：全部输入端口的驱动单元从 buf_2 改为 buf_16（其余参数与 SDC 第 15–16 行相同），看这条路径和 ss_n40C 下
# 全设计最差 in2reg 的 slack（用于 A-2-068）。第 1 轮的 rc_A-1-099 用 set_drive 0，被 SDC 中的 set_driving_cell 覆盖，没有生效
puts "buf_16 lib cells: [llength [get_lib_cells -quiet */sky130_fd_sc_hd__buf_16]]"
set_driving_cell -lib_cell sky130_fd_sc_hd__buf_16 -from_pin A -pin X -input_transition_rise 0 -input_transition_fall 0 [all_inputs -no_clocks]
report_checks -from [get_ports {in_b[2]}] -to [get_pins _12026_/D] -path_delay max -scenes ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 6
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -format end -digits 6
