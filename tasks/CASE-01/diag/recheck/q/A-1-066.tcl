# _12026_ 的连接：Q 端最终到达哪些端点（用于 A-1-066、B-1-052、C-1-017、A-1-103、B-1-057、C-1-029、B-1-080）
report_instance _12026_
foreach p [get_fanout -from [get_pins _12026_/Q] -endpoints_only -flat] { puts "Q fanout endpoint: [get_full_name $p]" }
