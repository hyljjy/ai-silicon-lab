# W02: per-port arrival times of every non-clock input in one scene (131 lines)
foreach p [all_inputs -no_clocks] { puts -nonewline "[get_full_name $p] "; flush stdout; report_arrival -scene ss_n40C_1v60 $p }
