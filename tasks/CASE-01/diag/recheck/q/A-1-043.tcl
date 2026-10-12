# 对照：_11512_ 的 B1->Y 弧，先看原样的延迟，再把 B1 端的 slew 指定为 0.1 ns，看延迟变成多少（用于 A-1-043）
report_dcalc -from [get_pins _11512_/B1] -to [get_pins _11512_/Y] -scene ss_n40C_1v60 -max -digits 4
set_assigned_transition -scene ss_n40C_1v60 -max 0.1 [get_pins _11512_/B1]
report_dcalc -from [get_pins _11512_/B1] -to [get_pins _11512_/Y] -scene ss_n40C_1v60 -max -digits 4
