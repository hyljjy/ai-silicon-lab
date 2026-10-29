# acceptance (ii): W02 without flush inside the loop; the executor's own flush must keep port name and arrival on one line
foreach p [all_inputs -no_clocks] { puts -nonewline "[get_full_name $p] "; report_arrival -scene ss_n40C_1v60 $p }
