foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene tt_025C_1v80 }
