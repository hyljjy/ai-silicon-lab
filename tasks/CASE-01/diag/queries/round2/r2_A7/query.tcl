set_input_delay -clock clk -max 0 [get_ports {in_a[*] in_b[*] in_valid rst}]
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
set_input_delay -clock clk -max [expr {0.2*27.91}] [get_ports {in_a[*] in_b[*] in_valid rst}]
