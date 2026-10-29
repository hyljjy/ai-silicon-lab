# 5.4 six-point worst_slack and whether TNS can be taken per scene.
foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { puts "WS $c max=[worst_slack -scene $c -max] min=[worst_slack -scene $c -min]" }
worst_slack -max
worst_slack -scene ss_n40C_1v60 -max
total_negative_slack -max
total_negative_slack -scene ss_n40C_1v60 -max
foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { puts "TNS $c max=[total_negative_slack -scene $c -max] min=[total_negative_slack -scene $c -min]" }
report_tns
report_tns -scene ss_n40C_1v60
report_tns -max
report_wns
report_wns -scene ss_n40C_1v60
report_worst_slack -max
report_worst_slack -scene ss_n40C_1v60 -max
worst_negative_slack -scene ss_n40C_1v60 -max
report_check_types -max_delay -scene ss_n40C_1v60
report_check_types -verbose -scene ss_n40C_1v60
