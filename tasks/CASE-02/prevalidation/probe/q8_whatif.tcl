# whatif mode: re-adding the in_b constraints inside the query (a legal comparison, protocol 6.4) and what it shows
report_checks -path_delay max -from [get_ports {in_b[2]}] -scene ss_n40C_1v60 -format summary
set_input_delay -clock clk -max 5.582 [get_ports {in_b[*]}]
set_input_delay -clock clk -min 0 [get_ports {in_b[*]}]
report_checks -path_delay max -from [get_ports {in_b[2]}] -scene ss_n40C_1v60 -format summary
report_checks -path_delay max -from [get_ports {in_b[*]}] -scene ss_n40C_1v60 -unconstrained -format summary
worst_slack -scene ss_n40C_1v60 -max
check_setup -verbose
