# which scene does report_checks pick when -scene is omitted? (full format prints the Corner: line)
report_checks -path_delay max -from [get_ports {in_a[34]}]
report_checks -path_delay max -from [get_ports {in_b[2]}] -unconstrained
report_checks -path_delay max -from [get_ports {in_a[34]}] -scene tt_025C_1v80 -format summary
