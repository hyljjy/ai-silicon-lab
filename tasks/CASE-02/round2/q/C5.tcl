foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene ss_n40C_1v60 }
