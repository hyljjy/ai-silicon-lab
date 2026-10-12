# 1) ss_n40C 下输入到寄存器 setup，列出前 20 条，而不只看缺省最差一条
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4 \
  -nworst 20

# 2) 跨全部 corner 看同类最差路径
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scenes {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} \
  -fields {slew cap input_pins fanout} \
  -digits 4

# 3) 只看终点 _12026_/D 的所有输入起点，判断是否为 _12026_ 集中收敛
report_checks \
  -from [all_inputs -no_clocks] \
  -to _12026_/D \
  -path_delay max \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4 \
  -nworst 50

# 4) 已知最差路径的完整单条报告
report_checks \
  -from in_b[2] \
  -to _12026_/D \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4

# 5) 经过高扇出点 _11509_/Y 的路径，以及该网络连接/驱动信息
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -through _11509_/Y \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4 \
  -nworst 10

report_net -connections _11509_
report_driver -net _11509_

# 6) 确认 reg2reg、reg2out 与 hold 情况
report_checks \
  -from [all_registers -clock_pins] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4

report_checks \
  -from [all_registers -clock_pins] \
  -to [all_outputs] \
  -path_delay max \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4 \
  -nworst 10

report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay min \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4 \
  -nworst 10

# 7) 仅作对照：临时把输入 max 延迟清 0，验证 H2；之后必须恢复原始 SDC
set_input_delay -clock clk -max 0 [get_ports {in_a[*] in_b[*] in_valid rst}]
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4

# 然后恢复原始约束：重新 source case01_sdc.tcl（保持 T、C_load 等不变）
