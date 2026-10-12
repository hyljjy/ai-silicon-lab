set ins [get_ports {in_a[*] in_b[*] in_valid rst}]

set_input_delay -clock clk -max 0 $ins

report_checks \
  -from [get_ports {in_b[2]}] \
  -to [get_pins {_12026_/D}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
