# acceptance (v): a loop that cannot finish within the safe-interpreter time limit; one STA call every 100000 iterations keeps the command counter far below 1000000 per call
set i 0
while {1} { incr i; if {$i % 100000 == 0} { report_units } }
