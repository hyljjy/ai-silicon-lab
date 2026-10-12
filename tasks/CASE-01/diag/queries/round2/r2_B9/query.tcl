report_checks \
  -from [get_pins {_12026_/CLK}] \
  -to [get_ports {out_data[0]}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
