# 5.4 report_checks / find_timing_paths candidates on scene ss_n40C_1v60, and the -unconstrained semantics.
report_checks -path_delay max -from [get_ports {in_b[*]}] -scene ss_n40C_1v60
report_checks -path_delay max -from [get_ports {in_b[*]}] -scene ss_n40C_1v60 -unconstrained
report_checks -path_delay min -from [get_ports {in_b[*]}] -scene ss_n40C_1v60
report_checks -path_delay min -from [get_ports {in_b[*]}] -scene ss_n40C_1v60 -unconstrained
find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -unconstrained
puts "COUNT in_b max plain=[llength [find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60]] unconstrained=[llength [find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -unconstrained]]"
puts "COUNT in_b min plain=[llength [find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay min -scenes ss_n40C_1v60]] unconstrained=[llength [find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay min -scenes ss_n40C_1v60 -unconstrained]]"
puts "COUNT in_a max plain=[llength [find_timing_paths -from [get_ports {in_a[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60]] unconstrained=[llength [find_timing_paths -from [get_ports {in_a[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -unconstrained]]"
foreach pe [find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -unconstrained] { puts "PE [get_full_name [get_property $pe startpoint]] -> [get_full_name [get_property $pe endpoint]] slack=[get_property $pe slack]" }
foreach pe [find_timing_paths -from [get_ports {in_a[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -unconstrained] { puts "PE in_a [get_full_name [get_property $pe startpoint]] -> [get_full_name [get_property $pe endpoint]] slack=[get_property $pe slack]" }
# semantics: -unconstrained with a constrained -from set, with no -from, and with a mixed set
report_checks -path_delay max -from [get_ports {in_a[*]}] -scene ss_n40C_1v60 -unconstrained -format summary
report_checks -path_delay max -scene ss_n40C_1v60 -unconstrained -format summary
report_checks -path_delay max -from [get_ports {in_a[34] in_b[2]}] -scene ss_n40C_1v60 -unconstrained -format summary
report_checks -path_delay max -from [get_ports {in_a[34] in_b[2]}] -scene ss_n40C_1v60 -unconstrained -group_path_count 4 -format summary
report_checks -path_delay max -from [get_ports {in_b[*]}] -scene ss_n40C_1v60 -unconstrained -group_path_count 200 -endpoint_path_count 200 -format summary
report_checks -path_delay max -from [get_ports {in_b[*]}] -scene ss_n40C_1v60 -unconstrained -group_path_count 200 -endpoint_path_count 200 -unique_paths_to_endpoint -format summary
# option spelling: -scenes on report_checks, -scene on find_timing_paths, no scene option, -corner
report_checks -path_delay max -from [get_ports {in_b[2]}] -scenes ss_n40C_1v60 -unconstrained -format summary
find_timing_paths -from [get_ports {in_b[2]}] -path_delay max -scene ss_n40C_1v60 -unconstrained
report_checks -path_delay max -from [get_ports {in_b[2]}] -unconstrained -format summary
report_checks -path_delay max -from [get_ports {in_b[2]}] -corner ss_n40C_1v60 -unconstrained -format summary
