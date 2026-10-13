# report_checks -format summary 输出哪些内容（用于 A-2-032）
report_checks -from [get_ports {in_b[2]}] -to [get_pins _12026_/D] -path_delay max -scenes ss_n40C_1v60 -format summary -digits 4
