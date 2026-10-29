foreach p [get_ports {in_b[*]}] { puts "PORT [get_full_name $p] [get_property $p direction]" }
