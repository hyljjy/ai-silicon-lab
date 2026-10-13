# 对照：周期改为 33.15 ns，输入、输出 max 延迟按 0.2T 改为 6.63 ns（只作对照，不证明电路变快），
# 看这条路径和 ss_n40C 下全设计最差 in2reg 的 slack（用于 A-1-088）
create_clock -name clk -period 33.15 -waveform {0 16.575} [get_ports clk]
set_input_delay -clock clk -max 6.63 [all_inputs -no_clocks]
set_output_delay -clock clk -max 6.63 [all_outputs]
report_checks -from [get_ports {in_b[2]}] -to [get_pins _12026_/D] -path_delay max -scenes ss_n40C_1v60 -digits 4
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -format end -digits 4
