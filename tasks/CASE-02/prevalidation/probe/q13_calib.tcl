# M1 calibration (whatif mode on the missing version, where in_b[*] start with no input delay): give six in_b ports six
# different constraint states and see what the allowed read-only queries print for each. Truth = the commands below.
# in_b[0]: explicit zero delay, no clock.   in_b[1]: max only.   in_b[2]: min only.
# in_b[3]: both, referenced to the falling edge.   in_b[4]: zero with clock, both.   in_b[5]: rise only, both min/max.
# in_b[6]: untouched (fully missing).   in_a[0]: original full constraint.
set_input_delay 0 [get_ports {in_b[0]}]
set_input_delay -clock clk -max 5.582 [get_ports {in_b[1]}]
set_input_delay -clock clk -min 0 [get_ports {in_b[2]}]
set_input_delay -clock clk -clock_fall -max 5.582 [get_ports {in_b[3]}]
set_input_delay -clock clk -clock_fall -min 0 [get_ports {in_b[3]}]
set_input_delay -clock clk 0 [get_ports {in_b[4]}]
set_input_delay -clock clk -rise -max 5.582 [get_ports {in_b[5]}]
set_input_delay -clock clk -rise -min 0 [get_ports {in_b[5]}]
foreach p [get_ports {in_a[0] in_b[0] in_b[1] in_b[2] in_b[3] in_b[4] in_b[5] in_b[6]}] { puts -nonewline "ARR [get_full_name $p] "; flush stdout; report_arrival -scene ss_n40C_1v60 $p }
foreach p [get_ports {in_a[0] in_b[0] in_b[1] in_b[2] in_b[3] in_b[4] in_b[5] in_b[6]}] { puts "FTP [get_full_name $p] max_c=[llength [find_timing_paths -from $p -path_delay max -scenes ss_n40C_1v60]] max_u=[llength [find_timing_paths -from $p -path_delay max -scenes ss_n40C_1v60 -unconstrained]] min_c=[llength [find_timing_paths -from $p -path_delay min -scenes ss_n40C_1v60]] min_u=[llength [find_timing_paths -from $p -path_delay min -scenes ss_n40C_1v60 -unconstrained]] slack_max=[get_property $p slack_max] slack_min=[get_property $p slack_min]" }
foreach p [get_ports {in_b[0] in_b[1] in_b[2] in_b[3] in_b[4] in_b[5]}] { puts "RC [get_full_name $p] max:"; report_checks -path_delay max -from $p -scene ss_n40C_1v60 -unconstrained -format summary; puts "RC [get_full_name $p] min:"; report_checks -path_delay min -from $p -scene ss_n40C_1v60 -unconstrained -format summary }
report_checks -path_delay max -from [get_ports {in_b[3]}] -scene ss_n40C_1v60 -unconstrained
report_checks -path_delay max -from [get_ports {in_b[1]}] -scene ss_n40C_1v60 -unconstrained
report_checks -path_delay min -from [get_ports {in_b[1]}] -scene ss_n40C_1v60 -unconstrained
check_setup -verbose
