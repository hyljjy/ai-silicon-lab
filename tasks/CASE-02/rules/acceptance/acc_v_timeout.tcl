# acceptance (v): reach the safe interpreter's 600 s time limit without touching the other limits.
# Attempt 1 (report_units every 100000 Tcl iterations) hit the 1000000-command limit after 14 s.
# Attempt 2 (an unbounded find_timing_paths over all inputs with -group_path_count 200 in a loop) grew without bound and
# the whole process tree died before the limit (no result written).
# This version repeats one cheap, bounded report: at most ~5 Tcl commands and 3 output lines per iteration, so the
# command limit (1000000) allows ~200000 iterations and the output stays under 10 MB; the time limit is reached first.
while {1} { report_checks -path_delay max -from [all_inputs -no_clocks] -to [all_registers -data_pins] -scene ss_n40C_1v60 -unconstrained -group_path_count 1 -format summary }
