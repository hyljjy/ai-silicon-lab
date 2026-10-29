# 5.5 per-port evidence candidates (local confirmation): one in_a port against one in_b port.
report_checks -path_delay max -from [get_ports {in_a[0]}] -scene ss_n40C_1v60
report_checks -path_delay max -from [get_ports {in_b[0]}] -scene ss_n40C_1v60
report_checks -path_delay max -from [get_ports {in_b[0]}] -scene ss_n40C_1v60 -unconstrained
report_checks -path_delay min -from [get_ports {in_b[0]}] -scene ss_n40C_1v60 -unconstrained
report_checks -path_delay min -from [get_ports {in_a[0]}] -scene ss_n40C_1v60 -format summary
report_checks -path_delay max -from [get_ports {in_b[0]}] -scene ss_n40C_1v60 -unconstrained -format full_clock_expanded
report_arrival [get_ports {in_a[0]}]
report_arrival [get_ports {in_b[0]}]
report_required [get_ports {in_a[0]}]
report_required [get_ports {in_b[0]}]
report_slack [get_ports {in_a[0]}]
report_slack [get_ports {in_b[0]}]
report_arrival -scene ss_n40C_1v60 [get_ports {in_a[0]}]
get_property [get_ports {in_a[0]}] slack_max
get_property [get_ports {in_b[0]}] slack_max
get_property [get_ports {in_a[0]}] slack_min
get_property [get_ports {in_b[0]}] slack_min
get_property [get_ports {in_a[0]}] arrival_max_rise
get_property [get_ports {in_b[0]}] arrival_max_rise
get_property [get_ports {in_a[0]}] input_delay
get_property [get_ports {in_b[0]}] clocks
get_property [get_ports {in_a[0]}] clocks
get_property [get_ports {in_a[0]}] bogus_property
get_property [get_pins {_12026_/D}] slack_max
get_clocks -of_objects [get_ports {in_a[0]}]
report_edges -from [get_ports {in_b[0]}]
report_edges -from [get_ports {in_a[0]}]
report_object_full_names [get_ports {in_b[*]}]
llength [get_ports {in_b[*]}]
get_property [get_ports {in_b[0]}] direction
report_checks -path_delay max -to [get_pins {_12026_/D}] -scene ss_n40C_1v60 -unconstrained -group_path_count 300 -endpoint_path_count 300 -format summary
