# does a natural "all six scenes" per-port enumeration fit the stage-A limits (safe interpreter 300 s, 200 lines)?
# (a) report_arrival loop over six scenes: 780 lines expected
foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { foreach p [all_inputs -no_clocks] { puts -nonewline "$c [get_full_name $p] "; flush stdout; report_arrival -scene $c $p } }
# (b) find_timing_paths loop over six scenes: 3120 calls
foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { foreach p [all_inputs -no_clocks] { puts "$c [get_full_name $p] max_c=[llength [find_timing_paths -from $p -path_delay max -scenes $c]] max_u=[llength [find_timing_paths -from $p -path_delay max -scenes $c -unconstrained]] min_c=[llength [find_timing_paths -from $p -path_delay min -scenes $c]] min_u=[llength [find_timing_paths -from $p -path_delay min -scenes $c -unconstrained]]" } }
puts "REACHED END"
