report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
  -scene ss_n40C_1v60 -group_path_count 200 -endpoint_path_count 1 -slack_max 0 -format end -digits 4
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
  -scene ss_100C_1v60 -group_path_count 200 -endpoint_path_count 1 -slack_max 0 -format end -digits 4
set ps [find_timing_paths -scenes ss_n40C_1v60 -path_delay max -group_path_count 1000 -endpoint_path_count 1 -slack_max 0]
puts [llength $ps]
report_tns -digits 4   ;# 无场景选项，结果对应全部场景（不确定是取最差还是汇总）
