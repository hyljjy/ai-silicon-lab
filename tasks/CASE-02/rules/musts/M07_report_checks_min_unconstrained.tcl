foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { puts "=== scene $c"; report_checks -path_delay min -from [get_ports {in_b[*]}] -scene $c -unconstrained }
