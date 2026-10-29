# acceptance (iv): a legal query that exceeds the per-instance cap: one full report_checks per input port (single scene)
foreach p [all_inputs -no_clocks] { puts "=== [get_full_name $p]"; flush stdout; report_checks -path_delay max -from $p -scene ss_n40C_1v60 -unconstrained }
