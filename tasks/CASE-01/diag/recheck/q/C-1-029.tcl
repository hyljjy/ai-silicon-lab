# 控制输入 rst、in_valid 出发的 in2reg 最差 setup 路径（ss_n40C），与数据路径的最差值比较（用于 C-1-029）
report_checks -from [get_ports {rst in_valid}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -format end -digits 6
