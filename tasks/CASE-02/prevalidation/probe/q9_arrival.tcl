# 5.5 per-port evidence through report_arrival / report_required / report_slack with -scene (multi-scene needs it),
# and the complete 130-port enumeration of arrivals on one scene.
report_arrival -scene ss_n40C_1v60 [get_ports {in_a[0]}]
report_arrival -scene ss_n40C_1v60 [get_ports {in_b[0]}]
report_arrival -scene ss_n40C_1v60 -min_max max [get_ports {in_b[0]}]
report_required -scene ss_n40C_1v60 [get_ports {in_a[0]}]
report_required -scene ss_n40C_1v60 [get_ports {in_b[0]}]
report_slack -scene ss_n40C_1v60 [get_ports {in_a[0]}]
report_slack -scene ss_n40C_1v60 [get_ports {in_b[0]}]
report_arrival -scene ss_n40C_1v60 [get_pins {_12026_/D}]
report_arrival -scene ss_n40C_1v60 [get_ports {in_a[0] in_b[0]}]
foreach p [all_inputs -no_clocks] { puts -nonewline "[get_full_name $p] "; report_arrival -scene ss_n40C_1v60 $p }
foreach p [get_ports {in_b[*]}] { puts -nonewline "[get_full_name $p] slack_max=[get_property $p slack_max] slack_min=[get_property $p slack_min] " ; report_arrival -scene ss_n40C_1v60 $p }
