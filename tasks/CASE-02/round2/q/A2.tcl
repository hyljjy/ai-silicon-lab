foreach p [all_inputs -no_clocks] { puts "== [get_full_name $p]"; report_arrival -scene ss_n40C_1v60 $p }
