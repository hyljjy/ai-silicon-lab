# W04: W01 and W02 in one instance (198 lines)
check_setup -verbose
foreach p [all_inputs -no_clocks] { puts -nonewline "[get_full_name $p] "; flush stdout; report_arrival -scene ss_n40C_1v60 $p }
