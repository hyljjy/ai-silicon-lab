# acceptance (vi): more output than the 50 MiB process limit within the 1000000-command limit: 300000 lines of 400 bytes
# (first attempt wrote 100-byte lines and hit the command limit at 25 MB)
for {set i 0} {$i < 300000} {incr i} { puts [string repeat x 400] }
