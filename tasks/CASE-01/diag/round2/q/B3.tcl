foreach scene [list \
    tt_025C_1v80 \
    tt_100C_1v80 \
    ss_100C_1v60 \
    ss_n40C_1v60 \
    ff_n40C_1v95 \
    ff_100C_1v95] {

  puts "===== $scene ====="
  report_checks \
    -from [get_ports {in_b[2]}] \
    -to [get_pins {_12026_/D}] \
    -path_delay max \
    -scene $scene \
    -format full_clock_expanded \
    -fields {slew cap input_pins fanout} \
    -digits 4
}
