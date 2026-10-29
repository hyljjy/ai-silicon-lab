# acceptance (v): an STA-heavy loop with almost no Tcl commands and no output, so the safe interpreter's 600 s time limit
# is reached long before the 1000000-command limit (first attempt used report_units every 100000 iterations and hit the
# command limit after 14 s)
while {1} { llength [find_timing_paths -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -unconstrained -group_path_count 200 -endpoint_path_count 200] }
