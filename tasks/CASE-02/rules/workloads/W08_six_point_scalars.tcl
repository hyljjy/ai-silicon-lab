# W08: worst slack and TNS of the six scenes, max and min (14 lines: two command echoes + 12)
foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { puts "WS $c max=[worst_slack -scene $c -max] min=[worst_slack -scene $c -min]" }
foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { puts "TNS $c max=[total_negative_slack -scene $c -max] min=[total_negative_slack -scene $c -min]" }
