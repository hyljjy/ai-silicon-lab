foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  set pes [find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay max -scenes $c -unconstrained]
  puts "FTP $c n=[llength $pes]"
  foreach pe $pes { puts "  [get_full_name [get_property $pe startpoint]] -> [get_full_name [get_property $pe endpoint]] slack=[get_property $pe slack]" }
}
