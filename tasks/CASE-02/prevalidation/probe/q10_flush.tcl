# output ordering: puts (Tcl channel buffer in the safe interpreter) versus report_* (written by the C++ side).
# q9 showed the two streams interleave out of order inside one loop. Does an explicit flush fix it?
foreach p [get_ports {in_a[0] in_b[0] in_b[63] rst}] { puts -nonewline "[get_full_name $p] "; flush stdout; report_arrival -scene ss_n40C_1v60 $p }
foreach p [all_inputs -no_clocks] { puts -nonewline "[get_full_name $p] "; flush stdout; report_arrival -scene ss_n40C_1v60 $p }
