# acceptance (vi): more output than the 50 MiB process limit (about 200 MB)
for {set i 0} {$i < 2000000} {incr i} { puts [string repeat x 100] }
